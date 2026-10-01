"""Tests for admin endpoints."""
from __future__ import annotations

import pytest


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def user_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "customer@zozi.com", "password": "customer123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_admin_users_list(client, admin_headers):
    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict) or isinstance(body, list)


@pytest.mark.integration
def test_admin_products_list(client, admin_headers):
    resp = client.get("/api/v1/products", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict) or isinstance(body, list)


@pytest.mark.integration
def test_admin_orders_list(client, admin_headers):
    resp = client.get("/api/v1/orders", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict) or isinstance(body, list)


@pytest.mark.integration
def test_admin_unauthorized(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401


@pytest.mark.integration
def test_admin_customer_access_forbidden(client, user_headers):
    resp = client.get("/api/v1/users", headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.integration
def test_admin_treasury_metrics(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/metrics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_credits" in body or "net_balance" in body


@pytest.mark.integration
def test_admin_treasury_ledger(client, admin_headers):
    resp = client.get(
        "/api/v1/admin/treasury/ledger",
        headers=admin_headers,
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "limit": 10},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_admin_treasury_payments_transactions(client, admin_headers):
    resp = client.get(
        "/api/v1/admin/treasury/payments/transactions",
        headers=admin_headers,
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_admin_cash_position(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/cash-position", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_admin_cash_flow_forecast(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/forecasts", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_admin_treasury_unauthorized(client):
    resp = client.get("/api/v1/admin/treasury/metrics")
    assert resp.status_code == 401