use bytes::Bytes;
use chrono::{DateTime, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;

use crate::config::SentinelConfig;
use crate::domain::{DomainError, DomainResult, GeoPolygon, SatelliteSource};

pub struct SentinelClient {
    client: Client,
    config: SentinelConfig,
    access_token: Arc<RwLock<Option<AccessToken>>>,
}

#[derive(Debug, Clone)]
struct AccessToken {
    token: String,
    expires_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
struct TokenRequest {
    grant_type: String,
    client_id: String,
    client_secret: String,
}

#[derive(Debug, Deserialize)]
struct TokenResponse {
    access_token: String,
    expires_in: i64,
}

#[derive(Debug, Serialize)]
pub struct SearchRequest {
    pub bbox: [f64; 4],
    pub datetime: String,
    pub collections: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub query: Option<SearchQuery>,
}

#[derive(Debug, Serialize)]
pub struct SearchQuery {
    #[serde(rename = "eo:cloud_cover")]
    pub cloud_cover: CloudCoverFilter,
}

#[derive(Debug, Serialize)]
pub struct CloudCoverFilter {
    pub lt: f32,
}

#[derive(Debug, Deserialize)]
pub struct SearchResponse {
    pub features: Vec<SatelliteFeature>,
    #[serde(default)]
    pub context: SearchContext,
}

#[derive(Debug, Deserialize, Default)]
pub struct SearchContext {
    #[serde(default)]
    pub matched: u32,
    #[serde(default)]
    pub returned: u32,
}

#[derive(Debug, Deserialize)]
pub struct SatelliteFeature {
    pub id: String,
    pub geometry: GeoJsonGeometry,
    pub properties: FeatureProperties,
    pub assets: FeatureAssets,
}

#[derive(Debug, Deserialize)]
pub struct GeoJsonGeometry {
    #[serde(rename = "type")]
    pub geometry_type: String,
    pub coordinates: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct FeatureProperties {
    pub datetime: String,
    #[serde(rename = "eo:cloud_cover")]
    pub cloud_cover: Option<f32>,
    pub platform: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct FeatureAssets {
    #[serde(flatten)]
    pub bands: std::collections::HashMap<String, BandAsset>,
}

#[derive(Debug, Deserialize)]
pub struct BandAsset {
    pub href: String,
    #[serde(rename = "type")]
    pub asset_type: Option<String>,
}

#[derive(Debug, Clone)]
pub struct DownloadedImage {
    pub id: String,
    pub source: SatelliteSource,
    pub acquisition_date: DateTime<Utc>,
    pub cloud_cover: f32,
    pub geometry: GeoPolygon,
    pub bands: Vec<BandData>,
}

#[derive(Debug, Clone)]
pub struct BandData {
    pub name: String,
    pub data: Bytes,
    pub resolution: f32,
}

impl SentinelClient {
    pub fn new(config: SentinelConfig) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(300))
            .connect_timeout(Duration::from_secs(30))
            .pool_max_idle_per_host(10)
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            config,
            access_token: Arc::new(RwLock::new(None)),
        }
    }

    async fn ensure_token(&self) -> DomainResult<String> {
        {
            let token_guard = self.access_token.read().await;
            if let Some(ref token) = *token_guard {
                if token.expires_at > Utc::now() + chrono::Duration::minutes(5) {
                    return Ok(token.token.clone());
                }
            }
        }

        let mut token_guard = self.access_token.write().await;
        
        if let Some(ref token) = *token_guard {
            if token.expires_at > Utc::now() + chrono::Duration::minutes(5) {
                return Ok(token.token.clone());
            }
        }

        let token_url = format!("{}/oauth/token", self.config.api_url);
        
        let response = self
            .client
            .post(&token_url)
            .form(&[
                ("grant_type", "client_credentials"),
                ("client_id", &self.config.client_id),
                ("client_secret", &self.config.client_secret),
            ])
            .send()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Token request failed: {}", e)))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            return Err(DomainError::satellite_api(format!(
                "Token request failed with status {}: {}",
                status, body
            )));
        }

        let token_response: TokenResponse = response
            .json()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Failed to parse token response: {}", e)))?;

        let new_token = AccessToken {
            token: token_response.access_token.clone(),
            expires_at: Utc::now() + chrono::Duration::seconds(token_response.expires_in),
        };

        *token_guard = Some(new_token);

        Ok(token_response.access_token)
    }

    pub async fn search(
        &self,
        bbox: [f64; 4],
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
        max_cloud_cover: f32,
        sources: Vec<SatelliteSource>,
    ) -> DomainResult<Vec<SatelliteFeature>> {
        let token = self.ensure_token().await?;

        let collections: Vec<String> = sources
            .iter()
            .map(|s| match s {
                SatelliteSource::Sentinel2 => "sentinel-2-l2a".to_string(),
                SatelliteSource::Sentinel1 => "sentinel-1-grd".to_string(),
                SatelliteSource::Landsat8 => "landsat-c2-l2".to_string(),
            })
            .collect();

        let datetime = format!(
            "{}/{}",
            start_date.format("%Y-%m-%dT%H:%M:%SZ"),
            end_date.format("%Y-%m-%dT%H:%M:%SZ")
        );

        let request = SearchRequest {
            bbox,
            datetime,
            collections,
            limit: Some(100),
            query: Some(SearchQuery {
                cloud_cover: CloudCoverFilter { lt: max_cloud_cover },
            }),
        };

        let search_url = format!("{}/api/v1/catalog/1.0.0/search", self.config.api_url);

        let response = self
            .client
            .post(&search_url)
            .bearer_auth(&token)
            .json(&request)
            .send()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Search request failed: {}", e)))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            return Err(DomainError::satellite_api(format!(
                "Search failed with status {}: {}",
                status, body
            )));
        }

        let search_response: SearchResponse = response
            .json()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Failed to parse search response: {}", e)))?;

        tracing::info!(
            "Found {} satellite images (matched: {})",
            search_response.context.returned,
            search_response.context.matched
        );

        Ok(search_response.features)
    }

    pub async fn download_band(&self, band_url: &str) -> DomainResult<Bytes> {
        let token = self.ensure_token().await?;

        let response = self
            .client
            .get(band_url)
            .bearer_auth(&token)
            .send()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Band download failed: {}", e)))?;

        if !response.status().is_success() {
            let status = response.status();
            return Err(DomainError::satellite_api(format!(
                "Band download failed with status {}",
                status
            )));
        }

        let bytes = response
            .bytes()
            .await
            .map_err(|e| DomainError::satellite_api(format!("Failed to read band data: {}", e)))?;

        Ok(bytes)
    }

    pub async fn download_image(
        &self,
        feature: &SatelliteFeature,
        bands: &[&str],
    ) -> DomainResult<DownloadedImage> {
        let mut band_data = Vec::new();

        for band_name in bands {
            if let Some(asset) = feature.assets.bands.get(*band_name) {
                let data = self.download_band(&asset.href).await?;
                band_data.push(BandData {
                    name: band_name.to_string(),
                    data,
                    resolution: self.get_band_resolution(band_name),
                });
            }
        }

        let acquisition_date = DateTime::parse_from_rfc3339(&feature.properties.datetime)
            .map(|dt| dt.with_timezone(&Utc))
            .unwrap_or_else(|_| Utc::now());

        let source = feature
            .properties
            .platform
            .as_ref()
            .map(|p| {
                if p.contains("sentinel-2") {
                    SatelliteSource::Sentinel2
                } else if p.contains("sentinel-1") {
                    SatelliteSource::Sentinel1
                } else {
                    SatelliteSource::Landsat8
                }
            })
            .unwrap_or(SatelliteSource::Sentinel2);

        Ok(DownloadedImage {
            id: feature.id.clone(),
            source,
            acquisition_date,
            cloud_cover: feature.properties.cloud_cover.unwrap_or(0.0),
            geometry: self.convert_geometry(&feature.geometry),
            bands: band_data,
        })
    }

    fn get_band_resolution(&self, band_name: &str) -> f32 {
        match band_name {
            "B02" | "B03" | "B04" | "B08" => 10.0,
            "B05" | "B06" | "B07" | "B8A" | "B11" | "B12" => 20.0,
            "B01" | "B09" | "B10" => 60.0,
            _ => 10.0,
        }
    }

    fn convert_geometry(&self, geo: &GeoJsonGeometry) -> GeoPolygon {
        let coordinates = if let serde_json::Value::Array(coords) = &geo.coordinates {
            coords
                .iter()
                .filter_map(|ring| {
                    if let serde_json::Value::Array(points) = ring {
                        Some(
                            points
                                .iter()
                                .filter_map(|p| {
                                    if let serde_json::Value::Array(coord) = p {
                                        if coord.len() >= 2 {
                                            Some([
                                                coord[0].as_f64().unwrap_or(0.0),
                                                coord[1].as_f64().unwrap_or(0.0),
                                            ])
                                        } else {
                                            None
                                        }
                                    } else {
                                        None
                                    }
                                })
                                .collect()
                        )
                    } else {
                        None
                    }
                })
                .collect()
        } else {
            vec![]
        };

        GeoPolygon {
            coordinates,
            crs: "EPSG:4326".to_string(),
        }
    }
}
