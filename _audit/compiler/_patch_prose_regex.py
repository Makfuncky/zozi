"""One-shot patch: make the prose finding-ID regex greedy.

The non-greedy `[0-9A-Za-z\\-_.]+?` collapsed every `### FIND-09-001: ...`
heading to the key `FIND-09`, so 09_laws.md deduplicated 23 findings down to
one. Greedy `(?:[-_][0-9A-Za-z]+)+` keeps the full ID and stops at the
separating colon or dash.
"""

import io

P = "_audit/compiler/parse_dimensions.py"

OLD = (
    '    prose = re.compile(r"^#{2,4}\\s*(?:\\*\\*)?(?:Finding\\s+)?'
    '([A-Z][A-Z0-9]*[-_][0-9A-Za-z\\-_.]+?)(?:\\*\\*)?'
    '\\s*[:\\u2014-]\\s*(.*)$")'
)

NEW = (
    '    # The ID part is greedy so `FIND-09-001:` does not collapse to `FIND-09`.\n'
    '    prose = re.compile(\n'
    '        r"^#{2,4}\\s*(?:\\*\\*)?(?:Finding\\s+)?"\n'
    '        r"([A-Za-z][A-Za-z0-9]*(?:[-_][0-9A-Za-z]+)+)"\n'
    '        r"(?:\\*\\*)?\\s*[:\\u2014\\u2013-]\\s*(.*)$"\n'
    '    )'
)


def main() -> int:
    text = io.open(P, encoding="utf-8").read()
    if OLD not in text:
        print("ANCHOR_MISSING - no change made")
        return 1
    io.open(P, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    print("patched prose regex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
