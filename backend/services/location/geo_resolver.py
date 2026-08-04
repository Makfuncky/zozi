"""Location resolution utilities for the Zozi order/delivery system.

These helpers turn a client IP into approximate coordinates and reverse-geocode
lat/long into a human readable address. They are used at order placement so the
parcel sheet and delivery routing have real customer coordinates instead of a
hardcoded fallback.

External lookups are performed live (no fake coordinates are ever returned). If a
network lookup fails the caller gets a clear error so the UI can fall back to the
browser Geolocation API rather than trusting a fabricated location.
"""


import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = float(os.getenv("LOCATION_HTTP_TIMEOUT", "4.0"))
CACHE_TTL_SECONDS = int(os.getenv("LOCATION_CACHE_TTL", "3600"))
USER_AGENT = os.getenv("LOCATION_USER_AGENT", "zozi-location-service/1.0")

# Free, key-less providers. Order = preference.
IP_GEO_PROVIDERS = [
    "https://ipwho.is/{ip}",
    "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,query,isp",
]
REVERSE_GEO_URL = "https://nominatim.openstreetmap.org/reverse"


@dataclass
class IpLocation:
    ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: Optional[str] = None
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "isp": self.isp,
            "source": self.source,
            "has_coordinates": self.latitude is not None and self.longitude is not None,
        }


@dataclass
class ReverseLocation:
    latitude: float
    longitude: float
    display_name: Optional[str] = None
    address: dict = None  # type: ignore[assignment]
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "display_name": self.display_name,
            "address": self.address or {},
            "source": self.source,
        }


class _Cache:
    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self.ttl = ttl
        self._store: dict = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expires_at = item
            if expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value) -> None:
        with self._lock:
            self._store[key] = (value, time.time() + self.ttl)


_cache = _Cache()


def _parse_ipwhois(payload: dict) -> Optional[IpLocation]:
    if not payload.get("success", True):
        return None
    try:
        return IpLocation(
            ip=str(payload.get("ip")),
            country=payload.get("country"),
            country_code=payload.get("countryCode"),
            region=payload.get("region"),
            city=payload.get("city"),
            latitude=_to_float(payload.get("latitude")),
            longitude=_to_float(payload.get("longitude")),
            isp=payload.get("connection", {}).get("isp") if isinstance(payload.get("connection"), dict) else payload.get("isp"),
            source="ipwho.is",
        )
    except (TypeError, ValueError):
        return None


def _parse_ipapi(payload: dict) -> Optional[IpLocation]:
    if payload.get("status") != "success":
        return None
    try:
        return IpLocation(
            ip=str(payload.get("query")),
            country=payload.get("country"),
            country_code=payload.get("countryCode"),
            region=payload.get("regionName"),
            city=payload.get("city"),
            latitude=_to_float(payload.get("lat")),
            longitude=_to_float(payload.get("lon")),
            isp=payload.get("isp"),
            source="ip-api.com",
        )
    except (TypeError, ValueError):
        return None


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _client_ip_from_request(client_host: str, forwarded_for: Optional[str], real_ip: Optional[str]) -> str:
    if real_ip:
        return real_ip.split(",")[0].strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return client_host


def resolve_ip_location(
    ip: Optional[str] = None,
    client_host: str = "127.0.0.1",
    forwarded_for: Optional[str] = None,
    real_ip: Optional[str] = None,
) -> IpLocation:
    """Resolve an IP to approximate coordinates using live key-less providers.

    If ``ip`` is not supplied the caller's real address is derived from proxy
    headers / socket host. Raises ``RuntimeError`` if no provider succeeds so the
    caller can fall back to the browser Geolocation API instead of faking coords.
    """
    if not ip:
        ip = _client_ip_from_request(client_host, forwarded_for, real_ip)

    # Private / loopback ranges cannot be geolocated externally; surface clearly.
    if ip in ("127.0.0.1", "::1", "localhost") or ip.startswith("10.") or ip.startswith("192.168."):
        raise RuntimeError(
            "Cannot geolocate a private/local IP address; use the browser Geolocation API for coordinates."
        )

    cache_key = f"ip:{ip}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    last_error: Optional[str] = None
    for template in IP_GEO_PROVIDERS:
        url = template.format(ip=ip)
        try:
            resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200:
                last_error = f"{url} -> HTTP {resp.status_code}"
                continue
            payload = resp.json()
            location = _parse_ipwhois(payload) if "ipwho.is" in url else _parse_ipapi(payload)
            if location is None or location.latitude is None:
                last_error = f"{url} -> unparsable payload"
                continue
            _cache.set(cache_key, location)
            return location
        except requests.RequestException as exc:  # network level failure, try next provider
            last_error = f"{url} -> {exc}"
            logger.warning("Location provider failed: %s", last_error)
            continue
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = f"{url} -> {exc}"
            logger.warning("Location provider returned bad JSON: %s", last_error)
            continue

    raise RuntimeError(f"All location providers failed: {last_error}")


def reverse_geocode(latitude: float, longitude: float) -> ReverseLocation:
    """Turn lat/long into a readable address via OpenStreetMap Nominatim (key-less)."""
    cache_key = f"rev:{round(latitude, 5)}:{round(longitude, 5)}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{REVERSE_GEO_URL}?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200:
            raise RuntimeError(f"Reverse geocode HTTP {resp.status_code}")
        payload = resp.json()
    except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Reverse geocode failed: {exc}")

    result = ReverseLocation(
        latitude=latitude,
        longitude=longitude,
        display_name=payload.get("display_name"),
        address=payload.get("address", {}),
        source="nominatim.openstreetmap.org",
    )
    _cache.set(cache_key, result)
    return result

