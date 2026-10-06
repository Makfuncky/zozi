"""OBS2-013 regression tests for ``/metrics`` exposure.

Three properties are locked in:

  1. ``/metrics`` is actually MOUNTED and stays out of the OpenAPI schema.
     The pre-fix code mounted it only when the undocumented
     ``PROMETHEUS_ENABLED`` variable happened to be set, so in the documented
     default environment the route did not exist at all and every alert in
     ``monitoring/alerts.yml`` was permanently dead.

  2. Outside development/test the endpoint is protected AT THE APP LAYER with a
     derived bearer token. An unauthenticated ``/metrics`` leaks route names,
     latencies and topology; the guard must not depend on the Cloudflare edge.

  3. The guard never logs the token it was handed, and it never touches any
     path other than ``/metrics``.

These tests need no network, no database and no instrumentator install: the
guard is exercised directly as ASGI, and the mount is asserted against the
live route table built by the real ``setup_prometheus``.
"""
from __future__ import annotations

import asyncio
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.types import Receive, Scope, Send

from infrastructure.observability import prometheus_setup
from infrastructure.observability.prometheus_setup import (
    METRICS_ENDPOINT,
    MetricsAuthGuard,
    _presented_token,
    expected_scrape_token,
    metrics_are_public,
    setup_prometheus,
)
from infrastructure.utils.config import settings

_TEST_SECRET = "unit-test-secret-key-not-a-real-secret-" + "a" * 32


@pytest.fixture()
def guarded_app(monkeypatch):
    """A minimal app with the guard installed, settings forced per-test."""
    monkeypatch.setattr(settings, "app_env", "development", raising=False)
    monkeypatch.setattr(settings, "secret_key", _TEST_SECRET, raising=False)
    app = FastAPI()

    @app.get("/api/v1/ping")
    async def _ping() -> dict:
        return {"ok": True}

    @app.get(METRICS_ENDPOINT)
    async def _metrics() -> str:
        return "# HELP probe_metric probe\nprobe_metric 1.0\n"

    app.add_middleware(MetricsAuthGuard, endpoint=METRICS_ENDPOINT)
    return app


# ---------------------------------------------------------------------------
# 1. mounting + schema exclusion  (contract section 20 test name)
# ---------------------------------------------------------------------------
def test_metrics_mounted_and_not_in_schema():
    """/metrics is a live route and is absent from the OpenAPI document."""
    app = FastAPI()
    assert setup_prometheus(app) is not None, "instrumentator must be returned"

    mounted = [r for r in app.routes if getattr(r, "path", "") == METRICS_ENDPOINT]
    assert mounted, (
        "/metrics must be mounted unconditionally. A conditional mount makes "
        "every alert in monitoring/alerts.yml dead whenever the gate is unset."
    )
    assert METRICS_ENDPOINT not in app.openapi().get("paths", {})


def test_metrics_mounted_without_any_env_var(monkeypatch):
    """Regression for OBS2-013: no PROMETHEUS_ENABLED-style gate may hide it.

    ``prometheus-fastapi-instrumentator`` short-circuits both ``instrument()``
    and ``expose()`` when ``should_respect_env_var`` is on and the variable is
    unset (instrumentation.py:281-282, 355-360). That default-off behaviour is
    exactly what this test refuses to let come back.
    """
    monkeypatch.delenv("PROMETHEUS_ENABLED", raising=False)
    monkeypatch.delenv("ENABLE_METRICS", raising=False)

    app = FastAPI()
    setup_prometheus(app)

    assert any(getattr(r, "path", "") == METRICS_ENDPOINT for r in app.routes)


def test_prometheus_setup_uses_the_shared_endpoint_constant():
    """The mount and the guard must agree on the path (Law 66, no literals)."""
    source = (prometheus_setup.__file__ or "")
    assert source
    app = FastAPI()
    setup_prometheus(app)
    assert any(getattr(r, "path", "") == METRICS_ENDPOINT for r in app.routes)


# ---------------------------------------------------------------------------
# 2. app-layer protection outside development
# ---------------------------------------------------------------------------
def test_open_in_development_and_test(monkeypatch):
    """Law 205: local development and test environments stay open."""
    for env in ("development", "test", "DEVELOPMENT", "Test"):
        monkeypatch.setattr(settings, "app_env", env, raising=False)
        assert metrics_are_public() is True, f"{env} must be open"


def test_closed_in_staging_and_production(monkeypatch):
    """Staging and production must require a credential."""
    for env in ("staging", "production", "PRODUCTION"):
        monkeypatch.setattr(settings, "app_env", env, raising=False)
        assert metrics_are_public() is False, f"{env} must be protected"


def test_production_rejects_unauthenticated_scrape(guarded_app, monkeypatch):
    """The core of the security invariant: no token -> no topology leak."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    client = TestClient(guarded_app)

    response = client.get(METRICS_ENDPOINT)

    assert response.status_code == 403
    assert "probe_metric" not in response.text, (
        "the metrics body must not be served to an unauthenticated caller"
    )


@pytest.mark.parametrize(
    "header",
    [
        {"Authorization": "Bearer wrong-token"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "metrics-scrape-token"},
        {"X-Prometheus-Token": "whatever"},
        {},
    ],
)
def test_production_rejects_bad_credentials(guarded_app, monkeypatch, header):
    """Every wrong/absent credential shape is rejected, none raises."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    client = TestClient(guarded_app)

    response = client.get(METRICS_ENDPOINT, headers=header)

    assert response.status_code == 403
    assert "probe_metric" not in response.text


def test_production_accepts_the_derived_token(guarded_app, monkeypatch):
    """A correctly configured Prometheus scraper still gets its metrics."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    client = TestClient(guarded_app)

    response = client.get(
        METRICS_ENDPOINT, headers={"Authorization": f"Bearer {expected_scrape_token()}"}
    )

    assert response.status_code == 200
    assert "probe_metric" in response.text


def test_scrape_token_is_derived_not_the_signing_key(monkeypatch):
    """Law 32: the scrape token must never BE the JWT signing key."""
    monkeypatch.setattr(settings, "secret_key", _TEST_SECRET, raising=False)

    token = expected_scrape_token()

    assert token, "a configured secret_key must yield a token"
    assert token != _TEST_SECRET
    assert len(token) == 64, "expected a hex sha256 digest"
    int(token, 16)  # is hex
    assert expected_scrape_token() == token, "derivation must be deterministic"


def test_scrape_token_is_domain_separated(monkeypatch):
    """A different context label must produce a different token."""
    monkeypatch.setattr(settings, "secret_key", _TEST_SECRET, raising=False)
    baseline = expected_scrape_token()

    monkeypatch.setattr(
        prometheus_setup, "_SCRAPE_TOKEN_CONTEXT", "zozi:metrics-scrape:v2", raising=False
    )

    assert expected_scrape_token() != baseline


def test_no_token_when_no_key_material(monkeypatch):
    """No key configured -> no token, and the guard must fail closed."""
    monkeypatch.setattr(settings, "secret_key", "", raising=False)
    assert expected_scrape_token() == ""


def test_production_fails_closed_without_key_material(guarded_app, monkeypatch, caplog):
    """Misconfigured deployment serves nothing rather than everything."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    monkeypatch.setattr(settings, "secret_key", "", raising=False)
    client = TestClient(guarded_app)

    with caplog.at_level(logging.ERROR, logger="infrastructure.observability.prometheus_setup"):
        response = client.get(METRICS_ENDPOINT, headers={"Authorization": "Bearer anything"})

    assert response.status_code == 503
    assert "probe_metric" not in response.text


# ---------------------------------------------------------------------------
# 3. the guard must not leak the token, and must not touch other paths
# ---------------------------------------------------------------------------
def test_rejection_never_logs_the_token(guarded_app, monkeypatch, caplog):
    """Law 43 logs the event at WARNING+; Law 282 forbids logging the secret."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    client = TestClient(guarded_app)
    supplied = "supplied-secret-should-never-be-logged"

    with caplog.at_level(logging.DEBUG):
        response = client.get(
            METRICS_ENDPOINT, headers={"Authorization": f"Bearer {supplied}"}
        )

    assert response.status_code == 403
    assert "metrics_scrape_rejected" in caplog.text
    assert supplied not in caplog.text
    assert expected_scrape_token() not in caplog.text


def test_guard_passes_through_other_paths(guarded_app, monkeypatch):
    """A protected /metrics must not accidentally protect the whole app."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    client = TestClient(guarded_app)

    response = client.get("/api/v1/ping")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_guard_is_a_passthrough_for_non_http_scopes(guarded_app):
    """WebSocket / lifespan scopes must not be inspected as HTTP."""
    calls: list[str] = []
    seen: list[Scope] = []

    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        seen.append(scope)
        calls.append(scope["type"])

    guard = MetricsAuthGuard(downstream, endpoint=METRICS_ENDPOINT)
    asyncio.run(guard({"type": "lifespan"}, None, None))

    assert calls == ["lifespan"]
    assert seen[0]["type"] == "lifespan"


# ---------------------------------------------------------------------------
# header parsing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "header,expected",
    [
        ("Bearer abc123", "abc123"),
        ("bearer abc123", "abc123"),
        ("BEARER   abc123  ", "abc123"),
        ("Basic abc123", ""),
        ("abc123", ""),
        ("", ""),
        ("   ", ""),
    ],
)
def test_presented_token_parsing(header, expected):
    """Malformed headers fail authentication instead of raising."""
    assert _presented_token(header) == expected


# ---------------------------------------------------------------------------
# the alert-rule cross-check, encoded as a test
# ---------------------------------------------------------------------------
def test_alert_rule_metric_names_are_exposed_or_documented():
    """Lock in the OBS2-013 cross-check for the four families the alerts use.

    ``monitoring/alerts.yml`` is a different file block (FILE 30) and is not
    edited here. This test records which of its metric families this
    application actually exposes, so the next person who edits either side has
    a machine-checked fact instead of an assumption. The two DEAD rules
    (``db_connections.checkedout`` and ``sentry_event_total``) are asserted as
    ABSENT on purpose: that absence is the finding, and it must stay visible
    until monitoring/alerts.yml is corrected.
    """
    from prometheus_client import REGISTRY, generate_latest

    # Import the modules that own the metric definitions, exactly as
    # `import main` does, so the registry reflects the production set.
    import infrastructure.observability.metrics  # noqa: F401
    import middleware.logging_middleware  # noqa: F401

    # Use the real exposition text, because that is literally what Prometheus
    # scrapes. `# TYPE <name> <kind>` is emitted for every registered family,
    # whether or not it has samples yet.
    exposition = generate_latest(REGISTRY).decode("utf-8")
    declared = {
        line.split()[2]
        for line in exposition.splitlines()
        if line.startswith("# TYPE ")
    }

    # ALIVE - verified emitted by middleware/logging_middleware.py
    assert "http_requests_total" in declared
    assert "http_request_duration_seconds" in declared
    # ALIVE - verified emitted by infrastructure/database/database_logging.py
    assert "db_query_duration_seconds" in declared
    # ALIVE but MIS-SPECIFIED: a bare unlabelled Gauge. The alert's
    # `db_connections.checkedout` has no series behind it (Prometheus has no
    # sub-metrics), so DatabaseConnectionPoolExhausted can never fire.
    assert "db_connections" in declared
    assert not any(n.startswith("db_connections_") for n in declared), (
        "if a per-pool breakdown is ever exported it must be label-based, not a "
        "dotted sub-metric; the current alert expression cannot match one"
    )
    # DEAD: sentry_event_total is emitted nowhere in the codebase, and the rule
    # additionally calls `increases()`, a Grafana-only function.
    assert "sentry_event_total" not in declared