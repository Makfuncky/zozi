"""For each missing module, find the exact symbols routers import from it,
then locate where each symbol is actually DEFINED in the codebase.

Output: a plan dict (module -> [(symbol, defined_in_file, line)]).
This does NOT modify anything; it's an analysis step.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

BACKEND = Path("backend")

# The 24 missing modules reported by scan_router_imports.py
MISSING = [
    "location_service",
    "models.upload_job",
    "routers.public_chat_api_access",
    "routers.public_command_center_api_management",
    "routers.public_effective_permissions_access",
    "routers.public_email_controller_access",
    "services.admin_analytics_service",
    "services.banner_write_service",
    "services.commerce_write_service",
    "services.commission_write_service",
    "services.communication_write_service",
    "services.country_write_service",
    "services.disputes_write_service",
    "services.employee_write_service",
    "services.hr_write_service",
    "services.iam_write_service",
    "services.invoice_write_service",
    "services.logistics_partner_write_service",
    "services.logistics_write_service",
    "services.misc_write_service",
    "services.payments_write_service",
    "services.products_write_service",
    "services.promotion_engine_service",
    "services.users_write_service",
]

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

# 1) Collect symbols imported FROM each missing module, by scanning all .py for
#    `from <missing> import (...)` / `from <missing> import a, b`
#    and `import <missing> as X` (the latter we can't know symbols for; skip).
imported_from = {m: set() for m in MISSING}
mod_pat = re.compile(r"^from\s+(" + "|".join(re.escape(m) for m in MISSING) + r")\s+import\s+(.+)$")
for p in BACKEND.rglob("*.py"):
    if "venv" in str(p) or "__pycache__" in str(p):
        continue
    txt = read(p)
    for line in txt.splitlines():
        m = mod_pat.match(line.strip())
        if not m:
            continue
        mod = m.group(1)
        rest = m.group(2)
        # handle parenthesized multi-line not captured here; best-effort single line
        # remove parentheses and split on commas
        rest = rest.strip()
        if rest.startswith("("):
            rest = rest[1:]
        if rest.endswith(")"):
            rest = rest[:-1]
        for sym in rest.split(","):
            sym = sym.strip()
            if not sym:
                continue
            # strip "as alias"
            sym = sym.split(" as ")[0].strip()
            if sym and re.match(r"^[A-Za-z_]\w*$", sym):
                imported_from[mod].add(sym)

# 2) For each missing module + symbol, find definition across backend (excluding venv).
def find_def(sym):
    hits = []
    pat = re.compile(r"^\s*(async\s+)?def\s+" + re.escape(sym) + r"\s*\(")
    pat_cls = re.compile(r"^\s*class\s+" + re.escape(sym) + r"\b")
    for p in BACKEND.rglob("*.py"):
        if "venv" in str(p) or "__pycache__" in str(p):
            continue
        txt = read(p)
        for i, line in enumerate(txt.splitlines(), 1):
            if pat.match(line) or pat_cls.match(line):
                hits.append(f"{p.relative_to(BACKEND).as_posix()}:{i}")
    return hits

plan = {}
for mod in MISSING:
    syms = sorted(imported_from[mod])
    plan[mod] = []
    for s in syms:
        locs = find_def(s)
        plan[mod].append({"symbol": s, "defs": locs})

# Print summary
for mod in MISSING:
    print(f"\n### {mod}  ({len(plan[mod])} symbols imported)")
    for item in plan[mod]:
        s = item["symbol"]
        if item["defs"]:
            # show first 3 def locations
            locs = item["defs"][:3]
            print(f"  {s:40s} -> {locs}")
        else:
            print(f"  {s:40s} -> *** NOT FOUND ANYWHERE ***")

# Save raw plan
Path("_extra_files/missing_symbol_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
print("\nplan saved -> _extra_files/missing_symbol_plan.json")
