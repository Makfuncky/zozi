"""controllers.hr.succession_controller (CONTROLLERS layer).

Wraps ``services.hr.succession_service`` and exposes the succession & alumni
network endpoints. The HTTP contract is declared with ``core.route_contract``
decorators so ``routers/generated/auto_router.py`` can auto-generate the thin
router — the previous hand-written ``routers/succession.py`` only instantiated
the services and built the eligibility response inline, which is
controller-level orchestration that now lives here.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from core.route_contract import get, post

from domains.hr.services.succession_service import (
    get_alumni_network,
    get_succession_matrix,
)

@get("/bench-strength", deps=["user", "db"])
def get_bench_strength_report(current_user: dict = None, db: Session = None):
    """Return the bench-strength report."""
    service = get_succession_matrix(db)
    return service.get_bench_strength_report()

@get("/successors/{role_name}", deps=["user", "db"], response_model=List[dict])
def get_successors(role_name: str, current_user: dict = None, db: Session = None):
    """Identify successors for a given role."""
    service = get_succession_matrix(db)
    return service.identify_successors(role_name)

@post("/alumni", deps=["user", "db"], query=["employee_id"])
def grant_alumni_status(employee_id: int, current_user: dict = None, db: Session = None):
    """Grant alumni status to an employee."""
    service = get_alumni_network(db)
    return service.grant_alumni_status(employee_id)

@get("/alumni/{employee_id}/eligibility", deps=["user", "db"])
def check_alumni_eligibility(employee_id: int, current_user: dict = None, db: Session = None):
    """Check whether an employee is eligible for alumni status."""
    service = get_alumni_network(db)
    is_eligible = service.check_alumni_eligibility(employee_id)
    return {"employee_id": employee_id, "is_eligible": is_eligible}

__all__ = [
    "get_bench_strength_report",
    "get_successors",
    "grant_alumni_status",
    "check_alumni_eligibility",
]
