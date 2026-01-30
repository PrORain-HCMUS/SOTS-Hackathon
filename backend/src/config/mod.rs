use once_cell::sync::Lazy;
use parking_lot::RwLock;
use std::env;

#[derive(Debug, Clone)]
pub struct AppConfig {
    pub database: DatabaseConfig,
    pub server: ServerConfig,
    pub sentinel: SentinelConfig,
    pub ai: AiConfig,
    pub jwt: JwtConfig,
    pub cors: CorsConfig,
}

#[derive(Debug, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
}

#[derive(Debug, Clone)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Clone)]
pub struct SentinelConfig {
    pub client_id: String,
    pub client_secret: String,
    pub api_url: String,
}

#[derive(Debug, Clone)]
pub struct AiConfig {
    pub onnx_model_path: String,
}

#[derive(Debug, Clone)]
pub struct JwtConfig {
    pub secret: String,
    pub expiration_hours: u64,
}

#[derive(Debug, Clone)]
pub struct CorsConfig {
    pub allowed_origins: Vec<String>,
}

static CONFIG: Lazy<RwLock<Option<AppConfig>>> = Lazy::new(|| RwLock::new(None));

impl AppConfig {
    pub fn load() -> Self {
        dotenvy::dotenv().ok();

        let config = Self {
            database: DatabaseConfig {
                url: env::var("DATABASE_URL")
                    .unwrap_or_else(|_| "postgres://localhost:5432/bio_radar".into()),
                max_connections: env::var("DATABASE_MAX_CONNECTIONS")
                    .unwrap_or_else(|_| "10".into())
                    .parse()
                    .unwrap_or(10),
            },
            server: ServerConfig {
                host: env::var("SERVER_HOST").unwrap_or_else(|_| "0.0.0.0".into()),
                port: env::var("SERVER_PORT")
                    .unwrap_or_else(|_| "8080".into())
                    .parse()
                    .unwrap_or(8080),
            },
            sentinel: SentinelConfig {
                client_id: env::var("SENTINEL_CLIENT_ID").unwrap_or_default(),
                client_secret: env::var("SENTINEL_CLIENT_SECRET").unwrap_or_default(),
                api_url: env::var("SENTINEL_API_URL")
                    .unwrap_or_else(|_| "https://services.sentinel-hub.com".into()),
            },
            ai: AiConfig {
                onnx_model_path: env::var("ONNX_MODEL_PATH")
                    .unwrap_or_else(|_| "./assets/models/hls_segmentation.onnx".into()),
            },
            jwt: JwtConfig {
                secret: env::var("JWT_SECRET").unwrap_or_else(|_| "default_secret".into()),
                expiration_hours: env::var("JWT_EXPIRATION_HOURS")
                    .unwrap_or_else(|_| "24".into())
                    .parse()
                    .unwrap_or(24),
            },
            cors: CorsConfig {
                allowed_origins: env::var("CORS_ALLOWED_ORIGINS")
                    .unwrap_or_else(|_| "http://localhost:3000".into())
                    .split(',')
                    .map(|s| s.trim().to_string())
                    .collect(),
            },
        };

        *CONFIG.write() = Some(config.clone());
        config
    }

    pub fn global() -> Self {
        CONFIG
            .read()
            .clone()
            .expect("Config not initialized. Call AppConfig::load() first.")
    }
}
