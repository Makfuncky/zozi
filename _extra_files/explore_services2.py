from pathlib import Path
from collections import defaultdict

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SERVICES = BACKEND / "services"

CANON = {
    "core","admin","comms","finance","geography","hr","security","supplier",
    "treasury","logistics","commerce","public","common","orders","catalog",
    "ai","gateways","users","audit","customer","system","analytics",
    "governance","country","employee","hierarchy","identity","location_service",
    "products","promotions","api","mcp","unknown",
}
# folder -> canonical domain it SHOULD belong to
FOLDER_CANON = {
    "users": "identity", "employee": "hr", "hierarchy": "hr",
    "country": "geography", "location_service": "geography",
    "products": "catalog", "promotions": "commerce",
    "gateways": "gateway", "api": "core",
}

# gather
folders = defaultdict(list)
for p in sorted(SERVICES.rglob("*.py")):
    if p.name == "__init__.py":
        continue
    parts = p.relative_to(BACKEND).parts
    folder = parts[1]
    folders[folder].append(p)

print("=== TOP-LEVEL SERVICE FOLDERS ===")
print(f"{'folder':<18}{'files':>5}  canonical? -> maps_to")
for f in sorted(folders, key=lambda x: -len(folders[x])):
    n = len(folders[f])
    canon = "yes(CANON)" if f in ("gateway","finance","treasury","orders","catalog",
        "commerce","supplier","customer","logistics","comms","hr","ai","audit",
        "security","identity","geography","media","analytics","configuration",
        "inventory","pricing","reviews","search","events","webhooks","documents",
        "reporting","shipping","billing","notifications","permissions","core",
        "governance","mcp","system","delegators","router_bridges","common") else "ALIAS"
    maps = FOLDER_CANON.get(f, "")
    print(f"{f:<18}{n:>5}  {canon:<10} -> {maps}")

# files living in alias folders
alias_files = [(f, p) for f, ps in folders.items() if f in FOLDER_CANON for p in ps]
print(f"\n=== FILES IN ALIAS FOLDERS (missed by domain detection): {len(alias_files)} ===")
for f, p in sorted(alias_files, key=lambda x: (x[0], str(x[1]))):
    print(f"  [{FOLDER_CANON[f]:<10}] {p.relative_to(BACKEND)}")

# big canonical folders: list stems to eyeball redundancy
print("\n=== FILE STEMS IN LARGEST FOLDERS (redundancy scan) ===")
for f in sorted(folders, key=lambda x: -len(folders[x]))[:8]:
    if len(folders[f]) < 20:
        continue
    stems = sorted(p.stem for p in folders[f])
    print(f"\n-- {f} ({len(stems)} files) --")
    for s in stems:
        print(f"   {s}")
