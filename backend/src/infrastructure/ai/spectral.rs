use ndarray::{Array2, ArrayView2};

use crate::domain::{
    DetectionType, DomainError, DomainResult, PeakValleyDetection, SpectralIndexType,
    SpectralMeanValues,
};

pub struct SpectralAnalyzer {
    peak_threshold: f32,
    valley_threshold: f32,
    smoothing_window: usize,
}

impl Default for SpectralAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

impl SpectralAnalyzer {
    pub fn new() -> Self {
        Self {
            peak_threshold: 0.15,
            valley_threshold: -0.15,
            smoothing_window: 3,
        }
    }

    pub fn with_thresholds(mut self, peak: f32, valley: f32) -> Self {
        self.peak_threshold = peak;
        self.valley_threshold = valley;
        self
    }

    pub fn calculate_ndvi(&self, nir: ArrayView2<f32>, red: ArrayView2<f32>) -> DomainResult<Array2<f32>> {
        if nir.shape() != red.shape() {
            return Err(DomainError::image_processing("NIR and Red bands must have same shape"));
        }

        let mut ndvi = Array2::zeros(nir.raw_dim());
        
        for ((i, j), val) in ndvi.indexed_iter_mut() {
            let nir_val = nir[[i, j]];
            let red_val = red[[i, j]];
            let sum = nir_val + red_val;
            
            *val = if sum.abs() > 1e-6 {
                (nir_val - red_val) / sum
            } else {
                0.0
            };
        }

        Ok(ndvi)
    }

    pub fn calculate_ndsi(&self, swir: ArrayView2<f32>, green: ArrayView2<f32>) -> DomainResult<Array2<f32>> {
        if swir.shape() != green.shape() {
            return Err(DomainError::image_processing("SWIR and Green bands must have same shape"));
        }

        let mut ndsi = Array2::zeros(swir.raw_dim());
        
        for ((i, j), val) in ndsi.indexed_iter_mut() {
            let swir_val = swir[[i, j]];
            let green_val = green[[i, j]];
            let sum = swir_val + green_val;
            
            *val = if sum.abs() > 1e-6 {
                (green_val - swir_val) / sum
            } else {
                0.0
            };
        }

        Ok(ndsi)
    }

    pub fn calculate_srvi(&self, nir: ArrayView2<f32>, red: ArrayView2<f32>) -> DomainResult<Array2<f32>> {
        if nir.shape() != red.shape() {
            return Err(DomainError::image_processing("NIR and Red bands must have same shape"));
        }

        let mut srvi = Array2::zeros(nir.raw_dim());
        
        for ((i, j), val) in srvi.indexed_iter_mut() {
            let nir_val = nir[[i, j]];
            let red_val = red[[i, j]];
            
            *val = if red_val.abs() > 1e-6 {
                nir_val / red_val
            } else {
                0.0
            };
        }

        Ok(srvi)
    }

    pub fn calculate_red_edge_index(
        &self,
        red_edge: ArrayView2<f32>,
        red: ArrayView2<f32>,
    ) -> DomainResult<Array2<f32>> {
        if red_edge.shape() != red.shape() {
            return Err(DomainError::image_processing("Red Edge and Red bands must have same shape"));
        }

        let mut rei = Array2::zeros(red_edge.raw_dim());
        
        for ((i, j), val) in rei.indexed_iter_mut() {
            let re_val = red_edge[[i, j]];
            let red_val = red[[i, j]];
            let sum = re_val + red_val;
            
            *val = if sum.abs() > 1e-6 {
                (re_val - red_val) / sum
            } else {
                0.0
            };
        }

        Ok(rei)
    }

    pub fn compute_mean_values(&self, indices: &SpectralIndicesData) -> SpectralMeanValues {
        SpectralMeanValues {
            ndvi_mean: self.mean(&indices.ndvi),
            ndvi_std: self.std(&indices.ndvi),
            ndsi_mean: self.mean(&indices.ndsi),
            ndsi_std: self.std(&indices.ndsi),
            red_edge_mean: self.mean(&indices.red_edge),
            red_edge_std: self.std(&indices.red_edge),
        }
    }

    fn mean(&self, array: &Array2<f32>) -> f32 {
        let sum: f32 = array.iter().sum();
        let count = array.len();
        if count > 0 {
            sum / count as f32
        } else {
            0.0
        }
    }

    fn std(&self, array: &Array2<f32>) -> f32 {
        let mean = self.mean(array);
        let variance: f32 = array.iter().map(|&x| (x - mean).powi(2)).sum::<f32>() / array.len() as f32;
        variance.sqrt()
    }

    pub fn detect_peak_valley(
        &self,
        current_value: f32,
        historical_values: &[f32],
        index_type: SpectralIndexType,
    ) -> PeakValleyDetection {
        let baseline = if historical_values.is_empty() {
            current_value
        } else {
            historical_values.iter().sum::<f32>() / historical_values.len() as f32
        };

        let deviation = if baseline.abs() > 1e-6 {
            (current_value - baseline) / baseline
        } else {
            0.0
        };

        let detection_type = if deviation > self.peak_threshold {
            DetectionType::Peak
        } else if deviation < self.valley_threshold {
            DetectionType::Valley
        } else {
            DetectionType::Normal
        };

        PeakValleyDetection {
            timestamp: chrono::Utc::now(),
            index_type,
            value: current_value,
            detection_type,
            baseline_value: baseline,
            deviation_percentage: deviation * 100.0,
        }
    }

    pub fn analyze_salinity_trend(&self, ndsi_series: &[f32]) -> SalinityTrend {
        if ndsi_series.len() < 2 {
            return SalinityTrend::Stable;
        }

        let smoothed = self.smooth_series(ndsi_series);
        let slope = self.calculate_slope(&smoothed);

        if slope > 0.02 {
            SalinityTrend::Increasing
        } else if slope < -0.02 {
            SalinityTrend::Decreasing
        } else {
            SalinityTrend::Stable
        }
    }

    fn smooth_series(&self, series: &[f32]) -> Vec<f32> {
        if series.len() < self.smoothing_window {
            return series.to_vec();
        }

        let mut smoothed = Vec::with_capacity(series.len());
        let half_window = self.smoothing_window / 2;

        for i in 0..series.len() {
            let start = i.saturating_sub(half_window);
            let end = (i + half_window + 1).min(series.len());
            let window_sum: f32 = series[start..end].iter().sum();
            smoothed.push(window_sum / (end - start) as f32);
        }

        smoothed
    }

    fn calculate_slope(&self, series: &[f32]) -> f32 {
        if series.len() < 2 {
            return 0.0;
        }

        let n = series.len() as f32;
        let x_mean = (n - 1.0) / 2.0;
        let y_mean: f32 = series.iter().sum::<f32>() / n;

        let mut numerator = 0.0;
        let mut denominator = 0.0;

        for (i, &y) in series.iter().enumerate() {
            let x = i as f32;
            numerator += (x - x_mean) * (y - y_mean);
            denominator += (x - x_mean).powi(2);
        }

        if denominator.abs() > 1e-6 {
            numerator / denominator
        } else {
            0.0
        }
    }
}

pub struct SpectralIndicesData {
    pub ndvi: Array2<f32>,
    pub ndsi: Array2<f32>,
    pub srvi: Array2<f32>,
    pub red_edge: Array2<f32>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum SalinityTrend {
    Increasing,
    Decreasing,
    Stable,
}
