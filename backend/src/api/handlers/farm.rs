use axum::{
    extract::{Path, State},
    Extension, Json,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;
use validator::Validate;

use crate::api::handlers::ApiResponse;
use crate::api::middleware::auth::Claims;
use crate::api::routes::AppState;
use crate::domain::{Alert, CropType, DomainError, Farm, GeoPolygon, SpectralIndices};

#[derive(Debug, Deserialize, Validate)]
pub struct CreateFarmRequest {
    #[validate(length(min = 1, message = "Name is required"))]
    pub name: String,
    pub geometry: GeoPolygonInput,
    pub crop_type: Option<String>,
}

#[derive(Debug, Deserialize, Validate)]
pub struct UpdateFarmRequest {
    pub name: Option<String>,
    pub geometry: Option<GeoPolygonInput>,
    pub crop_type: Option<String>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct GeoPolygonInput {
    pub coordinates: Vec<Vec<[f64; 2]>>,
    #[serde(default = "default_crs")]
    pub crs: String,
}

fn default_crs() -> String {
    "EPSG:4326".to_string()
}

#[derive(Debug, Serialize)]
pub struct FarmResponse {
    pub id: Uuid,
    pub name: String,
    pub geometry: GeoPolygon,
    pub area_hectares: f64,
    pub crop_type: Option<String>,
    pub created_at: String,
}

impl From<Farm> for FarmResponse {
    fn from(farm: Farm) -> Self {
        Self {
            id: farm.id,
            name: farm.name,
            geometry: farm.geometry,
            area_hectares: farm.area_hectares,
            crop_type: farm.crop_type.map(|c| match c {
                CropType::Rice => "rice".to_string(),
                CropType::Durian => "durian".to_string(),
                CropType::Mango => "mango".to_string(),
                CropType::Coconut => "coconut".to_string(),
                CropType::Shrimp => "shrimp".to_string(),
                CropType::Other(s) => s,
            }),
            created_at: farm.created_at.to_rfc3339(),
        }
    }
}

pub async fn list_farms(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<ApiResponse<Vec<FarmResponse>>>, DomainError> {
    tracing::info!("Listing farms for user: {}", claims.sub);

    Ok(Json(ApiResponse::success(vec![])))
}

pub async fn get_farm(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<FarmResponse>>, DomainError> {
    tracing::info!("Getting farm {} for user: {}", id, claims.sub);

    Err(DomainError::not_found(format!("Farm {} not found", id)))
}

pub async fn create_farm(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<CreateFarmRequest>,
) -> Result<Json<ApiResponse<FarmResponse>>, DomainError> {
    if let Err(e) = payload.validate() {
        return Err(DomainError::validation(e.to_string()));
    }

    let now = chrono::Utc::now();
    let geometry = GeoPolygon {
        coordinates: payload.geometry.coordinates,
        crs: payload.geometry.crs,
    };

    let area = calculate_area(&geometry);

    let farm = Farm {
        id: Uuid::new_v4(),
        user_id: claims.sub,
        name: payload.name,
        geometry,
        area_hectares: area,
        crop_type: payload.crop_type.map(|c| match c.as_str() {
            "rice" => CropType::Rice,
            "durian" => CropType::Durian,
            "mango" => CropType::Mango,
            "coconut" => CropType::Coconut,
            "shrimp" => CropType::Shrimp,
            other => CropType::Other(other.to_string()),
        }),
        created_at: now,
        updated_at: now,
    };

    tracing::info!("Created farm {} for user: {}", farm.id, claims.sub);

    Ok(Json(ApiResponse::success(FarmResponse::from(farm))))
}

pub async fn update_farm(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
    Json(_payload): Json<UpdateFarmRequest>,
) -> Result<Json<ApiResponse<FarmResponse>>, DomainError> {
    tracing::info!("Updating farm {} for user: {}", id, claims.sub);

    Err(DomainError::not_found(format!("Farm {} not found", id)))
}

pub async fn delete_farm(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<()>>, DomainError> {
    tracing::info!("Deleting farm {} for user: {}", id, claims.sub);

    Err(DomainError::not_found(format!("Farm {} not found", id)))
}

pub async fn get_farm_indices(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<Vec<SpectralIndices>>>, DomainError> {
    tracing::info!("Getting indices for farm {} user: {}", id, claims.sub);

    Ok(Json(ApiResponse::success(vec![])))
}

pub async fn get_farm_alerts(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<Vec<Alert>>>, DomainError> {
    tracing::info!("Getting alerts for farm {} user: {}", id, claims.sub);

    Ok(Json(ApiResponse::success(vec![])))
}

fn calculate_area(polygon: &GeoPolygon) -> f64 {
    if polygon.coordinates.is_empty() || polygon.coordinates[0].len() < 3 {
        return 0.0;
    }

    let coords = &polygon.coordinates[0];
    let n = coords.len();
    let mut area = 0.0;

    for i in 0..n {
        let j = (i + 1) % n;
        area += coords[i][0] * coords[j][1];
        area -= coords[j][0] * coords[i][1];
    }

    let area_deg2 = (area / 2.0).abs();
    let area_m2 = area_deg2 * 111_320.0 * 111_320.0;
    area_m2 / 10_000.0
}
