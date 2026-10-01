#!/usr/bin/env python3
"""Undo all changes from the first script - remove all require_feature calls and imports."""

import re
from pathlib import Path


def undo_changes(filepath):
    """Remove all require_feature calls and imports added by the first script."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    result = []
    removed_imports = 0
    removed_calls = 0

    for line in lines:
        stripped = line.strip()

        # Remove require_feature import
        if stripped == "from rbac.dependencies import require_feature":
            removed_imports += 1
            continue

        # Remove require_feature() calls
        if stripped.startswith("require_feature(") and stripped.endswith(")"):
            removed_calls += 1
            continue

        result.append(line)

    return "".join(result), removed_imports, removed_calls


def main():
    base_path = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\modules")

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

    for rel_path in files:
        filepath = base_path / rel_path
        if not filepath.exists():
            continue

        new_content, removed_imports, removed_calls = undo_changes(str(filepath))
        if removed_imports > 0 or removed_calls > 0:
            print(f"{rel_path}: removed {removed_imports} imports, {removed_calls} calls")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
        else:
            print(f"{rel_path}: no changes to undo")


if __name__ == "__main__":
    main()
