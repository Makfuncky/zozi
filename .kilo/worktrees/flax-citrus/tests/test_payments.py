"""Tests for payment processing and webhooks."""
from __future__ import annotations

import hmac
import hashlib
import json
import os
import pytest
import uuid
from unittest.mock import patch, MagicMock


@pytest.fixture
def customer_headers(client):
    email = f"payuser_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"payuser_{uuid.uuid4().hex[:8]}",
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
    email = f"payowner_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(
        email=email,
        username=f"payowner_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="supplier",
    )
    db_session.add(user)
    db_session.flush()
    product = Product(
        name="Payment Test Product",
        price=30.0,
        stock=50,
        category="Test",
        supplier_id=user.id,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def order_in_db(client, customer_headers, product_in_db):
    resp = client.post(
        "/api/v1/orders",
        headers=customer_headers,
        json={
            "items": [{"product_id": product_in_db.id, "quantity": 1}],
            "shipping_address": "123 Test St",
            "payment_method": "card",
        },
    )
    return resp.json()["id"]


def _mock_payment_intent(intent_id="pi_test_001", amount=3000, currency="usd"):
    intent = MagicMock()
    intent.id = intent_id
    intent.client_secret = f"cs_{intent_id}"
    intent.amount = amount
    intent.currency = currency
    intent.metadata = {}
    return intent


@pytest.mark.integration
def test_create_payment_intent(client, customer_headers, order_in_db):
    with patch("controllers.payments_controller.stripe") as mock_stripe, \
         patch("controllers.payments_controller._stripe_configured", return_value=True), \
         patch("controllers.payments_controller._payment_provider_mode_allows", return_value=True):
        mock_stripe.PaymentIntent.create.return_value = _mock_payment_intent()
        resp = client.post(
            "/api/v1/payments/create-payment-intent",
            headers=customer_headers,
            json={"order_id": order_in_db, "amount": 30.0},
        )
        assert resp.status_code == 200
        assert "client_secret" in resp.json()


@pytest.mark.integration
def test_create_payment_intent_invalid_amount(client, customer_headers, order_in_db):
    with patch("controllers.payments_controller._stripe_configured", return_value=True), \
         patch("controllers.payments_controller._payment_provider_mode_allows", return_value=True):
        resp = client.post(
            "/api/v1/payments/create-payment-intent",
            headers=customer_headers,
            json={"order_id": order_in_db, "amount": -5.0},
        )
        assert resp.status_code in (400, 422)


@pytest.mark.integration
def test_payment_methods_status(client, customer_headers):
    resp = client.get("/api/v1/payments/methods", headers=customer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert len(body) > 0


@pytest.mark.integration
def test_stripe_webhook_misconfigured(client):
    resp = client.post("/api/v1/payments/webhook", content="{}")
    assert resp.status_code == 503


@pytest.mark.integration
def test_stripe_webhook_bad_payload(client):
    with patch("controllers.payments_controller.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = "whsec_test"
        resp = client.post(
            "/api/v1/payments/webhook",
            content="not-json",
            headers={"Stripe-Signature": "t=1,v=0,s=bad"},
        )
        assert resp.status_code in (400, 401)


@pytest.mark.integration
def test_payment_gateway_list_admin(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.get("/api/v1/payments/config/gateways", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_payment_gateway_create_admin(client):
    admin_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@zozi.com", "password": "admin123"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    resp = client.put(
        "/api/v1/payments/config/gateways/stripe",
        headers=admin_headers,
        json={
            "provider_code": "stripe",
            "display_name": "Test Stripe",
            "is_active": True,
        },
    )
    assert resp.status_code in (200, 201)


@pytest.mark.integration
def test_payment_unauthorized(client):
    resp = client.post("/api/v1/payments/create-payment-intent", json={"order_id": 1, "amount": 10})
    assert resp.status_code == 401


@pytest.mark.integration
def test_payment_intent_for_nonexistent_order(client, customer_headers):
    with patch("controllers.payments_controller._stripe_configured", return_value=True), \
         patch("controllers.payments_controller._payment_provider_mode_allows", return_value=True):
        resp = client.post(
            "/api/v1/payments/create-payment-intent",
            headers=customer_headers,
            json={"order_id": 999999, "amount": 10.0},
        )
        assert resp.status_code in (404, 400)
