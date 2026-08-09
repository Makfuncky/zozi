"""Tests for product reviews."""
from __future__ import annotations

import pytest
import uuid


@pytest.fixture
def customer_headers(client):
    email = f"reviewer_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"reviewer_{uuid.uuid4().hex[:8]}",
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
    email = f"revowner_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(
        email=email,
        username=f"revowner_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
    )
    db_session.add(user)
    db_session.flush()
    product = Product(
        name="Review Test Product",
        price=10.0,
        stock=10,
        category="Test",
        supplier_id=user.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.mark.integration
def test_create_review(client, customer_headers, product_in_db):
    resp = client.post(
        f"/api/v1/reviews/products/{product_in_db.id}",
        headers=customer_headers,
        json={"rating": 5, "title": "Great", "comment": "Excellent product"},
    )
    assert resp.status_code in (200, 201)


@pytest.mark.integration
def test_create_review_invalid_rating(client, customer_headers, product_in_db):
    resp = client.post(
        f"/api/v1/reviews/products/{product_in_db.id}",
        headers=customer_headers,
        json={"rating": 6, "comment": "Too high"},
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_list_product_reviews(client, customer_headers, product_in_db):
    client.post(
        f"/api/v1/reviews/products/{product_in_db.id}",
        headers=customer_headers,
        json={"rating": 4, "comment": "Nice"},
    )
    resp = client.get(f"/api/v1/reviews/products/{product_in_db.id}", headers=customer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_update_review(client, customer_headers, product_in_db):
    create_resp = client.post(
        f"/api/v1/reviews/products/{product_in_db.id}",
        headers=customer_headers,
        json={"rating": 3, "comment": "Okay"},
    )
    review_id = create_resp.json()["id"]
    resp = client.put(
        f"/api/v1/reviews/{review_id}",
        headers=customer_headers,
        json={"rating": 5, "comment": "Updated"},
    )
    assert resp.status_code == 405


@pytest.mark.integration
def test_delete_review(client, customer_headers, product_in_db):
    create_resp = client.post(
        f"/api/v1/reviews/products/{product_in_db.id}",
        headers=customer_headers,
        json={"rating": 3, "comment": "Delete me"},
    )
    review_id = create_resp.json()["id"]
    resp = client.delete(f"/api/v1/reviews/{review_id}", headers=customer_headers)
    assert resp.status_code == 200


@pytest.mark.integration
def test_review_unauthorized(client, product_in_db):
    resp = client.post(f"/api/v1/reviews/products/{product_in_db.id}", json={"rating": 5})
    assert resp.status_code == 401


@pytest.mark.integration
def test_review_not_found(client, customer_headers, product_in_db):
    resp = client.get(f"/api/v1/reviews/products/{product_in_db.id}", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json() == []
