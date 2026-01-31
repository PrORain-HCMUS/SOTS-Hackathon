-- Extended schema for Dashboard, Analytics, Reports, and Settings

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    auto_refresh BOOLEAN NOT NULL DEFAULT TRUE,
    refresh_interval_minutes INTEGER NOT NULL DEFAULT 5,
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    data_retention_days INTEGER NOT NULL DEFAULT 90,
    theme VARCHAR(20) NOT NULL DEFAULT 'system',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    report_type VARCHAR(50) NOT NULL CHECK (report_type IN ('performance', 'risk_assessment', 'resource_audit', 'quarterly', 'weekly', 'seasonal', 'custom')),
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    file_path VARCHAR(1000),
    file_size_bytes BIGINT,
    parameters JSONB,
    generated_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- Regions table for geographic analysis
CREATE TABLE IF NOT EXISTS regions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_region_id BIGINT REFERENCES regions(id),
    geometry GEOMETRY(MULTIPOLYGON, 4326),
    area_hectares NUMERIC(14, 4),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regions_code ON regions(code);
CREATE INDEX IF NOT EXISTS idx_regions_geometry ON regions USING GIST(geometry);

-- Regional metrics for analytics (aggregated data)
CREATE TABLE IF NOT EXISTS regional_metrics (
    id BIGSERIAL PRIMARY KEY,
    region_id BIGINT NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_area_hectares NUMERIC(14, 4),
    avg_yield_per_hectare NUMERIC(10, 4),
    efficiency_percentage NUMERIC(6, 2),
    water_usage_liters NUMERIC(16, 2),
    cost_per_hectare NUMERIC(12, 2),
    risk_level VARCHAR(20) CHECK (risk_level IN ('excellent', 'good', 'fair', 'needs_attention', 'critical')),
    active_farms_count INTEGER DEFAULT 0,
    alerts_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(region_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_regional_metrics_region_id ON regional_metrics(region_id);
CREATE INDEX IF NOT EXISTS idx_regional_metrics_date ON regional_metrics(metric_date DESC);

-- System integrations status
CREATE TABLE IF NOT EXISTS integrations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    integration_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'disconnected' CHECK (status IN ('connected', 'active', 'offline', 'disconnected', 'error')),
    api_endpoint VARCHAR(1000),
    last_sync_at TIMESTAMPTZ,
    config JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sensors data for map display
CREATE TABLE IF NOT EXISTS sensors (
    id BIGSERIAL PRIMARY KEY,
    farm_id BIGINT REFERENCES farms(id) ON DELETE CASCADE,
    sensor_type VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    location GEOMETRY(POINT, 4326),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    last_reading_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensors_farm_id ON sensors(farm_id);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);
CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors USING GIST(location);

-- Dashboard statistics cache (for performance)
CREATE TABLE IF NOT EXISTS dashboard_stats_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    stat_type VARCHAR(50) NOT NULL,
    stat_value JSONB NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(user_id, stat_type)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_stats_user_id ON dashboard_stats_cache(user_id);

-- Triggers for updated_at
CREATE TRIGGER user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER integrations_updated_at BEFORE UPDATE ON integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER sensors_updated_at BEFORE UPDATE ON sensors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Insert default regions (Mekong Delta provinces)
INSERT INTO regions (name, code, area_hectares, metadata) VALUES
    ('Vietnam', 'VN', 33100000, '{"type": "country"}'),
    ('Mekong Delta', 'mekong', 4060000, '{"type": "region"}'),
    ('An Giang', 'angiang', 353700, '{"type": "province", "parent_code": "mekong"}'),
    ('Đồng Tháp', 'dongthap', 337600, '{"type": "province", "parent_code": "mekong"}'),
    ('Cần Thơ', 'cantho', 140900, '{"type": "province", "parent_code": "mekong"}'),
    ('Long An', 'longan', 449400, '{"type": "province", "parent_code": "mekong"}'),
    ('Tiền Giang', 'tiengiang', 250400, '{"type": "province", "parent_code": "mekong"}'),
    ('Bến Tre', 'bentre', 236000, '{"type": "province", "parent_code": "mekong"}'),
    ('Vĩnh Long', 'vinhlong', 147500, '{"type": "province", "parent_code": "mekong"}'),
    ('Trà Vinh', 'travinh', 234100, '{"type": "province", "parent_code": "mekong"}'),
    ('Sóc Trăng', 'soctrang', 331200, '{"type": "province", "parent_code": "mekong"}'),
    ('Bạc Liêu', 'baclieu', 266900, '{"type": "province", "parent_code": "mekong"}'),
    ('Cà Mau', 'camau', 529500, '{"type": "province", "parent_code": "mekong"}'),
    ('Kiên Giang', 'kiengiang', 634900, '{"type": "province", "parent_code": "mekong"}'),
    ('Hậu Giang', 'haugiang', 160200, '{"type": "province", "parent_code": "mekong"}')
ON CONFLICT DO NOTHING;

-- Insert default integrations
INSERT INTO integrations (name, integration_type, status, api_endpoint) VALUES
    ('OpenWeather API', 'weather', 'connected', 'https://api.openweathermap.org'),
    ('Sentinel-2 Satellite', 'satellite', 'active', 'https://scihub.copernicus.eu'),
    ('AgriSmart AI Engine', 'ai', 'offline', NULL)
ON CONFLICT DO NOTHING;

-- Insert sample regional metrics for demo
INSERT INTO regional_metrics (region_id, metric_date, total_area_hectares, avg_yield_per_hectare, efficiency_percentage, water_usage_liters, cost_per_hectare, risk_level, active_farms_count, alerts_count)
SELECT 
    r.id,
    CURRENT_DATE,
    r.area_hectares * 0.15,
    6.0 + random() * 1.5,
    85 + random() * 15,
    (r.area_hectares * 0.15) * 5000 * (0.8 + random() * 0.4),
    3500 + random() * 1500,
    CASE 
        WHEN random() < 0.3 THEN 'excellent'
        WHEN random() < 0.6 THEN 'good'
        WHEN random() < 0.85 THEN 'fair'
        ELSE 'needs_attention'
    END,
    floor(10 + random() * 50)::int,
    floor(random() * 5)::int
FROM regions r
WHERE r.code NOT IN ('VN', 'mekong')
ON CONFLICT DO NOTHING;
