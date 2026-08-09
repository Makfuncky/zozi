"""Scan backend/ (and tests/) for top-level module imports that cannot be resolved on disk.

Pure static resolution against the filesystem - does not execute any module.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"

# Top-level packages that live under backend/
ROOTS = {
    "controllers", "services", "models", "routers", "providers", "utils", "db",
    "data", "middleware", "events", "jobs", "tasks", "dependencies", "settings",
    "monitoring", "tools", "zozi_mcp", "alembic", "_triage",
}


def module_exists(dotted: str) -> bool:
    parts = dotted.split(".")
    if parts[0] not in ROOTS:
        return True  # third-party / stdlib / not our concern
    p = BACKEND.joinpath(*parts)
    if p.with_suffix(".py").is_file():
        return True
    if p.is_dir():
        return True
    return False


def scan(base: Path, label: str) -> list[tuple[str, int, str]]:
    missing: list[tuple[str, int, str]] = []
    for f in base.rglob("*.py"):
        if "__pycache__" in f.parts or "node_modules" in f.parts:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
        except SyntaxError as e:
            missing.append((str(f.relative_to(REPO)), e.lineno or 0, f"SYNTAX ERROR: {e.msg}"))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:  # relative import - resolve against package
                    continue
                mod = node.module or ""
                if not mod:
                    continue
                if not module_exists(mod):
                    missing.append((str(f.relative_to(REPO)), node.lineno, f"from {mod} import ..."))
                    continue
                # also check submodule targets:  from pkg import submodule
                parts = mod.split(".")
                if parts[0] in ROOTS:
                    pkg_dir = BACKEND.joinpath(*parts)
                    if pkg_dir.is_dir():
                        for a in node.names:
                            if a.name == "*":
                                continue
                            # only flag when a same-named .py/dir is clearly absent AND
                            # the package __init__ does not exist (namespace pkg -> must be a file)
                            init = pkg_dir / "__init__.py"
                            if not init.exists():
                                cand = pkg_dir / a.name
                                if not cand.with_suffix(".py").exists() and not cand.is_dir():
                                    missing.append(
                                        (str(f.relative_to(REPO)), node.lineno,
                                         f"from {mod} import {a.name}  (namespace pkg, no such submodule)")
                                    )
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if not module_exists(a.name):
                        missing.append((str(f.relative_to(REPO)), node.lineno, f"import {a.name}"))
    return missing


def main() -> None:
    targets = sys.argv[1:] or ["backend", "tests"]
    total = 0
    for t in targets:
        base = REPO / t
        if not base.exists():
            continue
        res = scan(base, t)
        total += len(res)
        print(f"\n########## {t}: {len(res)} unresolved imports ##########")
        for f, ln, what in sorted(res):
            print(f"{f}:{ln}  {what}")
    print(f"\nTOTAL: {total}")


if __name__ == "__main__":
    main()
