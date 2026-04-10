# Inventory / Jewelry ERP System - Architecture Documentation

**Version:** 1.0.0
**Last Updated:** March 31, 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Diagram](#architecture-diagram)
4. [Backend Structure](#backend-structure)
5. [Frontend Structure](#frontend-structure)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Item-Based Inventory Model](#item-based-inventory-model)
9. [Data Flow Examples](#data-flow-examples)
10. [Authentication](#authentication)
11. [Bulk Upload](#bulk-upload)
12. [Running the System](#running-the-system)

---

## System Overview

A production-ready ERP system designed for diamond and jewelry businesses featuring:

- **Item-based inventory tracking** - Each SKU represents ONE physical item
- **Status-based tracking** - AVAILABLE / SOLD / RESERVED (no quantity fields)
- **Jewelry-specific attributes** - Carat, gold purity, certification, etc.
- **Sales processing** - Automatic status updates on sale
- **Smart analytics** - Reorder suggestions based on sales velocity
- **Bulk operations** - Excel upload for product import
- **User management** - Role-based access control

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | UI rendering, state management |
| **Grid** | AG Grid v35 | Tabular data display |
| **Backend** | FastAPI | RESTful API server |
| **Validation** | Pydantic | Request/response schemas |
| **ORM** | SQLAlchemy 2.0 | Database mapping |
| **Database** | PostgreSQL | Data persistence |
| **Migrations** | Alembic | Schema versioning |
| **Auth** | JWT + bcrypt | Token authentication |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                             │
│               http://localhost:3002                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              REACT FRONTEND (Vite)                          │
│  Pages | Components | Services | Context | AG Grid          │
└────────────────────┬────────────────────────────────────────┘
                     │ Proxy: /api/* → localhost:8000
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             FASTAPI BACKEND (uvicorn)                       │
│  API Routers | Services | Models | Schemas                  │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLAlchemy
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL DATABASE                            │
│  products | inventory | sales | users | transactions        │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory
│   ├── api/
│   │   └── v1/
│   │       ├── products.py        # Product CRUD + bulk upload
│   │       ├── inventory.py       # Status adjustments
│   │       ├── sales.py           # Sale transactions
│   │       ├── stock.py           # Combined grid endpoint
│   │       ├── analytics.py       # Reorder suggestions
│   │       └── auth.py            # User management
│   ├── models/
│   │   ├── product.py             # Product table
│   │   ├── inventory.py           # Inventory + Transactions
│   │   ├── sale.py                # Sales + SaleItems
│   │   ├── user.py                # User authentication
│   │   └── reorder.py             # Reorder rules
│   ├── schemas/
│   │   ├── product.py             # ProductCreate, ProductUpdate
│   │   ├── inventory.py           # InventoryResponse
│   │   ├── sale.py                # SaleCreate, SaleItemCreate
│   │   └── auth.py                # Login, User schemas
│   ├── services/
│   │   ├── product_service.py     # Product CRUD
│   │   ├── inventory_service.py   # Status management
│   │   ├── sale_service.py        # Sale processing
│   │   ├── analytics_service.py   # Business intelligence
│   │   └── auth_service.py        # Authentication
│   ├── db/
│   │   └── base.py                # Engine, session, Base
│   ├── core/
│   │   └── config.py              # Settings
│   └── utils/
│       ├── exceptions.py          # Custom exceptions
│       └── sku_generator.py       # SKU generation
└── alembic/
    └── versions/
        ├── 001_initial_migration.py
        ├── 002_add_reorder_rules.py
        ├── 003_add_sales.py
        └── 004_convert_to_item_based.py
```

### Service Layer Responsibilities

| Service | Key Methods | Responsibility |
|---------|-------------|----------------|
| ProductService | create(), update(), delete() | Product CRUD, SKU generation |
| ProductBulkService | process_upload() | Excel file processing |
| InventoryService | mark_sold(), reserve(), adjust_status() | Status changes, logging |
| SaleService | create(), cancel() | Sale creation with validation |
| AnalyticsService | get_reorder_suggestions() | Business intelligence |
| AuthService | authenticate(), create_user() | JWT auth, user management |

---

## Frontend Structure

```
frontend/
├── src/
│   ├── main.jsx                   # Entry point
│   ├── App.jsx                    # Routing
│   ├── pages/
│   │   ├── DashboardPage.jsx      # Overview statistics
│   │   ├── StockPage.jsx          # Main stock grid
│   │   ├── ProductsPage.jsx       # Product management
│   │   ├── InventoryPage.jsx      # Status adjustments
│   │   ├── SalesPage.jsx          # Sales history
│   │   ├── CreateSalePage.jsx     # New sale form
│   │   ├── ReorderSuggestionsPage.jsx  # Smart suggestions
│   │   ├── LoginPage.jsx          # Authentication
│   │   └── AdminUsersPage.jsx     # User management
│   ├── components/
│   │   ├── Layout.jsx             # Main layout
│   │   └── BulkUploadModal.jsx    # Excel upload
│   ├── services/
│   │   └── api.js                 # API client
│   └── context/
│       └── AuthContext.jsx        # Auth state
├── vite.config.js
└── package.json
```

### API Service Modules

```javascript
// services/api.js exports:
- productsApi      // Product CRUD
- inventoryApi     // Status management
- salesApi         // Sale transactions
- analyticsApi     // Business intelligence
- stockApi         // Combined data
- authApi          // Authentication
```

---

## Database Schema

### Entity Relationship

```
Product (1) ────── (1) Inventory
   │                    │
   │                    │ (1:N)
   │                    ▼
   │              InventoryTransaction
   │
   │ (1:N)
   ▼
SaleItem (N) ────── (1) Sale
```

### Key Tables

#### products

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sku | VARCHAR(20) | Stock keeping unit (unique) |
| name | VARCHAR(255) | Product name |
| category | VARCHAR(100) | Product category |
| style_number | VARCHAR(50) | Jewelry style number |
| st_carat | NUMERIC(10,4) | Stone carat weight |
| gold_purity | VARCHAR(20) | 14K, 18K, etc. |
| certified | BOOLEAN | Certification flag |
| retail_price | NUMERIC(12,2) | Retail price |
| is_active | BOOLEAN | Active status |
| attributes | JSONB | Extensible attributes |

#### inventory

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| product_id | UUID | FK to products (unique) |
| status | VARCHAR(20) | AVAILABLE/SOLD/RESERVED |
| location | VARCHAR(255) | Storage location |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update |

#### sales

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sale_number | VARCHAR(50) | Unique identifier |
| customer_name | VARCHAR(255) | Customer name |
| sale_type | VARCHAR(20) | RETAIL/WHOLESALE/ONLINE |
| total_amount | NUMERIC(12,2) | Total amount |
| payment_method | VARCHAR(50) | CASH/CARD/TRANSFER |
| status | VARCHAR(20) | COMPLETED/CANCELLED |
| sale_date | TIMESTAMP | Sale timestamp |

#### inventory_transactions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| inventory_id | UUID | FK to inventory |
| transaction_type | VARCHAR(50) | SALE/RESTOCK/ADJUSTMENT |
| status_before | VARCHAR(20) | Previous status |
| status_after | VARCHAR(20) | New status |
| reference_id | UUID | Related entity (e.g., sale_id) |
| notes | VARCHAR(500) | Transaction notes |
| performed_by | VARCHAR(100) | User who performed action |

---

## API Endpoints

### Products API

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/products | POST | Create product |
| /api/v1/products | GET | List products |
| /api/v1/products/{id} | GET | Get by ID |
| /api/v1/products/sku/{sku} | GET | Get by SKU |
| /api/v1/products/{id} | PUT | Update product |
| /api/v1/products/{id} | DELETE | Soft delete |
| /api/v1/products/bulk-upload | POST | Excel upload |

### Inventory API

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/inventory | GET | List inventory |
| /api/v1/inventory/{product_id} | GET | Get by product |
| /api/v1/inventory/{product_id} | PUT | Update |
| /api/v1/inventory/{product_id}/adjust | POST | Adjust status |
| /api/v1/inventory/{product_id}/transactions | GET | Transaction history |

### Sales API

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/sales | GET | List sales |
| /api/v1/sales | POST | Create sale |
| /api/v1/sales/{id} | GET | Get by ID |
| /api/v1/sales/{id}/cancel | POST | Cancel sale |

### Stock API (Combined)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/stock | GET | Grid data (products + inventory) |
| /api/v1/stock/summary | GET | Summary statistics |
| /api/v1/stock/{product_id} | GET | Detailed info |

---

## Item-Based Inventory Model

### Core Concept

| Aspect | Quantity-Based | Item-Based (Current) |
|--------|----------------|----------------------|
| Tracking Unit | Quantity count | Individual status |
| Sale Effect | Reduces quantity | Sets status = SOLD |
| Validation | quantity > 0 | status == AVAILABLE |
| Best For | Commodities | Unique items (jewelry) |

### Status State Machine

```
         ┌─────────────┐
         │  AVAILABLE  │ ← Initial state
         └──────┬──────┘
                │
        ┌───────┼───────┐
        │       │       │
        ▼       ▼       │
┌─────────────┐ ┌─────────────┐
│    SOLD     │ │  RESERVED   │
└──────┬──────┘ └──────┬──────┘
       │               │
       └───────┬───────┘
               │
         (back to AVAILABLE)
```

### Valid Transitions

- AVAILABLE → SOLD (via sale)
- AVAILABLE → RESERVED (reservation)
- RESERVED → AVAILABLE (release)
- RESERVED → SOLD (sell reserved)
- SOLD → AVAILABLE (cancel/restock)

---

## Data Flow Examples

### Creating a Product

1. User fills form in ProductsPage
2. `productsApi.create(payload)` called
3. Backend validates ProductCreate schema
4. ProductService.create():
   - Generate SKU (format: SI00001)
   - Create Product record
   - Create Inventory (status=AVAILABLE)
   - Create ReorderRule
5. Database commits
6. Grid refreshes

### Selling an Item

1. CreateSalePage loads AVAILABLE items
2. User selects products, submits sale
3. Backend validates each item:
   - Product must exist
   - Inventory must exist
   - **Status MUST be AVAILABLE**
4. SaleService.create():
   - Create Sale record
   - Create SaleItem records
   - Call `mark_sold()` for each item
5. InventoryService creates transaction:
   - status_before: AVAILABLE
   - status_after: SOLD
6. Grid refreshes

---

## Authentication

### User Roles

| Role | Permissions |
|------|-------------|
| admin | Full access, user management |
| manager | Product/inventory/sales management |
| staff | View + create sales only |

### Auth Flow

1. User enters credentials
2. `authApi.login(username, password)`
3. Backend validates, generates JWT
4. Tokens stored in localStorage
5. Requests include `Authorization: Bearer <token>`

---

## Bulk Upload

### Excel Template Columns

| Column | Required | Format |
|--------|----------|---------|
| SKU | Yes | SI00001 (SI + 5 digits) |
| Category | No | Rings, Necklaces, etc. |
| Sub Category | No | Optional |
| Style Number | No | Style identifier |
| ST Carat | No | Decimal |
| Product wt | No | Grams (decimal) |
| Gold Purity | No | 10K, 14K, 18K, 22K, 24K |
| Certified | No | TRUE/FALSE |
| Wholesale Price | No | Decimal |
| Retail Price | Yes | Decimal |
| Online Price | No | Decimal |

### Validation Rules

- SKU must match `^SI\d{5}$`
- SKU must be unique
- Retail Price is required
- All rows validated before insertion (all-or-nothing)

---

## Running the System

### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

### Run Migrations

```bash
cd backend
alembic upgrade head
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## Quick Reference

### Common Operations

| Task | Command |
|------|---------|
| Check migrations | `alembic current` |
| Upgrade DB | `alembic upgrade head` |
| Downgrade | `alembic downgrade -1` |
| New migration | `alembic revision -m "desc"` |
| Install deps (backend) | `pip install -r requirements.txt` |
| Install deps (frontend) | `npm install` |

### File Locations

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/db/base.py` | Database configuration |
| `backend/app/core/config.py` | Environment settings |
| `frontend/src/services/api.js` | API client |
| `frontend/src/App.jsx` | React routing |
| `frontend/vite.config.js` | Vite + proxy config |

---

## System Statistics

- **Total Pages:** 9
- **API Endpoints:** 30+
- **Database Tables:** 8
- **Service Classes:** 6
- **Model Classes:** 8

---

*For complete documentation, see `Inventory_ERP_Documentation.docx`*
