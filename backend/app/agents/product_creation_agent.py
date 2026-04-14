"""
Product Creation Agent.
Creates products from natural language descriptions.

Actions:
- Parses natural language product descriptions
- Extracts attributes (carat, cut, clarity, color, metal, etc.)
- Inserts into DB via ProductService
- Generates appropriate SKU
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session

from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.claude_service import ClaudeService
from app.models.product import Product
from app.models.agent_audit import AgentAuditLog
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate


# Category mappings for jewelry products
CATEGORY_MAP = {
    "ring": "Rings",
    "necklace": "Necklaces",
    "pendant": "Pendants",
    "chain": "Chains",
    "earring": "Earrings",
    "bracelet": "Bracelets",
    "bangle": "Bracelets",
    "brooch": "Brooches",
    "cufflink": "Cufflinks",
}

# Diamond clarity grades
CLARITY_GRADES = [
    "FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "I1", "I2", "I3"
]

# Diamond color grades (D-Z scale)
COLOR_GRADES = [
    "D", "E", "F",  # Colorless
    "G", "H", "I", "J",  # Near colorless
    "K", "L", "M",  # Faint yellow
    "N", "O", "P", "Q", "R",  # Very light yellow
    "S", "T", "U", "V", "W", "X", "Y", "Z",  # Light yellow
]

# Cut grades
CUT_GRADES = ["Excellent", "Very Good", "Good", "Fair", "Poor"]

# Metal purity options
METAL_PURITIES = ["14K", "18K", "24K", "925", "PT900", "PT950", "Platinum"]


class ProductCreationAgent(AgentBase):
    """
    Agent that creates products from natural language descriptions.

    Example input:
    "Create 1ct round diamond, VS1, G color, 18K white gold ring"
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        super().__init__(db, claude, dry_run)
        self.product_service = ProductService(db)

    def run(self, description: str, category: Optional[str] = None) -> AgentResult:
        """
        Create a product from natural language description.

        Args:
            description: Natural language product description
            category: Optional category hint

        Returns:
            AgentResult with created product info
        """
        try:
            self.actions = []

            # Parse the description
            parsed = self.decide(description=description, category_hint=category)

            if "error" in parsed:
                return self._create_result(
                    success=False,
                    message=f"Failed to parse description: {parsed.get('error')}",
                    error=parsed.get("error"),
                )

            # Create the product
            product = self.act(parsed)

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Created product {product.name} ({product.sku})",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Product creation failed",
                error=str(e),
            )

    def decide(self, description: str, category_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse natural language description into structured product data.

        Args:
            description: Natural language description
            category_hint: Optional category hint

        Returns:
            Structured product data dict
        """
        system_prompt = """You are an expert jewelry product analyzer. Extract product attributes from natural language descriptions.

For each description, extract:
- product_type: ring, necklace, earring, bracelet, pendant, chain, etc.
- stone_type: diamond, ruby, sapphire, emerald, etc. (if applicable)
- carat_weight: numeric carat value for stones
- clarity: diamond clarity grade (FL, IF, VVS1, VVS2, VS1, VS2, SI1, SI2, I1, I2, I3)
- color: diamond color grade (D-Z) or metal color
- cut: cut grade or shape (round, princess, oval, emerald, pear, marquise, cushion, asscher, radiant, heart)
- metal_type: gold, silver, platinum
- metal_purity: 14K, 18K, 24K, 925, PT900, PT950
- metal_color: yellow, white, rose
- product_weight: weight in grams if mentioned
- style: any style descriptors
- certified: whether certification is mentioned (yes/no)

Respond ONLY with valid JSON:
{
    "product_type": "ring",
    "stone_type": "diamond",
    "carat_weight": 1.0,
    "clarity": "VS1",
    "color": "G",
    "cut": "round",
    "metal_type": "gold",
    "metal_purity": "18K",
    "metal_color": "white",
    "product_weight": null,
    "style": "solitaire",
    "certified": false,
    "suggested_name": "1ct Round Diamond VS1 G Color 18K White Gold Ring",
    "suggested_price": 5000.00
}

If an attribute is not mentioned, use null for that field."""

        user_message = f"Description: {description}"
        if category_hint:
            user_message += f"\nCategory hint: {category_hint}"

        parsed = self.claude.extract_structured_data(
            text=user_message,
            schema={
                "product_type": "Type of jewelry (ring, necklace, earring, etc.)",
                "stone_type": "Type of gemstone if applicable",
                "carat_weight": "Carat weight of main stone",
                "clarity": "Diamond clarity grade",
                "color": "Diamond color grade or metal color",
                "cut": "Cut grade or shape",
                "metal_type": "Metal type",
                "metal_purity": "Metal purity",
                "metal_color": "Metal color",
                "product_weight": "Weight in grams",
                "style": "Style description",
                "certified": "Whether certified",
                "suggested_name": "Generated product name",
                "suggested_price": "Suggested retail price",
            },
        )

        return parsed

    def act(self, parsed_data: Dict[str, Any]) -> Product:
        """
        Create product in database from parsed data.

        Args:
            parsed_data: Structured product data from decide()

        Returns:
            Created Product instance
        """
        # Map product type to category
        product_type = parsed_data.get("product_type", "").lower()
        category = CATEGORY_MAP.get(product_type, "Other")

        # Build attributes dict
        attributes = {}
        if parsed_data.get("stone_type"):
            attributes["stone_type"] = parsed_data["stone_type"]
        if parsed_data.get("carat_weight"):
            attributes["carat_weight"] = parsed_data["carat_weight"]
        if parsed_data.get("clarity"):
            attributes["clarity"] = parsed_data["clarity"]
        if parsed_data.get("color") and parsed_data.get("color").upper() in COLOR_GRADES:
            attributes["diamond_color"] = parsed_data["color"].upper()
        if parsed_data.get("cut"):
            attributes["cut"] = parsed_data["cut"]
        if parsed_data.get("style"):
            attributes["style"] = parsed_data["style"]
        if parsed_data.get("certified"):
            attributes["certified"] = parsed_data["certified"]

        # Determine gold purity
        gold_purity = ""
        if parsed_data.get("metal_purity"):
            gold_purity = parsed_data["metal_purity"]
            if parsed_data.get("metal_color"):
                gold_purity = f"{parsed_data['metal_color']} {gold_purity}"

        # Build product name if not provided
        name = parsed_data.get("suggested_name")
        if not name:
            name_parts = []
            if parsed_data.get("carat_weight"):
                name_parts.append(f"{parsed_data['carat_weight']}ct")
            if parsed_data.get("cut"):
                name_parts.append(parsed_data["cut"].capitalize())
            if parsed_data.get("stone_type"):
                name_parts.append(parsed_data["stone_type"].capitalize())
            if parsed_data.get("clarity"):
                name_parts.append(parsed_data["clarity"])
            if parsed_data.get("color") and parsed_data.get("color").upper() in COLOR_GRADES:
                name_parts.append(f"{parsed_data['color']} Color")
            if parsed_data.get("metal_purity"):
                name_parts.append(parsed_data["metal_purity"])
            if parsed_data.get("metal_color"):
                name_parts.append(parsed_data["metal_color"].capitalize())
            name_parts.append(category.rstrip('s'))  # e.g., "Rings" -> "Ring"
            name = " ".join(name_parts)

        # Create schema
        schema = ProductCreate(
            name=name,
            description=parsed_data.get("style") or f"{category} - {name}",
            category=category,
            sub_category=product_type if product_type else None,
            st_carat=parsed_data.get("carat_weight"),
            gold_purity=gold_purity,
            certified=parsed_data.get("certified", False),
            retail_price=parsed_data.get("suggested_price") or Decimal("0"),
            is_active=True,
            attributes=attributes,
            default_reorder_threshold=5,
        )

        # Create product
        if self.dry_run:
            # Simulate creation
            product = Product(
                sku="DRY-RUN-SKU",
                name=schema.name,
                description=schema.description,
                category=schema.category,
                retail_price=schema.retail_price,
                attributes=schema.attributes,
            )
        else:
            product = self.product_service.create(schema)

        self._log_action(
            action_type="CREATE_PRODUCT",
            description=f"Created product {product.name} ({product.sku})",
            entity_type="product",
            entity_id=product.id,
            data={
                "product_name": product.name,
                "product_sku": product.sku,
                "category": product.category,
                "attributes": attributes,
                "retail_price": float(product.retail_price) if product.retail_price else None,
            },
        )

        # Create audit log
        audit_log = AgentAuditLog(
            agent_name=self.get_name(),
            action_type="CREATE_PRODUCT",
            description=f"Product created: {product.name}",
            entity_type="product",
            entity_id=product.id,
            action_data={
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
            },
            dry_run=self.dry_run,
        )
        self.db.add(audit_log)

        return product

    def run_batch(self, descriptions: List[str]) -> AgentResult:
        """
        Create multiple products from descriptions.

        Args:
            descriptions: List of natural language descriptions

        Returns:
            AgentResult with summary of created products
        """
        try:
            self.actions = []
            created_count = 0
            failed_count = 0

            for desc in descriptions:
                try:
                    parsed = self.decide(description=desc)
                    if "error" not in parsed:
                        self.act(parsed)
                        created_count += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1

            self._commit_if_not_dry_run()

            return self._create_result(
                success=True,
                message=f"Created {created_count} products, {failed_count} failed",
            )

        except Exception as e:
            self._rollback()
            return self._create_result(
                success=False,
                message="Batch product creation failed",
                error=str(e),
            )
