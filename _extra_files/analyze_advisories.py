import json
from pathlib import Path
from collections import defaultdict

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
data = json.loads((REPO / "_extra_files" / "full_audit_findings.json").read_text(encoding="utf-8"))
F = data["findings"]

import importlib.util
spec = importlib.util.spec_from_file_location(
    "sysaudit2", str(REPO / "scripts" / "system_trackers" / "system_architecture_audit.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RM = m.RULE_MEANING

tally = defaultdict(lambda: {"n": 0, "sum": 0})
for f in F:
    k = (f["code"], f["sev"])
    tally[k]["n"] += 1
    tally[k]["sum"] += int(f.get("count") or 1)

align_prefixes = ("W", "Q", "M", "R", "G", "D", "S", "L", "A", "P", "H", "CIR",
                  "RN", "DG", "DOM", "MV", "SYM", "CG", "LC", "FT", "CA", "MW",
                  "BC", "REG", "SCF", "X", "API")
def is_align(code):
    return any(code.startswith(p) for p in align_prefixes) and not code.startswith("DBA")

# ---- RED breakdown ----
print("=== RED (VIOLATION) CODES BY SUM-COUNT ===")
red_rows = sorted(((c, v["n"], v["sum"], RM.get(c, ""))
                   for (c, s), v in tally.items() if s == "VIOLATION"),
                  key=lambda r: (-r[2], -r[1]))
for code, n, s, desc in red_rows[:50]:
    print(f"{code:7} {n:6} {s:7}  {desc[:55]}")
print(f"RED codes: {len(red_rows)}  RED findings: {sum(r[1] for r in red_rows)}")

# ---- Advisory breakdown ----
print("\n=== TOP ADVISORY (YEL) CODES BY SUM-COUNT ===")
rows = sorted(((c, v["n"], v["sum"], RM.get(c, ""))
               for (c, s), v in tally.items() if s == "ADVISORY"),
              key=lambda r: (-r[2], -r[1]))
for code, n, s, desc in rows[:70]:
    print(f"{code:7} {n:6} {s:7}  {desc[:55]}")
print(f"\nadvisory codes: {len(rows)}")

align_sum = sum(s for code, n, s, d in rows if is_align(code))
hyg_sum = sum(s for code, n, s, d in rows if not is_align(code))
print(f"\nAdvisory sum-count ALIGNED (structure/layer/dep/coupling/domain): {align_sum}")
print(f"Advisory sum-count HYGIENE/other/security-perf                   : {hyg_sum}")

# Where do advisories live (top files)
byfile = defaultdict(lambda: {"n": 0, "sum": 0})
for f in F:
    if f["sev"] == "ADVISORY":
        byfile[f["loc"]]["n"] += 1
        byfile[f["loc"]]["sum"] += int(f.get("count") or 1)
print("\n=== TOP 25 FILES BY ADVISORY SUM-COUNT ===")
for loc, v in sorted(byfile.items(), key=lambda kv: -kv[1]["sum"])[:25]:
    print(f"{v['sum']:6} {v['n']:5}  {loc}")
