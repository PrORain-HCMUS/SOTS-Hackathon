#!/usr/bin/env python
"""
Initialize Sentinel-2 tile grid for Vietnam.

This script creates tile records for the Sentinel-2 Military Grid Reference System (MGRS)
tiles that cover Vietnam.

Usage:
    python scripts/init_tiles_vn.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import get_db_context
from app.core.crud import get_tile, create_tile

# Sentinel-2 MGRS tiles covering Vietnam (approximate list)
# Format: tile_id, (min_lon, min_lat, max_lon, max_lat)
VIETNAM_TILES = [
    # Northern Vietnam
    ("48QWJ", (104.0, 22.0, 105.0, 23.0)),
    ("48QWK", (104.0, 23.0, 105.0, 24.0)),
    ("48QXJ", (105.0, 22.0, 106.0, 23.0)),
    ("48QXK", (105.0, 23.0, 106.0, 24.0)),
    ("48QYJ", (106.0, 22.0, 107.0, 23.0)),
    ("48QYK", (106.0, 23.0, 107.0, 24.0)),
    
    # Red River Delta
    ("48QWH", (104.0, 21.0, 105.0, 22.0)),
    ("48QXH", (105.0, 21.0, 106.0, 22.0)),
    ("48QYH", (106.0, 21.0, 107.0, 22.0)),
    
    # Central Vietnam
    ("48QWG", (104.0, 20.0, 105.0, 21.0)),
    ("48QXG", (105.0, 20.0, 106.0, 21.0)),
    ("48QYG", (106.0, 20.0, 107.0, 21.0)),
    ("48QWF", (104.0, 19.0, 105.0, 20.0)),
    ("48QXF", (105.0, 19.0, 106.0, 20.0)),
    ("48QYF", (106.0, 19.0, 107.0, 20.0)),
    ("48QWE", (104.0, 18.0, 105.0, 19.0)),
    ("48QXE", (105.0, 18.0, 106.0, 19.0)),
    ("48QYE", (106.0, 18.0, 107.0, 19.0)),
    
    # Central Highlands
    ("48QWD", (104.0, 17.0, 105.0, 18.0)),
    ("48QXD", (105.0, 17.0, 106.0, 18.0)),
    ("48QYD", (106.0, 17.0, 107.0, 18.0)),
    ("48QWC", (104.0, 16.0, 105.0, 17.0)),
    ("48QXC", (105.0, 16.0, 106.0, 17.0)),
    ("48QYC", (106.0, 16.0, 107.0, 17.0)),
    ("49QCV", (107.0, 16.0, 108.0, 17.0)),
    ("49QDV", (108.0, 16.0, 109.0, 17.0)),
    
    # South Central Coast
    ("49QCU", (107.0, 15.0, 108.0, 16.0)),
    ("49QDU", (108.0, 15.0, 109.0, 16.0)),
    ("49QCT", (107.0, 14.0, 108.0, 15.0)),
    ("49QDT", (108.0, 14.0, 109.0, 15.0)),
    ("49QCS", (107.0, 13.0, 108.0, 14.0)),
    ("49QDS", (108.0, 13.0, 109.0, 14.0)),
    
    # Southeast
    ("48PWR", (106.0, 12.0, 107.0, 13.0)),
    ("48PXR", (107.0, 12.0, 108.0, 13.0)),
    ("48PWQ", (106.0, 11.0, 107.0, 12.0)),
    ("48PXQ", (107.0, 11.0, 108.0, 12.0)),
    ("48PWP", (106.0, 10.0, 107.0, 11.0)),
    ("48PXP", (107.0, 10.0, 108.0, 11.0)),
    
    # Mekong Delta
    ("48PVN", (104.0, 9.0, 105.0, 10.0)),
    ("48PWN", (105.0, 9.0, 106.0, 10.0)),
    ("48PXN", (106.0, 9.0, 107.0, 10.0)),
    ("48PVM", (104.0, 8.0, 105.0, 9.0)),
    ("48PWM", (105.0, 8.0, 106.0, 9.0)),
    ("48PXM", (106.0, 8.0, 107.0, 9.0)),
]


def bbox_to_polygon_wkt(bbox):
    """Convert bbox tuple to WKT polygon string."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return (
        f"POLYGON(("
        f"{min_lon} {min_lat}, "
        f"{max_lon} {min_lat}, "
        f"{max_lon} {max_lat}, "
        f"{min_lon} {max_lat}, "
        f"{min_lon} {min_lat}"
        f"))"
    )


def main():
    """Initialize Vietnam tiles."""
    print("Initializing Sentinel-2 tiles for Vietnam...")
    print("=" * 50)
    
    created = 0
    skipped = 0
    
    with get_db_context() as db:
        for tile_id, bbox in VIETNAM_TILES:
            # Check if tile already exists
            existing = get_tile(db, tile_id)
            if existing:
                skipped += 1
                continue
            
            # Create tile
            geom_wkt = bbox_to_polygon_wkt(bbox)
            tile = create_tile(db, tile_id, geom_wkt)
            created += 1
            print(f"  Created tile: {tile_id}")
    
    print("\n" + "=" * 50)
    print(f"Created: {created} tiles")
    print(f"Skipped (existing): {skipped} tiles")
    print(f"Total: {len(VIETNAM_TILES)} tiles")
    print("\nNote: These are approximate tile boundaries.")
    print("For production, use actual MGRS grid definitions.")


if __name__ == "__main__":
    main()
