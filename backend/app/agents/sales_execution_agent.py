"""
Sales Execution Agent.
Processes sales transactions with full inventory integration.

Actions:
- Validates stock availability before sale
- Creates sale records via SaleService
- Deducts inventory automatically
- Handles returns and cancellations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.models.sale import Sale, SaleItem, SaleReturn
from app.models.agent_audit import AgentAuditLog
from app.services.sale_service import SaleService
from app.services.inventory_service import InventoryService
from app.schemas.sale import SaleCreate, SaleItemCreate, SaleType, PaymentMethod


class SalesExecutionAgent(AgentBase):
    """
    Agent that executes sales transactions.

    Triggers:
    - Natural language sale request
    - Bulk sale processing
    - Return/cancellation requests
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.sale_service = SaleService(db)
        self.inventory_service = InventoryService(db)

    def run(
        self,
        action: str,
        sale_data: Optional[Dict[str, Any]] = None,
        sale_id: Optional[UUID] = None,
        product_ids: Optional[List[UUID]] = None,
        customer_data: Optional[Dict[str, str]] = None,
    ) -> AgentResult:
        """
        Execute sales action.

        Args:
            action: Type of action (create_sale, cancel_sale, process_return)
            sale_data: Data for creating a sale
            sale_id: Sale ID for cancel/return operations
            product_ids: Product IDs for the sale
            customer_data: Customer information

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if action == "create_sale":
                self._create_sale(sale_data, product_ids, customer_data)
            elif action == "cancel_sale":
                self._cancel_sale(sale_id)
            elif action == "process_return":
                self._process_return(sale_id, product_ids, sale_data)
            else:
                return self._create_result(
                    success=False,
                    message=f"Unknown action: {action}",
                )

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Sales action '{action}' completed",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message=f"Sales action '{action}' failed",
                error=str(e),
            )

    def decide(
        self,
        action: str,
        product_ids: List[UUID],
        customer_data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Decide whether to proceed with the sale.

        Args:
            action: Type of sale action
            product_ids: Products involved
            customer_data: Customer information

        Returns:
            Decision dict with approval status and conditions
        """
        # Validate product availability
        availability_issues = []
        total_value = Decimal(0)

        for product_id in product_ids:
            product = self.db.get(Product, product_id)
            if not product:
                availability_issues.append(f"Product {product_id} not found")
                continue

            inventory = self.db.execute(
                select(Inventory).where(Inventory.product_id == product_id)
            ).scalar_one_or_none()

            if not inventory:
                availability_issues.append(f"No inventory record for {product.sku}")
                continue

            if inventory.status != InventoryStatus.AVAILABLE:
                availability_issues.append(
                    f"{product.sku} is {inventory.status}, not AVAILABLE"
                )
                continue

            # Add to total value
            total_value += product.retail_price or Decimal(0)

        # Check for fraud patterns using Claude
        if total_value > Decimal(10000):  # High-value sale
            situation = (
                f"High-value sale detected: ${total_value:.2f} for {len(product_ids)} items. "
                f"Customer: {customer_data or 'Walk-in'}"
            )

            fraud_decision = self.claude.generate_decision(
                situation=situation,
                options=[
                    "Proceed with standard processing",
                    "Flag for manager approval",
                    "Require additional verification",
                ],
                criteria="Balance customer experience with fraud prevention",
            )

            if "manager approval" in fraud_decision.get("selected_option", "").lower():
                return {
                    "approved": False,
                    "reason": "High-value sale requires manager approval",
                    "requires_approval": True,
                    "total_value": float(total_value),
                }

        if availability_issues:
            return {
                "approved": False,
                "reason": "Availability issues",
                "issues": availability_issues,
            }

        return {
            "approved": True,
            "reason": "All validations passed",
            "total_value": float(total_value),
            "item_count": len(product_ids),
        }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """Execute sale based on decision."""
        return self.actions

    def _create_sale(
        self,
        sale_data: Optional[Dict[str, Any]],
        product_ids: Optional[List[UUID]],
        customer_data: Optional[Dict[str, str]],
    ):
        """Create a new sale transaction."""
        if not product_ids:
            raise ValueError("product_ids required for sale creation")

        # Validate and decide
        decision = self.decide("create_sale", product_ids, customer_data)

        if not decision.get("approved"):
            if decision.get("requires_approval"):
                self._log_action(
                    action_type="SALE_PENDING_APPROVAL",
                    description=f"Sale pending manager approval: ${decision.get('total_value', 0):.2f}",
                    entity_type="sale",
                    data={
                        "reason": decision.get("reason"),
                        "product_count": len(product_ids),
                        "total_value": decision.get("total_value"),
                    },
                )
                return

            raise ValueError(f"Sale not approved: {', '.join(decision.get('issues', []))}")

        # Build sale schema
        sale_data = sale_data or {}
        customer_data = customer_data or {}

        items = [
            SaleItemCreate(
                product_id=pid,
                quantity=1,  # Item-based: each is 1 unit
            )
            for pid in product_ids
        ]

        sale_schema = SaleCreate(
            items=items,
            sale_type=SaleType(sale_data.get("sale_type", "RETAIL")),
            customer_name=customer_data.get("name", "Walk-in Customer"),
            customer_email=customer_data.get("email"),
            customer_phone=customer_data.get("phone"),
            tax_rate=sale_data.get("tax_rate", 8.25),
            discount_amount=Decimal(str(sale_data.get("discount_amount", 0))),
            payment_method=PaymentMethod(sale_data.get("payment_method", "CASH")),
            notes=sale_data.get("notes"),
        )

        # Execute sale
        sale = self.sale_service.create(sale_schema)

        self._log_action(
            action_type="CREATE_SALE",
            description=f"Created sale {sale.sale_number} with {len(product_ids)} items",
            entity_type="sale",
            entity_id=sale.id,
            data={
                "sale_number": sale.sale_number,
                "total_amount": float(sale.total_amount),
                "item_count": len(product_ids),
                "customer": customer_data.get("name", "Walk-in Customer"),
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="CREATE_SALE",
            description=f"Sale {sale.sale_number} created",
            entity_type="sale",
            entity_id=sale.id,
            action_data={
                "sale_number": sale.sale_number,
                "total_amount": float(sale.total_amount),
            },
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def _cancel_sale(self, sale_id: Optional[UUID]):
        """Cancel a sale and restore inventory."""
        if not sale_id:
            raise ValueError("sale_id required for cancellation")

        sale = self.db.get(Sale, sale_id)
        if not sale:
            raise ValueError(f"Sale {sale_id} not found")

        # Get item count for logging
        item_count = len(sale.items) if sale.items else 0

        # Cancel the sale (restores inventory)
        cancelled_sale = self.sale_service.cancel_sale(sale_id)

        self._log_action(
            action_type="CANCEL_SALE",
            description=f"Cancelled sale {cancelled_sale.sale_number}, restored {item_count} items",
            entity_type="sale",
            entity_id=cancelled_sale.id,
            data={
                "sale_number": cancelled_sale.sale_number,
                "original_status": sale.status,
                "new_status": cancelled_sale.status,
                "items_restored": item_count,
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="CANCEL_SALE",
            description=f"Sale {cancelled_sale.sale_number} cancelled",
            entity_type="sale",
            entity_id=cancelled_sale.id,
            action_data={"items_restored": item_count},
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def _process_return(
        self,
        sale_id: Optional[UUID],
        product_ids: Optional[List[UUID]],
        sale_data: Optional[Dict[str, Any]],
    ):
        """Process a return request."""
        if not sale_id:
            raise ValueError("sale_id required for return")

        sale_data = sale_data or {}
        product_ids = product_ids or []

        # Create return request
        return_record = self.sale_service.request_return(
            sale_id=sale_id,
            product_ids=product_ids,
            reason=sale_data.get("reason", "Customer return"),
            requested_by=sale_data.get("requested_by", "system"),
            refund_amount=sale_data.get("refund_amount"),
        )

        self._log_action(
            action_type="PROCESS_RETURN",
            description=f"Return requested for sale {sale_id}, {len(product_ids)} items",
            entity_type="sale_return",
            entity_id=return_record.id,
            data={
                "sale_id": str(sale_id),
                "product_count": len(product_ids),
                "refund_amount": float(return_record.refund_amount),
                "status": return_record.status,
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="PROCESS_RETURN",
            description=f"Return requested for sale {sale_id}",
            entity_type="sale_return",
            entity_id=return_record.id,
            action_data={"refund_amount": float(return_record.refund_amount)},
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)
