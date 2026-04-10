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

---

### 🪞 AR Virtual Try-On
- Three.js 3D rendering
- MediaPipe face mesh tracking
- Real-time camera overlay
- Session analytics & logging
- Screenshot capture

---

### 🧊 3D Model Generation
- Batch generation via Excel upload
- S3 / HTTP image ingestion
- GPU-based processing (TripoSR)
- SKU validation (SI-XXX format)
- Mandatory schema enforcement

---

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
