"""Tests for model integrity and database constraints."""
from __future__ import annotations

import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from models import (
    User, Category, Product, ProductVariant, Order, OrderItem,
    Payment, Coupon, Banner, Review, WishlistItem, CartItem,
    Address, Notification, CountryConfig, LogisticsPartner,
    SupplierProfile, Invoice, Account, TreasuryTransaction,
)
from db.base import Base


@pytest.mark.integration
def test_all_models_have_tablename(db_session):
    model_classes = [
        User, Category, Product, ProductVariant, Order, OrderItem,
        Payment, Coupon, Banner, Review, WishlistItem, CartItem,
        Address, Notification, CountryConfig, LogisticsPartner,
        SupplierProfile, Invoice, Account, TreasuryTransaction,
    ]
    for model in model_classes:
        assert hasattr(model, "__tablename__")
        assert model.__tablename__ is not None
        assert len(model.__tablename__) > 0


@pytest.mark.integration
def test_user_model_defaults(db_session):
    user = User(
        email=f"model_{uuid.uuid4().hex[:8]}@zozi.test",
        username=f"model_{uuid.uuid4().hex[:8]}",
        hashed_password="hashed",
        role="customer",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.is_active is True
    assert user.email_verified is False
    assert user.role == "customer"
    assert user.referral_points == 0


@pytest.mark.integration
def test_product_model_defaults(db_session):
    product = Product(
        name="Model Test Product",
        price=Decimal("10.00"),
        category="Test",
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    assert product.is_active is True
    assert product.is_featured is False
    assert product.stock == 0
    assert product.rating == 0


@pytest.mark.integration
def test_order_model_defaults(db_session):
    user = User(
        email=f"order_model_{uuid.uuid4().hex[:8]}@zozi.test",
        username=f"order_model_{uuid.uuid4().hex[:8]}",
        hashed_password="hashed",
        role="customer",
    )
    db_session.add(user)
    db_session.flush()
    order = Order(
        user_id=user.id,
        subtotal=Decimal("10.00"),
        total=Decimal("10.00"),
        payment_status="pending",
        status="pending",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    assert order.status == "pending"
    assert order.payment_status == "pending"


@pytest.mark.integration
def test_payment_model_constraint(db_session):
    from sqlalchemy.exc import IntegrityError
    payment = Payment(
        order_id=1,
        amount=Decimal("-5.00"),
        payment_method="card",
        status="pending",
    )
    db_session.add(payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_payment_status_check_constraint(db_session):
    from sqlalchemy.exc import IntegrityError
    payment = Payment(
        order_id=1,
        amount=Decimal("10.00"),
        payment_method="card",
        status="invalid_status",
    )
    db_session.add(payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_category_slug_unique(db_session):
    from sqlalchemy.exc import IntegrityError
    cat1 = Category(name="Cat A", slug="unique-slug")
    cat2 = Category(name="Cat B", slug="unique-slug")
    db_session.add_all([cat1, cat2])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_product_slug_unique(db_session):
    from sqlalchemy.exc import IntegrityError
    p1 = Product(name="Product A", slug="prod-slug", price=10.0)
    p2 = Product(name="Product B", slug="prod-slug", price=20.0)
    db_session.add_all([p1, p2])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_product_variant_unique_constraint(db_session):
    from sqlalchemy.exc import IntegrityError
    from models import Product, ProductVariant
    product = Product(name="Var Product", slug="var-prod", price=10.0)
    db_session.add(product)
    db_session.flush()
    v1 = ProductVariant(product_id=product.id, variant_key="same-key", size="M", color="Red")
    v2 = ProductVariant(product_id=product.id, variant_key="same-key", size="L", color="Blue")
    db_session.add_all([v1, v2])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_user_email_unique(db_session):
    from sqlalchemy.exc import IntegrityError
    u1 = User(email=f"same_{uuid.uuid4().hex[:8]}@zozi.test", username="u1", hashed_password="x", role="customer")
    u2 = User(email=u1.email, username="u2", hashed_password="x", role="customer")
    db_session.add_all([u1, u2])
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.integration
def test_order_items_relationship(db_session):
    from models import User, Product, Order, OrderItem
    user = User(email=f"rel_{uuid.uuid4().hex[:8]}@zozi.test", username=f"rel_{uuid.uuid4().hex[:8]}", hashed_password="x", role="customer")
    product = Product(name="Rel Product", slug="rel-prod", price=10.0)
    db_session.add_all([user, product])
    db_session.flush()
    order = Order(user_id=user.id, subtotal=Decimal("10.00"), total=Decimal("10.00"))
    db_session.add(order)
    db_session.flush()
    item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=Decimal("10.00"), price=Decimal("10.00"), total_price=Decimal("10.00"))
    db_session.add(item)
    db_session.commit()
    db_session.refresh(order)
    assert len(order.items) == 1
    assert order.items[0].product_id == product.id
