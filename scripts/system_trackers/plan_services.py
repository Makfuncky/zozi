"""Plan placement of flat services/ files into domain subfolders (read-only analysis).

Emits scripts/system_trackers/_services_plan.json and a report. No files moved.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
SERVICES = BACKEND / "services"
AUDIT = REPO / "scripts" / "system_trackers" / "system_architecture_audit.py"

spec = importlib.util.spec_from_file_location("arch_audit", AUDIT)
arch = importlib.util.module_from_spec(spec)
sys.modules["arch_audit"] = arch
spec.loader.exec_module(arch)
KEYWORDS: dict[str, set[str]] = arch.PLACEMENT_DOMAIN_KEYWORDS

ALIAS: dict[str, str] = {}
for dom, aliases in KEYWORDS.items():
    ALIAS[dom.lower()] = dom
    for a in aliases:
        ALIAS[str(a).lower()] = dom

EXISTING = {p.name for p in SERVICES.iterdir() if p.is_dir() and p.name != "__pycache__"}

FOLDER_FOR_DOMAIN = {
    "finance": "finance", "treasury": "treasury", "gateway": "gateways",
    "orders": "orders", "catalog": "catalog", "commerce": "commerce",
    "supplier": "supplier", "customer": "customer", "logistics": "logistics",
    "comms": "comms", "hr": "hr", "ai": "ai", "audit": "audit",
    "security": "security", "identity": "users", "geography": "geography",
    "media": "common", "analytics": "analytics", "configuration": "common",
    "inventory": "common", "pricing": "common", "reviews": "commerce",
    "search": "catalog", "events": "common", "webhooks": "gateways",
    "documents": "common", "reporting": "analytics", "shipping": "logistics",
    "billing": "finance", "notifications": "comms", "permissions": "security",
    "hierarchy": "hierarchy", "location": "location",
    "location_service": "location_service", "mcp": "mcp",
    "promotions": "promotions", "employee": "employee",
}

SCRATCH = {"script1", "run_py", "template", "maker",
           "write_files_script", "write_help", "write_helpers"}

# explicit overrides for ambiguous stems (matched after keyword logic)
OVERRIDE = {
    "command_center_service": "common", "command_center_background": "common",
    "confidence_scoring": "analytics", "content_service": "comms",
    "credit_control_service": "finance", "data_residency": "security",
    "data_residency_service": "security", "db_read": "common", "db_write": "common",
    "downstream_hooks": "common", "downstream_wiring": "common",
    "ediscovery": "audit", "escalation_sla": "comms", "expense_processing": "finance",
    "expense_routing": "finance", "external_contact": "comms",
    "flash_sale_write_service": "commerce", "hierarchy_service": "hierarchy",
    "import_service": "common", "je_reversal_service": "finance",
    "kms_encryption": "security", "learning_write_service": "hr",
    "misc_write_service": "common", "okr_engine": "hr",
    "payment_engine": "treasury", "payment_orchestrator": "treasury",
    "payments": "gateways", "payments_write_service": "gateways",
    "payment_event_handlers": "gateways", "period_close_service": "finance",
    "qr_service": "common", "referrals_service": "commerce",
    "retention_service": "customer", "trading_service": "finance",
    # geo / travel / map already covered by keywords; ensure:
    "travel_detector": "geography", "travel_service": "geography",
    "map_service": "logistics", "geo_fence_service": "logistics",
    "live_tracking_service": "logistics", "cross_border_detection": "geography",
    "cross_border_service": "geography", "cross_border_tracker": "geography",
}

SUBFILES: dict[str, str] = {}
for d in EXISTING:
    for f in (SERVICES / d).iterdir():
        if f.suffix == ".py":
            SUBFILES.setdefault(f.name, d)


def classify(stem: str):
    tokens = [t for t in stem.split("_") if t]
    tally: dict[str, int] = {}
    matched = []
    for t in tokens:
        dom = ALIAS.get(t.lower())
        if dom:
            tally[dom] = tally.get(dom, 0) + 1
            matched.append((t, dom))
    # substring keyword match (multi-word keywords)
    for dom, kws in KEYWORDS.items():
        for kw in kws:
            k = str(kw).lower()
            if k and k in stem.lower() and dom not in [m[1] for m in matched]:
                tally[dom] = tally.get(dom, 0) + 1
                matched.append((k, dom))
    if not tally:
        return None, matched
    best = max(tally.items(), key=lambda kv: kv[1])[0]
    return best, matched


def top_defs(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return set()
    return {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def lines(p: Path) -> int:
    return len(p.read_text(encoding="utf-8", errors="replace").splitlines())


plan = []
flat = sorted(p for p in SERVICES.iterdir() if p.is_file() and p.suffix == ".py"
              and p.name not in ("_registry.py", "__init__.py"))

collisions = []
scratch_out = []
unmapped = []

for f in flat:
    stem = f.stem
    if stem in SCRATCH:
        scratch_out.append(f.name)
        plan.append({"file": f.name, "domain": None, "folder": "SCRATCH",
                     "final_folder": None, "target": f"scripts/maintenance/{f.name}",
                     "collision": None, "keep": None, "reason": "scratch/debug script"})
        continue
    if stem in OVERRIDE:
        dom = None
        folder = OVERRIDE[stem]
        reason = "override"
    else:
        dom, matched = classify(stem)
        folder = FOLDER_FOR_DOMAIN.get(dom, "common") if dom else "common"
        reason = "kw:" + ",".join(f"{t}->{d}" for t, d in matched) if dom else "no-match"
    coll = SUBFILES.get(f.name)
    entry = {"file": f.name, "domain": dom, "folder": folder,
             "final_folder": folder, "target": f"services/{folder}/{f.name}",
             "collision": coll, "keep": None, "reason": reason}
    if coll:
        subp = SERVICES / coll / f.name
        flat_defs = top_defs(f)
        sub_defs = top_defs(subp)
        flat_lines = lines(f)
        sub_lines = lines(subp)
        flat_stub = flat_lines < 30 or flat_defs <= {"__getattr__"}
        sub_stub = sub_lines < 30 or sub_defs <= {"__getattr__"}
        if sub_stub and not flat_stub:
            keep = "flat"
        elif flat_stub and not sub_stub:
            keep = "sub"
        elif flat_defs > sub_defs:
            keep = "flat"
        elif sub_defs > flat_defs:
            keep = "sub"
        else:
            keep = "sub" if sub_lines >= flat_lines else "flat"
        entry["keep"] = keep
        entry["final_folder"] = folder if keep == "flat" else coll
        entry["target"] = f"services/{entry['final_folder']}/{f.name}"
        collisions.append({"file": f.name, "into": folder, "exists_in": coll,
                           "keep": keep, "flat_lines": flat_lines, "sub_lines": sub_lines,
                           "flat_defs": sorted(flat_defs), "sub_defs": sorted(sub_defs)})
        if keep == "flat":
            plan.append(entry)
        else:
            # flat will be deleted; keep sub in place. Still record for import map.
            plan.append({"file": f.name, "domain": dom, "folder": folder,
                         "final_folder": coll, "target": f"services/{coll}/{f.name}",
                         "collision": coll, "keep": "sub",
                         "reason": reason + " [keep subfolder, delete flat]"})
    else:
        plan.append(entry)

(REPO / "scripts" / "system_trackers" / "_services_plan.json").write_text(
    json.dumps(plan, indent=2), encoding="utf-8")

fc = Counter(e["final_folder"] for e in plan if e["folder"] != "SCRATCH")
print("=== FLAT FILE COUNT ===", len(flat))
print("=== FINAL FOLDER DISTRIBUTION (where each module will live) ===")
for k, v in sorted(fc.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print("=== SCRATCH -> scripts/maintenance ===", len(scratch_out), scratch_out)
still_unmapped = [e["file"] for e in plan if e["folder"] == "common" and e["domain"] is None and e["file"] not in SCRATCH]
print("=== STILL UNMAPPED (common, no keyword) ===", len(still_unmapped), still_unmapped)
print("=== COLLISIONS ===", len(collisions))
for c in collisions:
    print(f"  {c['file']:36s} keep={c['keep']:4s} flat={c['flat_lines']:>4}L sub={c['sub_lines']:>4}L "
          f"final={c['into'] if c['keep']=='flat' else c['exists_in']}")
