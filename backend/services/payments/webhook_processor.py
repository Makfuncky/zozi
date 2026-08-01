"""
Unified Webhook Processor Service.

Handles incoming webhooks from all payment gateways, verifies signatures,
normalizes events, and stores them for audit and processing.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Union

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from models import NormalizedWebhookEvent, ProcessedWebhookEvent
from services.payments.base import BasePaymentGateway
from services.payments.registry import PaymentGatewayRegistry
from services.payments.webhook_models import ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent
from utils.vault import decrypt_secret

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Unified webhook processor that handles signature verification,
    event normalization, and idempotency.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def _get_adapter(self, provider_code: str) -> Optional[BasePaymentGateway]:
        cls = PaymentGatewayRegistry.get(provider_code)
        return cls() if cls else None

    def _load_webhook_secret(self, provider_code: str) -> Optional[str]:
        from models import PaymentGatewayConnection
        record = self.db.query(PaymentGatewayConnection).filter(
            PaymentGatewayConnection.provider_code == provider_code,
            PaymentGatewayConnection.is_active == True,
        ).first()
        if record:
            return decrypt_secret(record.webhook_secret)
        return None

    def _is_already_processed(self, processor: str, event_id: str) -> bool:
        existing = self.db.query(ProcessedWebhookEvent).filter(
            ProcessedWebhookEvent.processor == processor,
            ProcessedWebhookEvent.event_id == event_id,
        ).first()
        return existing is not None

    def _record_processed_event(self, processor: str, event_id: str) -> None:
        self.db.add(ProcessedWebhookEvent(
            processor=processor,
            event_id=event_id,
        ))
        self.db.commit()

    def _store_normalized_event(
        self,
        event: Union[ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent],
    ) -> None:
        normalized = NormalizedWebhookEvent(
            provider_code=event.provider_code,
            gateway_event_id=event.gateway_event_id,
            event_type=event.event_type.value if hasattr(event, 'event_type') else str(event.event_type),
            status=event.status.value if hasattr(event, 'status') else str(event.status),
            environment=event.environment,
            processed_at=event.timestamp or datetime.utcnow(),
            zozi_order_id=event.zozi_order_id,
            gateway_transaction_id=event.gateway_transaction_id,
            gateway_customer_id=event.gateway_customer_id,
            gross_amount=event.gross_amount,
            currency=event.currency,
            gateway_fee=event.gateway_fee,
            net_settlement=event.net_settlement,
            fraud_score=event.fraud_score,
            three_ds_status=event.three_ds_status,
            avs_result=event.avs_result,
            raw_payload=json.dumps(event.raw_payload) if event.raw_payload else None,
        )
        self.db.add(normalized)
        self.db.commit()

    async def process_webhook(
        self,
        request: Request,
        provider_code: str,
    ) -> dict[str, Any]:
        raw_body = await request.body()
        headers = dict(request.headers)
        
        adapter = self._get_adapter(provider_code)
        if not adapter:
            raise HTTPException(status_code=503, detail=f"Gateway '{provider_code}' adapter not available")
        
        webhook_secret = self._load_webhook_secret(provider_code)
        if webhook_secret and not adapter.verify_webhook_signature(raw_body, headers, webhook_secret):
            logger.warning("Webhook signature verification failed for %s", provider_code)
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        try:
            normalized_event = adapter.normalize_webhook_payload(raw_body, headers)
        except Exception as e:
            logger.error("Failed to normalize webhook from %s: %s", provider_code, e)
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        
        event_id = normalized_event.gateway_event_id
        if self._is_already_processed(provider_code, event_id):
            logger.info("Duplicate webhook ignored: %s/%s", provider_code, event_id)
            return {"status": "ok", "duplicate": True}
        
        self._record_processed_event(provider_code, event_id)
        self._store_normalized_event(normalized_event)
        
        return {"status": "ok", "normalized_event": normalized_event.model_dump()}


def create_webhook_handler(provider_code: str):
    """Factory function to create a webhook handler for a specific provider."""
    async def handler(request: Request, db: Session):
        processor = WebhookProcessor(db)
        return await processor.process_webhook(request, provider_code)
    return handler

