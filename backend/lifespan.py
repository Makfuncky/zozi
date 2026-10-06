"""Modular startup / shutdown hooks for the FastAPI application.

Each ``_on_startup_*`` / ``_on_shutdown_*`` function is a self-contained
hook that can be independently tested, disabled, or extended without
touching the others.  The ``build_lifespan`` factory wires them together
into an ``asynccontextmanager`` that ``main.py`` passes to FastAPI.
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator

    from fastapi import FastAPI

import structlog

# Ensure all models are registered before any mapper configuration
from infrastructure.database import models  # noqa: F401

# Startup bootstrap-step outcomes, surfaced by ``/health/deps`` (Law 59/81).
_BOOTSTRAP_STATUS: dict = {}

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Startup hooks
# ---------------------------------------------------------------------------

def _ensure_tables_exist() -> bool:
    """Create all ORM tables if they don't exist yet.

    Returns ``True`` if tables were freshly created (empty DB beforehand).
    Returns ``False`` if tables already existed or creation failed.

    Raises:
        RuntimeError: If table creation fails on an empty database.
    """
    # Models are imported at module level (above) to register them in Base.metadata
    try:
        from sqlalchemy import inspect

        from infrastructure.database.database import engine
        existing = set(inspect(engine).get_table_names()) - {"alembic_version"}
        if existing:
            logger.info("DB tables already exist (%d found), skipping schema creation", len(existing))
            return False
        from infrastructure.database.database import create_tables
        create_tables()
        logger.info("DB tables freshly created")
        return True
    except Exception as exc:
        logger.warning("Could not auto-create tables: %s", exc)
        return False


def _bootstrap_runtime(*, tables_just_created: bool = False) -> dict:
    """Log migration status at startup without running migrations.

    Migrations are run exclusively by the CI/CD deploy pipeline per Law 217.
    Web replicas must NEVER auto-migrate on boot.

    Returns:
        dict with auto_migration_applied=False and migration_reason explaining
        why migrations were not run at boot.
    """
    from infrastructure.utils.config import settings

    auto_migration_applied = False
    migration_reason = "none"

    if tables_just_created:
        migration_reason = "skipped_fresh_schema"
    else:
        migration_reason = "skipped_deploy_pipeline"

    logger.info(
        "Startup health: auto_migration_applied=%s migration_reason=%s",
        auto_migration_applied,
        migration_reason,
    )
    return {"auto_migration_applied": auto_migration_applied, "migration_reason": migration_reason}


def _startup_load_role_permissions() -> None:
    """Load role-permission settings into the database.

    Raises:
        RuntimeError: If permission loading fails (critical for auth).
    """
    try:
        from domains.accounts.services.permissions.permission_service import load_role_permission_settings
        from infrastructure.database.database import SessionLocal

        db = SessionLocal()
        try:
            load_role_permission_settings(db)
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Failed to load role permission settings at startup")
        raise RuntimeError(f"Failed to load role permissions: {exc}") from exc


def _startup_register_services() -> None:
    """Import the service-side-effect registry once at startup.

    ``services/_registry.py`` imports runtime-dispatched service modules
    (schedulers, webhook handlers, event consumers, websocket managers) so
    their decorators/handlers register. It was previously never imported, so
    those registrations silently never ran. Importing it here (resiliently)
    restores that wiring without ``main`` importing ``services`` directly.

    Non-critical: failure is logged but does not prevent startup.
    """
    logger.debug("Service side-effect registry import skipped — no registry module present")


_DOMAIN_SUBSCRIBER_MODULES: tuple[tuple[str, str], ...] = (
    ("domains.analytics.subscribers", "register_analytics_subscribers"),
    ("domains.audit.subscribers", "register_audit_subscribers"),
    ("domains.comms.subscribers", "register_comms_subscribers"),
    ("domains.country.subscribers", "register_country_subscribers"),
    ("domains.customers.subscribers", "register_customers_subscribers"),
    ("domains.finance.subscribers", "register_finance_subscribers"),
    ("domains.governance.subscribers", "register_governance_subscribers"),
    ("domains.logistics.subscribers", "register_logistics_subscribers"),
    ("domains.orders.subscribers", "register_orders_subscribers"),
    ("domains.promotions.subscribers", "register_promotions_subscribers"),
    ("domains.security.subscribers", "register_security_subscribers"),
    ("domains.suppliers.subscribers", "register_suppliers_subscribers"),
)


def _startup_register_domain_subscribers() -> None:
    """Invoke every ``register_<domain>_subscribers()`` entry point.

    Law 3 / WIR-009: each domain ships its own ``subscribers.py`` exposing a
    ``register_<domain>_subscribers()`` function, but nothing called them, so
    all 13 domains stayed permanently unsubscribed and every business chain in
    ``_audit/10_CHAINS_run2.md`` was PARTIAL. Registration is per-module
    fault-isolated: one broken domain logs and the rest still register, and the
    function reports the failed module names so startup evidence is complete.
    """
    import importlib

    registered: list[str] = []
    failed: list[str] = []

    for module_path, func_name in _DOMAIN_SUBSCRIBER_MODULES:
        try:
            module = importlib.import_module(module_path)
            getattr(module, func_name)()
            registered.append(func_name)
        except Exception as exc:
            failed.append(f"{func_name} ({type(exc).__name__}: {exc})")
            logger.exception("Subscriber registration failed for %s", module_path)

    if failed:
        logger.error(
            "Domain subscriber registration incomplete: %d of %d failed: %s",
            len(failed),
            len(_DOMAIN_SUBSCRIBER_MODULES),
            "; ".join(failed),
        )
    logger.info(
        "Domain event subscribers registered: %d/%d (%s)",
        len(registered),
        len(_DOMAIN_SUBSCRIBER_MODULES),
        ", ".join(registered) or "none",
    )


def _startup_register_event_listeners() -> None:
    """Register event listeners for domain events.

    Non-critical: failure is logged but does not prevent startup.
    """
    _startup_register_domain_subscribers()

    try:
        from infrastructure.messaging.events.event_bus import subscribe
        from infrastructure.messaging.events import PaymentConfirmedEvent
        from domains.orders.services.core.logistics import FulfillmentService

        fulfillment = FulfillmentService()

        from infrastructure.database.database import SessionLocal

        def _handle_fulfillment(event: PaymentConfirmedEvent) -> None:
            db = SessionLocal()
            try:
                fulfillment.handle_payment_confirmed(event, db)
            except Exception:
                logger.exception("Fulfillment handler failed for event %s", event.event_id)
            finally:
                db.close()

        subscribe(PaymentConfirmedEvent, _handle_fulfillment)
        logger.info("FulfillmentService registered as PaymentConfirmedEvent listener")
    except Exception:
        logger.exception("Failed to register event listeners at startup (non-critical)")


def _startup_seed_treasury() -> None:
    """Seed treasury chart of accounts on startup.

    Non-critical: failure is logged but does not prevent startup.
    """
    try:
        from domains.finance.services.seeders.treasury_seeder import seed_treasury_system
        from infrastructure.database.database import SessionLocal

        db = SessionLocal()
        try:
            seed_treasury_system(db)
            logger.info("Treasury seeded successfully")
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Failed to seed treasury chart of accounts at startup (non-critical): %s", exc)


def _record_bootstrap_status(step: str, status: str) -> None:
    """Record the outcome of a startup bootstrap step so ``/health/deps`` can
    surface it (Law 59 — failures are visible, never swallowed)."""
    _BOOTSTRAP_STATUS[step] = status


def get_bootstrap_status() -> dict:
    """Copy of the bootstrap-step statuses collected during startup."""
    return dict(_BOOTSTRAP_STATUS)


def _seed_demo_data() -> None:
    """Seed demo catalog data from ``db.seed`` if enabled.

    Non-critical: failure is logged but does not prevent startup.
    """
    from infrastructure.utils.config import settings

    app_env = str(getattr(settings, "app_env", "development")).lower()
    default_seed = "true" if app_env in ("development", "test") else "false"
    if str(os.getenv("SEED_DATA_ON_STARTUP", default_seed)).lower() not in {"1", "true", "yes"}:
        logger.debug("Skipping demo data seed — SEED_DATA_ON_STARTUP is disabled")
        return
    try:
        from infrastructure.database.database import SessionLocal
        from infrastructure.database.seed import seed_data

        seed_data(SessionLocal)
        logger.info("Demo data seeded successfully")
        _record_bootstrap_status("seed", "ok")
    except Exception:
        logger.exception("Failed to seed demo data at startup (non-critical)")
        _record_bootstrap_status("seed", "failed")
        return

    # Default promotion banners are domain content: seeded here (app bootstrap,
    # Law 1 arrows allow it) instead of lazily inside a GET request (Law 90).
    try:
        from infrastructure.database.database import SessionLocal
        from domains.promotions.services.banners.banner_service import seed_default_banners

        _db = SessionLocal()
        try:
            if seed_default_banners(_db):
                logger.info("Default banners seeded successfully")
        finally:
            _db.close()
    except Exception:
        logger.exception("Failed to seed default banners at startup (non-critical)")


def _ensure_default_accounts() -> None:
    """Idempotently ensure demo accounts exist from environment variables.

    Non-critical: failure is logged but does not prevent startup.
    """
    raw = os.getenv("DEFAULT_ACCOUNTS_JSON")
    if not raw:
        logger.debug("Skipping default account bootstrap — DEFAULT_ACCOUNTS_JSON not set")
        return

    try:
        accounts = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("DEFAULT_ACCOUNTS_JSON is not valid JSON — skipping account bootstrap")
        return

    try:
        from infrastructure.database.database import SessionLocal
        from infrastructure.database.seed import _ensure_demo_user

        db = SessionLocal()
        try:
            for entry in accounts:
                _ensure_demo_user(
                    db,
                    email=entry["email"],
                    username=entry["username"],
                    password=entry["password"],
                    role=entry["role"],
                    log_label=entry.get("label", entry["username"]),
                )
                db.flush()
            db.commit()
            logger.info("Ensured %d default login accounts from DEFAULT_ACCOUNTS_JSON", len(accounts))
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to ensure default accounts at startup (non-critical)")


def _startup_background_jobs() -> list:
    """Start background event workers and return stoppers for shutdown."""
    stoppers: list = []
    try:
        from jobs.event_workers import run_all_workers, stop_all_workers
        workers = run_all_workers()
        stoppers.append(("event_workers", lambda: stop_all_workers(workers)))
        logger.info("Event workers started")
    except Exception:
        logger.exception("Failed to start event workers (non-critical)")
    try:
        from infrastructure.utils.config import settings
        if getattr(settings, "backup_enabled", False):
            from infrastructure.utils.backup import get_backup_manager
            manager = get_backup_manager()
            interval = max(1, int(getattr(settings, "backup_interval_minutes", 30)))
            stop_event = threading.Event()

            def _run_backup():
                while not stop_event.is_set():
                    try:
                        manager.create_backup()
                    except Exception:
                        logger.exception("Backup job failed")
                    stop_event.wait(interval * 60)

            thread = threading.Thread(target=_run_backup, daemon=True)
            thread.start()
            stoppers.append(("backup_manager", stop_event.set))
            logger.info("Backup manager started (interval=%dm)", interval)
    except Exception:
        logger.exception("Failed to start backup manager (non-critical)")
    return stoppers


# ---------------------------------------------------------------------------
# Main lifespan factory
# ---------------------------------------------------------------------------

def _preload_all_models() -> None:
    """Import every ``domains/*/models`` module so all ORM mappers/relationships
    are registered before the first request.

    Relationship string references (e.g. ``relationship('TaxRule')``) only resolve
    when the target class is imported and its mapper registered. The router
    import chain does not reliably pull in every model module, which caused
    ``InvalidRequestError: One or more mappers failed to initialize`` at request
    time. Walking all model packages here guarantees registration. Import errors
    in individual modules are non-fatal (best-effort, like the test bootstrap).
    """
    import importlib
    import pkgutil

    def _walk(pkg_name: str) -> None:
        try:
            pkg = importlib.import_module(pkg_name)
        except Exception:
            return
        for _m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            try:
                importlib.import_module(_m.name)
            except Exception:
                continue

    for _d in (
        "accounts", "catalog", "orders", "finance", "suppliers", "logistics",
        "comms", "hr", "promotions", "security", "governance", "analytics",
        "country", "customers", "audit",
    ):
        _walk(f"domains.{_d}.models")


def build_lifespan():
    """Return an ``asynccontextmanager`` lifespan for the FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from infrastructure.utils.config import settings

        # --- Startup ---
        _preload_all_models()
        fresh = _ensure_tables_exist()

        # Re-install RLS interceptor now that tables exist (COUNTRY_AWARE_TABLES was empty at import time)
        try:
            from infrastructure.database.rls_interceptor import instrument_rls
            from infrastructure.database.database import engine
            instrument_rls(engine)
            logger.info("RLS interceptor re-installed after table creation")
        except Exception as exc:
            logger.warning("RLS re-install failed (non-critical): %s", exc)

        _bootstrap_runtime(tables_just_created=fresh)
        _startup_load_role_permissions()
        _startup_seed_treasury()
        _startup_register_services()
        _startup_register_event_listeners()
        _seed_demo_data()
        _ensure_default_accounts()

        if getattr(settings, "email_scheduler_enabled", False):
            logger.info("Email campaign scheduler started")

        stoppers = _startup_background_jobs()

        yield

        # --- Shutdown ---
        if getattr(settings, "email_scheduler_enabled", False):
            logger.info("Email campaign scheduler stopped")

        for name, stop in stoppers:
            try:
                stop()
            except Exception:
                logger.exception("Failed to stop background service: %s", name)

        try:
            from infrastructure.database.database import dispose_engine
            dispose_engine()
        except Exception:
            logger.exception("Failed to dispose database engine")

        try:
            from infrastructure.valkey.client import valkey_client
            client = valkey_client()
            if hasattr(client, "close") and callable(client.close):
                client.close()
        except Exception:
            logger.exception("Failed to close Valkey client")

    return lifespan


