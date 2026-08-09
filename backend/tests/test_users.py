"""Tests for user profile and address management."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def user_headers(client):
    email = f"user_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_get_profile(client, user_headers):
    resp = client.get("/api/v1/users/me", headers=user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "email" in body
    assert "username" in body


@pytest.mark.integration
def test_update_profile(client, user_headers):
    resp = client.put(
        "/api/v1/users/me",
        headers=user_headers,
        json={"full_name": "Updated Name", "phone": "+96812345678"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Updated Name"
    assert body["phone"] == "+96812345678"


@pytest.mark.integration
def test_update_profile_unauthorized(client):
    resp = client.put("/api/v1/users/me", json={"full_name": "X"})
    assert resp.status_code == 401


@pytest.mark.integration
def test_list_users_as_admin(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_list_users_as_customer_forbidden(client, user_headers):
    resp = client.get("/users", headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.integration
def test_get_user_by_id(client, user_headers):
    me = client.get("/api/v1/users/me", headers=user_headers).json()
    user_id = me["id"]
    resp = client.get(f"/api/v1/users/{user_id}", headers=user_headers)
    assert resp.status_code in (200, 403)


@pytest.mark.integration
def test_get_user_not_found(client, user_headers):
    resp = client.get("/api/v1/users/999999", headers=user_headers)
    assert resp.status_code in (404, 403)


# ── Addresses ─────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_list_addresses_empty(client, user_headers):
    resp = client.get("/api/v1/addresses", headers=user_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_create_address(client, user_headers):
    resp = client.post(
        "/api/v1/addresses",
        headers=user_headers,
        json={
            "label": "Home",
            "street": "123 Test St",
            "city": "Muscat",
            "country": "OM",
            "postal_code": "123",
            "is_default": True,
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["label"] == "Home"
    assert body["city"] == "Muscat"


@pytest.mark.integration
def test_update_address(client, user_headers):
    create_resp = client.post(
        "/api/v1/addresses",
        headers=user_headers,
        json={
            "label": "Work",
            "street": "456 Work Ave",
            "city": "Dubai",
            "country": "AE",
            "postal_code": "00000",
        },
    )
    addr_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/v1/addresses/{addr_id}",
        headers=user_headers,
        json={"label": "Home Office", "city": "Abu Dhabi"},
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "Home Office"


@pytest.mark.integration
def test_delete_address(client, user_headers):
    create_resp = client.post(
        "/api/v1/addresses",
        headers=user_headers,
        json={
            "label": "Temp",
            "street": "789 Temp St",
            "city": "Riyadh",
            "country": "SA",
            "postal_code": "00000",
        },
    )
    addr_id = create_resp.json()["id"]
    resp = client.delete(f"/api/v1/addresses/{addr_id}", headers=user_headers)
    assert resp.status_code in (200, 405)


@pytest.mark.integration
def test_set_default_address(client, user_headers):
    create_resp = client.post(
        "/api/v1/addresses",
        headers=user_headers,
        json={
            "label": "Default Home",
            "street": "1 Main St",
            "city": "Muscat",
            "country": "OM",
            "postal_code": "111",
            "is_default": True,
        },
    )
    addr_id = create_resp.json()["id"]
    resp = client.post(f"/api/v1/addresses/{addr_id}/set-default", headers=user_headers)
    assert resp.status_code == 200


@pytest.mark.integration
def test_address_unauthorized(client):
    resp = client.get("/api/v1/addresses")
    assert resp.status_code == 401
