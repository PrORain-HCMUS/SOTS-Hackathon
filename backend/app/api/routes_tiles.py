"""
Tile serving API routes.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.crud import get_tile, get_tiles
from app.core.spaces import get_spaces_client

router = APIRouter(prefix="/tiles", tags=["tiles"])


class TileInfo(BaseModel):
    """Tile information."""
    
    tile_id: str
    last_seen_sensing_time: Optional[str] = None
    created_at: Optional[str] = None


class COGInfo(BaseModel):
    """Cloud-Optimized GeoTIFF information."""
    
    asset_type: str
    date: str
    cog_url: str
    s3_key: str
    bbox: Optional[List[float]] = None
    note: str = "Use with TiTiler or similar COG tile server"


@router.get("/", response_model=List[TileInfo])
def list_tiles(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List all registered tiles."""
    tiles = get_tiles(db, limit=limit)
    
    return [
        TileInfo(
            tile_id=tile.tile_id,
            last_seen_sensing_time=(
                tile.last_seen_sensing_time.isoformat()
                if tile.last_seen_sensing_time else None
            ),
            created_at=tile.created_at.isoformat() if tile.created_at else None,
        )
        for tile in tiles
    ]


@router.get("/{tile_id}", response_model=TileInfo)
def get_tile_info(
    tile_id: str = Path(..., description="Tile ID"),
    db: Session = Depends(get_db),
):
    """Get tile information by ID."""
    tile = get_tile(db, tile_id)
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")
    
    return TileInfo(
        tile_id=tile.tile_id,
        last_seen_sensing_time=(
            tile.last_seen_sensing_time.isoformat()
            if tile.last_seen_sensing_time else None
        ),
        created_at=tile.created_at.isoformat() if tile.created_at else None,
    )


@router.get("/{asset_type}/{date}/{z}/{x}/{y}.png")
def get_tile_png(
    asset_type: str = Path(..., description="Asset type (e.g., crop_map, s2_composite)"),
    date: str = Path(..., description="Date in YYYY-MM-DD format"),
    z: int = Path(..., ge=0, le=20, description="Zoom level"),
    x: int = Path(..., ge=0, description="X tile coordinate"),
    y: int = Path(..., ge=0, description="Y tile coordinate"),
    db: Session = Depends(get_db),
):
    """
    Get a map tile as PNG.
    
    NOTE: This is a placeholder endpoint. In production, you would use
    TiTiler or a similar COG tile server to serve tiles directly from
    the Cloud-Optimized GeoTIFFs stored in Spaces.
    
    For now, this returns a JSON response with the COG URL that can be
    used with a tile server.
    """
    settings = get_settings()
    
    # Find the asset for this date
    from app.core.models_sqlalchemy import Asset
    from datetime import datetime
    
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Query for matching asset
    asset = db.query(Asset).filter(
        Asset.asset_type.ilike(f"%{asset_type}%"),
        Asset.period_start <= target_date,
        Asset.period_end >= target_date,
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"No asset found for type={asset_type}, date={date}",
        )
    
    # Build COG URL
    spaces = get_spaces_client()
    cog_url = spaces.get_public_url(asset.s3_key)
    
    # If tile server is configured, redirect to it
    if settings.tile_server_base_url:
        tile_url = (
            f"{settings.tile_server_base_url}/cog/tiles/{z}/{x}/{y}.png"
            f"?url={cog_url}"
        )
        return JSONResponse(
            content={
                "tile_url": tile_url,
                "cog_url": cog_url,
            }
        )
    
    # Otherwise return COG info for client-side rendering
    return JSONResponse(
        content={
            "message": "Tile server not configured. Use COG URL with TiTiler.",
            "cog_url": cog_url,
            "s3_key": asset.s3_key,
            "asset_id": str(asset.asset_id),
            "bbox": asset.bbox,
            "note": "Configure TILE_SERVER_BASE_URL for direct tile serving",
        }
    )


@router.get("/{asset_type}/{date}/info", response_model=COGInfo)
def get_cog_info(
    asset_type: str = Path(..., description="Asset type"),
    date: str = Path(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """
    Get COG information for a specific asset type and date.
    
    Returns the public URL of the Cloud-Optimized GeoTIFF that can be
    used with TiTiler or similar services.
    """
    from app.core.models_sqlalchemy import Asset
    from datetime import datetime
    
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    asset = db.query(Asset).filter(
        Asset.asset_type.ilike(f"%{asset_type}%"),
        Asset.period_start <= target_date,
        Asset.period_end >= target_date,
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    spaces = get_spaces_client()
    cog_url = spaces.get_public_url(asset.s3_key)
    
    return COGInfo(
        asset_type=asset.asset_type,
        date=date,
        cog_url=cog_url,
        s3_key=asset.s3_key,
        bbox=asset.bbox,
    )
