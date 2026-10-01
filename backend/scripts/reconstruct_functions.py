#!/usr/bin/env python3
"""Reconstruct broken function definitions in router files.
The first script removed 'def func_name(...)' lines from single-line function defs.
This script detects @router decorators followed by indented parameter lines
(without a def line) and reconstructs the function definition with a generated name."""

import re
from pathlib import Path


def generate_function_name(method, path):
    """Generate a function name from HTTP method and path."""
    # Remove leading slash and replace special chars
    name = path.strip("/")
    name = name.replace("{", "").replace("}", "")
    name = name.replace("-", "_").replace("/", "_")
    name = name.strip("_")

    # Remove duplicate underscores
    while "__" in name:
        name = name.replace("__", "_")

    # Add method prefix
    method_prefix = {
        "get": "get",
        "post": "create",
        "put": "update",
        "delete": "delete",
        "patch": "update",
    }.get(method.lower(), method.lower())

    if name:
        return f"{method_prefix}_{name}"
    return f"{method_prefix}"


def fix_file(filepath):
    """Fix function definitions that were broken by the first script."""
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

            # Check if next line is a function definition (already correct)
            if re.match(r"(async\s+)?def\s+\w+\s*\(", next_stripped):
                result.append(next_line)
                i += 1
                continue

            # Check if next line starts with require_feature (misplaced)
            if next_stripped.startswith("require_feature("):
                i += 1
                continue

            # If next line is indented parameter code, the function def is missing
            if next_line.startswith(indent + "    ") or next_line.startswith(indent + "\t"):
                # Function def is missing - reconstruct it
                fixed += 1

                # Generate function name
                func_name = generate_function_name(method, path)

                # Check if any parameter uses async (for async def)
                # Look ahead to see if body uses await
                uses_async = False
                for j in range(i, min(i + 20, len(lines))):
                    if "await " in lines[j]:
                        uses_async = True
                        break

                # Add the function definition line
                async_prefix = "async " if uses_async else ""
                result.append(f"{indent}{async_prefix}def {func_name}(\n")

                # Now add the parameter lines and the rest of the function
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
    files = [
        r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\modules\logistics\routers\logistics.py",
        r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\modules\customer\routers\promotions.py",
        r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\modules\employee\routers\finance.py",
    ]

    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            print(f"WARNING: {filepath} not found")
            continue

        new_content, fixed = fix_file(str(path))
        print(f"{path.name}: fixed {fixed} broken functions")

        with open(str(path), "w", encoding="utf-8") as f:
            f.write(new_content)


if __name__ == "__main__":
    main()
