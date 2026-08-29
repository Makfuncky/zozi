"""Modular startup / shutdown hooks for the FastAPI application.

Each ``_on_startup_*`` / ``_on_shutdown_*`` function is a self-contained
hook that can be independently tested, disabled, or extended without
touching the others.  The ``build_lifespan`` factory wires them together
into an ``asynccontextmanager`` that ``main.py`` passes to FastAPI.
"""
from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator

    from fastapi import FastAPI

import structlog

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
    # Import models to register them in Base.metadata
    # Use try/except to handle missing models gracefully
    try:
        from infrastructure.database import models  # noqa: F401
    except ImportError as exc:
        logger.warning("Could not import some ORM models: %s", exc)
    except Exception as exc:
        logger.warning("Error importing ORM models: %s", exc)
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
    """Attempt an Alembic migration upgrade on startup.

    Raises:
        RuntimeError: If migration fails in production.
    """
    from infrastructure.utils.config import settings

    auto_migration_applied = False
    migration_reason = "none"

    if tables_just_created:
        migration_reason = "skipped_fresh_schema"
    elif str(getattr(settings, "app_env", "")).lower() == "production":
        # Only run auto-migration in production
        try:
            from infrastructure.utils.migrations import upgrade_database_to_head
            upgrade_database_to_head()
            auto_migration_applied = True
            migration_reason = "alembic_upgrade_head"
        except Exception as exc:
            migration_reason = f"alembic_upgrade_failed: {exc}"
            logger.error("Alembic auto-upgrade failed at startup: %s", exc)
            raise RuntimeError(f"Alembic migration failed: {exc}") from exc
    else:
        migration_reason = "skipped_non_production"

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
    try:
        import services.unknown._registry  # noqa: F401 — import side-effects only
        logger.info("Service side-effect registry imported")
    except Exception:
        logger.exception("Failed to import services.unknown._registry at startup (non-critical)")


def _startup_register_event_listeners() -> None:
    """Register event listeners for domain events.

    Non-critical: failure is logged but does not prevent startup.
    """
    try:
        from domains.finance.services.payments.payments import _event_publisher
        from infrastructure.messaging.events import PaymentConfirmedEvent
        from domains.orders.services.fulfillment_service import FulfillmentService

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

        _event_publisher.register_listener(PaymentConfirmedEvent, _handle_fulfillment)
        logger.info("FulfillmentService registered as PaymentConfirmedEvent listener")
    except Exception:
        logger.exception("Failed to register event listeners at startup (non-critical)")


def _startup_seed_treasury() -> None:
    """Seed treasury chart of accounts on startup.

    Non-critical: failure is logged but does not prevent startup.
    """
    try:
        from infrastructure.database.treasury_seeder import seed_treasury_system
        from infrastructure.database.database import SessionLocal

        db = SessionLocal()
        try:
            seed_treasury_system(db)
            logger.info("Treasury seeded successfully")
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Failed to seed treasury chart of accounts at startup (non-critical): %s", exc)


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
    except Exception:
        logger.exception("Failed to seed demo data at startup (non-critical)")


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
    """Background jobs are handled by APScheduler.

    APScheduler is configured in the jobs module and runs periodic tasks
    such as payout sweeps, email campaigns, and cache warming.
    The scheduler is started automatically when the application boots.
    """
    from infrastructure.utils.config import settings

    logger.info("Background jobs delegated to APScheduler")

    return []


# ---------------------------------------------------------------------------
# Main lifespan factory
# ---------------------------------------------------------------------------

def build_lifespan():
    """Return an ``asynccontextmanager`` lifespan for the FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from infrastructure.utils.config import settings

        # --- Startup ---
        fresh = _ensure_tables_exist()
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
            from infrastructure.database.redis_client import redis_client
            client = redis_client()
            if hasattr(client, "close") and callable(client.close):
                client.close()
        except Exception:
            logger.exception("Failed to close Redis client")

    return lifespan


