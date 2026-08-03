"""Shop/warehouse location router logic, extracted behind the service layer (clears W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional


def list_shop_locations(country_code: str, is_active: Optional[bool], skip: int, limit: int) -> List[dict]:
    from data.db import get_db_context
    from data.models import ShopWarehouseLocation

    cc = country_code.upper()
    with get_db_context() as db:
        query = db.query(ShopWarehouseLocation).filter(
            ShopWarehouseLocation.country_code == cc
        )
        if is_active is not None:
            query = query.filter(ShopWarehouseLocation.is_active == is_active)
        locations = query.order_by(ShopWarehouseLocation.name).offset(skip).limit(limit).all()
        return [
            {
                "id": loc.id,
                "name": loc.name,
                "warehouse_code": loc.warehouse_code,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "is_active": loc.is_active,
                "created_at": loc.created_at,
            }
            for loc in locations
        ]


def create_shop_location(country_code: str, payload: Optional[dict]) -> dict:
    from data.db import get_db_context
    from data.models import ShopWarehouseLocation, CountryConfig
    from data.services_write_helpers import add_and_flush, commit_and_refresh
    from fastapi import HTTPException

    payload = payload or {}
    cc = country_code.upper()
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if not config:
            raise HTTPException(status_code=404, detail="Country not found")
        location = ShopWarehouseLocation(
            country_code=cc,
            name=payload.get("name"),
            warehouse_code=payload.get("warehouse_code"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            address=payload.get("address"),
            is_active=payload.get("is_active", True),
        )
        add_and_flush(db, location)
        commit_and_refresh(db, location)
        return {"id": location.id, "message": "Shop location created"}


def update_shop_location(country_code: str, location_id: int, payload: Optional[dict]) -> dict:
    from data.db import get_db_context
    from data.models import ShopWarehouseLocation
    from data.services_write_helpers import commit_and_refresh
    from fastapi import HTTPException

    payload = payload or {}
    cc = country_code.upper()
    with get_db_context() as db:
        location = db.query(ShopWarehouseLocation).filter(
            ShopWarehouseLocation.id == location_id,
            ShopWarehouseLocation.country_code == cc,
        ).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        for field in ["name", "warehouse_code", "latitude", "longitude", "address", "is_active"]:
            if field in payload:
                setattr(location, field, payload[field])
        commit_and_refresh(db, location)
        return {"id": location.id, "message": "Shop location updated"}
