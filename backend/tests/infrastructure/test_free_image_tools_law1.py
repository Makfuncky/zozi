"""Regression tests for FILE-73 / LAW-EXTRACT-018:

``infrastructure/utils/free_image_tools.py`` must not create a static dependency on
``providers/*``. The fix replaces the top-level ``from X import *`` shim with a
lazy ``__getattr__`` + ``importlib.import_module`` proxy so static analysis sees
no upward arrow from ``infrastructure`` to ``providers``.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_BACKEND_ROOT = (
    pytest.importorskip("pathlib").Path(__file__).resolve().parent.parent.parent
)
_TARGET = _BACKEND_ROOT / "infrastructure" / "utils" / "free_image_tools.py"
_CANONICAL = "providers.image.free_image_tools"


def _parse(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def test_free_image_tools_has_no_static_provider_import():
    """No top-level ImportFrom for providers in free_image_tools.py."""
    tree = _parse(_TARGET)
    assert tree is not None
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top == "providers":
                offenders.append(f"from {node.module}")
    assert not offenders, (
        "LAW-EXTRACT-018 regression: free_image_tools.py must not statically import "
        f"from providers/: {offenders}"
    )


def test_free_image_tools_uses_lazy_getattr_proxy():
    """Shim uses __getattr__ + importlib.import_module for lazy resolution."""
    tree = _parse(_TARGET)
    assert tree is not None
    getattr_nodes = [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "__getattr__"
    ]
    assert len(getattr_nodes) == 1, "expected exactly one __getattr__"
    src = ast.unparse(getattr_nodes[0])
    assert "importlib.import_module" in src, "__getattr__ must use importlib.import_module"
    assert _CANONICAL in src, f"__getattr__ must proxy to {_CANONICAL}"


def test_free_image_tools_proxies_known_names():
    """Runtime: known public names from the canonical module are reachable."""
    import importlib

    shim = importlib.import_module("infrastructure.utils.free_image_tools")
    canonical = importlib.import_module(_CANONICAL)
    for name in ("TOOL_REGISTRY", "auto_process_image"):
        assert hasattr(shim, name), f"shim missing {name}"
        assert getattr(shim, name) is getattr(canonical, name), f"{name} proxy mismatch"


def test_free_image_tools_attribute_error_on_unknown_names():
    """Error path: unknown names raise AttributeError, not silent None."""
    import importlib

    shim = importlib.import_module("infrastructure.utils.free_image_tools")
    with pytest.raises(AttributeError):
        shim.ThisNameDoesNotExistAnywhere
