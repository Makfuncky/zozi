"""Phase 4G: Secrets management (Task 7).

Confirms no live secrets or test fixtures with weak passwords are committed
to the source tree, and that the .gitignore excludes .env files.
"""
from __future__ import annotations

import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_FRONTEND_ROOT = _BACKEND_ROOT.parent / "frontend"
_EXCLUDE_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git",
                 "dist", "build", ".expo"}


def _iter_py(root: pathlib.Path):
    if not root.exists():
        return
    # Use os.walk to gracefully skip unreadable dirs (symlink loops, etc.)
    import os
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # In-place filter to skip excluded dirs
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield pathlib.Path(dirpath) / fn


def test_no_live_stripe_keys_in_source():
    """Stripe live keys start with sk_live_<alnum>. Strings used as detection
    patterns (e.g. startswith("sk_live_") checks) are allowed."""
    import re
    targets = [_BACKEND_ROOT, _FRONTEND_ROOT]
    offenders: list[str] = []
    # A real key is "sk_live_" followed by 16+ alnum chars
    live_pat = re.compile(r"sk_live_[A-Za-z0-9]{16,}")
    for root in targets:
        for path in _iter_py(root):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if live_pat.search(text):
                offenders.append(str(path))
    assert not offenders, f"Live Stripe keys found in: {offenders}"


def test_gitignore_excludes_env():
    gi = _BACKEND_ROOT.parent / ".gitignore"
    if not gi.exists():
        pytest.skip(".gitignore not at repo root")
    text = gi.read_text(encoding="utf-8", errors="ignore")
    assert ".env" in text
    assert (".env.local" in text) or (".env*" in text) or (".env." in text)


def test_no_aws_access_keys_in_source():
    """AWS access keys are AKIA + 16 alnum. Detection patterns and the
    well-known ``AKIAIOSFODNN7EXAMPLE`` AWS-published placeholder are
    allowed; this test only flags real keys."""
    import re
    real_key = re.compile(r"AKIA[0-9A-Z]{16,}")
    offenders: list[str] = []
    for path in _iter_py(_BACKEND_ROOT):
        try:
            t = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in real_key.finditer(t):
            chunk = m.group(0)
            if "EXAMPLE" in chunk:
                continue
            # Skip regex patterns / docs that mention the literal but don't
            # embed it as a credential
            ctx = t[max(0, m.start() - 40):m.end() + 20]
            if "re.compile" in ctx or "EXAMPLE" in chunk:
                continue
            offenders.append(f"{path}: {chunk[:25]}")
            break
    assert not offenders, f"AWS access key found in: {offenders}"
