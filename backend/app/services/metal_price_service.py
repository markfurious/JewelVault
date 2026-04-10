"""
Metal Price Service for fetching and tracking precious metal prices.
Supports automatic jewelry price updates based on market rates.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from decimal import Decimal

import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.metal_price import MetalPrice, JewelryPriceLog
from app.models.jewelry import Jewelry
from app.core.config import settings


class MetalPriceService:
    """Service for metal price operations."""

    def __init__(self, db: Session):
        self.db = db
        # API configuration (using free API, can be upgraded to paid)
        self.api_url = os.environ.get(
            'METAL_PRICE_API_URL',
            'https://api.metalpriceapi.com/v1/latest'  # Free tier available
        )
        self.api_key = os.environ.get('METAL_PRICE_API_KEY', '')

    def fetch_latest_prices(self) -> Dict:
        """
        Fetch latest metal prices from external API.

        Returns dict with metal prices per gram in USD.
        Uses API if available, otherwise returns mock data for testing.
        """
        if self.api_key:
            try:
                response = requests.get(
                    self.api_url,
                    params={
                        'api_key': self.api_key,
                        'base': 'USD',
                        'currencies': 'XAU,XAG,XPT'  # Gold, Silver, Platinum
                    },
                    timeout=10
                )
                data = response.json()

                if data.get('success'):
                    rates = data.get('rates', {})
                    # Convert from per ounce to per gram (1 troy ounce = 31.1035 grams)
                    return {
                        'gold': float(rates.get('XAU', 0)) / 31.1035,
                        'silver': float(rates.get('XAG', 0)) / 31.1035,
                        'platinum': float(rates.get('XPT', 0)) / 31.1035,
                    }
            except Exception as e:
                print(f"Failed to fetch metal prices from API: {e}")

        # Mock data for testing (approximate real-world prices)
        return {
            'gold': 65.50,  # USD per gram
            'silver': 0.78,  # USD per gram
            'platinum': 32.20,  # USD per gram
        }

    def save_price(self, metal_type: str, price_per_gram: float, source: str = 'api') -> MetalPrice:
        """
        Save a metal price to the database.

        Args:
            metal_type: 'gold', 'silver', or 'platinum'
            price_per_gram: Price in USD per gram
            source: Source of the price data

        Returns:
            Created MetalPrice instance
        """
        metal_price = MetalPrice(
            metal_type=metal_type.lower(),
            price_per_gram=Decimal(str(price_per_gram)),
            currency='USD',
            unit='gram',
            source=source
        )
        self.db.add(metal_price)
        self.db.commit()
        self.db.refresh(metal_price)
        return metal_price

    def update_all_prices(self) -> Dict:
        """
        Fetch and save prices for all metals.

        Returns:
            Dict with saved prices and changes
        """
        prices = self.fetch_latest_prices()
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'prices': {},
            'changes': {}
        }

        for metal_type, price in prices.items():
            # Get previous price
            previous = self.db.query(MetalPrice).filter(
                MetalPrice.metal_type == metal_type
            ).order_by(desc(MetalPrice.created_at)).first()

            # Save new price
            self.save_price(metal_type, price)

            # Calculate change
            if previous and previous.price_per_gram > 0:
                change = ((Decimal(str(price)) - previous.price_per_gram) / previous.price_per_gram) * 100
                result['changes'][metal_type] = float(change)
            else:
                result['changes'][metal_type] = 0

            result['prices'][metal_type] = {
                'price_per_gram': price,
                'currency': 'USD',
                'previous_price': float(previous.price_per_gram) if previous else None,
                'change_percent': result['changes'][metal_type]
            }

        return result

    def get_latest_price(self, metal_type: str) -> Optional[Decimal]:
        """
        Get the latest price for a metal type.

        Args:
            metal_type: 'gold', 'silver', or 'platinum'

        Returns:
            Latest price per gram or None if not found
        """
        price = self.db.query(MetalPrice).filter(
            MetalPrice.metal_type == metal_type.lower()
        ).order_by(desc(MetalPrice.created_at)).first()

        return price.price_per_gram if price else None

    def get_price_history(
        self,
        metal_type: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Get price history for a metal type.

        Args:
            metal_type: 'gold', 'silver', or 'platinum'
            days: Number of days of history

        Returns:
            List of price records with timestamps
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        prices = self.db.query(MetalPrice).filter(
            MetalPrice.metal_type == metal_type.lower(),
            MetalPrice.created_at >= cutoff_date
        ).order_by(MetalPrice.created_at.desc()).limit(100).all()

        return [
            {
                'price_per_gram': float(p.price_per_gram),
                'created_at': p.created_at.isoformat(),
                'source': p.source
            }
            for p in prices
        ]

    def log_price_change(
        self,
        jewelry_id: str,
        old_price: float,
        new_price: float,
        reason: str,
        metal_type: str = None,
        metal_price_change: float = None
    ) -> JewelryPriceLog:
        """
        Log a jewelry price change.

        Args:
            jewelry_id: UUID of the jewelry item
            old_price: Previous price
            new_price: New price
            reason: Reason for the change
            metal_type: Which metal triggered the change
            metal_price_change: Percentage change in metal price

        Returns:
            Created JewelryPriceLog instance
        """
        log = JewelryPriceLog(
            jewelry_id=jewelry_id,
            old_price=Decimal(str(old_price)),
            new_price=Decimal(str(new_price)),
            reason=reason,
            metal_type=metal_type,
            metal_price_change=Decimal(str(metal_price_change)) if metal_price_change else None
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def update_jewelry_prices(
        self,
        metal_type: str,
        threshold_percent: float = 5.0
    ) -> Dict:
        """
        Update jewelry prices based on metal price changes.

        Only updates if metal price changed by more than threshold.

        Args:
            metal_type: 'gold', 'silver', or 'platinum'
            threshold_percent: Minimum change percent to trigger update

        Returns:
            Dict with update results
        """
        # Get latest metal price and previous price
        latest = self.db.query(MetalPrice).filter(
            MetalPrice.metal_type == metal_type.lower()
        ).order_by(desc(MetalPrice.created_at)).limit(2).all()

        if len(latest) < 2:
            return {'updated': 0, 'reason': 'Not enough price history'}

        current_price = latest[0].price_per_gram
        previous_price = latest[1].price_per_gram

        if previous_price == 0:
            return {'updated': 0, 'reason': 'Previous price is zero'}

        # Calculate percentage change
        change_percent = ((current_price - previous_price) / previous_price) * 100

        if abs(change_percent) < threshold_percent:
            return {
                'updated': 0,
                'reason': f'Change {change_percent:.2f}% below threshold {threshold_percent}%'
            }

        # Update jewelry prices for this metal type
        # Map metal type to jewelry types
        metal_to_jewelry = {
            'gold': ['ring', 'necklace'],  # Simplified mapping
            'silver': ['ring', 'necklace', 'earring'],
            'platinum': ['ring', 'necklace']
        }

        jewelry_types = metal_to_jewelry.get(metal_type.lower(), [])
        if not jewelry_types:
            return {'updated': 0, 'reason': 'No jewelry types mapped to this metal'}

        # Get all jewelry of relevant types
        jewelry_items = self.db.query(Jewelry).filter(
            Jewelry.type.in_(jewelry_types),
            Jewelry.is_active == 'true'
        ).all()

        updated_count = 0
        for item in jewelry_items:
            old_price = float(item.price)
            # Adjust price based on metal price change
            new_price = old_price * (1 + change_percent / 100)

            # Update price
            item.price = Decimal(str(round(new_price, 2)))
            updated_count += 1

            # Log the change
            self.log_price_change(
                jewelry_id=str(item.id),
                old_price=old_price,
                new_price=float(new_price),
                reason=f'{metal_type.capitalize()} price {"increased" if change_percent > 0 else "decreased"} by {abs(change_percent):.2f}%',
                metal_type=metal_type,
                metal_price_change=float(change_percent)
            )

        self.db.commit()

        return {
            'updated': updated_count,
            'metal_type': metal_type,
            'change_percent': float(change_percent),
            'threshold': threshold_percent
        }
