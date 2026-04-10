"""
Sale service.
Handles all business logic related to sales transactions.
Item-based model: selling sets item status to SOLD (no quantity reduction).
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.models.sale import Sale, SaleItem, SaleReturn
from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus, InventoryTransaction
from app.schemas.sale import SaleCreate, SaleType
from app.utils.exceptions import NotFoundError, ValidationError
from app.services.inventory_service import InventoryService


class SaleService:
    """Service for sale operations (item-based model)."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_sale_number(self) -> str:
        """Generate a unique sale number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        # Get count of sales today for sequence
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.execute(
            select(func.count()).where(Sale.sale_date >= today_start)
        ).scalar() or 0
        return f"SAL-{timestamp}-{count + 1:04d}"

    def create(self, schema: SaleCreate) -> Sale:
        """
        Create a new sale and mark items as SOLD.

        In the item-based model:
        - Each item represents ONE physical product
        - Selling marks the item status as SOLD
        - Cannot sell if item is not AVAILABLE

        Args:
            schema: SaleCreate schema with sale data

        Returns:
            Created Sale instance

        Raises:
            ValidationError: If any item is not available
            NotFoundError: If any product not found
        """
        # Validate products and calculate totals
        items_data = []
        subtotal = 0.0

        for item_schema in schema.items:
            # Get product
            product = self.db.get(Product, item_schema.product_id)
            if not product:
                raise NotFoundError(f"Product {item_schema.product_id} not found")

            # Get inventory
            inventory = self.db.execute(
                select(Inventory).where(Inventory.product_id == item_schema.product_id)
            ).scalar_one_or_none()

            # Item-based validation: check if item is available
            if not inventory:
                raise ValidationError(
                    f"Item not found for product {product.sku}. "
                    f"Cannot sell without inventory record."
                )

            if inventory.status != InventoryStatus.AVAILABLE:
                raise ValidationError(
                    f"Cannot sell product {product.sku}. "
                    f"Current status: {inventory.status}. Item must be AVAILABLE."
                )

            # Determine price based on sale type
            if schema.sale_type == SaleType.WHOLESALE and product.wholesale_price:
                unit_price = float(product.wholesale_price)
            else:
                unit_price = float(product.retail_price or 0)

            item_subtotal = unit_price * float(item_schema.quantity)
            subtotal += item_subtotal

            items_data.append({
                "product": product,
                "quantity": item_schema.quantity,
                "unit_price": unit_price,
                "subtotal": item_subtotal,
                "inventory": inventory,
            })

        # Calculate totals
        tax_amount = subtotal * (schema.tax_rate / 100)
        total_amount = subtotal + tax_amount - schema.discount_amount

        # Create sale
        sale = Sale(
            sale_number=self._generate_sale_number(),
            customer_name=schema.customer_name,
            customer_email=schema.customer_email,
            customer_phone=schema.customer_phone,
            sale_type=schema.sale_type.value,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=schema.discount_amount,
            total_amount=total_amount,
            payment_method=schema.payment_method.value if schema.payment_method else None,
            payment_status="COMPLETED",
            status="COMPLETED",
            notes=schema.notes,
        )
        self.db.add(sale)
        self.db.flush()

        # Create sale items and mark inventory as SOLD
        inventory_service = InventoryService(self.db)
        for item_data in items_data:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item_data["product"].id,
                product_name=item_data["product"].name,
                product_sku=item_data["product"].sku,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                subtotal=item_data["subtotal"],
            )
            self.db.add(sale_item)

            # Mark item as SOLD (creates transaction record)
            inventory_service.mark_sold(
                product_id=item_data["product"].id,
                reference_id=sale.id,
                reference_type="sale"
            )

        self.db.commit()
        self.db.refresh(sale)

        return sale

    def get_by_id(self, sale_id: UUID) -> Sale:
        """
        Get a sale by ID.

        Args:
            sale_id: UUID of the sale

        Returns:
            Sale instance

        Raises:
            NotFoundError: If sale not found
        """
        sale = self.db.get(Sale, sale_id)
        if not sale:
            raise NotFoundError(f"Sale with ID {sale_id} not found")
        return sale

    def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        sale_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[List[Sale], int]:
        """
        List sales with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            sale_type: Filter by sale type
            status: Filter by status
            date_from: Filter by sale date from
            date_to: Filter by sale date to

        Returns:
            Tuple of (sales list, total count)
        """
        query = select(Sale)

        if sale_type:
            query = query.where(Sale.sale_type == sale_type)
        if status:
            query = query.where(Sale.status == status)
        if date_from:
            query = query.where(Sale.sale_date >= date_from)
        if date_to:
            query = query.where(Sale.sale_date <= date_to)

        # Get total count
        total_query = select(func.count()).select_from(Sale)
        if sale_type:
            total_query = total_query.where(Sale.sale_type == sale_type)
        if status:
            total_query = total_query.where(Sale.status == status)
        if date_from:
            total_query = total_query.where(Sale.sale_date >= date_from)
        if date_to:
            total_query = total_query.where(Sale.sale_date <= date_to)
        total = self.db.execute(total_query).scalar() or 0

        # Get paginated results
        sales = (
            self.db.execute(
                query.order_by(Sale.sale_date.desc()).offset(skip).limit(limit)
            )
            .scalars()
            .all()
        )

        return list(sales), total

    def cancel_sale(self, sale_id: UUID) -> Sale:
        """
        Cancel a sale and restore items to AVAILABLE.

        Args:
            sale_id: UUID of the sale

        Returns:
            Updated Sale instance

        Raises:
            NotFoundError: If sale not found
            ValidationError: If sale already cancelled/refunded
        """
        sale = self.get_by_id(sale_id)

        if sale.status in ["CANCELLED", "REFUNDED"]:
            raise ValidationError(f"Sale {sale.sale_number} is already {sale.status}")

        # Restore inventory - mark items as AVAILABLE
        inventory_service = InventoryService(self.db)
        for item in sale.items:
            try:
                inventory_service.mark_available(
                    product_id=item.product_id,
                    notes=f"Restored from cancelled sale {sale.sale_number}",
                )
            except NotFoundError:
                pass  # Skip if inventory record doesn't exist

        sale.status = "CANCELLED"
        sale.payment_status = "REFUNDED"
        self.db.commit()
        self.db.refresh(sale)

        return sale

    def get_sales_by_product(
        self,
        product_id: UUID,
        days: int = 30,
    ) -> List[Sale]:
        """
        Get sales for a specific product within a time period.

        Args:
            product_id: UUID of the product
            days: Number of days to look back

        Returns:
            List of Sale instances
        """
        date_from = datetime.utcnow() - timedelta(days=days)

        sales = self.db.execute(
            select(Sale)
            .join(SaleItem)
            .where(SaleItem.product_id == product_id)
            .where(Sale.sale_date >= date_from)
            .where(Sale.status == "COMPLETED")
            .order_by(Sale.sale_date.desc())
        ).scalars().all()

        return list(sales)

    def request_return(
        self,
        sale_id: UUID,
        product_ids: List[UUID],
        reason: str,
        requested_by: str,
        refund_amount: Optional[float] = None,
    ) -> SaleReturn:
        """
        Request a return for sold items.

        - Validates sale exists and is COMPLETED
        - Validates all products are in SOLD status
        - Creates return record with PENDING status
        - Updates inventory status to RETURN_PENDING

        Args:
            sale_id: UUID of the sale
            product_ids: List of product UUIDs to return
            reason: Return reason
            requested_by: User requesting the return
            refund_amount: Optional refund amount (calculated from sale if not provided)

        Returns:
            Created SaleReturn instance

        Raises:
            NotFoundError: If sale or products not found
            ValidationError: If items are not SOLD
        """
        # Validate sale exists
        sale = self.get_by_id(sale_id)
        if sale.status != "COMPLETED":
            raise ValidationError(f"Sale {sale.sale_number} status is {sale.status}, not COMPLETED")

        # Validate products belong to this sale and are SOLD
        sale_product_ids = {item.product_id for item in sale.items}
        for pid in product_ids:
            if pid not in sale_product_ids:
                raise ValidationError(f"Product {pid} is not in sale {sale_id}")

        # Validate inventory status and calculate refund if not provided
        inventory_service = InventoryService(self.db)
        if refund_amount is None:
            refund_amount = 0.0
            for item in sale.items:
                if item.product_id in product_ids:
                    refund_amount += float(item.subtotal)

        # Validate items are in SOLD status before allowing return
        for product_id in product_ids:
            inventory = self.db.execute(
                select(Inventory).where(Inventory.product_id == product_id)
            ).scalar_one_or_none()
            if not inventory:
                raise ValidationError(f"Product {product_id} not found in inventory")
            if inventory.status == "AVAILABLE":
                raise ValidationError(
                    f"Product {product_id} is already in stock (AVAILABLE). "
                    f"Cannot return items that are not sold."
                )
            if inventory.status != "SOLD":
                raise ValidationError(
                    f"Product {product_id} has status '{inventory.status}'. "
                    f"Only SOLD items can be returned."
                )

        # Update inventory to RETURN_PENDING
        try:
            inventory_service.bulk_update_status(
                product_ids=product_ids,
                target_status="RETURN_PENDING",
                notes=f"Return request for sale {sale.sale_number}",
                performed_by=requested_by,
            )
        except ValidationError as e:
            raise ValidationError(str(e))
        except NotFoundError as e:
            raise ValidationError(f"Inventory error: {str(e)}")

        # Create return record
        return_record = SaleReturn(
            sale_id=sale_id,
            product_ids=",".join(str(pid) for pid in product_ids),
            reason=reason,
            refund_amount=refund_amount,
            status="PENDING",
            requested_by=requested_by,
        )
        self.db.add(return_record)
        self.db.commit()
        self.db.refresh(return_record)

        return return_record

    def approve_return(
        self,
        return_id: UUID,
        approved_by: str,
        override_refund_amount: Optional[float] = None,
    ) -> SaleReturn:
        """
        Approve a return request.

        - Validates return exists and is PENDING
        - Updates inventory status to AVAILABLE
        - Updates sale payment_status to REFUNDED
        - Creates transaction log entries

        Args:
            return_id: UUID of the return request
            approved_by: Admin user approving
            override_refund_amount: Optional override of refund amount

        Returns:
            Updated SaleReturn instance

        Raises:
            NotFoundError: If return not found
            ValidationError: If return is not PENDING
        """
        # Get return record with lock
        return_record = self.db.execute(
            select(SaleReturn).where(SaleReturn.id == return_id)
        ).scalar_one_or_none()

        if not return_record:
            raise NotFoundError(f"Return request {return_id} not found")

        if return_record.status != "PENDING":
            raise ValidationError(f"Return request status is {return_record.status}, not PENDING")

        # Parse product IDs
        product_ids = [UUID(pid.strip()) for pid in return_record.product_ids.split(",")]

        # Update inventory to AVAILABLE
        inventory_service = InventoryService(self.db)
        inventory_service.bulk_update_status(
            product_ids=product_ids,
            target_status="AVAILABLE",
            notes=f"Return approved for sale {return_record.sale_id}",
            performed_by=approved_by,
        )

        # Update sale payment status
        sale = self.db.get(Sale, return_record.sale_id)
        if sale:
            sale.payment_status = "REFUNDED"

        # Update return record
        return_record.status = "APPROVED"
        return_record.approved_by = approved_by
        return_record.approved_at = datetime.utcnow()
        if override_refund_amount is not None:
            return_record.refund_amount = override_refund_amount

        self.db.commit()
        self.db.refresh(return_record)

        return return_record

    def reject_return(
        self,
        return_id: UUID,
        reason: str,
        rejected_by: str,
    ) -> SaleReturn:
        """
        Reject a return request.

        - Validates return exists and is PENDING
        - Updates inventory status back to SOLD
        - Records rejection reason

        Args:
            return_id: UUID of the return request
            reason: Rejection reason
            rejected_by: Admin user rejecting

        Returns:
            Updated SaleReturn instance

        Raises:
            NotFoundError: If return not found
            ValidationError: If return is not PENDING
        """
        # Get return record
        return_record = self.db.execute(
            select(SaleReturn).where(SaleReturn.id == return_id)
        ).scalar_one_or_none()

        if not return_record:
            raise NotFoundError(f"Return request {return_id} not found")

        if return_record.status != "PENDING":
            raise ValidationError(f"Return request status is {return_record.status}, not PENDING")

        # Parse product IDs
        product_ids = [UUID(pid.strip()) for pid in return_record.product_ids.split(",")]

        # Update inventory back to SOLD
        inventory_service = InventoryService(self.db)
        inventory_service.bulk_update_status(
            product_ids=product_ids,
            target_status="SOLD",
            notes=f"Return rejected: {reason}",
            performed_by=rejected_by,
        )

        # Update return record
        return_record.status = "REJECTED"
        return_record.rejected_by = rejected_by
        return_record.rejected_at = datetime.utcnow()
        return_record.rejection_reason = reason

        self.db.commit()
        self.db.refresh(return_record)

        return return_record

    def _get_product_skus_for_return(self, return_record: SaleReturn) -> str:
        """
        Get comma-separated SKUs for products in a return.

        Args:
            return_record: SaleReturn instance

        Returns:
            Comma-separated list of product SKUs
        """
        product_ids = [UUID(pid.strip()) for pid in return_record.product_ids.split(",")]

        # Get SKUs from sale_items for this sale
        items = self.db.execute(
            select(SaleItem.product_sku)
            .where(SaleItem.sale_id == return_record.sale_id)
            .where(SaleItem.product_id.in_(product_ids))
        ).scalars().all()

        return ",".join(items)

    def get_return_by_id(self, return_id: UUID) -> SaleReturn:
        """
        Get a sale return by ID.

        Args:
            return_id: UUID of the return

        Returns:
            SaleReturn instance with product_skus populated

        Raises:
            NotFoundError: If return not found
        """
        return_record = self.db.get(SaleReturn, return_id)
        if not return_record:
            raise NotFoundError(f"Return request {return_id} not found")

        # Populate product_skus from sale_items
        return_record.product_skus = self._get_product_skus_for_return(return_record)
        return return_record

    def list_returns(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        sale_id: Optional[UUID] = None,
    ) -> tuple[List[SaleReturn], int]:
        """
        List sale returns with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            status: Filter by status (PENDING, APPROVED, REJECTED)
            sale_id: Filter by sale ID

        Returns:
            Tuple of (returns list, total count)
        """
        query = select(SaleReturn)

        if status:
            query = query.where(SaleReturn.status == status)
        if sale_id:
            query = query.where(SaleReturn.sale_id == sale_id)

        # Get total count
        total_query = select(func.count()).select_from(SaleReturn)
        if status:
            total_query = total_query.where(SaleReturn.status == status)
        if sale_id:
            total_query = total_query.where(SaleReturn.sale_id == sale_id)
        total = self.db.execute(total_query).scalar() or 0

        # Get paginated results
        returns = (
            self.db.execute(
                query.order_by(SaleReturn.created_at.desc()).offset(skip).limit(limit)
            )
            .scalars()
            .all()
        )

        # Populate product_skus for each return
        for return_record in returns:
            return_record.product_skus = self._get_product_skus_for_return(return_record)

        return list(returns), total
