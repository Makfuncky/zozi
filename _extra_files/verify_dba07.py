"""Verify how the audit script's FK parser reads ondelete for employee_models.py."""
import sys, ast
sys.path.insert(0, "scripts/system_trackers")
import system_architecture_audit as sa

import pathlib
p = pathlib.Path("backend/models/employee_models.py")
tree = ast.parse(p.read_text(encoding="utf-8"))

# Find the EmployeeTraining class and print its employee_id column parse result
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "EmployeeTraining":
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0].id
                if target in ("employee_id",):
                    if isinstance(stmt.value, ast.Call):
                        info = sa.dba_extract_column(target, stmt.value, stmt.lineno)
                        print(f"{target} @ line {stmt.lineno}: fk_target={info.fk_target!r} fk_ondelete={info.fk_ondelete!r}")

print("---- full model parse (fk columns) ----")
models = sa.dba_parse_models(pathlib.Path("."))
for m in models:
    if m.rel_path.replace("\\", "/").endswith("employee_models.py"):
        for c in m.columns:
            if c.fk_target and "employees.id" in c.fk_target:
                print(f"{m.table}.{c.name} -> target={c.fk_target!r} ondelete={c.fk_ondelete!r} line={c.line}")
