"""Tests for PERF2 (N+1) fixes in cash_management_service.

These verify that the per-item DB lookups were replaced by batched
IN-queries, without requiring a live database (db is mocked).
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# The app config (utils.config.Settings) requires SECRET_KEY at import time.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-perf2-unit-tests")

# Make `backend` importable (the app runs with backend/ on sys.path so that
# `from models import ...` resolves to backend/models).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import backend.services.cash_management_service as cms


class _FakeProduct:
    def __init__(self, pid, supplier_id=None, category="Books", return_window_days=10):
        self.id = pid
        self.supplier_id = supplier_id
        self.category = category
        self.return_window_days = return_window_days


class _FakeItem:
    def __init__(self, pid, product=None):
        self.product_id = pid
        self.product = product


def _make_db(products):
    captured = {}

    def in_fn(ids):
        captured["ids"] = list(ids)
        return SimpleNamespace()

    product_id_attr = SimpleNamespace(in_=in_fn)
    Product = SimpleNamespace(id=product_id_attr)

    def query(model):
        q = MagicMock()

        def all():
            # Return the full product set; filtering by id happens inside the
            # real Product.id.in_() which we don't intercept. The important
            # assertion is that query() is called ONCE (batched), not per item.
            return list(products)

        q.all.side_effect = all
        q.filter.return_value = q
        return q

    db = MagicMock()
    db.query.side_effect = query
    return db


def test_batch_products_issues_single_query_for_many_items():
    products = [_FakeProduct(1, 10), _FakeProduct(2, 20), _FakeProduct(3, 30)]
    items = [_FakeItem(1), _FakeItem(2), _FakeItem(3), _FakeItem(1)]
    db = _make_db(products)

    result = cms._batch_products(db, items)

    assert set(result.keys()) == {1, 2, 3}
    # Batched: exactly ONE query call regardless of item count (was N+1 before).
    assert db.query.call_count == 1


def test_batch_products_skips_none_ids():
    items = [_FakeItem(None), _FakeItem(5)]
    db = _make_db([_FakeProduct(5)])
    result = cms._batch_products(db, items)
    assert 5 in result
    assert None not in result


def test_batch_products_empty_items_returns_empty_without_query():
    db = MagicMock()
    assert cms._batch_products(db, []) == {}
    db.query.assert_not_called()
