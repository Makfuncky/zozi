"""AI image router — product image analysis."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from models import User
from utils.config import settings
from utils.dependencies import require_supplier

router = APIRouter()

@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...), current_user: User = Depends(require_supplier)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI service not configured")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large")
    # TODO: integrate OpenAI Vision for image analysis
    return {"tags": [], "description": "AI analysis coming soon", "suggested_category": None}

