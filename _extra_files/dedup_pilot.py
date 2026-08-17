"""Caller-aware duplicate consolidator (pilot on a single function name).

For functions that are byte-identical in body, pick a single canonical module,
rewrite every internal caller to import from it, and delete the duplicates.

Read-only by default; pass --apply to write.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(HERE), "backend")
sys.path.insert(0, BACKEND)

TARGET_DIRS = [
    os.path.join(BACKEND, "services"),
    os.path.join(BACKEND, "controllers"),
    os.path.join(BACKEND, "routers"),
]

# Empty = detect ALL body-identical function-name clusters (no pilot restriction).
PILOT_NAMES = set()


def body_src(node):
    # Normalize: drop decorators + leading docstring, then compare by source text.
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ast.unparse(node)
    # strip decorators by re-emitting without them
    node = ast.parse(ast.unparse(node)).body[0]
    node.decorator_list = []
    # drop docstring
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        node.body = node.body[1:]
    return ast.unparse(node)


def collect():
    defs = {}  # name -> list of (file, body_key, node)
    files = []
    for d in TARGET_DIRS:
        for dp, _, fs in os.walk(d):
            for fn in fs:
                if not fn.endswith(".py") or fn == "__init__.py":
                    continue
                fp = os.path.join(dp, fn)
                try:
                    tree = ast.parse(open(fp, encoding="utf-8").read(), filename=fp)
                except SyntaxError:
                    continue
                files.append((fp, tree))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if PILOT_NAMES and node.name not in PILOT_NAMES:
                            continue
                        key = body_src(node)
                        defs.setdefault(node.name, []).append((fp, key, node))
    return defs, files


def callers_of(files, name):
    """Return dict fp -> list of (line_text_original, col) where `name(` is called."""
    out = {}
    for fp, _ in files:
        lines = open(fp, encoding="utf-8").read().splitlines()
        hits = []
        for i, ln in enumerate(lines):
            if re.search(rf"\b{re.escape(name)}\s*\(", ln):
                hits.append((i, ln))
        if hits:
            out[fp] = hits
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    defs, files = collect()
    report = {"clusters": []}
    for name, entries in defs.items():
        bodies = {e[1] for e in entries}
        if len(bodies) != 1:
            report["clusters"].append({"name": name, "status": "SKIP_body_differs", "files": [e[0] for e in entries]})
            continue
        fps = [e[0] for e in entries]
        callers = callers_of(files, name)
        # A file is "internal" if it calls name and also defines it.
        internal = [fp for fp in fps if fp in callers]
        external = [fp for fp in callers if fp not in fps]
        # Canonical: keep the shortest path (most "core") definition, drop the rest.
        canonical = sorted(fps, key=lambda p: (len(p.split(os.sep)), p))[0]
        others = [fp for fp in fps if fp != canonical]
        report["clusters"].append({
            "name": name,
            "status": "CONSOLIDATE",
            "canonical": os.path.relpath(canonical, BACKEND),
            "duplicates": [os.path.relpath(o, BACKEND) for o in others],
            "external_callers": [os.path.relpath(x, BACKEND) for x in external],
        })
        if args.apply:
            # Rewrite internal callers (duplicate files) to import the canonical fn.
            for fp in others:
                if fp not in callers:
                    continue
                src = open(fp, encoding="utf-8").read()
                # Replace "name(" calls (not definitions) with canonical import usage.
                # Simplest safe transform for reset-style fns: keep the call but alias.
                # We add `from <mod> import <name>` and leave calls as-is (name matches).
                mod = _module_of(canonical)
                imp = f"from {mod} import {name}\n"
                if imp.strip() not in src:
                    src = _add_import(src, imp)
                open(fp, "w", encoding="utf-8").write(src)
            # Now remove the duplicate definitions from those files.
            for fp in others:
                _remove_def(fp, name)
    print(json.dumps(report, indent=2))


def _module_of(fp):
    rel = os.path.relpath(fp, BACKEND)[:-3].replace(os.sep, ".")
    return rel


def _add_import(src, imp):
    lines = src.splitlines(keepends=True)
    # insert after the last top-level import line / first code line
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("from ") or ln.startswith("import "):
            insert_at = i + 1
    lines.insert(insert_at, imp)
    return "".join(lines)


def _remove_def(fp, name):
    src = open(fp, encoding="utf-8").read()
    tree = ast.parse(src)
    new_body = [n for n in tree.body if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)]
    # Rebuild a module with only non-target top-level defs (best-effort: keep rest).
    # Use a marker-based textual removal to preserve formatting.
    lines = src.splitlines(keepends=True)
    remove_ranges = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            remove_ranges.append((start, end))
    remove_ranges.sort(reverse=True)
    for s, e in remove_ranges:
        del lines[s:e]
    open(fp, "w", encoding="utf-8").write("".join(lines))


if __name__ == "__main__":
    main()
