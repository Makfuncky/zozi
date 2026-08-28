from __future__ import annotations

# -------------------------------------------------------------------
# FROM: geo\geo_fence_service.py
# -------------------------------------------------------------------


import logging
from typing import Optional, List, Tuple
from math import radians, cos, sin, sqrt, atan2

logger = logging.getLogger(__name__)


class GeoFenceService:
    """
    Geo-fencing service for validating access points.
    """
    
    EARTH_RADIUS_KM = 6371.0
    
    def __init__(self, db):
        self.db = db
    
    def is_within_fence(
        self,
        lat: float,
        lon: float,
        fence_type: str,
        fence_id: Optional[int] = None,
    ) -> bool:
        """Check if coordinates are within a defined geo-fence."""
        if fence_type == "office":
            return self._check_office_fence(lat, lon, fence_id)
        elif fence_type == "country":
            return self._check_country_fence(lat, lon, fence_id)
        return True
    
    def _check_office_fence(self, lat: float, lon: float, office_id: Optional[int]) -> bool:
        """Check if within office boundaries."""
        if not office_id:
            return True
        
        from domains.hr.models.employee_models import Office
        office = self.db.query(Office).filter(Office.id == office_id).first()
        if not office:
            return True
        
        distance = self._haversine_distance(
            lat, lon,
            float(office.latitude), float(office.longitude)
        )
        return distance <= (office.geo_fence_radius_meters or 1000) / 1000
    
    def _check_country_fence(self, lat: float, lon: float, country_code: Optional[str]) -> bool:
        """Check if within country boundaries (approximate center check)."""
        if not country_code:
            return True
        
        from domains.country.models.countries import CountryConfig
        country = self.db.query(CountryConfig).filter(CountryConfig.code == country_code).first()
        if not country:
            return True
        
        return True
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return self.EARTH_RADIUS_KM * c
    
    def detect_impossible_travel(
        self,
        user_id: int,
        current_lat: float,
        current_lon: float,
        timestamp: Optional[float] = None,
    ) -> bool:
        """Detect if user's location changed impossibly fast."""
        from domains.governance.models.core import AuditLog
        import time
        
        check_time = timestamp or time.time()
        one_hour_ago = check_time - 3600
        
        last_location = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.actor_id == user_id,
                AuditLog.event_type == "location_update",
                AuditLog.occurred_at > one_hour_ago,
            )
            .order_by(AuditLog.occurred_at.desc())
            .first()
        )
        
        if not last_location:
            return False
        
        import json
        details = json.loads(last_location.details_json or "{}")
        prev_lat = details.get("latitude")
        prev_lon = details.get("longitude")
        prev_time = details.get("timestamp", one_hour_ago)
        
        if not prev_lat or not prev_lon:
            return False
        
        distance = self._haversine_distance(current_lat, current_lon, prev_lat, prev_lon)
        time_diff = check_time - prev_time
        
        if time_diff <= 0:
            return False
        
        speed_kmh = (distance / time_diff) * 3600
        return speed_kmh > 1000


# -------------------------------------------------------------------
# FROM: geo_resolver.py
# -------------------------------------------------------------------

"""Location resolution utilities for the Zozi order/delivery system.

The live key-less geo SDK calls (ipwho.is, ip-api, OpenStreetMap Nominatim)
now live in :mod:`providers.geo`. This module re-exports the public surface so
existing imports (``routers/api_geography_location.py``,
``services/location_service/main.py``) keep working unchanged.

External lookups are performed live (no fake coordinates are ever returned). If a
network lookup fails the caller gets a clear error so the UI can fall back to the
browser Geolocation API rather than trusting a fabricated location.
"""

from providers.geography.geo import (
    DEFAULT_TIMEOUT,
    CACHE_TTL_SECONDS,
    USER_AGENT,
    IP_GEO_PROVIDERS,
    REVERSE_GEO_URL,
    IpLocation,
    ReverseLocation,
    resolve_ip_location,
    reverse_geocode,
)

__all__ = [
    "DEFAULT_TIMEOUT",
    "CACHE_TTL_SECONDS",
    "USER_AGENT",
    "IP_GEO_PROVIDERS",
    "REVERSE_GEO_URL",
    "IpLocation",
    "ReverseLocation",
    "resolve_ip_location",
    "reverse_geocode",
]

# -------------------------------------------------------------------
# FROM: geo_service.py
# -------------------------------------------------------------------

"""Geo/router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import Optional
import structlog
logger = structlog.get_logger(__name__)


def resolve_country_from_ip(ip_address: str) -> Optional[str]:
    from infrastructure.database.database import get_db_context
from domains.country.ports import CountryDetectionService

    with get_db_context() as db:
        service = CountryDetectionService(db)
        country_code, _ = service._lookup_country_by_ip(ip_address)
        return country_code


def get_country_details(country_code: Optional[str]) -> dict:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig

    with get_db_context() as db:
        country = (
            db.query(CountryConfig).filter(CountryConfig.code == country_code).first()
            if country_code
            else None
        )
        return {
            "country_code": country_code,
            "country_name": country.name if country else None,
            "currency": country.currency if country else None,
            "currency_symbol": country.currency_symbol if country else None,
            "timezone": country.timezone if country else None,
            "language": country.language if country else None,
        }


def list_geo_countries(skip: int, limit: int) -> list:
    from infrastructure.database.database import get_db_context
    from domains.country.models.countries import CountryConfig

    with get_db_context() as db:
        countries = (
            db.query(CountryConfig)
            .filter(CountryConfig.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "code": c.code,
                "name": c.name,
                "currency": c.currency,
                "currency_symbol": c.currency_symbol,
                "phone_code": c.phone_code,
                "language": c.language,
                "timezone": c.timezone,
            }
            for c in countries
        ]

# -------------------------------------------------------------------
# FROM: geo\logistics_locations_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/logistics_locations.py."""

import logging

from typing import Optional

from fastapi import HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.logistics.models.logistics import LogisticsPartnerLocation
from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from domains.country.ports import get_country_config

logger = logging.getLogger(__name__)

def list_logistics_partner_locations(country_code: str, partner_id: Optional[int], is_active: Optional[bool], db: Session, current_user):
    query = db.query(LogisticsPartnerLocation).filter(
        LogisticsPartnerLocation.country_code == country_code.upper()
    )
    if partner_id is not None:
        query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
    if is_active is not None:
        query = query.filter(LogisticsPartnerLocation.is_active == is_active)
    locations = query.order_by(LogisticsPartnerLocation.location_type, LogisticsPartnerLocation.created_at).limit(SAFE_QUERY_LIMIT).all()
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
    config = get_country_config(db, country_code)
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


# -------------------------------------------------------------------
# FROM: geo\map_service.py
# -------------------------------------------------------------------

"""Map service for interactive country maps and geographic visualization.

Provides map rendering, city markers, zone management, and geographic data.
"""

import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCity
from domains.country.models.country_enhancements import CountryMapConfig
from domains.logistics.models.logistics import ShopWarehouseLocation

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
            from domains.logistics.models.logistics import ParcelLocationTracker

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

# -------------------------------------------------------------------
# FROM: api_geography_location_service.py
# -------------------------------------------------------------------

"""In-app location API mounted at /location (same-origin for the web/mobile apps).

This reuses the shared geo_resolver so the frontend can resolve the customer's
current coordinates without standing up the separate location server. The
standalone ``location_service`` remains available for direct IP geolocation.

No coordinates are ever fabricated: a failed lookup returns 502 with a clear
message so the UI can fall back to the browser Geolocation API.
"""
from fastapi import Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# TODO: Module not yet created
# from domains.country.services.geo.geo_resolver import resolve_ip_location
# TODO: Module not yet created
# from domains.country.services.geo.geo_resolver import reverse_geocode

class ReverseRequest(BaseModel):
    lat: float
    lon: float

class ResolveRequest(BaseModel):
    ip: str | None = None

# -------------------------------------------------------------------
# FROM: location_service.py
# -------------------------------------------------------------------

"""Logistics location write operations (partner / parcel / shop-warehouse).

Owns the DB writes for creating logistics partner locations, parcel
tracking entries, and shop/warehouse locations. Routers stay thin.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.country.models.country_control import ParcelLocationTracker
from domains.country.models.country_control import ShopWarehouseLocation
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import Shipment
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

