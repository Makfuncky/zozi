#!/usr/bin/env python3
"""Fix the logistics.py file by reconstructing broken function definitions.
The first script removed 'def func_name(...)' lines from single-line function defs.
This script detects @router decorators followed by indented parameter lines
(without a def line) and reconstructs the function definition."""

import re
from pathlib import Path


def fix_logistics_file(filepath):
    """Fix function definitions in the logistics file."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    result = []
    i = 0
    fixed = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a router decorator
        decorator_match = re.match(
            r'^(\s*)@router\.(get|post|put|delete|patch|head|options|trace)\("([^"]+)"[^)]*\)\s*$',
            line
        )

        if decorator_match:
            indent = decorator_match.group(1)
            method = decorator_match.group(2)
            path = decorator_match.group(3)

            # Add the decorator line
            result.append(line)
            i += 1

            # Skip blank lines
            while i < len(lines) and lines[i].strip() == "":
                result.append(lines[i])
                i += 1

            if i >= len(lines):
                break

            next_line = lines[i]
            next_stripped = next_line.strip()

            # Check if next line is a function definition
            if re.match(r"(async\s+)?def\s+\w+\s*\(", next_stripped):
                # Function def exists - it's fine
                result.append(next_line)
                i += 1
                continue

            # Check if next line is a docstring (function def was removed)
            if next_stripped.startswith('"""') or next_stripped.startswith("'''"):
                # Might be a docstring after a missing function def
                result.append(next_line)
                i += 1
                continue

            # Check if next line starts with require_feature (misplaced)
            if next_stripped.startswith("require_feature("):
                # This is a misplaced require_feature - skip it
                i += 1
                continue

            # If next line is indented body code, the function def is missing
            if next_line.startswith(indent + "    ") or next_line.startswith(indent + "\t"):
                # Function def is missing - we need to reconstruct it
                # But we don't know the original function name or signature
                # This is the broken case
                fixed += 1
                # We can't reconstruct without knowing the original signature
                # Just add the line as-is for now
                result.append(next_line)
                i += 1
                continue

            result.append(next_line)
            i += 1
            continue

        result.append(line)
        i += 1

    return "".join(result), fixed


def main():
    filepath = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\modules\logistics\routers\logistics.py")

    new_content, fixed = fix_logistics_file(str(filepath))
    print(f"Found {fixed} broken functions (cannot auto-fix without original signatures)")


if __name__ == "__main__":
    main()
