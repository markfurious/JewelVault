"""
Inventory Manager Agent.
Automatically manages inventory reordering and dead stock handling.

Actions:
- Creates reorder requests when stock < threshold
- Flags dead stock for discount
- Uses AnalyticsService for velocity data
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.inventory import Inventory, InventoryStatus
from app.models.product import Product
from app.models.reorder import ReorderRule
from app.models.agent_audit import AgentAuditLog
from app.models.agent_request import AgentRequest
from app.services.inventory_service import InventoryService
from app.services.analytics_service import AnalyticsService


class InventoryManagerAgent(AgentBase):
    """
    Agent that manages inventory reordering and dead stock.

    Triggers:
    - Low stock: Creates reorder requests
    - Dead stock: Flags for discount
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.inventory_service = InventoryService(db)
        self.analytics_service = AnalyticsService(db)

    def run(self, check_threshold: bool = True, check_dead_stock: bool = True) -> AgentResult:
        """
        Run inventory management checks.

        Args:
            check_threshold: Check for low stock reorders
            check_dead_stock: Check for dead stock to discount

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if check_threshold:
                self._check_low_stock()

            if check_dead_stock:
                self._check_dead_stock()

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Processed {len(self.actions)} inventory actions",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Inventory management failed",
                error=str(e),
            )

    def decide(self, product_id: UUID, current_stock: int, threshold: int) -> Dict[str, Any]:
        """
        Decide what action to take for a product.

        Args:
            product_id: Product to evaluate
            current_stock: Current stock level
            threshold: Reorder threshold

        Returns:
            Decision dict
        """
        if current_stock <= 0:
            return {
                "action": "urgent_reorder",
                "reason": "Stock depleted",
                "priority": "high",
            }
        elif current_stock < threshold:
            return {
                "action": "reorder",
                "reason": "Below threshold",
                "priority": "normal",
            }
        else:
            return {
                "action": "no_action",
                "reason": "Stock adequate",
                "priority": "low",
            }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """
        Execute inventory action based on decision.

        Args:
            decision: Decision from decide()

        Returns:
            List of actions taken
        """
        action_type = decision.get("action")

        if action_type == "no_action":
            return []

        # Decision already executed in run() - this is for interface compliance
        return self.actions

    def _check_low_stock(self):
        """Check for products below reorder threshold and create reorder requests."""
        # Get all active products with inventory
        products = self.db.execute(
            select(Product).join(Inventory).where(Product.is_active == True)
        ).scalars().all()

        for product in products:
            inventory = self.db.execute(
                select(Inventory).where(Inventory.product_id == product.id)
            ).scalar_one_or_none()

            if not inventory:
                continue

            # Get reorder rule
            rule = self.db.execute(
                select(ReorderRule).where(ReorderRule.product_id == product.id)
            ).scalar_one_or_none()

            if not rule or not rule.is_active:
                continue

            # Check if below threshold
            # In item-based model: status SOLD means needs reorder
            needs_reorder = inventory.status == InventoryStatus.SOLD

            if needs_reorder:
                decision = self.decide(
                    product_id=product.id,
                    current_stock=0,
                    threshold=float(rule.min_threshold),
                )

                if decision["action"] in ["reorder", "urgent_reorder"]:
                    self._create_reorder_request(product, rule, decision)

    def _check_dead_stock(self):
        """Check for dead stock (no sales in 90+ days) and flag for discount."""
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        # Get AVAILABLE products that haven't sold in 90 days
        products = self.db.execute(
            select(Product)
            .join(Inventory)
            .outerjoin(
                select(Product)
                .join(Inventory)
                .where(Inventory.status == InventoryStatus.SOLD)
                .where(Inventory.updated_at >= cutoff_date)
                .subquery()
            )
            .where(Product.is_active == True)
            .where(Inventory.status == InventoryStatus.AVAILABLE)
        ).scalars().all()

        for product in products:
            # Check if product has any sales history
            has_recent_sales = self.db.execute(
                select(Inventory)
                .where(Inventory.product_id == product.id)
                .where(Inventory.status == InventoryStatus.SOLD)
                .where(Inventory.updated_at >= cutoff_date)
            ).scalar_one_or_none()

            if not has_recent_sales:
                self._flag_for_discount(product)

    def _create_reorder_request(
        self,
        product: Product,
        rule: ReorderRule,
        decision: Dict[str, Any],
    ):
        """Create a reorder request for a product."""
        # Create agent request record for admin review
        request = AgentRequest(
            request_type="reorder",
            title=f"Reorder: {product.name}",
            description=f"Product {product.name} ({product.sku}) needs reordering. {decision['reason']}.",
            agent_name=self.get_name(),
            entity_type="product",
            entity_id=product.id,
            request_data={
                "product_name": product.name,
                "product_sku": product.sku,
                "priority": decision.get("priority", "normal"),
                "reason": decision["reason"],
                "min_threshold": str(rule.min_threshold),
                "target_stock": str(rule.target_stock),
                "preferred_supplier": rule.preferred_supplier,
            },
            proposed_action=f"Create purchase order for {rule.target_stock} units from {rule.preferred_supplier or 'preferred supplier'}",
            impact_summary=f"Restock {product.name} to maintain inventory levels. Current: 0, Target: {rule.target_stock}",
            status="pending",
        )
        self.db.add(request)

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="CREATE_REORDER_REQUEST",
            description=f"Reorder request for {product.name}",
            entity_type="product",
            entity_id=product.id,
            action_data={"priority": decision.get("priority"), "request_id": str(request.id)},
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def _flag_for_discount(self, product: Product):
        """Flag a product for discount due to dead stock."""
        discount_recommendation = 0.15  # 15% discount

        # Use Claude to suggest discount based on product attributes
        if product.attributes:
            situation = (
                f"Product {product.name} ({product.sku}) has been in stock for 90+ days. "
                f"Category: {product.category}, "
                f"Current retail price: ${product.retail_price}, "
                f"Cost price: ${product.cost_price}"
            )

            decision = self.claude.generate_decision(
                situation=situation,
                options=["10% discount", "15% discount", "20% discount", "25% discount"],
                criteria="Maximize clearance while minimizing margin loss",
            )

            discount_map = {
                "10% discount": 0.10,
                "15% discount": 0.15,
                "20% discount": 0.20,
                "25% discount": 0.25,
            }
            discount_recommendation = discount_map.get(decision.get("selected_option", ""), 0.15)

        # Create agent request record for admin review
        request = AgentRequest(
            request_type="dead_stock_discount",
            title=f"Discount: {product.name} (Dead Stock)",
            description=f"Product {product.name} ({product.sku}) has had no sales in 90+ days. Recommending {discount_recommendation*100:.0f}% discount to clear inventory.",
            agent_name=self.get_name(),
            entity_type="product",
            entity_id=product.id,
            request_data={
                "product_name": product.name,
                "product_sku": product.sku,
                "recommended_discount": discount_recommendation,
                "days_without_sales": 90,
                "current_price": str(product.retail_price),
                "new_price": str(product.retail_price * Decimal(str(1 - discount_recommendation))),
            },
            proposed_action=f"Apply {discount_recommendation*100:.0f}% discount to {product.name}, reducing price from ${product.retail_price} to ${product.retail_price * Decimal(str(1 - discount_recommendation)):.2f}",
            impact_summary=f"Clear dead stock and recover capital. Estimated new price: ${product.retail_price * Decimal(str(1 - discount_recommendation)):.2f}",
            status="pending",
        )
        self.db.add(request)

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="FLAG_DEAD_STOCK",
            description=f"Dead stock flag for {product.name}",
            entity_type="product",
            entity_id=product.id,
            action_data={"recommended_discount": discount_recommendation, "request_id": str(request.id)},
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)
