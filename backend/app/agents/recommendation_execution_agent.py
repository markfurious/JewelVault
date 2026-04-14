"""
Recommendation Execution Agent.
Generates and attaches product recommendations to inventory metadata.

Actions:
- Analyzes sales velocity and inventory patterns
- Generates product recommendations using Claude
- Attaches recommendations to product metadata (JSONB update)
- Tracks recommendation effectiveness
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import json

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.product import Product
from app.models.inventory import Inventory, InventoryStatus
from app.models.sale import SaleItem, Sale
from app.models.agent_audit import AgentAuditLog
from app.services.analytics_service import AnalyticsService
from app.services.product_service import ProductService


class RecommendationExecutionAgent(AgentBase):
    """
    Agent that generates and attaches product recommendations.

    Recommendations are stored in product.attributes['recommendations']
    and can be used for cross-selling and inventory planning.
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.analytics_service = AnalyticsService(db)
        self.product_service = ProductService(db)

    def run(
        self,
        product_id: Optional[UUID] = None,
        category: Optional[str] = None,
        recommendation_type: str = "cross_sell",
        max_recommendations: int = 5,
    ) -> AgentResult:
        """
        Generate and attach recommendations.

        Args:
            product_id: Specific product to generate recommendations for
            category: Category to analyze for recommendations
            recommendation_type: Type of recommendation (cross_sell, similar, complementary)
            max_recommendations: Maximum number of recommendations per product

        Returns:
            AgentResult with actions taken
        """
        try:
            self.actions = []

            if product_id:
                # Generate for specific product
                self._generate_for_product(product_id, recommendation_type, max_recommendations)
            elif category:
                # Generate for category
                self._generate_for_category(category, recommendation_type, max_recommendations)
            else:
                # Generate for all active products
                self._generate_all(recommendation_type, max_recommendations)

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Generated recommendations for {len(self.actions)} products",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Recommendation generation failed",
                error=str(e),
            )

    def decide(
        self,
        product: Product,
        candidate_products: List[Product],
        sales_data: Dict[str, Any],
        recommendation_type: str,
    ) -> Dict[str, Any]:
        """
        Decide which products to recommend.

        Args:
            product: Target product
            candidate_products: Potential recommendation candidates
            sales_data: Sales velocity and pattern data
            recommendation_type: Type of recommendation

        Returns:
            Decision with recommended product IDs and reasoning
        """
        # Build context for Claude
        product_context = f"""
Target Product:
- Name: {product.name}
- SKU: {product.sku}
- Category: {product.category}
- Price: ${product.retail_price}
- Attributes: {json.dumps(product.attributes or {})}
- Sales Velocity: {sales_data.get('daily_velocity', 0):.2f} units/day
"""

        candidates_context = "\nCandidate Products:\n"
        for i, p in enumerate(candidate_products[:10]):  # Limit context
            candidates_context += f"""
{i+1}. {p.name} ({p.sku})
   Category: {p.category}, Price: ${p.retail_price}
   Attributes: {json.dumps(p.attributes or {})}
"""

        situation = product_context + candidates_context

        # Get recommendation logic from Claude
        prompt_map = {
            "cross_sell": "Recommend products that customers often buy together or as alternatives.",
            "similar": "Recommend products with similar attributes, style, and price point.",
            "complementary": "Recommend products that complement this item (e.g., chain for pendant).",
            "upgrade": "Recommend higher-priced alternatives in the same category.",
        }

        criteria = prompt_map.get(recommendation_type, "Recommend relevant products.")

        decision = self.claude.generate_decision(
            situation=situation,
            options=[f"Recommend {p.sku}" for p in candidate_products[:5]],
            criteria=criteria,
        )

        # Parse selected options into product IDs
        recommended_skus = []
        selected = decision.get("selected_option", "")
        if "sku" in selected.lower():
            # Extract SKU from decision
            for p in candidate_products:
                if p.sku in selected:
                    recommended_skus.append(str(p.id))

        # If no specific selection, use top candidates by velocity
        if not recommended_skus and candidate_products:
            recommended_skus = [str(p.id) for p in candidate_products[:3]]

        return {
            "recommended_product_ids": recommended_skus,
            "reasoning": decision.get("reasoning", "Based on sales patterns and product attributes"),
            "confidence": decision.get("confidence", 0.7),
        }

    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """Execute recommendation attachment (called within run methods)."""
        return self.actions

    def _generate_for_product(
        self,
        product_id: UUID,
        recommendation_type: str,
        max_recommendations: int,
    ):
        """Generate recommendations for a specific product."""
        product = self.db.get(Product, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Get candidates based on recommendation type
        candidates = self._get_candidate_products(product, recommendation_type)

        # Get sales data
        sales_data = self._get_sales_data(product_id)

        # Make decision
        decision = self.decide(product, candidates, sales_data, recommendation_type)

        # Update product with recommendations
        self._attach_recommendations(
            product=product,
            recommended_ids=decision["recommended_product_ids"][:max_recommendations],
            recommendation_type=recommendation_type,
            reasoning=decision["reasoning"],
        )

    def _generate_for_category(
        self,
        category: str,
        recommendation_type: str,
        max_recommendations: int,
    ):
        """Generate recommendations for all products in a category."""
        products = self.db.execute(
            select(Product).where(Product.category == category).where(Product.is_active == True)
        ).scalars().all()

        for product in products:
            self._generate_for_product(product.id, recommendation_type, max_recommendations)

    def _generate_all(self, recommendation_type: str, max_recommendations: int):
        """Generate recommendations for all active products."""
        products = self.db.execute(
            select(Product).where(Product.is_active == True)
        ).scalars().all()

        for product in products:
            try:
                self._generate_for_product(product.id, recommendation_type, max_recommendations)
            except Exception as e:
                self.logger.warning(f"Failed to generate recommendations for {product.sku}: {e}")

    def _get_candidate_products(
        self,
        product: Product,
        recommendation_type: str,
    ) -> List[Product]:
        """Get candidate products for recommendation."""
        query = select(Product).where(Product.is_active == True).where(Product.id != product.id)

        if recommendation_type == "similar":
            # Same category, similar price range
            min_price = float(product.retail_price) * 0.5 if product.retail_price else 0
            max_price = float(product.retail_price) * 2.0 if product.retail_price else 10000
            query = query.where(
                Product.category == product.category
            ).where(
                Product.retail_price >= min_price
            ).where(
                Product.retail_price <= max_price
            )
        elif recommendation_type == "complementary":
            # Different category that complements
            complementary_categories = self._get_complementary_categories(product.category)
            if complementary_categories:
                query = query.where(Product.category.in_(complementary_categories))
        else:
            # Same category for cross-sell
            query = query.where(Product.category == product.category)

        # Limit candidates
        query = query.limit(20)

        return list(self.db.execute(query).scalars().all())

    def _get_complementary_categories(self, category: str) -> List[str]:
        """Get categories that complement the given category."""
        complementary_map = {
            "Rings": ["Necklaces", "Earrings", "Bracelets"],
            "Necklaces": ["Rings", "Earrings", "Pendants"],
            "Pendants": ["Chains", "Necklaces"],
            "Chains": ["Pendants", "Necklaces"],
            "Earrings": ["Rings", "Necklaces", "Bracelets"],
            "Bracelets": ["Rings", "Earrings", "Necklaces"],
        }
        return complementary_map.get(category, [])

    def _get_sales_data(self, product_id: UUID) -> Dict[str, Any]:
        """Get sales data for a product."""
        # Get sales in last 30 days
        date_from = datetime.utcnow() - timedelta(days=30)

        sales_count = self.db.execute(
            select(SaleItem)
            .join(Sale)
            .where(SaleItem.product_id == product_id)
            .where(Sale.sale_date >= date_from)
            .where(Sale.status == "COMPLETED")
        ).scalar_one_or_none()

        total_sales = self.db.execute(
            select(SaleItem)
            .where(SaleItem.product_id == product_id)
        ).scalar_one_or_none()

        return {
            "sales_last_30_days": 1 if sales_count else 0,
            "daily_velocity": (1 if sales_count else 0) / 30,
        }

    def _attach_recommendations(
        self,
        product: Product,
        recommended_ids: List[str],
        recommendation_type: str,
        reasoning: str,
    ):
        """Attach recommendations to product attributes."""
        # Initialize recommendations in attributes if not present
        if not product.attributes:
            product.attributes = {}

        if "recommendations" not in product.attributes:
            product.attributes["recommendations"] = {}

        # Update recommendations
        product.attributes["recommendations"][recommendation_type] = {
            "product_ids": recommended_ids,
            "generated_at": datetime.utcnow().isoformat(),
            "reasoning": reasoning,
            "algorithm": "claude_assisted",
        }

        if not self.dry_run:
            self.db.add(product)

        self._log_action(
            action_type="ATTACH_RECOMMENDATIONS",
            description=f"Attached {recommendation_type} recommendations to {product.name}",
            entity_type="product",
            entity_id=product.id,
            data={
                "product_name": product.name,
                "product_sku": product.sku,
                "recommendation_type": recommendation_type,
                "recommended_count": len(recommended_ids),
                "recommended_ids": recommended_ids,
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="ATTACH_RECOMMENDATIONS",
            description=f"Recommendations attached to {product.name}",
            entity_type="product",
            entity_id=product.id,
            action_data={
                "recommendation_type": recommendation_type,
                "count": len(recommended_ids),
            },
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

    def get_recommendations_for_product(
        self,
        product_id: UUID,
        recommendation_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve recommendations for a product."""
        product = self.db.get(Product, product_id)
        if not product or not product.attributes:
            return {"recommendations": {}}

        recommendations = product.attributes.get("recommendations", {})

        if recommendation_type:
            return {"recommendations": {recommendation_type: recommendations.get(recommendation_type, {})}}

        return {"recommendations": recommendations}
