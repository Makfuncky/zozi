"""List every direct DB write in ``backend/modules/**/routers/*.py`` (Law 2 / Law 90).

Routers must stay thin: ``get_db()`` + ``require_feature(...)`` + one
service call. Anything that touches ``db.add/commit/delete/execute/flush/
merge/refresh`` inside a router is a Law 2 offender that should be moved
into ``domains/<d>/services/`` first.

Usage::

    python -m scripts.audit.router_thinness           # text report
    python -m scripts.audit.router_thinness --json    # machine-readable
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from collections import defaultdict
from typing import Iterable

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_ROOT = os.path.join(BACKEND, "modules")

WRITE_METHODS = frozenset(
    {"add", "add_all", "commit", "delete", "execute", "flush", "merge", "refresh"}
)

# Receiver names that are likely DB sessions, not HTTP decorators.
DB_RECEIVER_HINTS = (
    "db",
    "session",
    "db_session",
    "tx",
    "conn",
    "connection",
)


def _iter_router_files() -> Iterable[str]:
    for dirpath, _dirs, files in os.walk(ROUTER_ROOT):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                yield os.path.join(dirpath, f)


def _scan_file(path: str) -> list[dict]:
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError:
        return []

    rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
    hits: list[dict] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        # Skip FastAPI route decorators: @router.<method>(...) lives at module scope
        # and writes nothing; its method attr is ``delete/post/put/get``.
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "router" and node.lineno == 0:
                continue

        attr_name, on_text = _extract_write_attr(func)
        if attr_name is None:
            continue
        if not _looks_like_db_receiver(on_text):
            continue

        func_name = _enclosing_function_name(tree, node)
        hits.append(
            {
                "file": rel,
                "line": node.lineno,
                "function": func_name,
                "method": attr_name,
                "on": on_text,
            }
        )

    return hits


def _extract_write_attr(node: ast.AST):
    """Return (method_name, receiver_text) for calls like ``<db>.commit()``.

    Rejects attribute chains like ``router.delete(...)`` whose receiver is the
    FastAPI router (handled by caller via ``_looks_like_db_receiver``).
    """
    if not isinstance(node, ast.Attribute):
        return None
    if node.attr not in WRITE_METHODS:
        return None
    on_text = _unparse(node.value)
    return node.attr, on_text


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _looks_like_db_receiver(receiver: str) -> bool:
    if not receiver:
        return False
    head = receiver.split(".", 1)[0]
    return head in DB_RECEIVER_HINTS


def _enclosing_function_name(tree: ast.Module, target: ast.AST) -> str | None:
    # Build a quick id->FunctionDef map for line numbers.
    funcs = [
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    # We don't need precise nesting; nearest preceding def by line number works.
    funcs.sort(key=lambda n: n.lineno)
    best = None
    for fn in funcs:
        if fn.lineno <= target.lineno:
            best = fn
        else:
            break
    return best.name if best else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print only the per-file counts and totals",
    )
    args = parser.parse_args()

    all_hits: list[dict] = []
    for path in _iter_router_files():
        all_hits.extend(_scan_file(path))

    if args.json:
        print(json.dumps({"total_offenders": len(all_hits), "hits": all_hits}, indent=2))
        return 0

    per_file: dict[str, list[dict]] = defaultdict(list)
    for hit in all_hits:
        per_file[hit["file"]].append(hit)

    if args.summary:
        for f in sorted(per_file):
            print(f"{f}: {len(per_file[f])}")
        print(f"TOTAL: {len(all_hits)} db-write offenders in routers")
        return 0

    print(f"# Router DB-write offenders (Law 2/90) — {len(all_hits)} hits in {len(per_file)} files\n")
    for f in sorted(per_file):
        print(f"\n## {f}  ({len(per_file[f])} hits)")
        for hit in per_file[f]:
            fn = hit["function"] or "<module>"
            print(f"  {hit['line']:>5}: {fn}() -> {hit['on']}.{hit['method']}()")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())