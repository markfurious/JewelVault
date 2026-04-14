"""
Agent Audit Log Model.
Tracks all actions taken by AI agents for accountability and debugging.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base import Base


class AgentAuditLog(Base):
    """
    Audit log for agent actions.

    Records:
    - Which agent took action
    - What action was taken
    - On which entity
    - Result of the action
    - Whether it was a dry run
    """

    __tablename__ = "agent_audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Agent identification
    agent_name = Column(String(255), nullable=False, index=True)

    # Action details
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    # Target entity
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Additional data (JSON for flexibility)
    action_data = Column(JSONB, nullable=True)

    # Result
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    # Execution mode
    dry_run = Column(Boolean, nullable=False, default=False)

    # Timestamps
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Optional reference to related records
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_type = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<AgentAuditLog {self.agent_name}: {self.action_type} at {self.executed_at}>"
