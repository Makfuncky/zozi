"""W1 regression test for routers/admin_promotions.py.

Mirrors the auditor's W1 detection: a router must not issue db.add /
db.commit / db.delete etc. directly. Those writes must be delegated to a
service (services.promotions.promotion_admin_write_service via
controllers.promotion_admin_controller).
"""
import ast
import importlib

WRITE_VERBS = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_save_objects", "bulk_insert_mappings", "bulk_update_mappings",
    "bulk_update", "begin", "begin_nested",
}
ROUTER_NAMES = {"router", "app", "country_router"}


def _write_calls_in(path: str):
    tree = ast.parse(open(path, encoding="utf-8").read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr not in WRITE_VERBS:
                continue
            base = node.func.value
            if isinstance(base, ast.Name) and base.id in ROUTER_NAMES:
                continue
            hits.append((node.lineno, node.func.attr))
    return hits


def test_admin_promotions_router_has_no_db_writes():
    hits = _write_calls_in("backend/routers/admin_promotions.py")
    assert hits == [], f"W1: router still writes to DB at {hits}"


def test_admin_promotions_controller_has_no_db_writes():
    hits = _write_calls_in("backend/controllers/promotion_admin_controller.py")
    assert hits == [], f"W1: controller still writes to DB at {hits}"


def test_admin_promotions_wiring_imports_resolve():
    router = importlib.import_module("routers.admin_promotions_governance")
    controller = importlib.import_module("controllers.promotion_admin_controller")
    service = importlib.import_module("services.promotions.promotion_admin_write_service")
    assert hasattr(router, "router")
    assert hasattr(controller, "create_coupon")
    assert hasattr(controller, "create_banner")
    assert hasattr(controller, "delete_banner_by_country")
    assert hasattr(service, "create_coupon")
    assert hasattr(service, "banner_to_dict")
