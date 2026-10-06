"""Media domain — event subscribers (Law 3)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def handle_media_asset_created(payload: dict) -> None:
    logger.debug("media.asset.created received: %s", payload)


def handle_media_asset_deleted(payload: dict) -> None:
    logger.debug("media.asset.deleted received: %s", payload)


def handle_upload_session_completed(payload: dict) -> None:
    logger.debug("media.upload_session.completed received: %s", payload)


__all__ = [
    "handle_media_asset_created",
    "handle_media_asset_deleted",
    "handle_upload_session_completed",
]
