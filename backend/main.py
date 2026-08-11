"""
Runtime entry point for the Zozi E-commerce API.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from middleware.orchestrator import setup_middleware
from utils.ip_utils import set_request_ip
from db.database import engine
from db.base import Base
# RLS is auto-registered via @event.listens_for(Engine, ...) in rls_interceptor.py
from utils.config import settings
from utils.logging_config import setup_structlog, get_request_id
from utils.error_handler import ErrorHandler, create_error_handler, global_exception_handler
from utils.versioning import VERSION_PREFIX, get_version_path, versioned_prefix, get_active_versions

# Initialize structured logging
setup_structlog(log_level=logging.INFO if settings.debug else logging.WARNING)

# Instrument SQLAlchemy engine for query timing (enables db_query_time_ms in logs)
from database_logging import instrument_database_engine
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
from utils.prometheus_setup import setup_prometheus
setup_prometheus(app)

# Initialize OpenTelemetry tracing (requires OTEL_EXPORTER_OTLP_ENDPOINT env var)
try:
    from utils.tracing import setup_tracing
    from db.database import engine
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
    from utils.config import settings
    from utils.auth import _get_redis
    from db.database import check_connection_health
    
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
    from utils.config import settings
    from utils.auth import _get_redis
    from db.database import check_connection_health
    from services.gateways.payments import _payment_provider_runtime_status
    from types import SimpleNamespace
    
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
    from utils.config import settings
    if not settings.smtp_host:
        return {"provider": "disabled", "available": False, "live": False}
    return {"provider": "smtp", "available": True, "live": True}


# Backwards-compatible alias for the user realtime socket. The ws_chat router is
# mounted under the "/ws-chat" prefix (=> /ws-chat/ws/user), but mobile/web
# clients connect to the bare "/ws/user" path. Keep both working.
from routers.public_comms_status import websocket_user  # noqa: E402

app.add_api_websocket_route("/ws/user", websocket_user)

# Admin background-jobs WebSocket — pushes real-time status updates after each
# background sweep completes, replacing the 15-second polling interval on the
# /admin/payouts/background-jobs dashboard.
from utils.websocket_manager import manager, BACKGROUND_JOBS_ROOM  # noqa: E402


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
    """Lazy load routers to avoid circular imports."""
    import importlib
    import glob
    
    # Routers are auto-discovered from the ``routers`` package -- no central
    # registry. Each router carries its own prefix (co-located on
    # ``APIRouter(prefix=...)``); thin delegator modules that re-export a
    # router from a controller expose it through a module-level
    # ``__router_prefix__`` so the prefix stays next to the route definition.
    failed_routers = []
    _routers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routers")
    for _path in sorted(glob.glob(os.path.join(_routers_dir, "*.py"))):
        _modname = os.path.splitext(os.path.basename(_path))[0]
        if _modname == "__init__":
            continue
        try:
            _module = importlib.import_module(f"routers.{_modname}")
        except Exception as e:  # noqa: BLE001
            failed_routers.append((_modname, str(e)))
            continue
        _router = getattr(_module, "router", None)
        if _router is None:
            continue
        _prefix = getattr(_module, "__router_prefix__", None)
        if _prefix:
            app.include_router(_router, prefix=_prefix)
        else:
            app.include_router(_router)
        if getattr(_module, "public_router", None) is not None:
            app.include_router(_module.public_router, prefix=_prefix or "")

    if failed_routers:
        _names = ", ".join(n for n, _ in failed_routers)
        logger.error("Failed to load %d router(s): %s", len(failed_routers), _names)

    # Register country-scoped routers that expose /admin/{code}/... paths
    try:
        from routers.admin_promotions_routes import country_router as promotions_country_router
        app.include_router(promotions_country_router, prefix="/admin")
    except Exception as e:
        logger.warning(f"Could not register promotions country router: {e}")

    # Alias the logistics-partner router under the plural form used by the mobile
    # app so both web ('/logistics-partner') and mobile ('/logistics-partners')
    # clients can reach shipments/scan/status endpoints.
    try:
        lp_module = importlib.import_module("routers.logistics_partner_verify")
        if hasattr(lp_module, "router"):
            app.include_router(lp_module.router, prefix="/logistics-partners")
    except Exception as e:
        logger.warning(f"Could not register plural logistics-partner router: {e}")

    # Expose the country control-plane under BOTH /countries/admin and
    # /admin/countries. The admin UI calls /admin/countries/{code}/... while the
    # public/legacy surface uses /countries/admin/{code}/..., so both must work.
    try:
        countries_module = importlib.import_module("routers.core_countries_routes")
        if hasattr(countries_module, "router"):
            app.include_router(countries_module.router, prefix="/admin/countries")
    except Exception as e:
        logger.warning(f"Could not register /admin/countries alias: {e}")


_load_routers()

# Auto-generated routers (Design 3) are emitted by `routers/generated/auto_router.py`
# directly into the `routers/` surface folder, so the auto-discovery above already
# includes them. Keep them in sync after controller changes with
# `python routers/generated/auto_router.py` (CI runs `--verify`).

# Serve uploaded media files — only mount local disk when using local storage
if str(getattr(settings, "storage_backend", "") or os.getenv("STORAGE_BACKEND", "local")).lower() != "s3":
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    handler = get_error_handler()
    return await global_exception_handler(request, exc, handler)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
