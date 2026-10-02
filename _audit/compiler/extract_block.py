"""Extract one or more file blocks from `_audit/TO_BE_RESOLVE.md` verbatim,
so a resolver agent can be handed exactly its dispatch unit.

Usage:
  python _audit/compiler/extract_block.py FILE 1 2 3
  python _audit/compiler/extract_block.py --phase emergency boot
"""

from __future__ import annotations

import io
import re
import sys

WL = "_audit/TO_BE_RESOLVE.md"


def load() -> tuple[str, list[tuple[int, str, str]]]:
    text = io.open(WL, encoding="utf-8").read()
    cut = text.find("# SECTION 2")
    if cut == -1:
        cut = len(text)
    head = text[:cut]
    spans: list[tuple[int, str, str]] = []
    starts = [(m.start(), m.group(1), m.group(2))
              for m in re.finditer(r"^## FILE (\d+): (.+?)$", head, re.M)]
    for i, (pos, no, path) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(head)
        block = head[pos:end]
        m = re.search(r"^- \*\*Phase:\*\* (\w+)", block, re.M)
        spans.append((int(no), path, m.group(1) if m else "?"))
    return text, spans


def main() -> int:
    args = sys.argv[1:]
    text, spans = load()
    cut = text.find("# SECTION 2")
    head = text[:cut]
    starts = [(m.start(), m.group(1))
              for m in re.finditer(r"^## FILE (\d+): ", head, re.M)]

    wanted: list[int] = []
    if args and args[0] == "--phase":
        phases = set(args[1:])
        wanted = [no for no, _p, ph in spans if ph in phases]
    else:
        wanted = [int(a) for a in args if a.isdigit()]

    for i, (pos, no) in enumerate(starts):
        if int(no) not in wanted:
            continue
        end = starts[i + 1][0] if i + 1 < len(starts) else cut
        print(head[pos:end].rstrip())
        print("\n" + "=" * 96 + "\n")
    if not wanted:
        print("no matching blocks", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())