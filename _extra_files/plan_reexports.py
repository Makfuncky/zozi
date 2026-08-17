import ast, re, importlib, traceback
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
EXCLUDE = {"venv","__pycache__",".git","node_modules","tests","alembic","_migration_trash",".pytest_cache",".hypothesis"}

def iter_py():
    for p in ROOT.rglob("*.py"):
        if any(part in EXCLUDE for part in p.parts): continue
        yield p

# Build map symbol -> defining module(s) by AST
defn = {}  # name -> list of module dotted names where defined (def/class or module-level assign)
for p in iter_py():
    rel = p.relative_to(ROOT)
    parts = rel.with_suffix("").parts
    mod = ".".join(parts)
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defn.setdefault(node.name, []).append(mod)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isidentifier():
                    defn.setdefault(t.id, []).append(mod)

def module_names(modname):
    try:
        m = importlib.import_module(modname)
    except Exception:
        return None
    return set(dir(m))

# Controllers that import from a target module; find missing names
failing_controllers = [
    "controllers.core.admin_controller",
    "controllers.core.admin_chat_controller",
    "controllers.core.admin_payouts_controller",
    "controllers.core.admin_promotions_controller",
    "controllers.core.admin_users_controller",
    "controllers.core.countries_controller",
    "controllers.core.permissions_controller",
    "controllers.public.public_permissions_validation_controller",
    "controllers.public.public_geography_configuration_controller",
    "controllers.public.public_security_detection_controller",
    "controllers.logistics.logistics_logistics_status_controller",
]

# Map each target module -> canonical module to re-export from (prefer same-domain admin/module)
# We'll auto-detect: for a missing name, pick the defining module that is NOT the target and
# is 'closest' (prefer services.admin.* for core/admin, services.orders/* etc). Fallback: first def.

plan = {}  # target_module -> {name: canonical}
for ctrl in failing_controllers:
    p = ROOT / (ctrl.replace(".","/") + ".py")
    if not p.exists():
        print("MISSING CONTROLLER FILE", ctrl); continue
    tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            tgt = node.module
            if tgt.startswith("services") or True:
                names = [a.name for a in node.names]
                try:
                    cur = module_names(tgt)
                except Exception:
                    cur = None
                if cur is None:
                    # target itself doesn't import; treat all as needing re-export
                    need = names
                else:
                    need = [n for n in names if n not in cur]
                for n in need:
                    if n in ("logger",):  # skip logger to avoid shadowing
                        continue
                    cands = [c for c in defn.get(n, []) if c != tgt]
                    # prefer a services.admin.* or services.<domain> over logistics hub etc
                    canon = None
                    for pref in ("services.admin.","services.orders.","services.security.","services.geography.","services.finance.","services.commerce.","services.catalog.","services.users."):
                        hit=[c for c in cands if c.startswith(pref)]
                        if hit: canon=hit[0]; break
                    if canon is None and cands:
                        canon = cands[0]
                    if canon:
                        plan.setdefault(tgt, {})[n] = canon

for tgt, names in plan.items():
    print(f"\n### RE-EXPORT INTO {tgt} ({len(names)} names)")
    by_canon = {}
    for n,c in names.items():
        by_canon.setdefault(c, []).append(n)
    for c, ns in by_canon.items():
        print(f"  from {c} import {', '.join(sorted(ns))}")
