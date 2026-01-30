use thiserror::Error;

#[derive(Error, Debug)]
pub enum DomainError {
    #[error("Entity not found: {0}")]
    NotFound(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Database error: {0}")]
    Database(String),

    #[error("AI inference error: {0}")]
    AiInference(String),

    #[error("Satellite API error: {0}")]
    SatelliteApi(String),

    #[error("GeoProcessing error: {0}")]
    GeoProcessing(String),

    #[error("Image processing error: {0}")]
    ImageProcessing(String),

    #[error("Authentication error: {0}")]
    Authentication(String),

    #[error("Authorization error: {0}")]
    Authorization(String),

    #[error("Internal error: {0}")]
    Internal(String),
}

impl DomainError {
    pub fn not_found(entity: impl Into<String>) -> Self {
        Self::NotFound(entity.into())
    }

    pub fn validation(msg: impl Into<String>) -> Self {
        Self::Validation(msg.into())
    }

    pub fn database(msg: impl Into<String>) -> Self {
        Self::Database(msg.into())
    }

    pub fn ai_inference(msg: impl Into<String>) -> Self {
        Self::AiInference(msg.into())
    }

    pub fn satellite_api(msg: impl Into<String>) -> Self {
        Self::SatelliteApi(msg.into())
    }

    pub fn geo_processing(msg: impl Into<String>) -> Self {
        Self::GeoProcessing(msg.into())
    }

    pub fn image_processing(msg: impl Into<String>) -> Self {
        Self::ImageProcessing(msg.into())
    }
}

pub type DomainResult<T> = Result<T, DomainError>;
