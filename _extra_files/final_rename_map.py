import os, re, json
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")
files = sorted(f for f in os.listdir(ROUTERS) if f.endswith(".py") and f != "__init__.py")
PREFIXED = {"admin", "supplier", "public", "customer", "country", "system", "logistics"}

def read(p):
    try: return open(p, encoding="utf-8", errors="ignore").read()
    except: return ""

def analyze(src):
    routes = re.findall(r"@\w+\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]*)['\"]", src)
    defs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", src)
    return routes, defs

# surface overrides for unprefixed files
FINANCE = {"finance_automation","finance_erp","trading","treasury","accounting",
           "invoices","commission","payroll","risk","compliance"}
PRODUCT_OPS = {"product_moderation","product_verification","product_videos"}
REFDATA = {"countries","addresses"}

# operation word priority (most specific first)
OP_PRIORITY = ["management","tracking","register","registration","login","validation",
    "verify","moderate","report","reporting","sync","import","export","upload","approve",
    "approval","review","status","config","configuration","analytics","dashboard","lookup",
    "search","catalog","messaging","message","pay","payment","payout","refund","create",
    "creation","update","delete","list","get"]

def op_from_content(defs, routes):
    text = " ".join(defs + [r[1] for r in routes]).lower()
    for k in OP_PRIORITY:
        if k in text:
            return k
    return ""

mapping = {}
for f in files:
    base = f[:-3]
    toks = base.split("_")
    if toks[0] in PREFIXED:
        surface = toks[0]; rest = toks[1:]
    else:
        if base in FINANCE: surface = "core"
        elif base in PRODUCT_OPS: surface = "admin"
        elif base in REFDATA: surface = "core"
        else:
            surface = "store" if base in {"products","orders","cart","payments","categories",
                "banners","coupons","wishlist","reviews","returns","shipments","referrals",
                "flash_sales","currency","cross_border","parcel_tracking","shop_locations"} else "core"
        rest = toks
    routes, defs = analyze(read(os.path.join(ROUTERS, f)))
    # already 3-part meaningful name (>=2 rest tokens) -> keep
    if len(rest) >= 2:
        new = base
    else:
        domain = rest[0] if rest else "core"
        if routes or defs:
            op = op_from_content(defs, routes) or "routes"
        else:
            op = "routes"
        new = f"{surface}_{domain}_{op}"
    mapping[f] = new

# collisions
rev = defaultdict(list)
for o, n in mapping.items(): rev[n].append(o)
collisions = {k: v for k, v in rev.items() if len(v) > 1}

with open(os.path.join(ROOT, "_extra_files", "final_rename_map.json"), "w", encoding="utf-8") as fh:
    json.dump(mapping, fh, indent=2)
with open(os.path.join(ROOT, "_extra_files", "final_rename_map.txt"), "w", encoding="utf-8") as fh:
    for o in files:
        flag = "  <<COLLISION" if mapping[o] in collisions else ""
        fh.write(f"{o:<42} -> {mapping[o]}{flag}\n")
    fh.write(f"\nTOTAL={len(mapping)} COLLISIONS={len(collisions)}\n")
    for k, v in collisions.items():
        fh.write(f"  {k} <= {v}\n")

print("TOTAL", len(mapping), "COLLISIONS", len(collisions))
for k, v in collisions.items():
    print("COLLISION:", k, "<=", v)
# show the ones that CHANGE (excluding collisions; show changed names)
changed = [(o, n) for o, n in mapping.items() if o[:-3] != n and n not in collisions]
print(f"\nFILES THAT WILL BE RENAMED: {len(changed)} (of {len(mapping)})")
for o, n in changed:
    print(f"  {o:<42} -> {n}")
