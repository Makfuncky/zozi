"""
OKR Engine
Features: Live KPI linking, continuous performance tracking, PIP triggering
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from models.employee_models import Employee
from db.database import get_service_session

logger = logging.getLogger("zozi.okr")


def _to_iso(value):
    """Safely coerce a datetime-or-string value to an ISO string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)


class Objective:
    """Represents an OKR objective."""
    
    def __init__(
        self,
        employee_id: int,
        title: str,
        description: str,
        key_results: List[Dict[str, Any]],
        period_start: str,
        period_end: str
    ):
        self.employee_id = employee_id
        self.title = title
        self.description = description
        self.key_results = key_results
        self.period_start = period_start
        self.period_end = period_end
        self.status = "active"
        self.created_at = datetime.now(timezone.utc)
        self.progress = 0.0


class OKREngine:
    """Manages OKRs and live KPI linking."""
    
    FAILURE_THRESHOLD_DAYS = 30
    PIP_THRESHOLD = 0.5
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
    
    def create_objective(
        self,
        employee_id: int,
        title: str,
        description: str,
        key_results: List[Dict[str, Any]],
        period_start: str,
        period_end: str
    ) -> Dict[str, Any]:
        """Create a new OKR objective with live KPI key results."""
        objective = Objective(
            employee_id=employee_id,
            title=title,
            description=description,
            key_results=key_results,
            period_start=period_start,
            period_end=period_end
        )
        
        self.db.execute(
            text("""
                INSERT INTO okr_objectives (employee_id, title, description, key_results, period_start, period_end, status, created_at)
                VALUES (:eid, :title, :desc, :krs, :ps, :pe, :status, :created)
            """),
            {
                "eid": employee_id,
                "title": title,
                "desc": description,
                "krs": json.dumps(key_results),
                "ps": period_start,
                "pe": period_end,
                "status": "active",
                "created": datetime.now(timezone.utc)
            }
        )
        self.db.commit()
        
        return {
            "employee_id": employee_id,
            "title": title,
            "key_results": key_results,
            "status": "active"
        }
    
    def evaluate_kpi(
        self,
        employee_id: int,
        metric_query_hash: str,
        target_value: float,
        current_value: float
    ) -> Dict[str, Any]:
        """Evaluate a live KPI against target."""
        progress = min(current_value / target_value, 1.0) if target_value > 0 else 0.0
        
        status = "on_track"
        if progress < self.PIP_THRESHOLD:
            status = "at_risk"
        elif progress < 0.7:
            status = "behind"
        
        is_failing = self._check_persistence(employee_id, metric_query_hash, progress)
        
        result = {
            "employee_id": employee_id,
            "metric": metric_query_hash,
            "target": target_value,
            "current": current_value,
            "progress": progress,
            "status": status,
            "is_failing": is_failing,
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if is_failing:
            self._trigger_pip_workflow(employee_id, metric_query_hash, progress)
        
        return result
    
    def _check_persistence(self, employee_id: int, metric_hash: str, progress: float) -> bool:
        """Check if KPI has been failing for threshold period."""
        count = self.db.execute(
            text("""
                SELECT COUNT(*) FROM okr_evaluations
                WHERE employee_id = :eid AND metric_hash = :mhash
                  AND progress < :threshold
                  AND evaluated_at > :since
            """),
            {
                "eid": employee_id,
                "mhash": metric_hash,
                "threshold": self.PIP_THRESHOLD,
                "since": datetime.now(timezone.utc) - timedelta(days=self.FAILURE_THRESHOLD_DAYS)
            }
        ).scalar()
        
        return count >= self.FAILURE_THRESHOLD_DAYS
    
    def _trigger_pip_workflow(self, employee_id: int, metric_hash: str, progress: float):
        """Trigger Performance Improvement Plan workflow."""
        self.db.execute(
            text("""
                INSERT INTO pip_workflows (employee_id, metric_hash, progress, status, triggered_at)
                VALUES (:eid, :mhash, :prog, :status, :triggered)
            """),
            {
                "eid": employee_id,
                "mhash": metric_hash,
                "prog": progress,
                "status": "active",
                "triggered": datetime.now(timezone.utc)
            }
        )
        self.db.commit()
        
        logger.warning(f"PIP triggered for employee {employee_id} on metric {metric_hash}")
    
    def get_employee_okrs(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get all OKRs for an employee."""
        results = self.db.execute(
            text("""
                SELECT id, title, description, key_results, status, progress, created_at
                FROM okr_objectives
                WHERE employee_id = :eid
                ORDER BY created_at DESC
            """),
            {"eid": employee_id}
        ).fetchall()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "description": r[2],
                "key_results": json.loads(r[3]) if r[3] else [],
                "status": r[4],
                "progress": r[5],
                "created_at": _to_iso(r[6])
            }
            for r in results
        ]


def get_okr_engine(db: Session = None) -> OKREngine:
    return OKREngine(db or get_service_session())
