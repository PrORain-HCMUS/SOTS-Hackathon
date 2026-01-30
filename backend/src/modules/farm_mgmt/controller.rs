use axum::{
    extract::{Path, State, Extension, Query},
    Json,
};
use crate::shared::{AppState, error::AppError, utils::parse_geojson_to_wkt};
use crate::modules::auth::models::Claims;
use super::{
    models::{CreateFarmRequest, UpdateFarmRequest, FarmResponse, ConvertRequest, ConvertResponse, IntersectionQuery},
    repository, service,
};

pub async fn create_farm(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<CreateFarmRequest>,
) -> Result<Json<FarmResponse>, AppError> {
    service::validate_polygon(&payload.geojson)?;
    let normalized_geojson = service::normalize_geojson(&payload.geojson)?;

    let farm = repository::create(&state.db, claims.sub, &payload.name, &normalized_geojson).await?;
    
    let geojson = repository::get_geojson(&state.db, farm.id)
        .await?
        .ok_or_else(|| AppError::Internal("Failed to retrieve GeoJSON".to_string()))?;

    Ok(Json(FarmResponse::from_farm(farm, geojson)))
}

pub async fn list_farms(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<Vec<FarmResponse>>, AppError> {
    let farms_with_geojson = repository::get_by_user_with_geojson(&state.db, claims.sub).await?;
    
    let responses = farms_with_geojson
        .into_iter()
        .map(|(farm, geojson)| FarmResponse::from_farm(farm, geojson))
        .collect();

    Ok(Json(responses))
}

pub async fn get_farm(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
) -> Result<Json<FarmResponse>, AppError> {
    let farm = repository::get_by_id(&state.db, id)
        .await?
        .ok_or_else(|| AppError::NotFound(format!("Farm {} not found", id)))?;

    if farm.user_id != claims.sub {
        return Err(AppError::Unauthorized("Not authorized to access this farm".to_string()));
    }

    let geojson = repository::get_geojson(&state.db, farm.id)
        .await?
        .ok_or_else(|| AppError::Internal("Failed to retrieve GeoJSON".to_string()))?;

    Ok(Json(FarmResponse::from_farm(farm, geojson)))
}

pub async fn update_farm(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
    Json(payload): Json<UpdateFarmRequest>,
) -> Result<Json<FarmResponse>, AppError> {
    let existing = repository::get_by_id(&state.db, id)
        .await?
        .ok_or_else(|| AppError::NotFound(format!("Farm {} not found", id)))?;

    if existing.user_id != claims.sub {
        return Err(AppError::Unauthorized("Not authorized to update this farm".to_string()));
    }

    let normalized_geojson = if let Some(ref geojson) = payload.geojson {
        service::validate_polygon(geojson)?;
        Some(service::normalize_geojson(geojson)?)
    } else {
        None
    };

    let farm = repository::update(
        &state.db,
        id,
        payload.name.as_deref(),
        normalized_geojson.as_deref(),
    ).await?;

    let geojson = repository::get_geojson(&state.db, farm.id)
        .await?
        .ok_or_else(|| AppError::Internal("Failed to retrieve GeoJSON".to_string()))?;

    Ok(Json(FarmResponse::from_farm(farm, geojson)))
}

pub async fn delete_farm(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
) -> Result<Json<serde_json::Value>, AppError> {
    let existing = repository::get_by_id(&state.db, id)
        .await?
        .ok_or_else(|| AppError::NotFound(format!("Farm {} not found", id)))?;

    if existing.user_id != claims.sub {
        return Err(AppError::Unauthorized("Not authorized to delete this farm".to_string()));
    }

    repository::delete(&state.db, id).await?;

    Ok(Json(serde_json::json!({ "success": true })))
}

pub async fn convert_to_wkt(
    Json(payload): Json<ConvertRequest>,
) -> Result<Json<ConvertResponse>, AppError> {
    let wkt = parse_geojson_to_wkt(&payload.geojson)?;
    Ok(Json(ConvertResponse { wkt }))
}

pub async fn find_intersecting_farms(
    State(state): State<AppState>,
    Query(query): Query<IntersectionQuery>,
) -> Result<Json<Vec<FarmResponse>>, AppError> {
    let farms = repository::find_intersecting(&state.db, &query.bbox_geojson).await?;
    
    let mut responses = Vec::with_capacity(farms.len());
    for farm in farms {
        if let Some(geojson) = repository::get_geojson(&state.db, farm.id).await? {
            responses.push(FarmResponse::from_farm(farm, geojson));
        }
    }

    Ok(Json(responses))
}