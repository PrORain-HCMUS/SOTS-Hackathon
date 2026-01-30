#!/usr/bin/env python
"""
Initialize Vietnam administrative units (provinces and districts).

This script populates the admin_units table with Vietnam's provinces.
For a complete implementation, you would load from a GeoJSON file with
actual boundaries.

Usage:
    python scripts/init_admin_units.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import get_db_context
from app.core.crud import create_admin_unit, get_admin_units_by_level

# Vietnam provinces (63 provinces + municipalities)
VIETNAM_PROVINCES = [
    {"name": "Hà Nội", "code": "HN", "name_en": "Hanoi"},
    {"name": "Hồ Chí Minh", "code": "HCM", "name_en": "Ho Chi Minh City"},
    {"name": "Đà Nẵng", "code": "DN", "name_en": "Da Nang"},
    {"name": "Hải Phòng", "code": "HP", "name_en": "Hai Phong"},
    {"name": "Cần Thơ", "code": "CT", "name_en": "Can Tho"},
    {"name": "An Giang", "code": "AG", "name_en": "An Giang"},
    {"name": "Bà Rịa - Vũng Tàu", "code": "BRVT", "name_en": "Ba Ria - Vung Tau"},
    {"name": "Bắc Giang", "code": "BG", "name_en": "Bac Giang"},
    {"name": "Bắc Kạn", "code": "BK", "name_en": "Bac Kan"},
    {"name": "Bạc Liêu", "code": "BL", "name_en": "Bac Lieu"},
    {"name": "Bắc Ninh", "code": "BN", "name_en": "Bac Ninh"},
    {"name": "Bến Tre", "code": "BT", "name_en": "Ben Tre"},
    {"name": "Bình Định", "code": "BD", "name_en": "Binh Dinh"},
    {"name": "Bình Dương", "code": "BDG", "name_en": "Binh Duong"},
    {"name": "Bình Phước", "code": "BP", "name_en": "Binh Phuoc"},
    {"name": "Bình Thuận", "code": "BTH", "name_en": "Binh Thuan"},
    {"name": "Cà Mau", "code": "CM", "name_en": "Ca Mau"},
    {"name": "Cao Bằng", "code": "CB", "name_en": "Cao Bang"},
    {"name": "Đắk Lắk", "code": "DL", "name_en": "Dak Lak"},
    {"name": "Đắk Nông", "code": "DNG", "name_en": "Dak Nong"},
    {"name": "Điện Biên", "code": "DB", "name_en": "Dien Bien"},
    {"name": "Đồng Nai", "code": "DNA", "name_en": "Dong Nai"},
    {"name": "Đồng Tháp", "code": "DT", "name_en": "Dong Thap"},
    {"name": "Gia Lai", "code": "GL", "name_en": "Gia Lai"},
    {"name": "Hà Giang", "code": "HG", "name_en": "Ha Giang"},
    {"name": "Hà Nam", "code": "HNA", "name_en": "Ha Nam"},
    {"name": "Hà Tĩnh", "code": "HT", "name_en": "Ha Tinh"},
    {"name": "Hải Dương", "code": "HD", "name_en": "Hai Duong"},
    {"name": "Hậu Giang", "code": "HGI", "name_en": "Hau Giang"},
    {"name": "Hòa Bình", "code": "HB", "name_en": "Hoa Binh"},
    {"name": "Hưng Yên", "code": "HY", "name_en": "Hung Yen"},
    {"name": "Khánh Hòa", "code": "KH", "name_en": "Khanh Hoa"},
    {"name": "Kiên Giang", "code": "KG", "name_en": "Kien Giang"},
    {"name": "Kon Tum", "code": "KT", "name_en": "Kon Tum"},
    {"name": "Lai Châu", "code": "LC", "name_en": "Lai Chau"},
    {"name": "Lâm Đồng", "code": "LD", "name_en": "Lam Dong"},
    {"name": "Lạng Sơn", "code": "LS", "name_en": "Lang Son"},
    {"name": "Lào Cai", "code": "LCA", "name_en": "Lao Cai"},
    {"name": "Long An", "code": "LA", "name_en": "Long An"},
    {"name": "Nam Định", "code": "ND", "name_en": "Nam Dinh"},
    {"name": "Nghệ An", "code": "NA", "name_en": "Nghe An"},
    {"name": "Ninh Bình", "code": "NB", "name_en": "Ninh Binh"},
    {"name": "Ninh Thuận", "code": "NT", "name_en": "Ninh Thuan"},
    {"name": "Phú Thọ", "code": "PT", "name_en": "Phu Tho"},
    {"name": "Phú Yên", "code": "PY", "name_en": "Phu Yen"},
    {"name": "Quảng Bình", "code": "QB", "name_en": "Quang Binh"},
    {"name": "Quảng Nam", "code": "QNA", "name_en": "Quang Nam"},
    {"name": "Quảng Ngãi", "code": "QNG", "name_en": "Quang Ngai"},
    {"name": "Quảng Ninh", "code": "QN", "name_en": "Quang Ninh"},
    {"name": "Quảng Trị", "code": "QT", "name_en": "Quang Tri"},
    {"name": "Sóc Trăng", "code": "ST", "name_en": "Soc Trang"},
    {"name": "Sơn La", "code": "SL", "name_en": "Son La"},
    {"name": "Tây Ninh", "code": "TN", "name_en": "Tay Ninh"},
    {"name": "Thái Bình", "code": "TB", "name_en": "Thai Binh"},
    {"name": "Thái Nguyên", "code": "TNG", "name_en": "Thai Nguyen"},
    {"name": "Thanh Hóa", "code": "TH", "name_en": "Thanh Hoa"},
    {"name": "Thừa Thiên Huế", "code": "TTH", "name_en": "Thua Thien Hue"},
    {"name": "Tiền Giang", "code": "TG", "name_en": "Tien Giang"},
    {"name": "Trà Vinh", "code": "TV", "name_en": "Tra Vinh"},
    {"name": "Tuyên Quang", "code": "TQ", "name_en": "Tuyen Quang"},
    {"name": "Vĩnh Long", "code": "VL", "name_en": "Vinh Long"},
    {"name": "Vĩnh Phúc", "code": "VP", "name_en": "Vinh Phuc"},
    {"name": "Yên Bái", "code": "YB", "name_en": "Yen Bai"},
]


def init_country():
    """Initialize Vietnam as country-level admin unit."""
    with get_db_context() as db:
        # Check if country already exists
        existing = get_admin_units_by_level(db, level=0)
        if existing:
            print("Country already initialized")
            return existing[0]
        
        # Create Vietnam country record
        # Simplified bounding box for Vietnam
        vietnam_bbox = "MULTIPOLYGON(((102.0 8.0, 110.0 8.0, 110.0 24.0, 102.0 24.0, 102.0 8.0)))"
        
        country = create_admin_unit(
            db=db,
            name="Việt Nam",
            level=0,
            code="VN",
            geom_wkt=vietnam_bbox,
        )
        print(f"Created country: {country.name} (admin_id={country.admin_id})")
        return country


def init_provinces(parent_admin_id):
    """Initialize Vietnam provinces."""
    with get_db_context() as db:
        # Check existing provinces
        existing = get_admin_units_by_level(db, level=1)
        existing_codes = {p.code for p in existing}
        
        created = 0
        for prov in VIETNAM_PROVINCES:
            if prov["code"] in existing_codes:
                continue
            
            # Note: In production, load actual province boundaries from GeoJSON
            # For now, we create without geometry
            admin = create_admin_unit(
                db=db,
                name=prov["name"],
                level=1,
                code=prov["code"],
                parent_admin_id=parent_admin_id,
                geom_wkt=None,  # Would load from GeoJSON
            )
            created += 1
            print(f"  Created province: {admin.name}")
        
        print(f"Created {created} provinces")


def main():
    """Main initialization function."""
    print("Initializing Vietnam administrative units...")
    print("=" * 50)
    
    # Initialize country
    country = init_country()
    
    # Initialize provinces
    print("\nInitializing provinces...")
    init_provinces(country.admin_id)
    
    print("\n" + "=" * 50)
    print("Initialization complete!")
    print("\nNote: Province geometries are not included in this script.")
    print("For production, load boundaries from a GeoJSON file.")


if __name__ == "__main__":
    main()
