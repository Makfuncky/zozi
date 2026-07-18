from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from .base import BasePaymentGateway
from .base_models import ConnectionTestResult, PaymentResult, RefundResult
from .webhook_models import ZoziEventStatus, ZoziEventType, ZoziPaymentEvent

logger = logging.getLogger(__name__)

THAWANI_API_BASE = "https://uatcheckout.thawani.om"


class ThawaniAdapter(BasePaymentGateway):
    gateway_id = "thawani"
    display_name = "Thawani"

    def _headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        key = credentials.get("secret_key", "")
        return {
            "thawani-api-key": key,
            "Content-Type": "application/json",
        }

    def _publishable_key(self, credentials: dict[str, Any]) -> str:
        return credentials.get("publishable_key", "")

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
        amount_baisa = int(round(amount * 1000))
        url = f"{THAWANI_API_BASE}/api/v1/checkout/session"
        payload = {
            "client_reference_id": str(order_id or ""),
            "mode": "payment",
            "products": [{
                "name": description or "Order payment",
                "quantity": 1,
                "unit_amount": amount_baisa,
            }],
            "success_url": kwargs.get("success_url", ""),
            "cancel_url": kwargs.get("cancel_url", ""),
            "metadata": dict(metadata or {}),
        }
        if customer:
            payload["customer"] = {
                "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
            }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            session_id = data.get("session_id") or data.get("id")
            if resp.is_success and session_id:
                pk = self._publishable_key(credentials)
                redirect = f"{THAWANI_API_BASE}/pay/{session_id}?key={pk}" if pk else None
                return PaymentResult(
                    success=True,
                    transaction_id=session_id,
                    gateway_ref=session_id,
                    amount=amount,
                    currency=currency.upper(),
                    status="initiated",
                    redirect_url=redirect,
                    raw_response=data,
                )
            return PaymentResult(
                success=False,
                error_code=data.get("code", "thawani_error"),
                error_message=data.get("message", str(data)),
                raw_response=data,
            )
        except httpx.RequestError as exc:
            logger.warning("Thawani error: %s", exc)
            return PaymentResult(success=False, error_code="thawani_connection_error", error_message=str(exc))

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        url = f"{THAWANI_API_BASE}/api/v1/checkout/session/{transaction_id}/refund"
        payload: dict[str, Any] = {}
        if amount is not None:
            payload["amount"] = int(round(amount * 1000))
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            if resp.is_success:
                return RefundResult(
                    success=True,
                    refund_id=data.get("id", transaction_id),
                    gateway_ref=data.get("id", transaction_id),
                    amount=amount,
                    status="completed",
                )
            return RefundResult(
                success=False,
                error_code=data.get("code", "thawani_refund_error"),
                error_message=data.get("message", str(data)),
            )
        except httpx.RequestError as exc:
            logger.warning("Thawani refund error: %s", exc)
            return RefundResult(success=False, error_code="thawani_connection_error", error_message=str(exc))

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{THAWANI_API_BASE}/api/v1/checkout/session",
                    headers=self._headers(credentials),
                )
            return ConnectionTestResult(
                success=resp.is_success,
                message="Thawani connection OK" if resp.is_success else f"HTTP {resp.status_code}",
            )
        except httpx.RequestError as exc:
            return ConnectionTestResult(success=False, message=str(exc))

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        headers: dict[str, str],
        webhook_secret: str,
    ) -> bool:
        if not webhook_secret:
            return False
        timestamp = headers.get("thawani-timestamp", "")
        signature = headers.get("thawani-signature", "")
        if not timestamp or not signature:
            return False
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            f"{raw_body.decode('utf-8')}-{timestamp}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> ZoziPaymentEvent:
        data = json.loads(raw_body)
        event_type = str(data.get("type") or data.get("event_type") or "").strip()
        payload_data = data.get("data") or {}
        
        invoice_id = str(payload_data.get("invoice") or payload_data.get("id") or "").strip()
        session_id = str(payload_data.get("session_id") or payload_data.get("checkout_session_id") or "").strip()
        
        client_ref = str(payload_data.get("client_reference_id") or "").strip()
        zozi_order_id = client_ref if client_ref.isdigit() else None
        
        payment_status = str(payload_data.get("payment_status") or "").strip().lower()
        
        gateway_fee = Decimal(str(payload_data.get("gateway_fee") or 0))
        gross_amount = Decimal(str(payload_data.get("amount") or 0))
        
        normalized_status = ZoziEventStatus.PAYMENT_CAPTURED if payment_status == "paid" else ZoziEventStatus.PAYMENT_FAILED
        
        return ZoziPaymentEvent(
            provider_code="thawani",
            gateway_event_id=f"{event_type}:{invoice_id or session_id}",
            event_type=ZoziEventType.PAYMENT_SUCCESS if payment_status == "paid" else ZoziEventType.PAYMENT_FAILURE,
            status=normalized_status,
            environment="live",
            timestamp=datetime.utcnow(),
            zozi_order_id=zozi_order_id,
            gateway_transaction_id=invoice_id or session_id,
            gross_amount=gross_amount,
            currency="OMR",
            gateway_fee=gateway_fee,
            net_settlement=gross_amount - gateway_fee,
            raw_payload=data,
        )

