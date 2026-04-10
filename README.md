# JewelVault - Inventory Management System with AR Try-On

A production-ready inventory management system designed for diamond and jewelry businesses, featuring AR virtual try-on, AI-powered 3D model generation, and metal price tracking.

## Features

### Core Inventory Management
- **Product Management**: Create, update, and manage products with extensible attributes (diamond cut, clarity, carat, certification)
- **Inventory Tracking**: Real-time stock levels with complete transaction history
- **Sales Processing**: Point-of-sale functionality with automatic inventory reduction
- **Smart Reordering**: AI-ready reorder suggestions based on sales velocity analysis
- **Natural Language Queries**: Rule-based query parsing ready for LLM integration
- **Feature Tags**: Mark products with special tags (bestseller, new_arrival, handcrafted, limited_edition, etc.)

### AR Virtual Try-On
- **3D Model Rendering**: Three.js-based AR viewer for jewelry visualization
- **Face Tracking**: MediaPipe Face Mesh for accurate earring placement
- **Real-time Overlay**: Live camera feed with 3D jewelry overlay
- **Session Logging**: Track try-on sessions for analytics
- **Screenshot Capture**: Save try-on moments

### 3D Model Generation
- **Batch Processing**: Generate 3D models from Excel spreadsheet with S3/HTTP URLs
- **Excel Template**: Downloadable template with required format
- **Image Download**: Automatic image fetching from S3 or any HTTP URL
- **TripoSR Integration**: Self-hosted 3D model generation (GPU-accelerated)
- **SKU Validation**: Enforce "SI" prefix for all SKUs (e.g., SI-001)
- **Mandatory Fields**: Enforce required fields (SKU, name, description, image)

### Metal Price Tracking
- **Live Price Updates**: Fetch gold, silver, and platinum prices from market APIs
- **Automatic Jewelry Pricing**: Update jewelry prices based on metal price changes
- **Threshold-Based Updates**: Configure percentage threshold for price updates
- **Price History**: Track and view historical metal prices
- **Price Audit Log**: Maintain logs of all jewelry price changes

### User & Company Management
- **Multi-Company Support**: Manage multiple companies/organizations
- **Role-Based Access**: SuperAdmin, Admin, and User roles
- **User Management**: Create and manage user accounts per company
- **Return Management**: Admin interface for handling product returns

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 + Alembic |
| Validation | Pydantic v2 |
| Frontend | React 18 + Vite |
| API Style | REST |

## Project Structure

```
inventory-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── products.py      # Product endpoints
│   │   │       ├── inventory.py     # Inventory endpoints
│   │   │       ├── sales.py         # Sales endpoints
│   │   │       └── analytics.py     # Analytics & AI query endpoints
│   │   ├── core/
│   │   │   └── config.py            # Application settings
│   │   ├── models/
│   │   │   ├── product.py           # Product model
│   │   │   ├── inventory.py         # Inventory & transactions
│   │   │   ├── sale.py              # Sales models
│   │   │   └── reorder.py           # Reorder rules
│   │   ├── schemas/
│   │   │   ├── product.py           # Product Pydantic schemas
│   │   │   ├── inventory.py         # Inventory schemas
│   │   │   ├── sale.py              # Sales schemas
│   │   │   ├── reorder.py           # Reorder schemas
│   │   │   └── analytics.py         # Analytics/AI schemas
│   │   ├── services/
│   │   │   ├── product_service.py   # Product business logic
│   │   │   ├── inventory_service.py # Inventory operations
│   │   │   ├── sale_service.py      # Sales processing
│   │   │   ├── analytics_service.py # Analytics & reporting
│   │   │   └── ai_query_service.py  # NL query parsing (AI-ready)
│   │   ├── db/
│   │   │   └── base.py              # DB session & base model
│   │   ├── utils/
│   │   │   └── exceptions.py        # Custom exceptions
│   │   └── main.py                  # FastAPI app entry point
│   ├── alembic/
│   │   └── versions/                # Database migrations
│   ├── alembic.ini                  # Alembic configuration
│   └── requirements.txt             # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/              # Reusable components
    │   ├── pages/
    │   │   ├── ProductsPage.jsx     # Product list & create
    │   │   ├── InventoryPage.jsx    # Inventory management
    │   │   ├── SalesPage.jsx        # Sales history
    │   │   ├── CreateSalePage.jsx   # New sale form
    │   │   └── ReorderSuggestionsPage.jsx # Smart reordering
    │   ├── services/
    │   │   └── api.js               # API client
    │   ├── App.jsx                  # Main app component
    │   ├── main.jsx                 # React entry point
    │   └── index.css                # Global styles
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js 18+

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb inventory_db
# Or via psql:
# psql -c "CREATE DATABASE inventory_db;"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and set your DATABASE_URL
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/inventory_db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products` | Create product |
| GET | `/api/v1/products` | List products |
| GET | `/api/v1/products/{id}` | Get product |
| GET | `/api/v1/products/sku/{sku}` | Get by SKU |
| PUT | `/api/v1/products/{id}` | Update product |
| DELETE | `/api/v1/products/{id}` | Soft delete |

### Inventory

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory` | List all inventory |
| GET | `/api/v1/inventory/{id}` | Get product inventory |
| PUT | `/api/v1/inventory/{id}` | Update quantity |
| POST | `/api/v1/inventory/{id}/adjust` | Delta adjustment |
| POST | `/api/v1/inventory/{id}/restock` | Restock shortcut |
| GET | `/api/v1/inventory/{id}/transactions` | Transaction history |

### Sales

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sales` | Create sale |
| GET | `/api/v1/sales` | List sales |
| GET | `/api/v1/sales/{id}` | Get sale details |
| POST | `/api/v1/sales/{id}/cancel` | Cancel sale |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/reorder-suggestions` | Smart reorder list |
| GET | `/api/v1/analytics/sales-velocity` | Velocity report |
| GET | `/api/v1/analytics/inventory/summary` | Inventory summary |
| GET | `/api/v1/analytics/top-products` | Top sellers |
| POST | `/api/v1/analytics/query` | Natural language query |

## Database Schema

### Core Tables

```
products
├── id (UUID, PK)
├── sku (String, unique)
├── name (String)
├── category (String, indexed)
├── cost_price, retail_price, wholesale_price (Numeric)
├── attributes (JSONB) - extensible for diamond properties
├── default_reorder_threshold (Numeric)
└── timestamps

inventory
├── id (UUID, PK)
├── product_id (UUID, FK)
├── quantity (Numeric)
├── reserved_quantity (Numeric)
├── location, warehouse_code (String)
└── timestamps

inventory_transactions
├── id (UUID, PK)
├── inventory_id (UUID, FK)
├── transaction_type (String)
├── quantity_change, quantity_before, quantity_after (Numeric)
├── reference_id, reference_type (for tracking source)
└── timestamps

sales
├── id (UUID, PK)
├── sale_number (String, unique)
├── customer_name, customer_email, customer_phone
├── sale_type (RETAIL/WHOLESALE/ONLINE)
├── subtotal, tax_amount, discount_amount, total_amount (Numeric)
├── payment_method, payment_status, status
└── timestamps

sale_items
├── id (UUID, PK)
├── sale_id (UUID, FK)
├── product_id (UUID, FK)
├── product_name, product_sku (snapshot)
├── quantity, unit_price, subtotal (Numeric)
└── timestamps

reorder_rules
├── id (UUID, PK)
├── product_id (UUID, FK, unique)
├── min_threshold, target_stock (Numeric)
├── velocity_days, velocity_multiplier (Numeric)
├── preferred_supplier, supplier_lead_time_days
└── timestamps
```

## Smart Reorder System

The reorder suggestion algorithm considers:

1. **Stock Level vs Threshold**: Flags products below minimum threshold as urgent
2. **Sales Velocity**: Calculates average daily sales over configurable period
3. **Fast-Moving Detection**: Identifies products selling >1 unit/day
4. **Stockout Prediction**: Estimates days until stockout
5. **Smart Quantity Calculation**:
   ```
   reorder_qty = (target_stock - current_stock) + (daily_velocity × multiplier × 7)
   ```

### Example Response

```json
{
  "product_id": "uuid",
  "product_name": "1ct Round Brilliant",
  "product_sku": "DIA-1CT-RB-VS1",
  "current_stock": 3,
  "min_threshold": 5,
  "target_stock": 25,
  "sales_velocity": 0.5,
  "is_urgent": true,
  "is_fast_moving": false,
  "recommended_reorder_quantity": 25.5,
  "estimated_days_until_stockout": 6
}
```

## AI-Ready Architecture

### Natural Language Query Interface

The `AIQueryService` provides an interface for converting natural language to structured queries:

```python
# Example usage
service = AIQueryService()
response = service.parse_query("Show top 10 selling products from last 30 days")

# Returns structured query:
{
  "query_type": "AGGREGATE",
  "target_entity": "sales",
  "aggregations": ["sum", "count"],
  "order_by": "desc",
  "limit": 10,
  "time_range": {"period": "30 days"}
}
```

### Extension Points for LLM Integration

1. **`ai_query_service.py`**: Replace rule-based parsing with LLM calls
2. **Prompt Template**: Define structured output schema for the LLM
3. **Query Execution**: Map structured queries to SQLAlchemy queries
4. **Caching**: Implement query result caching for common questions

## Scaling to Full ERP

### Phase 1: Multi-Store Inventory

```python
# Add to Inventory model
class Inventory(Base):
    store_id = Column(UUID, ForeignKey('stores.id'))
    warehouse_id = Column(UUID, ForeignKey('warehouses.id'))
    transfer_history = relationship('StockTransfer')

# New tables
class Store(Base):
    id = Column(UUID, PK)
    name = Column(String)
    location = Column(String)
    is_active = Column(Boolean)

class StockTransfer(Base):
    id = Column(UUID, PK)
    from_store_id = Column(UUID, ForeignKey('stores.id'))
    to_store_id = Column(UUID, ForeignKey('stores.id'))
    product_id = Column(UUID, ForeignKey('products.id'))
    quantity = Column(Numeric)
    status = Column(String)  # PENDING, IN_TRANSIT, COMPLETED
```

### Phase 2: Vendor Management

```python
class Vendor(Base):
    id = Column(UUID, PK)
    name = Column(String)
    contact_email = Column(String)
    payment_terms = Column(String)
    lead_time_days = Column(Integer)

class PurchaseOrder(Base):
    id = Column(UUID, PK)
    vendor_id = Column(UUID, ForeignKey('vendors.id'))
    items = relationship('PurchaseOrderItem')
    status = Column(String)  # DRAFT, SENT, PARTIAL, RECEIVED
    expected_date = Column(DateTime)
```

### Phase 3: Diamond-Specific Attributes

```python
# Extend Product.attributes with structured schema
class DiamondAttributes(TypedDict):
    # 4Cs
    carat: float
    cut: str  # EXCELLENT, VERY_GOOD, GOOD, FAIR
    color: str  # D-Z scale
    clarity: str  # FL, IF, VVS1, VVS2, VS1, VS2, SI1, SI2, I1, I2, I3

    # Certifications
    certification: str  # GIA, AGS, EGL, IGI, NONE
    certificate_number: str

    # Additional
    shape: str  # ROUND, PRINCESS, OVAL, MARQUISE, etc.
    fluorescence: str
    measurements: Dict[str, float]  # length, width, depth
    table_percentage: float
    depth_percentage: float
```

## AI Roadmap

### 1. Talk to Your Database (Natural Language Interface)

```python
# Future implementation with LLM
class AIQueryService:
    async def parse_with_llm(self, query: str) -> StructuredQuery:
        # Use Claude/OpenAI to parse natural language
        response = await llm.chat.completions.create(
            model="claude-sonnet-4-6",
            messages=[
                {"role": "system", "content": QUERY_PARSER_PROMPT},
                {"role": "user", "content": query}
            ]
        )
        return parse_structured_response(response)

    async def execute_and_explain(self, structured_query: StructuredQuery) -> dict:
        # Execute query and generate natural language summary
        results = await self.execute(structured_query)
        explanation = await llm.generate_summary(results)
        return {"data": results, "explanation": explanation}
```

### 2. Sales Prediction

```python
class SalesForecastService:
    def forecast_demand(
        self,
        product_id: UUID,
        days_ahead: int = 30,
        include_seasonality: bool = True
    ) -> ForecastResult:
        """
        Predict future sales using:
        - Historical velocity
        - Trend analysis
        - Seasonal patterns (if enabled)
        - External factors (holidays, events)
        """
        pass
```

### 3. Inventory Optimization

```python
class InventoryOptimizationService:
    def optimize_stock_levels(self) -> List[OptimizationRecommendation]:
        """
        ML-based optimization considering:
        - Demand variability
        - Supplier lead times
        - Holding costs
        - Stockout costs
        - Service level targets
        """
        pass

    def calculate_safety_stock(
        self,
        product_id: UUID,
        service_level: float = 0.95
    ) -> float:
        """Calculate optimal safety stock using statistical methods."""
        pass
```

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Style

```bash
# Backend
black app/
isort app/
flake8 app/

# Frontend
npm run lint
```

### Database Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `APP_NAME` | Application name | Inventory Management System |
| `DEBUG` | Enable debug mode | true |
| `SECRET_KEY` | Secret key for sessions | Required in production |
| `ALLOWED_ORIGINS` | CORS allowed origins | http://localhost:3000 |

## License

MIT
# Inventory-Resource-Planner
