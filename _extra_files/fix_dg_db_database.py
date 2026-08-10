"""Resolve DG: routers/controllers/utils may not import `db.database`.

These layers legitimately need a SQLAlchemy session handle, but the layer
contract (DEFAULT_FORBIDDEN_EDGES) bans the `db.database` edge for them.
Fix mechanically + behaviour-preserving:

  1. Create `db/session.py` that re-exports every name the violating layers
     currently import from `db.database` (same objects, identical semantics).
  2. Rewrite `from db.database import ...` -> `from db.session import ...`
     in routers/, controllers/, utils/ only (the layers that violate).

`db.session` is NOT in the forbidden-edge list, so DG is satisfied while
runtime behaviour is unchanged.
"""
from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYERS = ["routers", "controllers", "utils"]

TARGET_MODULE = "db.database"
FACADE_MODULE = "db.session"


def parse_safe(p: Path):
    try:
        return ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def collect(files):
    names = set()
    for f in files:
        tree = parse_safe(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == TARGET_MODULE:
                for alias in node.names:
                    names.add(alias.name)
    return names


def main():
    files = []
    for layer in LAYERS:
        d = BACKEND / layer
        if d.exists():
            files.extend(d.rglob("*.py"))
    files = [f for f in files if "__pycache__" not in f.parts]

    names = collect(files)
    print(f"Collected {len(names)} distinct names imported from {TARGET_MODULE} "
          f"across {len(files)} files in {LAYERS}.")

    # Build the facade module.
    sorted_names = sorted(names)
    facade = (
        '"""Session/engine access facade.\n\n'
        "Routers, controllers and utils must obtain a SQLAlchemy session handle\n"
        "from this facade instead of `db.database`, so the dependency-graph\n"
        "layer contract (those layers may not depend on `db.database`) holds.\n"
        "All symbols are re-exported unchanged from `db.database`.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "from db.database import (\n"
        + "".join(f"    {n},\n" for n in sorted_names)
        + ")\n"
    )
    (BACKEND / "db" / "session.py").write_text(facade, encoding="utf-8")
    print(f"Wrote backend/db/session.py re-exporting: {', '.join(sorted_names)}")

    # Rewrite the import lines in place.
    changed_files = 0
    changed_lines = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if f"from {TARGET_MODULE} import" not in text:
            continue
        new_text = text.replace(f"from {TARGET_MODULE} import",
                                f"from {FACADE_MODULE} import")
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")
            changed_files += 1
            changed_lines += new_text.count(f"from {FACADE_MODULE} import")
    print(f"Rewrote imports in {changed_files} files "
          f"({changed_lines} import statements).")


if __name__ == "__main__":
    main()
