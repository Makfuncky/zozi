"""Async AI country research endpoints."""
from __future__ import annotations
import logging
from typing import Any, Dict
from fastapi import HTTPException
from pydantic import BaseModel
from domains.finance.services.shared.ai_research_jobs import decrement_running_jobs
from domains.finance.services.shared.ai_research_jobs import enqueue_job
from domains.finance.services.shared.ai_research_jobs import get_completed_result
from domains.finance.services.shared.ai_research_jobs import get_job
from domains.finance.services.shared.ai_research_jobs import increment_running_jobs
from domains.finance.services.shared.ai_research_jobs import mark_job_failed
from domains.finance.services.shared.ai_research_jobs import mark_job_running
from domains.finance.services.country.country_ai_research import CountryAIResearchService
from infrastructure.utils.config import settings
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
