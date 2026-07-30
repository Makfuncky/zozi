"""Tests for authentication endpoints."""
from __future__ import annotations

import time
import uuid

import pytest


@pytest.fixture
def auth_headers(client):
    """Return authorization headers for a registered customer."""
    email = f"authtest_{uuid.uuid4().hex[:8]}@zozi.test"
    password = "SecurePass1!"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"authtest_{uuid.uuid4().hex[:8]}",
            "password": password,
            "role": "customer",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, email=None, username=None, password="SecurePass1!", role="customer"):
    email = email or f"user_{uuid.uuid4().hex[:8]}@zozi.test"
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password, "role": role},
    )
    assert reg.status_code in (200, 201), f"Registration failed: {reg.text}"
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, f"Login failed: {login.text}"
    return login.json()


# ── Registration ──────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_register_new_user(client):
    email = f"reg_{uuid.uuid4().hex[:8]}@zozi.test"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"reguser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["user"]["email"] == email
    assert "hashed_password" not in body["user"]
    assert "id" in body["user"]


@pytest.mark.integration
def test_register_duplicate_email(client):
    email = f"dup_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": "dupuser1",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    time.sleep(0.5)
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": "dupuser2",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert resp.status_code == 400
    assert "Email already registered" in resp.json()["detail"]


@pytest.mark.integration
def test_register_duplicate_username(client):
    username = f"dupname_{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dup2_{uuid.uuid4().hex[:8]}@zozi.test",
            "username": username,
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    time.sleep(0.5)
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"dup2b_{uuid.uuid4().hex[:8]}@zozi.test",
            "username": username,
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert resp.status_code == 400
    assert "Username already taken" in resp.json()["detail"]


@pytest.mark.integration
def test_register_weak_password(client):
    time.sleep(0.5)
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"weak_{uuid.uuid4().hex[:8]}@zozi.test",
            "username": f"weak_{uuid.uuid4().hex[:8]}",
            "password": "weak",
            "role": "customer",
        },
    )
    assert resp.status_code in (422, 429)


@pytest.mark.integration
def test_register_invalid_email(client):
    time.sleep(0.5)
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "username": f"inv_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert resp.status_code in (422, 429)


# ── Login ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_login_success_with_email(client):
    email = f"login_{uuid.uuid4().hex[:8]}@zozi.test"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"loginuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert reg.status_code in (200, 201), f"Registration failed: {reg.text}"
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == email


@pytest.mark.integration
def test_login_success_with_username(client):
    username = f"loginuser_{uuid.uuid4().hex[:8]}"
    email = f"login_{uuid.uuid4().hex[:8]}@zozi.test"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert reg.status_code in (200, 201), f"Registration failed: {reg.text}"
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": "SecurePass1!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.integration
def test_login_wrong_password(client):
    data = _register_and_login(client)
    email = data["user"]["email"]
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1!"})
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.integration
def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", json={"email": "nobody@zozi.test", "password": "SecurePass1!"})
    assert resp.status_code == 401


@pytest.mark.integration
def test_login_inactive_user(client, db_session):
    from models import User
    from utils.auth import get_password_hash
    user = User(
        email=f"inactive_{uuid.uuid4().hex[:8]}@zozi.test",
        username=f"inactive_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="customer",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": "SecurePass1!"})
    assert resp.status_code == 403
    assert "inactive" in resp.json()["detail"].lower()


@pytest.mark.integration
def test_login_missing_credentials(client):
    resp = client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


# ── Current user ──────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_current_user(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "email" in body
    assert "role" in body


@pytest.mark.integration
def test_get_current_user_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── Token refresh ─────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_refresh_token(client):
    data = _register_and_login(client)
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": data["refresh_token"]},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.integration
def test_refresh_token_invalid(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
    assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_logout(client, auth_headers):
    resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.integration
def test_logout_unauthorized(client):
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


# ── Role-based admin login ────────────────────────────────────────────────────


@pytest.mark.integration
def test_admin_can_login_via_default_account(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "admin"
