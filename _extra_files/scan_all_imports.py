import importlib, os, sys, traceback
from pathlib import Path

ROOT = Path("D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules", "tests", "alembic", "_migration_trash", ".pytest_cache", ".hypothesis"}

def mods():
    out = []
    for p in ROOT.rglob("*.py"):
        if any(part in EXCLUDE for part in p.parts):
            continue
        rel = p.relative_to(ROOT)
        if rel.name == "__init__.py":
            parts = rel.parts[:-1]
        else:
            parts = rel.with_suffix("").parts
        out.append((".".join(parts), p))
    return out

results = []
for modname, path in mods():
    try:
        importlib.import_module(modname)
    except Exception as e:
        tb = traceback.format_exc(limit=1)
        # find the most relevant ImportError line
        msg = str(e)
        results.append((modname, msg))

for m, msg in sorted(results):
    print(f"BROKEN\t{m}\t{msg}")
print(f"\nTOTAL BROKEN: {len(results)}")
