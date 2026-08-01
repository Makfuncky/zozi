"""Idempotency patcher for ALL migration files.

Wraps stateful DDL (``op.create_table``, ``op.add_column``, ``op.create_index``,
``op.create_foreign_key``, ``op.drop_*`` …) in the ``safe_*`` helpers from
``utils.migration_helpers`` so the chain is reproducible from a clean database.

Uses a word-boundary regex (``\bop\.``) so ``batch_op.add_column`` and similar
inside ``batch_alter_table`` blocks are NOT touched. Idempotent: safe to re-run.
"""
import re
from pathlib import Path

ROOT = Path("backend/alembic/versions")

OPS = [
    "create_table",
    "drop_table",
    "add_column",
    "drop_column",
    "create_index",
    "drop_index",
    "create_foreign_key",
    "drop_constraint",
]

PATTERN = re.compile(r"\bop\.(" + "|".join(OPS) + r")\(", re.MULTILINE)
SAFE_NAMES = {op_name: f"safe_{op_name}" for op_name in OPS}


def _used_names(src: str) -> list[str]:
    present = set()
    for op_name, safe in SAFE_NAMES.items():
        if f"{safe}(op," in src or f"{safe}(op," in "\n".join(src.splitlines()):
            present.add(safe)
    return sorted(present)


def _ensure_import(lines: list[str], names: list[str]):
    if not names:
        return lines
    joined = ", ".join(names)
    target = "from utils.migration_helpers import " + joined
    for i, line in enumerate(lines):
        if line.startswith("from utils.migration_helpers import"):
            existing = [n.strip() for n in line.split("import", 1)[1].split(",")]
            merged = existing + [n for n in names if n not in existing]
            lines[i] = "from utils.migration_helpers import " + ", ".join(merged) + "\n"
            return lines
    insert_at = 0
    for i, line in enumerate(lines):
        if re.match(r"^(import |from )", line):
            insert_at = i + 1
    lines.insert(insert_at, target + "\n")
    return lines


def patch_file(path: Path):
    src = path.read_text(encoding="utf-8", errors="replace")
    new = PATTERN.sub(lambda m: f"safe_{m.group(1)}(op, ", src)
    if new == src:
        return False, []
    lines = new.splitlines(keepends=True)
    names = _used_names(new)
    lines = _ensure_import(lines, names)
    path.write_text("".join(lines), encoding="utf-8")
    return True, names


if __name__ == "__main__":
    for p in sorted(ROOT.glob("*.py")):
        if p.name.startswith("_"):
            continue
        changed, names = patch_file(p)
        print(f"{'PATCHED' if changed else 'no-op':7} {p.name} +{','.join(names)}")
