"""
GCC Compliance Controller
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from controllers.auth_controller import get_current_user
from services.compliance_engine import GCCComplianceEngine, get_compliance_engine

logger = logging.getLogger("zozi.api.compliance")
router = APIRouter()


@router.get("/compliance/work-hours/{employee_id}")
def check_work_hours(employee_id: int, date: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    return engine.validate_work_hours(employee_id, dt)


@router.get("/compliance/report/{employee_id}")
def get_report(employee_id: int, month: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(month + "-01")
    return engine.get_compliance_report(employee_id, dt)


@router.post("/compliance/overtime")
def calculate_overtime(employee_id: int, week_start: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(week_start + "-01")
    return {"overtime_hours": str(engine.calculate_overtime(employee_id, dt))}
