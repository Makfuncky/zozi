"""SQLite-compatible schema helpers for Alembic migrations and the app engine.

The ORM models are organised into 16 bounded-context PostgreSQL schemas, but
SQLite has no concept of schemas. On SQLite the engine maps every bounded
context schema to ``None`` (flat namespace) via ``schema_translate_map`` so the
same ORM metadata can be reflected without per-schema prefixes.

Because foreign-key targets in the model layer are often written as bare
``"users.id"`` while the owning table is registered as ``"core.users"``
(schema-qualified), a metadata-level patch is required before
``configure_mappers()`` / ``create_all()`` can resolve cross-table references
on SQLite. This module centralises that patch so both the test conftest and
``alembic/env.py`` share one implementation.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import configure_mappers

SCHEMA_TRANSLATE_MAP = {
    "core": None,
    "commerce": None,
    "supplier": None,
    "customer": None,
    "logistics": None,
    "finance": None,
    "treasury": None,
    "hr": None,
    "country": None,
    "media": None,
    "ai": None,
    "communication": None,
    "audit": None,
    "security": None,
    "analytics": None,
    "configuration": None,
    "trading": None,
}


def _table_schema_map(metadata: MetaData) -> dict[str, str | None]:
    mapping: dict[str, str | None] = {}
    for table in metadata.tables.values():
        if "." in table.key:
            schema, name_part = table.key.split(".", 1)
            mapping[name_part] = schema
        else:
            mapping[table.name] = None
    return mapping


def patch_fk_schemas(metadata: MetaData | None = None) -> int:
    """Rewrite bare ``"table.column"`` foreign-key targets to their
    schema-qualified form (``"schema.table.column"``) so that mapper
    configuration succeeds when tables are registered under a schema while the
    FK is written without one.

    Returns the number of patched references. Idempotent.
    """
    if metadata is None:
        from data.base import Base

        metadata = Base.metadata

    table_schemas = _table_schema_map(metadata)
    patched = 0

    for table in metadata.tables.values():
        for column in table.columns:
            for fk in column.foreign_keys:
                target = fk._colspec
                if not isinstance(target, str):
                    continue
                parts = target.split(".")
                if len(parts) == 2:
                    tbl_name, col_name = parts
                    schema = table_schemas.get(tbl_name)
                    if schema:
                        fk._colspec = f"{schema}.{tbl_name}.{col_name}"
                        if hasattr(fk, "_column_tokens"):
                            del fk._column_tokens
                        patched += 1
                elif len(parts) == 3:
                    schema, tbl_name, col_name = parts
                    expected_schema = table_schemas.get(tbl_name)
                    if expected_schema and expected_schema != schema:
                        fk._colspec = f"{expected_schema}.{tbl_name}.{col_name}"
                        if hasattr(fk, "_column_tokens"):
                            del fk._column_tokens
                        patched += 1
    return patched


def bind_metadata(metadata: MetaData | None = None) -> MetaData:
    """Apply the SQLite FK patch and configure mappers so the metadata is
    safe to ``create_all`` / reflect on SQLite."""
    if metadata is None:
        from data.base import Base

        metadata = Base.metadata
    patch_fk_schemas(metadata)
    configure_mappers()
    return metadata
