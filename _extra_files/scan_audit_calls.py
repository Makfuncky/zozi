"""Read-only: AST-scan every audit_log(...) call site in the backend.

Prints: file:line  n_positional  keywords
"""
from __future__ import annotations

import ast
import collections
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / "backend"
SKIP = {"venv", "__pycache__", ".venv", "node_modules", ".pytest_cache"}

shapes: collections.Counter[tuple] = collections.Counter()
rows: list[str] = []

for p in ROOT.rglob("*.py"):
    if any(x in p.parts for x in SKIP):
        continue
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
        if name not in {"audit_log", "_audit_log"}:
            continue
        kw = tuple(sorted(k.arg for k in node.keywords if k.arg))
        npos = len(node.args)
        shapes[(npos, kw)] += 1
        rows.append(f"{p.relative_to(ROOT)}:{node.lineno}  pos={npos}  kw={kw}")

print("=== SHAPES ===")
for (npos, kw), n in sorted(shapes.items(), key=lambda kv: -kv[1]):
    print(f"{n:4d}  pos={npos}  kw={list(kw)}")
print()
print("=== POSITIONAL >1 ===")
for r in rows:
    if "pos=0" not in r and "pos=1" not in r:
        print(r)
print()
print("TOTAL CALLS", sum(shapes.values()))
