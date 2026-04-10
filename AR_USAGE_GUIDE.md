# AR Try-On - Complete Usage Guide

## Quick Start

### 1. Access the Feature

**Frontend URL:** http://localhost:3000/ar-tryon

**Backend API:** http://localhost:8000/api/v1/jewelry

**API Docs:** http://localhost:8000/docs

---

## Frontend Usage (User Interface)

### Step-by-Step

1. **Navigate to AR Try-On**
   - Click "AR Try-On" in the top navigation bar
   - Or go directly to: http://localhost:3000/ar-tryon

2. **Start AR Session**
   - Click the **"Start AR Try-On"** button
   - Browser will ask for camera permission → Click "Allow"
   - You'll see your webcam feed with a mirrored effect

3. **Select Jewelry**
   - Use the right panel to browse available earrings
   - Click on any jewelry card to select it
   - The 3D model will load and overlay on your ears

4. **Try Different Items**
   - Click different jewelry cards to switch between earrings
   - Each item loads its unique 3D model

5. **Capture Screenshot**
   - Click the **"📷 Capture"** button
   - Screenshot downloads automatically as PNG
   - Image includes your video + 3D jewelry overlay

6. **End Session**
   - Click **"End Session"** when done
   - Session analytics are logged to backend

### UI Elements

```
┌─────────────────────────────────────────────────────────────┐
│  Virtual Try-On                          [Start AR Try-On]  │
├──────────────────────────────┬──────────────────────────────┤
│                              │  Select Jewelry              │
│                              │  ┌─────────────────────────┐ │
│    [WEBCAM FEED]             │  │ 💎 Diamond Stud         │ │
│    + 3D Overlay              │  │          $299.99   ✓    │ │
│                              │  └─────────────────────────┘ │
│                              │  ┌─────────────────────────┐ │
│                              │  │ 💎 Gold Hoop            │ │
│                              │  │          $199.99        │ │
│                              │  └─────────────────────────┘ │
│                              │  ┌─────────────────────────┐ │
│                              │  │ 💎 Pearl Drop           │ │
│                              │  │          $149.99        │ │
│                              │  └─────────────────────────┘ │
│                              │                              │
│                              │  Session: session_123...    │
│                              │  Duration: 45s              │
└──────────────────────────────┴──────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Start/Stop AR |
| C | Capture screenshot |
| Esc | Close AR |

---

## Backend Usage (API)

### 1. List All Jewelry

```bash
curl http://localhost:8000/api/v1/jewelry
```

**Response:**
```json
{
  "items": [
    {
      "id": "960ecaa3-64d9-4c17-9d8e-f9fe4d07dc3c",
      "name": "Diamond Stud Earrings",
      "type": "earring",
      "price": 299.99,
      "model_url": "/models/placeholder-earring.glb",
      "thumbnail_url": "/thumbnails/earring-stud.jpg",
      "description": "Classic diamond stud earrings",
      "is_active": true
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

### 2. Filter by Type

```bash
# Get only earrings
curl "http://localhost:8000/api/v1/jewelry?type=earring"

# Get only rings (when added)
curl "http://localhost:8000/api/v1/jewelry?type=ring"
```

### 3. Get Single Item

```bash
curl http://localhost:8000/api/v1/jewelry/960ecaa3-64d9-4c17-9d8e-f9fe4d07dc3c
```

### 4. Create New Jewelry

```bash
curl -X POST http://localhost:8000/api/v1/jewelry \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ruby Drop Earrings",
    "type": "earring",
    "model_url": "/models/ruby-drop.glb",
    "thumbnail_url": "/thumbnails/ruby-drop.jpg",
    "price": 499.99,
    "description": "Elegant ruby drop earrings"
  }'
```

### 5. Upload 3D Model

```bash
curl -X POST http://localhost:8000/api/v1/jewelry/upload-model \
  -F "file=@/path/to/your/earring.glb"
```

**Response:**
```json
{
  "model_url": "/models/abc123def456.glb",
  "filename": "abc123def456.glb",
  "size": 245678
}
```

### 6. Log Try-On Event

```bash
curl -X POST http://localhost:8000/api/v1/jewelry/tryon/log \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "960ecaa3-64d9-4c17-9d8e-f9fe4d07dc3c",
    "session_id": "my_session_123",
    "duration_seconds": 45
  }'
```

### 7. Get Try-On Analytics

```bash
# Overall stats
curl http://localhost:8000/api/v1/jewelry/tryon/stats

# Stats for specific product
curl "http://localhost:8000/api/v1/jewelry/tryon/stats?product_id=960ecaa3-64d9-4c17-9d8e-f9fe4d07dc3c"

# Get all logs
curl "http://localhost:8000/api/v1/jewelry/tryon/logs"
```

**Analytics Response:**
```json
{
  "total_tryons": 156,
  "unique_users": 42,
  "unique_sessions": 89,
  "average_duration_seconds": 38.5,
  "by_type": {
    "earring": 120,
    "ring": 36
  }
}
```

---

## Database Direct Access

### View All Jewelry

```sql
SELECT id, name, type, price, model_url, is_active, created_at
FROM jewelry
ORDER BY created_at DESC;
```

### View Try-On Logs

```sql
SELECT
  tl.id,
  j.name as jewelry_name,
  tl.session_id,
  tl.duration_seconds,
  tl.screenshot_url,
  tl.timestamp
FROM tryon_logs tl
JOIN jewelry j ON tl.product_id = j.id
ORDER BY tl.timestamp DESC
LIMIT 10;
```

### Analytics Queries

```sql
-- Try-ons per day
SELECT DATE(timestamp) as date, COUNT(*) as tryons
FROM tryon_logs
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Most popular jewelry
SELECT j.name, COUNT(tl.id) as tryon_count
FROM jewelry j
LEFT JOIN tryon_logs tl ON j.id = tl.product_id
GROUP BY j.id, j.name
ORDER BY tryon_count DESC;

-- Average session duration
SELECT AVG(duration_seconds) as avg_duration
FROM tryon_logs
WHERE duration_seconds IS NOT NULL;
```

---

## Adding New Jewelry (Complete Workflow)

### Option A: Via API

```bash
# 1. Upload 3D model
MODEL_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/jewelry/upload-model \
  -F "file=@earring.glb")

MODEL_URL=$(echo $MODEL_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['model_url'])")

# 2. Create jewelry record
curl -X POST http://localhost:8000/api/v1/jewelry \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"New Earring\",
    \"type\": \"earring\",
    \"model_url\": \"$MODEL_URL\",
    \"price\": 199.99
  }"
```

### Option B: Direct Database

```sql
-- Insert new jewelry
INSERT INTO jewelry (name, type, model_url, thumbnail_url, price, description, is_active, created_at)
VALUES (
  'Emerald Studs',
  'earring',
  '/models/emerald-studs.glb',
  '/thumbnails/emerald-studs.jpg',
  349.99,
  'Beautiful emerald stud earrings',
  'true',
  NOW()
);

-- Verify
SELECT * FROM jewelry WHERE name = 'Emerald Studs';
```

### Option C: Via Swagger UI

1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/jewelry`
3. Click "Try it out"
4. Fill in the form:
   ```json
   {
     "name": "Sapphire Earrings",
     "type": "earring",
     "model_url": "/models/sapphire.glb",
     "price": 599.99
   }
   ```
5. Click "Execute"

---

## Troubleshooting

### Frontend Issues

**Camera not showing:**
```
1. Check browser permissions (chrome://settings/content/camera)
2. Ensure using HTTPS or localhost
3. Try Chrome/Edge (best MediaPipe support)
```

**3D model not loading:**
```
1. Open browser console (F12)
2. Check for 404 errors on model URL
3. Verify file exists: ls backend/public/models/
```

**Low FPS:**
```
1. Close other browser tabs
2. Reduce camera resolution in code
3. Use simpler 3D models (< 300KB)
```

### Backend Issues

**API not responding:**
```bash
# Check server is running
lsof -i :8000

# Restart if needed
cd backend && source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Database errors:**
```bash
# Check connection
cd backend && source venv/bin/activate
python -c "from app.db.base import engine; print(engine.connect())"

# Run migrations
alembic upgrade head
```

---

## Performance Metrics

### Expected Performance

| Metric | Target | Acceptable |
|--------|--------|------------|
| FPS | 30 | 20+ |
| Model Load Time | < 1s | < 3s |
| Face Detection | < 50ms | < 100ms |
| Screenshot Capture | < 500ms | < 1s |

### Monitoring

Check FPS counter in top-right corner of AR view.

---

## File Locations

```
backend/
├── public/
│   ├── models/           # 3D model files (.glb, .gltf)
│   └── tryon-screenshots/ # Captured screenshots
└── app/
    ├── models/jewelry.py
    ├── api/v1/jewelry.py
    └── services/jewelry_service.py

frontend/
└── src/
    ├── components/ar/FaceMeshAR.jsx
    └── pages/ar/ARTryOnPage.jsx
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND                        BACKEND                    │
│  ──────────                      ───────                    │
│  URL: localhost:3000/ar-tryon    API: localhost:8000        │
│                                  Docs: localhost:8000/docs  │
│                                                             │
│  BUTTONS:                          API ENDPOINTS:           │
│  [Start AR Try-On]               GET  /api/v1/jewelry       │
│  [📷 Capture]                    POST /api/v1/jewelry       │
│  [End Session]                   POST /api/v1/jewelry/tryon/log
│                                                             │
│  SELECTION:                      DATABASE:                  │
│  Click jewelry card              Table: jewelry             │
│  Switches 3D model               Table: tryon_logs          │
└─────────────────────────────────────────────────────────────┘
```
