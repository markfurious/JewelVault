"""
Anomaly Action Agent.
Detects unusual patterns and takes automated actions.

Actions:
- Detects price anomalies (unusual discounts, price mismatches)
- Detects rapid sales patterns (potential fraud)
- Detects inventory anomalies (status changes, missing items)
- Takes action: block transaction OR flag record for review
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import json

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus, InventoryTransaction
from app.models.sale import Sale, SaleItem
from app.models.agent_audit import AgentAuditLog


class AnomalyActionAgent(AgentBase):
    """
    Agent that detects and responds to anomalies.

    Detection categories:
    - Price anomalies: Unusual discounts, cost > retail
    - Sales anomalies: Rapid successive sales, high-value transactions
    - Inventory anomalies: Unusual status changes, pattern deviations
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)

        # Anomaly thresholds
        self.price_anomaly_threshold = 0.3  # 30% below cost
        self.rapid_sale_threshold = 5  # Sales per hour
        self.high_value_threshold = Decimal(10000)  # $10,000

    def run(
        self,
        anomaly_type: str,
        entity_id: Optional[UUID] = None,
        time_window_hours: int = 24,
    ) -> AgentResult:
        """
        Run anomaly detection.

        Args:
            anomaly_type: Type to detect (price, sales, inventory, all)
            entity_id: Specific entity to analyze
            time_window_hours: Hours to look back

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if anomaly_type in ["price", "all"]:
                self._detect_price_anomalies(entity_id)

            if anomaly_type in ["sales", "all"]:
                self._detect_sales_anomalies(time_window_hours)

            if anomaly_type in ["inventory", "all"]:
                self._detect_inventory_anomalies(time_window_hours)

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Anomaly detection complete: {len(self.actions)} anomalies found",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Anomaly detection failed",
                error=str(e),
            )

    def decide(
        self,
        anomaly_type: str,
        anomaly_data: Dict[str, Any],
        severity: str,
    ) -> Dict[str, Any]:
        """
        Decide what action to take for detected anomaly.

        Args:
            anomaly_type: Type of anomaly
            anomaly_data: Details about the anomaly
            severity: Severity level (low, medium, high, critical)

        Returns:
            Decision dict with action and reasoning
        """
        # Build situation description for Claude
        situation = f"""
Anomaly Detected:
- Type: {anomaly_type}
- Severity: {severity}
- Details: {json.dumps(anomaly_data, default=str)}
"""

        # Define actions based on severity
        if severity == "critical":
            options = [
                "Block transaction immediately",
                "Flag for immediate review + notify admin",
                "Freeze related accounts",
            ]
        elif severity == "high":
            options = [
                "Flag for urgent review",
                "Block pending approval",
                "Add to watchlist",
            ]
        elif severity == "medium":
            options = [
                "Flag for review",
                "Log for pattern analysis",
                "Standard monitoring",
            ]
        else:  # low
            options = [
                "Log for analysis",
                "No action required",
                "Add to daily report",
            ]

        decision = self.claude.generate_decision(
            situation=situation,
            options=options,
            criteria="Balance risk mitigation with operational efficiency",
        )

        return {
            "action": decision.get("selected_option", "Log for analysis"),
            "severity": severity,
            "reasoning": decision.get("reasoning", "Automated risk assessment"),
            "confidence": decision.get("confidence", 0.7),
            "requires_human_review": severity in ["critical", "high"],
        }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """Execute action based on decision."""
        return self.actions

    def _detect_price_anomalies(self, entity_id: Optional[UUID] = None):
        """Detect price-related anomalies."""
        query = select(Product).where(Product.is_active == True)

        if entity_id:
            query = query.where(Product.id == entity_id)

        products = self.db.execute(query).scalars().all()

        for product in products:
            anomalies_found = []

            # Check: Retail price below cost
            if product.retail_price and product.cost_price:
                if product.retail_price < product.cost_price:
                    anomalies_found.append({
                        "type": "price_below_cost",
                        "details": {
                            "cost_price": float(product.cost_price),
                            "retail_price": float(product.retail_price),
                            "loss_margin": float(product.cost_price - product.retail_price),
                        },
                        "severity": "high",
                    })

            # Check: Unusual price gap between retail and wholesale
            if product.retail_price and product.wholesale_price:
                if product.wholesale_price > product.retail_price * Decimal("0.9"):
                    anomalies_found.append({
                        "type": "wholesale_retail_mismatch",
                        "details": {
                            "retail_price": float(product.retail_price),
                            "wholesale_price": float(product.wholesale_price),
                        },
                        "severity": "medium",
                    })

            # Check: Zero or very low price
            if product.retail_price and product.retail_price < Decimal("1"):
                anomalies_found.append({
                    "type": "zero_price",
                    "details": {
                        "retail_price": float(product.retail_price),
                    },
                    "severity": "high",
                })

            # Process each anomaly
            for anomaly in anomalies_found:
                decision = self.decide(
                    anomaly_type="price",
                    anomaly_data=anomaly["details"],
                    severity=anomaly["severity"],
                )

                self._log_anomaly(
                    anomaly_type="price",
                    entity_type="product",
                    entity_id=product.id,
                    anomaly_data=anomaly,
                    decision=decision,
                )

    def _detect_sales_anomalies(self, time_window_hours: int):
        """Detect sales-related anomalies."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Check: High-value sales
        high_value_sales = self.db.execute(
            select(Sale)
            .where(Sale.sale_date >= cutoff_time)
            .where(Sale.total_amount >= self.high_value_threshold)
            .order_by(Sale.total_amount.desc())
        ).scalars().all()

        for sale in high_value_sales:
            decision = self.decide(
                anomaly_type="sales",
                anomaly_data={
                    "sale_number": sale.sale_number,
                    "total_amount": float(sale.total_amount),
                    "customer": sale.customer_name,
                    "payment_method": sale.payment_method,
                },
                severity="high" if sale.total_amount >= self.high_value_threshold * 2 else "medium",
            )

            self._log_anomaly(
                anomaly_type="sales",
                entity_type="sale",
                entity_id=sale.id,
                anomaly_data={
                    "type": "high_value_sale",
                    "details": decision,
                },
                decision=decision,
            )

        # Check: Rapid successive sales (same customer or payment method)
        recent_sales = self.db.execute(
            select(Sale)
            .where(Sale.sale_date >= cutoff_time)
            .where(Sale.status == "COMPLETED")
            .order_by(Sale.sale_date.desc())
        ).scalars().all()

        # Group by customer
        customer_sales = {}
        for sale in recent_sales:
            key = sale.customer_email or sale.customer_phone or sale.customer_name
            if key:
                customer_sales.setdefault(key, []).append(sale)

        for customer, sales in customer_sales.items():
            if len(sales) >= self.rapid_sale_threshold:
                decision = self.decide(
                    anomaly_type="sales",
                    anomaly_data={
                        "customer": customer,
                        "sale_count": len(sales),
                        "time_window_hours": time_window_hours,
                        "total_value": sum(float(s.total_amount) for s in sales),
                    },
                    severity="high",
                )

                self._log_anomaly(
                    anomaly_type="sales",
                    entity_type="customer",
                    entity_id=None,
                    anomaly_data={
                        "type": "rapid_sales",
                        "details": {"customer": customer, "count": len(sales)},
                    },
                    decision=decision,
                )

    def _detect_inventory_anomalies(self, time_window_hours: int):
        """Detect inventory-related anomalies."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Check: Unusual status change patterns
        transactions = self.db.execute(
            select(InventoryTransaction)
            .where(InventoryTransaction.created_at >= cutoff_time)
            .order_by(InventoryTransaction.created_at.desc())
        ).scalars().all()

        # Group by inventory item
        item_transactions = {}
        for txn in transactions:
            item_transactions.setdefault(txn.inventory_id, []).append(txn)

        for inventory_id, txns in item_transactions.items():
            # Check for multiple status changes in short period
            if len(txns) >= 5:
                # Get product info
                inventory = self.db.get(Inventory, inventory_id)
                product = self.db.get(Product, inventory.product_id) if inventory else None

                decision = self.decide(
                    anomaly_type="inventory",
                    anomaly_data={
                        "product_sku": product.sku if product else "Unknown",
                        "transaction_count": len(txns),
                        "time_window_hours": time_window_hours,
                        "status_changes": [
                            {"from": t.status_before, "to": t.status_after}
                            for t in txns[:5]
                        ],
                    },
                    severity="medium",
                )

                self._log_anomaly(
                    anomaly_type="inventory",
                    entity_type="inventory",
                    entity_id=inventory.product_id if inventory else None,
                    anomaly_data={
                        "type": "frequent_status_changes",
                        "details": {"count": len(txns)},
                    },
                    decision=decision,
                )

        # Check: SOLD items without corresponding sale record
        sold_inventory = self.db.execute(
            select(Inventory)
            .where(Inventory.status == InventoryStatus.SOLD)
            .where(Inventory.updated_at >= cutoff_time)
        ).scalars().all()

        for inv in sold_inventory:
            # Verify sale record exists
            has_sale = self.db.execute(
                select(SaleItem)
                .where(SaleItem.product_id == inv.product_id)
                .limit(1)
            ).scalar_one_or_none()

            if not has_sale:
                product = self.db.get(Product, inv.product_id)

                decision = self.decide(
                    anomaly_type="inventory",
                    anomaly_data={
                        "product_sku": product.sku if product else "Unknown",
                        "status": "SOLD",
                        "no_sale_record": True,
                    },
                    severity="high",
                )

                self._log_anomaly(
                    anomaly_type="inventory",
                    entity_type="product",
                    entity_id=inv.product_id,
                    anomaly_data={
                        "type": "sold_without_sale_record",
                        "details": {"sku": product.sku if product else "Unknown"},
                    },
                    decision=decision,
                )

    def _log_anomaly(
        self,
        anomaly_type: str,
        entity_type: str,
        entity_id: Optional[UUID],
        anomaly_data: Dict[str, Any],
        decision: Dict[str, Any],
    ):
        """Log detected anomaly and action taken."""
        action_type = decision.get("action", "Log for analysis")

        self._log_action(
            action_type=f"DETECT_{anomaly_type.upper()}_ANOMALY",
            description=f"{anomaly_type} anomaly: {action_type}",
            entity_type=entity_type,
            entity_id=entity_id,
            data={
                "anomaly_type": anomaly_type,
                "anomaly_details": anomaly_data,
                "severity": decision.get("severity"),
                "action_taken": action_type,
                "requires_review": decision.get("requires_human_review", False),
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type=f"DETECT_{anomaly_type.upper()}_ANOMALY",
            description=f"{anomaly_type.capitalize()} anomaly detected",
            entity_type=entity_type,
            entity_id=entity_id,
            action_data={
                "anomaly": anomaly_data,
                "decision": decision,
            },
            success=not decision.get("requires_human_review", False),
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def block_transaction(
        self,
        sale_id: UUID,
        reason: str,
    ) -> AgentResult:
        """Block a transaction (mark for review)."""
        sale = self.db.get(Sale, sale_id)
        if not sale:
            return self._create_result(
                success=False,
                message=f"Sale {sale_id} not found",
            )

        # Update sale status
        sale.status = "PENDING_REVIEW"
        sale.notes = f"BLOCKED by anomaly agent: {reason}" if sale.notes else f"BLOCKED: {reason}"

        if not self.dry_run:
            self.db.add(sale)

        self._log_action(
            action_type="BLOCK_TRANSACTION",
            description=f"Blocked sale {sale.sale_number}: {reason}",
            entity_type="sale",
            entity_id=sale.id,
            data={"reason": reason, "sale_number": sale.sale_number},
        )

        self._commit_if_not_dry_run()

        return self._create_result(
            success=True,
            message=f"Transaction blocked: {reason}",
        )

    def flag_record(
        self,
        entity_type: str,
        entity_id: UUID,
        reason: str,
        priority: str = "normal",
    ) -> AgentResult:
        """Flag a record for review."""
        self._log_action(
            action_type="FLAG_FOR_REVIEW",
            description=f"Flagged {entity_type} {entity_id}: {reason}",
            entity_type=entity_type,
            entity_id=entity_id,
            data={"reason": reason, "priority": priority},
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="FLAG_FOR_REVIEW",
            description=f"Flagged for review: {reason}",
            entity_type=entity_type,
            entity_id=entity_id,
            action_data={"reason": reason, "priority": priority},
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

        self._commit_if_not_dry_run()

        return self._create_result(
            success=True,
            message=f"Record flagged for review: {reason}",
        )
