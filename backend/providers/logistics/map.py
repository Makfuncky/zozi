"""
Map Provider
============
Map and location provider system.
Test file: backend/tests/_test_provider/test_map.py
"""
from __future__ import annotations
import logging
from typing import Optional, Tuple


class settings:
    map_timeout = 10
    map_cache_ttl = 3600

logger = logging.getLogger(__name__)


class LocationProvider:
    """Map and location provider system for the Zozi platform."""

    def __init__(self):
        self._default_timeout = float(settings.geo_ipapi_timeout)
        self._user_agent = "zozi-location-provider/1.0"

    def resolve_ip(self, ip: str) -> dict:
        """Resolve an IP address to location data.

        Args:
            ip: IP address string.

        Returns:
            Dict with location details: country, region, city, lat, lon, isp.
        """
        import json
        import urllib.request

        for provider_url in self._get_ip_providers():
            try:
                url = provider_url.format(ip=ip)
                req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
                with urllib.request.urlopen(req, timeout=self._default_timeout) as resp:
                    data = json.loads(resp.read().decode())
                    return {
                        "ip": ip,
                        "country": data.get("country") or data.get("country_name", ""),
                        "country_code": data.get("country_code", ""),
                        "region": data.get("regionName") or data.get("region", ""),
                        "city": data.get("city", ""),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon") or data.get("longitude"),
                        "isp": data.get("isp", ""),
                        "source": provider_url.split("/")[2],
                    }
            except Exception as exc:
                logger.debug("IP resolution failed for %s via %s: %s", ip, provider_url, exc)
                continue

        return {
            "ip": ip,
            "country": "",
            "country_code": "",
            "region": "",
            "city": "",
            "latitude": None,
            "longitude": None,
            "isp": "",
            "source": "none",
        }

    def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Reverse geocode coordinates to a human-readable address.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.

        Returns:
            Dict with address components.
        """
        import json
        import urllib.request

        url = "https://nominatim.openstreetmap.org/reverse"
        params = f"?format=json&lat={latitude}&lon={longitude}&zoom=10"
        try:
            req = urllib.request.Request(
                url + params,
                headers={"User-Agent": self._user_agent},
            )
            with urllib.request.urlopen(req, timeout=self._default_timeout) as resp:
                data = json.loads(resp.read().decode())
                return {
                    "display_name": data.get("display_name", ""),
                    "road": data.get("address", {}).get("road", ""),
                    "city": data.get("address", {}).get("city", data.get("address", {}).get("town", "")),
                    "state": data.get("address", {}).get("state", ""),
                    "country": data.get("address", {}).get("country", ""),
                    "country_code": data.get("address", {}).get("country_code", ""),
                    "postcode": data.get("address", {}).get("postcode", ""),
                    "latitude": latitude,
                    "longitude": longitude,
                }
        except Exception as exc:
            logger.error("Reverse geocoding failed for %s, %s: %s", latitude, longitude, exc)
            return {
                "display_name": "",
                "road": "",
                "city": "",
                "state": "",
                "country": "",
                "country_code": "",
                "postcode": "",
                "latitude": latitude,
                "longitude": longitude,
            }

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two coordinates in kilometers.

        Uses the Haversine formula.
        """
        import math

        R = 6371.0
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_ip_providers(self) -> list:
        return [
            "https://ipwho.is/{ip}",
            "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,query,isp",
        ]