import sys, importlib.util
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts\system_trackers")

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
spec = importlib.util.spec_from_file_location(
    "migration_tracker", ROOT / "scripts/system_trackers/migration_tracker.py"
)
mt = importlib.util.module_from_spec(spec)
sys.modules["migration_tracker"] = mt
spec.loader.exec_module(mt)
print("CANONICAL_DOMAINS source OK, count =", len(mt.CANONICAL_DOMAINS))

routers = mt.scan_directory(mt.ROUTERS_DIR, "router")
controllers = mt.scan_directory(mt.CONTROLLERS_DIR, "controller")
services = mt.scan_directory(mt.SERVICES_DIR, "service")
models = mt.scan_directory(mt.MODELS_DIR, "model")
all_files = routers + controllers + services + models

import_map = mt._build_import_map(all_files)
sc = mt.analyze_service_consolidation(services, all_files, import_map)

# Now run the FULL main() pipeline and compare
full = mt.run_full_audit(strict=False)
fsc = full.service_consolidation
print("=== COMPARISON: direct call vs full run_full_audit() ===")
print("direct  tier5 pairs:", len(sc.tier5_structural_dups), "| target:", sc.realistic_target)
print("full    tier5 pairs:", len(fsc.tier5_structural_dups), "| target:", fsc.realistic_target)
print("full    union target check: 534 -", end=" ")
t0d={f.file_a for f in fsc.tier0_safe_deletes if f.action=='DELETE'}
t0r={f.file_a for f in fsc.tier0_safe_deletes if f.action=='REVIEW'}
t1s=set()
for f in fsc.tier1_exact_duplicates: t1s.add(f.file_a); t1s.add(f.file_b)
t2s={f.file_a for f in fsc.tier2_naming_variants}
t3s={f.file_a for f in fsc.tier3_read_write_split}
t4m={f.file_a for f in fsc.tier4_thin_forwarders if f.action=='MERGE'}
t4r={f.file_a for f in fsc.tier4_thin_forwarders if f.action=='REVIEW'}
t5s=set()
for f in fsc.tier5_structural_dups: t5s.add(f.file_a); t5s.add(f.file_b)
t6s=set()
for f in fsc.tier6_cross_folder: t6s.add(f.file_a); t6s.add(f.file_b)
print("union =", len(t0d|t0r|t1s|t2s|t3s|t4m|t4r|t5s|t6s), "-> target", 534-len(t0d|t0r|t1s|t2s|t3s|t4m|t4r|t5s|t6s))

t0_del = {f.file_a for f in sc.tier0_safe_deletes if f.action == "DELETE"}
t0_rev = {f.file_a for f in sc.tier0_safe_deletes if f.action == "REVIEW"}
t1 = set()
for f in sc.tier1_exact_duplicates:
    t1.add(f.file_a); t1.add(f.file_b)
t2 = {f.file_a for f in sc.tier2_naming_variants}
t3 = {f.file_a for f in sc.tier3_read_write_split}
t4_merge = {f.file_a for f in sc.tier4_thin_forwarders if f.action == "MERGE"}
t4_rev = {f.file_a for f in sc.tier4_thin_forwarders if f.action == "REVIEW"}
t5 = set()
for f in sc.tier5_structural_dups:
    t5.add(f.file_a); t5.add(f.file_b)
t6 = set()
for f in sc.tier6_cross_folder:
    t6.add(f.file_a); t6.add(f.file_b)

union = t0_del | t0_rev | t1 | t2 | t3 | t4_merge | t4_rev | t5 | t6

print("Total services:", sc.total_services)
print("Tier0 DELETE :", len(t0_del), "| Tier0 REVIEW:", len(t0_rev))
print("Tier1 files  :", len(t1))
print("Tier2 files  :", len(t2))
print("Tier3 files  :", len(t3))
print("Tier4 MERGE  :", len(t4_merge), "| Tier4 REVIEW:", len(t4_rev))
print("Tier5 files  :", len(t5), "(from", len(sc.tier5_structural_dups), "pairs)")
print("Tier6 files  :", len(t6), "(from", len(sc.tier6_cross_folder), "pairs)")
print("Sum of tier file-sets (with overlaps):",
      len(t0_del)+len(t0_rev)+len(t1)+len(t2)+len(t3)+len(t4_merge)+len(t4_rev)+len(t5))
print("UNIQUE union :", len(union))
print("534 - union  :", sc.total_services - len(union))
print("realistic_target (engine):", sc.realistic_target)
print("safe_immediate (t0_del|t1|t4_merge):", len(t0_del | t1 | t4_merge))
print("Tier0 DELETE files:", sorted(t0_del))
print("Tier0 REVIEW files:", sorted(t0_rev))
