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
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger(__name__)

COUNTRY_PATH_PATTERN = re.compile(r"^/admin/([A-Za-z]{2})(?:/|$)")
COUNTRY_HEADER = "X-Country-Code"


class CountryContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

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
                    pass

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
            svc = CountryDetectionService()
            ip = svc._extract_ip(dict(request.headers), client_ip)
            if ip and not svc._is_private_ip(ip):
                country, _ = svc._lookup_country_by_ip(ip)
                if country:
                    logger.debug("IP geolocation: %s -> %s", ip, country)
                    return country
        except Exception as exc:
            logger.debug("IP geolocation failed: %s", exc)
        return None

