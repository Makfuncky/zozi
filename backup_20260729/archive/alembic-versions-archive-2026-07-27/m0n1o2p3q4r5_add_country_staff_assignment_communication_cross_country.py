"""add_country_staff_assignment_communication_cross_country

Revision ID: m0n1o2p3q4r5
Revises: a4b5c6d7e8f9
Create Date: 2026-06-24 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "m0n1o2p3q4r5"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # ── 1. CountryStaffAssignment ──────────────────────────────────────────
    if "country_staff_assignments" not in existing_tables:
        op.create_table(
            "country_staff_assignments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("role_in_country", sa.String(length=40), nullable=False, server_default="country_manager"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("assigned_by", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "country_code", name="uq_country_staff_assignment_user_country"),
        )
        op.create_index("ix_country_staff_assignment_country", "country_staff_assignments", ["country_code"])
        op.create_index("ix_country_staff_assignment_user", "country_staff_assignments", ["user_id"])

    # ── 2. CountryCommunication ────────────────────────────────────────────
    if "country_communications" not in existing_tables:
        op.create_table(
            "country_communications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("from_user_id", sa.Integer(), nullable=True),
            sa.Column("to_user_id", sa.Integer(), nullable=True),
            sa.Column("subject", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="unread"),
            sa.Column("category", sa.String(length=40), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["country_code"], ["country_configs.code"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_country_comms_country_status", "country_communications", ["country_code", "status"])
        op.create_index("ix_country_comms_recipient", "country_communications", ["to_user_id", "status"])

    # ── 3. CrossCountryCustomerSession ─────────────────────────────────────
    if "cross_country_customer_sessions" not in existing_tables:
        op.create_table(
            "cross_country_customer_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("source_country_code", sa.String(length=10), nullable=False),
            sa.Column("target_country_code", sa.String(length=10), nullable=False),
            sa.Column("session_data", sa.JSON(), nullable=True),
            sa.Column("conversion", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("order_id", sa.Integer(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_country_code"], ["country_configs.code"], ),
            sa.ForeignKeyConstraint(["target_country_code"], ["country_configs.code"], ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_cc_customer_sessions_source", "cross_country_customer_sessions", ["source_country_code"])
        op.create_index("ix_cc_customer_sessions_target", "cross_country_customer_sessions", ["target_country_code"])
        op.create_index("ix_cc_customer_sessions_user", "cross_country_customer_sessions", ["user_id"])


def downgrade() -> None:
    if op.get_bind().dialect.has_table(op.get_bind(), "cross_country_customer_sessions"):
        op.drop_index("ix_cc_customer_sessions_user", table_name="cross_country_customer_sessions")
        op.drop_index("ix_cc_customer_sessions_target", table_name="cross_country_customer_sessions")
        op.drop_index("ix_cc_customer_sessions_source", table_name="cross_country_customer_sessions")
        op.drop_table("cross_country_customer_sessions")

    if op.get_bind().dialect.has_table(op.get_bind(), "country_communications"):
        op.drop_index("ix_country_comms_recipient", table_name="country_communications")
        op.drop_index("ix_country_comms_country_status", table_name="country_communications")
        op.drop_table("country_communications")

    if op.get_bind().dialect.has_table(op.get_bind(), "country_staff_assignments"):
        op.drop_index("ix_country_staff_assignment_user", table_name="country_staff_assignments")
        op.drop_index("ix_country_staff_assignment_country", table_name="country_staff_assignments")
        op.drop_table("country_staff_assignments")

