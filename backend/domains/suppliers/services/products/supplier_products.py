"""Supplier sub-module — imports shared helpers from supplier_shared."""

from datetime import datetime
from typing import Any, List, Optional, cast

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from infrastructure.utils.pagination import keyset_offset_window
from domains.catalog.models.products import Product
from domains.suppliers.services.supplier_shared import (
    _UNSET,
    _build_list_page_payload,
    _build_supplier_product_payload,
    _normalize_optional_product_text,
    _normalize_product_video_reference,
    _normalize_product_visibility_regions,
    _parse_product_variants_payload,
    _parse_supplier_return_window_days,
    _persist_supplier_product,
    _replace_product_variants,
)

def get_supplier_products(current_user: dict, db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    base_query = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    )
    total = base_query.count()
    sort_keys = [(Product.created_at, "desc"), (Product.id, "desc")]
    products = keyset_offset_window(
        base_query,
        sort_keys=sort_keys,
        offset=offset,
        limit=limit if limit is not None else 100,
    )

    product_ids = [cast(int, product.id) for product in products]
    sales_rows = (
        db.query(
            OrderItem.product_id.label("product_id"),
            func.count(OrderItem.id).label("sales_count"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .filter(OrderItem.product_id.in_(product_ids))
        .group_by(OrderItem.product_id)
        .all()
    ) if product_ids else []
    sales_map = {
        cast(int, row.product_id): {
            "sales_count": int(row.sales_count or 0),
            "revenue": float(row.revenue or 0),
        }
        for row in sales_rows
    }

    result = []
    for product in products:
        sales_data = sales_map.get(cast(int, product.id), {"sales_count": 0, "revenue": 0.0})

        result.append({
            **_build_supplier_product_payload(
                product,
                sales_count=int(sales_data["sales_count"]),
                revenue=float(sales_data["revenue"]),
            )
        })
    resolved_page_size = limit if limit is not None else len(result)
    return _build_list_page_payload(result, total, offset=offset, page_size=resolved_page_size)


def get_supplier_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sales_data = db.query(
        func.count(OrderItem.id).label("sales_count"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).filter(OrderItem.product_id == product.id).first()

    return _build_supplier_product_payload(
        product,
        sales_count=sales_data.sales_count or 0,
        revenue=float(sales_data.revenue or 0),
    )


def _save_upload(file: UploadFile, supplier_id: int, country_code: str = None, product_id: int = None, db: Session = None) -> str:
    """Save an uploaded product media file using hierarchical path structure."""
    from domains.comms.ports import auto_process_image, save_product_media, save_supplier_media
    return save_product_media(file, db=db, supplier_id=supplier_id, country_code=country_code, product_id=product_id or 0, is_main=False)


def _save_supplier_profile_media_upload(file: UploadFile, supplier_id: int, field: str, country_code: str = None, db: Session = None) -> str:
    """Save supplier profile media using hierarchical path structure."""
    return save_supplier_media(file, db=db, supplier_id=supplier_id, country_code=country_code, media_type=field.replace("_url", ""))


def _process_image_with_tools(data: bytes, tools: dict, bg_preset: Optional[str] = None) -> bytes:
    """Apply free image processing tools (magic_erase, smart_crop, rotate, auto_light, upscale).

    If ``bg_preset`` is set, the chosen background-removal preset is applied
    first (replacing the generic ``magic_erase`` tool to avoid double removal).
    """
    if not tools and not bg_preset:
        return data
    if bg_preset:
        try:
            from domains.finance.ports import remove_background
            data = remove_background(data, strategy=bg_preset)
        except Exception as exc:
            logger.warning("bg_preset application failed, using original: %s", exc)
        tools = {k: v for k, v in tools.items() if k != "magic_erase"}
    enabled = [k for k, v in tools.items() if v]
    if not enabled:
        return data
    try:
        return auto_process_image(data, tools=enabled)
    except Exception as exc:
        logger.warning("Image processing failed: %s", exc)
        return data


async def process_product_image(
    image: UploadFile,
    generate_angles: bool,
    current_user: dict,
) -> dict:
    """
    AI image pipeline for a product photo:
      1. Remove background → white background JPEG
      2. (optional) Generate 4 novel-angle views via zero123-plus

    Returns:
      {
        "bg_removed_url":  "uploads/supplier_X_bg_…jpg",
        "angle_urls":      ["uploads/supplier_X_angle0_….jpg", …],
        "angles_generated": 4,
                "bg_removed": true,
                "angles_notice": "..."
      }
    """
    from providers.ai.image_similarity import image_ai_service
    from infrastructure.utils.storage import storage as _storage

    raw = image.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    uid = current_user["id"]

    # -- Step 1: background removal ----------------------------------------------
    original_bytes = raw
    bg_removed_bytes = image_ai_service.remove_background(raw)
    bg_was_removed = bg_removed_bytes != original_bytes

    bg_key = f"supplier_{uid}_bg_{uuid.uuid4().hex[:8]}.jpg"
    bg_url = _storage.save(bg_key, bg_removed_bytes, content_type="image/jpeg")

    # -- Step 2: multi-angle generation -------------------------------------------
    angle_urls: list = []
    angles_notice: Optional[str] = None
    if generate_angles:
        try:
            angle_list = image_ai_service.generate_angles(original_bytes)
            for i, angle_bytes in enumerate(angle_list):
                angle_key = f"supplier_{uid}_angle{i}_{uuid.uuid4().hex[:8]}.jpg"
                angle_url = _storage.save(angle_key, angle_bytes, content_type="image/jpeg")
                angle_urls.append(angle_url)
            if not angle_urls:
                angles_notice = "Real AI angle generation is unavailable right now. Background removal was applied, but no new product views were produced."
        except Exception as exc:
            logger.warning("Angle generation failed: %s", exc)
            angles_notice = "Real AI angle generation failed for this image. Background removal was applied, but no new product views were produced."

    return {
        "bg_removed_url": bg_url,
        "angle_urls": angle_urls,
        "angles_generated": len(angle_urls),
        "bg_removed": bg_was_removed,
        "angles_notice": angles_notice,
    }


async def create_supplier_product_upload(
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    subcategory: Optional[str],
    color: Optional[str],
    brand: Optional[str],
    tags: Optional[str],
    sizes: Optional[str],
    materials: Optional[str],
    visibility_regions: Optional[object],
    weight: Optional[float],
    dimensions: Optional[str],
    compare_price: Optional[float],
    discount_starts_at: Optional[datetime],
    discount_ends_at: Optional[datetime],
    return_window_days: Optional[int],
    is_active: bool,
    video: Optional[UploadFile],
    image: Optional[UploadFile],
    additional_images: List[UploadFile],
    current_user: dict,
    db: Session,
    video_url_link: Optional[str] = None,
    image_url_link: Optional[str] = None,    # Web URL alternative to file upload
    extra_image_urls: Optional[List[str]] = None,  # Web URLs for extra images
    variants_payload: Optional[object] = None,
    image_tools: Optional[dict] = None,
    bg_preset: Optional[str] = None,
) -> Product:
    """Full supplier upload: main image + up to 20 additional gallery media files + variant details.
    Gallery media can be provided as uploads or web URLs."""
    MAX_ADDITIONAL_IMAGES = 20

    # Pre-process image through free AI tools if any are enabled
    if image and image.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
        try:
            raw = image.file.read()
            processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
            from io import BytesIO
            from fastapi import UploadFile
            image.file = BytesIO(processed)
            image.file.seek(0)
        except Exception as exc:
            logger.warning("Image pre-processing failed, using original: %s", exc)
            image.file.seek(0)

    # Resolve main image: prefer file upload, fall back to web URL or local uploads/ path
    if image and image.filename:
        image_url = _save_upload(image, current_user["id"], db=db)
    elif image_url_link and image_url_link.strip().startswith(("http://", "https://", "uploads/")):
        image_url = image_url_link.strip()
    else:
        image_url = None

    if video and video.filename:
        video_url = _save_upload(video, current_user["id"], db=db)
    else:
        video_url = _normalize_product_video_reference(video_url_link)

    # Resolve gallery media: file uploads first, then URL entries
    extra_paths: list = []
    for extra_file in additional_images:
        try:
            if extra_file and extra_file.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
                try:
                    raw = extra_file.file.read()
                    processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
                    from io import BytesIO
                    extra_file.file = BytesIO(processed)
                    extra_file.file.seek(0)
                except Exception:
                    extra_file.file.seek(0)
            path = _save_upload(extra_file, current_user["id"], db=db)
            extra_paths.append(path)
        except Exception:
            pass  # skip invalid extra images
    # Append web URL extra images
    for url in (extra_image_urls or []):
        if url and url.strip().startswith(("http://", "https://")):
            extra_paths.append(url.strip())

    if len(extra_paths) > MAX_ADDITIONAL_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"A product can include up to {MAX_ADDITIONAL_IMAGES} gallery media items",
        )

    new_product = _persist_supplier_product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        subcategory=subcategory,
        color=color,
        brand=brand,
        tags=tags,
        sizes=sizes,
        materials=materials,
        visibility_regions=visibility_regions,
        weight=weight,
        dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        is_active=is_active,
        image_url=image_url,
        video_url=video_url,
        additional_media=extra_paths,
        ai_description=None,
        variants_payload=variants_payload,
        current_user=current_user,
        db=db,
    )
    db.commit()
    _bump_product_cache_version()
    db.refresh(new_product)
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPLOAD,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="product",
        resource_id=new_product.id,
        details={"name": new_product.name, "category": new_product.category},
        status="success",
    )
    return new_product

def create_supplier_product(
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    subcategory: Optional[str],
    is_active: bool,
    image: Optional[UploadFile],
    current_user: dict,
    db: Session,
    color: Optional[str] = None,
    tags: Optional[str] = None,
    sizes: Optional[str] = None,
    materials: Optional[str] = None,
    visibility_regions: Optional[object] = None,
    weight: Optional[float] = None,
    dimensions: Optional[str] = None,
    compare_price: Optional[float] = None,
    discount_starts_at: Optional[datetime] = None,
    discount_ends_at: Optional[datetime] = None,
    return_window_days: Optional[int] = None,
    video_url: Optional[object] = None,
    video: Optional[UploadFile] = None,
    variants_payload: Optional[object] = None,
    additional_images: Optional[List[UploadFile]] = None,
    brand: Optional[str] = None,
    image_tools: Optional[dict] = None,
    bg_preset: Optional[str] = None,
    variant_axes: Optional[object] = None,
    extra_attributes: Optional[dict] = None,
) -> dict:
    # Pre-process main image through free AI tools
    if image and image.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
        try:
            raw = image.file.read()
            processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
            from io import BytesIO
            image.file = BytesIO(processed)
            image.file.seek(0)
        except Exception as exc:
            logger.warning("Image pre-processing failed, using original: %s", exc)
            image.file.seek(0)

    image_url = _save_upload(image, current_user["id"], db=db) if image and image.filename else None
    # A recorded/uploaded video file is saved like an image and its stored path
    # is used directly (already validated as MP4/WebM by save_product_media).
    # A string reference (YouTube/Vimeo/MP4 URL) goes through link normalization.
    if video is not None and getattr(video, "filename", None):
        normalized_video_url = _save_upload(video, current_user["id"], db=db)
    else:
        normalized_video_url = _normalize_product_video_reference(video_url)
    extra_paths: list[str] = []
    for extra_file in additional_images or []:
        if extra_file and extra_file.filename:
            try:
                if image_tools and any(v for v in image_tools.values()) or bg_preset:
                    try:
                        raw = extra_file.file.read()
                        processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
                        from io import BytesIO
                        extra_file.file = BytesIO(processed)
                        extra_file.file.seek(0)
                    except Exception:
                        extra_file.file.seek(0)
                extra_paths.append(_save_upload(extra_file, current_user["id"], db=db))
            except Exception:
                continue

    new_product = _persist_supplier_product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        subcategory=subcategory,
        color=color,
        brand=brand,
        tags=tags,
        sizes=sizes,
        materials=materials,
        visibility_regions=visibility_regions,
        weight=weight,
        dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        is_active=is_active,
        image_url=image_url,
        video_url=normalized_video_url,
        additional_media=extra_paths,
        ai_description=None,
        variants_payload=variants_payload,
        variant_axes=variant_axes,
        bg_preset=bg_preset,
        extra_attributes=extra_attributes,
        current_user=current_user,
        db=db,
    )
    db.commit()
    _bump_product_cache_version()
    db.refresh(new_product)

    return _build_supplier_product_payload(new_product)


def update_supplier_product(
    product_id: int,
    name: Optional[str],
    description: Optional[str],
    price: Optional[float],
    stock_quantity: Optional[int],
    category: Optional[str],
    subcategory: Optional[str],
    is_active: Optional[bool],
    image: Optional[UploadFile],
    current_user: dict,
    db: Session,
    color: Optional[str] = None,
    tags: Optional[str] = None,
    sizes: Optional[str] = None,
    materials: Optional[str] = None,
    visibility_regions: object = _UNSET,
    weight: Optional[float] = None,
    dimensions: Optional[str] = None,
    compare_price: object = _UNSET,
    discount_starts_at: object = _UNSET,
    discount_ends_at: object = _UNSET,
    return_window_days: object = _UNSET,
    video_url: object = _UNSET,
    variants_payload: object = _UNSET,
    is_new: object = _UNSET,
    additional_images: Optional[List[UploadFile]] = None,
) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if image:
        file_path = _save_upload(image, current_user["id"], db=db)
        if product.image_url and os.path.exists(product.image_url):
            os.remove(product.image_url)
        product.image_url = file_path

    if additional_images:
        existing_media: list[str] = []
        if product.images:
            try:
                parsed_media = json.loads(product.images) if isinstance(product.images, str) else product.images
                if isinstance(parsed_media, list):
                    existing_media = [str(item).strip() for item in parsed_media if str(item).strip()]
            except (json.JSONDecodeError, TypeError):
                existing_media = []

        appended_media = existing_media[:]
        for media_file in additional_images:
            if media_file and media_file.filename:
                appended_media.append(_save_upload(media_file, current_user["id"], db=db))
        product.images = json.dumps(appended_media) if appended_media else None

    if name is not None:
        product.name = html.escape(name.strip())
    if description is not None:
        product.description = html.escape(description)
    if price is not None:
        product.price = price
    if stock_quantity is not None:
        product.stock = stock_quantity
    if category is not None:
        product.category = category
    if subcategory is not None:
        product.subcategory = _normalize_optional_product_text(subcategory)
    if color is not None:
        product.color = color
    if is_active is not None:
        product.is_active = is_active
    if tags is not None:
        product.tags = tags
    if sizes is not None:
        product.sizes = sizes
    if materials is not None:
        product.materials = materials
    if visibility_regions is not _UNSET:
        normalized_visibility_regions = _normalize_product_visibility_regions(visibility_regions)
        product.visibility_regions = json.dumps(normalized_visibility_regions) if normalized_visibility_regions else None
    if weight is not None:
        product.weight = weight
    if dimensions is not None:
        product.dimensions = dimensions
    if compare_price is not _UNSET:
        product.compare_price = compare_price
    if discount_starts_at is not _UNSET:
        product.discount_starts_at = discount_starts_at
    if discount_ends_at is not _UNSET:
        product.discount_ends_at = discount_ends_at
    if return_window_days is not _UNSET:
        product.return_window_days = _parse_supplier_return_window_days(
            return_window_days,
            supplier_id=current_user["id"],
            db=db,
        )
    if is_new is not _UNSET:
        product.is_new = is_new
    if variants_payload is not _UNSET:
        _replace_product_variants(product, _parse_product_variants_payload(variants_payload), db)

    db.commit()
    _bump_product_cache_version()
    db.refresh(product)

    return _build_supplier_product_payload(product)


def delete_supplier_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_deleted = True
    db.commit()
    _bump_product_cache_version()
    return {"message": "Product deleted successfully"}


# ── Analytics ─────────────────────────────────────────────────────────────────

