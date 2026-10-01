"""Verification for the orders-module DBA06 rescue.

DBA06 flags cross-schema foreign keys (a ``ForeignKey`` whose target lives in a
different database schema than the declaring table).  The orders models live in
the ``commerce`` schema, so any FK pointing at ``core.*``, ``finance.*``,
``logistics.*``, ``country.*``, etc. is a cross-schema FK and must be removed.

This test asserts that the orders models no longer declare any cross-schema FK
constraint while keeping the integer ID columns (application-side integrity) and
that the ORM registry still configures (relationships use explicit primaryjoin).
"""
from __future__ import annotations

import models.orders.orders as orders_mod
from db.base import Base
from sqlalchemy.orm import configure_mappers

# Schemas that are NOT the orders schema.  Any FK target in one of these is a
# cross-schema (DBA06) violation.
_CROSS_SCHEMA_PREFIXES = (
    "core.", "finance.", "logistics.", "country.", "hr.", "security.",
    "treasury.", "supplier.", "customer.", "audit.", "communication.",
    "ai.", "analytics.", "configuration.", "trading.",
)

_ORDERS_TABLES = {
    "orders", "order_items", "order_logistics_allocations",
    "return_requests", "order_notifications",
}


def _table(name: str):
    for t in Base.metadata.tables.values():
        if t.name == name:
            return t
    raise KeyError(name)


def _collect_cross_schema_fks():
    bad = []
    for table in Base.metadata.tables.values():
        if table.name not in _ORDERS_TABLES:
            continue
        for col in table.columns:
            for fk in col.foreign_keys:
                target = fk.target_fullname
                schema = target.split(".")[0] if "." in target else None
                if schema and schema.lower() != "commerce":
                    bad.append((table.name, col.name, target))
    return bad


def test_orders_models_configure():
    # Must not raise (relationships reference non-FK integer columns via
    # explicit primaryjoin after the DBA06 fix).
    configure_mappers()
    for name in (
        "Order", "OrderItem", "OrderLogisticsAllocation",
        "ReturnRequest", "OrderNotification",
    ):
        assert hasattr(orders_mod, name), f"missing model {name}"


def test_orders_no_cross_schema_fks():
    bad = _collect_cross_schema_fks()
    assert bad == [], f"cross-schema FKs still present in orders models: {bad}"


def test_orders_keeps_integer_id_columns():
    # Removing the FK constraint must NOT remove the integer ID columns that
    # carry the relationship data (application-side referential integrity).
    orders = _table("orders")
    for col in ("user_id", "customer_id", "invoice_id", "country_code"):
        assert col in orders.columns, f"orders missing expected column {col}"

    alloc = _table("order_logistics_allocations")
    for col in ("supplier_id", "shipment_id", "partner_id", "service_area_id"):
        assert col in alloc.columns, f"order_logistics_allocations missing {col}"
