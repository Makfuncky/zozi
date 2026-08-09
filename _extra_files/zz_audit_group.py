"""Temp helper: parse SYSTEM_AUDIT_REPORT.md section 9 findings and group by backend domain."""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPORT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

FINDING_RE = re.compile(r"^- (?P<sev>[^ ]+) \*\*(?P<code>[A-Z0-9]+)\*\* `(?P<loc>[^`]*)` — (?P<msg>.*)$")
DOMAIN_RE = re.compile(
    r"backend[\\/](?:models|services|controllers|providers|events|jobs)[\\/]([a-z_0-9]+)[\\/]"
)


def load():
    lines = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## 9."))
    end = next(i for i, l in enumerate(lines) if l.startswith("## 10."))
    section = None
    out = []
    for line in lines[start:end]:
        if line.startswith("### "):
            section = line[4:].split(" (")[0]
            continue
        m = FINDING_RE.match(line.strip())
        if m:
            out.append(
                {
                    "section": section,
                    "sev": m.group("sev"),
                    "code": m.group("code"),
                    "loc": m.group("loc"),
                    "msg": m.group("msg"),
                }
            )
    return out


def main() -> None:
    findings = load()
    print(f"total findings parsed: {len(findings)}")

    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if mode == "summary":
        by_domain = defaultdict(list)
        for f in findings:
            blob = (f["loc"] + " " + f["msg"]).replace("/", "\\")
            doms = set(DOMAIN_RE.findall(blob))
            if not doms:
                by_domain["<none>"].append(f)
            for d in doms:
                by_domain[d].append(f)
        for d, fs in sorted(by_domain.items(), key=lambda kv: -len(kv[1])):
            reds = sum(1 for f in fs if "\U0001f534" in f["sev"])
            print(f"{d:20s} total={len(fs):5d} red={reds:4d}")
        return

    # mode == substring match on loc
    needle = mode.lower()
    fs = [f for f in findings if needle in (f["loc"] + " " + f["msg"]).lower()]
    print(f"=== matches for '{needle}': {len(fs)} ===")
    c = Counter(f["code"] for f in fs)
    for code, n in c.most_common():
        print(f"  {code}: {n}")
    if len(sys.argv) > 2 and sys.argv[2] == "full":
        print()
        seen = set()
        for f in sorted(fs, key=lambda x: (x["code"], x["loc"])):
            key = (f["code"], f["loc"], f["msg"])
            if key in seen:
                continue
            seen.add(key)
            print(f"{f['sev']} [{f['code']}] ({f['section']}) {f['loc']}\n      {f['msg']}")


if __name__ == "__main__":
    main()
