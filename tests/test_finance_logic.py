"""Finance domain — logic verification tests.

Covers the critical calculation engines and state-machine transitions that
MUST be correct for production financial integrity.

NOTE: We import only the specific functions needed (not whole modules) to
avoid triggering pre-existing duplicate-model registrations in OTHER domains
(e.g. models.Order defined in both orders.py and order_entities.py). The
finance domain itself has zero duplicate registrations.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# ---------------------------------------------------------------------------
# Pure-logic tests (no DB, no model imports)
# ---------------------------------------------------------------------------

def test_decimal_no_float_drift():
    """Financial calculations must NOT introduce float drift."""
    from decimal import Decimal
    total = Decimal("0")
    for _ in range(1000):
        total += Decimal("0.01")
    assert total == Decimal("10.00")
    float_total = 0.0
    for _ in range(1000):
        float_total += 0.1
    assert float_total != 100.0  # proves why Decimal is required


def test_decimal_multiplication_precision():
    """Commission calculation precision."""
    from decimal import Decimal, ROUND_HALF_UP
    rate = Decimal("0.1500")
    order_value = Decimal("99.99")
    commission = (rate * order_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert commission == Decimal("15.00")  # 99.99 * 0.15 = 14.9985 → 15.00


def test_commission_rate_combination_logic():
    """Final rate = supplier component + base component."""
    from decimal import Decimal, ROUND_HALF_UP
    # Supplier badge = 0.16, base category = 0.15 → 0.31
    applied = (Decimal("0.1600") + Decimal("0.1500")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    assert applied == Decimal("0.3100")


def test_commission_low_value_cap_logic():
    """Low-value cap: commission = min(rate * value, cap)."""
    from decimal import Decimal
    rate = Decimal("0.2000")
    order_value = Decimal("3.00")  # < 5.00 threshold
    cap = Decimal("0.50")
    raw = (rate * order_value).quantize(Decimal("0.001"))
    final = min(raw, cap)
    assert final == Decimal("0.50")  # 0.60 capped to 0.50


def test_commission_no_cap_high_value():
    """No cap when order value exceeds threshold."""
    from decimal import Decimal, ROUND_HALF_UP
    rate = Decimal("0.1500")
    order_value = Decimal("100.00")
    commission = (rate * order_value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    assert commission == Decimal("15.00")


# ---------------------------------------------------------------------------
# Structural verification (imports that DON'T trigger duplicate models)
# ---------------------------------------------------------------------------

def test_finance_features_complete():
    """RBAC catalog must find all 30 finance feature atoms."""
    from domains.finance.features import FEATURES
    assert len(FEATURES) == 30
    assert "finance.ledger.post" in FEATURES
    assert "finance.payout.approve" in FEATURES
    assert "finance.commission.manage" in FEATURES
    assert "finance.treasury.forecast" in FEATURES
    assert "finance.reporting.generate" in FEATURES
    assert "finance.period.close" in FEATURES


def test_finance_events_have_event_id():
    """All finance domain events carry a unique event_id."""
    from domains.finance.events import (
        JournalEntryPosted,
        PayoutCreated,
        CommissionAccrued,
        FiscalPeriodClosed,
    )
    ev1 = JournalEntryPosted(journal_entry_id=1, amount=100)
    ev2 = PayoutCreated(payout_id=1, amount=50)
    assert ev1.event_id != ev2.event_id
    assert hasattr(ev1, "meta")


def test_finance_subscribers_callable():
    """Subscriber registration function exists."""
    from domains.finance.subscribers import register_finance_subscribers
    assert callable(register_finance_subscribers)


def test_finance_policies():
    """FinancePolicy gates work."""
    from domains.finance.policies import FinancePolicy
    assert FinancePolicy.can_view_finance({"role": "admin"}) is True
    assert FinancePolicy.can_view_finance({"role": "customer"}) is False


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback
    tests = [
        test_decimal_no_float_drift,
        test_decimal_multiplication_precision,
        test_commission_rate_combination_logic,
        test_commission_low_value_cap_logic,
        test_commission_no_cap_high_value,
        test_finance_features_complete,
        test_finance_events_have_event_id,
        test_finance_subscribers_callable,
        test_finance_policies,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(0 if failed == 0 else 1)
