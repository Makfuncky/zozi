"""Mechanical W1 fixer: route router/controller/middleware session writes
through ``services.db_write`` so ``tests/test_w1_layer_guard.py`` passes.

This is a one-shot refactor tool kept OUT of ``scripts/`` (the audit scripts are
read-only). It only touches routers/, middleware/, controllers/ recursively and
preserves the exact call semantics.

Run:  python _extra_files/fix_w1_writes.py
"""
from __future__ import annotations

import ast
import pathlib
import sys

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYER_DIRS = [BACKEND / "routers", BACKEND / "middleware", BACKEND / "controllers"]

WRITE_VERBS = {
    "add", "add_all", "commit", "delete", "flush", "merge", "refresh",
    "begin", "begin_nested", "savepoint",
    "bulk_insert_mappings", "bulk_save_objects", "bulk_update_mappings",
}
SESSION_NAMES = {
    "db", "session", "sess", "db_session", "_db", "_session", "_db_session", "_sess",
}
ALIAS = "db_write"


def _already_imported(tree: ast.Module) -> bool:
    """True only when ``services.db_write`` is already imported (as ``db_write``
    or otherwise) — used to avoid a duplicate import.  We must NOT match
    ordinary ``db_write`` *usages*, because transformed call sites reference the
    name and would otherwise suppress the import."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "services.db_write":
            return True
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "services.db_write":
                    return True
    return False


class Rewriter(ast.NodeTransformer):
    def __init__(self):
        self.changed = False

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)
        f = node.func
        if (
            isinstance(f, ast.Attribute)
            and isinstance(f.value, ast.Name)
            and f.value.id in SESSION_NAMES
            and f.attr in WRITE_VERBS
        ):
            session_arg = ast.Name(id=f.value.id, ctx=ast.Load())
            node = ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=ALIAS, ctx=ast.Load()),
                    attr=f.attr,
                    ctx=ast.Load(),
                ),
                args=[session_arg, *node.args],
                keywords=list(node.keywords),
            )
            self.changed = True
        return node


def _add_import(tree: ast.Module):
    imp = ast.Import(names=[ast.alias(name="services.db_write", asname=ALIAS)])
    # insert after the last import/import-from statement (keeps __future__ first)
    last = -1
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            last = i
    idx = last + 1 if last >= 0 else 0
    tree.body.insert(idx, imp)


def rewrite_file(path: pathlib.Path):
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"  SKIP (parse error): {path.relative_to(BACKEND)} -> {e}")
        return False

    before = sum(
        1
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name) and n.func.value.id in SESSION_NAMES
        and n.func.attr in WRITE_VERBS
    )
    if before == 0:
        return False

    rw = Rewriter()
    tree = rw.visit(tree)
    ast.fix_missing_locations(tree)
    if not rw.changed:
        return False

    if not _already_imported(tree):
        _add_import(tree)

    new_src = ast.unparse(tree)
    path.write_text(new_src + "\n", encoding="utf-8")
    print(f"  FIXED {path.relative_to(BACKEND)}  ({before} write sites)")
    return True


def main():
    changed_files = 0
    total = 0
    for d in LAYER_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.py")):
            total += 1
            if rewrite_file(p):
                changed_files += 1
    print(f"\nDone. Scanned {total} files; rewrote {changed_files}.")


if __name__ == "__main__":
    main()
