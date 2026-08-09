"""Regression tests for the remaining security-domain audit fixes.

Covers (per SYSTEM_AUDIT_REPORT.md):
  * routers/fraud_detection.py  -> W1 / LC1 / CG1  (no db.query / session writes / data.models import)
  * middleware/coi_middleware.py + country_context.py -> CG1 (middleware only calls 'data'/'utils', no service layer)
  * middleware/country_context.py -> SEC101 (parameterized set_config, no raw SQL interpolation)
  * data/pg_rls_policies.sql + app.current_country_code signal -> DBA05
  * 6 RLS enforcers consolidated to one -> L1
  * utils/error_handler.py:148 SEC101 -> FALSE POSITIVE (no raw SQL present)
"""
from __future__ import annotations

import importlib
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("CSRF_DISABLED", "true")

from pathlib import Path

import pytest

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

FORBIDDEN_ROUTER_OPS = (
    "db.add(", "db.commit(", "db.delete(", "db.query(",
    "session.add(", "session.commit(", "session.delete(",
    "session.execute(",
)


def _read(rel: str) -> str:
    return (BACKEND / rel).read_text(encoding="utf-8")


def _rglob_rls_hits() -> list[str]:
    hits = []
    for f in BACKEND.rglob("*.py"):
        if any(part in f.parts for part in ("_trash", "_extra_files", "experiments", "backend_backup")):
            continue
        stem = f.stem
        if stem.startswith("rls_") or stem == "country_rls":
            hits.append(str(f))
    return hits


# --- fraud_detection.py : W1 / LC1 / CG1 ---------------------------------


def test_fraud_router_no_models_import():
    src = _read("routers/fraud_detection.py")
    assert "from data.models import" not in src
    assert "import data.models" not in src


@pytest.mark.parametrize("op", FORBIDDEN_ROUTER_OPS)
def test_fraud_router_no_session_writes(op):
    src = _read("routers/fraud_detection.py")
    assert op not in src, f"forbidden router operation present: {op}"


def test_fraud_router_delegates_to_controller():
    src = _read("routers/fraud_detection.py")
    assert "from controllers.fraud_controller import" in src
    for helper in (
        "fraud_list_events", "fraud_list_blacklist", "fraud_add_blacklist",
        "fraud_remove_blacklist", "fraud_list_rules", "fraud_create_rule",
        "fraud_list_review_queue", "fraud_assign_review", "fraud_resolve_review",
        "fraud_list_ip_reputation", "fraud_list_device_fingerprints",
        "fraud_threat_feed_status",
    ):
        assert helper in src, f"router does not delegate to {helper}"


def test_fraud_writes_moved_to_service_layer():
    """W1 resolution: the actual session writes now live in the service layer."""
    svc = _read("services/fraud_admin_service.py")
    assert "db.add(" in svc and "db.commit(" in svc
    # service is allowed to do so; router is not (verified above).


def test_fraud_service_and_controller_importable():
    svc = importlib.import_module("services.fraud_admin_service")
    ctrl = importlib.import_module("controllers.fraud_controller")
    assert hasattr(svc, "list_fraud_events")
    assert hasattr(ctrl, "fraud_list_events")


# --- middleware CG1 (coi_middleware / country_context) -------------------


def test_middleware_imports_only_allowed_layers():
    for rel in ("middleware/coi_middleware.py", "middleware/country_context.py"):
        src = _read(rel)
        # middleware may import db / utils / dependencies / data (circuit contract).
        # It must NOT import the real 'services' layer package.
        assert "from services." not in src, f"{rel} imports the services layer (CG1)"
        assert "import services." not in src, f"{rel} imports the services layer (CG1)"
        assert "from routers." not in src
        assert "import routers." not in src


def test_coi_middleware_resolves_coi_via_data_service():
    src = _read("middleware/coi_middleware.py")
    # COIService lives under the 'data' facade package -> layer 'data' (allowed).
    assert "from data.services_coi_service import COIService" in src


# --- SEC101 : country_context raw SQL --------------------------------------


def test_country_context_no_raw_sql_interpolation():
    src = _read("middleware/country_context.py")
    assert "SET LOCAL app.country_scope" not in src
    # Replaced with a parameterized set_config() call (no string interpolation).
    assert "set_config('app.current_country_code'" in src
    assert "text(f\"" not in src.replace(" ", "") or "app.current_country_code" not in src


def test_error_handler_has_no_raw_sql_false_positive():
    """The audit reported SEC101 at error_handler.py:148. That is a FALSE POSITIVE
    in the audit's own regex (raw_sql_re = (execute|executemany|text)\\s*\\(\\s*['"]...).

    The substring 'text(' occurs inside 'set_context(' — the Sentry call
    ``scope.set_context("request", {...})`` at line 148 — and a '{' follows, so the
    regex matches it. There is NO actual SQL. This test verifies the file performs
    no real raw SQL: no SQLAlchemy ``text``/``execute`` usage and no SQL keywords.
    """
    src = _read("utils/error_handler.py")
    assert ".execute(" not in src
    assert "from sqlalchemy" not in src
    assert "import text" not in src
    assert not any(kw in src for kw in ("SELECT ", "UPDATE ", "INSERT ", "DELETE "))


# --- DBA05 : RLS sql file + app.current_country_code signal ---------------


def test_dba05_rls_sql_file_exists_with_rls():
    sql = BACKEND / "data" / "pg_rls_policies.sql"
    assert sql.exists()
    txt = sql.read_text(encoding="utf-8")
    assert "ROW LEVEL SECURITY" in txt
    assert "app.current_country_code" in txt
    assert "zozi_rls_check" in txt


def test_middleware_sets_country_code_guc():
    src = _read("middleware/country_context.py")
    assert "app.current_country_code" in src


# --- L1 : RLS enforcer consolidation ---------------------------------------


def test_rls_enforcers_consolidated_to_one():
    hits = _rglob_rls_hits()
    assert hits == [str(BACKEND / "utils" / "rls_interceptor.py")], (
        f"Expected exactly one RLS enforcer (utils/rls_interceptor.py), found: {hits}"
    )


def test_dead_rls_files_removed():
    for rel in (
        "utils/rls_context.py",
        "utils/rls_middleware.py",
        "middleware/rls_dependency.py",
        "dependencies/country_rls.py",
    ):
        assert not (BACKEND / rel).exists(), f"{rel} should have been removed"


def test_country_access_renamed_and_used():
    assert (BACKEND / "utils" / "country_access.py").exists()
    found = any(
        "utils.country_access" in f.read_text(encoding="utf-8", errors="ignore")
        for f in (BACKEND / "routers").rglob("*.py")
    )
    assert found, "no router imports utils.country_access after rename"


# --- boot ------------------------------------------------------------------


def test_import_main_boots():
    importlib.import_module("main")
