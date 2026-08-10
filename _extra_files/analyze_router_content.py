import os, re, json
from collections import defaultdict, Counter

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")

files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")

PREFIXED = {"admin", "supplier", "public", "customer", "country", "system", "logistics"}

def read(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""

def analyze(src):
    info = {}
    # APIRouter prefix
    m = re.search(r"APIRouter\(\s*(?:tags\s*=\s*\[[^\]]*\]\s*,)?\s*prefix\s*=\s*['\"]([^'\"]+)['\"]", src)
    if not m:
        m = re.search(r"APIRouter\(\s*prefix\s*=\s*['\"]([^'\"]+)['\"]", src)
    info["prefix"] = m.group(1) if m else ""
    # tags
    mt = re.search(r"APIRouter\([^)]*tags\s*=\s*\[([^\]]*)\]", src, re.S)
    info["tags"] = re.findall(r"['\"]([^'\"]+)['\"]", mt.group(1)) if mt else []
    # routes: @router.X("/path") def name
    routes = []
    for mm in re.finditer(r"@\w+\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]", src):
        routes.append((mm.group(1), mm.group(2)))
    info["routes"] = routes
    # function defs
    defs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", src)
    info["defs"] = defs
    # controller/service imports -> domain hint
    imp = re.findall(r"from\s+backend\.(controllers|services)\.([a-zA-Z0-9_.]+)\s+import", src)
    info["ctrl_imp"] = sorted(set(c for _, c in imp))
    return info

# verb-ish operation keywords found in function/route names
OP_VERBS = ["management","create","creation","list","get","update","delete","search","sync",
            "upload","download","import","export","status","track","tracking","verify",
            "validation","validate","register","registration","login","logout","refresh",
            "approve","approval","reject","review","moderate","report","reporting","health",
            "config","configuration","settings","analytics","dashboard","notify","message",
            "messaging","pay","payment","payout","refund","order","orders","catalog","profile",
            "documents","geography","location","lookup","lookup","toggle","enable","disable"]

records = {}
for f in files:
    src = read(os.path.join(ROUTERS, f))
    records[f] = analyze(src)

# Build a content-derived "operation" guess for files needing one
def op_hint(info):
    text = " ".join(info["defs"] + [r[1] for r in info["routes"]])
    found = [v for v in OP_VERBS if v in text]
    # priority: pick a strong noun/verb
    if "management" in found: return "management"
    for k in ["tracking","register","registration","login","validation","verify","moderate",
              "report","reporting","sync","import","export","upload","approve","approval",
              "review","status","config","configuration","analytics","dashboard","lookup",
              "search","catalog","messaging","message","pay","payment","payout","refund",
              "create","creation","update","delete","list","get"]:
        if k in found:
            return k
    return ""

summary = []
for f in files:
    base = f[:-3]
    toks = base.split("_")
    if toks[0] in PREFIXED:
        surface = toks[0]; rest = toks[1:]
    else:
        surface = "store" if base in {"products","orders","cart","payments","categories",
            "banners","coupons","wishlist","reviews","returns","shipments","addresses",
            "referrals","flash_sales","currency","trading","cross_border","parcel_tracking",
            "shop_locations","countries","commission","invoices","treasury","finance_automation",
            "finance_erp","accounting","payroll","risk","compliance"} else "core"
        rest = toks
    info = records[f]
    op = op_hint(info)
    domain = rest[0] if rest else "core"
    operation = "_".join(rest[1:]) if len(rest) > 1 else (op or "routes")
    new = f"{surface}_{domain}_{operation}"
    summary.append({
        "file": f, "surface": surface, "domain": domain, "operation": operation,
        "new": new, "prefix": info["prefix"], "n_routes": len(info["routes"]),
        "n_defs": len(info["defs"]), "defs_sample": info["defs"][:8],
        "ctrl_imp": info["ctrl_imp"][:4],
    })

with open(os.path.join(ROOT, "_extra_files", "router_content_analysis.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)

# print compact
for s in summary:
    print(f"{s['file']:<40} -> {s['new']:<42} routes={s['n_routes']:<3} prefix={s['prefix']}")
    if s['defs_sample']:
        print(f"      defs: {', '.join(s['defs_sample'])}")
