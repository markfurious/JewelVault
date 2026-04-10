"""
Jewelry API routes for AR try-on feature.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import os
import uuid as uuid_lib
import tempfile
import shutil
import pandas as pd

from app.api.dependencies import get_db
from app.services.jewelry_service import JewelryService
from app.services.model_generator import generate_3d_for_all_jewelry, get_generator, process_excel_and_generate_3d
from app.schemas.jewelry import (
    JewelryCreate,
    JewelryUpdate,
    JewelryResponse,
    JewelryListResponse,
    TryOnLogCreate,
    TryOnLogResponse,
    TryOnLogListResponse,
)
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/jewelry", tags=["jewelry"])

# Directory for storing 3D models and screenshots
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "public", "models")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "public", "tryon-screenshots")

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


@router.get("", response_model=JewelryListResponse)
def list_jewelry(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="Filter by type: earring, ring, necklace"),
    db: Session = Depends(get_db),
):
    """
    List all jewelry items for AR try-on.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records (max 100)
    - **type**: Filter by jewelry type
    """
    service = JewelryService(db)
    items, total = service.get_all(
        skip=skip,
        limit=limit,
        jewelry_type=type,
    )

    return JewelryListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/generate-3d-batch")
def generate_3d_batch(
    db: Session = Depends(get_db),
):
    """
    Generate 3D models for all jewelry items that have thumbnails but no 3D models.

    Uses TripoSR (self-hosted) to convert product photos to 3D models.
    This is a batch operation - processes all pending items in queue.

    Note: Requires TripoSR installed at /opt/TripoSR or TRIPOR_PATH env var.
    GPU recommended (8GB+ VRAM). CPU fallback available but slower (5-10 min per model).

    Returns:
    - List of items processed with status (success/failed/no_image)
    - Summary counts
    """
    try:
        results = generate_3d_for_all_jewelry()

        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = sum(1 for r in results if r.get('status') == 'failed')
        no_image_count = sum(1 for r in results if r.get('status') == 'no_image')

        return {
            "status": "completed",
            "total_processed": len(results),
            "success": success_count,
            "failed": failed_count,
            "no_image": no_image_count,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@router.get("/check-3d-generator")
def check_3d_generator():
    """
    Check if TripoSR is installed and available.

    Returns installation status and recommended settings.
    """
    generator = get_generator()

    # Check if it's TripoSR or fallback
    is_tripo_sr = generator.__class__.__name__ == "TripoSRGenerator"
    tripors_installed = is_tripo_sr and generator.check_installation()

    return {
        "tripors_installed": tripors_installed,
        "tripors_path": generator.tripo_sr_path if is_tripo_sr else None,
        "using_fallback": not tripors_installed,
        "fallback_generator": "Simple3DGenerator (stable-fast-3d)" if not tripors_installed else None,
        "recommendation": "Install TripoSR for better quality models" if not tripors_installed else "TripoSR ready"
    }


@router.get("/download-template")
async def download_template():
    """
    Download Excel template for 3D model generation.

    Returns an Excel file with sample data and correct column format.
    """
    from io import BytesIO

    # Create template DataFrame
    sample_data = {
        'sku': ['SI-001', 'SI-002', 'SI-003', 'SI-004', 'SI-005'],
        'name': [
            'Diamond Stud Earrings',
            'Gold Hoop Earrings',
            'Pearl Drop Earrings',
            'Ruby Ring',
            'Silver Necklace'
        ],
        'type': ['earring', 'earring', 'earring', 'ring', 'necklace'],
        'image_url': [
            'https://your-s3-bucket.s3.amazonaws.com/products/earring1.jpg',
            'https://your-s3-bucket.s3.amazonaws.com/products/earring2.jpg',
            'https://your-s3-bucket.s3.amazonaws.com/products/earring3.jpg',
            'https://your-s3-bucket.s3.amazonaws.com/products/ring1.jpg',
            'https://your-s3-bucket.s3.amazonaws.com/products/necklace1.jpg'
        ],
        'price': [299.99, 199.99, 149.99, 599.99, 399.99],
        'description': [
            'Classic diamond stud earrings with brilliant cut stones',
            'Elegant gold hoop earrings perfect for daily wear',
            'Beautiful pearl drop earrings for special occasions',
            'Stunning ruby ring set in 18k gold',
            'Elegant silver necklace with delicate chain design'
        ]
    }

    df = pd.DataFrame(sample_data)

    # Write to BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')

    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=jewelry_3d_template.xlsx"}
    )


@router.post("/upload-excel-and-generate")
async def upload_excel_and_generate(
    file: UploadFile = File(..., description="Excel file with S3 URLs"),
    db: Session = Depends(get_db),
):
    """
    Upload Excel file with S3 URLs and generate 3D models.

    Excel file should have columns:
    - name: Jewelry name (required)
    - image_url: URL to product image - S3 or any HTTP URL (required)
    - type: Jewelry type - earring, ring, necklace (optional, default: earring)
    - price: Price (optional, default: 0)
    - description: Description (optional)

    The endpoint will:
    1. Download images from URLs
    2. Generate 3D models using TripoSR
    3. Create jewelry records in database
    4. Return results with status for each row

    Note: This is a synchronous operation. For large files, consider using
    a background task or queue system.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file extension
    allowed_extensions = [".xlsx", ".xls"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file to temp location
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process Excel and generate 3D models
        results = process_excel_and_generate_3d(temp_file_path)

        # Summary
        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = len(results) - success_count

        return {
            "status": "completed",
            "total_processed": len(results),
            "success": success_count,
            "failed": failed_count,
            "results": results
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up temp files
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@router.get("/{jewelry_id}", response_model=JewelryResponse)
def get_jewelry(
    jewelry_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a specific jewelry item by ID.
    """
    service = JewelryService(db)
    try:
        return service.get_by_id(jewelry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=JewelryResponse, status_code=201)
def create_jewelry(
    schema: JewelryCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new jewelry item.

    - **name**: Jewelry name (required)
    - **type**: earring, ring, or necklace (required)
    - **model_url**: Path to 3D model file (required)
    - **thumbnail_url**: Path to thumbnail image (optional)
    - **price**: Price in currency units
    - **description**: Optional description
    """
    service = JewelryService(db)
    try:
        return service.create(schema)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{jewelry_id}", response_model=JewelryResponse)
def update_jewelry(
    jewelry_id: UUID,
    schema: JewelryUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a jewelry item.
    """
    service = JewelryService(db)
    try:
        return service.update(jewelry_id, schema)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{jewelry_id}", status_code=204)
def delete_jewelry(
    jewelry_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a jewelry item.
    """
    service = JewelryService(db)
    try:
        service.delete(jewelry_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/upload-model")
async def upload_model(
    file: UploadFile = File(..., description="3D model file (.glb or .gltf)"),
    db: Session = Depends(get_db),
):
    """
    Upload a 3D model file for jewelry.

    Accepts .glb or .gltf files. Stores in public/models directory.
    Returns the URL path to access the model.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file extension
    allowed_extensions = [".glb", ".gltf"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique filename
    unique_id = uuid_lib.uuid4().hex
    new_filename = f"{unique_id}{file_ext}"
    file_path = os.path.join(MODELS_DIR, new_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Return URL path (relative to public folder)
    model_url = f"/models/{new_filename}"

    return {"model_url": model_url, "filename": new_filename, "size": len(content)}


@router.post("/tryon/log", response_model=TryOnLogResponse, status_code=201)
def log_tryon(
    schema: TryOnLogCreate,
    db: Session = Depends(get_db),
):
    """
    Log a try-on event for analytics.

    - **product_id**: UUID of the jewelry item (required)
    - **session_id**: Browser session identifier (optional)
    - **user_id**: User ID if logged in (optional)
    - **screenshot_url**: Path to captured screenshot (optional)
    - **duration_seconds**: How long user tried on (optional)
    """
    service = JewelryService(db)
    try:
        return service.log_tryon(schema)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tryon/logs", response_model=TryOnLogListResponse)
def get_tryon_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get try-on logs with pagination and filters.
    """
    service = JewelryService(db)
    items, total = service.get_tryon_logs(
        skip=skip,
        limit=limit,
        product_id=product_id,
        session_id=session_id,
    )

    return TryOnLogListResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/tryon/stats")
def get_tryon_stats(
    product_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """
    Get try-on analytics and statistics.

    Returns:
    - total_tryons: Total number of try-on events
    - unique_users: Number of unique users
    - unique_sessions: Number of unique sessions
    - average_duration_seconds: Average try-on duration
    - by_type: Breakdown by jewelry type
    """
    service = JewelryService(db)
    return service.get_tryon_stats(product_id=product_id)
