"""Comms domain — public facade.

Exports the public API for the comms domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "ChatService": ("domains.comms.services.messaging.chat_service", "ChatService"),
    "EmailGateway": ("domains.comms.services.email.email_gateway", "EmailGateway"),
    "EmailManagement": ("domains.comms.services.email.email_management", "EmailManagement"),
    "TransactionalEmail": ("domains.comms.services.email.transactional", "TransactionalEmail"),
    "TicketsService": ("domains.comms.services.tickets.tickets_service", "TicketsService"),
    "ProxyCommunication": ("domains.comms.services.proxy_communication", "ProxyCommunication"),
    # models
    "Chat": ("domains.comms.models.chat", "Chat"),
    "Communication": ("domains.comms.models.communication", "Communication"),
    "NewsletterSubscriber": ("domains.comms.models.marketing", "NewsletterSubscriber"),
    "EmailCampaign": ("domains.comms.models.marketing", "EmailCampaign"),
    # functions
    "send_notification": ("domains.comms.services.proxy_communication", "send_notification"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.comms' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
