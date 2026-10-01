"""Law 2 smoke test: module routers must not contain DB writes or business logic.

ARCHITECTURE_DIAGRAM.md §3 + §12 Law 2: module routers are auth context +
``require_feature(...)`` + ONE service call. No ``db.add``, ``db.commit``,
``db.delete`` or business logic is allowed in the router module.

This is a regression guard for Phase B finding #15.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_MODULES_DIR = _BACKEND_ROOT / "modules"

_FORBIDDEN_CALLS = {
    "add",       # db.add
    "commit",    # db.commit
    "delete",    # db.delete
    "execute",   # db.execute / session.execute
    "flush",     # db.flush
    "merge",     # db.merge
    "expire_all",
    "expunge",
}


def _iter_router_files() -> list[pathlib.Path]:
    if not _MODULES_DIR.exists():
        return []
    return [
        p
        for p in _MODULES_DIR.rglob("routers/*.py")
        if p.name != "__init__.py"
    ]


def _has_db_call(node: ast.Call, db_aliases: set[str]) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in _FORBIDDEN_CALLS:
        return False
    # func.value must be in db_aliases (heuristic: the name of the Session
    # parameter is typically ``db`` or ``session``).
    if not isinstance(func.value, ast.Name):
        return False
    return func.value.id in db_aliases


def _db_param_names(file_text: str) -> set[str]:
    """Heuristically find parameter names bound to ``Session`` in router signatures.

    We look for ``db: Session``, ``db=Depends(get_db)`` and the
    ``session=Depends(get_db)`` / ``db_session=Depends(get_db)`` patterns.
    """
    import re

    aliases: set[str] = set()
    # ``db: Session = Depends(get_db)`` or ``db=Depends(get_db)``
    for match in re.finditer(
        r"([A-Za-z_]\w*)\s*[:=][^=\n]*?Depends\(\s*get_db\s*\)", file_text
    ):
        aliases.add(match.group(1))
    return aliases


def test_no_router_db_writes() -> None:
    offenders: list[str] = []
    for path in _iter_router_files():
        text = path.read_text(encoding="utf-8")
        aliases = _db_param_names(text)
        if not aliases:
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _has_db_call(node, aliases):
                offenders.append(
                    f"{path.relative_to(_BACKEND_ROOT)}:"
                    f"{node.lineno}: {ast.unparse(node.func)}"
                )
    if offenders:
        msg = "\n  ".join(offenders)
        pytest.fail(
            "Law 2 violation: module routers must not perform DB writes/flushes.\n"
            "Move the transaction to a domain service and call it from the router.\n"
            f"  {msg}"
        )