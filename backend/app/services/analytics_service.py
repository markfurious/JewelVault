"""
Analytics service.
Handles business intelligence, reporting, and reorder suggestions.
Item-based model: tracks items by status, not quantity.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.models.sale import Sale, SaleItem
from app.models.reorder import ReorderRule
from app.schemas.reorder import ReorderSuggestion


class AnalyticsService:
    """Service for analytics and reporting operations (item-based model)."""

    def __init__(self, db: Session):
        self.db = db

    def get_reorder_suggestions(
        self,
        include_sold_recently: bool = True,
        velocity_days: int = 30,
    ) -> List[ReorderSuggestion]:
        """
        Generate reorder suggestions for item-based inventory.

        In item-based model, we suggest reordering when:
        - Item is SOLD (needs replacement)
        - Item has sales velocity and may need proactive reorder

        Args:
            include_sold_recently: Include recently sold items
            velocity_days: Number of days to consider for velocity calculation

        Returns:
            List of ReorderSuggestion ordered by urgency
        """
        suggestions = []
        date_from = datetime.utcnow() - timedelta(days=velocity_days)

        # Get all active products with SOLD status or sales history
        query = select(Product).join(Inventory).where(Product.is_active == True)

        if include_sold_recently:
            # Include products that are SOLD or have sales in the period
            sold_subquery = select(SaleItem.product_id).join(Sale).where(
                Sale.sale_date >= date_from
            ).where(Sale.status == "COMPLETED").distinct()
            query = query.where(
                (Inventory.status == InventoryStatus.SOLD) |
                (Product.id.in_(sold_subquery))
            )
        else:
            query = query.where(Inventory.status == InventoryStatus.SOLD)

        products = self.db.execute(query).scalars().all()

        for product in products:
            inventory = product.inventory

            # Calculate sales velocity (count of sales, not quantity)
            total_sold = self.db.execute(
                select(func.count(SaleItem.id))
                .join(Sale)
                .where(SaleItem.product_id == product.id)
                .where(Sale.sale_date >= date_from)
                .where(Sale.status == "COMPLETED")
            ).scalar() or 0

            daily_velocity = float(total_sold) / velocity_days if total_sold else 0.0

            # In item-based model: SOLD means needs reorder
            is_sold = inventory.status == InventoryStatus.SOLD
            is_fast_moving = daily_velocity > 0.5  # More than 0.5 sales/day

            # Calculate days until "stockout" (already sold)
            days_until_stockout = None
            if daily_velocity > 0 and is_sold:
                days_until_stockout = 0  # Already sold
            elif daily_velocity > 0:
                days_until_stockout = int(1 / daily_velocity)  # Time to sell 1 item

            # Calculate recommended reorder quantity (always 1 for item-based)
            recommended_quantity = 0
            if is_sold:
                recommended_quantity = 1  # Replace the sold item
            elif is_fast_moving and include_sold_recently:
                # Proactive reorder for fast movers
                recommended_quantity = 1

            # Only include if there's a recommendation
            if recommended_quantity > 0:
                suggestion = ReorderSuggestion(
                    product_id=product.id,
                    product_name=product.name,
                    product_sku=product.sku,
                    current_stock=0 if is_sold else 1,
                    min_threshold=1,  # Item-based: threshold is always 1
                    target_stock=1,
                    sales_velocity=round(daily_velocity, 2),
                    velocity_period_days=velocity_days,
                    is_urgent=is_sold,
                    is_fast_moving=is_fast_moving,
                    recommended_reorder_quantity=round(recommended_quantity, 2),
                    estimated_days_until_stockout=days_until_stockout,
                )
                suggestions.append(suggestion)

        # Sort by urgency (sold items first, then by velocity)
        suggestions.sort(
            key=lambda x: (
                not x.is_urgent,
                -x.sales_velocity,
            )
        )

        return suggestions

    def get_sales_velocity_report(
        self,
        days: int = 30,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get sales velocity report for top products.

        Args:
            days: Number of days for the report
            limit: Maximum number of products to return

        Returns:
            List of sales velocity data
        """
        date_from = datetime.utcnow() - timedelta(days=days)

        # Get products with sales in the period (count sales, not quantities)
        results = self.db.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.count(SaleItem.id).label("total_sales"),
                func.sum(SaleItem.subtotal).label("total_revenue"),
            )
            .join(SaleItem)
            .join(Sale)
            .where(Sale.sale_date >= date_from)
            .where(Sale.status == "COMPLETED")
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(func.count(SaleItem.id).desc())
            .limit(limit)
        ).all()

        report = []
        for row in results:
            daily_velocity = row.total_sales / days if days > 0 else 0

            # Determine trend (compare first half vs second half)
            mid_date = datetime.utcnow() - timedelta(days=days // 2)
            first_half = self.db.execute(
                select(func.count(SaleItem.id))
                .join(Sale)
                .where(SaleItem.product_id == row.id)
                .where(Sale.sale_date >= date_from)
                .where(Sale.sale_date < mid_date)
            ).scalar() or 0

            second_half = self.db.execute(
                select(func.count(SaleItem.id))
                .join(Sale)
                .where(SaleItem.product_id == row.id)
                .where(Sale.sale_date >= mid_date)
            ).scalar() or 0

            if second_half > first_half * 1.1:
                trend = "INCREASING"
            elif second_half < first_half * 0.9:
                trend = "DECREASING"
            else:
                trend = "STABLE"

            report.append({
                "product_id": row.id,
                "product_name": row.name,
                "product_sku": row.sku,
                "total_sales": row.total_sales,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
                "period_days": days,
                "daily_velocity": round(daily_velocity, 2),
                "trend": trend,
            })

        return report

    def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Get overall inventory summary (item-based model).

        Returns:
            Dictionary with inventory statistics by status
        """
        # Total products
        total_products = self.db.execute(
            select(func.count()).where(Product.is_active == True)
        ).scalar() or 0

        # Status breakdown
        status_counts = self.db.execute(
            select(
                Inventory.status,
                func.count(Inventory.id).label('count'),
            )
            .join(Product)
            .where(Product.is_active == True)
            .group_by(Inventory.status)
        ).all()

        status_breakdown = {
            "available": 0,
            "sold": 0,
            "reserved": 0,
        }
        for row in status_counts:
            if row.status:
                status_breakdown[row.status.lower()] = row.count

        # Total inventory value (available items only)
        stock_value = self.db.execute(
            select(func.sum(Product.cost_price))
            .join(Inventory)
            .join(Product)
            .where(Product.is_active == True)
            .where(Inventory.status == InventoryStatus.AVAILABLE)
        ).scalar() or 0

        return {
            "total_products": total_products,
            "total_stock_value": float(stock_value),
            "available_count": status_breakdown["available"],
            "sold_count": status_breakdown["sold"],
            "reserved_count": status_breakdown["reserved"],
        }

    def get_top_selling_products(
        self,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top selling products by sales count and revenue.

        Args:
            days: Number of days for the report
            limit: Maximum number of products

        Returns:
            List of top selling products
        """
        date_from = datetime.utcnow() - timedelta(days=days)

        results = self.db.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.count(SaleItem.id).label("total_sales"),
                func.sum(SaleItem.subtotal).label("total_revenue"),
            )
            .join(SaleItem)
            .join(Sale)
            .where(Sale.sale_date >= date_from)
            .where(Sale.status == "COMPLETED")
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(func.count(SaleItem.id).desc())
            .limit(limit)
        ).all()

        return [
            {
                "product_id": row.id,
                "product_name": row.name,
                "product_sku": row.sku,
                "total_sales": row.total_sales,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
            }
            for row in results
        ]
