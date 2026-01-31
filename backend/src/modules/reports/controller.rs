use axum::{
    extract::{Path, Query, State},
    response::IntoResponse,
    http::StatusCode,
    Extension, Json,
};
use chrono::Utc;
use crate::shared::{AppState, error::{AppResult, AppError}};
use crate::modules::auth::models::Claims;
use super::{models::*, repository};

pub async fn list_reports(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Query(query): Query<ReportListQuery>,
) -> AppResult<impl IntoResponse> {
    let limit = query.limit.unwrap_or(50).min(100);
    let offset = query.offset.unwrap_or(0);
    
    let reports = repository::list_reports(
        claims.sub,
        query.status.as_deref(),
        query.report_type.as_deref(),
        limit,
        offset,
        state.db(),
    ).await?;
    
    let responses: Vec<ReportResponse> = reports.into_iter().map(Into::into).collect();
    Ok(Json(responses))
}

pub async fn create_report(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<CreateReportRequest>,
) -> AppResult<impl IntoResponse> {
    let report = repository::create_report(claims.sub, &req, state.db()).await?;
    Ok((StatusCode::CREATED, Json(ReportResponse::from(report))))
}

pub async fn get_report(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let report = repository::get_report_by_id(id, claims.sub, state.db()).await?
        .ok_or_else(|| AppError::NotFound("Report not found".to_string()))?;
    
    Ok(Json(ReportResponse::from(report)))
}

pub async fn delete_report(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let deleted = repository::delete_report(id, claims.sub, state.db()).await?;
    
    if !deleted {
        return Err(AppError::NotFound("Report not found".to_string()));
    }
    
    Ok(Json(serde_json::json!({ "success": true })))
}

pub async fn download_report(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let report = repository::get_report_by_id(id, claims.sub, state.db()).await?
        .ok_or_else(|| AppError::NotFound("Report not found".to_string()))?;
    
    if report.status != "completed" {
        return Err(AppError::BadRequest("Report is not ready for download".to_string()));
    }
    
    // In a real implementation, this would return the file content
    // For now, return a placeholder response
    Ok(Json(serde_json::json!({
        "download_url": format!("/api/reports/files/{}", report.file_path.unwrap_or_default()),
        "filename": format!("{}.pdf", report.title.replace(" ", "_")),
        "size": report.file_size_bytes,
        "expires_at": (Utc::now() + chrono::Duration::hours(1)).to_rfc3339()
    })))
}

pub async fn generate_report(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<GenerateReportRequest>,
) -> AppResult<impl IntoResponse> {
    let title = req.title.unwrap_or_else(|| {
        let now = Utc::now();
        match req.report_type.as_str() {
            "performance" => format!("Performance Report - {}", now.format("%Y-%m-%d")),
            "risk_assessment" => format!("Risk Assessment - {}", now.format("%Y-%m-%d")),
            "resource_audit" => format!("Resource Audit - {}", now.format("%Y-%m-%d")),
            _ => format!("Report - {}", now.format("%Y-%m-%d %H:%M")),
        }
    });
    
    let create_req = CreateReportRequest {
        title,
        report_type: req.report_type,
        scheduled_for: None,
        parameters: req.parameters,
    };
    
    let report = repository::create_report(claims.sub, &create_req, state.db()).await?;
    
    // In a real implementation, this would trigger async report generation
    // For demo, we'll mark it as processing
    repository::update_report_status(report.id, "processing", Some(0), state.db()).await?;
    
    Ok((StatusCode::ACCEPTED, Json(serde_json::json!({
        "id": report.id.to_string(),
        "status": "processing",
        "message": "Report generation started"
    }))))
}

pub async fn export_data(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(format): Path<String>,
    Json(req): Json<ExportRequest>,
) -> AppResult<impl IntoResponse> {
    let valid_formats = ["json", "csv", "xlsx", "pdf"];
    if !valid_formats.contains(&format.as_str()) {
        return Err(AppError::BadRequest(format!("Invalid format: {}. Valid formats: {:?}", format, valid_formats)));
    }
    
    let (data, count) = repository::get_export_data(claims.sub, &req.data_type, state.db()).await?;
    
    let response = ExportResponse {
        format: format.clone(),
        data,
        generated_at: Utc::now(),
        record_count: count,
    };
    
    Ok(Json(response))
}

pub async fn get_templates() -> AppResult<impl IntoResponse> {
    let templates = vec![
        ReportTemplate {
            id: "performance".to_string(),
            title: "Performance".to_string(),
            description: "Yield and efficiency analysis".to_string(),
            report_type: "performance".to_string(),
            icon: "graph".to_string(),
            color: "blue".to_string(),
        },
        ReportTemplate {
            id: "risk_assessment".to_string(),
            title: "Risk Assessment".to_string(),
            description: "Identify potential threats".to_string(),
            report_type: "risk_assessment".to_string(),
            icon: "alert".to_string(),
            color: "rose".to_string(),
        },
        ReportTemplate {
            id: "resource_audit".to_string(),
            title: "Resource Audit".to_string(),
            description: "Water and cost optimization".to_string(),
            report_type: "resource_audit".to_string(),
            icon: "water".to_string(),
            color: "indigo".to_string(),
        },
    ];
    
    Ok(Json(templates))
}
