"""Workflow tests for registration → login flow.

Covers Laws 69-74 (Authentication & Authorization) and 207-214 (Customer Journey):
  - Successful registration
  - Duplicate email registration fails
  - Login with correct credentials
  - Login with wrong password
  - Token refresh
  - Token blacklist after logout
  - /auth/me returns correct user info
"""
from __future__ import annotations

import uuid

import pytest


def _unique_email(prefix: str = "reg") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@zozi.test"


def _unique_username(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestRegistrationLoginFlow:
    """End-to-end tests for the registration → login flow."""

    def test_successful_registration(self, client):
        """A new user can register with valid credentials."""
        email = _unique_email()
        username = _unique_username()
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["user"]["email"] == email
        assert "hashed_password" not in body["user"]
        assert "id" in body["user"]

    def test_duplicate_email_registration_fails(self, client):
        """Registering with an already-registered email returns 400."""
        email = _unique_email("dup")
        username1 = _unique_username("dup1")
        username2 = _unique_username("dup2")

        resp1 = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username1,
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp1.status_code == 201, resp1.text

        resp2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username2,
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp2.status_code == 400
        assert "Email already registered" in resp2.json()["detail"]

    def test_login_with_correct_credentials(self, client):
        """A registered user can log in with correct credentials."""
        email = _unique_email("login")
        password = "SecurePass1!"

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": _unique_username("login"),
                "password": password,
                "role": "customer",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        body = login_resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == email

    def test_login_with_wrong_password(self, client):
        """Login with incorrect password returns 401."""
        email = _unique_email("wrongpwd")
        password = "SecurePass1!"

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": _unique_username("wrongpwd"),
                "password": password,
                "role": "customer",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword1!"},
        )
        assert login_resp.status_code == 401
        assert "Invalid credentials" in login_resp.json()["detail"]

    def test_token_refresh(self, client):
        """A refresh token can be used to obtain a new access token."""
        email = _unique_email("refresh")
        password = "SecurePass1!"

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": _unique_username("refresh"),
                "password": password,
                "role": "customer",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    def test_token_blacklist_after_logout(self, client):
        """After logout, the access token is blacklisted and cannot be reused."""
        email = _unique_email("logout")
        password = "SecurePass1!"

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": _unique_username("logout"),
                "password": password,
                "role": "customer",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        access_token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Logout should succeed
        logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert logout_resp.status_code == 200

        # After logout, /auth/me should reject the blacklisted token
        me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_resp.status_code == 401

    def test_auth_me_returns_correct_user_info(self, client):
        """/auth/me returns the correct user info for an authenticated user."""
        email = _unique_email("me")
        password = "SecurePass1!"
        username = _unique_username("me")

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "role": "customer",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text
        user_id = reg_resp.json()["user"]["id"]

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        access_token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_resp.status_code == 200
        body = me_resp.json()
        assert body["email"] == email
        assert body["id"] == user_id
        assert body["role"] == "customer"
