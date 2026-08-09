"""Regression tests for Logistics architecture fixes (QUAL3)."""
from __future__ import annotations

from pathlib import Path
import ast
import pytest

def _repo_root() -> Path:
    d = Path(__file__).resolve().parent
    for _ in range(5):
        if (d / "backend").is_dir():
            return d
        d = d.parent
    return Path(__file__).resolve().parent.parent


REPO_ROOT = _repo_root()
BACKEND = REPO_ROOT / "backend"
QUAL3_FUNC_LINE_LIMIT = 120


def _function_lengths(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node.end_lineno - node.lineno + 1
    return out


def test_logistics_pricing_functions_within_qual3_limit():
    """QUAL3 fix: build_service_area_pricing_breakdown stays under 120 lines
    after extracting _resolve_pricing_inputs and _apply_pricing_adjustments."""
    path = BACKEND / "services" / "logistics" / "logistics_partner_pricing.py"
    assert path.exists()
    lengths = _function_lengths(path)
    assert lengths["build_service_area_pricing_breakdown"] <= QUAL3_FUNC_LINE_LIMIT
    assert lengths["_resolve_pricing_inputs"] <= QUAL3_FUNC_LINE_LIMIT
    assert lengths["_apply_pricing_adjustments"] <= QUAL3_FUNC_LINE_LIMIT