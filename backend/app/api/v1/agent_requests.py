"""
Agent Requests API Router.
Endpoints for reviewing and approving agent-generated requests.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api.dependencies import get_db, require_admin
from app.models.user import User
from app.models.agent_request import AgentRequest
from app.schemas.agent_request import (
    AgentRequestCreate,
    AgentRequestResponse,
    AgentRequestReview,
)

router = APIRouter(prefix="/agent-requests", tags=["Agent Requests"])


@router.get("", response_model=List[AgentRequestResponse])
def list_agent_requests(
    status: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List agent requests with filters."""
    query = db.query(AgentRequest)

    if status:
        query = query.filter(AgentRequest.status == status)
    if request_type:
        query = query.filter(AgentRequest.request_type == request_type)
    if agent_name:
        query = query.filter(AgentRequest.agent_name == agent_name)

    requests = query.order_by(AgentRequest.created_at.desc()).offset(skip).limit(limit).all()

    return requests


@router.get("/pending", response_model=List[AgentRequestResponse])
def list_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get all pending requests awaiting review."""
    return db.query(AgentRequest).filter(
        AgentRequest.status == "pending"
    ).order_by(AgentRequest.created_at.desc()).all()


@router.get("/{request_id}", response_model=AgentRequestResponse)
def get_agent_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a specific agent request by ID."""
    request = db.query(AgentRequest).filter(AgentRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.post("", response_model=AgentRequestResponse, status_code=201)
def create_agent_request(
    request_data: AgentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new agent request (typically called by agents)."""
    request = AgentRequest(**request_data.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.post("/{request_id}/review", response_model=AgentRequestResponse)
def review_agent_request(
    request_id: UUID,
    review_data: AgentRequestReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Review and approve/reject an agent request."""
    request = db.query(AgentRequest).filter(AgentRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Request is already {request.status}",
        )

    # Update review fields
    request.status = review_data.status
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    request.review_notes = review_data.notes

    if review_data.status == "approved":
        # Execute the proposed action
        execution_result = _execute_request(db, request)
        request.status = "executed"
        request.executed_at = datetime.utcnow()
        request.execution_result = execution_result

    db.commit()
    db.refresh(request)
    return request


def _execute_request(db: Session, request: AgentRequest) -> dict:
    """Execute the proposed action from a request."""
    from app.services.product_service import ProductService
    from app.models.product import Product

    request_type = request.request_type
    data = request.request_data or {}

    try:
        if request_type == "reorder":
            # Create reorder record (would integrate with reorder service)
            return {"action": "reorder_created", "product_id": str(data.get("product_id"))}

        elif request_type == "price_update":
            # Update product price
            product_id = data.get("product_id")
            new_price = data.get("new_price")
            if product_id and new_price:
                db.execute(
                    "UPDATE products SET retail_price = :price WHERE id = :id",
                    {"price": new_price, "id": product_id}
                )
                db.commit()
                return {"action": "price_updated", "product_id": str(product_id), "new_price": new_price}

        elif request_type == "dead_stock_discount":
            # Apply discount to product
            product_id = data.get("product_id")
            discount_percent = data.get("discount_percent", 0.15)
            if product_id:
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    new_price = float(product.retail_price) * (1 - discount_percent)
                    product.retail_price = new_price
                    db.commit()
                    return {"action": "discount_applied", "product_id": str(product_id), "new_price": new_price}

        elif request_type == "transaction_block":
            # Keep transaction blocked (status already set)
            return {"action": "transaction_blocked", "sale_id": str(data.get("sale_id"))}

        elif request_type == "product_create":
            # Product would have been created in draft, now activate
            product_id = data.get("product_id")
            if product_id:
                return {"action": "product_activated", "product_id": str(product_id)}

        elif request_type == "bulk_update":
            # Execute bulk operation
            return {"action": "bulk_update_executed", "count": data.get("count", 0)}

        return {"action": "unknown_type", "type": request_type}

    except Exception as e:
        return {"error": str(e)}
