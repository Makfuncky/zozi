"""Normalize __table_args__ tuples so any schema/option dict (e.g. {'schema': 'x'})
is the LAST element. SQLAlchemy 2.0 rejects dicts that are not last. Safe & idempotent.
"""
import ast
import os

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models"


def _unwrap(node):
    # A single-element tuple wrapping a dict: ({'schema': 'x'},) -> {'schema': 'x'}
    if isinstance(node, ast.Tuple) and len(node.elts) == 1 and isinstance(node.elts[0], ast.Dict):
        return node.elts[0]
    return node


def _is_dict_literal(node):
    return isinstance(node, ast.Dict)


def normalize_tree(tree):
    changed = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "__table_args__"):
                continue
            val = stmt.value
            if not isinstance(val, ast.Tuple):
                continue
            # unwrap single-dict tuples
            new_elts = [_unwrap(e) for e in val.elts]
            if [ast.unparse(e) for e in new_elts] != [ast.unparse(e) for e in val.elts]:
                val.elts = new_elts
                changed = True
            dicts = [e for e in val.elts if _is_dict_literal(e)]
            others = [e for e in val.elts if not _is_dict_literal(e)]
            if dicts and len(dicts) != len(val.elts):
                # move dicts to the end, preserving order
                new_elts = others + dicts
                if [ast.unparse(e) for e in new_elts] != [ast.unparse(e) for e in val.elts]:
                    val.elts = new_elts
                    changed = True
    return changed


def run():
    count = 0
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            if not f.endswith(".py"):
                continue
            full = os.path.join(dp, f)
            src = open(full, encoding="utf-8").read()
            tree = ast.parse(src)
            if normalize_tree(tree):
                ast.fix_missing_locations(tree)
                try:
                    with open(full, "w", encoding="utf-8") as fh:
                        fh.write(ast.unparse(tree))
                    count += 1
                    print("normalized", os.path.relpath(full, ROOT))
                except Exception as e:
                    print("WRITE-ERROR", os.path.relpath(full, ROOT), type(e).__name__, e)
    print("TOTAL normalized:", count)


if __name__ == "__main__":
    run()
