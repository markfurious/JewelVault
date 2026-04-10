"""
Reusable model mixins for common fields.
Provides timestamp tracking and soft delete capability.
"""
from datetime import datetime
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality (future use)."""

    deleted_at = Column(DateTime, nullable=True, index=True)
