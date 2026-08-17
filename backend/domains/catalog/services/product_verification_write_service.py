"""Product Verification write service.

Owns the DB write primitives for product-verification CRUD (add/commit/refresh
and bulk commit). Moved out of controllers/product_verification_controller.py to
satisfy the W1 layer contract (read-only orchestration layers must not write to
the DB). Validation and (de)serialization logic stays in the controller.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from _legacy.models import ProductVerification


def verification_persist_create(db: Session, verification: ProductVerification) -> ProductVerification:
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def verification_persist_update(db: Session, verification: ProductVerification) -> ProductVerification:
    db.commit()
    db.refresh(verification)
    return verification


def verification_persist_bulk_commit(db: Session) -> None:
    db.commit()
