"""Paired test: SCHEMA_TRANSLATE_MAP must cover every schema declared by
an ORM model in Base.metadata, and the test engine must be able to run
create_all() without raising ``unknown database <schema>``.

This test fails before the fix (missing schemas in the map) and passes after.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

from tests.conftest import Base, SCHEMA_TRANSLATE_MAP


class TestSchemaTranslateMapCoverage:
    """Every schema used by an ORM model must be present in the translate map."""

    def test_all_metadata_schemas_are_translated(self):
        declared_schemas = {t.schema for t in Base.metadata.tables.values() if t.schema}
        missing = declared_schemas - set(SCHEMA_TRANSLATE_MAP.keys())
        assert not missing, (
            "SCHEMA_TRANSLATE_MAP is missing schemas used by ORM models: "
            f"{sorted(missing)}"
        )

    def test_create_all_succeeds_for_all_tables(self):
        engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": SCHEMA_TRANSLATE_MAP},
        )
        Base.metadata.create_all(bind=engine)
        insp = inspect(engine)
        created = insp.get_table_names()
        declared = {t.name for t in Base.metadata.tables.values()}
        missing_tables = declared - set(created)
        assert not missing_tables, (
            "create_all() did not create the following tables: "
            f"{sorted(missing_tables)}"
        )
        engine.dispose()
