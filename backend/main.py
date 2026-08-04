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
from utils.database_logging import instrument_database_engine
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
    from data.services_finance import _payment_provider_runtime_status
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
from routers.ws_chat import websocket_user  # noqa: E402

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
    
    router_names = [
        ("auth", "/api/v1/auth"),
        ("users", "/api/v1/users"),
        ("products", "/api/v1/products"),
        ("orders", "/api/v1/orders"),
        ("cart", "/api/v1/cart"),
        ("payments", "/api/v1/payments"),
        ("categories", "/api/v1/categories"),
        ("countries", "/api/v1/countries"),
        ("logistics", "/api/v1/logistics"),
        ("logistics_health", "/api/v1/logistics-health"),
        ("logistics_partner", "/api/v1/logistics-partner"),
        ("logistics_orders", "/api/v1/logistics-orders"),
        ("logistics_locations", "/api/v1/logistics-locations"),
        ("finance", "/api/v1/finance"),
        ("jobs", "/api/v1/jobs"),
        ("treasury", "/api/v1/treasury"),
        ("admin_treasury", "/api/v1/admin/treasury"),
        ("admin", "/api/v1/admin"),
        ("admin_fallback", "/api/v1/admin"),
        ("notifications", "/api/v1/notifications"),
        ("search", "/api/v1/search"),
        ("reviews", "/api/v1/reviews"),
        ("wishlist", "/api/v1/wishlist"),
        ("coupons", "/api/v1/coupons"),
        ("banners", "/api/v1/banners"),
        ("chat", "/api/v1/chat"),
        ("chatbot", "/api/v1/chatbot"),
        ("employees", "/api/v1"),
        ("hr", "/api/v1/hr"),
        ("hr_dashboard", "/api/v1"),
        ("expenses", "/api/v1/expenses"),
        ("export", "/api/v1/admin/export"),
        ("cash_management", "/api/v1/cash-management"),
        ("invoices", "/api/v1/invoices"),
        ("commission", "/api/v1/commission"),
        ("compliance", "/api/v1/compliance"),
        ("risk", "/api/v1/risk"),
        ("audit", "/api/v1/audit"),
        ("supplier_documents", "/api/v1/supplier-documents"),
        ("supplier", "/api/v1/supplier"),
        ("supplier_health", "/api/v1/supplier-health"),
        ("supplier_analytics", "/api/v1/supplier-analytics"),
        ("supplier_orders", "/api/v1/supplier-orders"),
        ("supplier_orders", "/api/v1/supplier/orders"),
        ("supplier_payouts", "/api/v1/supplier-payouts"),
        ("supplier_payouts", "/api/v1/supplier/payouts"),
        ("supplier_finance", "/api/v1/supplier-finance"),
        ("supplier_finance", "/api/v1/supplier/finance"),
        ("supplier_products", "/api/v1/supplier-products"),
        ("supplier_profile", "/api/v1/supplier-profile"),
        ("logistics_orders_v2", "/api/v1/logistics-orders-v2"),
        ("parcel_tracking", "/api/v1/parcel-tracking"),
        ("shop_locations", "/api/v1/shop-locations"),
        ("cross_border", "/api/v1/cross-border"),
        ("country_maps", "/api/v1/country-maps"),
        ("country_admin", "/api/v1/country-admin"),
        ("country_dropdown", "/api/v1/country-dropdown"),
        ("country_staff", "/api/v1/country-staff"),
        ("country_payouts", "/api/v1/country-payouts"),
        ("country_auto_populate", "/api/v1/country-auto-populate"),
        ("command_center", "/api/v1"),
        ("ai", "/api/v1/ai"),
        ("ai_image", "/api/v1/ai-image"),
        ("ai_upload", "/api/v1/ai-upload"),
        ("entity_chat", "/api/v1/entity-chat"),
        ("entity_communication", "/api/v1/entity-communication"),
        ("internal_channels", "/api/v1/internal-channels"),
        ("onboarding", "/api/v1/onboarding"),
        ("proxy_communication", "/api/v1/proxy-communication"),
        ("translate", "/api/v1/translate"),
        ("video_controller", "/api/v1/video-controller"),
        ("travel", "/api/v1/travel"),
        ("shift_handover", "/api/v1/shift-handover"),
        ("succession", "/api/v1/succession"),
        ("performance", "/api/v1"),
        ("okr", "/api/v1/okr"),
        ("ediscovery", "/api/v1/ediscovery"),
        ("workflows", "/api/v1/workflows"),
        ("tickets", "/api/v1/tickets"),
        ("video", "/api/v1/video"),
        ("upload", "/api/v1/upload"),
        ("flash_sales", "/api/v1/flash-sales"),
        ("admin_users", "/api/v1/admin"),
        ("admin_products", "/api/v1/admin"),
        ("admin_orders", "/api/v1/admin"),
        ("admin_settings", "/api/v1/admin/settings"),
        ("admin_promotions", "/api/v1/admin/promotions"),
        ("admin_categories", "/api/v1/admin"),
        ("admin_banners", "/api/v1/admin"),
        ("admin_payouts", "/api/v1/admin"),
        ("payout_approval", "/api/v1/admin/payout-approval"),
        ("admin_cash", "/api/v1/admin"),
        ("admin_commission", "/api/v1/admin"),
        ("admin_logistics", "/api/v1/admin"),
        ("admin_email", "/api/v1/admin"),
        ("admin_suppliers", "/api/v1/admin"),
        ("admin_analytics", "/api/v1/admin"),
        ("admin_chat", "/api/v1/admin"),
        ("admin_video", "/api/v1/admin"),
        ("accounting", "/api/v1/accounting"),
        ("finance_automation", "/api/v1/accounting"),
        ("finance_erp", "/api/v1/accounting"),
        ("addresses", "/api/v1/addresses"),
        ("returns", "/api/v1/returns"),
        ("geo", "/api/v1/geo"),
        ("iam", "/api/v1/iam"),
        ("currency", "/api/v1/currency"),
        ("csp_reporting", "/api/v1/csp-reporting"),
        ("product_videos", "/api/v1/product-videos"),
        ("referrals", "/api/v1/referrals"),
        ("fraud_detection", "/api/v1/fraud-detection"),
        ("product_verification", "/api/v1/product-verifications"),
        ("public_suppliers", "/api/v1/suppliers"),
        ("push_notifications", "/api/v1/push-notifications"),
        ("messaging", "/api/v1/messaging"),
        ("ws_chat", "/api/v1/ws-chat"),
        ("contact", "/api/v1/contact"),
        ("email", "/api/v1/email"),
        ("customer_health", "/api/v1/customer-health"),
        ("permissions", "/api/v1/permissions"),
        ("payroll", "/api/v1/payroll"),
        ("comm", "/api/v1/comm"),
        ("comms_unified", "/api/v1/comms"),
        ("escalation", "/api/v1/escalation"),
        ("incident", "/api/v1/incident"),
        ("hierarchy", "/api/v1/hierarchy"),
        ("lms", "/api/v1/lms"),
        ("product_moderation", "/api/v1/product-moderation"),
        ("shipments", "/api/v1/shipments"),
        ("location_api", "/api/v1/location"),
        ("supplier_bg_ab_test", "/api/v1/supplier"),
        ("upload_jobs", "/api/v1"),
        ("batch_upload", "/api/v1/supplier"),
        ("trading", "/api/v1/trading"),
        ("imports", "/api/v1/imports"),
        ("automation", "/api/v1/automation"),
        ("country_research", "/api/v1/country-research"),
        ("ai_research", "/api/v1/country-research/ai"),
        ("frontend_errors", "/api/v1"),
        ("chat_enrichment", "/api/v1/chat-enrichment"),
        ("email_enrichment", "/api/v1/email-enrichment"),
        ("ess", "/api/v1/ess"),
        ("email_controller", "/api/v1/email-gateway"),
    ]

    failed_routers = []
    for name, prefix in router_names:
        try:
            module = importlib.import_module(f"routers.{name}")
        except ImportError:
            try:
                module = importlib.import_module(f"controllers.{name}")
            except ImportError as e:
                failed_routers.append((name, str(e)))
                continue
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=prefix)
        # Mount public/unauthenticated routers (e.g. payment & email webhooks)
        # alongside the authenticated router so webhook callbacks are reachable.
        if hasattr(module, "public_router"):
            app.include_router(module.public_router, prefix=prefix)

    if failed_routers:
        names = ", ".join(n for n, _ in failed_routers)
        logger.error(
            "Failed to load %d router(s): %s",
            len(failed_routers),
            names,
        )

    # Register country-scoped routers that expose /admin/{code}/... paths
    try:
        from routers.admin_promotions import country_router as promotions_country_router
        app.include_router(promotions_country_router, prefix="/admin")
    except Exception as e:
        logger.warning(f"Could not register promotions country router: {e}")

    # Alias the logistics-partner router under the plural form used by the mobile
    # app so both web ('/logistics-partner') and mobile ('/logistics-partners')
    # clients can reach shipments/scan/status endpoints.
    try:
        lp_module = importlib.import_module("routers.logistics_partner")
        if hasattr(lp_module, "router"):
            app.include_router(lp_module.router, prefix="/logistics-partners")
    except Exception as e:
        logger.warning(f"Could not register plural logistics-partner router: {e}")

    # Expose the country control-plane under BOTH /countries/admin and
    # /admin/countries. The admin UI calls /admin/countries/{code}/... while the
    # public/legacy surface uses /countries/admin/{code}/..., so both must work.
    try:
        countries_module = importlib.import_module("routers.countries")
        if hasattr(countries_module, "router"):
            app.include_router(countries_module.router, prefix="/admin/countries")
    except Exception as e:
        logger.warning(f"Could not register /admin/countries alias: {e}")


_load_routers()

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
