"""Definitive scan for MERGEABLE duplicates across the whole backend (fast v2).

Candidate iff module-level, decorator-free, not in __all__, not dunder,
byte-identical (normalized AST) to one in a DIFFERENT file.
"""
from __future__ import annotations

import ast
import os
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, BACKEND)


def mod_of(rel):
    return rel[:-3].replace("/", ".").replace("\\", ".")


def parent_map(tree):
    p = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            p[child] = node
    return p


def main():
    func_norm = {}
    import_index = {}
    total_funcs = 0
    import time
    t0 = time.time()
    nfiles = 0
    for root, dirs, files in os.walk(os.path.join(BACKEND, "services")):
        if "_extra_files" in root:
            continue
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            nfiles += 1
            if nfiles % 50 == 0:
                sys.stderr.write(f"[{time.time()-t0:.1f}s] scanned {nfiles} files\n")
                sys.stderr.flush()
            rel = os.path.relpath(os.path.join(root, fn), BACKEND)
            try:
                src = open(os.path.join(root, fn), encoding="utf-8").read()
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue
            all_list = set()
            for n in tree.body:
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "__all__":
                    if isinstance(n.value, (ast.List, ast.Tuple)):
                        for el in n.value.elts:
                            if isinstance(el, ast.Constant):
                                all_list.add(el.value)
            imported_basenames = set()
            for n in ast.walk(tree):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    mod = n.module if isinstance(n, ast.ImportFrom) else None
                    if mod:
                        imported_basenames.add(mod.split(".")[-1])
                    for a in n.names:
                        imported_basenames.add(a.name.split(".")[0])
            for b in imported_basenames:
                import_index.setdefault(b, set()).add(rel)
            pm = parent_map(tree)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # enclosing class?
                    cur = node
                    in_class = False
                    par = pm.get(cur)
                    while par is not None:
                        if isinstance(par, ast.ClassDef):
                            in_class = True
                            break
                        par = pm.get(par)
                    if in_class:
                        continue
                    if node.decorator_list:
                        continue
                    if node.name in all_list:
                        continue
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue
                    norm = ast.unparse(node)
                    func_norm.setdefault(norm, []).append((rel, node.name))
                    total_funcs += 1

    groups = []
    for norm, items in func_norm.items():
        seen = set()
        uniq = []
        for rel, name in items:
            k = (rel, name)
            if k in seen:
                continue
            seen.add(k)
            uniq.append((rel, name))
        if len({r for r, _ in uniq}) < 2:
            continue
        groups.append((norm, uniq))

    groups.sort(key=lambda g: -len(g[1]))
    print(f"Scanned module-level funcs: {total_funcs}")
    print(f"TOTAL mergeable groups: {len(groups)}")
    for i, (norm, uniq) in enumerate(groups, 1):
        print(f"\n--- group {i} ({len(uniq)} occ, {len({r for r,_ in uniq})} files) ---")
        scored = []
        for rel, name in uniq:
            mod = mod_of(rel)
            base = mod.split(".")[-1]
            imp = len(import_index.get(base, set()))
            scored.append((imp, rel, name, mod))
        scored.sort(reverse=True)
        for imp, rel, name, mod in scored:
            print(f"   importers={imp:3d}  {rel} :: {name}")
        best = scored[0]
        canon_src = open(os.path.join(BACKEND, best[1]), encoding="utf-8").read()
        safe = True
        for imp, rel, name, mod in scored[1:]:
            cb = mod.split(".")[-1]
            if cb in canon_src and ("import " + cb) in canon_src.replace(".", " "):
                safe = False
        print(f"   -> canonical: {best[1]} :: {best[2]}  (cycle_safe={safe})")


if __name__ == "__main__":
    main()
