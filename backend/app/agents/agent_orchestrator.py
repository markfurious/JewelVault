"""
Agent Orchestrator.
Central routing and execution engine for all AI agents.

Routes natural language queries to appropriate agents and executes actions.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
import json

from sqlalchemy.orm import Session

from app.agents.claude_service import ClaudeService
from app.agents.agent_base import AgentResult
from app.agents.inventory_manager_agent import InventoryManagerAgent
from app.agents.pricing_update_agent import PricingUpdateAgent
from app.agents.sales_execution_agent import SalesExecutionAgent
from app.agents.product_creation_agent import ProductCreationAgent
from app.agents.recommendation_execution_agent import RecommendationExecutionAgent
from app.agents.ar_session_agent import ARSessionAgent
from app.agents.anomaly_action_agent import AnomalyActionAgent


# Agent intent mappings
INTENT_AGENT_MAP = {
    "update_inventory": "inventory_manager",
    "create_reorder": "inventory_manager",
    "flag_dead_stock": "inventory_manager",
    "manage_inventory": "inventory_manager",

    "update_prices": "pricing_update",
    "recalculate_prices": "pricing_update",
    "metal_price_update": "pricing_update",

    "process_sale": "sales_execution",
    "create_sale": "sales_execution",
    "cancel_sale": "sales_execution",
    "process_return": "sales_execution",

    "create_product": "product_creation",
    "add_product": "product_creation",

    "generate_recommendations": "recommendation_execution",
    "attach_recommendations": "recommendation_execution",

    "log_ar_session": "ar_session",
    "analyze_ar_session": "ar_session",
    "ar_tryon": "ar_session",

    "detect_anomaly": "anomaly_action",
    "block_transaction": "anomaly_action",
    "flag_for_review": "anomaly_action",
}

# Agent class mapping
AGENT_CLASS_MAP = {
    "inventory_manager": InventoryManagerAgent,
    "pricing_update": PricingUpdateAgent,
    "sales_execution": SalesExecutionAgent,
    "product_creation": ProductCreationAgent,
    "recommendation_execution": RecommendationExecutionAgent,
    "ar_session": ARSessionAgent,
    "anomaly_action": AnomalyActionAgent,
}


class AgentOrchestrator:
    """
    Central orchestrator for AI agents.

    Routes queries to appropriate agents and manages execution.
    """

    def __init__(self, db: Session, claude: Optional[ClaudeService] = None):
        self.db = db
        self.claude = claude or ClaudeService()
        self.agents: Dict[str, Any] = {}

    def _get_agent(self, agent_name: str, dry_run: bool = False):
        """Get or create agent instance."""
        if agent_name not in self.agents:
            agent_class = AGENT_CLASS_MAP.get(agent_name)
            if not agent_class:
                raise ValueError(f"Unknown agent: {agent_name}")
            self.agents[agent_name] = agent_class(self.db, self.claude, dry_run)
        return self.agents[agent_name]

    def _parse_intent(self, query: str) -> Dict[str, Any]:
        """Parse query to determine intent and parameters."""
        parsed = self.claude.parse_natural_language(
            query=query,
            context="Jewelry inventory management system with agents for inventory, pricing, sales, products, recommendations, AR, and anomaly detection.",
            expected_entities=["product", "category", "metal_type", "price", "quantity"],
        )

        # Map parsed intent to agent
        raw_intent = parsed.get("intent", "").lower().replace(" ", "_")

        # Find matching agent
        matched_agent = None
        for intent_key, agent_name in INTENT_AGENT_MAP.items():
            if intent_key in raw_intent or raw_intent in intent_key:
                matched_agent = agent_name
                break

        # Fallback: use Claude to determine best agent
        if not matched_agent:
            situation = f"User query: {query}\n\nAvailable agents: {list(AGENT_CLASS_MAP.keys())}"
            decision = self.claude.generate_decision(
                situation=situation,
                options=list(AGENT_CLASS_MAP.keys()),
                criteria="Select the agent best suited to handle this query",
            )
            matched_agent = decision.get("selected_option", "inventory_manager")

        return {
            "intent": raw_intent,
            "agent": matched_agent,
            "entities": parsed.get("entities", {}),
            "parameters": parsed.get("parameters", {}),
            "confidence": parsed.get("confidence", 0.5),
        }

    def run(
        self,
        query: str,
        dry_run: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute a query through the appropriate agent.

        Args:
            query: Natural language query
            dry_run: Simulate without DB writes
            **kwargs: Additional parameters

        Returns:
            Dict with agent, action_taken, status
        """
        # Parse intent
        intent_data = self._parse_intent(query)
        agent_name = intent_data["agent"]

        # Get agent and execute
        agent = self._get_agent(agent_name, dry_run)

        # Route to agent's run method with appropriate parameters
        result = self._route_to_agent(agent, intent_data, query, kwargs)

        return {
            "agent": agent_name,
            "intent": intent_data["intent"],
            "action_taken": result.message,
            "actions": result.actions,
            "status": "success" if result.success else "error",
            "error": result.error,
            "dry_run": dry_run,
        }

    def _route_to_agent(
        self,
        agent: Any,
        intent_data: Dict[str, Any],
        query: str,
        kwargs: Dict[str, Any],
    ) -> AgentResult:
        """Route to specific agent based on intent."""
        agent_name = intent_data["agent"]
        params = intent_data.get("parameters", {})
        entities = intent_data.get("entities", {})

        if agent_name == "inventory_manager":
            return agent.run(
                check_threshold=params.get("check_threshold", True),
                check_dead_stock=params.get("check_dead_stock", True),
            )

        elif agent_name == "pricing_update":
            return agent.run(
                metal_type=params.get("metal_type") or entities.get("metal_type"),
                threshold_percent=params.get("threshold", 2.0),
                product_ids=params.get("product_ids"),
            )

        elif agent_name == "sales_execution":
            action = params.get("action", "create_sale")
            if "cancel" in query.lower():
                action = "cancel_sale"
            elif "return" in query.lower():
                action = "process_return"

            return agent.run(
                action=action,
                sale_data=params,
                product_ids=params.get("product_ids"),
                customer_data=entities.get("customer"),
                sale_id=params.get("sale_id"),
            )

        elif agent_name == "product_creation":
            return agent.run(
                description=query,
                category=params.get("category"),
            )

        elif agent_name == "recommendation_execution":
            return agent.run(
                product_id=params.get("product_id"),
                category=params.get("category"),
                recommendation_type=params.get("type", "cross_sell"),
                max_recommendations=params.get("max", 5),
            )

        elif agent_name == "ar_session":
            action = params.get("action", "log_session")
            if "analyze" in query.lower():
                action = "analyze_session"
            elif "insight" in query.lower():
                action = "generate_insights"

            return agent.run(
                action=action,
                session_data=params,
                product_id=params.get("product_id"),
                session_id=params.get("session_id"),
            )

        elif agent_name == "anomaly_action":
            action = params.get("action", "detect")
            if "block" in query.lower():
                action = "block"
            elif "flag" in query.lower():
                action = "flag"

            if action == "detect":
                return agent.run(
                    anomaly_type=params.get("type", "all"),
                    entity_id=params.get("entity_id"),
                    time_window_hours=params.get("hours", 24),
                )
            elif action == "block" and params.get("sale_id"):
                return agent.block_transaction(
                    sale_id=params["sale_id"],
                    reason=params.get("reason", "Anomaly detected"),
                )
            elif action == "flag" and params.get("entity_id"):
                return agent.flag_record(
                    entity_type=params.get("entity_type", "unknown"),
                    entity_id=params["entity_id"],
                    reason=params.get("reason", "Flagged for review"),
                    priority=params.get("priority", "normal"),
                )

        # Default fallback
        return AgentResult(
            agent_name=agent_name,
            success=False,
            message=f"Unknown intent for agent {agent_name}",
            error="Could not determine action to take",
        )

    def run_direct(
        self,
        agent_name: str,
        action: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run a specific agent directly (bypass intent parsing).

        Args:
            agent_name: Name of agent to run
            action: Action to perform
            **kwargs: Agent-specific parameters

        Returns:
            Dict with execution results
        """
        agent = self._get_agent(agent_name)
        kwargs["dry_run"] = kwargs.get("dry_run", False)

        if agent_name == "inventory_manager":
            result = agent.run(
                check_threshold=kwargs.get("check_threshold", True),
                check_dead_stock=kwargs.get("check_dead_stock", True),
            )
        elif agent_name == "pricing_update":
            result = agent.run(
                metal_type=kwargs.get("metal_type"),
                threshold_percent=kwargs.get("threshold_percent", 2.0),
            )
        elif agent_name == "sales_execution":
            result = agent.run(
                action=action,
                sale_data=kwargs,
                product_ids=kwargs.get("product_ids"),
                sale_id=kwargs.get("sale_id"),
            )
        elif agent_name == "product_creation":
            result = agent.run(
                description=kwargs.get("description", action),
            )
        elif agent_name == "recommendation_execution":
            result = agent.run(
                product_id=kwargs.get("product_id"),
                recommendation_type=kwargs.get("type", "cross_sell"),
            )
        elif agent_name == "ar_session":
            result = agent.run(
                action=action,
                session_data=kwargs,
                product_id=kwargs.get("product_id"),
            )
        elif agent_name == "anomaly_action":
            result = agent.run(
                anomaly_type=kwargs.get("type", "all"),
            )
        else:
            result = AgentResult(
                agent_name=agent_name,
                success=False,
                message=f"Unknown agent: {agent_name}",
            )

        return {
            "agent": agent_name,
            "action_taken": result.message,
            "actions": [a.to_dict() for a in result.actions],
            "status": "success" if result.success else "error",
            "error": result.error,
            "dry_run": kwargs.get("dry_run", False),
        }

    def list_agents(self) -> List[Dict[str, str]]:
        """List all available agents and their capabilities."""
        return [
            {"name": "inventory_manager", "description": "Manages inventory reordering and dead stock"},
            {"name": "pricing_update", "description": "Updates prices based on metal market changes"},
            {"name": "sales_execution", "description": "Processes sales, returns, and cancellations"},
            {"name": "product_creation", "description": "Creates products from natural language"},
            {"name": "recommendation_execution", "description": "Generates and attaches product recommendations"},
            {"name": "ar_session", "description": "Logs and analyzes AR try-on sessions"},
            {"name": "anomaly_action", "description": "Detects and responds to anomalies"},
        ]
