# AgriPulse Backend

Vietnam-first agricultural monitoring system using Sentinel-2 satellite imagery and S4A ConvLSTM model for crop classification.

## Features

- **Near-real-time processing**: Scheduler runs every 6 hours to discover new Sentinel-2 scenes over Vietnam
- **Cloud-masked composites**: Daily and weekly composites with cloud/shadow masking
- **Crop classification**: S4A ConvLSTM model for pixel-wise crop classification (61x61 patches)
- **Area statistics**: Aggregated crop area (ha) by administrative boundaries
- **Anomaly alerts**: Rule-based detection using NDVI/NDWI/MSI time-series

## Tech Stack

- **API**: FastAPI
- **Database**: PostgreSQL + PostGIS
- **ORM**: SQLAlchemy 2.x + Alembic migrations
- **Task Queue**: Celery + Redis (with Celery Beat scheduler)
- **Object Storage**: DigitalOcean Spaces (S3-compatible)
- **Satellite Data**: Sentinel Hub API
- **Raster Processing**: Rasterio, rio-cogeo

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker & Docker Compose
- DigitalOcean Spaces account
- Sentinel Hub account

### 2. Setup Environment

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your credentials
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker compose up -d

# Wait for services to be healthy
docker compose ps
```

### 4. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Initialize Vietnam admin units (provinces/districts)
python scripts/init_admin_units.py

# Initialize Sentinel-2 tile grid for Vietnam
python scripts/init_tiles_vn.py

# Register S4A model (after uploading weights to Spaces)
python scripts/register_model_s4a.py
```

### 5. Run Services

**Terminal 1 - API Server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.workers.celery_app worker -l INFO
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A app.workers.celery_app beat -l INFO
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/jobs/trigger` | Trigger pipeline for bbox/tile |
| GET | `/stats/country` | Country-level crop statistics |
| GET | `/stats/province` | Province-level crop statistics |
| GET | `/alerts` | Query anomaly alerts |
| GET | `/tiles/{asset_type}/{date}/{z}/{x}/{y}.png` | Tile endpoint (placeholder) |

## Testing

```bash
# Run unit tests (no external dependencies)
pytest -m "not integration" -v

# Run integration tests (requires credentials in .env)
pytest -m "integration" -v

# Run all tests
pytest -v
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API routes
│   │   ├── routes_health.py
│   │   ├── routes_jobs.py
│   │   ├── routes_tiles.py
│   │   ├── routes_stats.py
│   │   └── routes_alerts.py
│   ├── core/                   # Core modules
│   │   ├── config.py           # Settings & configuration
│   │   ├── db.py               # Database connection
│   │   ├── models_sqlalchemy.py # SQLAlchemy models
│   │   ├── crud.py             # CRUD operations
│   │   ├── spaces.py           # DigitalOcean Spaces client
│   │   ├── sentinelhub_client.py # Sentinel Hub client
│   │   ├── raster_utils.py     # Raster I/O utilities
│   │   ├── time_utils.py       # Time/date utilities
│   │   ├── s4a_infer.py        # S4A model inference
│   │   ├── aggregation.py      # Zonal statistics
│   │   └── alerts.py           # Anomaly detection
│   └── workers/                # Celery tasks
│       ├── celery_app.py
│       ├── tasks_discover.py
│       ├── tasks_preprocess.py
│       ├── tasks_infer.py
│       ├── tasks_aggregate.py
│       └── tasks_alerts.py
├── ml/
│   └── s4a_vendor/             # S4A model code (user-provided)
│       └── README.md
├── scripts/                    # Initialization scripts
│   ├── init_admin_units.py
│   ├── init_tiles_vn.py
│   └── register_model_s4a.py
├── tests/                      # Pytest tests
│   ├── test_01_env.py
│   ├── test_02_db.py
│   ├── test_03_spaces.py
│   ├── test_04_sentinelhub_fetch.py
│   ├── test_05_s4a_infer_patch.py
│   ├── test_06_geotiff_write.py
│   └── test_07_area_stats.py
├── alembic/                    # Database migrations
├── alembic.ini
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

## S4A Model Setup

1. Place S4A ConvLSTM model code in `ml/s4a_vendor/`
2. Upload model checkpoint to DigitalOcean Spaces
3. Run `python scripts/register_model_s4a.py` to register the model

See `ml/s4a_vendor/README.md` for detailed instructions.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `DO_SPACES_REGION` | DigitalOcean Spaces region | Yes |
| `DO_SPACES_BUCKET` | Spaces bucket name | Yes |
| `DO_SPACES_KEY` | Spaces access key | Yes |
| `DO_SPACES_SECRET` | Spaces secret key | Yes |
| `DO_SPACES_ENDPOINT` | Spaces endpoint URL | Yes |
| `SENTINELHUB_CLIENT_ID` | Sentinel Hub client ID | Yes |
| `SENTINELHUB_CLIENT_SECRET` | Sentinel Hub client secret | Yes |
| `TILE_SERVER_BASE_URL` | Optional tile server URL | No |

## License

Proprietary - AgriPulse Project
