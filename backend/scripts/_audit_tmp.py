import ast, os, re, json, glob
ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
MARKER = "AUTO-GENERATED"
FORBIDDEN = ("db.commit", "session.commit", "db.flush", "session.flush")
ROUTE_RE = re.compile(r'@\w+\.(get|post|put|patch|delete|websocket)\(\s*("|\')')

def read(p):
    try: return open(p, encoding="utf-8").read()
    except Exception: return ""

def subpackages(base):
    out = set()
    for dp, _, files in os.walk(base):
        if "__pycache__" in dp: continue
        rel = os.path.relpath(dp, base)
        if rel == ".": continue
        out.add(rel.replace(os.sep, "."))
    return sorted(out)

routers_dir = os.path.join(ROOT, "routers")
legacy, generated = [], []
for fp in glob.glob(os.path.join(routers_dir, "**", "*.py"), recursive=True):
    if "__pycache__" in fp or fp.endswith("__init__.py"): continue
    name = os.path.basename(fp)
    if name.endswith(".bak"): continue
    if "generated" in fp.split(os.sep): continue
    txt = read(fp)
    if MARKER in txt[:400]:
        generated.append(name); continue
    routes = ROUTE_RE.findall(txt)
    models_imp = sorted({m.group(1) for m in re.finditer(r'(?:from|import)\s+(models(?:\.\w+)?)', txt)})
    services_imp = sorted({m.group(1) for m in re.finditer(r'(?:from|import)\s+(services(?:\.\w+)?)', txt)})
    forb = [f for f in FORBIDDEN if f in txt]
    legacy.append({"file": name, "routes": len(routes), "models_imports": models_imp,
                   "services_imports": services_imp, "forbidden": forb, "offender": bool(forb or models_imp)})

controllers_dir = os.path.join(ROOT, "controllers")
ctrl = []
for fp in glob.glob(os.path.join(controllers_dir, "**", "*.py"), recursive=True):
    if "__pycache__" in fp or fp.endswith("__init__.py"): continue
    txt = read(fp)
    has_dec = bool(re.search(r'@(route|get|post|put|patch|delete)\s*\(', txt))
    ctrl.append({"file": os.path.relpath(fp, ROOT), "has_decorator": has_dec})

result = {
    "counts": {"legacy_routers": len(legacy), "generated_routers": len(generated),
        "legacy_offenders": sum(1 for r in legacy if r["offender"]),
        "controllers_total": len(ctrl),
        "controllers_no_dec": sum(1 for c in ctrl if not c["has_decorator"]),
        "controllers_with_dec": sum(1 for c in ctrl if c["has_decorator"])},
    "offenders": [r for r in legacy if r["offender"]],
    "controllers_no_dec": [c for c in ctrl if not c["has_decorator"]],
    "subpackages": {"models": subpackages(os.path.join(ROOT,"models")),
                     "services": subpackages(os.path.join(ROOT,"services")),
                     "controllers": subpackages(os.path.join(ROOT,"controllers"))},
}
with open(r"C:\Users\user\AppData\Local\Temp\kilo\audit.json","w",encoding="utf-8") as f:
    json.dump(result, f, indent=2)
print("legacy", len(legacy), "generated", len(generated), "offenders", result["counts"]["legacy_offenders"],
      "ctrl_no_dec", result["counts"]["controllers_no_dec"])
