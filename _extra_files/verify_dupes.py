"""Verify true-duplicate functions across services/ by AST body hashing.

Emits a JSON report of (name, normalized-body-hash) collisions that occur in
TWO OR MORE distinct files. This is the ground truth for the "450 true
duplicates" claim in ARCHITECTURE_MIGRATION_REPORT.md.
"""
import ast
import hashlib
import json
import os
import sys

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\services"
OUT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\verified_duplicates.json"


def norm_src(node):
    """Stable textual form of a function, ignoring decorator lines and docstring."""
    # drop decorators
    node = ast.parse(ast.unparse(node))
    func = node.body[0]
    func.decorator_list = []
    # drop leading docstring (first expr if it's a Str)
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    func.body = body
    return ast.unparse(func)


def visit(path, tree, results):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                src = norm_src(node)
            except Exception:
                continue
            h = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
            results.setdefault(node.name, {}).setdefault(h, []).append(
                {"file": path, "lineno": node.lineno, "src_len": len(src)}
            )
        elif isinstance(node, ast.ClassDef):
            # also scan methods
            sub = ast.Module(body=node.body, type_ignores=[])
            visit(path, sub, results)


def main():
    results = {}
    files = []
    for dirpath, _, fnames in os.walk(ROOT):
        for fn in fnames:
            if fn.endswith(".py"):
                fp = os.path.join(dirpath, fn)
                files.append(fp)
                try:
                    tree = ast.parse(open(fp, encoding="utf-8").read(), filename=fp)
                except Exception as e:
                    print(f"PARSE FAIL {fp}: {e}", file=sys.stderr)
                    continue
                visit(fp, tree, results)

    # Collapse to cross-file collisions
    collisions = []
    for name, hashes in results.items():
        for h, occ in hashes.items():
            files_in = sorted({o["file"] for o in occ})
            if len(files_in) >= 2:
                collisions.append(
                    {
                        "name": name,
                        "hash": h,
                        "files": files_in,
                        "occurrences": len(occ),
                    }
                )

    collisions.sort(key=lambda c: (c["name"], c["files"][0]))
    out = {
        "files_scanned": len(files),
        "total_named_functions": sum(len(h) for h in results.values()),
        "cross_file_dupe_groups": len(collisions),
        "collisions": collisions,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Scanned {len(files)} files")
    print(f"Distinct named functions: {out['total_named_functions']}")
    print(f"Cross-file IDENTICAL groups: {len(collisions)}")
    # quick function-name count of groups
    names = {}
    for c in collisions:
        names[c["name"]] = names.get(c["name"], 0) + 1
    print("Top repeated names:", sorted(names.items(), key=lambda x: -x[1])[:20])


if __name__ == "__main__":
    main()
