"""
Banner Controller — DB-backed banner management.

Replaces the legacy banner.json file-based approach with proper
multi-instance-safe PostgreSQL storage using the Banner model.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from controllers.audit_controller import audit_log, AuditAction
from utils.cache import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from models import Banner

logger = logging.getLogger(__name__)

_BANNER_CACHE_TTL = 120


def _build_list_page_payload(items: list[dict], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }

# ── Default banners seeded when DB is empty ─────────────────────────────────

_DEFAULT_BANNERS = [
    {
        "title": "Curated global finds, delivered with polish.",
        "subtitle": "A more elegant marketplace flow with verified suppliers, secure checkout, and weekly featured drops tailored for discovery.",
        "image_url": None,
        "cta_label": "Explore the edit",
        "cta_url": "/products",
        "banner_type": "hero",
        "sort_order": 0,
        "bg_color": "#22c55e",
        "text_color": "#ffffff",
        "subtitle_color": "rgba(255,255,255,0.86)",
        "btn_bg_color": "rgba(255,255,255,0.16)",
        "btn_text_color": "#ffffff",
        "badge_text": "Marketplace Edit",
        "badge_color": "rgba(255,255,255,0.14)",
        "effect": "aurora",
    },
    {
        "title": "Flash deals, staged like a premium campaign.",
        "subtitle": "Seasonal offers rotate automatically so every live promotion gets room to breathe across categories and suppliers.",
        "image_url": None,
        "cta_label": "View offers",
        "cta_url": "/products?deals=1",
        "banner_type": "flash",
        "sort_order": 1,
        "bg_color": "#0f172a",
        "text_color": "#f8fafc",
        "subtitle_color": "rgba(248,250,252,0.82)",
        "btn_bg_color": "#ffd400",
        "btn_text_color": "#111111",
        "badge_text": "Flash Deals",
        "badge_color": "rgba(255,255,255,0.14)",
        "effect": "poppers",
    },
    {
        "title": "Ramadan collection with calm, luminous motion.",
        "subtitle": "Set the homepage mood with moonlit movement, elegant festive tones, and curated seasonal campaigns from the admin panel.",
        "image_url": None,
        "cta_label": "View seasonal picks",
        "cta_url": "/products?newArrivals=1",
        "banner_type": "seasonal",
        "sort_order": 2,
        "bg_color": "#14532d",
        "text_color": "#ffffff",
        "subtitle_color": "rgba(255,255,255,0.84)",
        "btn_bg_color": "rgba(255,255,255,0.16)",
        "btn_text_color": "#ffffff",
        "badge_text": "Ramadan Highlights",
        "badge_color": "rgba(255,255,255,0.14)",
        "effect": "ramadan",
    },
    {
        "title": "Eid celebrations with brighter festive energy.",
        "subtitle": "Switch to a sparkling celebratory backdrop for launch days, festive sales, and special homepage moments.",
        "image_url": None,
        "cta_label": "Celebrate with deals",
        "cta_url": "/products?deals=1",
        "banner_type": "seasonal",
        "sort_order": 3,
        "bg_color": "#4338ca",
        "text_color": "#ffffff",
        "subtitle_color": "rgba(255,255,255,0.84)",
        "btn_bg_color": "#f8fafc",
        "btn_text_color": "#111111",
        "badge_text": "Eid Celebration",
        "badge_color": "rgba(255,255,255,0.14)",
        "effect": "eid",
    },
    {
        "title": "Verified suppliers and secure checkout, always.",
        "subtitle": "Transparent ratings, protected payments, and global dispatch from curated partners.",
        "image_url": None,
        "cta_label": "Shop best sellers",
        "cta_url": "/products?bestSellers=1",
        "banner_type": "hero",
        "sort_order": 4,
        "bg_color": "#0f172a",
        "text_color": "#f8fafc",
        "subtitle_color": "rgba(248,250,252,0.82)",
        "btn_bg_color": "rgba(255,255,255,0.16)",
        "btn_text_color": "#ffffff",
        "badge_text": "Trust & Safety",
        "badge_color": "rgba(255,255,255,0.14)",
        "effect": "aurora",
    },
]

# ── Pydantic Models ──────────────────────────────────────────────────────────

class BannerCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    cta_label: Optional[str] = "Shop Now"
    cta_url: Optional[str] = "/products"
    banner_type: Optional[str] = "hero"
    is_active: Optional[bool] = True
    sort_order: Optional[int] = 0
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    # Appearance — all optional; frontend applies smart defaults when absent
    bg_color: Optional[str] = None
    text_color: Optional[str] = None
    subtitle_color: Optional[str] = None
    btn_bg_color: Optional[str] = None
    btn_text_color: Optional[str] = None
    badge_text: Optional[str] = None
    badge_color: Optional[str] = None
    effect: Optional[str] = None
    video_url: Optional[str] = None
    country_code: Optional[str] = None
    # Free-form canvas editor layout (JSON-encoded string)
    layout_json: Optional[str] = None


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None
    banner_type: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    # Appearance
    bg_color: Optional[str] = None
    text_color: Optional[str] = None
    subtitle_color: Optional[str] = None
    btn_bg_color: Optional[str] = None
    btn_text_color: Optional[str] = None
    badge_text: Optional[str] = None
    badge_color: Optional[str] = None
    effect: Optional[str] = None
    video_url: Optional[str] = None
    country_code: Optional[str] = None
    # Free-form canvas editor layout (JSON-encoded string)
    layout_json: Optional[str] = None


def _banner_to_dict(banner: Banner) -> dict:
    starts_at = cast(datetime | None, getattr(banner, "starts_at"))
    ends_at = cast(datetime | None, getattr(banner, "ends_at"))
    created_at = cast(datetime | None, getattr(banner, "created_at"))
    updated_at = cast(datetime | None, getattr(banner, "updated_at"))
    banner_type = cast(str | None, getattr(banner, "banner_type", None)) or "hero"
    image_url = cast(str | None, getattr(banner, "image_url", None)) or ""
    return {
        "id": banner.id,
        "title": banner.title,
        "subtitle": banner.subtitle,
        "image_url": image_url,
        "cta_label": banner.cta_label,
        "cta_url": banner.cta_url,
        "banner_type": banner_type,
        "position": banner_type,
        "is_active": banner.is_active,
        "sort_order": banner.sort_order,
        "starts_at": starts_at.isoformat() if starts_at else None,
        "ends_at": ends_at.isoformat() if ends_at else None,
        # Appearance fields — may be None (frontend applies defaults)
        "bg_color": banner.bg_color,
        "text_color": banner.text_color,
        "subtitle_color": banner.subtitle_color,
        "btn_bg_color": banner.btn_bg_color,
        "btn_text_color": banner.btn_text_color,
        "badge_text": banner.badge_text,
        "badge_color": banner.badge_color,
        "effect": banner.effect,
        "video_url": banner.video_url,
        "country_code": banner.country_code,
        "layout_json": getattr(banner, "layout_json", None),
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def _seed_defaults(db: Session) -> None:
    """Insert default banners if the table is empty."""
    count = db.query(Banner).count()
    if count == 0:
        for d in _DEFAULT_BANNERS:
            db.add(Banner(**d))
        db.commit()
        return

    existing_titles = {title for (title,) in db.query(Banner.title).all()}
    inserted = False
    for default_banner in _DEFAULT_BANNERS:
        if default_banner["title"] in existing_titles:
            continue
        db.add(Banner(**default_banner))
        inserted = True
    if inserted:
        db.commit()


def get_banners(db: Session, banner_type: Optional[str] = None, active_only: bool = False, country_code: Optional[str] = None) -> list[dict]:
    """Return banners, optionally filtered by type and/or active status."""
    _seed_defaults(db)
    cache_key: Optional[str] = None
    if active_only:
        cache_key = build_versioned_cache_key(
            "banners",
            "list",
            {"banner_type": banner_type, "active_only": active_only},
        )
        cached_payload = cache_get_json(cache_key)
        if isinstance(cached_payload, list):
            return cached_payload

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    q = db.query(Banner)
    if country_code:
        q = q.filter(or_(Banner.country_code == country_code, Banner.country_code == None))
    if banner_type:
        q = q.filter(Banner.banner_type == banner_type)
    if active_only:
        q = q.filter(Banner.is_active == True)
        q = q.filter(
            (Banner.starts_at == None) | (Banner.starts_at <= now)
        ).filter(
            (Banner.ends_at == None) | (Banner.ends_at >= now)
        )
    banners = q.order_by(Banner.sort_order.asc(), Banner.id.asc()).limit(100).all()
    serialized = [_banner_to_dict(b) for b in banners]
    if cache_key is not None:
        cache_set_json(cache_key, serialized, _BANNER_CACHE_TTL)
    return serialized


def get_banners_page(
    db: Session,
    banner_type: Optional[str] = None,
    active_only: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> dict:
    _seed_defaults(db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    query = db.query(Banner)
    if banner_type:
        query = query.filter(Banner.banner_type == banner_type)
    if active_only:
        query = query.filter(Banner.is_active == True)
        query = query.filter(
            (Banner.starts_at == None) | (Banner.starts_at <= now)
        ).filter(
            (Banner.ends_at == None) | (Banner.ends_at >= now)
        )

    total = query.count()
    query = query.order_by(Banner.sort_order.asc(), Banner.id.asc())
    if offset:
        query = query.offset(offset)
    query = query.limit(limit if limit is not None else 100)
    banners = query.all()
    serialized = [_banner_to_dict(banner) for banner in banners]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=limit if limit is not None else len(serialized))


def get_banner_by_id(banner_id: int, db: Session) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return _banner_to_dict(banner)


def create_banner(payload: BannerCreate, admin_id: int, current_admin: dict, db: Session) -> dict:
    banner = Banner(
        title=payload.title,
        subtitle=payload.subtitle,
        image_url=payload.image_url,
        cta_label=payload.cta_label,
        cta_url=payload.cta_url,
        banner_type=payload.banner_type,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        bg_color=payload.bg_color,
        text_color=payload.text_color,
        subtitle_color=payload.subtitle_color,
        btn_bg_color=payload.btn_bg_color,
        btn_text_color=payload.btn_text_color,
        badge_text=payload.badge_text,
        badge_color=payload.badge_color,
        effect=payload.effect,
        video_url=payload.video_url,
        country_code=payload.country_code,
        layout_json=payload.layout_json,
        created_by=admin_id,
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    audit_log(
        db,
        action=AuditAction.BANNER_CREATED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="banner",
        resource_id=cast(int, getattr(banner, "id")),
        details={"title": banner.title, "banner_type": banner.banner_type},
    )
    bump_cache_version("banners")
    return _banner_to_dict(banner)


def update_banner(banner_id: int, payload: BannerUpdate, current_admin: dict, db: Session) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    updates = payload.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(banner, field, value)
    setattr(banner, "updated_at", datetime.now(timezone.utc).replace(tzinfo=None))
    db.commit()
    db.refresh(banner)
    audit_log(
        db,
        action=AuditAction.BANNER_UPDATED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="banner",
        resource_id=cast(int, getattr(banner, "id")),
        details={"updated_fields": sorted(updates.keys())},
    )
    bump_cache_version("banners")
    return _banner_to_dict(banner)


def delete_banner(banner_id: int, current_admin: dict, db: Session) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    banner_title = banner.title
    db.delete(banner)
    db.commit()
    audit_log(
        db,
        action=AuditAction.BANNER_DELETED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="banner",
        resource_id=banner_id,
        details={"title": banner_title},
    )
    bump_cache_version("banners")
    return {"detail": "Banner deleted"}


async def upload_banner_image(
    banner_id: int,
    file: UploadFile,
    current_admin: dict,
    db: Session,
) -> dict:
    """Upload and attach an image to a banner."""
    from utils.file_validation import validate_upload_image
    from services.storage import storage as _storage

    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    content = await file.read()
    ext = validate_upload_image(content, file.filename or "banner")
    suffix = ext if ext.startswith(".") else f".{ext}"
    filename = f"banner_{uuid.uuid4().hex[:8]}{suffix}"
    key = f"banners/{filename}"
    url = _storage.save(key, content, content_type=file.content_type)

    setattr(banner, "image_url", url)
    setattr(banner, "updated_at", datetime.now(timezone.utc).replace(tzinfo=None))
    db.commit()
    db.refresh(banner)
    audit_log(
        db,
        action=AuditAction.BANNER_IMAGE_UPLOADED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="banner",
        resource_id=cast(int, getattr(banner, "id")),
        details={"filename": filename},
    )
    bump_cache_version("banners")
    return _banner_to_dict(banner)


def reorder_banners(banner_ids: list[int], current_admin: dict, db: Session) -> list[dict]:
    """Accept an ordered list of banner IDs and reassign sort_order accordingly."""
    for index, bid in enumerate(banner_ids):
        db.query(Banner).filter(Banner.id == bid).update({"sort_order": index})
    db.commit()
    audit_log(
        db,
        action=AuditAction.BANNER_REORDERED,
        user_id=current_admin.get("id"),
        username=current_admin.get("username"),
        user_role=current_admin.get("role"),
        resource_type="banner",
        details={"banner_ids": banner_ids},
    )
    bump_cache_version("banners")
    return get_banners(db)

