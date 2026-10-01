"""Phase tech: cache directory gitignore checks."""
from __future__ import annotations

from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def test_backend_gitignore_excludes_ruff_cache() -> None:
    gi = _BACKEND_ROOT / ".gitignore"
    assert gi.exists(), "backend/.gitignore must exist"
    text = gi.read_text(encoding="utf-8")
    assert ".ruff_cache/" in text, "backend/.gitignore must exclude .ruff_cache/"
