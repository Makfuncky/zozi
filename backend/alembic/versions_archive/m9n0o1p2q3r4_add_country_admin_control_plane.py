"""add_country_admin_control_plane

Revision ID: m9n0o1p2q3r4
Revises: z0y1x2w3v4u5
Create Date: 2026-05-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "m9n0o1p2q3r4"
down_revision: Union[str, Sequence[str], None] = "z0y1x2w3v4u5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COUNTRY_CP_TABLES = (
    "country_configs",
    "supplier_country_commissions",
    "oman_delivery_zones",
    "country_feature_flags",
    "country_config_versions",
    "admin_change_audit_logs",
)


def _seed_if_missing(bind) -> None:
    country_rows = [
        {
            "code": "OM",
            "name": "Oman",
            "currency": "OMR",
            "timezone": "Asia/Muscat",
            "tax_type": "VAT",
            "tax_rate": 0.0500,
            "tax_name": "VAT (5%)",
            "tax_inclusive": 0,
            "tax_exempt_categories_json": '["health-medicine","education"]',
            "tax_reduced_rates_json": "{}",
            "logistics_model": "fixed",
            "default_vehicle_type": "car",
            "base_rate": None,
            "per_km_rate": None,
            "minimum_charge": None,
            "weight_surcharge_rate": 0.500,
            "weight_surcharge_threshold_kg": 10.0,
            "payment_methods_json": '["tap","stripe","cod"]',
            "is_active": 1,
        },
        {
            "code": "PK",
            "name": "Pakistan",
            "currency": "PKR",
            "timezone": "Asia/Karachi",
            "tax_type": "GST",
            "tax_rate": 0.1700,
            "tax_name": "GST (17%)",
            "tax_inclusive": 0,
            "tax_exempt_categories_json": "[]",
            "tax_reduced_rates_json": '{"grocery":0.05,"baby-kids":0.05,"health-medicine":0.05}',
            "logistics_model": "per_km",
            "default_vehicle_type": "bike",
            "base_rate": 50.00,
            "per_km_rate": 15.0000,
            "minimum_charge": 100.00,
            "weight_surcharge_rate": 5.00,
            "weight_surcharge_threshold_kg": 5.0,
            "payment_methods_json": '["jazzcash","easypaisa","bank_transfer","cod"]',
            "is_active": 1,
        },
    ]

    country_insert_sql = sa.text(
        """
        INSERT INTO country_configs (
            code, name, currency, timezone, tax_type, tax_rate, tax_name, tax_inclusive,
            tax_exempt_categories_json, tax_reduced_rates_json,
            logistics_model, default_vehicle_type, base_rate, per_km_rate, minimum_charge,
            weight_surcharge_rate, weight_surcharge_threshold_kg,
            payment_methods_json, is_active
        )
        SELECT
            :code, :name, :currency, :timezone, :tax_type, :tax_rate, :tax_name, :tax_inclusive,
            :tax_exempt_categories_json, :tax_reduced_rates_json,
            :logistics_model, :default_vehicle_type, :base_rate, :per_km_rate, :minimum_charge,
            :weight_surcharge_rate, :weight_surcharge_threshold_kg,
            :payment_methods_json, :is_active
        WHERE NOT EXISTS (
            SELECT 1 FROM country_configs WHERE code = :code
        )
        """
    )
    for row in country_rows:
        bind.execute(country_insert_sql, row)

    commission_rows = [
        {"country_code": "PK", "category_slug": "electronics", "commission_rate": 0.1200, "is_active": 1},
        {"country_code": "PK", "category_slug": "fashion", "commission_rate": 0.1800, "is_active": 1},
        {"country_code": "PK", "category_slug": "grocery", "commission_rate": 0.1000, "is_active": 1},
        {"country_code": "PK", "category_slug": "home-living", "commission_rate": 0.1500, "is_active": 1},
        {"country_code": "OM", "category_slug": "electronics", "commission_rate": 0.1000, "is_active": 1},
        {"country_code": "OM", "category_slug": "fashion", "commission_rate": 0.1500, "is_active": 1},
        {"country_code": "OM", "category_slug": "grocery", "commission_rate": 0.0800, "is_active": 1},
        {"country_code": "OM", "category_slug": "home-living", "commission_rate": 0.1200, "is_active": 1},
    ]
    commission_insert_sql = sa.text(
        """
        INSERT INTO supplier_country_commissions (country_code, category_slug, commission_rate, is_active)
        SELECT :country_code, :category_slug, :commission_rate, :is_active
        WHERE NOT EXISTS (
            SELECT 1 FROM supplier_country_commissions
            WHERE country_code = :country_code AND category_slug = :category_slug
        )
        """
    )
    for row in commission_rows:
        bind.execute(commission_insert_sql, row)

    zone_rows = [
        {
            "zone_code": "ZONE_1",
            "zone_name": "Muscat In-City",
            "description": "In-city Muscat deliveries",
            "car_rate": 2.000,
            "van_rate": 3.000,
            "truck_rate": 5.000,
            "weight_surcharge_rate": 0.500,
            "weight_surcharge_threshold_kg": 10.0,
            "cities_json": '["Muscat","Mutrah","Ruwi","Al Khuwair"]',
            "is_active": 1,
            "sort_order": 1,
        },
        {
            "zone_code": "ZONE_2",
            "zone_name": "Inter-City",
            "description": "Mainland Oman inter-city deliveries",
            "car_rate": 3.500,
            "van_rate": 4.500,
            "truck_rate": 7.000,
            "weight_surcharge_rate": 0.500,
            "weight_surcharge_threshold_kg": 10.0,
            "cities_json": '["Sohar","Nizwa","Sur","Salalah","Al Buraymi","Al Seeb"]',
            "is_active": 1,
            "sort_order": 2,
        },
        {
            "zone_code": "ZONE_3",
            "zone_name": "Remote",
            "description": "Remote governorates and islands",
            "car_rate": 5.000,
            "van_rate": 6.000,
            "truck_rate": 10.000,
            "weight_surcharge_rate": 0.500,
            "weight_surcharge_threshold_kg": 10.0,
            "cities_json": '["Duqm","Haima","Masirah Island","Musandam"]',
            "is_active": 1,
            "sort_order": 3,
        },
    ]
    zone_insert_sql = sa.text(
        """
        INSERT INTO oman_delivery_zones (
            zone_code, zone_name, description, car_rate, van_rate, truck_rate,
            weight_surcharge_rate, weight_surcharge_threshold_kg, cities_json, is_active, sort_order
        )
        SELECT
            :zone_code, :zone_name, :description, :car_rate, :van_rate, :truck_rate,
            :weight_surcharge_rate, :weight_surcharge_threshold_kg, :cities_json, :is_active, :sort_order
        WHERE NOT EXISTS (
            SELECT 1 FROM oman_delivery_zones WHERE zone_code = :zone_code
        )
        """
    )
    for row in zone_rows:
        bind.execute(zone_insert_sql, row)

    flag_rows = [
        {"country_code": "PK", "feature_key": "checkout_enabled", "is_enabled": 1, "rollout_audience": "all"},
        {"country_code": "PK", "feature_key": "country_selector_enabled", "is_enabled": 1, "rollout_audience": "all"},
        {"country_code": "OM", "feature_key": "checkout_enabled", "is_enabled": 1, "rollout_audience": "all"},
        {"country_code": "OM", "feature_key": "country_selector_enabled", "is_enabled": 1, "rollout_audience": "all"},
    ]
    flag_insert_sql = sa.text(
        """
        INSERT INTO country_feature_flags (country_code, feature_key, is_enabled, rollout_audience)
        SELECT :country_code, :feature_key, :is_enabled, :rollout_audience
        WHERE NOT EXISTS (
            SELECT 1 FROM country_feature_flags
            WHERE country_code = :country_code AND feature_key = :feature_key
        )
        """
    )
    for row in flag_rows:
        bind.execute(flag_insert_sql, row)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if all(inspector.has_table(name) for name in _COUNTRY_CP_TABLES):
        _seed_if_missing(bind)
        return

    op.create_table(
        "country_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="OMR"),
        sa.Column("timezone", sa.String(length=60), nullable=False, server_default="UTC"),
        sa.Column("tax_type", sa.String(length=20), nullable=False, server_default="VAT"),
        sa.Column("tax_rate", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0"),
        sa.Column("tax_name", sa.String(length=50), nullable=False, server_default="Tax"),
        sa.Column("tax_inclusive", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_exempt_categories_json", sa.Text(), nullable=True),
        sa.Column("tax_reduced_rates_json", sa.Text(), nullable=True),
        sa.Column("logistics_model", sa.String(length=20), nullable=False, server_default="fixed"),
        sa.Column("default_vehicle_type", sa.String(length=30), nullable=True),
        sa.Column("base_rate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("per_km_rate", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("minimum_charge", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("weight_surcharge_rate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("weight_surcharge_threshold_kg", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("payment_methods_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_country_configs_code"),
        sa.CheckConstraint("tax_rate >= 0 AND tax_rate <= 1", name="ck_country_configs_tax_rate_valid"),
        sa.CheckConstraint("base_rate IS NULL OR base_rate >= 0", name="ck_country_configs_base_rate_nonneg"),
        sa.CheckConstraint("per_km_rate IS NULL OR per_km_rate >= 0", name="ck_country_configs_per_km_nonneg"),
        sa.CheckConstraint("minimum_charge IS NULL OR minimum_charge >= 0", name="ck_country_configs_min_charge_nonneg"),
        sa.CheckConstraint("weight_surcharge_rate IS NULL OR weight_surcharge_rate >= 0", name="ck_country_configs_weight_rate_nonneg"),
        sa.CheckConstraint(
            "weight_surcharge_threshold_kg IS NULL OR weight_surcharge_threshold_kg >= 0",
            name="ck_country_configs_weight_threshold_nonneg",
        ),
    )
    op.create_index("ix_country_configs_id", "country_configs", ["id"], unique=False)
    op.create_index("ix_country_configs_code", "country_configs", ["code"], unique=True)
    op.create_index("ix_country_configs_active_code", "country_configs", ["is_active", "code"], unique=False)

    op.create_table(
        "supplier_country_commissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=10), nullable=False),
        sa.Column("category_slug", sa.String(length=60), nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", "category_slug", name="uq_supplier_country_commissions_country_category"),
        sa.CheckConstraint("commission_rate >= 0 AND commission_rate <= 1", name="ck_supplier_country_commission_rate_valid"),
    )
    op.create_index("ix_supplier_country_commissions_id", "supplier_country_commissions", ["id"], unique=False)
    op.create_index("ix_supplier_country_commissions_country_code", "supplier_country_commissions", ["country_code"], unique=False)
    op.create_index("ix_supplier_country_commissions_category_slug", "supplier_country_commissions", ["category_slug"], unique=False)
    op.create_index("ix_supplier_country_commissions_country_active", "supplier_country_commissions", ["country_code", "is_active"], unique=False)

    op.create_table(
        "oman_delivery_zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_code", sa.String(length=20), nullable=False),
        sa.Column("zone_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("car_rate", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("van_rate", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0"),
        sa.Column("truck_rate", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0"),
        sa.Column("weight_surcharge_rate", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("weight_surcharge_threshold_kg", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("cities_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zone_code", name="uq_oman_delivery_zones_code"),
        sa.CheckConstraint("car_rate >= 0", name="ck_oman_delivery_zones_car_nonneg"),
        sa.CheckConstraint("van_rate >= 0", name="ck_oman_delivery_zones_van_nonneg"),
        sa.CheckConstraint("truck_rate >= 0", name="ck_oman_delivery_zones_truck_nonneg"),
        sa.CheckConstraint("weight_surcharge_rate IS NULL OR weight_surcharge_rate >= 0", name="ck_oman_delivery_zones_weight_rate_nonneg"),
    )
    op.create_index("ix_oman_delivery_zones_id", "oman_delivery_zones", ["id"], unique=False)
    op.create_index("ix_oman_delivery_zones_zone_code", "oman_delivery_zones", ["zone_code"], unique=True)
    op.create_index("ix_oman_delivery_zones_active_order", "oman_delivery_zones", ["is_active", "sort_order"], unique=False)

    op.create_table(
        "country_feature_flags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=10), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("rollout_audience", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", "feature_key", name="uq_country_feature_flags_country_feature"),
    )
    op.create_index("ix_country_feature_flags_id", "country_feature_flags", ["id"], unique=False)
    op.create_index("ix_country_feature_flags_country_code", "country_feature_flags", ["country_code"], unique=False)
    op.create_index("ix_country_feature_flags_feature_key", "country_feature_flags", ["feature_key"], unique=False)
    op.create_index("ix_country_feature_flags_country_enabled", "country_feature_flags", ["country_code", "is_enabled"], unique=False)

    op.create_table(
        "country_config_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=10), nullable=False),
        sa.Column("config_type", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("draft_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"]),
        sa.ForeignKeyConstraint(["draft_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", "config_type", "version", name="uq_country_config_versions_triplet"),
    )
    op.create_index("ix_country_config_versions_id", "country_config_versions", ["id"], unique=False)
    op.create_index("ix_country_config_versions_country_code", "country_config_versions", ["country_code"], unique=False)
    op.create_index("ix_country_config_versions_country_type", "country_config_versions", ["country_code", "config_type"], unique=False)
    op.create_index("ix_country_config_versions_status_created", "country_config_versions", ["status", "created_at"], unique=False)

    op.create_table(
        "admin_change_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("entity", sa.String(length=60), nullable=False),
        sa.Column("entity_key", sa.String(length=120), nullable=True),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_change_audit_logs_id", "admin_change_audit_logs", ["id"], unique=False)
    op.create_index("ix_admin_change_audit_actor_created", "admin_change_audit_logs", ["actor_id", "created_at"], unique=False)
    op.create_index("ix_admin_change_audit_entity", "admin_change_audit_logs", ["entity", "entity_key"], unique=False)
    op.create_index("ix_admin_change_audit_logs_action", "admin_change_audit_logs", ["action"], unique=False)

    _seed_if_missing(bind)


def downgrade() -> None:
    op.drop_index("ix_admin_change_audit_logs_action", table_name="admin_change_audit_logs")
    op.drop_index("ix_admin_change_audit_entity", table_name="admin_change_audit_logs")
    op.drop_index("ix_admin_change_audit_actor_created", table_name="admin_change_audit_logs")
    op.drop_index("ix_admin_change_audit_logs_id", table_name="admin_change_audit_logs")
    op.drop_table("admin_change_audit_logs")

    op.drop_index("ix_country_config_versions_status_created", table_name="country_config_versions")
    op.drop_index("ix_country_config_versions_country_type", table_name="country_config_versions")
    op.drop_index("ix_country_config_versions_country_code", table_name="country_config_versions")
    op.drop_index("ix_country_config_versions_id", table_name="country_config_versions")
    op.drop_table("country_config_versions")

    op.drop_index("ix_country_feature_flags_country_enabled", table_name="country_feature_flags")
    op.drop_index("ix_country_feature_flags_feature_key", table_name="country_feature_flags")
    op.drop_index("ix_country_feature_flags_country_code", table_name="country_feature_flags")
    op.drop_index("ix_country_feature_flags_id", table_name="country_feature_flags")
    op.drop_table("country_feature_flags")

    op.drop_index("ix_oman_delivery_zones_active_order", table_name="oman_delivery_zones")
    op.drop_index("ix_oman_delivery_zones_zone_code", table_name="oman_delivery_zones")
    op.drop_index("ix_oman_delivery_zones_id", table_name="oman_delivery_zones")
    op.drop_table("oman_delivery_zones")

    op.drop_index("ix_supplier_country_commissions_country_active", table_name="supplier_country_commissions")
    op.drop_index("ix_supplier_country_commissions_category_slug", table_name="supplier_country_commissions")
    op.drop_index("ix_supplier_country_commissions_country_code", table_name="supplier_country_commissions")
    op.drop_index("ix_supplier_country_commissions_id", table_name="supplier_country_commissions")
    op.drop_table("supplier_country_commissions")

    op.drop_index("ix_country_configs_active_code", table_name="country_configs")
    op.drop_index("ix_country_configs_code", table_name="country_configs")
    op.drop_index("ix_country_configs_id", table_name="country_configs")
    op.drop_table("country_configs")

