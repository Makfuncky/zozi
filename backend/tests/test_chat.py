"""Tests for chat system."""

import uuid

import pytest


@pytest.fixture
def customer_headers(client):
    email = f"chatuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"chatuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def direct_chat_id(client):
    resp = client.post(
        "/api/v1/chat/direct",
        json={"participants": [1, 2]},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["chat_id"]


@pytest.mark.integration
def test_chat_send_message(client, direct_chat_id):
    resp = client.post(
        "/api/v1/chat/message",
        json={
            "chat_id": direct_chat_id,
            "sender_id": 1,
            "content": "Hello everyone",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body.get("content") == "Hello everyone"


@pytest.mark.integration
def test_chat_get_messages(client, direct_chat_id):
    client.post(
        "/api/v1/chat/message",
        json={
            "chat_id": direct_chat_id,
            "sender_id": 1,
            "content": "Test message",
        },
    )
    resp = client.get(f"/api/v1/chat/history/{direct_chat_id}")
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_chat_history_not_found(client):
    resp = client.get("/api/v1/chat/history/nonexistent_chat_99999")
    assert resp.status_code in (200, 404), resp.text


@pytest.mark.integration
def test_chat_list_threads(client):
    resp = client.get("/api/v1/chat/threads")
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_chatbot_query(client):
    resp = client.post("/api/v1/chatbot/message", json={"message": "What products do you have?"})
    assert resp.status_code in (200, 201, 503), resp.text
    body = resp.json()
    assert "response" in body or "message" in body or "result" in body or "reply" in body


@pytest.mark.integration
def test_chatbot_empty_query(client):
    resp = client.post("/api/v1/chatbot/message", json={"message": ""})
    assert resp.status_code in (200, 422, 503), resp.text


@pytest.mark.integration
def test_websocket_endpoint_exists(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = list(spec.get("paths", {}).keys())
    assert any("/ws/" in p or "/ws" in p for p in paths), paths
