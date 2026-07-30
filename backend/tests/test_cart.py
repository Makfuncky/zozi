"""Tests for shopping cart."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def user_with_product(client, db_session):
    from models import User, Product
    from utils.auth import get_password_hash
    supplier_email = f"cartsupplier_{uuid.uuid4().hex[:8]}@zozi.test"
    supplier = User(
        email=supplier_email,
        username=f"cartsupplier_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
    )
    db_session.add(supplier)
    db_session.commit()
    customer_email = f"cartuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": customer_email,
            "username": f"cartuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": customer_email, "password": "SecurePass1!"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    product = Product(
        name="Cart Test Product",
        price=10.0,
        stock=100,
        category="Test",
        supplier_id=supplier.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return headers, product


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_get_empty_cart(client, user_with_product):
    headers, _ = user_with_product
    resp = client.get("/api/v1/cart", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["subtotal"] == 0.0


@pytest.mark.integration
def test_add_to_cart(client, user_with_product):
    headers, product = user_with_product
    resp = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"product_id": product.id, "quantity": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Added to cart"


@pytest.mark.integration
def test_add_same_product_merges_quantity(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 2, "selected_size": "", "selected_color": ""})
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 3, "selected_size": "", "selected_color": ""})
    resp = client.get("/api/v1/cart", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 5


@pytest.mark.integration
def test_update_cart_item_quantity(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 2, "selected_size": "", "selected_color": ""})
    cart_resp = client.get("/api/v1/cart", headers=headers)
    cart_item_id = cart_resp.json()["items"][0]["id"]
    resp = client.put(f"/api/v1/cart/items/{cart_item_id}", headers=headers, json={"quantity": 5})
    assert resp.status_code == 200
    updated_cart = client.get("/api/v1/cart", headers=headers)
    items = updated_cart.json()["items"]
    assert items[0]["quantity"] == 5


@pytest.mark.integration
def test_remove_cart_item(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 1})
    resp = client.delete(f"/api/v1/cart/items/{product.id}", headers=headers)
    assert resp.status_code == 200
    cart_resp = client.get("/api/v1/cart", headers=headers)
    assert cart_resp.json()["items"] == []


@pytest.mark.integration
def test_clear_cart(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 3})
    resp = client.delete("/api/v1/cart", headers=headers)
    assert resp.status_code == 200
    cart_resp = client.get("/api/v1/cart", headers=headers)
    assert cart_resp.json()["items"] == []


@pytest.mark.integration
def test_add_inactive_product_to_cart(client, user_with_product, db_session):
    from models import Product
    headers, _ = user_with_product
    bad_product = Product(
        name="Inactive Product",
        price=5.0,
        stock=10,
        category="Test",
        is_active=False,
    )
    db_session.add(bad_product)
    db_session.commit()
    db_session.refresh(bad_product)
    resp = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"product_id": bad_product.id, "quantity": 1},
    )
    assert resp.status_code == 404


@pytest.mark.integration
def test_add_nonexistent_product_to_cart(client, user_with_product):
    headers, _ = user_with_product
    resp = client.post("/api/v1/cart/items", headers=headers, json={"product_id": 999999, "quantity": 1})
    assert resp.status_code == 404


@pytest.mark.integration
def test_cart_subtotal_calculation(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 3})
    resp = client.get("/api/v1/cart", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["subtotal"] == 30.0


@pytest.mark.integration
def test_cart_unauthorized(client):
    resp = client.get("/api/v1/cart")
    assert resp.status_code == 401


@pytest.mark.integration
def test_cart_item_count(client, user_with_product):
    headers, product = user_with_product
    client.post("/api/v1/cart/items", headers=headers, json={"product_id": product.id, "quantity": 2})
    resp = client.get("/api/v1/cart", headers=headers)
    assert resp.json()["item_count"] == 1
