from __future__ import annotations

import logging
import os
import ipaddress
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from providers.geography.ip import lookup_ipapi_co
from providers.geography.geoip import lookup_country_code

logger = logging.getLogger(__name__)


class CountryDetectionService:
    IP_HEADER_MAPPING = {
        "X-Forwarded-For": lambda v: v.split(",")[0].strip() if v else None,
        "X-Real-IP": lambda v: v.strip() if v else None,
        "CF-Connecting-IP": lambda v: v.strip() if v else None,
        "True-Client-IP": lambda v: v.strip() if v else None,
        "X-AppEngine-Canonical": lambda v: v.strip() if v else None,
    }

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def detect_country_from_ip(
        self,
        request_headers: dict,
        client_host: Optional[str] = None,
    ) -> Tuple[str, str]:
        ip = self._extract_ip(request_headers, client_host)
        if not ip:
            return self._default_country(), "unknown"

        if self._is_private_ip(ip):
            return self._default_country(), "private"

        country_code, source = self._lookup_country_by_ip(ip)
        return country_code, source

    def _extract_ip(self, headers: dict, client_host: Optional[str]) -> Optional[str]:
        for header_name, extractor in self.IP_HEADER_MAPPING.items():
            value = headers.get(header_name)
            if value:
                ip = extractor(value)
                if ip:
                    return ip
        return client_host

    def _is_private_ip(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            return False

    def _lookup_country_by_ip(self, ip: str) -> Tuple[str, str]:
        # 1. Try GeoLite2 local database
        country = self._lookup_geoip2(ip)
        if country:
            return country, "geoip2"

        # 2. Try ipapi.co (free, no key needed)
        country = self._lookup_ipapi(ip)
        if country:
            return country, "ipapi"

        # 3. Fallback to DB config
        return self._default_country(), "default"

    def _lookup_geoip2(self, ip: str) -> Optional[str]:
        return lookup_country_code(ip)

    def _lookup_ipapi(self, ip: str) -> Optional[str]:
        return lookup_ipapi_co(ip)

    def _default_country(self) -> str:
        if self.db:
            try:
                country = (
                    self.db.query(CountryConfig)
                    .filter(CountryConfig.is_active == True)
                    .first()
                )
                if country:
                    return country.code
            except Exception as _e:
                logger.debug("DB query failed: %s", _e)
        return "US"

    def get_country_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        tolerance_km: float = 100.0,
    ) -> Optional[str]:
        # Coordinates are accepted for API compatibility but not used for geo-lookup
        if self.db:
            try:
                country = (
                    self.db.query(CountryConfig)
                    .filter(CountryConfig.is_active == True)
                    .first()
                )
                if country:
                    return country.code
            except Exception as _e:
                logger.debug("DB query failed: %s", _e)
        return None


def get_country_session_key(country_code: str, user_id: int) -> str:
    return f"cross_country:{user_id}:{country_code}"

# === Merged from geo_fence_service.py ===
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


