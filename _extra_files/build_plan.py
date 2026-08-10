import os, re, json
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
data = json.load(open(os.path.join(ROOT, "_extra_files", "router_cleanup_data.json"), encoding="utf-8"))
ref = json.load(open(os.path.join(ROOT, "_extra_files", "router_referenced.json"), encoding="utf-8"))

by_hash = defaultdict(list)
for d in data:
    by_hash[d["hash"]].append(d)
dup_groups = [g for g in by_hash.values() if len(g) > 1]

# live controllers / tests considered "real" references
def real_refs(name):
    out = []
    for r in ref.get(name[:-3], []):
        if r.startswith("backend\\controllers\\") or r.startswith("backend/tests") or r.startswith("backend\\tests"):
            out.append(r)
    return out

L = []
L.append("# ROUTER CLEANUP PLAN — duplicates & empty (content-verified)")
L.append("")
L.append("## Summary")
L.append(f"- Total router files: {len(data)}")
L.append(f"- LIVE (registered in main._load_routers): {sum(1 for d in data if d['live'])}")
L.append(f"- ORPHANED (never loaded by main): {sum(1 for d in data if not d['live'])}")
empty = [d for d in data if d['routes'] == 0 and d['name'] != '__init__.py']
L.append(f"- EMPTY routers (0 route decorators): {len(empty)}  (LIVE: {sum(1 for d in empty if d['live'])}  ORPHAN: {sum(1 for d in empty if not d['live'])})")
L.append(f"- EXACT DUPLICATE groups (identical content): {len(dup_groups)}  -> {sum(len(g) for g in dup_groups)} files, ALL orphaned")
L.append("")

# ---------- DUPLICATES ----------
L.append("## PART A — DUPLICATE ROUTERS (identical content hash)")
L.append("")
L.append("All 109 groups are 100% orphaned (none are in main.py router_names), so none are loaded at runtime.")
L.append("Recommendation: remove both copies per group. EXCEPTION: groups flagged [REVIEW] have a member imported")
L.append("by a live controller or a test file — check those before deleting.")
L.append("")
idx = 0
for g in sorted(dup_groups, key=lambda grp: grp[0]['name']):
    idx += 1
    names = sorted(d['name'] for d in g)
    # verdict
    review = any(real_refs(n) for n in names)
    tag = "[REVIEW]" if review else "[SAFE]"
    L.append(f"A.{idx:03d} {tag}  hash={g[0]['hash'][:12]}")
    for n in names:
        rr = real_refs(n)
        note = ("  <- referenced by: " + ", ".join(rr)) if rr else ""
        L.append(f"      {n}{note}")
L.append("")

# ---------- EMPTY ----------
L.append("## PART B — EMPTY ROUTERS (0 route decorators)")
L.append("")
empty_live = sorted([d for d in empty if d['live']], key=lambda x: x['name'])
empty_orphan = sorted([d for d in empty if not d['live']], key=lambda x: x['name'])
L.append(f"### B1. EMPTY + LIVE ({len(empty_live)}) — KEEP (registered in main.py; these are intended stubs)")
L.append("")
for d in empty_live:
    L.append(f"    {d['name']:<46} L{d['lines']:<4} git={d['git']}")
L.append("")
L.append(f"### B2. EMPTY + ORPHAN ({len(empty_orphan)}) — candidates for removal (never loaded)")
L.append("")
# separate true stubs vs code-no-routes among orphan empties
orphan_stub = [d for d in empty_orphan if d['lines'] <= 12]
orphan_code = [d for d in empty_orphan if d['lines'] > 12]
L.append(f"#### B2a. Orphan EMPTY STUBS (<=12 lines, {len(orphan_stub)})")
for d in orphan_stub:
    L.append(f"    {d['name']:<46} L{d['lines']:<4} git={d['git']}")
L.append("")
L.append(f"#### B2b. Orphan HAS-CODE-BUT-NO-ROUTES (>12 lines, {len(orphan_code)})")
for d in orphan_code:
    L.append(f"    {d['name']:<46} L{d['lines']:<4} git={d['git']}")
L.append("")

# ---------- SAFE REMOVAL SET ----------
L.append("## PART C — PROPOSED SAFE-TO-REMOVE SET (auto-generated)")
L.append("")
# orphan duplicate files not referenced by live controllers/tests
safe_dup = []
review_dup = []
for g in dup_groups:
    names = [d['name'] for d in g]
    if any(real_refs(n) for n in names):
        review_dup.extend(names)
    else:
        safe_dup.extend(names)
safe_empty_orphan = [d['name'] for d in empty_orphan if not real_refs(d['name'])]
L.append(f"- Orphan duplicate files (SAFE): {len(safe_dup)}  [REVIEW: {len(set(review_dup))}]")
L.append(f"- Orphan empty files (SAFE): {len(safe_empty_orphan)}")
L.append(f"- TOTAL safe-remove candidates: {len(safe_dup) + len(safe_empty_orphan)}")
L.append("")
L.append("REVIEW-only files (do not auto-delete): " + ", ".join(sorted(set(review_dup))))
L.append("")
with open(os.path.join(ROOT, "_extra_files", "router_cleanup_plan.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))

# also write the safe-remove file list for easy scripting
safe_all = sorted(set(safe_dup) | set(safe_empty_orphan))
with open(os.path.join(ROOT, "_extra_files", "routers_to_remove_safe.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(safe_all))

print("\n".join(L))
print("\nWROTE _extra_files/router_cleanup_plan.txt and routers_to_remove_safe.txt")
