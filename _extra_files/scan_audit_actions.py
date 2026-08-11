"""Read-only: enumerate every AuditAction.<ATTR> referenced in the backend."""
from __future__ import annotations

import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1] / "backend"
SKIP = {"venv", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
PAT = re.compile(r"AuditAction\.([A-Za-z_][A-Za-z0-9_]*)")

counter: collections.Counter[str] = collections.Counter()
where: dict[str, set[str]] = collections.defaultdict(set)

for p in ROOT.rglob("*.py"):
    if any(x in p.parts for x in SKIP):
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    for m in PAT.finditer(text):
        counter[m.group(1)] += 1
        where[m.group(1)].add(str(p.relative_to(ROOT)))

for k, v in sorted(counter.items()):
    print(f"{k}\t{v}")
print("TOTAL DISTINCT", len(counter))
