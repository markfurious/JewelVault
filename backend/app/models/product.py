"""
Product model.
Core entity representing items in the inventory system.
Designed to be extensible for diamond and jewelry-specific attributes.
"""
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Product(Base, TimestampMixin):
    """
    Product model for inventory items.

    Extensible design:
    - attributes JSONB field allows storing diamond-specific properties
    - category/sub_category fields support product classification
    - SKU-based identification with unique constraint
    - Jewelry-specific fields for gold, carat, certification
    """

    __tablename__ = "products"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    sku = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Product classification
    category = Column(String(100), nullable=True, index=True)
    sub_category = Column(String(100), nullable=True)

    # Jewelry-specific fields
    style_number = Column(String(50), nullable=True)
    st_carat = Column(Numeric(10, 4), nullable=True)  # Stone carat weight
    product_weight = Column(Numeric(10, 4), nullable=True)  # Total product weight in grams
    gold_purity = Column(String(20), nullable=True)  # e.g., "14K", "18K", "22K", "24K"
    certified = Column(Boolean, default=False, nullable=True)

    # Pricing - using Numeric for precise decimal handling
    cost_price = Column(Numeric(12, 2), nullable=True)
    wholesale_price = Column(Numeric(12, 2), nullable=True)
    retail_price = Column(Numeric(12, 2), nullable=True)
    online_price = Column(Numeric(12, 2), nullable=True)

    # Product status
    is_active = Column(Boolean, default=True, nullable=False)

    # Extensible attributes (for diamonds: cut, clarity, carat, certification, etc.)
    # Stored as JSONB for flexible schema evolution
    attributes = Column(JSONB, nullable=True, default=dict)

    # Low stock threshold (can be overridden by ReorderRule)
    default_reorder_threshold = Column(Numeric(10, 2), default=10)

    # Unique constraint on SKU (redundant with unique=True but explicit)
    __table_args__ = (
        UniqueConstraint('sku', name='uq_products_sku'),
    )

    # Relationships
    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reorder_rules = relationship(
        "ReorderRule",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    sale_items = relationship(
        "SaleItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Product {self.name} ({self.sku})>"
