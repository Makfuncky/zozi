"""add_soft_delete_columns_to_all_entities

Revision ID: zc1d2e3f4a5
Revises: zb1c2d3e4f5
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as _inspect

revision: str = "zc1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "zb1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_tables_cache: set[str] | None = None

def _has_table(table: str, bind) -> bool:
    global _tables_cache
    if _tables_cache is None:
        _tables_cache = set(_inspect(bind).get_table_names())
    return table in _tables_cache

def _column_names(table: str) -> set[str]:
    return {c["name"] for c in _inspect(op.get_bind()).get_columns(table)}

def _add_soft_delete_columns(table: str) -> None:
    cols = _column_names(table)
    with op.batch_alter_table(table) as batch_op:
        if "is_deleted" not in cols:
            batch_op.add_column(sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        if "deleted_at" not in cols:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        if "deleted_by" not in cols:
            batch_op.add_column(sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("users.id", name=f"fk_{table}_softdel_deleted_by"), nullable=True))
        if "restore_at" not in cols:
            batch_op.add_column(sa.Column("restore_at", sa.DateTime(), nullable=True))
        if "restore_by" not in cols:
            batch_op.add_column(sa.Column("restore_by", sa.Integer(), sa.ForeignKey("users.id", name=f"fk_{table}_softdel_restore_by"), nullable=True))
        if "deletion_reason" not in cols:
            batch_op.add_column(sa.Column("deletion_reason", sa.Text(), nullable=True))
        if f"ix_{table}_deleted_at" not in {i["name"] for i in _inspect(op.get_bind()).get_indexes(table)}:
            batch_op.create_index(f"ix_{table}_deleted_at", ["is_deleted", "deleted_at"])
        if f"ix_{table}_deleted_by" not in {i["name"] for i in _inspect(op.get_bind()).get_indexes(table)}:
            batch_op.create_index(f"ix_{table}_deleted_by", ["deleted_by"])

def _drop_soft_delete_columns(table: str) -> None:
    with op.batch_alter_table(table) as batch_op:
        batch_op.drop_index(f"ix_{table}_deleted_at")
        batch_op.drop_index(f"ix_{table}_deleted_by")
        batch_op.drop_column("deletion_reason")
        batch_op.drop_column("restore_by")
        batch_op.drop_column("restore_at")
        batch_op.drop_column("deleted_by")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("is_deleted")

def upgrade() -> None:
    bind = op.get_bind()
    tables = [
        "users", "products", "orders", "categories", "supplier_profiles",
        "logistics_partners", "country_configs", "payouts",
        "logistics_partner_payouts", "coupons", "banners", "flash_sales",
        "promotion_engine_configs", "promotion_order_tiers",
        "support_tickets", "return_requests", "supplier_disputes",
        "invoices", "supplier_documents", "logistics_partner_documents",
        "shipments", "reviews",
    ]
    for t in tables:
        if _has_table(t, bind):
            _add_soft_delete_columns(t)

def downgrade() -> None:
    bind = op.get_bind()
    tables = [
        "users", "products", "orders", "categories", "supplier_profiles",
        "logistics_partners", "country_configs", "payouts",
        "logistics_partner_payouts", "coupons", "banners", "flash_sales",
        "promotion_engine_configs", "promotion_order_tiers",
        "support_tickets", "return_requests", "supplier_disputes",
        "invoices", "supplier_documents", "logistics_partner_documents",
        "shipments", "reviews",
    ]
    for t in tables:
        if _has_table(t, bind):
            _drop_soft_delete_columns(t)

