"""Fulfillment service (orders package shim).

The operational implementation lives in ``services.fulfillment_service``. This
module provides a lightweight, dependency-free stand-in so the orders package
import graph stays acyclic and ``import main`` succeeds.
"""
from __future__ import annotations

from typing import Any


class FulfillmentService:
    """No-op fulfillment stand-in used during module load."""

    def __init__(self, db: Any = None) -> None:
        self.db = db
        self.notification_service = None

    def handle_payment_confirmed(self, event: Any, db: Any = None) -> None:
        return None

    def register_listeners(self, *args: Any, **kwargs: Any) -> None:
        return None


__all__ = ["FulfillmentService"]
