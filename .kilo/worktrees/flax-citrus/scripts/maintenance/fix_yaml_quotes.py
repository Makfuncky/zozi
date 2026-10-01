#!/usr/bin/env python3
"""Fix unquoted list items in feature_definitions.yaml expected blocks."""
import re

path = r"scripts\system_trackers\feature_definitions.yaml"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    stripped = line.rstrip("\n")
    if not re.match(r"^\s+-\s+", stripped):
        continue
    if stripped.strip().startswith('"') or stripped.strip().startswith("'"):
        continue
    if "->" not in stripped:
        continue
    if ": " not in stripped.split("->")[-1]:
        continue
    m = re.match(r"^(\s+-\s+)(.*)$", stripped)
    if m:
        indent = m.group(1)
        value = m.group(2).replace('"', '\\"')
        lines[i] = f'{indent}"{value}"\n'
        fixed += 1

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Fixed {fixed} lines")
