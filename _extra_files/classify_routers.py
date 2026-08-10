import os, re, subprocess, json, hashlib
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
ROUTERS = os.path.join(ROOT, "backend", "routers")
MAIN = os.path.join(ROOT, "backend", "main.py")

# 1) parse router_names module names from main.py
main_src = open(MAIN, "r", encoding="utf-8", errors="replace").read()
m = re.search(r"router_names\s*=\s*\[(.*?)\]", main_src, re.S)
names_block = m.group(1)
live_names = set(re.findall(r'\(\s*"([^"]+)"\s*,', names_block))

# 2) git status porcelain for routers dir
out = subprocess.run(["git", "status", "--porcelain", "--", "backend/routers"],
                     cwd=ROOT, capture_output=True, text=True).stdout
status = {}
for line in out.splitlines():
    code = line[:2]
    path = line[3:].strip()
    status[os.path.basename(path)] = code

ROUTE_DECOR = re.compile(r"^\s*@\s*\w*\.?(get|post|put|patch|delete|head|options|trace|websocket)\b", re.I)

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

data = []
for name in sorted(os.listdir(ROUTERS)):
    if not name.endswith(".py"):
        continue
    p = os.path.join(ROUTERS, name)
    if not os.path.isfile(p):
        continue
    src = open(p, "r", encoding="utf-8", errors="replace").read()
    lines = src.splitlines()
    nr = sum(1 for ln in lines if ROUTE_DECOR.match(ln))
    data.append({
        "name": name,
        "lines": len(lines),
        "bytes": os.path.getsize(p),
        "hash": sha256(p),
        "routes": nr,
        "live": name[:-3] in live_names,
        "git": status.get(name, "?"),
    })

by_hash = defaultdict(list)
for d in data:
    by_hash[d["hash"]].append(d)

# Build structured findings
empty = [d for d in data if d["routes"] == 0 and d["name"] != "__init__.py"]
empty_stub = [d for d in empty if d["lines"] <= 12]      # true scaffold stubs
empty_code  = [d for d in empty if d["lines"] > 12]       # has code but 0 routes

dup_groups = [g for g in by_hash.values() if len(g) > 1]

def fmt(d):
    return f'{d["name"]:<48} L{d["lines"]:<4} R{d["routes"]:<3} {"LIVE" if d["live"] else "orphan":<6} git={d["git"]}'

out_lines = []
out_lines.append("=== LIVE (registered in main._load_routers) vs ORPHAN ===")
out_lines.append(f'total files: {len(data)}   live: {sum(1 for d in data if d["live"])}   orphan: {sum(1 for d in data if not d["live"])}')
out_lines.append("")

out_lines.append("===== CATEGORY 1: EMPTY ROUTERS (0 route decorators) =====")
out_lines.append(f'EMPTY TOTAL (excl __init__): {len(empty)}   of which true stubs(<=12 lines): {len(empty_stub)}   code-but-no-routes(>12): {len(empty_code)}')
out_lines.append("")
out_lines.append("-- 1a. EMPTY STUBS (<=12 lines) --")
for d in sorted(empty_stub, key=lambda x: x["name"]):
    out_lines.append("  " + fmt(d))
out_lines.append("")
out_lines.append("-- 1b. HAS CODE BUT 0 ROUTES (>12 lines) --")
for d in sorted(empty_code, key=lambda x: x["name"]):
    out_lines.append("  " + fmt(d))

out_lines.append("")
out_lines.append("===== CATEGORY 2: EXACT DUPLICATES (identical content hash) =====")
out_lines.append(f'duplicate groups: {len(dup_groups)}   files involved: {sum(len(g) for g in dup_groups)}')
# classify each group: all live / all orphan / mixed
for g in sorted(dup_groups, key=lambda grp: grp[0]["name"]):
    kinds = set(("LIVE" if d["live"] else "orphan") for d in g)
    live_all = all(d["live"] for d in g)
    tag = "ALL-LIVE" if live_all else ("ALL-ORPHAN" if all(not d["live"] for d in g) else "MIXED")
    out_lines.append(f'\n* {tag}  hash={g[0]["hash"][:14]}')
    for d in sorted(g, key=lambda x: x["name"]):
        out_lines.append("    " + fmt(d))

report = "\n".join(out_lines)
open(os.path.join(ROOT, "_extra_files", "router_cleanup_candidates.txt"), "w", encoding="utf-8").write(report)
json.dump(data, open(os.path.join(ROOT, "_extra_files", "router_cleanup_data.json"), "w", encoding="utf-8"), indent=2)

# quick summaries
print("LIVE:", sum(1 for d in data if d["live"]), " ORPHAN:", sum(1 for d in data if not d["live"]), " TOTAL:", len(data))
print("EMPTY total:", len(empty), " stubs:", len(empty_stub), " code-no-routes:", len(empty_code))
print("DUP groups:", len(dup_groups))
print("DUP groups ALL-ORPHAN:", sum(1 for g in dup_groups if all(not d['live'] for d in g)))
print("DUP groups ALL-LIVE:", sum(1 for g in dup_groups if all(d['live'] for d in g)))
print("DUP groups MIXED:", sum(1 for g in dup_groups if not all(d['live'] for d in g) and not all(not d['live'] for d in g)))
print("\nWROTE _extra_files/router_cleanup_candidates.txt + .json")
