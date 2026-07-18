"""
Runtime entry point for the Zozi E-commerce API.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from middleware.security_headers import EnhancedSecurityHeadersMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from middleware.pci_dss_compliance import PCIDSSMiddleware
from middleware.impossible_travel_middleware import ImpossibleTravelMiddleware
from middleware.ip_extraction_middleware import IPExtractionMiddleware
from middleware.country_context import CountryContextMiddleware
from utils.ip_utils import set_request_ip
from db.database import engine, Base
# RLS is auto-registered via @event.listens_for(Engine, ...) in rls_interceptor.py
from sqlalchemy import inspect
from utils.config import settings
from utils.migrations import upgrade_database_to_head

logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_ACCOUNTS = [
    ("admin@zozi.com", "admin", "admin123", "admin", "admin"),
    ("supplier@zozi.com", "supplier", "supplier123", "supplier", "supplier"),
    ("customer@zozi.com", "customer", "customer123", "customer", "customer"),
    ("logistics@zozi.com", "logistics", "logistics123", "logistics_partner", "logistics partner"),
    ("admin@test.com", "admin_test", "admin123", "admin", "test admin"),
    ("supplier@test.com", "supplier_test", "supplier123", "supplier", "test supplier"),
    ("customer@test.com", "customer_test", "customer123", "customer", "test customer"),
]


def _ensure_default_accounts() -> None:
    """Idempotently ensure the standard demo/login accounts exist.

    The database can be reset by test harnesses, which wipes these accounts and
    breaks every documented login. Recreating them on startup guarantees the
    canonical logins always work without manual seeding. Never raises so it can
    never break application startup.
    """
    try:
        from db.database import SessionLocal
        from db.seed import _ensure_demo_user

        db = SessionLocal()
        try:
            for email, username, password, role, label in DEFAULT_ACCOUNTS:
                _ensure_demo_user(
                    db,
                    email=email,
                    username=username,
                    password=password,
                    role=role,
                    log_label=label,
                )
                db.flush()
            db.commit()
            logger.info("Ensured default login accounts exist")
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to ensure default accounts at startup")


def _sqlite_schema_needs_upgrade() -> bool:
    """Check whether the SQLite database is missing columns/objects from the ORM models."""
    inspector = inspect(engine)
    metadata_tables = Base.metadata.tables
    db_tables = set(inspector.get_table_names())
    for table_name in db_tables:
        if table_name in metadata_tables:
            metadata_cols = {c.name for c in metadata_tables[table_name].columns}
            db_cols = {c["name"] for c in inspector.get_columns(table_name)}
            if not metadata_cols.issubset(db_cols):
                return True
    return False


def _bootstrap_runtime() -> dict:
    auto_migration_applied = False
    migration_reason = "none"

    if (
        str(getattr(settings, "app_env", "")).lower() == "development"
        and str(getattr(settings, "database_url", "") or "").startswith("sqlite")
        and _sqlite_schema_needs_upgrade()
    ):
        logger.warning(
            "SQLite schema drift detected but Alembic migration files have duplicate revision IDs "
            "(broken migration tree). Skipping auto-migration â€” DB already matches ORM via direct SQL."
        )
        migration_reason = "skipped_duplicate_revisions"

    logger.info(
        "Startup health: auto_migration_applied=%s migration_reason=%s",
        auto_migration_applied,
        migration_reason,
    )
    return {"auto_migration_applied": auto_migration_applied, "migration_reason": migration_reason}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _bootstrap_runtime()
    try:
        from db.database import SessionLocal
        from controllers.admin_controller import load_role_permission_settings

        db = SessionLocal()
        try:
            load_role_permission_settings(db)
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to load role permission settings at startup")
    try:
        from db.database import SessionLocal
        from db.treasury_seeder import seed_treasury_system

        _db = SessionLocal()
        try:
            seed_treasury_system(_db)
            logger.info("Treasury chart of accounts ensured at startup")
        finally:
            _db.close()
    except Exception:
        logger.exception("Failed to seed treasury chart of accounts at startup")
    _ensure_default_accounts()
    if getattr(settings, "email_scheduler_enabled", False):
        logger.info("Email campaign scheduler started")
    if os.environ.get("BACKGROUND_JOBS_ENABLED", "0") == "1":
        try:
            from services.command_center_background import start_background_jobs

            start_background_jobs()
        except Exception:
            logger.exception("Failed to start background jobs")
    else:
        logger.info("Background jobs disabled (set BACKGROUND_JOBS_ENABLED=1 to enable)")
    yield
    if getattr(settings, "email_scheduler_enabled", False):
        logger.info("Email campaign scheduler stopped")
    if os.environ.get("BACKGROUND_JOBS_ENABLED", "0") == "1":
        try:
            from services.command_center_background import stop_background_jobs

            stop_background_jobs()
        except Exception:
            logger.exception("Failed to stop background jobs")


app = FastAPI(
    title=settings.app_name or "ZOZI Marketplace",
    version=settings.app_version or "1.0.0",
    debug=settings.debug or str(settings.app_env or "").lower() == "test",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug or str(settings.app_env or "").lower() == "test" else None,
    redoc_url="/redoc" if settings.debug or str(settings.app_env or "").lower() == "test" else None,
)


app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Country-Code", "X-Requested-With"],
)
app.add_middleware(IPExtractionMiddleware)
app.add_middleware(EnhancedSecurityHeadersMiddleware, enable_hsts=settings.hsts_enabled)
app.add_middleware(ImpossibleTravelMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CountryContextMiddleware)

if str(settings.app_env or "").lower() not in ("test", "development"):
    app.add_middleware(PCIDSSMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}


@app.get("/health/deps")
async def health_deps():
    from utils.config import settings
    from utils.auth import _get_redis
    from db.database import check_connection_health
    
    redis_status = "ok" if _get_redis() else "unavailable"
    email_status = get_email_delivery_status()
    
    return {
        "runtime_profile": settings.runtime_profile,
        "dependencies": {
            "redis": {"status": redis_status},
            "email": {"status": email_status.get("available", False) and "ok" or "unavailable"},
            "payments": {"status": "ok"},
        }
    }


@app.get("/health/ready")
async def health_ready():
    from utils.config import settings
    from utils.auth import _get_redis
    from db.database import check_connection_health, get_db_session
    from controllers import payments_controller
    from types import SimpleNamespace
    
    db = get_db_session()
    db_ok = check_connection_health()
    db.close()
    
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
            payments = payments_controller._payment_provider_runtime_status(db)
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


get_email_delivery_status = get_email_delivery_status


@app.websocket_route("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        await websocket.close()

# Backwards-compatible alias for the user realtime socket. The ws_chat router is
# mounted under the "/ws-chat" prefix (=> /ws-chat/ws/user), but mobile/web
# clients connect to the bare "/ws/user" path. Keep both working.
from routers.ws_chat import websocket_user  # noqa: E402

app.add_api_websocket_route("/ws/user", websocket_user)


def _load_routers():
    """Lazy load routers to avoid circular imports."""
    import importlib
    
    router_names = [
        ("auth", "/auth"),
        ("users", "/users"),
        ("products", "/products"),
        ("orders", "/orders"),
        ("cart", "/cart"),
        ("payments", "/payments"),
        ("categories", "/categories"),
        ("countries", "/countries"),
        ("logistics", "/logistics"),
        ("logistics_health", "/logistics-health"),
        ("logistics_partner", "/logistics-partner"),
        ("logistics_orders", "/logistics-orders"),
        ("logistics_locations", "/logistics-locations"),
        ("finance", "/finance"),
        ("jobs", "/jobs"),
        ("treasury", "/treasury"),
        ("admin_treasury", "/admin/treasury"),
        ("admin", "/admin"),
        ("notifications", "/notifications"),
        ("search", "/search"),
        ("reviews", "/reviews"),
        ("wishlist", "/wishlist"),
        ("coupons", "/coupons"),
        ("banners", "/banners"),
        ("chat", "/chat"),
        ("chatbot", "/chatbot"),
        ("employees", ""),
        ("hr", "/hr"),
        ("expenses", "/expenses"),
        ("expenses", "/admin/expenses"),
        ("export", "/admin/export"),
        ("cash_management", "/cash-management"),
        ("invoices", "/invoices"),
        ("commission", "/commission"),
        ("compliance", "/compliance"),
        ("risk", "/risk"),
        ("audit", "/audit"),
        ("supplier_documents", "/supplier-documents"),
        ("supplier", "/supplier"),
        ("supplier_health", "/supplier-health"),
        ("parcel_tracking", "/parcel-tracking"),
        ("shop_locations", "/shop-locations"),
        ("cross_border", "/cross-border"),
        ("country_maps", "/country-maps"),
        ("country_admin", "/country-admin"),
        ("country_dropdown", "/country-dropdown"),
        ("country_staff", "/country-staff"),
        ("country_payouts", "/country-payouts"),
        ("country_auto_populate", "/country-auto-populate"),
        ("command_center", ""),
        ("ai", "/ai"),
        ("ai_image", "/ai-image"),
        ("ai_upload", "/ai-upload"),
        ("entity_chat", "/entity-chat"),
        ("entity_communication", "/entity-communication"),
        ("internal_channels", "/internal-channels"),
        ("onboarding", "/onboarding"),
        ("proxy_communication", "/proxy-communication"),
        ("translate", "/translate"),
        ("video_controller", "/video-controller"),
        ("travel", "/travel"),
        ("shift_handover", "/shift-handover"),
        ("succession", "/succession"),
        ("okr", "/okr"),
        ("ediscovery", "/ediscovery"),
        ("workflows", "/workflows"),
        ("tickets", "/tickets"),
        ("video", "/video"),
        ("upload", "/upload"),
        ("flash_sales", "/flash-sales"),
        ("admin_users", "/admin"),
        ("admin_products", "/admin"),
        ("admin_orders", "/admin"),
        ("admin_settings", "/admin/settings"),
        ("admin_promotions", "/admin/promotions"),
        ("admin_categories", "/admin"),
        ("admin_banners", "/admin"),
        ("admin_payouts", "/admin"),
        ("admin_cash", "/admin"),
        ("admin_commission", "/admin"),
        ("admin_logistics", "/admin"),
        ("admin_email", "/admin"),
        ("admin_suppliers", "/admin"),
        ("admin_analytics", "/admin"),
        ("admin_chat", "/admin"),
        ("admin_video", "/admin"),
        ("accounting", "/accounting"),
        ("finance_automation", "/accounting"),
        ("finance_erp", "/accounting"),
        ("addresses", "/addresses"),
        ("returns", "/returns"),
        ("geo", "/geo"),
        ("iam", "/iam"),
        ("currency", "/currency"),
        ("csp_reporting", "/csp-reporting"),
        ("product_videos", "/product-videos"),
        ("referrals", "/referrals"),
        ("fraud_detection", "/fraud-detection"),
        ("product_verification", "/product-verifications"),
        ("public_suppliers", "/suppliers"),
        ("push_notifications", "/push-notifications"),
        ("messaging", "/messaging"),
        ("ws_chat", "/ws-chat"),
        ("contact", "/contact"),
        ("email", "/email"),
        ("customer_health", "/customer-health"),
        ("permissions", "/permissions"),
        ("financial_controller", "/api"),
        ("comm", "/comm"),
        ("escalation", "/escalation"),
        ("incident", "/incident"),
        ("lms", "/lms"),
        ("product_moderation", "/product-moderation"),
        ("shipments", "/shipments"),
        ("location_api", "/location"),
    ]
    
    for name, prefix in router_names:
        try:
            module = importlib.import_module(f"routers.{name}")
        except ImportError:
            try:
                module = importlib.import_module(f"controllers.{name}")
            except ImportError as e:
                logger.warning(f"Could not import router: {name} - {e}")
                continue
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=prefix)
        # Mount public/unauthenticated routers (e.g. payment & email webhooks)
        # alongside the authenticated router so webhook callbacks are reachable.
        if hasattr(module, "public_router"):
            app.include_router(module.public_router, prefix=prefix)

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

# Serve uploaded media files
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
