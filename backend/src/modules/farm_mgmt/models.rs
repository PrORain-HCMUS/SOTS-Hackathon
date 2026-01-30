use serde::{Deserialize, Serialize};
use sqlx::types::chrono::{DateTime, Utc};
use bigdecimal::{BigDecimal, ToPrimitive};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Farm {
    pub id: i64,
    pub user_id: i64,
    pub name: String,
    pub area_hectares: Option<BigDecimal>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateFarmRequest {
    pub name: String,
    pub geojson: String,
}

#[derive(Debug, Deserialize)]
pub struct UpdateFarmRequest {
    pub name: Option<String>,
    pub geojson: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct FarmResponse {
    pub id: i64,
    pub user_id: i64,
    pub name: String,
    pub geojson: String,
    pub area_hectares: Option<f64>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl FarmResponse {
    pub fn from_farm(farm: Farm, geojson: String) -> Self {
        Self {
            id: farm.id,
            user_id: farm.user_id,
            name: farm.name,
            geojson,
            area_hectares: farm.area_hectares.and_then(|bd| bd.to_f64()),
            created_at: farm.created_at,
            updated_at: farm.updated_at,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct ConvertRequest {
    pub geojson: String,
}

#[derive(Debug, Serialize)]
pub struct ConvertResponse {
    pub wkt: String,
}

#[derive(Debug, Deserialize)]
pub struct IntersectionQuery {
    pub bbox_geojson: String,
}