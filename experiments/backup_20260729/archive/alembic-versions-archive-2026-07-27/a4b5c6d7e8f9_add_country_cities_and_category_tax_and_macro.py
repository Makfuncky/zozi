"""add_country_cities_and_category_tax_and_macro

Revision ID: a4b5c6d7e8f9
Revises: c2d3e4f5a6b7, d0e1f2a3b4c5, u4v5w6x7y8z9
Create Date: 2026-06-23 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union
from decimal import Decimal

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text as sa_text

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = (
    "c2d3e4f5a6b7",
    "d0e1f2a3b4c5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # ── 1. Create country_cities table ────────────────────────────────────
    if "country_cities" not in existing_tables:
        op.create_table(
            "country_cities",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("region", sa.String(length=120), nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("population", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source", sa.String(length=24), nullable=False, server_default="manual"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("country_code", "name", name="uq_country_cities_code_name"),
        )
        op.create_index("ix_country_cities_code_name", "country_cities", ["country_code", "name"])
        op.create_index("ix_country_cities_code_active", "country_cities", ["country_code", "is_active"])
        op.create_index("ix_country_cities_country_code", "country_cities", ["country_code"])

    # ── 2. Create country_category_tax_rates table ────────────────────────
    if "country_category_tax_rates" not in existing_tables:
        op.create_table(
            "country_category_tax_rates",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("category_slug", sa.String(length=60), nullable=False),
            sa.Column("rate", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
            sa.Column("is_exempt", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_reduced", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("source", sa.String(length=24), nullable=False, server_default="curated"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "country_code", "category_slug",
                name="uq_country_cat_tax_code_slug",
            ),
            sa.CheckConstraint(
                "rate >= 0 AND rate <= 1",
                name="ck_country_cat_tax_rate_valid",
            ),
        )
        op.create_index("ix_country_cat_tax_code_slug", "country_category_tax_rates", ["country_code", "category_slug"])
        op.create_index("ix_country_cat_tax_country_code", "country_category_tax_rates", ["country_code"])

    # ── 3. Add macro columns to country_configs ───────────────────────────
    macro_columns = [
        ("population", "INTEGER"),
        ("internet_penetration_pct", "NUMERIC(5, 2)"),
        ("gdp_per_capita_usd", "NUMERIC(12, 2)"),
        ("urbanization_pct", "NUMERIC(5, 2)"),
        ("mobile_subs_per_100", "NUMERIC(5, 2)"),
        ("public_holidays_json", "TEXT"),
        ("macro_indicators_json", "TEXT"),
    ]
    for col_name, col_type in macro_columns:
        if not _column_exists("country_configs", col_name):
            op.add_column("country_configs", sa.Column(col_name, sa.Text() if "json" in col_name else sa.Numeric(), nullable=True))

    # ── 4. Backfill country_cities from regions_json + CITY_SUGGESTIONS ──
    from data.vat_rates import CITY_SUGGESTIONS

    cities_backfill_sql = sa_text(
        """
        INSERT INTO country_cities (country_code, name, region, source, is_active, sort_order)
        SELECT :code, :name, :region, 'manual', 1, 0
        WHERE NOT EXISTS (
            SELECT 1 FROM country_cities
            WHERE country_code = :code AND name = :name
        )
        """
    )
    for code, cities in CITY_SUGGESTIONS.items():
        for city_name in cities:
            bind.execute(cities_backfill_sql, {"code": code, "name": city_name, "region": None})

    # ── 5. Backfill country_category_tax_rates from profiles ──────────────
    from data.category_tax_profiles import get_category_tax_profile
    from models import CountryConfig

    try:
        rows = bind.execute(sa_text("SELECT code, name FROM country_configs")).fetchall()
    except Exception:
        rows = []

    for row in rows:
        code = row[0]
        try:
            profile = get_category_tax_profile(code, None, None)
        except Exception:
            profile = []
        for entry in profile:
            tax_insert_sql = sa_text(
                """
                INSERT INTO country_category_tax_rates
                    (country_code, category_slug, rate, is_exempt, is_reduced, notes, source)
                SELECT :code, :slug, :rate, :exempt, :reduced, :notes, 'curated'
                WHERE NOT EXISTS (
                    SELECT 1 FROM country_category_tax_rates
                    WHERE country_code = :code AND category_slug = :slug
                )
                """
            )
            bind.execute(tax_insert_sql, {
                "code": code,
                "slug": entry["category_slug"],
                "rate": Decimal(str(entry["rate"])),
                "exempt": entry["is_exempt"],
                "reduced": entry["is_reduced"],
                "notes": entry.get("notes", ""),
            })


def downgrade() -> None:
    if op.get_bind().dialect.has_table(op.get_bind(), "country_category_tax_rates"):
        op.drop_index("ix_country_cat_tax_country_code", table_name="country_category_tax_rates")
        op.drop_index("ix_country_cat_tax_code_slug", table_name="country_category_tax_rates")
        op.drop_table("country_category_tax_rates")

    if op.get_bind().dialect.has_table(op.get_bind(), "country_cities"):
        op.drop_index("ix_country_cities_country_code", table_name="country_cities")
        op.drop_index("ix_country_cities_code_active", table_name="country_cities")
        op.drop_index("ix_country_cities_code_name", table_name="country_cities")
        op.drop_table("country_cities")

    macro_columns = [
        "population", "internet_penetration_pct", "gdp_per_capita_usd",
        "urbanization_pct", "mobile_subs_per_100",
        "public_holidays_json", "macro_indicators_json",
    ]
    for col_name in macro_columns:
        if _column_exists("country_configs", col_name):
            op.drop_column("country_configs", col_name)

