"""Law 27 / Law 32 — permanent guard: backend scratch scripts must be gitignored.

If this test fails, the .gitignore no longer blocks the exact patterns the
architecture gate (`test_no_debug_scripts_at_backend_root`) flags.  Fix the
.gitignore, do not silence this test.
"""
from __future__ import annotations

import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_GITIGNORE = _REPO_ROOT / ".gitignore"


_REQUIRED_PATTERNS = [
    "backend/_*.py",
    "backend/test_*.py",
    "backend/debug_*.py",
    "backend/check_*.py",
    "backend/fix_*.py",
]


def test_gitignore_blocks_backend_scratch_scripts() -> None:
    """The repo .gitignore must contain every Law 27 scratch-script pattern."""
    if not _GITIGNORE.exists():
        pytest.fail(".gitignore not found at repo root; Law 27 patterns cannot be enforced")
    text = _GITIGNORE.read_text(encoding="utf-8")
    missing = [p for p in _REQUIRED_PATTERNS if p not in text]
    assert not missing, (
        f".gitignore is missing Law 27 scratch-script patterns: {missing}"
    )
