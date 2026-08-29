"""Notification primitives (comms domain).

The canonical ``Notification`` ORM model lives in
``domains.comms.models.communication`` (per Law 6 — one table per domain). This
module provides the channel/priority enums used by the notification engine and
service layer.
"""
from __future__ import annotations

import enum


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
