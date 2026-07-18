from __future__ import annotations

import logging
from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from db.database import SessionLocal
from models import CountryConfig, User
from services.logistics_partner_pricing import normalize_country_code
from utils.config import settings

logger = logging.getLogger(__name__)
_FALLBACK_COUNTRY = "OM"


class CountryContextMiddleware(BaseHTTPMiddleware):
    """Resolve request country context and expose it on request.state.country_code."""

    async def dispatch(self, request: Request, call_next):
        db = SessionLocal()
        try:
            active_codes = _get_active_country_codes(db)
            resolved = _resolve_country_code(request, db, active_codes)
            request.state.country_code = resolved
            response: Response = await call_next(request)
            response.headers.setdefault("X-Resolved-Country-Code", resolved)
            return response
        finally:
            db.close()


def _get_active_country_codes(db) -> set[str]:
    rows: Iterable[tuple[str]] = (
        db.query(CountryConfig.code)
        .filter(CountryConfig.is_active == True)  # noqa: E712
        .all()
    )
    codes = {normalize_country_code(code) for (code,) in rows if code}
    normalized = {code for code in codes if code}
    if normalized:
        return normalized

    configured = normalize_country_code(
        str(getattr(settings, "default_country_code", "") or getattr(settings, "default_country", ""))
    )
    if configured:
        return {configured}
    return {_FALLBACK_COUNTRY}


def _resolve_default_country(active_codes: set[str]) -> str:
    configured = normalize_country_code(
        str(getattr(settings, "default_country_code", "") or getattr(settings, "default_country", ""))
    )
    if configured and configured in active_codes:
        return configured
    if active_codes:
        return sorted(active_codes)[0]
    return _FALLBACK_COUNTRY


def _resolve_country_code(request: Request, db, active_codes: set[str]) -> str:
    candidates = [
        request.headers.get("X-Country-Code"),
        request.query_params.get("country"),
    ]

    for value in candidates:
        code = normalize_country_code(value)
        if code and code in active_codes:
            return code

    header_country = _resolve_country_from_request_headers(request)
    if header_country and header_country in active_codes:
        return header_country

    auth_header = request.headers.get("Authorization")
    if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
        user_id = _resolve_user_id_from_token(auth_header.split(" ", 1)[1].strip())
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                preferred = normalize_country_code(getattr(user, "preferred_country", None))
                if preferred and preferred in active_codes:
                    return preferred

    return _resolve_default_country(active_codes)


def _resolve_country_from_request_headers(request: Request) -> str | None:
    direct_country = (
        request.headers.get("x-vercel-ip-country")
        or request.headers.get("cf-ipcountry")
        or request.headers.get("x-country")
    )
    direct_code = normalize_country_code(direct_country)
    if direct_code:
        return direct_code

    language = str(request.headers.get("accept-language") or "").lower()
    if "-pk" in language or "ur-pk" in language:
        return "PK"
    if "-om" in language or "ar-om" in language:
        return "OM"
    if "-ae" in language or "ar-ae" in language:
        return "AE"
    return None


def _resolve_user_id_from_token(token: str) -> int | None:
    if not token:
        return None
    try:
        from utils.auth import verify_token

        subject = verify_token(token)
        if subject is None:
            return None
        return int(subject)
    except Exception:
        # Token parse failures should not block requests with a hard error.
        return None

