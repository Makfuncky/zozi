#!/usr/bin/env python3
"""Fix the broken files from the first script."""

import argparse
import re
import sys
from pathlib import Path


def fix_file(filepath):
    """Fix the broken require_feature() placements."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    result = []
    i = 0
    fixed = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        decorator_match = re.match(
            r'^(\s*)@router\.(get|post|put|delete|patch|head|options|trace)\("([^"]+)"[^)]*\)\s*$',
            line
        )

        if decorator_match:
            indent = decorator_match.group(1)
            method = decorator_match.group(2)
            path = decorator_match.group(3)

            result.append(line)
            i += 1

            temp_i = i
            while temp_i < len(lines) and lines[temp_i].strip() == "":
                temp_i += 1

            if temp_i < len(lines) and lines[temp_i].strip().startswith("require_feature("):
                check_i = temp_i + 1
                while check_i < len(lines) and lines[check_i].strip() == "":
                    check_i += 1

                if check_i < len(lines):
                    next_line = lines[check_i].strip()
                    if next_line.startswith("def ") or next_line.startswith("async def "):
                        i = temp_i + 1
                        fixed += 1
                        continue
                    else:
                        i = temp_i + 1
                        fixed += 1
                        continue
            continue

        result.append(line)
        i += 1

    return "\n".join(result), fixed


def remove_fix_scripts(scripts_dir, dry_run=False):
    """Remove sibling fix_*.py scripts per Law 27."""
    removed = []
    for p in sorted(scripts_dir.glob("fix_*.py")):
        if p.name == Path(__file__).name:
            continue
        if dry_run:
            print(f"[DRY RUN] Would remove: {p}")
        else:
            p.unlink()
            print(f"Removed: {p}")
        removed.append(p)
    return removed


def main():
    parser = argparse.ArgumentParser(description="Fix misplaced require_feature() calls in module routers.")
    parser.add_argument("--dry-run", action="store_true", help="Report fixes without writing files or removing scripts.")
    args = parser.parse_args()

    base_path = Path(__file__).resolve().parent
    scripts_dir = base_path

    files = [
        "customer/routers/finance.py",
        "customer/routers/promotions.py",
        "employee/routers/accounts.py",
        "employee/routers/comms.py",
        "employee/routers/finance.py",
        "employee/routers/orders.py",
        "employee/routers/security.py",
        "employee/routers/suppliers.py",
        "logistics/routers/logistics.py",
    ]

    any_fixed = False

    for rel_path in files:
        filepath = base_path / rel_path
        if not filepath.exists():
            continue

        new_content, fixed = fix_file(str(filepath))
        if fixed > 0:
            any_fixed = True
            if args.dry_run:
                print(f"[DRY RUN] Would fix {rel_path}: removed {fixed} misplaced require_feature() calls")
            else:
                print(f"Fixed {rel_path}: removed {fixed} misplaced require_feature() calls")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
        else:
            print(f"{rel_path}: no issues found")

    remove_fix_scripts(scripts_dir, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN] No files written, no scripts removed.")
    elif any_fixed:
        self_path = Path(__file__).resolve()
        print(f"Removing self: {self_path}")
        self_path.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
