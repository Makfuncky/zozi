from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.marketing import FlashSale
from domains.governance.models.admin import PromotionEngineConfig
from domains.catalog.models.promotions import Banner
from domains.catalog.models.promotions import Coupon
import structlog
logger = structlog.get_logger(__name__)


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


def update_promotion_config(
    db: Session,
    *,
    config_id: int,
    engine_enabled: Optional[bool] = None,
    stacking_mode: Optional[str] = None,
) -> dict:
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


def create_banner(db: Session, *, title: str, country_code: Optional[str] = None, **fields) -> dict:
    banner = Banner(
        title=title,
        subtitle=fields.get("subtitle"),
        image_url=fields.get("image_url"),
        link=fields.get("link") or fields.get("cta_url"),
        banner_type=fields.get("banner_type", "hero"),
        is_active=fields.get("is_active", True),
        sort_order=fields.get("sort_order", 0),
        bg_color=fields.get("bg_color"),
        text_color=fields.get("text_color"),
        subtitle_color=fields.get("subtitle_color"),
        btn_bg_color=fields.get("btn_bg_color"),
        btn_text_color=fields.get("btn_text_color"),
        badge_text=fields.get("badge_text"),
        badge_color=fields.get("badge_color"),
        country_code=country_code.upper() if country_code else None,
    )
    if hasattr(banner, "effect"):
        banner.effect = fields.get("effect")
    if hasattr(banner, "layout_json"):
        banner.layout_json = fields.get("layout_json")
    if hasattr(banner, "video_url"):
        banner.video_url = fields.get("video_url")
    if hasattr(banner, "cta_label"):
        banner.cta_label = fields.get("cta_label")
    if hasattr(banner, "cta_url"):
        banner.cta_url = fields.get("cta_url")
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = None
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner_to_dict(banner)


def update_banner(db: Session, *, banner_id: int, country_code: Optional[str] = None, **fields) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    _apply_banner_fields(banner, country_code=country_code, **fields)
    db.commit()
    db.refresh(banner)
    return banner_to_dict(banner)


def delete_banner(db: Session, *, banner_id: int, admin_id: Any = None) -> dict:
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin_id
    if hasattr(banner, "deleted_at"):
        from infrastructure.utils.datetime_utils import utcnow

        banner.deleted_at = utcnow()
    db.commit()
    return {"message": "Banner deleted"}


def create_banner_by_country(db: Session, *, code: str, title: str, **fields) -> dict:
    country = code.upper() if code != "*" else None
    return create_banner(db, title=title, country_code=country, **fields)


def update_banner_by_country(db: Session, *, code: str, banner_id: int, **fields) -> dict:
    return update_banner(db, banner_id=banner_id, **fields)


def delete_banner_by_country(db: Session, *, code: str, banner_id: int, admin_id: Any = None) -> dict:
    return delete_banner(db, banner_id=banner_id, admin_id=admin_id)

