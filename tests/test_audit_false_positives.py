"""Regression tests locking in the verified resolution of the 4 remaining
RED findings from SYSTEM_AUDIT_REPORT.md (fresh audit: RED 102 -> 4).

Each test asserts the *verified* state of the codebase so the audit findings
cannot silently regress:

- DBA02 (2x)  ``create_all`` must never be an executable call in migrations —
               the audit matched the word inside module docstrings (FP).
- DS02 (1x)   no real ``<style>`` tag may exist in frontend component files —
               the audit matched a CSS comment mentioning the tag (FP).
- F5 (1x)     ``backend/.env`` must stay gitignored + untracked, with
               ``.env.example`` as the committed template (FP: file on disk
               is fine; it must never be committed).
- F4 (0x now) ``*.db`` dev artifacts must stay gitignored (already resolved).
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
MIGRATIONS = BACKEND / "alembic" / "versions"
FRONTEND_SRC = ROOT / "frontend" / "web_app" / "src"


def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


# ── DBA02: create_all must be docstring-only in migrations ─────────────────

def _strip_docstring(source: str) -> str:
    """Remove the leading triple-quoted module docstring, if present."""
    match = re.match(r'^\s*(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*', source)
    return source[match.end():] if match else source


def test_migrations_have_no_unguarded_create_all():
    """DBA02: any executable ``create_all`` must be dev-gated.

    The root baseline migration (b81bfc888610) legitimately materialises the
    ORM schema, but only behind an explicit fresh-database guard
    (``_database_has_tables``). All other migrations may only mention
    ``create_all`` inside docstrings.
    """
    baseline = "b81bfc888610"
    migration_files = list(MIGRATIONS.glob("*.py"))
    assert migration_files, "expected migration files to exist"

    offenders = []
    for path in migration_files:
        code = _strip_docstring(path.read_text(encoding="utf-8", errors="replace"))
        if "create_all" not in code:
            continue
        if baseline in path.name:
            # Allowed, but must be guarded by the fresh-DB check.
            assert "_database_has_tables" in code, (
                f"{path.name}: baseline create_all lost its fresh-DB guard"
            )
            assert re.search(r"if\s+not\s+_database_has_tables\(\)", code), (
                f"{path.name}: baseline create_all must be gated"
            )
            continue
        offenders.append(str(path))
    assert not offenders, f"unguarded create_all found in: {offenders}"


# ── DS02: no real <style> tag in frontend source ────────────────────────────

def test_no_real_style_tag_in_frontend_components():
    """DS02: no ``<style`` tag outside comments/CSS context."""
    offenders = []
    for path in FRONTEND_SRC.rglob("*"):
        if path.suffix not in {".tsx", ".jsx", ".ts", ".js"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            stripped = line.strip()
            if not stripped.startswith(("//", "*", "/*")):
                if re.search(r"<style\b", line):
                    offenders.append(f"{path}:{lineno}: {line.strip()[:80]}")
    assert not offenders, f"real <style> tag found:\n" + "\n".join(offenders)


# ── F5: .env must be gitignored + untracked, .env.example must exist ───────

def test_backend_env_is_gitignored_and_untracked():
    """F5: the dev .env may exist on disk but must never be committed."""
    env_path = BACKEND / ".env"
    if not env_path.exists():
        # Nothing on disk -> nothing to leak; also acceptable.
        return
    ignored = _run_git("check-ignore", "-q", str(env_path))
    tracked = _run_git("ls-files", str(env_path))
    assert not tracked, f"{env_path} is tracked by git (secret leak!)"
    assert ignored == "", f"{env_path} is NOT gitignored"


def test_env_example_exists():
    """F5: the committed template .env.example must exist."""
    assert (BACKEND / ".env.example").exists(), "missing backend/.env.example"


# ── F4: db artifacts must stay gitignored ───────────────────────────────────

def test_sqlite_db_artifacts_gitignored():
    """F4: dev *.db files may exist on disk but must never be tracked."""
    for candidate in (ROOT / "zozi.db", BACKEND / "zozi.db"):
        tracked = _run_git("ls-files", str(candidate))
        assert not tracked, f"{candidate} is tracked by git"
