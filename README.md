# 💎 JewelVault — Inventory Management System with AR Try-On

A **production-ready ERP-style inventory system** built for diamond & jewelry businesses, featuring **AR virtual try-on**, **AI-powered 3D model generation**, and **dynamic metal pricing**.

---

## 🚀 Key Highlights

- 🔥 Full-stack (FastAPI + React + PostgreSQL)
- 🧠 AI-ready architecture (LLM integration ready)
- 🪞 AR Try-On with real-time face tracking
- 📦 Smart inventory + reorder intelligence
- 💰 Live metal price-based pricing engine

---

## 🧩 Features

### 📦 Core Inventory Management
- Product lifecycle management (CRUD + attributes)
- Real-time inventory tracking with transaction logs
- Sales processing with automatic stock updates
- Smart reorder suggestions (velocity-based)
- Natural language queries (AI-ready)
- Feature tagging (bestseller, limited edition, etc.)


### 💰 Metal Price Tracking
- Live gold, silver, platinum prices
- Automatic jewelry price recalculation
- Threshold-based updates
- Historical tracking + audit logs

---

### 👥 User & Company Management
- Multi-tenant system
- Role-based access (Admin / User / SuperAdmin)
- Company-level user management
- Return management

---

## 🏗️ Tech Stack

| Layer | Technology |
|------|------------|
| Backend | FastAPI |
| Frontend | React 18 + Vite |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| API | REST |

---
## 📁 Project Structure

```bash
inventory-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── products.py
│   │   │       ├── inventory.py
│   │   │       ├── sales.py
│   │   │       └── analytics.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── models/
│   │   │   ├── product.py
│   │   │   ├── inventory.py
│   │   │   ├── sale.py
│   │   │   └── reorder.py
│   │   ├── schemas/
│   │   │   ├── product.py
│   │   │   ├── inventory.py
│   │   │   ├── sale.py
│   │   │   ├── reorder.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── product_service.py
│   │   │   ├── inventory_service.py
│   │   │   ├── sale_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── ai_query_service.py
│   │   ├── db/
│   │   │   └── base.py
│   │   ├── utils/
│   │   │   └── exceptions.py
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   │   ├── ProductsPage.jsx
    │   │   ├── InventoryPage.jsx
    │   │   ├── SalesPage.jsx
    │   │   ├── CreateSalePage.jsx
    │   │   └── ReorderSuggestionsPage.jsx
    │   ├── services/
    │   │   └── api.js
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    └── vite.config.js
---
```
## ⚡ Quick Start

### 1️⃣ Database Setup
```bash
createdb inventory_db
```
### 2️⃣ Backend Setup
```bash
cd backend

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env

alembic upgrade head

uvicorn app.main:app --reload --port 8000
```
### 3️⃣ Frontend Setup
```bash
cd frontend

npm install
npm run dev
```
### 🌐 Access
	•	Frontend → http://localhost:3000
	•	API Docs → http://localhost:8000/docs

⸻

### 📡 API Overview

Products
	•	POST /products
	•	GET /products
	•	PUT /products/{id}
	•	DELETE /products/{id}

Inventory
	•	Track stock
	•	Adjust quantities
	•	Transaction logs

Sales
	•	Create / cancel sales
	•	Sales history

Analytics
	•	Reorder suggestions
	•	Sales velocity
	•	Top products
	•	Natural language queries


### 🤖 AI-Ready Architecture
```Prompt
"Show top 10 selling products from last 30 days"
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
## 📸 Screenshots

| Dashboard | Stock |
|----------|-------|
| ![](./dashboard.jpeg) | ![](./stock.jpeg) |

| Sales | AI Agents |
|------|----------|
| ![](./sales.jpeg) | ![](./ai-agents.jpeg) |

| Admin | Returns | Metal |
|------|---------|-------|
| ![](./Admin_mangement.jpeg) | ![](./returns.jpeg) | ![](./metal.jpeg) |
## Scaling to Full ERP

### Phase 1: Vendor Management

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

### Phase 2: Diamond-Specific Attributes

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
