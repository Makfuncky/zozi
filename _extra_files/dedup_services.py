"""Consolidate module-level duplicated functions in services/.

Two functions are "duplicated" when their normalized body (decorators + docstring
stripped) is byte-identical. Within a name cluster, the shortest-path file is canonical;
every other file that defines the same body gets the definition removed and (if it called
the name internally) an import from the canonical module added.

Dunders and class methods are excluded (safe module-level only).
Every write is parse-checked; failures are skipped and logged (never partial state).
Read-only unless --apply.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(HERE), "backend")
sys.path.insert(0, BACKEND)
SERVICES = os.path.join(BACKEND, "services")


def strip_body(src_lines, node):
    seg = src_lines[node.lineno - 1: getattr(node, "end_lineno", node.lineno)]
    seg = [ln for ln in seg if not ln.lstrip().startswith("@")]
    return "\n".join(seg)


def module_level_funcs(fp):
    try:
        src = open(fp, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:
        return None
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("__"):
            out.append((node, src.splitlines()))
    return out


def import_insert_index(lines):
    """Index (0-based) after the last `from __future__ import ...` statement."""
    depth = 0
    at = 0
    for i, ln in enumerate(lines):
        depth += ln.count("(") + ln.count("[") + ln.count("{")
        depth -= ln.count(")") + ln.count("]") + ln.count("}")
        st = ln.lstrip()
        if depth == 0 and st.startswith("from __future__ import"):
            at = i + 1
    return at


def apply_one(dfp, name, cmod, calls):
    """Return (ok, reason). Repoints callers + removes the duplicate def, parse-checked."""
    src = open(dfp, encoding="utf-8").read()
    if calls and f"from {cmod} import {name}" not in src:
        lines = src.splitlines(keepends=True)
        at = import_insert_index(lines)
        lines.insert(at, f"from {cmod} import {name}\n")
        cand = "".join(lines)
        try:
            ast.parse(cand)
        except SyntaxError as e:
            return False, f"import-insert parse fail: {e}"
        src = cand
    # remove the def
    t = ast.parse(src)
    for node in t.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            sl = src.splitlines(keepends=True)
            del sl[node.lineno - 1: getattr(node, "end_lineno", node.lineno)]
            cand = "".join(sl)
            try:
                ast.parse(cand)
            except SyntaxError as e:
                return False, f"def-remove parse fail: {e}"
            open(dfp, "w", encoding="utf-8").write(cand)
            return True, "ok"
    return False, "def-not-found"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = {}
    for dp, _, fs in os.walk(SERVICES):
        for fn in fs:
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            fp = os.path.join(dp, fn)
            res = module_level_funcs(fp)
            if res is not None:
                files[fp] = res

    clusters = {}
    for fp, funcs in files.items():
        for node, lines in funcs:
            key = strip_body(lines, node)
            clusters.setdefault(node.name, {}).setdefault(key, []).append(fp)

    results = []
    for name, bybody in clusters.items():
        for key, fps in bybody.items():
            if len(fps) < 2:
                continue
            canonical = sorted(set(fps), key=lambda p: (len(p.split(os.sep)), p))[0]
            others = [p for p in set(fps) if p != canonical]
            results.append({
                "name": name,
                "canonical": os.path.relpath(canonical, BACKEND),
                "duplicates": [os.path.relpath(o, BACKEND) for o in others],
                "n": len(fps),
            })

    results.sort(key=lambda r: (-r["n"], r["name"]))

    if not args.apply:
        print(json.dumps({"total_clusters": len(results), "clusters": results}, indent=2))
        return

    modified = 0
    skipped = []
    for r in results:
        cfp = os.path.join(BACKEND, r["canonical"])
        cmod = r["canonical"][:-3].replace(os.sep, ".")
        for dup in r["duplicates"]:
            dfp = os.path.join(BACKEND, dup)
            dsrc = open(dfp, encoding="utf-8").read()
            dtree = ast.parse(dsrc)
            calls = any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == r["name"]
                for n in ast.walk(dtree)
            )
            ok, why = apply_one(dfp, r["name"], cmod, calls)
            if ok:
                modified += 1
            else:
                skipped.append({"file": dup, "name": r["name"], "reason": why})

    print(json.dumps({"modified_definitions": modified, "skipped": skipped}, indent=2))


if __name__ == "__main__":
    main()
