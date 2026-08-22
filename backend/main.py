"""
Runtime entry point for the Zozi E-commerce API.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Optional

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BACKEND_DIR)


from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from middleware.orchestrator import setup_middleware
from infrastructure.utils.ip_utils import set_request_ip
from infrastructure.database.database import engine
from infrastructure.database.base import Base
# RLS is auto-registered via @event.listens_for(Engine, ...) in rls_interceptor.py
from infrastructure.utils.config import settings
from infrastructure.utils.logging_config import setup_structlog, get_request_id
from kernel.error_handler import ErrorHandler, create_error_handler, global_exception_handler
from infrastructure.utils.versioning import VERSION_PREFIX, get_version_path, versioned_prefix, get_active_versions

# Initialize structured logging
setup_structlog(log_level=logging.INFO if settings.debug else logging.WARNING)

# Instrument SQLAlchemy engine for query timing (enables db_query_time_ms in logs)
from infrastructure.database.database_logging import instrument_database_engine
instrument_database_engine(engine)

import structlog
logger = structlog.get_logger(__name__)

# Global error handler instance (lazy init with Sentry DSN from settings)
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    global _error_handler
    if _error_handler is None:
        _error_handler = create_error_handler(
            sentry_dsn=settings.sentry_dsn,
            environment=str(settings.app_env or "development"),
        )
    return _error_handler


# Build lifespan from modular hooks (see lifespan.py)
from lifespan import build_lifespan


app = FastAPI(
    title=settings.app_name or "ZOZI Marketplace",
    version=settings.app_version or "1.0.0",
    debug=settings.debug or str(settings.app_env or "").lower() == "test",
    lifespan=build_lifespan(),
    docs_url="/docs",
    redoc_url="/redoc",
)


setup_middleware(app)

# Initialize Prometheus metrics exporter
from infrastructure.utils.prometheus_setup import setup_prometheus
setup_prometheus(app)

# Initialize OpenTelemetry tracing (requires OTEL_EXPORTER_OTLP_ENDPOINT env var)
try:
    from infrastructure.utils.tracing import setup_tracing
    from infrastructure.database.database import engine
    setup_tracing(app, db_engine=engine)
except Exception:
    logger.info("OpenTelemetry tracing skipped (packages not installed or no endpoint configured)")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "api_version": VERSION_PREFIX,
        "active_versions": get_active_versions(),
    }


@app.get("/health/deps")
async def health_deps():
    from infrastructure.utils.config import settings
    from infrastructure.utils.auth import _get_redis
    from infrastructure.database.database import check_connection_health
    
    redis_status = "ok" if _get_redis() else "unavailable"
    email_status = get_email_delivery_status()
    
    error_tracking_status = "ok" if get_error_handler().is_healthy() else "unconfigured"

    return {
        "runtime_profile": settings.runtime_profile,
        "dependencies": {
            "redis": {"status": redis_status},
            "email": {"status": email_status.get("available", False) and "ok" or "unavailable"},
            "payments": {"status": "ok"},
            "error_tracking": {"status": error_tracking_status},
        }
    }


@app.get("/health/ready")
async def health_ready():
    from infrastructure.utils.config import settings
    from infrastructure.utils.auth import _get_redis
    from infrastructure.database.database import check_connection_health
    from domains.payments.services.payments import _payment_provider_runtime_status

    db_ok = check_connection_health()
    
    deps = {"redis": "ok", "email": "ok", "payments": "ok"}
    blocking = []
    
    if settings.readiness_require_redis:
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
            from infrastructure.database.database import get_db
            with get_db() as db:
                payments = _payment_provider_runtime_status(db)
            if not payments.get("online_provider"):
                deps["payments"] = "unavailable"
                blocking.append("payments")
        except Exception:
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
from modules.admin.routers.public_comms_status import websocket_user  # noqa: E402

app.add_api_websocket_route("/ws/user", websocket_user)

# Admin background-jobs WebSocket — pushes real-time status updates after each
# background sweep completes, replacing the 15-second polling interval on the
# /admin/payouts/background-jobs dashboard.
from infrastructure.utils.websocket_manager import manager, BACKGROUND_JOBS_ROOM  # noqa: E402


@app.websocket_route("/ws/admin/background-jobs")
async def websocket_background_jobs(websocket: WebSocket):
    await websocket.accept()
    manager.active_connections[BACKGROUND_JOBS_ROOM].append(websocket)
    try:
        while True:
            # Keep the connection alive; client-side close or network drop
            # will raise an exception that we catch below.
            await websocket.receive_text()
    except Exception:
        pass
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
    """
    import importlib
    import logging

    logger = logging.getLogger(__name__)

    for _module in ["customer", "supplier", "logistics", "admin", "employee"]:
        try:
            _pkg = importlib.import_module(f"modules.{_module}.routers")
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to import modules.%s.routers: %s", _module, e)
            continue
        for _router in getattr(_pkg, "routers", []) or []:
            try:
                app.include_router(_router)
            except Exception as e:  # noqa: BLE001
                logger.error("Skipping router in %s: %s", _module, e)
        for _prouter in getattr(_pkg, "public_routers", []) or []:
            try:
                app.include_router(_prouter)
            except Exception as e:  # noqa: BLE001
                logger.error("Skipping public router in %s: %s", _module, e)

    # Alias the logistics-partner router under the plural form used by the mobile
    # app so both web ('/logistics-partner') and mobile ('/logistics-partners')
    # clients can reach shipments/scan/status endpoints.
    try:
        _lp = importlib.import_module("modules.logistics.routers.logistics_partner_verify")
        if hasattr(_lp, "router"):
            app.include_router(_lp.router, prefix="/logistics-partners")
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not register plural logistics-partner router: %s", e)

    # Expose the country control-plane under BOTH /countries/admin and
    # /admin/countries.
    try:
        _cc = importlib.import_module("modules.admin.routers.core_countries_routes")
        if hasattr(_cc, "router"):
            app.include_router(_cc.router, prefix="/admin/countries")
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not register /admin/countries alias: %s", e)


_load_routers()

# Router registration (NEW_STRUCTURE.md §3)
# Thin FastAPI routers are hand-maintained under
# ``modules/{customer,supplier,logistics,admin,employee}/routers/`` and discovered
# above. The old auto-router code-generator surface was retired during the
# NEW_STRUCTURE migration: controller ``@get/@post/...`` decorators are now
# HTTP-contract *markers* only (see ``infrastructure.routing.route_contract``).
# The retired generator lives in ``scripts/retired_auto_router.py``.

# Serve uploaded media files — only mount local disk when using local storage
if str(getattr(settings, "storage_backend", "") or os.getenv("STORAGE_BACKEND", "local")).lower() != "s3":
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    handler = get_error_handler()
    return await global_exception_handler(request, exc, handler)


from infrastructure.utils.router_loader import boot_summary, get_failed_imports, get_package_failures  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")


