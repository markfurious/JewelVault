"""
Reorder schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ReorderRuleCreate(BaseModel):
    """Schema for creating a reorder rule."""

    product_id: UUID
    min_threshold: float = Field(5, ge=0, description="Minimum stock threshold")
    target_stock: float = Field(50, ge=0, description="Target stock level")
    velocity_days: float = Field(30, ge=1, description="Days for velocity calculation")
    velocity_multiplier: float = Field(
        1.0, ge=0.1, le=3.0, description="Velocity adjustment multiplier"
    )
    preferred_supplier: Optional[str] = Field(None, max_length=255)
    supplier_lead_time_days: float = Field(7, ge=0)


class ReorderRuleResponse(BaseModel):
    """Schema for reorder rule responses."""

    id: UUID
    product_id: UUID
    min_threshold: float
    target_stock: float
    velocity_days: float
    velocity_multiplier: float
    preferred_supplier: Optional[str] = None
    supplier_lead_time_days: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderSuggestion(BaseModel):
    """Schema for reorder suggestions from analytics."""

    product_id: UUID
    product_name: str
    product_sku: str
    current_stock: float
    min_threshold: float
    target_stock: float
    sales_velocity: float  # Units per day
    velocity_period_days: int
    is_urgent: bool  # Stock below threshold
    is_fast_moving: bool  # High velocity product
    recommended_reorder_quantity: float
    estimated_days_until_stockout: Optional[int] = None

    class Config:
        from_attributes = True


class ReorderSuggestionList(BaseModel):
    """Schema for list of reorder suggestions."""

    items: list[ReorderSuggestion]
    total_count: int
    urgent_count: int
    fast_moving_count: int
    generated_at: datetime
