"""Tests for Sentry SDK initialisation via ErrorHandler.

The integration is opt-in: it must remain inert when ``SENTRY_DSN`` is unset
or the package is not installed.  These tests assert that contract without
ever contacting a Sentry server.
"""
from __future__ import annotations

import os
import sys
from unittest import mock

import pytest


def test_sentry_uninitialized_without_dsn(monkeypatch) -> None:
    """No SENTRY_DSN -> no init call, no exception."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    from infrastructure.observability.error_handler import create_error_handler
    handler = create_error_handler(sentry_dsn=None, environment="test")
    assert handler.sentry_initialized is False


def test_sentry_uninitialized_when_dsn_empty_string(monkeypatch) -> None:
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    from infrastructure.observability.error_handler import create_error_handler
    handler = create_error_handler(sentry_dsn="", environment="test")
    assert handler.sentry_initialized is False


def test_sentry_initialized_with_dsn(monkeypatch) -> None:
    """When SENTRY_DSN is set we expect a call to sentry_sdk.init with
    FastApi and Sqlalchemy integrations."""
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")
    sentry_sdk = mock.MagicMock()
    integrations_mock = mock.MagicMock()
    integrations_mock.__path__ = ["fake/path"]
    with mock.patch.dict(sys.modules, {"sentry_sdk": sentry_sdk}):
        sys.modules["sentry_sdk.integrations"] = integrations_mock
        sys.modules["sentry_sdk.integrations.fastapi"] = mock.MagicMock(FastApiIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.sqlalchemy"] = mock.MagicMock(SqlalchemyIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.redis"] = mock.MagicMock(RedisIntegration=mock.MagicMock())
        from infrastructure.observability.error_handler import create_error_handler
        handler = create_error_handler(
            sentry_dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
            environment="test",
        )
    assert handler.sentry_initialized is True
    sentry_sdk.init.assert_called_once()
    call_kwargs = sentry_sdk.init.call_args.kwargs
    assert call_kwargs["dsn"] == "https://examplePublicKey@o0.ingest.sentry.io/0"
    assert call_kwargs["traces_sample_rate"] == 0.05
    assert call_kwargs["environment"] == "test"


def test_sentry_init_failure_does_not_crash(monkeypatch) -> None:
    """If sentry_sdk.init raises, ErrorHandler init must not raise."""
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    sentry_sdk = mock.MagicMock()
    sentry_sdk.init.side_effect = RuntimeError("sentry down")
    integrations_mock = mock.MagicMock()
    integrations_mock.__path__ = ["fake/path"]
    with mock.patch.dict(sys.modules, {"sentry_sdk": sentry_sdk}):
        sys.modules["sentry_sdk.integrations"] = integrations_mock
        sys.modules["sentry_sdk.integrations.fastapi"] = mock.MagicMock(FastApiIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.sqlalchemy"] = mock.MagicMock(SqlalchemyIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.redis"] = mock.MagicMock(RedisIntegration=mock.MagicMock())
        from infrastructure.observability.error_handler import create_error_handler
        try:
            handler = create_error_handler(
                sentry_dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
                environment="test",
            )
        except RuntimeError:
            pytest.fail("ErrorHandler init raised on sentry_sdk.init failure")
