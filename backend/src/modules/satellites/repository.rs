use sqlx::PgPool;
use crate::shared::error::AppResult;
use super::models::*;

pub async fn get_all_tiles(db: &PgPool) -> AppResult<Vec<SatelliteTile>> {
    let tiles = sqlx::query_as::<_, SatelliteTile>(
        r#"
        SELECT 
            id, tile_id, tile_name, prediction_file, visualization_file,
            bounds, center_lat, center_lon, bbox, captured_at, processed_at
        FROM satellite_tiles
        ORDER BY tile_id
        "#
    )
    .fetch_all(db)
    .await?;
    
    Ok(tiles)
}

pub async fn get_tile_by_id(tile_id: i32, db: &PgPool) -> AppResult<Option<SatelliteTile>> {
    let tile = sqlx::query_as::<_, SatelliteTile>(
        r#"
        SELECT 
            id, tile_id, tile_name, prediction_file, visualization_file,
            bounds, center_lat, center_lon, bbox, captured_at, processed_at
        FROM satellite_tiles
        WHERE tile_id = $1
        "#
    )
    .bind(tile_id)
    .fetch_optional(db)
    .await?;
    
    Ok(tile)
}

pub async fn get_tile_stats(tile_id: i32, db: &PgPool) -> AppResult<Vec<TileCropStat>> {
    let stats = sqlx::query!(
        r#"
        SELECT 
            tcs.id,
            tcs.tile_id,
            tcs.crop_class_id,
            cc.name as crop_name,
            cc.color as crop_color,
            tcs.pixel_count,
            tcs.area_hectares,
            tcs.percentage
        FROM tile_crop_stats tcs
        JOIN crop_classes cc ON cc.id = tcs.crop_class_id
        WHERE tcs.tile_id = $1
        ORDER BY tcs.percentage DESC
        "#,
        tile_id
    )
    .fetch_all(db)
    .await?;
    
    Ok(stats.into_iter().map(|s| TileCropStat {
        id: s.id,
        tile_id: s.tile_id.unwrap_or(0),
        crop_class_id: s.crop_class_id.unwrap_or(0),
        crop_name: s.crop_name,
        crop_color: s.crop_color,
        pixel_count: s.pixel_count,
        area_hectares: s.area_hectares,
        percentage: s.percentage,
    }).collect())
}

pub async fn get_all_crop_classes(db: &PgPool) -> AppResult<Vec<CropClass>> {
    let classes = sqlx::query_as::<_, CropClass>(
        r#"
        SELECT id, name, color, description, created_at
        FROM crop_classes
        ORDER BY id
        "#
    )
    .fetch_all(db)
    .await?;
    
    Ok(classes)
}

pub async fn get_coverage_area(db: &PgPool) -> AppResult<CoverageArea> {
    // Get total tiles
    let total_tiles = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM satellite_tiles"
    )
    .fetch_one(db)
    .await?;
    
    // Get crop distribution
    let crop_stats = sqlx::query!(
        r#"
        SELECT 
            cc.id,
            cc.name,
            cc.color,
            COALESCE(SUM(tcs.area_hectares), 0) as total_area
        FROM crop_classes cc
        LEFT JOIN tile_crop_stats tcs ON tcs.crop_class_id = cc.id
        GROUP BY cc.id, cc.name, cc.color
        HAVING SUM(tcs.area_hectares) > 0
        ORDER BY total_area DESC
        "#
    )
    .fetch_all(db)
    .await?;
    
    let total_area: f64 = crop_stats.iter()
        .filter_map(|s| s.total_area.and_then(|v| v.to_string().parse::<f64>().ok()))
        .sum();
    
    let crop_distribution: Vec<CropDistribution> = crop_stats.iter().map(|s| {
        let area = s.total_area
            .and_then(|v| v.to_string().parse::<f64>().ok())
            .unwrap_or(0.0);
        
        CropDistribution {
            crop_id: s.id,
            crop_name: s.name.clone(),
            crop_color: s.color.clone(),
            total_area_hectares: area,
            percentage: if total_area > 0.0 { (area / total_area) * 100.0 } else { 0.0 },
        }
    }).collect();
    
    // Bounds from Mekong Delta region
    let bounds = Bounds {
        west: 104.5,
        south: 8.5,
        east: 107.0,
        north: 11.5,
    };
    
    Ok(CoverageArea {
        total_tiles,
        total_area_hectares: total_area,
        bounds,
        crop_distribution,
    })
}
