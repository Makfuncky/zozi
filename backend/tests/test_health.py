"""Tests for health endpoints."""
import pytest


@pytest.mark.integration
def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "version" in body


@pytest.mark.integration
def test_health_deps(client):
    resp = client.get("/health/deps")
    assert resp.status_code == 200
    body = resp.json()
    assert "runtime_profile" in body
    assert "dependencies" in body
    deps = body["dependencies"]
    assert "redis" in deps
    assert "email" in deps
    assert "payments" in deps


@pytest.mark.integration
def test_health_ready(client):
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "ready" in body
    assert "database" in body
    assert "dependencies" in body
    assert "blocking_dependencies" in body


@pytest.mark.integration
def test_health_ready_returns_valid_json(client):
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "ready" in body
    assert "database" in body
    assert "dependencies" in body
    assert "blocking_dependencies" in body


@pytest.mark.integration
def test_health_ready_reports_redis_status(client):
    resp = client.get("/health/ready")
    body = resp.json()
    assert "redis" in body["dependencies"]
    assert body["dependencies"]["redis"] in ("ok", "unavailable")
