"""Regression test for FILE-139: employee HR router must not duplicate succession routes.

Verifies that backend/modules/employee/routers/hr.py does not define inline
succession routes that duplicate backend/modules/employee/routers/hr/succession.py.
The succession routes must live only in succession.py to avoid maintenance burden
and ambiguous routing (AIDRIFT-011).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_BACKEND_ROOT))

HR_ROUTER = _BACKEND_ROOT / "modules" / "employee" / "routers" / "hr.py"
SUCCESSION_ROUTER = _BACKEND_ROOT / "modules" / "employee" / "routers" / "hr" / "succession.py"

_SUCCESSION_ROUTES = {
    "/bench-strength",
    "/successors/{role_name}",
    "/alumni",
    "/alumni/{employee_id}/eligibility",
}


def _extract_route_paths(tree: ast.Module) -> set[str]:
    paths: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"get", "post", "put", "delete", "patch"}:
                if node.args and isinstance(node.args[0], ast.Constant):
                    paths.add(node.args[0].value)
    return paths


class TestFile139SuccessionNoDuplicates:
    """FILE-139: succession routes must not be duplicated in hr.py."""

    def test_succession_router_file_exists(self):
        assert SUCCESSION_ROUTER.exists(), f"{SUCCESSION_ROUTER} missing"

    def test_hr_py_has_no_inline_succession_routes(self):
        tree = ast.parse(HR_ROUTER.read_text(encoding="utf-8"), filename=str(HR_ROUTER))
        defined = _extract_route_paths(tree)
        duplicates = defined & _SUCCESSION_ROUTES
        assert not duplicates, (
            f"hr.py still defines inline succession routes: {duplicates}. "
            f"These must live only in succession.py."
        )

    def test_succession_py_defines_all_routes(self):
        tree = ast.parse(
            SUCCESSION_ROUTER.read_text(encoding="utf-8"), filename=str(SUCCESSION_ROUTER)
        )
        defined = _extract_route_paths(tree)
        assert _SUCCESSION_ROUTES.issubset(defined), (
            f"succession.py missing routes: {_SUCCESSION_ROUTES - defined}"
        )
