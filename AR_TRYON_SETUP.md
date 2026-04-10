# AR Virtual Jewelry Try-On - Setup Guide

## Overview

This MVP implements a virtual jewelry try-on feature using:
- **Frontend**: React + Three.js + MediaPipe Face Mesh
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: Local public folder for 3D models

## Folder Structure

```
inventory-system/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── jewelry.py          # Jewelry & TryOnLog models
│   │   ├── schemas/
│   │   │   └── jewelry.py          # Pydantic schemas
│   │   ├── services/
│   │   │   └── jewelry_service.py  # Business logic
│   │   └── api/v1/
│   │       └── jewelry.py          # API routes
│   └── public/
│       ├── models/                 # 3D model files (.glb, .gltf)
│       └── tryon-screenshots/      # Captured screenshots
├── frontend/
│   └── src/
│       ├── components/ar/
│       │   └── FaceMeshAR.jsx      # AR component with face tracking
│       └── pages/ar/
│           └── ARTryOnPage.jsx     # Main try-on page
└── public/
    ├── models/                     # Accessible 3D model files
    └── thumbnails/                 # Jewelry thumbnails
```

## Database Setup

### 1. Run Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 2. Verify Tables

The migration creates two tables:

**jewelry** - Stores jewelry products:
- `id` (UUID, primary key)
- `name` (VARCHAR)
- `type` (VARCHAR: earring, ring, necklace)
- `model_url` (VARCHAR: path to 3D model)
- `thumbnail_url` (VARCHAR)
- `price` (DECIMAL)
- `description` (VARCHAR)
- `is_active` (VARCHAR)
- `created_at`, `updated_at` (DATETIME)

**tryon_logs** - Analytics tracking:
- `id` (UUID, primary key)
- `product_id` (UUID, foreign key)
- `session_id` (VARCHAR)
- `user_id` (UUID)
- `screenshot_url` (VARCHAR)
- `duration_seconds` (INT)
- `timestamp` (DATETIME)

### 3. Seed Sample Data

Sample earrings are auto-inserted on first migration. To add more:

```sql
INSERT INTO jewelry (id, name, type, model_url, thumbnail_url, price, description, is_active, created_at)
VALUES
  (gen_random_uuid(), 'Diamond Stud Earrings', 'earring', '/models/earring-stud.glb', '/thumbnails/earring-stud.jpg', 299.99, 'Classic diamond stud earrings', 'true', now()),
  (gen_random_uuid(), 'Gold Hoop Earrings', 'earring', '/models/earring-hoop.glb', '/thumbnails/earring-hoop.jpg', 199.99, 'Elegant gold hoop earrings', 'true', now()),
  (gen_random_uuid(), 'Pearl Drop Earrings', 'earring', '/models/earring-pearl.glb', '/thumbnails/earring-pearl.jpg', 149.99, 'Beautiful pearl drop earrings', 'true', now());
```

## 3D Model Requirements

### Supported Formats
- `.glb` (recommended - binary glTF)
- `.gltf` (ASCII glTF)

### Model Specifications
- **Scale**: Models should be sized for ~20-30mm earrings (real-world scale)
- **Origin**: Center the earring at (0, 0, 0)
- **Orientation**: Front-facing (positive Z axis)
- **File size**: Keep under 500KB for fast loading

### Getting 3D Models

1. **Create your own**: Use Blender, Maya, or Cinema 4D
2. **Download**: Sketchfab, TurboSquid, or free glTF repositories
3. **Convert**: Use online converters or Blender to convert from OBJ/FBX to glTF

### Adding Models

1. Place `.glb` files in `backend/public/models/`
2. Add thumbnails to `public/thumbnails/`
3. Insert database record:

```sql
INSERT INTO jewelry (name, type, model_url, thumbnail_url, price, description, is_active, created_at)
VALUES ('Ruby Earrings', 'earring', '/models/ruby-earrings.glb', '/thumbnails/ruby-earrings.jpg', 599.99, 'Stunning ruby earrings', 'true', now());
```

## Running Locally

### Backend

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Visit: http://localhost:3000

### Access AR Try-On

1. Navigate to **AR Try-On** in the navbar
2. Click **Start AR Try-On**
3. Grant camera permissions
4. Select jewelry from the right panel
5. View earrings overlaid on your ears
6. Click **Capture** to save a screenshot

## API Endpoints

### Jewelry Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jewelry` | List all jewelry |
| GET | `/api/v1/jewelry?type=earring` | Filter by type |
| GET | `/api/v1/jewelry/{id}` | Get single item |
| POST | `/api/v1/jewelry` | Create new item |
| PUT | `/api/v1/jewelry/{id}` | Update item |
| DELETE | `/api/v1/jewelry/{id}` | Delete item |
| POST | `/api/v1/jewelry/upload-model` | Upload 3D model |

### Try-On Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jewelry/tryon/log` | Log try-on event |
| GET | `/api/v1/jewelry/tryon/logs` | Get try-on logs |
| GET | `/api/v1/jewelry/tryon/stats` | Get analytics |

## Technical Details

### Face Tracking

- **Library**: MediaPipe Face Mesh
- **Landmarks**: 468 facial landmarks
- **Ear Detection**: Uses landmarks 127-136 (left) and 356-365 (right)
- **Performance**: Targets 25-30 FPS

### 3D Rendering

- **Engine**: Three.js
- **Lighting**: Ambient + Directional light
- **Positioning**: Maps 2D face landmarks to 3D coordinates
- **Mirroring**: Video and overlay mirrored for natural interaction

### Screenshot Capture

- Combines webcam video + Three.js canvas
- Downloads as PNG automatically
- Logs to database with timestamp

## Troubleshooting

### Camera not working
- Ensure HTTPS (or localhost)
- Grant camera permissions in browser
- Check browser compatibility (Chrome/Edge recommended)

### Model not loading
- Verify file is `.glb` or `.gltf`
- Check file path in database matches `public/models/`
- Open browser console for errors

### Low FPS
- Reduce model complexity
- Lower camera resolution
- Close other browser tabs

### Earrings not aligned
- Adjust model origin point in 3D software
- Modify `LEFT_EAR_LANDMARKS` / `RIGHT_EAR_LANDMARKS` arrays
- Tune scale factors in `updateEarringPositions()`

## Next Steps (Post-MVP)

1. **Cloud Storage**: Move to S3 for model/screenshot storage
2. **Ring Try-On**: Add hand tracking with MediaPipe Hands
3. **Necklace Try-On**: Extended face/neck tracking
4. **Multi-face**: Support multiple faces simultaneously
5. **Social Sharing**: Direct share to Instagram/TikTok
6. **Purchase Flow**: Add-to-cart from try-on screen
