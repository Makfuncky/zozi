from __future__ import annotations

import logging
import math
import time
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from infrastructure.utils.redis_client import redis_client as get_redis
from infrastructure.security.ip_utils import get_request_ip
from infrastructure.utils.auth import verify_token

from providers.geography.geoip import lookup_coordinates

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
        except Exception as exc:
            logger.debug("Redis cache get failed: %s", exc)

        coords = lookup_coordinates(ip)
        if coords is None:
            return None
        try:
            redis.setex(coord_key, 86400, f"{coords[0]},{coords[1]}")
        except Exception as exc:
            logger.debug("Redis coord cache set failed: %s", exc)
        return coords

    def _get_previous_location(self, redis, user_id: int) -> Optional[tuple[float, float, float]]:
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            data = redis.get(key)
            if data:
                parts = data.split(",")
                if len(parts) == 4:
                    return (float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception as exc:
            logger.debug("Redis previous location get failed: %s", exc)
        return None

    def _update_location(self, redis, user_id: int, lat: float, lon: float, ip: str) -> None:
        key = f"{self.REDIS_PREFIX}{user_id}"
        try:
            redis.setex(key, self.REDIS_TTL, f"{lat},{lon},{time.time()},{ip}")
        except Exception as exc:
            logger.debug("Redis location update failed: %s", exc)

    def _lock_session(self, redis, user_id: int, ip: str, distance: float, speed: float) -> None:
        lock_key = f"lock:impossible_travel:{user_id}"
        try:
            redis.setex(lock_key, 1800, f"{ip},{distance},{speed}")
        except Exception as exc:
            logger.debug("Redis session lock set failed: %s", exc)
        try:
            logger.warning(
                "Impossible travel detected: user_id=%s ip=%s distance=%.0fkm speed=%.0fkm/h",
                user_id, ip, distance, speed,
            )
        except Exception as exc:
            logger.debug("Logger warning failed: %s", exc)

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


# --- Fraud scoring middleware ---
# All DB / service access is delegated to ``middleware.dependencies.fraud_events``
# so this module never imports from ``domains/``.

SENSITIVE_PATHS: dict[str, str] = {
    "checkout": "/api/checkout",
    "cart": "/api/cart",
    "login": "/api/auth/login",
    "payment": "/api/payment",
    "payout": "/api/payout",
    "transfer": "/api/transfer",
    "wallet": "/api/wallet",
}
EXCLUDE_PATHS: frozenset[str] = frozenset(
    {
        "/static",
        "/media",
        "/docs",
        "/redoc",
        "/health",
        "/openapi.json",
    }
)


def _extract_user_id(request: Request) -> Optional[int]:
    """Best-effort user id from the Authorization bearer token (or cookie)."""
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.lower().startswith("Bearer ") else request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = verify_token(token)
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None


class FraudDetectionMiddleware(BaseHTTPMiddleware):
    """Real-time fraud detection for financial operations.

    All domain access is delegated to
    :mod:`middleware.dependencies.fraud_events`; this class only orchestrates
    request flow and the response.
    """

    FRAUD_RULES = {
        "max_login_attempts_per_hour": 5,
        "max_transactions_per_hour": 10,
        "max_transaction_amount": 10000,
        "suspicious_country_change_days": 30,
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if not any(path.startswith(p) for p in SENSITIVE_PATHS.values()):
            return await call_next(request)

        user_id = _extract_user_id(request)
        ip_address = get_request_ip(request)
        if user_id is None or not ip_address:
            return await call_next(request)

        country_code = request.headers.get("X-Country-Code") or getattr(request.state, "country_code", None)

        try:
            from middleware.dependencies.fraud_events import (
                detect_impossible_travel,
                detect_ghost_employee,
            )

            if country_code and detect_impossible_travel(user_id, country_code):
                logger.warning("Impossible travel detected", extra={"user_id": user_id, "ip": ip_address})
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied: impossible travel detected"},
                )

            if detect_ghost_employee(user_id):
                request.state.fraud_flag_ghost_employee = True
                logger.warning("Ghost employee detected", extra={"user_id": user_id})
        except Exception:
            logger.exception("Fraud detection check failed")

        return await call_next(request)

    def check_impossible_travel(self, db, user_id: int, country_code: str, ip_address: str) -> bool:
        """Deprecated thin wrapper kept for backward compatibility."""
        from middleware.dependencies.fraud_events import detect_impossible_travel
        return detect_impossible_travel(user_id, country_code)

    def check_ghost_employee(self, db, employee_id: int) -> bool:
        """Deprecated thin wrapper kept for backward compatibility."""
        from middleware.dependencies.fraud_events import detect_ghost_employee
        return detect_ghost_employee(employee_id)

    def check_coi(self, db, user_id: int, related_entity_id: int, entity_type: str) -> bool:
        """Deprecated thin wrapper kept for backward compatibility."""
        from middleware.dependencies.fraud_events import check_country_coi
        return check_country_coi(user_id, related_entity_id)


class FraudScoringMiddleware(BaseHTTPMiddleware):
    """Middleware that applies fraud scoring to sensitive endpoints."""

    def __init__(self, app):
        super().__init__(app)
        self.redis = get_redis()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        is_sensitive = any(path.startswith(p) for p in SENSITIVE_PATHS.values())
        is_excluded = any(path.startswith(p) for p in EXCLUDE_PATHS)
        if not (is_sensitive and not is_excluded):
            return await call_next(request)

        ip_address = get_request_ip(request)
        device_hash = getattr(request.state, "device_fingerprint", None)
        user_id = _extract_user_id(request)
        headers = dict(request.headers)

        if "checkout" in path:
            event_type = "checkout"
        elif "login" in path:
            event_type = "login"
        elif "payout" in path or "payment" in path:
            event_type = "payout"
        else:
            event_type = "other"

        try:
            from middleware.dependencies.fraud_events import calculate_fraud_score

            score_result = calculate_fraud_score(
                user_id=user_id,
                ip_address=ip_address,
                device_hash=device_hash,
                event_type=event_type,
                request_headers=headers,
            )

            if score_result.get("is_blocked"):
                logger.warning(
                    "Request blocked by fraud engine",
                    extra={
                        "path": path,
                        "ip": ip_address,
                        "score": score_result.get("score"),
                        "rules": score_result.get("triggered_rules"),
                    },
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Request blocked by fraud detection"},
                )

            request.state.fraud_score = score_result.get("score", 0)
            request.state.fraud_action = score_result.get("action", "allow")
        except Exception as e:
            logger.error(f"Fraud scoring error: {e}")

        return await call_next(request)
