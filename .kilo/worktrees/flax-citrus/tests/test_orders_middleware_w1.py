"""Regression tests for the admin/orders controller and impossible-travel
middleware W1 (DB-write) rescue.

These guard that:
  * ``controllers/admin/orders.py`` performs NO direct DB write (the
    bulk/single order-delete paths delegate to ``orders_write_service``).
  * ``middleware/impossible_travel_middleware.py`` performs NO direct DB
    write (the fraud event is delegated to ``fraud_service.record_fraud_event``,
    which owns its own session).

The check mirrors the audit's W1/Q1 detector: it walks the AST, tracks the
session parameter name, and flags any ``session.<write verb>()`` call on a
session variable (``db``/``session``/``s``/...).
"""

import ast
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
ORDERS_CONTROLLER = BACKEND / "controllers" / "admin" / "orders.py"
TRAVEL_MIDDLEWARE = BACKEND / "middleware" / "impossible_travel_middleware.py"

# Mirrors DEFAULT_WRITE_VERBS in the audit (incl. begin/begin_nested/savepoint).
WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge", "execute",
    "begin", "begin_nested", "savepoint",
}
READ_VERBS = {
    "query", "scalar", "first", "all", "get", "refresh", "execute",
}


def _session_params(func: ast.AST) -> set[str]:
    names = {"db", "session", "sess", "s", "db_session"}
    for arg in func.args.args + func.args.posonlyargs + func.args.kwonlyargs:
        if arg.arg in names:
            names.add(arg.arg)
        elif arg.annotation is not None:
            ann = ast.dump(arg.annotation)
            if "Session" in ann or "AsyncSession" in ann:
                names.add(arg.arg)
    return names


def _session_calls(func: ast.AST, session_vars: set[str]) -> list[tuple[int, str]]:
    hits = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        obj = node.func.value
        obj_name = obj.attr if isinstance(obj, ast.Attribute) else getattr(obj, "id", "")
        if obj_name in session_vars:
            hits.append((node.lineno, node.func.attr))
    return hits


def _func(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def test_orders_controller_bulk_delete_delegates_no_direct_write():
    tree = ast.parse(ORDERS_CONTROLLER.read_text(encoding="utf-8"))
    target = _func(tree, "bulk_delete_orders_admin")
    assert target is not None, "bulk_delete_orders_admin must exist"

    session_vars = _session_params(target)
    bad = [(ln, m) for ln, m in _session_calls(target, session_vars) if m in WRITE_VERBS]
    assert not bad, f"direct session write in bulk_delete_orders_admin: {bad}"

    # The write must be delegated to the savepoint-aware service function.
    body = ast.dump(target)
    assert "delete_order_with_savepoint" in body, "must delegate to delete_order_with_savepoint service"


def test_orders_controller_delete_order_admin_delegates_no_direct_write():
    tree = ast.parse(ORDERS_CONTROLLER.read_text(encoding="utf-8"))
    target = _func(tree, "delete_order_admin")
    assert target is not None, "delete_order_admin must exist"

    session_vars = _session_params(target)
    bad = [(ln, m) for ln, m in _session_calls(target, session_vars) if m in WRITE_VERBS]
    assert not bad, f"direct session write in delete_order_admin: {bad}"

    body = ast.dump(target)
    assert "delete_order" in body, "must delegate to delete_order service"


def test_middleware_lock_session_event_driven_no_direct_write():
    tree = ast.parse(TRAVEL_MIDDLEWARE.read_text(encoding="utf-8"))
    target = _func(tree, "_lock_session")
    assert target is not None, "_lock_session must exist"

    session_vars = _session_params(target)
    bad = [(ln, m) for ln, m in _session_calls(target, session_vars) if m in WRITE_VERBS]
    assert not bad, f"direct session write in _lock_session: {bad}"

    body = ast.dump(target)
    # The middleware must not open, write to, or commit a DB session itself;
    # fraud-event persistence is delegated (Redis queue or a service call).
    assert "log_impossible_travel_lock" in body or "fraud_events:queue" in body, \
        "must delegate fraud-event persistence (no direct DB write)"
    assert "get_service_session" not in body, "middleware must not open its own DB session"
