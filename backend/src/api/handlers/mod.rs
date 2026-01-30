pub mod auth;
pub mod chatbot;
pub mod farm;
pub mod health;
pub mod monitoring;

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;

use crate::domain::DomainError;

#[derive(Serialize)]
pub struct ApiResponse<T: Serialize> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(message: impl Into<String>) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message.into()),
        }
    }
}

impl IntoResponse for DomainError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            DomainError::NotFound(_) => (StatusCode::NOT_FOUND, self.to_string()),
            DomainError::Validation(_) => (StatusCode::BAD_REQUEST, self.to_string()),
            DomainError::Authentication(_) => (StatusCode::UNAUTHORIZED, self.to_string()),
            DomainError::Authorization(_) => (StatusCode::FORBIDDEN, self.to_string()),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };

        let body = ApiResponse::<()>::error(message);
        (status, Json(body)).into_response()
    }
}
