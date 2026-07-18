from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import stripe

from .base import BasePaymentGateway
from .base_models import ConnectionTestResult, PaymentResult, RefundResult
from .webhook_models import ZoziEventStatus, ZoziEventType, ZoziPaymentEvent

logger = logging.getLogger(__name__)


class StripeAdapter(BasePaymentGateway):
    gateway_id = "stripe"
    display_name = "Stripe"

    def _apply_key(self, credentials: dict[str, Any]) -> None:
        key = credentials.get("secret_key") or credentials.get("api_key") or ""
        if key:
            stripe.api_key = str(key).strip()

    def process_payment(
        self,
        amount: float,
        currency: str,
        credentials: dict[str, Any],
        *,
        order_id: int | None = None,
        description: str = "",
        customer: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PaymentResult:
        self._apply_key(credentials)
        try:
            amount_minor = int(round(amount * 100))
            meta = dict(metadata or {})
            if order_id:
                meta["order_id"] = str(order_id)

            intent = stripe.PaymentIntent.create(
                amount=amount_minor,
                currency=currency.lower(),
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                metadata=meta,
                description=description[:255] if description else None,
            )
            return PaymentResult(
                success=True,
                transaction_id=intent.id,
                gateway_ref=intent.id,
                amount=amount,
                currency=currency.upper(),
                status=intent.status,
                raw_response={"client_secret": intent.client_secret},
                redirect_url=None,
            )
        except stripe.StripeError as exc:
            logger.warning("Stripe payment error: %s", exc)
            return PaymentResult(
                success=False,
                error_code=getattr(exc, "code", "stripe_error"),
                error_message=str(getattr(exc, "user_message", str(exc))),
                status="failed",
            )

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        self._apply_key(credentials)
        try:
            params: dict[str, Any] = {"payment_intent": transaction_id}
            if amount is not None:
                params["amount"] = int(round(amount * 100))
            refund = stripe.Refund.create(**params)
            return RefundResult(
                success=True,
                refund_id=refund.id,
                gateway_ref=refund.id,
                amount=amount,
                status=refund.status,
            )
        except stripe.StripeError as exc:
            logger.warning("Stripe refund error: %s", exc)
            return RefundResult(
                success=False,
                error_code=getattr(exc, "code", "stripe_refund_error"),
                error_message=str(getattr(exc, "user_message", str(exc))),
                status="failed",
            )

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        self._apply_key(credentials)
        try:
            stripe.Balance.retrieve()
            return ConnectionTestResult(success=True, message="Stripe connection OK")
        except stripe.StripeError as exc:
            return ConnectionTestResult(
                success=False,
                message=str(getattr(exc, "user_message", str(exc))),
            )

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        headers: dict[str, str],
        webhook_secret: str,
    ) -> bool:
        sig_header = headers.get("stripe-signature", "")
        if not sig_header or not webhook_secret:
            return False
        try:
            stripe.Webhook.construct_event(raw_body, sig_header, webhook_secret)
            return True
        except Exception:
            return False

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> ZoziPaymentEvent:
        event = json.loads(raw_body)
        event_type = event.get("type", "")
        obj = event.get("data", {}).get("object", {})
        stripe_event_id = event.get("id", "")
        
        metadata = obj.get("metadata", {}) or {}
        zozi_order_id = metadata.get("order_id")
        
        amount = Decimal(str(obj.get("amount", 0))) / Decimal("100")
        gateway_fee = Decimal("0")
        
        status = obj.get("status", "")
        normalized_status = ZoziEventStatus.PAYMENT_CAPTURED if status == "succeeded" else ZoziEventStatus.PAYMENT_FAILED
        if status in ("requires_payment_method", "canceled"):
            normalized_status = ZoziEventStatus.PAYMENT_FAILED
        
        event_type_map = {
            "payment_intent.succeeded": ZoziEventType.PAYMENT_SUCCESS,
            "payment_intent.payment_failed": ZoziEventType.PAYMENT_FAILURE,
            "charge.refunded": ZoziEventType.REFUND,
        }
        
        return ZoziPaymentEvent(
            provider_code="stripe",
            gateway_event_id=stripe_event_id,
            event_type=event_type_map.get(event_type, ZoziEventType.PAYMENT_SUCCESS),
            status=normalized_status,
            environment="live" if stripe.api_key.startswith("sk_live_") else "sandbox",
            timestamp=datetime.utcnow(),
            zozi_order_id=zozi_order_id,
            gateway_transaction_id=obj.get("id"),
            gross_amount=amount,
            currency=obj.get("currency", "USD").upper(),
            gateway_fee=gateway_fee,
            net_settlement=amount - gateway_fee,
            raw_payload=event,
        )

