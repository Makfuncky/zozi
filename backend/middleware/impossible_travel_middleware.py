from __future__ import annotations

import hashlib
import logging
import math
import time
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from utils.redis_client import redis_client as get_redis
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/docs", "/openapi.json", "/redoc", "/health"}
PUBLIC_PREFIXES = {"/static", "/media", "/assets"}


class ImpossibleTravelMiddleware(BaseHTTPMiddleware):
    """
    Detects impossible travel patterns.
    If an authenticated user's requests originate from geographically
    impossible locations within the time window, the session is locked.
    """

    SPEED_THRESHOLD_KMH: float = 900.0
    REDIS_PREFIX = "travel:"
    REDIS_TTL = 3600

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._should_check(request):
            return await call_next(request)

        user_id = self._extract_user_id(request)
        if user_id is None:
            return await call_next(request)

        ip_address = self._extract_ip(request)
        if not ip_address:
            return await call_next(request)

        try:
            redis = get_redis()
            if isinstance(redis, dict):
                return await call_next(request)

            current_coords = self._get_coordinates(redis, ip_address)
            if current_coords is None:
                return await call_next(request)

            previous = self._get_previous_location(redis, user_id)

            if previous is not None:
                prev_lat, prev_lon, prev_ts = previous
                elapsed = time.time() - prev_ts
                if elapsed > 0:
                    distance = self._haversine(prev_lat, prev_lon, current_coords[0], current_coords[1])
                    speed = distance / (elapsed / 3600)
                    if speed > self.SPEED_THRESHOLD_KMH:
                        self._lock_session(redis, user_id, ip_address, distance, speed)
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "Session locked due to impossible travel",
                                "fraud_action": "block",
                                "distance_km": round(distance, 1),
                                "speed_kmh": round(speed, 1),
                            },
                        )

            self._update_location(redis, user_id, current_coords[0], current_coords[1], ip_address)
        except Exception:
            logger.exception("Impossible travel check failed")

        return await call_next(request)

    def _should_check(self, request: Request) -> bool:
        path = request.url.path
        if path in PUBLIC_PATHS:
            return False
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return False
        return True

    def _extract_user_id(self, request: Request) -> Optional[int]:
        user = getattr(request.state, "user", None)
        if user is None:
            return None
        if isinstance(user, dict):
            return user.get("id")
        return getattr(user, "id", None)

    def _extract_ip(self, request: Request) -> Optional[str]:
        return get_request_ip(request)

    def _get_coordinates(self, redis, ip: str) -> Optional[tuple[float, float]]:
        coord_key = f"geo:{ip}"
        try:
            cached = redis.get(coord_key)
            if cached:
                parts = cached.split(",")
                if len(parts) == 2:
                    return (float(parts[0]), float(parts[1]))
        except Exception:
            pass

        try:
            import geoip2.database
            reader = geoip2.database.Reader("data/GeoLite2-City.mmdb")
            response = reader.city(ip)
            lat = response.location.latitude
            lon = response.location.longitude
            reader.close()
            if lat is not None and lon is not None:
                redis.setex(coord_key, 86400, f"{lat},{lon}")
                return (lat, lon)
        except Exception:
            pass
        return None

    def _get_previous_location(self, redis, user_id: int) -> Optional[tuple[float, float, float]]:
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            data = redis.get(key)
            if data:
                parts = data.split(",")
                if len(parts) == 4:
                    return (float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception:
            pass
        return None

    def _update_location(self, redis, user_id: int, lat: float, lon: float, ip: str) -> None:
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            redis.setex(key, self.REDIS_TTL, f"{lat},{lon},{time.time()},{ip}")
        except Exception:
            pass

    def _lock_session(self, redis, user_id: int, ip: str, distance: float, speed: float) -> None:
        lock_key = f"lock:impossible_travel:{user_id}"
        try:
            redis.setex(lock_key, 1800, f"{ip},{distance},{speed}")
        except Exception:
            pass
        try:
            from db.database import get_service_session
            from models.fraud import FraudEvent
            db = get_service_session()
            event = FraudEvent(
                user_id=user_id,
                event_type="impossible_travel",
                risk_score=85,
                details={"ip": ip, "distance_km": round(distance, 1), "speed_kmh": round(speed, 1), "action": "session_locked"},
                is_flagged=True,
            )
            db.add(event)
            db.commit()
            db.close()
        except Exception:
            pass

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

