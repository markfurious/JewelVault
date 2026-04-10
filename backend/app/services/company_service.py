"""
Company service.
Handles business logic for company management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.utils.exceptions import NotFoundError, ValidationError


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, schema: CompanyCreate) -> Company:
        """Create a new company."""
        # Check for duplicate code
        existing = self.db.query(Company).filter(
            Company.code == schema.code
        ).first()
        if existing:
            raise ValidationError(f"Company with code '{schema.code}' already exists")

        company = Company(**schema.model_dump())
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def get_by_id(self, company_id: UUID) -> Company:
        """Get company by ID."""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise NotFoundError(f"Company with ID {company_id} not found")
        return company

    def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Company], int]:
        """List companies with pagination and filters."""
        query = select(Company)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (Company.name.ilike(search_filter)) |
                (Company.code.ilike(search_filter))
            )

        if is_active is not None:
            query = query.where(Company.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Company.name)
        companies = self.db.execute(query).scalars().all()

        return list(companies), total

    def update(self, company_id: UUID, schema: CompanyUpdate) -> Company:
        """Update a company."""
        company = self.get_by_id(company_id)

        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        self.db.commit()
        self.db.refresh(company)
        return company

    def delete(self, company_id: UUID) -> None:
        """Delete a company."""
        company = self.get_by_id(company_id)
        self.db.delete(company)
        self.db.commit()
