"""add payment_intents table

Creates the ``payments.payment_intents`` table for the ``PaymentIntent`` model
declared in ``domains/payments/models/payment_models.py`` (Phase 2H scaffold).

Money columns are NUMERIC(18, 4) per Law 19 (no float in money paths).
All rows are country-scoped per Law 5.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

revision: str = "20261001_0001"
down_revision: Union[str, None] = "20260930_0008"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    schema_prefix = "" if is_sqlite else "payments."

    op.create_table(
        f"{schema_prefix}payment_intents",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("0"), index=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("country_code", sa.String(2), nullable=False, index=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_intent_id", sa.String(120), nullable=True),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="AED"),
        sa.Column("status", sa.String(40), nullable=False, server_default="requires_payment_method"),
        sa.Column("client_secret", sa.String(255), nullable=True),
        sa.Column("finance_payment_id", sa.Integer, sa.ForeignKey("finance.payments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("last_payment_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_intent_id", name="uq_payment_intents_provider_intent"),
        sa.Index("ix_payment_intents_order", "order_id"),
        sa.Index("ix_payment_intents_user", "user_id"),
        sa.CheckConstraint(
            "status IN ('requires_payment_method','requires_confirmation','requires_action',"
            "'processing','requires_capture','canceled','succeeded')",
            name="chk_payment_intent_status_valid",
        ),
        sa.CheckConstraint("amount > 0", name="chk_payment_intent_amount_positive"),
        schema=("payments" if not is_sqlite else None),
    )


def downgrade() -> None:
    op.drop_table("payment_intents", schema="payments")
