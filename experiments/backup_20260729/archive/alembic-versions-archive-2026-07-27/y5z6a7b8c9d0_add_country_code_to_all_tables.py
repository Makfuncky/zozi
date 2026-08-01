"""Add country_code columns to all tables for multi-country RLS isolation."""
from __future__ import annotations

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

revision = "y5z6a7b8c9d0"
down_revision = "s_y5z6a7b8c9d0"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

TABLES_NEEDING_COUNTRY_CODE = {
    "banners": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "coupons": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "payments": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "support_tickets": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "promotion_engine_configs": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "return_requests": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "supplier_documents": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "logistics_partner_profiles": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "order_items": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
    "user_browsing_history": {"country_code": sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True, index=True)},
}


def upgrade():
    for table_name, columns in TABLES_NEEDING_COUNTRY_CODE.items():
        try:
            with op.batch_alter_table(table_name) as batch_op:
                for col_name, col in columns.items():
                    batch_op.add_column(col)
                    try:
                        batch_op.create_index(f"ix_{table_name}_{col_name}", [col_name])
                    except Exception:
                        logger.warning(f"Could not create index on {table_name}.{col_name}")
        except Exception as e:
            logger.warning(f"Could not add country_code to {table_name}: {e}")

    op.create_table(
        "permission_categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("permission_categories.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(150), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(20), nullable=False, server_default="global"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "role_permission_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("role_name", sa.String(80), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("granted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_granted", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("role_name", "permission_id", "country_code", name="uq_role_permission_country"),
    )

    op.create_table(
        "user_permission_overrides",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("is_granted", sa.Boolean(), default=True),
        sa.Column("granted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "permission_id", "country_code", name="uq_user_perm_override_country"),
    )

    op.create_table(
        "permission_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("target_role", sa.String(80), nullable=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    logger.info("Migration y5z6a7b8c9d0 complete: added country_code + permission tables")


def downgrade():
    op.drop_table("permission_audit_log")
    op.drop_table("user_permission_overrides")
    op.drop_table("role_permission_assignments")
    op.drop_table("permissions")
    op.drop_table("permission_categories")

    for table_name in reversed(list(TABLES_NEEDING_COUNTRY_CODE.keys())):
        try:
            with op.batch_alter_table(table_name) as batch_op:
                for col_name in TABLES_NEEDING_COUNTRY_CODE[table_name]:
                    batch_op.drop_column(col_name)
        except Exception as e:
            logger.warning(f"Could not drop country_code from {table_name}: {e}")

