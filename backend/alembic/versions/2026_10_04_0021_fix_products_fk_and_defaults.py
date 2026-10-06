"""fix catalog.products FK constraints and column defaults

The baseline ``commerce.products`` table (``20260806_0003``) was created without
foreign-key constraints on ``category_id``, ``supplier_id`` or ``country_code``,
and with ``is_deleted`` / ``created_at`` / ``updated_at`` columns that do not
match the current ORM contract.

After the schema split (``20260821_split_commerce``) the table lives in
``catalog.products`` and still carries the old definitions.  This revision
aligns it with the ORM:

  - ``category_id``   → FK ``catalog.categories(id) ON DELETE RESTRICT``
  - ``supplier_id``   → FK ``accounts.users(id) ON DELETE SET NULL``
  - ``country_code``  → FK ``country.country_configs(code) ON DELETE RESTRICT``,
                         type shrunk from String(3) to String(2)
  - ``is_deleted``    → Boolean NOT NULL DEFAULT false, indexed
  - ``created_at``    → DateTime NOT NULL DEFAULT now()
  - ``updated_at``    → DateTime DEFAULT now()

Idempotent: every step inspects the live catalog first.

Revision ID: 20261004_0021_fix_products_fk_and_defaults
Revises: 20261004_0020_create_mfa_factors_and_align_secret
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20261004_0021_fix_products_fk_and_defaults"
down_revision: Union[str, None] = "20261004_0020_create_mfa_factors_and_align_secret"
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


def _has_constraint(bind, table: str, constraint_name: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    try:
        constraints = inspector.get_foreign_keys(table, schema=schema)
        return any(c["name"] == constraint_name for c in constraints)
    except sa.exc.NoSuchTableError:
        return False


def _has_index(bind, table: str, index_name: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    try:
        indexes = inspector.get_indexes(table, schema=schema)
        return any(ix["name"] == index_name for ix in indexes)
    except sa.exc.NoSuchTableError:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    columns = {c["name"]: c for c in inspector.get_columns("products", schema="catalog")}

    # 1. shrink country_code from String(3) -> String(2) before adding FK
    if "country_code" in columns:
        col = columns["country_code"]
        current_type = str(col.get("type", ""))
        if "VARCHAR(3)" in current_type.upper() or "CHARACTER VARYING(3)" in current_type.upper():
            with op.batch_alter_table("products", schema="catalog") as batch_op:
                batch_op.alter_column(
                    "country_code",
                    existing_type=sa.String(length=3),
                    type_=sa.String(length=2),
                    existing_nullable=True,
                    nullable=True,
                )

    # 2. add FK constraints
    if not _has_constraint(bind, "products", "fk_products_category", "catalog"):
        op.create_foreign_key(
            "fk_products_category",
            "products",
            "categories",
            ["category_id"],
            ["id"],
            source_schema="catalog",
            referent_schema="catalog",
            ondelete="RESTRICT",
        )

    if not _has_constraint(bind, "products", "fk_products_supplier", "catalog"):
        op.create_foreign_key(
            "fk_products_supplier",
            "products",
            "users",
            ["supplier_id"],
            ["id"],
            source_schema="catalog",
            referent_schema="accounts",
            ondelete="SET NULL",
        )

    if not _has_constraint(bind, "products", "fk_products_country", "catalog"):
        op.create_foreign_key(
            "fk_products_country",
            "products",
            "country_configs",
            ["country_code"],
            ["code"],
            source_schema="catalog",
            referent_schema="country",
            ondelete="RESTRICT",
        )

    # 3. fix is_deleted: nullable=False, default false, indexed
    if "is_deleted" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "is_deleted",
                existing_type=sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        if not _has_index(bind, "products", "ix_products_is_deleted", "catalog"):
            op.create_index("ix_products_is_deleted", "products", ["is_deleted"], unique=False, schema="catalog")

    # 4. fix created_at: NOT NULL DEFAULT now()
    if "created_at" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            )

    # 5. fix updated_at: nullable=True DEFAULT now()
    if "updated_at" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=sa.func.now(),
            )


def downgrade() -> None:
    bind = op.get_bind()
    if _is_offline(bind):
        return
    if bind.dialect.name == "sqlite":
        return

    inspector = sa.inspect(bind)
    columns = {c["name"]: c for c in inspector.get_columns("products", schema="catalog")}

    # reverse defaults
    if "created_at" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=None,
            )

    if "updated_at" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=None,
            )

    if "is_deleted" in columns:
        op.drop_index("ix_products_is_deleted", table_name="products", schema="catalog")
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "is_deleted",
                existing_type=sa.Boolean(),
                nullable=True,
                server_default=None,
            )

    # drop FK constraints
    for constraint_name in ("fk_products_country", "fk_products_supplier", "fk_products_category"):
        try:
            op.drop_constraint(constraint_name, "products", type_="foreignkey", schema="catalog")
        except Exception:
            pass

    # restore country_code type
    if "country_code" in columns:
        with op.batch_alter_table("products", schema="catalog") as batch_op:
            batch_op.alter_column(
                "country_code",
                existing_type=sa.String(length=2),
                type_=sa.String(length=3),
                existing_nullable=True,
                nullable=True,
            )
