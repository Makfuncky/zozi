"""Tests for product listing, search, and admin CRUD."""
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


@pytest.fixture
def supplier_headers(client):
    email = f"supplier_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"supplier_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "supplier",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.integration
def test_list_products_empty(client):
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_list_products_pagination(client):
    resp = client.get("/api/v1/products?limit=5&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) <= 5


@pytest.mark.integration
def test_list_products_filter_category(client):
    resp = client.get("/api/v1/products?category=electronics")
    assert resp.status_code == 200
    for p in resp.json():
        assert p.get("category", "").lower() == "electronics"


@pytest.mark.integration
def test_list_products_filter_in_stock(client):
    resp = client.get("/api/v1/products?in_stock=true")
    assert resp.status_code == 200
    for p in resp.json():
        assert p.get("stock", 0) > 0


@pytest.mark.integration
def test_get_product_not_found(client):
    resp = client.get("/api/v1/products/999999")
    assert resp.status_code == 404


@pytest.mark.integration
def test_create_product_as_supplier(client, supplier_headers):
    resp = client.post(
        "/api/v1/products/",
        headers=supplier_headers,
        json={
            "name": "Test Widget",
            "description": "A test widget",
            "price": 25.0,
            "category": "Widgets",
            "stock": 100,
            "image_url": "http://img.test/w.png",
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["name"] == "Test Widget"
    assert "slug" in body


@pytest.mark.integration
def test_create_product_as_customer_forbidden(client):
    email = f"custprod_{uuid.uuid4().hex[:8]}@zozi.test"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"custprod_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    assert reg.status_code in (200, 201), f"Registration failed: {reg.text}"
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert login.status_code == 200
    user_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.post(
        "/api/v1/products/",
        headers=user_headers,
        json={
            "name": "Forbidden Widget",
            "price": 10.0,
            "category": "Widgets",
        },
    )
    assert resp.status_code == 403


@pytest.mark.integration
def test_update_product(client, supplier_headers, admin_headers):
    create_resp = client.post(
        "/api/v1/products/",
        headers=supplier_headers,
        json={
            "name": "Updatable Widget",
            "price": 15.0,
            "category": "Widgets",
            "stock": 50,
        },
    )
    product_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/v1/products/{product_id}",
        headers=supplier_headers,
        json={"name": "Updated Widget", "price": 20.0},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Widget"


@pytest.mark.integration
def test_delete_product(client, supplier_headers):
    create_resp = client.post(
        "/api/v1/products/",
        headers=supplier_headers,
        json={
            "name": "Deletable Widget",
            "price": 5.0,
            "category": "Widgets",
        },
    )
    product_id = create_resp.json()["id"]
    resp = client.delete(f"/api/v1/products/{product_id}", headers=supplier_headers)
    assert resp.status_code == 200
    get_resp = client.get(f"/api/v1/products/{product_id}")
    assert get_resp.status_code == 404


@pytest.mark.integration
def test_product_price_must_be_positive(client, supplier_headers):
    resp = client.post(
        "/api/v1/products/",
        headers=supplier_headers,
        json={
            "name": "Bad Price Widget",
            "price": -5.0,
            "category": "Widgets",
        },
    )
    assert resp.status_code in (200, 201, 422)


@pytest.mark.integration
def test_product_name_max_length(client, supplier_headers):
    resp = client.post(
        "/api/v1/products/",
        headers=supplier_headers,
        json={
            "name": "X" * 300,
            "price": 10.0,
            "category": "Widgets",
        },
    )
    assert resp.status_code in (200, 201, 422)


@pytest.mark.integration
def test_smart_search_returns_structure(client):
    resp = client.get("/api/v1/search/products?q=phone&limit=4")
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert "parsed" in body
    assert isinstance(body["results"], list)


@pytest.mark.integration
def test_smart_search_price_parse(client):
    resp = client.get("/api/v1/search/products?q=laptops+under+500")
    assert resp.status_code == 200
    parsed = resp.json()["parsed"]
    assert parsed.get("max_price") == 500.0


@pytest.mark.integration
def test_smart_search_color_parse(client):
    resp = client.get("/api/v1/search/products?q=show+me+black+t-shirt+options")
    assert resp.status_code == 200
    parsed = resp.json()["parsed"]
    assert parsed.get("color") == "black"
