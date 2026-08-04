"""Service methods for country communication data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from data.models import CountryCommunication


def get_country_communications(
    db: Session, user_id: int, status: str | None = None, priority: str | None = None, limit: int = 50
) -> list[dict]:
    """Get country communications for a user."""
    query = db.query(CountryCommunication).filter(
        (CountryCommunication.to_user_id == user_id)
        | (CountryCommunication.to_user_id.is_(None))
    )
    if status:
        query = query.filter(CountryCommunication.status == status)
    if priority:
        query = query.filter(CountryCommunication.priority == priority)
    comms = query.order_by(desc(CountryCommunication.created_at)).limit(limit).all()
    return [
        {
            "id": c.id,
            "country_code": c.country_code,
            "from_user_id": c.from_user_id,
            "subject": c.subject,
            "body": c.body,
            "priority": c.priority,
            "category": c.category,
            "related_entity_type": c.related_entity_type,
            "related_entity_id": c.related_entity_id,
            "status": c.status,
            "read_at": c.read_at.isoformat() if c.read_at else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in comms
    ]


def get_country_communication_by_id(db: Session, comm_id: int) -> CountryCommunication | None:
    """Get a single country communication by ID."""
    return db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()


def mark_country_communication_read(db: Session, comm: CountryCommunication) -> dict:
    """Mark a communication as read."""
    comm.status = "read"
    comm.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read", "read_at": comm.read_at.isoformat()}
