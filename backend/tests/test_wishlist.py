"""Tests for wishlist functionality."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def customer_headers(client):
    email = f"wishuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"wishuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "customer",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def product_in_db(client, db_session):
    from data.models import User, Product
    from utils.auth import get_password_hash
    email = f"wishowner_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(
        email=email,
        username=f"wishowner_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
    )
    db_session.add(user)
    db_session.flush()
    product = Product(
        name="Wishlist Test Product",
        price=15.0,
        stock=20,
        category="Test",
        supplier_id=user.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.mark.integration
def test_list_empty_wishlist(client, customer_headers):
    resp = client.get("/wishlist", headers=customer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_add_to_wishlist(client, customer_headers, product_in_db):
    resp = client.post(f"/wishlist/{product_in_db.id}", headers=customer_headers)
    assert resp.status_code in (200, 201)


@pytest.mark.integration
def test_remove_from_wishlist(client, customer_headers, product_in_db):
    client.post(f"/wishlist/{product_in_db.id}", headers=customer_headers)
    resp = client.delete(f"/wishlist/{product_in_db.id}", headers=customer_headers)
    assert resp.status_code == 200
    get_resp = client.get("/wishlist", headers=customer_headers)
    assert all(item["product_id"] != product_in_db.id for item in get_resp.json())


@pytest.mark.integration
def test_wishlist_shows_added_products(client, customer_headers, product_in_db):
    client.post(f"/wishlist/{product_in_db.id}", headers=customer_headers)
    resp = client.get("/wishlist", headers=customer_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert any(item["product_id"] == product_in_db.id for item in items)


@pytest.mark.integration
def test_wishlist_unauthorized(client):
    resp = client.get("/wishlist")
    assert resp.status_code == 401


@pytest.mark.integration
def test_wishlist_add_invalid_product(client, customer_headers):
    resp = client.post("/wishlist/999999", headers=customer_headers)
    assert resp.status_code in (404, 400)
