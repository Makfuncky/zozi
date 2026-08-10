"""Diff db/employee_models.py vs models/employee_models.py (class + table level)."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")


def collect(path: Path) -> dict[str, str | None]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    out: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            table = None
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            if isinstance(stmt.value, ast.Constant):
                                table = str(stmt.value.value)
            out[node.name] = table
    return out


def main() -> None:
    a = collect(ROOT / "db/employee_models.py")
    b = collect(ROOT / "models/employee_models.py")
    print("db.employee_models classes:", len(a))
    print("models.employee_models classes:", len(b))
    print("ONLY in db/ (would be lost if deleted):", sorted(set(a) - set(b)) or "none")
    print("ONLY in models/ (extra):", sorted(set(b) - set(a)) or "none")
    atab = {v for v in a.values() if v}
    btab = {v for v in b.values() if v}
    print("db tables:", len(atab), "models tables:", len(btab))
    print("tables ONLY in db/:", sorted(atab - btab) or "none")
    # total union table count
    print("union tables:", len(atab | btab))


if __name__ == "__main__":
    main()
