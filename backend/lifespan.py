"""Modular startup / shutdown hooks for the FastAPI application.

Each ``_on_startup_*`` / ``_on_shutdown_*`` function is a self-contained
hook that can be independently tested, disabled, or extended without
touching the others.  The ``build_lifespan`` factory wires them together
into an ``asynccontextmanager`` that ``main.py`` passes to FastAPI.
"""
from __future__ import annotations

import json
import logging
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
    """
    try:
        import data.models  # noqa: F401 — register ORM tables in Base.metadata
    except Exception as exc:
        logger.warning("Could not import ORM models: %s", exc)
        return False
    try:
        from sqlalchemy import inspect

        from data.db import engine
        existing = set(inspect(engine).get_table_names()) - {"alembic_version"}
        if existing:
            logger.info("DB tables already exist (%d found), skipping schema creation", len(existing))
            return False
        from data.db import create_tables
        create_tables()
        logger.info("DB tables freshly created")
        return True
    except Exception as exc:
        logger.warning("Could not auto-create tables: %s", exc)
        return False


def _bootstrap_runtime(*, tables_just_created: bool = False) -> dict:
    """Attempt an Alembic migration upgrade on startup."""
    from utils.config import settings

    auto_migration_applied = False
    migration_reason = "none"

    if tables_just_created:
        migration_reason = "skipped_fresh_schema"
    elif str(getattr(settings, "app_env", "")).lower() in ("development", "test"):
        try:
            from utils.migrations import upgrade_database_to_head
            upgrade_database_to_head()
            auto_migration_applied = True
            migration_reason = "alembic_upgrade_head"
        except Exception as exc:
            logger.warning("Alembic auto-upgrade failed at startup: %s", exc)
            migration_reason = f"alembic_upgrade_failed: {exc}"

    logger.info(
        "Startup health: auto_migration_applied=%s migration_reason=%s",
        auto_migration_applied,
        migration_reason,
    )
    return {"auto_migration_applied": auto_migration_applied, "migration_reason": migration_reason}


def _startup_load_role_permissions() -> None:
    try:
        from data.controllers_admin_controller import load_role_permission_settings
        from data.db import SessionLocal

        db = SessionLocal()
        try:
            load_role_permission_settings(db)
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to load role permission settings at startup")


def _startup_register_event_listeners() -> None:
    try:
        from data.services_orders import _event_publisher
        from data.events import PaymentConfirmedEvent
        from data.services_fulfillment_service import FulfillmentService

        fulfillment = FulfillmentService()
        from data.db import SessionLocal

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
        logger.exception("Failed to register event listeners at startup")


def _startup_seed_treasury() -> None:
    try:
        from data.db import SessionLocal
        from db.treasury_seeder import seed_treasury_system

        db = SessionLocal()
        try:
            seed_treasury_system(db)
            logger.info("Treasury chart of accounts ensured at startup")
        finally:
            db.close()
    except Exception:
        logger.exception("Failed to seed treasury chart of accounts at startup")


def _seed_demo_data() -> None:
    """Seed demo catalog data from ``db.seed`` if enabled."""
    from utils.config import settings

    app_env = str(getattr(settings, "app_env", "development")).lower()
    default_seed = "true" if app_env in ("development", "test") else "false"
    if str(os.getenv("SEED_DATA_ON_STARTUP", default_seed)).lower() not in {"1", "true", "yes"}:
        logger.debug("Skipping demo data seed — SEED_DATA_ON_STARTUP is disabled")
        return
    try:
        from data.db import SessionLocal
        from db.seed import seed_data

        seed_data(SessionLocal)
        logger.info("Demo data seeded successfully")
    except Exception:
        logger.exception("Failed to seed demo data at startup")


def _ensure_default_accounts() -> None:
    """Idempotently ensure demo accounts exist from environment variables."""
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
        from data.db import SessionLocal
        from db.seed import _ensure_demo_user

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
        logger.exception("Failed to ensure default accounts at startup")


def _startup_background_jobs() -> list:
    """Start background job services if enabled. Returns a list of stop callables."""
    from utils.config import settings

    stoppers: list = []

    if os.environ.get("BACKGROUND_JOBS_ENABLED", "0") != "1":
        logger.info("Background jobs disabled (set BACKGROUND_JOBS_ENABLED=1 to enable)")
        return stoppers

    try:
        from data.services_command_center_background import start_background_jobs, stop_background_jobs
        start_background_jobs()
        stoppers.append(("command_center_background", stop_background_jobs))
    except Exception:
        logger.exception("Failed to start background jobs")

    try:
        from data.services_auto_payout_scheduler import (
            start_auto_payout_background_job,
            stop_auto_payout_background_job,
        )
        start_auto_payout_background_job()
        stoppers.append(("auto_payout_scheduler", stop_auto_payout_background_job))
    except Exception:
        logger.exception("Failed to start auto-payout background job")

    return stoppers


# ---------------------------------------------------------------------------
# Main lifespan factory
# ---------------------------------------------------------------------------

def build_lifespan():
    """Return an ``asynccontextmanager`` lifespan for the FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from utils.config import settings

        # --- Startup ---
        fresh = _ensure_tables_exist()
        _bootstrap_runtime(tables_just_created=fresh)
        _startup_load_role_permissions()
        _startup_seed_treasury()
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

    return lifespan
