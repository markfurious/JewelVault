"""
Jewelry service for AR try-on feature.
Handles business logic for jewelry products and try-on analytics.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from app.models.jewelry import Jewelry, TryOnLog
from app.schemas.jewelry import JewelryCreate, JewelryUpdate, TryOnLogCreate
from app.utils.exceptions import NotFoundError, ValidationError


class JewelryService:
    """Service for jewelry operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        jewelry_type: Optional[str] = None,
        is_active: bool = True,
    ) -> Tuple[List[Jewelry], int]:
        """
        Get all jewelry items with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            jewelry_type: Filter by type (earring, ring, necklace)
            is_active: Filter by active status

        Returns:
            Tuple of (jewelry list, total count)
        """
        query = self.db.query(Jewelry)

        if jewelry_type:
            query = query.filter(Jewelry.type == jewelry_type.lower())

        if is_active:
            query = query.filter(Jewelry.is_active == "true")

        # Get total count
        total = query.count()

        # Get paginated results
        items = query.order_by(Jewelry.created_at.desc()).offset(skip).limit(limit).all()

        return items, total

    def get_by_id(self, jewelry_id: UUID) -> Jewelry:
        """
        Get jewelry by ID.

        Args:
            jewelry_id: UUID of the jewelry

        Returns:
            Jewelry instance

        Raises:
            NotFoundError: If jewelry not found
        """
        jewelry = self.db.query(Jewelry).filter(Jewelry.id == jewelry_id).first()
        if not jewelry:
            raise NotFoundError(f"Jewelry with ID {jewelry_id} not found")
        return jewelry

    def create(self, schema: JewelryCreate) -> Jewelry:
        """
        Create new jewelry item.

        Args:
            schema: JewelryCreate schema

        Returns:
            Created Jewelry instance
        """
        jewelry = Jewelry(
            sku=schema.sku,
            name=schema.name,
            type=schema.type.value,
            model_url=schema.model_url,
            thumbnail_url=schema.thumbnail_url,
            description=schema.description,
            price=schema.price,
            is_active="true" if schema.is_active else "false",
        )

        self.db.add(jewelry)
        self.db.commit()
        self.db.refresh(jewelry)

        return jewelry

    def update(self, jewelry_id: UUID, schema: JewelryUpdate) -> Jewelry:
        """
        Update jewelry item.

        Args:
            jewelry_id: UUID of the jewelry
            schema: JewelryUpdate schema

        Returns:
            Updated Jewelry instance

        Raises:
            NotFoundError: If jewelry not found
        """
        jewelry = self.get_by_id(jewelry_id)

        update_data = schema.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "is_active":
                setattr(jewelry, field, "true" if value else "false")
            else:
                setattr(jewelry, field, value)

        self.db.commit()
        self.db.refresh(jewelry)

        return jewelry

    def delete(self, jewelry_id: UUID) -> None:
        """
        Delete jewelry item.

        Args:
            jewelry_id: UUID of the jewelry

        Raises:
            NotFoundError: If jewelry not found
        """
        jewelry = self.get_by_id(jewelry_id)
        self.db.delete(jewelry)
        self.db.commit()

    def log_tryon(self, schema: TryOnLogCreate) -> TryOnLog:
        """
        Log a try-on event.

        Args:
            schema: TryOnLogCreate schema

        Returns:
            Created TryOnLog instance

        Raises:
            NotFoundError: If jewelry not found
        """
        # Validate jewelry exists
        jewelry = self.get_by_id(schema.product_id)

        tryon_log = TryOnLog(
            product_id=schema.product_id,
            session_id=schema.session_id,
            user_id=schema.user_id,
            screenshot_url=schema.screenshot_url,
            duration_seconds=schema.duration_seconds,
        )

        self.db.add(tryon_log)
        self.db.commit()
        self.db.refresh(tryon_log)

        return tryon_log

    def get_tryon_logs(
        self,
        skip: int = 0,
        limit: int = 20,
        product_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[List[TryOnLog], int]:
        """
        Get try-on logs with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            product_id: Filter by product ID
            session_id: Filter by session ID

        Returns:
            Tuple of (logs list, total count)
        """
        query = self.db.query(TryOnLog)

        if product_id:
            query = query.filter(TryOnLog.product_id == product_id)

        if session_id:
            query = query.filter(TryOnLog.session_id == session_id)

        total = query.count()
        logs = query.order_by(TryOnLog.timestamp.desc()).offset(skip).limit(limit).all()

        return logs, total

    def get_tryon_stats(self, product_id: Optional[UUID] = None) -> dict:
        """
        Get try-on analytics.

        Args:
            product_id: Optional product ID to filter stats

        Returns:
            Dictionary with analytics data
        """
        query = self.db.query(TryOnLog)

        if product_id:
            query = query.filter(TryOnLog.product_id == product_id)

        # Total try-ons
        total_tryons = query.count()

        # Unique users
        unique_users = query.distinct(TryOnLog.user_id).count()

        # Unique sessions
        unique_sessions = query.distinct(TryOnLog.session_id).count()

        # Average duration
        avg_duration = self.db.query(func.avg(TryOnLog.duration_seconds)).filter(
            TryOnLog.duration_seconds.isnot(None)
        ).scalar() or 0

        # Try-ons by type
        type_stats = self.db.query(
            Jewelry.type,
            func.count(TryOnLog.id).label('count')
        ).join(
            Jewelry, TryOnLog.product_id == Jewelry.id
        ).group_by(Jewelry.type).all()

        return {
            "total_tryons": total_tryons,
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "average_duration_seconds": round(float(avg_duration), 2),
            "by_type": {stat.type: stat.count for stat in type_stats},
        }
