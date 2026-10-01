"""Regression tests for ``backend/services/core/admin_operations_service.py``.

Locks in the removal of the dead ``get_unknown_first`` / ``get_unknown_scalar``
helpers, which referenced an undefined ``Unknown`` symbol (latent NameError)
and were never called anywhere in the codebase.
"""
from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
_MODULE_PATH = _BACKEND_DIR / "services" / "core" / "admin_operations_service.py"

for _p in (str(_BACKEND_DIR), str(Path(__file__).resolve().parent.parent)):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)


def _module_ast() -> ast.Module:
    return ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))


def test_dead_unknown_functions_removed():
    mod = importlib.import_module("services.core.admin_operations_service")
    for name in ("get_unknown_first", "get_unknown_scalar"):
        assert not hasattr(mod, name), f"Dead {name!r} should be removed"


def test_no_unknown_symbol_reference_in_code():
    """Only the literal string 'Unknown entity type' (a message) is allowed;
    no ``Unknown`` identifier (Name/Attribute) should survive."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id != "Unknown", f"Name 'Unknown' at line {node.lineno}"
        if isinstance(node, ast.Attribute):
            assert node.attr != "Unknown", f"Attr '.Unknown' at line {node.lineno}"


def test_seed_demo_data_still_present():
    """The function conftest relies on must remain."""
    mod = importlib.import_module("services.core.admin_operations_service")
    assert hasattr(mod, "seed_demo_data")
