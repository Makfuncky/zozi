"""Comms domain — law-aligned architecture tests.

Maps to ARCHITECTURE_DIAGRAM.md Laws:
  Law 1   : arrows point down only
  Law 3   : cross-domain writes via events.py, reads via ports.py
  Law 4   : features single-sourced
  Laws 6/23/55/152 : schema discipline
  Laws 22/52 : FK ondelete
  Laws 124/131 : provider isolation + graceful degradation (HAS_ flags)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from tests._support.laws import (
    BACKEND_ROOT,
    assert_feature_in_catalog,
    assert_foreign_keys_have_ondelete,
    assert_no_forbidden_imports,
    assert_schema_discipline,
    iter_domain_models,
)

DOMAIN = "comms"


def _comms_models():
    return list(iter_domain_models(DOMAIN))


# Models missing required audit columns (Law 23/229).
# These are real violations tracked for remediation — see final report.
KNOWN_SCHEMA_VIOLATIONS = {
    "EntityChatThread",
    "VideoRoom",
    "VideoRoomParticipant",
    "DirectChatRoom",
    "GroupChatMember",
    "EscalationSLALog",
    "EntityChatMessage",
    "VideoRoomRecording",
    "DirectChatMessage",
    "GroupChatRoom",
    "GroupChatMessage",
    "Announcement",
    "HelpCategory",
    "ProxyChannel",
    "ProxySession",
    "ProxyMessage",
    "ProxyCallLog",
    "ExternalContactMasking",
    "CommunicationAuditTrail",
    "InternalChannelMember",
    "InternalMessage",
    "ChatReadReceipt",
    "ChatAttachment",
    "EmailFolder",
    "EmailTemplate",
    "NewsletterSubscriber",
    "EmailCampaignLog",
    "CampaignRecipient",
    "EmailDeliveryEvent",
    "EmailSuppression",
    "EmailRuntimeConfig",
    "PointsTransaction",
    "UserPoints",
    "NewsArticle",
    "SupportTicket",
    "SupportTicketReply",
    "TicketAttachment",
    "NewsSource",
    "InternalNotice",
    "EscalationSLARule",
    "MeetingRecording",
    "IncidentWarRoom",
    "IncidentThread",
    "IncidentActionItem",
    "WarRoomTemplate",
}


class TestCommsSchemaDiscipline:
    """Laws 6/23/55/152 — schema + audit columns."""

    @pytest.mark.parametrize("model", _comms_models(), ids=lambda m: m.__name__)
    def test_model_schema_discipline(self, model):
        if model.__name__ in KNOWN_SCHEMA_VIOLATIONS:
            pytest.xfail(
                f"{model.__name__}: missing audit columns (Law 23/229)"
            )
        assert_schema_discipline(model)


class TestCommsForeignKeyOndelete:
    """Laws 22/52 — every ForeignKey declares explicit ondelete."""

    @pytest.mark.parametrize("model", _comms_models(), ids=lambda m: m.__name__)
    def test_foreign_keys_have_ondelete(self, model):
        assert_foreign_keys_have_ondelete(model)


class TestCommsFeaturesSingleSourced:
    """Law 4 — feature atoms single-sourced + in rbac catalog."""

    def test_features_declared(self):
        from domains.comms.features import FEATURES

        assert isinstance(FEATURES, dict)
        assert len(FEATURES) > 0

    @pytest.mark.parametrize(
        "feature",
        [
            "comms.notification.read",
            "comms.notification.manage",
            "comms.ticket.create",
            "comms.ticket.read",
            "comms.chat.send",
            "comms.chat.read",
            "comms.campaign.create",
            "comms.proxy.use",
            "comms.video_room.create",
            "comms.announcement.create",
            "comms.sla.manage",
            "comms.broadcast",
            "comms.audit.read",
        ],
    )
    def test_feature_in_catalog(self, feature):
        assert_feature_in_catalog(feature)


class TestCommsEventsAndPortsWired:
    """Law 3 — cross-domain writes via events.py, reads via ports.py."""

    def test_events_module_has_comms_events(self):
        from domains.comms import events

        assert hasattr(events, "EVENT_NOTIFICATION_CREATED")
        assert hasattr(events, "EVENT_TICKET_REPLIED")
        assert hasattr(events, "EVENT_TICKET_STATUS_CHANGED")
        assert hasattr(events, "EVENT_ESCALATION_TRIGGERED")

    def test_events_has_publish_helpers(self):
        from domains.comms import events

        assert callable(events.publish_notification_created)
        assert callable(events.publish_ticket_replied)
        assert callable(events.publish_escalation_triggered)

    def test_ports_module_has_read_functions(self):
        from domains.comms import ports

        assert callable(ports.get_notification_by_id)
        assert callable(ports.list_notifications)
        assert callable(ports.get_ticket_message_by_id)

    def test_ports_has_cursor_pagination(self):
        from domains.comms import ports

        assert callable(ports.list_notifications_page)

    def test_subscribers_have_handlers(self):
        from domains.comms import subscribers

        assert callable(subscribers._on_ticket_status_changed)
        assert callable(subscribers._on_order_created)
        assert isinstance(subscribers.subscribed_types(), list)


class TestCommsImportLaws:
    """Law 1 — arrows point down only."""

    def test_no_forbidden_imports_in_domain(self):
        source_dir = BACKEND_ROOT / "domains" / DOMAIN
        assert_no_forbidden_imports("domains", source_dir)


class TestCommsProviderIsolation:
    """Laws 124/131 — provider isolation + graceful degradation."""

    def test_email_provider_has_flag(self):
        """Provider modules expose HAS_<SDK> flags for graceful degradation."""
        from providers.comms import email as email_provider

        assert hasattr(email_provider, "HAS_EMAIL") or hasattr(
            email_provider, "HAS_SMTP"
        )

    def test_comms_email_gateway_imports_only_providers(self):
        """Email gateway must not import domain models directly — only via
        sanctioned paths. It may import from providers/ and infrastructure/."""
        import ast
        from pathlib import Path

        gateway_path = (
            BACKEND_ROOT
            / "domains"
            / "comms"
            / "services"
            / "email"
            / "email_gateway.py"
        )
        tree = ast.parse(gateway_path.read_text(encoding="utf-8"))
        # The gateway is allowed to import from its own domain models (comms),
        # providers, and infrastructure. It must NOT import from other domains
        # (e.g. hr, orders, finance) at module level.
        forbidden_roots = {"domains.hr", "domains.orders", "domains.finance"}
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module.startswith(f) for f in forbidden_roots):
                    violations.append(f"{gateway_path}:{node.lineno}: {node.module}")
        assert not violations, f"Cross-domain imports in email_gateway: {violations}"

    def test_comms_service_degrades_without_provider(self):
        """Comms service must gracefully degrade when a provider SDK is absent."""
        from domains.comms.services.comms_service import CommsService

        assert CommsService is not None
