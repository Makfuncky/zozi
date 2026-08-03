"""AI image router — product image analysis."""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from data.models import User
from utils.dependencies import require_supplier
from utils.config import settings


router = APIRouter()


class AIImageAnalysisRequest(BaseModel):
    file: UploadFile = Field(..., description="Image file to analyze")


class AIImageAnalysisResponse(BaseModel):
    tags: List[str] = Field(default_factory=list, description="Detected tags")
    description: str = Field(description="AI-generated description")
    suggested_category: Optional[str] = Field(None, description="Suggested category")
    colors: List[str] = Field(default_factory=list, description="Detected colors")
    confidence: float = Field(ge=0, le=1, description="Confidence score")


@router.post("/analyze-image", response_model=AIImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...), current_user: User = Depends(require_supplier)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI service not configured")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large")
    return {"tags": [], "description": "AI analysis coming soon", "suggested_category": None, "colors": [], "confidence": 0.0}

