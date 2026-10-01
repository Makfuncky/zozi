"""W1 regression test for routers/admin_commission.py.

Mirrors the auditor's W1 detection: a router (or controller) must not issue
db.add / db.commit / db.delete / etc. directly. Those writes must be delegated
to a service (here: services.finance.commission_admin_write_service via
controllers.admin_commission_controller).
"""
import ast
import importlib

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_save_objects", "bulk_insert_mappings", "bulk_update_mappings",
    "bulk_update", "begin", "begin_nested",
}


def _write_calls_in(path: str):
    tree = ast.parse(open(path, encoding="utf-8").read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in WRITE_VERBS:
                hits.append((node.lineno, node.func.attr))
    return hits


def test_admin_commission_router_has_no_db_writes():
    path = "backend/routers/admin_commission.py"
    hits = _write_calls_in(path)
    assert hits == [], f"W1: router still writes to DB at {hits}"


def test_admin_commission_controller_has_no_db_writes():
    path = "backend/controllers/admin_commission_controller.py"
    hits = _write_calls_in(path)
    assert hits == [], f"W1: controller still writes to DB at {hits}"


def test_admin_commission_wiring_imports_resolve():
    router = importlib.import_module("routers.admin_commission_governance")
    controller = importlib.import_module("controllers.admin_commission_controller")
    service = importlib.import_module("services.finance.commission_admin_write_service")
    assert hasattr(router, "router")
    assert hasattr(controller, "create_category_rate")
    assert hasattr(service, "create_commission_category_rate")
    # endpoint names must not shadow the controller imports
    assert router.create_badge_tier.__name__ == "create_badge_tier"
