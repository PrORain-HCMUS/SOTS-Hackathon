use std::sync::Arc;
use std::time::Instant;
use uuid::Uuid;

use crate::domain::{
    Alert, AlertMetadata, AlertSeverity, AlertType, DomainResult, IntrusionVector, SpectralIndices,
};
use crate::infrastructure::{
    ai::{SegmentationModel, SpectralAnalyzer},
    geo::VectorAnalyzer,
    satellite::SentinelClient,
    Database,
};

use super::dtos::{
    ProcessImageRequest, ProcessImageResult, RiskLevelDto, SalinityStatusDto, SalinityTrendDto,
};

pub struct AnalyzeService {
    db: Database,
    segmentation_model: Option<Arc<SegmentationModel>>,
    spectral_analyzer: SpectralAnalyzer,
    vector_analyzer: VectorAnalyzer,
    sentinel_client: Arc<SentinelClient>,
}

impl AnalyzeService {
    pub fn new(
        db: Database,
        segmentation_model: Option<Arc<SegmentationModel>>,
        sentinel_client: Arc<SentinelClient>,
    ) -> Self {
        Self {
            db,
            segmentation_model,
            spectral_analyzer: SpectralAnalyzer::new(),
            vector_analyzer: VectorAnalyzer::new(),
            sentinel_client,
        }
    }

    pub async fn process_satellite_image(
        &self,
        request: ProcessImageRequest,
    ) -> DomainResult<ProcessImageResult> {
        let start = Instant::now();

        let processed_farms = Vec::new();
        let alerts_generated = Vec::new();

        let processing_time_ms = start.elapsed().as_millis() as u64;

        Ok(ProcessImageResult {
            image_id: request.image_id,
            processed_farms,
            alerts_generated,
            processing_time_ms,
        })
    }

    pub async fn get_salinity_status(&self, farm_id: Uuid) -> DomainResult<SalinityStatusDto> {
        Ok(SalinityStatusDto {
            farm_id,
            current_ndsi: 0.0,
            baseline_ndsi: 0.0,
            deviation_percentage: 0.0,
            trend: SalinityTrendDto::Stable,
            risk_level: RiskLevelDto::Low,
            last_updated: chrono::Utc::now(),
        })
    }

    pub async fn calculate_intrusion_vector(
        &self,
        _farm_id: Uuid,
    ) -> DomainResult<Option<IntrusionVector>> {
        Ok(None)
    }

    pub fn detect_anomaly(
        &self,
        current_indices: &SpectralIndices,
        historical_indices: &[SpectralIndices],
    ) -> Option<(AlertType, AlertSeverity, String)> {
        if historical_indices.is_empty() {
            return None;
        }

        let historical_ndsi: Vec<f32> = historical_indices
            .iter()
            .filter_map(|i| i.ndsi)
            .collect();

        if let Some(current_ndsi) = current_indices.ndsi {
            let detection = self.spectral_analyzer.detect_peak_valley(
                current_ndsi,
                &historical_ndsi,
                crate::domain::SpectralIndexType::Ndsi,
            );

            if detection.detection_type == crate::domain::DetectionType::Peak {
                let severity = if detection.deviation_percentage > 50.0 {
                    AlertSeverity::Critical
                } else if detection.deviation_percentage > 30.0 {
                    AlertSeverity::High
                } else if detection.deviation_percentage > 15.0 {
                    AlertSeverity::Medium
                } else {
                    AlertSeverity::Low
                };

                return Some((
                    AlertType::SalinityIntrusion,
                    severity,
                    format!(
                        "NDSI increased by {:.1}% from baseline",
                        detection.deviation_percentage
                    ),
                ));
            }
        }

        if let Some(current_red_edge) = current_indices.red_edge_index {
            let historical_red_edge: Vec<f32> = historical_indices
                .iter()
                .filter_map(|i| i.red_edge_index)
                .collect();

            let detection = self.spectral_analyzer.detect_peak_valley(
                current_red_edge,
                &historical_red_edge,
                crate::domain::SpectralIndexType::RedEdge,
            );

            if detection.detection_type == crate::domain::DetectionType::Valley {
                let severity = if detection.deviation_percentage.abs() > 40.0 {
                    AlertSeverity::High
                } else if detection.deviation_percentage.abs() > 20.0 {
                    AlertSeverity::Medium
                } else {
                    AlertSeverity::Low
                };

                return Some((
                    AlertType::CropStress,
                    severity,
                    format!(
                        "Red Edge index decreased by {:.1}%, indicating potential crop stress",
                        detection.deviation_percentage.abs()
                    ),
                ));
            }
        }

        None
    }

    pub fn create_alert(
        &self,
        farm_id: Uuid,
        alert_type: AlertType,
        severity: AlertSeverity,
        description: String,
        intrusion_vector: Option<IntrusionVector>,
    ) -> Alert {
        let title = match alert_type {
            AlertType::SalinityIntrusion => "Cảnh báo xâm nhập mặn".to_string(),
            AlertType::CropStress => "Cảnh báo stress cây trồng".to_string(),
            AlertType::Deforestation => "Cảnh báo phá rừng".to_string(),
            AlertType::AnomalyDetected => "Phát hiện bất thường".to_string(),
        };

        Alert {
            id: Uuid::new_v4(),
            farm_id,
            alert_type,
            severity,
            title,
            description,
            geometry: None,
            detected_at: chrono::Utc::now(),
            acknowledged: false,
            acknowledged_at: None,
            metadata: AlertMetadata {
                intrusion_vector,
                ..Default::default()
            },
        }
    }
}
