"""add_missing_country_config_columns

Adds missing columns to country_configs per CTO Master Playbook:
- status: ENUM (draft/active/suspended/archived)
- is_default: BOOLEAN
- data_residency_tier: ENUM (standard/strict)
- supported_languages_json: TEXT (JSONB)
- payout_methods_json: TEXT (JSONB)
- logistics_zones_json: TEXT (JSONB)
- created_by: INTEGER FK -> users.id
- updated_by: INTEGER FK -> users.id
- active_version_id: INTEGER FK -> country_config_versions.id

Also adds tax_name column to country_category_tax_rates.

Revision ID: 20915daf9b29
Revises: n5o6p7q8r9s0
Create Date: 2026-06-24 09:04:58.223770

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20915daf9b29"
down_revision: Union[str, Sequence[str], None] = "n5o6p7q8r9s0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ── 1. country_configs: Missing columns ─────────────────────────────────
    if not _has_column("country_configs", "status"):
        op.add_column("country_configs",
            sa.Column("status", sa.String(20), nullable=False, server_default="active",
                      comment="draft|active|suspended|archived"))

    if not _has_column("country_configs", "is_default"):
        op.add_column("country_configs",
            sa.Column("is_default", sa.Boolean, nullable=False, server_default="0"))

    if not _has_column("country_configs", "data_residency_tier"):
        op.add_column("country_configs",
            sa.Column("data_residency_tier", sa.String(10), nullable=False, server_default="standard",
                      comment="standard|strict"))

    if not _has_column("country_configs", "supported_languages_json"):
        op.add_column("country_configs",
            sa.Column("supported_languages_json", sa.Text, nullable=True,
                      comment="JSON array of language codes"))

    if not _has_column("country_configs", "payout_methods_json"):
        op.add_column("country_configs",
            sa.Column("payout_methods_json", sa.Text, nullable=True,
                      comment="JSON array of payout method configs"))

    if not _has_column("country_configs", "logistics_zones_json"):
        op.add_column("country_configs",
            sa.Column("logistics_zones_json", sa.Text, nullable=True,
                      comment="JSON array of logistics zone configs"))

    if not _has_column("country_configs", "created_by"):
        op.add_column("country_configs",
            sa.Column("created_by", sa.Integer, nullable=True))

    if not _has_column("country_configs", "updated_by"):
        op.add_column("country_configs",
            sa.Column("updated_by", sa.Integer, nullable=True))

    if not _has_column("country_configs", "active_version_id"):
        op.add_column("country_configs",
            sa.Column("active_version_id", sa.Integer, nullable=True))

    # Add FK constraints for created_by, updated_by, active_version_id
    try:
        op.create_foreign_key(
            "fk_country_configs_created_by", "country_configs", "users",
            ["created_by"], ["id"], ondelete="SET NULL"
        )
    except Exception:
        pass

    try:
        op.create_foreign_key(
            "fk_country_configs_updated_by", "country_configs", "users",
            ["updated_by"], ["id"], ondelete="SET NULL"
        )
    except Exception:
        pass

    try:
        op.create_foreign_key(
            "fk_country_configs_active_version", "country_configs", "country_config_versions",
            ["active_version_id"], ["id"], ondelete="SET NULL"
        )
    except Exception:
        pass

    # Add indexes
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("country_configs")}
    if "ix_country_configs_status" not in existing_indexes:
        op.create_index("ix_country_configs_status", "country_configs", ["status"])
    if "ix_country_configs_is_default" not in existing_indexes:
        op.create_index("ix_country_configs_is_default", "country_configs", ["is_default"])
    if "ix_country_configs_active_version" not in existing_indexes:
        op.create_index("ix_country_configs_active_version", "country_configs", ["active_version_id"])

    # ── 2. country_category_tax_rates: Add tax_name column ──────────────────
    if not _has_column("country_category_tax_rates", "tax_name"):
        op.add_column("country_category_tax_rates",
            sa.Column("tax_name", sa.String(50), nullable=True))

    # ── 3. country_cities: Add name_ar and status columns ───────────────────
    if not _has_column("country_cities", "name_ar"):
        op.add_column("country_cities",
            sa.Column("name_ar", sa.String(200), nullable=True,
                      comment="City name in Arabic"))

    # The model uses is_active BOOLEAN, playbook says status ENUM.
    # Keep is_active for now, add status as alias column if needed later.


def downgrade() -> None:
    # country_configs
    for col in (
        "status", "is_default", "data_residency_tier", "supported_languages_json",
        "payout_methods_json", "logistics_zones_json", "created_by", "updated_by",
        "active_version_id",
    ):
        if _has_column("country_configs", col):
            op.drop_column("country_configs", col)

    # Drop FK constraints (will fail silently if not exist)
    for fk in ("fk_country_configs_created_by", "fk_country_configs_updated_by", "fk_country_configs_active_version"):
        try:
            op.drop_constraint(fk, "country_configs", type_="foreignkey")
        except Exception:
            pass

    # Indexes
    for idx in ("ix_country_configs_status", "ix_country_configs_is_default", "ix_country_configs_active_version"):
        try:
            op.drop_index(idx, table_name="country_configs")
        except Exception:
            pass

    # country_category_tax_rates
    if _has_column("country_category_tax_rates", "tax_name"):
        op.drop_column("country_category_tax_rates", "tax_name")

    # country_cities
    if _has_column("country_cities", "name_ar"):
        op.drop_column("country_cities", "name_ar")

