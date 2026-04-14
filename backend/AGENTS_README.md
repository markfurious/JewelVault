# JewelVault AI Agent System

Production-grade AI agent system for jewelry inventory management. These are **ACTION AGENTS** that take decisions and trigger real operations - not just analysis.

## Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"

# 2. Run the backend
cd /path/to/inventory-system/backend
python -m uvicorn app.main:app --reload

# 3. Execute agents via CLI
python run_agent.py "Restock low inventory products"
python run_agent.py "Update prices based on gold increase"

# 4. Or use the API
curl -X POST http://localhost:8000/api/v1/ai/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "Restock low inventory products"}'
```

## Architecture

```
backend/app/agents/
├── claude_service.py          # Claude API wrapper
├── agent_base.py              # Base class (run, decide, act)
├── agent_orchestrator.py      # Central routing engine
├── inventory_manager_agent.py # Auto-reordering, dead stock
├── pricing_update_agent.py    # Metal price-based updates
├── sales_execution_agent.py   # Sale processing
├── product_creation_agent.py  # NL product creation
├── recommendation_execution_agent.py  # Product recommendations
├── ar_session_agent.py        # AR try-on logging
├── anomaly_action_agent.py    # Fraud/anomaly detection
└── __init__.py
```

## Available Agents

| Agent | Purpose | Example Query |
|-------|---------|---------------|
| `inventory_manager` | Auto-reordering, dead stock | "Restock low inventory" |
| `pricing_update` | Metal price updates | "Update prices for gold increase" |
| `sales_execution` | Process sales/returns | "Process sale for John Doe" |
| `product_creation` | NL product creation | "Create 1ct diamond VS1 G ring" |
| `recommendation_execution` | Product recommendations | "Add recommendations for necklaces" |
| `ar_session` | AR try-on analytics | "Log AR session" |
| `anomaly_action` | Fraud detection | "Detect anomalies" |

## Usage

### CLI

```bash
# Basic execution
python run_agent.py "Restock low inventory products"

# Dry run (simulate without DB writes)
python run_agent.py "Update prices" --dry-run

# Direct agent execution
python run_agent.py "Create sale" --agent sales_execution --action create_sale

# Verbose output
python run_agent.py "Detect anomalies" -v

# List available agents
python run_agent.py --list-agents

# Health check
python run_agent.py --health
```

### API Endpoints

#### POST /api/v1/ai/execute

Execute agent via natural language query.

```json
// Request
{
  "query": "Restock low inventory products",
  "dry_run": false
}

// Response
{
  "agent": "inventory_manager",
  "intent": "create_reorder",
  "action_taken": "Processed 3 inventory actions",
  "actions": [
    {
      "action_type": "CREATE_REORDER_REQUEST",
      "description": "Reorder request for Diamond Ring (SKU-001)",
      "entity_type": "product",
      "entity_id": "uuid-here",
      "data": {"priority": "high"}
    }
  ],
  "status": "success",
  "dry_run": false
}
```

#### POST /api/v1/ai/execute/direct

Direct agent execution (bypass intent parsing).

```json
// Request
{
  "agent": "pricing_update",
  "action": "update_prices",
  "dry_run": false,
  "parameters": {
    "metal_type": "gold",
    "threshold_percent": 2.0
  }
}
```

#### GET /api/v1/ai/agents

List all available agents.

#### GET /api/v1/ai/audit-logs

Get agent execution audit logs.

```bash
curl http://localhost:8000/api/v1/ai/audit-logs?days=7&limit=50
```

#### GET /api/v1/ai/health

Health check for agent system.

## Agent Details

### Inventory Manager Agent

Automatically manages inventory reordering and dead stock.

**Actions:**
- Creates reorder requests when stock < threshold
- Flags dead stock (90+ days without sales) for discount
- Uses sales velocity for smart reordering

```python
# CLI
python run_agent.py "Check low stock and create reorders"

# API
POST /api/v1/ai/execute
{"query": "Restock products below threshold"}
```

### Pricing Update Agent

Recalculates product prices when metal prices change.

**Actions:**
- Fetches latest metal prices
- Recalculates based on weight and purity
- Updates retail, wholesale, and online prices
- Logs all price changes

```python
# CLI
python run_agent.py "Update prices based on gold increase"

# API
POST /api/v1/ai/execute/direct
{
  "agent": "pricing_update",
  "action": "update_prices",
  "parameters": {"metal_type": "gold", "threshold_percent": 2.0}
}
```

### Sales Execution Agent

Processes sales transactions with full inventory integration.

**Actions:**
- Validates stock availability before sale
- Creates sale records
- Marks inventory as SOLD
- Handles returns and cancellations

```python
# CLI
python run_agent.py "Process sale for customer Jane, items: PROD-001, PROD-002"

# API
POST /api/v1/ai/execute
{"query": "Create sale for walk-in customer"}
```

### Product Creation Agent

Creates products from natural language descriptions.

**Example:**
```
"Create 1ct round diamond, VS1 clarity, G color, 18K white gold ring"
```

**Extracted attributes:**
- Stone type: Diamond
- Carat: 1.0
- Clarity: VS1
- Color: G
- Cut: Round
- Metal: 18K White Gold
- Category: Rings

```python
# CLI
python run_agent.py "Create 1ct round diamond VS1 G color 18K white gold ring"
```

### Recommendation Execution Agent

Generates and attaches product recommendations.

**Types:**
- `cross_sell`: Products bought together
- `similar`: Similar attributes/price
- `complementary`: Complementary items

```python
# API
POST /api/v1/ai/execute/direct
{
  "agent": "recommendation_execution",
  "action": "generate",
  "parameters": {
    "category": "Rings",
    "type": "cross_sell",
    "max": 5
  }
}
```

### AR Session Agent

Logs and analyzes AR try-on sessions.

**Actions:**
- Logs session duration and screenshots
- Classifies engagement (low/medium/high)
- Triggers follow-up for high engagement

```python
# API
POST /api/v1/ai/execute/direct
{
  "agent": "ar_session",
  "action": "log_session",
  "parameters": {
    "session_id": "session_123",
    "product_id": "uuid",
    "duration_seconds": 45,
    "screenshot_url": "/path/to/screenshot.png"
  }
}
```

### Anomaly Action Agent

Detects and responds to anomalies.

**Detection:**
- Price anomalies (retail < cost)
- Rapid sales patterns
- High-value transactions
- Inventory status anomalies

**Actions:**
- Block transaction
- Flag for review
- Log for analysis

```python
# CLI
python run_agent.py "Detect all anomalies in last 24 hours"

# API
POST /api/v1/ai/execute
{"query": "Block suspicious sale SALE-001"}
```

## Configuration

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key-here"

# Database (default)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/inventory_db"

# Optional: Metal price API
export METAL_PRICE_API_KEY="your-metal-price-api-key"
```

### Dry Run Mode

All agents support `dry_run` mode for testing:

```python
from app.agents.inventory_manager_agent import InventoryManagerAgent
from app.db.base import db_session

db = db_session()
agent = InventoryManagerAgent(db, dry_run=True)
result = agent.run()

# result.dry_run == True, no DB changes made
```

## Audit Logging

All agent actions are logged to `agent_audit_logs` table:

- Agent name
- Action type
- Entity affected
- Result (success/error)
- Dry run flag
- Timestamp

Query audit logs:
```bash
curl "http://localhost:8000/api/v1/ai/audit-logs?agent_name=inventory_manager&days=7"
```

## Database Migration

Run migrations to create audit log table:

```bash
cd backend
alembic upgrade head
```

## Error Handling

Agents use structured error handling:

```python
try:
    result = orchestrator.run(query, dry_run=False)
    if result["status"] == "success":
        # Actions completed
    else:
        # result["error"] contains details
except ValueError as e:
    # Invalid input
except Exception as e:
    # System error
```

## Design Principles

1. **Action-Oriented**: Agents execute real operations, not just analysis
2. **Idempotent**: Operations can be safely retried
3. **Auditable**: All actions logged to database
4. **Dry-Run Support**: Test without side effects
5. **Error Handling**: Graceful failure with rollback
6. **No Hardcoding**: Configuration via environment and database

## Testing

```bash
# Health check
python run_agent.py --health

# List agents
python run_agent.py --list-agents

# Dry run test
python run_agent.py "Detect anomalies" --dry-run --verbose

# API test
curl http://localhost:8000/api/v1/ai/health
```

## Integration with Existing Services

Agents use existing service layer:
- `InventoryService` - Inventory operations
- `SaleService` - Sales transactions
- `ProductService` - Product CRUD
- `MetalPriceService` - Metal prices
- `JewelryService` - AR try-on
- `AnalyticsService` - Sales velocity

No mock data - all agents work with real database.

## API Documentation

Full API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
