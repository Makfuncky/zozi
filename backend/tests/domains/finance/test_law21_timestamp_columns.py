"""Paired gate for Law 21 — timestamp columns MUST carry server_default=func.now().

Walks BOTH ast.Assign (e.g. ``created_at = Column(...)``) and ast.AnnAssign
(e.g. ``created_at: Column = ...``) so the Stage-0 blind spot cannot hide
defects again.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

FILES = (
    pathlib.Path(__file__).resolve().parents[3]
    / "domains"
    / "finance"
    / "models"
    / "commission.py",
    pathlib.Path(__file__).resolve().parents[3]
    / "domains"
    / "finance"
    / "models"
    / "general_ledger.py",
    pathlib.Path(__file__).resolve().parents[3]
    / "domains"
    / "finance"
    / "models"
    / "tax_rules.py",
)

TIMESTAMP_NAMES = {"created_at", "updated_at"}


def _check_node(node: ast.AST, filepath: pathlib.Path, errors: list[str]) -> None:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return

    # target must be a simple Name whose id is created_at/updated_at
    if isinstance(node, ast.Assign):
        targets = node.targets
    else:
        targets = [node.target]

    for target in targets:
        if not isinstance(target, ast.Name):
            continue
        if target.id not in TIMESTAMP_NAMES:
            continue

        # value must be a Call to Column(...)
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "Column":
            continue

        has_server_default = False
        for kw in node.value.keywords:
            if kw.arg == "server_default":
                has_server_default = True
                break

        if not has_server_default:
            errors.append(
                f"{filepath}:{node.lineno} "
                f"{target.id} missing server_default=func.now() (Law 21)"
            )


def _audit_file(filepath: pathlib.Path) -> list[str]:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    errors: list[str] = []
    for node in ast.walk(tree):
        _check_node(node, filepath, errors)
    return errors


@pytest.mark.parametrize("filepath", FILES)
def test_timestamp_columns_have_server_default(filepath: pathlib.Path) -> None:
    errors = _audit_file(filepath)
    assert not errors, (
        "Timestamp columns missing server_default=func.now():\n"
        + "\n".join(errors)
    )
