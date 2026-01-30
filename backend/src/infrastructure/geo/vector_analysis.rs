use geo::{
    algorithm::area::Area,
    algorithm::centroid::Centroid,
    Coord, LineString, Polygon,
};

use crate::domain::{DomainError, DomainResult, GeoPolygon, IntrusionVector};

pub struct VectorAnalyzer;

impl Default for VectorAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

impl VectorAnalyzer {
    pub fn new() -> Self {
        Self
    }

    pub fn calculate_intrusion_vector(
        &self,
        salinity_t1: &[(f64, f64, f32)],
        salinity_t2: &[(f64, f64, f32)],
        threshold: f32,
        days_between: f32,
    ) -> DomainResult<Option<IntrusionVector>> {
        let peak_points_t1: Vec<_> = salinity_t1
            .iter()
            .filter(|(_, _, v)| *v > threshold)
            .collect();

        let peak_points_t2: Vec<_> = salinity_t2
            .iter()
            .filter(|(_, _, v)| *v > threshold)
            .collect();

        if peak_points_t1.is_empty() || peak_points_t2.is_empty() {
            return Ok(None);
        }

        let centroid_t1 = self.calculate_weighted_centroid(&peak_points_t1);
        let centroid_t2 = self.calculate_weighted_centroid(&peak_points_t2);

        let dx = centroid_t2.0 - centroid_t1.0;
        let dy = centroid_t2.1 - centroid_t1.1;

        let magnitude_degrees = (dx * dx + dy * dy).sqrt();
        let magnitude_meters = magnitude_degrees * 111_320.0;

        let direction_radians = dy.atan2(dx);
        let direction_degrees = direction_radians.to_degrees();
        let direction_normalized = if direction_degrees < 0.0 {
            direction_degrees + 360.0
        } else {
            direction_degrees
        };

        let velocity = if days_between > 0.0 {
            magnitude_meters / (days_between as f64)
        } else {
            0.0
        };

        Ok(Some(IntrusionVector {
            direction_degrees: direction_normalized as f32,
            magnitude_meters: magnitude_meters as f32,
            velocity_m_per_day: velocity as f32,
            start_point: [centroid_t1.0, centroid_t1.1],
            end_point: [centroid_t2.0, centroid_t2.1],
        }))
    }

    fn calculate_weighted_centroid(&self, points: &[&(f64, f64, f32)]) -> (f64, f64) {
        let total_weight: f32 = points.iter().map(|(_, _, w)| w).sum();

        if total_weight == 0.0 {
            return (0.0, 0.0);
        }

        let weighted_x: f64 = points.iter().map(|(x, _, w)| x * (*w as f64)).sum();
        let weighted_y: f64 = points.iter().map(|(_, y, w)| y * (*w as f64)).sum();

        (
            weighted_x / total_weight as f64,
            weighted_y / total_weight as f64,
        )
    }

    pub fn predict_affected_area(
        &self,
        intrusion_vector: &IntrusionVector,
        farm_geometry: &GeoPolygon,
        days_ahead: f32,
    ) -> DomainResult<PredictionResult> {
        let future_displacement = intrusion_vector.velocity_m_per_day * days_ahead;
        let displacement_degrees = future_displacement / 111_320.0;

        let direction_rad = (intrusion_vector.direction_degrees as f64).to_radians();
        let future_dx = (displacement_degrees as f64) * direction_rad.cos();
        let future_dy = (displacement_degrees as f64) * direction_rad.sin();

        let predicted_center = [
            intrusion_vector.end_point[0] + future_dx,
            intrusion_vector.end_point[1] + future_dy,
        ];

        let farm_centroid = self.polygon_centroid(farm_geometry)?;
        let distance_to_farm = self.haversine_distance(
            predicted_center[1],
            predicted_center[0],
            farm_centroid.1,
            farm_centroid.0,
        );

        let current_distance = self.haversine_distance(
            intrusion_vector.end_point[1],
            intrusion_vector.end_point[0],
            farm_centroid.1,
            farm_centroid.0,
        );

        let risk_level = if distance_to_farm < 500.0 {
            RiskLevel::Critical
        } else if distance_to_farm < 1000.0 {
            RiskLevel::High
        } else if distance_to_farm < 2000.0 {
            RiskLevel::Medium
        } else {
            RiskLevel::Low
        };

        let days_to_reach = if intrusion_vector.velocity_m_per_day > 0.0 {
            Some(current_distance / intrusion_vector.velocity_m_per_day)
        } else {
            None
        };

        Ok(PredictionResult {
            predicted_center,
            distance_to_farm_m: distance_to_farm,
            risk_level,
            days_to_reach,
        })
    }

    fn polygon_centroid(&self, polygon: &GeoPolygon) -> DomainResult<(f64, f64)> {
        if polygon.coordinates.is_empty() || polygon.coordinates[0].is_empty() {
            return Err(DomainError::geo_processing("Empty polygon"));
        }

        let coords: Vec<Coord<f64>> = polygon.coordinates[0]
            .iter()
            .map(|c| Coord { x: c[0], y: c[1] })
            .collect();

        let line_string = LineString::new(coords);
        let geo_polygon = Polygon::new(line_string, vec![]);

        if let Some(centroid) = geo_polygon.centroid() {
            Ok((centroid.x(), centroid.y()))
        } else {
            let sum_x: f64 = polygon.coordinates[0].iter().map(|c| c[0]).sum();
            let sum_y: f64 = polygon.coordinates[0].iter().map(|c| c[1]).sum();
            let n = polygon.coordinates[0].len() as f64;
            Ok((sum_x / n, sum_y / n))
        }
    }

    fn haversine_distance(&self, lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f32 {
        const R: f64 = 6_371_000.0;

        let phi1 = lat1.to_radians();
        let phi2 = lat2.to_radians();
        let delta_phi = (lat2 - lat1).to_radians();
        let delta_lambda = (lon2 - lon1).to_radians();

        let a = (delta_phi / 2.0).sin().powi(2)
            + phi1.cos() * phi2.cos() * (delta_lambda / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().asin();

        (R * c) as f32
    }

    pub fn calculate_polygon_area(&self, polygon: &GeoPolygon) -> DomainResult<f64> {
        if polygon.coordinates.is_empty() || polygon.coordinates[0].len() < 3 {
            return Ok(0.0);
        }

        let coords: Vec<Coord<f64>> = polygon.coordinates[0]
            .iter()
            .map(|c| Coord { x: c[0], y: c[1] })
            .collect();

        let line_string = LineString::new(coords);
        let geo_polygon = Polygon::new(line_string, vec![]);

        let area_deg2 = geo_polygon.unsigned_area();
        let area_m2 = area_deg2 * 111_320.0 * 111_320.0;
        let area_hectares = area_m2 / 10_000.0;

        Ok(area_hectares)
    }

    pub fn polygons_intersect(&self, p1: &GeoPolygon, p2: &GeoPolygon) -> bool {
        if p1.coordinates.is_empty() || p2.coordinates.is_empty() {
            return false;
        }

        let bbox1 = self.bounding_box(&p1.coordinates[0]);
        let bbox2 = self.bounding_box(&p2.coordinates[0]);

        bbox1.0 <= bbox2.2 && bbox1.2 >= bbox2.0 && bbox1.1 <= bbox2.3 && bbox1.3 >= bbox2.1
    }

    fn bounding_box(&self, coords: &[[f64; 2]]) -> (f64, f64, f64, f64) {
        let mut min_x = f64::MAX;
        let mut min_y = f64::MAX;
        let mut max_x = f64::MIN;
        let mut max_y = f64::MIN;

        for coord in coords {
            min_x = min_x.min(coord[0]);
            min_y = min_y.min(coord[1]);
            max_x = max_x.max(coord[0]);
            max_y = max_y.max(coord[1]);
        }

        (min_x, min_y, max_x, max_y)
    }

    pub fn point_in_polygon(&self, point: [f64; 2], polygon: &GeoPolygon) -> bool {
        if polygon.coordinates.is_empty() {
            return false;
        }

        let coords = &polygon.coordinates[0];
        let n = coords.len();
        if n < 3 {
            return false;
        }

        let mut inside = false;
        let mut j = n - 1;

        for i in 0..n {
            let xi = coords[i][0];
            let yi = coords[i][1];
            let xj = coords[j][0];
            let yj = coords[j][1];

            if ((yi > point[1]) != (yj > point[1]))
                && (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi)
            {
                inside = !inside;
            }

            j = i;
        }

        inside
    }
}

#[derive(Debug, Clone)]
pub struct PredictionResult {
    pub predicted_center: [f64; 2],
    pub distance_to_farm_m: f32,
    pub risk_level: RiskLevel,
    pub days_to_reach: Option<f32>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}
