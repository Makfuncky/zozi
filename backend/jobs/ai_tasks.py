"""Celery tasks for AI/ML processing (background removal, image analysis, angle generation)."""
from __future__ import annotations

import base64
import io
import logging
import uuid
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.ai_tasks.remove_background",
    max_retries=2,
    default_retry_delay=60,
)
def remove_background_task(
    self,
    image_data: str,  # base64 encoded
    strategy: str = "general",
    fast_mode: bool = True,
    model: Optional[str] = None,
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """
    Remove background from an image using rembg.
    
    Args:
        image_data: Base64 encoded image bytes
        strategy: Background removal strategy (general, wood, fabric, etc.)
        fast_mode: Use faster processing mode
        model: Specific rembg model to use
        owner_user_id: ID of the user who owns this job
        owner_role: Role of the user
        
    Returns:
        Dict with bg_removed_url (base64 encoded PNG) and metadata
    """
    try:
        # Import inside task to avoid loading ML libraries in web workers
        import numpy as np
        from PIL import Image
        from domains.finance.services.shared.bg_removal_service import remove_background, remove_background_model
        from providers.storage.storage_backend import storage as _store
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Process image
        if model:
            processed = remove_background_model(image_bytes, model, fast_mode=fast_mode)
        else:
            processed = remove_background(image_bytes, strategy=strategy, fast_mode=fast_mode)
        
        # Save to storage
        out_key = f"supplier_uploads/{uuid.uuid4().hex}_nobg.png"
        out_url = _store.save(out_key, processed, content_type="image/png")
        
        # Return base64 for small images, URL for large
        if len(processed) < 1024 * 1024:  # < 1MB
            return {
                "status": "completed",
                "bg_removed_data": base64.b64encode(processed).decode("utf-8"),
                "bg_removed_url": out_url,
                "bytes_len": len(processed),
            }
        else:
            return {
                "status": "completed",
                "bg_removed_url": out_url,
                "bytes_len": len(processed),
            }
            
    except Exception as exc:
        logger.exception("Background removal task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.ai_tasks.analyze_product_image",
    max_retries=2,
    default_retry_delay=60,
)
def analyze_product_image_task(
    self,
    image_data: str,  # base64 encoded
    filename: str = "",
    generate_copy: bool = True,
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """
    Analyze a product image using AI to extract product information.
    
    Args:
        image_data: Base64 encoded image bytes
        filename: Original filename
        generate_copy: Whether to generate marketing copy
        owner_user_id: ID of the user who owns this job
        owner_role: Role of the user
        
    Returns:
        Dict with product analysis results
    """
    try:
        import asyncio
        from domains.finance.services.shared.ai_variant_config import analyze_product_image
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Run async analysis
        result = asyncio.run(analyze_product_image(
            image_bytes, 
            filename=filename, 
            generate_copy=generate_copy
        ))
        
        return {
            "status": "completed",
            **result,
        }
        
    except Exception as exc:
        logger.exception("Product image analysis task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.ai_tasks.generate_angles",
    max_retries=1,
    default_retry_delay=120,
)
def generate_angles_task(
    self,
    image_data: str,  # base64 encoded
    filename: str = "",
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generate novel-angle product views from a single image.
    
    Args:
        image_data: Base64 encoded image bytes
        filename: Original filename
        owner_user_id: ID of the user who owns this job
        owner_role: Role of the user
        
    Returns:
        Dict with generated angle images
    """
    try:
        import asyncio
        from io import BytesIO
        from fastapi import UploadFile
        from domains.suppliers.services.supplier_service import process_product_image
        from providers.storage.storage_backend import storage as _store
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Create UploadFile-like object
        upload = UploadFile(filename=filename or "image.jpg", file=BytesIO(image_bytes))
        
        # Process (this will need current_user context - mock for now)
        class MockUser:
            id = owner_user_id
            role = owner_role or "supplier"
            
        result = asyncio.run(process_product_image(
            image=upload, 
            generate_angles=True, 
            current_user=MockUser()
        ))
        
        return {
            "status": "completed",
            **result,
        }
        
    except Exception as exc:
        logger.exception("Angle generation task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.ai_tasks.nlp_extract",
    max_retries=2,
    default_retry_delay=30,
)
def nlp_extract_task(
    self,
    transcript: str,
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """
    Extract structured product data from a voice transcript using NLP.
    
    Args:
        transcript: Natural language product description
        owner_user_id: ID of the user who owns this job
        owner_role: Role of the user
        
    Returns:
        Dict with extracted product data
    """
    try:
        import json
        import re
        from domains.finance.services.shared.ai_variant_config import _ollama_chat, _OLLAMA_TEXT_MODEL, _extract_json
        
        canonical_list = 'Clothing, Electronics, Home & Kitchen, Beauty, Sports, Books, Toys, Automotive, Grocery, Health, Jewelry, Office, Pet Supplies, Shoes, Bags, Furniture'
        en_prompt = f'You are a product data extraction assistant for an Oman/GCC marketplace.\nGiven the voice transcript below, extract structured product data.\nChoose the category from exactly this list: {canonical_list}.\nTRANSCRIPT: ' + transcript + '\n\nReply ONLY with valid JSON (double quotes, no markdown, no commentary).\n{\n  "product_name": "best guess product name (REQUIRED)",\n  "category": "one from the list or null",\n  "subcategory": "subcategory or null",\n  "colors": ["extracted colors"],\n  "fabric": "fabric type or null",\n  "print_text": "any print/pattern text or null",\n  "description": "2-3 sentence auto-generated product description",\n  "suggested_tags": ["8-12 lowercase SEO tags"],\n  "variants": {"color": ["Blue","Black"], "size": ["S","M","L"]},\n  "stock_hints": {"Blue": {"S": 0, "M": 0, "L": 0}},\n  "quantity": null,\n  "price": null\n}'
        
        try:
            content = asyncio.run(_ollama_chat(_OLLAMA_TEXT_MODEL, en_prompt, num_predict=400, temperature=0.2))
        except Exception:
            content = None
            
        parsed = _extract_json(content) if content else None
        
        if parsed and parsed.get("product_name"):
            return {"status": "completed", **parsed}
            
        # Fallback heuristic
        txt = transcript.lower()
        colors_found = [c for c in ['red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'orange', 'pink', 'brown', 'gray', 'grey', 'navy', 'gold', 'silver', 'beige', 'cream', 'maroon', 'teal', 'lavender'] if c in txt]
        sizes_found = [s for s in ['s', 'm', 'l', 'xl', 'xxl', 'xs', 'small', 'medium', 'large', 'extra large', 'x-large', 'xx-large'] if re.search(r'\b' + s + r'\b', txt)]
        
        return {
            "status": "completed",
            "product_name": transcript[:80].strip() if len(transcript) > 5 else "Unknown Product",
            "category": None,
            "subcategory": None,
            "colors": colors_found or ["Default"],
            "fabric": None,
            "print_text": None,
            "description": transcript,
            "suggested_tags": [t for t in re.findall(r'\b[a-z]{4,}\b', txt)][:10],
            "variants": {"Color": colors_found, "Size": sizes_found} if colors_found and sizes_found else {"Color": colors_found} if colors_found else {},
            "stock_hints": {},
            "quantity": None,
            "price": None,
            "source": "heuristic_fallback",
        }
        
    except Exception as exc:
        logger.exception("NLP extraction task failed: %s", exc)
        raise self.retry(exc=exc)


# Health check task
@shared_task(name="tasks.ai_tasks.health_check")
def health_check() -> dict[str, str]:
    """Health check for AI task workers."""
    return {"status": "healthy", "worker": "ai_tasks"}