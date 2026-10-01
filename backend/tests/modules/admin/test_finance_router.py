"""Regression tests for FILE-131: admin finance router input validation (Law 42).

Verifies that all write endpoints in backend/modules/admin/routers/finance.py
use typed Pydantic request models instead of raw dict = Body(...), and that
every protected endpoint carries a require_feature gate.
"""
from __future__ import annotations

import ast
import pathlib

ROUTER_PATH = pathlib.Path(
    __file__
).resolve().parents[3] / "modules" / "admin" / "routers" / "finance.py"

PYDANTIC_SCHEMA_NAMES = {
    "CommissionCategoryRateCreate",
    "CommissionBadgeTierCreate",
}


def test_no_dict_body_in_finance_router():
    """Law 42: no raw dict = Body(...) in the finance router."""
    source = ROUTER_PATH.read_text(encoding="utf-8")
    assert "dict = Body" not in source, (
        "finance router still contains 'dict = Body(...)' — Law 42 violation"
    )


def test_all_write_endpoints_use_pydantic_schemas():
    """Every write endpoint must annotate its body with a known Pydantic schema."""
    source = ROUTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    annotated_schemas: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for arg in node.args.args:
            if arg.annotation is None:
                continue
            ann_str = ast.unparse(arg.annotation)
            for schema_name in PYDANTIC_SCHEMA_NAMES:
                if schema_name in ann_str:
                    annotated_schemas.add(schema_name)

    assert annotated_schemas == PYDANTIC_SCHEMA_NAMES, (
        f"Expected schemas {PYDANTIC_SCHEMA_NAMES} found {annotated_schemas}"
    )


def test_all_protected_endpoints_have_feature_gate():
    """Law 4 / Law 88: every non-public endpoint must use require_feature."""
    source = ROUTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    REQUIRED_FEATURES = {
        "finance.commission.read",
        "finance.commission.write",
    }
    found_features: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name) and func.id == "require_feature":
                    if child.args and isinstance(child.args[0], ast.Constant):
                        found_features.add(child.args[0].value)

    assert REQUIRED_FEATURES.issubset(found_features), (
        f"Missing feature gates. Required {REQUIRED_FEATURES}, found {found_features}"
    )


def test_import_succeeds():
    """Smoke-test: the router module must be importable without error."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "finance_router_under_test", ROUTER_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "router"), "finance router module missing 'router' attribute"
