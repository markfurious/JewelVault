"""
Inventory service.
Handles all business logic related to item-based inventory management.
Each SKU represents exactly ONE physical item tracked by status.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.inventory import Inventory, InventoryStatus, InventoryTransaction
from app.models.product import Product
from app.schemas.inventory import InventoryUpdate, InventoryAdjustment
from app.utils.exceptions import NotFoundError, ValidationError


# Allowed status transitions (from_status -> [allowed_to_statuses])
ALLOWED_TRANSITIONS = {
    "AVAILABLE": ["SOLD", "RESERVED"],
    "RESERVED": ["AVAILABLE", "SOLD"],
    "SOLD": ["RETURN_PENDING"],
    "RETURN_PENDING": ["AVAILABLE", "SOLD"],
}


class InventoryService:
    """Service for inventory operations (item-based model)."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_product_id(self, product_id: UUID) -> Inventory:
        """
        Get inventory for a product.

        Args:
            product_id: UUID of the product

        Returns:
            Inventory instance

        Raises:
            NotFoundError: If inventory not found
        """
        inventory = self.db.execute(
            select(Inventory).where(Inventory.product_id == product_id)
        ).scalar_one_or_none()

        if not inventory:
            raise NotFoundError(f"Inventory for product {product_id} not found")
        return inventory

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> tuple[List[Inventory], int]:
        """
        Get all inventory with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            status_filter: Filter by status (AVAILABLE, SOLD, RESERVED)

        Returns:
            Tuple of (inventory list, total count)
        """
        query = select(Inventory).join(Product)

        if status_filter:
            query = query.where(Inventory.status == status_filter.upper())

        total = self.db.execute(select(func.count()).select_from(Inventory)).scalar() or 0
        inventories = (
            self.db.execute(query.offset(skip).limit(limit)).scalars().all()
        )

        return list(inventories), total

    def update_status(
        self,
        product_id: UUID,
        new_status: str,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None,
    ) -> Inventory:
        """
        Manually update inventory status.

        Args:
            product_id: UUID of the product
            new_status: New status (AVAILABLE, SOLD, RESERVED)
            notes: Optional notes for the update
            performed_by: User who performed the update

        Returns:
            Updated Inventory instance
        """
        inventory = self.get_by_product_id(product_id)
        old_status = inventory.status

        # Validate status
        if new_status not in [InventoryStatus.AVAILABLE, InventoryStatus.SOLD, InventoryStatus.RESERVED]:
            raise ValidationError(f"Invalid status: {new_status}")

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="ADJUSTMENT",
            status_before=old_status,
            status_after=new_status,
            notes=notes,
            performed_by=performed_by,
        )
        self.db.add(transaction)

        # Update status
        inventory.status = new_status
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def adjust_status(
        self,
        product_id: UUID,
        adjustment: InventoryAdjustment,
        performed_by: Optional[str] = None,
    ) -> Inventory:
        """
        Adjust inventory status.

        Args:
            product_id: UUID of the product
            adjustment: InventoryAdjustment schema
            performed_by: User who performed the adjustment

        Returns:
            Updated Inventory instance
        """
        inventory = self.get_by_product_id(product_id)
        old_status = inventory.status
        new_status = adjustment.status.value if hasattr(adjustment.status, 'value') else adjustment.status

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=adjustment.transaction_type,
            status_before=old_status,
            status_after=new_status,
            notes=adjustment.notes,
            performed_by=performed_by,
        )
        self.db.add(transaction)

        inventory.status = new_status
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def mark_sold(
        self,
        product_id: UUID,
        reference_id: Optional[UUID] = None,
        reference_type: str = "sale",
    ) -> Inventory:
        """
        Mark item as sold.

        Args:
            product_id: UUID of the product
            reference_id: Reference to related entity (e.g., sale ID)
            reference_type: Type of reference (e.g., "sale")

        Returns:
            Updated Inventory instance

        Raises:
            ValidationError: If item is not available
        """
        inventory = self.get_by_product_id(product_id)

        if inventory.status != InventoryStatus.AVAILABLE:
            raise ValidationError(
                f"Cannot sell item. Current status: {inventory.status}. "
                f"Item must be AVAILABLE to sell."
            )

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="SALE",
            status_before=inventory.status,
            status_after=InventoryStatus.SOLD,
            reference_id=reference_id,
            reference_type=reference_type,
        )
        self.db.add(transaction)

        inventory.status = InventoryStatus.SOLD
        self.db.commit()

        return inventory

    def mark_available(
        self,
        product_id: UUID,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None,
    ) -> Inventory:
        """
        Mark item as available (restock).

        Args:
            product_id: UUID of the product
            notes: Optional notes
            performed_by: User who performed the restock

        Returns:
            Updated Inventory instance
        """
        inventory = self.get_by_product_id(product_id)
        old_status = inventory.status

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="RESTOCK",
            status_before=old_status,
            status_after=InventoryStatus.AVAILABLE,
            notes=notes,
            performed_by=performed_by,
        )
        self.db.add(transaction)

        inventory.status = InventoryStatus.AVAILABLE
        self.db.commit()
        self.db.refresh(inventory)

        return inventory

    def reserve(
        self,
        product_id: UUID,
        reference_id: Optional[UUID] = None,
    ) -> Inventory:
        """
        Reserve item for an order.

        Args:
            product_id: UUID of the product
            reference_id: Reference to related entity (e.g., order ID)

        Returns:
            Updated Inventory instance

        Raises:
            ValidationError: If item is not available
        """
        inventory = self.get_by_product_id(product_id)

        if inventory.status != InventoryStatus.AVAILABLE:
            raise ValidationError(
                f"Cannot reserve item. Current status: {inventory.status}. "
                f"Item must be AVAILABLE to reserve."
            )

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="RESERVE",
            status_before=inventory.status,
            status_after=InventoryStatus.RESERVED,
            reference_id=reference_id,
            reference_type="order",
        )
        self.db.add(transaction)

        inventory.status = InventoryStatus.RESERVED
        self.db.commit()

        return inventory

    def release_reservation(
        self,
        product_id: UUID,
    ) -> Inventory:
        """
        Release reserved item back to available.

        Args:
            product_id: UUID of the product

        Returns:
            Updated Inventory instance

        Raises:
            ValidationError: If item is not reserved
        """
        inventory = self.get_by_product_id(product_id)

        if inventory.status != InventoryStatus.RESERVED:
            raise ValidationError(
                f"Cannot release reservation. Current status: {inventory.status}. "
                f"Item must be RESERVED to release."
            )

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="RELEASE",
            status_before=inventory.status,
            status_after=InventoryStatus.AVAILABLE,
        )
        self.db.add(transaction)

        inventory.status = InventoryStatus.AVAILABLE
        self.db.commit()

        return inventory

    def bulk_update_status(
        self,
        product_ids: List[UUID],
        target_status: str,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None,
    ) -> List[UUID]:
        """
        Atomically update status for multiple inventory items.

        - Locks all rows with SELECT ... FOR UPDATE
        - Validates ALL transitions BEFORE any update
        - Rejects entire batch if ANY item fails validation
        - Creates transaction log entries with accurate status_before
        - Returns list of updated product IDs

        Args:
            product_ids: List of product UUIDs to update
            target_status: New status to set
            notes: Optional notes for the transaction
            performed_by: User who performed the update

        Returns:
            List of updated product IDs

        Raises:
            ValidationError: If any transition is invalid
        """
        if not product_ids:
            raise ValidationError("No product IDs provided")

        # Validate target status is known
        if target_status not in ALLOWED_TRANSITIONS.keys():
            raise ValidationError(f"Invalid target status: {target_status}")

        # Lock all inventory rows for update (sorted to prevent deadlocks)
        sorted_ids = sorted(product_ids)
        lock_query = (
            select(Inventory)
            .where(Inventory.product_id.in_(sorted_ids))
            .with_for_update()
        )
        inventories = self.db.execute(lock_query).scalars().all()

        if len(inventories) != len(product_ids):
            found_ids = {str(inv.product_id) for inv in inventories}
            missing = set(str(pid) for pid in product_ids) - found_ids
            raise NotFoundError(f"Inventory not found for products: {', '.join(missing)}")

        # Validate ALL transitions BEFORE any update
        invalid_transitions = []
        for inv in inventories:
            current_status = inv.status
            allowed_targets = ALLOWED_TRANSITIONS.get(current_status, [])
            if target_status not in allowed_targets:
                invalid_transitions.append({
                    "product_id": str(inv.product_id),
                    "current_status": current_status,
                    "target_status": target_status,
                })

        if invalid_transitions:
            # Rollback is automatic since we haven't committed
            raise ValidationError(
                f"Invalid status transitions: " +
                "; ".join(
                    f"Product {t['product_id']}: {t['current_status']} -> {t['target_status']}"
                    for t in invalid_transitions
                )
            )

        # All valid - execute updates and create transaction logs
        updated_ids = []
        transactions = []
        for inv in inventories:
            old_status = inv.status
            inv.status = target_status
            updated_ids.append(inv.product_id)

            # Create transaction record
            txn = InventoryTransaction(
                inventory_id=inv.id,
                transaction_type="BULK_UPDATE",
                status_before=old_status,
                status_after=target_status,
                notes=notes,
                performed_by=performed_by,
            )
            transactions.append(txn)

        # Add all transactions in bulk
        self.db.add_all(transactions)

        return updated_ids

    def get_transaction_history(
        self,
        product_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InventoryTransaction]:
        """
        Get transaction history for a product.

        Args:
            product_id: UUID of the product
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of InventoryTransaction
        """
        inventory = self.get_by_product_id(product_id)

        transactions = (
            self.db.execute(
                select(InventoryTransaction)
                .where(InventoryTransaction.inventory_id == inventory.id)
                .order_by(InventoryTransaction.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(transactions)
