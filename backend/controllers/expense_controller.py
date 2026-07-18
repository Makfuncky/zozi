"""
Expense Claims Controller
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import get_db
from services.expense_routing import ExpenseRoutingEngine, get_expense_router

logger = logging.getLogger("zozi.api.expense")
router = APIRouter()


@router.post("/expense/route")
def route_claim(employee_id: int, amount: float, category: str, description: str,
                db: Session = Depends(get_db)):
    router = get_expense_router(db)
    return router.route_expense_claim(
        employee_id=employee_id,
        amount=Decimal(str(amount)),
        category=category,
        description=description
    )


@router.get("/expense/deadline")
def get_deadline(employee_id: int, submission_date: str, priority: str = "normal",
                 db: Session = Depends(get_db)):
    router = get_expense_router(db)
    dt = datetime.fromisoformat(submission_date)
    return {"deadline": router.calculate_reimbursement_deadline(dt, priority).isoformat()}


@router.get("/expense/chain/{employee_id}")
def get_chain(employee_id: int, amount: float, db: Session = Depends(get_db)):
    router = get_expense_router(db)
    return {"approval_chain": router.get_approval_chain(employee_id, Decimal(str(amount)))}


@router.get("/contractor-milestones")
def list_contractor_milestones(db: Session = Depends(get_db)):
    """Return contractor payment/delivery milestones."""
    rows = db.execute(
        text("""
            SELECT m.id, m.employee_id, e.employee_code, m.milestone_type,
                   m.due_date, m.status
            FROM contractor_milestones m
            LEFT JOIN employees e ON e.id = m.employee_id
            ORDER BY m.due_date ASC
        """)
    ).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "milestone_type": r[3],
            "due_date": r[4],
            "status": r[5],
        }
        for r in rows
    ]
