"""Read-only analyzer for SYSTEM_AUDIT_REPORT.md - groups findings by file/module."""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPORT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

ROW = re.compile(r"^\|\s*(\U0001F534|\U0001F7E1|\U0001F7E2)\s*\|\s*([A-Za-z0-9]+)\s*\|\s*([^|]*?)\s*\|\s*`([^`]+)`\s*\|(.*)$")
SEVMAP = {"\U0001F534": "RED", "\U0001F7E1": "YEL", "\U0001F7E2": "INF"}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    text = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    per_file = collections.Counter()
    per_file_y = collections.Counter()
    per_rule = collections.Counter()
    rows = []
    seen = set()
    for line in text:
        m = ROW.match(line)
        if not m:
            continue
        sev, rule, domain, loc, rest = m.groups()
        f = loc.split(":")[0]
        key = (sev, rule, loc, rest.strip())
        if key in seen:
            continue
        seen.add(key)
        rows.append((sev, rule, domain, f, loc, rest))
        if sev == "\U0001F534":
            per_file[f] += 1
            per_rule[rule] += 1
        elif sev == "\U0001F7E1":
            per_file_y[f] += 1

    arg = sys.argv[1] if len(sys.argv) > 1 else "top"

    if arg == "top":
        print("=== TOP FILES BY RED (deduped) ===")
        for f, c in per_file.most_common(80):
            print(f"{c:4d} RED  {per_file_y.get(f, 0):4d} YEL  {f}")
        print()
        print("=== RED RULE COUNTS ===")
        for r, c in per_rule.most_common():
            print(f"{c:5d}  {r}")
    elif arg == "prefix":
        pref = sys.argv[2]
        groups = collections.Counter()
        groups_y = collections.Counter()
        for sev, rule, domain, f, loc, rest in rows:
            if pref.lower() in f.lower():
                if sev == "\U0001F534":
                    groups[f] += 1
                elif sev == "\U0001F7E1":
                    groups_y[f] += 1
        keys = set(groups) | set(groups_y)
        for f in sorted(keys, key=lambda k: (-groups[k], -groups_y[k])):
            print(f"{groups[f]:4d} RED  {groups_y[f]:4d} YEL  {f}")
        print(f"TOTAL: {sum(groups.values())} RED, {sum(groups_y.values())} YEL")
    elif arg == "file":
        needles = [n.lower() for n in sys.argv[2:]]
        for sev, rule, domain, f, loc, rest in rows:
            if any(n in f.lower() for n in needles):
                print(f"{SEVMAP.get(sev, sev)} {rule:8s} {loc}  {rest.strip()}")
    elif arg == "rule":
        needle = sys.argv[2]
        for sev, rule, domain, f, loc, rest in rows:
            if rule == needle:
                print(f"{SEVMAP.get(sev, sev)} {rule:8s} {loc}  {rest.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
