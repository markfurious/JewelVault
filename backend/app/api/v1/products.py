"""
Product API routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db
from app.services.product_service import ProductService
from app.services.product_bulk_service import ProductBulkService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    BulkUploadResponse,
    BulkUploadErrorResponse,
    BulkUploadError,
)
from app.utils.exceptions import AppException, NotFoundError, DuplicateError

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    schema: ProductCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new product.

    - **sku**: Unique stock keeping unit (auto-generated if not provided, format: SI00001)
    - **name**: Product name (required)
    - **category**: Optional category for grouping
    - **sub_category**: Optional sub-category
    - **jewelry fields**: style_number, st_carat, product_weight, gold_purity, certified
    - **prices**: Cost, retail, wholesale, and online prices
    - **attributes**: JSON field for extensible properties (diamond attributes, etc.)
    - **initial_quantity**: Starting stock level
    """
    service = ProductService(db)
    try:
        product = service.create(schema)
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(
    file: UploadFile = File(..., description="Excel file (.xlsx) with product data"),
    initial_quantity: float = Form(0, description="Default initial stock quantity"),
    initial_location: Optional[str] = Form(None, description="Default initial stock location"),
    db: Session = Depends(get_db),
):
    """
    Bulk upload products from Excel file.

    **Required Excel Columns:**
    - SKU (format: SI00001)
    - Category
    - Sub Category
    - Style Number
    - ST Carat
    - Product wt
    - Gold Purity
    - Certified
    - Wholesale Price
    - Retail Price
    - Online Price

    **Validation Rules:**
    - All rows are validated before any insertion
    - If ANY row fails validation, entire file is rejected
    - SKU must match pattern ^SI\\d{5}$
    - SKU must be unique (not already in database)
    - Retail Price is required

    **Response:**
    - Success: `{ "message": "Bulk upload successful", "records_created": X }`
    - Failure: `{ "errors": [{ "row": N, "column": "X", "error": "..." }] }`
    """
    # Validate file type (.xlsx only, .xls not supported)
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx)"
        )

    # Read file bytes
    contents = await file.read()

    # Process upload
    service = ProductBulkService(db)
    success, result = service.process_upload(
        contents,
        initial_quantity=initial_quantity,
        initial_location=initial_location,
    )

    if success:
        return BulkUploadResponse(
            message="Bulk upload successful",
            records_created=result,
        )
    else:
        # Return validation errors
        raise HTTPException(
            status_code=400,
            detail=[
                {"row": int(err.row), "column": str(err.column), "error": str(err.error)}
                for err in result
            ],
        )


@router.get("", response_model=ProductListResponse)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    List all products with pagination and filters.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records (max 100)
    - **category**: Filter by category
    - **is_active**: Filter by active status
    """
    service = ProductService(db)
    products, total = service.list_all(
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active,
    )
    return ProductListResponse(
        items=products,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific product by ID."""
    service = ProductService(db)
    try:
        return service.get_by_id(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sku/{sku}", response_model=ProductResponse)
def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db),
):
    """Get a specific product by SKU."""
    service = ProductService(db)
    try:
        return service.get_by_sku(sku)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    schema: ProductUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a product.

    Only provided fields will be updated.
    """
    service = ProductService(db)
    try:
        return service.update(product_id, schema)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Soft delete a product (mark as inactive).

    The product will remain in the database but won't appear in active listings.
    """
    service = ProductService(db)
    try:
        service.delete(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
