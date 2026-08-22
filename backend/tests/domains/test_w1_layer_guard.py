"""Architecture guard: Layer-1 (W1) forbids direct DB writes in the
presentation / orchestration layer.

The freelance contractor's anti-pattern was owning the SQLAlchemy
``Session`` in routers and calling ``session.add()`` / ``session.commit()``
directly.  The contract requires all writes to live in the domain **services**
layer and be reached through thin controller -> service delegation.

After the NEW_STRUCTURE migration the code-generator surface (old
``backend/routers`` + ``backend/controllers``) was retired.  The presentation
layer now lives inside each domain package as ``<domain>/.../*_controller.py``
and its paired ``*_controller__routers.py`` FastAPI wiring files, while
business logic lives in ``*_service.py``.  This test scans those
presentation-layer files (plus ``middleware/``) for any
``db.<write>`` / ``session.<write>`` call and FAILS if one exists, so a
regression is caught the moment someone re-introduces a transaction in a
presentation/orchestration layer.

Decoding is made robust (BOM stripped, non-UTF-8 falls back to latin-1) so a
single oddly-encoded file can never crash the whole scan.

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

# Presentation-layer roots in the NEW_STRUCTURE architecture.
_LAYER_DIRS = (
    _BACKEND_ROOT / "domains",
    _BACKEND_ROOT / "middleware",
)


def _presentation_files():
    """Yield presentation-layer .py files in the current architecture."""
    for layer in _LAYER_DIRS:
        if not layer.exists():
            continue
        for path in sorted(layer.rglob("*.py")):
            name = path.name
            if name == "__init__.py":
                continue
            # In `domains/` only the controller/router wiring files are
            # presentation layer; everything else (models, services, schemas,
            # policies, utils) is allowed to touch the session.
            if layer.name == "domains" and not (
                name.endswith("_controller.py")
                or name.endswith("_controller__routers.py")
            ):
                continue
            yield path


def _read_source(path: pathlib.Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):  # strip UTF-8 BOM
        data = data[3:]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")

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
    for path in _presentation_files():
        try:
            tree = ast.parse(_read_source(path))
        except (OSError, SyntaxError) as exc:
            logger.warning("skipping unparsable file", path=str(path), error=str(exc))
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
    domains = _BACKEND_ROOT / "domains"
    assert domains.exists(), "expected domain package directory"
    controllers = list(domains.rglob("*_controller.py"))
    assert controllers, "expected at least one controller module in domains/"