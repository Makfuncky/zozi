"""B4 / R5 gate - forbid a catch-all permission wildcard in require_feature.

A bare require_feature("*") (literal asterisk) grants *every* feature and
silently defeats the entire RBAC surface. Namespace wildcards such as
require_feature("admin.*") are legitimate (they match a feature subtree) and
are NOT flagged by this test.

Run: pytest tests/architecture/test_require_feature_no_star.py -q
"""
from __future__ import annotations

import os
import re

import pytest

_ROOT = os.path.dirname(os.path.abspath(__file__))
while True:
    if os.path.exists(os.path.join(_ROOT, "main.py")) and os.path.isdir(os.path.join(_ROOT, "modules")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent

# Match a literal catch-all only: require_feature("*") with optional whitespace.
_CATCHALL = re.compile(r"require_feature\s*\(\s*[\"']\s*\*\s*[\"']\s*\)")

_EXCLUDES = {"venv", ".git", "__pycache__", "_extra_files", "tests"}


def _scan():
    hits = []
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDES]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read()
            except OSError:
                continue
            for m in _CATCHALL.finditer(txt):
                rel = os.path.relpath(p, _ROOT).replace(os.sep, "/")
                hits.append(f"{rel}: catch-all require_feature('*')")
    return hits


def test_no_catchall_require_feature():
    hits = _scan()
    assert not hits, "Catch-all permission wildcard(s) found:\n" + "\n".join(hits)
