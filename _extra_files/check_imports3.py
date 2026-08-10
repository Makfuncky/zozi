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

ref_by_name = defaultdict(set)   # module name (no .py) -> set of rel files referencing it
token_re = re.compile(r'(?:routers|controllers)\.([a-zA-Z_][a-zA-Z0-9_]*)')
for dp, _, fns in os.walk(BACKEND):
    for f in fns:
        if not f.endswith(".py"):
            continue
        p = os.path.join(dp, f)
        try:
            txt = open(p, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        rel = os.path.relpath(p, ROOT)
        for m in token_re.finditer(txt):
            ref_by_name[m.group(1)].add(rel)

def refs(name):
    return sorted(ref_by_name.get(name[:-3], set()))

report = []
report.append("=== IMPORT-SAFETY CHECK (orphaned duplicates + orphaned empty) ===")
report.append(f'orphan duplicate files checked: {len(orphan_dups)}')
report.append(f'orphan empty (non-dup) files checked: {len(orphan_empty)}')
report.append("")
report.append("--- DUPLICATE files referenced elsewhere (DO NOT delete blindly) ---")
anyd = False
for d in sorted(orphan_dups, key=lambda x: x["name"]):
    r = refs(d["name"])
    if r:
        anyd = True
        report.append(f'  {d["name"]}: ' + ", ".join(r))
if not anyd:
    report.append("  (none — no duplicate file is imported anywhere else)")
report.append("")
report.append("--- EMPTY (non-dup) orphan files referenced elsewhere ---")
anye = False
for d in sorted(orphan_empty, key=lambda x: x["name"]):
    r = refs(d["name"])
    if r:
        anye = True
        report.append(f'  {d["name"]}: ' + ", ".join(r))
if not anye:
    report.append("  (none — no empty orphan file is imported anywhere else)")

open(os.path.join(ROOT, "_extra_files", "router_import_safety.txt"), "w", encoding="utf-8").write("\n".join(report))
json.dump({n: sorted(v) for n, v in ref_by_name.items()},
          open(os.path.join(ROOT, "_extra_files", "router_referenced.json"), "w", encoding="utf-8"), indent=2)
print("\n".join(report))
print("\nWROTE _extra_files/router_import_safety.txt + router_referenced.json")
