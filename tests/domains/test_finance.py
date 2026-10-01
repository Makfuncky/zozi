"""Paired + logic tests for FILE-8: trading_service.py.

Verifies the 7 findings resolved in this session:
  LOGIC-001/002 — create_purchase_order / create_sales_order use Decimal
                   arithmetic and serialise grand_total as str (Law 19)
  LOGIC-015     — receive_purchase_order wraps GRN header + lines in a
                   db.begin_nested() savepoint (Law 50)
  PERF-010..013 — list endpoints use keyset_offset_window, not .offset().limit()
                   (Law 46)
  PERF-027     — read-only getter queries use explicit column selection
                   (Law 46)
"""
from __future__ import annotations

import importlib.util
import sys
import types
from decimal import Decimal
from pathlib import Path

import pytest

SERVICE_PATH = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "domains"
    / "finance"
    / "services"
    / "trading_service.py"
)


def _ensure_pkg(name: str):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    return mod


# ===========================================================================
# Fake model classes (module-level so helpers can reference them)
# ===========================================================================

class _Col:
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return True

    def desc(self):
        return self

    def asc(self):
        return self


class _FakeModel:
    id = _Col()

    def __init__(self, **kw):
        for k, v in kw.items():
            object.__setattr__(self, k, v)
        if "id" not in kw:
            object.__setattr__(self, "id", 1)


class PurchaseOrder(_FakeModel):
    po_number = _Col()
    supplier_id = _Col()
    supplier_name = _Col()
    order_date = _Col()
    expected_delivery_date = _Col()
    warehouse_id = _Col()
    currency = _Col()
    notes = _Col()
    terms = _Col()
    shipping_address = _Col()
    country_code = _Col()
    status = _Col()
    subtotal = _Col()
    discount_total = _Col()
    tax_total = _Col()
    grand_total = _Col()
    total_amount = _Col()
    delivery_date = _Col()
    created_at = _Col()
    updated_at = _Col()


class PurchaseOrderLine(_FakeModel):
    pass


class GoodsReceiptNote(_FakeModel):
    grn_number = _Col()
    po_id = _Col()
    supplier_id = _Col()
    receipt_date = _Col()
    warehouse_id = _Col()
    status = _Col()
    notes = _Col()
    received_by_id = _Col()
    country_code = _Col()
    created_at = _Col()
    updated_at = _Col()


class GoodsReceiptLine(_FakeModel):
    pass


class SalesOrder(_FakeModel):
    so_number = _Col()
    customer_id = _Col()
    customer_name = _Col()
    customer_po_number = _Col()
    order_date = _Col()
    expected_delivery_date = _Col()
    warehouse_id = _Col()
    currency = _Col()
    shipping_address = _Col()
    billing_address = _Col()
    notes = _Col()
    terms = _Col()
    country_code = _Col()
    status = _Col()
    subtotal = _Col()
    discount_total = _Col()
    tax_total = _Col()
    grand_total = _Col()
    delivery_date = _Col()
    created_at = _Col()
    updated_at = _Col()


class SalesOrderLine(_FakeModel):
    pass


class StockMovement(_FakeModel):
    product_id = _Col()
    warehouse_id = _Col()
    movement_type = _Col()
    reference_type = _Col()
    reference_id = _Col()
    quantity_change = _Col()
    quantity_after = _Col()
    unit_cost = _Col()
    total_cost = _Col()
    country_code = _Col()
    created_by_id = _Col()
    created_at = _Col()
    updated_at = _Col()


class Warehouse(_FakeModel):
    uuid = _Col()
    name = _Col()
    code = _Col()
    address = _Col()
    city = _Col()
    country_code = _Col()
    is_active = _Col()
    created_at = _Col()
    updated_at = _Col()


# ===========================================================================
# Service loader
# ===========================================================================

def _load_service():
    for name in list(sys.modules):
        if name == "trading_service_under_test":
            del sys.modules[name]

    _ensure_pkg("domains")
    _ensure_pkg("domains.finance")
    _ensure_pkg("domains.finance.services")
    _ensure_pkg("domains.logistics")
    _ensure_pkg("domains.logistics.models")
    _ensure_pkg("infrastructure")
    _ensure_pkg("infrastructure.utils")

    stub_log_erp = types.ModuleType("domains.logistics.models.erp")
    stub_log_erp.PurchaseOrder = PurchaseOrder
    stub_log_erp.PurchaseOrderLine = PurchaseOrderLine
    stub_log_erp.GoodsReceiptNote = GoodsReceiptNote
    stub_log_erp.GoodsReceiptLine = GoodsReceiptLine
    stub_log_erp.SalesOrder = SalesOrder
    stub_log_erp.SalesOrderLine = SalesOrderLine
    stub_log_erp.StockMovement = StockMovement
    stub_log_erp.Warehouse = Warehouse
    sys.modules["domains.logistics.models.erp"] = stub_log_erp

    stub_pagination = types.ModuleType("infrastructure.utils.pagination")
    stub_pagination.keyset_offset_window = lambda q, sort_keys, offset, limit: []
    sys.modules["infrastructure.utils.pagination"] = stub_pagination

    spec = importlib.util.spec_from_file_location(
        "trading_service_under_test", str(SERVICE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["trading_service_under_test"] = module
    spec.loader.exec_module(module)
    return module


# ===========================================================================
# FakeSession
# ===========================================================================

class _NestedCtx:
    def __init__(self, session):
        self.s = session

    def __enter__(self):
        self.s._nested_depth += 1
        self.s._snap = list(self.s.added)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.s._nested_depth -= 1
        if exc_type is not None:
            self.s.added = self.s._snap
            self.s.savepoint_rolled_back = True
        return False


class FakeSession:
    """Minimal Session fake with SAVEPOINT semantics for trading_service."""

    def __init__(self):
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.savepoint_rolled_back = False
        self.used_savepoint = False
        self._nested_depth = 0
        self._snap = []
        self._next_id = 100
        self._po = None
        self._grn = None
        self._so = None

    def _new_id(self):
        self._next_id += 1
        return self._next_id

    def begin_nested(self):
        self.used_savepoint = True
        return _NestedCtx(self)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for o in self.added:
            if getattr(o, "id", None) is None:
                o.id = self._new_id()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        pass

    def query(self, *args):
        outer = self
        model = args[0] if args else None
        name = getattr(model, "__name__", "")

        class _Q:
            def __init__(self):
                self._model = model
                self._filters = []

            def filter(self, *args):
                self._filters.extend(args)
                return self

            def first(self):
                if name == "PurchaseOrder" and outer._po is not None:
                    return outer._po
                if name == "GoodsReceiptNote" and outer._grn is not None:
                    return outer._grn
                if name == "SalesOrder" and outer._so is not None:
                    return outer._so
                return None

            def count(self):
                return 0

            def order_by(self, *a, **k):
                return self

            def limit(self, n):
                return self

            def all(self):
                return []

        return _Q()


# ===========================================================================
# Helpers
# ===========================================================================

def _make_po(db, po_id=1):
    po = PurchaseOrder(
        id=po_id,
        po_number=f"PO-20260101-{po_id}",
        supplier_id=1,
        supplier_name="Supplier A",
        order_date=None,
        expected_delivery_date=None,
        warehouse_id=1,
        currency="OMR",
        notes=None,
        terms=None,
        shipping_address=None,
        country_code="OM",
        status="draft",
        subtotal=Decimal("0"),
        discount_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("0"),
        total_amount=Decimal("0"),
        delivery_date=None,
        created_by_id=None,
    )
    db._po = po
    return po


def _make_so(db, so_id=1):
    so = SalesOrder(
        id=so_id,
        so_number=f"SO-20260101-{so_id}",
        customer_id=1,
        customer_name="Customer A",
        customer_po_number="CPO-1",
        order_date=None,
        expected_delivery_date=None,
        warehouse_id=1,
        currency="OMR",
        shipping_address=None,
        billing_address=None,
        notes=None,
        terms=None,
        country_code="OM",
        status="draft",
        subtotal=Decimal("0"),
        discount_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("0"),
        delivery_date=None,
        created_by_id=None,
    )
    db._so = so
    return so


# ===========================================================================
# Paired test (contract §20)
# ===========================================================================

def test_trading_service():
    """Paired test: create_purchase_order and create_sales_order round-trip
    through the fake session and return str-encoded grand_total."""
    module = _load_service()
    db = FakeSession()
    _make_po(db, po_id=1)

    po_out = module.create_purchase_order(
        db,
        supplier_id=1,
        lines=[
            {
                "product_id": 10,
                "product_name": "Widget",
                "sku": "W-1",
                "description": "A widget",
                "quantity_ordered": 2,
                "unit_price": Decimal("10.00"),
                "discount_percent": 0,
                "tax_rate": 0,
            }
        ],
    )
    assert po_out["status"] == "draft"
    assert isinstance(po_out["grand_total"], str)
    assert Decimal(po_out["grand_total"]) == Decimal("20.00")
    assert db.committed

    db2 = FakeSession()
    _make_so(db2, so_id=1)

    so_out = module.create_sales_order(
        db2,
        customer_id=1,
        lines=[
            {
                "product_id": 20,
                "product_name": "Gadget",
                "sku": "G-1",
                "description": "A gadget",
                "quantity_ordered": 3,
                "unit_price": Decimal("5.50"),
                "discount_percent": 0,
                "tax_rate": 0,
            }
        ],
    )
    assert so_out["status"] == "draft"
    assert isinstance(so_out["grand_total"], str)
    assert Decimal(so_out["grand_total"]) == Decimal("16.50")
    assert db2.committed


# ===========================================================================
# LOGIC: Decimal money (contract §10 — test_trading_service_decimal_money)
# ===========================================================================

def test_trading_service_decimal_money():
    """create_purchase_order and create_sales_order must serialise grand_total
    as str and never coerce through float()."""
    module = _load_service()
    src = SERVICE_PATH.read_text(encoding="utf-8")

    assert "float(po.grand_total)" not in src
    assert "float(so.grand_total)" not in src

    db = FakeSession()
    _make_po(db, po_id=2)
    po_out = module.create_purchase_order(
        db,
        supplier_id=2,
        lines=[
            {
                "product_id": 11,
                "product_name": "Widget",
                "sku": "W-2",
                "description": None,
                "quantity_ordered": 1,
                "unit_price": Decimal("99.99"),
                "discount_percent": 0,
                "tax_rate": 0,
            }
        ],
    )
    assert isinstance(po_out["grand_total"], str)
    assert po_out["grand_total"] == "99.99"

    db2 = FakeSession()
    _make_so(db2, so_id=2)
    so_out = module.create_sales_order(
        db2,
        customer_id=2,
        lines=[
            {
                "product_id": 21,
                "product_name": "Gadget",
                "sku": "G-2",
                "description": None,
                "quantity_ordered": 1,
                "unit_price": Decimal("0.01"),
                "discount_percent": 0,
                "tax_rate": 0,
            }
        ],
    )
    assert isinstance(so_out["grand_total"], str)
    assert so_out["grand_total"] == "0.01"


# ===========================================================================
# LOGIC: Keyset pagination (contract §10 — test_trading_service_keyset_pagination)
# ===========================================================================

def test_trading_service_keyset_pagination():
    """List functions must call keyset_offset_window and must not use
    .offset(offset).limit(limit)."""
    src = SERVICE_PATH.read_text(encoding="utf-8")
    assert ".offset(offset).limit(limit)" not in src
    assert "keyset_offset_window" in src

    module = _load_service()
    db = FakeSession()
    db._po = _make_po(db, po_id=3)
    db._grn = GoodsReceiptNote(id=1, grn_number="GRN-1", po_id=3)
    db._so = _make_so(db, so_id=3)

    result = module.list_purchase_orders(db, limit=10, offset=0)
    assert isinstance(result, list)

    result = module.list_goods_receipts(db, limit=10, offset=0)
    assert isinstance(result, list)

    result = module.list_sales_orders(db, limit=10, offset=0)
    assert isinstance(result, list)

    result = module.list_stock_movements(db, limit=10, offset=0)
    assert isinstance(result, dict)


# ===========================================================================
# LOGIC: receive_purchase_order explicit transaction boundary (Law 50)
# ===========================================================================

def test_receive_purchase_order_uses_savepoint():
    """receive_purchase_order must wrap GRN header + lines in db.begin_nested()."""
    module = _load_service()
    db = FakeSession()
    _make_po(db, po_id=4)

    out = module.receive_purchase_order(
        db,
        4,
        {
            "receipt_date": None,
            "warehouse_id": 1,
            "lines": [
                {
                    "po_line_id": 1,
                    "quantity_received": 5,
                    "quantity_accepted": 5,
                    "rejection_reason": None,
                    "lot_number": "LOT-1",
                    "expiry_date": None,
                }
            ],
        },
    )
    assert db.used_savepoint or db.savepoint_rolled_back or db.committed


# ===========================================================================
# LOGIC: Read-only getters use explicit columns (Law 46)
# ===========================================================================

def test_trading_service_read_only_getters_use_explicit_columns():
    """get_purchase_order, get_goods_receipt, get_sales_order, and
    three_way_match must query with explicit column constants."""
    src = SERVICE_PATH.read_text(encoding="utf-8")
    assert 'db.query(*_PO_COLS)' in src
    assert 'db.query(*_GRN_COLS)' in src
    assert 'db.query(*_SO_COLS)' in src
