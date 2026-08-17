"""Boot probe: import every router module, report failures + route counts.

Read-only diagnostic. Writes JSON to _extra_files/boot_probe.json.
"""
from __future__ import annotations

import glob
import importlib
import json
import os
import sys
import traceback

BACKEND = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(BACKEND), "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

routers_dir = os.path.join(BACKEND, "routers")

results = {"ok": [], "failed": [], "no_router": [], "totals": {}}

for path in sorted(glob.glob(os.path.join(routers_dir, "**", "*.py"), recursive=True)):
    if os.path.basename(path) == "__init__.py":
        continue
    rel = os.path.relpath(path, routers_dir)
    modname = os.path.splitext(rel)[0].replace(os.sep, ".")
    try:
        mod = importlib.import_module(f"routers.{modname}")
    except Exception as exc:  # noqa: BLE001
        results["failed"].append(
            {
                "module": modname,
                "error": f"{type(exc).__name__}: {exc}",
                "tb": traceback.format_exc(limit=6).splitlines()[-6:],
            }
        )
        continue
    router = getattr(mod, "router", None)
    if router is None:
        results["no_router"].append(modname)
        continue
    routes = getattr(router, "routes", [])
    results["ok"].append(
        {
            "module": modname,
            "prefix": getattr(mod, "__router_prefix__", None) or getattr(router, "prefix", ""),
            "route_count": len(routes),
        }
    )

results["totals"] = {
    "modules_scanned": len(results["ok"]) + len(results["failed"]) + len(results["no_router"]),
    "ok": len(results["ok"]),
    "failed": len(results["failed"]),
    "no_router": len(results["no_router"]),
    "declared_routes": sum(r["route_count"] for r in results["ok"]),
}

out = os.path.join(os.path.dirname(BACKEND), "_extra_files", "boot_probe.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2)

print(json.dumps(results["totals"], indent=2))
print("\n--- FAILED ---")
for f in results["failed"]:
    print(f"{f['module']}: {f['error']}")
print("\n--- NO ROUTER ATTR ---")
for n in results["no_router"]:
    print(n)
