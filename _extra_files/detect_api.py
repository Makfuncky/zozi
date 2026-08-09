"""Faithful replica of SYSTEM_AUDIT_REPORT.md API101 + API2 detection.

API101: endpoint (decorator with .get/.post/.put/.patch/.delete) lacking a
        response_model= kwarg.
API2:   symbol beginning with '_' that is used outside its defining module
        (or its submodules).

This script ONLY reads + reports; it never modifies anything. Use it to verify
the audit's advisories and to classify genuine issues vs false positives.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

BACKEND = Path("backend")
ROOT = Path(".")
SKIP = {"venv", "node_modules", "__pycache__", ".venv", ".git", "experiments"}

ROUTE_SUFFIXES = (".get", ".post", ".put", ".patch", ".delete")


def module_of(path: Path) -> str:
    rel = path.relative_to(BACKEND).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_test(parts) -> bool:
    return any(x in parts for x in {"tests", "test", "e2e", "testing",
                                    "loadtests", "validation"})


def is_migration(parts) -> bool:
    return "alembic" in parts and "versions" in parts


def dotted(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ""


def collect(paths):
    mods = {}
    for p in paths:
        mods[module_of(p)] = p
    return mods


def detect_api101(mods):
    """Return list of dicts: file, func, line, is_test, is_migration."""
    out = []
    for mod, path in mods.items():
        parts = mod.split(".")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            is_ep = False
            has_rm = False
            for dec in node.decorator_list:
                dname = dotted(dec.func) if isinstance(dec, ast.Call) else dotted(dec)
                if any(s in dname for s in ROUTE_SUFFIXES):
                    is_ep = True
                if isinstance(dec, ast.Call):
                    for kw in dec.keywords:
                        if kw.arg == "response_model":
                            has_rm = True
            if is_ep and not has_rm:
                out.append({
                    "file": str(path),
                    "func": node.name,
                    "line": node.lineno,
                    "is_test": is_test(parts),
                    "is_migration": is_migration(parts),
                })
    return out


def top_level_defs(tree):
    """Return set of private (leading _) top-level names defined in a module."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def detect_api2(mods):
    """Return list of dicts: file, symbol, line, kind, external_count,
    is_test, is_migration, is_dunder."""
    # Build per-module private top-level symbols.
    defs = {}
    for mod, path in mods.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    defs.setdefault(mod, {})[node.name] = (node.lineno, node.__class__.__name__)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.startswith("_"):
                        defs.setdefault(mod, {})[t.id] = (node.lineno, "Assign")

    # Scan every module for usages of each private name.
    # usage = (mod_using, line, ref_text)
    usages = {}
    for mod, path in mods.items():
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for n in node.names:
                    if n.name.startswith("_"):
                        usages.setdefault(n.name, []).append(
                            (mod, getattr(node, "lineno", 0), f"from {node.module} import {n.name}"))
            elif isinstance(node, ast.Import):
                pass  # handled via attribute access resolution below
            # attribute access M._sym
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                usages.setdefault(node.attr, []).append(
                    (mod, getattr(node, "lineno", 0), f"...{node.attr}"))

    # Now attribute access resolution: find `import M` then `M._sym`.
    # We approximate by recording raw usages; ownership is resolved by import edges.
    out = []
    for mod, syms in defs.items():
        parts = mod.split(".")
        for name, (line, kind) in syms.items():
            # find usages of this name NOT in this module or its submodules
            ext = []
            for (umod, uline, ref) in usages.get(name, []):
                if umod == mod or umod.startswith(mod + "."):
                    continue
                ext.append((umod, uline, ref))
            if ext:
                out.append({
                    "file": str(mods[mod]),
                    "symbol": name,
                    "line": line,
                    "kind": kind,
                    "external_count": len(ext),
                    "is_test": is_test(parts),
                    "is_migration": is_migration(parts),
                    "is_dunder": name.startswith("__") and name.endswith("__"),
                    "samples": ext[:3],
                })
    return out


def main():
    paths = []
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".py"):
                paths.append(Path(root) / f)
    mods = collect(paths)

    a101 = detect_api101(mods)
    a2 = detect_api2(mods)

    print(f"API101 endpoints missing response_model: {len(a101)}")
    test_a101 = [x for x in a101 if x["is_test"]]
    mig_a101 = [x for x in a101 if x["is_migration"]]
    real_a101 = [x for x in a101 if not x["is_test"] and not x["is_migration"]]
    print(f"  - production routers: {len(real_a101)}")
    print(f"  - test files: {len(test_a101)}")
    print(f"  - migration files: {len(mig_a101)}")

    print(f"\nAPI2 private symbols leaked externally: {len(a2)}")
    test_a2 = [x for x in a2 if x["is_test"]]
    mig_a2 = [x for x in a2 if x["is_migration"]]
    dunder_a2 = [x for x in a2 if x["is_dunder"]]
    real_a2 = [x for x in a2 if not x["is_test"] and not x["is_migration"] and not x["is_dunder"]]
    print(f"  - test-file symbols: {len(test_a2)}")
    print(f"  - migration-file symbols: {len(mig_a2)}")
    print(f"  - dunder (e.g. __init__): {len(dunder_a2)}")
    print(f"  - genuine source leaks: {len(real_a2)}")

    # Detailed dump for review
    print("\n--- API101 production routers (to fix) ---")
    for x in real_a101:
        print(f"  {x['file'].replace(str(BACKEND)+os.sep, 'backend'+os.sep)}:{x['line']}  {x['func']}")
    print("\n--- API101 test-file endpoints (likely false positive) ---")
    for x in test_a101:
        print(f"  {x['file'].replace(str(BACKEND)+os.sep, 'backend'+os.sep)}:{x['line']}  {x['func']}")
    print("\n--- API2 test-file symbols (review) ---")
    for x in test_a2:
        print(f"  {x['file'].replace(str(BACKEND)+os.sep, 'backend'+os.sep)}:{x['line']}  {x['symbol']}  used_by={x['external_count']}")
    print("\n--- API2 dunder symbols (likely false positive) ---")
    for x in dunder_a2:
        print(f"  {x['file'].replace(str(BACKEND)+os.sep, 'backend'+os.sep)}:{x['line']}  {x['symbol']}  used_by={x['external_count']}")
    print("\n--- API2 genuine source leaks (to fix) ---")
    for x in real_a2:
        print(f"  {x['file'].replace(str(BACKEND)+os.sep, 'backend'+os.sep)}:{x['line']}  {x['symbol']} ({x['kind']})  used_by={x['external_count']}")


if __name__ == "__main__":
    main()
