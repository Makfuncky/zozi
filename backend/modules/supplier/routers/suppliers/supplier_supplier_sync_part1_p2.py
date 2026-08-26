# === From supplier_supplier_sync.py ===
from suppliers.router import router  # noqa: F401
"""

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