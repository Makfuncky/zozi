"""Employee Activity Logger — lightweight append-only collaboration ledger.
Every service writes events here so the system always answers "who did what, with whom, when."
Leverages the employee_activity_logs table from the gap migration.
"""

__all__ = [
    "log_activity",
    "get_employee_activity",
    "get_team_activity",
    "get_collaboration_heatmap",
    "get_activity_stats",
]

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, func, select, or_, table, column

from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    actor_employee_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    target_employee_id: Optional[int] = None,
    country_code: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write an immutable event to the employee_activity_logs table.
    
    Args:
        actor_employee_id: Who performed the action
        action: Verb describing the action (e.g., 'login', 'submitted_review', 'approved_leave')
        entity_type: Type of entity the action was performed on
        entity_id: ID of the entity (string serialized for flexibility)
        target_employee_id: The "with whom" — another employee involved
        country_code: Country scope for RLS
        metadata_json: Arbitrary structured context
        ip_address: Client IP
        device_fingerprint: Device identifier
        session_id: Session identifier for correlating events
    """
    import json

    metadata_json_str = json.dumps(metadata_json or {})

    # Dialect-agnostic: pass JSON as a string parameter.
    # PostgreSQL's JSONB column coerces strings automatically.
    # SQLite stores as-is (JSON column is just text there).
    result = db.execute(
        text("""
            INSERT INTO employee_activity_logs
                (actor_employee_id, action, entity_type, entity_id,
                 target_employee_id, country_code, metadata_json,
                 ip_address, device_fingerprint, session_id)
            VALUES
                (:actor, :action, :entity_type, :entity_id,
                 :target, :country_code, :metadata_str,
                 :ip, :device, :session_id)
            RETURNING id, created_at
        """),
        {
            "actor": actor_employee_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "target": target_employee_id,
            "country_code": country_code,
            "metadata_str": metadata_json_str,
            "ip": ip_address,
            "device": device_fingerprint,
            "session_id": session_id,
        },
    )
    row = result.mappings().first()
    db.commit()

    raw_ts = row["created_at"]
    if raw_ts and hasattr(raw_ts, "isoformat"):
        ts_str = raw_ts.isoformat()
    else:
        ts_str = str(raw_ts) if raw_ts else None
    log_entry = {"id": row["id"], "created_at": ts_str}

    # Broadcast to HR activity WebSocket room (fire-and-forget, best-effort)
    try:
        from utils.websocket_manager import broadcast_activity_event
        broadcast_activity_event({
            "type": "activity.new",
            "id": log_entry["id"],
            "actor_employee_id": actor_employee_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "target_employee_id": target_employee_id,
            "country_code": country_code,
            "timestamp": log_entry["created_at"],
        })
    except ImportError:
        pass  # websocket_manager not available (tests, edge runtime)
    except Exception as exc:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Activity broadcast failed (non-critical): %s", exc)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Activity logged: employee=%s action=%s entity=%s/%s",
                     actor_employee_id, action, entity_type, entity_id)
    return log_entry


def get_employee_activity(
    db: Session,
    employee_id: int,
    limit: int = 50,
    offset: int = 0,
    action_filter: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Get activity log for a specific employee (actor or target)."""
    conditions = ["(actor_employee_id = :eid OR target_employee_id = :eid)"]
    params: Dict[str, Any] = {"eid": employee_id, "limit": limit, "offset": offset}

    if action_filter:
        conditions.append("action LIKE :action_pattern")
        params["action_pattern"] = f"%{action_filter}%"
    if since:
        conditions.append("created_at >= :since")
        params["since"] = since
    if until:
        conditions.append("created_at <= :until")
        params["until"] = until

    act_table = table('employee_activity_logs',
        column('id'), column('actor_employee_id'), column('action'),
        column('entity_type'), column('entity_id'), column('target_employee_id'),
        column('country_code'), column('metadata_json'), column('ip_address'),
        column('device_fingerprint'), column('session_id'), column('created_at'),
    )
    q = select(act_table).where(
        or_(
            act_table.c.actor_employee_id == employee_id,
            act_table.c.target_employee_id == employee_id,
        )
    )
    if action_filter:
        q = q.where(act_table.c.action.like(f"%{action_filter}%"))
    if since:
        q = q.where(act_table.c.created_at >= since)
    if until:
        q = q.where(act_table.c.created_at <= until)
    q = q.order_by(act_table.c.created_at.desc()).limit(limit).offset(offset)
    rows = db.execute(q).mappings().all()

    return [_serialize_activity(r) for r in rows]


def get_team_activity(
    db: Session,
    manager_employee_id: int,
    limit: int = 100,
    since: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Get activity log for all employees under a manager's subtree."""
    from services.hierarchy_service import get_all_subordinates as get_subs
    from data.models_employee_models import Employee
    mgr_emp = db.query(Employee).filter(Employee.id == manager_employee_id).first()
    if not mgr_emp:
        return []

    subs = get_subs(db, mgr_emp.user_id)
    sub_ids = [s["id"] for s in subs] + [manager_employee_id]

    if not sub_ids:
        return []

    act_table = table('employee_activity_logs',
        column('id'), column('actor_employee_id'), column('action'),
        column('entity_type'), column('entity_id'),
        column('target_employee_id'), column('country_code'),
        column('metadata_json'), column('created_at'),
    )
    q = select(act_table).where(
        act_table.c.actor_employee_id.in_(sub_ids)
    )
    if since:
        q = q.where(act_table.c.created_at >= since)
    q = q.order_by(act_table.c.created_at.desc()).limit(limit)
    rows = db.execute(q).mappings().all()
    return [_serialize_activity(r) for r in rows]


def get_collaboration_heatmap(
    db: Session,
    employee_id: int,
    days: int = 30,
) -> Dict[str, Any]:
    """Generate a collaboration heatmap showing who this employee interacts with most."""
    since = _utcnow() - timedelta(days=days)

    # Count interactions grouped by target employee
    rows = db.execute(
        text("""
            SELECT target_employee_id, action, COUNT(*) as count
            FROM employee_activity_logs
            WHERE actor_employee_id = :eid
              AND target_employee_id IS NOT NULL
              AND created_at >= :since
            GROUP BY target_employee_id, action
            ORDER BY count DESC
            LIMIT 20
        """),
        {"eid": employee_id, "since": since},
    ).mappings().all()

    # Get employee names for the targets
    target_ids = list(set(r["target_employee_id"] for r in rows if r["target_employee_id"]))
    target_names: Dict[int, str] = {}
    if target_ids:
        from data.models_employee_models import Employee
        emps = db.query(Employee).filter(Employee.id.in_(target_ids)).all()
        for emp in emps:
            target_names[emp.id] = emp.employee_code

    interactions = []
    for r in rows:
        tid = r["target_employee_id"]
        interactions.append({
            "target_employee_id": tid,
            "target_name": target_names.get(tid, f"#{tid}"),
            "action": r["action"],
            "count": r["count"],
        })

    return {
        "employee_id": employee_id,
        "period_days": days,
        "total_interactions": sum(r["count"] for r in rows),
        "interactions": interactions,
    }


def get_activity_stats(
    db: Session,
    country_code: Optional[str] = None,
    since: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get aggregate activity statistics for a country or across all countries."""
    conditions = []
    params: Dict[str, Any] = {}
    if country_code:
        conditions.append("country_code = :country")
        params["country"] = country_code
    if since:
        conditions.append("created_at >= :since")
        params["since"] = since

    act_table = table('employee_activity_logs',
        column('action'), column('country_code'), column('created_at'),
    )
    q = select(act_table.c.action, func.count().label('count')).group_by(act_table.c.action).order_by(func.count().desc())
    if country_code:
        q = q.where(act_table.c.country_code == country_code)
    if since:
        q = q.where(act_table.c.created_at >= since)
    rows = db.execute(q).mappings().all()

    total_q = select(func.count().label('total')).select_from(act_table)
    if country_code:
        total_q = total_q.where(act_table.c.country_code == country_code)
    if since:
        total_q = total_q.where(act_table.c.created_at >= since)
    total = db.execute(total_q).scalar()

    return {
        "total_events": total,
        "breakdown": {r["action"]: r["count"] for r in rows},
        "unique_actions": len(rows),
    }


def _serialize_activity(row: Any) -> Dict[str, Any]:
    """Convert a raw DB row to a safe dict."""
    return {
        "id": row["id"],
        "actor_employee_id": row["actor_employee_id"],
        "action": row["action"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "target_employee_id": row["target_employee_id"],
        "country_code": row["country_code"],
        "metadata": row["metadata_json"],
        "ip_address": row.get("ip_address"),
        "device_fingerprint": row.get("device_fingerprint"),
        "session_id": row.get("session_id"),
        "timestamp": row["created_at"].isoformat() if row.get("created_at") else None,
    }
