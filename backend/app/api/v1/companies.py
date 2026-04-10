"""
Companies API routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db, require_admin, get_current_user, require_super_admin
from app.services.company_service import CompanyService
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
)
from app.models.user import User
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
def create_company(
    schema: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Create a new company (ADMIN ONLY).

    - **name**: Company name (required)
    - **code**: Short unique code (required)
    - **address**: Optional address
    - **phone**: Optional phone number
    - **email**: Optional email
    - **tax_id**: Optional tax ID
    - **currency**: Default currency (default: USD)
    - **timezone**: Default timezone (default: UTC)
    """
    service = CompanyService(db)
    try:
        return service.create(schema)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=CompanyListResponse)
def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    List all companies with pagination and filters (super_admin only).
    """
    service = CompanyService(db)
    companies, total = service.list_all(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )
    return CompanyListResponse(
        items=companies,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Get a specific company by ID (super_admin only)."""
    service = CompanyService(db)
    try:
        return service.get_by_id(company_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    schema: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update a company (super_admin only).
    """
    service = CompanyService(db)
    try:
        return service.update(company_id, schema)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Delete a company (super_admin only).
    """
    service = CompanyService(db)
    try:
        service.delete(company_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
