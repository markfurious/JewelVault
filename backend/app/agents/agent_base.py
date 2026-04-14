"""
Agent Base Class.
Foundation for all action agents in the JewelVault system.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.agents.claude_service import ClaudeService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentAction:
    """Represents an action taken by an agent."""
    action_type: str
    description: str
    entity_type: str
    entity_id: Optional[UUID] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentResult:
    """Result of an agent execution."""
    agent_name: str
    success: bool
    actions: List[AgentAction] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "success": self.success,
            "actions": [a.to_dict() for a in self.actions],
            "message": self.message,
            "error": self.error,
            "dry_run": self.dry_run,
        }


class AgentBase(ABC):
    """
    Abstract base class for all action agents.

    All agents must implement:
    - run(): Main entry point for agent execution
    - decide(): Make decisions based on input
    - act(): Execute actions on the system

    Agents have access to:
    - db: SQLAlchemy session for database operations
    - claude: ClaudeService for LLM capabilities
    - dry_run: Flag to simulate without DB writes
    """

    def __init__(
        self,
        db: Session,
        claude: Optional[ClaudeService] = None,
        dry_run: bool = False,
    ):
        self.db = db
        self.claude = claude or ClaudeService()
        self.dry_run = dry_run
        self.actions: List[AgentAction] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def run(self, **kwargs) -> AgentResult:
        """
        Main entry point for agent execution.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            AgentResult with actions taken
        """
        pass

    @abstractmethod
    def decide(self, **kwargs) -> Dict[str, Any]:
        """
        Make decisions based on input.

        Args:
            **kwargs: Decision parameters

        Returns:
            Decision dict with selected action and reasoning
        """
        pass

    @abstractmethod
    def act(self, decision: Dict[str, Any]) -> List[AgentAction]:
        """
        Execute actions based on decision.

        Args:
            decision: Decision dict from decide()

        Returns:
            List of actions taken
        """
        pass

    def _log_action(
        self,
        action_type: str,
        description: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> AgentAction:
        """Log an action taken by the agent."""
        action = AgentAction(
            action_type=action_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
        )
        self.actions.append(action)

        if self.dry_run:
            self.logger.info(f"[DRY_RUN] {action_type}: {description}")
        else:
            self.logger.info(f"{action_type}: {description}")

        return action

    def _commit_if_not_dry_run(self):
        """Commit database changes if not in dry_run mode."""
        if not self.dry_run:
            self.db.commit()
            self.logger.info("Database changes committed")
        else:
            self.logger.info("Dry run mode - no database changes")
            self.db.rollback()

    def _rollback(self):
        """Rollback database changes."""
        self.db.rollback()
        self.logger.warning("Database changes rolled back")

    def get_name(self) -> str:
        """Get agent name."""
        return self.__class__.__name__

    def _create_result(
        self,
        success: bool,
        message: str,
        error: Optional[str] = None,
    ) -> AgentResult:
        """Create an agent result."""
        return AgentResult(
            agent_name=self.get_name(),
            success=success,
            actions=self.actions,
            message=message,
            error=error,
            dry_run=self.dry_run,
        )
