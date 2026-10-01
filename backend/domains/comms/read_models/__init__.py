# CQRS-lite read models for the `comms` domain.
# Sanctioned cross-domain READ surface (ARCHITECTURE_DIAGRAM.md Sec.3).
# Populated incrementally as projections are extracted from write services.

from .notification_read_models import (  # noqa: F401
    NotificationProjection,
    InboxItemProjection,
    CommandCenterNotificationProjection,
)

__all__ = [
    "NotificationProjection",
    "InboxItemProjection",
    "CommandCenterNotificationProjection",
]

