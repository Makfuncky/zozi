"""Logistics Partner Location router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional

from fastapi import HTTPException


def list_logistics_partner_locations(
    country_code: str, partner_id, is_active, skip: int, limit: int
) -> List[dict]:
    from data.db import get_db_context
    from data.models import LogisticsPartnerLocation

    cc = country_code.upper()
    with get_db_context() as db:
        query = db.query(LogisticsPartnerLocation).filter(
            LogisticsPartnerLocation.country_code == cc
        )
        if partner_id is not None:
            query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
        if is_active is not None:
            query = query.filter(LogisticsPartnerLocation.is_active == is_active)
        locations = (
            query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": loc.id,
                "partner_id": loc.partner_id,
                "location_type": loc.location_type,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "is_active": loc.is_active,
                "created_at": loc.created_at,
            }
            for loc in locations
        ]


def create_logistics_partner_location(country_code: str, payload) -> dict:
    from data.db import get_db_context
    from data.models import CountryConfig, LogisticsPartner, LogisticsPartnerLocation
    from data.services_write_helpers import add_and_flush, commit_and_refresh

    if not payload:
        payload = {}
    cc = country_code.upper()
    with get_db_context() as db:
        config = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if not config:
            raise HTTPException(status_code=404, detail="Country not found")

        partner_id = payload.get("partner_id")
        if not partner_id:
            raise HTTPException(status_code=422, detail="partner_id is required")

        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Logistics partner not found")

        location = LogisticsPartnerLocation(
            country_code=cc,
            partner_id=partner_id,
            location_type=payload.get("location_type", "warehouse"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            address=payload.get("address"),
            is_active=payload.get("is_active", True),
        )
        add_and_flush(db, location)
        commit_and_refresh(db, location)
        return {"id": location.id, "message": "Logistics partner location created"}
