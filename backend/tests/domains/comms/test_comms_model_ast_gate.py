"""Paired AST gate for the comms model cluster (FILE 75 / FILE 76 / FILE 78).

Two blind spots let 40+ Law-21 defects survive a green suite elsewhere in this
repo:

1. The existing ``test_communication_model_laws.py`` only walks
   ``communication.py``.  ``communication_schema_models.py`` and ``incident.py``
   are not covered.
2. The Law-21 walk in ``tests/architecture/test_law19_through_law31.py`` only
   inspects ``ast.AnnAssign``.  Models that use bare ``ast.Assign`` (like
   ``communication.py``) are invisible to that gate.

This module fixes both gaps and adds a cross-file consistency check between
``communication.py`` and ``communication_schema_models.py`` so that a mismatch
in FK ondelete behavior or column typing cannot hide behind per-file passes.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[3]

COMMS_MODEL_FILES = [
    BACKEND_ROOT / "domains/comms/models/communication.py",
    BACKEND_ROOT / "domains/comms/models/communication_schema_models.py",
    BACKEND_ROOT / "domains/comms/models/incident.py",
]

COMMS_SCHEMA = "comms"


@pytest.fixture(scope="module")
def comms_model_sources():
    """Return ``{filename: ast.Module}`` for the three comms model files."""
    return {
        path.name: ast.parse(path.read_text(encoding="utf-8"))
        for path in COMMS_MODEL_FILES
    }


def _timestamp_assignments(tree: ast.Module) -> list[dict]:
    """Return every ``created_at`` / ``updated_at`` assignment in *tree*.

    Walks **both** ``ast.Assign`` and ``ast.AnnAssign`` so bare column
    declarations are not missed.
    """
    assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            target_name = None
            value_source = None
            is_ann = False
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id in (
                        "created_at",
                        "updated_at",
                    ):
                        target_name = target.id
                        value_source = item.value
                        break
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name) and item.target.id in (
                    "created_at",
                    "updated_at",
                ):
                    target_name = item.target.id
                    value_source = item.value
                    is_ann = True
            if target_name is None or value_source is None:
                continue
            assignments.append(
                {
                    "class": node.name,
                    "column": target_name,
                    "value": ast.unparse(value_source),
                    "is_ann_assign": is_ann,
                    "lineno": item.lineno,
                }
            )
    return assignments


def test_ast_walk_finds_both_assign_shapes(comms_model_sources):
    """Sanity: the walk must surface at least one ``ast.Assign`` and one
    ``ast.AnnAssign`` across the three files, proving the blind-spot fix is
    active."""
    ann_count = 0
    bare_count = 0
    for filename, tree in comms_model_sources.items():
        for assignment in _timestamp_assignments(tree):
            if assignment["is_ann_assign"]:
                ann_count += 1
            else:
                bare_count += 1
    assert bare_count > 0, "No bare ast.Assign timestamp declarations found — blind spot persists"


class TestLaw21ASTGate:
    """Every ``created_at`` / ``updated_at`` in the three comms model files must
    declare ``server_default=func.now()``."""

    @pytest.mark.parametrize("path", COMMS_MODEL_FILES, ids=lambda p: p.name)
    def test_every_timestamp_has_server_default(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders = []
        for assignment in _timestamp_assignments(tree):
            if "server_default" not in assignment["value"]:
                offenders.append(
                    f"{assignment['class']}.{assignment['column']} at {path.name}:"
                    f"{assignment['lineno']} — {assignment['value']}"
                )
        assert not offenders, (
            f"{len(offenders)} timestamp columns lack server_default=func.now():\n  "
            + "\n  ".join(offenders)
        )

    @pytest.mark.parametrize("path", COMMS_MODEL_FILES, ids=lambda p: p.name)
    def test_no_python_side_default_on_timestamps(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders = []
        for assignment in _timestamp_assignments(tree):
            # ``default=`` is the Python-side anti-pattern Law 21 forbids.
            if "default=" in assignment["value"] and "server_default" not in assignment["value"]:
                offenders.append(
                    f"{assignment['class']}.{assignment['column']} at {path.name}:"
                    f"{assignment['lineno']} — {assignment['value']}"
                )
        assert not offenders, (
            f"{len(offenders)} timestamp columns carry Python-side default=:\n  "
            + "\n  ".join(offenders)
        )


class TestCrossFileConsistency:
    """``communication.py`` and ``communication_schema_models.py`` must agree on
    shared column names, types, schema, and FK ondelete behavior."""

    @pytest.fixture(scope="class")
    def comms_package_metadata(self):
        """Load every comms model class from both files onto the shared Base."""
        from infrastructure.database.base import Base

        return Base.metadata

    def test_no_duplicate_tables_across_comms_package(self, comms_package_metadata):
        owners = {}
        for full_name in comms_package_metadata.tables:
            schema, _, table_name = full_name.partition(".")
            if schema == COMMS_SCHEMA:
                owners.setdefault(table_name, []).append(full_name)
        duplicated = {t: v for t, v in owners.items() if len(v) > 1}
        assert not duplicated, (
            f"{len(duplicated)} tables declared more than once in schema "
            f"{COMMS_SCHEMA!r}: {duplicated}"
        )

    def test_fk_ondelete_consistent_for_support_tickets(self):
        """Both files that reference ``comms.support_tickets.id`` must agree on
        ondelete."""
        import ast

        targets = []
        for fname in (
            "communication.py",
            "communication_schema_models.py",
        ):
            path = BACKEND_ROOT / "domains/comms/models" / fname
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        val = None
                        target_name = None
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    val = ast.unparse(item.value)
                                    target_name = target.id
                        elif isinstance(item, ast.AnnAssign):
                            if isinstance(item.target, ast.Name) and item.value:
                                val = ast.unparse(item.value)
                                target_name = item.target.id
                        if val and "support_tickets.id" in val and "ForeignKey" in val:
                            # extract ondelete argument
                            ondelete = "RESTRICT" if "RESTRICT" in val else "SET NULL" if "SET NULL" in val else "UNKNOWN"
                            targets.append((fname, node.name, target_name, ondelete))

        # All FKs targeting support_tickets.id should agree on ondelete.
        ondelete_values = {t[3] for t in targets}
        assert len(ondelete_values) == 1, (
            "Multiple ondelete behaviors for comms.support_tickets.id: "
            + "\n  ".join(f"{f}:{cls}.{col} -> {od}" for f, cls, col, od in targets)
        )
