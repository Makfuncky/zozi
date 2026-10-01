"""Tests for banner management."""
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
def test_list_banners(client):
    resp = client.get("/api/v1/banners")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_create_banner(client, admin_headers):
    resp = client.post(
        "/api/v1/banners",
        headers=admin_headers,
        json={
            "title": f"Test Banner {uuid.uuid4().hex[:6]}",
            "image_url": "http://img.test/banner.png",
            "link_url": "/products",
            "is_active": True,
            "sort_order": 1,
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["title"].startswith("Test Banner")


@pytest.mark.integration
def test_update_banner(client, admin_headers):
    create_resp = client.post(
        "/api/v1/banners",
        headers=admin_headers,
        json={"title": "Updatable Banner", "image_url": "http://img.test/b.png", "is_active": True},
    )
    banner_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/v1/banners/{banner_id}",
        headers=admin_headers,
        json={"title": "Updated Banner", "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Banner"


@pytest.mark.integration
def test_delete_banner(client, admin_headers):
    create_resp = client.post(
        "/api/v1/banners",
        headers=admin_headers,
        json={"title": "Deletable Banner", "image_url": "http://img.test/b.png", "is_active": True},
    )
    banner_id = create_resp.json()["id"]
    resp = client.delete(f"/api/v1/banners/{banner_id}", headers=admin_headers)
    assert resp.status_code == 200
    get_resp = client.get(f"/api/v1/banners/{banner_id}", headers=admin_headers)
    assert get_resp.status_code == 404


@pytest.mark.integration
def test_banner_unauthorized(client):
    resp = client.post("/api/v1/banners", json={"title": "X"})
    assert resp.status_code == 401


@pytest.mark.integration
def test_active_banners_only(client, admin_headers):
    client.post(
        "/api/v1/banners",
        headers=admin_headers,
        json={"title": "Inactive Banner", "image_url": "http://img.test/b.png", "is_active": False},
    )
    resp = client.get("/api/v1/banners?active_only=true")
    assert resp.status_code == 200
    for b in resp.json():
        assert b.get("is_active") is True
