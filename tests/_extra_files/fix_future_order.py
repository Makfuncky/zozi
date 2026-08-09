"""Move ``from __future__ import ...`` to the top of each module (after the
docstring) so injected ``import structlog`` lines don't break ordering.

Idempotent and safe: future imports are only ever valid at the very top, so
relocating them upward never changes semantics.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
FUTURE_RE = re.compile(r"^\s*from\s+__future__\s+import\s+.+$")


def _classify(lines: list[str]):
    """Return (docstring_end_index, first_blocker_index).

    first_blocker = first top-level line that is not blank, not a comment,
    not part of the module docstring, and not a future import.
    """
    in_doc = False
    doc_done = False
    doc_end = 0
    blocker = None
    for i, line in enumerate(lines):
        s = line.strip()
        if not doc_done:
            if not s:
                continue
            if s.startswith('"""') or s.startswith("'''"):
                if s.count('"""') == 2 or s.count("'''") == 2:
                    doc_done = True
                    doc_end = i
                else:
                    in_doc = True
                    doc_done = False
                    doc_end = i
                continue
            doc_done = True
        if in_doc:
            if '"""' in s or "'''" in s:
                in_doc = False
                doc_done = True
                doc_end = i
            continue
        if FUTURE_RE.match(line):
            continue
        if not s or s.startswith("#"):
            continue
        blocker = i
        break
    return doc_end, blocker


def process(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    future_idxs = [i for i, l in enumerate(lines) if FUTURE_RE.match(l)]
    if not future_idxs:
        return False
    _, blocker = _classify(lines)
    if blocker is None:
        return False
    if all(idx < blocker for idx in future_idxs):
        return False  # already correctly ordered
    doc_end, _ = _classify(lines)
    future_lines = [lines[i] for i in future_idxs]
    kept = [l for i, l in enumerate(lines) if i not in set(future_idxs)]
    out = kept[: doc_end + 1] + future_lines + kept[doc_end + 1 :]
    path.write_text("\n".join(out), encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for f in BACKEND.rglob("*.py"):
        if "venv" in f.parts:
            continue
        try:
            if process(f):
                changed += 1
                print(f"[FIX-order] {f}")
        except Exception as ex:  # noqa: BLE001
            print(f"[ERR] {f}: {ex}", flush=True)
    print(f"\nDone: {changed} files reordered.")


if __name__ == "__main__":
    main()
