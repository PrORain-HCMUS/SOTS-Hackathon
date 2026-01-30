use geojson::{GeoJson, Geometry, Value};
use crate::shared::error::AppError;

pub fn validate_polygon(geojson_str: &str) -> Result<(), AppError> {
    let geojson: GeoJson = geojson_str.parse()
        .map_err(|e| AppError::BadRequest(format!("Invalid GeoJSON: {}", e)))?;

    match geojson {
        GeoJson::Geometry(geometry) => {
            validate_geometry(&geometry)?;
        }
        GeoJson::Feature(feature) => {
            if let Some(geometry) = feature.geometry {
                validate_geometry(&geometry)?;
            } else {
                return Err(AppError::BadRequest("Feature has no geometry".to_string()));
            }
        }
        GeoJson::FeatureCollection(_) => {
            return Err(AppError::BadRequest("FeatureCollection not supported, use single Polygon".to_string()));
        }
    }

    Ok(())
}

fn validate_geometry(geometry: &Geometry) -> Result<(), AppError> {
    match &geometry.value {
        Value::Polygon(coords) => {
            if coords.is_empty() {
                return Err(AppError::BadRequest("Polygon has no rings".to_string()));
            }
            
            let exterior = &coords[0];
            if exterior.len() < 4 {
                return Err(AppError::BadRequest("Polygon must have at least 4 points".to_string()));
            }

            if exterior.first() != exterior.last() {
                return Err(AppError::BadRequest("Polygon must be closed (first point = last point)".to_string()));
            }

            for point in exterior {
                if point.len() < 2 {
                    return Err(AppError::BadRequest("Invalid coordinate".to_string()));
                }
                let lon = point[0];
                let lat = point[1];
                if !(-180.0..=180.0).contains(&lon) || !(-90.0..=90.0).contains(&lat) {
                    return Err(AppError::BadRequest(format!("Invalid coordinates: [{}, {}]", lon, lat)));
                }
            }

            Ok(())
        }
        _ => Err(AppError::BadRequest("Only Polygon geometry is supported".to_string())),
    }
}

pub fn normalize_geojson(geojson_str: &str) -> Result<String, AppError> {
    let geojson: GeoJson = geojson_str.parse()
        .map_err(|e| AppError::BadRequest(format!("Invalid GeoJSON: {}", e)))?;

    let geometry = match geojson {
        GeoJson::Geometry(g) => g,
        GeoJson::Feature(f) => {
            f.geometry.ok_or_else(|| AppError::BadRequest("Feature has no geometry".to_string()))?
        }
        GeoJson::FeatureCollection(_) => {
            return Err(AppError::BadRequest("FeatureCollection not supported".to_string()));
        }
    };

    serde_json::to_string(&geometry)
        .map_err(|e| AppError::Internal(format!("Failed to serialize geometry: {}", e)))
}
