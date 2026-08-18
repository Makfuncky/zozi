"""Flash Sale write service.

Owns the DB write primitives for flash-sale CRUD (add/commit/refresh and
delete/commit). Moved out of controllers/flash_sale_controller.py to satisfy
the W1 layer contract (read-only orchestration layers must not write to the DB).
The surrounding validation, audit, and cache-bump logic stays in the controller.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from _legacy.models import FlashSale


def flash_sale_persist_create(db: Session, sale: FlashSale) -> FlashSale:
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def flash_sale_persist_update(db: Session, sale: FlashSale) -> FlashSale:
    db.commit()
    db.refresh(sale)
    return sale


def flash_sale_persist_delete(db: Session, sale: FlashSale) -> None:
    db.delete(sale)
    db.commit()
