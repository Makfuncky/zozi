"""Search routes — text, AI-powered, voice, visual, autocomplete, and recommendations."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user, get_optional_user
from controllers.search_controller import get_recommendations, smart_search
from db.database import get_db
from services.advanced_filter_service import AdvancedFilterService
from services.advanced_search_engine import AdvancedSearchEngine
from services.ai_search_service import AISearchService
from providers.image import process_image_search
from providers.voice_to_text import transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/voice")
async def voice_search(
    audio: UploadFile = File(None),
    text: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Voice search — accepts raw audio (transcribed via Whisper) OR pre-transcribed text.

    The frontend Web Speech API can send the transcript as `text` directly.
    For server-side whisper transcription, send the audio file as `audio`.

    Returns the transcript so the client can pass it to GET /search/filtered.
    """
    if text:
        transcript = text.strip()
    elif audio:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")
        transcript = transcribe_audio(audio_bytes) or ""
        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'audio' (file upload) or 'text' (transcript string)",
        )

    # Parse the transcript through the NLP engine for structured intent
    engine = AdvancedSearchEngine(db)
    parsed = engine.parse_query(transcript)

    return {
        "transcript": transcript,
        "parsed_query": parsed,
    }


@router.get("")
def search(
    response: Response,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return smart_search(q=q, limit=limit, db=db, response=response)


@router.get("/products")
def search_products(
    response: Response,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    supplier_id: int | None = None,
    db: Session = Depends(get_db),
):
    return smart_search(q=q, limit=limit, db=db, response=response, supplier_id=supplier_id)


@router.get("/recommendations")
def recommendations(
    limit: int = Query(8, ge=1, le=24),
    recent_categories: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    categories = [item.strip() for item in (recent_categories or "").split(",") if item.strip()]
    return get_recommendations(user_id=int(current_user["id"]), db=db, limit=limit, recent_categories=categories)


@router.get("/recommendations/public")
def public_recommendations(
    limit: int = Query(8, ge=1, le=24),
    recent_categories: str | None = None,
    current_user: dict | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    categories = [item.strip() for item in (recent_categories or "").split(",") if item.strip()]
    user_id = int(current_user["id"]) if current_user is not None else None
    return get_recommendations(user_id=user_id, db=db, limit=limit, recent_categories=categories)


@router.get("/filters")
def get_available_filters(
    response: Response,
    category_id: int | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = AdvancedFilterService(db)
    filters = service.get_available_filters(category_id=category_id, search_query=q)
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"filters": filters}


@router.get("/filters/summary")
def get_filters_summary(
    response: Response,
    category_id: int | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = AdvancedFilterService(db)
    summary = service.get_active_filters_summary(category_id=category_id, search_query=q)
    response.headers["Cache-Control"] = "public, max-age=60"
    return summary


@router.get("/advanced")
def advanced_search_endpoint(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    brands: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    has_video: bool = Query(False),
    sort_by: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|rating|newest)$"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    engine = AdvancedSearchEngine(db)
    filters = {
        "min_price": min_price,
        "max_price": max_price,
        "brands": brands,
        "min_rating": min_rating,
        "has_video": has_video,
    }
    return engine.search(
        query=q,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )


@router.get("/ai")
def ai_powered_search(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    ai_service = AISearchService(db)
    return ai_service.search_with_intent(
        query=q,
        limit=limit,
        offset=offset,
        category_id=category_id,
    )


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    engine = AdvancedSearchEngine(db)
    return {"suggestions": engine.get_autocomplete_suggestions(query=q, limit=limit)}


@router.post("/visual")
async def visual_search(
    image: UploadFile = File(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Visual similarity search — upload an image and find visually similar products.

    Accepts an image file, processes it through the AI image service,
    and returns visually similar products ranked by similarity score.
    """
    image_bytes = await image.read()
    result = await process_image_search(image_bytes=image_bytes, db=db, limit=limit)
    return result


@router.get("/trending")
def get_trending_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    ai_service = AISearchService(db)
    return {"queries": ai_service.get_trending_searches(limit=limit)}


@router.get("/fuzzy")
def fuzzy_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    cutoff: float = Query(0.6, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    engine = AdvancedSearchEngine(db)
    return engine.fuzzy_search(query=q, limit=limit, cutoff=cutoff)


@router.get("/predict")
def get_word_predictions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    engine = AdvancedSearchEngine(db)
    return {"predictions": engine.get_word_predictions(query=q, limit=limit)}


@router.post("/filtered")
def get_filtered_products(
    filters: Dict[str, Any],
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    service = AdvancedFilterService(db)
    return service.get_filtered_products(filters=filters, limit=limit, offset=offset)


