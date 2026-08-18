from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from infrastructure.utils.redis_client import redis_client as get_redis
from infrastructure.utils.ip_utils import get_request_ip
from infrastructure.utils.auth import verify_token

from providers.geography.geoip import lookup_coordinates

from sqlalchemy.orm import Session
from domains.accounts.models.core import AuditLog
from domains.accounts.models.user import User
from domains.hr.models.employee_models import Employee

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

        coords = lookup_coordinates(ip)
        if coords is None:
            return None
        try:
            redis.setex(coord_key, 86400, f"{coords[0]},{coords[1]}")
        except Exception:
            pass
        return coords

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
            from domains.governance.services.impossible_travel_write_service import log_impossible_travel_lock
            log_impossible_travel_lock(
                user_id=user_id,
                ip_address=ip,
                distance_km=distance,
                speed_kmh=speed,
            )
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

# --- Merged from fraud_prevention.py / fraud_scoring_middleware.py ---
# These two middlewares were consolidated here from the original
# ``fraud_prevention.py`` and ``fraud_scoring_middleware.py`` files.  Neither
# owns a DB write: persistence lives in ``services.security.fraud_detection_service``
# (FraudScoringEngine) and the models layer.  Each opens a short-lived, read-only
# service session per request, matching the other middleware (country_context /
# coi_middleware), so the Layer-1 W1 contract (no inline Session writes) holds.

# Path prefixes that should be fraud-scored.  These constants were lost in the
# original merge; the values mirror the fraud_scoring_middleware configuration.
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

    Runs read-only checks against the audit log / HR models.  A hard fraud signal
    (impossible travel between logins) blocks the request; softer signals (ghost
    employee) are flagged on ``request.state`` for downstream logging rather than
    blocking, to avoid locking out legitimate staff.
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
            from infrastructure.database.database import get_service_session

            with get_service_session() as db:
                if country_code and self.check_impossible_travel(db, user_id, country_code, ip_address):
                    logger.warning("Impossible travel detected", extra={"user_id": user_id, "ip": ip_address})
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Access denied: impossible travel detected"},
                    )

                employee = db.query(Employee).filter(Employee.user_id == user_id).first()
                if employee and self.check_ghost_employee(db, employee.id):
                    request.state.fraud_flag_ghost_employee = True
                    logger.warning("Ghost employee detected", extra={"user_id": user_id})
        except Exception:
            logger.exception("Fraud detection check failed")

        return await call_next(request)

    def check_impossible_travel(self, db: Session, user_id: int, country_code: str, ip_address: str) -> bool:
        """Return True if a login from a different country occurred in the last hour."""
        recent_logins = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user_id,
                AuditLog.action == "login",
                AuditLog.created_at > datetime.utcnow() - timedelta(hours=1),
            )
            .all()
        )
        for login in recent_logins:
            if not login.details:
                continue
            details = json.loads(login.details) if isinstance(login.details, str) else login.details
            prev_country = details.get("country_code") if isinstance(details, dict) else None
            if prev_country and prev_country != country_code:
                return True
        return False

    def check_ghost_employee(self, db: Session, employee_id: int) -> bool:
        """Return True if the employee has zero activity for 5+ days."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        recent_qr_scans = db.query(AuditLog).filter(
            AuditLog.entity_type == "attendance",
            AuditLog.entity_id == employee_id,
            AuditLog.created_at > five_days_ago,
        ).count()
        recent_api_activity = db.query(AuditLog).filter(
            AuditLog.user_id == employee_id,
            AuditLog.created_at > five_days_ago,
        ).count()
        return recent_qr_scans == 0 and recent_api_activity == 0

    def check_coi(self, db: Session, user_id: int, related_entity_id: int, entity_type: str) -> bool:
        """Return True if the user and related entity share a country (conflict of interest)."""
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            return False
        related_user = db.query(User).filter(User.id == related_entity_id).first()
        if not related_user:
            return False
        if employee.country_code and related_user.staff_country_codes:
            related_countries = {str(c).strip().upper() for c in related_user.staff_country_codes}
            if employee.country_code.upper() in related_countries:
                return True
        return False


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
            from infrastructure.database.database import get_service_session
            from domains.governance.services.fraud_detection_service import FraudScoringEngine

            with get_service_session() as db:
                engine = FraudScoringEngine(db, self.redis)
                score_result = engine.calculate_score(
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




