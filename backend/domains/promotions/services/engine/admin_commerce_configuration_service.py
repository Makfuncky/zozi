"""Admin promotions router — country-scoped."""
from typing import Optional
from fastapi import Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.comms.models.marketing import FlashSale
from domains.governance.models.admin import PromotionEngineConfig
from domains.governance.models.admin import PromotionOrderTier
from domains.catalog.models.promotions import Banner
from domains.catalog.models.promotions import Coupon
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import enforce_country_access
from domains.governance.services.settings.misc_service import archive_entity
from domains.governance.services.settings.misc_service import restore_entity
from domains.catalog.ports import bulk_archive_entities
from domains.catalog.ports import bulk_restore_entities
from domains.governance.services.settings.misc_service import hard_delete_entity

def _banner_to_dict(b: Banner) -> dict:
    return {'id': b.id, 'title': b.title, 'subtitle': b.subtitle, 'image_url': b.image_url, 'link': b.link, 'cta_label': getattr(b, 'cta_label', None), 'cta_url': getattr(b, 'cta_url', b.link), 'banner_type': b.banner_type, 'position': getattr(b, 'position', b.banner_type), 'is_active': b.is_active, 'is_deleted': b.is_deleted, 'sort_order': b.sort_order, 'bg_color': b.bg_color, 'text_color': b.text_color, 'subtitle_color': b.subtitle_color, 'btn_bg_color': b.btn_bg_color, 'btn_text_color': b.btn_text_color, 'badge_text': b.badge_text, 'badge_color': b.badge_color, 'effect': getattr(b, 'effect', None), 'layout_json': getattr(b, 'layout_json', None), 'video_url': getattr(b, 'video_url', None), 'country_code': b.country_code, 'starts_at': getattr(b, 'starts_at', None), 'ends_at': getattr(b, 'ends_at', None), 'created_at': b.created_at.isoformat() if b.created_at else None, 'updated_at': getattr(b, 'updated_at', b.created_at)}

def get_promotion_config(_: User=Depends(require_admin), db: Session=Depends(get_db)):
    config = db.query(PromotionEngineConfig).first()
    return config or {'message': 'No config found'}

def update_promotion_config(config_id: int, engine_enabled: Optional[bool]=None, stacking_mode: Optional[str]=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
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

def list_coupons(include_deleted: bool=False, country: Optional[str]=Query(None, description='Filter by country code'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Global coupon list with optional country filter."""
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if country and country != '*':
        q = q.filter(Coupon.country_code == country.upper())
    return q.all()

def create_coupon(code: str, discount_type: str='percentage', discount_value: float=0, minimum_order: Optional[float]=None, maximum_discount: Optional[float]=None, usage_limit: Optional[int]=None, starts_at: Optional[str]=None, expires_at: Optional[str]=None, is_active: bool=True, country_code: Optional[str]=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Create a coupon (optionally scoped to a country)."""
    from infrastructure.utils.datetime_utils import utcnow
    from datetime import datetime
    existing = db.query(Coupon).filter(Coupon.code == code).first()
    if existing:
        raise HTTPException(400, detail='Coupon code already exists')
    coupon = Coupon(code=code, discount_type=discount_type, discount_value=discount_value, minimum_order=minimum_order, maximum_discount=maximum_discount, usage_limit=usage_limit, starts_at=datetime.fromisoformat(starts_at) if starts_at else None, expires_at=datetime.fromisoformat(expires_at) if expires_at else None, is_active=is_active, country_code=country_code.upper() if country_code else None)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def list_flash_sales(include_deleted: bool=False, country: Optional[str]=Query(None, description='Filter by country code'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Global flash-sales list with optional country filter."""
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if country and country != '*':
        q = q.filter(FlashSale.country_code == country.upper())
    return q.all()

def create_flash_sale(title: str, discount_pct: float, starts_at: str, ends_at: str, description: Optional[str]=None, is_active: bool=True, country_code: Optional[str]=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Create a flash sale (optionally scoped to a country)."""
    from datetime import datetime
    sale = FlashSale(title=title, description=description, discount_pct=discount_pct, starts_at=datetime.fromisoformat(starts_at), ends_at=datetime.fromisoformat(ends_at), is_active=is_active, country_code=country_code.upper() if country_code else None)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale

def update_flash_sale(sale_id: int, title: Optional[str]=None, description: Optional[str]=None, discount_pct: Optional[float]=None, starts_at: Optional[str]=None, ends_at: Optional[str]=None, is_active: Optional[bool]=None, country_code: Optional[str]=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    from datetime import datetime
    sale = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not sale:
        raise HTTPException(404, detail='Flash sale not found')
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

def list_banners_promotions(include_deleted: bool=False, page: int=Query(1, ge=1), page_size: int=Query(50, ge=1, le=200), country: Optional[str]=Query(None, description='Filter by country code'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Paginated banners list with optional country filter."""
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.is_deleted == False)
    if country and country != '*':
        q = q.filter(Banner.country_code == country.upper())
    total = q.count()
    items = q.order_by(Banner.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': [_banner_to_dict(b) for b in items], 'total': total, 'page': page, 'page_size': page_size}

def create_banner_promotion(title: str, subtitle: Optional[str]=None, image_url: Optional[str]=None, link: Optional[str]=None, cta_label: Optional[str]=None, cta_url: Optional[str]=None, banner_type: str='hero', is_active: bool=True, sort_order: int=0, bg_color: Optional[str]=None, text_color: Optional[str]=None, subtitle_color: Optional[str]=None, btn_bg_color: Optional[str]=None, btn_text_color: Optional[str]=None, badge_text: Optional[str]=None, badge_color: Optional[str]=None, effect: Optional[str]=None, country_code: Optional[str]=None, layout_json: Optional[str]=None, video_url: Optional[str]=None, admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Create a banner (optionally scoped to a country)."""
    banner = Banner(title=title, subtitle=subtitle, image_url=image_url, link=link or cta_url, banner_type=banner_type, is_active=is_active, sort_order=sort_order, bg_color=bg_color, text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color, btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color, country_code=country_code.upper() if country_code else None)
    if hasattr(banner, 'effect'):
        banner.effect = effect
    if hasattr(banner, 'layout_json'):
        banner.layout_json = layout_json
    if hasattr(banner, 'video_url'):
        banner.video_url = video_url
    if hasattr(banner, 'cta_label'):
        banner.cta_label = cta_label
    if hasattr(banner, 'cta_url'):
        banner.cta_url = cta_url
    if hasattr(banner, 'deleted_by_id'):
        banner.deleted_by_id = None
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)

def update_banner_promotion(banner_id: int, title: Optional[str]=None, subtitle: Optional[str]=None, image_url: Optional[str]=None, link: Optional[str]=None, cta_label: Optional[str]=None, cta_url: Optional[str]=None, banner_type: Optional[str]=None, is_active: Optional[bool]=None, sort_order: Optional[int]=None, bg_color: Optional[str]=None, text_color: Optional[str]=None, subtitle_color: Optional[str]=None, btn_bg_color: Optional[str]=None, btn_text_color: Optional[str]=None, badge_text: Optional[str]=None, badge_color: Optional[str]=None, effect: Optional[str]=None, country_code: Optional[str]=None, layout_json: Optional[str]=None, video_url: Optional[str]=None, admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail='Banner not found')
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
    if effect is not None and hasattr(banner, 'effect'):
        banner.effect = effect
    if layout_json is not None and hasattr(banner, 'layout_json'):
        banner.layout_json = layout_json
    if video_url is not None and hasattr(banner, 'video_url'):
        banner.video_url = video_url
    if cta_label is not None and hasattr(banner, 'cta_label'):
        banner.cta_label = cta_label
    if cta_url is not None and hasattr(banner, 'cta_url'):
        banner.cta_url = cta_url
    if country_code is not None:
        banner.country_code = country_code.upper()
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)

def delete_banner_promotion(banner_id: int, admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail='Banner not found')
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, 'deleted_by_id'):
        banner.deleted_by_id = admin.id
    from infrastructure.utils.datetime_utils import utcnow
    if hasattr(banner, 'deleted_at'):
        banner.deleted_at = utcnow()
    db.commit()
    return {'message': 'Banner deleted'}

def list_promotion_tiers(_: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    q = db.query(PromotionOrderTier)
    total = q.count()
    rows = q.order_by(PromotionOrderTier.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}

def list_coupons_by_country(code: str=Path(..., description="ISO country code or '*' for all"), include_deleted: bool=False, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    q = db.query(Coupon)
    if not include_deleted:
        q = q.filter(Coupon.is_deleted == False)
    if code != '*':
        q = q.filter(Coupon.country_code == code.upper())
    return q.all()

def create_coupon_by_country(code: str=Path(...), coupon_code: str=Query(..., alias='code'), discount_type: str='percentage', discount_value: float=0, minimum_order: Optional[float]=None, maximum_discount: Optional[float]=None, usage_limit: Optional[int]=None, starts_at: Optional[str]=None, expires_at: Optional[str]=None, is_active: bool=True, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    from datetime import datetime
    existing = db.query(Coupon).filter(Coupon.code == coupon_code).first()
    if existing:
        raise HTTPException(400, detail='Coupon code already exists')
    country = code.upper() if code != '*' else None
    coupon = Coupon(code=coupon_code, discount_type=discount_type, discount_value=discount_value, minimum_order=minimum_order, maximum_discount=maximum_discount, usage_limit=usage_limit, starts_at=datetime.fromisoformat(starts_at) if starts_at else None, expires_at=datetime.fromisoformat(expires_at) if expires_at else None, is_active=is_active, country_code=country)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def list_flash_sales_by_country(code: str=Path(...), include_deleted: bool=False, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    q = db.query(FlashSale)
    if not include_deleted:
        q = q.filter(FlashSale.is_deleted == False)
    if code != '*':
        q = q.filter(FlashSale.country_code == code.upper())
    return q.all()

def list_banners_by_country(code: str=Path(...), include_deleted: bool=False, page: int=Query(1, ge=1), page_size: int=Query(50, ge=1, le=200), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    q = db.query(Banner)
    if not include_deleted:
        q = q.filter(Banner.is_deleted == False)
    if code != '*':
        q = q.filter(Banner.country_code == code.upper())
    total = q.count()
    items = q.order_by(Banner.sort_order).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': [_banner_to_dict(b) for b in items], 'total': total, 'page': page, 'page_size': page_size}

def create_banner_by_country(code: str=Path(...), title: str='', subtitle: Optional[str]=None, image_url: Optional[str]=None, link: Optional[str]=None, cta_label: Optional[str]=None, cta_url: Optional[str]=None, banner_type: str='hero', is_active: bool=True, sort_order: int=0, bg_color: Optional[str]=None, text_color: Optional[str]=None, subtitle_color: Optional[str]=None, btn_bg_color: Optional[str]=None, btn_text_color: Optional[str]=None, badge_text: Optional[str]=None, badge_color: Optional[str]=None, effect: Optional[str]=None, layout_json: Optional[str]=None, video_url: Optional[str]=None, admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    country = code.upper() if code != '*' else None
    banner = Banner(title=title, subtitle=subtitle, image_url=image_url, link=link or cta_url, banner_type=banner_type, is_active=is_active, sort_order=sort_order, bg_color=bg_color, text_color=text_color, subtitle_color=subtitle_color, btn_bg_color=btn_bg_color, btn_text_color=btn_text_color, badge_text=badge_text, badge_color=badge_color, country_code=country)
    if hasattr(banner, 'effect'):
        banner.effect = effect
    if hasattr(banner, 'layout_json'):
        banner.layout_json = layout_json
    if hasattr(banner, 'video_url'):
        banner.video_url = video_url
    if hasattr(banner, 'cta_label'):
        banner.cta_label = cta_label
    if hasattr(banner, 'cta_url'):
        banner.cta_url = cta_url
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)

def update_banner_by_country(code: str=Path(...), banner_id: int=Path(...), title: Optional[str]=None, subtitle: Optional[str]=None, image_url: Optional[str]=None, link: Optional[str]=None, cta_label: Optional[str]=None, cta_url: Optional[str]=None, banner_type: Optional[str]=None, is_active: Optional[bool]=None, sort_order: Optional[int]=None, bg_color: Optional[str]=None, text_color: Optional[str]=None, subtitle_color: Optional[str]=None, btn_bg_color: Optional[str]=None, btn_text_color: Optional[str]=None, badge_text: Optional[str]=None, badge_color: Optional[str]=None, effect: Optional[str]=None, layout_json: Optional[str]=None, video_url: Optional[str]=None, admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail='Banner not found')
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
    if effect is not None and hasattr(banner, 'effect'):
        banner.effect = effect
    if layout_json is not None and hasattr(banner, 'layout_json'):
        banner.layout_json = layout_json
    if video_url is not None and hasattr(banner, 'video_url'):
        banner.video_url = video_url
    if cta_label is not None and hasattr(banner, 'cta_label'):
        banner.cta_label = cta_label
    if cta_url is not None and hasattr(banner, 'cta_url'):
        banner.cta_url = cta_url
    db.commit()
    db.refresh(banner)
    return _banner_to_dict(banner)

def delete_banner_by_country(code: str=Path(...), banner_id: int=Path(...), admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    enforce_country_access(code, db=db)
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(404, detail='Banner not found')
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, 'deleted_by_id'):
        banner.deleted_by_id = admin.id
    from infrastructure.utils.datetime_utils import utcnow
    if hasattr(banner, 'deleted_at'):
        banner.deleted_at = utcnow()
    db.commit()
    return {'message': 'Banner deleted'}


# === Archive/restore wrappers (extracted from admin routers) ===

def archive_coupon(coupon_id: int, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return archive_entity("coupon", coupon_id, acting_user, db, reason)


def restore_coupon(coupon_id: int, acting_user: dict, db: Session) -> dict:
    return restore_entity("coupon", coupon_id, acting_user, db)


def bulk_archive_coupons(payload: dict, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return bulk_archive_entities("coupon", payload.get("ids", []), acting_user, db, reason)


def bulk_restore_coupons(payload: dict, acting_user: dict, db: Session) -> dict:
    return bulk_restore_entities("coupon", payload.get("ids", []), acting_user, db)


def archive_flash_sale(sale_id: int, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return archive_entity("flash_sale", sale_id, acting_user, db, reason)


def restore_flash_sale(sale_id: int, acting_user: dict, db: Session) -> dict:
    return restore_entity("flash_sale", sale_id, acting_user, db)


def bulk_archive_flash_sales(payload: dict, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return bulk_archive_entities("flash_sale", payload.get("ids", []), acting_user, db, reason)


def bulk_restore_flash_sales(payload: dict, acting_user: dict, db: Session) -> dict:
    return bulk_restore_entities("flash_sale", payload.get("ids", []), acting_user, db)


def archive_banner(banner_id: int, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return archive_entity("banner", banner_id, acting_user, db, reason)


def restore_banner(banner_id: int, acting_user: dict, db: Session) -> dict:
    return restore_entity("banner", banner_id, acting_user, db)


def bulk_archive_banners(payload: dict, acting_user: dict, db: Session, reason: Optional[str] = None) -> dict:
    return bulk_archive_entities("banner", payload.get("ids", []), acting_user, db, reason)


def bulk_restore_banners(payload: dict, acting_user: dict, db: Session) -> dict:
    return bulk_restore_entities("banner", payload.get("ids", []), acting_user, db)
