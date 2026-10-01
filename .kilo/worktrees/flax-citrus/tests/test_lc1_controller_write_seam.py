"""LC1 regression guard.

The audit flagged ``controllers/cash_management_controller.py`` for a write
operation in the controller layer: ``admin_queue_dispatch_transfer_batch`` owned
a ``SessionLocal()`` lifecycle and called ``session.commit()`` inside a
background job. Per the layer contract, only ``services/**`` may own DB
transactions.

Fix (2026-08-10): the dispatch logic already existed in the service layer
(``services.treasury.payout_dispatch_service`` — ``normalize_dispatch_kind``,
``dispatch_transfer_batch_with_audit``, ``run_dispatch_transfer_batch_job``).
The controller's private duplicates (``_normalize_dispatch_kind``,
``_dispatch_transfer_batch_with_audit``) were deleted and both public functions
now delegate to the service. The service's ``run_dispatch_transfer_batch_job``
owns the session lifecycle; the controller stays read-only orchestration.

These tests lock the seam so the write op cannot silently return to the
controller layer.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

CTRL = "controllers/cash_management_controller.py"
SRVC = "services/treasury/payout_dispatch_service.py"


def _src(rel: str) -> str:
    return (BACKEND / rel).read_text(encoding="utf-8")


# ── 1. The controller no longer owns a session lifecycle in the dispatch path ──
def test_controller_dispatch_path_has_no_session_commit():
    src = _src(CTRL)
    seg = src[src.index("def admin_dispatch_transfer_batch"):src.index("def admin_resolve_transaction_exception")]
    assert "SessionLocal" not in seg, "controller dispatch path must not create sessions"
    assert ".commit()" not in seg, "controller dispatch path must not commit"
    assert ".rollback()" not in seg
    assert "run_dispatch_transfer_batch_job(" in seg, "must delegate to the service job"
    assert "dispatch_transfer_batch_with_audit(" in seg, "sync path must delegate to the service"


# ── 2. The controller's private duplicates are gone ──
def test_controller_duplicates_removed():
    tree = ast.parse(_src(CTRL))
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_normalize_dispatch_kind" not in names
    assert "_dispatch_transfer_batch_with_audit" not in names


# ── 3. The service owns the session lifecycle ──
def test_service_owns_session_lifecycle():
    src = _src(SRVC)
    seg = src[src.index("def run_dispatch_transfer_batch_job"):]
    assert "session = SessionLocal()" in seg
    assert "session.commit()" in seg
    assert "session.rollback()" in seg
    assert "session.close()" in seg
    # the service imports SessionLocal from the canonical home, not a stale shim
    assert re.search(r"from db\.database import SessionLocal", src)
    assert "from utils.dependencies import SessionLocal" not in src


# ── 4. Behavior parity: normalize_dispatch_kind contract ──
def test_normalize_dispatch_kind_contract():
    from services.treasury.payout_dispatch_service import normalize_dispatch_kind
    from fastapi import HTTPException

    assert normalize_dispatch_kind("supplier") == ("supplier", "supplier-payout-transfers")
    assert normalize_dispatch_kind("logistics") == ("logistics", "logistics-payout-transfers")
    try:
        normalize_dispatch_kind("bogus")
    except HTTPException as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("bogus kind must raise HTTPException 422")


# ── 5. Public API surface preserved ──
def test_controller_public_api_preserved():
    import controllers.cash_management_controller as ctrl

    for name in ("admin_dispatch_transfer_batch", "admin_queue_dispatch_transfer_batch"):
        assert callable(getattr(ctrl, name, None)), f"{name} missing"
    # enqueue_job still used (the closure wraps the service job)
    assert "from utils.background_jobs import enqueue_job" in _src(CTRL)
