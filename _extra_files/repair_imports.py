"""Repair broken `from M import N` references after dedup consolidation.

For every `from M import N` in the backend, if N is not actually provided by M
(top-level def or re-export) but IS provided by exactly one other module C,
rewrite the import to point at C. Guarded: parse-checked, dry-run by default.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(HERE), "backend")
sys.path.insert(0, BACKEND)


def module_path_to_dotted(fp):
    rel = os.path.relpath(fp, BACKEND)[:-3]
    return rel.replace(os.sep, ".")


def collect():
    provided = {}   # module -> set of provided top-level names
    reexports = {}  # module -> set of imported names (from X import Y)
    files = {}
    for sub in ["services", "routers", "controllers"]:
        base = os.path.join(BACKEND, sub)
        if not os.path.isdir(base):
            continue
        for dp, _, fs in os.walk(base):
            if any(seg.startswith(".") for seg in dp.split(os.sep)):
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    src = open(fp, encoding="utf-8").read()
                    tree = ast.parse(src)
                except Exception:
                    continue
                mod = module_path_to_dotted(fp)
                files[fp] = src
                defs = set()
                imp = set()
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        defs.add(node.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        for a in node.names:
                            imp.add(a.asname or a.name)
                provided[mod] = defs
                reexports[mod] = imp
    return provided, reexports, files


def canonical_for(name, provided):
    owners = [m for m, names in provided.items() if name in names]
    if len(owners) == 1:
        return owners[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    provided, reexports, files = collect()
    # map: name -> canonical module (single owner)
    canon = {}
    for name in set(n for names in provided.values() for n in names):
        c = canonical_for(name, provided)
        if c:
            canon[name] = c

    fixes = []
    for fp, src in files.items():
        mod = module_path_to_dotted(fp)
        tree = ast.parse(src)
        new_src = src
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and not node.module.startswith("."):
                target = node.module
                if target not in provided:
                    continue
                for a in node.names:
                    n = a.asname or a.name
                    if n in provided.get(target, set()) or n in reexports.get(target, set()):
                        continue  # target actually provides it
                    c = canon.get(n)
                    if c and c != target:
                        # rewrite this alias's module
                        line = src.splitlines()[node.lineno - 1]
                        # handle multiline imports minimally: only single-line here
                        new_line = re.sub(r"\b" + re.escape(target) + r"\b", c, line, count=1)
                        if new_line != line:
                            sl = new_src.splitlines(keepends=True)
                            sl[node.lineno - 1] = new_line + ("\n" if not sl[node.lineno-1].endswith("\n") else "")
                            new_src = "".join(sl)
                            changed = True
                            fixes.append((fp, target, c, n))
        if changed:
            try:
                ast.parse(new_src)
            except SyntaxError:
                fixes.append(("PARSE_FAIL", fp, None, None))
                continue
            if args.apply:
                open(fp, "w", encoding="utf-8").write(new_src)

    print("DEBUG len(provided):", len(provided))
    print("DEBUG sample keys:", list(provided)[:5])
    print("DEBUG core key present:", 'services.core.customer_health_service' in provided)
    print("DEBUG customer_health keys:", [k for k in provided if 'customer_health' in k])
    print("DEBUG gch in core defs:", 'get_customer_health' in provided.get('services.core.customer_health_service', set()))
    print("DEBUG canon gch:", canon.get('get_customer_health'))
    print("fixes:", len([f for f in fixes if f and f[0] != "PARSE_FAIL"]))
    for f in fixes[:40]:
        print(f)


if __name__ == "__main__":
    main()
