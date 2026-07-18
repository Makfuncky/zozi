"""
AI Controller — product AI suggestion business logic.
"""
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile

from services import ai_service
from utils.background_jobs import enqueue_job
from utils.config import settings

logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB for AI analysis


def _collect_upload_sources(
    image: Optional[UploadFile] = None,
    images: Optional[List[UploadFile]] = None,
    image_url: str = "",
    image_urls: Optional[List[str]] = None,
) -> tuple[list[str], list[bytes]]:
    uploads: List[UploadFile] = []
    if image and image.filename:
        uploads.append(image)
    if images:
        uploads.extend(upload for upload in images if upload and upload.filename)

    upload_filenames = [upload.filename for upload in uploads if upload.filename]

    image_bytes_list: List[bytes] = []
    seen_uploads: set[str] = set()
    for upload in uploads[:4]:
        try:
            upload_key = f"{upload.filename}:{id(upload)}"
            if upload_key in seen_uploads:
                continue
            seen_uploads.add(upload_key)
            image_bytes = upload.file.read()
            if image_bytes and len(image_bytes) <= MAX_IMAGE_SIZE:
                image_bytes_list.append(image_bytes)
        except Exception:
            continue

    upload_root = Path(settings.upload_dir).resolve()
    root_name = upload_root.name
    seen_local_paths: set[str] = set()
    referenced_urls = [image_url, *(image_urls or [])]
    for candidate_url in referenced_urls:
        if len(image_bytes_list) >= 4:
            break
        raw_value = (candidate_url or "").strip()
        if not raw_value:
            continue
        parsed = urlparse(raw_value)
        path_value = (parsed.path if parsed.scheme in {"http", "https"} else raw_value).replace("\\", "/")
        normalized_path = path_value.lstrip("/")
        candidate_path = Path(normalized_path)
        if not candidate_path.parts or candidate_path.parts[0] != root_name or ".." in candidate_path.parts:
            continue
        resolved_path = upload_root.joinpath(*candidate_path.parts[1:]).resolve()
        if resolved_path != upload_root and upload_root not in resolved_path.parents:
            continue
        local_key = resolved_path.as_posix()
        if local_key in seen_local_paths or not resolved_path.is_file():
            continue
        try:
            image_bytes = resolved_path.read_bytes()
        except OSError:
            continue
        if not image_bytes or len(image_bytes) > MAX_IMAGE_SIZE:
            continue
        seen_local_paths.add(local_key)
        upload_filenames.append(resolved_path.name)
        image_bytes_list.append(image_bytes)

    return upload_filenames, image_bytes_list


def _generate_ai_suggestions(
    name: str,
    description: str,
    upload_filenames: list[str],
    image_bytes_list: list[bytes],
) -> dict:
    primary_image_bytes = image_bytes_list[0] if image_bytes_list else None
    visual_hint = ai_service.infer_visual_product_hint(image_bytes_list)

    captions: List[str] = []
    for image_bytes in image_bytes_list:
        try:
            caption = ai_service.extract_image_caption(image_bytes)
            if caption:
                captions.append(caption)
        except Exception as exc:
            logger.warning("Image caption extraction failed: %s", exc)

    merged_caption = ai_service.merge_image_captions(captions)

    resolved_name = ai_service.infer_product_name(
        name=name,
        description=description,
        caption=merged_caption,
        filenames=upload_filenames,
    )
    if visual_hint and ai_service.is_generic_product_name(resolved_name):
        resolved_name = visual_hint.get("name", resolved_name)
    has_media_source = bool(upload_filenames)

    category_hint = resolved_name or merged_caption or description.strip() or ("product photo" if has_media_source else "")
    if not category_hint and not name.strip():
        raise HTTPException(
            status_code=400,
            detail="Provide a product name or upload a product photo for AI suggestions",
        )

    try:
        category = ai_service.suggest_category(
            category_hint,
            description,
            image_bytes=primary_image_bytes,
            caption=merged_caption,
        )
    except Exception as exc:
        logger.warning("Category suggestion failed: %s", exc)
        category = "General"

    try:
        color = ai_service.detect_palette(image_bytes_list)
    except Exception as exc:
        logger.warning("Color suggestion failed: %s", exc)
        color = None

    filename_color = ai_service.infer_color_from_filenames(upload_filenames)
    neutral_color_fallbacks = {"white", "beige", "silver"}
    if filename_color and (not color or color.strip().lower() in neutral_color_fallbacks):
        color = filename_color

    if visual_hint and visual_hint.get("color"):
        color = visual_hint["color"]

    if category == "General" and upload_filenames:
        filename_category = ai_service.infer_category_from_filenames(upload_filenames)
        if filename_category != "General":
            category = filename_category

    if visual_hint and visual_hint.get("category") and category == "General":
        category = visual_hint["category"]

    color = ai_service.refine_color_palette(
        color,
        category=category,
        name=resolved_name or name,
        description=description,
        caption=merged_caption,
        filenames=upload_filenames,
    )

    if not resolved_name and has_media_source:
        resolved_name = ai_service.infer_product_name(
            name=name,
            description=description,
            caption=merged_caption,
            filenames=upload_filenames,
            category=category,
            color=color,
        )

    if visual_hint and ai_service.is_generic_product_name(resolved_name):
        resolved_name = visual_hint.get("name", resolved_name)

    if not resolved_name:
        raise HTTPException(
            status_code=400,
            detail="Provide a product name or upload a product photo for AI suggestions",
        )

    try:
        tag_context = ". ".join(part for part in (description.strip(), merged_caption) if part).strip()
        tags = ai_service.suggest_tags(resolved_name, category, tag_context)
    except Exception as exc:
        logger.warning("Tag suggestion failed: %s", exc)
        tags = []

    try:
        material_suggestions = ai_service.suggest_material_candidates(
            resolved_name,
            category,
            description=description,
            caption=merged_caption,
            tags=tags,
        )
    except Exception as exc:
        logger.warning("Material suggestion failed: %s", exc)
        material_suggestions = []

    try:
        variant_template = ai_service.suggest_variant_template(
            resolved_name,
            category,
            tags=tags,
            description=description or merged_caption,
        )
        variant_options = ai_service.suggest_variant_options(
            resolved_name,
            category,
            tags=tags,
            description=description or merged_caption,
        )
    except Exception as exc:
        logger.warning("Variant suggestion failed: %s", exc)
        variant_template = "universal"
        variant_options = []

    color_candidates = ai_service.expand_palette_candidates(color)

    try:
        ai_description = ai_service.generate_product_description(
            name=resolved_name,
            category=category,
            image_bytes=primary_image_bytes,
            caption=merged_caption,
        )
    except Exception as exc:
        logger.warning("Description generation failed: %s", exc)
        ai_description = f"Premium {category.lower()} product: {resolved_name}."

    return {
        "name": resolved_name,
        "category": category,
        "color": color,
        "color_candidates": color_candidates,
        "tags": tags,
        "tags_string": ", ".join(tags),
        "material_suggestions": material_suggestions,
        "variant_template": variant_template,
        "variant_options": variant_options,
        "description": ai_description,
        "caption": merged_caption,
        "ai_powered": bool(ai_service.HF_API_TOKEN),
    }


def _generate_product_angles(
    name: str,
    category: str,
    image_bytes: Optional[bytes],
) -> dict:
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Product name is required")

    try:
        angles = ai_service.generate_product_angles(
            name=name,
            category=category,
            image_bytes=image_bytes,
        )
    except Exception as exc:
        logger.warning("Angle generation failed: %s", exc)
        angles = []

    return {
        "angles": angles,
        "ai_powered": bool(ai_service.HF_API_TOKEN),
        "total": len(angles),
    }


def get_ai_suggestions(
    name: str,
    description: str = "",
    image: Optional[UploadFile] = None,
    images: Optional[List[UploadFile]] = None,
    image_url: str = "",
    image_urls: Optional[List[str]] = None,
) -> dict:
    """
    Generate AI-powered suggestions for product category, color, tags, and description.
    """
    upload_filenames, image_bytes_list = _collect_upload_sources(
        image=image,
        images=images,
        image_url=image_url,
        image_urls=image_urls,
    )
    return _generate_ai_suggestions(name, description, upload_filenames, image_bytes_list)


def queue_ai_suggestions_job(
    name: str,
    description: str,
    current_user: dict,
    image: Optional[UploadFile] = None,
    images: Optional[List[UploadFile]] = None,
    image_url: str = "",
    image_urls: Optional[List[str]] = None,
) -> dict:
    upload_filenames, image_bytes_list = _collect_upload_sources(
        image=image,
        images=images,
        image_url=image_url,
        image_urls=image_urls,
    )
    return enqueue_job(
        kind="ai-suggestions",
        owner_user_id=current_user.get("id"),
        owner_role=current_user.get("role"),
        metadata={"name": name[:120], "image_count": len(image_bytes_list)},
        func=lambda: _generate_ai_suggestions(name, description, upload_filenames, image_bytes_list),
    )


def queue_ai_text_suggestions_job(name: str, description: str, current_user: dict) -> dict:
    return enqueue_job(
        kind="ai-suggestions",
        owner_user_id=current_user.get("id"),
        owner_role=current_user.get("role"),
        metadata={"name": name[:120], "image_count": 0},
        func=lambda: _generate_ai_suggestions(name, description, [], []),
    )


def get_product_angles(
    name: str,
    category: str = "",
    image: Optional[UploadFile] = None,
) -> dict:
    """
    Generate AI-guided descriptions and shooting tips for multiple product photo angles.
    """
    image_bytes: Optional[bytes] = None
    if image and image.filename:
        try:
            image_bytes = image.file.read()
            if len(image_bytes) > MAX_IMAGE_SIZE:
                image_bytes = None
        except Exception:
            image_bytes = None
    return _generate_product_angles(name, category, image_bytes)


def queue_product_angles_job(
    name: str,
    category: str,
    current_user: dict,
    image: Optional[UploadFile] = None,
) -> dict:
    image_bytes: Optional[bytes] = None
    if image and image.filename:
        try:
            candidate = image.file.read()
            if len(candidate) <= MAX_IMAGE_SIZE:
                image_bytes = candidate
        except Exception:
            image_bytes = None

    return enqueue_job(
        kind="ai-product-angles",
        owner_user_id=current_user.get("id"),
        owner_role=current_user.get("role"),
        metadata={"name": name[:120], "category": category[:120]},
        func=lambda: _generate_product_angles(name, category, image_bytes),
    )

