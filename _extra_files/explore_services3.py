from pathlib import Path
from collections import defaultdict
import re

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SERVICES = BACKEND / "services"

SUFFIXES = [
    "_controller_service", "_write_service", "_read_service", "_ops_service",
    "_api_service", "_admin_service", "_query_service", "_fallback_service",
    "_create_service", "_update_service", "_delete_service", "_import_service",
    "_export_service", "_worker", "_engine", "_service",
]

def base(stem: str) -> str:
    s = stem.lower()
    for suf in SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s

files = []
for p in sorted(SERVICES.rglob("*.py")):
    if p.name == "__init__.py":
        continue
    parts = p.relative_to(BACKEND).parts
    folder = parts[1]
    b = base(p.stem)
    files.append((folder, b, p.relative_to(BACKEND)))

# group by concept base
by_base = defaultdict(list)
for folder, b, rel in files:
    by_base[b].append((folder, rel))

print("=== CROSS-FOLDER DUPLICATE CANDIDATES (same concept, >=2 folders) ===")
n_groups = 0
n_files = 0
for b in sorted(by_base, key=lambda x: -len(set(f for f, _ in by_base[x]))):
    folders = [f for f, _ in by_base[b]]
    uniq = sorted(set(folders))
    if len(uniq) >= 2:
        n_groups += 1
        n_files += len(by_base[b])
        print(f"\n[{b}]  folders={uniq}")
        for f, rel in sorted(by_base[b]):
            print(f"     {f:<12} {rel}")

print(f"\nTOTAL cross-folder concept groups: {n_groups}")
print(f"TOTAL files involved: {n_files}")

# also: same base appearing multiple times WITHIN same folder (intra-folder sprawl)
print("\n=== INTRA-FOLDER REPEATED CONCEPTS (>=3 files, same base in same folder) ===")
intra = defaultdict(list)
for folder, b, rel in files:
    intra[(folder, b)].append(rel)
for (folder, b), rels in sorted(intra.items(), key=lambda x: -len(x[1])):
    if len(rels) >= 3:
        print(f"  {folder}/{b}: {len(rels)} files")
