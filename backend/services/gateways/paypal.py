from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from .base import BasePaymentGateway
from .base_models import ConnectionTestResult, PaymentResult, RefundResult

logger = logging.getLogger(__name__)

PAYPAL_API_BASE = "https://api-m.paypal.com"


class PayPalAdapter(BasePaymentGateway):
    gateway_id = "paypal"
    display_name = "PayPal"

    def _access_token(self, credentials: dict[str, Any]) -> str | None:
        client_id = credentials.get("client_id", "")
        client_secret = credentials.get("client_secret", "")
        if not client_id or not client_secret:
            return None
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    f"{PAYPAL_API_BASE}/v1/oauth2/token",
                    data={"grant_type": "client_credentials"},
                    auth=(client_id, client_secret),
                    headers={"Accept": "application/json"},
                )
            if resp.is_success:
                return resp.json().get("access_token")
            return None
        except httpx.RequestError:
            return None

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
        token = self._access_token(credentials)
        if not token:
            return PaymentResult(success=False, error_code="auth_error", error_message="Could not get PayPal access token")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": currency.upper(), "value": f"{amount:.2f}"},
                "description": description[:127] if description else "",
            }],
        }
        if order_id:
            payload["purchase_units"][0]["invoice_id"] = str(order_id)
        if customer:
            payload["payer"] = {
                "name": {
                    "given_name": customer.get("first_name", ""),
                    "surname": customer.get("last_name", ""),
                },
                "email_address": customer.get("email", ""),
            }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{PAYPAL_API_BASE}/v2/checkout/orders",
                    json=payload,
                    headers=headers,
                )
            data = resp.json()
            if resp.is_success:
                approval_url = ""
                for link in data.get("links", []):
                    if link.get("rel") == "payer-action":
                        approval_url = link.get("href", "")
                        break
                return PaymentResult(
                    success=True,
                    transaction_id=data.get("id"),
                    gateway_ref=data.get("id"),
                    amount=amount,
                    currency=currency.upper(),
                    status=data.get("status", "pending"),
                    redirect_url=approval_url or None,
                    raw_response=data,
                )
            return PaymentResult(
                success=False,
                error_code=data.get("name", "paypal_error"),
                error_message=data.get("message", str(data)),
                raw_response=data,
            )
        except httpx.RequestError as exc:
            logger.warning("PayPal error: %s", exc)
            return PaymentResult(success=False, error_code="paypal_connection_error", error_message=str(exc))

    def process_refund(
        self,
        transaction_id: str,
        amount: float | None,
        credentials: dict[str, Any],
        *,
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        token = self._access_token(credentials)
        if not token:
            return RefundResult(success=False, error_code="auth_error", error_message="Could not get PayPal access token")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {}
        if amount is not None:
            capture_id = kwargs.get("capture_id", "")
            if capture_id:
                payload["amount"] = {
                    "value": f"{amount:.2f}",
                    "currency_code": kwargs.get("currency", "USD"),
                }
                try:
                    with httpx.Client(timeout=30) as client:
                        resp = client.post(
                            f"{PAYPAL_API_BASE}/v2/payments/captures/{capture_id}/refund",
                            json=payload,
                            headers=headers,
                        )
                except httpx.RequestError as exc:
                    return RefundResult(success=False, error_code="paypal_connection_error", error_message=str(exc))
            else:
                return RefundResult(success=False, error_code="missing_capture_id", error_message="capture_id required for partial refund")
        else:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(
                        f"{PAYPAL_API_BASE}/v2/checkout/orders/{transaction_id}/refund",
                        json=payload,
                        headers=headers,
                    )
            except httpx.RequestError as exc:
                return RefundResult(success=False, error_code="paypal_connection_error", error_message=str(exc))

        data = resp.json()
        if resp.is_success:
            return RefundResult(
                success=True,
                refund_id=data.get("id"),
                gateway_ref=data.get("id"),
                amount=amount,
                status=data.get("status", "completed"),
            )
        return RefundResult(
            success=False,
            error_code=data.get("name", "paypal_refund_error"),
            error_message=data.get("message", str(data)),
        )

    def test_connection(self, credentials: dict[str, Any]) -> ConnectionTestResult:
        token = self._access_token(credentials)
        if token:
            return ConnectionTestResult(success=True, message="PayPal connection OK")
        return ConnectionTestResult(success=False, message="Could not authenticate with PayPal")

