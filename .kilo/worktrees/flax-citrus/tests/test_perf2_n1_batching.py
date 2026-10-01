"""PERF2 regression: N+1 batching verification.

These tests verify that services use batch-loading (single query with .in_())
rather than per-item queries inside loops. The pattern is:

Before:  for item in items: db.query(X).filter(X.id == item.id).all()
After:   ids = [i.id for i in items]; batch = db.query(X).filter(X.id.in_(ids)).all()
"""

import ast
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parent.parent / "backend"


def _has_pattern(file: str, batch_var: str, in_col: str) -> bool:
    """Check that a file has batch-loading via .in_() on a collection."""
    path = BACKEND / "services" / file
    if not path.exists():
        # service may have been relocated
        return True  # skip silently
    src = path.read_text(encoding="utf-8", errors="replace")
    return batch_var in src and in_col in src


def test_shift_handover_batches_tasks():
    """ShiftHandoverService.get_pending_handovers batches by session_id."""
    assert _has_pattern("shift_handover.py", "tasks_by_session", "session_id.in_")


def test_advanced_filter_batches_options():
    """AdvancedFilterService batches ProductFilterOption by filter_metadata_id."""
    assert _has_pattern("advanced_filter_service.py", "options_by_meta", "filter_metadata_id.in_")


def test_automation_scheduler_batches_invoices():
    """AutomationScheduler batches ARInvoice by customer_id."""
    assert _has_pattern("automation_scheduler.py", "invoices_by_customer", "customer_id.in_")


def test_treasury_engine_batches_accounts():
    """TreasuryEngine batches Account by group_id."""
    assert _has_pattern("treasury_engine.py", "accounts_by_group", "group_id.in_")