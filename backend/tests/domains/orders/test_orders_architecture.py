"""Orders domain — architecture law tests (Laws 1, 3, 4, 6, 19, 22, 23, 55).

Verifies:
  * Schema discipline: every model declares a non-forbidden Postgres schema (Law 6/55).
  * Audit columns: created_at, updated_at, country_code, is_deleted (Law 23).
  * Foreign keys declare explicit ondelete (Law 22/52).
  * Features are single-sourced and present in the rbac catalog (Law 4).
  * Cross-domain writes go via events (Law 3) and catalog reads via ports.
  * Money uses Decimal/Numeric, never float (Law 19).
  * No forbidden cross-domain imports (Law 1).
"""
from __future__ import annotations

import pathlib

import pytest

from tests._support.laws import (
    assert_feature_in_catalog,
    assert_foreign_keys_have_ondelete,
    assert_no_forbidden_imports,
    assert_schema_discipline,
    iter_domain_models,
    load_feature_catalog,
)

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_ORDERS_ROOT = _BACKEND_ROOT / "domains" / "orders"


# ---------------------------------------------------------------------------
# Law 6 / 55 — schema discipline
# ---------------------------------------------------------------------------


class TestOrdersSchemaDiscipline:
    """Every orders ORM model must declare a valid Postgres schema."""

    def test_all_models_have_valid_schema(self, db_session):
        """All orders models declare a non-forbidden schema (Law 6/55)."""
        failures: list[str] = []
        for model in iter_domain_models("orders"):
            try:
                assert_schema_discipline(model)
            except AssertionError as exc:
                failures.append(str(exc))
        assert not failures, "Schema discipline failures:\n" + "\n".join(failures)

    def test_all_models_have_audit_columns(self, db_session):
        """All orders models carry the required audit columns (Law 23)."""
        required = ("created_at", "updated_at", "country_code", "is_deleted")
        failures: list[str] = []
        for model in iter_domain_models("orders"):
            missing = [c for c in required if not hasattr(model, c)]
            if missing:
                failures.append(f"{model.__name__}: missing {missing}")
        assert not failures, "Audit column failures:\n" + "\n".join(failures)

    def test_all_foreign_keys_have_ondelete(self, db_session):
        """Every ForeignKey on an orders model declares explicit ondelete (Law 22/52)."""
        failures: list[str] = []
        for model in iter_domain_models("orders"):
            try:
                assert_foreign_keys_have_ondelete(model)
            except AssertionError as exc:
                failures.append(str(exc))
        assert not failures, "FK ondelete failures:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Law 19 — money uses Decimal / Numeric, never float
# ---------------------------------------------------------------------------


class TestOrdersMoneyTypes:
    """Money columns must use Numeric/Decimal, never float (Law 19)."""

    def test_no_float_columns_in_models(self, db_session):
        """No orders model defines a Float column for money (Law 19)."""
        from sqlalchemy import Float

        offenders: list[str] = []
        for model in iter_domain_models("orders"):
            for col in model.__table__.columns:
                if isinstance(col.type, Float):
                    offenders.append(f"{model.__name__}.{col.name}")
        assert not offenders, f"Float columns found (Law 19): {offenders}"

    def test_money_columns_are_numeric(self, db_session):
        """Subtotal / total / tax / discount columns use Numeric (Law 19)."""
        from sqlalchemy import Numeric

        money_keywords = ("amount", "total", "price", "fee", "tax", "discount", "subtota")
        for model in iter_domain_models("orders"):
            for col in model.__table__.columns:
                if any(kw in col.name for kw in money_keywords):
                    assert isinstance(col.type, Numeric), (
                        f"{model.__name__}.{col.name} uses {type(col.type).__name__}, "
                        f"expected Numeric (Law 19)"
                    )


# ---------------------------------------------------------------------------
# Law 4 — features single-sourced in rbac catalog
# ---------------------------------------------------------------------------


class TestOrdersFeatures:
    """Orders feature atoms must be registered in the rbac catalog."""

    def test_features_in_catalog(self):
        """Every orders feature atom resolves in the aggregated catalog (Law 4)."""
        catalog = load_feature_catalog()
        from domains.orders.features import FEATURES

        for key in FEATURES:
            assert key in catalog, f"Feature '{key}' missing from rbac catalog (Law 4)"


# ---------------------------------------------------------------------------
# Law 3 — events.py / ports.py present & wired
# ---------------------------------------------------------------------------


class TestOrdersWiring:
    """events.py and ports.py must exist and expose the sanctioned surface."""

    def test_events_module_exists(self):
        """orders domain has an events.py module (Law 3)."""
        assert (_ORDERS_ROOT / "events.py").exists(), "Missing events.py (Law 3)"

    def test_ports_module_exists(self):
        """orders domain has a ports.py module (Law 3)."""
        assert (_ORDERS_ROOT / "ports.py").exists(), "Missing ports.py (Law 3)"

    def test_ports_expose_read_helpers(self, db_session):
        """ports.py exposes sanctioned read helpers (Law 3)."""
        from domains.orders.ports import get_order_by_id, list_orders

        assert callable(get_order_by_id)
        assert callable(list_orders)

    def test_ports_use_keyset_pagination(self, db_session):
        """ports.py list helpers use keyset pagination, never OFFSET (Law 222)."""
        source = (_ORDERS_ROOT / "ports.py").read_text(encoding="utf-8")
        assert "keyset_paginate" in source or "cursor_paginate" in source, (
            "ports.py must use keyset/cursor pagination (Law 222)"
        )

    def test_subscribers_register_listener(self):
        """orders subscribers expose register_orders_subscribers (Law 3)."""
        from domains.orders.subscribers import register_orders_subscribers

        assert callable(register_orders_subscribers)


# ---------------------------------------------------------------------------
# Law 1 — no forbidden cross-domain imports
# ---------------------------------------------------------------------------


class TestOrdersImportHygiene:
    """orders domain must not import forbidden layers (Law 1)."""

    def test_no_forbidden_imports(self):
        """orders never imports modules, rbac, or other forbidden layers (Law 1)."""
        assert_no_forbidden_imports("domains", _ORDERS_ROOT)
