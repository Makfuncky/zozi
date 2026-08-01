"""add_payout_provider_metadata

Revision ID: a9b0c1d2e3f4
Revises: z7b8c9d0e1f2
Create Date: 2026-04-04 18:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = "z7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_PAYOUT_METADATA_COLUMNS: tuple[sa.Column, ...] = (
    sa.Column("provider", sa.String(length=50), nullable=True),
    sa.Column("provider_recipient_id", sa.String(length=255), nullable=True),
    sa.Column("provider_quote_id", sa.String(length=255), nullable=True),
    sa.Column("provider_transfer_id", sa.String(length=255), nullable=True),
    sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
    sa.Column("provider_status", sa.String(length=50), nullable=True),
    sa.Column("last_provider_sync_at", sa.DateTime(), nullable=True),
)


def _ensure_columns(table_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        for column in _PAYOUT_METADATA_COLUMNS:
            if column.name not in existing_columns:
                batch_op.add_column(column.copy())

    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    transfer_index = f"ix_{table_name}_provider_transfer"
    payment_index = f"ix_{table_name}_provider_payment"
    status_index = f"ix_{table_name}_provider_status"

    if transfer_index not in existing_indexes:
        op.create_index(transfer_index, table_name, ["provider", "provider_transfer_id"], unique=False)
    if payment_index not in existing_indexes:
        op.create_index(payment_index, table_name, ["provider", "provider_payment_id"], unique=False)
    if status_index not in existing_indexes:
        op.create_index(status_index, table_name, ["provider", "provider_status"], unique=False)


def upgrade() -> None:
    _ensure_columns("payouts")
    _ensure_columns("logistics_partner_payouts")


def _drop_columns(table_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}

    for index_name in (
        f"ix_{table_name}_provider_transfer",
        f"ix_{table_name}_provider_payment",
        f"ix_{table_name}_provider_status",
    ):
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        for column_name in (
            "last_provider_sync_at",
            "provider_status",
            "provider_payment_id",
            "provider_transfer_id",
            "provider_quote_id",
            "provider_recipient_id",
            "provider",
        ):
            if column_name in existing_columns:
                batch_op.drop_column(column_name)


def downgrade() -> None:
    _drop_columns("logistics_partner_payouts")
    _drop_columns("payouts")

