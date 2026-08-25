from __future__ import annotations

# -------------------------------------------------------------------
# FROM: live_tracking_service.py
# -------------------------------------------------------------------

"""Live GPS tracking service for parcels and logistics partners.

Provides real-time location tracking, GPS updates, and tracking visualization.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.country.models.country_control import ParcelLocationTracker
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import LogisticsPartner
from domains.country.models.country_control import ShopWarehouseLocation

logger = logging.getLogger(__name__)


class LiveTrackingService:
    """Service for live GPS tracking of parcels."""

    def __init__(self, db: Session):
        self.db = db

    def get_parcel_track(self, parcel_id: int, country_code: str) -> Dict[str, Any]:
        """Get tracking history for a parcel."""
        trackers = (
            self.db.query(ParcelLocationTracker)
            .filter(
                ParcelLocationTracker.parcel_id == parcel_id,
                ParcelLocationTracker.country_code == country_code.upper(),
            )
            .order_by(ParcelLocationTracker.timestamp.desc())
            .all()
        )

        if not trackers:
            return {"parcel_id": parcel_id, "locations": [], "status": "not_found"}

        latest = trackers[0]
        return {
            "parcel_id": parcel_id,
            "current_location": {
                "latitude": latest.latitude,
                "longitude": latest.longitude,
                "location_name": latest.location_name,
                "timestamp": latest.timestamp.isoformat() if latest.timestamp else None,
            },
            "history": [
                {
                    "latitude": t.latitude,
                    "longitude": t.longitude,
                    "location_name": t.location_name,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                }
                for t in trackers[1:]
            ],
            "status": "tracking",
        }

    def update_parcel_location(
        self,
        parcel_id: int,
        country_code: str,
        latitude: Optional[float],
        longitude: Optional[float],
        location_name: Optional[str] = None,
    ) -> ParcelLocationTracker:
        """Update parcel location with GPS coordinates."""
        tracker = ParcelLocationTracker(
            parcel_id=parcel_id,
            country_code=country_code.upper(),
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )
        self.db.add(tracker)
        self.db.commit()
        self.db.refresh(tracker)
        return tracker

    def get_partner_locations(
        self, partner_id: Optional[int] = None, country_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get locations for logistics partners."""
        query = self.db.query(LogisticsPartnerLocation)

        if partner_id:
            query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
        if country_code:
            query = query.filter(LogisticsPartnerLocation.country_code == country_code.upper())

        locations = query.all()
        return [
            {
                "partner_id": loc.partner_id,
                "country_code": loc.country_code,
                "location_type": loc.location_type,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "is_active": loc.is_active,
            }
            for loc in locations
        ]

    def get_map_data(
        self, country_code: str, include_parcels: bool = False
    ) -> Dict[str, Any]:
        """Get map data for a country including warehouses and optionally parcels."""
        warehouses = (
            self.db.query(ShopWarehouseLocation)
            .filter(
                ShopWarehouseLocation.country_code == country_code.upper(),
                ShopWarehouseLocation.is_active == True,
            )
            .all()
        )

        base_map = {
            "country_code": country_code.upper(),
            "warehouses": [
                {
                    "id": w.id,
                    "name": w.name,
                    "warehouse_code": w.warehouse_code,
                    "latitude": w.latitude,
                    "longitude": w.longitude,
                    "address": w.address,
                }
                for w in warehouses
            ],
        }

        if include_parcels:
            parcel_locations = (
                self.db.query(ParcelLocationTracker)
                .filter(
                    ParcelLocationTracker.country_code == country_code.upper(),
                )
                .order_by(ParcelLocationTracker.parcel_id, ParcelLocationTracker.timestamp.desc())
                .all()
            )

            seen_parcel_ids = set()
            parcels = []
            for pl in parcel_locations:
                if pl.parcel_id not in seen_parcel_ids:
                    parcels.append({
                        "parcel_id": pl.parcel_id,
                        "latitude": pl.latitude,
                        "longitude": pl.longitude,
                        "location_name": pl.location_name,
                    })
                    seen_parcel_ids.add(pl.parcel_id)

            base_map["parcels"] = parcels

        return base_map


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def estimate_arrival_time(
    current_lat: float,
    current_lon: float,
    dest_lat: float,
    dest_lon: float,
    speed_kmh: float = 50.0,
) -> Optional[datetime]:
    """Estimate arrival time based on current position and speed."""
    distance = calculate_distance(current_lat, current_lon, dest_lat, dest_lon)
    hours = distance / speed_kmh
    return datetime.utcnow() + __import__("datetime").timedelta(hours=hours)

# -------------------------------------------------------------------
# FROM: operations\live_tracking_service.py
# -------------------------------------------------------------------

"""Live GPS tracking service for parcels and logistics partners.

Provides real-time location tracking, GPS updates, and tracking visualization.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from domains.logistics.models.logistics import ParcelLocationTracker
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import ShopWarehouseLocation

logger = logging.getLogger(__name__)


class LiveTrackingService:
    """Service for live GPS tracking of parcels."""

    def __init__(self, db: Session):
        self.db = db

    def get_parcel_track(self, parcel_id: int, country_code: str) -> Dict[str, Any]:
        """Get tracking history for a parcel."""
        trackers = (
            self.db.query(ParcelLocationTracker)
            .filter(
                ParcelLocationTracker.parcel_id == parcel_id,
                ParcelLocationTracker.country_code == country_code.upper(),
            )
            .order_by(ParcelLocationTracker.timestamp.desc())
            .all()
        )

        if not trackers:
            return {"parcel_id": parcel_id, "locations": [], "status": "not_found"}

        latest = trackers[0]
        return {
            "parcel_id": parcel_id,
            "current_location": {
                "latitude": latest.latitude,
                "longitude": latest.longitude,
                "location_name": latest.location_name,
                "timestamp": latest.timestamp.isoformat() if latest.timestamp else None,
            },
            "history": [
                {
                    "latitude": t.latitude,
                    "longitude": t.longitude,
                    "location_name": t.location_name,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                }
                for t in trackers[1:]
            ],
            "status": "tracking",
        }

    def update_parcel_location(
        self,
        parcel_id: int,
        country_code: str,
        latitude: Optional[float],
        longitude: Optional[float],
        location_name: Optional[str] = None,
    ) -> ParcelLocationTracker:
        """Update parcel location with GPS coordinates."""
        tracker = ParcelLocationTracker(
            parcel_id=parcel_id,
            country_code=country_code.upper(),
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
        )
        self.db.add(tracker)
        self.db.commit()
        self.db.refresh(tracker)
        return tracker

    def get_partner_locations(
        self, partner_id: Optional[int] = None, country_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get locations for logistics partners."""
        query = self.db.query(LogisticsPartnerLocation)

        if partner_id:
            query = query.filter(LogisticsPartnerLocation.partner_id == partner_id)
        if country_code:
            query = query.filter(LogisticsPartnerLocation.country_code == country_code.upper())

        locations = query.all()
        return [
            {
                "partner_id": loc.partner_id,
                "country_code": loc.country_code,
                "location_type": loc.location_type,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address,
                "is_active": loc.is_active,
            }
            for loc in locations
        ]

    def get_map_data(
        self, country_code: str, include_parcels: bool = False
    ) -> Dict[str, Any]:
        """Get map data for a country including warehouses and optionally parcels."""
        warehouses = (
            self.db.query(ShopWarehouseLocation)
            .filter(
                ShopWarehouseLocation.country_code == country_code.upper(),
                ShopWarehouseLocation.is_active == True,
            )
            .all()
        )

        base_map = {
            "country_code": country_code.upper(),
            "warehouses": [
                {
                    "id": w.id,
                    "name": w.name,
                    "warehouse_code": w.warehouse_code,
                    "latitude": w.latitude,
                    "longitude": w.longitude,
                    "address": w.address,
                }
                for w in warehouses
            ],
        }

        if include_parcels:
            parcel_locations = (
                self.db.query(ParcelLocationTracker)
                .filter(
                    ParcelLocationTracker.country_code == country_code.upper(),
                )
                .order_by(ParcelLocationTracker.parcel_id, ParcelLocationTracker.timestamp.desc())
                .all()
            )

            seen_parcel_ids = set()
            parcels = []
            for pl in parcel_locations:
                if pl.parcel_id not in seen_parcel_ids:
                    parcels.append({
                        "parcel_id": pl.parcel_id,
                        "latitude": pl.latitude,
                        "longitude": pl.longitude,
                        "location_name": pl.location_name,
                    })
                    seen_parcel_ids.add(pl.parcel_id)

            base_map["parcels"] = parcels

        return base_map


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def estimate_arrival_time(
    current_lat: float,
    current_lon: float,
    dest_lat: float,
    dest_lon: float,
    speed_kmh: float = 50.0,
) -> Optional[datetime]:
    """Estimate arrival time based on current position and speed."""
    distance = calculate_distance(current_lat, current_lon, dest_lat, dest_lon)
    hours = distance / speed_kmh
    return datetime.utcnow() + __import__("datetime").timedelta(hours=hours)

# -------------------------------------------------------------------
# FROM: logistics_orders_list_service.py
# -------------------------------------------------------------------

"""Logistics partner orders router."""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import LogisticsPartner
from infrastructure.utils.dependencies import require_logistics

def list_assigned_shipments(current_user: User=Depends(require_logistics), db: Session=Depends(get_db)):
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(404)
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).all()
    return [{'id': s.id, 'order_id': s.order_id, 'status': s.status, 'tracking_number': s.tracking_number, 'carrier_name': s.carrier_name, 'distribution_channel': s.distribution_channel, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None} for s in shipments]

# -------------------------------------------------------------------
# FROM: logistics_orders_v2_service.py
# -------------------------------------------------------------------

"""
Logistics Partner Order Management Router — full lifecycle.
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import Shipment
from infrastructure.utils.dependencies import require_logistics, require_admin
from domains.orders.services.order_tracking_service import get_available_orders_for_logistics
from domains.orders.services.order_tracking_service import get_order_shipment_label
from domains.orders.services.order_tracking_service import logistics_confirm_pickup
from domains.orders.services.order_tracking_service import logistics_scan_and_receive
from domains.orders.services.order_tracking_service import logistics_update_transit_status
from domains.orders.services.order_tracking_service import logistics_deliver_order
from domains.orders.services.order_tracking_service import logistics_cancel_pickup
logger = logging.getLogger(__name__)

class ScanReceiveRequest(BaseModel):
    scan_code: str
    location: Optional[str] = None

class UpdateTransitRequest(BaseModel):
    event_type: str
    location: Optional[str] = None
    notes: Optional[str] = None

class DeliverRequest(BaseModel):
    signature_name: Optional[str] = None
    signature_data_url: Optional[str] = None
    notes: Optional[str] = None

class CancelPickupRequest(BaseModel):
    reason: Optional[str] = None

def list_my_pickups(current_user: User=Depends(require_logistics), db: Session=Depends(get_db)):
    """List shipments assigned to this logistics partner."""
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.id).first()
    if not partner:
        raise HTTPException(404, 'Logistics partner profile not found')
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).order_by(Shipment.updated_at.desc()).all()
    return [{'id': s.id, 'order_id': s.order_id, 'status': s.status, 'tracking_number': s.tracking_number, 'scan_code': s.scan_code, 'current_hub': s.current_hub, 'package_weight_kg': float(s.package_weight_kg) if s.package_weight_kg else None, 'packaged_at': s.packaged_at.isoformat() if s.packaged_at else None, 'shipped_at': s.shipped_at.isoformat() if s.shipped_at else None, 'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None, 'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None, 'delivery_signature_name': s.delivery_signature_name, 'updated_at': s.updated_at.isoformat() if s.updated_at else None} for s in shipments]

# -------------------------------------------------------------------
# FROM: partner_shipments_service.py
# -------------------------------------------------------------------

"""Assigned-shipment read service for logistics partners.

Extracted from the surface router so HTTP/presentation concerns stay out of the
data layer (routers -> controllers -> services).
"""

from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import Shipment


def serialize_shipment(shipment: Shipment) -> Dict[str, Any]:
    """Project a Shipment ORM row into the API response shape."""
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "status": shipment.status,
        "tracking_number": shipment.tracking_number,
        "carrier_name": shipment.carrier_name,
        "distribution_channel": shipment.distribution_channel,
        "estimated_delivery": (
            shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None
        ),
        "actual_delivery": (
            shipment.actual_delivery.isoformat() if shipment.actual_delivery else None
        ),
    }


def list_assigned_shipments(db: Session, user: Any) -> List[Dict[str, Any]]:
    """Return the shipments assigned to the logistics partner linked to ``user``.

    Raises 404 if the authenticated user is not linked to a logistics partner.
    """
    partner = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.user_id == user.id)
        .first()
    )
    if not partner:
        raise HTTPException(status_code=404, detail="Logistics partner not found for user")

    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner.id)
        .all()
    )
    return [serialize_shipment(s) for s in shipments]

