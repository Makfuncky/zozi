"""Idempotency patcher for the 9 table-creating migrations.

Replaces `op.create_table(` -> `safe_create_table(op,` and
`op.drop_table(` -> `safe_drop_table(op,` and ensures the import is present.
Safe, formatting-preserving (no re-indentation): the helpers forward all args.
"""
import re
from pathlib import Path

ROOT = Path("backend/alembic/versions")

FILES = [
    "2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py",
    "2026_07_28_0000_employee_hr_tables.py",
    "2026_07_30_0001-20260730_0001_create_user_points_table.py",
    "2026_07_30_0002-20260730_0002_create_points_transactions_table.py",
    "2026_07_30_0003-20260730_0003_create_upload_jobs_table.py",
    "2026_07_30_0004-20260730_0004_create_event_tables.py",
    "20260730_0008_split_country_configs_into_domain_tables.py",
    "2026_07_31_0010_create_canonical_platform_tables.py",
]

IMPORT_LINE = "from utils.migration_helpers import safe_create_table, safe_drop_table\n"


def patch_file(path: Path):
    src = path.read_text(encoding="utf-8", errors="replace")
    changed = False

    # Ensure import present (after the last top-level import block).
    if "safe_create_table" not in src:
        # find insertion point: after the last top-level import line
        lines = src.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if re.match(r"^(import |from .+ import )", line):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        src = "\n".join(lines) + "\n" if not src.endswith("\n") else "\n".join(lines)
        changed = True

    new = src
    new = new.replace("op.create_table(", "safe_create_table(op, ")
    new = new.replace("op.drop_table(", "safe_drop_table(op, ")
    if new != src:
        changed = True
    path.write_text(new, encoding="utf-8")
    return changed


if __name__ == "__main__":
    for name in FILES:
        p = ROOT / name
        if not p.exists():
            print(f"MISSING: {name}")
            continue
        ok = patch_file(p)
        print(f"{'PATCHED' if ok else 'NO-CHANGE':10} {name}")
