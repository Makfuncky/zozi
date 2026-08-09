"""Parse SYSTEM_AUDIT_REPORT.md section 9 and group findings by backend module/domain."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "SYSTEM_AUDIT_REPORT.md"

LINE_RE = re.compile(r"^- (?P<sev>[\U0001F534\U0001F7E1\U0001F7E2]) \*\*(?P<code>[A-Z0-9]+)\*\* `(?P<loc>[^`]+)`")

SEV_MAP = {"\U0001F534": "RED", "\U0001F7E1": "YELLOW", "\U0001F7E2": "INFO"}

DOMAIN_TOKENS = [
    "treasury", "finance", "orders", "catalog", "media", "supplier", "logistics",
    "comms", "communication", "security", "hr", "analytics", "ai", "country",
    "geography", "commerce", "core", "customer", "audit", "configuration",
]


def domain_of(loc: str) -> str:
    p = loc.replace("\\", "/").lower()
    parts = p.split("/")
    # explicit domain folder
    for i, seg in enumerate(parts):
        if seg in {"services", "models", "controllers", "providers", "events", "jobs"} and i + 1 < len(parts):
            nxt = parts[i + 1]
            if nxt in DOMAIN_TOKENS:
                return nxt
    stem = parts[-1]
    for tok in DOMAIN_TOKENS:
        if tok in stem:
            return tok
    return "?"


def main() -> None:
    text = REPORT.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, l in enumerate(text) if l.startswith("## 9."))
    end = next(i for i, l in enumerate(text) if l.startswith("## 10."))

    by_domain: dict[str, Counter] = defaultdict(Counter)
    by_domain_sev: dict[str, Counter] = defaultdict(Counter)
    by_file: Counter = Counter()
    by_file_red: Counter = Counter()
    rows: list[tuple[str, str, str, str]] = []

    for line in text[start:end]:
        m = LINE_RE.match(line)
        if not m:
            continue
        sev = SEV_MAP.get(m.group("sev"), "?")
        code = m.group("code")
        loc = m.group("loc")
        f = loc.split(":")[0]
        d = domain_of(f)
        by_domain[d][code] += 1
        by_domain_sev[d][sev] += 1
        by_file[f] += 1
        if sev == "RED":
            by_file_red[f] += 1
        rows.append((sev, code, loc, d))

    print(f"TOTAL parsed findings: {len(rows)}")
    print("\n=== BY DOMAIN (sev breakdown) ===")
    order = sorted(by_domain_sev.items(), key=lambda kv: -(kv[1]["RED"] * 100 + kv[1]["YELLOW"]))
    for d, c in order:
        print(f"{d:16s} RED={c['RED']:4d} YEL={c['YELLOW']:5d} INFO={c['INFO']:4d} total={sum(c.values()):5d}")

    print("\n=== TOP 40 FILES BY FINDING COUNT ===")
    for f, n in by_file.most_common(40):
        print(f"{n:5d} (red={by_file_red.get(f,0):3d})  {f}")

    print("\n=== PER-DOMAIN CODE HISTOGRAM (top domains) ===")
    for d, _ in order[:8]:
        print(f"\n-- {d} --")
        for code, n in by_domain[d].most_common(30):
            print(f"   {code:8s} {n}")


if __name__ == "__main__":
    main()
