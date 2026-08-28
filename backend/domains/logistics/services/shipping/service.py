from __future__ import annotations

# -------------------------------------------------------------------
# FROM: shipments_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/shipments.py."""

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    ShipmentCreate,
    ShipmentEventCreate,
    ShipmentEventOut,
    ShipmentOut,
    ShipmentUpdate,
)

from domains.accounts.models.user import User
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent

from infrastructure.utils.dependencies import get_current_user, require_admin, require_logistics

def get_shipment(shipment_id: int, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    return s

def track_shipment(tracking_number: str, db: Session):
    s = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
    if not s: raise HTTPException(404, "Tracking number not found")
    return s

def create_shipment(payload: ShipmentCreate, _: User, db: Session):
    s = Shipment(**payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return s

def update_shipment(shipment_id: int, payload: ShipmentUpdate, _: User, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s)
    return s

def add_event(shipment_id: int, payload: ShipmentEventCreate, current_user: User, db: Session):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s: raise HTTPException(404, "Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=current_user.id, **payload.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return event



# -------------------------------------------------------------------
# FROM: shipment_service.py
# -------------------------------------------------------------------

"""Shipment write operations (logistics domain).

Owns the DB writes for shipment creation, updates, event creation and
admin status changes. Routers must not mutate the session directly.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_shipment(db: Session, data: dict[str, Any]) -> Shipment:
    s = Shipment(**data)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_shipment(db: Session, shipment_id: int, data: dict[str, Any]) -> Shipment:
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


def add_shipment_event(
    db: Session, shipment_id: int, user_id: int, data: dict[str, Any]
) -> ShipmentEvent:
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    event = ShipmentEvent(shipment_id=shipment_id, created_by=user_id, **data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def admin_set_shipment_status(
    db: Session,
    shipment_id: int,
    new_status: str,
    note: str = "Admin status update",
) -> dict:
    """Admin endpoint to update a shipment status directly (bypasses supplier check)."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    now = _utcnow()
    shipment.status = new_status
    if new_status == "delivered" and not shipment.actual_delivery:
        shipment.actual_delivery = now
    elif new_status == "shipped" and not shipment.shipped_at:
        shipment.shipped_at = now
    event = ShipmentEvent(
        shipment_id=shipment_id,
        event_type="status_change",
        status_after=new_status,
        location=shipment.current_hub,
        notes=note,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(shipment)
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
    }


def lookup_shipment_by_code(db: Session, code: str) -> dict[str, Any]:
    """Look up a shipment by tracking number or scan code (admin scan lookup).

    Behaviour-preserving extraction of the inline handler in
    ``routers.logistics_logistics_status.scan_lookup_shipment``.
    """
    shipment = db.query(Shipment).filter(
        (Shipment.tracking_number == code)
        | (Shipment.id == (int(code) if code.isdigit() else -1))
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "carrier_name": shipment.carrier_name,
        "tracking_number": shipment.tracking_number,
        "distribution_channel": shipment.distribution_channel,
        "current_hub": shipment.current_hub,
        "shipping_address": (shipment.order.shipping_address if shipment.order else None),
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
    }

# -------------------------------------------------------------------
# FROM: logistics_shipment_service.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.logistics.shipment_service re-exports for HTTP routers."""
# TODO: Module not yet created
# from domains.logistics.services.shipment_service import lookup_shipment_by_code

# -------------------------------------------------------------------
# FROM: logistics_shipping_tier.py
# -------------------------------------------------------------------

# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""services.logistics.shipping_tier re-exports for HTTP routers."""
# TODO: Module not yet created
# from domains.logistics.services.shipping_tier import resolve_shipping_tier

# -------------------------------------------------------------------
# FROM: map_service.py
# -------------------------------------------------------------------

"""Map service for interactive country maps and geographic visualization.

Provides map rendering, city markers, zone management, and geographic data.
"""

import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCity
from domains.country.models.country_control import CountryMapConfig
from domains.country.models.country_control import ShopWarehouseLocation

logger = logging.getLogger(__name__)


class MapService:
    """Service for interactive map rendering and geographic data."""

    def __init__(self, db: Session):
        self.db = db

    def get_country_map_config(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get map configuration for a country."""
        config = (
            self.db.query(CountryMapConfig)
            .filter(CountryMapConfig.country_code == country_code.upper())
            .first()
        )

        if not config:
            country = (
                self.db.query(CountryConfig)
                .filter(CountryConfig.code == country_code.upper())
                .first()
            )
            if country and country.latitude and country.longitude:
                return {
                    "country_code": country_code.upper(),
                    "map_provider": "google",
                    "api_key_ref": None,
                    "default_zoom": 5,
                    "show_regions": True,
                    "show_cities": True,
                    "center_lat": float(country.latitude),
                    "center_lng": float(country.longitude),
                }
            return None

        return {
            "country_code": country_code.upper(),
            "map_provider": config.map_provider,
            "api_key_ref": config.api_key_ref,
            "default_zoom": config.default_zoom,
            "show_regions": config.show_regions,
            "show_cities": config.show_cities,
        }

    def get_cities_for_map(
        self,
        country_code: str,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get cities with coordinates for map markers."""
        query = (
            self.db.query(CountryCity)
            .filter(
                CountryCity.country_code == country_code.upper(),
                CountryCity.is_active == True,
            )
            .limit(limit)
        )

        if region:
            query = query.filter(CountryCity.region == region)

        cities = query.all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region,
                "latitude": float(c.latitude) if c.latitude else None,
                "longitude": float(c.longitude) if c.longitude else None,
                "population": c.population,
                "is_active": c.is_active,
            }
            for c in cities
        ]

    def get_warehouses_for_map(
        self, country_code: str, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """Get warehouse locations for map."""
        query = self.db.query(ShopWarehouseLocation).filter(
            ShopWarehouseLocation.country_code == country_code.upper()
        )

        if not include_inactive:
            query = query.filter(ShopWarehouseLocation.is_active == True)

        warehouses = query.all()
        return [
            {
                "id": w.id,
                "name": w.name,
                "warehouse_code": w.warehouse_code,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "address": w.address,
                "is_active": w.is_active,
            }
            for w in warehouses
        ]

    def get_delivery_zones(
        self, country_code: str, zone_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get delivery zones for a country."""
        from domains.country.models.country_enhancements import OmanDeliveryZone

        query = self.db.query(OmanDeliveryZone).filter(
            OmanDeliveryZone.is_active == True
        )

        zones = query.all()
        return [
            {
                "zone_code": z.zone_code,
                "zone_name": z.zone_name,
                "description": z.description,
                "car_rate": float(z.car_rate) if z.car_rate else 0,
                "van_rate": float(z.van_rate) if z.van_rate else 0,
                "truck_rate": float(z.truck_rate) if z.truck_rate else 0,
                "weight_surcharge_rate": float(z.weight_surcharge_rate) if z.weight_surcharge_rate else 0,
                "cities": z.cities_json,
                "sort_order": z.sort_order,
            }
            for z in zones
        ]

    def generate_map_markers(
        self, country_code: str, include_parcels: bool = False
    ) -> Dict[str, Any]:
        """Generate complete marker data for map visualization."""
        cities = self.get_cities_for_map(country_code)
        warehouses = self.get_warehouses_for_map(country_code)

        markers = {
            "cities": [
                {
                    "type": "city",
                    "id": f"city_{c['id']}",
                    "name": c["name"],
                    "lat": c["latitude"],
                    "lng": c["longitude"],
                    "popup": f"<strong>{c['name']}</strong><br/>Population: {c['population'] or 'N/A'}",
                }
                for c in cities
                if c["latitude"] and c["longitude"]
            ],
            "warehouses": [
                {
                    "type": "warehouse",
                    "id": f"wh_{w['id']}",
                    "name": w["name"],
                    "lat": w["latitude"],
                    "lng": w["longitude"],
                    "popup": f"<strong>{w['name']}</strong><br/>{w['warehouse_code']}",
                }
                for w in warehouses
                if w["latitude"] and w["longitude"]
            ],
        }

        if include_parcels:
            from domains.logistics.models.logistics import Shipment
            from domains.country.models.country_control import ParcelLocationTracker

            shipments = (
                self.db.query(Shipment)
                .filter(Shipment.country_code == country_code.upper())
                .all()
            )

            parcel_trackers = (
                self.db.query(ParcelLocationTracker)
                .filter(ParcelLocationTracker.country_code == country_code.upper())
                .all()
            )

            latest_locations = {}
            for pt in parcel_trackers:
                if pt.parcel_id not in latest_locations or pt.timestamp > latest_locations[pt.parcel_id].timestamp:
                    latest_locations[pt.parcel_id] = pt

            markers["parcels"] = [
                {
                    "type": "parcel",
                    "id": f"parcel_{pid}",
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "popup": f"Parcel {pid}",
                }
                for pid, loc in latest_locations.items()
                if loc.latitude and loc.longitude
            ]

        return markers

    def get_region_bounds(
        self, country_code: str, region_name: str
    ) -> Optional[Dict[str, float]]:
        """Calculate bounding box for a region."""
        cities = (
            self.db.query(CountryCity)
            .filter(
                CountryCity.country_code == country_code.upper(),
                CountryCity.region == region_name,
                CountryCity.latitude.isnot(None),
                CountryCity.longitude.isnot(None),
            )
            .all()
        )

        if not cities:
            return None

        lats = [float(c.latitude) for c in cities]
        lons = [float(c.longitude) for c in cities]

        padding = 0.1
        return {
            "north": max(lats) + padding,
            "south": min(lats) - padding,
            "east": max(lons) + padding,
            "west": min(lons) - padding,
        }

