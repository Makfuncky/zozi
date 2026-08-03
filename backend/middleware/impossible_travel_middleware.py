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
            from data.db import get_service_session
            from data.models_fraud import FraudEvent
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

# --- Merged from fraud_prevention.py ---
class FraudDetectionMiddleware:
    """Real-time fraud detection for financial operations."""
    
    FRAUD_RULES = {
        "max_login_attempts_per_hour": 5,
        "max_transactions_per_hour": 10,
        "max_transaction_amount": 10000,
        "suspicious_country_change_days": 30,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_impossible_travel(self, user_id: int, country_code: str, ip_address: str) -> bool:
        """Check if login location is physically impossible."""
        recent_logins = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.actor_id == user_id,
                AuditLog.event_type == "login",
                AuditLog.occurred_at > datetime.utcnow() - timedelta(hours=1),
            )
            .all()
        )
        
        for login in recent_logins:
            if login.details_json:
                details = json.loads(login.details_json)
                prev_country = details.get("country_code")
                if prev_country and prev_country != country_code:
                    return True
        return False
    
    def check_ghost_employee(self, employee_id: int) -> bool:
        """Check if employee has zero activity for 5+ working days."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        
        recent_qr_scans = self.db.query(AuditLog).filter(
            AuditLog.resource_type == "attendance",
            AuditLog.resource_id == employee_id,
            AuditLog.occurred_at > five_days_ago,
        ).count()
        
        recent_api_activity = self.db.query(AuditLog).filter(
            AuditLog.actor_id == employee_id,
            AuditLog.occurred_at > five_days_ago,
        ).count()
        
        return recent_qr_scans == 0 and recent_api_activity == 0
    
    def check_coi(self, user_id: int, related_entity_id: int, entity_type: str) -> bool:
        """Check for conflict of interest."""
        employee = self.db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            return False
        
        related_user = self.db.query(User).filter(User.id == related_entity_id).first()
        if not related_user:
            return False
        
        if employee.country_code and related_user.staff_country_codes:
            related_countries = set(str(c).strip().upper() for c in related_user.staff_country_codes)
            if employee.country_code.upper() in related_countries:
                return True
        
        return False

# --- Merged from fraud_scoring_middleware.py ---
class FraudScoringMiddleware(BaseHTTPMiddleware):
    """Middleware that applies fraud scoring to sensitive endpoints."""
    
    def __init__(self, app, db_session=None):
        super().__init__(app)
        self.db = db_session
        self.redis = get_redis()
        self.engine = FraudScoringEngine(db_session, self.redis) if db_session else None
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        is_sensitive = any(
            path.startswith(sensitive_path) 
            for sensitive_path in SENSITIVE_PATHS.values()
        )
        is_excluded = any(path.startswith(exclude_path) for exclude_path in EXCLUDE_PATHS)
        
        if is_sensitive and not is_excluded and self.engine:
            ip_address = get_request_ip(request)
            device_hash = getattr(request.state, "device_fingerprint", None)
            user_id = None
            
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id
            
            headers = dict(request.headers)
            
            try:
                if "checkout" in path:
                    event_type = "checkout"
                elif "login" in path:
                    event_type = "login"
                elif "payout" in path or "payment" in path:
                    event_type = "payout"
                else:
                    event_type = "other"
                
                score_result = self.engine.calculate_score(
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
                        }
                    )
                    return Response(
                        content=json.dumps({"detail": "Request blocked by fraud detection"}),
                        status_code=403,
                        media_type="application/json",
                    )
                
                request.state.fraud_score = score_result.get("score", 0)
                request.state.fraud_action = score_result.get("action", "allow")
                
            except Exception as e:
                logger.error(f"Fraud scoring error: {e}")
        
        return await call_next(request)


