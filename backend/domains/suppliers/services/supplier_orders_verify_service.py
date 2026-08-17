"""Supplier orders sub-router.

DB reads/writes live in ``services.supplier.supplier_order_service``; this
router keeps request parsing, file handling, storage and parcel-AI logic.
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional
from fastapi import Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from db.database import get_db
from _legacy.models import Order, OrderItem, SupplierProfile, User
from utils.dependencies import require_supplier
from services.common.storage import storage as _storage
from services.supplier.supplier_order_service import get_supplier_order, get_supplier_order_for_verify, get_supplier_order_items, get_supplier_order_items_for_verify, get_supplier_profile_by_user_id, list_supplier_order_ids, list_supplier_orders, mark_order_prepared_if_processing, resolve_shipment_info
ai_logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

def _get_user_id(current_user: User | dict) -> int:
    """`require_supplier` may return a dict or a User ORM model.
    This helper normalises both to an int ID."""
    if isinstance(current_user, dict):
        uid = current_user.get('id') or current_user.get('user_id')
        if not uid:
            raise HTTPException(status_code=401, detail='Invalid user session: missing user ID')
        return int(uid)
    return current_user.id

async def replace_reference_image(order_id: int, file: UploadFile=File(...), current_user: User=Depends(require_supplier), db: Session=Depends(get_db)):
    """Replace the reference image for this order's parcel-proof homography engine."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)
    allowed_types = {'image/jpeg', 'image/png', 'image/webp', 'image/jpg'}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail='Only JPEG, PNG, and WebP images are accepted')
    prefix = f'parcel_proofs/{order_id}/'
    for old_ref in _storage.list(prefix):
        if os.path.basename(old_ref).startswith('reference_'):
            try:
                _storage.delete(old_ref)
            except Exception:
                pass
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='File size exceeds 10 MB limit')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(file.filename or '.jpg')[1] or '.jpg'
    ref_filename = f'reference_{timestamp}{ext}'
    ref_key = f'parcel_proofs/{order_id}/{ref_filename}'
    ref_url = _storage.save(ref_key, content, content_type=file.content_type)
    return {'status': 'success', 'message': 'Reference image replaced successfully. Future verification runs will use this image for homography comparison.', 'reference_image_url': ref_url, 'filename': ref_filename}

async def upload_parcel_proof(order_id: int, file: UploadFile=File(...), notes: str=Form(''), current_user: User=Depends(require_supplier), db: Session=Depends(get_db)):
    """Upload a packed parcel photo as proof of packaging."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)
    allowed_types = {'image/jpeg', 'image/png', 'image/webp', 'image/jpg'}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail='Only JPEG, PNG, and WebP images are accepted')
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='File size exceeds 10 MB limit')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(file.filename or '.jpg')[1] or '.jpg'
    proof_filename = f'proof_{timestamp}{ext}'
    proof_key = f'parcel_proofs/{order_id}/{proof_filename}'
    proof_url = _storage.save(proof_key, content, content_type=file.content_type)
    existing_refs = [k for k in _storage.list(f'parcel_proofs/{order_id}/') if k.startswith('parcel_proofs/' + str(order_id) + '/reference_')]
    is_first_proof = len(existing_refs) == 0
    if is_first_proof:
        ref_filename = f'reference_{timestamp}{ext}'
        ref_key = f'parcel_proofs/{order_id}/{ref_filename}'
        ref_url = _storage.save(ref_key, content, content_type=file.content_type)
    else:
        ref_key = existing_refs[0]
        ref_url = _storage.url(ref_key)
    proof = {'order_id': order_id, 'supplier_id': supplier.id, 'image_url': proof_url, 'reference_image_url': ref_url, 'is_reference': is_first_proof, 'notes': notes, 'result': 'pending', 'created_at': datetime.now().isoformat()}
    mark_order_prepared_if_processing(order, db)
    return {'status': 'success', 'message': 'Parcel proof uploaded successfully', 'reference_captured': is_first_proof, 'proof': proof}

async def verify_parcel_proof(order_id: int, current_user: User=Depends(require_supplier), db: Session=Depends(get_db)):
    """AI-powered verification: match the uploaded parcel photo against the packing sheet."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order_for_verify(db, order_id, user_id)
    prefix = f'parcel_proofs/{order_id}/'
    proof_keys = sorted([k for k in _storage.list(prefix) if os.path.basename(k).startswith('proof_')], reverse=True)
    if not proof_keys:
        raise HTTPException(status_code=404, detail='No parcel proof image found for this order.')
    latest_key = proof_keys[0]
    image_bytes = _storage.read(latest_key)
    items = get_supplier_order_items_for_verify(db, order_id, user_id)
    item_descriptions = [f'{item.product_name} x{item.quantity}' for item in items]
    reference_image_bytes: bytes | None = None
    ref_keys = sorted([k for k in _storage.list(prefix) if os.path.basename(k).startswith('reference_')], reverse=True)
    if ref_keys:
        try:
            reference_image_bytes = _storage.read(ref_keys[0])
        except Exception as exc:
            ai_logger.warning('Could not read reference image %s for order %s: %s', ref_keys[0], order_id, exc)
    try:
        from providers.image.parcel_verification import verify_parcel_photo, verify_parcel_fast
        try:
            result = verify_parcel_photo(image_bytes=image_bytes, item_descriptions=item_descriptions, reference_image_bytes=reference_image_bytes, run_ssim=True, run_feature_match=True, run_homography=True, run_vision_ai=True)
        except Exception as exc:
            ai_logger.warning('Full parcel verification failed for order %s, falling back to fast mode: %s', order_id, exc)
            result = verify_parcel_fast(image_bytes=image_bytes, item_descriptions=item_descriptions, reference_image_bytes=reference_image_bytes)
        result['image_analyzed'] = os.path.basename(latest_key)
        result['order_id'] = order_id
        result['reference_used'] = reference_image_bytes is not None
        result['supplier_id'] = user_id
        result['order_number'] = getattr(order, 'order_number', f'ORD-{order_id}')
        _persist_verification_result(prefix, result, os.path.basename(latest_key))
        ai_logger.info('Parcel verification for order %s: status=%s match_score=%s engines=%s elapsed=%ss reference=%s', order_id, result.get('status'), result.get('match_percentage'), result.get('engines_used'), result.get('elapsed_seconds'), 'yes' if reference_image_bytes else 'no')
        return result
    except ImportError:
        ai_logger.warning('Parcel verification provider not available — returning basic check')
        result = {'status': 'pending', 'match_score': 0.0, 'message': 'AI verification unavailable. The parcel photo has been saved for manual review.', 'total_items': len(item_descriptions), 'matched_items': 0, 'reference_used': reference_image_bytes is not None}
        _persist_verification_result(prefix, {**result, 'order_id': order_id, 'supplier_id': user_id, 'image_analyzed': os.path.basename(latest_key)}, os.path.basename(latest_key))
        return result
    except Exception as exc:
        ai_logger.exception('Failed to verify parcel proof for order %s', order_id)
        return {'status': 'error', 'match_score': 0.0, 'message': f'Verification engine failed: {exc}', 'total_items': len(item_descriptions), 'matched_items': 0, 'reference_used': reference_image_bytes is not None}

def _persist_verification_result(prefix: str, result: dict, image_filename: str) -> None:
    """Save the verification result as JSON in storage."""
    key = prefix.rstrip('/') + '/_verification_result.json'
    existing: list = []
    try:
        raw = _storage.read(key)
        existing = json.loads(raw.decode('utf-8')) if isinstance(raw, (bytes, bytearray)) else []
    except Exception:
        existing = []
    if not isinstance(existing, list):
        existing = []
    entry = {'analyzed_at': result.get('analyzed_at', datetime.utcnow().isoformat()), 'image_filename': image_filename, 'order_id': result.get('order_id'), 'order_number': result.get('order_number', ''), 'status': result.get('status', 'unknown'), 'match_score': result.get('match_score', 0.0), 'match_percentage': result.get('match_percentage', 0.0), 'engines_used': result.get('engines_used', 0), 'total_items': result.get('total_items', 0), 'matched_items': result.get('matched_items', 0), 'elapsed_seconds': result.get('elapsed_seconds', 0.0), 'engine_details': result.get('engine_details', {})}
    existing.insert(0, entry)
    existing = existing[:20]
    _storage.save(key, json.dumps(existing, indent=2, default=str).encode('utf-8'), content_type='application/json')
