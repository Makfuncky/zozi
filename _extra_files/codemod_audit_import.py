"""One-shot codemod: repoint `controllers.audit_controller` imports at `utils.audit`.

Rule W3 — `audit_controller` is a mis-housed controller; every layer imported it
as shared logic. The canonical primitives now live in `utils.audit`.

Run:  python _extra_files/codemod_audit_import.py [--apply]
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1] / "backend"
SKIP = {"venv", "__pycache__", ".venv", "node_modules", ".pytest_cache", "alembic"}
APPLY = "--apply" in sys.argv

PATTERNS = [
    (re.compile(r"^(\s*)from controllers\.audit_controller import (.+)$", re.M), r"\1from utils.audit import \2"),
    (re.compile(r"^(\s*)from backend\.controllers\.audit_controller import (.+)$", re.M), r"\1from utils.audit import \2"),
    (re.compile(r"^(\s*)import controllers\.audit_controller as (\w+)$", re.M), r"\1import utils.audit as \2"),
]

changed = 0
for p in sorted(ROOT.rglob("*.py")):
    if any(x in p.parts for x in SKIP):
        continue
    if p.name == "audit_controller.py":
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    if "audit_controller" not in text:
        continue
    new = text
    for pat, repl in PATTERNS:
        new = pat.sub(repl, new)
    if new != text:
        changed += 1
        print(("APPLY " if APPLY else "WOULD ") + str(p.relative_to(ROOT)))
        if APPLY:
            p.write_text(new, encoding="utf-8")

print(f"\n{'changed' if APPLY else 'would change'}: {changed} file(s)")
