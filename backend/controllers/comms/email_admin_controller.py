"""Email admin controller.

Thin orchestration between the email router (admin surface) and
``services.comms.email_write_service``. Satisfies CIR2 (routers → controllers →
services); all DB writes live in the service. The router keeps request
validation, authorization, and response serialization.
"""
from __future__ import annotations

from services.comms.email_write_service import (
    apply_suppression_update as _apply_suppression_update,
    create_email_campaign as _create_email_campaign,
    create_email_template as _create_email_template,
    delete_email_campaign as _delete_email_campaign,
    delete_email_template as _delete_email_template,
    update_email_template as _update_email_template,
    upsert_email_runtime_config as _upsert_email_runtime_config,
)
import structlog
logger = structlog.get_logger(__name__)


def _actor_id(current_user) -> object:
    return current_user.get("id") if isinstance(current_user, dict) else None


def create_campaign(db, payload: dict, current_user) -> object:
    return _create_email_campaign(
        db,
        name=payload.get("name", "Untitled Campaign"),
        subject=payload.get("subject", ""),
        status=payload.get("status", "draft"),
        target_audience=payload.get("target_audience"),
        country_code=payload.get("country_code"),
        created_by=_actor_id(current_user),
    )


def delete_campaign(db, campaign) -> None:
    _delete_email_campaign(db, campaign)


def apply_suppression_update(db, suppression, body: dict) -> None:
    _apply_suppression_update(db, suppression, body)


def create_template(db, payload: dict, current_user) -> object:
    return _create_email_template(
        db,
        name=payload.get("name", ""),
        subject=payload.get("subject", ""),
        content=payload.get("content"),
        template_type=payload.get("template_type", "marketing"),
        created_by=_actor_id(current_user),
    )


def update_template(db, template, payload: dict) -> None:
    _update_email_template(db, template, payload)


def delete_template(db, template) -> None:
    _delete_email_template(db, template)


def upsert_runtime_config(db, payload: dict) -> object:
    return _upsert_email_runtime_config(db, payload)
