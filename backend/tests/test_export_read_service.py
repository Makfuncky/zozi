"""Regression tests for ``services.core.export_read_service``.

These guard the HL502 fix: the module previously used a star import
(``from data.models import *``) that relied on a non-existent ``Unknown``
model and an undefined ``MAX_EXPORT_ROWS``.  The import is now explicit and
``get_unknown_scalar`` (dead code referencing the undefined ``Unknown``) is
removed.
"""
from __future__ import annotations

import pathlib

import pytest

import services.core.export_read_service as ers

_SOURCE = pathlib.Path(ers.__file__).read_text(encoding="utf-8")


def test_no_star_import():
    """HL502: the functional service must not use a wildcard import."""
    assert "from data.models import *" not in _SOURCE
    assert "import *" not in _SOURCE


def test_explicit_symbols_resolve():
    """The model symbols used by the module are importable explicitly."""
    for name in ("User", "Order", "Product", "Coupon", "AuditLog"):
        assert hasattr(ers, name), f"{name} should be explicitly imported"
    assert ers.MAX_EXPORT_ROWS == 5000


def test_dead_unknown_scalar_removed():
    """The dead function referencing the undefined ``Unknown`` model is gone."""
    assert not hasattr(ers, "get_unknown_scalar")


def test_list_and_count_on_empty_db(db_session):
    """Read helpers return sane values against an empty database."""
    assert ers.list_user(db_session) == []
    assert ers.list_order(db_session) == []
    assert ers.list_product(db_session) == []
    assert ers.list_coupon(db_session) == []
    assert ers.get_user_first(db_session) is None
    assert ers.count_user(db_session) == 0
    assert ers.count_order(db_session) == 0
    assert ers.count_product(db_session) == 0
    assert ers.count_coupon(db_session) == 0


def test_export_capped_query_returns_query(db_session):
    """Capped export helpers execute without NameError on MAX_EXPORT_ROWS."""
    assert ers.db_user_all_0(db_session) == []
    assert ers.db_order_all_1(db_session) == []
    assert ers.db_product_all_2(db_session) == []
    assert ers.db_coupon_all_3(db_session) == []
    # Query builders return a SQLAlchemy Query, not a materialised list.
    assert ers.db_auditlog_query_4(db_session) is not None
    assert ers.db_user_query_5(db_session) is not None
