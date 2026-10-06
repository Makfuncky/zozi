"""Media domain — sanctioned cross-domain READ surface (ports)."""
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from providers.media.models.media_asset import MediaAsset


def get_media_asset_by_id(db: Session, id_: int) -> Optional[MediaAsset]:
    return db.get(MediaAsset, id_)


def list_media_assets(
    db: Session,
    country_code: Optional[str] = None,
    limit: int = 100,
) -> list[MediaAsset]:
    q = db.query(MediaAsset)
    if country_code:
        q = q.filter(MediaAsset.country_code == country_code)
    return q.limit(limit).all()


__all__ = ["get_media_asset_by_id", "list_media_assets"]
