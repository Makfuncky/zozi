"""Diff db/media_models.py vs models/media_models.py."""
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
    a = collect(ROOT / "db/media_models.py")
    b = collect(ROOT / "models/media_models.py")
    print("db.media_models classes:", len(a))
    print("models.media_models classes:", len(b))
    print("ONLY in db/ (would be lost):", sorted(set(a) - set(b)) or "none")
    print("ONLY in models/ (extra):", sorted(set(b) - set(a)) or "none")
    print("tables ONLY in db/:", sorted({v for v in a.values() if v} - {v for v in b.values() if v}) or "none")


if __name__ == "__main__":
    main()
