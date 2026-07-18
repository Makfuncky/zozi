"""add_finance_bank_accounts

Revision ID: u4v5w6x7y8z9
Revises: 8a1e29bb7c55
Create Date: 2026-04-03 23:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "u4v5w6x7y8z9"
down_revision: Union[str, Sequence[str], None] = "8a1e29bb7c55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "finance_bank_accounts" in inspector.get_table_names():
        return

    op.create_table(
        "finance_bank_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=50), nullable=False),
        sa.Column("account_label", sa.String(length=150), nullable=True),
        sa.Column("beneficiary_name", sa.Text(), nullable=True),
        sa.Column("bank_name", sa.String(length=200), nullable=True),
        sa.Column("branch_name", sa.String(length=200), nullable=True),
        sa.Column("account_number", sa.Text(), nullable=True),
        sa.Column("iban", sa.Text(), nullable=True),
        sa.Column("swift_code", sa.Text(), nullable=True),
        sa.Column("routing_number", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="AED"),
        sa.Column("support_email", sa.Text(), nullable=True),
        sa.Column("support_phone", sa.Text(), nullable=True),
        sa.Column("remittance_reference_prefix", sa.String(length=50), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", name="uq_finance_bank_accounts_scope"),
    )
    op.create_index(
        "ix_finance_bank_accounts_scope_active",
        "finance_bank_accounts",
        ["scope", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "finance_bank_accounts" not in inspector.get_table_names():
        return

    op.drop_index("ix_finance_bank_accounts_scope_active", table_name="finance_bank_accounts")
    op.drop_table("finance_bank_accounts")

