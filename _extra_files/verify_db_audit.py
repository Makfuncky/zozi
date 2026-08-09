from __future__ import annotations
"""Read-only DATABASE audit harness.

Imports the audit module as a library and runs ONLY dba_run_all_checks()
in-memory. It never calls main(), so SYSTEM_AUDIT_REPORT.md is NOT regenerated
and no audit script is modified.
"""
import sys
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
AUDIT_DIR = REPO / "scripts" / "system_trackers"

sys.path.insert(0, str(AUDIT_DIR))

import system_architecture_audit as A  # noqa: E402

rep = A.Report()
db_models, db_minfo, db_rls = A.dba_run_all_checks(REPO, rep)

codes = {}
for f in rep.findings:
    codes.setdefault(f.code, 0)
    codes[f.code] += 1

print("=== ALL DATABASE (DBA*) FINDINGS ===")
for code in sorted(codes):
    if code.startswith("DBA") or code.startswith("DB"):
        print(f"  {code}: {codes[code]}")

print("\n=== ALL FLAGGED CODES (detail, capped) ===")
for code in sorted(codes):
    if not (code.startswith("DBA") or code.startswith("DB")):
        continue
    items = [f for f in rep.findings if f.code == code]
    print(f"\n-- {code}: {len(items)} finding(s) --")
    for it in items[:400]:
        print(f"    [{it.sev}] {it.path}:{it.line} | {it.message}")
