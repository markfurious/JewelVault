"""
Agent Request Model.
Stores agent-generated requests that require admin review/approval.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base import Base


class AgentRequest(Base):
    """
    Agent-generated request requiring admin review.

    Use cases:
    - Large price changes (>10%)
    - High-value transaction blocks
    - Bulk inventory reorders
    - Anomaly flags needing investigation
    """

    __tablename__ = "agent_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Request identification (using String instead of Enum for simplicity)
    request_type = Column(String(50), nullable=False)  # reorder, price_update, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Agent that created the request
    agent_name = Column(String(255), nullable=False)

    # Target entity
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Request details (JSON for flexibility)
    request_data = Column(JSONB, nullable=True)

    # Proposed action
    proposed_action = Column(Text, nullable=False)
    impact_summary = Column(Text, nullable=True)

    # Status tracking (using String instead of Enum)
    status = Column(
        String(20),
        nullable=False,
        default="pending",  # pending, approved, rejected, executed
        index=True,
    )

    # Review tracking
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Execution tracking
    executed_at = Column(DateTime, nullable=True)
    execution_result = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationship to reviewer
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<AgentRequest {self.request_type}: {self.title} ({self.status})>"
