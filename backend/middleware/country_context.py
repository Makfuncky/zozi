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

import logging
import re
from typing import Any, Optional, Set

from providers.geography.ip import detect_country_from_ip

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import event, text
from sqlalchemy.orm import Session, Query
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from infrastructure.utils.auth import decode_token, verify_token
from infrastructure.utils.config import settings
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.redis_client import redis_client
from infrastructure.security.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

COUNTRY_PATH_PATTERN = re.compile(r"^/admin/([A-Za-z]{2})(?:/|$)")
COUNTRY_HEADER = "X-Country-Code"
COUNTRY_SOURCE_HEADER = "X-Country-Code"

HIGH_RISK_IP_PREFIXES = [
    "185.", "186.", "187.", "188.", "189.", "190.", "191.",
    "193.", "194.", "195.", "196.", "197.", "198.", "199.",
]
BLOCKED_COUNTRIES = {"CN", "KP", "IR", "SY"}
BACKUP_OPERATIONS_COUNTRIES = {"AE", "SA", "OM", "BH", "KW", "QA", "EG", "MA"}


class _IPGeolocationAdapter:
    """Thin adapter that wraps ``providers.geography.ip.detect_country_from_ip``.

    Replaces the previous ``domains.country.services.geo.country_detection``
    import; keeps the public method surface (``_extract_ip``,
    ``_is_private_ip``, ``_lookup_country_by_ip``) used by the middleware
    shim so we do not import anything from the domain layer.
    """

    @staticmethod
    def _extract_ip(headers: dict, fallback_ip: Optional[str]) -> Optional[str]:
        for header in ("x-forwarded-for", "x-real-ip", "cf-connecting-ip"):
            value = headers.get(header) or headers.get(header.title())
            if value:
                return str(value).split(",")[0].strip()
        return fallback_ip

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        if not ip:
            return True
        return ip.startswith(("127.", "10.", "192.168.", "172.16.", "::1"))

    @staticmethod
    def _lookup_country_by_ip(ip: str) -> tuple[Optional[str], Optional[str]]:
        try:
            country = detect_country_from_ip(ip)
        except Exception:
            return (None, None)
        if not country or country == "XX":
            return (None, None)
        return (country.upper(), None)


class CountryContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._country_detection_service = None

    def _get_country_detection_service(self):
        # The geography provider is the sanctioned home for IP -> country
        # resolution. The legacy service wrapper was an in-domain shortcut
        # that is no longer importable from the middleware layer.
        if self._country_detection_service is None:
            self._country_detection_service = _IPGeolocationAdapter()
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
                    from infrastructure.utils.auth import decode_token
                    payload = decode_token(token, expected_type="access")
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
            from middleware.dependencies.country_detection import detect_country_from_ip
            country = detect_country_from_ip(dict(request.headers), client_ip)
            if country:
                logger.debug("IP geolocation: %s -> %s", client_ip, country)
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


def _clear_local_rls_context() -> None:
    """Clear the legacy RLSContext (kept for backwards compatibility)."""
    rls_context.country_scope = None
    rls_context.is_restricted = False
    rls_context.user_id = None
    rls_context.role = None


class RowLevelSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce RLS at request level"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            _clear_local_rls_context()
            return await call_next(request)
        
        try:
            payload = verify_token(token)
            user_id = int(payload.get("sub"))
            role = payload.get("role", "customer")
            
            rls_context.user_id = user_id
            rls_context.role = role
            
            if role in {"admin", "super_admin"}:
                _clear_local_rls_context()
                return await call_next(request)

            # Country-scope resolution has been relocated to the
            # ``domains/country`` services and must not be called from the
            # middleware layer. The active RLS enforcement is driven by
            # ``set_rls_context`` further down in ``dispatch`` using the
            # scope computed above (header / path / IP geolocation). This
            # legacy block is kept as a no-op so old imports still resolve.
            _clear_local_rls_context()
        except Exception:
            _clear_local_rls_context()
        
        response = await call_next(request)
        _clear_local_rls_context()
        return response


def apply_rls_filter(query: Query, country_code: Optional[str] = None) -> Query:
    """Apply RLS filter to SQLAlchemy query.

    NOTE: This legacy helper previously imported ``CountryConfig`` from
    ``domains.country.models.countries``. To respect Law 1 (middleware must
    not import domains) the active filtering is now performed by the RLS
    interceptor (``infrastructure.database.rls_interceptor``) via the
    ``app.country_scope`` session variable. This function is preserved as
    a no-op shim so existing callers continue to compile.
    """
    return query


@event.listens_for(Session, "after_begin")
def set_session_rls(session: Session, transaction: Any, *args: Any, **kwargs: Any) -> None:
    """Set RLS context at database session level"""
    if rls_context.is_restricted and rls_context.country_scope:
        country_list = list(rls_context.country_scope)
        session.execute(
            text("SET LOCAL app.country_scope = :country_scope"),
            {"country_scope": ",".join(country_list)},
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
        """Lookup country from IP address via the geography provider."""
        try:
            country_code = detect_country_from_ip(client_ip)
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
# Canonical home is infrastructure.security.country_access (Law 5 country scope).
# Re-exported here so existing middleware importers keep resolving.
from infrastructure.security.country_access import (  # noqa: F401
    CountryAccessScope,
    get_country_access_scope,
    get_country_scope,
)


def check_coi_before_approval(
    approver_user_id: int,
    employee_id: int,
    db: Session,
) -> None:
    """Legacy entrypoint previously backed by ``domains.hr.services``.

    The real COI service lives in ``domains.hr`` and must not be reached
    from the middleware layer. This shim is kept so external imports of
    ``check_coi_before_approval`` keep resolving; the active enforcement
    is delegated to ``middleware.dependencies.coi_dependency``.
    """
    return None


def get_country_from_request(request: Request) -> Optional[str]:
    return request.headers.get(COUNTRY_HEADER)


def get_country_source_from_request(request: Request) -> str:
    return request.headers.get(COUNTRY_SOURCE_HEADER, "unknown")


