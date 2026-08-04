import json
import logging
import ipaddress
import os
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from data.models import CountryConfig

logger = logging.getLogger(__name__)

GEOIP_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "GeoLite2-Country.mmdb"
_geoip_reader = None


def _get_geoip_reader():
    """Lazy-load the GeoLite2 reader (cached)."""
    global _geoip_reader
    if _geoip_reader is None and GEOIP_DB_PATH.exists():
        try:
            import geoip2.database
            _geoip_reader = geoip2.database.Reader(str(GEOIP_DB_PATH))
            logger.info("GeoIP2 reader loaded from %s", GEOIP_DB_PATH)
        except Exception as exc:
            logger.warning("Failed to load GeoIP2 database: %s", exc)
    return _geoip_reader


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
        reader = _get_geoip_reader()
        if reader is None:
            return None
        try:
            response = reader.country(ip)
            if response and response.country and response.country.iso_code:
                return response.country.iso_code
        except Exception:
            pass
        return None

    def _lookup_ipapi(self, ip: str) -> Optional[str]:
        try:
            url = f"https://ipapi.co/{ip}/json/"
            req = urllib.request.Request(url, headers={"User-Agent": "Zozi-CountryDetection"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data.get("country_code") or data.get("country")
        except Exception as exc:
            logger.debug("ipapi.co lookup failed for %s: %s", ip, exc)
        return None

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
