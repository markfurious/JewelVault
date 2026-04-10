"""
Inventory models.
Tracks individual items by status (item-based model).
Each SKU represents exactly ONE physical item.
"""
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class InventoryStatus(str):
    """Enumeration of inventory status values."""
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    RESERVED = "RESERVED"
    RETURN_PENDING = "RETURN_PENDING"


class Inventory(Base, TimestampMixin):
    """
    Inventory tracking model (item-based).
    One-to-one relationship with Product.
    Each SKU represents exactly ONE item tracked by status.
    """

    __tablename__ = "inventory"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Item status (replaces quantity-based tracking)
    status = Column(
        String(20),
        default=InventoryStatus.AVAILABLE,
        nullable=False,
        index=True,
    )

    # Location tracking (extensible for multi-store)
    location = Column(String(255), nullable=True)
    warehouse_code = Column(String(50), nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('AVAILABLE', 'SOLD', 'RESERVED', 'RETURN_PENDING')",
            name="check_status_valid",
        ),
    )

    # Relationships
    product = relationship("Product", back_populates="inventory")
    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
        order_by="InventoryTransaction.created_at.desc()",
    )

    @property
    def is_available(self) -> bool:
        """Check if item is available for sale."""
        return self.status == InventoryStatus.AVAILABLE

    def __repr__(self):
        return f"<Inventory {self.product_id}: {self.status}>"


class InventoryTransaction(Base, TimestampMixin):
    """
    Inventory transaction history.
    Records all status changes for audit trail.
    """

    __tablename__ = "inventory_transactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    inventory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction details
    transaction_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # SALE, RESTOCK, ADJUSTMENT, RETURN, RESERVE, RELEASE

    # Status tracking (replaces quantity tracking)
    status_before = Column(String(20), nullable=False)
    status_after = Column(String(20), nullable=False)

    # Reference tracking
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # e.g., sale_id
    reference_type = Column(String(50), nullable=True)  # e.g., "sale"

    # Notes
    notes = Column(String(500), nullable=True)
    performed_by = Column(String(100), nullable=True)  # User/system

    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.transaction_type}: {self.status_before} -> {self.status_after}>"
