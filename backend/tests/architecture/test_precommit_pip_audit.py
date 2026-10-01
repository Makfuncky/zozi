"""Regression tests for the pip-audit pre-commit hook configuration.

Locks the corrected behavior from FILE-104:
  * pip-audit must NOT carry --fix or --ignore-vuln args.
  * pip-audit must point at the canonical version from TECHNOLOGY_STACK.md §11.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_CONFIG = _REPO_ROOT / ".pre-commit-config.yaml"
_PIP_AUDIT_REPO = "https://github.com/pypa/pip-audit"
_FORBIDDEN_ARGS = {"--fix", "--ignore-vuln"}


def _pip_audit_repo() -> dict:
    config = yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        if repo.get("repo") == _PIP_AUDIT_REPO:
            return repo
    pytest.fail("pip-audit repo is not registered in .pre-commit-config.yaml")


def test_pip_audit_has_no_forbidden_args() -> None:
    repo = _pip_audit_repo()
    hook = repo["hooks"][0]
    args = hook.get("args", [])
    forbidden = _FORBIDDEN_ARGS.intersection(args)
    assert not forbidden, (
        "pip-audit must not suppress or auto-fix vulnerabilities in pre-commit; "
        f"forbidden args present: {sorted(forbidden)}"
    )


def test_pip_audit_runs_on_commit_stage() -> None:
    repo = _pip_audit_repo()
    hook = repo["hooks"][0]
    assert hook.get("stages") == ["commit"], (
        "pip-audit must run on every commit to catch dependency CVEs early"
    )


def test_pip_audit_version_matches_technology_stack() -> None:
    repo = _pip_audit_repo()
    rev = repo.get("rev", "")
    assert rev.startswith("v2.10.1"), (
        f"pip-audit rev must satisfy TECHNOLOGY_STACK.md §11 (2.10.1+), got {rev!r}"
    )
