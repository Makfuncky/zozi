#!/usr/bin/env python3
"""DBA31 fix: add composite index (country_code, created_at) on tables that
have both columns but no composite index and an un-indexed country_code.

Reuses the robust __table_args__ append logic (Tuple / None / BinOp).
"""
import ast
import glob

ROOT = "backend/models"


def line_offsets(text):
    offs, acc = [], 0
    for ln in text.split("\n"):
        offs.append(acc)
        acc += len(ln) + 1
    return offs


def pos(offs, lineno, col):
    return offs[lineno - 1] + col


def node_text(text, offs, node):
    return text[pos(offs, node.lineno, node.col_offset): pos(offs, node.end_lineno, node.end_col_offset)]


def class_columns(cls):
    cols = []
    for stmt in cls.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "Column"):
            cols.append(stmt.targets[0].id)
    return cols


def tablename(cls):
    for stmt in cls.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "__tablename__"
                and isinstance(stmt.value, ast.Constant)):
            return stmt.value.value
    return None


def table_args(cls):
    for stmt in cls.body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "__table_args__"):
            return stmt.value
    return None


def process_file(path):
    text = open(path, encoding="utf-8").read()
    offs = line_offsets(text)
    tree = ast.parse(text)
    edits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cols = class_columns(node)
        if "country_code" not in cols or "created_at" not in cols:
            continue
        ta = table_args(node)
        ta_text = node_text(text, offs, ta) if ta is not None else ""
        if "country_code" in ta_text.lower() and "created_at" in ta_text.lower():
            continue  # composite already present
        table = tablename(node) or node.name.lower()
        idx = 'Index("ix_%s_country_created", "country_code", "created_at")' % table
        if ta is None:
            last = node.body[-1]
            at = pos(offs, last.end_lineno, last.end_col_offset)
            edits.append((at, at, "\n    __table_args__ = (" + idx + ",)"))
        else:
            if isinstance(ta, ast.Tuple):
                begin = pos(offs, ta.lineno, ta.col_offset)
                end = pos(offs, ta.end_lineno, ta.end_col_offset)
                elts = [node_text(text, offs, e) for e in ta.elts]
                items = elts + [idx]
                edits.append((begin, end, "(" + ", ".join(items) + ("," if items else "") + ")"))
            else:
                end = pos(offs, ta.end_lineno, ta.end_col_offset)
                edits.append((end, end, " + (" + idx + ",)"))
    if not edits:
        return "skip"
    edits.sort(key=lambda e: e[0], reverse=True)
    new = text
    for b, e, r in edits:
        new = new[:b] + r + new[e:]
    try:
        ast.parse(new)
    except SyntaxError as ex:
        return "fail:" + str(ex)
    open(path, "w", encoding="utf-8").write(new)
    return "ok"


def main():
    files = sorted(set(glob.glob(ROOT + "/**/*.py", recursive=True) +
                       glob.glob(ROOT + "/*.py")))
    ok = skip = fail = 0
    for f in files:
        if f.endswith("__init__.py"):
            continue
        try:
            r = process_file(f)
        except Exception as e:
            r = "err:" + str(e)
        if r == "skip":
            skip += 1
        elif r == "ok":
            ok += 1
            print("OK  ", f)
        else:
            fail += 1
            print("FAIL", f, r)
    print(f"\nTOTAL ok={ok} skip={skip} fail={fail}")


if __name__ == "__main__":
    main()
