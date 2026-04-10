"""
User model.
Handles user authentication and role-based access control.
"""
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for authentication and authorization.

    Roles:
    - admin: Full access to all features including user management
    - user: Standard access to inventory, products, sales
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # User profile
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Company relationship
    company_id = Column(
        UUID(as_uuid=True),
        sa.ForeignKey('companies.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    # Role-based access
    role = Column(
        String(20),
        nullable=False,
        default="company_user",
    )  # super_admin, company_admin, company_user

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="users")

    @property
    def is_super_admin(self) -> bool:
        """Check if user has super admin role (access to all companies)."""
        return self.role == "super_admin"

    @property
    def is_company_admin(self) -> bool:
        """Check if user is company admin (admin within their company)."""
        return self.role == "company_admin"

    @property
    def is_admin(self) -> bool:
        """Check if user has any admin role."""
        return self.is_super_admin or self.is_company_admin

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
