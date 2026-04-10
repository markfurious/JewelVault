"""
Sales API routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.api.dependencies import get_db
from app.api.v1.auth import get_current_user, require_admin
from app.services.sale_service import SaleService
from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleListResponse,
    SaleReturnRequest,
    SaleReturnResponse,
    SaleReturnApprove,
    SaleReturnReject,
)
from app.models.user import User
from app.utils.exceptions import AppException, NotFoundError, InsufficientStockError, ValidationError

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    schema: SaleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new sale.

    This will:
    1. Validate all products exist
    2. Check stock availability
    3. Calculate totals (subtotal, tax, discount)
    4. Reduce inventory automatically
    5. Generate a unique sale number

    - **items**: List of products with quantities (required)
    - **customer_name**: Optional customer name
    - **sale_type**: RETAIL, WHOLESALE, or ONLINE
    - **tax_rate**: Tax percentage (0-100)
    - **discount_amount**: Fixed discount amount
    - **payment_method**: CASH, CARD, TRANSFER, or CHECK
    """
    service = SaleService(db)
    try:
        sale = service.create(schema)
        return sale
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=SaleListResponse)
def list_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sale_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """
    List all sales with pagination and filters.
    """
    service = SaleService(db)
    sales, total = service.list_all(
        skip=skip,
        limit=limit,
        sale_type=sale_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return SaleListResponse(
        items=sales,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


# ============ Sale Return Endpoints (Must be before /{sale_id} routes) ============

@router.get("/returns", response_model=List[SaleReturnResponse])
def list_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
    sale_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """List sale returns with pagination and filters."""
    service = SaleService(db)
    returns, total = service.list_returns(
        skip=skip,
        limit=limit,
        status=status,
        sale_id=sale_id,
    )
    return returns


@router.get("/returns/{return_id}", response_model=SaleReturnResponse)
def get_return(
    return_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific return request by ID."""
    service = SaleService(db)
    try:
        return service.get_return_by_id(return_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/returns/{return_id}/approve", response_model=SaleReturnResponse)
def approve_return(
    return_id: UUID,
    request_data: SaleReturnApprove = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Approve a return request (ADMIN ONLY)."""
    service = SaleService(db)
    try:
        override_amount = request_data.refund_amount if request_data else None
        return_record = service.approve_return(
            return_id=return_id,
            approved_by=current_user.username,
            override_refund_amount=override_amount,
        )
        return return_record
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/returns/{return_id}/reject", response_model=SaleReturnResponse)
def reject_return(
    return_id: UUID,
    request_data: SaleReturnReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reject a return request (ADMIN ONLY)."""
    service = SaleService(db)
    try:
        return_record = service.reject_return(
            return_id=return_id,
            reason=request_data.reason,
            rejected_by=current_user.username,
        )
        return return_record
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sale_id}/return", response_model=SaleReturnResponse)
def request_return(
    sale_id: UUID,
    request_data: SaleReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request a return for a completed sale."""
    service = SaleService(db)
    try:
        return_record = service.request_return(
            sale_id=sale_id,
            product_ids=request_data.product_ids,
            reason=request_data.reason,
            requested_by=current_user.username,
            refund_amount=request_data.refund_amount,
        )
        return return_record
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
def cancel_sale(
    sale_id: UUID,
    db: Session = Depends(get_db),
):
    """Cancel a sale and restore inventory."""
    service = SaleService(db)
    try:
        return service.cancel_sale(sale_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific sale by ID."""
    service = SaleService(db)
    try:
        return service.get_by_id(sale_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
