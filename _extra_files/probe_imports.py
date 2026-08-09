"""Ground-truth probe for broken submodule-path imports.

Combines the static AST scan (candidates) with a runtime `exec` of every
candidate statement, so only imports that ACTUALLY fail at import time are
reported. This eliminates false positives from:
  - star re-exports (`from ._exports import *`)
  - runtime package shims (`models/__init__.py` `_apply_legacy_import_shims`)
  - MetaPathFinders (`services/__init__.py` `_LegacyFlatServiceFinder`)
  - PEP 562 `__getattr__`

Usage:  python probe_imports.py [backend_root]
Exit code 0 = clean, 1 = real failures found.
"""

from __future__ import annotations

import ast
import os
import sys

BACKEND = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "backend")
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)


def backend_dir(dotted: str) -> str | None:
    parts = dotted.split(".")
    first = os.path.join(BACKEND, parts[0])
    if not os.path.isdir(first):
        return None
    path = first
    for p in parts[1:]:
        path = os.path.join(path, p)
        if not os.path.isdir(path):
            return None
    return path


def package_prefix_len(parts: list[str]) -> int:
    """How many leading parts form a package chain (with __init__.py) under BACKEND."""
    cur = BACKEND
    n = 0
    for p in parts:
        cur = os.path.join(cur, p)
        if os.path.isdir(cur) and os.path.isfile(os.path.join(cur, "__init__.py")):
            n += 1
        else:
            break
    return n


def module_path(dotted: str) -> str | None:
    parts = dotted.split(".")
    first = os.path.join(BACKEND, parts[0])
    if not os.path.isdir(first):
        return None
    path = first
    for p in parts[1:]:
        path = os.path.join(path, p)
    if os.path.isfile(path + ".py"):
        return path + ".py"
    if os.path.isdir(path):
        return path
    return None


def file_package(file_path: str) -> str | None:
    d = os.path.dirname(file_path)
    while d.startswith(BACKEND) and len(d) >= len(BACKEND):
        if os.path.isfile(os.path.join(d, "__init__.py")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


# ---- collect candidate statements ----
candidates: list[tuple[str, int, str]] = []  # (relpath, lineno, statement)


def add(path: str, lineno: int, stmt: str) -> None:
    rel = os.path.relpath(path, BACKEND)
    candidates.append((rel, lineno, stmt))


for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv", "venv")]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except SyntaxError:
            continue
        my_pkg = file_package(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if "." not in a.name:
                        continue
                    top = a.name.split(".")[0]
                    if not os.path.isdir(os.path.join(BACKEND, top)):
                        continue
                    if module_path(a.name) is None:
                        add(path, node.lineno, f"import {a.name}")
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name == "*":
                        continue
                    if node.level == 0:
                        mod = node.module or ""
                        if not mod:
                            continue
                        parts = mod.split(".")
                        if not os.path.isdir(os.path.join(BACKEND, parts[0])):
                            continue  # external
                        pplen = package_prefix_len(parts)
                        if pplen == 0:
                            continue
                        if pplen == len(parts):
                            pkg_dir = os.path.join(BACKEND, *parts)
                            if os.path.isfile(os.path.join(pkg_dir, a.name + ".py")) or (
                                os.path.isdir(os.path.join(pkg_dir, a.name))
                                and os.path.isfile(os.path.join(pkg_dir, a.name, "__init__.py"))
                            ):
                                continue
                            add(path, node.lineno, f"from {mod} import {a.name}")
                        else:
                            if module_path(mod) is None:
                                add(path, node.lineno, f"from {mod} import {a.name}")
                    else:
                        if my_pkg is None:
                            continue
                        pkg_dir = my_pkg
                        for _ in range(node.level - 1):
                            nd = os.path.dirname(pkg_dir)
                            if nd == pkg_dir or not nd.startswith(BACKEND):
                                break
                            pkg_dir = nd
                        if node.module:
                            dotted = os.path.relpath(pkg_dir, BACKEND).replace(os.sep, ".") + "." + node.module
                            if module_path(dotted) is None:
                                add(path, node.lineno, f"from {'.' * node.level}{node.module} import {a.name}")
                        else:
                            if os.path.isfile(os.path.join(pkg_dir, a.name + ".py")) or (
                                os.path.isdir(os.path.join(pkg_dir, a.name))
                                and os.path.isfile(os.path.join(pkg_dir, a.name, "__init__.py"))
                            ):
                                continue
                            rel_dotted = os.path.relpath(pkg_dir, BACKEND).replace(os.sep, ".")
                            add(path, node.lineno, f"from {rel_dotted} import {a.name}")

# ---- runtime probe ----
print(f"PROBING: {len(candidates)} candidate statements from {BACKEND}")
failures: list[tuple[str, int, str, str]] = []
import importlib  # noqa
import traceback

# Import the top-level packages first so finders/shim functions install.
for _top in ("models", "services", "controllers", "providers", "data", "utils"):
    try:
        importlib.import_module(_top)
    except Exception:
        pass

seen: set[tuple[str, int, str]] = set()
ns: dict = {}
for rel, lineno, stmt in candidates:
    if (rel, lineno, stmt) in seen:
        continue
    seen.add((rel, lineno, stmt))
    try:
        exec(stmt, ns)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        msg = f"{type(e).__name__}: {e}".splitlines()[0][:140]
        failures.append((rel, lineno, stmt, msg))

failures.sort()
print(f"REAL FAILURES: {len(failures)}")
for rel, lineno, stmt, msg in failures:
    print(f"  {rel}:{lineno}  {stmt}\n      -> {msg}")
sys.exit(1 if failures else 0)
