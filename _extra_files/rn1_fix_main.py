"""Fixup v2: update main.py router_names using the names still listed there.

The second pass already moved files (e.g. public_health_management.py ->
public_health_access.py). main.py still lists the old names. This reads the old
names from main.py's ("old", "/prefix") tuples, computes the new name with the
same transform, verifies the target file exists, and rewrites the tuples.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
ROUTERS = REPO / "backend" / "routers"
MAIN = REPO / "backend" / "main.py"


def load_tables():
    sys.path.insert(0, str(REPO / "scripts" / "system_trackers"))
    import system_architecture_audit as A
    return (A.PLACEMENT_ALIAS_TO_DOMAIN,
            {str(x).lower() for x in A.DEFAULT_SURFACE_NAMES})


def tokens(stem):
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]


def surface_of(t, surfaces):
    for x in t:
        if x in surfaces:
            return x
    return None


def domain_of(t, aliases):
    for x in t:
        if aliases.get(x):
            return aliases.get(x)
    return None


def op_verb(surface):
    return {
        "admin": "governance", "supplier": "fulfillment", "customer": "tracking",
        "public": "access", "partner": "operations", "logistics_partner": "operations",
    }.get(surface, "tracking")


def main() -> int:
    aliases, surfaces = load_tables()
    text = MAIN.read_text(encoding="utf-8")
    # all first-elements of ("name", ...) tuples in main.py
    names = re.findall(r'\(\s*["\']([^"\']+)["\']\s*,', text)
    plan: dict[str, str] = {}
    for old in names:
        m = re.match(r"^(.*)_(management|endpoint)$", old)
        if not m:
            continue
        base = m.group(1)
        toks = tokens(base)
        s = surface_of(toks, surfaces)
        d = domain_of(toks, aliases)
        if d is None:
            continue
        new = f"{base}_{op_verb(s)}"
        if new == old:
            continue
        if not (ROUTERS / f"{new}.py").exists():
            print(f"  SKIP (target missing): {old} -> {new}")
            continue
        plan[old] = new

    print(f"Plan entries: {len(plan)}")
    mc = 0
    for old, new in plan.items():
        text, n = re.subn(r'\("' + re.escape(old) + r'"\s*,', f'("{new}",', text)
        mc += n
    print(f"router_names entries updated: {mc}")

    tmp = MAIN.with_suffix(".main.tmp")
    for _ in range(5):
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, MAIN)
            print("main.py written OK")
            return 0
        except OSError:
            time.sleep(0.3)
    print("FAILED to write main.py")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
