"""Rescue tests for the Cart router (cart.py).

Verifies the W1/CG1 violations from SYSTEM_AUDIT_REPORT.md are resolved:
the router performs no DB writes (W1) and delegates all operations to the
shared cart service ``domains.orders.services.cart_service`` (CG1). Also locks
the module location and mounted prefix so client calls to ``/cart`` resolve.
"""
from __future__ import annotations

import ast
import importlib.util
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_PATH = os.path.join(BACKEND, "modules", "customer", "routers", "cart.py")


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


def test_cart_router_delegates_to_service():
    src = _read(ROUTER_PATH)
    assert "from domains.orders.services.cart_service import" in src
    assert "cart_service" in src, "router must delegate to the cart service"


def test_cart_service_imports_and_has_key_fns():
    import domains.orders.services.cart_service as svc

    for fn in ("get_cart", "add_to_cart", "update_cart_item", "remove_cart_item", "clear_cart", "sync_cart"):
        assert hasattr(svc, fn), f"cart_service missing {fn}"


def test_cart_router_imports_and_has_routes():
    spec = importlib.util.spec_from_file_location("cart_under_test", ROUTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router")
    assert len(mod.router.routes) > 0


def test_cart_endpoint_mounted_under_cart():
    import main  # noqa: F401

    paths = [getattr(r, "path", "") for r in main.app.routes]
    cart_routes = [p for p in paths if p.startswith("/cart")]
    assert cart_routes, "No /cart routes mounted"
