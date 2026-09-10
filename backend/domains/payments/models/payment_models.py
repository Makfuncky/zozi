"""payments domain — models.

Phase 2H scaffold: the canonical Payment / Payout / Gateway models still live
in ``domains/finance/models/payments.py`` because they reference finance
schema/columns. This module adds *thin* payments-domain projections:
- PaymentMethod (customer-saved payment method, scoped per country)
- PaymentAttempt (idempotent retry record for a payment intent)
- Refund (refund record)

These keep the payments domain's own public schema (``payments.*``) so that
routers/modules can speak the ``payments.*`` vocabulary without going through
finance for the read path.

The final refactor that moves ``Payment`` here is tracked in
``docs/refactors/payments_split.md`` (TODO).
"""
from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["PaymentMethod", "PaymentAttempt", "Refund", "PaymentIntent"]


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint("user_id", "provider_method_id", name="uq_payment_methods_user_provider"),
        Index("ix_payment_methods_user_country", "user_id", "country_code"),
        {"schema": "payments"},
    )

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # Law 5
    provider = Column(String(40), nullable=False)  # stripe, tap, paypal, paytabs, thawani
    provider_method_id = Column(String(120), nullable=False)
    method_type = Column(String(40), nullable=False)  # card, wallet, bank_account
    last4 = Column(String(4), nullable=True)
    brand = Column(String(40), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class PaymentAttempt(Base):
    """Idempotent retry record for a single payment intent.

    Each call to the gateway produces a row here. The unique
    ``(payment_id, attempt_no)`` makes the contract idempotent.
    """
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("payment_id", "attempt_no", name="uq_payment_attempts_payment_no"),
        CheckConstraint("attempt_no >= 1", name="chk_payment_attempt_no_positive"),
        CheckConstraint(
            "status IN ('pending','authorized','captured','failed','voided')",
            name="chk_payment_attempt_status",
        ),
        {"schema": "payments"},
    )

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    payment_id = Column(Integer, ForeignKey("finance.payments.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # Law 5
    attempt_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    provider = Column(String(40), nullable=False)
    provider_intent_id = Column(String(120), nullable=True)
    error_code = Column(String(80), nullable=True)
    error_message = Column(Text, nullable=True)
    raw_response = Column(JSON, nullable=True)
    attempted_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_refund_amount_positive"),
        CheckConstraint(
            "status IN ('pending','succeeded','failed','cancelled')",
            name="chk_refund_status_valid",
        ),
        Index("ix_refunds_payment", "payment_id"),
        {"schema": "payments"},
    )

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    payment_id = Column(Integer, ForeignKey("finance.payments.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # Law 5
    amount = Column(Numeric(18, 4), nullable=False)  # Law 19: money in NUMERIC, no float
    currency = Column(String(3), nullable=False, default="AED")
    reason = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    provider = Column(String(40), nullable=False)
    provider_refund_id = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    requested_by_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True, index=True)
    approved_by_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=True, index=True)
    requested_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class PaymentIntent(Base):
    """PSP-agnostic payment-intent projection.

    Stripe, Tap, PayPal, PayTabs, and Thawani all expose a "create intent"
    primitive before capture. This row is the payments-domain record of that
    intent so module routers can look up ``client_secret`` + status without
    going through the finance orchestrator on the read path.

    The actual financial record (amount captured, fees, ledger entry) lives
    in ``finance.payments`` and is referenced via ``finance_payment_id`` once
    the intent succeeds.
    """
    __tablename__ = "payment_intents"
    __table_args__ = (
        {"schema": "payments"},
        UniqueConstraint("provider", "provider_intent_id", name="uq_payment_intents_provider_intent"),
        Index("ix_payment_intents_order", "order_id"),
        Index("ix_payment_intents_user", "user_id"),
        CheckConstraint(
            "status IN ('requires_payment_method','requires_confirmation','requires_action',"
            "'processing','requires_capture','canceled','succeeded')",
            name="chk_payment_intent_status_valid",
        ),
        CheckConstraint("amount > 0", name="chk_payment_intent_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # Law 5
    amount = Column(Numeric(18, 4), nullable=False)  # Law 19: money in NUMERIC, no float
    currency = Column(String(3), nullable=False, default="AED")
    provider = Column(String(40), nullable=False)
    provider_intent_id = Column(String(120), nullable=True)
    status = Column(String(40), nullable=False, default="requires_payment_method")
    client_secret = Column(String(255), nullable=True)
    finance_payment_id = Column(
        Integer,
        ForeignKey("finance.payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metadata_json = Column("metadata", JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
