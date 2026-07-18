"""Admin promotions router — country-scoped."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import PromotionEngineConfig, PromotionOrderTier, FlashSale, Banner, Coupon, User
from db.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.country_rls import enforce_country_access
from controllers.admin_controller import (
    archive_entity,
    restore_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    hard_delete_entity,
)

router = APIRouter()


def _user_ctx(u: User) -> dict:
    return {"id": u.id, "username": u.username, "role": u.role}


# ── Promotion Engine Config ───────────────────────────────────────────────────

@router.get("/config")
def get_promotion_config(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    config = db.query(PromotionEngineConfig).first()
    return config or {"message": "No config found"}


@router.put("/config")
def update_promotion_config(
    config_id: int,
    engine_enabled: Optional[bool] = None,
    stacking_mode: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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

@router.get("/coupons")
def list_coupons(
    include_deleted: bool = False,
    country: Optional[str] = Query(None, description="Filter by country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Global coupon list with optional country filter."""
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if country and country != "*":
        q = q.filter(Coupon.country_code == country.upper())
    return q.all()


@router.post("/coupons")
def create_coupon(
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
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a coupon (optionally scoped to a country)."""
    from utils.datetime_utils import utcnow
    from datetime import datetime

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


@router.post("/coupons/{coupon_id}/archive")
def archive_coupon(
    coupon_id: int,
    payload: Optional[ArchiveRequest] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return archive_entity("coupon", coupon_id, _user_ctx(current_user), db, payload.reason if payload else None)


@router.post("/coupons/{coupon_id}/restore")
def restore_coupon(
    coupon_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return restore_entity("coupon", coupon_id, _user_ctx(current_user), db)


@router.post("/coupons/bulk-archive")
def bulk_archive_coupons(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_archive_entities("coupon", payload.ids, _user_ctx(current_user), db, payload.reason)


@router.post("/coupons/bulk-restore")
def bulk_restore_coupons(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_restore_entities("coupon", payload.ids, _user_ctx(current_user), db)


# ── Flash Sales ───────────────────────────────────────────────────────────────

@router.get("/flash-sales")
def list_flash_sales(
    include_deleted: bool = False,
    country: Optional[str] = Query(None, description="Filter by country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Global flash-sales list with optional country filter."""
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if country and country != "*":
        q = q.filter(FlashSale.country_code == country.upper())
    return q.all()


@router.post("/flash-sales")
def create_flash_sale(
    title: str,
    discount_pct: float,
    starts_at: str,
    ends_at: str,
    description: Optional[str] = None,
    is_active: bool = True,
    country_code: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a flash sale (optionally scoped to a country)."""
    from datetime import datetime
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


@router.put("/flash-sales/{sale_id}")
def update_flash_sale(
    sale_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_pct: Optional[float] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    is_active: Optional[bool] = None,
    country_code: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from datetime import datetime
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


@router.post("/flash-sales/{sale_id}/archive")
def archive_flash_sale(
    sale_id: int,
    payload: Optional[ArchiveRequest] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return archive_entity("flash_sale", sale_id, _user_ctx(current_user), db, payload.reason if payload else None)


@router.post("/flash-sales/{sale_id}/restore")
def restore_flash_sale(
    sale_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return restore_entity("flash_sale", sale_id, _user_ctx(current_user), db)


@router.post("/flash-sales/bulk-archive")
def bulk_archive_flash_sales(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_archive_entities("flash_sale", payload.ids, _user_ctx(current_user), db, payload.reason)


@router.post("/flash-sales/bulk-restore")
def bulk_restore_flash_sales(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_restore_entities("flash_sale", payload.ids, _user_ctx(current_user), db)


# ── Banners ───────────────────────────────────────────────────────────────────

@router.get("/banners")
def list_banners_promotions(
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    country: Optional[str] = Query(None, description="Filter by country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Paginated banners list with optional country filter."""
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


@router.post("/banners")
def create_banner_promotion(
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
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a banner (optionally scoped to a country)."""
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
    return _banner_to_dict(banner)


@router.put("/banners/{banner_id}")
def update_banner_promotion(
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
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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
    return _banner_to_dict(banner)


@router.delete("/banners/{banner_id}")
def delete_banner_promotion(
    banner_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin.id
    from utils.datetime_utils import utcnow
    if hasattr(banner, "deleted_at"):
        banner.deleted_at = utcnow()
    db.commit()
    return {"message": "Banner deleted"}


@router.post("/banners/{banner_id}/archive")
def archive_banner(
    banner_id: int,
    payload: Optional[ArchiveRequest] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return archive_entity("banner", banner_id, _user_ctx(current_user), db, payload.reason if payload else None)


@router.post("/banners/{banner_id}/restore")
def restore_banner(
    banner_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return restore_entity("banner", banner_id, _user_ctx(current_user), db)


@router.post("/banners/bulk-archive")
def bulk_archive_banners(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_archive_entities("banner", payload.ids, _user_ctx(current_user), db, payload.reason)


@router.post("/banners/bulk-restore")
def bulk_restore_banners(
    payload: BulkActionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return bulk_restore_entities("banner", payload.ids, _user_ctx(current_user), db)


# ── Promotion Order Tiers ─────────────────────────────────────────────────────

@router.get("/tiers")
def list_promotion_tiers(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(PromotionOrderTier).order_by(PromotionOrderTier.sort_order).all()


# ── Country-scoped sub-routes for Promotions ─────────────────────────────────
# These allow /admin/{code}/promotions/coupons etc., registered from main.py

country_router = APIRouter()


@country_router.get("/{code}/promotions/coupons")
def list_coupons_by_country(
    code: str = Path(..., description="ISO country code or '*' for all"),
    include_deleted: bool = False,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if code != "*":
        q = q.filter(Coupon.country_code == code.upper())
    return q.all()


@country_router.post("/{code}/promotions/coupons")
def create_coupon_by_country(
    code: str = Path(...),
    coupon_code: str = Query(..., alias="code"),
    discount_type: str = "percentage",
    discount_value: float = 0,
    minimum_order: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    is_active: bool = True,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    from datetime import datetime

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


@country_router.get("/{code}/promotions/flash-sales")
def list_flash_sales_by_country(
    code: str = Path(...),
    include_deleted: bool = False,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if code != "*":
        q = q.filter(FlashSale.country_code == code.upper())
    return q.all()


@country_router.get("/{code}/promotions/banners")
def list_banners_by_country(
    code: str = Path(...),
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
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


@country_router.post("/{code}/promotions/banners")
def create_banner_by_country(
    code: str = Path(...),
    title: str = "",
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
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    country = code.upper() if code != "*" else None
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
        country_code=country,
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
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


@country_router.put("/{code}/promotions/banners/{banner_id}")
def update_banner_by_country(
    code: str = Path(...),
    banner_id: int = Path(...),
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
    layout_json: Optional[str] = None,
    video_url: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
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
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)


@country_router.delete("/{code}/promotions/banners/{banner_id}")
def delete_banner_by_country(
    code: str = Path(...),
    banner_id: int = Path(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail="Banner not found")
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, "deleted_by_id"):
        banner.deleted_by_id = admin.id
    from utils.datetime_utils import utcnow
    if hasattr(banner, "deleted_at"):
        banner.deleted_at = utcnow()
    db.commit()
    return {"message": "Banner deleted"}


# ── Helpers ───────────────────────────────────────────────────────────────────

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

