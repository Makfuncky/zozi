"""POSITIVE / NEGATIVE fixtures for every detector.

Two detector bugs shipped before this file existed:

1. ``s05_wiring.py`` sliced ``splitlines()[start:end]`` with a **1-based** AST
   ``lineno``, so the ``def`` line — where an auth guard lives — was skipped.
   Every endpoint guarded by ``Depends(require_admin)`` was reported ungated:
   46 of 48 findings false, 3 of them P0 blockers.
2. ``zz_core/probes.py`` gave ``CLUSTER-idempotency`` a ``text_absent`` probe.
   The defect *is* the presence of ``idempotency_key: Optional[str] = None``, so
   the probe asserted the opposite of its own claim and the verifier discarded 10
   genuine P0 findings as false positives.

Both were invisible because no test ever ran a detector against a known positive
and a known negative. That is what this file is for.

Each case is a minimal, self-contained snippet. ``POSITIVE`` means a correct
detector MUST flag it; ``NEGATIVE`` means a correct detector MUST NOT. A detector
that fails a NEGATIVE case produces false positives; one that fails a POSITIVE
case produces false negatives — both are silent, which is why they survived.
"""
from __future__ import annotations

#: (filename, content, expectation, detector_key)
#: ``expectation`` is "flag" or "silent".
FIXTURES: list[tuple[str, str, str, str]] = [
    # ---------------------------------------------------------------- auth gate
    (
        "auth_gated_admin.py",
        '''
from fastapi import APIRouter, Depends
from backend.rbac.guards import require_admin

router = APIRouter(prefix="/admin/analytics", tags=["admin"])


@router.get("/health")
def health(_: dict = Depends(require_admin)):
    """Guarded by Depends(require_admin) — NOT ungated."""
    return {"status": "ok"}
''',
        "silent", "ungated_route",
    ),
    (
        "auth_gated_feature.py",
        '''
from fastapi import APIRouter, Depends
from backend.rbac.guards import require_feature

router = APIRouter(prefix="/admin/security", tags=["admin"])


@router.get("/rbac/catalog")
def get_rbac_catalog(_gate: None = Depends(require_feature("security.read"))):
    return {"features": []}
''',
        "silent", "ungated_route",
    ),
    (
        "auth_gated_multiline.py",
        '''
from fastapi import APIRouter, Depends, Session
from backend.db.session import get_db
from backend.rbac.guards import require_feature

router = APIRouter(prefix="/admin/analytics", tags=["admin"])


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    __: None = Depends(require_feature("analytics.dashboard.view")),
):
    return {"rows": []}
''',
        "silent", "ungated_route",
    ),
    (
        "auth_ungated.py",
        '''
from fastapi import APIRouter

router = APIRouter(prefix="/admin/billing", tags=["admin"])


@router.get("/invoices")
def list_invoices():
    """No auth dependency at all — a genuine defect."""
    return []
''',
        "flag", "ungated_route",
    ),
    (
        "auth_logout_ungated.py",
        '''
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/customer", tags=["auth"])


@router.post("/logout")
def logout(request: Request, response: Response):
    return {"ok": True}
''',
        "flag", "ungated_route",
    ),

    # ------------------------------------------------------------- silent except
    (
        "silent_except_pass.py",
        '''
def load_profile(user_id):
    try:
        return repository.fetch(user_id)
    except Exception:
        pass
''',
        "flag", "silent_except",
    ),
    (
        "silent_except_ellipsis.py",
        '''
def settle_batch(batch_id):
    try:
        return ledger.post(batch_id)
    except ValueError:
        ...
''',
        "flag", "silent_except",
    ),
    (
        "logged_except_ok.py",
        '''
import logging

logger = logging.getLogger(__name__)


def load_profile(user_id):
    try:
        return repository.fetch(user_id)
    except Exception:
        logger.warning("profile load failed", exc_info=True)
        raise
''',
        "silent", "silent_except",
    ),

    # ------------------------------------------------------------------ float money
    (
        "float_money.py",
        '''
from sqlalchemy.orm import Mapped, mapped_column


class Order:
    order_total: Mapped[float] = mapped_column()
''',
        "flag", "float_money",
    ),
    (
        "decimal_money_ok.py",
        '''
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column


class Order:
    order_total: Mapped[Decimal] = mapped_column()
''',
        "silent", "float_money",
    ),

    # ------------------------------------------------------------ timestamp default
    (
        "python_timestamp_default.py",
        '''
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column


class Thread:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
''',
        "flag", "timestamp_default",
    ),
    (
        "server_timestamp_ok.py",
        '''
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class Thread:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
''',
        "silent", "timestamp_default",
    ),

    # ------------------------------------------------------------ relationship lazy
    (
        "relationship_lazy_select.py",
        '''
from sqlalchemy.orm import relationship


class Message:
    user = relationship("User", lazy="select")
''',
        "flag", "relationship_lazy",
    ),
    (
        "relationship_selectin_ok.py",
        '''
from sqlalchemy.orm import relationship


class Message:
    user = relationship("User", lazy="selectin")
''',
        "silent", "relationship_lazy",
    ),

    # ---------------------------------------------------------------- idempotency
    # POSITIVE: Law 239 requires the key on money paths. An *optional* key is the
    # defect, so this MUST be flagged. An earlier probe inverted this and the
    # verifier discarded the finding.
    (
        "idempotency_optional.py",
        '''
from typing import Optional


def capture_payment(charge_id: str, idempotency_key: Optional[str] = None):
    return gateway.charge(charge_id, idempotency_key)
''',
        "flag", "idempotency_optional",
    ),
    (
        "idempotency_required_ok.py",
        '''
def capture_payment(charge_id: str, idempotency_key: str):
    return gateway.charge(charge_id, idempotency_key)
''',
        "silent", "idempotency_optional",
    ),

    # ------------------------------------------------------------------- dead branch
    (
        "unreachable_return.py",
        '''
def settle(order):
    return order.settled
    if order.archived:
        return order.settled_at
''',
        "flag", "dead_branch",
    ),
    (
        "reachable_code_ok.py",
        '''
def settle(order):
    if order.archived:
        return order.settled_at
    return order.settled
''',
        "silent", "dead_branch",
    ),
]


def by_detector() -> dict[str, list[tuple[str, str, str]]]:
    """Grouped as detector -> [(filename, expectation, content)]."""
    out: dict[str, list[tuple[str, str, str]]] = {}
    for name, content, expectation, detector in FIXTURES:
        out.setdefault(detector, []).append((name, expectation, content))
    return out


def counts() -> dict[str, dict[str, int]]:
    """detector -> {"flag": n, "silent": n} — a detector needs both to be tested."""
    out: dict[str, dict[str, int]] = {}
    for _n, _c, expectation, detector in FIXTURES:
        slot = out.setdefault(detector, {"flag": 0, "silent": 0})
        slot[expectation] += 1
    return out


def write_all(directory) -> list[str]:
    """Materialise every fixture as a real file. Returns the paths written."""
    from pathlib import Path
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content, _expectation, _detector in FIXTURES:
        p = d / name
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(str(p))
    return written