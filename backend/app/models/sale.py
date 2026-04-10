"""
Sale models.
Tracks sales transactions and line items.
"""
from sqlalchemy import (
    Column,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Sale(Base, TimestampMixin):
    """
    Sale header model.
    Represents a complete sales transaction.
    """

    __tablename__ = "sales"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Sale identification
    sale_number = Column(String(50), unique=True, nullable=False, index=True)

    # Customer info (extensible for full CRM)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)

    # Sale type
    sale_type = Column(
        String(20),
        nullable=False,
        default="RETAIL",
    )  # RETAIL, WHOLESALE, ONLINE

    # Financial
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)

    # Payment
    payment_method = Column(String(50), nullable=True)  # CASH, CARD, TRANSFER
    payment_status = Column(
        String(20),
        default="COMPLETED",
    )  # PENDING, COMPLETED, REFUNDED

    # Status
    status = Column(
        String(20),
        default="COMPLETED",
        nullable=False,
    )  # COMPLETED, CANCELLED, REFUNDED

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    sale_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Sale {self.sale_number}: {self.total_amount}>"


class SaleItem(Base, TimestampMixin):
    """
    Sale line item model.
    Individual items within a sale.
    """

    __tablename__ = "sale_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    sale_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Item details (snapshot at time of sale)
    product_name = Column(String(255), nullable=False)  # Snapshot of product name
    product_sku = Column(String(100), nullable=False)  # Snapshot of SKU

    # Quantities and pricing
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_sale_item_quantity_positive"),
    )

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleItem {self.product_name} x{self.quantity}>"


class SaleReturn(Base, TimestampMixin):
    """
    Sale return tracking model.
    Records return requests and approval workflow.
    """

    __tablename__ = "sale_returns"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    sale_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_ids = Column(
        String(500),  # Comma-separated UUIDs
        nullable=False,
    )
    reason = Column(String(500), nullable=False)
    refund_amount = Column(Numeric(12, 2), nullable=False)

    # Return status: PENDING, APPROVED, REJECTED
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
        index=True,
    )

    # Request info
    requested_by = Column(String(100), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Approval info
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Rejection info
    rejected_by = Column(String(100), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    # Relationships
    sale = relationship("Sale", back_populates="returns")

    def __repr__(self):
        return f"<SaleReturn {self.id}: {self.status}>"


# Add reverse relationship to Sale
Sale.returns = relationship(
    "SaleReturn",
    back_populates="sale",
    cascade="all, delete-orphan",
    order_by="SaleReturn.created_at.desc()",
)
