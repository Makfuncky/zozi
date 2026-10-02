"""Validate the compiler verdict files and roll up performance.

Read-only. Reports, per agent: JSON validity, verdict counts against the
dispatched expected count, duplicates, contradictions, cross-cutting
candidates, and coverage gaps. Fails loudly on drift or silent omission.
"""

from __future__ import annotations

import collections
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMP = os.path.join(ROOT, "_audit", "compiler")
VERD = os.path.join(COMP, "verdicts")
LOG = os.path.join(COMP, "logs", "agent_performance.jsonl")

HARD_VIOLATIONS = {"FORBIDDEN_VERB", "D-SCOPE", "D-EVIDENCE", "D-REMOVAL"}


def dispatched() -> dict[str, int]:
    out: dict[str, int] = {}
    if not os.path.exists(LOG):
        return out
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event") == "dispatch":
                out[r["agent_id"]] = r.get("expected", 0)
    return out


def main() -> int:
    exp = dispatched()
    files = sorted(glob.glob(os.path.join(VERD, "*.json")))
    if not files:
        print("NO VERDICT FILES YET")
        return 1

    totals = collections.Counter()
    problems: list[str] = []
    print(f"{'agent':<34} {'exp':>5} {'got':>5} {'REAL':>5} {'FP':>4} "
          f"{'FIXD':>5} {'CONTR':>5} {'dup':>4} {'xc':>4} {'gap':>4}  flags")
    print("-" * 100)

    for f in files:
        name = os.path.basename(f)[:-5]
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"{name:<34} INVALID JSON: {exc}")
            problems.append(f"{name}: invalid JSON")
            continue

        v = d.get("verdicts", [])
        c = collections.Counter(x.get("verdict") for x in v)
        totals.update(c)
        agent = d.get("agent_id") or name
        e = exp.get(agent, 0)
        flags = []

        if e and len(v) != e:
            flags.append(f"COUNT_MISMATCH(exp={e})")
            problems.append(f"{agent}: {len(v)} verdicts vs {e} expected")
        keys = [x.get("key") for x in v]
        if len(keys) != len(set(keys)):
            dupn = len(keys) - len(set(keys))
            flags.append(f"DUP_KEYS({dupn})")
            problems.append(f"{agent}: {dupn} duplicate verdict keys")
        for x in v:
            if x.get("verdict") == "FALSE_POSITIVE" and not (x.get("counter_evidence") or "").strip():
                flags.append("FP_WITHOUT_EVIDENCE")
                problems.append(f"{agent}/{x.get('key')}: FALSE_POSITIVE without counter-evidence")
                break
            if x.get("verdict") == "ALREADY_FIXED" and not (x.get("verify_output") or "").strip():
                flags.append("FIXED_WITHOUT_OUTPUT")
                problems.append(f"{agent}/{x.get('key')}: ALREADY_FIXED without verify_output")
                break
        if d.get("hard_violations"):
            hard = set(d["hard_violations"]) & HARD_VIOLATIONS
            if hard:
                flags.append("HARD:" + ",".join(sorted(hard)))
                problems.append(f"{agent}: hard violation {hard}")

        print(f"{agent:<34} {e:>5} {len(v):>5} {c.get('REAL',0):>5} "
              f"{c.get('FALSE_POSITIVE',0):>4} {c.get('ALREADY_FIXED',0):>5} "
              f"{c.get('BLOCKED_BY_CONTRADICTION',0):>5} "
              f"{len(d.get('duplicates_merged',[])):>4} "
              f"{len(d.get('cross_cutting_candidates',[])):>4} "
              f"{len(d.get('coverage_gaps',[])):>4}  {' '.join(flags)}")

    print("-" * 100)
    print(f"verdict files : {len(files)}")
    print(f"verdicts      : {sum(totals.values())} {dict(totals)}")
    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for p in problems[:40]:
            print(f"  - {p}")
        return 2
    print("\nno integrity problems detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
