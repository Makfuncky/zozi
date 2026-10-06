"""Guard: the FastAPI lifespan must complete startup without raising.

Regression test for the `backup_verify_on_create` missing-settings defect
that crashed the lifespan during `_startup_background_jobs` because
`BackupManager()` read `settings.backup_verify_on_create` at construction
time. A missing setting that crashes startup is a production deployment
blocker, not just a test problem.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from fastapi import FastAPI


class TestLifespanStartupGuard:
    """build_lifespan must complete its startup phase without exception."""

    def test_lifespan_starts_without_missing_setting_error(self):
        from backend.lifespan import build_lifespan

        with patch("lifespan._ensure_tables_exist", return_value=False), \
             patch("lifespan._bootstrap_runtime", return_value={}), \
             patch("lifespan._startup_load_role_permissions"), \
             patch("lifespan._startup_seed_treasury"), \
             patch("lifespan._startup_register_services"), \
             patch("lifespan._startup_register_event_listeners"), \
             patch("lifespan._seed_demo_data"), \
             patch("lifespan._ensure_default_accounts"), \
             patch("lifespan._preload_all_models"), \
             patch("infrastructure.database.rls_interceptor.instrument_rls"):
            cm = build_lifespan()
            app = FastAPI(lifespan=cm)
            from fastapi.testclient import TestClient
            with TestClient(app) as client:
                assert client is not None
