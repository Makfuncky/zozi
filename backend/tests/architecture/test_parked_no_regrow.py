"""B1 follow-up - forbid regrowth of the ORD-SLICE `_parked` graveyard.

After the deep audit (RESOLVER.md PART 5, Sec 37), the 24 files under
``domains/_parked`` are archived historical leftovers. Their useful logic
(BOGO #18, Points/Loyalty #20) was merged into live ``catalog`` modules; the
rest are dead. This gate enforces two invariants so the graveyard cannot
silently grow again:

1. The set of ``.py`` files under ``domains/_parked`` is exactly the 24
   baselined below. Any NEW file added (regrowth) or accidental deletion
   fails CI, forcing a review.
2. No module OUTSIDE ``_parked`` imports from ``domains._parked`` (dead code
   must stay dead). The live merged copies are the only sanctioned owners.

Run: pytest tests/architecture/test_parked_no_regrow.py -q
"""
from __future__ import annotations

import os
import ast
import sys

import pytest

_ROOT = os.path.dirname(os.path.abspath(__file__))
while True:
    if os.path.exists(os.path.join(_ROOT, "main.py")) and os.path.isdir(os.path.join(_ROOT, "modules")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_EXCLUDES = {"venv", ".git", "__pycache__", "_extra_files", "domains"}

# The domains/_parked graveyard (24 archived files per RESOLVER.md PART 5) was
# removed during the design-system / structure cleanup. Regenerate the baseline
# to an empty set; the law now simply guards against re-introducing a graveyard.
_KNOWN_PARKED = frozenset()

_PARKED_DIR = os.path.join(_ROOT, "domains", "_parked")


def _collect_parked_imports():
    seen = []
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        # Skip the graveyard itself and scratch/test/infra dirs.
        if os.path.abspath(dirpath) == os.path.abspath(_PARKED_DIR):
            continue
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDES]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    tree = ast.parse(fh.read())
            except (OSError, SyntaxError):
                continue
            for n in ast.walk(tree):
                mod = None
                if isinstance(n, ast.Import):
                    for a in n.names:
                        if a.name and "._parked" in a.name or (a.name or "").startswith("domains._parked"):
                            mod = a.name
                elif isinstance(n, ast.ImportFrom):
                    if (n.module or "").startswith("domains._parked") or "._parked" in (n.module or ""):
                        mod = n.module
                if mod:
                    seen.append((os.path.relpath(p, _ROOT), mod))
    return seen


def test_parked_file_set_stable():
    present = frozenset(
        f for f in os.listdir(_PARKED_DIR) if f.endswith(".py")
    ) if os.path.isdir(_PARKED_DIR) else frozenset()
    assert present == _KNOWN_PARKED, (
        "The domains/_parked graveyard drifted from its 24-file baseline.\n"
        "Added: " + ", ".join(sorted(present - _KNOWN_PARKED)) + "\n"
        "Removed: " + ", ".join(sorted(_KNOWN_PARKED - present)) + "\n"
        "Archive (do not delete) or merge+remove via RESOLVER.md PART 5 process."
    )


def test_no_live_imports_from_parked():
    bad = _collect_parked_imports()
    assert not bad, (
        "Modules outside domains/_parked must not import from it (dead code stays dead):\n"
        + "\n".join(f"  {f} -> import {m}" for f, m in bad)
    )
