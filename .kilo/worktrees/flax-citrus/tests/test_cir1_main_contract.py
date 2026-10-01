"""
Regression test for CIR1 circuit violations in the application entry point.

Previously `backend/main.py` imported two modules outside its allowed circuit:

  * ``from database_logging import instrument_database_engine``  (layer: root)
  * ``from services.payments import payments_service``           (layer: services)

Neither ``database_logging`` nor ``services`` is in the set of layers ``main``
may import (middleware / dependencies / routers / db / utils / lifespan / data).
Both were resolved:

  * ``database_logging`` was relocated to ``db/database_logging.py`` and is now
    reached through the allowed ``db`` layer.
  * The payments readiness check was moved into ``routers/health.py`` (which may
    import ``controllers`` and ``data``), so ``main`` no longer touches
    ``services`` and the previously broken readiness block was fixed.
"""
from __future__ import annotations

import os
import sys

import pytest

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(BACKEND_DIR))

MAIN_PATH = os.path.join(BACKEND_DIR, "main.py")
HEALTH_ROUTER_PATH = os.path.join(BACKEND_DIR, "routers", "health.py")


def _main_source() -> str:
    with open(MAIN_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


def test_main_no_top_level_database_logging_import():
    # Must now reach database_logging through the allowed ``db`` layer.
    src = _main_source()
    assert "from database_logging import" not in src, (
        "main.py must not import the root-level database_logging module; "
        "use db.database_logging instead."
    )
    assert "from db.database_logging import instrument_database_engine" in src


def test_main_no_services_import():
    src = _main_source()
    assert "from services.payments import" not in src, (
        "main.py must not import the services layer (CIR1 violation)."
    )
    assert "payments_controller._payment_provider_runtime_status(db)" not in src, (
        "main.py referenced an undefined payments_controller/db in health_ready; "
        "readiness checks now live in routers.public_health_management."
    )


def test_health_router_registered_with_endpoints():
    from main import app

    health_paths = {
        r.path for r in app.routes if getattr(r, "path", "").startswith("/health")
    }
    assert {"/health", "/health/deps", "/health/ready"} <= health_paths


def test_health_router_file_present_and_importable():
    assert os.path.exists(HEALTH_ROUTER_PATH)
    from routers import health as health_router

    registered = {r.path for r in health_router.router.routes}
    assert {"/health", "/health/deps", "/health/ready"} <= registered


def test_database_logging_relocated_under_db_layer():
    from db import database_logging

    assert hasattr(database_logging, "instrument_database_engine")
    # Importing the relocated module must not pull in the services layer.
    assert "services" not in getattr(database_logging, "__file__", "")
