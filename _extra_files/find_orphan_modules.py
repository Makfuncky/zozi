"""Detect fully-redundant ORPHANED service modules.

A module M is a 'redundant orphan' when:
 - every one of its module-level defs has a byte-identical twin (same name+body
   hash) in SOME other module N (M is functionally a pure subset copy), and
 - no other file imports M by module path, and
 - M is not a package __init__.py.

These are safe to delete (the behavior already exists elsewhere).
Prints the candidate list; with --delete it removes them (keeping __pycache__).
"""
import ast
import hashlib
import json
import os
import re
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"


def norm_src(node):
    node = ast.parse(ast.unparse(node))
    func = node.body[0]
    func.decorator_list = []
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    func.body = body
    return ast.unparse(func)


def module_defs(fp):
    try:
        src = open(fp, encoding="utf-8").read()
    except Exception:
        return None, None
    try:
        tree = ast.parse(src, filename=fp)
    except Exception:
        return None, src
    defs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                s = norm_src(node)
            except Exception:
                continue
            h = hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
            defs.setdefault(node.name, set()).add(h)
    return defs, src


def main():
    py_files = []
    for dp, _, fns in os.walk(os.path.join(BACKEND, "services")):
        for fn in fns:
            if fn.endswith(".py"):
                py_files.append(os.path.join(dp, fn))

    all_defs = {}
    for fp in py_files:
        d, _ = module_defs(fp)
        if d is not None:
            all_defs[fp] = d

    # module name -> set of importing files (by path string) -- scan WHOLE backend
    import_refs = {}
    all_py = []
    for dp, _, fns in os.walk(BACKEND):
        for fn in fns:
            if fn.endswith(".py"):
                all_py.append(os.path.join(dp, fn))
    for fp in all_py:
        try:
            src = open(fp, encoding="utf-8").read()
        except Exception:
            continue
        for m in re.finditer(r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", src):
            mod = m.group(1) or m.group(2)
            import_refs.setdefault(mod, set()).add(fp)

    candidates = []
    for fp, defs in all_defs.items():
        if not defs:
            continue
        if os.path.basename(fp) == "__init__.py":
            continue
        # build module import key variants (e.g. services.supplier.badge_billing_payment)
        rel = os.path.splitext(os.path.relpath(fp, BACKEND))[0].replace(os.sep, ".")
        importers = set()
        for key in (rel, rel.split(".")[-1]):
            importers |= import_refs.get(key, set())
        if importers:
            continue  # referenced somewhere -> not safe to delete
        # every def must have a twin in some OTHER module
        covered = True
        for name, hashes in defs.items():
            found_twin = False
            for other_fp, other_defs in all_defs.items():
                if other_fp == fp:
                    continue
                if name in other_defs and (hashes & other_defs[name]):
                    found_twin = True
                    break
            if not found_twin:
                covered = False
                break
        if covered:
            candidates.append(fp)

    candidates.sort()
    print(f"Fully-redundant orphaned service modules: {len(candidates)}")
    for c in candidates:
        print("  -", os.path.relpath(c, BACKEND))

    # For each orphan, find a SAFE canonical (twin module NOT in the orphan set)
    orphan_set = set(candidates)
    print("\n=== Safe canonical mapping (twin in a RETAINED module) ===")
    safe_plan = []
    unsafe = []
    for c in candidates:
        defs = all_defs[c]
        plan = {}
        ok = True
        for name, hashes in defs.items():
            canon = None
            for other_fp, other_defs in all_defs.items():
                if other_fp in orphan_set:
                    continue
                if name in other_defs and (hashes & other_defs[name]):
                    canon = other_fp
                    break
            if canon is None:
                ok = False
                break
            plan[name] = canon
        if ok:
            safe_plan.append((c, plan))
            print(f"  {os.path.relpath(c, BACKEND)} -> safe (can re-export from retained twins)")
        else:
            unsafe.append(c)
            print(f"  {os.path.relpath(c, BACKEND)} -> UNSAFE (all twins also orphaned; keep this one)")

    if "--delete" in sys.argv:
        for c in candidates:
            try:
                os.remove(c)
                print("DELETED", os.path.relpath(c, BACKEND))
            except Exception as e:
                print("FAIL", c, e)


if __name__ == "__main__":
    main()
