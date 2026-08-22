"""Tests for the orders write-service façade (ORD-CONSUMER keystone).

Validates that the façade can read orders as DTOs and apply order mutations
without the caller ever touching the ORM ``Order`` object, and that the façade
stays Law-1 clean (no ``providers.*`` import).

Uses duck-typed fakes (no real ORM instances, so no mapper/DDL needed) that
provide exactly the surface the façade touches: scalar attributes for the DTO
mapper, and a ``__table__.columns`` namespace for ``update_order``'s whitelist
check.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

from domains.orders.services import orders_write_facade
from domains.orders.services.order_dtos import OrderDTO


def _columns(*keys):
    return [SimpleNamespace(key=k) for k in keys]


class FakeOrder:
    _COL_KEYS = [
        "id", "order_number", "user_id", "customer_id", "status", "payment_status",
        "payment_method", "payment_provider", "payment_intent_id", "total", "currency",
        "country_code", "paid_at", "created_at", "updated_at",
    ]

    def __init__(self):
        self.id = 1
        self.order_number = "ORD-1"
        self.user_id = 42
        self.customer_id = None
        self.status = "pending"
        self.payment_status = "pending"
        self.payment_method = "card"
        self.payment_provider = None
        self.payment_intent_id = "pi_abc"
        self.total = 10
        self.currency = "USD"
        self.country_code = "OM"
        self.paid_at = None
        self.created_at = None
        self.items = [FakeItem()]
        self.__table__ = SimpleNamespace(columns=_columns(*self._COL_KEYS))


class FakeItem:
    def __init__(self):
        self.id = 10
        self.order_id = 1
        self.product_id = 7
        self.quantity = 2
        self.unit_price = 5
        self.price = 5
        self.total_price = 10
        self.selected_size = "M"
        self.selected_color = "red"
        self.country_code = "OM"


class FakeDB:
    def __init__(self, order: FakeOrder, return_none: bool = False):
        self._order = order
        self._return_none = return_none

    def get(self, cls, pk):
        if not self._return_none and pk == self._order.id:
            return self._order
        return None

    def query(self, cls):
        return FakeQuery(self, cls)

    def commit(self):
        pass


class FakeQuery:
    def __init__(self, db: FakeDB, cls):
        self._db = db
        self._cls = cls

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        if not self._db._return_none:
            return self._db._order
        return None

    def all(self):
        if self._db._order is not None:
            return self._db._order.items
        return []


def _make_db(return_none: bool = False) -> FakeDB:
    return FakeDB(FakeOrder(), return_none=return_none)


def test_facade_is_law1_clean():
    import ast

    tree = ast.parse(inspect.getsource(orders_write_facade))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    # The façade must not reach into providers (Law 1) nor any other domain's
    # models/services; it may only import the orders domain + stdlib/sqlalchemy.
    assert not any("providers" in m for m in imported), "facade must not import providers (Law 1)"
    assert not any(
        m.startswith("domains.") and not m.startswith("domains.orders") for m in imported
    ), "facade must not import other domains (Law 1)"
    assert any(m.startswith("domains.orders") for m in imported)


def test_get_order_by_id_returns_dto():
    dto = orders_write_facade.get_order_by_id(_make_db(), 1, include_items=True)
    assert isinstance(dto, OrderDTO)
    assert dto.id == 1
    assert dto.status == "pending"
    assert dto.payment_intent_id == "pi_abc"
    assert len(dto.items) == 1
    assert dto.items[0].product_id == 7


def test_get_order_by_id_missing():
    assert orders_write_facade.get_order_by_id(_make_db(return_none=True), 999) is None


def test_get_order_by_payment_intent_id():
    assert orders_write_facade.get_order_by_payment_intent_id(_make_db(), "pi_abc").id == 1
    assert orders_write_facade.get_order_by_payment_intent_id(_make_db(return_none=True), "nope") is None


def test_apply_order_status_persists():
    db = _make_db()
    dto = orders_write_facade.apply_order_status(db, 1, "confirmed")
    assert dto.status == "confirmed"
    # update_order committed the change onto the same instance.
    assert db._order.status == "confirmed"


def test_mark_order_paid_sets_paid_at():
    db = _make_db()
    dto = orders_write_facade.mark_order_paid(db, 1)
    assert dto.paid_at is not None
    assert db._order.paid_at is not None


def test_apply_order_payment_intent():
    dto = orders_write_facade.apply_order_payment_intent(_make_db(), 1, "pi_new")
    assert dto.payment_intent_id == "pi_new"


def test_apply_order_payment_method():
    dto = orders_write_facade.apply_order_payment_method(_make_db(), 1, "cod")
    assert dto.payment_method == "cod"


def test_apply_order_fields_generic():
    dto = orders_write_facade.apply_order_fields(_make_db(), 1, status="shipped", payment_status="paid")
    assert dto.status == "shipped"
    assert dto.payment_status == "paid"


def test_get_order_items():
    items = orders_write_facade.get_order_items(_make_db(), 1)
    assert len(items) == 1 and items[0].product_id == 7
