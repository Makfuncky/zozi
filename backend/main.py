"""
Runtime entry point for the Zozi E-commerce API.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Optional

# Import all models FIRST to ensure SQLAlchemy class registry is populated
# before any mapper configuration happens. This MUST be the first import.
from infrastructure.database import models  # noqa: F401  # registers all ORM models

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BACKEND_DIR)


from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from middleware.orchestrator import setup_middleware
from infrastructure.utils.ip_utils import set_request_ip
from infrastructure.database.database import engine
from infrastructure.database.base import Base
from infrastructure.database.rls_interceptor import instrument_rls, install_rls_policies
from infrastructure.utils.config import settings
from infrastructure.observability.logging_config import setup_structlog, get_request_id
from infrastructure.observability.error_handler import ErrorHandler, create_error_handler, global_exception_handler
from infrastructure.utils.versioning import VERSION_PREFIX, get_version_path, versioned_prefix, get_active_versions

# Initialize structured logging (file handler activated via LOG_FILE path)
_log_file_path = os.environ.get("LOG_FILE") or os.path.join(_BACKEND_DIR, "logs", "zozi.log")
setup_structlog(
    log_level=logging.INFO if settings.debug else logging.WARNING,
    log_file=_log_file_path,
)

import structlog
logger = structlog.get_logger(__name__)

# Instrument SQLAlchemy engine for query timing (enables db_query_time_ms in logs)
from infrastructure.database.database_logging import instrument_database_engine
instrument_database_engine(engine)

# Wire RLS: per-connection before_execute interceptor (works for SQLite dev + Postgres prod)
instrument_rls(engine)

# Install RLS policies on Postgres (no-op for SQLite). Skipped during tests to
# avoid mutating the test database.
if not (settings.app_env or "").lower() == "test":
    try:
        install_rls_policies(engine)
    except Exception as _rls_exc:  # pragma: no cover - defensive
        logger.warning("RLS policy install skipped: %s", _rls_exc)

# Global error handler instance (eager init with Sentry DSN from settings)
_error_handler: ErrorHandler = create_error_handler(
    sentry_dsn=settings.sentry_dsn,
    environment=str(settings.app_env or "development"),
)


def get_error_handler() -> ErrorHandler:
    return _error_handler


# Build lifespan from modular hooks (see lifespan.py)
from lifespan import build_lifespan


app = FastAPI(
    title=settings.app_name or "ZOZI Marketplace",
    version=settings.app_version or "1.0.0",
    debug=settings.debug,
    lifespan=build_lifespan(),
    docs_url="/docs",
    redoc_url="/redoc",
)


setup_middleware(app)

# Initialize Prometheus metrics exporter
from infrastructure.observability.prometheus_setup import setup_prometheus
setup_prometheus(app)

# Mount static files for local uploads (development only)
# In production, S3/CloudFront serves media directly
import os
_uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if os.path.isdir(_uploads_dir):
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

# Initialize OpenTelemetry tracing (requires OTEL_EXPORTER_OTLP_ENDPOINT env var)
try:
    from infrastructure.utils.tracing import setup_tracing
    from infrastructure.database.database import engine
    setup_tracing(app, db_engine=engine)
except Exception as _tracing_exc:
    logger.warning("OpenTelemetry tracing disabled: %s", _tracing_exc)


@app.get("/health")
async def health_check():
    from infrastructure.database.database import check_connection_health
    from infrastructure.valkey.client import get_valkey_health_status

    db_ok = check_connection_health()
    valkey_status = get_valkey_health_status()
    email_status = get_email_delivery_status()

    try:
        from infrastructure.database.database import get_db_context
        from domains.finance.services.payments.payment_engine import _payment_provider_runtime_status
        with get_db_context() as db:
            payments_runtime = _payment_provider_runtime_status(db)
        online_provider = (
            payments_runtime.get("online_provider")
            if isinstance(payments_runtime, dict)
            else getattr(payments_runtime, "online_provider", None)
        )
        payments_ok = bool(online_provider)
    except Exception:
        payments_ok = False

    deps = {
        "database": {"status": "ok" if db_ok else "failed"},
        "valkey": {"status": "ok" if valkey_status.get("available") else "unavailable"},
        "email": {"status": "ok" if email_status.get("available") else "unavailable"},
        "payments": {"status": "ok" if payments_ok else "unavailable"},
    }

    readiness_require_valkey = getattr(settings, "readiness_require_valkey", False)
    readiness_require_email = getattr(settings, "readiness_require_email", False)
    readiness_require_payments = getattr(settings, "readiness_require_payments", False)

    valkey_blocking = readiness_require_valkey and valkey_status.get("configured", False) and not valkey_status.get("available")
    email_blocking = readiness_require_email and not email_status.get("available")
    payments_blocking = readiness_require_payments and not payments_ok

    app_env = (settings.app_env or "").lower()
    if not db_ok or valkey_blocking or email_blocking or payments_blocking:
        if app_env == "test":
            return {
                "status": "degraded",
                "version": settings.app_version,
                "api_version": VERSION_PREFIX,
                "active_versions": get_active_versions(),
                "dependencies": deps,
            }
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": settings.app_version,
                "api_version": VERSION_PREFIX,
                "active_versions": get_active_versions(),
                "dependencies": deps,
            }
        )

    return {
        "status": "healthy",
        "version": settings.app_version,
        "api_version": VERSION_PREFIX,
        "active_versions": get_active_versions(),
        "dependencies": deps,
    }


def _get_storage_health_status() -> dict:
    """Check storage/R2 health and return a status dict."""
    from infrastructure.storage.storage import get_storage, S3Storage

    store = get_storage()
    if isinstance(store, S3Storage):
        try:
            if store.client is None:
                return {"status": "unavailable", "backend": "r2", "detail": "client not initialized"}
            store.client.list_objects_v2(Bucket=store.bucket, MaxKeys=1)
            return {"status": "ok", "backend": "r2"}
        except Exception as exc:
            return {"status": "unavailable", "backend": "r2", "detail": str(exc)}
    else:
        try:
            test_file = os.path.join(store.base_dir, ".health_check")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return {"status": "ok", "backend": "local"}
        except Exception as exc:
            return {"status": "unavailable", "backend": "local", "detail": str(exc)}


@app.get("/health/deps")
async def health_deps():
    from infrastructure.utils.config import settings
    from infrastructure.valkey.client import get_valkey_health_status
    from infrastructure.database.database import check_connection_health, get_db_context
    from domains.finance.services.payments.payment_engine import _payment_provider_runtime_status
    from infrastructure.observability.circuit_breaker import get_all_breaker_stats

    db_ok = check_connection_health()

    valkey_health = get_valkey_health_status()
    valkey_status = "ok" if valkey_health.get("available") else "unavailable"
    email_status = get_email_delivery_status()

    try:
        with get_db_context() as db:
            payments_runtime = _payment_provider_runtime_status(db)
        online_provider = (
            payments_runtime.get("online_provider")
            if isinstance(payments_runtime, dict)
            else getattr(payments_runtime, "online_provider", None)
        )
        payments_status = "ok" if online_provider else "unavailable"
    except Exception:
        payments_status = "unavailable"

    error_tracking_status = "ok" if get_error_handler().is_healthy() else "unconfigured"

    breaker_stats = get_all_breaker_stats()

    storage_status = _get_storage_health_status()

    critical_deps = {
        "database": db_ok,
        "valkey": valkey_status == "ok",
        "email": email_status.get("available", False),
        "payments": payments_status == "ok",
        "storage": storage_status.get("status") == "ok",
    }

    readiness_require_valkey = getattr(settings, "readiness_require_valkey", False)
    readiness_require_email = getattr(settings, "readiness_require_email", False)
    readiness_require_payments = getattr(settings, "readiness_require_payments", False)

    flag_map = {
        "database": False,
        "valkey": readiness_require_valkey,
        "email": readiness_require_email,
        "payments": readiness_require_payments,
        "storage": False,
    }

    failed_deps = [name for name, ok in critical_deps.items() if not ok and flag_map.get(name, False)]

    response_body = {
        "runtime_profile": settings.runtime_profile,
        "dependencies": {
            "database": {"status": "ok" if db_ok else "failed"},
            "valkey": {"status": valkey_status},
            "email": {"status": email_status.get("available", False) and "ok" or "unavailable"},
            "payments": {"status": payments_status},
            "storage": storage_status,
            "error_tracking": {"status": error_tracking_status},
            "circuit_breakers": breaker_stats,
        },
    }

    if failed_deps:
        response_body["failed_dependencies"] = failed_deps
        app_env = (settings.app_env or "").lower()
        if app_env == "test" and "database" not in failed_deps:
            response_body["status"] = "degraded"
            return response_body
        return JSONResponse(status_code=503, content=response_body)

    return response_body


@app.get("/health/ready")
async def health_ready():
    from infrastructure.utils.config import settings
    from infrastructure.valkey.client import get_valkey
    from infrastructure.database.database import check_connection_health, get_db
    from domains.finance.services.payments.payment_engine import _payment_provider_runtime_status

    db_ok = check_connection_health()

    deps = {"valkey": "ok", "email": "ok", "payments": "ok"}
    blocking = []

    readiness_require_valkey = getattr(settings, "readiness_require_valkey", False)
    readiness_require_email = getattr(settings, "readiness_require_email", False)
    readiness_require_payments = getattr(settings, "readiness_require_payments", False)

    valkey_client = get_valkey()
    if not valkey_client:
        deps["valkey"] = "unavailable"
        if readiness_require_valkey:
            blocking.append("valkey")

    email = get_email_delivery_status()
    if not email.get("available"):
        deps["email"] = "unavailable"
        if readiness_require_email:
            blocking.append("email")

    try:
        with get_db() as db:
            payments = _payment_provider_runtime_status(db)
        if not payments.get("online_provider"):
            deps["payments"] = "unavailable"
            if readiness_require_payments:
                blocking.append("payments")
    except Exception:
        deps["payments"] = "unavailable"
        if readiness_require_payments:
            blocking.append("payments")

    status_code = 503 if blocking else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": len(blocking) == 0,
            "database": {"db": "ok" if db_ok else "failed"},
            "dependencies": deps,
            "blocking_dependencies": blocking,
        }
    )


def get_email_delivery_status():
    from infrastructure.utils.config import settings
    if not settings.smtp_host:
        return {"provider": "disabled", "available": False, "live": False}
    return {"provider": "smtp", "available": True, "live": True}


# Backwards-compatible alias for the user realtime socket. The ws_chat router is
# mounted under the "/ws-chat" prefix (=> /ws-chat/ws/user), but mobile/web
# clients connect to the bare "/ws/user" path. Keep both working.
from modules.admin.routers.comms import websocket_user  # noqa: E402

app.add_api_websocket_route("/ws/user", websocket_user)

# Admin background-jobs WebSocket — pushes real-time status updates after each
# background sweep completes, replacing the 15-second polling interval on the
# /admin/payouts/background-jobs dashboard.
from infrastructure.utils.websocket_manager import manager, BACKGROUND_JOBS_ROOM  # noqa: E402


@app.websocket_route("/ws/admin/background-jobs")
async def websocket_background_jobs(websocket: WebSocket, token: str = None):
    # Authenticate via JWT query param (same pattern as websocket_user)
    from infrastructure.utils.auth import decode_token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        payload = decode_token(token, expected_type="access")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return
    # Verify admin role
    role = payload.get("role")
    if str(role or "").lower() not in ("admin", "super_admin"):
        await websocket.close(code=4003, reason="Admin access required")
        return
    await websocket.accept()
    manager.active_connections[BACKGROUND_JOBS_ROOM].append(websocket)
    try:
        while True:
            # Keep the connection alive; client-side close or network drop
            # will raise an exception that we catch below.
            await websocket.receive_text()
    except Exception as e:
        # Expected: WebSocketDisconnect (client closed), network drop, or
        # transport error — these are normal lifecycle events, not bugs.
        # Unexpected: anything else (e.g. RuntimeError) may indicate a real issue
        # and is logged above for investigation. No reconnection logic here
        # because the client is responsible for reconnecting with a fresh token.
        logger.warning("WebSocket background jobs connection error", exc_info=e)
    finally:
        manager.disconnect(websocket, BACKGROUND_JOBS_ROOM)


def _load_routers():
    """Lazy-load routers from the per-actor module packages.

    Routers were re-homed from the flat ``routers`` package into
    ``modules/{customer,supplier,logistics,admin,employee}/routers/`` (see
    NEW_STRUCTURE.md section 3). Each ``modules/<m>/routers/__init__.py`` exposes
    ``routers`` and ``public_routers`` lists built from its router modules. A
    router carries its own ``APIRouter(prefix=...)``, so it is mounted at that
    prefix (no extra module prefix is added, to preserve existing URLs).

    A modular monolith must keep serving its healthy modules, so a failing
    submodule does not abort the boot. It is however never *silent*: failures
    are recorded in ``infrastructure.utils.router_loader`` with a full
    traceback, printed in the boot summary, and exposed through
    ``/health/ready``. Previously these failures were only logged with a single
    ``Skipping router`` line, which is how an entire router package could
    vanish while the app booted healthy and its routes 404'd.
    """
    import importlib
    import logging

    from infrastructure.utils.router_loader import record_package_failure

    logger = logging.getLogger(__name__)

    _failed_packages = 0
    _failed_mounts = 0

    for _module in ["customer", "supplier", "logistics", "admin", "employee"]:
        _pkg_path = f"modules.{_module}.routers"
        try:
            _pkg = importlib.import_module(_pkg_path)
        except Exception as e:
            record_package_failure(_pkg_path, f"{type(e).__name__}: {e}")
            logger.error("Failed to import %s", _pkg_path, exc_info=e)
            _failed_packages += 1
            continue

        for _label, _attr in (("router", "routers"), ("public router", "public_routers")):
            for _r in getattr(_pkg, _attr, []) or []:
                try:
                    app.include_router(_r)
                except Exception as e:  # noqa: BLE001
                    record_package_failure(
                        f"{_pkg_path}:{_label}", f"{type(e).__name__}: {e}"
                    )
                    logger.error(
                        "Failed to mount %s %r from %s",
                        _label,
                        getattr(_r, "prefix", _r),
                        _pkg_path,
                        exc_info=e,
                    )
                    _failed_mounts += 1

    if _failed_packages or _failed_mounts:
        from infrastructure.utils.router_loader import boot_summary

        logger.error(
            "ROUTER BOOT DEGRADED: %d package(s), %d mount(s) failed; app is "
            "serving a REDUCED route surface. Summary:\n%s",
            _failed_packages,
            _failed_mounts,
            boot_summary() or "(no detail)",
        )
    else:
        logger.info("Router boot clean: no package or mount failures.")




_load_routers()

# Router registration (NEW_STRUCTURE.md §3)
# Thin FastAPI routers are hand-maintained under
# ``modules/{customer,supplier,logistics,admin,employee}/routers/`` and discovered
# above. The old auto-router code-generator surface and its
# ``infrastructure.routing.route_contract`` marker decorators were fully retired
# during this cleanup — controllers and route markers have been removed; HTTP
# routes are declared directly in module routers. The retired generator lives in
# ``scripts/retired_auto_router.py``.

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    handler = get_error_handler()
    return await global_exception_handler(request, exc, handler)


from infrastructure.utils.router_loader import boot_summary, get_failed_imports, get_package_failures  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")


