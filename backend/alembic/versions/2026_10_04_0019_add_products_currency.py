"""add catalog.products.currency column

The ORM declares ``catalog.products.currency`` as ``String(3) NOT NULL DEFAULT 'USD'``
but no migration ever created the column. The baseline ``commerce.products`` table
(created in ``20260806_0003``) omitted it entirely, and the subsequent schema split
(``20260821_split_commerce``) moved the table to ``catalog`` without adding it.

This revision is additive and idempotent: it adds the column with a server-side
default so existing rows receive 'USD' automatically.

Revision ID: 20261004_0019_add_products_currency
Revises: 20261004_0018_add_missing_server_default_now
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261004_0019_add_products_currency"
down_revision: Union[str, None] = "20261004_0018"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.exc import NoInspectionAvailable
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def upgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns("products", schema="catalog")}
    if "currency" not in existing:
        op.add_column(
            "products",
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
            schema="catalog",
        )
        op.create_index(
            "ix_products_currency",
            "products",
            ["currency"],
            unique=False,
            schema="catalog",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns("products", schema="catalog")}
    if "currency" in existing:
        op.drop_index("ix_products_currency", table_name="products", schema="catalog")
        op.drop_column("products", "currency", schema="catalog")
