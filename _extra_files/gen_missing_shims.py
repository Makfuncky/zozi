"""Generate thin re-export shim modules for the 24 missing modules.

Strategy: for each missing module M importing symbol S, find S's definition.
Prefer the "canonical" file (a real *_write_service.py under the matching
services subpackage, or routers/controllers file). Emit M as a re-export shim.

This is additive only (creates files that did not exist). It does NOT touch
any router/controller. After generation, re-run scan_router_imports.py to
confirm the routers resolve.

Heuristic for canonical source of a symbol:
  * If a file matching the missing module leaf under a subpackage exists
    (e.g. services/geography/country_write_service.py), prefer it.
  * Else prefer a definition file whose path contains 'service' or matches
    the module domain, else the first definition found.
  * If no definition found anywhere, emit a stub that raises NotImplementedError
    (so the module imports; failures surface at call time, not import time).
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

BACKEND = Path("backend")
PLAN = Path("_extra_files/missing_symbol_plan.json")

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

# Canonical subpackage hint: missing module -> likely real file (relative to backend)
CANON = {
    "services.country_write_service": "services/geography/country_write_service.py",
    "services.communication_write_service": "services/comms/communication_write_service.py",
    "services.commission_write_service": "services/commission/commission_write_service.py",
    "services.payments_write_service": "services/payments/payments_write_service.py",
    "services.products_write_service": "services/products/products_write_service.py",
    "services.employee_write_service": "services/employees/employee_write_service.py",
    "services.hr_write_service": "services/hr/hr_write_service.py",
    "services.iam_write_service": "services/iam/iam_write_service.py",
    "services.invoice_write_service": "services/invoices/invoice_write_service.py",
    "services.logistics_write_service": "services/logistics/logistics_write_service.py",
    "services.logistics_partner_write_service": "services/logistics/logistics_partner_write_service.py",
    "services.banner_write_service": "services/banners/banner_write_service.py",
    "services.commerce_write_service": "services/commerce/commerce_write_service.py",
    "services.disputes_write_service": "services/disputes/disputes_write_service.py",
    "services.users_write_service": "services/users/users_write_service.py",
    "services.misc_write_service": "services/misc/misc_write_service.py",
    "services.admin_analytics_service": "services/admin/admin_analytics_service.py",
    "services.promotion_engine_service": "services/promotions/promotion_engine_service.py",
    "models.upload_job": "models/upload_job.py",
    "routers.public_chat_api_access": "routers/chat_api.py",
    "routers.public_command_center_api_management": "routers/command_center_api.py",
    "routers.public_email_controller_access": "routers/email_controller.py",
    "routers.public_effective_permissions_access": "routers/effective_permissions.py",
    "location_service": "services/location_service.py",
}

# Symbols that should come from a specific helper regardless of other defs
ALWAYS = {
    "commit_and_refresh": "services.write_helpers",
    "add_and_flush": "services.write_helpers",
    "commit_only": "services.write_helpers",
}

# ---- index definitions ----
defs: dict[str, list[str]] = {}
for p in BACKEND.rglob("*.py"):
    if "venv" in str(p) or "__pycache__" in str(p):
        continue
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    rel = p.relative_to(BACKEND).as_posix()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.setdefault(node.name, []).append(rel)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defs.setdefault(t.id, []).append(rel)


def choose_source(mod: str, sym: str) -> str | None:
    if sym in ALWAYS:
        return ALWAYS[sym]
    if mod in CANON:
        canon = CANON[mod]
        if canon in defs.get(sym, []):
            return canon
    # prefer a def location whose path contains the module leaf (minus services./routers.)
    leaf = mod.split(".")[-1]
    cands = defs.get(sym, [])
    for c in cands:
        if leaf in c:
            return c
    # prefer a 'service' file
    for c in cands:
        if "service" in c:
            return c
    # prefer routers/controllers
    for c in cands:
        if c.startswith("routers/") or c.startswith("controllers/"):
            return c
    return cands[0] if cands else None


plan = json.loads(PLAN.read_text(encoding="utf-8"))

created = []
for mod in MISSING:
    syms = [e["symbol"] for e in plan.get(mod, [])]
    if not syms:
        # still create a placeholder so imports resolve (empty module)
        syms = []
    # determine source per symbol
    mapping = {}  # sym -> source module path (dotted)
    stubbed = []
    for s in syms:
        src = choose_source(mod, s)
        if src is None:
            stubbed.append(s)
            continue
        dotted = src[:-3].replace("/", ".").lstrip(".")
        mapping[s] = dotted

    # build file content
    target_path = BACKEND / (mod.replace(".", "/") + ".py")
    lines = [
        '"""Generated re-export shim.',
        '',
        f'This module was missing after a refactor that relocated handlers into',
        f'subpackage service modules. It re-exports the symbols from their',
        f'canonical locations so legacy imports (e.g. `from {mod} import ...`)',
        f'keep resolving. Prefer importing from the canonical module directly',
        f'in new code.',
        '"""',
        "from __future__ import annotations",
        "",
    ]
    # group imports by source to keep clean
    by_src: dict[str, list[str]] = {}
    for s, src in mapping.items():
        by_src.setdefault(src, []).append(s)
    for src, ss in sorted(by_src.items()):
        ss_sorted = sorted(set(ss))
        if len(ss_sorted) == 1:
            lines.append(f"from {src} import {ss_sorted[0]}")
        else:
            lines.append(f"from {src} import (")
            for s in ss_sorted:
                lines.append(f"    {s},")
            lines.append(")")
        lines.append("")
    if stubbed:
        lines.append("# The following symbols were referenced but have NO definition")
        lines.append("# anywhere in the codebase. They are stubbed to fail loudly at")
        lines.append("# call time rather than break import of this module.")
        lines.append("def _missing_symbol(name):")
        lines.append("    def _f(*_a, **_k):")
        lines.append("        raise NotImplementedError(")
        lines.append("            f\"'{mod}.{name}' is not implemented (refactor gap)\")")
        lines.append("    return _f")
        lines.append("")
        for s in sorted(set(stubbed)):
            lines.append(f"{s} = _missing_symbol({s!r})")
        lines.append("")
    lines.append("")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("\n".join(lines), encoding="utf-8")
    created.append((mod, len(mapping), len(stubbed)))

print("Generated shims:")
for mod, n, st in created:
    print(f"  {mod:42s} reexports={n} stubbed={st}")
print(f"\nTotal: {len(created)} modules created")
