"""Validation tests for SEC5 / SEC6 / SYM1 / SYM2 fixes.

These tests verify the audit findings are resolved without importing the full
application (which requires DB / SECRET_KEY wiring). Symbol presence is checked
via AST parsing of the relevant source files.
"""
from __future__ import annotations

import ast
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only-0123456789abcdef")

from pathlib import Path

import pytest

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")


def _parse(rel: str) -> ast.Module:
    return ast.parse((BACKEND / rel).read_text(encoding="utf-8"))


def _class_names(tree: ast.Module) -> set[str]:
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


def _func_names(tree: ast.Module) -> set[str]:
    return {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.col_offset == 0
    }


# --- SEC6: SSRF mitigation helper ----------------------------------------
def test_url_security_blocks_private_and_bad_hosts():
    from utils.url_security import is_safe_url, require_safe_url

    assert is_safe_url("https://ipwho.is/1.2.3.4", allowed_hosts={"ipwho.is"})
    assert not is_safe_url("http://169.254.169.254/latest", allowed_hosts={"ipwho.is"})
    assert not is_safe_url("http://localhost/x")
    assert not is_safe_url("https://evil.com/x", allowed_hosts={"ipwho.is"})
    assert not is_safe_url("ftp://example.com/x")

    with pytest.raises(ValueError):
        require_safe_url("http://127.0.0.1/x")


# --- SEC5: no f-string SQL interpolation in command router --------------
def test_sec5_no_fstring_sql_interpolation():
    tree = _parse("routers/api_comms_command.py")
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):  # f-string
            src = ast.unparse(node) if hasattr(ast, "unparse") else ""
            assert "SELECT" not in src.upper(), "f-string SQL interpolation remains"


# --- SYM1: dead symbols removed ------------------------------------------
def test_sym1_dead_classes_removed():
    dead = {
        "routers/api_ai_generation.py": {"AIImageAnalysisRequest"},
        "services/hr/attendance_service.py": {"AttendanceService"},
        "middleware/behavioral_analytics.py": {"BehaviorProfile", "BehavioralAnalyzer"},
    }
    for rel, names in dead.items():
        tree = _parse(rel)
        present = _class_names(tree) & names
        assert not present, f"{rel} still defines dead symbols: {present}"


# --- SYM2: within-file duplicates removed --------------------------------
def test_sym2_within_file_duplicates_removed():
    geo = _parse("routers/api_geography_registry.py")
    for name in ("CommissionTierItem", "CommissionTiersDraftBody", "PayoutSettingsDraftBody"):
        count = sum(
            1 for n in ast.walk(geo)
            if isinstance(n, ast.ClassDef) and n.name == name
        )
        assert count == 1, f"{name} defined {count} times in api_geography_registry.py"

    pvc = _parse("controllers/catalog/product_verification_controller.py")
    for name in ("bulk_update_verifications", "get_verification", "update_verification", "_serialize"):
        count = sum(
            1 for n in ast.walk(pvc)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name == name and n.col_offset == 0
        )
        assert count == 1, f"{name} defined {count} times in product_verification_controller.py"
