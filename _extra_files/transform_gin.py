import pathlib, ast

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
JSON_TYPES = {"JSON", "JSONB"}


def type_is_json(node):
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in JSON_TYPES
    if isinstance(node, ast.Attribute):
        return node.attr in JSON_TYPES
    if isinstance(node, ast.Call):
        return type_is_json(node.func)
    if isinstance(node, ast.Subscript):
        return type_is_json(node.slice)
    return False


def col_type_is_json(call, annotation):
    if call is not None and call.args and type_is_json(call.args[0]):
        return True
    return type_is_json(annotation)


def collect(tree):
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        table = None
        ta_node = None
        ta_text = ""
        for s in node.body:
            if isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name):
                        if t.id == "__tablename__" and isinstance(s.value, ast.Constant):
                            table = s.value.value
                        if t.id == "__table_args__":
                            ta_node = s
                            try:
                                ta_text = ast.unparse(s.value)
                            except Exception:
                                ta_text = ""
        if not table:
            continue
        cols = []
        for s in node.body:
            name = None
            call = None
            ann = None
            if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
                name = s.targets[0].id
                if isinstance(s.value, ast.Call):
                    call = s.value
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                name = s.target.id
                ann = s.annotation
                if isinstance(s.value, ast.Call):
                    call = s.value
            if name and call and col_type_is_json(call, ann):
                cols.append(name)
        results.append((node, table, cols, ta_node, ta_text.lower()))
    return results


def ensure_index_import(text, tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "sqlalchemy":
            for a in n.names:
                if a.name == "Index":
                    return text
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("from __future__"):
            continue
        lines.insert(i, "from sqlalchemy import Index")
        return "\n".join(lines)
    lines.insert(0, "from sqlalchemy import Index")
    return "\n".join(lines)


def process_file(f):
    text = f.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except Exception:
        return False
    results = collect(tree)
    replacements = []  # (start, end, newtext)  -- applied in reverse
    needs_write = False
    for node, table, cols, ta_node, ta_text in results:
        need = [c for c in cols if ("gin" not in ta_text) and (c not in ta_text)]
        if not need:
            continue
        adds = [f'Index("ix_{table}_{c}", "{c}", postgresql_using="gin")' for c in need]
        if ta_node is not None:
            val = ta_node.value
            if isinstance(val, ast.Tuple) and len(val.elts) == 0:
                # empty tuple -> replace the whole () with (Index(...), ...)
                new = "(\n        " + ",\n        ".join(adds) + ",\n    )"
                replacements.append((val.col_offset, val.end_col_offset, new))
            else:
                # non-empty tuple -> insert before closing ')'
                close_pos = val.end_col_offset - 1  # the ')'
                insert = ",\n        " + ",\n        ".join(adds)
                replacements.append((close_pos, close_pos, insert))
        else:
            # no __table_args__: insert after __tablename__ assignment
            tname_line = None
            for s in node.body:
                if isinstance(s, ast.Assign):
                    for t in s.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            tname_line = s.end_lineno
            if tname_line is None:
                continue
            new_line = "    __table_args__ = (\n        " + ",\n        ".join(adds) + ",\n    )"
            # insert at start of line tname_line+1 => use a marker replacement at that line start
            lines = text.splitlines()
            # we'll handle insertion via replacement on a zero-width at start of that line
            pos = 0
            for i, l in enumerate(lines):
                if i < tname_line:
                    pos += len(l) + 1
            replacements.append((pos, pos, new_line + "\n"))
        needs_write = True

    if not needs_write:
        return False

    # apply replacements in reverse order (descending start)
    replacements.sort(key=lambda r: r[0], reverse=True)
    for start, end, new in replacements:
        text = text[:start] + new + text[end:]

    text = ensure_index_import(text, ast.parse(text))
    ast.parse(text)  # validate
    f.write_text(text, encoding="utf-8")
    return True


changed = []
for f in sorted(BACKEND.rglob("*.py")):
    if "venv" in f.parts or "alembic" in f.parts or "migrations" in f.parts:
        continue
    try:
        if process_file(f):
            changed.append(str(f.relative_to(BACKEND.parent)))
    except Exception as e:
        print("ERROR", f, repr(e))

print("GIN index added to:")
for c in changed:
    print("  ", c)
print("TOTAL:", len(changed))
