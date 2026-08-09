"""Dry-run analysis for RN1: extract flagged router filenames and propose renames.

Does NOT rename anything. Prints the proposed {surface}_{domain}_{operation}
mapping so it can be reviewed before any file moves.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
REP = REPO / "SYSTEM_AUDIT_REPORT.md"
ROUTERS = REPO / "backend" / "routers"

rep_text = REP.read_text(encoding="utf-8")
rows = re.findall(
    r'\|\s*🟡\s*\|\s*RN1\s*\|\s*routers\s*\|\s*`backend\\routers\\([^`]+)`',
    rep_text,
)
print("RN1 router rows found:", len(rows))

stems = sorted({pathlib.Path(r).stem for r in rows})
missing = [s for s in stems if not (ROUTERS / f"{s}.py").exists()]
print("unique stems:", len(stems), "| missing on disk:", len(missing))
for m in missing:
    print("  MISSING:", m)

KNOWN_SURFACES = ("logistics_partner", "admin", "supplier", "customer", "public", "partner")


def propose(stem: str) -> str:
    """{surface}_{domain}_management — consistent, contract-compliant.

    - strip leading underscore (internal primitives module)
    - surface = first token if it's a known surface, else 'public'
    - domain = remaining tokens (or 'core' when the name is only a surface)
    - operation = 'management' (universal, matches report's admin_orders_management)
    """
    s = stem
    if s.startswith("_"):
        s = s[1:]
    tokens = s.split("_")
    surface = None
    for cand in KNOWN_SURFACES:
        if tokens[0] == cand:
            surface = cand
            break
    if surface is None:
        surface = "public"
        rest = tokens
    else:
        rest = tokens[1:]
    domain = "_".join(rest) if rest else "core"
    return f"{surface}_{domain}_management"

print("\n=== PROPOSED RENAME MAP (sample of 40) ===")
for s in stems[:40]:
    print(f"  {s}.py  ->  {propose(s)}.py")

print("\n=== collisions check ===")
targets = {}
for s in stems:
    t = propose(s)
    targets.setdefault(t, []).append(s)
for t, srcs in targets.items():
    if len(srcs) > 1:
        print(f"  COLLISION: {t} <- {srcs}")
print("total proposed targets:", len(targets), "vs sources:", len(stems))
