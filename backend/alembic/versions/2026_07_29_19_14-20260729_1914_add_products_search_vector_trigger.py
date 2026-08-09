"""add products search_vector tsvector column + trigger

Persist the full-text search vector on the products table so the GIN index
is maintained automatically by Postgres instead of being recomputed on
every query. This also fixes the previous config mismatch where the
existing expression index used ``english`` but the query used ``simple``.

Revision ID: 20260729_1914
Revises: 9ff24a0683dd
Create Date: 2026-07-29 19:14:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

revision: str = "20260729_1914"
down_revision: Union[str, None] = "9ff24a0683dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres(conn: Connection) -> bool:
    return conn.dialect.name == "postgresql"


def upgrade() -> None:
    conn = op.get_bind()

    if _is_postgres(conn):
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        op.execute("DROP INDEX IF EXISTS ix_products_fts")

        op.execute(
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS search_vector tsvector"
        )

        op.execute(
            """
            CREATE OR REPLACE FUNCTION products_search_vector_update() RETURNS trigger AS $$
            BEGIN
              NEW.search_vector :=
                to_tsvector('simple',
                  coalesce(NEW.name, '') || ' ' ||
                  coalesce(NEW.description, '') || ' ' ||
                  coalesce(NEW.category, '') || ' ' ||
                  coalesce(NEW.brand, '') || ' ' ||
                  coalesce(NEW.tags, '') || ' ' ||
                  coalesce(NEW.ai_description, '') || ' ' ||
                  coalesce(NEW.materials, '') || ' ' ||
                  coalesce(NEW.color, '') || ' ' ||
                  coalesce(NEW.sizes, '')
                );
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )

        op.execute(
            """
            DROP TRIGGER IF EXISTS products_search_vector_trigger ON products
            """
        )
        op.execute(
            """
            CREATE TRIGGER products_search_vector_trigger
            BEFORE INSERT OR UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION products_search_vector_update()
            """
        )

        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_search_vector_gin "
            "ON products USING GIN (search_vector)"
        )

        op.execute(
            """
            UPDATE products
            SET search_vector = to_tsvector('simple',
              coalesce(name, '') || ' ' ||
              coalesce(description, '') || ' ' ||
              coalesce(category, '') || ' ' ||
              coalesce(brand, '') || ' ' ||
              coalesce(tags, '') || ' ' ||
              coalesce(ai_description, '') || ' ' ||
              coalesce(materials, '') || ' ' ||
              coalesce(color, '') || ' ' ||
              coalesce(sizes, '')
            )
            WHERE search_vector IS NULL
            """
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _is_postgres(conn):
        op.execute("DROP INDEX IF EXISTS ix_products_search_vector_gin")
        op.execute("DROP TRIGGER IF EXISTS products_search_vector_trigger ON products")
        op.execute("DROP FUNCTION IF EXISTS products_search_vector_update")
        op.execute("ALTER TABLE products DROP COLUMN IF EXISTS search_vector")

        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_products_fts
            ON products USING GIN (
              to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))
            )
            """
        )
