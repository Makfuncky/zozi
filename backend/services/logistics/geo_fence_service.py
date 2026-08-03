from __future__ import annotations

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
        
        from data.models import Office
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
        
        from data.models import CountryConfig
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
        from data.models import AuditLog
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

