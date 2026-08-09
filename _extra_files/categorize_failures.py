from pathlib import Path
rep = Path("_extra_files/router_import_report.txt").read_text(encoding="utf-8")
fails = [l for l in rep.splitlines() if l.startswith("FAIL ")]
print("remaining router failures:", len(fails))
circular = [l for l in fails if "partially initialized" in l or "cannot import name" in l]
missing_mod = [l for l in fails if "No module named" in l and "partially" not in l]
print("\n-- circular/import-name errors (need non-cyclic source) --", len(circular))
for l in circular:
    name = l.split("  ")[0].strip()
    detail = l.split("miss=")[-1][:100]
    print(f"  {name:30s} :: {detail}")
print("\n-- missing-module errors --", len(missing_mod))
for l in missing_mod:
    name = l.split("  ")[0].strip()
    detail = l.split("miss=")[-1][:100]
    print(f"  {name:30s} :: {detail}")
