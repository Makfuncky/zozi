"""Classify SYM1 (dead-symbol) audit findings (efficient).

The architecture audit already proved each SYM1 symbol has NO usage outside its
own module within app layers. So a symbol is only "not truly dead" if it is:
  (a) used *internally* within its own defining file, or
  (b) used in tests/ or scripts/ (outside the audit's app_layers set).

We therefore only index: each symbol's own defining file + all tests/ + scripts/.
  - name appears only at its definition line -> DEAD (safe to delete)
  - otherwise                              -> FALSE_POSITIVE (keep)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
REPORT = REPO / "ARCHITECTURE_AUDIT_REPORT.md"
OUT = REPO / "_extra_files" / "sym1_classification.json"

LINE_RE = re.compile(
    r"SYM1\s*\|\s*(\w+)\s*\|\s*`([^`]+):(\d+)`\s*\|\s*symbol '([^']+)' \((\w+)\)"
)


def collect_symbols() -> list[dict]:
    syms: list[dict] = []
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    for m in LINE_RE.finditer(text):
        layer, loc, line, name, kind = m.groups()
        syms.append(
            {
                "name": name,
                "kind": kind,
                "layer": layer,
                "file": loc.replace("\\", "/"),
                "line": int(line),
                "abspath": str(REPORT.parent / loc.replace("\\", "/")),
            }
        )
    return syms


def build_index(syms: list[dict]) -> list[tuple[str, str]]:
    paths = {s["abspath"] for s in syms}
    for root in ("tests", "scripts"):
        base = REPORT.parent / root
        if base.exists():
            for p in base.rglob("*.py"):
                paths.add(str(p))
    idx: list[tuple[str, str]] = []
    for path in paths:
        try:
            txt = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        idx.append((path, txt))
    return idx


def main() -> None:
    syms = collect_symbols()
    print(f"Parsed {len(syms)} SYM1 entries; indexing own files + tests + scripts...")
    files = build_index(syms)
    print(f"Indexed {len(files)} files.")
    results = []
    for s in syms:
        pat = re.compile(r"\b" + re.escape(s["name"]) + r"\b")
        total = 0
        in_def = 0
        for path, txt in files:
            c = len(pat.findall(txt))
            if c:
                total += c
                if path == s["abspath"]:
                    in_def += c
        truly_dead = total == 1 and in_def == 1
        results.append(
            {
                "name": s["name"],
                "kind": s["kind"],
                "layer": s["layer"],
                "file": s["file"],
                "line": s["line"],
                "repo_total": total,
                "in_def_file": in_def,
                "external_occurrences": total - in_def,
                "verdict": "DEAD" if truly_dead else "FALSE_POSITIVE",
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    dead = [r for r in results if r["verdict"] == "DEAD"]
    fp = [r for r in results if r["verdict"] == "FALSE_POSITIVE"]
    print(f"SYM1 entries parsed : {len(results)}")
    print(f"  TRULY DEAD        : {len(dead)}")
    print(f"  FALSE POSITIVE    : {len(fp)}")
    print("DEAD symbols:")
    for r in dead:
        print(f"  - {r['name']} ({r['kind']}) in {r['file']}:{r['line']}")
    print(f"Classification written to {OUT}")


if __name__ == "__main__":
    main()
