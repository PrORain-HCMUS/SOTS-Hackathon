# Bio-Radar Backend

High-performance Rust backend for satellite image analysis and salinity intrusion detection in the Mekong Delta region.

## Tech Stack

- **Framework**: Axum (high-performance async web framework)
- **Database**: PostgreSQL + PostGIS (spatial data)
- **AI**: ONNX Runtime (HLS Foundation Model for segmentation)
- **Async Runtime**: Tokio

## Architecture

```
src/
├── main.rs              # Entry point
├── lib.rs               # Module exports
├── config/              # Configuration management
├── domain/              # Core business entities & repository traits
├── infrastructure/      # External adapters (DB, AI, Satellite API)
├── application/         # Use cases & services
└── api/                 # HTTP handlers & routes
```

## Quick Start

### Prerequisites

- Rust 1.75+
- PostgreSQL 15+ with PostGIS
- Docker (optional)

### Development

```bash
# Clone and setup
cd backend

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run with cargo
cargo run

# Or with docker-compose
docker-compose up -d
```

### API Endpoints

#### Public
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

#### Protected (requires JWT)
- `GET /api/v1/farms` - List user farms
- `POST /api/v1/farms` - Create farm
- `GET /api/v1/farms/:id` - Get farm details
- `GET /api/v1/farms/:id/indices` - Get spectral indices
- `GET /api/v1/farms/:id/alerts` - Get farm alerts

#### Monitoring
- `GET /api/v1/monitoring/status` - System status
- `GET /api/v1/monitoring/alerts` - List alerts
- `GET /api/v1/monitoring/salinity` - Get salinity data
- `GET /api/v1/monitoring/intrusion-vector` - Get intrusion vector
- `POST /api/v1/monitoring/process` - Trigger processing

#### Chatbot
- `POST /api/v1/chatbot/message` - Send chat message
- `GET /api/v1/chatbot/todos` - List todos
- `POST /api/v1/chatbot/todos` - Create todo
- `POST /api/v1/chatbot/report` - Generate report

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8080` |
| `SENTINEL_CLIENT_ID` | Sentinel Hub client ID | - |
| `SENTINEL_CLIENT_SECRET` | Sentinel Hub client secret | - |
| `JWT_SECRET` | JWT signing secret | Required |
| `ONNX_MODEL_PATH` | Path to ONNX model | `./assets/models/hls_segmentation.onnx` |

## Core Features

### 1. Satellite Image Processing
- Multi-spectral image analysis (Sentinel-2/Sentinel-1)
- Cloud cover filtering and fallback to SAR data
- Automatic segmentation using HLS Foundation Model

### 2. Spectral Indices Calculation
- **NDVI**: Vegetation health index
- **NDSI**: Salinity detection index
- **SRVI**: Soil-vegetation separation
- **Red Edge Index**: Early stress detection

### 3. Anomaly Detection
- Peak/Valley detection algorithm
- Historical baseline comparison
- Multi-index correlation analysis

### 4. Intrusion Vector Analysis
- Salinity movement tracking
- Direction and velocity calculation
- Farm impact prediction

### 5. Chatbot Integration
- Personalized context (user's farms only)
- Function calling: `get_salinity_status`, `predict_intrusion`, `write_todos`, `generate_report`

## Performance Optimizations

- Connection pooling with configurable limits
- Async I/O throughout
- ONNX model inference with optimized threading
- Spatial indexing with PostGIS GIST indexes
- Response compression (gzip)
- Release build with LTO enabled

## License

MIT
