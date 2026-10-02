"""Patches from the completeness gate run:

1. SECTION 2's `Feature Relation` block emitted `- **Findings:**` where a
   `Confirmation` marker was required, so the marker count came up one short.
2. The executive summary counted the cross-cutting pseudo-block under `defer`,
   but per-file blocks exclude it, so the summary could never reconcile.
3. The gate's own finding-ID regex rejected digit-leading IDs such as
   `07_tables_fields-P0`, producing a false WARN.
"""

import io

ASM = "_audit/compiler/assemble_worklist.py"
GATE = "_audit/compiler/completeness_gate.py"


def patch_asm() -> bool:
    t = io.open(ASM, encoding="utf-8").read()

    old_fr = (
        '        L.append(f"- **Findings:** {len(fr)}" if fr '
        'else "- **Confirmation:** \\u2714\\ufe0f")'
    )
    new_fr = (
        '        L.append("- **Confirmation:** " + ("\\u274c" if fr else "\\u2714\\ufe0f"))\n'
        '        if fr:\n'
        '            L.append(f"- **Findings:** {len(fr)}")'
    )
    if old_fr in t:
        t = t.replace(old_fr, new_fr, 1)
    else:
        # the source may hold the literal glyph rather than the escape
        old_fr2 = (
            '        L.append(f"- **Findings:** {len(fr)}" if fr '
            'else "- **Confirmation:** \u2714\ufe0f")'
        )
        if old_fr2 not in t:
            print("ASM: feature-relation anchor not found")
            return False
        t = t.replace(old_fr2, new_fr, 1)

    old_sum = """    for ph in PHASE_ORDER:
        fs = [g for p, _, g in ordered if p == ph]
        if fs:
            L.append(f"| {ph} | {len(fs)} | {sum(len(x) for x in fs)} |")"""
    new_sum = """    for ph in PHASE_ORDER:
        # the cross-cutting pseudo-block is SECTION 2, not a per-file block,
        # so it is reported on its own row rather than inside a phase
        fs = [g for p, path, g in ordered
              if p == ph and not path.startswith("(cross-cutting")]
        if fs:
            L.append(f"| {ph} | {len(fs)} | {sum(len(x) for x in fs)} |")
    if over_all:
        L.append(f"| _section 2 (cross-cutting) | 1 | {len(over_all)} |")"""
    if old_sum not in t:
        print("ASM: executive-summary anchor not found")
        return False
    t = t.replace(old_sum, new_sum, 1)

    io.open(ASM, "w", encoding="utf-8").write(t)
    print("assembler patched: confirmation marker + executive summary")
    return True


def patch_gate() -> bool:
    t = io.open(GATE, encoding="utf-8").read()
    old = r'r"`[A-Za-z][A-Za-z0-9_]*-[A-Za-z0-9._-]+`"'
    new = r'r"`[A-Za-z0-9][A-Za-z0-9_]*-[A-Za-z0-9._-]+`"'
    if old not in t:
        print("GATE: id-regex anchor not found")
        return False
    t = t.replace(old, new, 1)
    old_need = 'n_needed = len(blocks) * 10 + 11  # 10 generic subsections per block + section 2'
    new_need = ('n_needed = len(blocks) * 10 + 11  # 10 generic subsections per block '
                '+ section 2 (Feature Relation included)')
    if old_need in t:
        t = t.replace(old_need, new_need, 1)
    io.open(GATE, "w", encoding="utf-8").write(t)
    print("gate patched: id regex accepts digit-leading IDs")
    return True


def main() -> int:
    ok = patch_asm() and patch_gate()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())