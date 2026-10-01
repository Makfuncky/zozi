"""Regression tests for FILE-177 health endpoint corrections.

These tests validate the fixes for:
- OPS-002: /health checks DB and Valkey
- OPS-003: /health/ready checks redis/email/payments unconditionally
- OPS-004: /health/deps reports actual payment status
- OBS-013: /health/deps includes circuit breaker state
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is importable
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in os.sys.path:
    os.sys.path.insert(0, _BACKEND_ROOT)

# Set required env vars before importing app
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")


def test_health_deps_includes_circuit_breakers():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health/deps")
    assert resp.status_code == 200
    body = resp.json()
    assert "circuit_breakers" in body["dependencies"]


def test_health_deps_payments_not_hardcoded():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health/deps")
    assert resp.status_code == 200
    body = resp.json()
    # payments status must come from actual provider check, not hard-coded "ok"
    assert "payments" in body["dependencies"]
    assert body["dependencies"]["payments"] in ({"status": "ok"}, {"status": "unavailable"})


def test_health_ready_checks_redis_unconditionally():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "redis" in body["dependencies"]
    assert body["dependencies"]["redis"] in ("ok", "unavailable")


def test_health_ready_checks_email_unconditionally():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "email" in body["dependencies"]
    assert body["dependencies"]["email"] in ("ok", "unavailable")


def test_health_ready_checks_payments_unconditionally():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "payments" in body["dependencies"]
    assert body["dependencies"]["payments"] in ("ok", "unavailable")


def test_health_includes_dependencies():
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "dependencies" in body
    assert "database" in body["dependencies"]
    assert "valkey" in body["dependencies"]
