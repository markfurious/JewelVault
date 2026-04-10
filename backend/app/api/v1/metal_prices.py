"""
Metal Prices API routes for tracking and updating precious metal prices.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.api.dependencies import get_db
from app.services.metal_price_service import MetalPriceService

router = APIRouter(prefix="/metal-prices", tags=["metal-prices"])


@router.get("/latest")
def get_latest_prices(
    metal_type: Optional[str] = Query(None, description="Filter by metal: gold, silver, platinum"),
    db: Session = Depends(get_db),
):
    """
    Get latest metal prices.

    - **metal_type**: Optional filter by specific metal
    """
    service = MetalPriceService(db)

    if metal_type:
        price = service.get_latest_price(metal_type)
        if price is None:
            raise HTTPException(status_code=404, detail=f"No price found for {metal_type}")
        return {
            'metal_type': metal_type,
            'price_per_gram': float(price),
            'currency': 'USD'
        }

    # Get all latest prices
    results = {}
    for metal in ['gold', 'silver', 'platinum']:
        price = service.get_latest_price(metal)
        if price:
            results[metal] = {
                'price_per_gram': float(price),
                'currency': 'USD'
            }

    return results


@router.post("/update")
def update_prices(db: Session = Depends(get_db)):
    """
    Fetch and save latest metal prices from external API.

    Returns updated prices with percentage changes from previous prices.
    """
    service = MetalPriceService(db)
    return service.update_all_prices()


@router.get("/history/{metal_type}")
def get_price_history(
    metal_type: str,
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db),
):
    """
    Get price history for a metal type.

    - **metal_type**: gold, silver, or platinum
    - **days**: Number of days of history (1-365)
    """
    if metal_type.lower() not in ['gold', 'silver', 'platinum']:
        raise HTTPException(
            status_code=400,
            detail="Invalid metal type. Must be gold, silver, or platinum"
        )

    service = MetalPriceService(db)
    return {
        'metal_type': metal_type,
        'days': days,
        'history': service.get_price_history(metal_type, days)
    }


@router.post("/update-jewelry-prices")
def update_jewelry_prices(
    metal_type: str = Query(..., description="Metal type: gold, silver, platinum"),
    threshold: float = Query(5.0, ge=0, description="Minimum change percent to trigger update"),
    db: Session = Depends(get_db),
):
    """
    Update jewelry prices based on metal price changes.

    Only updates if metal price changed by more than threshold percent.

    - **metal_type**: Which metal's price change triggers the update
    - **threshold**: Minimum percentage change (default 5%)
    """
    if metal_type.lower() not in ['gold', 'silver', 'platinum']:
        raise HTTPException(
            status_code=400,
            detail="Invalid metal type. Must be gold, silver, or platinum"
        )

    service = MetalPriceService(db)
    result = service.update_jewelry_prices(metal_type.lower(), threshold)

    return result


@router.get("/stats")
def get_price_stats(db: Session = Depends(get_db)):
    """
    Get metal price statistics and trends.

    Returns current prices, 24h change, and 7-day average.
    """
    service = MetalPriceService(db)
    results = {}

    for metal in ['gold', 'silver', 'platinum']:
        latest = service.get_latest_price(metal)
        history = service.get_price_history(metal, days=7)

        if latest and history:
            # Calculate 7-day average
            avg_price = sum(h['price_per_gram'] for h in history) / len(history)

            # Calculate 24h change (compare latest to oldest in history)
            if len(history) > 1:
                oldest = history[-1]['price_per_gram']
                change_24h = ((latest - oldest) / oldest) * 100 if oldest > 0 else 0
            else:
                change_24h = 0

            results[metal] = {
                'current_price': float(latest),
                'currency': 'USD',
                'unit': 'gram',
                'avg_7d': avg_price,
                'change_24h_percent': float(change_24h)
            }

    return results
