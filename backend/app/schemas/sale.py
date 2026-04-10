"""
Sale schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class SaleType(str, Enum):
    """Enumeration of sale types."""

    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    ONLINE = "ONLINE"


class PaymentMethod(str, Enum):
    """Enumeration of payment methods."""

    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    CHECK = "CHECK"


class SaleItemCreate(BaseModel):
    """Schema for creating a sale line item.

    In item-based model, quantity is always 1 (each SKU = one item).
    """

    product_id: UUID
    quantity: float = Field(1, gt=0, description="Quantity (always 1 in item-based model)")


class SaleItemResponse(BaseModel):
    """Schema for sale item responses."""

    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    quantity: float
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class SaleCreate(BaseModel):
    """Schema for creating a new sale."""

    items: List[SaleItemCreate] = Field(..., min_length=1)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_email: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=50)
    sale_type: SaleType = SaleType.RETAIL
    tax_rate: float = Field(0, ge=0, le=100, description="Tax percentage")
    discount_amount: float = Field(0, ge=0, description="Discount in currency units")
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class SaleResponse(BaseModel):
    """Schema for sale responses."""

    id: UUID
    sale_number: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    sale_type: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    payment_method: Optional[str] = None
    payment_status: str
    status: str
    sale_date: datetime
    items: List[SaleItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    """Schema for paginated sale list response."""

    items: List[SaleResponse]
    total: int
    page: int = 1
    page_size: int = 20


class SaleReturnRequest(BaseModel):
    """Schema for requesting a sale return."""

    product_ids: List[UUID] = Field(..., min_length=1, description="Products to return")
    reason: str = Field(..., min_length=1, max_length=500, description="Return reason")
    refund_amount: Optional[float] = Field(None, ge=0, description="Refund amount (full if not specified)")


class SaleReturnResponse(BaseModel):
    """Schema for sale return response."""

    id: UUID
    sale_id: UUID
    status: str  # PENDING, APPROVED, REJECTED
    reason: str
    refund_amount: float
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    # Product SKUs being returned (comma-separated)
    product_skus: Optional[str] = None

    class Config:
        from_attributes = True


class SaleReturnApprove(BaseModel):
    """Schema for approving a return."""

    refund_amount: Optional[float] = Field(None, ge=0, description="Override refund amount")


class SaleReturnReject(BaseModel):
    """Schema for rejecting a return."""

    reason: str = Field(..., min_length=1, max_length=500, description="Rejection reason")
