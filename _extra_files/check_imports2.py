import os, re, json
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
data = json.load(open(os.path.join(ROOT, "_extra_files", "router_cleanup_data.json"), encoding="utf-8"))

by_hash = defaultdict(list)
for d in data:
    by_hash[d["hash"]].append(d)
dup_names = {d["name"] for g in by_hash.values() if len(g) > 1 for d in g}
orphan_dups = [d for d in data if (d["name"] in dup_names) and not d["live"]]
orphan_empty = [d for d in data if d["routes"] == 0 and not d["live"] and d["name"] not in dup_names and d["name"] != "__init__.py"]

# load all backend py once
contents = {}
for dp, _, fns in os.walk(BACKEND):
    for f in fns:
        if f.endswith(".py"):
            p = os.path.join(dp, f)
            try:
                contents[os.path.relpath(p, ROOT)] = open(p, "r", encoding="utf-8", errors="replace").read()
            except Exception:
                pass

cand_names = set(d["name"][:-3] for d in orphan_dups + orphan_empty)
# one combined regex
pat = re.compile(r'(?:from|import)\s+(?:routers|controllers)\s*\.\s*(' + "|".join(re.escape(n) for n in cand_names) + r')\b')

referenced = defaultdict(list)
for rel, txt in contents.items():
    for m in pat.finditer(txt):
        referenced[m.group(1) + ".py"].append(rel)

report = []
report.append("=== IMPORT-SAFETY CHECK (orphaned duplicates + orphaned empty) ===")
report.append(f'orphan duplicate files checked: {len(orphan_dups)}')
report.append(f'orphan empty (non-dup) files checked: {len(orphan_empty)}')
report.append("")
report.append("--- DUPLICATE files referenced elsewhere (DO NOT delete blindly) ---")
dup_ref = {n: referenced.get(n, []) for n in (d["name"] for d in orphan_dups)}
if all(not v for v in dup_ref.values()):
    report.append("  (none — no duplicate file is imported anywhere else)")
else:
    for n in sorted(dup_ref):
        if dup_ref[n]:
            report.append(f'  {n}: ' + ", ".join(dup_ref[n]))
report.append("")
report.append("--- EMPTY (non-dup) orphan files referenced elsewhere ---")
empty_ref = {n: referenced.get(n, []) for n in (d["name"] for d in orphan_empty)}
if all(not v for v in empty_ref.values()):
    report.append("  (none — no empty orphan file is imported elsewhere)")
else:
    for n in sorted(empty_ref):
        if empty_ref[n]:
            report.append(f'  {n}: ' + ", ".join(empty_ref[n]))

open(os.path.join(ROOT, "_extra_files", "router_import_safety.txt"), "w", encoding="utf-8").write("\n".join(report))
json.dump(referenced, open(os.path.join(ROOT, "_extra_files", "router_referenced.json"), "w", encoding="utf-8"), indent=2)
print("\n".join(report))
print("\nWROTE _extra_files/router_import_safety.txt + router_referenced.json")
