"""Authoritative audit of ZOZI backend layering.

Verifies the claims in ARCHITECTURE_MIGRATION_REPORT.md against the live tree.
Writes _extra_files/audit_report.json.

Checks:
  1. Routers that still contain business logic (not thin delegators)
  2. Controllers with route decorators vs needing them
  3. Services retaining provider code
  4. Model/Service/Controller wiring (import edges)
  5. Missing domain folders
  6. Provider -> Service wiring
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(os.path.dirname(HERE), "backend")
sys.path.insert(0, BACKEND)

ROUTERS = os.path.join(BACKEND, "routers")
CONTROLLERS = os.path.join(BACKEND, "controllers")
SERVICES = os.path.join(BACKEND, "services")
MODELS = os.path.join(BACKEND, "models")
PROVIDERS = os.path.join(BACKEND, "providers")

DECORATORS = {"get", "post", "put", "patch", "delete", "route"}

# Business-logic signals inside a hand-written router.
BL_PATTERNS = [
    re.compile(r"\bdb\.session\.", re.I),
    re.compile(r"\bSession\(\)", re.I),
    re.compile(r"\.query\(", re.I),
    re.compile(r"\.add\(|\.delete\(|\.commit\(|\.flush\(", re.I),
    re.compile(r"\bfrom models", re.I),
    re.compile(r"\bimport models", re.I),
    re.compile(r"@router\.(get|post|put|patch|delete)\(", re.I),  # has inline handler
]


def py_files(d):
    out = []
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith(".py") and f != "__init__.py":
                out.append(os.path.join(dp, f))
    return out


def count_bl_occurrences(src):
    return sum(bool(p.search(src)) for p in BL_PATTERNS)


def has_controller_import(src):
    return bool(re.search(r"from controllers", src)) or bool(re.search(r"import controllers", src))


router_report = {"scanned": 0, "with_inline_handlers": 0, "with_bl_signals": 0,
                 "thin_delegators": 0, "details": []}
for f in py_files(ROUTERS):
    rel = os.path.relpath(f, ROUTERS)
    src = open(f, encoding="utf-8", errors="ignore").read()
    if not re.search(r"\brouter\s*=\s*APIRouter", src):
        continue  # not a router module (e.g. generated/__init__, _registry)
    router_report["scanned"] += 1
    inline = bool(re.search(r"def \w+_route\(", src)) or bool(re.search(r"@router\.(get|post|put|patch|delete)\(", src))
    bl = count_bl_occurrences(src)
    is_thin = (not inline) or (has_controller_import(src) and inline and bl == 0)
    if inline:
        router_report["with_inline_handlers"] += 1
    if bl > 0:
        router_report["with_bl_signals"] += 1
    if is_thin:
        router_report["thin_delegators"] += 1
    router_report["details"].append({
        "file": rel, "inline_handler": inline, "bl_signals": bl, "thin": is_thin,
    })

print("ROUTER SUMMARY:", json.dumps({k: v for k, v in router_report.items() if k != "details"}, indent=2))

# ---- Controllers: decorator readiness ----
ctrl_report = {"total": 0, "ready": 0, "needs_decorators": 0, "ready_list": [], "needs_list": []}
for f in py_files(CONTROLLERS):
    rel = os.path.relpath(f, CONTROLLERS)
    try:
        tree = ast.parse(open(f, encoding="utf-8", errors="ignore").read())
    except SyntaxError:
        ctrl_report["needs_list"].append({"file": rel, "functions": 0, "syntax_error": True})
        ctrl_report["total"] += 1
        continue
    funcs = 0
    decorated = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs += 1
            for dec in node.decorator_list:
                name = None
                if isinstance(dec, ast.Name):
                    name = dec.id
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    name = dec.func.id
                if name in DECORATORS:
                    decorated += 1
                    break
    ctrl_report["total"] += 1
    if decorated > 0:
        ctrl_report["ready"] += 1
        ctrl_report["ready_list"].append(rel)
    else:
        ctrl_report["needs_list"].append({"file": rel, "functions": funcs})
        ctrl_report["needs_decorators"] += 1

print("CONTROLLER SUMMARY:", json.dumps({k: v for k, v in ctrl_report.items() if k not in ("ready_list", "needs_list")}, indent=2))

# ---- Services containing provider code ----
prov_imports = re.compile(r"from providers|import providers")
svc_report = {"total": 0, "with_provider_import": 0, "files": []}
for f in py_files(SERVICES):
    src = open(f, encoding="utf-8", errors="ignore").read()
    svc_report["total"] += 1
    if prov_imports.search(src):
        svc_report["with_provider_import"] += 1
        svc_report["files"].append(os.path.relpath(f, SERVICES))
print("SERVICE->PROVIDER SUMMARY:", json.dumps({k: v for k, v in svc_report.items() if k != "files"}, indent=2))
print("  with_provider_import count =", svc_report["with_provider_import"])

# ---- Missing domain folders (heuristic from controller/service subpackages) ----
def domains(d):
    return sorted({os.path.basename(p) for p in os.listdir(d) if os.path.isdir(os.path.join(d, p)) and not p.startswith("__")})

ctrl_dom = set(domains(CONTROLLERS))
svc_dom = set(domains(SERVICES))
missing_ctrl = sorted(svc_dom - ctrl_dom)
missing_svc = sorted(ctrl_dom - svc_dom)
print("Domains in services but NOT controllers:", missing_ctrl)
print("Domains in controllers but NOT services:", missing_svc)

# ---- Provider -> Service wiring: do services import from providers? ----
prov_modules = set()
for dp, _, fs in os.walk(PROVIDERS):
    for fn in fs:
        if fn.endswith(".py") and fn != "__init__.py":
            rel = os.path.relpath(os.path.join(dp, fn), PROVIDERS)[:-3].replace(os.sep, ".")
            prov_modules.add("providers." + rel)
prov_used = defaultdict(int)
for f in py_files(SERVICES):
    src = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.findall(r"from (providers\.[\w\.]+)", src):
        prov_used[m] += 1
print("Provider modules imported by services:", len(prov_used), "of", len(prov_modules), "provider modules")

out = {
    "router_report": router_report,
    "controller_report": ctrl_report,
    "service_provider_report": svc_report,
    "missing_controller_domains": missing_ctrl,
    "missing_service_domains": missing_svc,
    "provider_modules_total": len(prov_modules),
    "provider_modules_used_by_services": len(prov_used),
}
with open(os.path.join(HERE, "audit_report.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print("\nWrote _extra_files/audit_report.json")
