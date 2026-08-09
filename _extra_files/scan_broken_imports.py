"""Scan backend/*.py for absolute imports that point at non-existent modules.

Read-only diagnostic. Writes a summary to stdout.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

BACKEND = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")

SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", "alembic", "static", "uploads"}

# Top-level package names that live inside backend/
LOCAL_ROOTS = {
    p.name
    for p in BACKEND.iterdir()
    if p.is_dir() and (p / "__init__.py").exists() and p.name not in SKIP_DIRS
}
LOCAL_ROOTS |= {p.stem for p in BACKEND.glob("*.py")}


def module_exists(dotted: str) -> bool:
    parts = dotted.split(".")
    base = BACKEND.joinpath(*parts)
    if base.with_suffix(".py").exists():
        return True
    if base.is_dir():
        return True
    return False


def iter_files():
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def main() -> int:
    broken: list[tuple[str, int, str]] = []
    for path in iter_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError as exc:
            broken.append((str(path.relative_to(BACKEND)), exc.lineno or 0, f"SYNTAX ERROR: {exc.msg}"))
            continue
        rel = path.relative_to(BACKEND)
        pkg_parts = list(rel.parts[:-1])
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg_parts[: len(pkg_parts) - (node.level - 1)] if node.level > 1 else pkg_parts
                    mod = ".".join(base + ([node.module] if node.module else []))
                    targets = [mod] if mod else []
                elif node.module:
                    targets = [node.module]
            for t in targets:
                if not t:
                    continue
                root = t.split(".")[0]
                if root not in LOCAL_ROOTS:
                    continue
                if not module_exists(t):
                    broken.append((str(rel), node.lineno, t))

    by_target: dict[str, list[str]] = {}
    for rel, line, target in broken:
        by_target.setdefault(target, []).append(f"{rel}:{line}")

    print(f"LOCAL_ROOTS={sorted(LOCAL_ROOTS)}\n")
    print(f"TOTAL broken import statements: {len(broken)} across {len(by_target)} targets\n")
    for target in sorted(by_target):
        print(f"MISSING: {target}")
        for loc in sorted(by_target[target]):
            print(f"    {loc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
