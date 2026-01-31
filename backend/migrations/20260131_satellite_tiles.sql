-- Migration: Add satellite tiles and crop classification tables
-- Date: 2026-01-31

-- Crop classes (land use types from satellite imagery)
CREATE TABLE IF NOT EXISTS crop_classes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Satellite tiles with spatial data
CREATE TABLE IF NOT EXISTS satellite_tiles (
    id SERIAL PRIMARY KEY,
    tile_id INTEGER NOT NULL UNIQUE,
    tile_name VARCHAR(100) NOT NULL,
    prediction_file VARCHAR(255) NOT NULL,
    visualization_file VARCHAR(255) NOT NULL,
    bounds JSONB NOT NULL,
    center_lat DOUBLE PRECISION NOT NULL,
    center_lon DOUBLE PRECISION NOT NULL,
    bbox JSONB NOT NULL,
    geometry GEOMETRY(POLYGON, 4326),
    captured_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_satellite_tiles_geometry 
ON satellite_tiles USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_satellite_tiles_tile_id 
ON satellite_tiles (tile_id);

-- Tile crop statistics (aggregated from prediction files)
CREATE TABLE IF NOT EXISTS tile_crop_stats (
    id SERIAL PRIMARY KEY,
    tile_id INTEGER REFERENCES satellite_tiles(tile_id) ON DELETE CASCADE,
    crop_class_id INTEGER REFERENCES crop_classes(id),
    pixel_count INTEGER NOT NULL,
    area_hectares DOUBLE PRECISION,
    percentage DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tile_crop_stats_tile_id 
ON tile_crop_stats (tile_id);

CREATE INDEX IF NOT EXISTS idx_tile_crop_stats_crop_class_id 
ON tile_crop_stats (crop_class_id);

-- Add composite index for querying tile statistics by crop type
CREATE INDEX IF NOT EXISTS idx_tile_crop_stats_tile_crop 
ON tile_crop_stats (tile_id, crop_class_id);
