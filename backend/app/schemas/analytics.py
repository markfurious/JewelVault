"""
Analytics schemas for AI query service and reports.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class QueryType(str, Enum):
    """Types of supported natural language queries."""

    LIST = "LIST"
    AGGREGATE = "AGGREGATE"
    TREND = "TREND"
    COMPARISON = "COMPARISON"
    FILTER = "FILTER"
    UNKNOWN = "UNKNOWN"


class AIQueryRequest(BaseModel):
    """Schema for AI query requests."""

    query: str = Field(..., description="Natural language query")
    context: Optional[str] = Field(None, description="Additional context")


class StructuredQuery(BaseModel):
    """Schema for parsed structured query."""

    query_type: QueryType
    target_entity: str  # products, sales, inventory
    filters: Optional[Dict[str, Any]] = None
    aggregations: Optional[List[str]] = None
    order_by: Optional[str] = None
    limit: Optional[int] = None
    time_range: Optional[Dict[str, Any]] = None
    raw_query: str


class AIQueryResponse(BaseModel):
    """Schema for AI query responses."""

    original_query: str
    structured_query: StructuredQuery
    explanation: str
    confidence: float = Field(ge=0, le=1)


class SalesVelocityReport(BaseModel):
    """Schema for sales velocity analytics."""

    product_id: UUID
    product_name: str
    product_sku: str
    total_sold: float
    period_days: int
    daily_velocity: float
    trend: str  # INCREASING, DECREASING, STABLE


class InventorySummary(BaseModel):
    """Schema for inventory summary."""

    total_products: int
    total_stock_value: float
    low_stock_count: int
    out_of_stock_count: int
    overstock_count: int
