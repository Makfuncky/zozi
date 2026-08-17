"""Triage the 124 baseline routers: classify complexity + collision-safety.

Safe target  = none of its (METHOD, path) pairs appear in any OTHER top-level
               hand-written router (so the migrated controller won't collide).
"""
import ast, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTERS = os.path.join(ROOT, "routers")
BASELINE = os.path.join(ROOT, "tests", "_router_logic_baseline.txt")

baseline = [l.strip() for l in open(BASELINE, encoding="utf-8")
            if l.strip() and not l.startswith("#")]

# Collect every (METHOD, full_path) from ALL top-level hand-written routers.
route_re = re.compile(r'@\w+\.(get|post|put|patch|delete)\(\s*"([^"]*)"')
prefix_re = re.compile(r'APIRouter\(\s*prefix\s*=\s*"([^"]*)"')
all_routes = {}
file_routes = {}
for fn in os.listdir(ROUTERS):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    fp = os.path.join(ROUTERS, fn)
    text = open(fp, encoding="utf-8").read()
    if "AUTO-GENERATED" in text:
        continue
    m = prefix_re.search(text)
    pref = m.group(1) if m else ""
    routes = set()
    for mm in route_re.finditer(text):
        method = mm.group(1).upper()
        path = mm.group(2)
        full = path if path.startswith("/") else "/" + path
        full = pref + full
        routes.add((method, full))
        all_routes.setdefault((method, full), set()).add(fn)
    file_routes[fn] = routes

rows = []
for name in baseline:
    fn = name if name.endswith(".py") else name + ".py"
    fp = os.path.join(ROUTERS, fn)
    if not os.path.exists(fp):
        rows.append((fn, 0, "MISSING", 0, "", "", ""))
        continue
    text = open(fp, encoding="utf-8").read()
    tree = ast.parse(text)
    n_routes = 0
    has_ws = "websocket" in text
    has_upload = "File(" in text or "UploadFile" in text
    has_bg = "BackgroundTasks" in text
    has_custom_dep = bool(re.search(r"Depends\((?!get_db|require_admin|get_current_user|get_current_user_optional)", text))
    n_funcs = sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
    routes = file_routes.get(fn, set())
    # collision: any of my routes also registered by another top-level file
    collisions = sorted({rp for rp in routes if all_routes.get(rp, set()) - {fn}})
    safe = "SAFE" if not collisions else "COLLIDE"
    rows.append((fn, len(routes), safe, n_funcs,
                 "WS" if has_ws else "", "UP" if has_upload else "",
                 "BG" if has_bg else "", "CDEP" if has_custom_dep else "",
                 ";".join(f"{m} {p}" for m, p in collisions[:3])))

rows.sort(key=lambda r: (r[2] != "SAFE", r[1], r[0]))
print(f"{'file':40} {'rt':>3} {'safety':7} {'fn':>3} flags  collisions")
for r in rows:
    fn, nr, safe, nf, *flags = r
    col = r[-1]
    flagstr = "".join(flags[:-1])
    print(f"{fn:40} {nr:3} {safe:7} {nf:3} {flagstr:7} {col}")
sys.stderr.write(f"\nTOTAL baseline={len(baseline)} SAFE={sum(1 for r in rows if r[2]=='SAFE')} COLLIDE={sum(1 for r in rows if r[2]=='COLLIDE')}\n")
