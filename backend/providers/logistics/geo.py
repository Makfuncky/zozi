from __future__ import annotations

"""
Geo Provider
============
IP address detection for customer location and country detection.
Test file: backend/tests/_test_provider/test_geo.py
"""
import ipaddress
import json
import logging
import urllib.request
from typing import Optional, Tuple


class settings:
    geo_timeout = 10
    ip_geolocation_api = "http://ip-api.com"

logger = logging.getLogger(__name__)


class CountryDetectionProvider:
    """IP address detection for customer location and country detection."""

    IP_HEADER_MAPPING = {
        "X-Forwarded-For": lambda v: v.split(",")[0].strip() if v else None,
        "X-Real-IP": lambda v: v.strip() if v else None,
        "CF-Connecting-IP": lambda v: v.strip() if v else None,
        "True-Client-IP": lambda v: v.strip() if v else None,
        "X-AppEngine-Canonical": lambda v: v.strip() if v else None,
    }

    def __init__(self):
        self._geoip_reader = None
        self._default_country = settings.geo_default_country

    def detect_country_from_ip(
        self,
        request_headers: dict,
        client_host: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Detect country from IP address using request headers.

        Args:
            request_headers: HTTP request headers.
            client_host: Direct client IP if headers are unavailable.

        Returns:
            Tuple of (country_code, source) where source is 'geoip2',
            'ipapi', 'private', or 'default'.
        """
        ip = self._extract_ip(request_headers, client_host)
        if not ip:
            return self._default_country, "unknown"

        if self._is_private_ip(ip):
            return self._default_country, "private"

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
        country = self._lookup_geoip2(ip)
        if country:
            return country, "geoip2"

        country = self._lookup_ipapi(ip)
        if country:
            return country, "ipapi"

        return self._default_country, "default"

    def _lookup_geoip2(self, ip: str) -> Optional[str]:
        try:
            import geoip2.database
            if self._geoip_reader is None:
                geoip_db_path = "/usr/share/GeoIP/GeoLite2-Country.mmdb"
                try:
                    self._geoip_reader = geoip2.database.Reader(geoip_db_path)
                except Exception:
                    return None
            if self._geoip_reader:
                response = self._geoip_reader.country(ip)
                if response and response.country and response.country.iso_code:
                    return response.country.iso_code
        except Exception:
            pass
        return None

    def _lookup_ipapi(self, ip: str) -> Optional[str]:
        try:
            url = f"https://ipapi.co/{ip}/json/"
            req = urllib.request.Request(url, headers={"User-Agent": "Zozi-CountryDetection"})
            with urllib.request.urlopen(req, timeout=settings.geo_ipapi_timeout) as resp:
                data = json.loads(resp.read().decode())
                return data.get("country_code") or data.get("country")
        except Exception as exc:
            logger.debug("ipapi.co lookup failed for %s: %s", ip, exc)
        return None

    def get_country_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        tolerance_km: float = 100.0,
    ) -> Optional[str]:
        """Get country code from coordinates."""
        return self._default_country

    def get_country_details(self, country_code: str) -> dict:
        """Get detailed information about a country."""
        return {
            "code": country_code,
            "name": country_code,
            "currency": "USD",
            "capital": "Unknown",
            "languages": [],
            "region": "Unknown",
        }