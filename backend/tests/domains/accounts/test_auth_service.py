"""Paired test for FILE-60: PII logging in auth_service.py (OBS-010, CR-04).

Observability/Resilience findings:
- OBS-010: auth_service.py logs phone/email PII via %s formatting
- CR-04: Raw phone/email logged via %s formatting at multiple lines

Fix: Switch from %s positional formatting to structured kwargs so the
structlog PII scrubber can inspect keys and redact values.
"""
from __future__ import annotations

from pathlib import Path

import pytest


SRC_FILE = Path(__file__).resolve().parent.parent.parent.parent / "domains" / "accounts" / "services" / "auth" / "auth_service.py"


def test_no_pii_phone_in_otp_log_formatting():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("OTP generated for %s' not in src
    assert 'logger.info("otp_generated"' in src


def test_no_pii_email_in_sso_log_formatting():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("Auto-provisioned SSO user: %s' not in src
    assert 'logger.info("sso_user_auto_provisioned"' in src


def test_no_pii_destination_in_otp_delivery_log_formatting():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("OTP(email) user=%s destination=%s"' not in src
    assert 'logger.info("OTP(sms) user=%s destination=%s"' not in src
    assert 'logger.info("otp_delivery"' in src


def test_no_pii_identifier_in_verification_email_log_formatting():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.error("Failed to resend verification email for %s: %s"' not in src
    assert 'logger.error("verification_email_resend_failed"' in src


def test_otp_generated_uses_structured_kwargs():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("otp_generated", phone=phone, expires_in=OTP_EXPIRY_SECONDS)' in src


def test_sso_auto_provisioned_uses_structured_kwargs():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("sso_user_auto_provisioned", email=email, employee_id=employee.id)' in src


def test_otp_delivery_uses_structured_kwargs():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.info("otp_delivery", channel="email", user_id=user.id, email=dest)' in src
    assert 'logger.info("otp_delivery", channel="sms", user_id=user.id, phone=dest)' in src


def test_verification_email_resend_uses_structured_kwargs():
    src = SRC_FILE.read_text(encoding="utf-8")
    assert 'logger.error("verification_email_resend_failed", identifier=identifier, error=str(exc))' in src
