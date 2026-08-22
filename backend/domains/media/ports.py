"""media domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.media.models`` or ``domains.media.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.media.models.ai_upload import AIGenerationLog, AIStagingProduct, AIStagingVariant, AIUploadJob
from domains.media.models.media_models import MediaAsset, MediaUploadSession
from domains.media.models.upload_job import UploadJob
from domains.media.models.media_schema_models import VideoRoomRecording, OCRResult  # A3: sanctioned ports surface for accounts hub
from domains.media.services.ai import ai_service


def get_a_i_upload_job_by_id(db: Session, id_: int) -> Optional[AIUploadJob]:
    """Return AIUploadJob by primary key (or None)."""
    return db.get(AIUploadJob, id_)

def list_a_i_upload_jobs(db: Session, limit: int = 100) -> List[AIUploadJob]:
    """Return up to ``limit`` AIUploadJob rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AIUploadJob, db, limit)

def list_a_i_upload_jobs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AIUploadJob rows (scale-ready)."""
    return _keyset_page(AIUploadJob, db, cursor, page_size)

def get_a_i_staging_product_by_id(db: Session, id_: int) -> Optional[AIStagingProduct]:
    """Return AIStagingProduct by primary key (or None)."""
    return db.get(AIStagingProduct, id_)

def list_a_i_staging_products(db: Session, limit: int = 100) -> List[AIStagingProduct]:
    """Return up to ``limit`` AIStagingProduct rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AIStagingProduct, db, limit)

def list_a_i_staging_products_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AIStagingProduct rows (scale-ready)."""
    return _keyset_page(AIStagingProduct, db, cursor, page_size)

def get_a_i_staging_variant_by_id(db: Session, id_: int) -> Optional[AIStagingVariant]:
    """Return AIStagingVariant by primary key (or None)."""
    return db.get(AIStagingVariant, id_)

def list_a_i_staging_variants(db: Session, limit: int = 100) -> List[AIStagingVariant]:
    """Return up to ``limit`` AIStagingVariant rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AIStagingVariant, db, limit)

def list_a_i_staging_variants_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AIStagingVariant rows (scale-ready)."""
    return _keyset_page(AIStagingVariant, db, cursor, page_size)

def get_a_i_generation_log_by_id(db: Session, id_: int) -> Optional[AIGenerationLog]:
    """Return AIGenerationLog by primary key (or None)."""
    return db.get(AIGenerationLog, id_)

def list_a_i_generation_logs(db: Session, limit: int = 100) -> List[AIGenerationLog]:
    """Return up to ``limit`` AIGenerationLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AIGenerationLog, db, limit)

def list_a_i_generation_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AIGenerationLog rows (scale-ready)."""
    return _keyset_page(AIGenerationLog, db, cursor, page_size)

def get_media_asset_by_id(db: Session, id_: int) -> Optional[MediaAsset]:
    """Return MediaAsset by primary key (or None)."""
    return db.get(MediaAsset, id_)

def list_media_assets(db: Session, limit: int = 100) -> List[MediaAsset]:
    """Return up to ``limit`` MediaAsset rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MediaAsset, db, limit)

def list_media_assets_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MediaAsset rows (scale-ready)."""
    return _keyset_page(MediaAsset, db, cursor, page_size)

def get_media_upload_session_by_id(db: Session, id_: int) -> Optional[MediaUploadSession]:
    """Return MediaUploadSession by primary key (or None)."""
    return db.get(MediaUploadSession, id_)

def list_media_upload_sessions(db: Session, limit: int = 100) -> List[MediaUploadSession]:
    """Return up to ``limit`` MediaUploadSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MediaUploadSession, db, limit)

def list_media_upload_sessions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MediaUploadSession rows (scale-ready)."""
    return _keyset_page(MediaUploadSession, db, cursor, page_size)

def get_upload_job_by_id(db: Session, id_: int) -> Optional[UploadJob]:
    """Return UploadJob by primary key (or None)."""
    return db.get(UploadJob, id_)

def list_upload_jobs(db: Session, limit: int = 100) -> List[UploadJob]:
    """Return up to ``limit`` UploadJob rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(UploadJob, db, limit)

def list_upload_jobs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of UploadJob rows (scale-ready)."""
    return _keyset_page(UploadJob, db, cursor, page_size)
