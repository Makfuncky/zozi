"""Regression tests for FILE-75 / LAW-EXTRACT-018:

``infrastructure/utils/media_service.py`` must not create a static dependency on
``providers/*`` or on ``infrastructure.storage.storage``. The fix replaces the
top-level ``from X import *`` shim with a lazy ``__getattr__`` +
``importlib.import_module`` proxy so static analysis sees no upward arrow from
``infrastructure`` to ``providers``.
"""
from __future__ import annotations

import ast

import pytest

_BACKEND_ROOT = (
    pytest.importorskip("pathlib").Path(__file__).resolve().parent.parent.parent
)
_TARGET = _BACKEND_ROOT / "infrastructure" / "utils" / "media_service.py"
_CANONICAL = "infrastructure.storage.storage"


def _parse(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def test_media_service_has_no_static_provider_or_infrastructure_storage_import():
    """No top-level ImportFrom for providers or infrastructure.storage.storage."""
    tree = _parse(_TARGET)
    assert tree is not None
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top == "providers":
                offenders.append(f"from {node.module}")
            if node.module == "infrastructure.storage.storage":
                offenders.append(f"from {node.module}")
    assert not offenders, (
        "LAW-EXTRACT-018 regression: media_service.py must not statically import "
        f"from providers/ or infrastructure.storage.storage: {offenders}"
    )


def test_media_service_uses_lazy_getattr_proxy():
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


def test_media_service_proxies_known_names():
    """Runtime: known public names from the canonical module are reachable."""
    import importlib

    shim = importlib.import_module("infrastructure.utils.media_service")
    canonical = importlib.import_module(_CANONICAL)
    for name in ("StorageBackend", "LocalStorage", "S3Storage", "get_storage", "storage"):
        assert hasattr(shim, name), f"shim missing {name}"
        assert getattr(shim, name) is getattr(canonical, name), f"{name} proxy mismatch"


def test_media_service_attribute_error_on_unknown_names():
    """Error path: unknown names raise AttributeError, not silent None."""
    import importlib

    shim = importlib.import_module("infrastructure.utils.media_service")
    with pytest.raises(AttributeError):
        shim.ThisNameDoesNotExistAnywhere
