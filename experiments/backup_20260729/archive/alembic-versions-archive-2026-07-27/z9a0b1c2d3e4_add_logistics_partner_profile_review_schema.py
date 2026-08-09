"""Add logistics partner profile review fields and service area table.

Revision ID: z9a0b1c2d3e4
Revises: d3ec18c6ac15
Create Date: 2026-04-02 16:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'z9a0b1c2d3e4'
down_revision = "d3ec18c6ac15"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    if not _table_exists(inspector, table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    if not _table_exists(inspector, table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    logistics_partner_columns = _column_names(inspector, "logistics_partners")
    if logistics_partner_columns:
        partner_columns_to_add = [
            ("business_type", sa.String(length=50), True),
            ("country", sa.String(length=100), True),
            ("region", sa.String(length=100), True),
            ("city", sa.String(length=100), True),
            ("address", sa.Text(), True),
            ("postal_code", sa.String(length=40), True),
            ("tax_id", sa.String(length=120), True),
            ("bio", sa.Text(), True),
            ("about_us", sa.Text(), True),
            ("logo_url", sa.String(length=500), True),
            ("banner_url", sa.String(length=500), True),
            ("latitude", sa.Float(), True),
            ("longitude", sa.Float(), True),
            ("social_links", sa.Text(), True),
            ("is_terms_accepted", sa.Boolean(), True),
            ("terms_version", sa.String(length=30), True),
            ("terms_accepted_at", sa.DateTime(), True),
            ("verification_status", sa.String(length=30), True),
            ("verification_note", sa.Text(), True),
            ("verified_at", sa.DateTime(), True),
            ("verified_by", sa.Integer(), True),
        ]
        for name, column_type, nullable in partner_columns_to_add:
            if name in logistics_partner_columns:
                continue
            if name == "is_terms_accepted":
                op.add_column(
                    "logistics_partners",
                    sa.Column(name, column_type, nullable=nullable, server_default=sa.false()),
                )
            elif name == "verification_status":
                op.add_column(
                    "logistics_partners",
                    sa.Column(name, column_type, nullable=nullable, server_default="pending"),
                )
            else:
                op.add_column("logistics_partners", sa.Column(name, column_type, nullable=nullable))

        partner_indexes = _index_names(inspector, "logistics_partners")
        if "ix_logistics_partners_verification_status" not in partner_indexes:
            op.create_index("ix_logistics_partners_verification_status", "logistics_partners", ["verification_status"], unique=False)

    if not _table_exists(inspector, "logistics_partner_service_areas"):
        op.create_table(
            "logistics_partner_service_areas",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("partner_id", sa.Integer(), nullable=False),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("country_name", sa.String(length=120), nullable=False),
            sa.Column("city_name", sa.String(length=120), nullable=True),
            sa.Column("zone_label", sa.String(length=120), nullable=True),
            sa.Column("charge_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="AED"),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("delivery_days_min", sa.Integer(), nullable=True),
            sa.Column("delivery_days_max", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column("approval_status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("charge_amount >= 0", name="ck_lp_service_areas_charge_nonnegative"),
            sa.CheckConstraint(
                "delivery_days_min IS NULL OR delivery_days_min >= 0",
                name="ck_lp_service_areas_days_min_nonnegative",
            ),
            sa.CheckConstraint(
                "delivery_days_max IS NULL OR delivery_days_max >= 0",
                name="ck_lp_service_areas_days_max_nonnegative",
            ),
            sa.CheckConstraint(
                "delivery_days_min IS NULL OR delivery_days_max IS NULL OR delivery_days_min <= delivery_days_max",
                name="ck_lp_service_areas_days_min_le_max",
            ),
            sa.ForeignKeyConstraint(["partner_id"], ["logistics_partners.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("logistics_partner_service_areas", schema=None) as batch_op:
            batch_op.create_index("ix_logistics_partner_service_areas_id", ["id"], unique=False)
            batch_op.create_index("ix_logistics_partner_service_areas_partner_id", ["partner_id"], unique=False)
            batch_op.create_index("ix_logistics_partner_service_areas_country_code", ["country_code"], unique=False)
            batch_op.create_index("ix_logistics_partner_service_areas_city_name", ["city_name"], unique=False)
            batch_op.create_index("ix_lp_service_areas_partner_status", ["partner_id", "approval_status"], unique=False)
            batch_op.create_index("ix_lp_service_areas_destination", ["country_code", "city_name", "approval_status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "logistics_partner_service_areas"):
        with op.batch_alter_table("logistics_partner_service_areas", schema=None) as batch_op:
            for index_name in [
                "ix_lp_service_areas_destination",
                "ix_lp_service_areas_partner_status",
                "ix_logistics_partner_service_areas_city_name",
                "ix_logistics_partner_service_areas_country_code",
                "ix_logistics_partner_service_areas_partner_id",
                "ix_logistics_partner_service_areas_id",
            ]:
                try:
                    batch_op.drop_index(index_name)
                except Exception:
                    pass
        op.drop_table("logistics_partner_service_areas")

    logistics_partner_columns = _column_names(inspector, "logistics_partners")
    if logistics_partner_columns:
        with op.batch_alter_table("logistics_partners", schema=None) as batch_op:
            if "ix_logistics_partners_verification_status" in _index_names(inspector, "logistics_partners"):
                batch_op.drop_index("ix_logistics_partners_verification_status")
            for column_name in [
                "verified_by",
                "verified_at",
                "verification_note",
                "verification_status",
                "terms_accepted_at",
                "terms_version",
                "is_terms_accepted",
                "social_links",
                "longitude",
                "latitude",
                "banner_url",
                "logo_url",
                "about_us",
                "bio",
                "tax_id",
                "postal_code",
                "address",
                "city",
                "region",
                "country",
                "business_type",
            ]:
                if column_name in logistics_partner_columns:
                    batch_op.drop_column(column_name)

