"""add payments schema models (Phase 2H)

Adds the payments-domain projections:
- payments.payment_methods
- payments.payment_attempts
- payments.refunds

These are thin payments-domain projections over the canonical finance
``Payment`` model. The full refactor that moves ``Payment`` here is tracked
separately; see ``docs/refactors/payments_split.md``.

Money columns are NUMERIC(18, 4) per Law 19 (no float in money paths).
All rows are country-scoped per Law 5.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_09_03_0007"
down_revision = "2026_09_03_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    schema_prefix = "" if is_sqlite else "payments."

    op.create_table(
        f"{schema_prefix}payment_methods",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("0"), index=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("country_code", sa.String(2), nullable=False, index=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_method_id", sa.String(120), nullable=False),
        sa.Column("method_type", sa.String(40), nullable=False),
        sa.Column("last4", sa.String(4), nullable=True),
        sa.Column("brand", sa.String(40), nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "provider_method_id", name="uq_payment_methods_user_provider"),
        sa.Index("ix_payment_methods_user_country", "user_id", "country_code"),
        schema=("payments" if not is_sqlite else None),
    )

    op.create_table(
        f"{schema_prefix}payment_attempts",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("0"), index=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("payment_id", sa.Integer, sa.ForeignKey("finance.payments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("country_code", sa.String(2), nullable=False, index=True),
        sa.Column("attempt_no", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_intent_id", sa.String(120), nullable=True),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("raw_response", sa.JSON, nullable=True),
        sa.Column("attempted_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("payment_id", "attempt_no", name="uq_payment_attempts_payment_no"),
        sa.CheckConstraint("attempt_no >= 1", name="chk_payment_attempt_no_positive"),
        sa.CheckConstraint(
            "status IN ('pending','authorized','captured','failed','voided')",
            name="chk_payment_attempt_status",
        ),
        sa.Index("ix_payment_attempts_status", "status"),
        schema=("payments" if not is_sqlite else None),
    )

    op.create_table(
        f"{schema_prefix}refunds",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("0"), index=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("payment_id", sa.Integer, sa.ForeignKey("finance.payments.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("country_code", sa.String(2), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),  # Law 19: money in NUMERIC
        sa.Column("currency", sa.String(3), nullable=False, server_default="AED"),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_refund_id", sa.String(120), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("requested_by", sa.Integer, sa.ForeignKey("accounts.users.id"), nullable=True),
        sa.Column("approved_by", sa.Integer, sa.ForeignKey("accounts.users.id"), nullable=True),
        sa.Column("requested_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="chk_refund_amount_positive"),
        sa.CheckConstraint(
            "status IN ('pending','succeeded','failed','cancelled')",
            name="chk_refund_status_valid",
        ),
        sa.Index("ix_refunds_payment", "payment_id"),
        sa.Index("ix_refunds_status_country", "status", "country_code"),
        schema=("payments" if not is_sqlite else None),
    )


def downgrade() -> None:
    op.drop_table("refunds")
    op.drop_table("payment_attempts")
    op.drop_table("payment_methods")
