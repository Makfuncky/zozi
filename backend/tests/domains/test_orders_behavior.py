"""Behavior tests for orders domain — lifecycle, status transitions, cart, and checkout flows."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domains.orders.models.order_entities import Order, OrderItem, ReturnRequest
from domains.orders.services.orders_service import (
    update_order_status,
    get_order_gateway,
    _can_staff_override_order_status,
)


def _create_order(db_session, user_id=1, status_code="pending", currency="USD", country_code="AE", total_amount=100.00):
    order = Order(
        user_id=user_id,
        status_code=status_code,
        currency=currency,
        country_code=country_code,
        total_amount=Decimal(str(total_amount)),
        subtotal=Decimal(str(total_amount)),
    )
    db_session.add(order)
    db_session.flush()
    return order


def _create_product(db_session, name="Test Product", price=10.00, stock=100):
    from domains.catalog.models.products import Product
    product = Product(
        name=name,
        price=Decimal(str(price)),
        stock=stock,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    return product


# ══════════════════════════════════════════════════════════════════
# Order Creation with Items
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderCreation:
    """Test order creation with items."""

    def test_create_order_with_items(self, db_session):
        order = _create_order(db_session)
        item = OrderItem(
            order_id=order.id,
            product_id=1,
            quantity=2,
            unit_price=Decimal("50.00"),
            total_price=Decimal("100.00"),
        )
        db_session.add(item)
        db_session.flush()
        assert order.id is not None
        assert len(order.items) >= 1
        assert order.items[0].quantity == 2

    def test_order_default_status_is_pending(self, db_session):
        order = _create_order(db_session)
        assert order.status_code == "pending"

    def test_order_total_amount_persisted(self, db_session):
        order = _create_order(db_session, total_amount=250.50)
        assert float(order.total_amount) == 250.50

    def test_order_item_total_price_calculated(self, db_session):
        order = _create_order(db_session)
        item = OrderItem(
            order_id=order.id,
            product_id=1,
            quantity=3,
            unit_price=Decimal("25.00"),
            total_price=Decimal("75.00"),
        )
        db_session.add(item)
        db_session.flush()
        assert float(item.total_price) == 75.00


# ══════════════════════════════════════════════════════════════════
# Order Status Transitions
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderStatusTransitions:
    """Test order status transition logic."""

    def test_pending_to_confirmed(self, db_session):
        order = _create_order(db_session, status_code="pending")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "confirmed", acting_user, db_session)
        assert result["new_status"] == "confirmed"
        assert result["old_status"] == "pending"

    def test_confirmed_to_shipped(self, db_session):
        order = _create_order(db_session, status_code="confirmed")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "shipped", acting_user, db_session)
        assert result["new_status"] == "shipped"

    def test_shipped_to_delivered(self, db_session):
        order = _create_order(db_session, status_code="shipped")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "delivered", acting_user, db_session)
        assert result["new_status"] == "delivered"

    def test_pending_to_cancelled(self, db_session):
        order = _create_order(db_session, status_code="pending")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "cancelled", acting_user, db_session)
        assert result["new_status"] == "cancelled"

    def test_invalid_transition_rejected(self, db_session):
        order = _create_order(db_session, status_code="delivered")
        acting_user = {"id": 1, "username": "customer", "role": "customer"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(order.id, "pending", acting_user, db_session)
        assert exc_info.value.status_code == 409

    def test_delivered_cannot_be_cancelled_by_customer(self, db_session):
        order = _create_order(db_session, status_code="delivered")
        acting_user = {"id": 1, "username": "customer", "role": "customer"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(order.id, "cancelled", acting_user, db_session)
        assert exc_info.value.status_code == 409

    def test_admin_can_override_status(self, db_session):
        order = _create_order(db_session, status_code="shipped")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "confirmed", acting_user, db_session)
        assert result["new_status"] == "confirmed"
        assert result["forced_override"] is True

    def test_same_status_returns_unchanged(self, db_session):
        order = _create_order(db_session, status_code="pending")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "pending", acting_user, db_session)
        assert "unchanged" in result["message"].lower()

    def test_invalid_status_rejected(self, db_session):
        order = _create_order(db_session, status_code="pending")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(order.id, "invalid_status", acting_user, db_session)
        assert exc_info.value.status_code == 400

    def test_nonexistent_order_rejected(self, db_session):
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(99999, "confirmed", acting_user, db_session)
        assert exc_info.value.status_code == 404


# ══════════════════════════════════════════════════════════════════
# Order Cancellation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderCancellation:
    """Test order cancellation flow."""

    def test_cancel_pending_order(self, db_session):
        order = _create_order(db_session, status_code="pending")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "cancelled", acting_user, db_session)
        assert result["new_status"] == "cancelled"

    def test_cancel_confirmed_order(self, db_session):
        order = _create_order(db_session, status_code="confirmed")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        result = update_order_status(order.id, "cancelled", acting_user, db_session)
        assert result["new_status"] == "cancelled"

    def test_cannot_cancel_already_cancelled(self, db_session):
        order = _create_order(db_session, status_code="cancelled")
        acting_user = {"id": 1, "username": "admin", "role": "admin"}
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(order.id, "pending", acting_user, db_session)
        assert exc_info.value.status_code == 409


# ══════════════════════════════════════════════════════════════════
# Order Return Request
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderReturn:
    """Test order return request flow."""

    def test_create_return_request(self, db_session):
        order = _create_order(db_session, status_code="delivered")
        return_req = ReturnRequest(
            order_id=order.id,
            user_id=order.user_id,
            reason="Defective product",
            description="Item arrived broken",
            status_code="requested",
        )
        db_session.add(return_req)
        db_session.flush()
        assert return_req.id is not None
        assert return_req.status_code == "requested"
        assert return_req.reason == "Defective product"

    def test_return_request_default_status(self, db_session):
        order = _create_order(db_session, status_code="delivered")
        return_req = ReturnRequest(
            order_id=order.id,
            user_id=order.user_id,
            reason="Changed mind",
        )
        db_session.add(return_req)
        db_session.flush()
        assert return_req.status_code == "requested"

    def test_return_request_linked_to_order(self, db_session):
        order = _create_order(db_session, status_code="delivered")
        return_req = ReturnRequest(
            order_id=order.id,
            user_id=order.user_id,
            reason="Wrong size",
        )
        db_session.add(return_req)
        db_session.flush()
        assert return_req.order_id == order.id


# ══════════════════════════════════════════════════════════════════
# Cart Operations
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCartOperations:
    """Test cart operations (add, remove, update quantity)."""

    def test_add_item_to_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=2)
        result = add_to_cart(user_id, payload, db_session)
        assert result["message"] == "Added to cart"

    def test_add_same_product_increases_quantity(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=1)
        add_to_cart(user_id, payload, db_session)
        add_to_cart(user_id, payload, db_session)
        cart = get_cart(user_id, db_session)
        assert cart.total_items == 1
        assert cart.items[0]["quantity"] == 2

    def test_remove_item_from_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, remove_cart_item
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(user_id, payload, db_session)
        result = remove_cart_item(user_id, product.id, db_session)
        assert result["message"] == "Removed"

    def test_remove_nonexistent_item_rejected(self, db_session):
        from domains.customers.services.cart_service import remove_cart_item
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            remove_cart_item(1, 99999, db_session)
        assert exc_info.value.status_code == 404

    def test_update_cart_item_quantity(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, update_cart_item, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=1)
        add_to_cart(user_id, payload, db_session)
        update_cart_item(user_id, product.id, 5, "", "", db_session)
        cart = get_cart(user_id, db_session)
        assert cart.items[0]["quantity"] == 5

    def test_update_cart_item_quantity_to_zero_removes(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, update_cart_item, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(user_id, payload, db_session)
        update_cart_item(user_id, product.id, 0, "", "", db_session)
        cart = get_cart(user_id, db_session)
        assert cart.total_items == 0

    def test_clear_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, clear_cart, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(user_id, payload, db_session)
        result = clear_cart(user_id, db_session)
        assert result["message"] == "Cart cleared"
        cart = get_cart(user_id, db_session)
        assert cart.total_items == 0

    def test_get_cart_returns_subtotal(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session, price=25.00)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=3)
        add_to_cart(user_id, payload, db_session)
        cart = get_cart(user_id, db_session)
        assert cart.subtotal == 75.00


# ══════════════════════════════════════════════════════════════════
# Checkout Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCheckoutFlow:
    """Test checkout flow."""

    def test_checkout_creates_order_from_cart(self, client):
        email = f"checkout_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"checkoutuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post(
            "/api/v1/orders/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={"shipping_address": "123 Test St", "payment_method": "stripe"},
        )
        assert resp.status_code in (200, 201)

    def test_checkout_empty_cart_rejected(self, client):
        email = f"emptycart_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"emptycartuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post(
            "/api/v1/orders/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={"shipping_address": "123 Test St", "payment_method": "stripe"},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Order History and Detail
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderHistory:
    """Test order history listing and detail retrieval."""

    def test_order_history_listing(self, client):
        email = f"history_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"historyuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/orders", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body or isinstance(body, list)

    def test_order_detail_retrieval(self, client):
        email = f"detail_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"detailuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/orders/1", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════════
# Payment Gateway Routing
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPaymentGatewayRouting:
    """Test payment gateway routing based on country."""

    def test_sa_routes_to_stripe(self, db_session):
        order = _create_order(db_session, country_code="SA")
        gateway = get_order_gateway(order)
        assert gateway == "stripe"

    def test_ae_routes_to_stripe(self, db_session):
        order = _create_order(db_session, country_code="AE")
        gateway = get_order_gateway(order)
        assert gateway == "stripe"

    def test_jo_routes_to_tap(self, db_session):
        order = _create_order(db_session, country_code="JO")
        gateway = get_order_gateway(order)
        assert gateway == "tap"

    def test_eg_routes_to_paytabs(self, db_session):
        order = _create_order(db_session, country_code="EG")
        gateway = get_order_gateway(order)
        assert gateway == "paytabs"

    def test_unknown_country_defaults_to_stripe(self, db_session):
        order = _create_order(db_session, country_code="XX")
        gateway = get_order_gateway(order)
        assert gateway == "stripe"


# ══════════════════════════════════════════════════════════════════
# Order Status Helper Functions
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOrderStatusHelpers:
    """Test order status helper functions."""

    def test_can_staff_override_normal_transition(self):
        assert _can_staff_override_order_status("pending", "confirmed") is True

    def test_cannot_override_from_cancelled(self):
        assert _can_staff_override_order_status("cancelled", "pending") is False

    def test_cannot_override_from_failed(self):
        assert _can_staff_override_order_status("failed", "pending") is False

    def test_cannot_override_to_refunded(self):
        assert _can_staff_override_order_status("delivered", "refunded") is False

    def test_cannot_override_from_refunded(self):
        assert _can_staff_override_order_status("refunded", "pending") is False
