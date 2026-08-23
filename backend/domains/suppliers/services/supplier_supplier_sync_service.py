"""
Supplier Router — route declarations only (HTTP layer).
All business logic lives in controllers/supplier_controller.py.
"""
from typing import Annotated, Any, List, Optional, cast
from fastapi import Body, Depends, UploadFile, File, Form, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ListPage, Product as ProductSchema, SupplierReturnReviewUpdate
from domains.governance.services.admin_controller import require_roles
from domains.finance.services.finance import commission_controller
import domains.suppliers.services.supplier_controller as ctrl
import domains.orders.services.returns_controller as returns_ctrl
import domains.orders.services.disputes_controller as disputes_ctrl
SupplierOrAdminUser = Annotated[dict, Depends(require_roles('supplier', 'admin'))]
SupplierAdminOrSubAdminUser = Annotated[dict, Depends(require_roles('supplier', 'admin', 'sub_admin'))]

async def update_product(product_id: int, request: Request, current_user: dict=Depends(require_roles('supplier', 'admin')), image: UploadFile=File(None), additional_images: List[UploadFile]=File(default=[]), db: Session=Depends(get_db)):
    product_update: dict[str, Any] = {}
    content_type = request.headers.get('content-type', '')
    if 'application/json' in content_type:
        product_update = cast(dict[str, Any], await request.json())
    else:
        form = await request.form()
        product_update = cast(dict[str, Any], dict(form))
    compare_price_value = ctrl._UNSET
    if 'compare_price' in product_update or 'discount_price' in product_update:
        compare_price_value = product_update.get('compare_price', product_update.get('discount_price'))
    discount_starts_at_value = ctrl._UNSET
    if 'discount_starts_at' in product_update:
        discount_starts_at_value = ctrl._parse_optional_datetime(product_update.get('discount_starts_at'))
    discount_ends_at_value = ctrl._UNSET
    if 'discount_ends_at' in product_update:
        discount_ends_at_value = ctrl._parse_optional_datetime(product_update.get('discount_ends_at'))
    return_window_days_value = ctrl._UNSET
    if 'return_window_days' in product_update:
        return_window_days_value = product_update.get('return_window_days')
    video_url_value = ctrl._UNSET
    if 'video_url' in product_update:
        video_url_value = product_update.get('video_url')
    variants_payload_value = ctrl._UNSET
    if 'variants' in product_update or 'variants_json' in product_update:
        variants_payload_value = product_update.get('variants', product_update.get('variants_json'))
    visibility_regions_value = product_update.get('visibility_regions', ctrl._UNSET)
    is_new_value = product_update.get('is_new', ctrl._UNSET)
    return ctrl.update_supplier_product(product_id=product_id, name=product_update.get('name'), description=product_update.get('description'), price=product_update.get('price'), stock_quantity=product_update.get('stock_quantity', product_update.get('stock')), category=product_update.get('category'), subcategory=product_update.get('subcategory', product_update.get('sub_category')), color=product_update.get('color'), is_active=product_update.get('is_active'), tags=product_update.get('tags'), sizes=product_update.get('sizes'), materials=product_update.get('materials'), visibility_regions=visibility_regions_value, weight=product_update.get('weight'), dimensions=product_update.get('dimensions'), compare_price=compare_price_value, discount_starts_at=discount_starts_at_value, discount_ends_at=discount_ends_at_value, return_window_days=return_window_days_value, video_url=video_url_value, variants_payload=variants_payload_value, is_new=is_new_value, image=image, additional_images=[file for file in additional_images if file and file.filename], current_user=current_user, db=db)

async def process_image_ai(current_user: dict=Depends(require_roles('supplier', 'admin')), image: UploadFile=File(...), generate_angles: bool=Form(True)):
    """Enqueue AI image processing as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job
    removes the background and optionally generates novel-angle views.
    """
    import uuid
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail='Empty image file')
    owner_id = current_user.get('id') or current_user.get('user_id')
    owner_role = current_user.get('role', 'supplier')
    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or 'image/jpeg')

    def _run_process_image() -> dict:
        from domains.suppliers.services.supplier_controller import process_product_image
        from io import BytesIO
        from fastapi import UploadFile
        import asyncio
        upload = UploadFile(filename=image.filename or 'image.jpg', file=BytesIO(raw))
        result = asyncio.run(process_product_image(image=upload, generate_angles=generate_angles, current_user=current_user))
        return result
    job = enqueue_ml_job(owner_user_id=owner_id, owner_role=owner_role, func=_run_process_image, metadata={'generate_angles': generate_angles}, max_retries=1)
    return {'job_id': job['id'], 'status': 'queued'}

async def create_product(request: Request, current_user: dict=Depends(require_roles('supplier', 'admin')), name: Optional[str]=Form(None), description: str=Form(''), price: Optional[float]=Form(None), stock_quantity: Optional[int]=Form(None), category: Optional[str]=Form(None), subcategory: Optional[str]=Form(None), brand: Optional[str]=Form(None), color: Optional[str]=Form(None), is_active: bool=Form(True), tags: Optional[str]=Form(None), sizes: Optional[str]=Form(None), materials: Optional[str]=Form(None), visibility_regions: Optional[str]=Form(None), weight: Optional[float]=Form(None), dimensions: Optional[str]=Form(None), compare_price: Optional[float]=Form(None), discount_starts_at: Optional[datetime]=Form(None), discount_ends_at: Optional[datetime]=Form(None), return_window_days: Optional[int]=Form(None), video_url: Optional[str]=Form(None), variants_json: Optional[str]=Form(None), variant_axes_json: Optional[str]=Form(None), countries: Optional[str]=Form(None), weight_kg: Optional[float]=Form(None), saso_cert: Optional[str]=Form(None), halal_compliance: bool=Form(False), name_ar: Optional[str]=Form(None), description_ar: Optional[str]=Form(None), image: UploadFile=File(None), additional_images: List[UploadFile]=File(default=[]), video: UploadFile=File(None), process_magic_erase: bool=Form(False), process_smart_crop: bool=Form(False), process_rotate: bool=Form(False), process_auto_light: bool=Form(False), process_upscale: bool=Form(False), process_white_balance: bool=Form(False), process_denoise: bool=Form(False), process_sharpen: bool=Form(False), process_compress: bool=Form(False), process_webp_convert: bool=Form(False), process_color_enhance: bool=Form(False), process_auto_levels: bool=Form(False), bg_preset: Optional[str]=Form(None), db: Session=Depends(get_db)):
    if 'application/json' in request.headers.get('content-type', ''):
        payload = cast(dict[str, Any], await request.json())
        name = payload.get('name')
        description = payload.get('description') or ''
        price = payload.get('price')
        stock_quantity = payload.get('stock_quantity', payload.get('stock'))
        category = payload.get('category')
        subcategory = payload.get('subcategory', payload.get('sub_category'))
        brand = payload.get('brand')
        color = payload.get('color')
        is_active = payload.get('is_active', True)
        tags = payload.get('tags')
        sizes = payload.get('sizes')
        materials = payload.get('materials')
        visibility_regions = payload.get('visibility_regions')
        weight = payload.get('weight')
        dimensions = payload.get('dimensions')
        compare_price = payload.get('compare_price', payload.get('discount_price'))
        discount_starts_at = ctrl._parse_optional_datetime(payload.get('discount_starts_at'))
        discount_ends_at = ctrl._parse_optional_datetime(payload.get('discount_ends_at'))
        return_window_days = payload.get('return_window_days')
        video_url = payload.get('video_url')
        variants_json = payload.get('variants')
        variant_axes_json = payload.get('variant_axes') or payload.get('variant_axes_json')
        countries = payload.get('countries')
        weight_kg = payload.get('weight_kg')
        saso_cert = payload.get('saso_cert')
        halal_compliance = payload.get('halal_compliance', False)
        name_ar = payload.get('name_ar')
        description_ar = payload.get('description_ar')
    if name is None or price is None or stock_quantity is None or (category is None):
        raise HTTPException(status_code=422, detail='name, price, stock_quantity and category are required')
    if countries and (not visibility_regions):
        visibility_regions = countries
    if weight_kg is not None and weight is None:
        weight = weight_kg
    from domains.logistics.services.shipping_tier import resolve_shipping_tier
    shipping_tier = resolve_shipping_tier(weight_kg=weight, dimensions=dimensions)
    from domains.comms.services.content_service import moderate_content
    moderation = moderate_content(text=f"{name or ''} {description or ''}", category=category or '')
    extra_attributes = {'shipping_tier': shipping_tier, 'moderation': moderation}
    if saso_cert:
        extra_attributes['saso_cert'] = saso_cert
    if halal_compliance:
        extra_attributes['halal_compliance'] = True
    if name_ar:
        extra_attributes['name_ar'] = name_ar
    if description_ar:
        extra_attributes['description_ar'] = description_ar
    return ctrl.create_supplier_product(name=name, description=description, price=price, stock_quantity=stock_quantity, category=category, subcategory=subcategory, is_active=is_active, brand=brand, color=color, tags=tags, sizes=sizes, materials=materials, visibility_regions=visibility_regions, weight=weight, dimensions=dimensions, compare_price=compare_price, discount_starts_at=discount_starts_at, discount_ends_at=discount_ends_at, return_window_days=return_window_days, video_url=video_url, video=video if video is not None and getattr(video, 'filename', None) else None, variants_payload=variants_json, variant_axes=variant_axes_json, extra_attributes=extra_attributes, image=image, additional_images=[file for file in additional_images if file and file.filename], current_user=current_user, db=db, image_tools={'magic_erase': process_magic_erase, 'smart_crop': process_smart_crop, 'rotate': process_rotate, 'auto_light': process_auto_light, 'upscale': process_upscale, 'white_balance': process_white_balance, 'denoise': process_denoise, 'sharpen': process_sharpen, 'compress': process_compress, 'webp_convert': process_webp_convert, 'color_enhance': process_color_enhance, 'auto_levels': process_auto_levels}, bg_preset=bg_preset)

async def analyze_async(current_user: dict=Depends(require_roles('supplier', 'admin')), image: UploadFile=File(...)):
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
        raise HTTPException(status_code=400, detail='Empty image file')
    owner_id = current_user.get('id') or current_user.get('user_id')
    owner_role = current_user.get('role', 'supplier')
    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    image_url = _storage.save(image_key, raw, content_type=image.content_type or 'image/jpeg')

    def _run_analysis() -> dict:
        import asyncio
        from domains.finance.services.shared.bg_removal_service import remove_background
        from domains.finance.services.shared.ai_variant_config import analyze_product_image
        from infrastructure.utils.storage import storage as _store
        bg_result = remove_background(raw, strategy='general', fast_mode=True)
        ai_result = asyncio.run(analyze_product_image(raw, filename=image.filename or '', generate_copy=True))
        bg_key = f'supplier_uploads/{uuid.uuid4().hex}_nobg.png'
        bg_url = _store.save(bg_key, bg_result, content_type='image/png')
        return {'bg_removed_url': bg_url, 'product_name': ai_result.get('product_name_hint', ''), 'suggested_category': ai_result.get('suggested_category', ''), 'suggested_subcategory': ai_result.get('suggested_subcategory', ''), 'suggested_brand': ai_result.get('suggested_brand', ''), 'product_description': ai_result.get('product_description', ''), 'suggested_tags': ai_result.get('suggested_tags', []), 'detected_colors': ai_result.get('detected_attributes', {}).get('color', []), 'detected_materials': ai_result.get('detected_attributes', {}).get('material', []), 'variant_options': ai_result.get('variant_options', {}), 'suggested_variants': ai_result.get('suggested_variants', []), 'price_suggestion': ai_result.get('ai_suggested_price', 0), 'price_min': ai_result.get('price_min', 0), 'price_max': ai_result.get('price_max', 0), 'stock_hints': ai_result.get('stock_hints', {}), 'photo_analysis': ai_result.get('photo_analysis', {}), 'source': ai_result.get('source', 'heuristic_fallback')}
    job = enqueue_ml_job(owner_user_id=owner_id, owner_role=owner_role, func=_run_analysis, metadata={'image_key': image_key}, max_retries=1)
    return {'job_id': job['id'], 'status': 'queued'}

async def remove_background(current_user: dict=Depends(require_roles('supplier', 'admin')), image: UploadFile=File(...), preset: str=Form('general'), model: str=Form(''), fast_mode: bool=Form(False)):
    """Enqueue background removal as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. This keeps
    rembg inference off the HTTP worker so upload bursts can't freeze the API.
    """
    import uuid
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail='Empty image file')
    owner_id = current_user.get('id') or current_user.get('user_id')
    owner_role = current_user.get('role', 'supplier')
    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or 'image/jpeg')

    def _run_remove_background() -> dict:
        from domains.finance.services.shared.bg_removal_service import remove_background_model
        from domains.finance.services.shared.bg_removal_service import AVAILABLE_MODELS
        from domains.finance.services.shared.bg_removal_service import VALID_STRATEGIES
        from infrastructure.utils.storage import storage as _store
        if model and model in AVAILABLE_MODELS:
            processed = remove_background_model(raw, model, fast_mode=fast_mode)
        else:
            preset_effective = preset if preset in VALID_STRATEGIES else 'general'
            from domains.finance.services.shared.bg_removal_service import remove_background
            processed = remove_background(raw, strategy=preset_effective, fast_mode=fast_mode)
        out_key = f'supplier_uploads/{uuid.uuid4().hex}_nobg.png'
        out_url = _store.save(out_key, processed, content_type='image/png')
        return {'bg_removed_url': out_url, 'bytes_len': len(processed)}
    job = enqueue_ml_job(owner_user_id=owner_id, owner_role=owner_role, func=_run_remove_background, metadata={'preset': preset, 'model': model, 'fast_mode': fast_mode}, max_retries=1)
    return {'job_id': job['id'], 'status': 'queued'}

async def nlp_extract(current_user: dict=Depends(require_roles('supplier', 'admin')), transcript: str=Form(...)):
    """Extract structured product data from a voice transcript using NLP.

    Accepts a natural-language product description (e.g. "A T-shirt, 4 colors:
    blue, yellow, black, white, having print 'I love Oman'") and returns
    structured fields: product name, category, colors, variants, tags,
    description, fabric, print text, stock hints.

    Uses Ollama (phi3:mini) for extraction with heuristic fallbacks.
    Never 500s.
    """
    if not transcript.strip():
        raise HTTPException(status_code=400, detail='Empty transcript')
    import json, re
    from domains.finance.services.shared.ai_variant_config import _ollama_chat
    from domains.finance.services.shared.ai_variant_config import _OLLAMA_TEXT_MODEL
    from domains.finance.services.shared.ai_variant_config import _extract_json
    canonical_list = 'Clothing, Electronics, Home & Kitchen, Beauty, Sports, Books, Toys, Automotive, Grocery, Health, Jewelry, Office, Pet Supplies, Shoes, Bags, Furniture'
    en_prompt = f'You are a product data extraction assistant for an Oman/GCC marketplace.\nGiven the voice transcript below, extract structured product data.\nChoose the category from exactly this list: {canonical_list}.\nTRANSCRIPT: ' + transcript + '\n\nReply ONLY with valid JSON (double quotes, no markdown, no commentary).\n{\n  "product_name": "best guess product name (REQUIRED)",\n  "category": "one from the list or null",\n  "subcategory": "subcategory or null",\n  "colors": ["extracted colors"],\n  "fabric": "fabric type or null",\n  "print_text": "any print/pattern text or null",\n  "description": "2-3 sentence auto-generated product description",\n  "suggested_tags": ["8-12 lowercase SEO tags"],\n  "variants": {"color": ["Blue","Black"], "size": ["S","M","L"]},\n  "stock_hints": {"Blue": {"S": 0, "M": 0, "L": 0}},\n  "quantity": null,\n  "price": null\n}'
    try:
        content = await _ollama_chat(_OLLAMA_TEXT_MODEL, en_prompt, num_predict=400, temperature=0.2)
    except Exception:
        content = None
    parsed = _extract_json(content) if content else None
    if parsed and parsed.get('product_name'):
        return parsed
    txt = transcript.lower()
    colors_found = [c for c in ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'orange', 'pink', 'brown', 'gray', 'grey', 'navy', 'gold', 'silver', 'beige', 'cream', 'maroon', 'teal', 'lavender'] if c in txt]
    sizes_found = [s for s in ['s', 'm', 'l', 'xl', 'xxl', 'xs', 'small', 'medium', 'large', 'extra large', 'x-large', 'xx-large'] if re.search('\\b' + s + '\\b', txt)]
    return {'product_name': transcript[:80].strip() if len(transcript) > 5 else 'Unknown Product', 'category': None, 'subcategory': None, 'colors': colors_found or ['Default'], 'fabric': None, 'print_text': None, 'description': transcript, 'suggested_tags': [t for t in re.findall('\\b[a-z]{4,}\\b', txt)][:10], 'variants': {'Color': colors_found, 'Size': sizes_found} if colors_found and sizes_found else {'Color': colors_found} if colors_found else {}, 'stock_hints': {}, 'quantity': None, 'price': None}

async def generate_angles(current_user: dict=Depends(require_roles('supplier', 'admin')), image: UploadFile=File(...)):
    """Enqueue AI angle generation as an ML job and return ``job_id``.

    Poll ``GET /supplier/upload/jobs/{job_id}`` for the result. The job
    removes the background and creates novel-angle product views.
    """
    import uuid
    from infrastructure.utils.background_jobs import enqueue_ml_job
    from infrastructure.utils.storage import storage as _storage
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail='Empty image file')
    owner_id = current_user.get('id') or current_user.get('user_id')
    owner_role = current_user.get('role', 'supplier')
    image_key = f"analysis_input/{uuid.uuid4().hex}_{image.filename or 'image'}"
    _storage.save(image_key, raw, content_type=image.content_type or 'image/jpeg')

    def _run_generate_angles() -> dict:
        from domains.suppliers.services.supplier_controller import process_product_image
        from io import BytesIO
        from fastapi import UploadFile
        import asyncio
        upload = UploadFile(filename=image.filename or 'image.jpg', file=BytesIO(raw))
        result = asyncio.run(process_product_image(image=upload, generate_angles=True, current_user=current_user))
        return result
    job = enqueue_ml_job(owner_user_id=owner_id, owner_role=owner_role, func=_run_generate_angles, metadata={'generate_angles': True}, max_retries=1)
    return {'job_id': job['id'], 'status': 'queued'}
