"""
Inventory schemas for request/response validation.
Item-based model - each SKU represents ONE item tracked by status.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class InventoryStatusEnum(str, Enum):
    """Enumeration of inventory status values."""
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    RESERVED = "RESERVED"
    RETURN_PENDING = "RETURN_PENDING"


class InventoryResponse(BaseModel):
    """Schema for inventory responses."""

    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    status: str
    location: Optional[str] = None
    warehouse_code: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    """Schema for manual inventory status update."""

    status: InventoryStatusEnum = Field(..., description="New status: AVAILABLE, SOLD, or RESERVED")
    location: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)


class InventoryAdjustment(BaseModel):
    """Schema for status adjustment."""

    status: InventoryStatusEnum = Field(
        ..., description="New status to set"
    )
    transaction_type: str = Field(
        ..., description="RESTOCK, ADJUSTMENT, RETURN, RESERVE, RELEASE, etc."
    )
    notes: Optional[str] = Field(None, max_length=500)


class InventoryTransactionResponse(BaseModel):
    """Schema for inventory transaction history."""

    id: UUID
    inventory_id: UUID
    transaction_type: str
    status_before: str
    status_after: str
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryListResponse(BaseModel):
    """Paginated response for inventory list."""

    items: list[InventoryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
