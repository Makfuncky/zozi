"""Supplier orders sub-router.

All DB work is delegated to ``services/supplier/supplier_orders_service.py``
so this router stays a thin delegator (layering: LC1/W1).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User
from utils.dependencies import require_supplier
from services.storage import storage as _storage

# AI analysis for parcel-photo matching (uses the vision provider)
ai_logger = logging.getLogger(__name__)

from services.supplier.supplier_orders_service import (
    get_order_for_parcel_verification,
    get_parcel_item_descriptions,
    get_supplier_order_for_user,
    get_supplier_order_label,
    get_user_id,
    list_orders_for_supplier,
    list_supplier_order_ids,
    mark_order_prepared_if_processing,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
def list_supplier_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    return list_orders_for_supplier(db, current_user, skip=skip, limit=limit)


@router.get("/{order_id}/label")
def get_supplier_label(
    order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return packing sheet / label data for a supplier order."""
    return get_supplier_order_label(db, current_user, order_id)


@router.post("/{order_id}/parcel-proof")
async def upload_parcel_proof(
    order_id: int,
    file: UploadFile = File(...),
    notes: str = Form(""),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Upload a packed parcel photo as proof of packaging."""
    supplier, order = get_supplier_order_for_user(db, current_user, order_id)

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are accepted")

    # Read file content
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
    proof_filename = f"proof_{timestamp}{ext}"
    proof_key = f"parcel_proofs/{order_id}/{proof_filename}"
    proof_url = _storage.save(proof_key, content, content_type=file.content_type)

    # If this is the first proof for this order, save it as the reference image
    # (used by the ORB homography engine for future parcel-photo comparisons)
    existing_refs = [k for k in _storage.list(f"parcel_proofs/{order_id}/") if k.startswith("parcel_proofs/" + str(order_id) + "/reference_")]
    is_first_proof = len(existing_refs) == 0

    if is_first_proof:
        ref_filename = f"reference_{timestamp}{ext}"
        ref_key = f"parcel_proofs/{order_id}/{ref_filename}"
        ref_url = _storage.save(ref_key, content, content_type=file.content_type)
    else:
        ref_key = existing_refs[0]
        ref_url = _storage.url(ref_key)

    # Store the proof record
    proof = {
        "order_id": order_id,
        "supplier_id": supplier.id,
        "image_url": proof_url,
        "reference_image_url": ref_url,
        "is_reference": is_first_proof,
        "notes": notes,
        "result": "pending",
        "created_at": datetime.now().isoformat(),
    }

    # Update order status to prepared if currently processing
    mark_order_prepared_if_processing(db, order)

    return {
        "status": "success",
        "message": "Parcel proof uploaded successfully",
        "reference_captured": is_first_proof,
        "proof": proof,
    }


@router.post("/{order_id}/parcel-proof/verify")
async def verify_parcel_proof(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """AI-powered verification: match the uploaded parcel photo against the packing sheet.

    Uses the vision provider to analyze the uploaded parcel proof image and
    verify that it matches the expected items from the order's packing sheet.
    Returns a match score and any discrepancies found.
    """
    user_id = get_user_id(current_user)
    order = get_order_for_parcel_verification(db, current_user, order_id)

    prefix = f"parcel_proofs/{order_id}/"
    proof_keys = sorted(
        [k for k in _storage.list(prefix) if os.path.basename(k).startswith("proof_")],
        reverse=True,
    )
    if not proof_keys:
        raise HTTPException(
            status_code=404,
            detail="No parcel proof image found for this order.",
        )

    latest_key = proof_keys[0]

    # Read the image bytes from storage
    image_bytes = _storage.read(latest_key)

    # Get packing sheet items for comparison context
    item_descriptions = get_parcel_item_descriptions(db, current_user, order_id)

    # Check for a reference image to pass to the homography engine
    reference_image_bytes: bytes | None = None
    ref_keys = sorted(
        [k for k in _storage.list(prefix) if os.path.basename(k).startswith("reference_")],
        reverse=True,
    )
    if ref_keys:
        try:
            reference_image_bytes = _storage.read(ref_keys[0])
        except Exception as exc:
            ai_logger.warning(
                "Could not read reference image %s for order %s: %s",
                ref_keys[0], order_id, exc,
            )

    # Use the parcel verification provider (multi-engine: SSIM + feature match + homography + vision AI)
    try:
        from data.providers_parcel_verification import verify_parcel_photo, verify_parcel_fast

        # Try full verification first (with vision AI); fall back to fast on failure
        try:
            result = verify_parcel_photo(
                image_bytes=image_bytes,
                item_descriptions=item_descriptions,
                reference_image_bytes=reference_image_bytes,
                run_ssim=True,
                run_feature_match=True,
                run_homography=True,
                run_vision_ai=True,
            )
        except Exception as exc:
            ai_logger.warning(
                "Full parcel verification failed for order %s, falling back to fast mode: %s",
                order_id, exc,
            )
            result = verify_parcel_fast(
                image_bytes=image_bytes,
                item_descriptions=item_descriptions,
                reference_image_bytes=reference_image_bytes,
            )

        result["image_analyzed"] = os.path.basename(latest_key)
        result["order_id"] = order_id
        result["reference_used"] = reference_image_bytes is not None
        result["supplier_id"] = user_id
        result["order_number"] = getattr(order, "order_number", f"ORD-{order_id}")

        # Persist the verification result in storage
        _persist_verification_result(prefix, result, os.path.basename(latest_key))

        # Log the verification result
        ai_logger.info(
            "Parcel verification for order %s: status=%s match_score=%s engines=%s elapsed=%ss reference=%s",
            order_id,
            result.get("status"),
            result.get("match_percentage"),
            result.get("engines_used"),
            result.get("elapsed_seconds"),
            "yes" if reference_image_bytes else "no",
        )

        return result

    except ImportError:
        ai_logger.warning("Parcel verification provider not available â€” returning basic check")
        result = {
            "status": "pending",
            "match_score": 0.0,
            "message": "AI verification unavailable. The parcel photo has been saved for manual review.",
            "total_items": len(item_descriptions),
            "matched_items": 0,
            "reference_used": reference_image_bytes is not None,
        }
        _persist_verification_result(prefix, {**result, "order_id": order_id, "supplier_id": user_id, "image_analyzed": os.path.basename(latest_key)}, os.path.basename(latest_key))
        return result
    except Exception as exc:
        ai_logger.exception("Failed to verify parcel proof for order %s", order_id)
        return {
            "status": "error",
            "match_score": 0.0,
            "message": f"Verification engine failed: {exc}",
            "total_items": len(item_descriptions),
            "matched_items": 0,
            "reference_used": reference_image_bytes is not None,
        }


def _persist_verification_result(
    prefix: str,
    result: dict,
    image_filename: str,
) -> None:
    """Save the verification result as JSON in storage."""
    import json
    key = prefix.rstrip("/") + "/_verification_result.json"
    existing: list = []
    try:
        raw = _storage.read(key)
        existing = json.loads(raw.decode("utf-8")) if isinstance(raw, (bytes, bytearray)) else []
    except Exception:
        existing = []
    if not isinstance(existing, list):
        existing = []
    entry = {
        "analyzed_at": result.get("analyzed_at", datetime.utcnow().isoformat()),
        "image_filename": image_filename,
        "order_id": result.get("order_id"),
        "order_number": result.get("order_number", ""),
        "status": result.get("status", "unknown"),
        "match_score": result.get("match_score", 0.0),
        "match_percentage": result.get("match_percentage", 0.0),
        "engines_used": result.get("engines_used", 0),
        "total_items": result.get("total_items", 0),
        "matched_items": result.get("matched_items", 0),
        "elapsed_seconds": result.get("elapsed_seconds", 0.0),
        "engine_details": result.get("engine_details", {}),
    }
    existing.insert(0, entry)
    existing = existing[:20]
    _storage.save(key, json.dumps(existing, indent=2, default=str).encode("utf-8"), content_type="application/json")


@router.post("/{order_id}/parcel-proof/reference")
async def replace_reference_image(
    order_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Replace the reference image for this order's parcel-proof homography engine.

    The old reference_* file(s) are removed and the uploaded image becomes the new
    reference.  Future calls to the verify endpoint will compare parcel photos
    against this new reference.
    """
    get_supplier_order_for_user(db, current_user, order_id)

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are accepted")

    # Remove all existing reference_* files
    prefix = f"parcel_proofs/{order_id}/"
    for old_ref in _storage.list(prefix):
        if os.path.basename(old_ref).startswith("reference_"):
            try:
                _storage.delete(old_ref)
            except Exception:
                pass

    # Read and save the new reference
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
    ref_filename = f"reference_{timestamp}{ext}"
    ref_key = f"parcel_proofs/{order_id}/{ref_filename}"
    ref_url = _storage.save(ref_key, content, content_type=file.content_type)

    return {
        "status": "success",
        "message": "Reference image replaced successfully. Future verification runs will use this image for homography comparison.",
        "reference_image_url": ref_url,
        "filename": ref_filename,
    }


@router.get("/{order_id}/parcel-proof/reference-image")
def get_reference_image(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the latest reference image for this order.

    Returns the image file directly (JPEG/PNG/WebP) or 404 if no reference
    has been set yet.
    """
    get_supplier_order_for_user(db, current_user, order_id)

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
    # Collect all verification results across this supplier's orders
    all_entries: list[dict] = []
    supplier_order_ids = list_supplier_order_ids(db, current_user)

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
