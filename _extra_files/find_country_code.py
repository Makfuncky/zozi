from __future__ import annotations
import ast
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
models_dir = BACKEND / "models"

def width_of(col_call):
    for a in col_call.args:
        if isinstance(a, ast.Call) and getattr(a.func, "id", "") == "String":
            if a.args and isinstance(a.args[0], ast.Constant) and isinstance(a.args[0].value, int):
                return a.args[0].value
    for kw in col_call.keywords:
        if kw.arg in ("type", "type_") and isinstance(kw.value, ast.Call) and getattr(kw.value.func, "id", "") == "String":
            if kw.value.args and isinstance(kw.value.args[0], ast.Constant):
                return kw.value.args[0].value
    return None

for f in sorted(models_dir.rglob("*.py")):
    if f.name == "__init__.py":
        continue
    try:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
    except Exception as e:
        print("PARSE ERR", f, e); continue
    for node in tree.body:  # top-level only
        if not isinstance(node, ast.ClassDef):
            continue
        cur_table = None
        for stmt in node.body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                tgt = stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target
                if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                    cur_table = stmt.value.value if isinstance(stmt.value, ast.Constant) else None
        for stmt in node.body:
            # attribute country_code = Column(...)
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if isinstance(tgt, ast.Name) and tgt.id == "country_code":
                    if isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", "") == "Column":
                        w = width_of(stmt.value)
                        if w is not None and w != 3:
                            print(f"{str(f.relative_to(BACKEND))}:{stmt.lineno}  table={cur_table}  String({w})")
                        elif w is None:
                            print(f"{str(f.relative_to(BACKEND))}:{stmt.lineno}  table={cur_table}  width=UNKNOWN")
            # Column("country_code", String(n)) form
            if isinstance(stmt, ast.Assign) and getattr(stmt.value, "func", None) and getattr(stmt.value.func, "id", "") == "Column":
                args = stmt.value.args
                if args and isinstance(args[0], ast.Constant) and args[0].value == "country_code":
                    w = width_of(stmt.value)
                    if w is not None and w != 3:
                        print(f"{str(f.relative_to(BACKEND))}:{stmt.lineno}  table={cur_table}  String({w}) [string-first]")
