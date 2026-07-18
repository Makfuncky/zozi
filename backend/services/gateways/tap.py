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

TAP_API_BASE = "https://api.tap.company/v2"


class TapAdapter(BasePaymentGateway):
    gateway_id = "tap"
    display_name = "Tap"

    def _headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        key = credentials.get("secret_key") or credentials.get("api_key") or ""
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

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
        url = f"{TAP_API_BASE}/charges"
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": currency.upper(),
            "threeDSecure": True,
            "description": description,
            "metadata": dict(metadata or {}),
        }
        if order_id:
            payload["reference"] = {"transaction": str(order_id), "order": str(order_id)}
        if customer:
            payload["customer"] = {
                "first_name": customer.get("first_name", ""),
                "last_name": customer.get("last_name", ""),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
            }
        source_id = kwargs.get("source_id")
        if source_id:
            payload["source"] = {"id": source_id}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            if resp.is_success and data.get("status") == "INITIATED":
                return PaymentResult(
                    success=True,
                    transaction_id=data.get("id"),
                    gateway_ref=data.get("id"),
                    amount=amount,
                    currency=currency.upper(),
                    status="initiated",
                    redirect_url=data.get("transaction", {}).get("url"),
                    raw_response=data,
                )
            error_msg = data.get("errors", [{}])[0].get("description", str(data))
            return PaymentResult(
                success=False,
                error_code=data.get("status", "tap_error"),
                error_message=error_msg,
                raw_response=data,
            )
        except httpx.RequestError as exc:
            logger.warning("Tap payment error: %s", exc)
            return PaymentResult(success=False, error_code="tap_connection_error", error_message=str(exc))

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        url = f"{TAP_API_BASE}/refunds"
        payload: dict[str, Any] = {"charge_id": transaction_id}
        if amount is not None:
            payload["amount"] = amount
        if reason:
            payload["reason"] = reason

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            if resp.is_success:
                return RefundResult(
                    success=True,
                    refund_id=data.get("id"),
                    gateway_ref=data.get("id"),
                    amount=amount,
                    status=data.get("status", "pending"),
                )
            return RefundResult(
                success=False,
                error_code=data.get("status", "tap_refund_error"),
                error_message=str(data),
            )
        except httpx.RequestError as exc:
            logger.warning("Tap refund error: %s", exc)
            return RefundResult(success=False, error_code="tap_connection_error", error_message=str(exc))

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(f"{TAP_API_BASE}/charges", headers=self._headers(credentials))
            if resp.is_success:
                return ConnectionTestResult(success=True, message="Tap connection OK")
            return ConnectionTestResult(success=False, message=f"HTTP {resp.status_code}")
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
        sig_header = headers.get("hashstring", "")
        if not sig_header:
            return False
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, sig_header)

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> ZoziPaymentEvent:
        data = json.loads(raw_body)
        charge_id = data.get("id", "")
        status = str(data.get("status", "") or "").upper()
        
        metadata = data.get("metadata", {}) or {}
        zozi_order_id = metadata.get("order_id")
        
        amount = Decimal(str(data.get("amount", 0)))
        gateway_fee = Decimal(str(data.get("fee", {}).get("debit", 0) or 0))
        
        normalized_status = ZoziEventStatus.PAYMENT_CAPTURED if status == "CAPTURED" else ZoziEventStatus.PAYMENT_FAILED
        if status == "REFUNDED":
            normalized_status = ZoziEventStatus.REFUND_SUCCEEDED
        
        return ZoziPaymentEvent(
            provider_code="tap",
            gateway_event_id=f"{charge_id}:{status}",
            event_type=ZoziEventType.PAYMENT_SUCCESS if status == "CAPTURED" else ZoziEventType.PAYMENT_FAILURE,
            status=normalized_status,
            environment="live",
            timestamp=datetime.utcnow(),
            zozi_order_id=zozi_order_id,
            gateway_transaction_id=charge_id,
            gross_amount=amount,
            currency=data.get("currency", "USD").upper(),
            gateway_fee=gateway_fee,
            net_settlement=amount - gateway_fee,
            raw_payload=data,
        )

