"""ORD-CONSUMER payment-flow regression harness.

Locks the behaviour of the sanctioned orders write surface
(``domains.orders.services.orders_write_facade``) and of the payment
confirmation funnel (``providers.payments._order._apply_successful_payment``)
so the ORD-CONSUMER rewire -- routing every in-provider ``setattr(order, …)``
through the façade -- cannot silently regress.

Run from the backend package root::

    python -m pytest tests/test_orders_payment_flow.py -q
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text

from domains.orders.ports import Order, OrderItem
from domains.finance.models.payments import Payment


def _make_order(db, **kw) -> Order:
    order = Order(
        user_id=1,
        status="pending",
        payment_method="card",
        total_amount=Decimal("10.00"),
        **kw,
    )
    db.add(order)
    db.flush()
    return order


def test_facade_writes_persist(db_session) -> None:
    """Every façade writer must round-trip to the database."""
    from domains.orders.services import orders_write_facade as owf

    order = _make_order(db_session, payment_intent_id="pi_abc")
    db_session.flush()

    dto = owf.get_order_by_payment_intent_id(db_session, "pi_abc")
    assert dto is not None
    oid = dto.id

    # Items surface
    db_session.add(
        OrderItem(order_id=oid, product_id=1, quantity=1, unit_price=Decimal("5"))
    )
    db_session.flush()
    assert len(owf.get_order_items(db_session, oid)) == 1

    # Status
    owf.apply_order_status(db_session, oid, "confirmed")
    assert owf.get_order_by_id(db_session, oid).status == "confirmed"

    # Paid
    owf.mark_order_paid(db_session, oid)
    assert owf.get_order_by_id(db_session, oid).paid_at is not None

    # Payment intent reference
    owf.apply_order_payment_intent(db_session, oid, "pi_xyz")
    assert owf.get_order_by_payment_intent_id(db_session, "pi_xyz").id == oid

    # Payment method
    owf.apply_order_payment_method(db_session, oid, "visa")
    assert owf.get_order_by_id(db_session, oid).payment_method == "visa"

    # Arbitrary whitelisted fields
    owf.apply_order_fields(db_session, oid, payment_status="approved")
    assert owf.get_order_by_id(db_session, oid).payment_status == "approved"


def test_apply_successful_payment_funnel(db_session, monkeypatch) -> None:
    """Successful-payment confirmation must confirm + pay the order and flip
    the matching Payment row to ``completed`` -- the observable contract that
    the ORD-CONSUMER rewire must preserve."""
    from domains.orders.services import orders_write_facade as owf
    from providers.payments import _order as _ord

    # Isolate from any real broker / subscriber side-effects.
    monkeypatch.setattr(_ord._event_publisher, "publish", lambda *a, **k: None)

    order = _make_order(db_session, payment_intent_id="pi_test")
    db_session.flush()
    # ``currency_code`` is not a mapped column but is read on the publisher path;
    # set it as a plain instance attribute so that read does not raise.
    order.currency_code = "AED"
    db_session.flush()

    db_session.add(
        Payment(
            order_id=order.id,
            provider="card",
            status="pending",
            amount=Decimal("10.00"),
            payment_method="card",
        )
    )
    db_session.flush()

    _ord._apply_successful_payment(order, "Order payment confirmed", db_session)

    dto = owf.get_order_by_id(db_session, order.id)
    assert dto.status == "confirmed"
    assert dto.paid_at is not None

    paid = (
        db_session.query(Payment)
        .filter(Payment.order_id == order.id, Payment.provider == "card")
        .first()
    )
    assert paid is not None
    assert paid.status == "completed"
