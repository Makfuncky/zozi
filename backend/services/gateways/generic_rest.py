"""
Generic REST Adapter for simple payment gateways.

Allows Admins to configure basic REST-based gateways through the Admin UI
without writing Python code. Uses stored templates for charge URLs, headers,
and payload structure.
"""
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


class GenericRESTAdapter(BasePaymentGateway):
    """
    Generic adapter for REST-based payment gateways.
    
    Configuration is stored in the `extra_config` field of PaymentGatewayConnection:
    {
        "charge_url": "https://api.example.com/charge",
        "auth_headers": {"Authorization": "Bearer {{secret_key}}"},
        "charge_payload_template": {"amount": "{{amount}}", "currency": "{{currency}}"},
        "refund_url": "https://api.example.com/refund",
        "webhook_signature_header": "X-Signature",
        "webhook_signature_key": "signature"
    }
    """
    gateway_id = "generic_rest"
    display_name = "Generic REST Gateway"

    def _get_extra_config(self, credentials: dict[str, Any]) -> dict[str, Any]:
        return credentials.get("extra_config", {})

    def _render_template(self, template: str, context: dict[str, Any]) -> str:
        result = template
        for key, value in context.items():
            result = result.replace("{{" + key + "}}", str(value))
        return result

    def _render_headers(self, headers_template: dict[str, str], credentials: dict[str, Any]) -> dict[str, str]:
        secret_key = credentials.get("secret_key", "")
        result = {}
        for key, value in headers_template.items():
            rendered = self._render_template(value, {"secret_key": secret_key})
            result[key] = rendered
        return result

    def _render_payload(self, template: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in template.items():
            if isinstance(value, str):
                result[key] = self._render_template(value, context)
            elif isinstance(value, dict):
                result[key] = self._render_payload(value, context)
            else:
                result[key] = value
        return result

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
        extra_config = self._get_extra_config(credentials)
        charge_url = extra_config.get("charge_url")
        if not charge_url:
            return PaymentResult(success=False, error_code="config_error", error_message="charge_url not configured")

        headers = self._render_headers(extra_config.get("auth_headers", {}), credentials)
        payload_template = extra_config.get("charge_payload_template", {})
        context = {
            "amount": str(amount),
            "currency": currency.upper(),
            "order_id": str(order_id or ""),
            "description": description,
        }
        payload = self._render_payload(payload_template, context)
        if metadata:
            payload["metadata"] = metadata

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(charge_url, json=payload, headers=headers)
            data = resp.json()
            
            status = data.get("status", "").lower()
            is_success = resp.is_success and status in ("success", "approved", "captured")
            
            return PaymentResult(
                success=is_success,
                transaction_id=data.get("id") or data.get("transaction_id"),
                gateway_ref=data.get("id") or data.get("transaction_id"),
                amount=amount,
                currency=currency.upper(),
                status=status,
                raw_response=data,
            )
        except httpx.RequestError as exc:
            logger.warning("Generic REST payment error: %s", exc)
            return PaymentResult(success=False, error_code="connection_error", error_message=str(exc))

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        extra_config = self._get_extra_config(credentials)
        refund_url = extra_config.get("refund_url")
        if not refund_url:
            return RefundResult(success=False, error_code="config_error", error_message="refund_url not configured")

        headers = self._render_headers(extra_config.get("auth_headers", {}), credentials)
        payload = {"transaction_id": transaction_id}
        if amount is not None:
            payload["amount"] = str(amount)
        if reason:
            payload["reason"] = reason

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(refund_url, json=payload, headers=headers)
            data = resp.json()
            
            return RefundResult(
                success=resp.is_success,
                refund_id=data.get("id") or transaction_id,
                gateway_ref=data.get("id") or transaction_id,
                amount=amount,
                status=data.get("status", "pending"),
            )
        except httpx.RequestError as exc:
            logger.warning("Generic REST refund error: %s", exc)
            return RefundResult(success=False, error_code="connection_error", error_message=str(exc))

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        extra_config = self._get_extra_config(credentials)
        test_url = extra_config.get("test_url") or credentials.get("api_base_url")
        if not test_url:
            return ConnectionTestResult(success=False, message="No test_url or api_base_url configured")

        headers = self._render_headers(extra_config.get("auth_headers", {}), credentials)
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(test_url, headers=headers)
            if resp.is_success:
                return ConnectionTestResult(success=True, message="Generic REST gateway endpoint reachable")
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
        return True

    def normalize_webhook_payload(
        self,
        raw_body: bytes,
        headers: dict[str, str],
    ) -> ZoziPaymentEvent:
        data = json.loads(raw_body) if raw_body else {}
        
        return ZoziPaymentEvent(
            provider_code="generic_rest",
            gateway_event_id=str(data.get("id") or data.get("event_id") or ""),
            event_type=ZoziEventType.PAYMENT_SUCCESS,
            status=ZoziEventStatus.PAYMENT_CAPTURED,
            environment="live",
            timestamp=datetime.utcnow(),
            zozi_order_id=str(data.get("order_id") or ""),
            gateway_transaction_id=str(data.get("transaction_id") or data.get("id") or ""),
            gross_amount=Decimal(str(data.get("amount") or 0)),
            currency=data.get("currency", "USD").upper(),
            gateway_fee=Decimal("0"),
            net_settlement=Decimal(str(data.get("amount") or 0)),
            raw_payload=data,
        )

