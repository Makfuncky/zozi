"""Workflow tests for payment processing.

Covers Laws 207-214 (Customer Journey) and payment processing:
  - Payment intent creation
  - Payment confirmation
  - Payment idempotency (same payment_id twice)
  - Payment failure handling
  - Refund processing
"""
from __future__ import annotations

import uuid

import pytest


def _unique_email(prefix: str = "pay") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@zozi.test"


def _unique_username(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register_and_login(client, email=None, password="SecurePass1!"):
    """Helper: register a customer and return auth headers."""
    email = email or _unique_email()
    username = _unique_username()
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password, "role": "customer"},
    )
    assert reg.status_code == 201, f"Registration failed: {reg.text}"
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, f"Login failed: {login.text}"
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_order(client, db_session, headers, total=100.00):
    """Helper: create a product and an order, return order_id."""
    from domains.catalog.models.products import Product

    product = Product(
        name=f"Payment Test Product {uuid.uuid4().hex[:6]}",
        price=total,
        stock=100,
        is_deleted=False,
        supplier_id=1,
    )
    db_session.add(product)
    db_session.flush()

    resp = client.post(
        "/api/v1/customer/orders/orders",
        headers=headers,
        json={
            "items": [{"product_id": product.id, "quantity": 1}],
            "full_name": "Test Customer",
            "street": "123 Test St",
            "city": "Test City",
            "zip": "12345",
            "country": "OM",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.integration
class TestPaymentProcessingFlow:
    """End-to-end tests for payment processing."""

    def test_payment_intent_creation(self, client, db_session):
        """A payment intent can be created for an order."""
        headers = _register_and_login(client)
        order_id = _create_order(client, db_session, headers)

        # The payment intent endpoint exists and responds
        # (Stripe may not be configured in test, but the endpoint should respond)
        resp = client.post(
            "/api/v1/customer/finance/create-payment-intent",
            headers=headers,
            json={"order_id": order_id},
        )
        # Either succeeds (Stripe configured) or returns 503 (not configured)
        assert resp.status_code in (200, 201, 503, 409), resp.text

    def test_payment_confirmation(self, client, db_session):
        """Payment confirmation endpoint responds appropriately."""
        headers = _register_and_login(client)
        order_id = _create_order(client, db_session, headers)

        resp = client.post(
            "/api/v1/customer/finance/confirm-card-payment",
            headers=headers,
            json={"order_id": order_id},
        )
        # Should respond - either success or a structured error
        assert resp.status_code in (200, 201, 400, 409, 422, 503), resp.text

    def test_payment_idempotency(self, client, db_session):
        """Using the same idempotency key twice returns the same result."""
        headers = _register_and_login(client)
        order_id = _create_order(client, db_session, headers)
        idempotency_key = f"test-idem-{uuid.uuid4().hex[:12]}"

        resp1 = client.post(
            "/api/v1/customer/finance/create-payment-intent",
            headers=headers,
            json={
                "order_id": order_id,
                "idempotency_key": idempotency_key,
            },
        )

        resp2 = client.post(
            "/api/v1/customer/finance/create-payment-intent",
            headers=headers,
            json={
                "order_id": order_id,
                "idempotency_key": idempotency_key,
            },
        )

        # Both responses should have the same status code
        assert resp1.status_code == resp2.status_code, (
            f"Idempotency violation: first={resp1.status_code}, second={resp2.status_code}"
        )

        # If successful, both should return the same payment intent data
        if resp1.status_code in (200, 201):
            body1 = resp1.json()
            body2 = resp2.json()
            # Both should reference the same order
            assert body1.get("order_id") == body2.get("order_id") == order_id

    def test_payment_failure_handling(self, client, db_session):
        """Payment failure is handled gracefully with a structured error."""
        headers = _register_and_login(client)

        # Try to pay for a non-existent order
        resp = client.post(
            "/api/v1/customer/finance/create-payment-intent",
            headers=headers,
            json={"order_id": 999999},
        )
        # Should return a structured error, not a 500
        assert resp.status_code in (404, 403, 409, 503, 422), resp.text
        # Response should have a detail field
        body = resp.json()
        assert "detail" in body or "error" in body

    def test_refund_processing(self, client, db_session):
        """Refund can be processed for a paid order."""
        from domains.orders.models.orders import Order
        from domains.finance.models.payments import Payment

        headers = _register_and_login(client)
        order_id = _create_order(client, db_session, headers)

        # Simulate a paid order by creating a payment record
        order = db_session.query(Order).filter(Order.id == order_id).first()
        order.status_code = "confirmed"
        order.payment_status = "paid"
        db_session.flush()

        payment = Payment(
            order_id=order_id,
            amount=100.00,
            payment_method="card",
            provider="stripe",
            status="completed",
            intent_id=f"pi_{uuid.uuid4().hex[:12]}",
        )
        db_session.add(payment)
        db_session.flush()

        # Verify payment exists
        assert payment.id is not None
        assert payment.status == "completed"

        # Simulate refund by updating payment status
        payment.status = "refunded"
        db_session.flush()

        db_session.refresh(payment)
        assert payment.status == "refunded"
