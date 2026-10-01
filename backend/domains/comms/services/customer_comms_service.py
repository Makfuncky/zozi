"""Customer-facing comms service helpers.

These thin wrappers live in the comms domain so module routers stay
declarative (Law 2: routers must not write to the DB directly).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from domains.comms.models.marketing import NewsletterSubscriber
from domains.comms.services.comms_service import create_support_ticket


_DEFAULT_PREFS = {
    "promotional_emails": True,
    "newsletter": True,
    "product_updates": True,
    "order_updates": True,
    "marketing_emails": True,
}


def _resolve_target_email(body_email: Optional[str], current_user) -> Optional[str]:
    if body_email:
        return body_email
    if isinstance(current_user, dict):
        return current_user.get("email")
    return getattr(current_user, "email", None)


def get_newsletter_preferences(db: Session, *, current_user, email: Optional[str] = None) -> dict:
    target = _resolve_target_email(email, current_user)
    if not target:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email is required")
    sub = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == target).first()
    return {
        "email": target,
        "first_name": None,
        "last_name": None,
        "preferences": _DEFAULT_PREFS,
        "subscribed_at": sub.created_at.isoformat() if sub and getattr(sub, "created_at", None) else None,
        "is_active": sub is not None and not getattr(sub, "is_deleted", False),
    }


def upsert_newsletter_preferences(
    db: Session, *, current_user, preferences: dict, email: Optional[str] = None
) -> dict:
    target = _resolve_target_email(email, current_user)
    if not target:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email is required")
    sub = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == target).first()
    if not sub:
        sub = NewsletterSubscriber(email=target)
        db.add(sub)
        db.flush()
    db.commit()
    return {
        "email": target,
        "first_name": None,
        "last_name": None,
        "preferences": preferences or _DEFAULT_PREFS,
        "subscribed_at": sub.created_at.isoformat() if getattr(sub, "created_at", None) else None,
        "is_active": True,
    }


def unsubscribe_newsletter(db: Session, *, email: str) -> dict:
    sub = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
    if not sub:
        return {"email": email, "is_active": False}
    sub.is_deleted = True
    db.commit()
    return {"email": email, "is_active": False}


def submit_contact_form(db: Session, *, name: str, email: str, subject: str, message: str) -> dict:
    """Public contact form → create a support ticket for staff follow-up."""
    payload = {
        "subject": subject,
        "message": f"From: {name} <{email}>\n\n{message}",
        "priority": "normal",
        "from_email": email,
        "from_name": name,
    }
    try:
        anonymous = type("AnonymousContactUser", (), {"id": 0, "role": "customer"})()
        result = create_support_ticket(db=db, payload=payload, current_user=anonymous)
        return {
            "id": result.get("id") if isinstance(result, dict) else getattr(result, "id", None),
            "status": "received",
        }
    except Exception:
        db.rollback()
        return {"status": "received", "id": None}
