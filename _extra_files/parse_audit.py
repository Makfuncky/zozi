"""Parse SYSTEM_AUDIT_REPORT.md section 9 findings into a structured table.

Usage:
  python parse_audit.py [--path-contains SUBSTR] [--group]

Read-only.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

REPORT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

# - 🔴 **CODE** `path:line` — message → *fix*
LINE_RE = re.compile(r"^- (?P<sev>[^\s]+) \*\*(?P<code>[A-Z0-9_]+)\*\* `(?P<loc>[^`]*)` — (?P<msg>.*)$")
SEC_RE = re.compile(r"^### (?P<name>.+?) \((?P<n>\d+) findings\)$")


def parse():
    rows = []
    section = ""
    in_sec9 = False
    for raw in REPORT.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("## 9."):
            in_sec9 = True
            continue
        if in_sec9 and raw.startswith("## ") and not raw.startswith("## 9."):
            break
        if not in_sec9:
            continue
        m = SEC_RE.match(raw)
        if m:
            section = m.group("name")
            continue
        m = LINE_RE.match(raw)
        if m:
            loc = m.group("loc")
            msg = m.group("msg")
            fix = ""
            if " → *" in msg:
                msg, fix = msg.split(" → *", 1)
                fix = fix.rstrip("*")
            rows.append(
                {
                    "section": section,
                    "sev": m.group("sev"),
                    "code": m.group("code"),
                    "loc": loc,
                    "file": loc.split(":")[0],
                    "msg": msg,
                    "fix": fix,
                }
            )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path-contains", action="append", default=[])
    ap.add_argument("--group", choices=["file", "code", "section"], default=None)
    ap.add_argument("--code", action="append", default=[])
    ap.add_argument("--sev", default=None, help="red|yellow|green")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = parse()
    if args.path_contains:
        rows = [r for r in rows if any(s.lower() in r["file"].lower() for s in args.path_contains)]
    if args.code:
        rows = [r for r in rows if r["code"] in args.code]
    if args.sev:
        want = {"red": "🔴", "yellow": "🟡", "green": "🟢"}[args.sev]
        rows = [r for r in rows if r["sev"] == want]

    print(f"TOTAL parsed findings after filter: {len(rows)}")
    if args.group:
        c = Counter(r[args.group] for r in rows)
        for k, v in c.most_common(args.limit or None):
            print(f"{v:6d}  {k}")
        return
    for r in rows[: args.limit or None]:
        print(f"{r['sev']} {r['code']:8s} {r['loc']:70s} {r['msg']}")


if __name__ == "__main__":
    main()
