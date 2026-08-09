"""Dump every audit finding whose location mentions any of the given keywords."""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"
FINDING_RE = re.compile(r"^- (?:\U0001F7E2|\U0001F7E1|\U0001F534) \*\*([A-Z0-9]+)\*\* `([^`]*)`")


def main() -> int:
    keys = [k.lower() for k in sys.argv[1:]]
    seen: set[str] = set()
    rows: list[tuple[str, str, str]] = []
    for line in REPORT.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        m = FINDING_RE.match(s)
        if not m:
            continue
        code, loc = m.group(1), m.group(2)
        low = loc.lower()
        if not any(k in low for k in keys):
            continue
        if s in seen:
            continue
        seen.add(s)
        rows.append((code, loc, s))

    print(f"TOTAL={len(rows)}")
    print("\nBY CODE:", collections.Counter(r[0] for r in rows).most_common())
    print("\nBY FILE:")
    for f, n in collections.Counter(r[1].split(":")[0] for r in rows).most_common():
        print(f"  {n:4d}  {f}")
    print("\nFINDINGS:")
    for code in sorted({r[0] for r in rows}):
        sub = [r for r in rows if r[0] == code]
        print(f"\n--- {code} ({len(sub)}) ---")
        for _, _, s in sub:
            print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
