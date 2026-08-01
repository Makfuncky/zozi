from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from models import CountryConfig, CountryGatewayCredentials
from services.payments.base import BasePaymentGateway, PaymentResult, ConnectionTestResult, RefundResult
from services.payments.registry import PaymentGatewayRegistry

logger = logging.getLogger(__name__)


class PaymentEngine:
    """Orchestrates payment operations across countries and gateways.

    Usage::

        engine = PaymentEngine(db)
        result = engine.process_payment(
            country_code="SA",
            gateway_id="stripe",
            amount=199.99,
            currency="SAR",
            order_id=42,
        )
    """

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def process_payment(
        self,
        country_code: str,
        gateway_id: str,
        amount: float,
        currency: str,
        *,
        order_id: int | None = None,
        description: str = "",
        customer: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        environment: str = "test",
        **kwargs: Any,
    ) -> PaymentResult:
        country = self._get_country(country_code)
        if not country:
            return PaymentResult(
                success=False,
                error_code="country_not_found",
                error_message=f"Country '{country_code}' not configured",
            )
        if not self._gateway_enabled_for_country(country, gateway_id):
            return PaymentResult(
                success=False,
                error_code="gateway_not_enabled",
                error_message=f"Gateway '{gateway_id}' is not enabled for {country_code}",
            )
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        if not self._validate_adapter_creds(adapter, credentials):
            return PaymentResult(
                success=False,
                error_code="credentials_invalid",
                error_message=f"Invalid or missing credentials for {gateway_id} ({environment})",
            )
        return adapter.process_payment(
            amount=amount,
            currency=currency,
            credentials=credentials,
            order_id=order_id,
            description=description,
            customer=customer,
            metadata=metadata,
            **kwargs,
        )

    def process_refund(
        self,
        country_code: str,
        gateway_id: str,
        transaction_id: str,
        amount: float | None = None,
        *,
        environment: str = "test",
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        return adapter.process_refund(
            transaction_id=transaction_id,
            amount=amount,
            credentials=credentials,
            reason=reason,
            **kwargs,
        )

    def test_gateway_connection(
        self,
        country_code: str,
        gateway_id: str,
        *,
        environment: str = "test",
    ) -> ConnectionTestResult:
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        return adapter.test_connection(credentials)

    def get_available_gateways(self, country_code: str | None = None) -> list[dict[str, Any]]:
        gateways = []
        for gid in PaymentGatewayRegistry.list_available():
            cls = PaymentGatewayRegistry.get(gid)
            enabled = True
            if country_code:
                country = self._get_country(country_code)
                enabled = self._gateway_enabled_for_country(country, gid) if country else False
            gateways.append({
                "gateway_id": gid,
                "display_name": cls.display_name if cls else gid,
                "enabled": enabled,
            })
        return gateways

    def validate_credentials(
        self,
        gateway_id: str,
        credentials: dict[str, Any],
    ) -> bool:
        adapter_cls = PaymentGatewayRegistry.get(gateway_id)
        if not adapter_cls:
            return False
        return adapter_cls().validate_credentials(credentials)

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _get_country(self, country_code: str) -> CountryConfig | None:
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper(),
            CountryConfig.is_active == True,
        ).first()

    def _gateway_enabled_for_country(self, country: CountryConfig, gateway_id: str) -> bool:
        raw = country.payment_gateways_json
        if not raw:
            return False
        try:
            gateways = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return False
        if not isinstance(gateways, list):
            return False
        for gw in gateways:
            if isinstance(gw, dict) and str(gw.get("gateway_id", "")).lower() == gateway_id.lower():
                return bool(gw.get("enabled", False))
        return False

    def _get_adapter(self, gateway_id: str) -> BasePaymentGateway:
        cls = PaymentGatewayRegistry.get_or_raise(gateway_id)
        return cls()

    def _load_credentials(
        self,
        country_code: str,
        gateway_id: str,
        environment: str,
    ) -> dict[str, Any]:
        record = self.db.query(CountryGatewayCredentials).filter(
            CountryGatewayCredentials.country_code == country_code.upper(),
            CountryGatewayCredentials.gateway_id == gateway_id,
            CountryGatewayCredentials.environment == environment,
            CountryGatewayCredentials.is_active == True,
        ).first()
        if record and record.encrypted_credentials:
            try:
                import json
                return json.loads(record.encrypted_credentials)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Could not decode credentials for %s/%s/%s", country_code, gateway_id, environment)
                return {}
        return {}

    def _validate_adapter_creds(self, adapter: BasePaymentGateway, credentials: dict[str, Any]) -> bool:
        return bool(credentials) and adapter.validate_credentials(credentials)

