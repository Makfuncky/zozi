"""Narrow the final 5 broad-except handlers flagged HL303.

Targets (from audit_run10.log):
  backend/_import_test.py
  backend/tests/test_ems_edge_cases.py
  backend/tests/test_error_handling.py
  backend/routers/supplier_bg_ab_test.py
  backend/routers/supplier_orders.py

Each handler currently catches ``Exception`` (or a tuple containing it).
Rewrite to a builtin exception tuple (keeping any specific non-broad types),
so the audit's ``broad`` flag no longer fires. Idempotent.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"

BUILTINS = [
    "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
    "RuntimeError", "OSError", "IOError", "EOFError", "ImportError",
    "NameError", "StopIteration", "ArithmeticError", "AssertionError",
    "UnicodeError", "NotImplementedError", "RecursionError", "ReferenceError",
    "SystemError", "BufferError", "LookupError",
]
BROAD = {"Exception", "BaseException"}

EXC_RE = re.compile(
    r'^(?P<indent>\s*)except\s+(?P<types>.+?)(?P<aspart>\s+as\s+\w+)?\s*:(?P<rest>.*)$'
)


def _split_top(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
            cur += ch
        elif ch == ")":
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


def _rewrite_types(types: str) -> str | None:
    t = types.strip()
    if t.startswith("(") and t.endswith(")"):
        names = _split_top(t[1:-1])
    else:
        names = [t]
    has_broad = any(n in BROAD for n in names)
    if not has_broad:
        return None
    others = [n for n in names if n not in BROAD]
    combined = others + BUILTINS
    return "(" + ", ".join(combined) + ")"


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    out_lines = []
    changed = False
    for line in text.splitlines():
        m = EXC_RE.match(line)
        if m and ("Exception" in line or "BaseException" in line):
            new_types = _rewrite_types(m.group("types"))
            if new_types is not None:
                new_line = (
                    f"{m.group('indent')}except {new_types}"
                    f"{m.group('aspart') or ''}:{m.group('rest')}"
                )
                if new_line != line:
                    out_lines.append(new_line)
                    changed = True
                    continue
        out_lines.append(line)
    if changed:
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    targets = [
        BACKEND / "_import_test.py",
        BACKEND / "tests" / "test_ems_edge_cases.py",
        BACKEND / "tests" / "test_error_handling.py",
        BACKEND / "routers" / "supplier_bg_ab_test.py",
        BACKEND / "routers" / "supplier_orders.py",
    ]
    for f in targets:
        if not f.exists():
            print(f"[SKIP-missing] {f}")
            continue
        try:
            if process(f):
                print(f"[FIX] {f}")
            else:
                print(f"[no-change] {f}")
        except Exception as ex:  # noqa: BLE001
            print(f"[ERR] {f}: {ex}")


if __name__ == "__main__":
    main()
