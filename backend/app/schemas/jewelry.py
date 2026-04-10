"""
Jewelry schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class JewelryType(str, Enum):
    """Jewelry types for AR try-on."""
    EARRING = "earring"
    RING = "ring"
    NECKLACE = "necklace"


from pydantic import BaseModel, Field, field_validator
import re


class JewelryBase(BaseModel):
    """Base jewelry schema."""
    model_config = {"protected_namespaces": ()}

    sku: str = Field(..., min_length=1, max_length=100)  # Mandatory SKU starting with SI
    name: str = Field(..., min_length=1, max_length=255)
    type: JewelryType
    description: str = Field(..., min_length=1, max_length=1000)  # Made mandatory
    price: float = Field(0, ge=0)
    feature: Optional[str] = Field(None, max_length=100)  # Special feature tag
    is_active: bool = True

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v):
        if not v.upper().startswith('SI'):
            raise ValueError('SKU must start with "SI" (e.g., SI-001, SI001)')
        return v.upper()


class JewelryCreate(JewelryBase):
    """Schema for creating jewelry."""
    model_url: str = Field(..., min_length=1, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    image_link: Optional[str] = Field(None, max_length=500)  # Image link for Excel import


class JewelryUpdate(BaseModel):
    """Schema for updating jewelry."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    model_url: Optional[str] = Field(None, min_length=1, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, ge=0)
    feature: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class JewelryResponse(JewelryBase):
    """Schema for jewelry responses."""
    id: UUID
    model_url: str
    thumbnail_url: Optional[str] = None
    image_link: Optional[str] = None  # Original S3/HTTP image link
    feature: Optional[str] = None  # Special feature tag
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JewelryListResponse(BaseModel):
    """Schema for paginated jewelry list."""
    items: List[JewelryResponse]
    total: int
    page: int = 1
    page_size: int = 20


class TryOnLogCreate(BaseModel):
    """Schema for logging try-on events."""
    product_id: UUID
    session_id: Optional[str] = None
    user_id: Optional[UUID] = None
    screenshot_url: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=0)


class TryOnLogResponse(BaseModel):
    """Schema for try-on log responses."""
    id: UUID
    product_id: UUID
    session_id: Optional[str] = None
    user_id: Optional[UUID] = None
    screenshot_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    timestamp: datetime
    jewelry: Optional[JewelryResponse] = None

    class Config:
        from_attributes = True


class TryOnLogListResponse(BaseModel):
    """Schema for paginated try-on logs."""
    items: List[TryOnLogResponse]
    total: int
    page: int = 1
    page_size: int = 20
