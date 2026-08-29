"""Admin promotions write/persistence service (Promotions domain).

Owns the DB writes (W1) for ``routers.admin_promotions_governance``: promotion engine
config, coupons, flash sales and banners (global + country-scoped). Router
handlers stay thin HTTP adapters that preserve the exact return shapes (the
router keeps applying ``_banner_to_dict`` for banner endpoints).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.promotions.models.promotions import FlashSale
from domains.promotions.models.promotion_config import PromotionEngineConfig
from domains.governance.models.admin import PromotionOrderTier
from domains.promotions.models.promotions import Banner
from domains.promotions.models.promotions import Coupon
import structlog
logger = structlog.get_logger(__name__)


# ── Promotion Engine Config ─────────────────────────────────────────


def update_promotion_config(
    db: Session,
    *,
    config_id: int,
    engine_enabled: Optional[bool] = None,
    stacking_mode: Optional[str] = None,
) -> PromotionEngineConfig:
    config = db.query(PromotionEngineConfig).filter(PromotionEngineConfig.id == config_id).first()
    if not config:
        raise HTTPException(404)
    if engine_enabled is not None:
        config.engine_enabled = engine_enabled
    if stacking_mode is not None:
        config.stacking_mode = stacking_mode
    db.commit()
    db.refresh(config)
    return config


# ── Coupons ─────────────────────────────────────────────────────────


def create_coupon(
    db: Session,
    *,
    code: str,
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    is_active: bool = True,
    country_code: Optional[str] = None,
) -> Coupon:
    existing = db.query(Coupon).filter(Coupon.code == code).first()
    if existing:
        raise HTTPException(400, detail="Coupon code already exists")
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        minimum_order=minimum_order,
        maximum_discount=maximum_discount,
        usage_limit=usage_limit,
        starts_at=datetime.fromisoformat(starts_at) if starts_at else None,
        expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        is_active=is_active,
        country_code=country_code.upper() if country_code else None,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


# ── Flash Sales ────────────────────────────────────────────────────


def create_flash_sale(
    db: Session,
    *,
    title: str,
    discount_pct: float,
    starts_at: str,
    ends_at: str,
    description: Optional[str] = None,
    is_active: bool = True,
    country_code: Optional[str] = None,
) -> FlashSale:
    sale = FlashSale(
        title=title,
        description=description,
        discount_pct=discount_pct,
        starts_at=datetime.fromisoformat(starts_at),
        ends_at=datetime.fromisoformat(ends_at),
        is_active=is_active,
        country_code=country_code.upper() if country_code else None,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def update_flash_sale(
    db: Session,
    *,
    sale_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_pct: Optional[float] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    is_active: Optional[bool] = None,
    country_code: Optional[str] = None,
) -> FlashSale:
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(404, detail="Flash sale not found")
    if title is not None:
        sale.title = title
    if description is not None:
        sale.description = description
    if discount_pct is not None:
        sale.discount_pct = discount_pct
    if starts_at is not None:
        sale.starts_at = datetime.fromisoformat(starts_at)
    if ends_at is not None:
        sale.ends_at = datetime.fromisoformat(ends_at)
    if is_active is not None:
        sale.is_active = is_active
    if country_code is not None:
        sale.country_code = country_code.upper()
    db.commit()
    db.refresh(sale)
    return sale


# ── Banners ─────────────────────────────────────────────────────────


def create_banner(
    db: Session,
    *,
    title: str,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: str = "hero",
    is_active: bool = True,
    sort_order: int = 0,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    country_code: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
) -> Banner:
    banner = Banner(
        title=title,
        subtitle=subtitle,
        image_url=image_url,
        link=link or cta_url,
        banner_type=banner_type,
        is_active=is_active,
        sort_order=sort_order,
        bg_color=bg_color,
        text_color=text_color,
        subtitle_color=subtitle_color,
        btn_bg_color=btn_bg_color,
        btn_text_color=btn_text_color,
        badge_text=badge_text,
        badge_color=badge_color,
        country_code=country_code.upper() if country_code else None,
    )
    if hasattr(banner, "effect"):
        banner.effect = effect
    if hasattr(banner, "layout_json"):
        banner.layout_json = layout_json
    if hasattr(banner, "video_url"):
        banner.video_url = video_url
    if hasattr(banner, "cta_label"):
        banner.cta_label = cta_label
    if hasattr(banner, "cta_url"):
        banner.cta_url = cta_url
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = None
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(
    db: Session,
    *,
    banner_id: int,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    link: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    banner_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_order: Optional[int] = None,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    subtitle_color: Optional[str] = None,
    btn_bg_color: Optional[str] = None,
    btn_text_color: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: Optional[str] = None,
    effect: Optional[str] = None,
    country_code: Optional[str] = None,
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
) -> Banner:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    if title is not None:
        banner.title = title
    if subtitle is not None:
        banner.subtitle = subtitle
    if image_url is not None:
        banner.image_url = image_url
    if link is not None:
        banner.link = link
    if banner_type is not None:
        banner.banner_type = banner_type
    if is_active is not None:
        banner.is_active = is_active
    if sort_order is not None:
        banner.sort_order = sort_order
    if bg_color is not None:
        banner.bg_color = bg_color
    if text_color is not None:
        banner.text_color = text_color
    if subtitle_color is not None:
        banner.subtitle_color = subtitle_color
    if btn_bg_color is not None:
        banner.btn_bg_color = btn_bg_color
    if btn_text_color is not None:
        banner.btn_text_color = btn_text_color
    if badge_text is not None:
        banner.badge_text = badge_text
    if badge_color is not None:
        banner.badge_color = badge_color
    if effect is not None and hasattr(banner, "effect"):
        banner.effect = effect
    if layout_json is not None and hasattr(banner, "layout_json"):
        banner.layout_json = layout_json
    if video_url is not None and hasattr(banner, "video_url"):
        banner.video_url = video_url
    if cta_label is not None and hasattr(banner, "cta_label"):
        banner.cta_label = cta_label
    if cta_url is not None and hasattr(banner, "cta_url"):
        banner.cta_url = cta_url
    if country_code is not None:
        banner.country_code = country_code.upper()
    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, *, banner_id: int, admin_id: Optional[int] = None) -> None:
    from infrastructure.utils.datetime_utils import utcnow

    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin_id
    if hasattr(banner, "deleted_at"):
        banner.deleted_at = utcnow()
    db.commit()


# ── Reads (Q1) ──────────────────────────────────────────────────────
# Routers delegate list/get endpoints here so DB reads live in the
# service layer, not in routers/controllers.


def get_promotion_config(db: Session):
    return db.query(PromotionEngineConfig).first()


def list_coupons(
    db: Session,
    *,
    include_deleted: bool = False,
    country: Optional[str] = None,
) -> list:
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)  # noqa: E712
    if country and country != "*":
        q = q.filter(Coupon.country_code == country.upper())
    return q.limit(1000).all()


def list_flash_sales(
    db: Session,
    *,
    include_deleted: bool = False,
    country: Optional[str] = None,
) -> list:
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)  # noqa: E712
    if country and country != "*":
        q = q.filter(FlashSale.country_code == country.upper())
    return q.limit(1000).all()


def list_banners_paginated(
    db: Session,
    *,
    include_deleted: bool = False,
    page: int = 1,
    page_size: int = 50,
    country: Optional[str] = None,
):
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.is_deleted == False)  # noqa: E712
    if country and country != "*":
        q = q.filter(Banner.country_code == country.upper())
    total = q.count()
    items = (
        q.order_by(Banner.sort_order)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def list_promotion_tiers(db: Session, *, page: int = 1, page_size: int = 20):
    q = db.query(PromotionOrderTier)
    total = q.count()
    rows = (
        q.order_by(PromotionOrderTier.sort_order)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return rows, total


def banner_to_dict(b: Banner) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "image_url": b.image_url,
        "link": b.link,
        "cta_label": getattr(b, "cta_label", None),
        "cta_url": getattr(b, "cta_url", b.link),
        "banner_type": b.banner_type,
        "position": getattr(b, "position", b.banner_type),
        "is_active": b.is_active,
        "is_deleted": b.is_deleted,
        "sort_order": b.sort_order,
        "bg_color": b.bg_color,
        "text_color": b.text_color,
        "subtitle_color": b.subtitle_color,
        "btn_bg_color": b.btn_bg_color,
        "btn_text_color": b.btn_text_color,
        "badge_text": b.badge_text,
        "badge_color": b.badge_color,
        "effect": getattr(b, "effect", None),
        "layout_json": getattr(b, "layout_json", None),
        "video_url": getattr(b, "video_url", None),
        "country_code": b.country_code,
        "starts_at": getattr(b, "starts_at", None),
        "ends_at": getattr(b, "ends_at", None),
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": getattr(b, "updated_at", b.created_at),
    }


# Backwards-compatible alias (router historically named it _banner_to_dict).
_banner_to_dict = banner_to_dict


# ── Country-scoped variants (from promotion_admin_write_service) ─────────────────


def create_coupon_by_country(
    db: Session,
    *,
    code: str,
    coupon_code: str,
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    is_active: bool = True,
) -> Coupon:
    existing = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if existing:
        raise HTTPException(400, detail="Coupon code already exists")
    country = code.upper() if code != "*" else None
    coupon = Coupon(
        code=coupon_code,
        discount_type=discount_type,
        discount_value=discount_value,
        minimum_order=minimum_order,
        maximum_discount=maximum_discount,
        usage_limit=usage_limit,
        starts_at=datetime.fromisoformat(starts_at) if starts_at else None,
        expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        is_active=is_active,
        country_code=country,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def _apply_banner_fields(banner: Banner, **fields) -> None:
    banner.title = fields["title"] if fields.get("title") is not None else banner.title
    if fields.get("subtitle") is not None:
        banner.subtitle = fields["subtitle"]
    if fields.get("image_url") is not None:
        banner.image_url = fields["image_url"]
    if fields.get("link") is not None:
        banner.link = fields["link"]
    if fields.get("banner_type") is not None:
        banner.banner_type = fields["banner_type"]
    if fields.get("is_active") is not None:
        banner.is_active = fields["is_active"]
    if fields.get("sort_order") is not None:
        banner.sort_order = fields["sort_order"]
    if fields.get("bg_color") is not None:
        banner.bg_color = fields["bg_color"]
    if fields.get("text_color") is not None:
        banner.text_color = fields["text_color"]
    if fields.get("subtitle_color") is not None:
        banner.subtitle_color = fields["subtitle_color"]
    if fields.get("btn_bg_color") is not None:
        banner.btn_bg_color = fields["btn_bg_color"]
    if fields.get("btn_text_color") is not None:
        banner.btn_text_color = fields["btn_text_color"]
    if fields.get("badge_text") is not None:
        banner.badge_text = fields["badge_text"]
    if fields.get("badge_color") is not None:
        banner.badge_color = fields["badge_color"]
    if fields.get("effect") is not None and hasattr(banner, "effect"):
        banner.effect = fields["effect"]
    if fields.get("layout_json") is not None and hasattr(banner, "layout_json"):
        banner.layout_json = fields["layout_json"]
    if fields.get("video_url") is not None and hasattr(banner, "video_url"):
        banner.video_url = fields["video_url"]
    if fields.get("cta_label") is not None and hasattr(banner, "cta_label"):
        banner.cta_label = fields["cta_label"]
    if fields.get("cta_url") is not None and hasattr(banner, "cta_url"):
        banner.cta_url = fields["cta_url"]
    if fields.get("country_code") is not None:
        banner.country_code = fields["country_code"].upper()


def create_banner_by_country(db: Session, *, code: str, title: str, **fields) -> dict:
    country = code.upper() if code != "*" else None
    return create_banner(db, title=title, country_code=country, **fields)


def update_banner_by_country(db: Session, *, code: str, banner_id: int, **fields) -> dict:
    return update_banner(db, banner_id=banner_id, **fields)


def delete_banner_by_country(db: Session, *, code: str, banner_id: int, admin_id: Any = None) -> dict:
    return delete_banner(db, banner_id=banner_id, admin_id=admin_id)


def health():
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}


def status():
    return {"router": "admin_promotions_routes", "controller": "controllers.commerce.promotion_admin_controller"}


def update_config(config_id: int, engine_enabled: Optional[bool] = None, stacking_mode: Optional[str] = None, db=None, current_user: dict = None) -> dict:
    return update_promotion_config(config_id, engine_enabled, stacking_mode, db, current_user)


create_coupon_for_country = create_coupon_by_country
create_banner_for_country = create_banner_by_country
update_banner_for_country = update_banner_by_country
delete_banner_for_country = delete_banner_by_country
