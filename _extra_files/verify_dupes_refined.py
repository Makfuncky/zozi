"""Fast refined duplicate analyzer.

Reads each .py file ONCE, captures AST defs (module-level + methods) and a
word Counter for reference analysis. Then classifies cross-file identical
groups and reports external references for module-level ones.
"""
import ast
import hashlib
import json
import os
import re
from collections import Counter

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
OUT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\verified_duplicates_refined.json"

WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def norm_src(node):
    node = ast.parse(ast.unparse(node))
    func = node.body[0]
    func.decorator_list = []
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    func.body = body
    return ast.unparse(func)


def main():
    files = []
    for dp, _, fns in os.walk(BACKEND):
        if "node_modules" in dp or "venv" in dp or "__pycache__" in dp:
            continue
        for fn in fns:
            if fn.endswith(".py"):
                files.append(os.path.join(dp, fn))

    defs = {}      # (name, hash) -> [ {file, scope, cls, lineno} ]
    file_words = {}  # file -> Counter of words
    for fp in files:
        try:
            src = open(fp, encoding="utf-8").read()
        except Exception:
            continue
        file_words[fp] = Counter(WORD_RE.findall(src))
        try:
            tree = ast.parse(src, filename=fp)
        except Exception:
            continue
        scan(fp, tree, defs)

    # cross-file groups
    groups = []
    for (name, h), occ in defs.items():
        fset = sorted({o["file"] for o in occ})
        if len(fset) < 2:
            continue
        if name.startswith("__") and name.endswith("__"):
            kind = "dunder"
        elif any(o["scope"] != "module" for o in occ):
            kind = "mixed_or_method"
        else:
            kind = "module_level"
        ext_files = []
        ext_total = 0
        if kind == "module_level":
            for fp, cnt in file_words.items():
                c = cnt.get(name, 0)
                if c and fp not in fset:
                    ext_files.append(fp)
                    ext_total += c
        groups.append({
            "name": name, "hash": h, "kind": kind,
            "occurrences": len(occ),
            "files": [{"file": o["file"], "scope": o["scope"], "cls": o.get("cls"), "lineno": o["lineno"]} for o in occ],
            "external_ref_files": sorted(ext_files),
            "external_ref_count": ext_total,
        })

    groups.sort(key=lambda g: (g["kind"] != "module_level", g["name"]))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"groups": groups}, f, indent=2)

    by_kind = {}
    for g in groups:
        by_kind[g["kind"]] = by_kind.get(g["kind"], 0) + 1
    print(f"Total cross-file groups: {len(groups)}  by_kind={by_kind}")
    print("\n=== MODULE-LEVEL (safe consolidation candidates) ===")
    for g in groups:
        if g["kind"] == "module_level":
            rels = [os.path.relpath(o["file"], BACKEND) + f":{o['lineno']}" for o in g["files"]]
            print(f"{g['name']}  occ={g['occurrences']} ext_refs={g['external_ref_count']}")
            for r in rels:
                print(f"    - {r}")


def scan(scan_fp, tree, defs, classname=None):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                src = norm_src(node)
            except Exception:
                continue
            h = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
            scope = "module" if classname is None else "method"
            defs.setdefault((node.name, h), []).append(
                {"file": scan_fp, "scope": scope, "cls": classname, "lineno": node.lineno}
            )
        elif isinstance(node, ast.ClassDef):
            sub = ast.Module(body=node.body, type_ignores=[])
            scan(scan_fp, sub, defs, node.name)


if __name__ == "__main__":
    main()
