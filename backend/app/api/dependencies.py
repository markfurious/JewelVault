"""
API dependencies.
Common dependencies used across routes.
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.db.base import get_db as db_session
from app.api.v1.auth import get_current_user, require_admin, require_super_admin


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request.
    """
    yield from db_session()


__all__ = ["get_db", "get_current_user", "require_admin", "require_super_admin"]
