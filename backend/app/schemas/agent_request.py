"""
Agent Request Schemas.
Pydantic models for agent request API.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime


RequestStatus = Literal["pending", "approved", "rejected", "executed"]
RequestType = Literal["reorder", "price_update", "dead_stock_discount",
                      "anomaly_flag", "transaction_block", "product_create", "bulk_update"]


class AgentRequestCreate(BaseModel):
    """Schema for creating an agent request."""
    request_type: RequestType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    agent_name: str = Field(..., min_length=1)
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    request_data: Optional[Dict[str, Any]] = None
    proposed_action: str = Field(..., min_length=1)
    impact_summary: Optional[str] = None


class AgentRequestResponse(BaseModel):
    """Schema for agent request response."""
    id: UUID
    request_type: RequestType
    title: str
    description: str
    agent_name: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    request_data: Optional[Dict[str, Any]]
    proposed_action: str
    impact_summary: Optional[str]
    status: RequestStatus
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    executed_at: Optional[datetime]
    execution_result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentRequestReview(BaseModel):
    """Schema for reviewing an agent request."""
    status: RequestStatus = Field(..., description="APPROVED or REJECTED")
    notes: Optional[str] = Field(None, description="Review notes")
