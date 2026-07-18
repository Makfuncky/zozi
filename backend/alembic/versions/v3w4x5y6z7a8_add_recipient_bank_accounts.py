"""add_recipient_bank_accounts

Revision ID: v3w4x5y6z7a8
Revises: 8a1e29bb7c55
Create Date: 2026-04-03 23:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "v3w4x5y6z7a8"
# Pointing to 8a1e29bb7c55 because the intermediate stub (u4v5w6x7y8z9) was deleted.
down_revision: Union[str, Sequence[str], None] = "8a1e29bb7c55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Strict declarative table creation. 
    # Removed runtime inspector checks to enforce strict Alembic state tracking.
    
    op.create_table(
        "supplier_bank_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("beneficiary_name", sa.Text(), nullable=True),
        sa.Column("bank_name", sa.String(length=200), nullable=True),
        sa.Column("branch_name", sa.String(length=200), nullable=True),
        sa.Column("account_number", sa.Text(), nullable=True),
        sa.Column("iban", sa.Text(), nullable=True),
        sa.Column("swift_code", sa.Text(), nullable=True),
        sa.Column("routing_number", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="OMR"),
        sa.Column("bank_country", sa.String(length=100), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", name="uq_supplier_bank_accounts_supplier"),
    )
    op.create_index(
        "ix_supplier_bank_accounts_supplier_id",
        "supplier_bank_accounts",
        ["supplier_id"],
        unique=True,
    )
    op.create_index(
        "ix_supplier_bank_accounts_status",
        "supplier_bank_accounts",
        ["verification_status"],
        unique=False,
    )

    op.create_table(
        "logistics_partner_bank_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("beneficiary_name", sa.Text(), nullable=True),
        sa.Column("bank_name", sa.String(length=200), nullable=True),
        sa.Column("branch_name", sa.String(length=200), nullable=True),
        sa.Column("account_number", sa.Text(), nullable=True),
        sa.Column("iban", sa.Text(), nullable=True),
        sa.Column("swift_code", sa.Text(), nullable=True),
        sa.Column("routing_number", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="OMR"),
        sa.Column("bank_country", sa.String(length=100), nullable=True),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["logistics_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", name="uq_logistics_partner_bank_accounts_partner"),
    )
    op.create_index(
        "ix_logistics_partner_bank_accounts_partner_id",
        "logistics_partner_bank_accounts",
        ["partner_id"],
        unique=True,
    )
    op.create_index(
        "ix_logistics_partner_bank_accounts_status",
        "logistics_partner_bank_accounts",
        ["verification_status"],
        unique=False,
    )


def downgrade() -> None:
    # Explicitly drop indexes before dropping tables for clean cross-dialect rollbacks
    op.drop_index("ix_logistics_partner_bank_accounts_status", table_name="logistics_partner_bank_accounts")
    op.drop_index("ix_logistics_partner_bank_accounts_partner_id", table_name="logistics_partner_bank_accounts")
    op.drop_table("logistics_partner_bank_accounts")
    
    op.drop_index("ix_supplier_bank_accounts_status", table_name="supplier_bank_accounts")
    op.drop_index("ix_supplier_bank_accounts_supplier_id", table_name="supplier_bank_accounts")
    op.drop_table("supplier_bank_accounts")

