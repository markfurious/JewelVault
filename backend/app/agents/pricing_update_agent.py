"""
Pricing Update Agent.
Automatically recalculates product prices when metal prices change.

Actions:
- Recalculates prices based on metal content and weight
- Updates DB prices directly via ProductService
- Uses MetalPriceService for current rates
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.product import Product
from app.models.metal_price import MetalPrice
from app.models.agent_audit import AgentAuditLog
from app.models.agent_request import AgentRequest
from app.services.product_service import ProductService
from app.services.metal_price_service import MetalPriceService


# Metal type mappings for product categories
METAL_CATEGORY_MAP = {
    "gold": ["gold", "Gold", "14K", "18K", "24K", "yellow gold", "white gold", "rose gold"],
    "silver": ["silver", "Silver", "sterling", "925"],
    "platinum": ["platinum", "Platinum", "PT900", "PT950"],
}

# Default purity percentages
METAL_PURITY_MAP = {
    "14K": 0.585,
    "18K": 0.750,
    "24K": 0.999,
    "925": 0.925,
    "PT900": 0.900,
    "PT950": 0.950,
    "default": 0.750,  # Default to 18K equivalent
}


class PricingUpdateAgent(AgentBase):
    """
    Agent that updates product prices based on metal price changes.

    Triggers:
    - Metal price change exceeds threshold
    - Manual price recalculation request
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.product_service = ProductService(db)
        self.metal_price_service = MetalPriceService(db)

    def run(
        self,
        metal_type: Optional[str] = None,
        threshold_percent: float = 2.0,
        product_ids: Optional[List[UUID]] = None,
    ) -> AgentResult:
        """
        Run price update based on metal price changes.

        Args:
            metal_type: Specific metal to update (gold, silver, platinum)
            threshold_percent: Minimum price change to trigger update
            product_ids: Specific products to update (optional)

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if metal_type:
                # Update for specific metal
                self._update_prices_for_metal(metal_type, threshold_percent, product_ids)
            else:
                # Update for all metals
                for metal in ["gold", "silver", "platinum"]:
                    self._update_prices_for_metal(metal, threshold_percent, product_ids)

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Processed {len(self.actions)} price updates",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Price update failed",
                error=str(e),
            )

    def decide(
        self,
        product: Product,
        metal_price_change: float,
        current_price: Decimal,
    ) -> Dict[str, Any]:
        """
        Decide whether and how to update a product's price.

        Args:
            product: Product to evaluate
            metal_price_change: Percentage change in metal price
            current_price: Current product price

        Returns:
            Decision dict with update recommendation
        """
        # Calculate new price based on metal content
        metal_content = self._get_metal_content(product)
        if not metal_content:
            return {
                "action": "no_update",
                "reason": "No metal content data",
            }

        metal_type, weight_grams, purity = metal_content

        # Calculate price impact
        metal_cost_change = Decimal(str(weight_grams)) * Decimal(str(metal_price_change / 100))
        new_price = current_price + metal_cost_change

        price_change_percent = ((new_price - current_price) / current_price * 100) if current_price > 0 else Decimal(0)

        # Decision logic
        if abs(price_change_percent) < 1.0:
            return {
                "action": "no_update",
                "reason": "Price change below 1% threshold",
                "new_price": new_price,
            }

        # Use Claude for nuanced decisions on significant changes
        if abs(price_change_percent) > 10:
            situation = (
                f"Product {product.name} price would change by {price_change_percent:.1f}% due to metal price movement. "
                f"Current: ${current_price}, Proposed: ${new_price:.2f}"
            )

            decision = self.claude.generate_decision(
                situation=situation,
                options=[
                    "Apply full price change",
                    "Apply 50% of price change",
                    "Apply 75% of price change",
                    "Defer price change for review",
                ],
                criteria="Balance competitiveness with margin protection",
            )

            adjustment_map = {
                "Apply full price change": 1.0,
                "Apply 50% of price change": 0.5,
                "Apply 75% of price change": 0.75,
                "Defer price change for review": 0.0,
            }
            adjustment = adjustment_map.get(decision.get("selected_option", ""), 1.0)

            if adjustment == 0:
                return {
                    "action": "defer_review",
                    "reason": "Large price change requires manual review",
                    "new_price": new_price,
                    "adjustment_factor": adjustment,
                }

            adjusted_price = current_price + (new_price - current_price) * Decimal(str(adjustment))
        else:
            adjusted_price = new_price
            adjustment = 1.0

        return {
            "action": "update_price",
            "reason": f"Metal price change: {metal_price_change:.2f}%",
            "old_price": float(current_price),
            "new_price": float(adjusted_price),
            "adjustment_factor": adjustment,
        }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """Execute price update based on decision."""
        action_type = decision.get("action")

        if action_type == "no_update":
            return []

        return self.actions

    def _get_metal_content(self, product: Product) -> Optional[tuple]:
        """
        Extract metal content from product.

        Returns:
            Tuple of (metal_type, weight_grams, purity) or None
        """
        # Check product attributes first
        attributes = product.attributes or {}

        # Try to determine metal type from category or attributes
        category = (product.category or "").lower()
        sub_category = (product.sub_category or "").lower()
        gold_purity = product.gold_purity or ""

        metal_type = None
        purity = METAL_PURITY_MAP["default"]

        # Check category/sub_category for metal type
        for m_type, keywords in METAL_CATEGORY_MAP.items():
            for keyword in keywords:
                if keyword.lower() in category or keyword.lower() in sub_category or keyword.lower() in gold_purity.lower():
                    metal_type = m_type
                    break
            if metal_type:
                break

        # Check attributes for more specific info
        if attributes:
            attr_str = str(attributes).lower()
            for m_type, keywords in METAL_CATEGORY_MAP.items():
                for keyword in keywords:
                    if keyword.lower() in attr_str:
                        metal_type = m_type
                        break

        if not metal_type:
            return None

        # Get weight
        weight_grams = float(product.product_weight) if product.product_weight else 0.0

        # Get purity from gold_purity field
        if gold_purity:
            for purity_key, purity_val in METAL_PURITY_MAP.items():
                if purity_key.lower() in gold_purity.lower():
                    purity = purity_val
                    break

        return (metal_type, weight_grams, purity)

    def _update_prices_for_metal(
        self,
        metal_type: str,
        threshold_percent: float,
        product_ids: Optional[List[UUID]] = None,
    ):
        """Update prices for products containing a specific metal."""
        # Get current and previous metal prices
        prices = self.db.execute(
            select(MetalPrice)
            .where(MetalPrice.metal_type == metal_type)
            .order_by(desc(MetalPrice.created_at))
            .limit(2)
        ).scalars().all()

        if len(prices) < 2:
            self.logger.warning(f"Not enough price history for {metal_type}")
            return

        current_price = float(prices[0].price_per_gram)
        previous_price = float(prices[1].price_per_gram)

        if previous_price == 0:
            self.logger.warning(f"Previous {metal_type} price is zero")
            return

        price_change_percent = ((current_price - previous_price) / previous_price) * 100

        if abs(price_change_percent) < threshold_percent:
            self.logger.info(
                f"{metal_type} price change {price_change_percent:.2f}% below threshold {threshold_percent}%"
            )
            return

        self.logger.info(
            f"Processing {metal_type} price update: {price_change_percent:.2f}% change"
        )

        # Query products - filter by category if product_ids not specified
        query = select(Product).where(Product.is_active == True)

        # Add category filter based on metal type
        category_keywords = METAL_CATEGORY_MAP.get(metal_type, [])
        if category_keywords and not product_ids:
            # Simple category matching - can be enhanced with proper filtering
            pass

        if product_ids:
            query = query.where(Product.id.in_(product_ids))

        products = self.db.execute(query).scalars().all()

        updated_count = 0
        deferred_count = 0

        for product in products:
            metal_content = self._get_metal_content(product)
            if not metal_content:
                continue

            content_metal_type, _, _ = metal_content
            if content_metal_type != metal_type:
                continue

            # Get current price (use retail_price as base)
            current_product_price = product.retail_price or Decimal(0)
            if current_product_price == 0:
                continue

            # Make decision
            decision = self.decide(product, price_change_percent, current_product_price)

            if decision["action"] == "update_price":
                # Update product price
                old_price = float(current_product_price)
                new_price = Decimal(str(decision["new_price"]))

                if not self.dry_run:
                    product.retail_price = new_price
                    # Also update wholesale and online prices proportionally
                    if product.wholesale_price:
                        ratio = new_price / current_product_price
                        product.wholesale_price = product.wholesale_price * ratio
                    if product.online_price:
                        ratio = new_price / current_product_price
                        product.online_price = product.online_price * ratio

                self._log_action(
                    action_type="UPDATE_PRODUCT_PRICE",
                    description=f"Updated {product.name} ({product.sku}) price: ${old_price:.2f} → ${float(new_price):.2f}",
                    entity_type="product",
                    entity_id=product.id,
                    data={
                        "product_name": product.name,
                        "product_sku": product.sku,
                        "old_price": old_price,
                        "new_price": float(new_price),
                        "metal_type": metal_type,
                        "metal_price_change": price_change_percent,
                    },
                )

                # Create audit log
                audit_log = AgentAuditLog(
                    agent_name=self.get_name(),
                    action_type="UPDATE_PRODUCT_PRICE",
                    description=f"Price update for {product.name}",
                    entity_type="product",
                    entity_id=product.id,
                    action_data={
                        "old_price": old_price,
                        "new_price": float(new_price),
                        "metal_type": metal_type,
                    },
                    dry_run=self.dry_run,
                )
                self.db.add(audit_log)
                updated_count += 1

            elif decision["action"] == "defer_review":
                # Create agent request for admin review
                request = AgentRequest(
                    request_type="price_update",
                    title=f"Price Update: {product.name}",
                    description=f"Large price change ({price_change_percent:.1f}%) detected for {product.name} ({product.sku}) due to {metal_type} price movement. Requires manual review.",
                    agent_name=self.get_name(),
                    entity_type="product",
                    entity_id=product.id,
                    request_data={
                        "product_name": product.name,
                        "product_sku": product.sku,
                        "current_price": float(current_product_price),
                        "proposed_price": decision["new_price"],
                        "metal_type": metal_type,
                        "metal_price_change": price_change_percent,
                    },
                    proposed_action=f"Update {product.name} price from ${current_product_price:.2f} to ${decision['new_price']:.2f} ({price_change_percent:.1f}% change)",
                    impact_summary=f"Price adjustment due to {metal_type} market price change of {price_change_percent:.1f}%",
                    status="pending",
                )
                self.db.add(request)

                self._log_action(
                    action_type="DEFER_PRICE_UPDATE",
                    description=f"Deferred {product.name} ({product.sku}) price update for review",
                    entity_type="product",
                    entity_id=product.id,
                    data={
                        "product_name": product.name,
                        "product_sku": product.sku,
                        "proposed_price": decision["new_price"],
                        "reason": decision["reason"],
                        "request_id": str(request.id),
                    },
                )
                deferred_count += 1

        self.logger.info(
            f"{metal_type.capitalize()} price update complete: {updated_count} updated, {deferred_count} deferred"
        )
