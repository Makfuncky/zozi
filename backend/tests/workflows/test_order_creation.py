"""Workflow tests for order creation flow.

Covers Laws 207-214 (Customer Journey) and order lifecycle:
  - Creating an order with valid items
  - Creating an order with insufficient stock
  - Order total calculation
  - Order status is "pending" after creation
  - Order items are correctly associated
  - Inventory is deducted after payment
  - Coupon application
  - Concurrent orders don't oversell
"""
from __future__ import annotations

import threading
import uuid

import pytest


def _unique_email(prefix: str = "order") -> str:
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


def _create_product(db_session, name="Test Product", price=25.00, stock=100):
    """Helper: create a product directly in the database."""
    from domains.catalog.models.products import Product

    product = Product(
        name=name,
        price=price,
        stock=stock,
        is_deleted=False,
        supplier_id=1,
    )
    db_session.add(product)
    db_session.flush()
    return product


@pytest.mark.integration
class TestOrderCreationFlow:
    """End-to-end tests for the order creation flow."""

    def test_create_order_with_valid_items(self, client, db_session):
        """A customer can create an order with valid items."""
        headers = _register_and_login(client)
        product = _create_product(db_session, name="Valid Item Product", price=10.00, stock=50)

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [{"product_id": product.id, "quantity": 2}],
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "pending"
        assert len(body["items"]) == 1
        assert body["items"][0]["product_id"] == product.id
        assert body["items"][0]["quantity"] == 2

    def test_create_order_with_insufficient_stock(self, client, db_session):
        """Creating an order with more items than available stock fails."""
        headers = _register_and_login(client)
        product = _create_product(db_session, name="Low Stock Product", price=10.00, stock=3)

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [{"product_id": product.id, "quantity": 10}],
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 409, resp.text
        assert "Insufficient stock" in resp.json()["detail"]

    def test_order_total_calculation(self, client, db_session):
        """Order total is correctly calculated from items."""
        headers = _register_and_login(client)
        product = _create_product(db_session, name="Priced Product", price=25.50, stock=50)

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [{"product_id": product.id, "quantity": 3}],
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # Total should be at least the item subtotal (25.50 * 3 = 76.50)
        # plus tax/shipping as calculated server-side
        assert body["total"] >= 76.50

    def test_order_status_pending_after_creation(self, client, db_session):
        """A newly created order has status 'pending'."""
        headers = _register_and_login(client)
        product = _create_product(db_session, name="Status Test Product", price=10.00, stock=50)

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
        assert resp.json()["status"] == "pending"

    def test_order_items_correctly_associated(self, client, db_session):
        """Order items are correctly associated with the order."""
        headers = _register_and_login(client)
        product1 = _create_product(db_session, name="Product A", price=10.00, stock=50)
        product2 = _create_product(db_session, name="Product B", price=20.00, stock=50)

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [
                    {"product_id": product1.id, "quantity": 2},
                    {"product_id": product2.id, "quantity": 1},
                ],
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert len(body["items"]) == 2
        product_ids = {item["product_id"] for item in body["items"]}
        assert product1.id in product_ids
        assert product2.id in product_ids

    def test_inventory_deducted_after_payment(self, client, db_session):
        """Inventory is deducted after a successful payment."""
        from domains.orders.models.orders import Order

        headers = _register_and_login(client)
        initial_stock = 10
        product = _create_product(db_session, name="Inventory Product", price=15.00, stock=initial_stock)

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [{"product_id": product.id, "quantity": 3}],
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 201, resp.text
        order_id = resp.json()["id"]

        # Simulate payment confirmation by updating order status to confirmed
        order = db_session.query(Order).filter(Order.id == order_id).first()
        order.status_code = "confirmed"
        db_session.flush()

        # Refresh product to check stock
        db_session.refresh(product)
        assert product.stock == initial_stock - 3

    def test_coupon_application(self, client, db_session):
        """A coupon code can be applied to an order."""
        from domains.promotions.models.promotions import Coupon

        headers = _register_and_login(client)
        product = _create_product(db_session, name="Coupon Product", price=100.00, stock=50)

        # Create a coupon
        coupon = Coupon(
            code="TEST10",
            discount_type="percentage",
            discount_value=10.0,
            is_active=True,
            max_uses=100,
            current_uses=0,
        )
        db_session.add(coupon)
        db_session.flush()

        resp = client.post(
            "/api/v1/customer/orders/orders",
            headers=headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "coupon_code": "TEST10",
                "full_name": "Test Customer",
                "street": "123 Test St",
                "city": "Test City",
                "zip": "12345",
                "country": "OM",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # With a 10% discount on 100.00, the discount should be 10.00
        assert body.get("discount_amount", 0) >= 10.0 or body.get("total", 100) < 100.0

    def test_concurrent_orders_dont_oversell(self, client, db_session):
        """Concurrent orders cannot oversell a product."""
        headers = _register_and_login(client)
        # Create a product with limited stock
        product = _create_product(db_session, name="Limited Product", price=10.00, stock=5)

        results: list[int] = []
        errors: list[str] = []

        def place_order():
            resp = client.post(
                "/api/v1/customer/orders/orders",
                headers=headers,
                json={
                    "items": [{"product_id": product.id, "quantity": 3}],
                    "full_name": "Test Customer",
                    "street": "123 Test St",
                    "city": "Test City",
                    "zip": "12345",
                    "country": "OM",
                },
            )
            results.append(resp.status_code)
            if resp.status_code != 201:
                errors.append(resp.text)

        # Launch 3 concurrent orders of 3 units each (total 9 > stock 5)
        threads = [threading.Thread(target=place_order) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # At most 1 order of 3 units can succeed (stock=5, so 1 succeeds, 2 fail)
        # Or possibly 1 succeeds and the others fail due to insufficient stock
        successful = results.count(201)
        assert successful <= 1, f"Expected at most 1 successful order, got {successful}. Results: {results}"
        assert successful >= 1, f"Expected at least 1 successful order. Results: {results}"
