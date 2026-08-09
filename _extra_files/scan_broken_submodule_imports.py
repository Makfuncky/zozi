"""Scan backend for broken submodule-path imports.

Bug pattern (same as services.orders.order_payment_functions):
  - `from X import Y` where X is a package dir (X/__init__.py exists)
  - X/Y.py (or X/Y/__init__.py) no longer exists on disk
  - AND the name Y is NOT bound in X/__init__.py (only inner names were re-exported)

At runtime, `from X import Y` falls back to importing the submodule X.Y when
getattr(X, 'Y') fails. If the file is gone, this raises ImportError — but only
*sometimes*, because a stale X/__pycache__/Y.cpython-*.pyc can still be loaded
as a lone bytecode module, making the failure depend on import order / cache
state. That is exactly the intermittent 8-vs-0 router-load failure we saw.

Also flags the harder forms (deterministic ModuleNotFoundError):
  - `import X.Y` / `import X.Y.Z`        (module path missing on disk)
  - `from X.Y import Z`                  (module path X.Y missing on disk)
  - relative `from . import Y` inside a package with the same missing-file hazard

Rules:
  - Namespace packages (dirs without __init__.py) are tolerated at intermediate
    levels — only the target file/package must exist.
  - `from X import Y` is SAFE if X/__init__.py binds Y itself
    (`from . import Y`, `from .. import Y`, `from other.pkg import Y`,
     `from other.pkg import Y as W`, `import a.b as W`, `Y = ...`, `def Y`),
    or defines a PEP 562 module-level `__getattr__`.
  - `from X.mod import name` / `import X.mod` are checked against the module
    path X.mod only — `name` is a plain attribute of that module.

Usage:  python scan_broken_submodule_imports.py [backend_root]
Exit code 0 = clean, 1 = hits found.
"""

from __future__ import annotations

import ast
import os
import sys

BACKEND = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "backend")


def is_pkg_dir(d: str) -> bool:
    return os.path.isfile(os.path.join(d, "__init__.py"))


def package_prefix_len(parts: list[str]) -> int:
    """How many leading parts form a package chain under BACKEND."""
    cur = BACKEND
    n = 0
    for p in parts:
        cur = os.path.join(cur, p)
        if os.path.isdir(cur) and is_pkg_dir(cur):
            n += 1
        else:
            break
    return n


def module_path(dotted: str) -> str | None:
    """Return the file/package path for dotted module, or None if missing."""
    parts = dotted.split(".")
    first = os.path.join(BACKEND, parts[0])
    if not os.path.isdir(first):
        return None  # external -> caller decides
    path = first
    for p in parts[1:]:
        path = os.path.join(path, p)
    if os.path.isfile(path + ".py"):
        return path + ".py"
    if os.path.isdir(path):
        return path
    return None


def bound_names_in_init(pkg_dir: str) -> set[str] | None:
    """Names bound by pkg_dir/__init__.py; None => PEP 562 __getattr__ present."""
    init = os.path.join(pkg_dir, "__init__.py")
    if not os.path.isfile(init):
        return set()
    try:
        tree = ast.parse(open(init, encoding="utf-8", errors="replace").read())
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__getattr__":
            return None
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                names.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def file_package(file_path: str) -> str | None:
    """Nearest ancestor package dir of file_path (with __init__.py)."""
    d = os.path.dirname(file_path)
    while d.startswith(BACKEND) and len(d) >= len(BACKEND):
        if is_pkg_dir(d):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


def check_import_module(path: str, lineno: int, dotted: str, src: str) -> None:
    """`import X.Y` — module path must exist."""
    if "." not in dotted:
        return  # plain `import X` is always fine
    top = dotted.split(".")[0]
    if not os.path.isdir(os.path.join(BACKEND, top)):
        return  # external
    if module_path(dotted) is None:
        _flag(path, lineno, src, f"import {dotted}  ->  module path missing on disk")


def check_from_import(path: str, lineno: int, node: ast.ImportFrom, src: str) -> None:
    for a in node.names:
        if a.name == "*":
            continue
        # ---- absolute form ----
        if node.level == 0:
            mod = node.module or ""
            if not mod:
                continue
            parts = mod.split(".")
            if not os.path.isdir(os.path.join(BACKEND, parts[0])):
                continue  # external (stdlib/third-party)
            pplen = package_prefix_len(parts)
            if pplen == 0:
                continue  # not a package chain in our tree
            if pplen == len(parts):
                # mod is a package: `from X import Y` -> submodule check on Y
                pkg_dir = os.path.join(BACKEND, *parts)
                if os.path.isfile(os.path.join(pkg_dir, a.name + ".py")) or (
                    os.path.isdir(os.path.join(pkg_dir, a.name))
                    and is_pkg_dir(os.path.join(pkg_dir, a.name))
                ):
                    continue  # real submodule exists
                bound = bound_names_in_init(pkg_dir)
                if bound is None or a.name in bound:
                    continue  # name re-exported in __init__ -> getattr works
                _flag(path, lineno, src,
                      f"from {mod} import {a.name}  ->  submodule file missing & not bound in {mod}/__init__.py")
            else:
                # mod is X.Y where Y must be a module/package on disk
                if module_path(mod) is None:
                    _flag(path, lineno, src,
                          f"from {mod} import {a.name}  ->  module {mod} missing on disk")
            continue
        # ---- relative form ----
        my_pkg = file_package(path)
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
                _flag(path, lineno, src,
                      f"from {'.' * node.level}{node.module} import {a.name}  ->  module {dotted} missing on disk")
        else:
            if os.path.isfile(os.path.join(pkg_dir, a.name + ".py")) or (
                os.path.isdir(os.path.join(pkg_dir, a.name))
                and is_pkg_dir(os.path.join(pkg_dir, a.name))
            ):
                continue
            bound = bound_names_in_init(pkg_dir)
            if bound is None or a.name in bound:
                continue
            rel = os.path.relpath(pkg_dir, BACKEND).replace(os.sep, ".")
            _flag(path, lineno, src,
                  f"from . import {a.name}  ->  submodule file missing & not bound in {rel}/__init__.py")


hits: list[tuple[str, str]] = []


def _flag(path: str, lineno: int, src: str, msg: str) -> None:
    rel = os.path.relpath(path, BACKEND)
    try:
        stmt = src.splitlines()[lineno - 1].strip()
    except IndexError:
        stmt = ""
    hits.append((rel, f"{rel}:{lineno}  {msg}  ::  {stmt}"))


for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        path = os.path.join(root, fn)
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    check_import_module(path, node.lineno, a.name, src)
            elif isinstance(node, ast.ImportFrom):
                check_from_import(path, node.lineno, node, src)

hits.sort()
print(f"SCANNED: {BACKEND}")
print(f"HITS: {len(hits)}")
for _, line in hits:
    print("  " + line)
sys.exit(1 if hits else 0)
