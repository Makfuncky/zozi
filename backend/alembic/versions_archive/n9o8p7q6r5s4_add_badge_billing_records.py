"""add_badge_billing_records

Revision ID: n9o8p7q6r5s4
Revises: 598ce7e939d1
Create Date: 2026-04-06 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n9o8p7q6r5s4"
down_revision: Union[str, Sequence[str], None] = "598ce7e939d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())
    bank_transaction_column = sa.Column("bank_transaction_id", sa.Integer(), nullable=True)
    if "bank_transactions" in table_names:
        bank_transaction_column = sa.Column(
            "bank_transaction_id",
            sa.Integer(),
            sa.ForeignKey("bank_transactions.id"),
            nullable=True,
        )

    op.create_table(
        "badge_billing_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("billing_reference", sa.String(length=50), nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("badge_level", sa.String(length=30), nullable=False),
        sa.Column("charge_type", sa.String(length=20), nullable=False, server_default="setup"),
        sa.Column("charge_source", sa.String(length=30), nullable=False, server_default="manual_purchase"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="invoiced"),
        sa.Column("amount", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="AED"),
        sa.Column("period_start", sa.DateTime(), nullable=True),
        sa.Column("period_end", sa.DateTime(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("billed_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        bank_transaction_column,
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("amount >= 0", name="ck_badge_billing_amount_nonneg"),
        sa.CheckConstraint(
            "charge_type IN ('setup','recurring','adjustment')",
            name="ck_badge_billing_charge_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('draft','invoiced','paid','waived','cancelled')",
            name="ck_badge_billing_status_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("billing_reference", name="uq_badge_billing_reference"),
    )
    with op.batch_alter_table("badge_billing_records", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_badge_billing_records_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_badge_billing_records_billing_reference"), ["billing_reference"], unique=True)
        batch_op.create_index(batch_op.f("ix_badge_billing_records_supplier_id"), ["supplier_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_badge_billing_records_badge_level"), ["badge_level"], unique=False)
        batch_op.create_index(batch_op.f("ix_badge_billing_records_bank_transaction_id"), ["bank_transaction_id"], unique=False)
        batch_op.create_index("ix_badge_billing_supplier_status", ["supplier_id", "status"], unique=False)
        batch_op.create_index("ix_badge_billing_badge_charge", ["badge_level", "charge_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("badge_billing_records", schema=None) as batch_op:
        batch_op.drop_index("ix_badge_billing_badge_charge")
        batch_op.drop_index("ix_badge_billing_supplier_status")
        batch_op.drop_index(batch_op.f("ix_badge_billing_records_bank_transaction_id"))
        batch_op.drop_index(batch_op.f("ix_badge_billing_records_badge_level"))
        batch_op.drop_index(batch_op.f("ix_badge_billing_records_supplier_id"))
        batch_op.drop_index(batch_op.f("ix_badge_billing_records_billing_reference"))
        batch_op.drop_index(batch_op.f("ix_badge_billing_records_id"))
    op.drop_table("badge_billing_records")

