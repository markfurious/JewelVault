"""
Analytics API routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.api.dependencies import get_db
from app.services.analytics_service import AnalyticsService
from app.services.ai_query_service import AIQueryService
from app.schemas.reorder import ReorderSuggestionList
from app.schemas.analytics import (
    AIQueryRequest,
    AIQueryResponse,
    InventorySummary,
)
from app.utils.exceptions import AppException

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/reorder-suggestions", response_model=ReorderSuggestionList)
def get_reorder_suggestions(
    include_fast_moving: bool = True,
    velocity_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get smart reorder suggestions based on stock levels and sales velocity.

    Returns products that:
    - Are below their minimum threshold (urgent)
    - Are fast-moving and may need proactive reordering

    The algorithm considers:
    - Current stock vs threshold
    - Sales velocity (units/day over the specified period)
    - Supplier lead time
    - Safety stock buffer

    - **include_fast_moving**: Include fast-moving products even if above threshold
    - **velocity_days**: Number of days to consider for velocity calculation
    """
    analytics_service = AnalyticsService(db)
    suggestions = analytics_service.get_reorder_suggestions(
        include_fast_moving=include_fast_moving,
        velocity_days=velocity_days,
    )

    urgent_count = sum(1 for s in suggestions if s.is_urgent)
    fast_moving_count = sum(1 for s in suggestions if s.is_fast_moving)

    return ReorderSuggestionList(
        items=suggestions,
        total_count=len(suggestions),
        urgent_count=urgent_count,
        fast_moving_count=fast_moving_count,
        generated_at=datetime.utcnow(),
    )


@router.get("/sales-velocity", response_model=List[dict])
def get_sales_velocity(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get sales velocity report for top products.

    Shows products ranked by units sold, with trend analysis.

    - **days**: Number of days for the report
    - **limit**: Maximum number of products to return
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_sales_velocity_report(days=days, limit=limit)


@router.get("/inventory/summary", response_model=InventorySummary)
def get_inventory_summary(
    db: Session = Depends(get_db),
):
    """
    Get overall inventory summary.

    Returns:
    - Total products count
    - Total stock value
    - Low stock count (below threshold)
    - Out of stock count
    - Overstock count (above target by 50%)
    """
    analytics_service = AnalyticsService(db)
    summary = analytics_service.get_inventory_summary()
    return InventorySummary(**summary)


@router.get("/top-products", response_model=List[dict])
def get_top_selling_products(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get top selling products by quantity and revenue.

    - **days**: Number of days for the report
    - **limit**: Maximum number of products to return
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_top_selling_products(days=days, limit=limit)


@router.post("/query", response_model=AIQueryResponse)
def natural_language_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Query the database using natural language.

    This endpoint accepts natural language queries and converts them
    to structured query format. Currently uses rule-based parsing,
    designed for future LLM integration.

    Examples:
    - "Show top 10 selling products"
    - "List products with low stock"
    - "Get sales from last 30 days"
    - "Show inventory value by category"

    - **query**: Natural language query string
    - **context**: Optional additional context
    """
    ai_service = AIQueryService()
    response = ai_service.parse_query(
        query=request.query,
        context=request.context,
    )
    return response


@router.post("/query/execute", response_model=dict)
def execute_natural_language_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a natural language query and return results.

    Note: Currently returns mock execution results.
    Future implementation will execute against the database.

    - **query**: Natural language query string
    - **context**: Optional additional context
    """
    ai_service = AIQueryService()
    structured = ai_service.parse_query(query=request.query)
    result = ai_service.execute_query(structured.structured_query)
    return result
