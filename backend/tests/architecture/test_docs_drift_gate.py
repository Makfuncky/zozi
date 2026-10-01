"""Regression and error-path tests for the docs-drift pre-commit gate.

The gate itself has to live inline in .pre-commit-config.yaml because the
resolution contract authorises that single file and no helper script. These
tests therefore lock three things:

  * regression  - the hook is registered, wired to run on every commit, and the
    real canonical docs are in lock-step with the code, so the gate is green.
  * error paths - every drift class the gate advertises (missing canonical doc,
    law-matrix drift, version literal in the architecture doc, undeclared
    domain/module directory) really does fail with a non-zero exit code.
  * payload     - the inline payload still carries all four assertions, so a
    later "simplification" of the entry cannot silently drop a check.

Every mutation happens inside a pytest tmp_path sandbox built from copies; the
real _most_imp_docx documents are never written to.
"""
from __future__ import annotations

import pathlib
import shlex
import shutil
import subprocess

import pytest
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_CONFIG = _REPO_ROOT / ".pre-commit-config.yaml"
_ARCH = "_most_imp_docx/ARCHITECTURE_STACK.md"
_TECH = "_most_imp_docx/TECHNOLOGY_STACK.md"
_ARCH_LABEL = "ARCHITECTURE_STACK.md"
_CLEAN = "docs-drift: canonical docs in lock-step with code"
_LAW_COUNT = 325


def _hook() -> dict:
    config = yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        if repo["repo"] != "local":
            continue
        for hook in repo["hooks"]:
            if hook["id"] == "check-docs-drift":
                return hook
    pytest.fail("check-docs-drift hook is not registered in .pre-commit-config.yaml")


def _argv() -> list[str]:
    """Split `entry` exactly as pre-commit does, on every platform."""
    argv = shlex.split(_hook()["entry"], posix=True)
    assert argv[0:2] == ["python", "-c"], f"unexpected entry shape: {argv[0:2]}"
    return argv


def _payload() -> str:
    return _argv()[2]


def _run(cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(_argv(), cwd=cwd, capture_output=True, text=True)


def _sandbox(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build a throwaway tree that mirrors the repo's docs and backend groups."""
    (tmp_path / "_most_imp_docx").mkdir()
    for rel in (_ARCH, _TECH):
        shutil.copy2(_REPO_ROOT / rel, tmp_path / rel)
    for group in ("domains", "modules"):
        for child in sorted((_REPO_ROOT / "backend" / group).iterdir()):
            if child.is_dir() and child.name != "__pycache__":
                (tmp_path / "backend" / group / child.name).mkdir(parents=True)
    return tmp_path


def _read_arch(root: pathlib.Path) -> str:
    return (root / _ARCH).read_text(encoding="utf-8")


def _write_arch(root: pathlib.Path, text: str) -> None:
    (root / _ARCH).write_text(text, encoding="utf-8")


def _law_lines(text: str, law_id: int) -> list[str]:
    return [ln for ln in text.splitlines(keepends=True) if ln.startswith(f"| {law_id} |")]


def test_sandbox_mirrors_a_green_repo(tmp_path: pathlib.Path) -> None:
    """The fixture must be clean before any mutation is trusted to prove anything."""
    root = _sandbox(tmp_path)
    proc = _run(root)
    assert proc.returncode == 0, f"sandbox fixture is not clean:\n{proc.stdout}"
    assert _CLEAN in proc.stdout


# --------------------------------------------------------------------------
# Regression tests
# --------------------------------------------------------------------------


def test_docs_drift_hook_is_registered_and_wired() -> None:
    """The gate must run on every commit regardless of which files are staged."""
    hook = _hook()
    assert hook["language"] == "system", "the gate must stay offline (no pip download)"
    assert hook["always_run"] is True, (
        "a files:-scoped hook never fires for a backend-only commit while the "
        "canonical docs are stale, which is the drift this gate exists to catch"
    )
    assert hook["pass_filenames"] is False, (
        "the gate reads the canonical docs and the backend tree by path, not from argv"
    )
    assert hook["stages"] == ["commit"]
    assert "files" not in hook, "always_run and files: together would re-gate every file"


def test_docs_drift_hook_asserts_every_drift_class() -> None:
    """The inline payload must carry all four advertised assertions."""
    src = _payload()
    for token, why in (
        (_ARCH, "assertion A: canonical doc presence"),
        (_TECH, "assertion A: canonical doc presence"),
        ("missing canonical doc", "assertion A must name the offending path"),
        (f"list(range(1,{_LAW_COUNT + 1}))", f"assertion B: law ids must be 1..{_LAW_COUNT}"),
        ("law matrix drift", "assertion B must report law-matrix drift"),
        ("[0-9]+[.][0-9]+[.][0-9]+", "assertion C: no version literals in the arch doc"),
        ("version literal", "assertion C must name the offending version"),
        ("undeclared ", "assertion D: every domain/module must be documented"),
        ("sys.exit(1 if E else 0)", "the gate must fail loudly, never swallow findings"),
    ):
        assert token in src, f"missing {why} (expected {token!r} in the entry payload)"


def test_repo_canonical_docs_pass_docs_drift_gate() -> None:
    """Regression: the repository is in lock-step, so the gate is green here."""
    proc = _run(_REPO_ROOT)
    assert proc.returncode == 0, (
        "docs-drift gate fails on the real repository:\n"
        f"{proc.stdout}\n{proc.stderr}"
    )
    assert _CLEAN in proc.stdout


# --------------------------------------------------------------------------
# Error-path tests - one per drift class the gate claims to catch
# --------------------------------------------------------------------------


def test_gate_fails_when_canonical_doc_is_missing(tmp_path: pathlib.Path) -> None:
    """Law 245 / section 14 Deletion Policy: a deleted canonical doc must fail."""
    root = _sandbox(tmp_path)
    (root / _TECH).unlink()
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"missing canonical doc: {_TECH}" in proc.stdout
    assert _CLEAN not in proc.stdout


def test_gate_fails_when_a_law_row_is_deleted(tmp_path: pathlib.Path) -> None:
    """Section 12: all 325 laws, each exactly once - a gap must fail."""
    root = _sandbox(tmp_path)
    text = _read_arch(root)
    hits = _law_lines(text, 100)
    assert len(hits) == 1, "law 100 row not found exactly once in the canonical doc"
    _write_arch(root, text.replace(hits[0], "", 1))
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"law matrix drift: docs declare {_LAW_COUNT} laws, parsed 324 unique ids" in proc.stdout


def test_gate_fails_when_a_law_row_is_duplicated(tmp_path: pathlib.Path) -> None:
    """Section 12: each law appears once - a duplicate must fail too."""
    root = _sandbox(tmp_path)
    text = _read_arch(root)
    hits = _law_lines(text, 7)
    assert len(hits) == 1, "law 7 row not found exactly once in the canonical doc"
    _write_arch(root, text.replace(hits[0], hits[0] * 2, 1))
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"law matrix drift: docs declare {_LAW_COUNT} laws, parsed 324 unique ids" in proc.stdout


def test_gate_fails_on_version_literal_in_architecture_doc(tmp_path: pathlib.Path) -> None:
    """Section 14 Sync Rule: the architecture doc carries no version literals."""
    root = _sandbox(tmp_path)
    _write_arch(root, _read_arch(root) + "\nPinned reference to FastAPI 0.141.4.\n")
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"version literal 0.141.4 in {_ARCH_LABEL}" in proc.stdout


def test_gate_fails_on_undeclared_domain_directory(tmp_path: pathlib.Path) -> None:
    """Law 12 / Law 160: a domain directory the architecture doc never names."""
    root = _sandbox(tmp_path)
    (root / "backend" / "domains" / "billing").mkdir()
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"undeclared domains/billing not named in {_ARCH_LABEL}" in proc.stdout


def test_gate_fails_on_undeclared_module_directory(tmp_path: pathlib.Path) -> None:
    """Law 13 / Law 138: a module directory the architecture doc never names."""
    root = _sandbox(tmp_path)
    (root / "backend" / "modules" / "warehouse").mkdir()
    proc = _run(root)
    assert proc.returncode == 1, f"expected failure, got rc={proc.returncode}"
    assert f"undeclared modules/warehouse not named in {_ARCH_LABEL}" in proc.stdout


def test_gate_ignores_pycache_directories(tmp_path: pathlib.Path) -> None:
    """Build artefacts must not be reported as undeclared domains or modules."""
    root = _sandbox(tmp_path)
    (root / "backend" / "domains" / "__pycache__").mkdir()
    (root / "backend" / "modules" / "__pycache__").mkdir()
    proc = _run(root)
    assert proc.returncode == 0, f"__pycache__ must not fail the gate:\n{proc.stdout}"
    assert _CLEAN in proc.stdout