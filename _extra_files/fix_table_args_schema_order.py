"""One-off repair: move {'schema': ...} dict to the END of __table_args__ tuples.

The prior domain-schema migration placed the schema dict FIRST in tuples that
also contain Index/Constraint items, e.g. `({'schema': 'security'}, Index(...))`.
SQLAlchemy rejects a schema dict that is not the final positional item, so every
model import fails. This script reorders each affected tuple so the schema dict
is last, which SQLAlchemy accepts: `(Index(...), {'schema': 'security'})`.

Run from backend/. Idempotent: only rewrites files where the dict is not last.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_ROOTS = [Path("models"), Path("data")]

TABLE_ARGS_RE = re.compile(r"(__table_args__\s*=\s*\()", re.DOTALL)


def balanced_span(text: str, start: int) -> int:
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        elif ch in "'\"":
            quote = ch
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    break
                i += 1
        i += 1
    return -1


def split_top_level(items_text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    cur = ""
    for ch in items_text:
        if ch in "([{":
            depth += 1
            cur += ch
        elif ch in ")]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


SCHEMA_DICT_RE = re.compile(r"^\{\s*'schema'\s*:\s*'[^']+'\s*\}$")


def fix_inner(inner: str) -> str | None:
    items = split_top_level(inner)
    if not items:
        return None
    schema_items = [it for it in items if SCHEMA_DICT_RE.match(it)]
    if len(schema_items) != 1:
        return None
    schema_dict = schema_items[0]
    if items[-1] == schema_dict:
        return None
    others = [it for it in items if it != schema_dict]
    if not others:
        return None
    return ",\n    ".join(others + [schema_dict])


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    spans: list[tuple[int, int, str]] = []
    for m in TABLE_ARGS_RE.finditer(text):
        open_idx = m.end() - 1
        close_idx = balanced_span(text, open_idx)
        if close_idx == -1:
            continue
        inner = text[open_idx + 1 : close_idx]
        fixed = fix_inner(inner)
        if fixed is not None:
            spans.append((open_idx, close_idx, fixed))
    if not spans:
        return False
    # Apply in reverse so original indices stay valid.
    new_text = text
    for open_idx, close_idx, fixed in reversed(spans):
        new_text = new_text[: open_idx + 1] + fixed + new_text[close_idx:]
    compile(new_text, str(path), "exec")
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for root in MODEL_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if p.name == "__init__.py":
                continue
            try:
                if fix_file(p):
                    changed += 1
                    print(f"fixed: {p}")
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR in {p}: {exc}", file=sys.stderr)
                return 2
    print(f"changed {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
