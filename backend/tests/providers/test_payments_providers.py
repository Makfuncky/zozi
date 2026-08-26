"""Comprehensive tests for the payments/ provider subpackage.

Tests cover:
- backend/providers/payments/ (config, base, base_models, webhook_models,
  webhooks, generic, connect, registry, stripe_sdk, paypal, paytabs, tap, thawani)

Run with: pytest tests/providers/test_payments_providers.py -v
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


# ===========================================================================
# webhook_models.py — ZoziPaymentEvent, ZoziRefundEvent, ZoziChargebackEvent
# ===========================================================================


class TestWebhookEventType:
    def test_payment_value(self):
        from providers.payments.webhook_models import WebhookEventType
        assert WebhookEventType.PAYMENT == "payment"

    def test_refund_value(self):
        from providers.payments.webhook_models import WebhookEventType
        assert WebhookEventType.REFUND == "refund"

    def test_chargeback_value(self):
        from providers.payments.webhook_models import WebhookEventType
        assert WebhookEventType.CHARGEBACK == "chargeback"

    def test_unknown_value(self):
        from providers.payments.webhook_models import WebhookEventType
        assert WebhookEventType.UNKNOWN == "unknown"

    def test_is_str_enum(self):
        from providers.payments.webhook_models import WebhookEventType
        assert isinstance(WebhookEventType.PAYMENT, str)


class TestWebhookStatus:
    def test_succeeded_value(self):
        from providers.payments.webhook_models import WebhookStatus
        assert WebhookStatus.SUCCEEDED == "succeeded"

    def test_failed_value(self):
        from providers.payments.webhook_models import WebhookStatus
        assert WebhookStatus.FAILED == "failed"

    def test_pending_value(self):
        from providers.payments.webhook_models import WebhookStatus
        assert WebhookStatus.PENDING == "pending"

    def test_disputed_value(self):
        from providers.payments.webhook_models import WebhookStatus
        assert WebhookStatus.DISPUTED == "disputed"

    def test_unknown_value(self):
        from providers.payments.webhook_models import WebhookStatus
        assert WebhookStatus.UNKNOWN == "unknown"


class TestZoziPaymentEvent:
    def test_create_minimal(self):
        from providers.payments.webhook_models import ZoziPaymentEvent
        event = ZoziPaymentEvent(provider_code="stripe", gateway_event_id="evt_123")
        assert event.provider_code == "stripe"
        assert event.gateway_event_id == "evt_123"

    def test_event_type_defaults_to_payment(self):
        from providers.payments.webhook_models import ZoziPaymentEvent, WebhookEventType
        event = ZoziPaymentEvent(provider_code="stripe", gateway_event_id="evt_123")
        assert event.event_type == WebhookEventType.PAYMENT

    def test_status_defaults_to_unknown(self):
        from providers.payments.webhook_models import ZoziPaymentEvent, WebhookStatus
        event = ZoziPaymentEvent(provider_code="stripe", gateway_event_id="evt_123")
        assert event.status == WebhookStatus.UNKNOWN

    def test_full_create(self):
        from providers.payments.webhook_models import ZoziPaymentEvent, WebhookEventType, WebhookStatus
        now = datetime.now(tz=timezone.utc)
        event = ZoziPaymentEvent(
            provider_code="stripe",
            gateway_event_id="evt_full",
            event_type=WebhookEventType.PAYMENT,
            status=WebhookStatus.SUCCEEDED,
            environment="live",
            timestamp=now,
            zozi_order_id="order_42",
            gateway_transaction_id="txn_42",
            gateway_customer_id="cus_42",
            gross_amount=99.99,
            currency="USD",
            gateway_fee=3.30,
            net_settlement=96.69,
            fraud_score=0.1,
            three_ds_status="Y",
            avs_result="match",
            raw_payload={"foo": "bar"},
        )
        assert event.environment == "live"
        assert event.gross_amount == 99.99
        assert event.currency == "USD"
        assert event.raw_payload == {"foo": "bar"}


class TestZoziRefundEvent:
    def test_event_type_defaults_to_refund(self):
        from providers.payments.webhook_models import ZoziRefundEvent, WebhookEventType
        event = ZoziRefundEvent(provider_code="stripe", gateway_event_id="evt_ref")
        assert event.event_type == WebhookEventType.REFUND

    def test_create(self):
        from providers.payments.webhook_models import ZoziRefundEvent
        event = ZoziRefundEvent(
            provider_code="paypal",
            gateway_event_id="evt_paypal_ref",
            zozi_order_id="order_42",
            gross_amount=50.00,
            currency="USD",
        )
        assert event.gross_amount == 50.00
        assert event.zozi_order_id == "order_42"


class TestZoziChargebackEvent:
    def test_event_type_defaults_to_chargeback(self):
        from providers.payments.webhook_models import ZoziChargebackEvent, WebhookEventType
        event = ZoziChargebackEvent(provider_code="stripe", gateway_event_id="evt_cb")
        assert event.event_type == WebhookEventType.CHARGEBACK

    def test_create(self):
        from providers.payments.webhook_models import ZoziChargebackEvent
        event = ZoziChargebackEvent(
            provider_code="stripe",
            gateway_event_id="evt_cb_1",
            fraud_score=0.95,
        )
        assert event.fraud_score == 0.95


# ===========================================================================
# base_models.py — ConnectionTestResult, PaymentResult, RefundResult
# ===========================================================================


class TestConnectionTestResult:
    def test_create_success(self):
        from providers.payments.base_models import ConnectionTestResult
        result = ConnectionTestResult(success=True, message="OK")
        assert result.success is True
        assert result.message == "OK"
        assert result.details == {}
        assert result.tested_at is None

    def test_create_failure(self):
        from providers.payments.base_models import ConnectionTestResult
        result = ConnectionTestResult(success=False, message="Invalid key")
        assert result.success is False

    def test_with_details(self):
        from providers.payments.base_models import ConnectionTestResult
        result = ConnectionTestResult(
            success=True, message="OK",
            details={"latency_ms": 120, "region": "us-east-1"},
            tested_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        assert result.details["latency_ms"] == 120


class TestPaymentResult:
    def test_create_success(self):
        from providers.payments.base_models import PaymentResult
        result = PaymentResult(
            success=True,
            transaction_id="txn_123",
            amount=99.99,
            currency="USD",
        )
        assert result.success is True
        assert result.transaction_id == "txn_123"

    def test_create_failure(self):
        from providers.payments.base_models import PaymentResult
        result = PaymentResult(
            success=False,
            error_code="card_declined",
            error_message="Your card was declined.",
        )
        assert result.success is False
        assert result.error_code == "card_declined"

    def test_defaults(self):
        from providers.payments.base_models import PaymentResult
        result = PaymentResult(success=True)
        assert result.transaction_id is None
        assert result.gateway_response == {}


class TestRefundResult:
    def test_create_success(self):
        from providers.payments.base_models import RefundResult
        result = RefundResult(
            success=True,
            refund_id="ref_456",
            amount=25.00,
            currency="USD",
        )
        assert result.success is True
        assert result.refund_id == "ref_456"

    def test_create_failure(self):
        from providers.payments.base_models import RefundResult
        result = RefundResult(
            success=False,
            error_code="refund_failed",
            error_message="Cannot refund",
        )
        assert result.success is False

    def test_defaults(self):
        from providers.payments.base_models import RefundResult
        result = RefundResult(success=True)
        assert result.refund_id is None
        assert result.gateway_response == {}


# ===========================================================================
# base.py — GatewaySettings, GatewayDefinition, registry, BasePaymentGateway
# ===========================================================================


class TestGatewaySettings:
    def test_is_usable_enabled_with_key(self):
        from providers.payments.base import GatewaySettings
        settings = GatewaySettings(
            provider_code="stripe",
            provider_kind="card",
            display_name="Stripe",
            is_enabled=True,
            secret_key="sk_live_xxx",
        )
        assert settings.is_usable() is True

    def test_is_usable_disabled(self):
        from providers.payments.base import GatewaySettings
        settings = GatewaySettings(
            provider_code="stripe",
            provider_kind="card",
            display_name="Stripe",
            is_enabled=False,
            secret_key="sk_live_xxx",
        )
        assert settings.is_usable() is False

    def test_is_usable_missing_secret(self):
        from providers.payments.base import GatewaySettings
        settings = GatewaySettings(
            provider_code="stripe",
            provider_kind="card",
            display_name="Stripe",
            is_enabled=True,
            secret_key=None,
        )
        assert settings.is_usable() is False

    def test_defaults(self):
        from providers.payments.base import GatewaySettings
        settings = GatewaySettings(
            provider_code="tap",
            provider_kind="card",
            display_name="Tap",
        )
        assert settings.is_enabled is False
        assert settings.mode == "test"
        assert settings.supports_customer_checkout is False
        assert settings.supports_payouts is False


class TestGatewayDefinition:
    def test_create(self):
        from providers.payments.base import GatewayDefinition
        defn = GatewayDefinition(
            code="stripe",
            kind="card",
            label="Stripe",
            module="providers.payments.stripe_sdk",
            settings_resolver=lambda: {},
            is_configured=lambda: True,
        )
        assert defn.code == "stripe"
        assert defn.operations == {}

    def test_create_with_operations(self):
        from providers.payments.base import GatewayDefinition
        defn = GatewayDefinition(
            code="stripe",
            kind="card",
            label="Stripe",
            module="providers.payments.stripe_sdk",
            settings_resolver=lambda: {},
            is_configured=lambda: True,
            operations={"create": lambda: None},
        )
        assert "create" in defn.operations


class TestProviderRegistry:
    def setup_method(self):
        from providers.payments.base import _REGISTRY, register_provider, get_provider
        self.REGISTRY = _REGISTRY
        self.register_provider = register_provider
        self.get_provider = get_provider
        self._original = dict(_REGISTRY)

    def teardown_method(self):
        self.REGISTRY.clear()
        self.REGISTRY.update(self._original)

    def test_register_and_get(self):
        from providers.payments.base import GatewayDefinition
        defn = GatewayDefinition(
            code="test_gw",
            kind="card",
            label="Test GW",
            module="test_module",
            settings_resolver=lambda: {},
            is_configured=lambda: True,
        )
        self.register_provider(defn)
        result = self.get_provider("test_gw")
        assert result is defn

    def test_get_missing_returns_none(self):
        result = self.get_provider("nonexistent_gateway_xyz")
        assert result is None


class TestDispatchProviderOperation:
    def setup_method(self):
        from providers.payments.base import _REGISTRY
        self._original = dict(_REGISTRY)

    def teardown_method(self):
        from providers.payments.base import _REGISTRY
        _REGISTRY.clear()
        _REGISTRY.update(self._original)

    def test_dispatch_success(self):
        from providers.payments.base import GatewayDefinition, register_provider, dispatch_provider_operation
        mock_handler = MagicMock(return_value={"result": "ok"})
        defn = GatewayDefinition(
            code="test_dispatch",
            kind="card",
            label="Test Dispatch",
            module="test_module",
            settings_resolver=lambda: {},
            is_configured=lambda: True,
            operations={"create": mock_handler},
        )
        register_provider(defn)
        result = dispatch_provider_operation("test_dispatch", "create", 1, 2, key="val")
        mock_handler.assert_called_once_with(1, 2, key="val")
        assert result == {"result": "ok"}

    def test_dispatch_provider_not_found(self):
        from providers.payments.base import dispatch_provider_operation
        with pytest.raises(LookupError, match="No payment provider registered"):
            dispatch_provider_operation("nonexistent", "create")

    def test_dispatch_operation_not_found(self):
        from providers.payments.base import GatewayDefinition, register_provider, dispatch_provider_operation
        defn = GatewayDefinition(
            code="test_no_op",
            kind="card",
            label="Test",
            module="test",
            settings_resolver=lambda: {},
            is_configured=lambda: True,
            operations={},
        )
        register_provider(defn)
        with pytest.raises(LookupError, match="does not implement operation"):
            dispatch_provider_operation("test_no_op", "create")


class TestBasePaymentGateway:
    def test_validate_credentials_nonempty(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        assert gw.validate_credentials({"key": "val"}) is True

    def test_validate_credentials_empty(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        assert gw.validate_credentials({}) is False

    def test_process_payment_default(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        result = gw.process_payment(100.0, "USD", {"key": "val"})
        assert result.success is False
        assert result.error_code == "not_implemented"

    def test_process_refund_default(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        result = gw.process_refund("txn_1", amount=50.0, credentials={"key": "val"})
        assert result.success is False
        assert result.error_code == "not_implemented"

    def test_test_connection_default(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        result = gw.test_connection({"key": "val"})
        assert result.success is False

    def test_verify_webhook_signature_empty_secret(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        assert gw.verify_webhook_signature(b"body", "sig", "") is False

    def test_verify_webhook_signature_nonempty_secret(self):
        from providers.payments.base import BasePaymentGateway

        class ConcreteGateway(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="test", gateway_event_id="e1")

        gw = ConcreteGateway()
        assert gw.verify_webhook_signature(b"body", "sig", "secret") is True

    def test_normalize_webhook_payload_abstract(self):
        from providers.payments.base import BasePaymentGateway
        with pytest.raises(TypeError):
            BasePaymentGateway()

    def test_display_name_default(self):
        from providers.payments.base import BasePaymentGateway
        assert BasePaymentGateway.display_name == "Gateway"


# ===========================================================================
# registry.py — PaymentGatewayRegistry
# ===========================================================================


class TestPaymentGatewayRegistry:
    def setup_method(self):
        from providers.payments.registry import PaymentGatewayRegistry
        self.registry = PaymentGatewayRegistry
        PaymentGatewayRegistry.clear()

    def teardown_method(self):
        self.registry.clear()

    def test_register_and_get(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        assert self.registry.get("mygw") is MyGw

    def test_register_lowercases_code(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("MyGW", MyGw)
        assert self.registry.get("mygw") is MyGw

    def test_get_missing_returns_none(self):
        assert self.registry.get("nonexistent") is None

    def test_get_or_raise_found(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        assert self.registry.get_or_raise("mygw") is MyGw

    def test_get_or_raise_missing_raises(self):
        with pytest.raises(KeyError, match="No gateway adapter registered"):
            self.registry.get_or_raise("nonexistent")

    def test_list_available_empty(self):
        assert self.registry.list_available() == []

    def test_list_available_sorted(self):
        from providers.payments.base import BasePaymentGateway

        class GwA(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="a", gateway_event_id="e1")

        class GwB(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="b", gateway_event_id="e1")

        self.registry.register("bravo", GwB)
        self.registry.register("alpha", GwA)
        result = self.registry.list_available()
        assert result == ["alpha", "bravo"]

    def test_unregister(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        self.registry.unregister("mygw")
        assert self.registry.get("mygw") is None

    def test_unregister_nonexistent_no_error(self):
        self.registry.unregister("nonexistent")

    def test_clear(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        self.registry.clear()
        assert self.registry.all() == {}

    def test_all(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        result = self.registry.all()
        assert "mygw" in result

    def test_register_adapter_decorator(self):
        from providers.payments.base import BasePaymentGateway

        @self.registry.register_adapter("decorated_gw")
        class MyGw(BasePaymentGateway):
            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="decorated_gw", gateway_event_id="e1")

        assert self.registry.get("decorated_gw") is MyGw

    def test_build(self):
        from providers.payments.base import BasePaymentGateway

        class MyGw(BasePaymentGateway):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def normalize_webhook_payload(self, raw_body, headers):
                from providers.payments.webhook_models import ZoziPaymentEvent
                return ZoziPaymentEvent(provider_code="mygw", gateway_event_id="e1")

        self.registry.register("mygw", MyGw)
        instance = self.registry.build("mygw", "arg1", key="val")
        assert isinstance(instance, MyGw)
        assert instance.args == ("arg1",)
        assert instance.kwargs == {"key": "val"}

    def test_build_or_raise_not_found(self):
        with pytest.raises(KeyError):
            self.registry.build("nonexistent")


# ===========================================================================
# config.py — Stripe config helpers
# ===========================================================================


class TestStripeConfig:
    @patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_live_abc123"}, clear=False)
    def test_resolve_stripe_secret_key_from_env(self):
        from providers.payments.config import resolve_stripe_secret_key
        result = resolve_stripe_secret_key()
        assert result == "sk_live_abc123"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_stripe_secret_key_empty(self):
        from providers.payments.config import resolve_stripe_secret_key
        result = resolve_stripe_secret_key()
        assert result == ""

    @patch.dict(os.environ, {"STRIPE_SECRET_KEY": "  sk_test_xyz  "}, clear=False)
    def test_resolve_stripe_secret_key_strips_whitespace(self):
        from providers.payments.config import resolve_stripe_secret_key
        result = resolve_stripe_secret_key()
        assert result == "sk_test_xyz"

    @patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_123"}, clear=False)
    def test_resolve_stripe_webhook_secret(self):
        from providers.payments.config import resolve_stripe_webhook_secret
        result = resolve_stripe_webhook_secret()
        assert result == "whsec_123"

    @patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_live_abc"}, clear=False)
    def test_is_stripe_configured_true(self):
        from providers.payments.config import is_stripe_configured
        assert is_stripe_configured() is True

    @patch.dict(os.environ, {"STRIPE_SECRET_KEY": "placeholder"}, clear=False)
    def test_is_stripe_configured_placeholder(self):
        from providers.payments.config import is_stripe_configured
        assert is_stripe_configured() is False

    @patch.dict(os.environ, {}, clear=False)
    def test_is_stripe_configured_empty(self):
        from providers.payments.config import is_stripe_configured
        assert is_stripe_configured() is False

    @patch("providers.payments.config.stripe")
    def test_apply_stripe_runtime_key_sets_key(self, mock_stripe):
        from providers.payments.config import apply_stripe_runtime_key
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_apply"}):
            result = apply_stripe_runtime_key()
            assert result == "sk_test_apply"
            mock_stripe.api_key = "sk_test_apply"


# ===========================================================================
# config.py — Tap config helpers
# ===========================================================================


class TestTapConfig:
    @patch.dict(os.environ, {"TAP_SECRET_KEY": "sk_test_tap"}, clear=False)
    def test_resolve_tap_secret_key(self):
        from providers.payments.config import resolve_tap_secret_key
        assert resolve_tap_secret_key() == "sk_test_tap"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_tap_secret_key_empty(self):
        from providers.payments.config import resolve_tap_secret_key
        assert resolve_tap_secret_key() == ""

    @patch.dict(os.environ, {"TAP_WEBHOOK_SECRET": "wh_tap"}, clear=False)
    def test_resolve_tap_webhook_secret(self):
        from providers.payments.config import resolve_tap_webhook_secret
        assert resolve_tap_webhook_secret() == "wh_tap"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_tap_api_base_url_default(self):
        from providers.payments.config import resolve_tap_api_base_url
        assert resolve_tap_api_base_url() == "https://api.tap.company"

    @patch.dict(os.environ, {"TAP_API_BASE_URL": "https://custom.tap.com/"}, clear=False)
    def test_resolve_tap_api_base_url_custom(self):
        from providers.payments.config import resolve_tap_api_base_url
        assert resolve_tap_api_base_url() == "https://custom.tap.com"

    @patch.dict(os.environ, {"TAP_WEBHOOK_URL": "https://webhook.tap.com"}, clear=False)
    def test_resolve_tap_webhook_url(self):
        from providers.payments.config import resolve_tap_webhook_url
        assert resolve_tap_webhook_url() == "https://webhook.tap.com"

    @patch.dict(os.environ, {"TAP_SECRET_KEY": "sk_test_tap"}, clear=False)
    def test_is_tap_configured_true(self):
        from providers.payments.config import is_tap_configured
        assert is_tap_configured() is True

    @patch.dict(os.environ, {"TAP_SECRET_KEY": "sk_live_xxx"}, clear=False)
    def test_is_tap_configured_live(self):
        from providers.payments.config import is_tap_configured
        assert is_tap_configured() is True

    @patch.dict(os.environ, {"TAP_SECRET_KEY": "sk_xxx"}, clear=False)
    def test_is_tap_configured_generic_sk(self):
        from providers.payments.config import is_tap_configured
        assert is_tap_configured() is True

    @patch.dict(os.environ, {"TAP_SECRET_KEY": "no_prefix"}, clear=False)
    def test_is_tap_configured_no_prefix(self):
        from providers.payments.config import is_tap_configured
        assert is_tap_configured() is False

    @patch.dict(os.environ, {}, clear=False)
    def test_is_tap_configured_empty(self):
        from providers.payments.config import is_tap_configured
        assert is_tap_configured() is False


# ===========================================================================
# config.py — PayTabs config helpers
# ===========================================================================


class TestPayTabsConfig:
    @patch.dict(os.environ, {"PAYTABS_SERVER_KEY": "server_key_123"}, clear=False)
    def test_resolve_paytabs_server_key(self):
        from providers.payments.config import resolve_paytabs_server_key
        assert resolve_paytabs_server_key() == "server_key_123"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_paytabs_server_key_empty(self):
        from providers.payments.config import resolve_paytabs_server_key
        assert resolve_paytabs_server_key() == ""

    @patch.dict(os.environ, {"PAYTABS_WEBHOOK_SECRET": "wh_paytabs"}, clear=False)
    def test_resolve_paytabs_webhook_secret(self):
        from providers.payments.config import resolve_paytabs_webhook_secret
        assert resolve_paytabs_webhook_secret() == "wh_paytabs"

    @patch.dict(os.environ, {"PAYTABS_PROFILE_ID": "prof_42"}, clear=False)
    def test_resolve_paytabs_profile_id(self):
        from providers.payments.config import resolve_paytabs_profile_id
        assert resolve_paytabs_profile_id() == "prof_42"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_paytabs_api_base_url_default(self):
        from providers.payments.config import resolve_paytabs_api_base_url
        assert resolve_paytabs_api_base_url() == "https://secure.paytabs.com"

    @patch.dict(os.environ, {"PAYTABS_API_BASE_URL": "https://custom.paytabs.com/"}, clear=False)
    def test_resolve_paytabs_api_base_url_custom(self):
        from providers.payments.config import resolve_paytabs_api_base_url
        assert resolve_paytabs_api_base_url() == "https://custom.paytabs.com"

    @patch.dict(os.environ, {"PAYTABS_CALLBACK_URL": "https://callback.paytabs.com"}, clear=False)
    def test_resolve_paytabs_callback_url(self):
        from providers.payments.config import resolve_paytabs_callback_url
        assert resolve_paytabs_callback_url() == "https://callback.paytabs.com"

    @patch.dict(os.environ, {"PAYTABS_SERVER_KEY": "srv", "PAYTABS_PROFILE_ID": "prof"}, clear=False)
    def test_is_paytabs_configured_true(self):
        from providers.payments.config import is_paytabs_configured
        assert is_paytabs_configured() is True

    @patch.dict(os.environ, {"PAYTABS_SERVER_KEY": "srv"}, clear=False)
    def test_is_paytabs_configured_missing_profile(self):
        from providers.payments.config import is_paytabs_configured
        assert is_paytabs_configured() is False

    @patch.dict(os.environ, {}, clear=False)
    def test_is_paytabs_configured_empty(self):
        from providers.payments.config import is_paytabs_configured
        assert is_paytabs_configured() is False


# ===========================================================================
# config.py — Thawani config helpers
# ===========================================================================


class TestThawaniConfig:
    @patch.dict(os.environ, {"THAWANI_SECRET_KEY": "thawani_sk"}, clear=False)
    def test_resolve_thawani_secret_key(self):
        from providers.payments.config import resolve_thawani_secret_key
        assert resolve_thawani_secret_key() == "thawani_sk"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_thawani_secret_key_empty(self):
        from providers.payments.config import resolve_thawani_secret_key
        assert resolve_thawani_secret_key() == ""

    @patch.dict(os.environ, {"THAWANI_PUBLISHABLE_KEY": "thawani_pk"}, clear=False)
    def test_resolve_thawani_publishable_key(self):
        from providers.payments.config import resolve_thawani_publishable_key
        assert resolve_thawani_publishable_key() == "thawani_pk"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_thawani_api_base_url_default(self):
        from providers.payments.config import resolve_thawani_api_base_url
        assert resolve_thawani_api_base_url() == "https://uatcheckout.thawani.om/api/v1"

    @patch.dict(os.environ, {"THAWANI_API_BASE_URL": "https://custom.thawani.om/"}, clear=False)
    def test_resolve_thawani_api_base_url_custom(self):
        from providers.payments.config import resolve_thawani_api_base_url
        assert resolve_thawani_api_base_url() == "https://custom.thawani.om"

    @patch.dict(os.environ, {"THAWANI_WEBHOOK_SECRET": "wh_thawani"}, clear=False)
    def test_resolve_thawani_webhook_secret(self):
        from providers.payments.config import resolve_thawani_webhook_secret
        assert resolve_thawani_webhook_secret() == "wh_thawani"

    @patch.dict(os.environ, {"THAWANI_SECRET_KEY": "sk", "THAWANI_PUBLISHABLE_KEY": "pk"}, clear=False)
    def test_is_thawani_configured_true(self):
        from providers.payments.config import is_thawani_configured
        assert is_thawani_configured() is True

    @patch.dict(os.environ, {"THAWANI_SECRET_KEY": "sk"}, clear=False)
    def test_is_thawani_configured_missing_pk(self):
        from providers.payments.config import is_thawani_configured
        assert is_thawani_configured() is False

    @patch.dict(os.environ, {}, clear=False)
    def test_is_thawani_configured_empty(self):
        from providers.payments.config import is_thawani_configured
        assert is_thawani_configured() is False


# ===========================================================================
# config.py — PayPal config helpers
# ===========================================================================


class TestPayPalConfig:
    @patch.dict(os.environ, {
        "PAYPAL_CLIENT_ID": "client_123",
        "PAYPAL_SECRET": "secret_456",
        "PAYPAL_MODE": "live",
    }, clear=False)
    def test_resolve_paypal_credentials_live(self):
        from providers.payments.config import resolve_paypal_credentials
        client_id, secret, base_url = resolve_paypal_credentials()
        assert client_id == "client_123"
        assert secret == "secret_456"
        assert base_url == "https://api-m.paypal.com"

    @patch.dict(os.environ, {
        "PAYPAL_CLIENT_ID": "client_123",
        "PAYPAL_SECRET": "secret_456",
        "PAYPAL_MODE": "sandbox",
    }, clear=False)
    def test_resolve_paypal_credentials_sandbox(self):
        from providers.payments.config import resolve_paypal_credentials
        client_id, secret, base_url = resolve_paypal_credentials()
        assert base_url == "https://api-m.sandbox.paypal.com"

    @patch.dict(os.environ, {
        "PAYPAL_CLIENT_ID": "client_123",
        "PAYPAL_SECRET": "secret_456",
    }, clear=False)
    def test_resolve_paypal_credentials_default_mode(self):
        from providers.payments.config import resolve_paypal_credentials
        client_id, secret, base_url = resolve_paypal_credentials()
        assert base_url == "https://api-m.sandbox.paypal.com"

    @patch.dict(os.environ, {}, clear=False)
    def test_resolve_paypal_credentials_empty(self):
        from providers.payments.config import resolve_paypal_credentials
        client_id, secret, base_url = resolve_paypal_credentials()
        assert client_id is None
        assert secret is None

    @patch.dict(os.environ, {
        "PAYPAL_CLIENT_ID": "cid",
        "PAYPAL_SECRET": "sec",
    }, clear=False)
    def test_is_paypal_configured_true(self):
        from providers.payments.config import is_paypal_configured
        assert is_paypal_configured() is True

    @patch.dict(os.environ, {"PAYPAL_CLIENT_ID": "cid"}, clear=False)
    def test_is_paypal_configured_missing_secret(self):
        from providers.payments.config import is_paypal_configured
        assert is_paypal_configured() is False

    @patch.dict(os.environ, {}, clear=False)
    def test_is_paypal_configured_empty(self):
        from providers.payments.config import is_paypal_configured
        assert is_paypal_configured() is False


# ===========================================================================
# webhooks.py — _verify_paytabs_signature, _verify_tap_signature
# ===========================================================================


class TestVerifyPayTabsSignature:
    def _expected_sig(self, payload: bytes, secret: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def test_valid_signature(self):
        from providers.payments.webhooks import _verify_paytabs_signature
        payload = b'{"event": "payment"}'
        secret = "my_secret"
        sig = self._expected_sig(payload, secret)
        assert _verify_paytabs_signature(payload, sig, secret) is True

    def test_invalid_signature(self):
        from providers.payments.webhooks import _verify_paytabs_signature
        payload = b'{"event": "payment"}'
        assert _verify_paytabs_signature(payload, "bad_sig", "secret") is False

    def test_empty_secret(self):
        from providers.payments.webhooks import _verify_paytabs_signature
        assert _verify_paytabs_signature(b"body", "sig", "") is False

    def test_empty_signature(self):
        from providers.payments.webhooks import _verify_paytabs_signature
        assert _verify_paytabs_signature(b"body", "", "secret") is False

    def test_empty_payload_with_valid_sig(self):
        from providers.payments.webhooks import _verify_paytabs_signature
        sig = self._expected_sig(b"", "secret")
        assert _verify_paytabs_signature(b"", sig, "secret") is True


class TestVerifyTapSignature:
    def _expected_sig(self, payload: bytes, secret: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def test_valid_signature(self):
        from providers.payments.webhooks import _verify_tap_signature
        payload = b'{"event": "charge"}'
        secret = "tap_secret"
        sig = self._expected_sig(payload, secret)
        assert _verify_tap_signature(payload, sig, secret) is True

    def test_invalid_signature(self):
        from providers.payments.webhooks import _verify_tap_signature
        assert _verify_tap_signature(b"body", "wrong_sig", "secret") is False

    def test_empty_secret(self):
        from providers.payments.webhooks import _verify_tap_signature
        assert _verify_tap_signature(b"body", "sig", "") is False


# ===========================================================================
# generic.py — parse_generic_payload, fill_gateway_template, normalize_generic_status
# ===========================================================================


class TestParseGenericPayload:
    def test_json_body(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b'{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_non_json_body_parse_qs(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b"key=value&num=42")
        assert result == {"key": "value", "num": "42"}

    def test_empty_body(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b"")
        assert result == {}

    def test_non_dict_json(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b"[1, 2, 3]")
        assert result == {}

    def test_query_params_merged(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b'{"a": 1}', query_params={"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_query_params_no_override(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b'{"a": 1}', query_params={"a": 2})
        assert result["a"] == 1

    def test_invalid_body_returns_empty(self):
        from providers.payments.generic import parse_generic_payload
        result = parse_generic_payload(b"\xff\xfe\xfd\x00invalid")
        assert result == {}


class TestFillGatewayTemplate:
    def test_simple_substitution(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("Hello {name}", {"name": "World"})
        assert result == "Hello World"

    def test_multiple_substitutions(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("{greeting} {name}", {"greeting": "Hi", "name": "Alice"})
        assert result == "Hi Alice"

    def test_missing_key_replaced_empty(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("Hello {missing}", {})
        assert result == "Hello "

    def test_none_value_replaced_empty(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("Hello {name}", {"name": None})
        assert result == "Hello "

    def test_no_placeholders(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("No placeholders here", {"key": "val"})
        assert result == "No placeholders here"

    def test_numeric_value(self):
        from providers.payments.generic import fill_gateway_template
        result = fill_gateway_template("Amount: {amount}", {"amount": 42})
        assert result == "Amount: 42"


class TestNormalizeGenericStatus:
    def test_empty_status(self):
        from providers.payments.generic import normalize_generic_status
        assert normalize_generic_status("") == "unknown"

    def test_none_status(self):
        from providers.payments.generic import normalize_generic_status
        assert normalize_generic_status(None) == "unknown"

    def test_whitespace_status(self):
        from providers.payments.generic import normalize_generic_status
        assert normalize_generic_status("   ") == "unknown"

    def test_success_match(self):
        from providers.payments.generic import normalize_generic_status
        result = normalize_generic_status(
            "CAPTURED",
            success_values=["captured", "success"],
        )
        assert result == "success"

    def test_failure_match(self):
        from providers.payments.generic import normalize_generic_status
        result = normalize_generic_status(
            "DECLINED",
            failure_values=["declined", "failed"],
        )
        assert result == "failed"

    def test_no_match_returns_normalized(self):
        from providers.payments.generic import normalize_generic_status
        result = normalize_generic_status("PENDING")
        assert result == "pending"

    def test_case_insensitive_success(self):
        from providers.payments.generic import normalize_generic_status
        result = normalize_generic_status(
            "Success",
            success_values=["success"],
        )
        assert result == "success"

    def test_whitespace_trimmed(self):
        from providers.payments.generic import normalize_generic_status
        result = normalize_generic_status("  captured  ", success_values=["captured"])
        assert result == "success"


# ===========================================================================
# stripe_sdk.py — HAS_STRIPE, stripe
# ===========================================================================


class TestStripeSdk:
    def test_has_stripe_is_bool(self):
        from providers.payments.stripe_sdk import HAS_STRIPE
        assert isinstance(HAS_STRIPE, bool)

    def test_stripe_is_available_or_none(self):
        from providers.payments.stripe_sdk import stripe, HAS_STRIPE
        if HAS_STRIPE:
            assert stripe is not None
        else:
            assert stripe is None


# ===========================================================================
# connect.py — configure_stripe_connect, create/modify account, transfer
# ===========================================================================


class TestConfigureStripeConnect:
    @patch("providers.payments.connect.stripe")
    def test_configure_with_key(self, mock_stripe):
        from providers.payments.connect import configure_stripe_connect
        configure_stripe_connect(api_key="sk_test_123")
        mock_stripe.api_key = "sk_test_123"

    @patch("providers.payments.connect.stripe")
    def test_configure_with_version(self, mock_stripe):
        from providers.payments.connect import configure_stripe_connect
        configure_stripe_connect(api_key="sk_test_123", api_version="2024-01-01")
        mock_stripe.api_version = "2024-01-01"

    @patch("providers.payments.connect.stripe")
    def test_configure_without_version(self, mock_stripe):
        from providers.payments.connect import configure_stripe_connect
        configure_stripe_connect(api_key="sk_test_123")
        mock_stripe.api_key = "sk_test_123"

    def test_configure_empty_key_raises(self):
        from providers.payments.connect import configure_stripe_connect
        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY must be configured"):
            configure_stripe_connect(api_key="")

    def test_configure_none_key_raises(self):
        from providers.payments.connect import configure_stripe_connect
        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY must be configured"):
            configure_stripe_connect(api_key=None)

    def test_configure_whitespace_key_raises(self):
        from providers.payments.connect import configure_stripe_connect
        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY must be configured"):
            configure_stripe_connect(api_key="   ")


class TestCreateConnectAccount:
    @patch("providers.payments.connect.stripe")
    def test_create_account(self, mock_stripe):
        from providers.payments.connect import create_connect_account
        mock_stripe.Account.create.return_value = {"id": "acct_123"}
        result = create_connect_account(type="standard")
        mock_stripe.Account.create.assert_called_once_with(type="standard")
        assert result == {"id": "acct_123"}


class TestModifyConnectAccount:
    @patch("providers.payments.connect.stripe")
    def test_modify_account(self, mock_stripe):
        from providers.payments.connect import modify_connect_account
        mock_stripe.Account.modify.return_value = {"id": "acct_123"}
        result = modify_connect_account("acct_123", business_type="company")
        mock_stripe.Account.modify.assert_called_once_with("acct_123", business_type="company")
        assert result == {"id": "acct_123"}


class TestCreateConnectTransfer:
    @patch("providers.payments.connect.stripe")
    def test_create_transfer(self, mock_stripe):
        from providers.payments.connect import create_connect_transfer
        mock_stripe.Transfer.create.return_value = {"id": "tr_123"}
        result = create_connect_transfer(amount=1000, currency="usd", destination="acct_123")
        mock_stripe.Transfer.create.assert_called_once_with(
            amount=1000, currency="usd", destination="acct_123"
        )
        assert result == {"id": "tr_123"}


# ===========================================================================
# paypal.py — PayPal provider
# ===========================================================================


class TestPayPalExceptions:
    def test_paypal_error_is_exception(self):
        from providers.payments.paypal import PayPalError
        assert issubclass(PayPalError, Exception)

    def test_order_not_found_error(self):
        from providers.payments.paypal import PayPalOrderNotFoundError, PayPalError
        assert issubclass(PayPalOrderNotFoundError, PayPalError)

    def test_capture_error(self):
        from providers.payments.paypal import PayPalCaptureError, PayPalError
        assert issubclass(PayPalCaptureError, PayPalError)

    def test_refund_error(self):
        from providers.payments.paypal import PayPalRefundError, PayPalError
        assert issubclass(PayPalRefundError, PayPalError)

    def test_void_error(self):
        from providers.payments.paypal import PayPalVoidError, PayPalError
        assert issubclass(PayPalVoidError, PayPalError)

    def test_configuration_error(self):
        from providers.payments.paypal import PayPalConfigurationError, PayPalError
        assert issubclass(PayPalConfigurationError, PayPalError)


class TestPayPalHasFlag:
    def test_has_paypal_is_bool(self):
        from providers.payments.paypal import HAS_PAYPAL
        assert isinstance(HAS_PAYPAL, bool)


class TestPayPalIsAvailable:
    @patch("providers.payments.paypal.is_paypal_configured")
    def test_available_when_configured(self, mock_configured):
        from providers.payments.paypal import is_available, HAS_PAYPAL
        mock_configured.return_value = True
        if HAS_PAYPAL:
            assert is_available() is True
        else:
            assert is_available() is False

    @patch("providers.payments.paypal.is_paypal_configured")
    def test_not_available_when_unconfigured(self, mock_configured):
        from providers.payments.paypal import is_available
        mock_configured.return_value = False
        assert is_available() is False


class TestPayPalGetSdk:
    @patch("providers.payments.paypal.HAS_PAYPAL", True)
    @patch("providers.payments.paypal._paypal_sdk", MagicMock())
    def test_get_sdk_success(self):
        from providers.payments.paypal import _get_sdk, _paypal_sdk
        result = _get_sdk()
        assert result is _paypal_sdk

    @patch("providers.payments.paypal.HAS_PAYPAL", False)
    @patch("providers.payments.paypal._paypal_sdk", None)
    def test_get_sdk_not_installed(self):
        from providers.payments.paypal import _get_sdk, PayPalConfigurationError
        with pytest.raises(PayPalConfigurationError, match="PayPal SDK is not installed"):
            _get_sdk()


# ===========================================================================
# paytabs.py — PayTabs provider
# ===========================================================================


class TestPayTabsExceptions:
    def test_base_error(self):
        from providers.payments.paytabs import PayTabsError
        assert issubclass(PayTabsError, Exception)

    def test_payment_not_found_error(self):
        from providers.payments.paytabs import PayTabsPaymentNotFoundError, PayTabsError
        assert issubclass(PayTabsPaymentNotFoundError, PayTabsError)

    def test_refund_error(self):
        from providers.payments.paytabs import PayTabsRefundError, PayTabsError
        assert issubclass(PayTabsRefundError, PayTabsError)

    def test_configuration_error(self):
        from providers.payments.paytabs import PayTabsConfigurationError, PayTabsError
        assert issubclass(PayTabsConfigurationError, PayTabsError)


class TestPayTabsIsAvailable:
    @patch("providers.payments.paytabs.is_paytabs_configured")
    def test_available(self, mock_configured):
        from providers.payments.paytabs import is_available
        mock_configured.return_value = True
        assert is_available() is True

    @patch("providers.payments.paytabs.is_paytabs_configured")
    def test_not_available(self, mock_configured):
        from providers.payments.paytabs import is_available
        mock_configured.return_value = False
        assert is_available() is False


class TestPayTabsGetHeaders:
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_headers_with_valid_key(self, mock_key):
        from providers.payments.paytabs import _get_headers
        mock_key.return_value = "server_key_123"
        headers = _get_headers()
        assert headers["Authorization"] == "server_key_123"
        assert headers["Content-Type"] == "application/json"

    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_headers_missing_key_raises(self, mock_key):
        from providers.payments.paytabs import _get_headers, PayTabsConfigurationError
        mock_key.return_value = ""
        with pytest.raises(PayTabsConfigurationError, match="PAYTABS_SERVER_KEY must be set"):
            _get_headers()


class TestPayTabsCreatePaymentPage:
    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_callback_url")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_create_page_success(
        self, mock_key, mock_cb, mock_profile, mock_base, mock_post
    ):
        from providers.payments.paytabs import create_payment_page
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_cb.return_value = "https://cb.example.com"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "payment_url": "https://pay.example.com",
            "tran_ref": "txn_42",
        }
        mock_post.return_value = mock_response

        result = create_payment_page(
            Decimal("99.99"), "USD",
            customer_name="John Doe",
            customer_email="john@example.com",
        )
        assert result["payment_url"] == "https://pay.example.com"
        assert result["transaction_id"] == "txn_42"

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_callback_url")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_create_page_request_exception(
        self, mock_key, mock_cb, mock_profile, mock_base, mock_post
    ):
        import requests
        from providers.payments.paytabs import create_payment_page, PayTabsError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_cb.return_value = "https://cb.example.com"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_post.side_effect = requests.RequestException("timeout")

        with pytest.raises(PayTabsError, match="API request failed"):
            create_payment_page(
                Decimal("10.00"), "USD",
                customer_name="John",
                customer_email="j@x.com",
            )

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_callback_url")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_create_page_non_200_status(
        self, mock_key, mock_cb, mock_profile, mock_base, mock_post
    ):
        from providers.payments.paytabs import create_payment_page, PayTabsError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_cb.return_value = "https://cb.example.com"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(PayTabsError, match="status 500"):
            create_payment_page(
                Decimal("10.00"), "USD",
                customer_name="John",
                customer_email="j@x.com",
            )

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_callback_url")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_create_page_unexpected_response(
        self, mock_key, mock_cb, mock_profile, mock_base, mock_post
    ):
        from providers.payments.paytabs import create_payment_page, PayTabsError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_cb.return_value = "https://cb.example.com"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "data"}
        mock_post.return_value = mock_response

        with pytest.raises(PayTabsError, match="unexpected response"):
            create_payment_page(
                Decimal("10.00"), "USD",
                customer_name="John",
                customer_email="j@x.com",
            )


class TestPayTabsGetPaymentStatus:
    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_get_status_success(self, mock_key, mock_profile, mock_base, mock_post):
        from providers.payments.paytabs import get_payment_status
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tran_ref": "txn_42",
            "payment_result": {"response_status": "A"},
            "cart_amount": "99.99",
            "cart_currency": "USD",
        }
        mock_post.return_value = mock_response

        result = get_payment_status("txn_42")
        assert result["transaction_id"] == "txn_42"
        assert result["status"] == "A"

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_get_status_not_found(self, mock_key, mock_profile, mock_base, mock_post):
        from providers.payments.paytabs import get_payment_status, PayTabsPaymentNotFoundError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 404, "message": "Transaction not found"}
        mock_post.return_value = mock_response

        with pytest.raises(PayTabsPaymentNotFoundError):
            get_payment_status("txn_missing")


class TestPayTabsRefund:
    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_refund_success(self, mock_key, mock_profile, mock_base, mock_post):
        from providers.payments.paytabs import refund
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tran_ref": "ref_1",
            "payment_result": {"response_status": "R"},
            "cart_amount": "50.00",
        }
        mock_post.return_value = mock_response

        result = refund("txn_42", amount=Decimal("50.00"), currency="USD")
        assert result["refund_id"] == "ref_1"

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_refund_not_found(self, mock_key, mock_profile, mock_base, mock_post):
        from providers.payments.paytabs import refund, PayTabsPaymentNotFoundError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 404, "message": "Transaction not found"}
        mock_post.return_value = mock_response

        with pytest.raises(PayTabsPaymentNotFoundError):
            refund("txn_missing")

    @patch("providers.payments.paytabs.requests.post")
    @patch("providers.payments.paytabs.resolve_paytabs_api_base_url")
    @patch("providers.payments.paytabs.resolve_paytabs_profile_id")
    @patch("providers.payments.paytabs.resolve_paytabs_server_key")
    def test_refund_request_exception(self, mock_key, mock_profile, mock_base, mock_post):
        import requests
        from providers.payments.paytabs import refund, PayTabsRefundError
        mock_key.return_value = "srv_key"
        mock_profile.return_value = "prof_1"
        mock_base.return_value = "https://secure.paytabs.com"
        mock_post.side_effect = requests.RequestException("timeout")

        with pytest.raises(PayTabsRefundError, match="API request failed"):
            refund("txn_42")


class TestPayTabsVerifyWebhook:
    @patch("providers.payments.paytabs._verify_paytabs_signature")
    def test_verify_webhook_delegates(self, mock_verify):
        from providers.payments.paytabs import verify_webhook
        mock_verify.return_value = True
        result = verify_webhook(b"body", "sig", "secret")
        assert result is True
        mock_verify.assert_called_once_with(b"body", "sig", "secret")


# ===========================================================================
# tap.py — Tap provider
# ===========================================================================


class TestTapExceptions:
    def test_base_error(self):
        from providers.payments.tap import TapError
        assert issubclass(TapError, Exception)

    def test_charge_not_found_error(self):
        from providers.payments.tap import TapChargeNotFoundError, TapError
        assert issubclass(TapChargeNotFoundError, TapError)

    def test_refund_error(self):
        from providers.payments.tap import TapRefundError, TapError
        assert issubclass(TapRefundError, TapError)

    def test_configuration_error(self):
        from providers.payments.tap import TapConfigurationError, TapError
        assert issubclass(TapConfigurationError, TapError)


class TestTapIsAvailable:
    @patch("providers.payments.tap.is_tap_configured")
    def test_available(self, mock_configured):
        from providers.payments.tap import is_available
        mock_configured.return_value = True
        assert is_available() is True

    @patch("providers.payments.tap.is_tap_configured")
    def test_not_available(self, mock_configured):
        from providers.payments.tap import is_available
        mock_configured.return_value = False
        assert is_available() is False


class TestTapGetHeaders:
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_headers_with_valid_key(self, mock_key):
        from providers.payments.tap import _get_headers
        mock_key.return_value = "sk_tap_123"
        headers = _get_headers()
        assert headers["Authorization"] == "Bearer sk_tap_123"
        assert headers["Content-Type"] == "application/json"

    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_headers_missing_key_raises(self, mock_key):
        from providers.payments.tap import _get_headers, TapConfigurationError
        mock_key.return_value = ""
        with pytest.raises(TapConfigurationError, match="TAP_SECRET_KEY must be set"):
            _get_headers()


class TestTapCreateCharge:
    @patch("providers.payments.tap.requests.post")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_create_charge_success(self, mock_key, mock_base, mock_post):
        from providers.payments.tap import create_charge
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chg_123",
            "transaction": {"id": "txn_456", "url": "https://tap.pay/xyz"},
            "status": "INITIATED",
            "amount": "10.000",
            "currency": "KWD",
        }
        mock_post.return_value = mock_response

        result = create_charge(
            Decimal("10.000"), "KWD",
            customer_name="Ahmed Ali",
            customer_email="ahmed@example.com",
        )
        assert result["id"] == "chg_123"
        assert result["payment_url"] == "https://tap.pay/xyz"

    @patch("providers.payments.tap.requests.post")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_create_charge_request_exception(self, mock_key, mock_base, mock_post):
        import requests
        from providers.payments.tap import create_charge, TapError
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_post.side_effect = requests.RequestException("timeout")

        with pytest.raises(TapError, match="API request failed"):
            create_charge(Decimal("10"), "KWD", customer_name="Test")

    @patch("providers.payments.tap.requests.post")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_create_charge_non_200(self, mock_key, mock_base, mock_post):
        from providers.payments.tap import create_charge, TapError
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable"
        mock_post.return_value = mock_response

        with pytest.raises(TapError, match="status 422"):
            create_charge(Decimal("10"), "KWD", customer_name="Test")


class TestTapGetCharge:
    @patch("providers.payments.tap.requests.get")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_get_charge_success(self, mock_key, mock_base, mock_post):
        from providers.payments.tap import get_charge
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chg_123",
            "status": "CAPTURED",
            "amount": "10.000",
            "currency": "KWD",
        }
        mock_post.return_value = mock_response

        result = get_charge("chg_123")
        assert result["id"] == "chg_123"
        assert result["status"] == "CAPTURED"

    @patch("providers.payments.tap.requests.get")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_get_charge_not_found(self, mock_key, mock_base, mock_get):
        from providers.payments.tap import get_charge, TapChargeNotFoundError
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(TapChargeNotFoundError):
            get_charge("chg_missing")


class TestTapRefundCharge:
    @patch("providers.payments.tap.requests.post")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_refund_success(self, mock_key, mock_base, mock_post):
        from providers.payments.tap import refund_charge
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "ref_1",
            "status": "REFUNDED",
            "amount": "5.000",
        }
        mock_post.return_value = mock_response

        result = refund_charge("chg_123", amount=Decimal("5.000"))
        assert result["id"] == "ref_1"

    @patch("providers.payments.tap.requests.post")
    @patch("providers.payments.tap.resolve_tap_api_base_url")
    @patch("providers.payments.tap.resolve_tap_secret_key")
    def test_refund_not_found(self, mock_key, mock_base, mock_post):
        from providers.payments.tap import refund_charge, TapChargeNotFoundError
        mock_key.return_value = "sk_tap"
        mock_base.return_value = "https://api.tap.company"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(TapChargeNotFoundError):
            refund_charge("chg_missing")


class TestTapVerifyWebhook:
    @patch("providers.payments.tap._verify_tap_signature")
    def test_verify_webhook_delegates(self, mock_verify):
        from providers.payments.tap import verify_webhook
        mock_verify.return_value = True
        result = verify_webhook(b"body", "hash_val", "secret")
        assert result is True
        mock_verify.assert_called_once_with(b"body", "hash_val", "secret")


# ===========================================================================
# thawani.py — Thawani provider
# ===========================================================================


class TestThawaniExceptions:
    def test_base_error(self):
        from providers.payments.thawani import ThawaniError
        assert issubclass(ThawaniError, Exception)

    def test_session_not_found_error(self):
        from providers.payments.thawani import ThawaniSessionNotFoundError, ThawaniError
        assert issubclass(ThawaniSessionNotFoundError, ThawaniError)

    def test_refund_error(self):
        from providers.payments.thawani import ThawaniRefundError, ThawaniError
        assert issubclass(ThawaniRefundError, ThawaniError)

    def test_configuration_error(self):
        from providers.payments.thawani import ThawaniConfigurationError, ThawaniError
        assert issubclass(ThawaniConfigurationError, ThawaniError)


class TestThawaniIsAvailable:
    @patch("providers.payments.thawani.is_thawani_configured")
    def test_available(self, mock_configured):
        from providers.payments.thawani import is_available
        mock_configured.return_value = True
        assert is_available() is True

    @patch("providers.payments.thawani.is_thawani_configured")
    def test_not_available(self, mock_configured):
        from providers.payments.thawani import is_available
        mock_configured.return_value = False
        assert is_available() is False


class TestThawaniGetHeaders:
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_headers_with_valid_key(self, mock_key):
        from providers.payments.thawani import _get_headers
        mock_key.return_value = "thawani_sk_123"
        headers = _get_headers()
        assert headers["Thawani-Api-Key"] == "thawani_sk_123"
        assert headers["Content-Type"] == "application/json"

    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_headers_missing_key_raises(self, mock_key):
        from providers.payments.thawani import _get_headers, ThawaniConfigurationError
        mock_key.return_value = ""
        with pytest.raises(ThawaniConfigurationError, match="THAWANI_SECRET_KEY must be set"):
            _get_headers()


class TestThawaniCreateSession:
    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_publishable_key")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_create_session_success(
        self, mock_key, mock_pk, mock_base, mock_post
    ):
        from providers.payments.thawani import create_session
        mock_key.return_value = "thawani_sk"
        mock_pk.return_value = "thawani_pk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"session_id": "sess_123"},
            "status": 200,
        }
        mock_post.return_value = mock_response

        result = create_session(Decimal("10.000"), "OMR", order_id="order_42")
        assert result["session_id"] == "sess_123"
        assert "sess_123" in result["checkout_url"]
        assert "thawani_pk" in result["checkout_url"]

    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_publishable_key")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_create_session_no_publishable_key(
        self, mock_key, mock_pk, mock_base, mock_post
    ):
        from providers.payments.thawani import create_session
        mock_key.return_value = "thawani_sk"
        mock_pk.return_value = ""
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"session_id": "sess_123"},
            "status": 200,
        }
        mock_post.return_value = mock_response

        result = create_session(Decimal("10.000"), "OMR")
        assert result["checkout_url"] == ""

    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_publishable_key")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_create_session_request_exception(
        self, mock_key, mock_pk, mock_base, mock_post
    ):
        import requests
        from providers.payments.thawani import create_session, ThawaniError
        mock_key.return_value = "thawani_sk"
        mock_pk.return_value = "pk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_post.side_effect = requests.RequestException("timeout")

        with pytest.raises(ThawaniError, match="API request failed"):
            create_session(Decimal("10.000"), "OMR")

    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_publishable_key")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_create_session_non_200(
        self, mock_key, mock_pk, mock_base, mock_post
    ):
        from providers.payments.thawani import create_session, ThawaniError
        mock_key.return_value = "thawani_sk"
        mock_pk.return_value = "pk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(ThawaniError, match="status 500"):
            create_session(Decimal("10.000"), "OMR")


class TestThawaniGetSession:
    @patch("providers.payments.thawani.requests.get")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_get_session_success(self, mock_key, mock_base, mock_get):
        from providers.payments.thawani import get_session
        mock_key.return_value = "thawani_sk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "payment_status": "paid",
                "total_amount": "10.000",
                "currency": "OMR",
                "customer_key": "cus_1",
            },
        }
        mock_get.return_value = mock_response

        result = get_session("sess_123")
        assert result["session_id"] == "sess_123"
        assert result["status"] == "paid"

    @patch("providers.payments.thawani.requests.get")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_get_session_not_found(self, mock_key, mock_base, mock_get):
        from providers.payments.thawani import get_session, ThawaniSessionNotFoundError
        mock_key.return_value = "thawani_sk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ThawaniSessionNotFoundError):
            get_session("sess_missing")


class TestThawaniRefundSession:
    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_refund_success(self, mock_key, mock_base, mock_post):
        from providers.payments.thawani import refund_session
        mock_key.return_value = "thawani_sk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"refund_id": "ref_1"},
            "status": 200,
        }
        mock_post.return_value = mock_response

        result = refund_session("sess_123", reason="Customer request")
        assert result["refund_id"] == "ref_1"

    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_refund_not_found(self, mock_key, mock_base, mock_post):
        from providers.payments.thawani import refund_session, ThawaniSessionNotFoundError
        mock_key.return_value = "thawani_sk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(ThawaniSessionNotFoundError):
            refund_session("sess_missing")

    @patch("providers.payments.thawani.requests.post")
    @patch("providers.payments.thawani.resolve_thawani_api_base_url")
    @patch("providers.payments.thawani.resolve_thawani_secret_key")
    def test_refund_request_exception(self, mock_key, mock_base, mock_post):
        import requests
        from providers.payments.thawani import refund_session, ThawaniRefundError
        mock_key.return_value = "thawani_sk"
        mock_base.return_value = "https://uatcheckout.thawani.om/api/v1"
        mock_post.side_effect = requests.RequestException("timeout")

        with pytest.raises(ThawaniRefundError, match="API request failed"):
            refund_session("sess_123")


class TestThawaniVerifyWebhook:
    def _expected_sig(self, payload: bytes, secret: str) -> str:
        return hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

    def test_valid_signature(self):
        from providers.payments.thawani import verify_webhook
        payload = b'{"event": "payment"}'
        secret = "thawani_wh"
        sig = self._expected_sig(payload, secret)
        assert verify_webhook(payload, sig, secret) is True

    def test_invalid_signature(self):
        from providers.payments.thawani import verify_webhook
        assert verify_webhook(b"body", "wrong_sig", "secret") is False

    def test_empty_secret(self):
        from providers.payments.thawani import verify_webhook
        assert verify_webhook(b"body", "sig", "") is False

    def test_empty_signature(self):
        from providers.payments.thawani import verify_webhook
        assert verify_webhook(b"body", "", "secret") is False


# ===========================================================================
# __init__.py — Package exports
# ===========================================================================


class TestPackageInit:
    def test_config_exports(self):
        from providers.payments import config
        assert hasattr(config, "__all__")
        assert "resolve_stripe_secret_key" in config.__all__
        assert "is_stripe_configured" in config.__all__

    def test_webhooks_exports(self):
        from providers.payments import webhooks
        assert hasattr(webhooks, "__all__")
        assert "_verify_paytabs_signature" in webhooks.__all__
        assert "_verify_tap_signature" in webhooks.__all__

    def test_generic_exports(self):
        from providers.payments import generic
        assert hasattr(generic, "__all__")
        assert "parse_generic_payload" in generic.__all__
        assert "fill_gateway_template" in generic.__all__
        assert "normalize_generic_status" in generic.__all__

    def test_connect_exports(self):
        from providers.payments import connect
        assert hasattr(connect, "__all__")
        assert "configure_stripe_connect" in connect.__all__
        assert "create_connect_account" in connect.__all__
        assert "modify_connect_account" in connect.__all__
        assert "create_connect_transfer" in connect.__all__

    def test_all_combines_submodule_exports(self):
        import providers.payments as pkg
        assert hasattr(pkg, "__all__")
        assert len(pkg.__all__) > 0


# ===========================================================================
# base.py — Operation constants
# ===========================================================================


class TestOperationConstants:
    def test_operation_create(self):
        from providers.payments.base import OPERATION_CREATE
        assert OPERATION_CREATE == "create"

    def test_operation_confirm(self):
        from providers.payments.base import OPERATION_CONFIRM
        assert OPERATION_CONFIRM == "confirm"

    def test_operation_webhook(self):
        from providers.payments.base import OPERATION_WEBHOOK
        assert OPERATION_WEBHOOK == "webhook"
