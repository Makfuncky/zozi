"""Import every router module in isolation and report the failure reason.

Unlike `import main` (which stops at the first error and only logs a few), this
iterates ALL router modules so we see every broken import. Prints a compact
table: module -> error-type -> message. Read-only except it writes a report.
"""
from __future__ import annotations

import importlib
import traceback
from pathlib import Path

BACKEND = Path("backend")
routers_dir = BACKEND / "routers"

results = []  # (name, ok, err_type, msg, top_missing_module)
# collect set of "No module named 'X'" across all to find missing service modules
missing_modules = set()

out = Path("_extra_files/router_import_report.txt")

for p in sorted(routers_dir.glob("*.py")):
    name = p.stem
    if name.startswith("_"):
        continue
    mod = f"routers.{name}"
    try:
        importlib.import_module(mod)
        results.append((name, True, "", "", ""))
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        # find deepest "No module named 'X'" in traceback
        miss = None
        for line in tb.splitlines():
            if "No module named" in line:
                import re
                m = re.search(r"No module named '([^']+)'", line)
                if m:
                    miss = m.group(1)
                    missing_modules.add(miss)
        results.append((name, False, type(e).__name__, str(e).splitlines()[0][:120], miss or ""))

fails = [r for r in results if not r[1]]
with out.open("w", encoding="utf-8") as f:
    f.write(f"TOTAL routers: {len(results)}  OK: {len(results)-len(fails)}  FAIL: {len(fails)}\n")
    f.write("\n=== FAILURES ===\n")
    for name, ok, et, msg, miss in fails:
        f.write(f"{name:35s} {et:20s} miss={miss or '-':45s} {msg}\n")
    f.write("\n=== UNIQUE MISSING MODULES (from all tracebacks) ===\n")
    for m in sorted(missing_modules):
        f.write(f"  {m}\n")
print(f"TOTAL routers: {len(results)}  OK: {len(results)-len(fails)}  FAIL: {len(fails)}")
print(f"report -> {out}")
with out.open("w", encoding="utf-8") as f:
    f.write(f"TOTAL={len(results)} OK={len(results)-len(fails)} FAIL={len(fails)}\n")
    for name, ok, et, msg, miss in fails:
        f.write(f"FAIL {name} {et} miss={miss} {msg}\n")
    f.write("MISSING_MODULES:\n")
    for m in sorted(missing_modules):
        f.write(f"  {m}\n")
print(f"\nreport -> {out}")
