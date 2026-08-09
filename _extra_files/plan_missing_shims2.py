"""Accurate AST-based analysis of missing-module imports.

For each of the 24 missing modules, collect the exact symbols routers/other
code import from it (handles multi-line parenthesized `from x import (...)`),
then locate where each symbol is actually DEFINED (def/class) anywhere in the
backend (excluding venv). Outputs a JSON plan used to generate shims.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

BACKEND = Path("backend")

MISSING = [
    "location_service", "models.upload_job", "routers.public_chat_api_access",
    "routers.public_command_center_api_management", "routers.public_effective_permissions_access",
    "routers.public_email_controller_access", "services.admin_analytics_service",
    "services.banner_write_service", "services.commerce_write_service",
    "services.commission_write_service", "services.communication_write_service",
    "services.country_write_service", "services.disputes_write_service",
    "services.employee_write_service", "services.hr_write_service",
    "services.iam_write_service", "services.invoice_write_service",
    "services.logistics_partner_write_service", "services.logistics_write_service",
    "services.misc_write_service", "services.payments_write_service",
    "services.products_write_service", "services.promotion_engine_service",
    "services.users_write_service",
]

MISSING_SET = set(MISSING)

def iter_py():
    for p in BACKEND.rglob("*.py"):
        if "venv" in str(p) or "__pycache__" in str(p):
            continue
        yield p

# 1) gather imported symbols per missing module
imported: dict[str, set[str]] = {m: set() for m in MISSING}
for p in iter_py():
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in MISSING_SET:
            for n in node.names:
                imported[node.module].add(n.name)

# 2) index all top-level defs/classes by name
#    name -> list of (relpath, line)
defs: dict[str, list[str]] = {}
for p in iter_py():
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    rel = p.relative_to(BACKEND).as_posix()
    # module-level
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.setdefault(node.name, []).append(f"{rel}:{node.lineno}")
    # also assignments at module level (e.g. `router = APIRouter()`)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defs.setdefault(t.id, []).append(f"{rel}:{node.lineno}(assign)")

# 3) build plan
plan = {}
for m in MISSING:
    syms = sorted(imported[m])
    entries = []
    for s in syms:
        entries.append({"symbol": s, "defs": defs.get(s, [])})
    plan[m] = entries

# print report
total_missing_sym = 0
for m in MISSING:
    print(f"\n### {m}  ({len(plan[m])} imported symbols)")
    for e in plan[m]:
        s = e["symbol"]
        if e["defs"]:
            print(f"  {s:42s} -> {e['defs'][:3]}")
        else:
            total_missing_sym += 1
            print(f"  {s:42s} -> *** NOT FOUND ***")

print(f"\nTotal imported symbols with NO definition found: {total_missing_sym}")
Path("_extra_files/missing_symbol_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
print("plan saved")
