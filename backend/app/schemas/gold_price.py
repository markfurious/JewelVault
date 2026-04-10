"""
Gold Price schemas.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class GoldPriceCreate(BaseModel):
    """Schema for recording a gold price."""
    price: float = Field(..., gt=0, description="Gold price per troy ounce")
    currency: Optional[str] = "USD"


class GoldPriceResponse(BaseModel):
    """Schema for gold price response."""
    current_price: float
    currency: str = "USD"
    unit: str = "troy_ounce"
    last_updated: datetime

    class Config:
        from_attributes = True
