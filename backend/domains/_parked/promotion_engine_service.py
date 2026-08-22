# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Promotion engine configuration service.

Implements the previously-stubbed helpers used by ``controllers.commerce.promotion_controller``:
ensuring the promotion tables exist and getting-or-creating the engine config row.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from domains.governance.ports import PromotionEngineConfig
from infrastructure.database.base import Base
from infrastructure.utils.config import settings
import structlog
logger = structlog.get_logger(__name__)


def ensure_promotion_tables(db: Session) -> None:
    """Create any missing promotion-engine tables.

    In dev/test (SQLite) the schema is rebuilt from the ORM metadata so nothing
    extra is needed; on other backends we create only tables that are missing.
    Never auto-mutates schema in production — migrations own the prod schema.
    """
    if str(getattr(settings, "app_env", "")).strip().lower() == "production":
        return
    bind = db.get_bind()
    inspector = sa_inspect(bind)
    existing = set(inspector.get_table_names())
    to_create = [
        t for t in Base.metadata.tables.values()
        if t.name not in existing
    ]
    if to_create:
        Base.metadata.create_all(bind, tables=to_create, checkfirst=True)


def get_or_create_config(
    db: Session,
    *,
    key: str = "default",
    country_code: Optional[str] = None,
    defaults: Optional[dict] = None,
) -> PromotionEngineConfig:
    """Return the singleton promotion-engine config, creating it if absent.

    The controller calls this with only ``db``; we resolve the first non-deleted
    config row (or create one) so the helper is safe under that call form.
    """
    config = (
        db.query(PromotionEngineConfig)
        .filter(PromotionEngineConfig.is_deleted.is_(False))
        .order_by(PromotionEngineConfig.id.asc())
        .first()
    )
    if config is not None:
        return config

    fields: dict = dict(defaults or {})
    fields.setdefault("country_code", country_code)
    fields.setdefault("engine_enabled", False)
    config = PromotionEngineConfig(**fields)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config
