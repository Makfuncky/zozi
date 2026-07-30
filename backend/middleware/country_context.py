"""
Country Context Middleware
Sets the RLS country scope for every request based on:
1. JWT token country_scope claim (for staff users)
2. CountryStaffAssignment records (for users with assigned countries)
3. X-Country-Code header (for admin/super-admin)
4. IP geolocation fallback (for anonymous / customer users)

The middleware runs BEFORE request handlers so that all DB queries
are automatically scoped by the RLS interceptor.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
import urllib.request
from typing import Any, Optional, Set

from fastapi import Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy import event, text
from sqlalchemy.orm import Session, Query
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from db.database import get_db
from models import User, CountryStaffAssignment, CountryConfig
from utils.auth import decode_token, verify_token, SECRET_KEY, ALGORITHM
from utils.config import settings
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.redis_client import redis_client
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

COUNTRY_PATH_PATTERN = re.compile(r"^/admin/([A-Za-z]{2})(?:/|$)")
COUNTRY_HEADER = "X-Country-Code"

HIGH_RISK_IP_PREFIXES = [
    "185.", "186.", "187.", "188.", "189.", "190.", "191.",
    "193.", "194.", "195.", "196.", "197.", "198.", "199.",
]
BLOCKED_COUNTRIES = {"CN", "KP", "IR", "SY"}
BACKUP_OPERATIONS_COUNTRIES = {"AE", "SA", "OM", "BH", "KW", "QA", "EG", "MA"}


class CountryContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._country_detection_service = None

    def _get_country_detection_service(self):
        if self._country_detection_service is None:
            from services.country_detection import CountryDetectionService
            self._country_detection_service = CountryDetectionService()
        return self._country_detection_service

    async def dispatch(self, request: Request, call_next) -> Response:
        scope: Optional[set[str]] = None
        is_restricted = False

        user = getattr(request.state, "user", None)
        role = ""
        user_id = None

        if user is not None:
            role = str(getattr(user, "role", "") or "").lower()
            user_id = getattr(user, "id", None)
        else:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
                try:
                    from utils.auth import decode_token
                    payload = decode_token(token)
                    role = str(payload.get("role", "") or "").lower()
                    user_id = payload.get("sub")
                except Exception:
                    logger.warning("Failed to decode JWT in country context middleware")
                    role = ""
                    user_id = None

        path_country = self._extract_country_from_path(request.url.path)
        header_country = request.headers.get(COUNTRY_HEADER)
        country_from_header = header_country.upper() if header_country else None

        if role in ("admin", "super_admin"):
            if country_from_header:
                scope = {country_from_header}
                request.state.country_code = country_from_header
            elif path_country:
                scope = {path_country}
                request.state.country_code = path_country
            else:
                request.state.country_code = None
            is_restricted = False
        else:
            if country_from_header:
                scope = {country_from_header}
                request.state.country_code = country_from_header
            elif path_country:
                scope = {path_country}
                request.state.country_code = path_country
            else:
                staff_codes = None
                if user is not None:
                    if isinstance(user, dict):
                        staff_codes = user.get("staff_country_codes")
                    else:
                        staff_codes = getattr(user, "staff_country_codes", None)
                if staff_codes and isinstance(staff_codes, (list, tuple)):
                    codes = {str(c).upper() for c in staff_codes if c}
                    if codes:
                        scope = codes
                        is_restricted = True

                if scope:
                    request.state.country_code = next(iter(scope))
                else:
                    country_code = self._detect_country_from_request(request)
                    if country_code:
                        request.state.country_code = country_code
            request.state.country_is_restricted = is_restricted
            request.state.country_scope = scope

        set_rls_context(scope, is_restricted=is_restricted)

        response: Response = await call_next(request)
        clear_rls_context()
        return response

    @staticmethod
    def _extract_country_from_path(path: str) -> Optional[str]:
        match = COUNTRY_PATH_PATTERN.match(path)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def _detect_country_from_request(request: Request) -> Optional[str]:
        client_ip = getattr(request.state, "client_ip", None)
        if not client_ip:
            return None
        try:
            from services.country_detection import CountryDetectionService
            svc = self._get_country_detection_service()
            ip = svc._extract_ip(dict(request.headers), client_ip)
            if ip and not svc._is_private_ip(ip):
                country, _ = svc._lookup_country_by_ip(ip)
                if country:
                    logger.debug("IP geolocation: %s -> %s", ip, country)
                    return country
        except Exception as exc:
            logger.debug("IP geolocation failed: %s", exc)
        return None

# --- Merged from advanced_rls.py ---
class RLSContext:
    """Request context for RLS enforcement"""
    def __init__(self):
        self.country_scope: Optional[Set[str]] = None
        self.is_restricted: bool = False
        self.user_id: Optional[int] = None
        self.role: Optional[str] = None


rls_context = RLSContext()


def get_rls_context() -> RLSContext:
    return rls_context


def clear_rls_context() -> None:
    rls_context.country_scope = None
    rls_context.is_restricted = False
    rls_context.user_id = None
    rls_context.role = None


def resolve_user_country_scope(user: User, db: Session) -> Set[str]:
    """Resolve allowed country codes for a user"""
    if user.role in {"admin", "super_admin"}:
        return set()
    
    assignments = (
        db.query(CountryStaffAssignment.country_code)
        .filter(
            CountryStaffAssignment.user_id == user.id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    
    codes = {str(row[0]).upper().strip() for row in assignments if row[0]}
    return codes


class RowLevelSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce RLS at request level"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            clear_rls_context()
            return await call_next(request)
        
        try:
            payload = verify_token(token)
            user_id = int(payload.get("sub"))
            role = payload.get("role", "customer")
            
            rls_context.user_id = user_id
            rls_context.role = role
            
            if role in {"admin", "super_admin"}:
                clear_rls_context()
                return await call_next(request)
            
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    scope = resolve_user_country_scope(user, db)
                    rls_context.country_scope = scope
                    rls_context.is_restricted = bool(scope)
        except Exception:
            clear_rls_context()
        
        response = await call_next(request)
        clear_rls_context()
        return response


def apply_rls_filter(query: Query, country_code: Optional[str] = None) -> Query:
    """Apply RLS filter to SQLAlchemy query"""
    if rls_context.is_restricted:
        if rls_context.country_scope:
            return query.filter(CountryConfig.code.in_(rls_context.country_scope))
    return query


@event.listens_for(Session, "after_begin")
def set_session_rls(session: Session, transaction: Any, *args: Any, **kwargs: Any) -> None:
    """Set RLS context at database session level"""
    if rls_context.is_restricted and rls_context.country_scope:
        country_list = list(rls_context.country_scope)
        session.execute(
            text(f"SET LOCAL app.country_scope = '{','.join(country_list)}'")
        )


# PostgreSQL function for RLS
"""
CREATE OR REPLACE FUNCTION rls_check_country()
RETURNS BOOLEAN AS $$
BEGIN
    IF current_setting('app.country_scope', true) = '' THEN
        RETURN TRUE;
    END IF;
    RETURN country_code::text = ANY(string_to_array(current_setting('app.country_scope'), ','));
END;
$$ LANGUAGE plpgsql;
"""

# --- Merged from geo_blocking.py ---
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

# --- Merged from rls_dependency.py ---
class CountryAccessScope:
    def __init__(self, country_codes: list[str]):
        self.country_codes = country_codes
    
    def has_access(self, country_code: str) -> bool:
        return country_code.upper() in [c.upper() for c in self.country_codes]


def get_country_access_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    if not current_user:
        return CountryAccessScope([])
    
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return CountryAccessScope(["ALL"])
    
    codes = current_user.get("staff_country_codes", [])
    return CountryAccessScope(codes or [])


def get_country_scope(current_user: Optional[dict] = Depends(None)) -> CountryAccessScope:
    return get_country_access_scope(current_user)


def check_coi_before_approval(
    approver_user_id: int,
    employee_id: int,
    db: Session,
) -> None:
    blocked, reason = check_approval_blocked(approver_user_id, employee_id, db)
    if blocked:
        raise HTTPException(
            status_code=403,
            detail=f"Approval blocked due to Conflict of Interest: {reason}"
        )
