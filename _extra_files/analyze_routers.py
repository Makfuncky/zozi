import os, re, hashlib, json
from collections import defaultdict

ROUTERS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers"

def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

ROUTE_DECOR = re.compile(r"^\s*@\s*\w*\.?(get|post|put|patch|delete|head|options|trace|websocket)\b", re.I)
APIROUTER_DEF = re.compile(r"^\s*(?:[\w]+|router)\s*=\s*APIRouter\s*\((.*)\)\s*$", re.S | re.M)
PREFIX_RE = re.compile(r"prefix\s*=\s*['\"]([^'\"]+)['\"]")
TAGS_RE = re.compile(r"tags\s*=\s*\[([^\]]*)\]")

data = []
for name in sorted(os.listdir(ROUTERS)):
    if not name.endswith(".py"):
        continue
    path = os.path.join(ROUTERS, name)
    if not os.path.isfile(path):
        continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    lines = src.splitlines()
    h = sha256(path)
    n_routes = sum(1 for ln in lines if ROUTE_DECOR.match(ln))
    m = APIROUTER_DEF.search(src)
    prefix = None; tags = []
    if m:
        body = m.group(1)
        pm = PREFIX_RE.search(body)
        if pm: prefix = pm.group(1)
        tm = TAGS_RE.search(body)
        if tm:
            tags = re.findall(r"['\"]([^'\"]+)['\"]", tm.group(1))
    data.append({
        "name": name,
        "bytes": os.path.getsize(path),
        "lines": len(lines),
        "hash": h,
        "n_routes": n_routes,
        "prefix": prefix,
        "tags": tags,
        "empty": n_routes == 0,
    })

# exact duplicates by hash
by_hash = defaultdict(list)
for d in data:
    by_hash[d["hash"]].append(d)

# prefix collisions
by_prefix = defaultdict(list)
for d in data:
    if d["prefix"]:
        by_prefix[d["prefix"]].append(d)

out = []
out.append("TOTAL FILES: %d" % len(data))
out.append("STUB/EMPTY (no route decorators): %d" % sum(1 for d in data if d["empty"]))

out.append("\n===== EXACT DUPLICATES (same sha256) =====")
dup_groups = [g for g in by_hash.values() if len(g) > 1]
out.append("Groups with identical content: %d" % len(dup_groups))
for g in dup_groups:
    out.append("\nHash %s  (x%d)" % (g[0]["hash"][:16], len(g)))
    for d in g:
        out.append("  %-45s lines=%-4d routes=%-3d prefix=%s" % (d["name"], d["lines"], d["n_routes"], d["prefix"]))

out.append("\n===== STUB/EMPTY ROUTERS (no routes) =====")
for d in sorted(data, key=lambda x: x["name"]):
    if d["empty"]:
        out.append("  %-45s lines=%-4d bytes=%-5d prefix=%s" % (d["name"], d["lines"], d["bytes"], d["prefix"]))

out.append("\n===== PREFIX COLLISIONS (same prefix, multiple files) =====")
coll = {p: g for p, g in by_prefix.items() if len(g) > 1}
out.append("Colliding prefixes: %d" % len(coll))
for p in sorted(coll):
    g = coll[p]
    out.append("\nPrefix %r  (x%d)" % (p, len(g)))
    for d in sorted(g, key=lambda x: x["name"]):
        out.append("  %-45s lines=%-4d routes=%-3d hash=%s" % (d["name"], d["lines"], d["n_routes"], d["hash"][:12]))

report = "\n".join(out)
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\router_analysis.txt", "w", encoding="utf-8") as f:
    f.write(report)

# also dump JSON for convenience
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\router_analysis.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(report)
print("\nWROTE _extra_files/router_analysis.txt and .json")
