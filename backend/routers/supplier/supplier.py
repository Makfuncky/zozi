"""
Supplier Router — route declarations only (HTTP layer).
All business logic lives in controllers/supplier_controller.py.
"""
from typing import Annotated, Any, List, Optional, cast
from fastapi import APIRouter, Body, Depends, UploadFile, File, Form, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime

from data.db import get_db
from data.schemas import ListPage, Product as ProductSchema, SupplierReturnReviewUpdate
from data.controllers_admin_controller import require_roles
from controllers import commission_controller
import controllers.supplier_controller as ctrl
import controllers.returns_controller as returns_ctrl
import controllers.disputes_controller as disputes_ctrl
from utils.pagination import cursor_paginate_desc, build_cursor_pagination_payload

router = APIRouter()


@router.get("/upload/history")
async def get_upload_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """
    Return the supplier's product upload history with status tracking.

    Returns products ordered by creation date (newest first) with
    upload status inferred from the product state (completed=active,
    processing=inactive + has images). Designed to feed the
    Real-Time Upload Dashboard on the frontend.

    Returns:
      {
        "items": [{ id, name, status, progress, started_at, completed_at,
                     bg_strategy, ai_result: { name, category, price, variants_count },
                     image_thumbnail, error }],
        "total": int
      }
    """
    products_data = ctrl.get_supplier_products(current_user, db, limit=limit, offset=offset)
    items = products_data.get("items", products_data.get("data", [])) if isinstance(products_data, dict) else (products_data or [])
    total = products_data.get("total", len(items)) if isinstance(products_data, dict) else len(items)

    history = []
    for p in items:
        created = getattr(p, "created_at", None) or getattr(p, "updated_at", None) or ""
        is_active = getattr(p, "is_active", True)
        variants = getattr(p, "variants", None) or getattr(p, "variants_json", None) or []
        if isinstance(variants, str):
            import json
            try:
                variants = json.loads(variants)
            except Exception:
                variants = []
        variants_count = len(variants) if isinstance(variants, (list, dict)) else 0

        record = {
            "id": str(getattr(p, "id", 0)),
            "filename": getattr(p, "name", "Product") or "Product",
            "status": "completed" if is_active else "processing_bg",
            "progress": 100 if is_active else 65,
            "started_at": str(created) if created else "",
            "completed_at": str(created) if created else "",
            "image_thumbnail": getattr(p, "image_url", None) or getattr(p, "images", [None] * 1)[0] or None,
            "bg_strategy": getattr(p, "bg_preset", None),
            "ai_result": {
                "name": getattr(p, "name", ""),
                "category": getattr(p, "category", ""),
                "price": getattr(p, "price", 0) or 0,
                "variants_count": variants_count,
            },
            "error": None,
        }
        history.append(record)

    return {"items": history, "total": total}


SupplierOrAdminUser = Annotated[dict, Depends(require_roles("supplier", "admin"))]
SupplierAdminOrSubAdminUser = Annotated[dict, Depends(require_roles("supplier", "admin", "sub_admin"))]


@router.get("/commission/policy")
def get_supplier_commission_policy(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return commission_controller.get_supplier_policy_snapshot(current_user, db)


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=ListPage[dict])
def get_orders(
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_orders(current_user, db, limit=limit, offset=offset, search=search, status=status)

@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_supplier_order_status(order_id, status_update, current_user, db)

@router.put("/orders/{order_id}")
def update_order_status_alias(
    order_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Backward-compatible alias used by older web clients."""
    return ctrl.update_supplier_order_status(order_id, status_update, current_user, db)


@router.get("/orders/{order_id}")
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_order_detail(order_id, current_user, db)


@router.get("/orders/{order_id}/label")
def get_order_label_payload(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_label_payload(order_id, current_user, db)

@router.post("/orders/{order_id}/parcel-proof", status_code=201)
def upload_parcel_proof(
    order_id: int,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.upload_supplier_parcel_proof(order_id, file, notes, current_user, db)


@router.get("/returns", response_model=ListPage[dict])
def list_supplier_returns(
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return returns_ctrl.list_supplier_return_requests(current_user, db, limit=limit, offset=offset)

@router.put("/returns/{return_id}")
def update_supplier_return(
    return_id: int,
    payload: SupplierReturnReviewUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return returns_ctrl.update_supplier_return_request(return_id, payload, current_user, db)


@router.get("/notification-preferences")
def get_supplier_notification_preferences(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return disputes_ctrl.get_supplier_notification_preferences(current_user, db)

@router.put("/notification-preferences")
def update_supplier_notification_preferences(
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return disputes_ctrl.update_supplier_notification_preferences(payload, current_user, db)


@router.get("/disputes")
def list_supplier_disputes(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return disputes_ctrl.list_supplier_disputes(
        current_user=current_user,
        db=db,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )

@router.post("/disputes", status_code=201)
def create_supplier_dispute(
    payload: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return disputes_ctrl.create_supplier_dispute(payload, current_user, db)


@router.get("/disputes/{dispute_id}")
def get_supplier_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return disputes_ctrl.get_supplier_dispute(dispute_id, current_user, db)


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/products/export")
def export_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return ctrl.export_products_csv(current_user, db)

@router.post("/products/import")
async def import_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await ctrl.import_products_csv(file, current_user, db)

@router.post("/products/bulk")
def bulk_operation(
    operation: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return ctrl.execute_bulk_operation(operation, current_user, db)

@router.post("/products/bulk-upload")
async def bulk_upload_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    products_json: str = Form(...),
    use_ai: bool = Form(False),
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """Bulk-upload multiple products at once with optional AI enrichment."""
    return await ctrl.bulk_upload_products(
        products_json=products_json,
        images=images,
        use_ai=use_ai,
        current_user=current_user,
        db=db,
    )


@router.get("/products", response_model=ListPage[ProductSchema])
def get_products(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return ctrl.get_supplier_products(current_user, db, limit=limit, offset=offset)


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return ctrl.get_supplier_product(product_id, current_user, db)

@router.post("/process-image")
async def process_image_ai(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
    generate_angles: bool = Form(True),
):
    """Enqueue AI image processing as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job
    removes the background and optionally generates novel-angle views.
    """
    import uuid
    from utils.background_jobs import enqueue_ml_job
    from services.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_process_image() -> dict:
        from controllers.supplier_controller import process_product_image
        from io import BytesIO
        from fastapi import UploadFile
        import asyncio

        upload = UploadFile(filename=image.filename or "image.jpg", file=BytesIO(raw))
        result = asyncio.run(process_product_image(
            image=upload,
            generate_angles=generate_angles,
            current_user=current_user,
        ))
        return result

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_process_image,
        metadata={"generate_angles": generate_angles},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}

@router.post("/upload")
async def upload_product(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock_quantity: int = Form(...),
    category: str = Form(...),
    subcategory: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    sizes: Optional[str] = Form(None),         # JSON array string
    materials: Optional[str] = Form(None),
    visibility_regions: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    compare_price: Optional[float] = Form(None),
    discount_starts_at: Optional[datetime] = Form(None),
    discount_ends_at: Optional[datetime] = Form(None),
    return_window_days: Optional[int] = Form(None),
    is_active: bool = Form(True),
    video_url_link: Optional[str] = Form(None),
    variants_json: Optional[str] = Form(None),
    image_url_link: Optional[str] = Form(None),  # Web URL as alternative to file upload
    video: UploadFile = File(None),
    image: UploadFile = File(None),
    additional_images: List[UploadFile] = File(default=[]),
    additional_image_1: UploadFile = File(None),
    additional_image_2: UploadFile = File(None),
    additional_image_3: UploadFile = File(None),
    # Extra image web URLs as alternative to file upload
    extra_image_urls: Optional[List[str]] = Form(default=None),
    extra_url_1: Optional[str] = Form(None),
    extra_url_2: Optional[str] = Form(None),
    extra_url_3: Optional[str] = Form(None),
    # Image processing tools (free, open-source)
    process_magic_erase: bool = Form(False),
    process_smart_crop: bool = Form(False),
    process_rotate: bool = Form(False),
    process_auto_light: bool = Form(False),
    process_upscale: bool = Form(False),
    process_white_balance: bool = Form(False),
    process_denoise: bool = Form(False),
    process_sharpen: bool = Form(False),
    process_compress: bool = Form(False),
    process_webp_convert: bool = Form(False),
    process_color_enhance: bool = Form(False),
    process_auto_levels: bool = Form(False),
    bg_preset: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Create a product with a main image and up to 20 additional gallery media items (file or URL)."""
    extra_urls = [u for u in ((extra_image_urls or []) + [extra_url_1, extra_url_2, extra_url_3]) if u and u.strip()]
    combined_additional_images = [f for f in additional_images if f and f.filename] + [
        f for f in [additional_image_1, additional_image_2, additional_image_3] if f and f.filename
    ]
    return await ctrl.create_supplier_product_upload(
        name=name, description=description, price=price,
        stock_quantity=stock_quantity, category=category, subcategory=subcategory, color=color,
        brand=brand, tags=tags, sizes=sizes, materials=materials,
        visibility_regions=visibility_regions,
        weight=weight, dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        is_active=is_active,
        video_url_link=video_url_link,
        variants_payload=variants_json,
        video=video,
        image_url_link=image_url_link,
        image=image,
        additional_images=combined_additional_images,
        extra_image_urls=extra_urls,
        current_user=current_user, db=db,
        image_tools={
            "magic_erase": process_magic_erase,
            "smart_crop": process_smart_crop,
            "rotate": process_rotate,
            "auto_light": process_auto_light,
            "upscale": process_upscale,
            "white_balance": process_white_balance,
            "denoise": process_denoise,
            "sharpen": process_sharpen,
            "compress": process_compress,
            "webp_convert": process_webp_convert,
            "color_enhance": process_color_enhance,
            "auto_levels": process_auto_levels,
        },
        bg_preset=bg_preset,
    )

@router.post("/products")
async def create_product(
    request: Request,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    name: Optional[str] = Form(None),
    description: str = Form(""),
    price: Optional[float] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    category: Optional[str] = Form(None),
    subcategory: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    is_active: bool = Form(True),
    tags: Optional[str] = Form(None),
    sizes: Optional[str] = Form(None),
    materials: Optional[str] = Form(None),
    visibility_regions: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    compare_price: Optional[float] = Form(None),
    discount_starts_at: Optional[datetime] = Form(None),
    discount_ends_at: Optional[datetime] = Form(None),
    return_window_days: Optional[int] = Form(None),
    video_url: Optional[str] = Form(None),
    variants_json: Optional[str] = Form(None),
    variant_axes_json: Optional[str] = Form(None),
    # Multi-country publishing + logistics (Step 8)
    countries: Optional[str] = Form(None),
    weight_kg: Optional[float] = Form(None),
    saso_cert: Optional[str] = Form(None),
    halal_compliance: bool = Form(False),
    # GCC localization (Step 6)
    name_ar: Optional[str] = Form(None),
    description_ar: Optional[str] = Form(None),
    image: UploadFile = File(None),
    additional_images: List[UploadFile] = File(default=[]),
    video: UploadFile = File(None),
    # Image processing tools (free, open-source)
    process_magic_erase: bool = Form(False),
    process_smart_crop: bool = Form(False),
    process_rotate: bool = Form(False),
    process_auto_light: bool = Form(False),
    process_upscale: bool = Form(False),
    process_white_balance: bool = Form(False),
    process_denoise: bool = Form(False),
    process_sharpen: bool = Form(False),
    process_compress: bool = Form(False),
    process_webp_convert: bool = Form(False),
    process_color_enhance: bool = Form(False),
    process_auto_levels: bool = Form(False),
    bg_preset: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if "application/json" in request.headers.get("content-type", ""):
        payload = cast(dict[str, Any], await request.json())
        name = payload.get("name")
        description = payload.get("description") or ""
        price = payload.get("price")
        stock_quantity = payload.get("stock_quantity", payload.get("stock"))
        category = payload.get("category")
        subcategory = payload.get("subcategory", payload.get("sub_category"))
        brand = payload.get("brand")
        color = payload.get("color")
        is_active = payload.get("is_active", True)
        tags = payload.get("tags")
        sizes = payload.get("sizes")
        materials = payload.get("materials")
        visibility_regions = payload.get("visibility_regions")
        weight = payload.get("weight")
        dimensions = payload.get("dimensions")
        compare_price = payload.get("compare_price", payload.get("discount_price"))
        discount_starts_at = ctrl._parse_optional_datetime(payload.get("discount_starts_at"))
        discount_ends_at = ctrl._parse_optional_datetime(payload.get("discount_ends_at"))
        return_window_days = payload.get("return_window_days")
        video_url = payload.get("video_url")
        variants_json = payload.get("variants")
        variant_axes_json = payload.get("variant_axes") or payload.get("variant_axes_json")
        countries = payload.get("countries")
        weight_kg = payload.get("weight_kg")
        saso_cert = payload.get("saso_cert")
        halal_compliance = payload.get("halal_compliance", False)
        name_ar = payload.get("name_ar")
        description_ar = payload.get("description_ar")

    if name is None or price is None or stock_quantity is None or category is None:
        raise HTTPException(status_code=422, detail="name, price, stock_quantity and category are required")

    # Step 8 — multi-country publishing + auto logistics tier.
    if countries and not visibility_regions:
        visibility_regions = countries
    if weight_kg is not None and weight is None:
        weight = weight_kg
    from services.shipping_tier import resolve_shipping_tier
    shipping_tier = resolve_shipping_tier(weight_kg=weight, dimensions=dimensions)

    from services.content_service import moderate_content
    moderation = moderate_content(text=f"{name or ''} {description or ''}", category=category or "")

    extra_attributes = {
        "shipping_tier": shipping_tier,
        "moderation": moderation,
    }
    if saso_cert:
        extra_attributes["saso_cert"] = saso_cert
    if halal_compliance:
        extra_attributes["halal_compliance"] = True
    if name_ar:
        extra_attributes["name_ar"] = name_ar
    if description_ar:
        extra_attributes["description_ar"] = description_ar

    return ctrl.create_supplier_product(
        name=name, description=description, price=price,
        stock_quantity=stock_quantity, category=category, subcategory=subcategory, is_active=is_active,
        brand=brand,
        color=color,
        tags=tags, sizes=sizes, materials=materials, visibility_regions=visibility_regions, weight=weight,
        dimensions=dimensions, compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        video_url=video_url,
        video=video if (video is not None and getattr(video, "filename", None)) else None,
        variants_payload=variants_json,
        variant_axes=variant_axes_json,
        extra_attributes=extra_attributes,
        image=image, additional_images=[file for file in additional_images if file and file.filename], current_user=current_user, db=db,
        image_tools={
            "magic_erase": process_magic_erase,
            "smart_crop": process_smart_crop,
            "rotate": process_rotate,
            "auto_light": process_auto_light,
            "upscale": process_upscale,
            "white_balance": process_white_balance,
            "denoise": process_denoise,
            "sharpen": process_sharpen,
            "compress": process_compress,
            "webp_convert": process_webp_convert,
            "color_enhance": process_color_enhance,
            "auto_levels": process_auto_levels,
        },
        bg_preset=bg_preset,
    )


@router.post("/upload/analyze-async")
async def analyze_async(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
):
    """
    Enqueue BG removal + AI product analysis as an ML background job and
    return immediately with a ``job_id`` the frontend polls at
    ``GET /supplier/upload/jobs/{job_id}``.

    This prevents ML inference from blocking HTTP workers — under an upload
    burst the job is queued and processed by the dedicated ML worker pool.
    """
    import uuid
    from utils.background_jobs import enqueue_ml_job
    from services.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    # Save the image bytes to storage so the ML worker can read them
    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    image_url = _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_analysis() -> dict:
        import asyncio
        from data.services_bg_removal_service import remove_background
        from services.ai_variant_config import analyze_product_image
        from services.storage import storage as _store

        bg_result = remove_background(raw, strategy="general", fast_mode=True)
        ai_result = asyncio.run(analyze_product_image(
            raw, filename=image.filename or "", generate_copy=True
        ))

        bg_key = f"supplier_uploads/{uuid.uuid4().hex}_nobg.png"
        bg_url = _store.save(bg_key, bg_result, content_type="image/png")

        return {
            "bg_removed_url": bg_url,
            "product_name": ai_result.get("product_name_hint", ""),
            "suggested_category": ai_result.get("suggested_category", ""),
            "suggested_subcategory": ai_result.get("suggested_subcategory", ""),
            "suggested_brand": ai_result.get("suggested_brand", ""),
            "product_description": ai_result.get("product_description", ""),
            "suggested_tags": ai_result.get("suggested_tags", []),
            "detected_colors": ai_result.get("detected_attributes", {}).get("color", []),
            "detected_materials": ai_result.get("detected_attributes", {}).get("material", []),
            "variant_options": ai_result.get("variant_options", {}),
            "suggested_variants": ai_result.get("suggested_variants", []),
            "price_suggestion": ai_result.get("ai_suggested_price", 0),
            "price_min": ai_result.get("price_min", 0),
            "price_max": ai_result.get("price_max", 0),
            "stock_hints": ai_result.get("stock_hints", {}),
            "photo_analysis": ai_result.get("photo_analysis", {}),
            "source": ai_result.get("source", "heuristic_fallback"),
        }

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_analysis,
        metadata={"image_key": image_key},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}


@router.get("/upload/jobs/{job_id}")
async def get_async_job_result(job_id: str):
    """Poll the result of an async analysis job."""
    from utils.background_jobs import get_job

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    resp: dict[str, Any] = {
        "job_id": job["id"],
        "status": job["status"],
        "kind": job["kind"],
    }
    if job.get("result"):
        resp["result"] = job["result"]
    if job.get("error"):
        resp["error"] = job["error"]
    return resp


@router.post("/upload/remove-background")
async def remove_background(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
    preset: str = Form("general"),
    model: str = Form(""),
    fast_mode: bool = Form(False),
):
    """Enqueue background removal as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. This keeps
    rembg inference off the HTTP worker so upload bursts can't freeze the API.
    """
    import uuid
    from utils.background_jobs import enqueue_ml_job
    from services.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_remove_background() -> dict:
        from data.services_bg_removal_service import (
            remove_background_model,
            AVAILABLE_MODELS,
            VALID_STRATEGIES,
        )
        from services.storage import storage as _store

        if model and model in AVAILABLE_MODELS:
            processed = remove_background_model(raw, model, fast_mode=fast_mode)
        else:
            preset_effective = preset if preset in VALID_STRATEGIES else "general"
            from data.services_bg_removal_service import remove_background
            processed = remove_background(raw, strategy=preset_effective, fast_mode=fast_mode)

        out_key = f"supplier_uploads/{uuid.uuid4().hex}_nobg.png"
        out_url = _store.save(out_key, processed, content_type="image/png")
        return {"bg_removed_url": out_url, "bytes_len": len(processed)}

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_remove_background,
        metadata={"preset": preset, "model": model, "fast_mode": fast_mode},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}

@router.post("/upload/ai-analyze")
async def ai_analyze(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
    generate_copy: bool = Form(True),
):
    """
    AI-assisted product analysis: detect category + suggest variants.

    Returns an **instant** heuristic result (category, variants, tags, a
    baseline EN description). Because the full EN/AR marketing copy is
    CPU-bound (~60-90s via Ollama), it is generated in a background job when
    ``generate_copy`` is true; the response includes a ``copy_job_id`` the
    frontend polls at ``GET /supplier/upload/ai-copy/{job_id}``. Never 500s.
    """
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")
    from services.ai_variant_config import analyze_product_image
    # Instant, photo-derived heuristic result (colours from the actual pixels,
    # category/name from the filename + config). Real vision understanding runs
    # in the background job below and the frontend polls it to refine the form.
    result = await analyze_product_image(raw, filename=image.filename or "", generate_copy=False)
    if generate_copy:
        from services.ai_copy_jobs import enqueue_copy_job
        result["copy_job_id"] = enqueue_copy_job(raw, filename=image.filename or "")
    return result


@router.post("/upload/voice-transcribe")
async def voice_transcribe(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    audio: UploadFile = File(...),
    language: str = Form("en"),
):
    """Transcribe voice recording using OpenAI Whisper.

    Accepts an audio file (webm, wav, mp3, ogg, m4a) and returns the
    transcribed text. Falls back gracefully if the API key is missing.
    """
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio file")
    from services.video_conferencing import VideoConferenceRoom
    vcr = VideoConferenceRoom()
    transcript = await vcr._transcribe_audio(raw, source_language=language)
    return {"transcript": transcript, "detected_language": language}


@router.post("/upload/nlp-extract")
async def nlp_extract(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    transcript: str = Form(...),
):
    """Extract structured product data from a voice transcript using NLP.

    Accepts a natural-language product description (e.g. "A T-shirt, 4 colors:
    blue, yellow, black, white, having print 'I love Oman'") and returns
    structured fields: product name, category, colors, variants, tags,
    description, fabric, print text, stock hints.

    Uses Ollama (phi3:mini) for extraction with heuristic fallbacks.
    Never 500s.
    """
    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Empty transcript")
    import json, re

    # Try structured extraction via direct Ollama call
    from services.ai_variant_config import _ollama_chat, _OLLAMA_TEXT_MODEL, _extract_json

    canonical_list = "Clothing, Electronics, Home & Kitchen, Beauty, Sports, Books, Toys, Automotive, Grocery, Health, Jewelry, Office, Pet Supplies, Shoes, Bags, Furniture"
    en_prompt = (
        "You are a product data extraction assistant for an Oman/GCC marketplace.\n"
        f"Given the voice transcript below, extract structured product data.\n"
        f"Choose the category from exactly this list: {canonical_list}.\n"
        "TRANSCRIPT: " + transcript + "\n\n"
        "Reply ONLY with valid JSON (double quotes, no markdown, no commentary).\n"
        "{\n"
        '  "product_name": "best guess product name (REQUIRED)",\n'
        '  "category": "one from the list or null",\n'
        '  "subcategory": "subcategory or null",\n'
        '  "colors": ["extracted colors"],\n'
        '  "fabric": "fabric type or null",\n'
        '  "print_text": "any print/pattern text or null",\n'
        '  "description": "2-3 sentence auto-generated product description",\n'
        '  "suggested_tags": ["8-12 lowercase SEO tags"],\n'
        '  "variants": {"color": ["Blue","Black"], "size": ["S","M","L"]},\n'
        '  "stock_hints": {"Blue": {"S": 0, "M": 0, "L": 0}},\n'
        '  "quantity": null,\n'
        '  "price": null\n'
        "}"
    )
    try:
        content = await _ollama_chat(_OLLAMA_TEXT_MODEL, en_prompt, num_predict=400, temperature=0.2)
    except Exception:
        content = None

    parsed = _extract_json(content) if content else None
    if parsed and parsed.get("product_name"):
        return parsed

    # Fallback: heuristic regex extraction
    txt = transcript.lower()
    colors_found = [c for c in ["red","blue","green","yellow","black","white",
        "purple","orange","pink","brown","gray","grey","navy","gold",
        "silver","beige","cream","maroon","teal","lavender"]
        if c in txt]

    # Detect sizes mentioned
    sizes_found = [s for s in ["s","m","l","xl","xxl","xs","small","medium","large","extra large","x-large","xx-large"]
        if re.search(r'\b' + s + r'\b', txt)]

    return {
        "product_name": transcript[:80].strip() if len(transcript) > 5 else "Unknown Product",
        "category": None,
        "subcategory": None,
        "colors": colors_found or ["Default"],
        "fabric": None,
        "print_text": None,
        "description": transcript,
        "suggested_tags": [t for t in re.findall(r'\b[a-z]{4,}\b', txt)][:10],
        "variants": {"Color": colors_found, "Size": sizes_found} if colors_found and sizes_found
                    else ({"Color": colors_found} if colors_found else {}),
        "stock_hints": {},
        "quantity": None,
        "price": None,
    }


@router.get("/upload/ai-copy/{job_id}")
async def ai_copy_status(
    job_id: str,
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Poll the status/result of a background AI-copy generation job.

    Returns ``{status: pending|done|error, result?}``. ``result`` carries the
    full EN/AR marketing copy once ``status == "done"``.
    """
    from services.ai_copy_jobs import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown or expired copy job")
    return job


@router.post("/upload/translate")
async def translate_text(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    text: str = Form(...),
    target: str = Form("ar"),
):
    """Step 6 — EN→AR translation for product titles/descriptions (best-effort)."""
    from services.content_service import translate_en_to_ar
    translated = await translate_en_to_ar(text)
    return {"translated_text": translated, "target": target}


@router.get("/upload/variant-axes")
async def get_variant_axes(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    category: str = Query("Clothing", description="Picker category name e.g. Clothing, Electronics"),
    subcategory: str = Query(None, description="Optional subcategory"),
):
    """
    Return applicable variant axes + default options for a product category.

    Used by the frontend to render correct quantity-modals for any product type:
    - Apparel: color × size, sleeve_length, fit, etc.
    - Electronics: storage × RAM, processor, screen_size, etc.
    - Beauty: volume × scent, etc.
    - Jewelry: karat × plating, chain_length, ring_size, etc.

    Reads from zozi_variant_config.json at runtime.
    """
    from services.variant_config_service import get_axes_for_category
    return {
        "category": category,
        "axes": get_axes_for_category(category, subcategory=subcategory),
    }


@router.post("/upload/moderate")
async def moderate_text(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    text: str = Form(""),
    category: str = Form(""),
):
    """Step 6 — GCC content moderation for text (alcohol/pork/gambling/tobacco)."""
    from services.content_service import moderate_content
    return moderate_content(text=text, category=category)


@router.post("/upload/generate-angles")
async def generate_angles(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
):
    """Enqueue AI angle generation as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job
    removes the background and creates novel-angle product views.
    """
    import uuid
    from utils.background_jobs import enqueue_ml_job
    from services.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_generate_angles() -> dict:
        from controllers.supplier_controller import process_product_image
        from io import BytesIO
        from fastapi import UploadFile
        import asyncio

        upload = UploadFile(filename=image.filename or "image.jpg", file=BytesIO(raw))
        result = asyncio.run(process_product_image(
            image=upload,
            generate_angles=True,
            current_user=current_user,
        ))
        return result

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_generate_angles,
        metadata={"generate_angles": True},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}

@router.post("/upload/process-tools")
async def process_tools(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(...),
    process_magic_erase: bool = Form(False),
    process_smart_crop: bool = Form(False),
    process_rotate: bool = Form(False),
    process_auto_light: bool = Form(False),
    process_upscale: bool = Form(False),
    process_white_balance: bool = Form(False),
    process_denoise: bool = Form(False),
    process_sharpen: bool = Form(False),
    process_compress: bool = Form(False),
    process_webp_convert: bool = Form(False),
    process_color_enhance: bool = Form(False),
    process_auto_levels: bool = Form(False),
    bg_preset: str = Form(""),
):
    """
    Apply one or more image processing tools (magic_erase, smart_crop, rotate,
    auto_light, upscale, white_balance, denoise, sharpen, compress, webp_convert,
    color_enhance, auto_levels) to the uploaded image and return the result.

    Accepts an optional ``bg_preset`` for background removal before other tools.
    Returns the processed image bytes with the same MIME type as the input.
    Never 500s — returns the original image if all tools fail.
    """
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")
    from controllers.supplier_controller import _process_image_with_tools
    tools = {
        "magic_erase": process_magic_erase,
        "smart_crop": process_smart_crop,
        "rotate": process_rotate,
        "auto_light": process_auto_light,
        "upscale": process_upscale,
        "white_balance": process_white_balance,
        "denoise": process_denoise,
        "sharpen": process_sharpen,
        "compress": process_compress,
        "webp_convert": process_webp_convert,
        "color_enhance": process_color_enhance,
        "auto_levels": process_auto_levels,
    }
    bg = bg_preset.strip() or None
    try:
        processed = _process_image_with_tools(raw, tools, bg_preset=bg)
    except Exception:
        processed = raw
    content_type = image.content_type or "image/png"
    return Response(content=processed, media_type=content_type)


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    image: UploadFile = File(None),
    additional_images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    # Accept JSON payloads and form submissions (e.g., `data=` in test clients).
    product_update: dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        product_update = cast(dict[str, Any], await request.json())
    else:
        form = await request.form()
        product_update = cast(dict[str, Any], dict(form))

    compare_price_value = ctrl._UNSET
    if "compare_price" in product_update or "discount_price" in product_update:
        compare_price_value = product_update.get("compare_price", product_update.get("discount_price"))

    discount_starts_at_value = ctrl._UNSET
    if "discount_starts_at" in product_update:
        discount_starts_at_value = ctrl._parse_optional_datetime(product_update.get("discount_starts_at"))

    discount_ends_at_value = ctrl._UNSET
    if "discount_ends_at" in product_update:
        discount_ends_at_value = ctrl._parse_optional_datetime(product_update.get("discount_ends_at"))

    return_window_days_value = ctrl._UNSET
    if "return_window_days" in product_update:
        return_window_days_value = product_update.get("return_window_days")

    video_url_value = ctrl._UNSET
    if "video_url" in product_update:
        video_url_value = product_update.get("video_url")

    variants_payload_value = ctrl._UNSET
    if "variants" in product_update or "variants_json" in product_update:
        variants_payload_value = product_update.get("variants", product_update.get("variants_json"))

    visibility_regions_value = product_update.get("visibility_regions", ctrl._UNSET)

    is_new_value = product_update.get("is_new", ctrl._UNSET)

    return ctrl.update_supplier_product(
        product_id=product_id,
        name=product_update.get("name"),
        description=product_update.get("description"),
        price=product_update.get("price"),
        stock_quantity=product_update.get("stock_quantity", product_update.get("stock")),
        category=product_update.get("category"),
        subcategory=product_update.get("subcategory", product_update.get("sub_category")),
        color=product_update.get("color"),
        is_active=product_update.get("is_active"),
        tags=product_update.get("tags"),
        sizes=product_update.get("sizes"),
        materials=product_update.get("materials"),
        visibility_regions=visibility_regions_value,
        weight=product_update.get("weight"),
        dimensions=product_update.get("dimensions"),
        compare_price=compare_price_value,
        discount_starts_at=discount_starts_at_value,
        discount_ends_at=discount_ends_at_value,
        return_window_days=return_window_days_value,
        video_url=video_url_value,
        variants_payload=variants_payload_value,
        is_new=is_new_value,
        image=image,
        additional_images=[file for file in additional_images if file and file.filename],
        current_user=current_user,
        db=db,
    )

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    return ctrl.delete_supplier_product(product_id, current_user, db)

@router.patch("/products/{product_id}/return-window")
def update_return_window(
    product_id: int,
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Set the return window (days) for a specific product. Min 10 days."""
    from pydantic import BaseModel, Field

    class ReturnWindowBody(BaseModel):
        days: int = Field(..., ge=10, le=365, description="Return window in days (minimum 10)")

    validated = ReturnWindowBody(**body)
    import controllers.products_controller as products_ctrl
    return products_ctrl.update_product_return_window(
        product_id=product_id,
        days=validated.days,
        current_user=current_user,
        db=db,
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_analytics(period, current_user, db)


@router.get("/reports")
def get_reports(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_reports(period, current_user, db)

@router.post("/reports/ai-audit/run")
def run_reports_ai_audit(
    limit: int = 0,
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.queue_supplier_ai_audit(current_user, limit=limit)


# ── Inventory ─────────────────────────────────────────────────────────────────

@router.get("/inventory/alerts")
def get_inventory_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_inventory_alerts(current_user, db)


@router.get("/inventory")
def get_inventory(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_inventory(current_user, db)

@router.put("/inventory/{product_id}/stock")
def update_stock(
    product_id: int,
    stock_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_product_stock(product_id, stock_update, current_user, db)

@router.put("/inventory/{product_id}/levels")
def update_levels(
    product_id: int,
    levels_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_inventory_levels(product_id, levels_update, current_user, db)

@router.post("/inventory/bulk-adjust")
def bulk_adjust_inventory(
    adjustments: List[dict],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Bulk set or adjust stock levels for multiple products (up to 200)."""
    return ctrl.bulk_inventory_adjust(adjustments, current_user, db)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_profile(current_user, db)

@router.put("/profile")
def update_profile(
    profile_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.update_supplier_profile(profile_update, current_user, db)

@router.post("/profile/verify")
def request_verification(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.request_verification(current_user, db)


# ── Payouts ───────────────────────────────────────────────────────────────────

@router.get("/payouts")
def get_payouts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_payout_history(current_user, db)


@router.get("/shipments")
def get_shipments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.get_supplier_shipments(current_user, db)

@router.post("/payouts/request")
def request_payout(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    return ctrl.request_payout(body, current_user, db)


# ── Business Profile ──────────────────────────────────────────────────────────

@router.get("/profile/business")
def get_business_profile(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return the supplier's business profile (creates one on first access)."""
    return ctrl.get_supplier_profile_business(current_user, db)

@router.put("/profile/business")
def update_business_profile(
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Update editable fields on the supplier's business profile."""
    return ctrl.update_supplier_profile_business(body, current_user, db)

@router.post("/profile/business/media")
async def upload_business_profile_media(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    field: str = Form(...),
    index: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a supplier storefront logo, banner, or hosted video file."""
    return ctrl.upload_supplier_profile_business_media(field, file, current_user, db, index=index)

@router.post("/terms/accept")
def accept_terms(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Record that the current supplier has accepted the Terms & Conditions."""
    return ctrl.accept_supplier_terms(current_user, db)


@router.get("/onboarding/status")
def onboarding_status(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return the supplier's onboarding checklist status."""
    return ctrl.get_supplier_onboarding_status(current_user, db)


# ── Regions / Countries of Operation ─────────────────────────────────────────

@router.get("/regions")
def get_regions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return the supplier's operating regions/countries."""
    return ctrl.get_supplier_regions(current_user, db)

@router.put("/regions")
def update_regions(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Update the supplier's operating regions/countries."""
    return ctrl.update_supplier_regions(body, current_user, db)


# ── Credibility Badge & Document Verification ─────────────────────────────────

@router.get("/badge")
def get_supplier_badge(
    current_user: SupplierAdminOrSubAdminUser,
    db: Session = Depends(get_db),
):
    """Return the current supplier's credibility score and badge level."""
    return ctrl.refresh_supplier_badge(current_user["id"], db)


@router.get("/badge/catalog")
def get_supplier_badge_catalog(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return active badge tiers plus the supplier's current eligibility metrics."""
    return ctrl.list_supplier_badge_catalog(current_user, db)


@router.get("/badge/billing")
def get_supplier_badge_billing_history(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Return badge billing records for the authenticated supplier."""
    return ctrl.list_supplier_badge_billing_history(current_user, db)

@router.post("/badge/purchase")
def purchase_supplier_badge(
    body: dict,
    current_user: dict = Depends(require_roles("supplier", "admin")),
    db: Session = Depends(get_db),
):
    """Create a badge purchase or renewal billing record for the authenticated supplier."""
    return ctrl.purchase_supplier_badge(body, current_user, db)

@router.post("/profile/verify-documents")
async def upload_verification_documents_route(
    current_user: dict = Depends(require_roles("supplier", "admin")),
    files: List[UploadFile] = File(...),
    doc_types: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    """Upload KYC documents (trade license, tax cert, ID, etc.) for verification."""
    return await ctrl.upload_verification_documents(files, doc_types, current_user, db)



# -- Supplier Analytics Timeseries ------------------------------------------

@router.get("/analytics/revenue")
def get_analytics_revenue(
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return daily revenue + order timeseries for the authenticated supplier."""
    return ctrl.get_supplier_analytics_timeseries(current_user, period, db)


# ── Supplier Bank Account (Payout Beneficiary) ────────────────────────────────

@router.get("/bank-account")
def get_bank_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Get the supplier's saved payout bank account."""
    return ctrl.get_supplier_bank_account(current_user, db)

@router.put("/bank-account")
def upsert_bank_account(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Submit or update the supplier's payout bank account. Triggers admin verification."""
    return ctrl.upsert_supplier_bank_account(body, current_user, db)

