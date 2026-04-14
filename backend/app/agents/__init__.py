"""
AI Agents Package for JewelVault.

Action agents that can take decisions and trigger real operations:
- Inventory Manager: Auto-reordering and dead stock handling
- Pricing Update: Metal price-based price recalculation
- Sales Execution: Sale processing with inventory integration
- Product Creation: Natural language product creation
- Recommendation Execution: Product recommendations
- AR Session: Try-on session logging and analytics
- Anomaly Action: Fraud/anomaly detection and response

Usage:
    from app.agents.agent_orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator(db)
    result = orchestrator.run("Restock low inventory")
"""

from app.agents.claude_service import ClaudeService
from app.agents.agent_base import AgentBase, AgentResult, AgentAction
from app.agents.agent_orchestrator import AgentOrchestrator

from app.agents.inventory_manager_agent import InventoryManagerAgent
from app.agents.pricing_update_agent import PricingUpdateAgent
from app.agents.sales_execution_agent import SalesExecutionAgent
from app.agents.product_creation_agent import ProductCreationAgent
from app.agents.recommendation_execution_agent import RecommendationExecutionAgent
from app.agents.ar_session_agent import ARSessionAgent
from app.agents.anomaly_action_agent import AnomalyActionAgent

__all__ = [
    # Core
    "ClaudeService",
    "AgentBase",
    "AgentResult",
    "AgentAction",
    "AgentOrchestrator",
    # Agents
    "InventoryManagerAgent",
    "PricingUpdateAgent",
    "SalesExecutionAgent",
    "ProductCreationAgent",
    "RecommendationExecutionAgent",
    "ARSessionAgent",
    "AnomalyActionAgent",
]
