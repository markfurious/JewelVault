"""
Reorder rules model.
Defines when and how much to reorder for each product.
"""
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ReorderRule(Base, TimestampMixin):
    """
    Reorder rule model.
    Defines reorder thresholds and quantities for products.

    Supports smart reordering based on:
    - Minimum threshold (absolute minimum stock)
    - Target stock level (desired stock after reorder)
    - Sales velocity multiplier (adjust for fast/slow movers)
    """

    __tablename__ = "reorder_rules"

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

    # Reorder thresholds
    min_threshold = Column(
        Numeric(10, 2),
        nullable=False,
        default=5,
    )  # Trigger reorder when below this
    target_stock = Column(
        Numeric(10, 2),
        nullable=False,
        default=50,
    )  # Target stock level after reorder

    # Velocity-based settings
    velocity_days = Column(
        Numeric(5, 2),
        default=30,
    )  # Days to consider for velocity calculation
    velocity_multiplier = Column(
        Numeric(5, 2),
        default=1.0,
    )  # Multiplier for fast/slow movers (0.5-2.0)

    # Supplier info (extensible for vendor management)
    preferred_supplier = Column(String(255), nullable=True)
    supplier_lead_time_days = Column(Numeric(5, 2), default=7)

    # Rule status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="reorder_rules")

    @property
    def reorder_quantity(self, current_stock: float, daily_velocity: float) -> float:
        """
        Calculate recommended reorder quantity.

        Args:
            current_stock: Current inventory level
            daily_velocity: Average daily sales

        Returns:
            Recommended quantity to reorder
        """
        if current_stock >= self.min_threshold:
            return 0

        # Base reorder: bring to target level
        base_quantity = float(self.target_stock) - current_stock

        # Adjust for velocity
        velocity_adjustment = daily_velocity * float(self.velocity_multiplier)

        return max(0, base_quantity + velocity_adjustment)

    def __repr__(self):
        return f"<ReorderRule {self.product_id}: threshold={self.min_threshold}>"
