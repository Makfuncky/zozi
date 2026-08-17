"""Include probe: replicate main._load_routers() and record per-router include failures.

Read-only diagnostic. Writes JSON to _extra_files/include_probe.json.
"""
from __future__ import annotations

import glob
import importlib
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(HERE), "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from fastapi import FastAPI  # noqa: E402

app = FastAPI()

routers_dir = os.path.join(BACKEND, "routers")
report = {"import_failed": [], "include_failed": [], "included": [], "totals": {}}

for path in sorted(glob.glob(os.path.join(routers_dir, "**", "*.py"), recursive=True)):
    if os.path.basename(path) == "__init__.py":
        continue
    rel = os.path.relpath(path, routers_dir)
    modname = os.path.splitext(rel)[0].replace(os.sep, ".")
    try:
        mod = importlib.import_module(f"routers.{modname}")
    except Exception as exc:  # noqa: BLE001
        report["import_failed"].append({"module": modname, "error": f"{type(exc).__name__}: {exc}"})
        continue
    router = getattr(mod, "router", None)
    if router is None:
        continue
    prefix = getattr(mod, "__router_prefix__", None)
    declared = len(getattr(router, "routes", []))
    before = len(app.routes)
    try:
        if prefix:
            app.include_router(router, prefix=prefix)
        else:
            app.include_router(router)
        after = len(app.routes)
        report["included"].append(
            {"module": modname, "declared": declared, "added": after - before}
        )
    except Exception as exc:  # noqa: BLE001
        after = len(app.routes)
        report["include_failed"].append(
            {
                "module": modname,
                "declared": declared,
                "added_before_failure": after - before,
                "error": f"{type(exc).__name__}: {exc}",
                "tb_tail": traceback.format_exc().strip().splitlines()[-4:],
            }
        )

report["totals"] = {
    "import_failed": len(report["import_failed"]),
    "include_failed": len(report["include_failed"]),
    "included_ok": len(report["included"]),
    "declared_total": sum(r["declared"] for r in report["included"])
    + sum(r["declared"] for r in report["include_failed"]),
    "app_routes": len(app.routes),
    "lost_routes": sum(
        r["declared"] - r["added_before_failure"] for r in report["include_failed"]
    ),
}

out = os.path.join(HERE, "include_probe.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)

print(json.dumps(report["totals"], indent=2))
print("\n--- INCLUDE FAILURES (grouped by error) ---")
groups: dict[str, list[str]] = {}
for f in report["include_failed"]:
    groups.setdefault(f["error"], []).append(f["module"])
for err, mods in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print(f"\n[{len(mods)}] {err}")
    for m in mods[:15]:
        print(f"    - {m}")
    if len(mods) > 15:
        print(f"    ... +{len(mods) - 15} more")
