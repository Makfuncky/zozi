"""Architecture guard: Layer-1 (W1) forbids direct DB writes in the
router / controller / middleware layers.

The freelance contractor's anti-pattern was owning the SQLAlchemy
``Session`` in routers and calling ``session.add()`` / ``session.commit()``
directly.  The contract requires all writes to live in ``services/`` and be
reached through thin router -> controller -> service (or router -> service)
delegation.

This test scans the real source tree (routers, middleware, controllers) for
any ``db.<write>`` / ``session.<write>`` call and FAILS if one exists, so a
regression is caught the moment someone re-introduces a transaction in a
presentation/orchestration layer.

Allowed write verbs mirror the audit rule (W1): add / add_all / commit /
delete / flush / merge / refresh / begin / begin_nested / savepoint and the
bulk_* helpers.  ``execute`` is intentionally excluded because read queries
are permitted in controllers; only mutation verbs break the contract.
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)

import ast
import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent

_LAYER_DIRS = (
    _BACKEND_ROOT / "routers",
    _BACKEND_ROOT / "middleware",
    _BACKEND_ROOT / "controllers",
)

_WRITE_VERBS = {
    "add",
    "add_all",
    "commit",
    "delete",
    "flush",
    "merge",
    "refresh",
    "begin",
    "begin_nested",
    "savepoint",
    "bulk_insert_mappings",
    "bulk_save_objects",
    "bulk_update_mappings",
}

_SESSION_NAMES = {
    "db",
    "session",
    "sess",
    "db_session",
    "_db",
    "_session",
    "_db_session",
    "_sess",
}


def _scan_layer_writes() -> list[tuple[str, int, str]]:
    offenders: list[tuple[str, int, str]] = []
    for layer in _LAYER_DIRS:
        if not layer.exists():
            continue
        for path in sorted(layer.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                logger.exception("unhandled exception", error=str(None))
                continue
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                ):
                    continue
                value = node.func.value
                if (
                    isinstance(value, ast.Name)
                    and value.id in _SESSION_NAMES
                    and node.func.attr in _WRITE_VERBS
                ):
                    rel = str(path.relative_to(_BACKEND_ROOT))
                    offenders.append((rel, node.lineno, f"{value.id}.{node.func.attr}"))
    return offenders


_OFFENDERS = _scan_layer_writes()


def test_no_layer1_session_writes() -> None:
    if _OFFENDERS:
        lines = "\n".join(f"  {f}:{ln}  {call}" for f, ln, call in _OFFENDERS)
        raise AssertionError(
            "W1 violation: direct Session writes found in router/controller/"
            f"middleware layers (writes must live in services):\n{lines}"
        )
    assert _OFFENDERS == []


def test_layers_exist() -> None:
    for layer in _LAYER_DIRS:
        assert layer.exists(), f"expected layer directory {layer}"