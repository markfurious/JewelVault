"""
AI Agents API Router.
Provides endpoints for executing AI agent actions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.api.dependencies import get_db
from app.agents.agent_orchestrator import AgentOrchestrator
from app.agents.claude_service import ClaudeService
from app.schemas.agent import (
    AgentExecuteRequest,
    AgentDirectRequest,
    AgentExecuteResponse,
    AgentListResponse,
    AuditLogResponse,
    AgentHealthResponse,
    AgentActionResponse,
)
from app.models.agent_audit import AgentAuditLog

router = APIRouter(prefix="/ai", tags=["AI Agents"])


@router.post("/execute", response_model=AgentExecuteResponse)
def execute_agent(
    request: AgentExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Execute an AI agent action based on natural language query.

    Examples:
    - "Restock low inventory products"
    - "Update prices based on gold increase"
    - "Create a 1ct diamond ring in VS1 G color"
    - "Process sale for customer John Doe"
    - "Generate recommendations for necklaces"

    Args:
        request: Execute request with query and dry_run flag

    Returns:
        Execution result with actions taken
    """
    try:
        orchestrator = AgentOrchestrator(db)
        result = orchestrator.run(
            query=request.query,
            dry_run=request.dry_run,
        )

        # Convert actions to response format
        actions = []
        for action in result.get("actions", []):
            if hasattr(action, "to_dict"):
                action_dict = action.to_dict()
            else:
                action_dict = action
            actions.append(AgentActionResponse(**action_dict))

        return AgentExecuteResponse(
            agent=result["agent"],
            intent=result.get("intent"),
            action_taken=result["action_taken"],
            actions=actions,
            status=result["status"],
            error=result.get("error"),
            dry_run=result.get("dry_run", False),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/execute/direct", response_model=AgentExecuteResponse)
def execute_agent_direct(
    request: AgentDirectRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a specific agent directly (bypass intent parsing).

    Use this when you know which agent to use and want direct control.

    Args:
        request: Direct execution request with agent name and action

    Returns:
        Execution result with actions taken
    """
    try:
        orchestrator = AgentOrchestrator(db)
        result = orchestrator.run_direct(
            agent_name=request.agent,
            action=request.action,
            dry_run=request.dry_run,
            **(request.parameters or {}),
        )

        # Convert actions to response format
        actions = []
        for action in result.get("actions", []):
            if hasattr(action, "to_dict"):
                action_dict = action.to_dict()
            else:
                action_dict = action
            actions.append(AgentActionResponse(**action_dict))

        return AgentExecuteResponse(
            agent=result["agent"],
            action_taken=result["action_taken"],
            actions=actions,
            status=result["status"],
            error=result.get("error"),
            dry_run=result.get("dry_run", False),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get("/agents", response_model=AgentListResponse)
def list_agents():
    """List all available agents and their capabilities."""
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    return AgentListResponse(agents=orchestrator.list_agents())


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    db: Session = Depends(get_db),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    days: int = Query(7, description="Number of days of history"),
    limit: int = Query(50, description="Maximum results"),
):
    """Get agent audit logs."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(AgentAuditLog).where(AgentAuditLog.executed_at >= cutoff_date)

    if agent_name:
        query = query.where(AgentAuditLog.agent_name == agent_name)

    if action_type:
        query = query.where(AgentAuditLog.action_type == action_type)

    logs = query.order_by(AgentAuditLog.executed_at.desc()).limit(limit).all()

    return [
        AuditLogResponse(
            id=str(log.id),
            agent_name=log.agent_name,
            action_type=log.action_type,
            description=log.description,
            entity_type=log.entity_type,
            entity_id=str(log.entity_id) if log.entity_id else None,
            success=log.success,
            dry_run=log.dry_run,
            executed_at=log.executed_at.isoformat(),
        )
        for log in logs
    ]


@router.get("/health", response_model=AgentHealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Check agent system health."""
    # Check database connection
    from sqlalchemy import text
    db_connected = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    # Check Claude API
    claude_connected = False
    try:
        claude = ClaudeService()
        claude_connected = claude.api_key is not None
    except Exception:
        pass

    return AgentHealthResponse(
        status="healthy" if db_connected and claude_connected else "degraded",
        agents_available=7,  # Number of agents
        claude_api_connected=claude_connected,
        database_connected=db_connected,
    )
