"""Law 7 — DOMAIN_ALLOWLIST.yaml only shrinks (HEAD~1 diff enforcement).

ARCHITECTURE_DIAGRAM.md Law 7: cross-domain imports are allowed only via the
explicit, shrinking allowlist in ``backend/DOMAIN_ALLOWLIST.yaml``. To keep
the allowlist honest we run this test on every CI build; it diffs the current
working-tree copy against the version recorded in ``HEAD~1`` of the same file
and fails the build if the new file has more lines / more entries than the
one from the previous commit.

When ``git`` is unavailable (e.g. shallow CI clones without ``HEAD~1``), the
test degrades to a recorded-baseline file alongside the existing
``test_law7_allowlist_shrink.py`` policy.

Closes audit finding #19.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent.parent  # tests/
_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_ALLOWLIST_REL = "DOMAIN_ALLOWLIST.yaml"
_ALLOWLIST = _BACKEND_ROOT / _ALLOWLIST_REL
_REPO_ROOT = _BACKEND_ROOT.parent  # zozi/
_BASELINE_FALLBACK = _TESTS_DIR / "architecture" / "_allowlist_shrinks_baseline.txt"


def _entry_count(text: str) -> int:
    """Count allowlist ``- `` entries at any indent (a yaml-tolerant heuristic)."""
    return sum(
        1
        for line in text.splitlines()
        if line.lstrip().startswith("- ") and "->" in line
    )


def _git_show(ref: str) -> str | None:
    """Return the file contents at ``ref`` (HEAD~1, HEAD, etc.) or None."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{_ALLOWLIST_REL}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


@pytest.mark.architecture
def test_allowlist_does_not_grow_between_commits() -> None:
    """Compare current file against HEAD~1; fail if it grew.

    Behaviour matrix:
      - file missing                 : FAIL (allowlist must exist, Law 7)
      - git + HEAD~1 readable        : diff and assert size shrank or stayed equal
      - git unavailable              : fall back to recorded baseline file
      - no HEAD~1 (initial commit)   : fall back to recorded baseline file
    """
    if not _ALLOWLIST.exists():
        pytest.fail(
            f"{_ALLOWLIST_REL} must exist (Law 7 allowlist rule). "
            "Create it under backend/DOMAIN_ALLOWLIST.yaml."
        )

    current_text = _ALLOWLIST.read_text(encoding="utf-8", errors="replace")
    current_count = _entry_count(current_text)
    assert current_count > 0, "DOMAIN_ALLOWLIST.yaml has no entries — nothing to enforce."

    previous = _git_show("HEAD~1")
    if previous is not None:
        previous_count = _entry_count(previous)
        assert current_count <= previous_count, (
            f"DOMAIN_ALLOWLIST.yaml grew from {previous_count} entries at HEAD~1 "
            f"to {current_count} entries at HEAD. Law 7: allowlist must only shrink. "
            "Remove obsolete entries before adding new ones."
        )
        return

    # Fallback: recorded baseline file. Refresh it intentionally to match the
    # current (presumably just-shrunk) count.
    if _BASELINE_FALLBACK.exists():
        baseline = int(_BASELINE_FALLBACK.read_text(encoding="utf-8").strip() or "0")
        assert current_count <= baseline, (
            f"DOMAIN_ALLOWLIST.yaml grew from {baseline} (baseline) to {current_count} "
            f"entries. Law 7: allowlist must only shrink."
        )
    _BASELINE_FALLBACK.write_text(str(current_count), encoding="utf-8")


@pytest.mark.architecture
def test_allowlist_file_is_not_empty() -> None:
    if not _ALLOWLIST.exists():
        pytest.skip("DOMAIN_ALLOWLIST.yaml missing — see companion test")
    text = _ALLOWLIST.read_text(encoding="utf-8", errors="replace")
    assert "cross_domain_imports:" in text, (
        "DOMAIN_ALLOWLIST.yaml must declare a 'cross_domain_imports:' section"
    )
