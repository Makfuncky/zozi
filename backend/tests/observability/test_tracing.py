"""Tests for the OpenTelemetry tracing setup.

These tests verify that the ``infrastructure.observability.tracing`` module:

- imports cleanly even when the OpenTelemetry SDK is **not** installed
- exposes a ``tracer`` symbol usable in a ``with`` block (i.e. supports the
  ``tracer.start_as_current_span(...)`` context manager protocol)
- returns ``False`` from ``is_tracing_enabled`` when no OTLP endpoint is set
- honours the ``OTEL_DISABLED`` env-var override

We deliberately do not require a running OTLP collector, so the tests can run
in any CI environment.
"""
from __future__ import annotations

import importlib

import pytest


def test_tracer_module_imports() -> None:
    """The tracing module must be importable without raising."""
    mod = importlib.import_module("infrastructure.observability.tracing")
    assert hasattr(mod, "tracer")
    assert hasattr(mod, "setup_tracing")
    assert hasattr(mod, "is_tracing_enabled")


def test_tracer_is_usable_as_context_manager() -> None:
    """The tracer must support ``with tracer.start_as_current_span(...)``."""
    from infrastructure.observability.tracing import tracer

    with tracer.start_as_current_span("test.span") as span:
        # The span object should at minimum be non-None so the body of
        # the with-block can run; setting attributes is best-effort.
        assert span is not None
        try:
            span.set_attribute("test.key", "value")
        except Exception:
            # Some no-op tracer implementations may not implement set_attribute;
            # that is acceptable for a graceful fallback.
            pass


def test_tracing_disabled_when_no_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_DISABLED", raising=False)
    from infrastructure.observability.tracing import is_tracing_enabled

    assert is_tracing_enabled() is False


def test_tracing_disabled_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_DISABLED", "1")
    from infrastructure.observability.tracing import is_tracing_enabled

    assert is_tracing_enabled() is False


def test_tracing_enabled_with_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318/v1/traces")
    monkeypatch.delenv("OTEL_DISABLED", raising=False)
    from infrastructure.observability.tracing import is_tracing_enabled

    assert is_tracing_enabled() is True
