"""
Authentication schemas.
Pydantic models for JWT tokens and user authentication.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class TokenPayload(BaseModel):
    """JWT token payload."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None  # "access" or "refresh"
    exp: Optional[int] = None


class CompanyInfo(BaseModel):
    """Minimal company info for user response."""
    id: UUID
    name: str
    code: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model."""
    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_locked: bool
    last_login: Optional[datetime] = None
    company_id: Optional[UUID] = None
    company: Optional[CompanyInfo] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response for login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    """Login request payload."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""
    refresh_token: str


class UserCreate(BaseModel):
    """User creation request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: str = "company_user"  # Default to company_user
    company_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    """User update request."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    company_id: Optional[UUID] = None


class UserChangePassword(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=6)
