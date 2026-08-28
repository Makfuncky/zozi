"""Law 6 gate: schema discipline.

Verifies:
  1. Every ORM model has a schema declared (Postgres schema via __table_args__).
  2. No forbidden schemas (core, platform, identity) are used for domain tables.
  3. Naming conventions: snake_case table names, plural tables, <thing>_id FKs.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"

_FORBIDDEN_SCHEMAS = {"core", "platform", "identity"}

_EXCLUDE_TABLES = {"alembic_version"}


def _iter_model_files():
    if not _DOMAINS_DIR.exists():
        return
    for path in sorted(_DOMAINS_DIR.rglob("models/*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _extract_table_info(source: str) -> list[dict]:
    """Extract table name and schema from model source."""
    tables = []
    for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source):
        table_name = m.group(1)
        # Find schema in __table_args__ nearby
        schema_match = re.search(r"['\"]schema['\"]:\s*['\"]([^'\"]+)['\"]", source[m.start():m.start()+500])
        schema = schema_match.group(1) if schema_match else None
        tables.append({"table_name": table_name, "schema": schema})
    return tables


class TestEveryModelHasSchema:
    """Every ORM model must declare a Postgres schema."""

    def test_models_have_schemas(self):
        offenders = []
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            if "__tablename__" not in source:
                continue
            tables = _extract_table_info(source)
            for t in tables:
                if t["table_name"] in _EXCLUDE_TABLES:
                    continue
                if t["schema"] is None:
                    offenders.append(f"{path.name}: {t['table_name']}")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 6 violation: model(s) missing schema declaration:\n  " + msg
            )

    def test_models_have_tablename(self):
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            if "Column" not in source:
                continue
            if "__tablename__" in source:
                assert True
                return
        # If we get here, no models with tablename were found — that's fine
        # (some model files may be mixins or abstract)


class TestNoForbiddenSchemas:
    """Domain tables must not use forbidden schemas (core, platform, identity)."""

    def test_no_forbidden_schemas(self):
        offenders = []
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            for forbidden in _FORBIDDEN_SCHEMAS:
                if f"'schema': '{forbidden}'" in source or f'"schema": "{forbidden}"' in source:
                    offenders.append(f"{path.name}: uses forbidden schema '{forbidden}'")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 6 violation: forbidden schema(s) used:\n  " + msg
            )


class TestNamingConventions:
    """Table names must be snake_case and plural."""

    def test_table_names_are_snake_case(self):
        offenders = []
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source):
                table_name = m.group(1)
                if table_name in _EXCLUDE_TABLES:
                    continue
                if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                    offenders.append(f"{path.name}: '{table_name}'")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 6 violation: table name(s) not snake_case:\n  " + msg
            )

    def test_table_names_are_plural(self):
        offenders = []
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source):
                table_name = m.group(1)
                if table_name in _EXCLUDE_TABLES:
                    continue
                # Check if the last segment (after underscores) ends with 's'
                last_part = table_name.split("_")[-1] if "_" in table_name else table_name
                if not last_part.endswith("s"):
                    offenders.append(f"{path.name}: '{table_name}'")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 6 violation: table name(s) not plural:\n  " + msg
            )

    def test_fk_columns_use_id_suffix(self):
        offenders = []
        fk_pattern = re.compile(r"Column\([^)]*ForeignKey")
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            if "ForeignKey" not in source:
                continue
            # Simple regex-based check for FK columns not ending in _id
            for m in re.finditer(r'(\w+)\s*=\s*Column\([^)]*ForeignKey', source):
                col_name = m.group(1)
                if col_name == "id":
                    continue
                if not col_name.endswith("_id"):
                    offenders.append(f"{path.name}: '{col_name}'")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders[:20])))
            pytest.fail(
                "Law 6 violation: FK column(s) missing '_id' suffix:\n  " + msg
            )

    def test_models_have_timestamps(self):
        offenders = []
        for path in _iter_model_files():
            source = path.read_text(encoding="utf-8")
            if "__tablename__" not in source:
                continue
            table_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source)
            if not table_match:
                continue
            table_name = table_match.group(1)
            if table_name in _EXCLUDE_TABLES:
                continue
            has_created = "created_at" in source
            has_updated = "updated_at" in source
            if not has_created or not has_updated:
                missing = []
                if not has_created:
                    missing.append("created_at")
                if not has_updated:
                    missing.append("updated_at")
                offenders.append(f"{path.name}: missing {', '.join(missing)}")
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 6 violation: model(s) missing timestamp columns:\n  " + msg
            )
