"""add_logistics_cod_remittance_receipts

Revision ID: w9x8y7z6a5b4
Revises: v1w2x3y4z5a6
Create Date: 2026-04-08 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "w9x8y7z6a5b4"
down_revision: Union[str, Sequence[str], None] = "v1w2x3y4z5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "logistics_cod_remittance_receipts" not in inspector.get_table_names():
        op.create_table(
            "logistics_cod_remittance_receipts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("settlement_id", sa.Integer(), nullable=False),
            sa.Column("partner_id", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="OMR"),
            sa.Column("bank_reference", sa.String(length=200), nullable=True),
            sa.Column("receipt_file_url", sa.String(length=500), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("bank_transaction_id", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("amount > 0", name="ck_logistics_cod_receipts_amount_positive"),
            sa.ForeignKeyConstraint(["settlement_id"], ["logistics_settlements.id"]),
            sa.ForeignKeyConstraint(["partner_id"], ["logistics_partners.id"]),
            sa.ForeignKeyConstraint(["bank_transaction_id"], ["bank_transactions.id"]),
            sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("logistics_cod_remittance_receipts")}
    if "ix_logistics_cod_remittance_receipts_id" not in existing_indexes:
        op.create_index(
            "ix_logistics_cod_remittance_receipts_id",
            "logistics_cod_remittance_receipts",
            ["id"],
            unique=False,
        )
    if "ix_logistics_cod_remittance_receipts_settlement_id" not in existing_indexes:
        op.create_index(
            "ix_logistics_cod_remittance_receipts_settlement_id",
            "logistics_cod_remittance_receipts",
            ["settlement_id"],
            unique=False,
        )
    if "ix_logistics_cod_remittance_receipts_partner_id" not in existing_indexes:
        op.create_index(
            "ix_logistics_cod_remittance_receipts_partner_id",
            "logistics_cod_remittance_receipts",
            ["partner_id"],
            unique=False,
        )
    if "ix_logistics_cod_receipts_partner_status" not in existing_indexes:
        op.create_index(
            "ix_logistics_cod_receipts_partner_status",
            "logistics_cod_remittance_receipts",
            ["partner_id", "status"],
            unique=False,
        )
    if "ix_logistics_cod_receipts_settlement" not in existing_indexes:
        op.create_index(
            "ix_logistics_cod_receipts_settlement",
            "logistics_cod_remittance_receipts",
            ["settlement_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "logistics_cod_remittance_receipts" not in inspector.get_table_names():
        return

    existing_indexes = {index["name"] for index in inspector.get_indexes("logistics_cod_remittance_receipts")}
    for index_name in (
        "ix_logistics_cod_receipts_settlement",
        "ix_logistics_cod_receipts_partner_status",
        "ix_logistics_cod_remittance_receipts_partner_id",
        "ix_logistics_cod_remittance_receipts_settlement_id",
        "ix_logistics_cod_remittance_receipts_id",
    ):
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name="logistics_cod_remittance_receipts")

    op.drop_table("logistics_cod_remittance_receipts")

