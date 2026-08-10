"""Regression tests for the consolidated RLS (Row Level Security) module.

Validates the canonical-enforcer consolidation (report advisory L1) and the
SEC101 identifier-injection hardening on the RLS DDL generator.

Scope:
  * `utils.rls_interceptor` is the single canonical RLS engine and now owns a
    pure `normalize_country_code` (no upward import into `services`).
  * `utils.country_rls` is the HTTP facade and must import `normalize_country_code`
    from the canonical `utils` layer, NOT from `services.logistics_partner_pricing`.
  * The duplicate `utils.country_access` and broken `middleware.rls_dependency`
    must no longer exist (deleted during consolidation).
  * `generate_rls_policy_sql` must validate every SQL identifier (SEC101) so an
    unsafe schema/table/column name can never be concatenated into DDL.
"""

import importlib
import os
import sys

import pytest

# Ensure backend/ is importable when the suite is run from the repo root.
_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, os.path.abspath(_BACKEND))

import utils.rls_interceptor as rls  # noqa: E402


def test_country_access_module_deleted():
    """Duplicate near-copy of country_rls must be gone (L1 consolidation)."""
    path = os.path.join(_BACKEND, "utils", "country_access.py")
    assert not os.path.exists(path), "utils/country_access.py should be deleted"


def test_rls_dependency_module_deleted():
    """Broken no-op RLS dependency middleware must be gone (L1 consolidation)."""
    path = os.path.join(_BACKEND, "middleware", "rls_dependency.py")
    assert not os.path.exists(path), "middleware/rls_dependency.py should be deleted"


def test_normalize_country_code_is_canonical_and_pure():
    """Canonical normalize lives in the utils layer and behaves correctly."""
    assert rls.normalize_country_code("UAE") == "AE"
    assert rls.normalize_country_code("Saudi Arabia") == "SA"
    assert rls.normalize_country_code("usa") == "US"
    assert rls.normalize_country_code("uk") == "GB"
    assert rls.normalize_country_code("") == ""
    assert rls.normalize_country_code(None) == ""
    assert rls.normalize_country_code("xyz") == "XY"


def test_country_rls_facade_imports_from_canonical_layer():
    """country_rls must not reach *up* into services for normalize_country_code."""
    src = open(os.path.join(_BACKEND, "utils", "country_rls.py"), encoding="utf-8").read()
    assert "from utils.rls_interceptor import" in src
    assert "normalize_country_code" in src
    assert "from services.logistics_partner_pricing import normalize_country_code" not in src


def test_sec101_rejects_unsafe_identifiers():
    """SEC101: DDL identifier building must reject injection attempts."""
    # Valid identifiers are accepted.
    assert rls._assert_safe_identifier("public") == "public"
    assert rls._assert_safe_identifier("orders_rls_policy") == "orders_rls_policy"

    # Dangerous payloads are rejected.
    for bad in ("public; DROP TABLE x", "a b", "1table", "tbl;--", "tbl\x00"):
        with pytest.raises(ValueError):
            rls._assert_safe_identifier(bad, "schema")


def test_sec101_generate_rls_policy_sql_rejects_unsafe_schema():
    """SEC101: an unsafe schema name must never reach the generated DDL."""
    with pytest.raises(ValueError):
        rls.generate_rls_policy_sql(schema="public; DROP TABLE users;")

    # Safe schema produces SQL without the injection marker.
    sql = rls.generate_rls_policy_sql(schema="public")
    assert "DROP TABLE" not in sql
    assert "CREATE POLICY" in sql


def test_rls_interceptor_is_importable_without_services_cycle():
    """The canonical engine imports cleanly (no upward service dependency)."""
    importlib.reload(rls)
    assert hasattr(rls, "normalize_country_code")
    assert hasattr(rls, "set_rls_context")
    assert hasattr(rls, "generate_rls_policy_sql")
