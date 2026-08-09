"""Find ALL modules imported-but-missing anywhere in the backend.

Unlike scan_router_imports (which stops at first error per module), this
recursively imports every .py file (routers, controllers, services, models)
and collects EVERY 'No module named X' from the tracebacks. This reveals the
full set of missing modules hidden behind cascading imports.
"""
from __future__ import annotations

import importlib, traceback, re
from pathlib import Path

B = Path("backend")
missing = set()
ok = 0
total = 0
for p in B.rglob("*.py"):
    if "venv" in str(p) or "__pycache__" in str(p):
        continue
    rel = p.relative_to(B).with_suffix("").as_posix().replace("/", ".")
    if rel.endswith(".__init__"):
        rel = rel[: -len(".__init__")]
    total += 1
    try:
        importlib.import_module(rel)
        ok += 1
    except Exception as e:
        tb = traceback.format_exc()
        for line in tb.splitlines():
            m = re.search(r"No module named '([^']+)'", line)
            if m:
                missing.add(m.group(1))

print(f"modules scanned={total} ok={ok} missing_distinct={len(missing)}")
miss_sorted = sorted(missing)
for m in miss_sorted:
    print("  ", m)
Path("_extra_files/all_missing_modules.txt").write_text("\n".join(miss_sorted), encoding="utf-8")
