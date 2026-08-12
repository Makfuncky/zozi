"""Logistics location write operations (partner / parcel / shop-warehouse).

Owns the DB writes for creating logistics partner locations, parcel
tracking entries, and shop/warehouse locations. Routers stay thin.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    CountryConfig,
    LogisticsPartner,
    LogisticsPartnerLocation,
    ParcelLocationTracker,
    Shipment,
    ShopWarehouseLocation,
)
import structlog
logger = structlog.get_logger(__name__)


def create_logistics_partner_location(
    db: Session,
    country_code: str,
    payload: dict,
) -> LogisticsPartnerLocation:
    code = country_code.upper()
    config = db.query(CountryConfig).filter(CountryConfig.code == code).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    partner_id = payload.get("partner_id")
    if not partner_id:
        raise HTTPException(status_code=422, detail="partner_id is required")
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found")
    location = LogisticsPartnerLocation(
        country_code=code,
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
    return location


def create_parcel_tracking(
    db: Session, parcel_id: int, payload: dict
) -> ParcelLocationTracker:
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
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def create_shop_location(
    db: Session, country_code: str, payload: dict
) -> ShopWarehouseLocation:
    code = country_code.upper()
    config = db.query(CountryConfig).filter(CountryConfig.code == code).first()
    if not config:
        raise HTTPException(status_code=404, detail="Country not found")
    location = ShopWarehouseLocation(
        country_code=code,
        name=payload.get("name"),
        warehouse_code=payload.get("warehouse_code"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        address=payload.get("address"),
        is_active=payload.get("is_active", True),
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update_shop_location(
    db: Session, location_id: int, country_code: str, payload: dict
) -> ShopWarehouseLocation:
    code = country_code.upper()
    location = (
        db.query(ShopWarehouseLocation)
        .filter(
            ShopWarehouseLocation.id == location_id,
            ShopWarehouseLocation.country_code == code,
        )
        .first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    for field in ["name", "warehouse_code", "latitude", "longitude", "address", "is_active"]:
        if field in payload:
            setattr(location, field, payload[field])
    db.commit()
    db.refresh(location)
    return location
