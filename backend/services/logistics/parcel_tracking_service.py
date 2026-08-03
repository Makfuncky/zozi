"""Parcel location tracking router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional


def list_parcel_tracking(parcel_id: int, country_code: Optional[str], limit: int) -> List[dict]:
    from data.db import get_db_context
    from data.models import ParcelLocationTracker

    with get_db_context() as db:
        query = db.query(ParcelLocationTracker).filter(
            ParcelLocationTracker.parcel_id == parcel_id
        )
        if country_code:
            query = query.filter(
                ParcelLocationTracker.country_code == country_code.upper()
            )
        locations = query.order_by(ParcelLocationTracker.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": loc.id,
                "parcel_id": loc.parcel_id,
                "country_code": loc.country_code,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "location_name": loc.location_name,
                "timestamp": loc.timestamp,
                "created_at": loc.created_at,
            }
            for loc in locations
        ]


def create_parcel_tracking(parcel_id: int, payload: Optional[dict]) -> dict:
    from data.db import get_db_context
    from data.models import ParcelLocationTracker, Shipment
    from data.services_write_helpers import add_and_flush, commit_and_refresh
    from fastapi import HTTPException

    payload = payload or {}
    with get_db_context() as db:
        shipment = db.query(Shipment).filter(Shipment.id == parcel_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Parcel not found")
        location = ParcelLocationTracker(
            parcel_id=parcel_id,
            country_code=payload.get("country_code"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            location_name=payload.get("location_name"),
        )
        add_and_flush(db, location)
        commit_and_refresh(db, location)
        return {"id": location.id, "message": "Parcel tracking entry created"}
