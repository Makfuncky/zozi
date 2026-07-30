"""HR Dashboard router — onboarding pipeline, performance health, activity feed.
Also exposes a WebSocket endpoint for real-time activity push.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text

from controllers.auth_controller import get_current_user
from db.database import get_db
from utils.country_rls import enforce_country_access
from utils.datetime_utils import utcnow as _utcnow
from utils.websocket_manager import manager as ws_manager, ACTIVITY_ROOM
from utils.auth import decode_token as _decode_token

logger = logging.getLogger(__name__)

router = APIRouter()


# ── WebSocket: Real-Time Activity Feed ─────────────────────────
@router.websocket("/ws/hr/activity")
async def websocket_hr_activity(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time HR activity feed.
    
    Clients connect with a JWT token. Events are broadcast to all
    connected clients whenever `log_activity()` is called.
    """
    # Authenticate
    payload = _decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return
    user_id = int(user_id)

    await ws_manager.connect(websocket, ACTIVITY_ROOM, user_id=user_id)
    await websocket.send_json({"type": "connected", "room": ACTIVITY_ROOM, "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, ACTIVITY_ROOM)
    except Exception as exc:
        logger.exception("HR Activity WebSocket error: %s", exc)
        ws_manager.disconnect(websocket, ACTIVITY_ROOM)


# ── REST Endpoints ──────────────────────────────────────────────


@router.get("/hr/dashboard")
def get_hr_dashboard(
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    days: int = Query(7, ge=1, le=90, description="Recent activity window in days"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return HR dashboard data: onboarding pipeline, performance health, activity feed."""
    result = {}
    country_filter = ""
    params: dict = {"days": days}

    if country_code:
        enforce_country_access(country_code, db=db)
        country_filter = " AND country_code = :country_code"
        params["country_code"] = country_code

    now = _utcnow()

    # ── Onboarding Pipeline Stats ──
    try:
        pipeline_counts = db.execute(
            text(f"""
                SELECT
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'in_progress' AND due_date < :now THEN 1 ELSE 0 END) as overdue,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM onboarding_pipelines
                WHERE 1=1 {country_filter}
            """),
            {**params, "now": now},
        ).mappings().first()

        overdue_items = db.execute(
            text(f"""
                SELECT p.id, p.employee_id, p.current_step, p.total_steps,
                       p.completed_steps, p.due_date,
                       e.employee_code, e.department, e.position
                FROM onboarding_pipelines p
                LEFT JOIN employees e ON e.id = p.employee_id
                WHERE p.status = 'in_progress' AND p.due_date < :now {country_filter}
                ORDER BY p.due_date ASC
                LIMIT 20
            """),
            {**params, "now": now},
        ).mappings().all()

        result["onboarding"] = {
            "stats": dict(pipeline_counts) if pipeline_counts else {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0},
            "overdue_items": [dict(r) for r in overdue_items],
        }
    except Exception as e:
        logger.warning("Onboarding data unavailable (migration may not be run): %s", e)
        result["onboarding"] = {"stats": {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0}, "overdue_items": []}

    # ── Performance Health Board ──
    try:
        health_data = db.execute(
            text(f"""
                SELECT
                    SUM(CASE WHEN performance_score >= 4.0 THEN 1 ELSE 0 END) as green,
                    SUM(CASE WHEN performance_score >= 2.5 AND performance_score < 4.0 THEN 1 ELSE 0 END) as amber,
                    SUM(CASE WHEN performance_score < 2.5 AND performance_score IS NOT NULL THEN 1 ELSE 0 END) as red,
                    SUM(CASE WHEN performance_score IS NULL THEN 1 ELSE 0 END) as not_scored,
                    ROUND(AVG(performance_score), 2) as avg_score
                FROM employees
                WHERE employment_status = 'active' {country_filter}
            """),
            params,
        ).mappings().first()

        top_performers = db.execute(
            text(f"""
                SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
                FROM employees e
                WHERE e.employment_status = 'active'
                  AND e.performance_score IS NOT NULL {country_filter}
                ORDER BY e.performance_score DESC
                LIMIT 10
            """),
            params,
        ).mappings().all()

        bottom_performers = db.execute(
            text(f"""
                SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
                FROM employees e
                WHERE e.employment_status = 'active'
                  AND e.performance_score IS NOT NULL {country_filter}
                ORDER BY e.performance_score ASC
                LIMIT 5
            """),
            params,
        ).mappings().all()

        result["performance"] = {
            "stats": dict(health_data) if health_data else {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None},
            "top_performers": [dict(r) for r in top_performers],
            "bottom_performers": [dict(r) for r in bottom_performers],
        }
    except Exception as e:
        logger.warning("Performance data unavailable (performance_score column may not exist): %s", e)
        result["performance"] = {"stats": {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None}, "top_performers": [], "bottom_performers": []}

    # ── Recent Activity Feed ──
    try:
        since_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        params["since"] = since_date

        activity = db.execute(
            text(f"""
                SELECT al.id, al.actor_employee_id, al.action, al.entity_type,
                       al.entity_id, al.target_employee_id, al.metadata_json,
                       al.created_at,
                       ae.employee_code as actor_code,
                       te.employee_code as target_code
                FROM employee_activity_logs al
                LEFT JOIN employees ae ON ae.id = al.actor_employee_id
                LEFT JOIN employees te ON te.id = al.target_employee_id
                WHERE al.created_at >= :since {country_filter}
                ORDER BY al.created_at DESC
                LIMIT 50
            """),
            params,
        ).mappings().all()

        # Aggregate activity stats
        total_recent = len(activity)
        action_breakdown: dict = {}
        for a in activity:
            action = a["action"]
            action_breakdown[action] = action_breakdown.get(action, 0) + 1

        result["activity"] = {
            "total_events": total_recent,
            "action_breakdown": action_breakdown,
            "events": [
                {
                    "id": e["id"],
                    "actor_employee_id": e["actor_employee_id"],
                    "actor_code": e["actor_code"],
                    "action": e["action"],
                    "entity_type": e["entity_type"],
                    "target_code": e["target_code"],
                    "timestamp": e["created_at"].isoformat() if e["created_at"] else None,
                }
                for e in activity
            ],
        }
    except Exception as e:
        logger.warning("Activity data unavailable (table may not exist): %s", e)
        result["activity"] = {"total_events": 0, "action_breakdown": {}, "events": []}

    # ── Employee Counts ──
    try:
        emp_counts = db.execute(
            text(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN employment_status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN employment_status = 'terminating' THEN 1 ELSE 0 END) as terminating,
                    SUM(CASE WHEN employment_status = 'terminated' THEN 1 ELSE 0 END) as terminated
                FROM employees
                WHERE 1=1 {country_filter}
            """),
            params,
        ).mappings().first()
        result["employees"] = dict(emp_counts) if emp_counts else {"total": 0, "active": 0, "terminating": 0, "terminated": 0}
    except Exception as e:
        logger.warning("Employee counts unavailable: %s", e)
        result["employees"] = {"total": 0, "active": 0, "terminating": 0, "terminated": 0}

    result["dashboard_date"] = now.isoformat()
    return result
