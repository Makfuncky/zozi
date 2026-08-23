"""Regression tests for the implemented financial write services.

Guards the remediation that replaced ``_missing_symbol`` stubs in
``commission_write_service``, ``payments_write_service`` and
``invoice_write_service`` with real DB-write logic.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

import domains.finance.services.commission.commission_write_service as commission
import domains.finance.services.payments.payments_write_service as payments
import domains.finance.services.ledger.invoice_write_service as invoice
from infrastructure.database.models import (
    CommissionAgreement,
    CommissionBadgeTier,
    CommissionCategoryRate,
    CommissionGlobalConfig,
    CommissionLedgerEntry,
    Order,
    Product,
    User,
)


def _user(db):
    u = User(
        email=f"u{uuid.uuid4().hex[:12]}@ex.com",
        username=f"u{uuid.uuid4().hex[:12]}",
        hashed_password="x",
        country_code="OM",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _product(db, user):
    p = Product(name="Test", price=Decimal("1.00"), supplier_id=user.id, country_code="OM")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _order(db, user):
    o = Order(
        user_id=user.id,
        order_number=f"ORD-{uuid.uuid4().hex[:12]}",
        subtotal=Decimal("0"),
        subtotal_amount=Decimal("0"),
        total=Decimal("0"),
        total_amount=Decimal("0"),
        country_code="OM",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def test_commission_agreement_create_and_delete(db_session):
    user = _user(db_session)
    obj = commission.create_commission_agreement(db_session, supplier_id=user.id, tier="gold", rate=0.1)
    assert obj.id is not None
    assert obj.tier == "gold"
    acting = {"id": user.id, "username": "tester", "role": "admin"}
    commission.delete_commission_agreement(db_session, obj.id, acting_user=acting, reason="test")
    reloaded = db_session.get(CommissionAgreement, obj.id)
    assert reloaded.is_deleted is True


def test_commission_override_create_update(db_session):
    user = _user(db_session)
    product = _product(db_session, user)
    obj = commission.create_product_commission_override(db_session, product_id=product.id, supplier_id=user.id, rate_percent=5.0)
    assert obj.id is not None
    updated = commission.update_product_commission_override(db_session, obj.id, rate_percent=7.5, is_active=False)
    assert updated.rate_percent == 7.5
    assert updated.is_active is False


@pytest.mark.parametrize(
    "model,update_fn,defaults,change",
    [
        (CommissionBadgeTier, commission.update_commission_badge_tier,
         dict(name="Gold", badge_level="gold", commission_rate=0.1), dict(is_active=False)),
        (CommissionCategoryRate, commission.update_commission_category_rate,
         dict(category_slug="electronics", rate_percent=3.0), dict(is_active=False)),
        (CommissionGlobalConfig, commission.update_commission_global_config,
         dict(default_rate=0.2), dict(default_rate=0.35)),
        (CommissionLedgerEntry, commission.update_commission_ledger_entry,
         dict(supplier_id=1, amount=1.5, status="pending"), dict(status="adjusted")),
    ],
)
def test_commission_update_fns(db_session, model, update_fn, defaults, change):
    row = model(**defaults)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    changed = update_fn(db_session, row.id, **change)
    assert changed.id == row.id


def test_payment_create_update(db_session):
    user = _user(db_session)
    order = _order(db_session, user)
    pay = payments.create_payment(db_session, order_id=order.id, amount=10.0, payment_method="card")
    assert pay.id is not None
    updated = payments.update_payment(db_session, pay.id, status="completed")
    assert updated.status == "completed"


def test_payment_provider_config_crud(db_session):
    cfg = payments.create_payment_provider_config(db_session, provider_name="stripe", config={"key": "v"})
    assert cfg.id is not None
    updated = payments.update_payment_provider_config(db_session, cfg.id, is_active=False)
    assert updated.is_active is False
    no_refresh = payments.update_payment_provider_config_no_refresh(db_session, cfg.id, is_active=True)
    assert no_refresh.is_active is True


def test_gateway_connection_upsert(db_session):
    first = payments.create_or_update_gateway_connection(
        db_session, provider_code="stripe", gateway_name="Stripe", country_code="OM",
        display_name="Stripe OM", mode="test",
    )
    second = payments.create_or_update_gateway_connection(
        db_session, provider_code="stripe", gateway_name="Stripe", country_code="OM",
        display_name="Stripe OM", mode="live",
    )
    assert first.id == second.id
    assert second.mode == "live"
    updated = payments.update_gateway_connection(db_session, first.id, is_enabled=False)
    assert updated.is_enabled is False


def test_webhook_and_notification(db_session):
    evt = payments.add_processed_webhook_event(db_session, processor="stripe", event_id="evt_1")
    assert evt.id is not None
    assert evt.payload_hash  # auto-populated by before_insert listener
    note = payments.add_notification(db_session, user_id=1, title="Hi", message="Hello", country_code="OM")
    assert note.id is not None
    assert note.message == "Hello"


def test_flush_model(db_session):
    user = _user(db_session)
    order = _order(db_session, user)
    pay = payments.create_payment(db_session, order_id=order.id, amount=5.0, payment_method="card")
    db_session.expunge(pay)
    res = payments.flush_model(db_session, pay)
    assert res is pay


def test_invoice_create_with_items(db_session):
    user = _user(db_session)
    order = _order(db_session, user)
    inv = invoice.create_invoice_with_items(
        db_session,
        order_id=order.id,
        items=[{"description": "Widget", "unit_price": 10.0, "quantity": 2}],
        country_code="OM",
    )
    assert inv.id is not None
    assert inv.subtotal is not None
    assert len(inv.items) == 1
    updated = invoice.update_invoice(db_session, inv.id, status="paid")
    assert updated.status == "paid"


def test_invoice_create_controller_call_shape(db_session):
    """Mirrors the positional call ``invoice_controller`` makes:
    ``create_invoice_with_items(db, invoice_data, items_data)``."""
    user = _user(db_session)
    order = _order(db_session, user)
    invoice_data = {
        "order_id": order.id,
        "invoice_type": "sale",
        "currency": "OMR",
        "country_code": "OM",
        "notes": "controller-shape",
    }
    items_data = [
        {
            "description": "Gadget",
            "unit_price": 20.0,
            "quantity": 3,
            "tax_rate": 5.0,
            "discount_amount": 0,
        }
    ]
    inv = invoice.create_invoice_with_items(db_session, invoice_data, items_data)
    assert inv.id is not None
    assert inv.order_id == order.id
    assert len(inv.items) == 1
    assert inv.items[0].quantity == 3


def test_commission_update_positional_call_shape(db_session):
    """Mirrors the positional call in ``commission_controller``:
    ``update_commission_category_rate(db, row, updates)``."""
    row = CommissionCategoryRate(category_slug="books", rate_percent=2.5)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    updated = commission.update_commission_category_rate(db_session, row, {"rate_percent": 4.0, "is_active": False})
    assert updated.id == row.id
    assert updated.rate_percent == 4.0
    assert updated.is_active is False

    # Also accept an integer id in the first positional slot.
    again = commission.update_commission_category_rate(db_session, row.id, {"is_active": True})
    assert again.is_active is True
