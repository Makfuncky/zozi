from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from data.db import SessionLocal
from data.models import CampaignRecipient, EmailDeliveryEvent, EmailProviderConfig, EmailSuppression, ProcessedWebhookEvent
from utils.config import settings

logger = logging.getLogger(__name__)

_SVIX_TOLERANCE_SECONDS = 300
_SUPPRESSION_EVENT_TYPES = {"bounced", "complained", "suppressed"}
_TERMINAL_RECIPIENT_STATUSES = {"bounced", "unsubscribed"}
_RESEND_EVENT_TYPE_MAP = {
    "email.sent": "sent",
    "email.delivered": "delivered",
    "email.delivery_delayed": "delayed",
    "email.bounced": "bounced",
    "email.complained": "complained",
    "email.opened": "opened",
    "email.clicked": "clicked",
}


def normalize_email_address(value: str | None) -> str:
    return (value or "").strip().lower()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _db_side_effects_enabled() -> bool:
    return settings.app_env != "test" and not bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def resolve_resend_webhook_secret(db: Session) -> str:
    record = db.query(EmailProviderConfig).order_by(EmailProviderConfig.id.desc()).first()
    if record and record.resend_webhook_secret:
        return str(record.resend_webhook_secret)
    return settings.resend_webhook_secret or os.getenv("RESEND_WEBHOOK_SECRET", "")


def verify_resend_webhook_request(payload: str, headers: Mapping[str, str], secret: str) -> tuple[bool, str]:
    if not secret:
        return False, "Webhook secret not configured"

    msg_id = headers.get("svix-id") or headers.get("webhook-id") or ""
    timestamp = headers.get("svix-timestamp") or headers.get("webhook-timestamp") or ""
    signature_header = headers.get("svix-signature") or headers.get("webhook-signature") or ""
    if not msg_id or not timestamp or not signature_header:
        return False, "Missing webhook verification headers"

    try:
        timestamp_value = int(timestamp)
    except (TypeError, ValueError):
        return False, "Invalid webhook timestamp"

    current_epoch = int(datetime.now(timezone.utc).timestamp())
    if abs(current_epoch - timestamp_value) > _SVIX_TOLERANCE_SECONDS:
        return False, "Webhook timestamp is outside the allowed tolerance"

    secret_body = secret.split("_", 1)[1] if secret.startswith("whsec_") else secret
    try:
        secret_bytes = base64.b64decode(secret_body)
    except Exception:
        secret_bytes = secret_body.encode("utf-8")

    signed_content = f"{msg_id}.{timestamp}.{payload}".encode("utf-8")
    expected_signature = base64.b64encode(hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()).decode("utf-8")
    provided_signatures: list[str] = []
    for fragment in signature_header.split():
        version, _, signature = fragment.partition(",")
        if version == "v1" and signature:
            provided_signatures.append(signature)

    if not provided_signatures:
        return False, "Missing v1 webhook signature"
    if not any(hmac.compare_digest(expected_signature, signature) for signature in provided_signatures):
        return False, "Invalid webhook signature"
    return True, "ok"


def get_active_email_suppression(email: str, db: Session) -> EmailSuppression | None:
    normalized = normalize_email_address(email)
    if not normalized:
        return None
    return (
        db.query(EmailSuppression)
        .filter(EmailSuppression.email == normalized, EmailSuppression.status == "active")
        .first()
    )


def is_email_suppressed(email: str) -> bool:
    normalized = normalize_email_address(email)
    if not normalized or not _db_side_effects_enabled():
        return False
    from data.db import get_service_session
    try:
        with get_service_session() as db:
            return get_active_email_suppression(normalized, db) is not None
    except Exception:
        logger.exception("Failed to query email suppression state for %s", normalized)
        return False


def _serialize_payload(payload: Any) -> str | None:
    if payload is None:
        return None
    try:
        return json.dumps(payload, default=str)
    except Exception:
        return json.dumps({"value": str(payload)})


def _match_campaign_recipient(
    db: Session,
    recipient_email: str,
    *,
    campaign_recipient_id: int | None = None,
) -> CampaignRecipient | None:
    if campaign_recipient_id is not None:
        recipient = (
            db.query(CampaignRecipient)
            .filter(CampaignRecipient.id == campaign_recipient_id)
            .first()
        )
        if recipient is None:
            return None
        if normalize_email_address(getattr(recipient, "email", None)) != recipient_email:
            logger.warning(
                "Ignoring mismatched campaign recipient %s for %s",
                campaign_recipient_id,
                recipient_email,
            )
            return None
        return recipient

    return (
        db.query(CampaignRecipient)
        .filter(CampaignRecipient.email == recipient_email)
        .order_by(CampaignRecipient.created_at.desc(), CampaignRecipient.id.desc())
        .first()
    )


def _apply_campaign_recipient_event(recipient: CampaignRecipient | None, event_type: str, occurred_at: datetime | None) -> None:
    if recipient is None:
        return

    stamp = occurred_at or _utcnow()
    current_status = str(getattr(recipient, "status", "pending"))
    if event_type == "delivered" and current_status not in _TERMINAL_RECIPIENT_STATUSES:
        recipient.status = "delivered"
    elif event_type == "bounced" and current_status != "unsubscribed":
        recipient.status = "bounced"
        recipient.bounced_at = stamp
    elif event_type == "opened" and getattr(recipient, "opened_at", None) is None:
        recipient.opened_at = stamp
        if current_status not in _TERMINAL_RECIPIENT_STATUSES:
            recipient.status = "opened"
    elif event_type == "clicked" and getattr(recipient, "clicked_at", None) is None:
        recipient.clicked_at = stamp
        if current_status not in _TERMINAL_RECIPIENT_STATUSES:
            recipient.status = "clicked"


def upsert_email_suppression(
    db: Session,
    *,
    email: str,
    reason: str,
    source: str,
    provider: str | None = None,
    event_id: str | None = None,
    event_at: datetime | None = None,
    notes: str | None = None,
) -> EmailSuppression:
    normalized = normalize_email_address(email)
    suppression = db.query(EmailSuppression).filter(EmailSuppression.email == normalized).first()
    stamp = event_at or _utcnow()
    if suppression is None:
        suppression = EmailSuppression(
            email=normalized,
            reason=reason,
            source=source,
            provider=provider,
            status="active",
            notes=notes,
            first_event_id=event_id,
            last_event_id=event_id,
            suppressed_at=stamp,
            last_event_at=stamp,
        )
        db.add(suppression)
        return suppression

    suppression.reason = reason
    suppression.source = source
    suppression.provider = provider
    suppression.status = "active"
    suppression.notes = notes
    suppression.last_event_id = event_id
    suppression.last_event_at = stamp
    if suppression.first_event_id is None:
        suppression.first_event_id = event_id
    if suppression.suppressed_at is None:
        suppression.suppressed_at = stamp
    return suppression


def record_email_delivery_event(
    *,
    recipient_email: str,
    processor: str,
    event_type: str,
    source: str,
    subject: str | None = None,
    purpose: str | None = None,
    event_id: str | None = None,
    message_id: str | None = None,
    campaign_recipient_id: int | None = None,
    occurred_at: datetime | None = None,
    payload: Any = None,
    db: Session | None = None,
) -> EmailDeliveryEvent | None:
    normalized = normalize_email_address(recipient_email)
    if not normalized:
        return None

    owns_session = db is None
    if owns_session:
        if not _db_side_effects_enabled():
            return None
        db = SessionLocal()

    try:
        recipient = _match_campaign_recipient(
            db,
            normalized,
            campaign_recipient_id=campaign_recipient_id,
        )
        event = EmailDeliveryEvent(
            event_id=event_id,
            processor=processor,
            message_id=message_id,
            recipient_email=normalized,
            subject=subject,
            purpose=purpose,
            event_type=event_type,
            source=source,
            campaign_recipient_id=getattr(recipient, "id", None),
            payload=_serialize_payload(payload),
            occurred_at=occurred_at,
        )
        db.add(event)
        _apply_campaign_recipient_event(recipient, event_type, occurred_at)
        if owns_session:
            db.commit()
            db.refresh(event)
        return event
    except Exception:
        if owns_session:
            db.rollback()
        logger.exception("Failed to record email delivery event for %s", normalized)
        return None
    finally:
        if owns_session:
            db.close()


def process_resend_webhook(payload: dict[str, Any], headers: Mapping[str, str], db: Session) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    event_type_raw = str(payload.get("type") or "unknown").strip().lower()
    normalized_event_type = _RESEND_EVENT_TYPE_MAP.get(event_type_raw, event_type_raw.removeprefix("email."))
    webhook_id = str(headers.get("svix-id") or headers.get("webhook-id") or payload.get("id") or "")

    if webhook_id:
        duplicate = (
            db.query(ProcessedWebhookEvent)
            .filter(
                ProcessedWebhookEvent.event_id == webhook_id,
                ProcessedWebhookEvent.processor == "resend-email",
            )
            .first()
        )
        if duplicate:
            return {"status": "duplicate", "event_type": normalized_event_type}

    recipients = data.get("to") if isinstance(data.get("to"), list) else [data.get("to")]
    recipient_email = next((normalize_email_address(item) for item in recipients if normalize_email_address(item)), "")
    message_id = str(data.get("email_id") or data.get("id") or "") or None
    occurred_at = _parse_datetime(payload.get("created_at")) or _parse_datetime(data.get("created_at")) or _utcnow()
    subject = str(data.get("subject") or "").strip() or None

    if recipient_email:
        record_email_delivery_event(
            recipient_email=recipient_email,
            processor="resend",
            event_type=normalized_event_type,
            source="webhook",
            subject=subject,
            event_id=webhook_id or None,
            message_id=message_id,
            occurred_at=occurred_at,
            payload=payload,
            db=db,
        )

    if recipient_email and normalized_event_type in _SUPPRESSION_EVENT_TYPES:
        bounce = data.get("bounce") if isinstance(data.get("bounce"), dict) else {}
        upsert_email_suppression(
            db,
            email=recipient_email,
            reason=str(bounce.get("subType") or bounce.get("type") or bounce.get("message") or normalized_event_type),
            source="resend-webhook",
            provider="resend",
            event_id=webhook_id or message_id,
            event_at=occurred_at,
            notes=str(bounce.get("message") or data.get("message") or event_type_raw),
        )

    if webhook_id:
        db.add(ProcessedWebhookEvent(event_id=webhook_id, processor="resend-email"))
    db.commit()
    return {
        "status": "processed",
        "event_type": normalized_event_type,
        "recipient_email": recipient_email or None,
        "message_id": message_id,
        "suppressed": bool(recipient_email and normalized_event_type in _SUPPRESSION_EVENT_TYPES),
    }

