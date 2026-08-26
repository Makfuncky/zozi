# === From supplier_orders.py ===
from suppliers.router import router  # noqa: F401
"""Supplier orders sub-router."""

import json

# AI analysis for parcel-photo matching (uses the vision provider)
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.suppliers.models.suppliers import SupplierProfile
from domains.orders.models.order_entities import Order
from domains.orders.models.order_entities import OrderItem
from infrastructure.utils.storage import storage as _storage
from infrastructure.utils.dependencies import require_supplier


def get_reference_image(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the latest reference image for this order.

    Returns the image file directly (JPEG/PNG/WebP) or 404 if no reference
    has been set yet.
    """
    user_id = _get_user_id(current_user)
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    prefix = f"parcel_proofs/{order_id}/"
    refs = sorted(
        [k for k in _storage.list(prefix) if os.path.basename(k).startswith("reference_")],
        reverse=True,
    )
    if not refs:
        raise HTTPException(status_code=404, detail="No reference image set for this order.")

    latest_key = refs[0]
    latest_url = _storage.url(latest_key)
    ext = os.path.splitext(latest_key)[1].lower()
    media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/jpeg")

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=latest_url, status_code=302)


@router.get("/parcel-verification-history")
def get_parcel_verification_history(
    limit: int = 10,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the last N parcel verification results for this supplier.

    Scans the uploads/parcel_proofs/ directory for the supplier's order
    proof images, reads the verification result JSON files, and returns
    them sorted by analysis timestamp (newest first).

    Each entry includes:
    - match_percentage (0-100)
    - status (verified / partial / unverified)
    - enginge_details breakdown (ssim, feature_match, vision_ai scores)
    - image_url for the thumbnail of the uploaded proof
    - order_number, order_id, items summary, analyzed_at
    """
    user_id = _get_user_id(current_user)
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    # Collect all verification results across this supplier's orders
    all_entries: list[dict] = []
    supplier_order_ids = [
        row[0] for row in db.query(Order.id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
        .all()
    ]

    for order_id in supplier_order_ids:
        prefix = f"parcel_proofs/{order_id}/"
        keys = _storage.list(prefix)

        ref_keys = sorted(
            [k for k in keys if os.path.basename(k).startswith("reference_")],
            reverse=True,
        )
        reference_image_url: str | None = None
        if ref_keys:
            reference_image_url = _storage.url(ref_keys[0])

        result_key = prefix + "_verification_result.json"
        if result_key not in keys:
            continue

        try:
            raw = _storage.read(result_key)
            entries = json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else []
            if not isinstance(entries, list):
                entries = [entries]
            for entry in entries:
                image_file = entry.get("image_filename", "")
                entry["image_url"] = _storage.url(prefix + image_file) if image_file else None
                entry["reference_image_url"] = reference_image_url
                all_entries.append(entry)
        except (json.JSONDecodeError, Exception):
            continue

    # Sort by analyzed_at descending, take the top N
    all_entries.sort(key=lambda e: e.get("analyzed_at", ""), reverse=True)
    items = all_entries[:limit]

    return {"items": items, "total": len(all_entries)}

