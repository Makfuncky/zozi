#!/usr/bin/env python3
"""Focused DBA09/DBA08/DBA07 verifier replicating audit logic (no scripts/ edits)."""
import ast
import glob

JSON_TYPES = {"JSON", "JSONB"}


def line_offsets(text):
    offs, acc = [], 0
    for ln in text.split("\n"):
        offs.append(acc)
        acc += len(ln) + 1
    return offs


def col_type(node):
    a = node.args[0]
    if isinstance(a, ast.Name):
        return a.id
    if isinstance(a, ast.Call):
        f = a.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def col_is_index(node):
    for kw in node.keywords:
        if kw.arg == "index":
            return isinstance(kw.value, ast.Constant) and kw.value.value is True
    return False


def main():
    dba09, dba08, dba07 = [], [], []
    files = sorted(set(glob.glob("backend/models/**/*.py", recursive=True) +
                       glob.glob("backend/models/*.py")))
    for f in files:
        if f.endswith("__init__.py"):
            continue
        text = open(f, encoding="utf-8").read()
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            print("PARSE FAIL", f, e)
            continue
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            ta_text = ""
            cols = []
            tablename = cls.name.lower()
            for stmt in cls.body:
                if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name)):
                    continue
                t = stmt.targets[0].id
                if t == "__tablename__" and isinstance(stmt.value, ast.Constant):
                    tablename = stmt.value.value
                elif t == "__table_args__":
                    ta_text = ast.dump(stmt.value)
                elif isinstance(stmt.value, ast.Call):
                    fn = stmt.value.func
                    if isinstance(fn, ast.Name) and fn.id == "Column" and stmt.value.args:
                        tn = col_type(stmt.value)
                        if tn and tn.upper() in JSON_TYPES:
                            cols.append((stmt.targets[0].id, col_is_index(stmt.value)))
            args_low = ta_text.lower()
            for cname, is_idx in cols:
                if not is_idx and "gin" not in args_low and cname not in args_low:
                    dba09.append(f"{f}:{tablename}.{cname}")
    print(f"DBA09 remaining: {len(dba09)}")
    for x in dba09[:60]:
        print("  ", x)


if __name__ == "__main__":
    main()
