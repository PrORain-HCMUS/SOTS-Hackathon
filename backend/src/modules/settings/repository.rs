use sqlx::PgPool;
use crate::shared::error::AppResult;
use super::models::{UserPreferences, Integration, UpdatePreferencesRequest};

pub async fn get_or_create_preferences(user_id: i64, db: &PgPool) -> AppResult<UserPreferences> {
    // Try to get existing preferences
    let existing = sqlx::query_as!(
        UserPreferences,
        r#"
        SELECT id, user_id, auto_refresh, refresh_interval_minutes, notifications_enabled,
               email_alerts_enabled, data_retention_days, theme, language, created_at, updated_at
        FROM user_preferences
        WHERE user_id = $1
        "#,
        user_id
    )
    .fetch_optional(db)
    .await?;
    
    if let Some(prefs) = existing {
        return Ok(prefs);
    }
    
    // Create default preferences
    let prefs = sqlx::query_as!(
        UserPreferences,
        r#"
        INSERT INTO user_preferences (user_id)
        VALUES ($1)
        RETURNING id, user_id, auto_refresh, refresh_interval_minutes, notifications_enabled,
                  email_alerts_enabled, data_retention_days, theme, language, created_at, updated_at
        "#,
        user_id
    )
    .fetch_one(db)
    .await?;
    
    Ok(prefs)
}

pub async fn update_preferences(
    user_id: i64,
    req: &UpdatePreferencesRequest,
    db: &PgPool,
) -> AppResult<UserPreferences> {
    // Ensure preferences exist
    get_or_create_preferences(user_id, db).await?;
    
    // Update with provided values
    let prefs = sqlx::query_as!(
        UserPreferences,
        r#"
        UPDATE user_preferences
        SET 
            auto_refresh = COALESCE($2, auto_refresh),
            refresh_interval_minutes = COALESCE($3, refresh_interval_minutes),
            notifications_enabled = COALESCE($4, notifications_enabled),
            email_alerts_enabled = COALESCE($5, email_alerts_enabled),
            data_retention_days = COALESCE($6, data_retention_days),
            theme = COALESCE($7, theme),
            language = COALESCE($8, language),
            updated_at = NOW()
        WHERE user_id = $1
        RETURNING id, user_id, auto_refresh, refresh_interval_minutes, notifications_enabled,
                  email_alerts_enabled, data_retention_days, theme, language, created_at, updated_at
        "#,
        user_id,
        req.auto_refresh,
        req.refresh_interval_minutes,
        req.notifications_enabled,
        req.email_alerts_enabled,
        req.data_retention_days,
        req.theme,
        req.language
    )
    .fetch_one(db)
    .await?;
    
    Ok(prefs)
}

pub async fn list_integrations(db: &PgPool) -> AppResult<Vec<Integration>> {
    let integrations = sqlx::query_as!(
        Integration,
        r#"
        SELECT id, name, integration_type, status, api_endpoint, last_sync_at, 
               config, created_at, updated_at
        FROM integrations
        ORDER BY name
        "#
    )
    .fetch_all(db)
    .await?;
    
    Ok(integrations)
}

pub async fn get_integration_by_id(id: i64, db: &PgPool) -> AppResult<Option<Integration>> {
    let integration = sqlx::query_as!(
        Integration,
        r#"
        SELECT id, name, integration_type, status, api_endpoint, last_sync_at, 
               config, created_at, updated_at
        FROM integrations
        WHERE id = $1
        "#,
        id
    )
    .fetch_optional(db)
    .await?;
    
    Ok(integration)
}

pub async fn update_integration_status(id: i64, status: &str, db: &PgPool) -> AppResult<Integration> {
    let integration = sqlx::query_as!(
        Integration,
        r#"
        UPDATE integrations
        SET status = $2, updated_at = NOW()
        WHERE id = $1
        RETURNING id, name, integration_type, status, api_endpoint, last_sync_at, 
                  config, created_at, updated_at
        "#,
        id,
        status
    )
    .fetch_one(db)
    .await?;
    
    Ok(integration)
}

pub async fn purge_cache(user_id: i64, db: &PgPool) -> AppResult<i64> {
    // Delete cached dashboard stats for user
    let result = sqlx::query!(
        "DELETE FROM dashboard_stats_cache WHERE user_id = $1 OR user_id IS NULL",
        user_id
    )
    .execute(db)
    .await?;
    
    Ok(result.rows_affected() as i64)
}

pub async fn get_global_export_data(user_id: i64, db: &PgPool) -> AppResult<serde_json::Value> {
    // Gather all user data for export
    let farms = sqlx::query!(
        r#"
        SELECT id, name, area_hectares, created_at
        FROM farms
        WHERE user_id = $1
        "#,
        user_id
    )
    .fetch_all(db)
    .await?;
    
    let alerts = sqlx::query!(
        r#"
        SELECT a.id, a.severity, a.message, a.detected_at
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
    
    let reports = sqlx::query!(
        r#"
        SELECT id, title, report_type, status, created_at
        FROM reports
        WHERE user_id = $1
        "#,
        user_id
    )
    .fetch_all(db)
    .await?;
    
    Ok(serde_json::json!({
        "farms": farms.into_iter().map(|f| serde_json::json!({
            "id": f.id,
            "name": f.name,
            "area_hectares": f.area_hectares.map(|v| v.to_string()),
            "created_at": f.created_at.to_rfc3339()
        })).collect::<Vec<_>>(),
        "alerts": alerts.into_iter().map(|a| serde_json::json!({
            "id": a.id,
            "severity": a.severity,
            "message": a.message,
            "detected_at": a.detected_at.to_rfc3339()
        })).collect::<Vec<_>>(),
        "reports": reports.into_iter().map(|r| serde_json::json!({
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "status": r.status,
            "created_at": r.created_at.to_rfc3339()
        })).collect::<Vec<_>>(),
        "exported_at": chrono::Utc::now().to_rfc3339()
    }))
}
