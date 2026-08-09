"""Regression tests for the Orders module fixes.

Verifies:
  1. DB31 fix - composite (country_code, created_at) index exists on
     `commerce.orders` (tenant time-series queries).
  2. OB101 fix - Orders service modules carry a structured logger
     (`logging.getLogger(__name__)`).

Run:  python tests/test_orders_module_fixes.py
"""
import os
import sys
import glob

ZOZI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ZOZI, "backend")
sys.path.insert(0, BACKEND)

os.environ.setdefault("SECRET_KEY", "test-key")
os.environ["APP_ENV"] = "test"
os.environ["CSRF_DISABLED"] = "true"


def test_orders_composite_index():
    from models.orders.orders import Order
    t = Order.__table__
    cols = {c.name for c in t.columns}
    assert "country_code" in cols, "orders.country_code missing"
    assert "created_at" in cols, "orders.created_at missing"
    composite = any(
        set(i.columns.keys()) == {"country_code", "created_at"}
        for i in t.indexes
    )
    assert composite, (
        "commerce.orders missing composite index (country_code, created_at); "
        f"have indexes {[i.name for i in t.indexes]}"
    )


def test_orders_service_modules_have_logger():
    orders_dir = os.path.join(BACKEND, "services", "orders")
    files = [
        p for p in glob.glob(os.path.join(orders_dir, "*.py"))
        if os.path.basename(p) != "__init__.py"
    ]
    assert files, "no Orders service modules found"
    missing = []
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            if "getLogger" not in fh.read():
                missing.append(os.path.basename(path))
    assert not missing, f"Orders service modules missing structured logger: {missing}"


def _column_indexed(table, column):
    if column.index:
        return True
    return any(column.name in idx.columns for idx in table.indexes)


def test_return_deadline_renamed():
    """DB11 — datetime column must follow *_at convention."""
    from models.orders.orders import ReturnRequest
    cols = {c.name for c in ReturnRequest.__table__.columns}
    assert "return_deadline_at" in cols, "return_deadline_at column missing"
    assert "return_deadline" not in cols, "legacy return_deadline column still present"


def test_orders_fk_explicit_ondelete():
    """DB07 — every FK on Orders tables must declare an ON DELETE rule."""
    from models.orders.orders import (
        Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification,
    )
    for model in (Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification):
        for fk in model.__table__.foreign_keys:
            assert fk.ondelete is not None, (
                f"{model.__tablename__}.{fk.parent.name} FK missing explicit ondelete rule"
            )


def test_orders_fk_columns_indexed():
    """DB08 — every FK column on Orders tables must be indexed."""
    from models.orders.orders import (
        Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification,
    )
    for model in (Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification):
        t = model.__table__
        for fk in t.foreign_keys:
            col = fk.parent
            assert _column_indexed(t, col), (
                f"{t.name}.{col.name} FK column is not indexed"
            )


if __name__ == "__main__":
    import traceback
    failures = 0
    for fn in (
        test_orders_composite_index,
        test_orders_service_modules_have_logger,
        test_return_deadline_renamed,
        test_orders_fk_explicit_ondelete,
        test_orders_fk_columns_indexed,
    ):
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"FAIL {fn.__name__}: {e}")
            traceback.print_exc()
    sys.exit(1 if failures else 0)
