import os, re, json, subprocess
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
data = json.load(open(os.path.join(ROOT, "_extra_files", "router_cleanup_data.json"), encoding="utf-8"))

candidates = [d for d in data if d["routes"] == 0 or d["name"] in {
    d2["name"] for g in defaultdict(list) for d2 in g  # duplicates
}]
# rebuild dup set properly
by_hash = defaultdict(list)
for d in data:
    by_hash[d["hash"]].append(d)
dup_names = {d["name"] for g in by_hash.values() if len(g) > 1 for d in g}
orphan_dups = [d for d in data if (d["name"] in dup_names) and not d["live"]]
orphan_empty = [d for d in data if d["routes"] == 0 and not d["live"] and d["name"] not in dup_names and d["name"] != "__init__.py"]

# gather all .py in backend
all_py = []
for dp, _, fns in os.walk(BACKEND):
    for f in fns:
        if f.endswith(".py"):
            all_py.append(os.path.join(dp, f))

def imports_of(basename):
    pat = re.compile(r'(?:from|import)\s+(?:routers|controllers)\s*\.\s*' + re.escape(basename) + r'\b')
    hits = []
    for p in all_py:
        try:
            txt = open(p, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if pat.search(txt):
            hits.append(os.path.relpath(p, ROOT))
    return hits

report = []
referenced = {}  # name -> list of importers
for d in orphan_dups + orphan_empty:
    refs = imports_of(d["name"][:-3])
    referenced[d["name"]] = refs

# also any import of the bare module name without routers./controllers. prefix? skip, too noisy

# Summary
dup_ref = {n: r for n, r in referenced.items() if n in dup_names}
empty_ref = {n: r for n, r in referenced.items() if n not in dup_names}

report.append("=== IMPORT-SAFETY CHECK (orphaned duplicates + orphaned empty) ===")
report.append(f'orphan duplicate files checked: {len(orphan_dups)}')
report.append(f'orphan empty (non-dup) files checked: {len(orphan_empty)}')
report.append("")
report.append("--- DUPLICATE files that ARE referenced elsewhere (DO NOT delete blindly) ---")
any_ref_dup = False
for n in sorted(dup_ref):
    if dup_ref[n]:
        any_ref_dup = True
        report.append(f'  {n}: ' + ", ".join(dup_ref[n]))
if not any_ref_dup:
    report.append("  (none — no duplicate file is imported anywhere else)")
report.append("")
report.append("--- EMPTY (non-dup) orphan files that ARE referenced elsewhere ---")
any_ref_empty = False
for n in sorted(empty_ref):
    if empty_ref[n]:
        any_ref_empty = True
        report.append(f'  {n}: ' + ", ".join(empty_ref[n]))
if not any_ref_empty:
    report.append("  (none — no empty orphan file is imported elsewhere)")

open(os.path.join(ROOT, "_extra_files", "router_import_safety.txt"), "w", encoding="utf-8").write("\n".join(report))
json.dump(referenced, open(os.path.join(ROOT, "_extra_files", "router_referenced.json"), "w", encoding="utf-8"), indent=2)
print("\n".join(report))
print("\nWROTE _extra_files/router_import_safety.txt + router_referenced.json")
