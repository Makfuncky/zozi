# === From supplier_supplier_sync.py ===
from suppliers.router import router  # noqa: F401
"""

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

