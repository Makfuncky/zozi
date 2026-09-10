"""payments domain — authorization policies.

Pure-Python policy classes. NO business logic; just rule evaluation. The
payment services call into these to enforce maker-checker, refund caps, and
chargeback windows before performing the actual write.

Per Law 1, this module does not import from ``modules/*`` or any other domain.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal


# ── Refund policy ────────────────────────────────────────────────────────────

REFUND_FULL_REFUND_WINDOW_DAYS = 30  # full refund window after capture
REFUND_PARTIAL_REFUND_WINDOW_DAYS = 90  # partial refund window
REFUND_MAX_PARTIAL_PERCENT = Decimal("50")  # partial cap (% of original)


@dataclass(frozen=True)
class RefundDecision:
    allowed: bool
    reason: str
    max_amount: Decimal


class RefundPolicy:
    """Authorization + amount-cap policies for refunds.

    These are the same rules the finance/payments orchestrator applies; kept
    here so the payments domain can validate at the request boundary.
    """

    @staticmethod
    def evaluate(
        *,
        requested_amount: Decimal,
        captured_amount: Decimal,
        captured_at: datetime,
        already_refunded: Decimal,
        now: datetime | None = None,
    ) -> RefundDecision:
        now = now or datetime.now(tz=timezone.utc)
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)

        remaining = captured_amount - already_refunded
        if requested_amount > remaining:
            return RefundDecision(
                allowed=False,
                reason="requested_amount exceeds remaining refundable",
                max_amount=remaining,
            )

        days_since_capture = (now - captured_at).days
        is_full_refund = requested_amount == captured_amount

        if is_full_refund and days_since_capture > REFUND_FULL_REFUND_WINDOW_DAYS:
            return RefundDecision(
                allowed=False,
                reason=f"full refund window expired ({REFUND_FULL_REFUND_WINDOW_DAYS}d)",
                max_amount=Decimal("0"),
            )

        if not is_full_refund and days_since_capture > REFUND_PARTIAL_REFUND_WINDOW_DAYS:
            cap = (captured_amount * REFUND_MAX_PARTIAL_PERCENT) / Decimal("100")
            return RefundDecision(
                allowed=False,
                reason=f"partial refund window expired ({REFUND_PARTIAL_REFUND_WINDOW_DAYS}d)",
                max_amount=cap,
            )

        return RefundDecision(
            allowed=True,
            reason="within refund window",
            max_amount=remaining,
        )


# ── Chargeback policy ───────────────────────────────────────────────────────

CHARGEBACK_RESPONSE_WINDOW_DAYS = 7  # supplier must submit evidence within N days


class ChargebackPolicy:
    """Policy for incoming chargebacks (disputes)."""

    @staticmethod
    def response_deadline(received_at: datetime) -> datetime:
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
        return received_at + timedelta(days=CHARGEBACK_RESPONSE_WINDOW_DAYS)

    @staticmethod
    def can_submit_evidence(*, received_at: datetime, now: datetime | None = None) -> bool:
        now = now or datetime.now(tz=timezone.utc)
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
        return now <= ChargebackPolicy.response_deadline(received_at)


# ── Maker-checker policy (payouts) ──────────────────────────────────────────

class PayoutApprovalPolicy:
    """Payouts >= MAKER_CHECKER_THRESHOLD require a different approver than the
    requester (separation-of-duties)."""
    MAKER_CHECKER_THRESHOLD = Decimal("5000")  # AED/SAR

    @staticmethod
    def requires_dual_approval(amount: Decimal) -> bool:
        return Decimal(amount) >= PayoutApprovalPolicy.MAKER_CHECKER_THRESHOLD

    @staticmethod
    def can_approve(*, requested_by_id: int, approver_id: int, amount: Decimal) -> bool:
        if requested_by_id == approver_id:
            return False
        if PayoutApprovalPolicy.requires_dual_approval(amount):
            # both maker and checker; checker must differ from maker
            return approver_id != requested_by_id
        return True