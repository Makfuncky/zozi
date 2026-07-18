"""search_snapshots_and_schema_hardening

Revision ID: f1a2b3c4d5e6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    dialect = bind.dialect.name

    if "products" in existing_tables:
        product_columns = _table_columns(inspector, "products")
        product_indexes = _table_indexes(inspector, "products")
        if "category_id" not in product_columns:
            with op.batch_alter_table("products", schema=None) as batch_op:
                batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_products_category_id_categories", "categories", ["category_id"], ["id"])
                batch_op.create_index("ix_products_category_id_deleted_created", ["category_id", "is_deleted", "created_at"], unique=False)
        elif "ix_products_category_id_deleted_created" not in product_indexes:
            with op.batch_alter_table("products", schema=None) as batch_op:
                batch_op.create_index("ix_products_category_id_deleted_created", ["category_id", "is_deleted", "created_at"], unique=False)

        if "categories" in existing_tables:
            op.execute(
                """
                UPDATE products
                SET category_id = (
                    SELECT categories.id
                    FROM categories
                    WHERE lower(categories.name) = lower(products.category)
                       OR lower(categories.slug) = lower(products.category)
                    ORDER BY categories.id ASC
                    LIMIT 1
                )
                WHERE category_id IS NULL
                  AND category IS NOT NULL
                  AND trim(category) <> ''
                """
            )

        if dialect == "postgresql" and "ix_products_search_fts" not in product_indexes:
            op.execute(
                """
                CREATE INDEX ix_products_search_fts
                ON products
                USING gin (
                    to_tsvector(
                        'simple',
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
                )
                """
            )

    if "order_items" in existing_tables:
        order_item_columns = _table_columns(inspector, "order_items")
        order_item_indexes = _table_indexes(inspector, "order_items")
        if "variant_id" not in order_item_columns:
            with op.batch_alter_table("order_items", schema=None) as batch_op:
                batch_op.add_column(sa.Column("variant_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_order_items_variant_id_product_variants", "product_variants", ["variant_id"], ["id"])
                batch_op.create_index("ix_order_items_variant_order", ["variant_id", "order_id"], unique=False)
        elif "ix_order_items_variant_order" not in order_item_indexes:
            with op.batch_alter_table("order_items", schema=None) as batch_op:
                batch_op.create_index("ix_order_items_variant_order", ["variant_id", "order_id"], unique=False)

        op.execute(
            """
            UPDATE order_items
            SET variant_id = (
                SELECT product_variants.id
                FROM product_variants
                WHERE product_variants.product_id = order_items.product_id
                  AND (
                    COALESCE(order_items.selected_size, '') = ''
                    OR COALESCE(product_variants.size, '') = COALESCE(order_items.selected_size, '')
                  )
                  AND (
                    COALESCE(order_items.selected_color, '') = ''
                    OR COALESCE(product_variants.color, '') = COALESCE(order_items.selected_color, '')
                  )
                ORDER BY product_variants.is_active DESC, product_variants.sort_order ASC, product_variants.id ASC
                LIMIT 1
            )
            WHERE variant_id IS NULL
            """
        )

    if "return_requests" in existing_tables:
        return_columns = _table_columns(inspector, "return_requests")
        return_indexes = _table_indexes(inspector, "return_requests")
        if "order_item_id" not in return_columns:
            with op.batch_alter_table("return_requests", schema=None) as batch_op:
                batch_op.add_column(sa.Column("order_item_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_return_requests_order_item_id_order_items", "order_items", ["order_item_id"], ["id"])
                batch_op.create_index("ix_return_requests_order_item_status", ["order_item_id", "status"], unique=False)
        elif "ix_return_requests_order_item_status" not in return_indexes:
            with op.batch_alter_table("return_requests", schema=None) as batch_op:
                batch_op.create_index("ix_return_requests_order_item_status", ["order_item_id", "status"], unique=False)

        op.execute(
            """
            UPDATE return_requests
            SET order_item_id = (
                SELECT order_items.id
                FROM order_items
                WHERE order_items.order_id = return_requests.order_id
                ORDER BY order_items.id ASC
                LIMIT 1
            )
            WHERE order_item_id IS NULL
              AND (
                SELECT COUNT(*)
                FROM order_items AS order_item_count
                WHERE order_item_count.order_id = return_requests.order_id
              ) = 1
            """
        )

    if "admin_analytics_snapshots" not in existing_tables:
        op.create_table(
            "admin_analytics_snapshots",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("snapshot_key", sa.String(length=120), nullable=False),
            sa.Column("snapshot_group", sa.String(length=80), nullable=False),
            sa.Column("period", sa.String(length=40), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("computed_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("snapshot_key", name="uq_admin_analytics_snapshots_key"),
        )
        with op.batch_alter_table("admin_analytics_snapshots", schema=None) as batch_op:
            batch_op.create_index("ix_admin_analytics_snapshots_group_computed", ["snapshot_group", "computed_at"], unique=False)
            batch_op.create_index("ix_admin_analytics_snapshots_expires", ["expires_at"], unique=False)
            batch_op.create_index("ix_admin_analytics_snapshots_snapshot_key", ["snapshot_key"], unique=False)

    if "payment_reconciliation_runs" not in existing_tables:
        op.create_table(
            "payment_reconciliation_runs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reconciled_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("unmatched_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("stale_pending_orders", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recent_webhook_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("result_json", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("payment_reconciliation_runs", schema=None) as batch_op:
            batch_op.create_index("ix_payment_reconciliation_runs_started", ["started_at"], unique=False)
            batch_op.create_index("ix_payment_reconciliation_runs_status", ["status", "started_at"], unique=False)

    if "retention_job_runs" not in existing_tables:
        op.create_table(
            "retention_job_runs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("target_name", sa.String(length=80), nullable=False),
            sa.Column("cutoff_days", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("archived_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("deleted_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("artifact_path", sa.String(length=500), nullable=True),
            sa.Column("result_json", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("retention_job_runs", schema=None) as batch_op:
            batch_op.create_index("ix_retention_job_runs_status", ["status", "started_at"], unique=False)
            batch_op.create_index("ix_retention_job_runs_target_started", ["target_name", "started_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    dialect = bind.dialect.name

    if dialect == "postgresql" and "products" in existing_tables:
        product_indexes = _table_indexes(inspector, "products")
        if "ix_products_search_fts" in product_indexes:
            op.execute("DROP INDEX ix_products_search_fts")

    if "retention_job_runs" in existing_tables:
        with op.batch_alter_table("retention_job_runs", schema=None) as batch_op:
            batch_op.drop_index("ix_retention_job_runs_target_started")
            batch_op.drop_index("ix_retention_job_runs_status")
        op.drop_table("retention_job_runs")

    if "payment_reconciliation_runs" in existing_tables:
        with op.batch_alter_table("payment_reconciliation_runs", schema=None) as batch_op:
            batch_op.drop_index("ix_payment_reconciliation_runs_status")
            batch_op.drop_index("ix_payment_reconciliation_runs_started")
        op.drop_table("payment_reconciliation_runs")

    if "admin_analytics_snapshots" in existing_tables:
        with op.batch_alter_table("admin_analytics_snapshots", schema=None) as batch_op:
            batch_op.drop_index("ix_admin_analytics_snapshots_snapshot_key")
            batch_op.drop_index("ix_admin_analytics_snapshots_expires")
            batch_op.drop_index("ix_admin_analytics_snapshots_group_computed")
        op.drop_table("admin_analytics_snapshots")

    if "return_requests" in existing_tables and "order_item_id" in _table_columns(inspector, "return_requests"):
        with op.batch_alter_table("return_requests", schema=None) as batch_op:
            if "ix_return_requests_order_item_status" in _table_indexes(inspector, "return_requests"):
                batch_op.drop_index("ix_return_requests_order_item_status")
            batch_op.drop_column("order_item_id")

    if "order_items" in existing_tables and "variant_id" in _table_columns(inspector, "order_items"):
        with op.batch_alter_table("order_items", schema=None) as batch_op:
            if "ix_order_items_variant_order" in _table_indexes(inspector, "order_items"):
                batch_op.drop_index("ix_order_items_variant_order")
            batch_op.drop_column("variant_id")

    if "products" in existing_tables and "category_id" in _table_columns(inspector, "products"):
        with op.batch_alter_table("products", schema=None) as batch_op:
            if "ix_products_category_id_deleted_created" in _table_indexes(inspector, "products"):
                batch_op.drop_index("ix_products_category_id_deleted_created")
            batch_op.drop_column("category_id")

