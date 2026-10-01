"""Tests for admin_orders_status_service.

Contract: _audit/resolver/contracts/FILE-44-admin-orders-status.md
Finding fixed:
  AIDRIFT-001 — Stale TODO, misleading docstring, and direct db.query(Order)
  calls removed from service layer; functions now accept an `orders` iterable
  instead of a DB session.
"""
from __future__ import annotations

import types
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend"
    / "domains"
    / "orders"
    / "services"
    / "admin_orders_status_service.py"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_order(order_id, status_code="pending", is_deleted=False, country_code="AE"):
    """Build a minimal order-like object for unit testing."""
    order = types.SimpleNamespace()
    order.id = order_id
    order.status_code = status_code
    order.is_deleted = is_deleted
    order.country_code = country_code
    return order


def _import_service():
    """Import the service module fresh for each test."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "admin_orders_status_service", SERVICE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Static / source-level tests ───────────────────────────────────────────────

class TestSourceCleanliness:
    """Verify the source file has no stale TODO and no direct DB queries."""

    def test_no_stale_todo(self):
        source = SERVICE_PATH.read_text(encoding="utf-8")
        assert "TODO" not in source, "Stale TODO comment still present in source"

    def test_no_commented_out_import(self):
        source = SERVICE_PATH.read_text(encoding="utf-8")
        assert "# from domains.governance" not in source, \
            "Commented-out governance import still present"

    def test_docstring_not_router(self):
        source = SERVICE_PATH.read_text(encoding="utf-8")
        first_line = source.splitlines()[0].lower()
        assert "router" not in first_line, \
            f"First line still describes file as a router: {first_line!r}"

    def test_no_db_query_order_call(self):
        source = SERVICE_PATH.read_text(encoding="utf-8")
        assert "db.query(Order)" not in source, \
            "Direct db.query(Order) call still present in source"


# ── list_all_orders tests ─────────────────────────────────────────────────────

class TestListAllOrders:
    """Verify list_all_orders filters, paginates, and respects include_deleted."""

    def test_returns_all_orders_when_no_filter(self):
        svc = _import_service()
        orders = [_make_order(i) for i in range(1, 6)]
        result = svc.list_all_orders(orders=orders)
        assert result["total"] == 5
        assert len(result["items"]) == 5

    def test_filters_by_status_code(self):
        svc = _import_service()
        orders = [
            _make_order(1, status_code="pending"),
            _make_order(2, status_code="confirmed"),
            _make_order(3, status_code="pending"),
        ]
        result = svc.list_all_orders(orders=orders, status="pending")
        assert result["total"] == 2
        assert all(o.status_code == "pending" for o in result["items"])

    def test_excludes_deleted_by_default(self):
        svc = _import_service()
        orders = [
            _make_order(1, is_deleted=False),
            _make_order(2, is_deleted=True),
            _make_order(3, is_deleted=False),
        ]
        result = svc.list_all_orders(orders=orders)
        assert result["total"] == 2
        assert all(not o.is_deleted for o in result["items"])

    def test_includes_deleted_when_flag_set(self):
        svc = _import_service()
        orders = [
            _make_order(1, is_deleted=False),
            _make_order(2, is_deleted=True),
        ]
        result = svc.list_all_orders(orders=orders, include_deleted=True)
        assert result["total"] == 2

    def test_pagination_returns_correct_slice(self):
        svc = _import_service()
        orders = [_make_order(i) for i in range(1, 11)]  # 10 orders
        result = svc.list_all_orders(orders=orders, page=2, size=3)
        assert len(result["items"]) == 3
        assert result["page"] == 2
        assert result["total"] == 10
        assert result["pages"] == 4

    def test_empty_orders_returns_zero(self):
        svc = _import_service()
        result = svc.list_all_orders(orders=[])
        assert result["total"] == 0
        assert result["items"] == []
        assert result["pages"] == 1

    def test_returns_pages_one_when_total_zero(self):
        svc = _import_service()
        result = svc.list_all_orders(orders=[])
        assert result["pages"] == 1


# ── bulk_update_order_status tests ────────────────────────────────────────────

class TestBulkUpdateOrderStatus:
    """Verify bulk_update_order_status updates matching orders only."""

    def test_updates_matching_order_ids(self):
        svc = _import_service()
        orders = [_make_order(i) for i in range(1, 6)]
        result = svc.bulk_update_order_status(
            orders=orders, ids=[1, 3, 5], status="confirmed"
        )
        assert result["updated"] == 3
        assert orders[0].status_code == "confirmed"
        assert orders[2].status_code == "confirmed"
        assert orders[4].status_code == "confirmed"

    def test_skips_non_existent_ids(self):
        svc = _import_service()
        orders = [_make_order(1), _make_order(2)]
        result = svc.bulk_update_order_status(
            orders=orders, ids=[1, 99], status="shipped"
        )
        assert result["updated"] == 1
        assert orders[0].status_code == "shipped"
        assert orders[1].status_code == "pending"  # unchanged

    def test_empty_ids_returns_zero_updated(self):
        svc = _import_service()
        orders = [_make_order(1), _make_order(2)]
        result = svc.bulk_update_order_status(orders=orders, ids=[], status="cancelled")
        assert result["updated"] == 0
        assert result["message"] == "Status updated for 0 orders"

    def test_no_database_commit_called(self):
        """bulk_update_order_status must not call db.commit()."""
        svc = _import_service()
        source = SERVICE_PATH.read_text(encoding="utf-8")
        assert "db.commit()" not in source, \
            "bulk_update_order_status must not call db.commit()"

    def test_does_not_mutate_non_matching_orders(self):
        svc = _import_service()
        orders = [
            _make_order(1, status_code="pending"),
            _make_order(2, status_code="confirmed"),
        ]
        svc.bulk_update_order_status(orders=orders, ids=[1], status="cancelled")
        assert orders[1].status_code == "confirmed"  # untouched
