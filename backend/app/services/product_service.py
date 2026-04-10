"""
Product service.
Handles all business logic related to products.
Item-based model: each SKU represents ONE item tracked by status.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.models.reorder import ReorderRule
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.exceptions import NotFoundError, DuplicateError
from app.utils.sku_generator import get_or_generate_sku


def _to_decimal(value):
    """Convert value to Decimal for database storage."""
    if value is None:
        return None
    return Decimal(str(value))


class ProductService:
    """Service for product operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, schema: ProductCreate) -> Product:
        """
        Create a new product with initial inventory.

        Item-based model:
        - initial_quantity > 0 → status = AVAILABLE
        - initial_quantity = 0 → status = AVAILABLE (ready for restock)

        Args:
            schema: ProductCreate schema with product data

        Returns:
            Created Product instance

        Raises:
            DuplicateError: If SKU already exists
            ValueError: If SKU format is invalid
        """
        # Generate or validate SKU
        try:
            final_sku = get_or_generate_sku(self.db, schema.sku)
        except ValueError as e:
            raise DuplicateError(str(e))

        # Create product with all fields including jewelry-specific ones
        product = Product(
            sku=final_sku,
            name=schema.name,
            description=schema.description,
            category=schema.category,
            sub_category=schema.sub_category,
            style_number=schema.style_number,
            st_carat=_to_decimal(schema.st_carat),
            product_weight=_to_decimal(schema.product_weight),
            gold_purity=schema.gold_purity,
            certified=schema.certified,
            cost_price=_to_decimal(schema.cost_price),
            retail_price=_to_decimal(schema.retail_price),
            wholesale_price=_to_decimal(schema.wholesale_price),
            online_price=_to_decimal(schema.online_price),
            is_active=schema.is_active,
            attributes=schema.attributes or {},
            default_reorder_threshold=schema.default_reorder_threshold,
        )
        self.db.add(product)
        self.db.flush()  # Get the ID

        # Create initial inventory (item-based: always create with status)
        # In item-based model, each product has exactly one inventory item
        initial_status = InventoryStatus.AVAILABLE
        inventory = Inventory(
            product_id=product.id,
            status=initial_status,
            location=schema.initial_location,
        )
        self.db.add(inventory)

        # Create default reorder rule
        reorder_rule = ReorderRule(
            product_id=product.id,
            min_threshold=schema.default_reorder_threshold,
            target_stock=schema.default_reorder_threshold * 5,
        )
        self.db.add(reorder_rule)

        self.db.commit()
        self.db.refresh(product)

        return product

    def get_by_id(self, product_id: UUID) -> Product:
        """
        Get a product by ID.

        Args:
            product_id: UUID of the product

        Returns:
            Product instance

        Raises:
            NotFoundError: If product not found
        """
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundError(f"Product with ID {product_id} not found")
        return product

    def get_by_sku(self, sku: str) -> Product:
        """
        Get a product by SKU.

        Args:
            sku: Stock Keeping Unit

        Returns:
            Product instance

        Raises:
            NotFoundError: If product not found
        """
        product = self.db.execute(
            select(Product).where(Product.sku == sku)
        ).scalar_one_or_none()

        if not product:
            raise NotFoundError(f"Product with SKU '{sku}' not found")
        return product

    def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[Product], int]:
        """
        List products with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            category: Filter by category
            is_active: Filter by active status

        Returns:
            Tuple of (products list, total count)
        """
        query = select(Product)

        if category:
            query = query.where(Product.category == category)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)

        # Get total count
        total_query = select(func.count()).select_from(Product)
        if category:
            total_query = total_query.where(Product.category == category)
        if is_active is not None:
            total_query = total_query.where(Product.is_active == is_active)

        total = self.db.execute(total_query).scalar() or 0

        # Get paginated results
        products = (
            self.db.execute(query.offset(skip).limit(limit)).scalars().all()
        )

        return list(products), total

    def update(self, product_id: UUID, schema: ProductUpdate) -> Product:
        """
        Update a product.

        Args:
            product_id: UUID of the product
            schema: ProductUpdate schema with updates

        Returns:
            Updated Product instance

        Raises:
            NotFoundError: If product not found
            DuplicateError: If new SKU already exists
        """
        product = self.get_by_id(product_id)

        # Check SKU uniqueness if changing
        if schema.sku and schema.sku != product.sku:
            existing = self.db.execute(
                select(Product).where(Product.sku == schema.sku)
            ).scalar_one_or_none()
            if existing:
                raise DuplicateError(f"Product with SKU '{schema.sku}' already exists")

        # Update fields
        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # Convert numeric fields to Decimal for DB
            if field in ['st_carat', 'product_weight', 'cost_price', 'retail_price',
                         'wholesale_price', 'online_price', 'default_reorder_threshold']:
                value = _to_decimal(value)
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)

        return product

    def delete(self, product_id: UUID) -> None:
        """
        Soft delete a product (mark as inactive).

        Args:
            product_id: UUID of the product

        Raises:
            NotFoundError: If product not found
        """
        product = self.get_by_id(product_id)
        product.is_active = False
        self.db.commit()

    def hard_delete(self, product_id: UUID) -> None:
        """
        Permanently delete a product.

        Args:
            product_id: UUID of the product

        Raises:
            NotFoundError: If product not found
        """
        product = self.get_by_id(product_id)
        self.db.delete(product)
        self.db.commit()
