"""
Metal Price models for tracking gold, silver, platinum prices.
Used for automatic jewelry price updates based on market rates.
"""
from sqlalchemy import Column, String, Numeric, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class MetalPrice(Base):
    """
    Metal price history model.
    Stores daily (or more frequent) price updates for precious metals.
    """

    __tablename__ = "metal_prices"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    metal_type = Column(String(50), nullable=False, index=True)  # gold, silver, platinum
    price_per_gram = Column(Numeric(12, 4), nullable=False)  # Price per gram in base currency
    currency = Column(String(3), default='USD', nullable=False)  # USD, EUR, etc.
    unit = Column(String(20), default='gram')  # gram, ounce, tola
    source = Column(String(100), nullable=True)  # API source name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<MetalPrice {self.metal_type}: {self.price_per_gram} {self.currency}/{self.unit}>"


class JewelryPriceLog(Base):
    """
    Log of automatic jewelry price updates.
    Tracks when and why prices were changed.
    """

    __tablename__ = "jewelry_price_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    jewelry_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    old_price = Column(Numeric(12, 2), nullable=False)
    new_price = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=True)  # e.g., "Gold price increased by 2.5%"
    metal_type = Column(String(50), nullable=True)  # Which metal triggered the update
    metal_price_change = Column(Numeric(8, 4), nullable=True)  # Percentage change in metal price
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<JewelryPriceLog {self.jewelry_id}: {self.old_price} -> {self.new_price}>"
