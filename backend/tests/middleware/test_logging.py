"""Tests for PII redaction in the logging middleware."""
from __future__ import annotations

import importlib

import pytest


def _import_middleware():
    return importlib.import_module("middleware.logging_middleware")


class TestPIIRedaction:
    """Test PII redaction rules in logging middleware."""

    def test_redact_pii_redacts_password_field(self):
        middleware = _import_middleware()
        data = {"username": "john", "password": "secret123"}
        result = middleware.redact_pii(data)
        assert result["password"] == "<redacted>"
        assert result["username"] == "john"

    def test_redact_pii_redacts_email_field(self):
        middleware = _import_middleware()
        data = {"email": "user@example.com", "username": "john"}
        result = middleware.redact_pii(data)
        assert result["email"] == "<redacted>"
        assert result["username"] == "john"

    def test_redact_pii_redacts_phone_field(self):
        middleware = _import_middleware()
        data = {"phone": "+971-500-1234", "name": "john"}
        result = middleware.redact_pii(data)
        assert result["phone"] == "<redacted>"
        assert result["name"] == "john"

    def test_redact_pii_redacts_address_fields(self):
        middleware = _import_middleware()
        data = {"address": "123 Main St", "city": "Dubai", "country": "AE"}
        result = middleware.redact_pii(data)
        assert result["address"] == "<redacted>"
        assert result["city"] == "<redacted>"
        assert result["country"] == "<redacted>"

    def test_redact_pii_redacts_token_fields(self):
        middleware = _import_middleware()
        data = {"access_token": "abc123", "refresh_token": "xyz789", "role": "customer"}
        result = middleware.redact_pii(data)
        assert result["access_token"] == "<redacted>"
        assert result["refresh_token"] == "<redacted>"
        assert result["role"] == "customer"

    def test_redact_pii_redacts_authorization_header_value(self):
        middleware = _import_middleware()
        data = {"Authorization": "Bearer abc123xyz"}
        result = middleware.redact_pii(data)
        assert result["Authorization"] == "<redacted>"

    def test_redact_pii_redacts_card_fields(self):
        middleware = _import_middleware()
        data = {"card_number": "4111111111111111", "cvv": "123", "amount": 100}
        result = middleware.redact_pii(data)
        assert result["card_number"] == "<redacted>"
        assert result["cvv"] == "<redacted>"
        assert result["amount"] == 100

    def test_redact_pii_redacts_bank_fields(self):
        middleware = _import_middleware()
        data = {"bank_account": "1234567890", "iban": "AE07 0331 2345 6789", "currency": "AED"}
        result = middleware.redact_pii(data)
        assert result["bank_account"] == "<redacted>"
        assert result["iban"] == "<redacted>"
        assert result["currency"] == "AED"

    def test_redact_pii_redacts_nested_dict(self):
        middleware = _import_middleware()
        data = {"user": {"email": "test@example.com", "name": "John"}}
        result = middleware.redact_pii(data)
        assert result["user"]["email"] == "<redacted>"
        assert result["user"]["name"] == "John"

    def test_redact_pii_redacts_list_of_dicts(self):
        middleware = _import_middleware()
        data = [{"email": "a@b.com"}, {"password": "secret"}]
        result = middleware.redact_pii(data)
        assert result[0]["email"] == "<redacted>"
        assert result[1]["password"] == "<redacted>"

    def test_redact_pii_redacts_email_in_string(self):
        middleware = _import_middleware()
        result = middleware.redact_pii("Contact me at user@example.com for help")
        assert "user@example.com" not in result
        assert "<redacted>" in result

    def test_redact_pii_redacts_long_numbers_in_string(self):
        middleware = _import_middleware()
        result = middleware.redact_pii("Card 4111111111111111 was used")
        assert "4111111111111111" not in result
        assert "<redacted>" in result

    def test_redact_pii_redacts_bearer_token_in_string(self):
        middleware = _import_middleware()
        result = middleware.redact_pii("Authorization: Bearer abc123xyz")
        assert "abc123xyz" not in result
        assert "<redacted>" in result

    def test_redact_pii_preserves_non_pii_string(self):
        middleware = _import_middleware()
        result = middleware.redact_pii("Hello world, this is a test")
        assert result == "Hello world, this is a test"

    def test_redact_pii_handles_none(self):
        middleware = _import_middleware()
        result = middleware.redact_pii(None)
        assert result is None

    def test_redact_pii_handles_int(self):
        middleware = _import_middleware()
        result = middleware.redact_pii(42)
        assert result == 42

    def test_redact_pii_case_insensitive_field_names(self):
        middleware = _import_middleware()
        data = {"EMAIL": "test@example.com", "Password": "secret", "Role": "admin"}
        result = middleware.redact_pii(data)
        assert result["EMAIL"] == "<redacted>"
        assert result["Password"] == "<redacted>"
        assert result["Role"] == "admin"

    def test_redact_pii_custom_sensitive_fields(self):
        middleware = _import_middleware()
        data = {"custom_secret": "value", "normal_field": "safe"}
        result = middleware.redact_pii(data, sensitive_fields=("custom_secret",))
        assert result["custom_secret"] == "<redacted>"
        assert result["normal_field"] == "safe"

    def test_pii_field_patterns_exist(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "PII_FIELD_PATTERNS")
        assert len(middleware.PII_FIELD_PATTERNS) > 0

    def test_pii_value_patterns_exist(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "PII_VALUE_PATTERNS")
        assert len(middleware.PII_VALUE_PATTERNS) > 0

    def test_redaction_placeholder_constant_exists(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "REDACTION_PLACEHOLDER")
        assert middleware.REDACTION_PLACEHOLDER == "<redacted>"


class TestLoggingMiddlewareBehavior:
    """Ensure existing logging middleware behavior is unchanged."""

    def test_middleware_imports_successfully(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "RequestLoggingMiddleware")

    def test_middleware_has_required_context_vars(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "request_id_ctx")
        assert hasattr(middleware, "user_id_ctx")
        assert hasattr(middleware, "country_code_ctx")
        assert hasattr(middleware, "db_query_time_ctx")

    def test_middleware_has_prometheus_metrics(self):
        middleware = _import_middleware()
        assert hasattr(middleware, "http_request_duration_seconds")
        assert hasattr(middleware, "http_requests_total")
