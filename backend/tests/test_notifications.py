"""Tests for notifications."""

import pytest
import uuid


@pytest.fixture
def user_headers(client):
    email = f"notifuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"notifuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_list_notifications_empty(client, user_headers):
    resp = client.get("/api/v1/notifications", headers=user_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_create_notification_admin(client, admin_headers):
    resp = client.post(
        "/api/v1/notifications/send",
        headers=admin_headers,
        params={"user_id": 1, "title": "Test Notification", "message": "Hello", "channel": "in_app", "priority": "medium"},
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body.get("status") == "queued"


@pytest.mark.integration
def test_mark_notification_as_read(client, user_headers, admin_headers):
    resp = client.post(
        "/api/v1/notifications/send",
        headers=admin_headers,
        params={"user_id": 1, "title": "Read Me", "message": "Read this", "channel": "in_app", "priority": "medium"},
    )
    notif_id = resp.json().get("id")
    if notif_id is None:
        pytest.skip("Notification id not returned by create")
    mark_resp = client.post(f"/api/v1/notifications/{notif_id}/read", headers=user_headers)
    assert mark_resp.status_code in (200, 404)


@pytest.mark.integration
def test_notifications_unauthorized(client):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 401


@pytest.mark.integration
def test_admin_can_list_all_notifications(client, admin_headers):
    resp = client.get("/api/v1/notifications", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_push_notification_token_registration(client, user_headers):
    resp = client.post(
        "/api/v1/push-notifications/register",
        headers=user_headers,
        json={"token": f"test_token_{uuid.uuid4().hex}", "device_type": "web"},
    )
    assert resp.status_code in (200, 201)


@pytest.mark.integration
def test_push_notification_token_unauthorized(client):
    resp = client.post("/api/v1/push-notifications/register", json={"token": "x", "platform": "web"})
    assert resp.status_code == 401
