"""
Company model.
Handles multi-company support for the inventory system.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class Company(Base):
    """
    Company model for multi-tenant support.

    Each user belongs to one company, and data is scoped by company.
    """

    __tablename__ = "companies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # Short code for internal use

    # Company details
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    tax_id = Column(String(100), nullable=True)

    # Settings
    currency = Column(String(10), default="USD", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="company", lazy="dynamic")

    def __repr__(self):
        return f"<Company {self.name} ({self.code})>"
