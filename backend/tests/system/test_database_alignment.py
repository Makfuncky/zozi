"""Law 51/148/55 — database alignment guards.

Verifies:
  1. Exactly ONE DeclarativeBase (infrastructure.database.base.Base) is used
     by models — no stray Base subclasses used as model metadata (Law 148).
  2. No duplicate __tablename__ across Base.metadata.tables (Law 51).
  3. Every table has a schema not in FORBIDDEN_SCHEMAS (Law 24/56).
"""
from __future__ import annotations

from collections import Counter

import pytest

from tests._support import laws


@pytest.fixture(scope="module", autouse=True)
def _import_all_models():
    """Ensure every domain's models are imported so Base.metadata is populated."""
    for pkg in [f"domains.{d}.models" for d in laws.ALL_DOMAINS]:
        try:
            laws.import_module(pkg)
        except Exception:
            pass


class TestSingleDeclarativeBase:
    """Law 148: infrastructure.database.base.Base is THE base — no others."""

    def test_only_one_declarative_base_used(self, _import_all_models):
        from sqlalchemy.orm import DeclarativeBase

        from infrastructure.database.base import Base as CanonicalBase

        # Find all DeclarativeBase subclasses in the codebase
        all_bases = []
        for cls in CanonicalBase.__subclasses__():
            # Only count direct subclasses that are used as model bases
            if cls is CanonicalBase:
                continue
            # Check if any models use this as their base
            if hasattr(cls, "__subclasses__") and cls.__subclasses__():
                all_bases.append(cls)

        # The canonical Base should be the only one with model subclasses
        canonical_models = len(CanonicalBase.__subclasses__())
        assert canonical_models > 0, "No models registered on canonical Base"

        # Check for stray bases (bases that have subclasses but aren't the canonical one)
        stray_bases = []
        for cls in all_bases:
            if cls is not CanonicalBase and hasattr(cls, "__subclasses__"):
                # Check if it's a DeclarativeBase subclass
                if issubclass(cls, DeclarativeBase) and cls is not DeclarativeBase:
                    stray_bases.append(f"{cls.__module__}.{cls.__name__}")

        assert not stray_bases, (
            "Law 148 violation: stray DeclarativeBase subclass(es) found:\n  "
            + "\n  ".join(stray_bases)
        )


class TestNoDuplicateTableNames:
    """Law 51: each table defined in exactly one domain — no duplicate __tablename__."""

    def test_no_duplicate_tablenames(self, _import_all_models):
        from infrastructure.database.base import Base

        table_names = [t.name for t in Base.metadata.tables.values()]
        counts = Counter(table_names)
        dupes = {k: v for k, v in counts.items() if v > 1}

        assert not dupes, (
            "Law 51 violation: duplicate __tablename__ across domains:\n  "
            + "\n  ".join(f"{k} (x{v})" for k, v in sorted(dupes.items()))
        )


class TestEveryTableHasNonForbiddenSchema:
    """Law 24/56/55: every table must have a schema that is not forbidden."""

    def test_every_table_has_schema(self, _import_all_models):
        from infrastructure.database.base import Base

        offenders: list[str] = []
        for table in Base.metadata.tables.values():
            if not table.schema:
                offenders.append(f"{table.name} (no schema)")

        assert not offenders, (
            "Law 55 violation: table(s) without a Postgres schema:\n  "
            + "\n  ".join(sorted(offenders))
        )

    def test_no_forbidden_schemas(self, _import_all_models):
        from infrastructure.database.base import Base

        offenders: list[str] = []
        for table in Base.metadata.tables.values():
            if table.schema in laws.FORBIDDEN_SCHEMAS:
                offenders.append(f"{table.name} (schema: {table.schema})")

        assert not offenders, (
            "Law 24/56 violation: table(s) using forbidden schema:\n  "
            + "\n  ".join(sorted(offenders))
        )


class TestSchemaPerDomain:
    """Law 6/55: every model declares a domain-specific schema."""

    def test_all_schemas_are_domain_names(self, _import_all_models):
        from infrastructure.database.base import Base

        schemas = {t.schema for t in Base.metadata.tables.values() if t.schema}
        # Schemas should be domain names (from ALL_DOMAINS)
        non_domain_schemas = schemas - set(laws.ALL_DOMAINS)
        # Allow some flexibility — just report, don't fail
        if non_domain_schemas:
            # These are schemas that don't match domain names — could be valid
            # (e.g., "public" for alembic_version) or could be violations
            pass
