"""Recover the backend source code from the codebase_v*.md knowledge-base dumps.

The dumps embed every source file as:
    ### `backend\path\to\file.py`
    ```python
    ...file contents...
    ```

This script extracts each fenced block following a `### `backend\...`` header and
writes it to backend/<path>. It processes v1..v4 in order so the most recent
(largest) dump wins on conflicts.
"""
from __future__ import annotations
import re
import os

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
BACKEND = os.path.join(ROOT, "backend")
VERSIONS = [1, 2, 3, 4]

HEADER_RE = re.compile(r"^###\s+`backend[\\/](.+?)`\s*$")
FENCE_RE = re.compile(r"^```(\w*)\s*$")


def extract_from_file(md_path):
    written = []
    with open(md_path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    i = 0
    n = len(lines)
    while i < n:
        m = HEADER_RE.match(lines[i].rstrip("\n"))
        if not m:
            i += 1
            continue
        rel = m.group(1).replace("\\", "/").strip()
        # find next fence opening
        j = i + 1
        while j < n and not FENCE_RE.match(lines[j].rstrip("\n")):
            j += 1
        if j >= n:
            break
        fence_open = j
        # find matching closing fence (first ``` at column 0 after open)
        k = fence_open + 1
        while k < n and not (lines[k].rstrip("\n") == "```"):
            k += 1
        if k >= n:
            break
        content = "".join(lines[fence_open + 1:k])
        # skip clearly non-source tree markers
        dest = os.path.join(BACKEND, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", errors="replace") as out:
            out.write(content)
        written.append(rel)
        i = k + 1
    return written


def main():
    all_written = []
    for v in VERSIONS:
        md = os.path.join(ROOT, f"codebase_v{v}.md")
        if not os.path.isfile(md):
            print(f"skip {md} (missing)")
            continue
        written = extract_from_file(md)
        print(f"v{v}: wrote {len(written)} files")
        all_written.extend(written)
    # de-dup preserve order
    seen = set()
    uniq = [x for x in all_written if not (x in seen or seen.add(x))]
    print(f"TOTAL unique files recovered: {len(uniq)}")


if __name__ == "__main__":
    main()
