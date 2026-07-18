"""Live GPS tracking service for parcels and logistics partners.

Provides real-time location tracking, GPS updates, and tracking visualization.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import ParcelLocationTracker, Shipment, LogisticsPartner
from models.country_control import ShopWarehouseLocation

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
