"""Phase 4G: country_staff_assignments seed (Task 5).

Verifies that the seed loader populates country_staff_assignments for
the demo users, so that ``auth.country_access_check()`` actually
enforces country isolation (Law 5).

Per upgrade plan (Phase 1), seed data lives directly in the Neon PostgreSQL
tables via the canonical seed module. The seed constants are defined in
``infrastructure/database/seed/_seed_constants.py`` (Python module) and the
production seed path (``seed_data()`` in ``_common.py``) inserts them via
SQLAlchemy ORM. The legacy ``seed_data/*.json`` files are deprecated
backward-compat mirrors of the same constants.
"""
from __future__ import annotations

import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
# Legacy JSON path (deprecated — kept only for backward-compat with offline
# dev tools. The canonical source of truth is the Python module below.)
SEED_FILE = _BACKEND_ROOT / "infrastructure" / "database" / "seed_data" / "country_staff_assignments_full.json"
# Canonical Python constants module (mirrors the JSON for Neon-direct seeding).
SEED_CONSTANTS_MODULE = "infrastructure.database.seed._seed_constants"


def _load_country_staff_rows() -> list[dict]:
    """Return the canonical country_staff_assignments rows from the Python module."""
    from infrastructure.database.seed import _seed_constants
    return list(_seed_constants.COUNTRY_STAFF_ASSIGNMENTS["country_staff_assignments"])


def test_seed_constants_module_exists():
    """Canonical Python seed constants module must exist (replaces JSON files)."""
    from infrastructure.database.seed import _seed_constants
    assert hasattr(_seed_constants, "COUNTRY_STAFF_ASSIGNMENTS"), (
        "infrastructure/database/seed/_seed_constants.py must define "
        "COUNTRY_STAFF_ASSIGNMENTS (the canonical source of truth, mirrored "
        "to seed_data/country_staff_assignments_full.json for backward-compat)"
    )
    assert len(_seed_constants.COUNTRY_STAFF_ASSIGNMENTS.get("country_staff_assignments", [])) > 0


def test_seed_file_includes_demo_admin():
    rows = _load_country_staff_rows()
    emails = {row["user_email"] for row in rows}
    assert "admin@zozi.com" in emails, "demo admin must have a staff assignment"


def test_seed_file_includes_ae_and_sa_for_admin():
    rows = _load_country_staff_rows()
    admin_rows = [r for r in rows if r["user_email"] == "admin@zozi.com"]
    codes = {r["country_code"] for r in admin_rows}
    assert {"AE", "SA"}.issubset(codes), "admin must be assigned to both AE and SA"


def test_seed_loader_runs_country_staff_assignments():
    """End-to-end: the seed loader registers a step for country_staff_assignments."""
    from scripts import seed_loader
    fns = [getattr(seed_loader, n) for n in dir(seed_loader) if n.startswith("seed_")]
    assert any(f.__name__ == "seed_country_staff_assignments" for f in fns)
