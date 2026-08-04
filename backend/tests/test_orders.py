"""Tests for order lifecycle."""

import pytest
import uuid
from unittest.mock import patch


@pytest.fixture
def customer_headers(client):
    email = f"orderuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"orderuser_{uuid.uuid4().hex[:8]}",
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
    email = f"prodowner_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(
        email=email,
        username=f"prodowner_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
    )
    db_session.add(user)
    db_session.flush()
    product = Product(
        name="Order Test Product",
        price=20.0,
        stock=100,
        category="Test",
        supplier_id=user.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.mark.integration
def test_create_order(client, customer_headers, product_in_db):
    resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 2}],
            "shipping_address": "123 Test St, Muscat, OM",
            "payment_method": "card",
        },
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert "id" in body
    assert body["status"] == "pending"
    assert body["total_amount"] == 40.0


@pytest.mark.integration
def test_create_order_insufficient_stock(client, customer_headers, product_in_db, db_session):
    from data.models import Product
    product_in_db.stock = 0
    db_session.commit()
    resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    assert resp.status_code == 409


@pytest.mark.integration
def test_get_order_by_id(client, customer_headers, product_in_db):
    create_resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    order_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/orders/{order_id}", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


@pytest.mark.integration
def test_list_user_orders(client, customer_headers, product_in_db):
    client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    resp = client.get("/api/v1/orders", headers=customer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.integration
def test_get_order_not_found(client, customer_headers):
    resp = client.get("/api/v1/orders/999999", headers=customer_headers)
    assert resp.status_code == 404


@pytest.mark.integration
def test_cancel_order(client, customer_headers, product_in_db):
    create_resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    order_id = create_resp.json()["id"]
    resp = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.integration
def test_cancel_already_shipped_order(client, customer_headers, product_in_db, db_session):
    from data.models import Order
    create_resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    order_id = create_resp.json()["id"]
    order = db_session.query(Order).filter(Order.id == order_id).first()
    order.status = "shipped"
    db_session.commit()
    resp = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_headers)
    assert resp.status_code == 409


@pytest.mark.integration
def test_order_requires_authentication(client):
    resp = client.post("/api/v1/orders", json={"items": [], "shipping_address": "X"})
    assert resp.status_code == 401


@pytest.mark.integration
def test_order_validation_empty_items(client, customer_headers):
    resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={"items": [], "shipping_address": "123 Test St"},
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_order_payment_status_transitions(client, customer_headers, product_in_db, db_session):
    from data.models import Order
    create_resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    order_id = create_resp.json()["id"]
    order = db_session.query(Order).filter(Order.id == order_id).first()
    assert order.payment_status == "pending"
    order.payment_status = "completed"
    db_session.commit()
    resp = client.get(f"/api/v1/orders/{order_id}", headers=customer_headers)
    assert resp.json()["payment_status"] == "completed"
