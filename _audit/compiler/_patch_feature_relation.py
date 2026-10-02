"""One-shot patch: emit the `Feature Relation` subsection exactly once per
block. It is the 11th subsection but carries relation fields, not
Confirmation/Problem/Solution, so it must not go through the generic loop.
"""

import io

P = "_audit/compiler/assemble_worklist.py"

PER_FILE_OLD = """        for name, laws in SUBSECTIONS:
            rows = sub_map.get(name, [])
            L.append(f"### {name}")"""
PER_FILE_NEW = """        for name, laws in SUBSECTIONS:
            # Feature Relation is the 11th subsection but carries relation
            # fields, not Confirmation/Problem/Solution. Emitted once, below.
            if name == "Feature Relation":
                continue
            rows = sub_map.get(name, [])
            L.append(f"### {name}")"""

SEC2_OLD = """        for name, laws in SUBSECTIONS:
            rows = sub_map.get(name, [])
            L.append(f"## Codebase Implementation \u2014 {name}")"""
SEC2_NEW = """        for name, laws in SUBSECTIONS:
            if name == "Feature Relation":
                continue
            rows = sub_map.get(name, [])
            L.append(f"## Codebase Implementation \u2014 {name}")"""

SEC2_FR_OLD = """        L.append("### Resolution")
        L.append("")
        L.append("- **Verify (cross-cutting):**"""
SEC2_FR_NEW = """        fr = sub_map.get("Feature Relation", [])
        L.append("## Codebase Implementation \u2014 Feature Relation")
        L.append("")
        L.append("<!-- laws: feature IDs, chain IDs, upstream/downstream -->")
        L.append(f"- **Findings:** {len(fr)}" if fr else "- **Confirmation:** \u2714\ufe0f")
        for line in feature_relation(fr or over_all):
            L.append(line)
        L.append("")
        L.append("### Resolution")
        L.append("")
        L.append("- **Verify (cross-cutting):**"""


def main() -> int:
    t = io.open(P, encoding="utf-8").read()
    for old, new, label in (
        (PER_FILE_OLD, PER_FILE_NEW, "per-file loop"),
        (SEC2_OLD, SEC2_NEW, "section-2 loop"),
        (SEC2_FR_OLD, SEC2_FR_NEW, "section-2 feature relation"),
    ):
        if old not in t:
            print(f"ANCHOR_MISSING: {label}")
            return 1
        t = t.replace(old, new, 1)
    io.open(P, "w", encoding="utf-8").write(t)
    print("patched: Feature Relation now emitted once per block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())