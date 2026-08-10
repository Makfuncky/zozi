"""Resolve DG: utils/middleware/dependencies may not import the `models`
top-level package, but may import the `db` layer (only `db.database`,
`db.create_tables`, `db.init_db` are banned for them).

Fix (behaviour-preserving, mirrors the db.session facade):
  1. Create `db/models.py` that re-exports every public name of the `models`
     package (model classes, Base, helpers) unchanged.
  2. Rewrite `from models[.sub] import ...` -> `from db.models import ...`
     in utils/, middleware/, dependencies/ only (the violating layers).
"""
from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYERS = ["utils", "middleware", "dependencies"]
RE = re.compile(r"from models(\.[A-Za-z_][\w.]*)? import")


def main():
    facade = (
        '"""ORM model registry facade.\n\n'
        "Application layers (utils, middleware, dependencies, and any layer that\n"
        "must not depend on the `models` top-level package per the dependency-graph\n"
        "contract) reference ORM model classes through `db.models`. The `db` layer\n"
        "is permitted; only `db.database` / `db.create_tables` / `db.init_db` are\n"
        "banned for those layers. All model classes are re-exported unchanged.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "import types as _types\n"
        "import models as _models\n\n"
        "_g = globals()\n"
        "for _n in dir(_models):\n"
        "    if _n.startswith(\"_\"):\n"
        "        continue\n"
        "    _v = getattr(_models, _n)\n"
        "    if isinstance(_v, _types.ModuleType):\n"
        "        continue\n"
        "    _g[_n] = _v\n"
    )
    (BACKEND / "db" / "models.py").write_text(facade, encoding="utf-8")
    print("Wrote backend/db/models.py")

    changed = 0
    stmts = 0
    for layer in LAYERS:
        d = BACKEND / layer
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            if "from models" not in text:
                continue
            new = RE.sub("from db.models import", text)
            if new != text:
                f.write_text(new, encoding="utf-8")
                changed += 1
                stmts += len(RE.findall(new))
    print(f"Rewrote model imports in {changed} files ({stmts} statements).")


if __name__ == "__main__":
    main()
