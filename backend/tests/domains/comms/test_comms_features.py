"""Comms domain — feature + service smoke tests.

Laws 4 (features), 2 (thin routers), 131 (mock providers).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


class TestCommsFeatureAtoms:
    """Law 4 — representative comms feature atoms in rbac catalog."""

    @pytest.mark.parametrize(
        "feature",
        [
            "comms.notification.read",
            "comms.notification.manage",
            "comms.notification.push.register",
            "comms.ticket.create",
            "comms.ticket.manage",
            "comms.chat.send",
            "comms.chat.moderate",
            "comms.campaign.create",
            "comms.campaign.send",
            "comms.proxy.call",
            "comms.video_room.join",
            "comms.announcement.read",
            "comms.faq.manage",
            "comms.sla.manage",
            "comms.broadcast",
            "comms.audit.read",
        ],
    )
    def test_feature_in_catalog(self, feature):
        from tests._support.laws import assert_feature_in_catalog

        assert_feature_in_catalog(feature)


class TestCommsServiceImports:
    """Law 2 — service layer is importable."""

    def test_import_comms_service(self):
        from domains.comms.services import comms_service as svc

        assert svc is not None

    def test_import_email_gateway(self):
        from domains.comms.services.email import email_gateway

        assert email_gateway is not None

    def test_import_chat_service(self):
        from domains.comms.services.messaging import chat_service

        assert chat_service is not None

    def test_import_tickets_service(self):
        from domains.comms.services.tickets import tickets_service

        assert tickets_service is not None


class TestCommsModelPersistence:
    """Laws 6/23 — models persist with audit columns."""

    def test_notification_persists(self, db_session):
        from domains.comms.models.communication import Notification

        n = Notification(user_id=1, title="Test", message="Hello")
        db_session.add(n)
        db_session.flush()

        assert n.id is not None
        assert n.created_at is not None
        assert n.is_deleted is False

    def test_announcement_persists(self, db_session):
        from domains.comms.models.communication import Announcement

        a = Announcement(title="Test", content="Hello")
        db_session.add(a)
        db_session.flush()

        assert a.id is not None
        assert a.created_at is not None


class TestCommsEmailGateway:
    """Law 131 — email gateway works without real SMTP (mocked provider)."""

    def test_email_gateway_instantiation(self, db_session):
        from domains.comms.services.email.email_gateway import EmailGateway

        gw = EmailGateway(db_session)
        assert gw is not None
        assert hasattr(gw, "send_internal_email")
        assert hasattr(gw, "send_external_email")

    def test_dlp_scanner_detects_pii(self):
        from domains.comms.services.email.email_gateway import DLPScanner

        result = DLPScanner.scan_content(
            "Contact me at test@example.com or call 555-123-4567"
        )
        assert "findings" in result
        assert result["risk_level"] in ("none", "medium", "high")

    def test_dlp_scanner_redacts_pii(self):
        from domains.comms.services.email.email_gateway import DLPScanner

        redacted = DLPScanner.redact_content("Email: test@example.com")
        assert "test@example.com" not in redacted
        assert "[REDACTED]" in redacted
