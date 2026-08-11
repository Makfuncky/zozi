"""Backward-compatible re-export shim for banner write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.catalog.banner_controller`, which created
an import-time circular-import cycle (`banner_controller` ->
`banner_write_service` -> `banner_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_banner": ("controllers.catalog.banner_controller", "create_banner"),
    "delete_banner": ("controllers.catalog.banner_controller", "delete_banner"),
    "reorder_banners": ("controllers.catalog.banner_controller", "reorder_banners"),
    "update_banner": ("controllers.catalog.banner_controller", "update_banner"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from data.models import Banner
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    return isinstance(obj, Model)


def add_banner_if_missing(db: Session, banner=None, **kw) -> Banner:
    """Insert a banner only when no banner with the same (title, country_code) exists.

    ``banner`` may be a dict (legacy controller form) or omitted in favour of
    keyword arguments (spec form ``title``/``country_code``/``**kw``).
    """
    if isinstance(banner, dict):
        title = banner.get("title")
        country_code = banner.get("country_code")
        fields = dict(banner)
    else:
        title = kw.get("title")
        country_code = kw.get("country_code")
        fields = dict(kw)

    if not title:
        raise ValueError("title is required to add a banner")

    existing = db.query(Banner).filter(
        Banner.title == title,
        Banner.is_deleted.is_(False),
        Banner.country_code == country_code,
    ).first()
    if existing is not None:
        return existing

    record = Banner(**fields)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def bulk_add_banners(db: Session, banners: list) -> list:
    """Insert many banners, de-duplicating against existing titles per country."""
    created = []
    for item in banners or []:
        if not isinstance(item, dict):
            continue
        record = add_banner_if_missing(db, item)
        created.append(record)
    return created


def update_banner_image(db: Session, banner_or_id, image_url: str, filename: Optional[str] = None, **kw) -> Banner:
    """Update a banner's image (legacy controller form passes a banner object)."""
    if _is_orm(banner_or_id, Banner):
        record = banner_or_id
    else:
        record = db.get(Banner, int(banner_or_id))
        if record is None:
            raise ValueError(f"Banner {banner_or_id} not found")
    record.image_url = image_url
    if filename is not None and hasattr(record, "image_filename"):
        record.image_filename = filename
    if kw:
        for k, v in kw.items():
            if hasattr(record, k) and v is not None:
                setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record
