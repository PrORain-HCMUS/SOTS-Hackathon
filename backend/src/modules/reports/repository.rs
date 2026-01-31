use sqlx::PgPool;
use crate::shared::error::AppResult;
use super::models::{Report, CreateReportRequest};

pub async fn create_report(
    user_id: i64,
    req: &CreateReportRequest,
    db: &PgPool,
) -> AppResult<Report> {
    let report = sqlx::query_as!(
        Report,
        r#"
        INSERT INTO reports (user_id, title, report_type, status, scheduled_for, parameters)
        VALUES ($1, $2, $3, 'scheduled', $4, $5)
        RETURNING id, user_id, title, report_type, status, progress, file_path, 
                  file_size_bytes, parameters, generated_at, scheduled_for, created_at, updated_at
        "#,
        user_id,
        req.title,
        req.report_type,
        req.scheduled_for,
        req.parameters
    )
    .fetch_one(db)
    .await?;
    
    Ok(report)
}

pub async fn get_report_by_id(id: i64, user_id: i64, db: &PgPool) -> AppResult<Option<Report>> {
    let report = sqlx::query_as!(
        Report,
        r#"
        SELECT id, user_id, title, report_type, status, progress, file_path, 
               file_size_bytes, parameters, generated_at, scheduled_for, created_at, updated_at
        FROM reports
        WHERE id = $1 AND user_id = $2
        "#,
        id,
        user_id
    )
    .fetch_optional(db)
    .await?;
    
    Ok(report)
}

pub async fn list_reports(
    user_id: i64,
    status: Option<&str>,
    report_type: Option<&str>,
    limit: i64,
    offset: i64,
    db: &PgPool,
) -> AppResult<Vec<Report>> {
    let reports = sqlx::query_as!(
        Report,
        r#"
        SELECT id, user_id, title, report_type, status, progress, file_path, 
               file_size_bytes, parameters, generated_at, scheduled_for, created_at, updated_at
        FROM reports
        WHERE user_id = $1
        AND ($2::text IS NULL OR status = $2)
        AND ($3::text IS NULL OR report_type = $3)
        ORDER BY created_at DESC
        LIMIT $4 OFFSET $5
        "#,
        user_id,
        status,
        report_type,
        limit,
        offset
    )
    .fetch_all(db)
    .await?;
    
    Ok(reports)
}

pub async fn delete_report(id: i64, user_id: i64, db: &PgPool) -> AppResult<bool> {
    let result = sqlx::query!(
        "DELETE FROM reports WHERE id = $1 AND user_id = $2",
        id,
        user_id
    )
    .execute(db)
    .await?;
    
    Ok(result.rows_affected() > 0)
}

pub async fn update_report_status(
    id: i64,
    status: &str,
    progress: Option<i32>,
    db: &PgPool,
) -> AppResult<()> {
    sqlx::query!(
        r#"
        UPDATE reports 
        SET status = $2, progress = $3, updated_at = NOW()
        WHERE id = $1
        "#,
        id,
        status,
        progress
    )
    .execute(db)
    .await?;
    
    Ok(())
}

pub async fn complete_report(
    id: i64,
    file_path: &str,
    file_size: i64,
    db: &PgPool,
) -> AppResult<()> {
    sqlx::query!(
        r#"
        UPDATE reports 
        SET status = 'completed', progress = 100, file_path = $2, 
            file_size_bytes = $3, generated_at = NOW(), updated_at = NOW()
        WHERE id = $1
        "#,
        id,
        file_path,
        file_size
    )
    .execute(db)
    .await?;
    
    Ok(())
}

pub async fn get_export_data(
    user_id: i64,
    data_type: &str,
    db: &PgPool,
) -> AppResult<(serde_json::Value, i64)> {
    match data_type {
        "farms" => {
            let farms = sqlx::query!(
                r#"
                SELECT id, name, area_hectares, created_at
                FROM farms
                WHERE user_id = $1
                ORDER BY created_at DESC
                "#,
                user_id
            )
            .fetch_all(db)
            .await?;
            
            let count = farms.len() as i64;
            let data: Vec<serde_json::Value> = farms.into_iter().map(|f| {
                serde_json::json!({
                    "id": f.id,
                    "name": f.name,
                    "area_hectares": f.area_hectares.map(|v| v.to_string()),
                    "created_at": f.created_at.to_rfc3339()
                })
            }).collect();
            
            Ok((serde_json::json!(data), count))
        }
        "alerts" => {
            let alerts = sqlx::query!(
                r#"
                SELECT a.id, a.severity, a.message, a.detected_at, f.name as farm_name
                FROM alerts a
                JOIN farms f ON f.id = a.farm_id
                WHERE f.user_id = $1
                ORDER BY a.detected_at DESC
                LIMIT 1000
                "#,
                user_id
            )
            .fetch_all(db)
            .await?;
            
            let count = alerts.len() as i64;
            let data: Vec<serde_json::Value> = alerts.into_iter().map(|a| {
                serde_json::json!({
                    "id": a.id,
                    "severity": a.severity,
                    "message": a.message,
                    "farm_name": a.farm_name,
                    "detected_at": a.detected_at.to_rfc3339()
                })
            }).collect();
            
            Ok((serde_json::json!(data), count))
        }
        "analytics" => {
            let metrics = sqlx::query!(
                r#"
                SELECT r.name as region, rm.metric_date, rm.avg_yield_per_hectare, 
                       rm.efficiency_percentage, rm.risk_level
                FROM regional_metrics rm
                JOIN regions r ON r.id = rm.region_id
                ORDER BY rm.metric_date DESC
                LIMIT 500
                "#
            )
            .fetch_all(db)
            .await?;
            
            let count = metrics.len() as i64;
            let data: Vec<serde_json::Value> = metrics.into_iter().map(|m| {
                serde_json::json!({
                    "region": m.region,
                    "date": m.metric_date.to_string(),
                    "avg_yield": m.avg_yield_per_hectare.map(|v| v.to_string()),
                    "efficiency": m.efficiency_percentage.map(|v| v.to_string()),
                    "risk_level": m.risk_level
                })
            }).collect();
            
            Ok((serde_json::json!(data), count))
        }
        _ => Ok((serde_json::json!([]), 0))
    }
}
