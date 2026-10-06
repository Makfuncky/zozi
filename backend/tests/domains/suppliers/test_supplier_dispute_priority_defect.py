"""Fail-before reproduction: SupplierDispute.priority AttributeError.

``SupplierDispute.priority`` does not exist in either the ORM
(``backend/domains/suppliers/models/suppliers.py``) or the database
(``suppliers.supplier_disputes``).  Two services filter on it:

  - domains/suppliers/services/disputes_service.py:284,347
  - domains/orders/services/disputes/service.py:284,347

Accessing the attribute at the ORM level raises AttributeError immediately.
This test is the paired reproduction for that live defect.
"""
from __future__ import annotations

import pytest


def test_supplier_dispute_priority_attribute_does_not_exist():
    """FAIL-BEFORE: accessing .priority raises AttributeError (confirmed live
    defect, not a hypothetical)."""
    from domains.suppliers.models.suppliers import SupplierDispute

    with pytest.raises(AttributeError, match="priority"):
        _ = SupplierDispute.priority


def test_supplier_dispute_priority_column_not_in_table():
    """Confirm priority is absent from the mapped Table, not just the class."""
    from domains.suppliers.models.suppliers import SupplierDispute

    assert "priority" not in SupplierDispute.__table__.c, (
        "priority column unexpectedly present in SupplierDispute.__table__"
    )


def test_supplier_disputes_db_has_no_priority_column():
    """DB half: suppliers.supplier_disputes.priority does not exist."""
    from sqlalchemy import text
    from infrastructure.database.database import engine

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT column_name FROM information_schema.columns "
                 "WHERE table_schema='suppliers' AND table_name='supplier_disputes' "
                 "AND column_name='priority'")
        ).fetchone()
    assert row is None, (
        f"priority column unexpectedly exists in DB: {row}"
    )
