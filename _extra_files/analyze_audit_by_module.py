"""Analyze SYSTEM_AUDIT_REPORT.md findings and group them by backend domain module.

Read-only helper. Writes nothing except stdout.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

DOMAINS = [
    "ai", "analytics", "audit", "catalog", "commerce", "comms", "communication",
    "configuration", "core", "country", "customer", "finance", "geography", "hr",
    "location", "logistics", "media", "orders", "security", "supplier", "suppliers",
    "treasury",
]

FINDING_RE = re.compile(r"^- (?:🟢|🟡|🔴) \*\*([A-Z0-9]+)\*\* `([^`]*)`")


def main() -> int:
    text = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    per_domain: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    per_domain_files: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    total = 0
    for line in text:
        m = FINDING_RE.match(line.strip())
        if not m:
            continue
        code, loc = m.group(1), m.group(2)
        total += 1
        norm = loc.replace("\\", "/").lower()
        matched = set()
        for d in DOMAINS:
            if re.search(rf"(^|/)(models|services|controllers|providers|events|jobs)/{d}(/|$)", norm):
                matched.add(d)
            elif re.search(rf"(^|/)routers/[a-z_]*_{d}_", norm) or re.search(rf"(^|/)routers/{d}_", norm):
                matched.add(d)
        for d in matched:
            per_domain[d][code] += 1
            per_domain_files[d][loc.split(":")[0]] += 1

    print(f"total parsed findings: {total}\n")
    rows = sorted(per_domain.items(), key=lambda kv: -sum(kv[1].values()))
    for d, counter in rows:
        print(f"=== {d}: {sum(counter.values())} findings, {len(per_domain_files[d])} files")
        print("    codes:", ", ".join(f"{c}={n}" for c, n in counter.most_common(18)))
    print()
    focus = sys.argv[1] if len(sys.argv) > 1 else None
    if focus:
        print(f"--- files for {focus} ---")
        for f, n in per_domain_files[focus].most_common(200):
            print(f"{n:5d}  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
