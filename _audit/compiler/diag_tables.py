"""Diagnostic: report every markdown table in every dimension file, whether the
normaliser accepted it, and why not. Read-only. No judgement about findings.
"""
from __future__ import annotations

import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_dimensions import (  # noqa: E402
    DIM_DIR, ROOT, is_table_header, norm_header, split_row, STATUS_TOKENS,
)

TARGETS = set(sys.argv[1:]) or {
    "00_boot_smoke_test", "08_providers", "09_laws", "21_contradictions",
    "23_code_intent", "22_anti_patterns",
}

for f in sorted(glob.glob(os.path.join(DIM_DIR, "*.md"))):
    dim = os.path.splitext(os.path.basename(f))[0]
    if dim not in TARGETS:
        continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    print(f"\n{'=' * 100}\n### {dim}\n{'=' * 100}")
    section = "(top)"
    i, n, t = 0, len(lines), 0
    while i < n:
        h = lines[i].strip()
        if h.startswith("#"):
            section = h.lstrip("#").strip()
        if h.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            header = split_row(h)
            body, j = [], i + 2
            while j < n and lines[j].strip().startswith("|"):
                body.append(lines[j]); j += 1
            t += 1
            matched = [(x, norm_header(x)) for x in header]
            hits = [m for m in matched if m[1]]
            status_like = any(
                norm_header(x) == "Status"
                or re.search(r"\b(" + "|".join(STATUS_TOKENS) + r")\b", x, re.I)
                for x in header
            )
            first = split_row(body[0]) if body else []
            first_tok = " ".join(first[:3])[:70]
            verdict = "ACCEPT" if (is_table_header(header) and status_like) else "REJECT"
            reason = []
            if not is_table_header(header):
                reason.append(f"alias_hits={len(hits)}<3 or cols={len(header)}<3")
            if not status_like:
                reason.append("no_status_like_header")
            print(f"  table#{t} [{verdict}] section={section!r} cols={len(header)} "
                  f"rows={len(body)} {';'.join(reason)}")
            print(f"    header: {header}")
            print(f"    hits  : {hits}")
            print(f"    row1  : {first_tok}")
            i = j
            continue
        i += 1
