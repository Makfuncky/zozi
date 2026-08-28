"""Law 5 gate: country is the orthogonal scope axis.

Verifies:
  1. RLS session context is managed by the country domain.
  2. country_staff_assignments table exists and tracks staff-to-country mapping.
  3. Country-scoped models include country_code.
"""
from __future__ import annotations

import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_COUNTRY_DIR = _DOMAINS_DIR / "country"


class TestRLSSessionContext:
    """Row-level security session context for country scoping."""

    def test_country_domain_exists(self):
        assert _COUNTRY_DIR.exists(), "domains/country/ must exist"

    def test_country_rls_module_exists(self):
        rls_path = _COUNTRY_DIR / "utils" / "country_rls.py"
        assert rls_path.exists(), "country/utils/country_rls.py must exist for RLS context"

    def test_rls_module_has_normalize_function(self):
        rls_path = _COUNTRY_DIR / "utils" / "country_rls.py"
        source = rls_path.read_text(encoding="utf-8")
        assert "normalize_country_code" in source

    def test_rls_module_has_scope_function(self):
        rls_path = _COUNTRY_DIR / "utils" / "country_rls.py"
        source = rls_path.read_text(encoding="utf-8")
        assert "get_country_scope_from_db" in source or "get_current_country_scope" in source

    def test_rls_interceptor_exists(self):
        rls_path = _BACKEND_ROOT / "infrastructure" / "database" / "rls_interceptor.py"
        assert rls_path.exists(), "infrastructure/database/rls_interceptor.py must exist"

    def test_rls_interceptor_has_set_context(self):
        rls_path = _BACKEND_ROOT / "infrastructure" / "database" / "rls_interceptor.py"
        source = rls_path.read_text(encoding="utf-8")
        assert "set_rls_context" in source

    def test_rls_interceptor_has_clear_context(self):
        rls_path = _BACKEND_ROOT / "infrastructure" / "database" / "rls_interceptor.py"
        source = rls_path.read_text(encoding="utf-8")
        assert "clear_rls_context" in source

    def test_normalize_country_code_uppercases(self):
        from domains.country.utils.country_rls import normalize_country_code
        assert normalize_country_code("ae") == "AE"
        assert normalize_country_code("us") == "US"

    def test_normalize_country_code_strips_whitespace(self):
        from domains.country.utils.country_rls import normalize_country_code
        assert normalize_country_code("  AE  ") == "AE"

    def test_normalize_country_code_empty(self):
        from domains.country.utils.country_rls import normalize_country_code
        assert normalize_country_code("") == ""


class TestCountryStaffAssignments:
    """country_staff_assignments tracks staff-to-country mapping."""

    def test_country_enhancements_model_exists(self):
        model_path = _COUNTRY_DIR / "models" / "country_enhancements.py"
        assert model_path.exists(), "country/models/country_enhancements.py must exist"

    def test_staff_assignment_model_defined(self):
        model_path = _COUNTRY_DIR / "models" / "country_enhancements.py"
        source = model_path.read_text(encoding="utf-8")
        assert "CountryStaffAssignment" in source

    def test_staff_assignment_has_country_code(self):
        model_path = _COUNTRY_DIR / "models" / "country_enhancements.py"
        source = model_path.read_text(encoding="utf-8")
        assert "country_code" in source
        assert "user_id" in source

    def test_staff_assignment_has_is_active(self):
        model_path = _COUNTRY_DIR / "models" / "country_enhancements.py"
        source = model_path.read_text(encoding="utf-8")
        assert "is_active" in source

    def test_staff_assignment_table_name(self):
        model_path = _COUNTRY_DIR / "models" / "country_enhancements.py"
        source = model_path.read_text(encoding="utf-8")
        assert "country_staff_assignments" in source

    def test_staff_write_service_exists(self):
        service_path = _COUNTRY_DIR / "services" / "staff" / "country_staff_write_service.py"
        assert service_path.exists(), "country staff write service must exist"

    def test_staff_write_service_has_list_function(self):
        service_path = _COUNTRY_DIR / "services" / "staff" / "country_staff_write_service.py"
        source = service_path.read_text(encoding="utf-8")
        assert "list_country_staff" in source


class TestCountryScopedModels:
    """Country-scoped models must include country_code."""

    def test_country_config_has_country_code(self):
        model_path = _COUNTRY_DIR / "models" / "countries.py"
        if not model_path.exists():
            pytest.skip("countries.py does not exist")
        source = model_path.read_text(encoding="utf-8")
        assert "country_code" in source or "code" in source

    def test_country_configs_table_in_db(self, db_session):
        from sqlalchemy import text
        result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%country_config%'"))
        tables = [row[0] for row in result.fetchall()]
        assert len(tables) > 0, "country_configs table must exist in the database"

    def test_country_staff_assignments_table_in_db(self, db_session):
        from sqlalchemy import text
        result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%country_staff_assignment%'"))
        tables = [row[0] for row in result.fetchall()]
        assert len(tables) > 0, "country_staff_assignments table must exist in the database"
