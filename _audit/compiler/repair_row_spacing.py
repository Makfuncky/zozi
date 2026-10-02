"""Restore markdown pipe spacing on the rows the status rewrite touched.

The rewrite rebuilt table rows with `"|".join(cells)`, which removed the
` | ` padding the audit had written. The tables still render, but it created
a noisy diff across 567 lines in 30 files. This restores the original
spacing on exactly those rows — those whose first cell is a known finding ID —
and leaves every other table byte-identical.
"""

from __future__ import annotations

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIM = os.path.join(ROOT, "_audit", "dimensions")
FINDINGS = os.path.join(ROOT, "_audit", "compiler", "_findings.json")

ROW = re.compile(r"^\|\s*([A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9][A-Za-z0-9._-]*)\s*\|")


def main() -> int:
    corpus = json.load(open(FINDINGS, encoding="utf-8"))
    ids = {r["ID"] for r in corpus["findings"]}
    fixed = 0
    touched = 0
    for path in sorted(glob.glob(os.path.join(DIM, "*.md"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        changed = 0
        for i, line in enumerate(lines):
            m = ROW.match(line)
            if not m or m.group(1) not in ids:
                continue
            if " | " in line:          # already spaced correctly
                continue
            if not line.rstrip().endswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            lines[i] = "| " + " | ".join(cells) + " |"
            changed += 1
        if changed:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            fixed += changed
            touched += 1
    print(f"restored pipe spacing on {fixed} rows across {touched} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())