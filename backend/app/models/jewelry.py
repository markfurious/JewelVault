"""
Jewelry models for AR try-on feature.
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Jewelry(Base):
    """
    Jewelry product model for AR try-on.
    Stores 3D model references and product details.
    """

    __tablename__ = "jewelry"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    sku = Column(String(100), nullable=False, unique=True, index=True)  # SKU number
    name = Column(String(255), nullable=False, index=True)
    type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # earring, ring, necklace
    model_url = Column(String(500), nullable=False)  # Local path to 3D model
    thumbnail_url = Column(String(500), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    description = Column(String(1000), nullable=False)  # Made mandatory
    feature = Column(String(100), nullable=True)  # Special feature tag (e.g., bestseller, new_arrival)
    is_active = Column(String(20), default="true", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tryon_logs = relationship("TryOnLog", back_populates="jewelry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Jewelry {self.name} ({self.type})>"


class TryOnLog(Base):
    """
    Logs user try-on interactions for analytics.
    """

    __tablename__ = "tryon_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jewelry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(255), nullable=True, index=True)  # Browser session ID
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # If user is logged in
    screenshot_url = Column(String(500), nullable=True)  # Path to captured screenshot
    duration_seconds = Column(Integer, nullable=True)  # How long user tried on
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    jewelry = relationship("Jewelry", back_populates="tryon_logs")

    def __repr__(self):
        return f"<TryOnLog {self.id} - Product {self.product_id}>"
