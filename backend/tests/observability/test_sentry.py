"""Tests for Sentry SDK initialisation.

The integration is opt-in: it must remain inert when ``SENTRY_DSN`` is unset
or the package is not installed.  These tests assert that contract without
ever contacting a Sentry server.

We deliberately do **not** import ``main`` in this test (the main module
triggers a large import chain that includes circular dependencies which
make standalone re-import brittle).  Instead we test the helper in
isolation.
"""
from __future__ import annotations

import importlib
import os
import sys
from unittest import mock


def _init_helper(dotted_path: str = "main"):
    """Call main's Sentry init block by exec'ing the relevant lines.

    The init block in main.py is deliberately idempotent and short, so we
    can safely evaluate it under controlled environment variables.
    """
    import pathlib
    main_path = pathlib.Path(__file__).resolve().parents[2] / "main.py"
    source = main_path.read_text(encoding="utf-8")
    # Slice from the Sentry init block to the end of the database
    # instrument block.  We execute the lines as a small standalone
    # script so we don't have to import the full main module.
    lines = source.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if "_sentry_dsn = os.getenv(\"SENTRY_DSN\")" in ln),
        None,
    )
    assert start is not None, "Could not find Sentry init block in main.py"
    # Find the next blank-line separated block of code; execute up to the
    # "instrument_database_engine(engine)" line so the SQLAlchemy engine
    # instrumentation that uses `engine` is skipped (it would need the
    # full app context).
    end = next(
        (i for i, ln in enumerate(lines[start:], start) if "instrument_database_engine(engine)" in ln),
        None,
    )
    assert end is not None, "Could not find end of Sentry init block"
    # Run the block in a controlled namespace
    namespace = {
        "os": os,
        "logger": mock.MagicMock(),
        "settings": mock.MagicMock(sentry_dsn=None, app_env="test"),
    }
    exec(  # noqa: S102
        "\n".join(lines[start:end]),
        namespace,
    )


def test_sentry_uninitialized_without_dsn(monkeypatch) -> None:
    """No SENTRY_DSN -> no init call, no exception."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    _init_helper()
    # We never import sentry_sdk; absence of exception is the assertion.


def test_sentry_uninitialized_when_dsn_empty_string(monkeypatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "")
    _init_helper()


def test_sentry_initialized_with_dsn(monkeypatch) -> None:
    """When SENTRY_DSN is set we expect a call to sentry_sdk.init with
    FastApi and Sqlalchemy integrations."""
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")
    sentry_sdk = mock.MagicMock()
    with mock.patch.dict(sys.modules, {"sentry_sdk": sentry_sdk}):
        # Stub the integration modules so the import works
        sys.modules["sentry_sdk.integrations"] = mock.MagicMock()
        sys.modules["sentry_sdk.integrations.fastapi"] = mock.MagicMock(FastApiIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.sqlalchemy"] = mock.MagicMock(SqlalchemyIntegration=mock.MagicMock())
        _init_helper()
    sentry_sdk.init.assert_called_once()
    call_kwargs = sentry_sdk.init.call_args.kwargs
    assert call_kwargs["dsn"] == "https://examplePublicKey@o0.ingest.sentry.io/0"
    assert call_kwargs["traces_sample_rate"] == 0.05
    assert call_kwargs["environment"] == "test"


def test_sentry_init_failure_does_not_crash(monkeypatch) -> None:
    """If sentry_sdk.init raises, main must still import successfully."""
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    sentry_sdk = mock.MagicMock()
    sentry_sdk.init.side_effect = RuntimeError("sentry down")
    with mock.patch.dict(sys.modules, {"sentry_sdk": sentry_sdk}):
        sys.modules["sentry_sdk.integrations"] = mock.MagicMock()
        sys.modules["sentry_sdk.integrations.fastapi"] = mock.MagicMock(FastApiIntegration=mock.MagicMock())
        sys.modules["sentry_sdk.integrations.sqlalchemy"] = mock.MagicMock(SqlalchemyIntegration=mock.MagicMock())
        _init_helper()  # must not raise
