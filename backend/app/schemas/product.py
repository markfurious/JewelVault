"""
Product schemas for request/response validation.
"""
import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# SKU validation pattern: SI followed by exactly 5 digits
SKU_PATTERN = re.compile(r'^SI\d{5}$')


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    sku: Optional[str] = Field(None, description="Stock Keeping Unit (auto-generated if not provided)")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    sub_category: Optional[str] = Field(None, max_length=100)

    # Jewelry-specific fields
    style_number: Optional[str] = Field(None, max_length=50)
    st_carat: Optional[float] = Field(None, ge=0, description="Stone carat weight")
    product_weight: Optional[float] = Field(None, ge=0, description="Product weight in grams")
    gold_purity: Optional[str] = Field(None, max_length=20, description="e.g., 14K, 18K, 22K, 24K")
    certified: Optional[bool] = Field(False, description="Whether product is certified")

    # Pricing
    cost_price: Optional[float] = Field(None, ge=0)
    wholesale_price: Optional[float] = Field(None, ge=0)
    retail_price: Optional[float] = Field(None, ge=0)
    online_price: Optional[float] = Field(None, ge=0)

    is_active: bool = True
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extensible attributes (cut, clarity, carat, etc.)",
    )
    default_reorder_threshold: float = Field(10, ge=0)

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        """Validate SKU format if provided."""
        if v is not None and not SKU_PATTERN.match(v):
            raise ValueError(
                f"Invalid SKU format: '{v}'. Must match pattern: ^SI\\d{{5}}$ (e.g., SI00001)"
            )
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    initial_quantity: float = Field(0, ge=0, description="Initial stock quantity")
    initial_location: Optional[str] = Field(None, description="Initial stock location")


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""

    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None

    # Jewelry-specific fields
    style_number: Optional[str] = None
    st_carat: Optional[float] = Field(None, ge=0)
    product_weight: Optional[float] = Field(None, ge=0)
    gold_purity: Optional[str] = None
    certified: Optional[bool] = None

    # Pricing
    cost_price: Optional[float] = Field(None, ge=0)
    wholesale_price: Optional[float] = Field(None, ge=0)
    retail_price: Optional[float] = Field(None, ge=0)
    online_price: Optional[float] = Field(None, ge=0)

    is_active: Optional[bool] = None
    attributes: Optional[Dict[str, Any]] = None
    default_reorder_threshold: Optional[float] = Field(None, ge=0)

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        """Validate SKU format if provided."""
        if v is not None and not SKU_PATTERN.match(v):
            raise ValueError(
                f"Invalid SKU format: '{v}'. Must match pattern: ^SI\\d{{5}}$ (e.g., SI00001)"
            )
        return v


class ProductResponse(ProductBase):
    """Schema for product responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response."""

    items: list[ProductResponse]
    total: int
    page: int = 1
    page_size: int = 20


class BulkUploadError(BaseModel):
    """Schema for bulk upload error."""

    row: int
    column: str
    error: str


class BulkUploadResponse(BaseModel):
    """Schema for successful bulk upload response."""

    message: str
    records_created: int


class BulkUploadErrorResponse(BaseModel):
    """Schema for failed bulk upload response."""

    errors: list[BulkUploadError]


class BulkProductRow(BaseModel):
    """Schema for a single row in bulk upload."""

    SKU: str
    Category: Optional[str] = None
    Sub_Category: Optional[str] = None
    Style_Number: Optional[str] = None
    ST_Carat: Optional[float] = None
    Product_wt: Optional[float] = None
    Gold_Purity: Optional[str] = None
    Certified: Optional[bool] = False
    Wholesale_Price: Optional[float] = None
    Retail_Price: Optional[float] = None
    Online_Price: Optional[float] = None

    @field_validator('SKU')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU format."""
        if not SKU_PATTERN.match(v):
            raise ValueError(f"Invalid SKU format: '{v}'. Must match pattern: ^SI\\d{{5}}$")
        return v


class StockItemResponse(BaseModel):
    """Schema for stock grid item response (item-based model)."""

    id: str
    sku: str
    name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    style_number: Optional[str] = None
    st_carat: Optional[float] = None
    product_weight: Optional[float] = None
    gold_purity: Optional[str] = None
    certified: Optional[bool] = False
    cost_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    retail_price: Optional[float] = None
    online_price: Optional[float] = None
    is_active: bool = True
    status: str = "AVAILABLE"  # Item-based: AVAILABLE, SOLD, RESERVED
    location: Optional[str] = None


class StockListResponse(BaseModel):
    """Schema for paginated stock list response."""

    items: list[StockItemResponse]
    total: int
    page: int = 1
    page_size: int = 100


class BulkActionRequest(BaseModel):
    """Schema for bulk action requests on selected rows."""

    action: str  # "mark_sold", "mark_available", "mark_reserved"
    ids: list[str]  # List of product IDs (UUIDs as strings)
    notes: str = ""  # Optional notes for the transaction


class BulkActionResponse(BaseModel):
    """Schema for bulk action response."""

    message: str
    updated_count: int
    action: str
