"""Nature-specific check for FILE-8 trading-service fixes (static analysis).

Validates the four findings resolved in this session via source-code inspection:
  LOGIC-001   — no float() casts for monetary values (Law 19)
  LOGIC-015   — receive_purchase_order wraps line insertions in begin_nested (Law 50)
  PERF-010..013 — list endpoints use keyset pagination, not .offset().limit() (Law 46)
  PERF-027    — queries use explicit column selection (Law 46)
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend"
    / "domains"
    / "finance"
    / "services"
    / "trading_service.py"
)


def _read_src() -> str:
    return SERVICE_PATH.read_text(encoding="utf-8")


def _get_function_body(src: str, func_name: str) -> str:
    """Return the source of the named function (or '' if not found)."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.get_source_segment(src, node) or ""
    return ""


# ===========================================================================
# LOGIC-001: No float() casts for monetary values (Law 19)
# ===========================================================================

def test_no_float_grand_total_in_create_purchase_order():
    src = _read_src()
    assert "float(po.grand_total)" not in src, (
        "LOGIC-001: float(po.grand_total) found — replace with str() per Law 19"
    )


def test_no_float_grand_total_in_create_sales_order():
    src = _read_src()
    assert "float(so.grand_total)" not in src, (
        "LOGIC-001: float(so.grand_total) found — replace with str() per Law 19"
    )


def test_create_purchase_order_returns_str_grand_total():
    """Outcome: grand_total is serialised as str, not float."""
    src = _read_src()
    func_body = _get_function_body(src, "create_purchase_order")
    assert 'grand_total": str(po.grand_total)' in func_body, (
        "create_purchase_order must serialise grand_total via str()"
    )


def test_create_sales_order_returns_str_grand_total():
    """Outcome: grand_total is serialised as str, not float."""
    src = _read_src()
    func_body = _get_function_body(src, "create_sales_order")
    assert 'grand_total": str(so.grand_total)' in func_body, (
        "create_sales_order must serialise grand_total via str()"
    )


# ===========================================================================
# LOGIC-015: receive_purchase_order wraps line insertions in begin_nested (Law 50)
# ===========================================================================

def test_receive_po_uses_begin_nested_for_lines():
    src = _read_src()
    func_body = _get_function_body(src, "receive_purchase_order")
    assert "with db.begin_nested():" in func_body, (
        "LOGIC-015: receive_purchase_order must wrap line insertions in "
        "db.begin_nested() (Law 50)"
    )


def test_receive_po_begin_nested_after_grn_flush():
    """The begin_nested must appear after the GRN header flush."""
    src = _read_src()
    func_body = _get_function_body(src, "receive_purchase_order")
    flush_pos = func_body.find("db.flush()")
    begin_nested_pos = func_body.find("with db.begin_nested():")
    assert begin_nested_pos > flush_pos, (
        "LOGIC-015: db.begin_nested() must appear after the GRN db.flush() "
        "in receive_purchase_order"
    )


# ===========================================================================
# PERF-010..013: List endpoints use keyset pagination (Law 46)
# ===========================================================================

def _list_funcs():
    return [
        "list_purchase_orders",
        "list_goods_receipts",
        "list_sales_orders",
        "list_stock_movements",
    ]


@pytest.mark.parametrize("func_name", _list_funcs())
def test_no_offset_limit_in_list_functions(func_name):
    """Each list function must not use .offset(offset).limit(limit)."""
    src = _read_src()
    func_body = _get_function_body(src, func_name)
    assert ".offset(offset).limit(limit)" not in func_body, (
        f"PERF: {func_name} still uses .offset().limit() — "
        "migrate to keyset_offset_window"
    )


def test_keyset_offset_window_import_present():
    """The service must import keyset_offset_window from the pagination util."""
    src = _read_src()
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "pagination" in node.module:
                for alias in node.names:
                    if alias.name == "keyset_offset_window":
                        found = True
    assert found, (
        "keyset_offset_window must be imported from infrastructure.utils.pagination"
    )


def test_keyset_offset_window_called_in_list_functions():
    """Each list function must call keyset_offset_window."""
    src = _read_src()
    for func_name in _list_funcs():
        func_body = _get_function_body(src, func_name)
        assert "keyset_offset_window(" in func_body, (
            f"{func_name} must call keyset_offset_window"
        )


# ===========================================================================
# PERF-027: Explicit column selection (Law 46)
# ===========================================================================

_EXPLICIT_COL_CONSTANTS = ["_PO_COLS", "_GRN_COLS", "_SO_COLS", "_SM_COLS", "_WH_COLS"]


def test_explicit_column_constants_defined():
    src = _read_src()
    for const in _EXPLICIT_COL_CONSTANTS:
        assert const in src, f"Missing explicit column constant: {const}"


def test_no_bare_query_in_list_purchase_orders():
    src = _read_src()
    func_body = _get_function_body(src, "list_purchase_orders")
    assert "db.query(PurchaseOrder)" not in func_body, (
        "PERF-027: list_purchase_orders uses db.query(PurchaseOrder) — "
        "replace with db.query(*_PO_COLS)"
    )


def test_no_bare_query_in_list_goods_receipts():
    src = _read_src()
    func_body = _get_function_body(src, "list_goods_receipts")
    assert "db.query(GoodsReceiptNote)" not in func_body, (
        "PERF-027: list_goods_receipts uses db.query(GoodsReceiptNote) — "
        "replace with db.query(*_GRN_COLS)"
    )


def test_no_bare_query_in_list_sales_orders():
    src = _read_src()
    func_body = _get_function_body(src, "list_sales_orders")
    assert "db.query(SalesOrder)" not in func_body, (
        "PERF-027: list_sales_orders uses db.query(SalesOrder) — "
        "replace with db.query(*_SO_COLS)"
    )


def test_no_bare_query_in_list_stock_movements():
    src = _read_src()
    func_body = _get_function_body(src, "list_stock_movements")
    assert "db.query(StockMovement)" not in func_body, (
        "PERF-027: list_stock_movements uses db.query(StockMovement) — "
        "replace with db.query(*_SM_COLS)"
    )


def test_list_queries_use_explicit_column_constants():
    src = _read_src()
    assert "db.query(*_PO_COLS)" in src
    assert "db.query(*_GRN_COLS)" in src
    assert "db.query(*_SO_COLS)" in src
    assert "db.query(*_SM_COLS)" in src


# ===========================================================================
# Static source-level sanity checks (combined)
# ===========================================================================

def test_no_float_money_patterns_in_source():
    """Law 19: No float() casts for monetary values anywhere in source."""
    src = _read_src()
    assert "float(po.grand_total)" not in src
    assert "float(so.grand_total)" not in src
    assert "float(po.subtotal)" not in src
    assert "float(so.subtotal)" not in src


def test_no_offset_limit_pattern_in_source():
    """Law 46: No .offset(offset).limit(limit) anywhere in the source."""
    src = _read_src()
    assert ".offset(offset).limit(limit)" not in src, (
        "Found .offset(offset).limit(limit) in trading_service.py — "
        "all list endpoints must use keyset_offset_window"
    )
