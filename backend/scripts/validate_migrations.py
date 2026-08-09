"""Alembic migration validator — checks revision chain integrity."""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

REVISION_RE = re.compile(r'^revision.*=\s*["\']([a-f0-9_]+)["\']', re.MULTILINE)
DOWN_REVISION_RE = re.compile(r'^down_revision.*=\s*["\']?([a-f0-9_]+|None)["\']?', re.MULTILINE)


def _parse_revision(content: str):
    rev = REVISION_RE.search(content)
    down = DOWN_REVISION_RE.search(content)
    rev_id = rev.group(1) or rev.group(2) if rev else None
    down_id = down.group(1) or down.group(2) if down else None
    if down_id == "None":
        down_id = None
    return rev_id, down_id


def validate():
    if not MIGRATIONS_DIR.exists():
        print(f"Migrations directory not found: {MIGRATIONS_DIR}")
        return False

    files = sorted(MIGRATIONS_DIR.glob("*.py"))
    if not files:
        print("No migration files found.")
        return False

    revisions: dict[str, tuple[str, str | None, str]] = {}
    errors = []

    for f in files:
        content = f.read_text("utf-8")
        rev, down = _parse_revision(content)
        if not rev:
            errors.append(f"{f.name}: missing revision id")
            continue
        if rev in revisions:
            errors.append(f"{f.name}: duplicate revision id {rev} (also in {revisions[rev][2]})")
        revisions[rev] = (f.name, down, str(f))

    for rev, (name, down, _) in revisions.items():
        if down is None or down == "None":
            print(f"  [root] {name} (rev={rev})")
        elif down in revisions:
            print(f"  [{down[:8]}..] {name} (rev={rev})")
        else:
            errors.append(f"{name}: down_revision {down} not found")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return False

    print(f"\nAll {len(files)} migrations valid.")
    print(f"Chain: {' -> '.join(r[0].split('_', 1)[-1].replace('.py', '') for r in revisions.values())}")
    return True


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
