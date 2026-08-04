"""Employee Lifecycle Service — Onboarding pipeline and Offboarding workflow.
Leverages existing employee_models and the gap-table migration for
onboarding_pipelines, onboarding_steps, and offboarding_cases.
"""

__all__ = [
    "create_onboarding_pipeline",
    "complete_onboarding_step",
    "get_onboarding_progress",
    "get_overdue_onboardings",
    "initiate_offboarding",
    "complete_offboarding_step",
    "get_offboarding_status",
    "cancel_offboarding",
]

import json
import logging
from datetime import datetime, timedelta, date
from typing import Any, Optional, List, Dict, Any as _Any

from sqlalchemy.orm import Session
from sqlalchemy import and_

from data.models import User
from data.models_employee_models import (
    Employee, EmployeeAsset, EmployeeDocument, DynamicQRSession,
    EmployeeBiometric, PhysicalIDCard,
)
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


# ── Default Onboarding Steps ───────────────────────────────────

DEFAULT_ONBOARDING_STEPS = [
    {"step_name": "document_collection", "label": "Document Collection", "sla_hours": 48,
     "description": "Collect ID, passport, visa, and educational certificates"},
    {"step_name": "background_check", "label": "Background & Watchlist Screening", "sla_hours": 24,
     "description": "Dangerous goods / sanctions / watchlist screening via external API — blocks onboarding if flagged"},
    {"step_name": "biometric_enrollment", "label": "Biometric Enrollment", "sla_hours": 24,
     "description": "Enroll fingerprint and/or face recognition"},
    {"step_name": "equipment_assignment", "label": "Equipment Assignment", "sla_hours": 24,
     "description": "Assign laptop, phone, badge, and other equipment"},
    {"step_name": "id_card_issuance", "label": "ID Card Issuance", "sla_hours": 48,
     "description": "Issue physical ID card with employee photo and details"},
    {"step_name": "orientation", "label": "Orientation & Training", "sla_hours": 8,
     "description": "HR induction, policy review, and department orientation"},
    {"step_name": "system_access", "label": "System Access Provisioning", "sla_hours": 4,
     "description": "Create email, ERP, and platform accounts"},
    {"step_name": "buddy_assignment", "label": "Buddy Assignment", "sla_hours": 2,
     "description": "Assign onboarding buddy from the same team"},
]

DEFAULT_OFFBOARDING_STEPS = [
    {"step_name": "exit_interview", "label": "Exit Interview", "description": "Conduct exit interview and collect feedback"},
    {"step_name": "asset_reclamation", "label": "Asset Reclamation", "description": "Return laptop, phone, badge, keys, and other assets"},
    {"step_name": "access_revocation", "label": "Access Revocation", "description": "Revoke system access, email, VPN, and door access"},
    {"step_name": "session_invalidation", "label": "Session Invalidation", "description": "Kill all active sessions and revoke tokens"},
    {"step_name": "final_payroll", "label": "Final Payroll", "description": "Calculate EOSB, final salary, and accrued leave encashment"},
    {"step_name": "knowledge_transfer", "label": "Knowledge Transfer", "description": "Document handover of ongoing tasks and projects"},
]


# ── Onboarding ─────────────────────────────────────────────────

def create_onboarding_pipeline(
    db: Session,
    employee_id: int,
    manager_id: Optional[int] = None,
    custom_steps: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create an onboarding pipeline for a new employee with default or custom steps."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} not found")

    # Validate employee status
    if employee.employment_status != "active":
        employee.employment_status = "active"

    steps = custom_steps or DEFAULT_ONBOARDING_STEPS

    # Create pipeline record using the gap-table model
    # We use raw SQL/table insert since the model may not be loaded yet
    now = _utcnow()
    pipeline_data = {
        "employee_id": employee_id,
        "country_code": employee.country_code,
        "current_step": steps[0]["step_name"] if steps else None,
        "total_steps": len(steps),
        "completed_steps": 0,
        "status": "in_progress",
        "started_at": now,
        "due_date": now + timedelta(hours=sum(s.get("sla_hours", 24) for s in steps)),
        "notes": None,
    }
    # Use bulk insert to avoid model import issues — the gap migration creates these
    try:
        from sqlalchemy import text
        result = db.execute(
            text("""
                INSERT INTO onboarding_pipelines
                    (employee_id, country_code, current_step, total_steps,
                     completed_steps, status, started_at, due_date)
                VALUES
                    (:employee_id, :country_code, :current_step, :total_steps,
                     :completed_steps, :status, :started_at, :due_date)
                RETURNING id
            """),
            pipeline_data,
        )
        pipeline_id = result.scalar()

        # Insert each step
        for order, step in enumerate(steps):
            db.execute(
                text("""
                    INSERT INTO onboarding_steps
                        (pipeline_id, employee_id, step_name, label, description,
                         sla_hours, step_order, status)
                    VALUES
                        (:pipeline_id, :employee_id, :step_name, :label, :description,
                         :sla_hours, :step_order, 'pending')
                """),
                {
                    "pipeline_id": pipeline_id,
                    "employee_id": employee_id,
                    "step_name": step["step_name"],
                    "label": step["label"],
                    "description": step.get("description", ""),
                    "sla_hours": step.get("sla_hours", 24),
                    "step_order": order,
                },
            )

        db.commit()
        logger.info("Onboarding pipeline %s created for employee %s", pipeline_id, employee_id)
        return {"id": pipeline_id, "employee_id": employee_id, "total_steps": len(steps), "status": "in_progress"}
    except Exception as e:
        db.rollback()
        logger.error("Failed to create onboarding pipeline: %s", e)
        raise


def complete_onboarding_step(
    db: Session,
    pipeline_id: int,
    step_name: str,
    completed_by: Optional[int] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark an onboarding step as completed and advance the pipeline.

    Only increments ``completed_steps`` if the step was actually pending
    (i.e. the UPDATE matched at least one row).  Calling this on an already
    completed or non-existent step is a no-op for the counter.
    """
    from sqlalchemy import text

    # Update the step and capture how many rows were actually changed
    result = db.execute(
        text("""
            UPDATE onboarding_steps
            SET status = 'completed',
                completed_at = :now,
                completed_by = :completed_by,
                notes = :notes
            WHERE pipeline_id = :pipeline_id AND step_name = :step_name AND status = 'pending'
        """),
        {
            "pipeline_id": pipeline_id,
            "step_name": step_name,
            "completed_by": completed_by,
            "notes": notes,
            "now": _utcnow(),
        },
    )
    rows_affected = result.rowcount

    # Get the pipeline
    pipeline = db.execute(
        text("SELECT id, total_steps, completed_steps, employee_id FROM onboarding_pipelines WHERE id = :id"),
        {"id": pipeline_id},
    ).mappings().first()

    if not pipeline:
        raise ValueError(f"Pipeline {pipeline_id} not found")

    # Only increment counter if the step UPDATE actually changed a row
    if rows_affected > 0:
        # ── Special handling: background_check runs watchlist screening ──
        if step_name == "background_check":
            return _handle_background_check_step(
                db, pipeline_id, pipeline, step_name, completed_by, notes,
            )

        new_completed = pipeline["completed_steps"] + 1
        db.execute(
            text("""
                UPDATE onboarding_pipelines
                SET completed_steps = :completed,
                    status = CASE WHEN :completed >= total_steps THEN 'completed' ELSE 'in_progress' END,
                    completed_at = CASE WHEN :completed >= total_steps THEN :now ELSE NULL END
                WHERE id = :id
            """),
            {"completed": new_completed, "id": pipeline_id, "now": _utcnow()},
        )

        # Auto-assign next step from onboarding_steps table
        if new_completed < pipeline["total_steps"]:
            next_step = db.execute(
                text("""
                    SELECT step_name FROM onboarding_steps
                    WHERE pipeline_id = :pipeline_id AND status = 'pending'
                    ORDER BY step_order ASC LIMIT 1
                """),
                {"pipeline_id": pipeline_id},
            ).mappings().first()
            if next_step:
                db.execute(
                    text("UPDATE onboarding_pipelines SET current_step = :step WHERE id = :id"),
                    {"step": next_step["step_name"], "id": pipeline_id},
                )

        new_progress = new_completed
    else:
        # No row updated — step was already completed or doesn't exist
        new_progress = pipeline["completed_steps"]

    db.commit()
    return {
        "pipeline_id": pipeline_id,
        "step": step_name,
        "completed": True,
        "progress": f"{new_progress}/{pipeline['total_steps']}",
    }


def get_onboarding_progress(db: Session, pipeline_id: int) -> Dict[str, Any]:
    """Get detailed progress of an onboarding pipeline."""
    from sqlalchemy import text

    pipeline = db.execute(
        text("""
            SELECT id, employee_id, country_code, current_step, total_steps,
                   completed_steps, status, started_at, due_date, completed_at
            FROM onboarding_pipelines WHERE id = :id
        """),
        {"id": pipeline_id},
    ).mappings().first()

    if not pipeline:
        raise ValueError(f"Pipeline {pipeline_id} not found")

    steps = db.execute(
        text("""
            SELECT id, step_name, label, description, status, sla_hours,
                   step_order, completed_at, notes
            FROM onboarding_steps
            WHERE pipeline_id = :pipeline_id
            ORDER BY step_order ASC
        """),
        {"pipeline_id": pipeline_id},
    ).mappings().all()

    due_date_val = pipeline["due_date"]
    if isinstance(due_date_val, str):
        from datetime import datetime as _dt_parser
        due_date_val = _dt_parser.fromisoformat(due_date_val)

    return {
        "pipeline": dict(pipeline),
        "steps": [dict(s) for s in steps],
        "is_overdue": bool(due_date_val) and _utcnow() > due_date_val,
    }


def get_overdue_onboardings(db: Session) -> List[Dict[str, Any]]:
    """Get all onboarding pipelines that are past their due date."""
    from sqlalchemy import text

    now = _utcnow()
    rows = db.execute(
        text("""
            SELECT p.id, p.employee_id, p.country_code, p.current_step,
                   p.total_steps, p.completed_steps, p.due_date,
                   e.employee_code, e.department, e.position
            FROM onboarding_pipelines p
            LEFT JOIN employees e ON e.id = p.employee_id
            WHERE p.status = 'in_progress'
            ORDER BY p.due_date ASC
        """),
    ).mappings().all()

    # Filter overdue in Python — SQLite stores due_date as TEXT, can't compare with datetime
    result = []
    for r in rows:
        due = r["due_date"]
        if isinstance(due, str):
            from datetime import datetime as _dt_parser
            due = _dt_parser.fromisoformat(due)
        if due and now > due:
            result.append(dict(r))
    return result


# ── Offboarding ────────────────────────────────────────────────

def initiate_offboarding(
    db: Session,
    employee_id: int,
    reason: str,
    initiated_by: int,
    notice_period_days: int = 30,
    custom_steps: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Initiate the offboarding workflow for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} not found")

    # Prevent offboarding an already-terminated employee
    if employee.employment_status == "terminated":
        raise ValueError(f"Employee {employee_id} is already terminated")

    steps = custom_steps or DEFAULT_OFFBOARDING_STEPS
    now = _utcnow()
    proposed_exit = now + timedelta(days=notice_period_days)

    from sqlalchemy import text

    # Create offboarding case
    result = db.execute(
        text("""
            INSERT INTO offboarding_cases
                (employee_id, country_code, reason, initiated_by,
                 status, total_steps, completed_steps, current_step,
                 initiated_at, proposed_exit_date, notice_period_days)
            VALUES
                (:employee_id, :country_code, :reason, :initiated_by,
                 'in_progress', :total_steps, 0, :current_step,
                 :now, :proposed_exit, :notice_period)
            RETURNING id
        """),
        {
            "employee_id": employee_id,
            "country_code": employee.country_code,
            "reason": reason,
            "initiated_by": initiated_by,
            "total_steps": len(steps),
            "current_step": steps[0]["step_name"],
            "now": now,
            "proposed_exit": proposed_exit,
            "notice_period": notice_period_days,
        },
    )
    case_id = result.scalar()

    # Update employee status to 'terminating'
    employee.employment_status = "terminating"
    db.flush()

    db.commit()
    logger.info("Offboarding case %s initiated for employee %s", case_id, employee_id)
    return {"id": case_id, "employee_id": employee_id, "status": "in_progress", "steps": len(steps)}


def complete_offboarding_step(
    db: Session,
    case_id: int,
    step_name: str,
    completed_by: Optional[int] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Complete an offboarding step. On final step, finalize the offboarding."""
    from sqlalchemy import text

    now = _utcnow()
    # Determine the next step from DEFAULT_OFFBOARDING_STEPS (no offboarding_steps table exists)
    case_rec = db.execute(
        text("SELECT completed_steps, total_steps FROM offboarding_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()
    if not case_rec:
        raise ValueError(f"Offboarding case {case_id} not found")

    new_completed = case_rec["completed_steps"] + 1
    next_step_name = "completed"
    if new_completed < case_rec["total_steps"] and case_rec["total_steps"] > 0:
        # Look up the next step from the predefined list by index
        step_idx = min(new_completed, len(DEFAULT_OFFBOARDING_STEPS) - 1)
        next_step_name = DEFAULT_OFFBOARDING_STEPS[step_idx]["step_name"]

    db.execute(
        text("""
            UPDATE offboarding_cases
            SET completed_steps = completed_steps + 1,
                current_step = :next_step,
                status = CASE WHEN completed_steps + 1 >= total_steps THEN 'completed' ELSE 'in_progress' END,
                completed_at = CASE WHEN completed_steps + 1 >= total_steps THEN :now ELSE NULL END
            WHERE id = :id
        """),
        {"id": case_id, "next_step": next_step_name, "now": now},
    )

    # If this is the access_revocation or session_invalidation step, perform cleanup
    if step_name == "session_invalidation":
        _invalidate_employee_sessions(db, case_id)
    elif step_name == "asset_reclamation":
        _mark_assets_returned(db, case_id)
    elif step_name == "final_payroll":
        _calculate_final_payroll(db, case_id)

    db.commit()
    return {"case_id": case_id, "step": step_name, "completed": True}


def get_offboarding_status(db: Session, case_id: int) -> Dict[str, Any]:
    """Get detailed status of an offboarding case."""
    from sqlalchemy import text

    case = db.execute(
        text("""
            SELECT id, employee_id, country_code, reason, status,
                   total_steps, completed_steps, current_step,
                   initiated_at, proposed_exit_date, completed_at, notice_period_days
            FROM offboarding_cases WHERE id = :id
        """),
        {"id": case_id},
    ).mappings().first()

    if not case:
        raise ValueError(f"Offboarding case {case_id} not found")

    return dict(case)


def cancel_offboarding(db: Session, case_id: int, reason: str) -> Dict[str, Any]:
    """Cancel an offboarding workflow (e.g., employee decides to stay).

    Raises ``ValueError`` if the case has already been cancelled or completed.
    """
    from sqlalchemy import text

    case = db.execute(
        text("SELECT id, employee_id, status FROM offboarding_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()

    if not case:
        raise ValueError(f"Offboarding case {case_id} not found")

    if case["status"] in ("cancelled", "completed"):
        raise ValueError(
            f"Offboarding case {case_id} is already {case['status']}"
        )

    db.execute(
        text("""
            UPDATE offboarding_cases
            SET status = 'cancelled', cancellation_reason = :reason, cancelled_at = :now
            WHERE id = :id
        """),
        {"reason": reason, "now": _utcnow(), "id": case_id},
    )

    # Revert employee status
    employee = db.query(Employee).filter(Employee.id == case["employee_id"]).first()
    if employee and employee.employment_status == "terminating":
        employee.employment_status = "active"

    db.commit()
    logger.info("Offboarding case %s cancelled: %s", case_id, reason)
    return {"case_id": case_id, "status": "cancelled"}


# ── Background check handler ────────────────────────────────


def _handle_background_check_step(
    db: Session,
    pipeline_id: int,
    pipeline: Any,
    step_name: str,
    completed_by: Optional[int] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the background check step: run watchlist screening.

    If the check passes (``clear``) the pipeline advances normally.
    If the check fails (``flagged``) the pipeline enters ``blocked``
    status and no further steps can be completed until the block is
    resolved.

    If the external API returns an ``error`` status (network timeout, etc.)
    the pipeline enters ``pending_review`` — not advanced, not blocked,
    so HR can manually inspect and decide.
    """
    from sqlalchemy import text
    from services.background_check import (
        run_background_check,
        BACKGROUND_CHECK_FLAGGED,
        BACKGROUND_CHECK_CLEAR,
    )
    from data.models_employee_models import Employee
    from data.models import User

    # Look up the employee's full name (stored on the User model)
    employee = db.query(Employee).filter(Employee.id == pipeline["employee_id"]).first()
    user_name = None
    employee_code = "UNKNOWN"
    if employee:
        employee_code = employee.employee_code or "UNKNOWN"
        user = db.query(User).filter(User.id == employee.user_id).first()
        user_name = user.full_name if user and user.full_name else f"Employee#{pipeline['employee_id']}"
    else:
        user_name = f"Employee#{pipeline['employee_id']}"

    # Run the screening
    check_result = run_background_check(
        employee_code=employee_code,
        full_name=user_name,
        country_code=pipeline.get("country_code") or "OM",
    )

    check_json = json.dumps(check_result.to_dict())

    # Store the result on the **step** notes so pipeline.notes is preserved
    db.execute(
        text("""
            UPDATE onboarding_steps
            SET notes = :check_json
            WHERE pipeline_id = :pipeline_id AND step_name = :step_name
        """),
        {"pipeline_id": pipeline_id, "step_name": step_name, "check_json": check_json},
    )

    if check_result.status == BACKGROUND_CHECK_FLAGGED:
        # Blocked — don't advance, keep current_step as "background_check"
        db.execute(
            text("""
                UPDATE onboarding_pipelines
                SET status = 'blocked', notes = notes
                WHERE id = :id
            """),
            {"id": pipeline_id},
        )
        db.commit()
        logger.warning(
            "Background check FLAGGED for employee %s (pipeline %s): %s",
            pipeline["employee_id"], pipeline_id, check_result.details,
        )
        return {
            "pipeline_id": pipeline_id,
            "step": step_name,
            "completed": True,
            "blocked": True,
            "block_reason": check_result.details,
            "check_result": check_result.to_dict(),
            "progress": f"{pipeline['completed_steps']}/{pipeline['total_steps']}",
        }

    if check_result.status != BACKGROUND_CHECK_CLEAR:
        # API error / unknown — pending_review, don't advance
        db.execute(
            text("""
                UPDATE onboarding_pipelines
                SET status = 'pending_review', notes = notes
                WHERE id = :id
            """),
            {"id": pipeline_id},
        )
        db.commit()
        logger.warning(
            "Background check ERROR for employee %s (pipeline %s): %s",
            pipeline["employee_id"], pipeline_id, check_result.details,
        )
        return {
            "pipeline_id": pipeline_id,
            "step": step_name,
            "completed": True,
            "blocked": False,
            "pending_review": True,
            "error_detail": check_result.details,
            "check_result": check_result.to_dict(),
            "progress": f"{pipeline['completed_steps']}/{pipeline['total_steps']}",
        }

    # Check passed — advance normally
    new_completed = pipeline["completed_steps"] + 1
    db.execute(
        text("""
            UPDATE onboarding_pipelines
            SET completed_steps = :completed,
                status = CASE WHEN :completed >= total_steps THEN 'completed' ELSE 'in_progress' END,
                completed_at = CASE WHEN :completed >= total_steps THEN :now ELSE NULL END
            WHERE id = :id
        """),
        {"completed": new_completed, "id": pipeline_id, "now": _utcnow()},
    )

    # Find the next pending step
    next_step = db.execute(
        text("""
            SELECT step_name FROM onboarding_steps
            WHERE pipeline_id = :pipeline_id AND status = 'pending'
            ORDER BY step_order ASC LIMIT 1
        """),
        {"pipeline_id": pipeline_id},
    ).mappings().first()
    if next_step:
        db.execute(
            text("UPDATE onboarding_pipelines SET current_step = :step WHERE id = :id"),
            {"step": next_step["step_name"], "id": pipeline_id},
        )

    db.commit()
    return {
        "pipeline_id": pipeline_id,
        "step": step_name,
        "completed": True,
        "blocked": False,
        "pending_review": False,
        "check_result": check_result.to_dict(),
        "progress": f"{new_completed}/{pipeline['total_steps']}",
    }


# ── Internal cleanup helpers ───────────────────────────────────

def _invalidate_employee_sessions(db: Session, case_id: int) -> int:
    """Kill all active QR sessions and mark the employee as terminated."""
    from sqlalchemy import text

    case = db.execute(
        text("SELECT employee_id FROM offboarding_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()
    if not case:
        return 0

    now = _utcnow()
    # Expire all QR sessions
    expired = db.execute(
        text("""
            UPDATE dynamic_qr_sessions
            SET expires_at = :now, used_at = :now
            WHERE employee_id = :eid AND expires_at > :now
        """),
        {"now": now, "eid": case["employee_id"]},
    ).rowcount

    # Update employee status
    employee = db.query(Employee).filter(Employee.id == case["employee_id"]).first()
    if employee:
        employee.employment_status = "terminated"
        employee.termination_date = now.date()

    return expired


def _mark_assets_returned(db: Session, case_id: int) -> int:
    """Mark all employee assets as returned."""
    from sqlalchemy import text

    case = db.execute(
        text("SELECT employee_id FROM offboarding_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()
    if not case:
        return 0

    now = _utcnow()
    count = db.execute(
        text("""
            UPDATE employee_assets
            SET status = 'returned', returned_at = :now
            WHERE employee_id = :eid AND status = 'assigned'
        """),
        {"now": now, "eid": case["employee_id"]},
    ).rowcount
    return count


def _calculate_final_payroll(db: Session, case_id: int) -> Dict[str, Any]:
    """Trigger final payroll calculation for the offboarding employee."""
    from sqlalchemy import text

    case = db.execute(
        text("SELECT employee_id FROM offboarding_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()
    if not case:
        return {}

    # Delegate to payroll engine for EOSB calculation
    from services.payroll_engine import PayrollEngine
    engine = PayrollEngine(db)
    eosb = engine.calculate_eosb(case["employee_id"])

    return {"employee_id": case["employee_id"], "eosb_amount": float(eosb)}
