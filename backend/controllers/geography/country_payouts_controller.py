"""Thin controller for country-level payout rules (category/product overrides).

Holds permission checks only; every DB read/write is delegated to
``services.geography.country_payout_write_service`` so routers and controllers
stay free of session mutations (W1). ``HTTPException`` raised by the service is
allowed to propagate untouched.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from controllers.admin_controller import require_country_access
from services.geography.country_payout_write_service import (
    create_payout_rule_category as _create_payout_rule_category,
    create_payout_rule_product as _create_payout_rule_product,
    delete_payout_rule_category as _delete_payout_rule_category,
    delete_payout_rule_product as _delete_payout_rule_product,
    list_payout_rule_categories as _list_payout_rule_categories,
    list_payout_rule_products as _list_payout_rule_products,
)
import structlog
logger = structlog.get_logger(__name__)


# ── Category-level payout rules ─────────────────────────────────────────────────

def list_categories(code: str, current_user: dict, db: Session) -> list[dict]:
    require_country_access(code, current_user)
    return _list_payout_rule_categories(db, code)


def create_category(code: str, body: Any, current_user: dict, db: Session) -> dict:
    require_country_access(code, current_user)
    return _create_payout_rule_category(db, code, body)


def delete_category(code: str, rule_id: int, current_user: dict, db: Session) -> dict:
    require_country_access(code, current_user)
    return _delete_payout_rule_category(db, code, rule_id)


# ── Product-level payout rules ──────────────────────────────────────────────────

def list_products(code: str, current_user: dict, db: Session) -> list[dict]:
    require_country_access(code, current_user)
    return _list_payout_rule_products(db, code)


def create_product(code: str, body: Any, current_user: dict, db: Session) -> dict:
    require_country_access(code, current_user)
    return _create_payout_rule_product(db, code, body)


def delete_product(code: str, rule_id: int, current_user: dict, db: Session) -> dict:
    require_country_access(code, current_user)
    return _delete_payout_rule_product(db, code, rule_id)
