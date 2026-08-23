"""Payments write operations (canonical module).

Implements the payments domain write surface. Previously stubbed with
``_missing_symbol`` placeholders; now contains real DB-write logic.
"""
from __future__ import annotations
from domains.finance.services.ledger.invoice_write_service import _apply_changes

from sqlalchemy import select
from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.comms.models.communication import Notification
from domains.governance.models.admin import PaymentProviderConfig
from domains.governance.models.admin import ProcessedWebhookEvent
from domains.finance.models.payments import Payment
from domains.finance.models.payments import PaymentGatewayConnection
import structlog
logger = structlog.get_logger(__name__)




def create_payment(
    db: Session,
    *,
    order_id: int,
    amount: float,
    payment_method: str,
    provider: str | None = None,
    status: str = "pending",
    intent_id: str | None = None,
    country_code: str | None = None,
    layout_json: str | None = None,
    created_by: int | None = None,
) -> Payment:
    obj = Payment(
        order_id=order_id,
        amount=amount,
        payment_method=payment_method,
        provider=provider,
        status=status,
        intent_id=intent_id,
        country_code=country_code,
        layout_json=layout_json,
        created_by=created_by,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_payment(db: Session, payment_id: int, **changes) -> Payment:
    obj = db.get(Payment, payment_id)
    if obj is None:
        raise ValueError(f"Payment {payment_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj


def create_payment_provider_config(
    db: Session,
    *,
    provider_name: str,
    config: dict | None = None,
    is_active: bool = True,
    country_code: str | None = None,
    created_by: int | None = None,
) -> PaymentProviderConfig:
    obj = PaymentProviderConfig(
        provider_name=provider_name,
        config=config,
        is_active=is_active,
        country_code=country_code,
        created_by=created_by,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_payment_provider_config(db: Session, config_id: int, **changes) -> PaymentProviderConfig:
    obj = db.get(PaymentProviderConfig, config_id)
    if obj is None:
        raise ValueError(f"PaymentProviderConfig {config_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj


def update_payment_provider_config_no_refresh(db: Session, config_id: int, **changes) -> PaymentProviderConfig:
    # Persist changes without triggering a provider adapter refresh.
    obj = db.get(PaymentProviderConfig, config_id)
    if obj is None:
        raise ValueError(f"PaymentProviderConfig {config_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj


def create_or_update_gateway_connection(
    db: Session,
    *,
    provider_code: str,
    gateway_name: str,
    country_code: str,
    **fields,
) -> PaymentGatewayConnection:
    existing = db.execute(
        select(PaymentGatewayConnection).where(
            PaymentGatewayConnection.provider_code == provider_code,
            PaymentGatewayConnection.country_code == country_code,
            PaymentGatewayConnection.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if existing is not None:
        _apply_changes(existing, fields)
        db.commit()
        db.refresh(existing)
        return existing
    obj = PaymentGatewayConnection(
        provider_code=provider_code,
        gateway_name=gateway_name,
        country_code=country_code,
        **fields,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_gateway_connection(db: Session, connection_id: int, **changes) -> PaymentGatewayConnection:
    obj = db.get(PaymentGatewayConnection, connection_id)
    if obj is None:
        raise ValueError(f"PaymentGatewayConnection {connection_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj


def add_processed_webhook_event(
    db: Session,
    *,
    processor: str,
    event_id: str,
    country_code: str | None = None,
    processed_at=None,
    **fields,
) -> ProcessedWebhookEvent:
    obj = ProcessedWebhookEvent(
        processor=processor,
        event_id=event_id,
        country_code=country_code,
        processed_at=processed_at,
        **fields,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def add_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    channel: str | None = None,
    priority: str | None = None,
    link: str | None = None,
    template: str | None = None,
    country_code: str | None = None,
    **fields,
) -> Notification:
    # ``Notification`` inherits a NOT NULL ``country_code`` from TenantMixin, so
    # resolve it from the owning user when the caller did not supply one.
    if country_code is None and user_id is not None:
        user = db.get(User, user_id)
        if user is not None:
            country_code = getattr(user, "country_code", None)
    obj = Notification(
        user_id=user_id,
        title=title,
        message=message,
        channel=channel,
        priority=priority,
        link=link,
        template=template,
        country_code=country_code,
        **fields,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def flush_model(db: Session, instance=None):
    db.flush()
    return instance


# Backwards-compatible alias: callers import this symbol as ``create_notification``.
create_notification = add_notification
