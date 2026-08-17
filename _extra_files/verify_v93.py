import re
from pathlib import Path

paths = [ln.strip() for ln in Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt").read_text().splitlines() if ln.strip()]
paths = [p for p in paths if p.endswith(".py")]

_STOP = {
    "service", "services", "controller", "controllers", "handler", "handlers",
    "manager", "managers", "helper", "helpers", "util", "utils", "common",
    "base", "abstract", "interface", "impl", "write", "read", "create",
    "update", "delete", "get", "list", "bulk", "batch", "query", "router",
    "routes", "ops", "operations", "operation", "admin", "public", "core",
    "api", "unified", "fallback", "engine", "background", "scheduler",
    "scheduling", "worker", "v1", "v2", "v3", "new", "old", "temp", "job",
    "jobs", "legacy", "sync", "upload", "uploads", "download", "mgr", "svc",
    "fn", "func", "function",
}

def norm(t):
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith("s") and len(t) > 3:
        return t[:-1]
    return t

groups = {}
for p in paths:
    stem = Path(p).stem.lower()
    toks = [t for t in re.split(r"[_\-]", stem) if t and t not in _STOP]
    key = tuple(sorted(norm(t) for t in toks))
    if not key:
        key = (stem,)
    groups.setdefault(key, []).append(p)

print(f"TOTAL FILES: {len(paths)}")
multi = {k: v for k, v in groups.items() if len(v) > 1}
print(f"DISTINCT CONCEPTS: {len(groups)}")
print(f"CONCEPTS WITH >1 FILE: {len(multi)}")
print(f"FILES IN MULTI-GROUPS: {sum(len(v) for v in multi.values())}")
print("=" * 80)

# Sort groups by size desc then key
for k in sorted(multi.keys(), key=lambda k: (-len(groups[k]), k)):
    print(f"\n[{len(groups[k])}] {k}")
    for f in sorted(groups[k]):
        print(f"     {f}")

print("\n" + "=" * 80)
print("SINGLETON CONCEPTS (one file each) — count:")
singles = [k for k in groups if len(groups[k]) == 1]
print(len(singles))
for k in sorted(singles):
    print(f"   {groups[k][0]}")
