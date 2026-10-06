"""Paired regression test for E-06: rbac/models/ must be scanned by conftest.

The ``permissions``, ``permission_categories``, ``role_permission_assignments``,
``user_permission_overrides`` and ``permission_audit_log`` tables are declared in
``rbac/models/permission_entities.py``.  The test ``conftest.py`` dynamic model
discovery previously scanned only ``domains/{domain}/models/*.py`` and never
reached ``rbac/models/``, so those tables were absent from the SQLite test
database, causing ``no such table: main.permissions`` failures across the RBAC
and security suites.

These tests will FAIL until the conftest discovery is extended to cover
``rbac/models/``, and PASS afterwards.
"""
from __future__ import annotations

import logging

from infrastructure.database.base import Base

# The conftest import phase runs at collection time (before any test fixture).
# By the time these tests execute, ``conftest.py`` has already imported every
# model module and populated Base.metadata.  We simply assert the expected
# tables are registered.
_SECURITY_RBAC_TABLES = {
    "security.permissions",
    "security.permission_categories",
    "security.role_permission_assignments",
    "security.user_permission_overrides",
    "security.permission_audit_log",
}


class TestConftestDiscoversRbacModels:
    """conftest's model discovery must include rbac/models/ (E-06)."""

    def test_permissions_table_in_metadata(self):
        missing = {
            name for name in _SECURITY_RBAC_TABLES
            if name not in Base.metadata.tables
        }
        assert not missing, (
            "conftest model discovery did not register the following RBAC "
            "tables in Base.metadata — rbac/models/ is not being scanned: "
            + ", ".join(sorted(missing))
        )

    def test_rbac_tables_have_security_schema(self):
        """All RBAC permission tables must carry the ``security`` schema."""
        bad = sorted(
            name
            for name in _SECURITY_RBAC_TABLES
            if name in Base.metadata.tables
            and Base.metadata.tables[name].schema != "security"
        )
        assert not bad, (
            "RBAC permission tables with wrong schema: " + ", ".join(bad)
        )


class TestConftestImportErrorsAreLogged:
    """D-SILENT guard: import failures during conftest model discovery must be
    visible, not silently swallowed."""

    def test_conftest_import_logger_defined(self):
        """The conftest discovery logger must be wired so broken imports are
        reported rather than hidden by a bare ``except: pass``."""
        import backend.tests.conftest as _conftest
        assert hasattr(_conftest, "_import_logger"), (
            "conftest.py is missing _import_logger — broken model imports are "
            "being silently swallowed (D-SILENT hazard)"
        )
        assert isinstance(_conftest._import_logger, logging.Logger), (
            "_import_logger must be a logging.Logger instance"
        )
