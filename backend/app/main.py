"""
FastAPI Application Entry Point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from pydantic import ValidationError

from app.core.config import settings
from app.api.v1 import (
    products_router,
    inventory_router,
    sales_router,
    analytics_router,
    auth_router,
    stock_router,
    companies_router,
    jewelry_router,
    metal_prices_router,
    agents_router,
    agent_requests_router,
)
from app.utils.exceptions import AppException


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="""
## Inventory Management System API

A production-ready inventory management system designed for diamond and jewelry businesses.

### Features
- **Product Management**: Create, update, and manage products with extensible attributes
- **Inventory Tracking**: Real-time stock levels with transaction history
- **Sales Processing**: Create sales with automatic inventory reduction
- **Smart Reordering**: AI-ready reorder suggestions based on sales velocity

### Architecture
- RESTful API design
- SQLAlchemy ORM with PostgreSQL
- Pydantic validation
- Modular service layer
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(inventory_router, prefix="/api/v1")
    app.include_router(sales_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(stock_router, prefix="/api/v1")
    app.include_router(companies_router, prefix="/api/v1")
    app.include_router(jewelry_router, prefix="/api/v1")
    app.include_router(metal_prices_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(agent_requests_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.APP_NAME}

    @app.get("/", tags=["root"])
    def root():
        """Root endpoint with API information."""
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"detail": [
                {"loc": list(error.get("loc", [])),
                 "msg": str(error.get("msg", "")),
                 "type": str(error.get("type", ""))}
                for error in exc.errors()
            ]},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
