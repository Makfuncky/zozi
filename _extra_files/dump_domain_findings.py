"""Dump all SYSTEM_AUDIT_REPORT.md findings for a given backend domain module."""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

FINDING_RE = re.compile(r"^- (?:🟢|🟡|🔴) \*\*([A-Z0-9]+)\*\* `([^`]*)`")


def main() -> int:
    domain = sys.argv[1]
    extra = sys.argv[2:] if len(sys.argv) > 2 else []
    pats = [
        re.compile(rf"(^|/)(models|services|controllers|providers|events|jobs)/{domain}(/|$)"),
        re.compile(rf"(^|/)routers/[a-z0-9_]*_{domain}_"),
        re.compile(rf"(^|/)routers/{domain}_"),
    ] + [re.compile(p) for p in extra]

    lines = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    seen: set[str] = set()
    by_code: dict[str, list[str]] = collections.defaultdict(list)
    for line in lines:
        s = line.strip()
        m = FINDING_RE.match(s)
        if not m:
            continue
        code, loc = m.group(1), m.group(2)
        norm = loc.replace("\\", "/").lower()
        if not any(p.search(norm) for p in pats):
            continue
        if s in seen:
            continue
        seen.add(s)
        by_code[code].append(s)

    total = sum(len(v) for v in by_code.values())
    print(f"### domain={domain}  total={total}\n")
    for code in sorted(by_code, key=lambda c: (-len(by_code[c]), c)):
        print(f"\n--- {code} ({len(by_code[code])}) ---")
        for s in by_code[code]:
            print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
