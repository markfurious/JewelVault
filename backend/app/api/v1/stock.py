"""
Stock API routes.
Combined endpoint for products with inventory data for grid display.
Item-based model: returns status instead of quantity.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db
from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.schemas.product import StockListResponse, BulkActionRequest, BulkActionResponse
from app.services.inventory_service import InventoryService
from app.utils.exceptions import ValidationError

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("", response_model=StockListResponse)
def get_stock_grid(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    gold_purity: Optional[str] = None,
    status: Optional[str] = Query(None, description="Filter by status: AVAILABLE, SOLD, RESERVED, RETURN_PENDING"),
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    Get stock grid data with products and inventory combined.

    Item-based model: each SKU represents ONE item tracked by status.

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records (max 100)
    - **search**: Search in SKU, name, category, style_number
    - **category**: Filter by category
    - **gold_purity**: Filter by gold purity (10K, 14K, 18K, etc.)
    - **status**: Filter by status (AVAILABLE, SOLD, RESERVED)
    - **available_only**: Show only AVAILABLE items
    """
    # Build base query with inventory join
    query = select(Product, Inventory.status.label('inventory_status'), Inventory.location).outerjoin(
        Inventory, Product.id == Inventory.product_id
    )

    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Product.sku.ilike(search_filter)) |
            (Product.name.ilike(search_filter)) |
            (Product.category.ilike(search_filter)) |
            (Product.style_number.ilike(search_filter))
        )

    if category:
        query = query.where(Product.category == category)

    if gold_purity:
        query = query.where(Product.gold_purity == gold_purity)

    if status:
        query = query.where(Inventory.status == status.upper())

    if available_only:
        query = query.where(Inventory.status == InventoryStatus.AVAILABLE)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Product.sku)

    results = db.execute(query).all()

    # Format response
    items = []
    for row in results:
        product = row[0]
        inv_status = row[1] if row[1] is not None else InventoryStatus.AVAILABLE
        location = row[2] if row[2] else None

        items.append({
            # Product fields
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "sub_category": product.sub_category,
            "style_number": product.style_number,
            "st_carat": float(product.st_carat) if product.st_carat else None,
            "product_weight": float(product.product_weight) if product.product_weight else None,
            "gold_purity": product.gold_purity,
            "certified": product.certified,
            "cost_price": float(product.cost_price) if product.cost_price else None,
            "wholesale_price": float(product.wholesale_price) if product.wholesale_price else None,
            "retail_price": float(product.retail_price) if product.retail_price else None,
            "online_price": float(product.online_price) if product.online_price else None,
            "is_active": product.is_active,
            # Inventory fields (item-based)
            "status": inv_status,
            "location": location,
        })

    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/summary")
def get_stock_summary(db: Session = Depends(get_db)):
    """Get stock summary statistics for dashboard (item-based model)."""

    # Total products
    total_products = db.query(func.count(Product.id)).scalar()

    # Products with inventory
    products_with_inv = db.query(Product).join(Inventory).count()

    # Status breakdown
    available_count = db.query(func.count(Product.id)).join(Inventory).where(
        Inventory.status == InventoryStatus.AVAILABLE
    ).scalar()

    sold_count = db.query(func.count(Product.id)).join(Inventory).where(
        Inventory.status == InventoryStatus.SOLD
    ).scalar()

    reserved_count = db.query(func.count(Product.id)).join(Inventory).where(
        Inventory.status == InventoryStatus.RESERVED
    ).scalar()

    # Total inventory value (available items only)
    total_value = db.query(
        func.sum(Product.cost_price)
    ).join(Inventory).where(
        Inventory.status == InventoryStatus.AVAILABLE
    ).scalar() or 0

    # Category breakdown
    category_stats = db.query(
        Product.category,
        func.count(Product.id).label('count'),
    ).join(Inventory).group_by(Product.category).all()

    categories = [
        {
            "name": cat.category or "Uncategorized",
            "product_count": cat.count,
        }
        for cat in category_stats
    ]

    # Gold purity breakdown
    purity_stats = db.query(
        Product.gold_purity,
        func.count(Product.id).label('count'),
    ).join(Inventory).group_by(Product.gold_purity).all()

    purities = [
        {
            "purity": stat.gold_purity or "Unknown",
            "product_count": stat.count,
        }
        for stat in purity_stats
    ]

    return {
        "total_products": total_products,
        "products_with_inventory": products_with_inv,
        "status_breakdown": {
            "available": available_count,
            "sold": sold_count,
            "reserved": reserved_count,
        },
        "total_inventory_value": float(total_value),
        "categories": categories,
        "gold_purities": purities,
    }


@router.get("/{product_id}")
def get_stock_item(product_id: str, db: Session = Depends(get_db)):
    """Get detailed stock information for a specific product."""
    from uuid import UUID

    try:
        product_id_uuid = UUID(product_id)
    except ValueError:
        # Try searching by SKU
        product = db.query(Product).filter(Product.sku == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        product_id_uuid = product.id
        product_id = product.sku

    product = db.query(Product).filter(Product.id == product_id_uuid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory = db.query(Inventory).filter(Inventory.product_id == product_id_uuid).first()

    return {
        "id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "sub_category": product.sub_category,
        "style_number": product.style_number,
        "st_carat": float(product.st_carat) if product.st_carat else None,
        "product_weight": float(product.product_weight) if product.product_weight else None,
        "gold_purity": product.gold_purity,
        "certified": product.certified,
        "cost_price": float(product.cost_price) if product.cost_price else None,
        "wholesale_price": float(product.wholesale_price) if product.wholesale_price else None,
        "retail_price": float(product.retail_price) if product.retail_price else None,
        "online_price": float(product.online_price) if product.online_price else None,
        "is_active": product.is_active,
        "inventory": {
            "status": inventory.status if inventory else InventoryStatus.AVAILABLE,
            "location": inventory.location if inventory else None,
        } if inventory else {"status": InventoryStatus.AVAILABLE, "location": None},
    }


@router.post("/action", response_model=BulkActionResponse)
def bulk_stock_action(
    request: BulkActionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute bulk action on selected stock items.

    **Actions:**
    - `mark_sold`: Set status to SOLD (only from AVAILABLE)
    - `mark_available`: Set status to AVAILABLE (from SOLD or RETURN_PENDING)
    - `mark_reserved`: Set status to RESERVED (only from AVAILABLE)

    **Request Body:**
    ```json
    {
        "action": "mark_sold",
        "ids": ["uuid1", "uuid2", "uuid3"],
        "notes": "Optional notes for transaction log"
    }
    ```

    **Safety:**
    - Atomic: all-or-nothing update
    - Validates ALL status transitions BEFORE any update
    - Uses SELECT ... FOR UPDATE to lock rows
    - Creates transaction logs with accurate status_before
    - Full rollback on any failure
    """
    # Validate action
    valid_actions = ["mark_sold", "mark_available", "mark_reserved"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
        )

    # Validate IDs (must be valid UUIDs)
    uuid_ids = []
    for id_str in request.ids:
        try:
            uuid_ids.append(UUID(id_str))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format: {id_str}"
            )

    if not uuid_ids:
        raise HTTPException(status_code=400, detail="No valid IDs provided")

    # Map action to status
    action_to_status = {
        "mark_sold": InventoryStatus.SOLD,
        "mark_available": InventoryStatus.AVAILABLE,
        "mark_reserved": InventoryStatus.RESERVED,
    }
    target_status = action_to_status[request.action]

    try:
        # Use service layer for atomic bulk update with proper validation
        service = InventoryService(db)
        updated_ids = service.bulk_update_status(
            product_ids=uuid_ids,
            target_status=target_status,
            notes=request.notes,
            performed_by="bulk_action",
        )

        db.commit()

        return BulkActionResponse(
            message=f"Successfully updated {len(updated_ids)} items to {target_status}",
            updated_count=len(updated_ids),
            action=request.action,
        )

    except ValidationError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
