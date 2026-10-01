"""Tests for category management."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def admin_headers(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_list_categories(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body or isinstance(body, list)
    data = body.get("data", body) if isinstance(body, dict) else body
    assert isinstance(data, list)


@pytest.mark.integration
def test_get_category_by_id(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    body = resp.json()
    cats = body.get("data", body) if isinstance(body, dict) else body
    if cats:
        cid = cats[0]["id"]
        resp2 = client.get(f"/api/v1/categories/{cid}")
        assert resp2.status_code == 200
        result = resp2.json()
        assert "id" in result or "data" in result
        if isinstance(result, dict) and "data" in result:
            assert result["data"]["id"] == cid
        else:
            assert result["id"] == cid


@pytest.mark.integration
def test_get_category_not_found(client):
    resp = client.get("/api/v1/categories/999999")
    assert resp.status_code == 404


@pytest.mark.integration
def test_create_category(client, admin_headers):
    resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={
            "name": f"Test Cat {uuid.uuid4().hex[:6]}",
            "slug": f"test-cat-{uuid.uuid4().hex[:6]}",
            "description": "A test category",
            "is_active": True,
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["name"].startswith("Test Cat")
    assert "slug" in body


@pytest.mark.integration
def test_create_category_duplicate_slug(client, admin_headers):
    slug = f"dup-cat-{uuid.uuid4().hex[:6]}"
    client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Cat A", "slug": slug},
    )
    resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Cat B", "slug": slug},
    )
    assert resp.status_code in (400, 409)


@pytest.mark.integration
def test_update_category(client, admin_headers):
    create_resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Updatable Cat", "slug": f"upd-cat-{uuid.uuid4().hex[:6]}"},
    )
    cid = create_resp.json()["id"]
    resp = client.put(
        f"/api/v1/categories/{cid}",
        headers=admin_headers,
        json={"name": "Renamed Cat", "description": "Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Cat"


@pytest.mark.integration
def test_delete_category(client, admin_headers):
    create_resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Deletable Cat", "slug": f"del-cat-{uuid.uuid4().hex[:6]}"},
    )
    cid = create_resp.json()["id"]
    resp = client.delete(f"/api/v1/categories/{cid}", headers=admin_headers)
    assert resp.status_code in (200, 404)


@pytest.mark.integration
def test_category_tree_parent_child(client, admin_headers):
    parent_resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Parent Cat", "slug": f"parent-cat-{uuid.uuid4().hex[:6]}"},
    )
    parent_id = parent_resp.json()["id"]
    child_resp = client.post(
        "/api/v1/categories",
        headers=admin_headers,
        json={"name": "Child Cat", "slug": f"child-cat-{uuid.uuid4().hex[:6]}", "parent_id": parent_id},
    )
    assert child_resp.status_code in (200, 201)
    assert child_resp.json()["parent_id"] == parent_id


@pytest.mark.integration
def test_category_unauthorized_create(client):
    resp = client.post("/api/v1/categories", json={"name": "Unauth Cat"})
    assert resp.status_code == 401
