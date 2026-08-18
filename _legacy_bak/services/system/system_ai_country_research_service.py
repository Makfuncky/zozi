"""Async AI country research endpoints."""
from __future__ import annotations
import logging
from typing import Any, Dict
from fastapi import HTTPException
from pydantic import BaseModel
from services.ai.ai_research_jobs import decrement_running_jobs, enqueue_job, get_completed_result, get_job, increment_running_jobs, mark_job_failed, mark_job_running
from services.ai.country_ai_research import CountryAIResearchService
from utils.config import settings
logger = logging.getLogger(__name__)

class AIResearchRequest(BaseModel):
    country_code: str
    base_report: Dict[str, Any]
    demographics: Dict[str, Any]
    economy: Dict[str, Any]
    news: list = []
    evidence: Dict[str, list] = {}

class AIResearchResponse(BaseModel):
    job_id: str
    country_code: str
    status: str
    created_at_utc: str
    updated_at_utc: str
    result: Dict[str, Any] | None = None
    error: str | None = None
