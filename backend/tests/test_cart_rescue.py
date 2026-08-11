"""Rescue tests for the Cart router (cart.py).

Verifies the W1/CG1 violations from SYSTEM_AUDIT_REPORT.md are resolved:
the router performs no DB writes (W1) and delegates all operations to
``controllers.commerce.cart_controller`` (CG1). Also locks the module name so it mounts
as ``/api/v1/cart`` via the existing ``("cart", "/api/v1/cart")`` registration.
"""
from __future__ import annotations

import ast
import importlib.util
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_PATH = os.path.join(BACKEND, "routers", "cart.py")
CONTROLLER_PATH = os.path.join(BACKEND, "controllers", "cart_controller.py")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _find_layer1_writes(source: str) -> list[str]:
    tree = ast.parse(source)
    findings: list[str] = []
    session_names = {"db", "session", "db_session", "sess", "_db", "_session"}
    write_verbs = {"add", "add_all", "commit", "flush", "delete", "merge"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name) and value.id in session_names:
                if node.func.attr in write_verbs:
                    findings.append(f"{value.id}.{node.func.attr}")
    return findings


def test_cart_router_has_no_layer1_writes():
    src = _read(ROUTER_PATH)
    assert _find_layer1_writes(src) == [], "cart router must not call db.<write>"


def test_cart_router_delegates_to_controller():
    src = _read(ROUTER_PATH)
    assert "import controllers.commerce.cart_controller" in src
    assert "cart_ctrl." in src, "router must delegate to cart_ctrl.*"


def test_cart_controller_imports_and_has_key_fns():
    import controllers.commerce.cart_controller as ctrl

    for fn in ("get_cart_view", "upsert_cart_item", "remove_cart_item", "set_cart_item_quantity", "clear_cart"):
        assert hasattr(ctrl, fn), f"cart_controller missing {fn}"


def test_cart_router_imports_and_has_routes():
    spec = importlib.util.spec_from_file_location("cart_under_test", ROUTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router")
    assert len(mod.router.routes) > 0


def test_cart_endpoint_mounted_under_api_v1_cart():
    import main  # noqa: F401

    paths = [getattr(r, "path", "") for r in main.app.routes]
    cart_routes = [p for p in paths if p.startswith("/api/v1/cart")]
    assert cart_routes, "No /api/v1/cart routes mounted"
