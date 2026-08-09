"""W1 regression test for routers/supplier_profile.py."""
import ast
import importlib

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_save_objects", "bulk_insert_mappings", "bulk_update_mappings",
    "bulk_update", "begin", "begin_nested",
}


def _write_calls_in(path: str):
    tree = ast.parse(open(path, encoding="utf-8").read())
    return [
        (n.lineno, n.func.attr)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr in WRITE_VERBS
    ]


def test_supplier_profile_router_no_db_writes():
    hits = _write_calls_in("backend/routers/supplier_profile.py")
    assert hits == [], f"W1: router still writes to DB at {hits}"


def test_supplier_profile_controller_no_db_writes():
    hits = _write_calls_in("backend/controllers/supplier_profile_controller.py")
    assert hits == [], f"W1: controller still writes to DB at {hits}"


def test_supplier_profile_wiring():
    router = importlib.import_module("routers.supplier_profile")
    controller = importlib.import_module("controllers.supplier_profile_controller")
    service = importlib.import_module("services.supplier.supplier_profile_write_service")
    assert hasattr(router, "router")
    assert hasattr(controller, "create_profile")
    assert hasattr(service, "create_supplier_profile")
