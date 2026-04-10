"""
SKU Generation Utility.

Generates unique SKUs in format: SI00001, SI00002, SI00003...

Features:
- Auto-increment with zero-padding (5 digits)
- Duplicate detection via unique constraint
- Simple sequential generation
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.product import Product


# SKU format pattern: SI followed by exactly 5 digits
SKU_PATTERN = re.compile(r'^SI\d{5}$')
SKU_PREFIX = "SI"
SKU_DIGITS = 5


def validate_sku_format(sku: str) -> bool:
    """
    Validate SKU format matches ^SI\d{5}$

    Args:
        sku: SKU string to validate

    Returns:
        True if valid format, False otherwise
    """
    return bool(SKU_PATTERN.match(sku))


def generate_next_sku(db: Session) -> str:
    """
    Generate the next available SKU using retry on duplicate.

    Finds the maximum existing SKU and increments by 1.
    Uniqueness is enforced by the database unique constraint.
    If a duplicate occurs (race condition), the caller should retry.

    Args:
        db: SQLAlchemy database session

    Returns:
        Next available SKU in format SI00001, SI00002, etc.
    """
    result = db.execute(
        select(func.max(Product.sku))
    ).scalar()

    if result is None:
        # No products exist yet, start from 1
        next_number = 1
    else:
        # Extract numeric part from max SKU
        if result.startswith('SI') and len(result) == 7 and result[2:].isdigit():
            existing_number = int(result[2:])
            next_number = existing_number + 1
        else:
            # Invalid SKU exists, find the actual max valid SKU
            valid_max = db.execute(
                select(func.max(Product.sku)).where(Product.sku.regexp_match(r'^SI\d{5}$'))
            ).scalar()
            if valid_max:
                next_number = int(valid_max[2:]) + 1
            else:
                next_number = 1

    # Format with zero-padding to 5 digits
    return f"{SKU_PREFIX}{next_number:0{SKU_DIGITS}d}"


def check_sku_exists(db: Session, sku: str) -> bool:
    """
    Check if a SKU already exists in the database.

    Args:
        db: SQLAlchemy database session
        sku: SKU to check

    Returns:
        True if SKU exists, False otherwise
    """
    result = db.execute(
        select(Product.id).where(Product.sku == sku)
    ).scalar_one_or_none()
    return result is not None


def get_or_generate_sku(db: Session, provided_sku: Optional[str] = None) -> str:
    """
    Get provided SKU or generate a new one.

    Args:
        db: SQLAlchemy database session
        provided_sku: Optional SKU provided by user

    Returns:
        Valid SKU string

    Raises:
        ValueError: If provided SKU has invalid format
        ValueError: If provided SKU already exists
    """
    if provided_sku:
        # Validate format
        if not validate_sku_format(provided_sku):
            raise ValueError(
                f"Invalid SKU format: '{provided_sku}'. "
                f"Must match pattern: {SKU_PATTERN.pattern}"
            )

        # Check for duplicate
        if check_sku_exists(db, provided_sku):
            raise ValueError(f"SKU '{provided_sku}' already exists")

        return provided_sku

    # Generate new SKU
    return generate_next_sku(db)
