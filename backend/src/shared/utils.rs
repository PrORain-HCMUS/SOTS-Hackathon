use crate::shared::error::{AppError, AppResult};
use geojson::GeoJson;
use wkt::ToWkt;

pub fn parse_geojson_to_wkt(geojson_str: &str) -> AppResult<String> {
    let geojson: GeoJson = geojson_str
        .parse()
        .map_err(|e| AppError::GeometryParsing(format!("Invalid GeoJSON: {}", e)))?;

    match geojson {
        GeoJson::Geometry(geometry) => {
            let geo_geometry: geo_types::Geometry<f64> = geometry
                .try_into()
                .map_err(|e| AppError::GeometryParsing(format!("Conversion error: {}", e)))?;
            Ok(geo_geometry.to_wkt().to_string())
        }
        GeoJson::Feature(feature) => {
            if let Some(geometry) = feature.geometry {
                let geo_geometry: geo_types::Geometry<f64> = geometry
                    .try_into()
                    .map_err(|e| AppError::GeometryParsing(format!("Conversion error: {}", e)))?;
                Ok(geo_geometry.to_wkt().to_string())
            } else {
                Err(AppError::GeometryParsing("Feature has no geometry".to_string()))
            }
        }
        _ => Err(AppError::GeometryParsing("Unsupported GeoJSON type".to_string())),
    }
}

pub fn calculate_centroid(points: &[(f64, f64)]) -> AppResult<(f64, f64)> {
    if points.is_empty() {
        return Err(AppError::Validation("Cannot calculate centroid of empty point set".to_string()));
    }

    let sum = points.iter().fold((0.0, 0.0), |(sum_x, sum_y), (x, y)| {
        (sum_x + x, sum_y + y)
    });

    let count = points.len() as f64;
    Ok((sum.0 / count, sum.1 / count))
}

pub fn calculate_angle_degrees(from: (f64, f64), to: (f64, f64)) -> f64 {
    let dx = to.0 - from.0;
    let dy = to.1 - from.1;
    dy.atan2(dx).to_degrees()
}

pub fn angle_to_direction(angle_degrees: f64) -> String {
    let normalized = ((angle_degrees + 360.0) % 360.0) as i32;
    match normalized {
        337..=360 | 0..=22 => "E".to_string(),
        23..=67 => "NE".to_string(),
        68..=112 => "N".to_string(),
        113..=157 => "NW".to_string(),
        158..=202 => "W".to_string(),
        203..=247 => "SW".to_string(),
        248..=292 => "S".to_string(),
        293..=336 => "SE".to_string(),
        _ => "UNKNOWN".to_string(),
    }
}

pub fn calculate_distance_km(from: (f64, f64), to: (f64, f64)) -> f64 {
    const EARTH_RADIUS_KM: f64 = 6371.0;
    
    let lat1 = from.1.to_radians();
    let lat2 = to.1.to_radians();
    let delta_lat = (to.1 - from.1).to_radians();
    let delta_lon = (to.0 - from.0).to_radians();

    let a = (delta_lat / 2.0).sin().powi(2)
        + lat1.cos() * lat2.cos() * (delta_lon / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());

    EARTH_RADIUS_KM * c
}
