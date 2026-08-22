"""Baseline + scanner for B6 / R6 (keyset pagination — never OFFSET on hot lists).

The ``ports.py`` read surface is already enforced offset-free by
``tests/architecture/test_keyset_pagination.py::test_all_domain_ports_are_offset_free``.
This module baselines the remaining **adoption-layer** OFFSET calls that live in
``domains/*/services``, ``modules/*/routers``, ``infrastructure`` and ``middleware``
— the ~245 SQL ``OFFSET`` calls the routers + frontend still depend on (the
PART 0.7 deferred sweep). They cannot be bulk-removed without a frontend cursor
contract change, so the architecture gate only **locks regressions**: the count of
``.offset(`` per file must never grow, and no new file may start using OFFSET.

``_offset_adoption_baseline.txt`` freezes the current offenders. Regenerate it after
an intentional migration (a list endpoint ported to a ``list_*_keyset`` reader)::

    python tests/_gen_offset_adoption_baseline.py
"""
from __future__ import annotations

import glob
import os

def _find_backend_root() -> str:
    """Walk up from this file to the backend root (contains main.py + modules/)."""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "modules")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_offset_adoption_baseline.txt")

# Adoption-layer roots that may still use OFFSET (everything except the ports
# read surface, which is enforced separately, and the sanctioned keyset engine).
SCAN_ROOTS = ["domains", "modules", "infrastructure", "middleware"]

# Files that are NOT part of the OFFSET debt baseline:
#  - ports.py : already offset-free, enforced by test_all_domain_ports_are_offset_free
#  - pagination.py : the keyset engine (infrastructure/utils/pagination.py)
EXCLUDE_BASENAMES = {"ports.py", "pagination.py"}
SKIP_DIR_PARTS = {"tests", "_extra_files", "scripts", "__pycache__", ".venv"}


def _offset_count(path: str) -> int:
    try:
        txt = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return 0
    return txt.count(".offset(")


def scan_all() -> dict[str, int]:
    """Return {relpath: count} for every adoption-layer file using OFFSET."""
    out: dict[str, int] = {}
    for root in SCAN_ROOTS:
        base = os.path.join(BACKEND, root)
        if not os.path.isdir(base):
            continue
        for path in glob.glob(os.path.join(base, "**", "*.py"), recursive=True):
            parts = set(path.replace("\\", "/").split("/"))
            if parts & SKIP_DIR_PARTS:
                continue
            if os.path.basename(path) in EXCLUDE_BASENAMES:
                continue
            rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
            cnt = _offset_count(path)
            if cnt:
                out[rel] = cnt
    return out


def load_baseline() -> dict[str, int]:
    if not os.path.exists(BASELINE_PATH):
        return {}
    out: dict[str, int] = {}
    for line in open(BASELINE_PATH, encoding="utf-8"):
        line = line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rel, _, cnt = stripped.partition(" ")
        if not cnt:
            continue
        try:
            out[rel] = int(cnt)
        except ValueError:
            continue
    return out


def regenerate() -> dict[str, int]:
    baseline = dict(sorted(scan_all().items()))
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        fh.write("# SQL OFFSET pagination calls in the adoption layer (B6 / R6 keyset sweep).\n")
        fh.write("# Baseline frozen by the architecture gate; the count per file must only DECREASE.\n")
        fh.write("# Regenerate with tests/_gen_offset_adoption_baseline.py after an intentional migration.\n")
        fh.write("# Excludes ports.py (enforced by test_all_domain_ports_are_offset_free)\n")
        fh.write("# and the keyset engine (infrastructure/utils/pagination.py).\n")
        for rel, cnt in baseline.items():
            fh.write(f"{rel} {cnt}\n")
    return baseline


if __name__ == "__main__":
    base = regenerate()
    print(f"Wrote {len(base)} baseline files ({sum(base.values())} OFFSET calls) to {BASELINE_PATH}")
