"""One-off migration: local ``uploads/`` files → object storage + CDN.

Usage:
    python scripts/migrate_media_to_s3.py
    python scripts/migrate_media_to_s3.py --dry-run
    python scripts/migrate_media_to_s3.py --batch-size 200

What it does:
    1. Walks ``backend/uploads/`` recursively.
    2. For each file, derives a storage key by stripping the ``uploads/`` prefix.
    3. Uploads the file to the active S3-compatible backend (when ``STORAGE_BACKEND=s3``).
       In ``local`` mode it only prints what it *would* do.
    4. Rewrites DB columns that still contain local ``/uploads/...`` or ``uploads/...``
       paths to the returned CDN/public URL, in batches.

Columns touched:
    products.image_url
    product_variants.image_url
    users.profile_image
    supplier_profiles.logo_url / banner_url / video_url
    supplier_documents.file_url
    logistics_partner_documents.file_url
    product_videos.video_url / thumbnail_url
    banners.image_url
    media_assets.file_url
    chat_attachments.url
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy.orm import Session

from data.db import get_db_context
from data.services_storage import get_storage, S3Storage
from data.utils_config import settings

logger = logging.getLogger("zozi.migrate_media")

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"

DEFAULT_BATCH_SIZE = 200

# Columns that may contain legacy local ``uploads/...`` paths.
# Each entry is ``(model_path, column_name)``.
LEGACY_PATH_COLUMNS = [
    ("models.products.Product", "image_url"),
    ("models.products.ProductVariant", "image_url"),
    ("models.user.User", "profile_image"),
    ("models.suppliers.SupplierProfile", "logo_url"),
    ("models.suppliers.SupplierProfile", "banner_url"),
    ("models.suppliers.SupplierProfile", "video_url"),
    ("models.suppliers.SupplierDocument", "file_url"),
    ("models.logistics.LogisticsPartnerDocument", "file_url"),
    ("models.products.ProductVideo", "video_url"),
    ("models.products.ProductVideo", "thumbnail_url"),
    ("models.payments.Banner", "image_url"),
    ("models.media_models.MediaAsset", "file_url"),
    ("models.employee_models.ChatAttachment", "url"),
]


def _load_model(model_path: str):
    module_path, class_name = model_path.rsplit(".", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _is_local_path(value: Optional[str]) -> bool:
    if not value or not isinstance(value, str):
        return False
    v = value.strip()
    return v.startswith("/uploads/") or v.startswith("uploads/")


def _relative_key_from_local_path(local_path: str) -> str:
    """``/uploads/products/x.jpg`` or ``uploads/products/x.jpg`` -> ``products/x.jpg``."""
    v = local_path.strip()
    if v.startswith("/uploads/"):
        v = v[len("/uploads/"):]
    elif v.startswith("uploads/"):
        v = v[len("uploads/"):]
    return v.replace("\\", "/").lstrip("/")


def migrate(dry_run: bool = False, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
    storage = get_storage()
    is_s3 = isinstance(storage, S3Storage)

    if not UPLOADS_DIR.is_dir():
        logger.warning("Uploads directory not found: %s — nothing to migrate.", UPLOADS_DIR)
        return

    files = sorted(p for p in UPLOADS_DIR.rglob("*") if p.is_file())
    logger.info("Found %d files under %s", len(files), UPLOADS_DIR)

    if not files:
        return

    if dry_run:
        logger.info("DRY RUN — no files will be uploaded and no DB rows will be updated.")
    elif not is_s3:
        logger.warning(
            "STORAGE_BACKEND=%s — switching to dry-run because S3 is not active.",
            getattr(settings, "storage_backend", "local"),
        )
        dry_run = True

    migrated = 0
    skipped = 0
    errors = 0

    for start in range(0, len(files), batch_size):
        batch = files[start : start + batch_size]
        logger.info("Processing batch %d-%d / %d", start + 1, start + len(batch), len(files))

        # Build mapping: normalized local path -> new public URL
        path_map: Dict[str, str] = {}
        for path in batch:
            rel = _relative_key_from_local_path(str(path.relative_to(UPLOADS_DIR)))
            local_norm = f"uploads/{rel}"
            if dry_run:
                path_map[local_norm] = f"[dry-run] s3://.../{rel}"
                path_map[f"/{local_norm}"] = f"[dry-run] s3://.../{rel}"
            else:
                try:
                    data = path.read_bytes()
                    url = storage.save(rel, data, content_type=None)
                    path_map[local_norm] = url
                    path_map[f"/{local_norm}"] = url
                except Exception as exc:
                    logger.error("Failed to upload %s: %s", path, exc)
                    errors += 1

        if not path_map:
            continue

        if not dry_run:
            try:
                with get_db_context() as db:
                    _rewrite_batch(db, path_map)
                migrated += len(path_map) // 2  # each file added 2 variants
            except Exception as exc:
                logger.exception("Batch DB update failed: %s", exc)
                errors += len(path_map) // 2
        else:
            skipped += len(path_map) // 2

    logger.info(
        "Migration complete. migrated=%d skipped=%d errors=%d",
        migrated,
        skipped,
        errors,
    )


def _rewrite_batch(db: Session, path_map: Dict[str, str]) -> None:
    """Rewrite legacy local paths to new URLs for one batch."""
    updated_total = 0
    for model_path, column_name in LEGACY_PATH_COLUMNS:
        try:
            model_cls = _load_model(model_path)
        except Exception as exc:
            logger.warning("Could not load %s: %s", model_path, exc)
            continue

        col = getattr(model_cls, column_name, None)
        if col is None:
            continue

        keys = list(path_map.keys())
        rows = db.query(model_cls).filter(col.in_(keys)).all()
        if not rows:
            continue

        updated = 0
        for row in rows:
            current = getattr(row, column_name)
            new_url = path_map.get(current)
            if new_url:
                setattr(row, column_name, new_url)
                updated += 1

        if updated:
            logger.debug("Updated %d %s.%s rows", updated, model_cls.__tablename__, column_name)
            updated_total += updated

    db.commit()
    logger.info("DB batch committed: %d rows updated", updated_total)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Migrate local uploads to object storage")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading or writing DB")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Files per batch")
    args = parser.parse_args()

    migrate(dry_run=args.dry_run, batch_size=args.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
