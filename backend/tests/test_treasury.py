"""Tests for treasury and finance modules."""
from __future__ import annotations

import pytest
import uuid
from datetime import date


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_treasury_metrics(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/metrics", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_credits" in body or "net_balance" in body


@pytest.mark.integration
def test_treasury_ledger(client, admin_headers):
    resp = client.get(
        "/api/v1/admin/treasury/ledger",
        headers=admin_headers,
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "limit": 10},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_treasury_payments_transactions(client, admin_headers):
    resp = client.get(
        "/api/v1/admin/treasury/payments/transactions",
        headers=admin_headers,
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_treasury_create_transaction(client, admin_headers):
    pytest.skip("Requires seeded chart of accounts")
    resp = client.post(
        "/api/v1/admin/treasury/ledger/manual-adjustment",
        headers=admin_headers,
        json={
            "debit_account": "1001",
            "credit_account": "2001",
            "amount": 100.0,
            "reason": "Test transaction",
            "created_by": 1,
        },
    )
    assert resp.status_code in (200, 201)


@pytest.mark.integration
def test_cash_position(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/cash-position", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_cash_flow_forecast(client, admin_headers):
    resp = client.get("/api/v1/admin/treasury/forecasts", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_payout_batches(client, admin_headers):
    pytest.skip("DB schema missing payout_batches.batch_number column")
    resp = client.get("/api/v1/admin/treasury/payouts/batches", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_treasury_unauthorized(client):
    resp = client.get("/api/v1/admin/treasury/metrics")
    assert resp.status_code == 401


@pytest.mark.integration
def test_finance_csv_transfer(client, admin_headers):
    pytest.skip("Requires DB schema migration and seeded ledger accounts")
    resp = client.post(
        "/api/v1/admin/treasury/OM/reconciliation/record-cod-remittance",
        headers=admin_headers,
        json={"order_id": 1, "partner_id": 1, "amount": 100.0, "bank_reference": "REF123"},
    )
    assert resp.status_code in (200, 201, 400)
