"""Locate Problem entries in the worklist that do not cite a finding ID, so
the completeness gate's WARN can be driven to zero or explained.
"""

import io
import re

WL = "_audit/TO_BE_RESOLVE.md"
ID = re.compile(r"`[A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9._-]+`")

lines = io.open(WL, encoding="utf-8").read().split("\n")
bad = 0
for i, line in enumerate(lines, 1):
    if re.match(r"^\s+\d+\. ", line) and line.rstrip().endswith(")") and not ID.search(line):
        bad += 1
        print(f"LINE {i}: {line[:400]}")
        for j in range(max(0, i - 6), i):
            print(f"   ctx {j + 1}: {lines[j][:120]}")
print(f"\nuncited Problem entries: {bad}")