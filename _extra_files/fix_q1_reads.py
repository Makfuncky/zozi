"""Mechanical Q1 fixer (mirrors the W1 writer fixer).

Routes ``db.query(...)`` / ``db.execute(...)`` calls in the router / controller /
middleware layers to the shared read layer::

    db.query(Model).filter(f).all()
        -> db_read_query(db, Model).filter(f).all()
    db.execute(stmt)
        -> db_read_execute(db, stmt)

The binding constraint is the per-router ``*_q1_rescue.py`` guards, which FAIL
if a literal ``db.query(...)`` / ``db.execute(...)`` token remains and require
the module to ``import ... from services.db_read``.

Because ``services.db_read.query`` / ``.execute`` return the live SQLAlchemy
``Query`` / ``Result``, the entire method chain (``.filter().options().all()``,
``.scalars().all()`` ...) is preserved unchanged.  Semantics are identical to
the original; only the receiver name of the first call changes.

Idempotent: files with zero offending sites are left untouched, and an existing
``services.db_read`` import is not duplicated.
"""
from __future__ import annotations

import ast
import pathlib

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYER_DIRS = (
    BACKEND / "routers",
    BACKEND / "controllers",
    BACKEND / "middleware",
)

SESSION_NAMES = {
    "db", "session", "sess", "db_session",
    "_db", "_session", "_db_session", "_sess",
}
READ_ATTRS = {"query", "execute"}

_QL_NAME = "db_read_query"
_EX_NAME = "db_read_execute"


def _add_import(tree: ast.Module) -> None:
    imp = ast.ImportFrom(
        module="services.db_read",
        names=[
            ast.alias(name="query", asname=_QL_NAME),
            ast.alias(name="execute", asname=_EX_NAME),
        ],
        level=0,
    )
    tree.body.insert(0, imp)


def fix_file(path: pathlib.Path) -> tuple[bool, int]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return (False, 0)

    sites: list[ast.Call] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id in SESSION_NAMES and node.func.attr in READ_ATTRS:
            sites.append(node)

    if not sites:
        return (False, 0)

    for node in sites:
        recv = node.func.value
        new_name = _QL_NAME if node.func.attr == "query" else _EX_NAME
        node.func = ast.Name(id=new_name, ctx=ast.Load())
        node.args.insert(0, recv)

    if "services.db_read" not in src:
        _add_import(tree)

    ast.fix_missing_locations(tree)
    new_src = ast.unparse(tree)
    path.write_text(new_src, encoding="utf-8")
    return (True, len(sites))


def main() -> None:
    changed = 0
    total_sites = 0
    for layer in LAYER_DIRS:
        if not layer.exists():
            continue
        for path in sorted(layer.rglob("*.py")):
            ok, n = fix_file(path)
            if ok:
                changed += 1
                total_sites += n
                print(f"fixed {path.relative_to(BACKEND)}  ({n} sites)")
    print(f"\nchanged_files={changed}  total_q1_sites={total_sites}")


if __name__ == "__main__":
    main()
