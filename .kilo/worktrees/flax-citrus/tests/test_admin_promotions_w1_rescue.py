"""W1 (+Q1) rescue test — admin_promotions router (Promotions domain).

Verifies the router no longer calls session.add()/commit()/delete()/refresh()
directly (W1), and that the DB reads (Q1) for promotion config, coupons, flash
sales, banners and tiers now live in
``services.promotions.admin_promotions_write_service``. Import integrity is
checked so the boot router-load chain (main.py) stays intact.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

_ROUTER_FILE = _BACKEND_ROOT / "routers" / "admin_promotions.py"
_SERVICE_MODULE = "services.promotions.admin_promotions_write_service"
_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def test_router_and_service_import_cleanly() -> None:
    importlib.import_module(_SERVICE_MODULE)
    importlib.import_module("routers.admin_promotions_governance")


def test_router_has_no_session_writes() -> None:
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        value = func.value
        target = value if isinstance(value, ast.Name) and value.id == "db" else (
            value.attr if isinstance(value, ast.Attribute) and value.attr == "db" else None
        )
        if target == "db" and func.attr in _SESSION_WRITES:
            violations.append((node.lineno, func.attr))
    assert not violations, f"admin_promotions still writes to the session: {violations}"


def test_router_has_no_session_reads() -> None:
    """Q1: routers must not call db.query() directly."""
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        value = func.value
        target = value if isinstance(value, ast.Name) and value.id == "db" else (
            value.attr if isinstance(value, ast.Attribute) and value.attr == "db" else None
        )
        if target == "db" and func.attr == "query":
            violations.append((node.lineno, func.attr))
    assert not violations, f"admin_promotions still reads via db.query(): {violations}"


def test_service_owns_reads_and_writes() -> None:
    svc = importlib.import_module(_SERVICE_MODULE)
    for fn in [
        # reads (Q1)
        "get_promotion_config",
        "list_coupons",
        "list_flash_sales",
        "list_banners_paginated",
        "list_promotion_tiers",
        "banner_to_dict",
        # writes (W1)
        "update_promotion_config",
        "create_coupon",
        "create_flash_sale",
        "update_flash_sale",
        "create_banner",
        "update_banner",
        "delete_banner",
    ]:
        assert callable(getattr(svc, fn)), f"missing service function: {fn}"
