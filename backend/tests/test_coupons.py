"""Tests for coupon system."""

import pytest
import uuid
from datetime import datetime, timezone


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_list_coupons_admin(client, admin_headers):
    resp = client.get("/api/v1/coupons", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_create_coupon_admin(client, admin_headers):
    resp = client.post(
        "/api/v1/coupons",
        headers=admin_headers,
        json={
            "code": f"TEST{uuid.uuid4().hex[:6].upper()}",
            "discount_type": "percentage",
            "discount_value": 10,
            "min_order_amount": 20.0,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).isoformat(),
            "usage_limit": 100,
            "is_active": True,
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert "code" in body
    assert body["discount_value"] == 10


@pytest.mark.integration
def test_validate_valid_coupon(client):
    resp = client.get("/api/v1/coupons/validate", params={"code": "WELCOME10", "order_amount": 50.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("valid") is True


@pytest.mark.integration
def test_validate_invalid_coupon(client):
    resp = client.get("/api/v1/coupons/validate", params={"code": "INVALIDCODE", "order_amount": 50.0})
    assert resp.status_code in (200, 404)
    body = resp.json()
    assert body.get("valid") is False


@pytest.mark.integration
def test_validate_coupon_below_min_order(client):
    resp = client.get("/api/v1/coupons/validate", params={"code": "WELCOME10", "order_amount": 5.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("valid") is False


@pytest.mark.integration
def test_validate_coupon_expired(client, admin_headers):
    code = f"EXP{uuid.uuid4().hex[:6].upper()}"
    past = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1).isoformat()
    future = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1).isoformat()
    client.post(
        "/api/v1/coupons",
        headers=admin_headers,
        json={
            "code": code,
            "discount_type": "fixed",
            "discount_value": 5,
            "min_order_amount": 0,
            "valid_from": past,
            "valid_until": future,
            "is_active": True,
        },
    )
    resp = client.get("/api/v1/coupons/validate", params={"code": code, "order_amount": 50.0})
    assert resp.status_code == 200
    assert resp.json().get("valid") is False


@pytest.mark.integration
def test_coupon_unauthorized(client):
    resp = client.get("/api/v1/coupons")
    assert resp.status_code == 401


@pytest.mark.integration
def test_coupon_create_unauthorized(client):
    resp = client.post("/api/v1/coupons", json={"code": "UNAUTH", "discount_value": 10})
    assert resp.status_code == 401
