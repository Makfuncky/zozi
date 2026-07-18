"""add_logistics_partner_payouts

Revision ID: r7s8t9u0v1w2
Revises: q6r7s8t9u0v1
Create Date: 2026-03-29 23:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "r7s8t9u0v1w2"
down_revision: Union[str, Sequence[str], None] = "q6r7s8t9u0v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "logistics_partner_payouts" in inspector.get_table_names():
        return

    op.create_table(
        "logistics_partner_payouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("logistics_partners.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=True, server_default="pending"),
        sa.Column("method", sa.String(), nullable=True, server_default="bank"),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("amount >= 0", name="ck_logistics_partner_payouts_amount_nonnegative"),
    )
    op.create_index(
        "ix_logistics_partner_payouts_partner_created",
        "logistics_partner_payouts",
        ["partner_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "logistics_partner_payouts" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("logistics_partner_payouts") if index.get("name")}
    if "ix_logistics_partner_payouts_partner_created" in indexes:
        op.drop_index("ix_logistics_partner_payouts_partner_created", table_name="logistics_partner_payouts")
    op.drop_table("logistics_partner_payouts")

