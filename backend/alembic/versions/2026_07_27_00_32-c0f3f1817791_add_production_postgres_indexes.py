"""add production postgres search indexes + partitioning

Postgres-only indexes (skipped on SQLite):
- pg_trgm extension + GIN indexes for ILIKE search on products.name,
  products.description, products.brand, products.tags, categories.name,
  supplier_profiles.business_name, users.email
- tsvector GIN index for full-text search on products

Partitioning preparation:
- audit_logs, notifications, shipment_events get created_at indexes
  for monthly partition pruning

Revision ID: c0f3f1817791
Revises: e70b2cb9a90f
Create Date: 2026-07-27 00:32:38.569321+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

revision: str = "c0f3f1817791"
down_revision: Union[str, None] = "e70b2cb9a90f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres(conn: Connection) -> bool:
    return conn.dialect.name == "postgresql"


def upgrade() -> None:
    conn = op.get_bind()

    if _is_postgres(conn):
        # ── pg_trgm extension for ILIKE / %term% substring search ───────
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

        # ── Product search indexes ──────────────────────────────────────
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_name_trgm "
            "ON products USING GIN (lower(name) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_description_trgm "
            "ON products USING GIN (lower(coalesce(description, '')) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_brand_trgm "
            "ON products USING GIN (lower(brand) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_tags_trgm "
            "ON products USING GIN (lower(tags) gin_trgm_ops)"
        )

        # ── Full-text search vector (tsvector) ──────────────────────────
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_fts "
            "ON products USING GIN ("
            "  to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))"
            ")"
        )

        # ── Category / supplier / user substring search ─────────────────
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_categories_name_trgm "
            "ON categories USING GIN (lower(name) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_supplier_profiles_business_name_trgm "
            "ON supplier_profiles USING GIN (lower(business_name) gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_users_email_trgm "
            "ON users USING GIN (lower(email) gin_trgm_ops)"
        )

    # ── Partitioning support — time-series indexes on high-growth tables ─
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], postgresql_using="btree")
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], postgresql_using="btree")
    op.create_index("ix_shipment_events_created_at", "shipment_events", ["created_at"], postgresql_using="btree")

    # ── Pagination / list-endpoint performance indexes ──────────────────
    op.create_index("ix_products_is_active_is_deleted", "products", ["is_active", "is_deleted"], postgresql_using="btree")
    op.create_index("ix_orders_created_at", "orders", ["created_at"], postgresql_using="btree")


def downgrade() -> None:
    conn = op.get_bind()

    if _is_postgres(conn):
        op.execute("DROP INDEX IF EXISTS ix_products_name_trgm")
        op.execute("DROP INDEX IF EXISTS ix_products_description_trgm")
        op.execute("DROP INDEX IF EXISTS ix_products_brand_trgm")
        op.execute("DROP INDEX IF EXISTS ix_products_tags_trgm")
        op.execute("DROP INDEX IF EXISTS ix_products_fts")
        op.execute("DROP INDEX IF EXISTS ix_categories_name_trgm")
        op.execute("DROP INDEX IF EXISTS ix_supplier_profiles_business_name_trgm")
        op.execute("DROP INDEX IF EXISTS ix_users_email_trgm")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_shipment_events_created_at", table_name="shipment_events")
    op.drop_index("ix_products_is_active_is_deleted", table_name="products")
    op.drop_index("ix_orders_created_at", table_name="orders")
