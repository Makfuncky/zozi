"""Read-only helper: slice SYSTEM_AUDIT_REPORT.md down to backend/controllers findings.

Usage:
    python _extra_files/audit_slice.py            # summary counts by code
    python _extra_files/audit_slice.py W1         # detail rows for a code
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

ROW = re.compile(r"^\|\s*(🔴|🟡|🟢)\s*\|\s*([A-Z0-9_]+)\s*\|\s*([^|]*?)\s*\|\s*`?([^|`]*?)`?\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")

TARGET = "backend\\controllers"


def rows():
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    # only the "All Findings by Domain" section onward, but rows are unique anyway
    seen = set()
    for line in text.splitlines():
        m = ROW.match(line.strip())
        if not m:
            continue
        sev, code, domain, path, msg, intended = m.groups()
        key = (code, path, msg)
        if key in seen:
            continue
        seen.add(key)
        yield sev, code, domain, path, msg, intended


def main() -> int:
    want = sys.argv[1] if len(sys.argv) > 1 else None
    counts = Counter()
    detail = defaultdict(list)
    for sev, code, domain, path, msg, intended in rows():
        if TARGET not in path:
            continue
        counts[(sev, code)] += 1
        detail[code].append((sev, path, msg))
    if want:
        for sev, path, msg in sorted(detail.get(want, [])):
            print(f"{sev} {path} :: {msg}")
        print(f"\nTOTAL {want}: {len(detail.get(want, []))}")
        return 0
    total_red = total_yel = 0
    for (sev, code), n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][1])):
        print(f"{sev} {code:<8} {n}")
        if sev == "🔴":
            total_red += n
        elif sev == "🟡":
            total_yel += n
    print(f"\ncontrollers RED={total_red} YELLOW={total_yel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
