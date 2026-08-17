import ast, importlib, re
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
EXCLUDE = {"venv","__pycache__",".git","node_modules","tests","alembic","_migration_trash",".pytest_cache",".hypothesis"}

def iter_py():
    for p in ROOT.rglob("*.py"):
        if any(part in EXCLUDE for part in p.parts): continue
        yield p

defn = {}
for p in iter_py():
    rel = p.relative_to(ROOT)
    mod = ".".join(rel.with_suffix("").parts)
    try: tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception: continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defn.setdefault(node.name, []).append(mod)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isidentifier():
                    defn.setdefault(t.id, []).append(mod)

failing_controllers = [
    "controllers.core.admin_controller","controllers.core.admin_chat_controller",
    "controllers.core.admin_payouts_controller","controllers.core.admin_promotions_controller",
    "controllers.core.admin_users_controller","controllers.core.countries_controller",
    "controllers.core.permissions_controller","controllers.public.public_permissions_validation_controller",
    "controllers.public.public_geography_configuration_controller","controllers.public.public_security_detection_controller",
    "controllers.logistics.logistics_logistics_status_controller",
    "controllers.logistics.logistics_partner_verify_controller",
    "controllers.public.public_geography_configuration_controller",
]

plan = {}  # target -> {name: canon}
for ctrl in failing_controllers:
    p = ROOT / (ctrl.replace(".","/") + ".py")
    if not p.exists(): continue
    tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("services"):
            tgt = node.module
            names = [a.name for a in node.names]
            try:
                cur = set(dir(importlib.import_module(tgt)))
            except Exception:
                cur = set()
            for n in names:
                if n in cur or n == "logger": continue
                cands = [c for c in defn.get(n, []) if c != tgt and not c.startswith("controllers.")]
                canon = None
                for pref in ("services.admin.","services.orders.","services.security.","services.geography.","services.finance.","services.commerce.","services.catalog.","services.users.","services.logistics.","services.treasury.","services.hierarchy.","services.common.","services.supplier.","services.core.","services.public."):
                    hit=[c for c in cands if c.startswith(pref)]
                    if hit: canon=hit[0]; break
                if canon is None and cands: canon = cands[0]
                if canon:
                    plan.setdefault(tgt, {})[n] = canon

MARK = "# === auto-wiring re-exports (migration repair) ==="
for tgt, names in plan.items():
    path = ROOT / (tgt.replace(".","/") + ".py")
    text = path.read_text(encoding="utf-8", errors="ignore")
    # cycle guard: skip canon if it imports tgt
    tgt_import_literal = tgt
    by_canon = {}
    for n,c in names.items():
        csrc = (ROOT / (c.replace(".","/") + ".py")).read_text(encoding="utf-8", errors="ignore")
        if tgt_import_literal in csrc:
            continue
        by_canon.setdefault(c, []).append(n)
    blocks = [MARK]
    for c, ns in by_canon.items():
        blocks.append(f"from {c} import (\n    " + ",\n    ".join(sorted(ns)) + "\n)")
    existing = [b for b in blocks[1:] if b.strip() in text]
    addition = "\n\n" + "\n".join([b for b in blocks if b not in existing]) + "\n"
    if addition.strip() == MARK:
        continue
    path.write_text(text + addition, encoding="utf-8")
    print(f"APPENDED to {tgt}: {sum(len(v) for v in by_canon.values())} re-exports from {len(by_canon)} modules")
