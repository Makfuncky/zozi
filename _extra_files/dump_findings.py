"""Dump all SYSTEM_AUDIT_REPORT.md findings matching a set of path keywords."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

LINE_RE = re.compile(r"^- (?P<sev>[\U0001F534\U0001F7E1\U0001F7E2]) \*\*(?P<code>[A-Z0-9]+)\*\* `(?P<loc>[^`]+)`(?P<rest>.*)$")
SEV_MAP = {"\U0001F534": "RED", "\U0001F7E1": "YEL", "\U0001F7E2": "INF"}


def main() -> None:
    keywords = [k.lower() for k in sys.argv[1:]]
    if not keywords:
        print("usage: dump_findings.py <kw> [kw...]")
        return
    text = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, l in enumerate(text) if l.startswith("## 9."))
    end = next(i for i, l in enumerate(text) if l.startswith("## 10."))

    hits: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for line in text[start:end]:
        m = LINE_RE.match(line)
        if not m:
            continue
        loc = m.group("loc")
        low = loc.replace("\\", "/").lower()
        if not any(k in low for k in keywords):
            continue
        key = line
        if key in seen:
            continue
        seen.add(key)
        hits.append((SEV_MAP.get(m.group("sev"), "?"), m.group("code"), loc, m.group("rest").strip()))

    codes = Counter(h[1] for h in hits)
    sevs = Counter(h[0] for h in hits)
    files = Counter(h[2].split(":")[0] for h in hits)

    print(f"MATCHED {len(hits)} findings  sev={dict(sevs)}")
    print("\n--- CODES ---")
    for c, n in codes.most_common():
        print(f"  {c:8s} {n}")
    print("\n--- FILES ---")
    for f, n in files.most_common():
        print(f"  {n:4d}  {f}")
    print("\n--- DETAIL ---")
    for sev, code, loc, rest in sorted(hits, key=lambda h: (h[0] != "RED", h[1], h[2])):
        print(f"[{sev}] {code:8s} {loc}  {rest}")


if __name__ == "__main__":
    main()
