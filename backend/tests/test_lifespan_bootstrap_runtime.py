"""Regression test for FILE-176: _bootstrap_runtime must not auto-migrate on boot.

Law 217: Web replicas NEVER auto-migrate on boot. Migrations are run exclusively
by the CI/CD deploy pipeline before new web replicas are provisioned.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.lifespan import _bootstrap_runtime


class TestBootstrapRuntimeNoAutoMigration:
    """_bootstrap_runtime must never call upgrade_database_to_head on boot."""

    def test_returns_false_for_fresh_schema(self):
        result = _bootstrap_runtime(tables_just_created=True)
        assert result["auto_migration_applied"] is False
        assert result["migration_reason"] == "skipped_fresh_schema"

    def test_returns_false_for_existing_schema(self):
        result = _bootstrap_runtime(tables_just_created=False)
        assert result["auto_migration_applied"] is False
        assert result["migration_reason"] == "skipped_deploy_pipeline"

    def test_does_not_import_or_call_upgrade_database_to_head(self):
        """Verify the source code of _bootstrap_runtime contains no alembic call."""
        import inspect
        src = inspect.getsource(_bootstrap_runtime)
        assert "upgrade_database_to_head" not in src
        assert "alembic" not in src

    def test_production_env_does_not_trigger_migration(self):
        """Even with production app_env, no migration is attempted."""
        with patch(
            "infrastructure.utils.config.settings",
            app_env="production",
        ):
            result = _bootstrap_runtime(tables_just_created=False)
        assert result["auto_migration_applied"] is False
        assert result["migration_reason"] == "skipped_deploy_pipeline"
