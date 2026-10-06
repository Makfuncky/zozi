from __future__ import annotations

import re
import time
import typing
from typing import Any, Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.observability.logging_config import (
    request_id_ctx,
    user_id_ctx,
    country_code_ctx,
    db_query_time_ctx,
)
from infrastructure.observability.metrics import (
    http_request_duration_seconds,
    http_requests_total,
)

REDACTION_PLACEHOLDER = "<redacted>"

PII_FIELD_PATTERNS = {
    "password",
    "passwd",
    "pwd",
    "email",
    "e_mail",
    "user_email",
    "customer_email",
    "mail",
    "phone",
    "phone_number",
    "mobile",
    "telephone",
    "cell",
    "address",
    "addr",
    "street",
    "address_line1",
    "address_line2",
    "city",
    "country",
    "access_token",
    "token",
    "api_token",
    "auth_token",
    "refresh_token",
    "authorization",
    "card_number",
    "card_num",
    "cc_number",
    "credit_card",
    "cvv",
    "cvc",
    "cvv2",
    "cvc2",
    "bank_account",
    "account_number",
    "account_no",
    "iban",
    "national_id",
    "nationalid",
    "ssn",
    "tax_id",
    "tin",
    "dob",
    "date_of_birth",
    "birth_date",
    "ip_address",
    "ip",
    "client_ip",
    "secret",
    "api_key",
    "apikey",
}

PII_VALUE_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b"),
    re.compile(r"(?i)\b(?:Bearer|Token)\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?i)(?:api_key|apikey|secret|password)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?"),
]


def _normalize_field_name(name: str) -> str:
    return re.sub(r"[_\-\s.]+", "_", name.strip().lower()).strip("_")


def _is_pii_field(key: str, extra_fields: typing.Container[str]) -> bool:
    normalized = _normalize_field_name(key)
    if normalized in PII_FIELD_PATTERNS:
        return True
    for field in extra_fields:
        if _normalize_field_name(field) == normalized:
            return True
    return False


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in PII_VALUE_PATTERNS:
        redacted = pattern.sub(REDACTION_PLACEHOLDER, redacted)
    return redacted


def redact_pii(data: Any, sensitive_fields: typing.Iterable[str] = ()) -> Any:
    if data is None:
        return None
    if isinstance(data, bool):
        return data
    if isinstance(data, (int, float)):
        return data
    if isinstance(data, str):
        return _redact_string(data)
    if isinstance(data, dict):
        extra = tuple(sensitive_fields)
        result: dict[str, Any] = {}
        for key, value in data.items():
            if _is_pii_field(key, extra):
                result[key] = REDACTION_PLACEHOLDER
            else:
                result[key] = redact_pii(value, extra)
        return result
    if isinstance(data, list):
        return [redact_pii(item, sensitive_fields) for item in data]
    return data


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        if request_id:
            request_id_ctx.set(request_id)
            request.state.request_id = request_id

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_id_ctx.set(str(user_id))

        country_code = getattr(request.state, "country_code", None)
        if country_code:
            country_code_ctx.set(country_code)

        start_time = time.monotonic()
        response: Response | None = None
        error_occurred = False
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_occurred = True
            raise
        finally:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            method = request.method
            path = str(request.url.path)

            http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration_ms / 1000)
            http_requests_total.labels(method=method, endpoint=path, status=str(status_code)).inc()

            log = structlog.get_logger("zozi.request")
            if error_occurred or status_code >= 400:
                log.error(
                    "request_failed",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error=error_occurred,
                )
            else:
                log.info(
                    "request_complete",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            db_query_time_ctx.set(0.0)


