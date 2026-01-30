// Disabled for Windows native build - uncomment when using Docker/Linux
// use ndarray::{Array4, ArrayView4};
// use ort::{
//     session::{builder::GraphOptimizationLevel, Session},
//     value::Value,
// };
use parking_lot::RwLock;
use std::path::Path;
use std::sync::Arc;

use crate::domain::{DomainError, DomainResult, GeoPolygon};

pub struct SegmentationModel {
    // session: Arc<RwLock<Session>>,
    model_version: String,
    input_height: usize,
    input_width: usize,
    num_classes: usize,
}

#[derive(Debug, Clone)]
pub struct SegmentationInput {
    // pub data: Array4<f32>,
    pub timestamps: Vec<i64>,
}

#[derive(Debug, Clone)]
pub struct SegmentationOutput {
    pub class_masks: Vec<ClassMask>,
    // pub confidence_map: Array4<f32>,
}

#[derive(Debug, Clone)]
pub struct ClassMask {
    pub class_id: u32,
    pub class_name: String,
    pub mask: Vec<Vec<bool>>,
    pub confidence: f32,
}

impl SegmentationModel {
    pub fn load<P: AsRef<Path>>(_model_path: P) -> DomainResult<Self> {
        // Disabled for Windows native build
        tracing::warn!("ONNX model loading disabled - using stub implementation");

        Ok(Self {
            // session: Arc::new(RwLock::new(session)),
            model_version: "hls-foundation-v1-stub".to_string(),
            input_height: 224,
            input_width: 224,
            num_classes: 10,
        })
    }

    pub fn preprocess(&self, _image_data: &[f32], _height: usize, _width: usize) -> Vec<f32> {
        // Stub implementation
        vec![0.0; self.input_height * self.input_width * 3]
    }

    pub fn infer(&self, _input: &[f32]) -> DomainResult<SegmentationOutput> {
        // Stub implementation
        tracing::warn!("ONNX inference disabled - returning empty result");
        
        Ok(SegmentationOutput {
            class_masks: vec![],
            // confidence_map,
        })
    }

    fn extract_class_masks(&self, _confidence_map: &[f32]) -> Vec<ClassMask> {
        let class_names = vec![
            "background", "rice", "durian", "mango", "coconut",
            "forest", "water", "bare_soil", "urban", "other",
        ];

        let height = confidence_map.shape()[2];
        let width = confidence_map.shape()[3];

        let mut masks = Vec::new();

        for class_id in 0..self.num_classes.min(confidence_map.shape()[1]) {
            let mut mask = vec![vec![false; width]; height];
            let mut total_confidence = 0.0;
            let mut pixel_count = 0;

            for h in 0..height {
                for w in 0..width {
                    let conf = confidence_map[[0, class_id, h, w]];
                    if conf > 0.5 {
                        mask[h][w] = true;
                        total_confidence += conf;
                        pixel_count += 1;
                    }
                }
            }

            let avg_confidence = if pixel_count > 0 {
                total_confidence / pixel_count as f32
            } else {
                0.0
            };

            if pixel_count > 0 {
                masks.push(ClassMask {
                    class_id: class_id as u32,
                    class_name: class_names.get(class_id).unwrap_or(&"unknown").to_string(),
                    mask,
                    confidence: avg_confidence,
                });
            }
        }

        masks
    }

    pub fn mask_to_polygons(&self, mask: &ClassMask, geo_transform: &GeoTransform) -> Vec<GeoPolygon> {
        let mut polygons = Vec::new();
        let height = mask.mask.len();
        let width = if height > 0 { mask.mask[0].len() } else { 0 };

        let mut visited = vec![vec![false; width]; height];

        for y in 0..height {
            for x in 0..width {
                if mask.mask[y][x] && !visited[y][x] {
                    if let Some(polygon) = self.trace_polygon(&mask.mask, &mut visited, x, y, geo_transform) {
                        polygons.push(polygon);
                    }
                }
            }
        }

        polygons
    }

    fn trace_polygon(
        &self,
        mask: &[Vec<bool>],
        visited: &mut [Vec<bool>],
        start_x: usize,
        start_y: usize,
        geo_transform: &GeoTransform,
    ) -> Option<GeoPolygon> {
        let mut boundary = Vec::new();
        let mut stack = vec![(start_x, start_y)];

        while let Some((x, y)) = stack.pop() {
            if visited[y][x] {
                continue;
            }
            visited[y][x] = true;

            let (lon, lat) = geo_transform.pixel_to_coord(x as f64, y as f64);
            boundary.push([lon, lat]);

            let neighbors = [(0i32, -1i32), (1, 0), (0, 1), (-1, 0)];
            for (dx, dy) in neighbors {
                let nx = x as i32 + dx;
                let ny = y as i32 + dy;

                if nx >= 0 && ny >= 0 {
                    let nx = nx as usize;
                    let ny = ny as usize;
                    if ny < mask.len() && nx < mask[0].len() && mask[ny][nx] && !visited[ny][nx] {
                        stack.push((nx, ny));
                    }
                }
            }
        }

        if boundary.len() >= 3 {
            boundary.push(boundary[0]);
            Some(GeoPolygon {
                coordinates: vec![boundary],
                crs: "EPSG:4326".to_string(),
            })
        } else {
            None
        }
    }

    pub fn model_version(&self) -> &str {
        &self.model_version
    }
}

#[derive(Debug, Clone)]
pub struct GeoTransform {
    pub origin_x: f64,
    pub origin_y: f64,
    pub pixel_width: f64,
    pub pixel_height: f64,
    pub rotation_x: f64,
    pub rotation_y: f64,
}

impl GeoTransform {
    pub fn new(origin_x: f64, origin_y: f64, pixel_width: f64, pixel_height: f64) -> Self {
        Self {
            origin_x,
            origin_y,
            pixel_width,
            pixel_height,
            rotation_x: 0.0,
            rotation_y: 0.0,
        }
    }

    pub fn pixel_to_coord(&self, x: f64, y: f64) -> (f64, f64) {
        let lon = self.origin_x + x * self.pixel_width + y * self.rotation_x;
        let lat = self.origin_y + x * self.rotation_y + y * self.pixel_height;
        (lon, lat)
    }

    pub fn coord_to_pixel(&self, lon: f64, lat: f64) -> (f64, f64) {
        let x = (lon - self.origin_x) / self.pixel_width;
        let y = (lat - self.origin_y) / self.pixel_height;
        (x, y)
    }
}
