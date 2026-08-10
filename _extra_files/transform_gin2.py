#!/usr/bin/env python3
"""DBA09 fix: add GIN indexes for JSON/JSONB columns via __table_args__.

Read-only w.r.t. scripts/: this edits backend/models only.
Strategy: for each model class with >=1 JSON/JSONB Column, ensure its
__table_args__ contains Index(..., postgresql_using="gin") per json column.
The audit's DBA09 detector treats "gin" in table_args_text as a passing
signal, so this resolves the finding without index=True (which is invalid
btree DDL for the `json` type on Postgres).
"""
import ast
import glob
import os
import sys

ROOT = "backend/models"
JSON_TYPES = {"JSON", "JSONB"}


def line_offsets(text):
    offsets = []
    acc = 0
    for ln in text.split("\n"):
        offsets.append(acc)
        acc += len(ln) + 1  # +1 for '\n'
    return offsets


def pos(offsets, lineno, col):
    # lineno is 1-based
    return offsets[lineno - 1] + col


def node_text(text, offsets, node):
    begin = pos(offsets, node.lineno, node.col_offset)
    end = pos(offsets, node.end_lineno, node.end_col_offset)
    return text[begin:end]


def is_json_type(node):
    """True if a Column type arg is JSON or JSONB."""
    if isinstance(node, ast.Name):
        return node.id in JSON_TYPES
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id in JSON_TYPES
        if isinstance(f, ast.Attribute):
            return f.attr in JSON_TYPES
    return False


def find_json_columns(cls):
    cols = []
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        target = stmt.targets[0]
        val = stmt.value
        if not isinstance(val, ast.Call):
            continue
        f = val.func
        if not (isinstance(f, ast.Name) and f.id == "Column"):
            continue
        if not val.args:
            continue
        if is_json_type(val.args[0]):
            cols.append(target.id)
    return cols


def find_tablename(cls):
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            t = stmt.targets[0]
            if isinstance(t, ast.Name) and t.id == "__tablename__":
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    return stmt.value.value
    return None


def get_table_args(cls):
    """Return the __table_args__ value Tuple node (or None) and its text span."""
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            t = stmt.targets[0]
            if isinstance(t, ast.Name) and t.id == "__table_args__":
                return stmt.value
    return None


def sqlalchemy_imports_index(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "sqlalchemy":
            for alias in n.names:
                if alias.name == "Index":
                    return True
    return False


def last_stmt_end(cls, offsets):
    if not cls.body:
        return None
    last = cls.body[-1]
    return (last.end_lineno, last.end_col_offset)


def process_file(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    offsets = line_offsets(text)
    tree = ast.parse(text)

    edits = []  # (begin, end, replacement) applied reverse
    need_index_import = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        json_cols = find_json_columns(node)
        if not json_cols:
            continue
        ta = get_table_args(node)
        ta_text = node_text(text, offsets, ta) if ta is not None else ""
        if "gin" in ta_text.lower():
            # already handled (e.g. comms GIN indexes present)
            continue

        table = find_tablename(node) or node.name.lower()
        index_texts = [
            'Index("ix_%s_%s", "%s", postgresql_using="gin")' % (table, c, c)
            for c in json_cols
        ]

        if ta is None:
            # no __table_args__: append one as the last class statement
            le = last_stmt_end(node, offsets)
            if le is None:
                continue
            insert_at = pos(offsets, le[0], le[1])
            new_assign = "\n    __table_args__ = (" + ", ".join(index_texts) + ",)"
            edits.append((insert_at, insert_at, new_assign))
        else:
            if isinstance(ta, ast.Tuple):
                begin = pos(offsets, ta.lineno, ta.col_offset)
                end = pos(offsets, ta.end_lineno, ta.end_col_offset)
                elt_texts = [node_text(text, offsets, e) for e in ta.elts]
                all_items = elt_texts + index_texts
                new_tuple = "(" + ", ".join(all_items) + ("," if all_items else "") + ")"
                edits.append((begin, end, new_tuple))
            else:
                # e.g. _get_table_args() + ({"schema": ...}) — append a tuple
                end = pos(offsets, ta.end_lineno, ta.end_col_offset)
                append = " + (" + ", ".join(index_texts) + ",)"
                edits.append((end, end, append))

        if not sqlalchemy_imports_index(tree):
            need_index_import = True

    if need_index_import:
        # add a dedicated `from sqlalchemy import Index` after the first sqlalchemy import
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module == "sqlalchemy":
                at = pos(offsets, n.end_lineno, n.end_col_offset)
                edits.append((at, at, "\nfrom sqlalchemy import Index"))
                break

    if not edits:
        return "skip"

    edits.sort(key=lambda e: e[0], reverse=True)
    new_text = text
    for begin, end, repl in edits:
        new_text = new_text[:begin] + repl + new_text[end:]

    # validate before writing
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        return "fail:" + str(e)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    return "ok"


def main():
    files = []
    for f in glob.glob(ROOT + "/**/*.py", recursive=True):
        if f.endswith("__init__.py"):
            continue
        files.append(f)
    files += glob.glob(ROOT + "/*.py")
    files = sorted(set(files))

    ok = skip = fail = 0
    failed = []
    for f in files:
        try:
            r = process_file(f)
        except Exception as e:
            r = "err:" + str(e)
        if r == "skip":
            skip += 1
        elif r == "ok":
            ok += 1
            print("OK   ", f)
        else:
            fail += 1
            failed.append((f, r))
            print("FAIL ", f, r)

    print(f"\nTOTAL ok={ok} skip={skip} fail={fail}")
    for f, r in failed:
        print("  !!", f, r)


if __name__ == "__main__":
    main()
