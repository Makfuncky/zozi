"""Paired test for FILE-9 trading_service: Decimal precision + savepoint atomicity.

Laws: 19 (Decimal money arithmetic, never float), 50 (explicit txn / savepoint).
Raw style: uses a FakeSession (no DB) so precision + rollback logic is tested
without fixture masking.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
os.environ.setdefault("APP_ENV", "test")

from domains.finance.services import trading_service


class _Stub:
    """Lightweight ORM stub — avoids configuring the repo-wide mapper
    registry (which has a pre-existing broken DocumentVerification
    relationship unrelated to FILE-9). Tests Law 19/50 logic only."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        if not hasattr(self, "id"):
            self.id = None


def _install_stubs(monkeypatch=None) -> None:
    import sys as _sys

    po_mod = _sys.modules.get("domains.logistics.models.erp")
    for cls_name in (
        "PurchaseOrder",
        "PurchaseOrderLine",
        "SalesOrder",
        "SalesOrderLine",
    ):
        stub = type(cls_name + "Stub", (_Stub,), {})
        stub.__name__ = cls_name
        if po_mod is not None:
            try:
                monkeypatch.setattr(po_mod, cls_name, stub) if monkeypatch else setattr(
                    po_mod, cls_name, stub
                )
            except Exception:
                pass
    # trading_service captured PurchaseOrder/SalesOrder at import time
    if monkeypatch is not None:
        monkeypatch.setattr(
            trading_service, "PurchaseOrder", _sys.modules["domains.logistics.models.erp"].PurchaseOrder
        )
        monkeypatch.setattr(
            trading_service, "SalesOrder", _sys.modules["domains.logistics.models.erp"].SalesOrder
        )
    else:
        trading_service.PurchaseOrder = _sys.modules["domains.logistics.models.erp"].PurchaseOrder
        trading_service.SalesOrder = _sys.modules["domains.logistics.models.erp"].SalesOrder


class FakeSession:
    """Minimal Session stub supporting savepoint protocol."""

    def __init__(self, fail_on_add: int | None = None):
        self.added: list = []
        self.committed = False
        self.rolled_back = False
        self.savepoint_entered = False
        self._add_count = 0
        self.fail_on_add = fail_on_add

    def add(self, obj) -> None:
        self._add_count += 1
        if self.fail_on_add is not None and self._add_count == self.fail_on_add:
            raise RuntimeError("forced line failure")
        if getattr(obj, "id", None) is None and self._add_count == 1:
            obj.id = 999
        self.added.append(obj)

    def flush(self) -> None:
        for o in self.added:
            if getattr(o, "id", None) is None:
                o.id = 999

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, obj) -> None:
        pass

    @contextmanager
    def begin_nested(self):
        self.savepoint_entered = True
        yield


def test_po_line_total_decimal_precision(monkeypatch) -> None:
    _install_stubs(monkeypatch)
    db = FakeSession()
    lines = [
        {"quantity_ordered": 3, "unit_price": 0.1},
        {"quantity_ordered": "2.5", "unit_price": "19.99"},
    ]
    trading_service.create_purchase_order(db, supplier_id=7, lines=lines)
    assert db.savepoint_entered is True
    assert db.committed is True and db.rolled_back is False
    po = db.added[0]
    # 3*0.1=0.3 exact; 2.5*19.99=49.975; total=50.275
    assert po.subtotal == Decimal("50.275")
    assert po.grand_total == Decimal("50.275")
    assert isinstance(po.subtotal, Decimal)
    line_totals = [o.line_total for o in db.added[1:]]
    assert line_totals[0] == Decimal("0.3")
    assert line_totals[1] == Decimal("49.975")
    assert all(isinstance(v, Decimal) for v in line_totals)
    # float would give 0.30000000000000004 — guard against regression
    assert line_totals[0] != float(3) * float(0.1) or line_totals[0] == Decimal("0.3")


def test_so_line_total_decimal_precision(monkeypatch) -> None:
    _install_stubs(monkeypatch)
    db = FakeSession()
    lines = [{"quantity_ordered": 3, "unit_price": 0.1}]
    trading_service.create_sales_order(db, customer_id=9, lines=lines)
    assert db.savepoint_entered is True
    so = db.added[0]
    assert so.grand_total == Decimal("0.3")
    assert isinstance(so.grand_total, Decimal)
    assert db.added[1].line_total == Decimal("0.3")


def test_po_atomic_rollback_on_line_failure(monkeypatch) -> None:
    _install_stubs(monkeypatch)
    # PO add=1, line1 add=2, line2 add=3 -> fail on 3
    db = FakeSession(fail_on_add=3)
    lines = [
        {"quantity_ordered": 1, "unit_price": "10.00"},
        {"quantity_ordered": 2, "unit_price": "5.00"},
    ]
    try:
        trading_service.create_purchase_order(db, supplier_id=7, lines=lines)
        raise AssertionError("expected forced failure to propagate")
    except RuntimeError as exc:
        assert "forced line failure" in str(exc)
    # No swallow, explicit rollback, no commit -> no orphans
    assert db.rolled_back is True
    assert db.committed is False
    assert db.savepoint_entered is True


def test_so_atomic_rollback_on_line_failure(monkeypatch) -> None:
    _install_stubs(monkeypatch)
    db = FakeSession(fail_on_add=3)
    lines = [
        {"quantity_ordered": 1, "unit_price": "10.00"},
        {"quantity_ordered": 2, "unit_price": "5.00"},
    ]
    try:
        trading_service.create_sales_order(db, customer_id=9, lines=lines)
        raise AssertionError("expected forced failure to propagate")
    except RuntimeError as exc:
        assert "forced line failure" in str(exc)
    assert db.rolled_back is True
    assert db.committed is False
    assert db.savepoint_entered is True


def test_no_float_line_arithmetic_in_source() -> None:
    src = Path(trading_service.__file__).read_text(encoding="utf-8")
    assert "float(line.get(\"quantity_ordered\"" not in src
    assert "float(line.get(\"unit_price\"" not in src
    assert "Decimal(str(line.get(\"quantity_ordered\"" in src
    assert "begin_nested()" in src
