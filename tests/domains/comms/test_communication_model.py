"""Tests for Communication domain model audit columns (Law 23)."""
from __future__ import annotations

import ast

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_FILE = REPO_ROOT / "backend" / "domains" / "comms" / "models" / "communication.py"

REQUIRED_COLUMNS = {"created_at", "updated_at", "country_code", "is_deleted"}
TARGET_MODELS = {"Announcement", "HelpCategory"}


def _get_model_columns(source: str):
    tree = ast.parse(source)
    columns = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_cols = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_cols.add(target.id)
            columns[node.name] = class_cols
    return columns


def test_communication_has_audit_columns():
    source = MODEL_FILE.read_text(encoding="utf-8")
    model_columns = _get_model_columns(source)

    for model_name in TARGET_MODELS:
        assert model_name in model_columns, f"Model {model_name} not found in file"
        missing = REQUIRED_COLUMNS - model_columns[model_name]
        assert not missing, f"{model_name} missing columns: {missing}"


def test_announcement_has_country_index():
    source = MODEL_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    index_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "Index":
                if node.args and isinstance(node.args[0], ast.Constant):
                    index_names.add(node.args[0].value)

    assert "ix_announcements_country_created" in index_names
    assert "ix_help_categories_country_created" in index_names
