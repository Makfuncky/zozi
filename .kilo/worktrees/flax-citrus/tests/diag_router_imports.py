"""Diagnostic: import every routers/*.py module and report the real failure.

Run from backend/ with the venv python. One-shot investigation only.
"""
import importlib
import pkgutil
import sys
import traceback
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

import routers as routers_pkg  # noqa: E402

ok = 0
fail = 0
summary = {}
details = []
for mod in pkgutil.iter_modules(routers_pkg.__path__):
    name = mod.name
    try:
        importlib.import_module(f"routers.{name}")
        ok += 1
    except Exception as e:  # noqa: BLE001
        fail += 1
        etype = type(e).__name__
        summary.setdefault(etype, []).append(name)
        tb = traceback.format_exc(limit=2)
        details.append(f"FAIL {name} [{etype}]: {e}\n{tb}")

print(f"=== SUMMARY ===\nok={ok} fail={fail}")
for etype, names in sorted(summary.items(), key=lambda kv: -len(kv[1])):
    print(f"{etype}: {len(names)} -> {names}")

print("\n=== DETAILS (first 40) ===")
for d in details[:40]:
    print(d)
