"""Inventory existing services.db_read call signatures (temp, read-only)."""
from __future__ import annotations

import ast
import collections
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BE = ROOT / "backend"


def main() -> None:
    sig: collections.Counter = collections.Counter()
    for py in BE.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            src = py.read_text(encoding="utf-8")
        except Exception:
            continue
        if "db_read" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        alias_map: dict[str, str] = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module == "services.db_read":
                for a in n.names:
                    alias_map[a.asname or a.name] = a.name
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            fname = None
            if isinstance(f, ast.Name) and f.id in alias_map:
                fname = alias_map[f.id]
            elif (
                isinstance(f, ast.Attribute)
                and isinstance(f.value, ast.Name)
                and f.value.id == "db_read"
            ):
                fname = f.attr
            if not fname:
                continue
            kw = tuple(sorted(k.arg for k in n.keywords if k.arg))
            sig[(fname, len(n.args), kw)] += 1

    for k, v in sorted(sig.items()):
        print(f"{v:>4}  {k[0]}(pos={k[1]}, kw={list(k[2])})")


if __name__ == "__main__":
    main()
