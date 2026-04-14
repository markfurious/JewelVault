"""
Agent API Schemas.
Pydantic models for agent API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent action."""
    query: str = Field(..., description="Natural language query describing the action")
    dry_run: bool = Field(False, description="Simulate without DB writes")
    agent: Optional[str] = Field(None, description="Specific agent to use (optional)")


class AgentDirectRequest(BaseModel):
    """Request to run a specific agent directly."""
    agent: str = Field(..., description="Agent name")
    action: str = Field(..., description="Action to perform")
    dry_run: bool = Field(False, description="Simulate without DB writes")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Agent-specific parameters")


class AgentActionResponse(BaseModel):
    """Single action taken by an agent."""
    action_type: str
    description: str
    entity_type: str
    entity_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class AgentExecuteResponse(BaseModel):
    """Response from agent execution."""
    agent: str
    intent: Optional[str] = None
    action_taken: str
    actions: List[AgentActionResponse] = []
    status: str  # "success" or "error"
    error: Optional[str] = None
    dry_run: bool = False


class AgentListResponse(BaseModel):
    """Response listing available agents."""
    agents: List[Dict[str, str]]


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: str
    agent_name: str
    action_type: str
    description: str
    entity_type: str
    entity_id: Optional[str] = None
    success: bool
    dry_run: bool
    executed_at: str


class AgentHealthResponse(BaseModel):
    """Agent system health check response."""
    status: str
    agents_available: int
    claude_api_connected: bool
    database_connected: bool
