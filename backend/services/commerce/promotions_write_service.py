"""Promotions write service — DB write operations for promotions and discounts.""" 

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from data.models import (
    Banner,
    Coupon,
    FlashSale,
    PromotionEngineConfig,
    PromotionLedgerEntry,
    PromotionOrderTier,
)


def create_promotion_engine_config(db: Session, **config_data) -> PromotionEngineConfig:
    config = PromotionEngineConfig(**config_data)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_promotion_engine_config(
    db: Session, config: PromotionEngineConfig, updates: dict
) -> PromotionEngineConfig:
    for key, value in updates.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


def create_flash_sale(db: Session, **sale_data) -> FlashSale:
    sale = FlashSale(**sale_data)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def update_flash_sale(db: Session, sale: FlashSale, updates: dict) -> FlashSale:
    for key, value in updates.items():
        setattr(sale, key, value)
    db.commit()
    db.refresh(sale)
    return sale


def save_flash_sale(db: Session, sale: FlashSale) -> FlashSale:
    db.commit()
    db.refresh(sale)
    return sale


def delete_flash_sale(db: Session, sale: FlashSale) -> None:
    db.delete(sale)
    db.commit()


def create_banner(db: Session, **banner_data) -> Banner:
    banner = Banner(**banner_data)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(db: Session, banner: Banner, updates: dict) -> Banner:
    for key, value in updates.items():
        setattr(banner, key, value)
    db.commit()
    db.refresh(banner)
    return banner


def save_banner(db: Session, banner: Banner) -> Banner:
    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, banner: Banner) -> None:
    db.delete(banner)
    db.commit()


def create_coupon(db: Session, **coupon_data) -> Coupon:
    coupon = Coupon(**coupon_data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def save_coupon(db: Session, coupon: Coupon) -> Coupon:
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def persist_flash_sale(db: Session, sale: FlashSale) -> FlashSale:
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def persist_banner(db: Session, banner: Banner) -> Banner:
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def persist_coupon(db: Session, coupon: Coupon) -> Coupon:
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def soft_delete_banner(
    db: Session, banner: Banner, admin_id: int | None = None
) -> Banner:
    banner.is_deleted = True
    banner.is_active = False
    if hasattr(banner, 'deleted_by_id'):
        banner.deleted_by_id = admin_id
    if hasattr(banner, 'deleted_at'):
        from utils.datetime_utils import utcnow
        banner.deleted_at = utcnow()
    db.commit()
    return banner
