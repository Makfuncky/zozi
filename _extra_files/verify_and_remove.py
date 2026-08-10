import os, re, json, shutil
from collections import defaultdict

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
ROUTERS = os.path.join(BACKEND, "routers")
TRASH = os.path.join(ROOT, "_extra_files", "_router_trash")

# intended delete set (the "SAFE" list from build_plan)
S = set()
for ln in open(os.path.join(ROOT, "_extra_files", "routers_to_remove_safe.txt"), encoding="utf-8").read().splitlines():
    ln = ln.strip()
    if ln:
        S.add(ln)  # e.g. "auth.py"? no -> these are orphan files like admin_audit_operations.py

# recompute references across backend
ref_by_name = defaultdict(set)
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

def importers_outside(mname):
    """Return importer rel-paths that are NOT routers being deleted (i.e. external)."""
    out = []
    for rel in ref_by_name.get(mname, set()):
        base = os.path.basename(rel)
        if base in S:
            continue  # peer being deleted -> safe
        out.append(rel)
    return out

final_safe = set()
review = {}
for name in S:
    mname = name[:-3]
    ext = importers_outside(mname)
    if ext:
        review[name] = ext
    else:
        final_safe.add(name)

os.makedirs(TRASH, exist_ok=True)
moved = []
for name in sorted(final_safe):
    src = os.path.join(ROUTERS, name)
    if os.path.exists(src):
        shutil.move(src, os.path.join(TRASH, name))
        moved.append(name)

# write reports
with open(os.path.join(ROOT, "_extra_files", "router_deleted_final.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(moved)))
with open(os.path.join(ROOT, "_extra_files", "router_delete_held_back.txt"), "w", encoding="utf-8") as f:
    f.write("Files HELD BACK (imported by external/live code) - do NOT auto-delete:\n\n")
    for n in sorted(review):
        f.write(f"{n}:\n  " + "\n  ".join(review[n]) + "\n")

print("Intended SAFE set size :", len(S))
print("DELETED (moved to trash):", len(moved))
print("HELD BACK (review)     :", len(review))
print()
print("HELD-BACK files and why:")
for n in sorted(review):
    print(f"  {n}: " + "; ".join(review[n]))
print("\nTrash dir:", TRASH)
