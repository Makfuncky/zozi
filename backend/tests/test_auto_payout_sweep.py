"""
Integration test for the auto-payout sweep (``run_auto_payout_sweep``).

Verifies the full pipeline:
  1. Create a ``SupplierSettlement`` with ``eligible_at`` in the past
  2. Run the sweep via ``run_auto_payout_sweep(db)``
  3. Assert ``Payout`` + ``PayoutBatch`` + ``PayoutBatchItem`` records exist
  4. Assert ``settlement.payout_id`` is set and ``status`` changed to "processed"
  5. Assert the sweep result dict contains expected keys and values
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from models import (
    Payout,
    PayoutBatch,
    PayoutBatchItem,
    SupplierSettlement,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _days_ago(n: int) -> datetime:
    """Return ``n`` days before (or after, if negative) the current moment."""
    return datetime.now(timezone.utc) - timedelta(days=n)


# ── Test ───────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.usefixtures("_seed_default_accounts")
def test_auto_payout_sweep_creates_payout_and_batch(
    db_session: Session,
) -> None:
    """Create a settlement whose holding period has elapsed, run the sweep,
    and verify Payout + PayoutBatch + settlement.payout_id are all set."""
    # ── 1. Look up the demo supplier ──────────────────────────────────────
    from models import User

    supplier = (
        db_session.query(User)
        .filter(User.email == "supplier@zozi.com")
        .first()
    )
    assert supplier is not None, "Demo supplier user must exist"
    supplier_id: int = supplier.id

    # ── 2. Create an eligible SupplierSettlement ──────────────────────────
    settlement = SupplierSettlement(
        supplier_id=supplier_id,
        gross_amount=Decimal("150.00"),
        commission_amount=Decimal("15.00"),
        net_amount=Decimal("135.00"),
        status="pending",
        eligible_at=_days_ago(5),  # eligible 5 days ago
        country_code="AE",
        currency="OMR",
    )
    db_session.add(settlement)
    db_session.flush()  # make settlement.id available
    settlement_id: int = settlement.id

    # ── 3. Run the sweep (mock email to avoid side effects) ───────────────
    from services.auto_payout_scheduler import run_auto_payout_sweep

    # Patch email_service.send_email — the notification service imports it
    # via ``from email_service import send_email`` inside the function body.
    with patch("email_service.send_email") as mock_send:
        result = run_auto_payout_sweep(db_session)

    # ── 4. Assert sweep result ────────────────────────────────────────────
    assert result["status"] == "ok", f"Sweep failed: {result.get('error')}"
    assert result["processed"] >= 1, "Expected at least 1 settlement processed"
    assert result["total_net_amount"] >= 135.0
    assert result["supplier_count"] >= 1
    assert result["batch_id"] is not None, "Expected a PayoutBatch to be created"
    assert result["batch_number"] is not None

    # ── 5. Assert settlement was updated ──────────────────────────────────
    db_session.flush()  # ensure sweep's flush is visible
    updated_settlement: SupplierSettlement | None = (
        db_session.query(SupplierSettlement)
        .filter(SupplierSettlement.id == settlement_id)
        .first()
    )
    assert updated_settlement is not None
    assert updated_settlement.status == "processed"
    assert updated_settlement.payout_id is not None, (
        "settlement.payout_id should be set after payout creation"
    )

    # ── 6. Assert Payout record was created ──────────────────────────────
    payout: Payout | None = (
        db_session.query(Payout)
        .filter(Payout.id == updated_settlement.payout_id)
        .first()
    )
    assert payout is not None, "Payout record not found"
    assert payout.supplier_id == supplier_id
    assert float(payout.amount) == pytest.approx(135.0, abs=0.01)
    assert payout.status == "pending"
    assert payout.country_code == "AE"

    # ── 7. Assert PayoutBatch record was created ─────────────────────────
    batch: PayoutBatch | None = (
        db_session.query(PayoutBatch)
        .filter(PayoutBatch.id == result["batch_id"])
        .first()
    )
    assert batch is not None, "PayoutBatch record not found"
    assert batch.status == "draft"
    assert batch.item_count >= 1

    # ── 8. Assert PayoutBatchItem exists with correct entity_type ────────
    batch_item: PayoutBatchItem | None = (
        db_session.query(PayoutBatchItem)
        .filter(
            PayoutBatchItem.batch_id == batch.id,
            PayoutBatchItem.entity_type == "supplier",
            PayoutBatchItem.entity_id == supplier_id,
        )
        .first()
    )
    assert batch_item is not None, (
        "PayoutBatchItem for this supplier not found in the batch"
    )
    assert float(batch_item.amount) == pytest.approx(135.0, abs=0.01)

    # ── 9. Assert email was sent (best-effort notification) ──────────────
    mock_send.assert_called()


@pytest.mark.integration
@pytest.mark.usefixtures("_seed_default_accounts")
def test_auto_payout_sweep_no_eligible_settlements(
    db_session: Session,
) -> None:
    """When no eligible settlements exist, the sweep returns
    ``no_eligible_settlements`` status."""
    from services.auto_payout_scheduler import run_auto_payout_sweep

    with patch("email_service.send_email"):
        result = run_auto_payout_sweep(db_session)

    assert result["status"] == "no_eligible_settlements"


@pytest.mark.integration
@pytest.mark.usefixtures("_seed_default_accounts")
def test_auto_payout_sweep_skips_future_eligible(
    db_session: Session,
) -> None:
    """A settlement with ``eligible_at`` in the future should NOT be picked up."""
    from models import User

    supplier = (
        db_session.query(User)
        .filter(User.email == "supplier@zozi.com")
        .first()
    )
    assert supplier is not None

    # Future-eligible settlement — eligible_at is 5 days in the future
    settlement = SupplierSettlement(
        supplier_id=supplier.id,
        gross_amount=Decimal("200.00"),
        net_amount=Decimal("180.00"),
        status="pending",
        eligible_at=_days_ago(-5),  # -5 days = 5 days in the future
        country_code="AE",
        currency="OMR",
    )
    db_session.add(settlement)
    db_session.flush()

    from services.auto_payout_scheduler import run_auto_payout_sweep

    with patch("email_service.send_email"):
        result = run_auto_payout_sweep(db_session)

    assert result["status"] == "no_eligible_settlements", (
        "Future-eligible settlement should not trigger a payout"
    )


@pytest.mark.integration
@pytest.mark.usefixtures("_seed_default_accounts")
def test_auto_payout_sweep_dry_run(
    db_session: Session,
) -> None:
    """Dry-run mode should count eligible settlements without creating records."""
    from models import User

    supplier = (
        db_session.query(User)
        .filter(User.email == "supplier@zozi.com")
        .first()
    )
    assert supplier is not None

    settlement = SupplierSettlement(
        supplier_id=supplier.id,
        gross_amount=Decimal("100.00"),
        net_amount=Decimal("90.00"),
        status="pending",
        eligible_at=_days_ago(5),
        country_code="AE",
        currency="OMR",
    )
    db_session.add(settlement)
    db_session.flush()

    from services.auto_payout_scheduler import run_auto_payout_sweep

    with patch("email_service.send_email"):
        result = run_auto_payout_sweep(db_session, dry_run=True)

    assert result["status"] == "ok"
    assert result["processed"] >= 1
    assert result["batch_id"] is None, (
        "Dry run should not create a PayoutBatch"
    )

    # Verify no Payout was actually created
    payout_count = db_session.query(Payout).count()
    assert payout_count == 0, (
        "Dry run should not create any Payout records"
    )
