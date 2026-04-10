"""
Gold Price API routes.
Tracks gold price over time.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from app.api.dependencies import get_db
from app.models.gold_price import GoldPrice
from app.schemas.gold_price import GoldPriceResponse, GoldPriceCreate

router = APIRouter(prefix="/gold", tags=["gold"])


@router.get("/price", response_model=GoldPriceResponse)
def get_gold_price(db: Session = Depends(get_db)):
    """
    Get the current gold price per troy ounce.

    Returns the most recent recorded price.
    """
    latest = db.query(GoldPrice).order_by(GoldPrice.date.desc()).first()

    if not latest:
        # Return a default price if no data exists
        return GoldPriceResponse(
            current_price=2000.00,
            currency="USD",
            unit="troy_ounce",
            last_updated=datetime.utcnow()
        )

    return GoldPriceResponse(
        current_price=float(latest.price),
        currency="USD",
        unit="troy_ounce",
        last_updated=latest.date
    )


@router.get("/history", response_model=List[GoldPriceResponse])
def get_gold_price_history(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get gold price history for the last N days.
    """
    prices = db.query(GoldPrice).order_by(GoldPrice.date.desc()).limit(days).all()

    return [
        GoldPriceResponse(
            current_price=float(p.price),
            currency="USD",
            unit="troy_ounce",
            last_updated=p.date
        )
        for p in prices
    ]


@router.post("/price", response_model=GoldPriceResponse)
def record_gold_price(
    price_data: GoldPriceCreate,
    db: Session = Depends(get_db)
):
    """
    Record a new gold price (for admin/API use).

    This would be called by an external API integration or admin user.
    """
    gold_price = GoldPrice(
        price=Decimal(str(price_data.price)),
        currency=price_data.currency or "USD",
        date=datetime.utcnow()
    )

    db.add(gold_price)
    db.commit()
    db.refresh(gold_price)

    return GoldPriceResponse(
        current_price=float(gold_price.price),
        currency=gold_price.currency,
        unit="troy_ounce",
        last_updated=gold_price.date
    )
