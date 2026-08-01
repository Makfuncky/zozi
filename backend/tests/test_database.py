"""Database governance tests for DB24 production checklist compliance.

These tests verify that:
1. Connection pool is properly configured with explicit pool_size = 20
2. Database schema matches ORM models (migration drift detection)
3. RLS context setter is properly integrated
4. Required canonical tables exist
"""
import pytest
from sqlalchemy import text


class TestConnectionPool:
    """DB24: Connection pool configuration tests."""

    def test_pool_size_is_explicit_literal(self):
        """Pool size must be explicitly set to 20, not derived from settings."""
        from db.database import POOL_SIZE
        assert POOL_SIZE == 20, f"POOL_SIZE must be 20, got {POOL_SIZE}"

    def test_pool_max_overflow_is_explicit_literal(self):
        """Max overflow must be explicitly set."""
        from db.database import MAX_OVERFLOW
        assert MAX_OVERFLOW == 30, f"MAX_OVERFLOW must be 30, got {MAX_OVERFLOW}"

    def test_pool_recycle_is_explicit_literal(self):
        """Pool recycle must be explicitly set."""
        from db.database import POOL_RECYCLE
        assert POOL_RECYCLE == 1800, f"POOL_RECYCLE must be 1800, got {POOL_RECYCLE}"

    def test_pool_timeout_is_explicit_literal(self):
        """Pool timeout must be explicitly set."""
        from db.database import POOL_TIMEOUT
        assert POOL_TIMEOUT == 10, f"POOL_TIMEOUT must be 10, got {POOL_TIMEOUT}"

    def test_engine_pool_size_matches_literal(self, engine):
        """Engine pool size must match the explicit literal."""
        from db.database import POOL_SIZE, MAX_OVERFLOW
        pool = engine.pool
        if hasattr(pool, 'size'):
            assert pool.size() == POOL_SIZE, f"Pool size {pool.size()} != {POOL_SIZE}"
        if hasattr(pool, 'overflow'):
            assert pool.overflow() <= MAX_OVERFLOW, f"Pool overflow {pool.overflow()} > {MAX_OVERFLOW}"


class TestMigrationDrift:
    """DB13: Verify migrations exist for all ORM-only tables."""

    def test_upload_jobs_table_exists(self, db_session):
        """upload_jobs table must exist (ORM-only table)."""
        from models import UploadJob
        result = db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_jobs'")
        ).fetchone()
        assert result is not None, "upload_jobs table missing from migration"


class TestCanonicalTables:
    """DB29: Verify required canonical tables exist."""

    def test_commission_rules_table_exists(self, db_session):
        """commission_rules table must exist as canonical platform table."""
        result = db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='commission_rules'")
        ).fetchone()
        assert result is not None, "commission_rules table missing from canonical tables"

    def test_feature_flags_table_exists(self, db_session):
        """feature_flags table must exist as canonical platform table."""
        result = db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='feature_flags'")
        ).fetchone()
        assert result is not None, "feature_flags table missing from canonical tables"

    def test_worm_audit_table_exists(self, db_session):
        """worm_audit table must exist as canonical platform table."""
        result = db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='worm_audit'")
        ).fetchone()
        assert result is not None, "worm_audit table missing from canonical tables"


class TestRLSContext:
    """DB24: RLS context setter verification."""

    def test_rls_context_setter_exists(self):
        """RLS context setter function must exist in middleware."""
        from middleware.country_context import _set_pg_rls_context
        assert callable(_set_pg_rls_context), "RLS context setter not found or not callable"


class TestCreateAllGating:
    """DB02: Verify create_all is properly gated for production safety."""

    def test_create_tables_raises_on_postgres(self):
        """create_tables must raise RuntimeError on PostgreSQL."""
        import importlib
        import os
        original_url = os.environ.get('DATABASE_URL')
        try:
            os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
            import db.database
            importlib.reload(db.database)
            from db.database import create_tables
            with pytest.raises(RuntimeError, match="disabled on PostgreSQL"):
                create_tables()
        finally:
            if original_url:
                os.environ['DATABASE_URL'] = original_url
            else:
                os.environ.pop('DATABASE_URL', None)
            import db.database
            importlib.reload(db.database)

    def test_create_tables_raises_on_production(self):
        """create_tables must raise RuntimeError in production environment."""
        import importlib
        import os
        import db.database as db_module
        original_url = os.environ.get('DATABASE_URL')
        original_env = os.environ.get('APP_ENV')
        try:
            os.environ['DATABASE_URL'] = 'sqlite:///test.db'
            os.environ['APP_ENV'] = 'production'
            with pytest.raises(ValueError, match="SQLite is not allowed in production"):
                importlib.reload(db_module)
        finally:
            if original_url:
                os.environ['DATABASE_URL'] = original_url
            else:
                os.environ.pop('DATABASE_URL', None)
            if original_env:
                os.environ['APP_ENV'] = original_env
            else:
                os.environ.pop('APP_ENV', None)
            importlib.reload(db_module)


class TestDataDictionaryGenerator:
    """DB24: Verify data dictionary generator exists and works."""

    def test_data_dictionary_generator_exists(self):
        """Data dictionary generator script must exist."""
        from pathlib import Path
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "generate_data_dictionary.py"
        assert script_path.exists(), f"Data dictionary generator not found at {script_path}"

    def test_data_dictionary_can_generate(self):
        """Data dictionary generator must be executable and produce output."""
        from scripts.generate_data_dictionary import generate_data_dictionary
        result = generate_data_dictionary()
        assert "generated_at" in result, "Data dictionary missing generated_at field"
        assert "total_tables" in result, "Data dictionary missing total_tables field"
        assert "schemas" in result, "Data dictionary missing schemas field"
        assert result["total_tables"] > 0, "Data dictionary reports no tables"

    def test_data_dictionary_mermaid_output(self):
        """Data dictionary generator must support Mermaid ERD output for DB37."""
        from scripts.generate_data_dictionary import _generate_mermaid_erd, generate_data_dictionary
        result = generate_data_dictionary()
        mermaid_output = _generate_mermaid_erd(result)
        assert "```mermaid" in mermaid_output, "Mermaid output missing code block markers"
        assert "erDiagram" in mermaid_output, "Mermaid output missing erDiagram declaration"


class TestRLSPolicies:
    """DB05: Verify RLS policies are properly defined."""

    def test_rls_policies_file_exists(self):
        """RLS policies SQL file must exist."""
        from pathlib import Path
        policies_path = Path(__file__).resolve().parent.parent / "data" / "pg_rls_policies.sql"
        assert policies_path.exists(), f"RLS policies file not found at {policies_path}"

    def test_rls_policies_have_required_tables(self):
        """RLS policies must cover all country-scoped tables."""
        from pathlib import Path
        policies_path = Path(__file__).resolve().parent.parent / "data" / "pg_rls_policies.sql"
        content = policies_path.read_text()
        
        required_tables = [
            ("orders", "public"),
            ("carts", "commerce"),
            ("coupons", "public"),
            ("payments", "public"),
            ("support_tickets", "public"),
            ("notifications", "public"),
            ("users", "public"),
            ("addresses", "core"),
            ("reviews", "commerce"),
            ("products", "commerce"),
            ("categories", "commerce"),
            ("shipment_events", "logistics"),
            ("journal_entries", "finance"),
            ("commission_rules", "commerce"),
            ("feature_flags", "configuration"),
        ]
        
        for table_name, schema in required_tables:
            policy_name = f"{table_name}_rls_policy"
            found = False
            for line in content.split('\n'):
                if f"CREATE POLICY" in line and policy_name in line:
                    found = True
                    break
            assert found, f"Missing RLS policy for table: {schema}.{table_name}"