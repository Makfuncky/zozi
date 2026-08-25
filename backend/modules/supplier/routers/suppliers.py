"""Supplier suppliers router — consolidated from 17 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/suppliers", tags=["supplier", "suppliers"])


# === From supplier.py ===
"""
Supplier Router — route declarations only (HTTP layer).
All business logic lives in controllers/supplier_controller.py.
"""
from datetime import datetime
from typing import Annotated, Any, List, Optional, cast

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

import domains.orders.services as disputes_ctrl
import domains.orders.services as returns_ctrl
import controllers.supplier_controller as ctrl
from controllers import commission_controller
from domains.security.services.iam.security_dependencies import require_roles
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ListPage, SupplierReturnReviewUpdate
from infrastructure.database.schemas import Product as ProductSchema


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

    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.background_jobs import enqueue_ml_job

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_process_image() -> dict:
        import asyncio
        from io import BytesIO

        from fastapi import UploadFile

        from controllers.supplier_controller import process_product_image

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
    from domains.logistics.services._auto_stubs import resolve_shipping_tier
    shipping_tier = resolve_shipping_tier(weight_kg=weight, dimensions=dimensions)

    from domains.comms.services._auto_stubs import moderate_content
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

    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.background_jobs import enqueue_ml_job

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

        from providers.ai.vision import analyze_product_image
        from infrastructure.media.image_ai_service import remove_background
        from infrastructure.utils.storage import storage as _store

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
    from infrastructure.utils.background_jobs import get_job

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

    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.background_jobs import enqueue_ml_job

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_remove_background() -> dict:
        from domains.finance.services._auto_stubs import AVAILABLE_MODELS
        from domains.finance.services._auto_stubs import VALID_STRATEGIES
        from infrastructure.media.image_ai_service import remove_background_model
        from infrastructure.utils.storage import storage as _store

        if model and model in AVAILABLE_MODELS:
            processed = remove_background_model(raw, model, fast_mode=fast_mode)
        else:
            preset_effective = preset if preset in VALID_STRATEGIES else "general"
            from infrastructure.media.image_ai_service import remove_background
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
    from providers.ai.vision import analyze_product_image
    # Instant, photo-derived heuristic result (colours from the actual pixels,
    # category/name from the filename + config). Real vision understanding runs
    # in the background job below and the frontend polls it to refine the form.
    result = await analyze_product_image(raw, filename=image.filename or "", generate_copy=False)
    if generate_copy:
        from providers.media.services.ai_copy_jobs import enqueue_copy_job
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
    from domains.comms.services._auto_stubs import VideoConferenceRoom
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
    import re

    # Try structured extraction via direct Ollama call
    from domains.finance.services._auto_stubs import _OLLAMA_TEXT_MODEL
    from providers.ai.text import _extract_json
    from providers.ai.text import _ollama_chat

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
    from infrastructure.utils.background_jobs import get_job
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
    from domains.comms.services._auto_stubs import translate_en_to_ar
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
    from domains.catalog.services.variants.variant_config_service import get_axes_for_category
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
    from domains.comms.services._auto_stubs import moderate_content
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

    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.background_jobs import enqueue_ml_job

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_generate_angles() -> dict:
        import asyncio
        from io import BytesIO

        from fastapi import UploadFile

        from controllers.supplier_controller import process_product_image

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
    import domains.catalog.services as products_ctrl
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


# === From supplier_core_routes.py ===
"""supplier core routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/supplier_core_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "supplier_core_routes", "prefix": "/api/v1/supplier"}


# === From supplier_documents.py ===
"""Supplier documents (KYC) sub-router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import SupplierDocumentOut
from domains.governance.models.user import User
from domains.suppliers.models.suppliers import SupplierDocument
from domains.suppliers.models.suppliers import SupplierProfile
from infrastructure.utils.dependencies import require_admin, require_supplier

__router_prefix__ = "/supplier/documents"


def list_my_documents(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return (
        db.query(SupplierDocument)
        .filter(SupplierDocument.supplier_id == profile.id, SupplierDocument.is_deleted == False)  # noqa: E712
        .order_by(SupplierDocument.id.desc())
        .all()
    )


@router.get("/all", response_model=list[SupplierDocumentOut])
def list_all_documents(
    status_filter: str | None = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.filter(SupplierDocument.status == status_filter)
    return q.order_by(SupplierDocument.id.desc()).all()


@router.put("/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str,
    note: str | None = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = new_status
    doc.review_note = note
    doc.reviewed_by = admin_user.id
    db.commit()
    return {"message": "Reviewed", "status": new_status}


# === From supplier_documents_review.py ===
"""Supplier documents (KYC) sub-router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import SupplierDocumentOut
from infrastructure.utils.dependencies import get_current_user, require_admin, require_supplier
from domains.suppliers.services.documents.supplier_document_service import list_all_supplier_documents
from domains.comms.ports import list_supplier_documents
from domains.suppliers.services.documents.supplier_document_service import review_supplier_document
from domains.catalog.services.products.products_service import get_supplier_profile


@router.get("", response_model=list[SupplierDocumentOut])
def list_my_documents(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = get_supplier_profile(current_user, db)
    return list_supplier_documents(db, profile.id)


@router.get("/all", response_model=list[SupplierDocumentOut])
def list_all_documents(status_filter: str | None = Query(None), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list_all_supplier_documents(db, status_filter)


@router.put("/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str,
    note: str | None = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return review_supplier_document(db, document_id, new_status, note, admin_user.id)


# === From supplier_health.py ===
"""
Supplier Health API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.suppliers.services.health.supplier_health_engine import get_supplier_health_engine


@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health(
    supplier_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Allow admins, or the supplier who owns the profile identified by supplier_id.
    if current_user.get("role") != "admin":
        from domains.suppliers.models.suppliers import SupplierProfile
        owns = db.query(SupplierProfile).filter(
            SupplierProfile.id == supplier_id,
            SupplierProfile.user_id == current_user["id"],
        ).first()
        if not owns:
            raise HTTPException(status_code=403, detail="Supplier access required")
    engine = get_supplier_health_engine(db)
    return engine.calculate_health_score(supplier_id, country_code)


@router.get("/health/suppliers")
def list_supplier_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only: enumerate supplier health/trust scores. Restricted from
    arbitrary authenticated users (P0.8)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from domains.suppliers.models.suppliers import SupplierProfile
    profiles = db.query(SupplierProfile).all()
    results = []
    for p in profiles:
        engine = get_supplier_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        avg_rating = getattr(p, "average_rating", None)
        health["profile"] = {
            "name": p.business_name,
            "rating": float(avg_rating) if avg_rating is not None else 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"suppliers": results[:50]}


# === From supplier_health_list.py ===
"""
Supplier Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from domains.suppliers.services.health.supplier_health_service import get_supplier_health_for_user
from domains.suppliers.services.health.supplier_health_service import list_supplier_health_for_admin


@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health(
    supplier_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_supplier_health_for_user(db, current_user, supplier_id, country_code)


@router.get("/health/suppliers")
def list_supplier_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only: enumerate supplier health/trust scores. Restricted from
    arbitrary authenticated users (P0.8)."""
    return list_supplier_health_for_admin(db, current_user, country_code)


# === From supplier_profile.py ===
"""Supplier profile router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate
from domains.governance.models.user import User
from domains.suppliers.models.suppliers import SupplierProfile
from infrastructure.utils.dependencies import get_current_user, require_supplier
from infrastructure.utils.slug import generate_slug


@router.get("/profile", response_model=SupplierProfileOut)
def get_supplier_profile(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404, "Profile not found")
    return profile

@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile(payload: SupplierProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first():
        raise HTTPException(400, "Profile already exists")
    profile = SupplierProfile(user_id=current_user.id, slug=generate_slug(payload.business_name), **payload.model_dump())
    db.add(profile); db.commit(); db.refresh(profile)
    current_user.role = "supplier"; db.commit()
    return profile

@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile(payload: SupplierProfileUpdate, current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404)
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(profile, k, v)
    db.commit(); db.refresh(profile)
    return profile


# === From supplier_profile_create.py ===
"""Supplier profile router.

Thin HTTP layer: delegates all profile business logic to
``services.supplier.supplier_profile_write_service`` so the router stays free of
``db.add``/``db.commit``. Endpoint paths, auth and response models are unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate
from infrastructure.utils.dependencies import get_current_user, require_supplier
from domains.accounts.services.auth.auth_service import create_supplier_profile
from domains.catalog.services.products.products_service import get_supplier_profile
from domains.suppliers.services.health.supplier_health import update_supplier_profile


@router.get("/profile", response_model=SupplierProfileOut)
def get_supplier_profile_route(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_profile(current_user, db)


@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile_route(payload: SupplierProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_supplier_profile(current_user, payload, db)


@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile_route(payload: SupplierProfileUpdate, current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = update_supplier_profile(current_user, payload, db)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


# === From onboarding.py ===
"""
Onboarding Pipeline API
"""
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.suppliers.services._auto_stubs import get_onboarding_service


@router.post("/pipelines", response_model=dict)
async def create_pipeline(
    pipeline_type: str = "kyc",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    pipeline = service.create_pipeline(user.id, pipeline_type)
    
    return {
        "pipeline_id": pipeline.id,
        "type": pipeline.pipeline_type,
        "status": pipeline.status
    }


@router.post("/pipelines/{pipeline_id}/documents", response_model=dict)
async def upload_document(
    pipeline_id: int,
    document_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    
    service = get_onboarding_service(db)
    verification = service.process_document(pipeline_id, document_type, content)
    
    return {
        "verification_id": verification.id,
        "document_type": verification.document_type,
        "status": verification.status,
        "ocr_confidence": verification.ocr_result.confidence_score if verification.ocr_result else None
    }


@router.post("/kyc", response_model=dict)
async def create_kyc_verification(
    documents: List[dict],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    kyc = service.create_kyc_verification(user.id, documents)
    
    return {
        "kyc_id": kyc.id,
        "status": kyc.status,
        "document_types": kyc.document_types
    }


@router.get("/status", response_model=dict)
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    service = get_onboarding_service(db)
    status = service.get_pipeline_status(user.id)
    
    if not status:
        return {"status": "not_started"}
    
    return status


@router.post("/pipelines/{pipeline_id}/steps/{step_name}/complete", response_model=dict)
async def complete_step(
    pipeline_id: int,
    step_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_onboarding_service(db)
    step = service.complete_step(pipeline_id, step_name)
    
    return {
        "step": step.step_name,
        "status": step.status,
        "completed_at": step.completed_at.isoformat() if step.completed_at else None
    }


# === From supplier_supplier_supplier_health.py ===
"""AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
from typing import Optional

from controllers.supplier.supplier_health_controller import get_supplier_health, list_supplier_health


@router.get("/health/suppliers/{supplier_id}", status_code=200, tags=['supplier-health'])
def get_supplier_health_route(
    supplier_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    country_code: Optional[str] = Query(None)
) -> dict:
    return get_supplier_health(supplier_id=supplier_id, current_user=current_user, db=db, country_code=country_code)

@router.get("/health/suppliers", status_code=200, tags=['supplier-health'])
def list_supplier_health_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    country_code: Optional[str] = Query(None)
) -> dict:
    return list_supplier_health(current_user=current_user, db=db, country_code=country_code)


# === From supplier_supplier_sync.py ===
"""
Supplier Router — route declarations only (HTTP layer).
All business logic lives in controllers/supplier_controller.py.
"""
from typing import Annotated, Any, List, Optional, cast
from fastapi import APIRouter, Body, Depends, UploadFile, File, Form, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime

from infrastructure.database.database import get_db
from infrastructure.database.schemas import ListPage, Product as ProductSchema, SupplierReturnReviewUpdate
from domains.security.services.iam.security_dependencies import require_roles
from domains.finance.services._auto_stubs import commission_controller
import domains.suppliers.services.supplier_controller as ctrl
import domains.orders.services.returns_controller as returns_ctrl
import domains.orders.services.disputes_controller as disputes_ctrl


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
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_process_image() -> dict:
        from providers.image.bg_remover import process_product_image
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
    from domains.logistics.services._auto_stubs import resolve_shipping_tier
    shipping_tier = resolve_shipping_tier(weight_kg=weight, dimensions=dimensions)

    from domains.comms.services._auto_stubs import moderate_content
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
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage

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
        from infrastructure.media.image_ai_service import remove_background
        from providers.ai.vision import analyze_product_image
        from infrastructure.utils.storage import storage as _store

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
    from infrastructure.utils.background_jobs import get_job

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
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_remove_background() -> dict:
        from infrastructure.media.image_ai_service import remove_background_model
        from domains.finance.services._auto_stubs import AVAILABLE_MODELS
        from domains.finance.services._auto_stubs import VALID_STRATEGIES
        from infrastructure.utils.storage import storage as _store

        if model and model in AVAILABLE_MODELS:
            processed = remove_background_model(raw, model, fast_mode=fast_mode)
        else:
            preset_effective = preset if preset in VALID_STRATEGIES else "general"
            from infrastructure.media.image_ai_service import remove_background
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
    from providers.ai.vision import analyze_product_image
    # Instant, photo-derived heuristic result (colours from the actual pixels,
    # category/name from the filename + config). Real vision understanding runs
    # in the background job below and the frontend polls it to refine the form.
    result = await analyze_product_image(raw, filename=image.filename or "", generate_copy=False)
    if generate_copy:
        from providers.media.services.ai_copy_jobs import enqueue_copy_job
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
    from domains.comms.services._auto_stubs import VideoConferenceRoom
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
    from providers.ai.text import _ollama_chat
    from domains.finance.services._auto_stubs import _OLLAMA_TEXT_MODEL
    from providers.ai.text import _extract_json

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
    from infrastructure.utils.background_jobs import get_job
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
    from domains.comms.services._auto_stubs import translate_en_to_ar
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
    from domains.catalog.services.variants.variant_config_service import get_axes_for_category
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
    from domains.comms.services._auto_stubs import moderate_content
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
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_generate_angles() -> dict:
        from providers.image.bg_remover import process_product_image
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
    from domains.suppliers.services.products.supplier_products import _process_image_with_tools
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
    import domains.catalog.services as products_ctrl
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


# === From supplier_supplier_upload.py ===
"""
BG Strategy A/B Testing Router
================================
Evaluates multiple background-removal strategies on the uploaded image and returns
quality metrics (edge clarity, alpha confidence, coverage) plus the best strategy.

The supplier frontend can then auto-select the winning strategy with one click
instead of manually trying each model.
"""

import gc
import logging
import time
from typing import Dict, Optional

import base64
import numpy as np
from PIL import Image

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from domains.security.services.iam.security_dependencies import require_roles
from domains.finance.services._auto_stubs import VALID_STRATEGIES
from infrastructure.media.image_ai_service import remove_background
from domains.finance.services._auto_stubs import _HAS_CV2
from providers.image.bg_remover import _bytes_to_image


logger = logging.getLogger(__name__)


# The 6 production strategies mapped to their display names
AB_TEST_STRATEGIES = [
    "clean_commercial",
    "precision_geometry",
    "birefnet_production",
    "ultimate_gaps",
    "marketing_variants",
    "lite_variants",
]


def _compute_quality_score(image_np: np.ndarray, alpha_map: np.ndarray) -> Dict[str, float]:
    """Compute quality metrics for a BG-removed result.

    Returns:
        edge_clarity: 0-1, how sharp the edges are (Laplacian variance on alpha edges)
        alpha_confidence: 0-1, mean alpha value of non-zero pixels
        coverage: 0-1, proportion of image covered by foreground
        overall: 0-1, weighted composite of the above
        edge_pixels_pct: 0-1, proportion of boundary pixels
    """
    h, w = alpha_map.shape
    total_pixels = h * w

    # Alpha confidence: how solid the foreground alpha is
    fg_mask = alpha_map > 0.05
    fg_pixels = np.sum(fg_mask)
    coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0

    if fg_pixels > 0:
        alpha_confidence = float(np.mean(alpha_map[fg_mask]))
    else:
        alpha_confidence = 0.0

    # Edge clarity: use Laplacian variance on the alpha edges
    edge_clarity = 0.0
    edge_pixels_pct = 0.0
    if _HAS_CV2:
        try:
            import cv2
        except ImportError:
            return {
                "edge_clarity": 0.0,
                "alpha_confidence": round(alpha_confidence, 4),
                "coverage": round(coverage, 4),
                "overall": round(alpha_confidence * 0.4 + coverage * 0.2, 4),
                "edge_pixels_pct": 0.0,
            }

        alpha_uint8 = (alpha_map * 255).astype(np.uint8)

        # Find edges in alpha
        edges = cv2.Canny(alpha_uint8, 30, 150)
        edge_pixels = np.sum(edges > 0)
        edge_pixels_pct = float(edge_pixels / total_pixels) if total_pixels > 0 else 0.0

        # For edge region, compute Laplacian variance on the RGB image
        if edge_pixels > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            edge_region = cv2.dilate(edges, kernel, iterations=2)

            if image_np.ndim == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np

            lap = cv2.Laplacian(gray, cv2.CV_64F)
            edge_variance = float(np.var(lap[edge_region > 0])) if np.sum(edge_region > 0) > 0 else 0.0

            # Normalize: typical good edge variance is 50-500
            edge_clarity = min(1.0, edge_variance / 300.0)

    # Overall composite score
    overall = (alpha_confidence * 0.4) + (coverage * 0.2) + (edge_clarity * 0.4)

    return {
        "edge_clarity": round(edge_clarity, 4),
        "alpha_confidence": round(alpha_confidence, 4),
        "coverage": round(coverage, 4),
        "overall": round(overall, 4),
        "edge_pixels_pct": round(edge_pixels_pct, 4),
    }


@router.post("/upload/ab-test-bg")
async def ab_test_bg_strategies(
    image: UploadFile = File(...),
    strategies: Optional[str] = Form(None),
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Enqueue A/B test across multiple BG removal strategies and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job tests
    up to 6 strategies and returns quality scores plus the winning image.
    """
    import uuid
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    owner_id = current_user.get("id") or current_user.get("user_id")
    owner_role = current_user.get("role", "supplier")

    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or "image/jpeg")

    def _run_ab_test() -> dict:
        from infrastructure.media.image_ai_service import remove_background
        from domains.finance.services._auto_stubs import VALID_STRATEGIES
        from providers.image.bg_remover import _bytes_to_image, _compute_quality_score
        from PIL import Image
        import base64, time, gc

        raw_local = raw
        test_strategies = AB_TEST_STRATEGIES
        if strategies:
            parsed = [s.strip() for s in strategies.split(",") if s.strip() in VALID_STRATEGIES]
            if parsed:
                test_strategies = parsed

        img = _bytes_to_image(raw_local)
        img_rgb = np.array(img.convert("RGB"))
        max_test_dim = 384
        if max(img.size) > max_test_dim:
            ratio = max_test_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            img_rgb = np.array(img.convert("RGB"))

        results = {}
        scores = {}
        timing = {}
        winner = test_strategies[0]
        best_score = -1.0

        for strategy in test_strategies:
            try:
                t0 = time.perf_counter()
                processed = remove_background(raw_local, strategy=strategy)
                elapsed = (time.perf_counter() - t0) * 1000
                processed_img = _bytes_to_image(processed)
                processed_np = np.array(processed_img)
                if processed_np.shape[2] == 4:
                    alpha = processed_np[:, :, 3].astype(np.float32) / 255.0
                else:
                    alpha = np.ones(processed_np.shape[:2], dtype=np.float32)
                score = _compute_quality_score(img_rgb, alpha)
                scores[strategy] = score
                timing[strategy] = round(elapsed, 1)
                img_b64 = base64.b64encode(processed).decode("utf-8")
                results[strategy] = f"data:image/png;base64,{img_b64}"
                if score["overall"] > best_score:
                    best_score = score["overall"]
                    winner = strategy
            except Exception as exc:
                logger.warning("A/B test strategy %s failed: %s", strategy, exc)
                scores[strategy] = {
                    "edge_clarity": 0.0,
                    "alpha_confidence": 0.0,
                    "coverage": 0.0,
                    "overall": 0.0,
                    "edge_pixels_pct": 0.0,
                }
                timing[strategy] = 0.0
                results[strategy] = ""

        gc.collect()
        return {"winner": winner, "scores": scores, "results": results, "timing_ms": timing,
                "strategies_tested": test_strategies,
                "image_dimensions": {"width": img.width, "height": img.height}}

    job = enqueue_ml_job(
        owner_user_id=owner_id,
        owner_role=owner_role,
        func=_run_ab_test,
        metadata={"strategies": strategies},
        max_retries=1,
    )
    return {"job_id": job["id"], "status": "queued"}

@router.get("/upload/ab-test-strategies")
async def list_ab_test_strategies(
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return the list of available BG strategies for A/B testing."""
    return {
        "strategies": [
            {
                "key": "clean_commercial",
                "label": "Clean Commercial",
                "description": "br05 — Best for simple product shots, clean edges",
                "icon": "Wand2",
            },
            {
                "key": "precision_geometry",
                "label": "Precision Geometry",
                "description": "br06 — Best for geometric shapes, electronics, accessories",
                "icon": "Layers",
            },
            {
                "key": "birefnet_production",
                "label": "Production BiRefNet",
                "description": "br08 — Best for general products, good quality-speed tradeoff",
                "icon": "Zap",
            },
            {
                "key": "ultimate_gaps",
                "label": "Ultimate v11",
                "description": "br11 — Best for complex shapes with gaps and fine details",
                "icon": "Sparkles",
            },
            {
                "key": "marketing_variants",
                "label": "Ultimate v12",
                "description": "br12 — Best for marketing photos, floating artifacts removal",
                "icon": "Tag",
            },
            {
                "key": "lite_variants",
                "label": "Variant Testing",
                "description": "br13 — Best for clothing / fabric, lightweight model chain",
                "icon": "Camera",
            },
        ]
    }


# ── In-memory cache for category recommendations ─────────────────────────
_CATEGORY_RECO_CACHE: Dict[str, tuple] = {}
_CATEGORY_RECO_TTL_S = 3600  # 1 hour


@router.get("/upload/bg-recommendations")
async def get_bg_recommendations(
    current_user: dict = Depends(require_roles("supplier", "admin")),
):
    """Return per-category BG strategy recommendations with metrics.

    Results are cached for 1 hour because the underlying visual-regression
    metrics only change when a new comparison run is executed.
    """
    import time
    from providers.bg_removal.bg_removal_service import _get_category_recommendations

    now = time.time()
    cache_key = "bg_category_recommendations"
    cached = _CATEGORY_RECO_CACHE.get(cache_key)
    if cached and (now - cached[1] < _CATEGORY_RECO_TTL_S):
        return cached[0]

    recommendations = _get_category_recommendations()
    payload = {
        "recommendations": recommendations,
        "strategies": [
            {"key": "clean_commercial", "label": "Clean Commercial", "icon": "Wand2"},
            {"key": "precision_geometry", "label": "Precision Geometry", "icon": "Layers"},
            {"key": "birefnet_production", "label": "Production BiRefNet", "icon": "Zap"},
            {"key": "ultimate_gaps", "label": "Ultimate v11", "icon": "Sparkles"},
            {"key": "marketing_variants", "label": "Ultimate v12", "icon": "Tag"},
            {"key": "lite_variants", "label": "Variant Testing", "icon": "Camera"},
        ],
    }
    _CATEGORY_RECO_CACHE[cache_key] = (payload, now)
    return payload


# === From supplier_sync.py ===
"""
Re-export shim for the supplier sync router.

The canonical supplier sync routes now live in
``modules.supplier.routers.supplier_supplier_sync``. This module previously held
a duplicated near-copy of that router; it is retained only as a re-export so any
lingering imports keep working (MERGE-NOT-DELETE policy — see RESOLVER.md §7 S1).
"""
from .supplier_supplier_sync import *  # noqa: F401,F403
from .supplier_supplier_sync import router  # noqa: F401
from rbac.dependencies import require_feature


# === From supplier_upload.py ===
"""
Re-export shim for the supplier upload (BG A/B testing) router.

The canonical BG-strategy A/B testing routes now live in
``modules.supplier.routers.supplier_supplier_upload``. This module previously
held a duplicated near-copy; it is retained only as a re-export
(MERGE-NOT-DELETE policy — see RESOLVER.md §7 S1).
"""
from .supplier_supplier_upload import *  # noqa: F401,F403
from .supplier_supplier_upload import router  # noqa: F401
from rbac.dependencies import require_feature


# === From supplier_bg_ab_test.py ===
"""supplier bg ab test router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/supplier_bg_ab_test/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "supplier_bg_ab_test", "prefix": "/api/v1/supplier"}


# === From supplier_orders.py ===
"""Supplier orders sub-router."""

import json

# AI analysis for parcel-photo matching (uses the vision provider)
import logging
import os
from datetime import datetime
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

ai_logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


# ── Helper: extract user ID from either a dict or a User ORM model ─────
def _get_user_id(current_user: User | dict) -> int:
    """`require_supplier` may return a dict or a User ORM model.
    This helper normalises both to an int ID."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session: missing user ID")
        return int(uid)
    return current_user.id


def _get_user_attr(current_user: User | dict, attr: str, default: Any = "") -> Any:
    """Safe attribute access for both dict and ORM current_user."""
    if isinstance(current_user, dict):
        return current_user.get(attr, default)
    return getattr(current_user, attr, default)


@router.get("")
def list_supplier_orders(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == _get_user_id(current_user)).first()
    if not supplier:
        raise HTTPException(404)
    orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
        .all()
    )
    return orders


@router.get("/{order_id}/label")
def get_supplier_label(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return packing sheet / label data for a supplier order."""
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

    items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.supplier_id == supplier.id,
        )
        .all()
    )

    subtotal = float(sum((item.price or 0) * item.quantity for item in items))
    vat = float(order.tax_amount or 0)
    shipping = float(order.shipping_fee or 0)
    discount = float(order.discount_amount or 0)
    total = subtotal + vat + shipping - discount

    # Resolve shipment info if available
    shipment_info = _resolve_shipment_info(db, order_id, supplier.id)

    return {
        "order_id": order.id,
        "order_number": order.order_number or f"ORD-{order.id}",
        "invoice_number": order.order_number or f"INV-{order.id}",
        "order_status": order.status,
        "payment_method": order.payment_method,
        "scan_code": f"ZOZI-{order.id}-{supplier.id}",
        "ordered_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
        "customer_name": getattr(order, "customer_name", _get_user_attr(current_user, "username", "Customer") or "Customer"),
        "customer_email": getattr(order, "customer_email", ""),
        "customer_phone": getattr(order, "customer_phone", ""),
        "shipping_address": getattr(order, "shipping_address", None),
        "delivery_location": getattr(order, "delivery_location", None),
        "delivery_note": getattr(order, "delivery_note", None),
        "supplier_name": supplier.business_name or _get_user_attr(current_user, "username", "Supplier"),
        "supplier_email": _get_user_attr(current_user, "email", ""),
        "supplier_phone": getattr(supplier, "phone_business", None),
        "supplier_address": getattr(supplier, "address", None),
        "supplier_website": getattr(supplier, "website", None),
        "supplier_tax_id": getattr(supplier, "tax_id", None),
        "supplier_logo_url": getattr(supplier, "logo_url", None),
        "subtotal": subtotal,
        "vat": vat,
        "shipping": shipping,
        "discount": discount,
        "total": total,
        "currency": getattr(order, "currency", "OMR"),
        "has_shipment": shipment_info.get("has_shipment", False),
        "shipment_id": shipment_info.get("shipment_id"),
        "shipment_status": shipment_info.get("shipment_status", "pending"),
        "shipment_status_label": shipment_info.get("shipment_status_label", "Pending"),
        "tracking_number": shipment_info.get("tracking_number"),
        "carrier_name": shipment_info.get("carrier_name"),
        "current_hub": shipment_info.get("current_hub"),
        "package_count": shipment_info.get("package_count"),
        "package_weight_kg": shipment_info.get("package_weight_kg"),
        "package_dimensions": shipment_info.get("package_dimensions"),
        "packaging_notes": shipment_info.get("packaging_notes"),
        "packaged_at": shipment_info.get("packaged_at"),
        "items": [
            {
                "order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.price or 0),
                "line_total": float((item.price or 0) * item.quantity),
            }
            for item in items
        ],
    }


def _resolve_shipment_info(
    db: Session, order_id: int, supplier_id: int
) -> dict[str, Any]:
    """Resolve shipment info from the logistics models if available."""
    try:
        from domains.logistics.models.logistics_entities import Shipment

        shipment = (
            db.query(Shipment)
            .filter(
                Shipment.order_id == order_id,
            )
            .first()
        )
        if not shipment:
            return {"has_shipment": False}

        return {
            "has_shipment": True,
            "shipment_id": shipment.id,
            "shipment_status": getattr(shipment, "status", "pending"),
            "shipment_status_label": getattr(shipment, "status", "pending").replace("_", " ").title(),
            "tracking_number": getattr(shipment, "tracking_number", None),
            "carrier_name": getattr(shipment, "carrier", None),
            "current_hub": getattr(shipment, "current_hub", None),
            "package_count": getattr(shipment, "package_count", None),
            "package_weight_kg": getattr(shipment, "package_weight_kg", None),
            "package_dimensions": getattr(shipment, "package_dimensions", None),
            "packaging_notes": getattr(shipment, "packaging_notes", None),
            "packaged_at": getattr(shipment, "packaged_at", None),
        }
    except Exception:
        logger.warning("Could not resolve shipment info for order %s", order_id)
        return {"has_shipment": False}


@router.post("/{order_id}/parcel-proof")
async def upload_parcel_proof(
    order_id: int,
    file: UploadFile = File(...),
    notes: str = Form(""),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Upload a packed parcel photo as proof of packaging."""
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
    if order.status == "processing":
        order.status = "prepared"
        db.commit()

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
        .join(OrderItem.product)
        .filter(OrderItem.product.has(supplier_id=user_id))
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

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
    items = (
        db.query(OrderItem)
        .join(OrderItem.product)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.product.has(supplier_id=user_id),
        )
        .all()
    )
    item_descriptions = [
        f"{item.product_name} x{item.quantity}" for item in items
    ]

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
        from providers.parcel_verification import (
            verify_parcel_fast,
            verify_parcel_photo,
        )

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
        ai_logger.warning("Parcel verification provider not available — returning basic check")
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


# === From supplier_orders_verify.py ===
"""Supplier orders sub-router.

DB reads/writes live in ``services.supplier.supplier_order_service``; this
router keeps request parsing, file handling, storage and parcel-AI logic.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.suppliers.models.suppliers import SupplierProfile
from domains.orders.models.order_entities import Order
from domains.orders.models.order_entities import OrderItem
from infrastructure.utils.dependencies import require_supplier
from infrastructure.utils.storage import storage as _storage
from domains.orders.ports import get_supplier_order
from domains.orders.ports import get_supplier_order_for_verify
from domains.orders.ports import get_supplier_order_items
from domains.orders.ports import get_supplier_order_items_for_verify
from domains.suppliers.services.orders.supplier_orders_service import get_supplier_profile_by_user_id
from domains.orders.ports import list_supplier_order_ids
from domains.suppliers.services.orders.supplier_orders_service import list_supplier_orders
from domains.suppliers.services.orders.supplier_orders_service import mark_order_prepared_if_processing
from domains.suppliers.services.orders.supplier_orders_service import resolve_shipment_info

ai_logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


# ── Helper: extract user ID from either a dict or a User ORM model ─────
def _get_user_id(current_user: User | dict) -> int:
    """`require_supplier` may return a dict or a User ORM model.
    This helper normalises both to an int ID."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session: missing user ID")
        return int(uid)
    return current_user.id


def _get_user_attr(current_user: User | dict, attr: str, default: Any = "") -> Any:
    """Safe attribute access for both dict and ORM current_user."""
    if isinstance(current_user, dict):
        return current_user.get(attr, default)
    return getattr(current_user, attr, default)


@router.get("")
def list_supplier_orders(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    supplier = get_supplier_profile_by_user_id(db, _get_user_id(current_user))
    return list_supplier_orders(db, supplier.id)


@router.get("/{order_id}/label")
def get_supplier_label(
    order_id: int,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return packing sheet / label data for a supplier order."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)
    items = get_supplier_order_items(db, order_id, supplier.id)

    subtotal = float(sum((item.price or 0) * item.quantity for item in items))
    vat = float(order.tax_amount or 0)
    shipping = float(order.shipping_fee or 0)
    discount = float(order.discount_amount or 0)
    total = subtotal + vat + shipping - discount

    shipment_info = resolve_shipment_info(db, order_id)

    return {
        "order_id": order.id,
        "order_number": order.order_number or f"ORD-{order.id}",
        "invoice_number": order.order_number or f"INV-{order.id}",
        "order_status": order.status,
        "payment_method": order.payment_method,
        "scan_code": f"ZOZI-{order.id}-{supplier.id}",
        "ordered_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
        "customer_name": getattr(order, "customer_name", _get_user_attr(current_user, "username", "Customer") or "Customer"),
        "customer_email": getattr(order, "customer_email", ""),
        "customer_phone": getattr(order, "customer_phone", ""),
        "shipping_address": getattr(order, "shipping_address", None),
        "delivery_location": getattr(order, "delivery_location", None),
        "delivery_note": getattr(order, "delivery_note", None),
        "supplier_name": supplier.business_name or _get_user_attr(current_user, "username", "Supplier"),
        "supplier_email": _get_user_attr(current_user, "email", ""),
        "supplier_phone": getattr(supplier, "phone_business", None),
        "supplier_address": getattr(supplier, "address", None),
        "supplier_website": getattr(supplier, "website", None),
        "supplier_tax_id": getattr(supplier, "tax_id", None),
        "supplier_logo_url": getattr(supplier, "logo_url", None),
        "subtotal": subtotal,
        "vat": vat,
        "shipping": shipping,
        "discount": discount,
        "total": total,
        "currency": getattr(order, "currency", "OMR"),
        "has_shipment": shipment_info.get("has_shipment", False),
        "shipment_id": shipment_info.get("shipment_id"),
        "shipment_status": shipment_info.get("shipment_status", "pending"),
        "shipment_status_label": shipment_info.get("shipment_status_label", "Pending"),
        "tracking_number": shipment_info.get("tracking_number"),
        "carrier_name": shipment_info.get("carrier_name"),
        "current_hub": shipment_info.get("current_hub"),
        "package_count": shipment_info.get("package_count"),
        "package_weight_kg": shipment_info.get("package_weight_kg"),
        "package_dimensions": shipment_info.get("package_dimensions"),
        "packaging_notes": shipment_info.get("packaging_notes"),
        "packaged_at": shipment_info.get("packaged_at"),
        "items": [
            {
                "order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.price or 0),
                "line_total": float((item.price or 0) * item.quantity),
            }
            for item in items
        ],
    }


@router.post("/{order_id}/parcel-proof")
async def upload_parcel_proof(
    order_id: int,
    file: UploadFile = File(...),
    notes: str = Form(""),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Upload a packed parcel photo as proof of packaging."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)

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
    mark_order_prepared_if_processing(order, db)

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
    """AI-powered verification: match the uploaded parcel photo against the packing sheet."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order_for_verify(db, order_id, user_id)

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
    items = get_supplier_order_items_for_verify(db, order_id, user_id)
    item_descriptions = [
        f"{item.product_name} x{item.quantity}" for item in items
    ]

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
        from providers.parcel_verification import verify_parcel_photo, verify_parcel_fast

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
        ai_logger.warning("Parcel verification provider not available — returning basic check")
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
    """Replace the reference image for this order's parcel-proof homography engine."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)

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
    """Return the latest reference image for this order (redirect to storage URL)."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)
    order = get_supplier_order(db, order_id, supplier.id)

    prefix = f"parcel_proofs/{order_id}/"
    refs = sorted(
        [k for k in _storage.list(prefix) if os.path.basename(k).startswith("reference_")],
        reverse=True,
    )
    if not refs:
        raise HTTPException(status_code=404, detail="No reference image set for this order.")

    latest_key = refs[0]
    latest_url = _storage.url(latest_key)
    return RedirectResponse(url=latest_url, status_code=302)


@router.get("/parcel-verification-history")
def get_parcel_verification_history(
    limit: int = 10,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Return the last N parcel verification results for this supplier."""
    user_id = _get_user_id(current_user)
    supplier = get_supplier_profile_by_user_id(db, user_id)

    # Collect all verification results across this supplier's orders
    all_entries: list[dict] = []
    supplier_order_ids = list_supplier_order_ids(db, supplier.id)

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

