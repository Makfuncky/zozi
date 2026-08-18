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
            except Exception:
                pass
        return "US"

    def get_country_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        tolerance_km: float = 100.0,
    ) -> Optional[str]:
        if self.db:
            try:
                country = (
                    self.db.query(CountryConfig)
                    .filter(CountryConfig.is_active == True)
                    .first()
                )
                if country:
                    return country.code
            except Exception:
                pass
        return None


def get_country_session_key(country_code: str, user_id: int) -> str:
    return f"cross_country:{user_id}:{country_code}"
