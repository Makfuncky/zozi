"""Encoding-robust rewrite of ALL service references (flat AND cross-domain)
to their canonical taxonomy folder. Idempotent.

For every moved module stem S with final folder F (or scripts/maintenance for
scratch), replace `services.(<domain>.)?S` -> `services.F.S` (or
`scripts.maintenance.S` for scratch) everywhere in backend/*.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
PLAN = REPO / "scripts" / "system_trackers" / "_services_plan.json"


def read_robust(p: Path) -> str:
    b = p.read_bytes()
    try:
        return b.decode("utf-8-sig")
    except UnicodeDecodeError:
        return b.decode("utf-16")


plan = json.loads(PLAN.read_text(encoding="utf-8"))
rules = []  # (compiled_pattern, replacement)
for e in plan:
    stem = e["file"][:-3]
    if e["folder"] == "SCRATCH":
        repl = f"scripts.maintenance.{stem}"
    else:
        repl = f"services.{e['final_folder']}.{stem}"
    pat = re.compile(r"services\.(?:[A-Za-z_]\w*\.)?" + re.escape(stem) + r"(?!\w)")
    rules.append((pat, repl))

total_files = 0
total_subs = 0
changed_files = 0
for p in BACKEND.rglob("*.py"):
    if "__pycache__" in p.parts or "venv" in p.parts:
        continue
    total_files += 1
    try:
        text = read_robust(p)
    except Exception:
        continue
    new = text
    n = 0
    for pat, repl in rules:
        new, c = pat.subn(repl, new)
        n += c
    if new != text:
        p.write_text(new, encoding="utf-8")
        changed_files += 1
        total_subs += n
print(f"files scanned: {total_files}, files changed: {changed_files}, refs rewritten: {total_subs}")
