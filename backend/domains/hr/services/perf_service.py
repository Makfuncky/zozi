"""HR Performance Service — encapsulates OKR/KPI/performance review logic."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_objective(db: Session, **kwargs) -> dict:
    from domains.hr.services.performance.performance_service import create_objective as _svc
    return _svc(db=db, **kwargs)


def get_objective_tree(db: Session, objective_id: int) -> Optional[dict]:
    from domains.hr.services.performance.performance_service import get_objective_tree as _svc
    return _svc(db, objective_id)


def update_objective_progress(db: Session, objective_id: int, **kwargs) -> dict:
    from domains.hr.services.performance.performance_service import update_objective_progress as _svc
    return _svc(db, objective_id, **kwargs)


def create_kpi_metric(db: Session, **kwargs) -> dict:
    from domains.hr.services.performance.performance_service import create_kpi_metric as _svc
    return _svc(db=db, **kwargs)


def record_kpi_value(db: Session, kpi_id: int, **kwargs) -> dict:
    from domains.hr.services.performance.performance_service import record_kpi_value as _svc
    return _svc(db, kpi_id, **kwargs)


def get_kpi_dashboard(db: Session, employee_id: int) -> dict:
    from domains.hr.services.performance.performance_service import get_kpi_dashboard as _svc
    return _svc(db, employee_id)


def submit_performance_review(db: Session, **kwargs) -> dict:
    from domains.hr.services.performance.performance_service import submit_performance_review as _svc
    return _svc(db=db, **kwargs)


def get_employee_reviews(db: Session, employee_id: int, review_cycle: Optional[str] = None) -> list:
    from domains.hr.services.performance.performance_service import get_employee_reviews as _svc
    return _svc(db, employee_id, review_cycle=review_cycle)


def compute_performance_health(db: Session, employee_id: int) -> dict:
    from domains.hr.services.performance.performance_service import compute_performance_health as _svc
    return _svc(db, employee_id)


def get_performance_health_board(db: Session, manager_employee_id: int, department: Optional[str] = None) -> dict:
    from domains.hr.services.performance.performance_service import get_performance_health_board as _svc
    return _svc(db, manager_employee_id, department=department)
