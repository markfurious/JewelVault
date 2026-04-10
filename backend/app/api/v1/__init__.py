"""API v1 module - All version 1 API routes."""
from app.api.v1.products import router as products_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.sales import router as sales_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.stock import router as stock_router
from app.api.v1.companies import router as companies_router
from app.api.v1.jewelry import router as jewelry_router
from app.api.v1.metal_prices import router as metal_prices_router

__all__ = [
    "products_router",
    "inventory_router",
    "sales_router",
    "analytics_router",
    "auth_router",
    "stock_router",
    "companies_router",
    "jewelry_router",
    "metal_prices_router",
]
