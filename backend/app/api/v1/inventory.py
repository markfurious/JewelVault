"""
Inventory API routes.
Item-based model: tracks items by status (AVAILABLE, SOLD, RESERVED).
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db
from app.services.inventory_service import InventoryService
from app.schemas.inventory import (
    InventoryResponse,
    InventoryUpdate,
    InventoryAdjustment,
    InventoryTransactionResponse,
    InventoryListResponse,
)
from app.utils.exceptions import AppException, NotFoundError, ValidationError

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryListResponse)
def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: AVAILABLE, SOLD, RESERVED"),
    db: Session = Depends(get_db),
):
    """
    List all inventory items.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records (max 100)
    - **status**: Filter by status (AVAILABLE, SOLD, RESERVED)
    """
    service = InventoryService(db)
    inventories, total = service.get_all(
        skip=skip,
        limit=limit,
        status_filter=status,
    )

    # Build response with product info
    items = []
    for inv in inventories:
        items.append(
            InventoryResponse(
                id=inv.id,
                product_id=inv.product_id,
                product_name=inv.product.name,
                product_sku=inv.product.sku,
                status=inv.status,
                location=inv.location,
                warehouse_code=inv.warehouse_code,
                updated_at=inv.updated_at,
            )
        )

    page = skip // limit + 1 if limit > 0 else 1
    return InventoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        has_more=(skip + limit) < total,
    )


@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """Get inventory for a specific product."""
    service = InventoryService(db)
    try:
        inventory = service.get_by_product_id(product_id)
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{product_id}", response_model=InventoryResponse)
def update_inventory(
    product_id: UUID,
    schema: InventoryUpdate,
    db: Session = Depends(get_db),
):
    """
    Manually update inventory status.

    This sets the absolute status value.
    """
    service = InventoryService(db)
    try:
        inventory = service.update_status(
            product_id=product_id,
            new_status=schema.status.value if hasattr(schema.status, 'value') else schema.status,
            notes=schema.notes,
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/adjust", response_model=InventoryResponse)
def adjust_inventory(
    product_id: UUID,
    schema: InventoryAdjustment,
    db: Session = Depends(get_db),
):
    """
    Adjust inventory status.

    - **status**: New status to set (AVAILABLE, SOLD, RESERVED)
    - **transaction_type**: Type of adjustment (RESTOCK, ADJUSTMENT, RETURN, RESERVE, RELEASE)
    - **notes**: Optional notes for the adjustment
    """
    service = InventoryService(db)
    try:
        inventory = service.adjust_status(
            product_id=product_id,
            adjustment=schema,
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/restock", response_model=InventoryResponse)
def restock_inventory(
    product_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Restock inventory (mark as AVAILABLE).

    Marks the item as AVAILABLE for sale.
    """
    service = InventoryService(db)
    try:
        inventory = service.mark_available(
            product_id=product_id,
            notes=notes,
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{product_id}/reserve", response_model=InventoryResponse)
def reserve_inventory(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Reserve inventory for an order.

    Marks the item as RESERVED (not available for sale).
    """
    service = InventoryService(db)
    try:
        inventory = service.reserve(
            product_id=product_id,
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/release", response_model=InventoryResponse)
def release_inventory(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Release reserved inventory back to available.

    Marks the item as AVAILABLE again.
    """
    service = InventoryService(db)
    try:
        inventory = service.release_reservation(
            product_id=product_id,
        )
        return InventoryResponse(
            id=inventory.id,
            product_id=inventory.product_id,
            product_name=inventory.product.name,
            product_sku=inventory.product.sku,
            status=inventory.status,
            location=inventory.location,
            warehouse_code=inventory.warehouse_code,
            updated_at=inventory.updated_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{product_id}/transactions", response_model=List[InventoryTransactionResponse])
def get_transaction_history(
    product_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get transaction history for a product."""
    service = InventoryService(db)
    try:
        transactions = service.get_transaction_history(
            product_id=product_id,
            skip=skip,
            limit=limit,
        )
        return transactions
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
