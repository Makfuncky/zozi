#!python
"""
Enhanced Geo-Blocking Middleware for Zozi Platform
Implements geographic access control with Redis caching and compliance blocking
"""

import time
import urllib.request
import urllib.error
import json
from typing import Optional, Dict, Set
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import settings
from utils.redis_client import redis_client
from utils.ip_utils import get_request_ip
import logging

logger = logging.getLogger(__name__)

BLOCKED_COUNTRIES: Set[str] = {
    "CN",
    "RU",
    "IR",
    "KP",
    "BY",
    "CU",
    "SD",
}

BACKUP_OPERATIONS_COUNTRIES: Set[str] = {
    "US", "CA", "GB", "DE", "FR", "JP",
    "AU", "NL", "SE", "CH", "SG", "KR"
}

HIGH_RISK_IP_PREFIXES = (
    "50.", "51.", "52.", "53.", "54.", "55.",
    "58.", "59.", "86.", "87.", "88.", "89.",
    "185.", "186.", "187.", "188.", "189.",
)


class EnhancedGeoBlockingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced geographic access control middleware with:
    - Country-based access blocking
    - Compliance-based geographic restrictions
    - Redis caching for geolocation lookups
    - Security zone classification
    """

    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis = redis_client()
        self.cache_ttl = 3600

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        client_ip = get_request_ip(request)

        country_code = await self._get_client_geolocation(client_ip)

        if country_code in BLOCKED_COUNTRIES:
            return await self._handle_blocked_request(request, country_code)

        response = await call_next(request)

        response.headers["X-Client-Country"] = country_code
        response.headers["X-Geo-Zone"] = self._get_security_zone(client_ip)

        return response

    async def _get_client_geolocation(self, client_ip: str) -> str:
        """Get client country code from IP address with Redis caching."""
        if client_ip.startswith(("192.168.", "10.", "172.16.", "127.")):
            return "INTERNAL"

        cache_key = f"geo:{client_ip}"

        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass

        country_code = self._lookup_country_from_ip(client_ip)

        if self.redis:
            try:
                self.redis.setex(cache_key, self.cache_ttl, country_code)
            except Exception:
                pass

        return country_code

    def _lookup_country_from_ip(self, client_ip: str) -> str:
        """Lookup country from IP address using ipapi.co API."""
        try:
            url = f"https://ipapi.co/{client_ip}/country/"
            req = urllib.request.Request(url, headers={"User-Agent": "Zozi-GeoIP"})
            with urllib.request.urlopen(req, timeout=5) as response:
                country_code = response.read().decode("utf-8").strip()
                return country_code if country_code and country_code != "XX" else "US"
        except Exception as e:
            logger.warning(f"GeoIP lookup failed for {client_ip}: {e}")
            return "US"

    async def _handle_blocked_request(self, request: Request, country_code: str) -> Response:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Geographic access restricted",
                "message": "Access from this jurisdiction is not permitted due to regulatory restrictions.",
                "blocked_country": country_code,
                "code": "GEOGRAPHIC_ACCESS_BLOCKED",
                "compliance": "SOX-HIPAA-GDPR",
            },
        )

    def _get_security_zone(self, client_ip: str) -> str:
        """Classify security zone based on client IP."""
        if client_ip.startswith(("192.168.", "10.", "172.16.", "127.")):
            return "INTERNAL_SECURE"
        elif client_ip.startswith(HIGH_RISK_IP_PREFIXES):
            return "HIGH_RISK_EXTERNAL"
        else:
            return "EXTERNAL_STANDARD"

    def is_country_allowed(self, country_code: str) -> bool:
        """Check if a country is allowed for operations."""
        return country_code not in BLOCKED_COUNTRIES

    def is_backup_operations_allowed(self, country_code: str) -> bool:
        """Check if country is allowed for backup operations."""
        return country_code in BACKUP_OPERATIONS_COUNTRIES

