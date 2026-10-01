"""W1 regression test for routers/countries.py.

Mirrors the auditor's W1 detection: a router (or controller) must not issue
db.add / db.commit / db.delete / etc. directly. Those writes must be delegated
to a service (services.geography.country_config_write_service via
controllers.country_admin_controller).
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
            if node.func.attr not in WRITE_VERBS:
                continue
            # Skip FastAPI router/app decorator registrations, e.g. @router.delete(...)
            base = node.func.value
            if isinstance(base, ast.Name) and base.id in {"router", "app"}:
                continue
            hits.append((node.lineno, node.func.attr))
    return hits


def test_countries_router_has_no_db_writes():
    path = "backend/routers/countries.py"
    hits = _write_calls_in(path)
    assert hits == [], f"W1: router still writes to DB at {hits}"


def test_countries_admin_controller_has_no_db_writes():
    path = "backend/controllers/country_admin_controller.py"
    hits = _write_calls_in(path)
    assert hits == [], f"W1: controller still writes to DB at {hits}"


def test_countries_w1_wiring_imports_resolve():
    router = importlib.import_module("routers.public_countries_access")
    controller = importlib.import_module("controllers.country_admin_controller")
    service = importlib.import_module("services.geography.country_config_write_service")
    assert hasattr(router, "router")
    assert hasattr(controller, "create_feature_flag")
    assert hasattr(controller, "toggle_active")
    assert hasattr(controller, "archive")
    assert hasattr(controller, "create_commission_rate")
    assert hasattr(service, "add_country_city")
    assert hasattr(service, "hard_delete_country")
