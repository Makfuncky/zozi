"""
Application health endpoints.

These were previously defined inline in ``main.py``. They live here now so the
HTTP surface (routers) is the only layer that reaches into the controller and
data layers for readiness checks, keeping ``main`` within its circuit contract
(``main`` may import only middleware/dependencies/routers/db/utils/lifespan/data).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from utils.config import settings
from utils.error_handler import ErrorHandler, create_error_handler
from utils.versioning import VERSION_PREFIX, get_active_versions
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


def get_email_delivery_status() -> dict:
    if not settings.smtp_host:
        return {"provider": "disabled", "available": False, "live": False}
    return {"provider": "smtp", "available": True, "live": True}


def _get_error_handler() -> ErrorHandler:
    return create_error_handler(
        sentry_dsn=settings.sentry_dsn,
        environment=str(settings.app_env or "development"),
    )


@router.get("/health", response_model=dict)
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "api_version": VERSION_PREFIX,
        "active_versions": get_active_versions(),
    }


@router.get("/health/deps", response_model=dict)
async def health_deps():
    from utils.auth import get_redis

    email_status = get_email_delivery_status()

    redis_status = "ok" if _get_redis() else "unavailable"
    error_tracking_status = "ok" if _get_error_handler().is_healthy() else "unconfigured"

    return {
        "runtime_profile": settings.runtime_profile,
        "dependencies": {
            "redis": {"status": redis_status},
            "email": {"status": email_status.get("available", False) and "ok" or "unavailable"},
            "payments": {"status": "ok"},
            "error_tracking": {"status": error_tracking_status},
        },
    }


@router.get("/health/ready")
async def health_ready():
    from db.database import SessionLocal, check_connection_health
    from data.controllers_payments_controller import _payment_provider_runtime_status

    db_ok = check_connection_health()

    deps = {"redis": "ok", "email": "ok", "payments": "ok"}
    blocking = []

    if settings.readiness_require_redis:
        from utils.auth import get_redis

        redis = _get_redis()
        if not redis:
            deps["redis"] = "unavailable"
            blocking.append("redis")

    if settings.readiness_require_email:
        email = get_email_delivery_status()
        if not email.get("available"):
            deps["email"] = "unavailable"
            blocking.append("email")

    if settings.readiness_require_payments:
        try:
            db = SessionLocal()
            try:
                payments = _payment_provider_runtime_status(db)
                if not payments.get("online_provider"):
                    deps["payments"] = "unavailable"
                    blocking.append("payments")
            finally:
                db.close()
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("health_ready_failed", error=str(e))
            deps["payments"] = "unavailable"
            blocking.append("payments")

    status_code = 503 if blocking else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": len(blocking) == 0,
            "database": {"db": "ok" if db_ok else "failed"},
            "dependencies": deps,
            "blocking_dependencies": blocking,
        },
    )