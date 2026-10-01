"""Regression test for FILE-054: verify the web root layout exists at the canonical path.

The audit previously recorded a stale path `app/_layout.tsx`; the real root layout
for the Next.js web app lives at `frontend/web_app/src/app/layout.tsx`.
This test guards against future path drift.
"""

import os

# Canonical path per ARCHITECTURE_STACK.md §2 (frontend layout)
# Test file is at backend/tests/frontend/ so we need ../../.. to reach project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
CANONICAL_WEB_LAYOUT = os.path.join(
    PROJECT_ROOT, "frontend", "web_app", "src", "app", "layout.tsx"
)

STALE_PATHS = [
    os.path.join(PROJECT_ROOT, "frontend", "web_app", "src", "app", "_layout.tsx"),
    os.path.join(PROJECT_ROOT, "frontend", "web_app", "app", "_layout.tsx"),
]


def test_web_root_layout_exists_at_canonical_path():
    """The Next.js root layout must exist at the canonical path."""
    canonical = os.path.abspath(CANONICAL_WEB_LAYOUT)
    assert os.path.isfile(canonical), f"Root layout missing at {canonical}"


def test_stale_underscore_layout_does_not_exist():
    """The stale `_layout.tsx` variant must NOT exist in the web app src/app tree."""
    for stale in STALE_PATHS:
        stale_abs = os.path.abspath(stale)
        assert not os.path.exists(stale_abs), (
            f"Stale path {stale_abs} must not exist; canonical is layout.tsx (no underscore)"
        )


def test_layout_contains_no_secrets():
    """Root layout must not expose sensitive data (API keys, tokens, passwords)."""
    canonical = os.path.abspath(CANONICAL_WEB_LAYOUT)
    with open(canonical, "r", encoding="utf-8") as fh:
        content = fh.read()

    sensitive_patterns = [
        "API_KEY",
        "SECRET_KEY",
        "TOKEN",
        "PASSWORD",
        "api_key",
        "secret_key",
        "password",
        "PRIVATE",
        "CREDENTIAL",
    ]
    for pattern in sensitive_patterns:
        assert pattern not in content, (
            f"Sensitive pattern '{pattern}' found in root layout"
        )
