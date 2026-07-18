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

PAYTABS_API_BASE = "https://secure.paytabs.com"


class PayTabsAdapter(BasePaymentGateway):
    gateway_id = "paytabs"
    display_name = "PayTabs"

    def _headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        return {
            "Authorization": credentials.get("server_key", ""),
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
        profile_id = credentials.get("profile_id", "")
        url = f"{PAYTABS_API_BASE}/payment/request"
        payload = {
            "profile_id": profile_id,
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_id": str(order_id or ""),
            "cart_currency": currency.upper(),
            "cart_amount": amount,
            "cart_description": description or "Order payment",
            "hide_shipping": True,
        }
        if customer:
            payload["customer_details"] = {
                "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
            }
        return_url = kwargs.get("return_url")
        if return_url:
            payload["return"] = return_url

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            if resp.is_success and data.get("redirect_url"):
                return PaymentResult(
                    success=True,
                    transaction_id=data.get("tran_ref"),
                    gateway_ref=data.get("tran_ref"),
                    amount=amount,
                    currency=currency.upper(),
                    status="pending",
                    redirect_url=data["redirect_url"],
                    raw_response=data,
                )
            return PaymentResult(
                success=False,
                error_code=data.get("code", "paytabs_error"),
                error_message=data.get("message", str(data)),
                raw_response=data,
            )
        except httpx.RequestError as exc:
            logger.warning("PayTabs payment error: %s", exc)
            return PaymentResult(success=False, error_code="paytabs_connection_error", error_message=str(exc))

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        profile_id = credentials.get("profile_id", "")
        url = f"{PAYTABS_API_BASE}/payment/request"
        payload = {
            "profile_id": profile_id,
            "tran_type": "refund",
            "tran_class": "ecom",
            "cart_id": transaction_id,
            "cart_amount": amount or 0,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload, headers=self._headers(credentials))
            data = resp.json()
            if resp.is_success:
                return RefundResult(
                    success=True,
                    refund_id=data.get("tran_ref"),
                    gateway_ref=data.get("tran_ref"),
                    amount=amount,
                    status=data.get("status", "pending"),
                )
            return RefundResult(
                success=False,
                error_code=data.get("code", "paytabs_refund_error"),
                error_message=data.get("message", str(data)),
            )
        except httpx.RequestError as exc:
            logger.warning("PayTabs refund error: %s", exc)
            return RefundResult(success=False, error_code="paytabs_connection_error", error_message=str(exc))

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{PAYTABS_API_BASE}/payment/request",
                    headers=self._headers(credentials),
                )
            return ConnectionTestResult(
                success=resp.is_success,
                message="PayTabs connection OK" if resp.is_success else f"HTTP {resp.status_code}",
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
        signature = headers.get("X-PAYTABS-SIGNATURE", "")
        if not signature:
            return False
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> ZoziPaymentEvent:
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            try:
                from urllib.parse import parse_qs
                parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
                payload = {key: values[-1] for key, values in parsed.items() if values}
            except Exception:
                pass
        
        for key, value in headers.items():
            if key.lower() not in ("content-type", "content-length"):
                if key not in payload:
                    payload[key] = value
        
        payment_result = payload.get("payment_result") or payload.get("result") or {}
        if isinstance(payment_result, dict):
            for key in ("response_status", "payment_status", "tran_status"):
                if key in payment_result:
                    payload[key] = payment_result[key]
        
        tran_ref = str(payload.get("tran_ref") or payload.get("transaction_reference") or "").strip()
        cart_id = str(payload.get("cart_id") or payload.get("order_id") or "").strip()
        
        response_status = str(payload.get("response_status") or payload.get("payment_status") or "").strip().lower()
        
        gross_amount = Decimal(str(payload.get("cart_amount") or 0))
        gateway_fee = Decimal("0")
        
        normalized_status = ZoziEventStatus.PAYMENT_CAPTURED if response_status in ("a", "approved", "success", "captured") else ZoziEventStatus.PAYMENT_FAILED
        
        return ZoziPaymentEvent(
            provider_code="paytabs",
            gateway_event_id=f"{tran_ref or cart_id}:{response_status}",
            event_type=ZoziEventType.PAYMENT_SUCCESS if response_status in ("a", "approved", "success", "captured") else ZoziEventType.PAYMENT_FAILURE,
            status=normalized_status,
            environment="live",
            timestamp=datetime.utcnow(),
            zozi_order_id=cart_id if cart_id.isdigit() else None,
            gateway_transaction_id=tran_ref or cart_id,
            gross_amount=gross_amount,
            currency=payload.get("cart_currency", "USD").upper(),
            gateway_fee=gateway_fee,
            net_settlement=gross_amount - gateway_fee,
            raw_payload=payload,
        )

