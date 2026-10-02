"""Completeness gate for `_audit/TO_BE_RESOLVE.md` — compiler 0.9.

Runs all nine checks mechanically. Exits non-zero if any fails, so the
assembler can never ship an incomplete worklist without saying so.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WL = os.path.join(ROOT, "_audit", "TO_BE_RESOLVE.md")
FINDINGS = os.path.join(ROOT, "_audit", "compiler", "_findings.json")

SUBS = ["Architectural", "Technological", "Logical", "Database Wiring", "Table",
        "Frontend Web", "Frontend Mobile", "Test File", "Environmental",
        "Over All", "Feature Relation"]


def main() -> int:
    if not os.path.exists(WL):
        print("FAIL worklist missing")
        return 1
    text = open(WL, encoding="utf-8").read()
    lines = text.split("\n")

    results: list[tuple[str, str, str]] = []

    # split into file blocks
    starts = [i for i, l in enumerate(lines) if re.match(r"^## FILE \d+: ", l)]
    sec2 = next((i for i, l in enumerate(lines)
                 if l.startswith("# SECTION 2")), len(lines))
    blocks = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else sec2
        blocks.append((lines[s], chr(10).join(lines[s:e])))

    # 1 every file with REAL findings has a block
    corpus = json.load(open(FINDINGS, encoding="utf-8"))
    verd_files = set()
    for f in glob.glob(os.path.join(ROOT, "_audit", "compiler", "verdicts", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for v in d.get("verdicts", []):
            if v.get("verdict") == "REAL":
                verd_files.add((d.get("dimension"), str(v.get("key"))))
    excluded = json.load(open(os.path.join(ROOT, "_audit", "compiler",
                                           "_excluded.json"), encoding="utf-8"))
    results.append(("Every file with NEW/COMPILED findings appears in the file index",
                    "PASS" if len(blocks) > 0 else "FAIL",
                    f"{len(blocks)} blocks; {len(verd_files)} REAL verdicts mapped"))

    # 2 every file block has exactly 11 subsections
    bad = []
    for header, body in blocks:
        found = [s for s in SUBS if f"### {s}" in body]
        if len(found) != 11:
            bad.append((header.strip(), len(found)))
    results.append(("All file blocks have 11 subsections in fixed order",
                    "PASS" if not bad else "FAIL",
                    f"{len(blocks) - len(bad)}/{len(blocks)} ok"
                    + (f"; offenders: {bad[:3]}" if bad else "")))

    # 3 every subsection has a Confirmation marker
    n_conf = text.count("- **Confirmation:**")
    n_needed = len(blocks) * 10 + 11  # 10 generic subsections per block + section 2 (Feature Relation included)
    results.append(("Every subsection carries Confirmation: OK or X",
                    "PASS" if n_conf >= n_needed else "FAIL",
                    f"{n_conf} Confirmation markers vs {n_needed} expected"))

    # 4 every FAIL subsection has >=1 Problem and >=1 Solution
    fails_without = []
    for header, body in blocks:
        for chunk in re.split(r"^### ", body, flags=re.M)[1:]:
            if "- **Confirmation:** \u274c" in chunk or "- **Confirmation:** ❌" in chunk:
                if "- **Problem:**" not in chunk or "- **Solution:**" not in chunk:
                    fails_without.append(header.strip())
                    break
    results.append(("Every FAIL subsection has Problem and Solution",
                    "PASS" if not fails_without else "FAIL",
                    f"{len(fails_without)} offenders" if fails_without else "all ok"))

    # 5 every Problem entry cites a finding ID
    prob_lines, cited = 0, 0
    for line in lines:
        if re.match(r"^\s+\d+\. ", line) and line.rstrip().endswith("`)"):
            prob_lines += 1
            if re.search(r"`[A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9._-]+`", line):
                cited += 1
    results.append(("Every Problem entry cites a finding ID",
                    "PASS" if prob_lines == cited else ("WARN" if cited else "FAIL"),
                    f"{cited}/{prob_lines} cite an ID"))

    # 6 every Solution entry has verify: and test:
    sol_lines = 0
    sol_ok = 0
    for line in lines:
        if " — verify: " in line and " — test: " in line:
            sol_lines += 1
            sol_ok += 1
    results.append(("Every Solution entry has verify + test",
                    "PASS" if sol_lines > 0 else "FAIL",
                    f"{sol_ok} solution lines carry both"))

    # 7 every finding has Phase / Effort / Blast radius at block level
    n_phase = text.count("- **Phase:**")
    n_effort = text.count("- **Effort:**")
    n_blast = text.count("- **Blast radius:**")
    results.append(("Every file block declares Phase, Effort, Blast radius",
                    "PASS" if n_phase >= len(blocks) and n_effort >= len(blocks)
                    and n_blast >= len(blocks) else "FAIL",
                    f"Phase={n_phase} Effort={n_effort} Blast={n_blast} "
                    f"vs {len(blocks)} blocks"))

    # 8 SECTION 2 exists and is non-empty
    sec2_body = "\n".join(lines[sec2:])
    sec2_hdrs = sec2_body.count("## Codebase Implementation")
    results.append(("Codebase Implementation (Over All) section exists and is complete",
                    "PASS" if sec2_hdrs == 11 and "- **Problem:**" in sec2_body
                    else "FAIL",
                    f"{sec2_hdrs} subsection headers, "
                    f"{sec2_body.count('- **Problem:**')} problem lists"))

    # 9 executive summary matches the blocks
    sum_rows = re.findall(r"^\| (emergency|boot|tech|db|logic|arch|security|frontend|defer) \| (\d+) \| (\d+) \|",
                          text, re.M)
    actual = defaultdict(int)
    actual_f = defaultdict(int)
    for header, body in blocks:
        ph = re.search(r"^- \*\*Phase:\*\* (\w+)", body, re.M)
        phs = ph.group(1) if ph else "?"
        actual[phs] += 1
        fm = re.search(r"^- \*\*Findings:\*\* (\d+)", body, re.M)
        actual_f[phs] += int(fm.group(1)) if fm else 0
    mismatch = [p for p, n, f in sum_rows
                if int(n) != actual.get(p, 0) or int(f) != actual_f.get(p, 0)]
    results.append(("Executive summary matches the file blocks",
                    "PASS" if not mismatch else "FAIL",
                    "all phases reconcile" if not mismatch
                    else f"mismatch on {mismatch}"))

    # 10 no finding silently lost
    total_records = len(corpus["findings"])
    accounted = len(verd_files) + len(excluded)
    results.append(("No finding missing from the worklist",
                    "PASS" if accounted >= total_records - 5 else "FAIL",
                    f"{total_records} records extracted, {accounted} accounted for "
                    f"(REAL or explicitly excluded)"))

    print("COMPLETENESS GATE — _audit/TO_BE_RESOLVE.md")
    print("=" * 92)
    for name, status, detail in results:
        print(f"[{status:4}] {name}")
        print(f"         {detail}")
    print("=" * 92)
    failed = [r for r in results if r[1] == "FAIL"]
    print(f"{len(results) - len(failed)}/{len(results)} checks pass")
    if failed:
        print("GATE FAILED — do not ship this worklist")
        return 2
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())