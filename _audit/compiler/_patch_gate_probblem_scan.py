"""Tighten the completeness gate's Problem-entry check.

The previous heuristic counted any line matching `^\\s+\\d+\\. ` that ended in
`)`. A Solution entry whose flag tail ended in `)` was miscounted as a Problem
entry, producing a false WARN. Restrict the scan to lines that actually sit
between a `- **Problem:**` marker and the next `- **Solution:**` marker.
"""

import io

P = "_audit/compiler/completeness_gate.py"

OLD = """    prob_lines, cited = 0, 0
    for line in lines:
        if re.match(r"^\\s+\\d+\\. ", line) and line.rstrip().endswith(")"):
            prob_lines += 1
            if re.search(r"`[A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9._-]+`", line):
                cited += 1"""

NEW = """    prob_lines, cited = 0, 0
    in_problem = False
    for line in lines:
        if line.strip() == "- **Problem:**":
            in_problem = True
            continue
        if line.strip() == "- **Solution:**":
            in_problem = False
            continue
        if in_problem and re.match(r"^\\s+\\d+\\. ", line):
            prob_lines += 1
            if re.search(r"`[A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9._-]+`", line):
                cited += 1"""


def main() -> int:
    t = io.open(P, encoding="utf-8").read()
    if OLD not in t:
        print("ANCHOR_MISSING")
        return 1
    io.open(P, "w", encoding="utf-8").write(t.replace(OLD, NEW, 1))
    print("gate patched: Problem-entry scan is now section-scoped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())