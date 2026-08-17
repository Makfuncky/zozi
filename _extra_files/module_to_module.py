import re
from pathlib import Path
from collections import defaultdict

paths = [ln.strip() for ln in Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt").read_text().splitlines()
         if ln.strip() and ln.strip().endswith(".py")]

STOP = {
    "service","services","controller","controllers","handler","handlers","helper","helpers",
    "util","utils","common","base","abstract","interface","impl","write","read","create",
    "update","delete","get","list","bulk","batch","query","router","routes","ops","operations",
    "operation","admin","public","core","api","unified","fallback","engine","background","scheduler",
    "scheduling","worker","v1","v2","v3","new","old","temp","job","jobs","legacy","sync","upload",
    "uploads","download","mgr","svc","fn","func","function",
}

def norm(t):
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith("s") and len(t) > 3:
        return t[:-1]
    return t

def concept(stem):
    toks = [t for t in re.split(r"[_\-]", stem.lower()) if t and t not in STOP]
    key = tuple(sorted(norm(t) for t in toks))
    return key if key else (stem.lower(),)

# Per-folder stats
folder_files = defaultdict(int)
folder_concepts = defaultdict(set)
for p in paths:
    parts = Path(p).parts
    folder = parts[0]
    folder_files[folder] += 1
    folder_concepts[folder].add(concept(Path(p).stem))

print("PER-FOLDER: files -> distinct concepts (within folder)")
total_files = 0
total_concepts = 0
for f in sorted(folder_files):
    total_files += folder_files[f]
    total_concepts += len(folder_concepts[f])
    print(f"  {f:12} {folder_files[f]:4} files  {len(folder_concepts[f]):4} concepts")
print(f"  {'TOTAL':12} {total_files:4} files  {total_concepts:4} concepts (within-folder, double counts cross-folder)")

# Cross-folder concepts (same concept appears in >=2 folders)
print("\nCROSS-FOLDER REDUNDANCY (concept spans multiple modules):")
by_concept = defaultdict(list)
for p in paths:
    folder = Path(p).parts[0]
    by_concept[concept(Path(p).stem)].append((folder, p))

cross = {k: v for k, v in by_concept.items() if len({f for f, _ in v}) >= 2}
print(f"  total cross-folder concepts: {len(cross)}")
multi_file = {k: v for k, v in by_concept.items() if len(v) > 1}
print(f"  total multi-file concepts (any): {len(multi_file)}")
print(f"  total raw files: {len(paths)}")
print(f"  distinct concepts overall: {len(by_concept)}")
print()
for k in sorted(cross, key=lambda k: -len({f for f, _ in cross[k]})):
    folders = sorted({f for f, _ in cross[k]})
    print(f"  {k}  ->  {len(folders)} modules: {folders}")
