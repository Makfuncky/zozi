"""
AI Router — AI suggestion endpoints for product management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from routers.auth import get_current_user
import controllers.ai_controller as ctrl

router = APIRouter()


@router.post("/suggest")
async def ai_suggest(
    name: str = Form(""),
    description: str = Form(""),
    image: Optional[UploadFile] = File(None),
    images: List[UploadFile] = File(default=[]),
    image_url: str = Form(""),
    image_urls: List[str] = Form(default=[]),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate AI suggestions for category, tags, and description.
    Accepts an optional product name, optional description text, and an optional product image.
    """
    return ctrl.get_ai_suggestions(
        name=name,
        description=description,
        image=image,
        images=images,
        image_url=image_url,
        image_urls=image_urls,
    )


@router.post("/suggest/async")
async def ai_suggest_async(
    name: str = Form(""),
    description: str = Form(""),
    image: Optional[UploadFile] = File(None),
    images: List[UploadFile] = File(default=[]),
    image_url: str = Form(""),
    image_urls: List[str] = Form(default=[]),
    current_user: dict = Depends(get_current_user),
):
    job = ctrl.queue_ai_suggestions_job(
        name=name,
        description=description,
        image=image,
        images=images,
        image_url=image_url,
        image_urls=image_urls,
        current_user=current_user,
    )
    return JSONResponse(status_code=202, content=job)


@router.post("/suggest/text")
async def ai_suggest_text_only(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate AI suggestions using only text (no image upload).
    Body: { "name": str, "description": str }
    """
    name = body.get("name", "")
    description = body.get("description", "")
    return ctrl.get_ai_suggestions(name=name, description=description, image=None)


@router.post("/suggest/text/async")
async def ai_suggest_text_only_async(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    job = ctrl.queue_ai_text_suggestions_job(
        name=body.get("name", ""),
        description=body.get("description", ""),
        current_user=current_user,
    )
    return JSONResponse(status_code=202, content=job)


@router.post("/generate-angles")
async def generate_product_angles(
    name: str = Form(...),
    category: str = Form(""),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate AI-guided photo angle descriptions for a product.
    Upload your main product image and get descriptions + shooting tips for 5 angles:
    Front, Back, Side, Detail Shot, and In-Use.
    """
    return ctrl.get_product_angles(name=name, category=category, image=image)


@router.post("/generate-angles/async")
async def generate_product_angles_async(
    name: str = Form(...),
    category: str = Form(""),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    job = ctrl.queue_product_angles_job(
        name=name,
        category=category,
        image=image,
        current_user=current_user,
    )
    return JSONResponse(status_code=202, content=job)

