import importlib, os, re, sys, logging

logging.basicConfig(level=logging.CRITICAL)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-wiring-check")

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
routers = os.path.join(backend, "routers")
sys.path.insert(0, backend)

# ---- (a) Wiring: import every router named in main.py ----
mainp = os.path.join(backend, "main.py")
with open(mainp, encoding="utf-8") as f:
    mt = f.read()
tuples = re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*\)', mt)
names = []
seen = set()
for n, _ in tuples:
    if n not in seen:
        seen.add(n); names.append(n)

ok = fail = 0
byerr = {}
for name in names:
    try:
        try:
            importlib.import_module("routers." + name)
        except ImportError:
            importlib.import_module("controllers." + name)
        ok += 1
    except Exception as e:
        fail += 1
        t = type(e).__name__
        byerr[t] = byerr.get(t, 0) + 1
        print("FAIL", name, "::", t, "::", str(e)[:200])
print("WIRING: TOTAL=%d OK=%d FAIL=%d  byerr=%s" % (len(names), ok, fail, byerr))

# ---- (b) RN1 across full routers/ dir ----
AUDIT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers\system_architecture_audit.py"
spec = importlib.util.spec_from_file_location("sa_audit", AUDIT)
am = importlib.util.module_from_spec(spec)
sys.modules["sa_audit"] = am
spec.loader.exec_module(am)
aliases = am.PLACEMENT_ALIAS_TO_DOMAIN
stop = set(am.PLACEMENT_STOP_TOKENS)
surfaces = {"public", "admin", "supplier", "logistics", "customer"}

def score(stem):
    toks = [x.lower() for x in re.split(r"[^A-Za-z0-9]+", stem) if x]
    surface = next((x for x in toks if x in surfaces), None)
    domain = next((x for x in toks if x in aliases), None)
    has_op = False
    for x in toks:
        if len(x) < 3: continue
        if x in stop: continue
        if surface and x == surface: continue
        if domain and (x == domain or aliases.get(x) == domain): continue
        has_op = True; break
    m = []
    if not surface: m.append("surface")
    if not domain: m.append("domain")
    if not has_op: m.append("operation")
    return m

rn1 = []
for fn in sorted(os.listdir(routers)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    m = score(fn[:-3])
    if m:
        rn1.append((fn, m))
print("RN1 TOTAL IN routers/ =", len(rn1))
for fn, m in rn1:
    print("  RN1", fn, m)
