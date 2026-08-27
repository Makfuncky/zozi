"""Auto-migrated service logic from routers/logistics_locations.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

# TODO: Module not yet created
# from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.logistics.models.logistics import LogisticsPartner

logger = logging.getLogger(__name__)

def list_logistics_partner_locations(country_code: str, partner_id: Optional[int], is_active: Optional[bool], db: Session, current_user):
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).all()
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

def create_logistics_partner_location(country_code: str, payload: dict, db: Session, current_user):
    if not payload:
        payload = {}
    config = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    
    location = LogisticsPartnerLocation(
        country_code=country_code.upper(),
        partner_id=partner_id,
        location_type=payload.get("location_type", "warehouse"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return {"id": location.id, "message": "Logistics partner location created"}


def list_assigned_shipments(db: Session, current_user) -> list:
    """List shipments assigned to the logistics partner associated with the current user."""
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner:
        from fastapi import HTTPException
        raise HTTPException(404)
    shipments = db.query(__import__("domains.logistics.models.logistics", fromlist=["Shipment"]).Shipment).filter(
        __import__("domains.logistics.models.logistics", fromlist=["Shipment"]).Shipment.assigned_partner_id == partner.id
    ).all()
    Shipment = __import__("domains.logistics.models.logistics", fromlist=["Shipment"]).Shipment
    return [{
        "id": s.id,
        "order_id": s.order_id,
        "status": s.status,
        "tracking_number": s.tracking_number,
        "carrier_name": s.carrier_name,
        "distribution_channel": s.distribution_channel,
        "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
        "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
    } for s in shipments]


def list_my_pickups(db: Session, current_user) -> list:
    """List shipments assigned to this logistics partner."""
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.user_id == current_user.id
    ).first()
    if not partner:
        from fastapi import HTTPException
        raise HTTPException(404, "Logistics partner profile not found")
    Shipment = __import__("domains.logistics.models.logistics", fromlist=["Shipment"]).Shipment
    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner.id)
        .order_by(Shipment.updated_at.desc())
        .all()
    )
    return [
        {
            "id": s.id, "order_id": s.order_id, "status": s.status,
            "tracking_number": s.tracking_number, "scan_code": s.scan_code,
            "current_hub": s.current_hub,
            "package_weight_kg": float(s.package_weight_kg) if s.package_weight_kg else None,
            "packaged_at": s.packaged_at.isoformat() if s.packaged_at else None,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
            "delivery_signature_name": s.delivery_signature_name,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in shipments
    ]

