"""Admin promotions configuration service layer.

Houses the inline business/DB logic previously embedded in
``routers/admin_commerce_configuration.py`` so the router stays a thin HTTP
delegator. Bulk archive/restore/hard-delete operations are intentionally left
to ``controllers.admin.admin_controller`` (already service-layer) and are not
duplicated here.

The module also exposes ``country_router``-equivalent handlers (country-scoped
sub-routes) — the router performs ``enforce_country_access`` before delegating.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.marketing import FlashSale
from domains.governance.models.admin import PromotionEngineConfig
from domains.governance.models.admin import PromotionOrderTier
from domains.payments.models.payments import Banner
from domains.payments.models.payments import Coupon


def _banner_to_dict(b: Banner) -> dict:
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


# ── Promotion Engine Config ───────────────────────────────────────────────────

def get_promotion_config(db: Session):
    config = db.query(PromotionEngineConfig).first()
    return config or {"message": "No config found"}


def update_promotion_config(db: Session, config_id: int, engine_enabled: Optional[bool], stacking_mode: Optional[str]):
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


# ── Coupons ───────────────────────────────────────────────────────────────────

def list_coupons(db: Session, include_deleted: bool, country: Optional[str]) -> list:
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if country and country != "*":
        q = q.filter(Coupon.country_code == country.upper())
    return q.all()


def create_coupon(
    db: Session, code: str, discount_type: str, discount_value: float,
    minimum_order: Optional[float], maximum_discount: Optional[float],
    usage_limit: Optional[int], starts_at: Optional[str], expires_at: Optional[str],
    is_active: bool, country_code: Optional[str],
):
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


# ── Flash Sales ───────────────────────────────────────────────────────────────

def list_flash_sales(db: Session, include_deleted: bool, country: Optional[str]) -> list:
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if country and country != "*":
        q = q.filter(FlashSale.country_code == country.upper())
    return q.all()


def create_flash_sale(
    db: Session, title: str, discount_pct: float, starts_at: str, ends_at: str,
    description: Optional[str], is_active: bool, country_code: Optional[str],
):
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
    db: Session, sale_id: int, title: Optional[str], description: Optional[str],
    discount_pct: Optional[float], starts_at: Optional[str], ends_at: Optional[str],
    is_active: Optional[bool], country_code: Optional[str],
):
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


# ── Banners ───────────────────────────────────────────────────────────────────

def _apply_banner_fields(
    banner: Banner, *, title, subtitle, image_url, link, cta_label, cta_url,
    banner_type, is_active, sort_order, bg_color, text_color, subtitle_color,
    btn_bg_color, btn_text_color, badge_text, badge_color, effect, layout_json,
    video_url, country_code,
) -> None:
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


def _build_banner(
    *, title, subtitle, image_url, link, cta_label, cta_url, banner_type,
    is_active, sort_order, bg_color, text_color, subtitle_color, btn_bg_color,
    btn_text_color, badge_text, badge_color, effect, layout_json, video_url,
    country_code,
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
    return banner


def list_banners(db: Session, include_deleted: bool, page: int, page_size: int, country: Optional[str]) -> dict:
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.is_deleted == False)
    if country and country != "*":
        q = q.filter(Banner.country_code == country.upper())
    total = q.count()
    items = q.order_by(Banner.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [_banner_to_dict(b) for b in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_banner(
    db: Session, *, title, subtitle, image_url, link, cta_label, cta_url,
    banner_type, is_active, sort_order, bg_color, text_color, subtitle_color,
    btn_bg_color, btn_text_color, badge_text, badge_color, effect, layout_json,
    video_url, country_code,
) -> dict:
    banner = _build_banner(
        title=title, subtitle=subtitle, image_url=image_url, link=link,
        cta_label=cta_label, cta_url=cta_url, banner_type=banner_type,
        is_active=is_active, sort_order=sort_order, bg_color=bg_color,
        text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color,
        btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color,
        effect=effect, layout_json=layout_json, video_url=video_url, country_code=country_code,
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


def update_banner(
    db: Session, banner_id: int, *, title, subtitle, image_url, link, cta_label,
    cta_url, banner_type, is_active, sort_order, bg_color, text_color,
    subtitle_color, btn_bg_color, btn_text_color, badge_text, badge_color, effect,
    layout_json, video_url, country_code,
) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    _apply_banner_fields(
        banner, title=title, subtitle=subtitle, image_url=image_url, link=link,
        cta_label=cta_label, cta_url=cta_url, banner_type=banner_type,
        is_active=is_active, sort_order=sort_order, bg_color=bg_color, text_color=text_color,
        subtitle_color=subtitle_color, btn_bg_color=btn_bg_color, btn_text_color=btn_text_color,
        badge_text=badge_text, badge_color=badge_color, effect=effect, layout_json=layout_json,
        video_url=video_url, country_code=country_code,
    )
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


def delete_banner(db: Session, banner_id: int, admin_id: int) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin_id
    from infrastructure.utils.datetime_utils import utcnow
    if hasattr(banner, "deleted_at"):
        banner.deleted_at = utcnow()
    db.commit()
    return {"message": "Banner deleted"}


# ── Promotion Order Tiers ─────────────────────────────────────────────────────

def list_promotion_tiers(db: Session, page: int, page_size: int) -> dict:
    q = db.query(PromotionOrderTier)
    total = q.count()
    rows = q.order_by(PromotionOrderTier.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


# ── Country-scoped sub-routes ─────────────────────────────────────────────────

def list_coupons_by_country(db: Session, code: str, include_deleted: bool) -> list:
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if code != "*":
        q = q.filter(Coupon.country_code == code.upper())
    return q.all()


def create_coupon_by_country(
    db: Session, code: str, coupon_code: str, discount_type: str, discount_value: float,
    minimum_order: Optional[float], maximum_discount: Optional[float],
    usage_limit: Optional[int], starts_at: Optional[str], expires_at: Optional[str],
    is_active: bool,
):
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


def list_flash_sales_by_country(db: Session, code: str, include_deleted: bool) -> list:
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if code != "*":
        q = q.filter(FlashSale.country_code == code.upper())
    return q.all()


def list_banners_by_country(db: Session, code: str, include_deleted: bool, page: int, page_size: int) -> dict:
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.is_deleted == False)
    if code != "*":
        q = q.filter(Banner.country_code == code.upper())
    total = q.count()
    items = q.order_by(Banner.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": [_banner_to_dict(b) for b in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_banner_by_country(
    db: Session, code: str, *, title, subtitle, image_url, link, cta_label,
    cta_url, banner_type, is_active, sort_order, bg_color, text_color,
    subtitle_color, btn_bg_color, btn_text_color, badge_text, badge_color,
    effect, layout_json, video_url,
) -> dict:
    country = code.upper() if code != "*" else None
    banner = _build_banner(
        title=title, subtitle=subtitle, image_url=image_url, link=link,
        cta_label=cta_label, cta_url=cta_url, banner_type=banner_type,
        is_active=is_active, sort_order=sort_order, bg_color=bg_color,
        text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color,
        btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color,
        effect=effect, layout_json=layout_json, video_url=video_url, country_code=country,
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


def update_banner_by_country(
    db: Session, code: str, banner_id: int, *, title, subtitle, image_url, link,
    cta_label, cta_url, banner_type, is_active, sort_order, bg_color, text_color,
    subtitle_color, btn_bg_color, btn_text_color, badge_text, badge_color, effect,
    layout_json, video_url,
) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    _apply_banner_fields(
        banner, title=title, subtitle=subtitle, image_url=image_url, link=link,
        cta_label=cta_label, cta_url=cta_url, banner_type=banner_type,
        is_active=is_active, sort_order=sort_order, bg_color=bg_color, text_color=text_color,
        subtitle_color=subtitle_color, btn_bg_color=btn_bg_color, btn_text_color=btn_text_color,
        badge_text=badge_text, badge_color=badge_color, effect=effect, layout_json=layout_json,
        video_url=video_url, country_code=None,
    )
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


def delete_banner_by_country(db: Session, code: str, banner_id: int, admin_id: int) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin_id
    from infrastructure.utils.datetime_utils import utcnow
    if hasattr(banner, "deleted_at"):
        banner.deleted_at = utcnow()
    db.commit()
    return {"message": "Banner deleted"}
