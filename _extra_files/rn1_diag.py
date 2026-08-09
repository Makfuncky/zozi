"""Diagnose why RN1 still fires after rename.

Imports the real audit module's placement tables and replicates the RN1
flat-mode helper logic to report, per current router stem, the
surface/domain/operation the audit sees and whether RN1 would fire.
"""
from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "system_trackers"))
import system_architecture_audit as A  # noqa: E402

aliases = A.PLACEMENT_ALIAS_TO_DOMAIN
stop = set(A.PLACEMENT_STOP_TOKENS)
surfaces = {str(x).lower() for x in A.DEFAULT_SURFACE_NAMES}


def _tokens(stem):
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]


def _surface(toks):
    for t in toks:
        if t in surfaces:
            return t
    return None


def _domain(toks):
    for t in toks:
        d = aliases.get(t)
        if d:
            return d
    return None


def _has_operation(toks, surface, domain):
    for t in toks:
        if len(t) < 3:
            continue
        if t in stop:
            continue
        if surface and t == surface:
            continue
        if domain and (t == domain or aliases.get(t) == domain):
            continue
        return True
    return False


routers = REPO / "backend" / "routers"
fails = 0
for f in sorted(routers.glob("*.py")):
    if f.name == "__init__.py":
        continue
    toks = _tokens(f.stem)
    s = _surface(toks)
    d = _domain(toks)
    op = _has_operation(toks, s, d)
    missing = [x for x, v in (("surface", s), ("domain", d), ("operation", op)) if not v]
    if missing:
        fails += 1
        if fails <= 120:
            print(f"FAIL {f.stem!r:55} toks={toks} surf={s} dom={d} op={op} miss={missing}")

print(f"\nTOTAL RN1-fail (per audit logic): {fails}")
print("aliases sample (banners?):", aliases.get("banners"), "| commerce:",
      aliases.get("commerce"), "| orders:", aliases.get("orders"))
