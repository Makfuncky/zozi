"""Paired tests for config.py test-mode behaviour.

Covers the three-environment contract:

  * ``test`` — Settings() must instantiate without any env var / .env leakage,
    using only safe deterministic defaults that are useless in production.
  * ``production`` — an empty payload must still raise (Law 83).
  * ``development`` — the module-level ``load_dotenv`` side-effect must fire
    when APP_ENV=development and pytest is not active.

No secret value is hard-coded here. Every literal is a synthetic throwaway
placeholder that exists only inside the test process.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_config_env() -> dict:
    """Return a snapshot of env vars that config.py touches, then clear them."""
    keys = [
        "APP_ENV",
        "SECRET_KEY",
        "DATABASE_URL",
        "DATABASE_URL_DIRECT",
        "FIELD_ENCRYPTION_SALT",
        "FIELD_ENCRYPTION_KEY",
        "AUDIT_CHAIN_KEY",
        "PYTEST_CURRENT_TEST",
    ]
    snapshot = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    return snapshot


def _restore_env(snapshot: dict) -> None:
    for k, v in snapshot.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# Test-mode behaviour
# ---------------------------------------------------------------------------


class TestTestModeInstantiatesWithNoArgs:
    """Law 83 relaxation for test mode: Settings() must not require any env var."""

    def test_settings_instantiates_in_test_mode_without_env(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "test"
            # Ensure a fresh import so module-level side-effects don't matter.
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            else:
                import config  # noqa: F401
            from config import Settings

            settings = Settings()
            assert settings.app_env == "test"
        finally:
            _restore_env(snapshot)

    def test_test_mode_supplies_safe_database_urls(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "test"
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            from config import Settings

            settings = Settings()
            assert settings.database_url == "sqlite:///:memory:"
            assert settings.database_url_direct == "sqlite:///:memory:"
        finally:
            _restore_env(snapshot)

    def test_test_mode_supplies_safe_secrets(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "test"
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            from config import Settings

            settings = Settings()
            assert settings.secret_key.startswith("test-secret-key-for-unit-tests-only-")
            assert len(settings.secret_key) >= 64
            assert settings.field_encryption_salt == "test-salt-for-unit-tests-only"
            assert settings.field_encryption_key.startswith(
                "test-field-encryption-key-for-unit-tests-only-"
            )
            assert len(settings.field_encryption_key) >= 64
            assert settings.audit_chain_key.startswith(
                "test-audit-chain-key-for-unit-tests-only-"
            )
            assert len(settings.audit_chain_key) >= 32
        finally:
            _restore_env(snapshot)

    def test_test_mode_explicit_values_override_defaults(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "test"
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            from config import Settings

            settings = Settings(
                database_url="postgresql://user:pass@localhost/db",
                secret_key="a" * 64,
            )
            assert settings.database_url == "postgresql://user:pass@localhost/db"
            assert settings.database_url_direct == "sqlite:///:memory:"
        finally:
            _restore_env(snapshot)

    def test_test_mode_defaults_are_safe_and_not_production_usable(self):
        """The injected test values must be rejected by the production validator."""
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "test"
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            from config import Settings
            from pydantic import ValidationError

            settings = Settings()
            # Passing the test defaults straight to a production Settings()
            # must fail closed. Exclude app_env to avoid the duplicate-keyword
            # TypeError from model_dump() including the field under its alias.
            payload = settings.model_dump(exclude={"app_env", "env"})
            with pytest.raises(ValidationError):
                Settings(app_env="production", **payload)
        finally:
            _restore_env(snapshot)


# ---------------------------------------------------------------------------
# Production behaviour (Law 83 — missing = immediate failure)
# ---------------------------------------------------------------------------


class TestProductionModeStillRaisesWhenEmpty:
    """Law 83: an empty payload in production must fail."""

    def test_production_with_nothing_raises(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "production"
            if "config" in sys.modules:
                importlib.reload(sys.modules["config"])
            from config import Settings
            from pydantic import ValidationError

            with pytest.raises(ValidationError):
                Settings()
        finally:
            _restore_env(snapshot)


# ---------------------------------------------------------------------------
# Development behaviour (loads .env)
# ---------------------------------------------------------------------------


class TestDevelopmentModeLoadsDotenv:
    """APP_ENV=development (and not inside pytest) must call load_dotenv."""

    def test_development_calls_load_dotenv(self):
        snapshot = _clear_config_env()
        try:
            os.environ["APP_ENV"] = "development"
            # PYTEST_CURRENT_TEST must be absent for the module-level branch.
            os.environ.pop("PYTEST_CURRENT_TEST", None)

            # Patch at the source so a reloaded module still sees the mock.
            with mock.patch("dotenv.load_dotenv") as mock_load:
                if "config" in sys.modules:
                    importlib.reload(sys.modules["config"])
                else:
                    import config  # noqa: F401

            assert mock_load.called, "load_dotenv was not called in development mode"
            call_kwargs = mock_load.call_args[1] if mock_load.call_args[1] else {}
            call_args = mock_load.call_args[0]
            # config.py resolves ROOT as parent.parent of itself, which is the
            # project root (zozi/), not backend/.
            expected_path = Path(__file__).resolve().parents[3] / ".env"
            passed_path = call_args[0] if call_args else call_kwargs.get("dotenv")
            assert passed_path == expected_path, (
                f"load_dotenv called with {passed_path!r}, expected {expected_path!r}"
            )
        finally:
            _restore_env(snapshot)
