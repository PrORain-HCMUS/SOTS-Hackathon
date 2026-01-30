# Build Instructions

## Issue: Windows Native Build

The ONNX Runtime (`ort` crate) has linking issues on Windows due to missing MSVC C++ standard library symbols (`__std_find_last_of_trivial_pos_1`, etc.).

## ✅ Recommended Solution: Use Docker

Docker provides a Linux build environment that avoids Windows-specific issues:

```powershell
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

The backend will be available at `http://localhost:8080`

## Alternative: Fix Windows Build

If you must build natively on Windows, you need:

1. **Install Visual Studio 2022 Build Tools** with:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)
   - Windows 11 SDK (10.0.22621.0 or later)
   - C++ CMake tools for Windows

2. **Or simplify dependencies** by removing ONNX:

```toml
# In Cargo.toml, comment out:
# ort = { version = "2.0.0-rc.11", features = ["ndarray"] }
# ndarray = "0.17"
```

Then comment out AI-related code in:
- `src/infrastructure/ai/segmentation.rs`
- `src/application/analyze_service.rs`

## Database Setup

Before running, ensure PostgreSQL with PostGIS is available:

```bash
# Using Docker (recommended)
docker-compose up -d db

# Or install locally:
# - PostgreSQL 15+
# - PostGIS extension
```

Set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgres://bioradar:bioradar@localhost:5432/bio_radar
```

## Environment Variables

Copy and configure:
```powershell
cp .env.example .env
# Edit .env with your settings
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Secret for JWT tokens
- `SERVER_HOST` - Server bind address (default: 0.0.0.0)
- `SERVER_PORT` - Server port (default: 8080)

Optional:
- `SENTINEL_CLIENT_ID` - Sentinel Hub API credentials
- `SENTINEL_CLIENT_SECRET`
- `ONNX_MODEL_PATH` - Path to ONNX model file

## Testing

```powershell
# Health check
curl http://localhost:8080/api/v1/health

# Should return: {"status":"healthy"}
```
