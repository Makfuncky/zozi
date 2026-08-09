"""Async AI country research endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.ai_research_jobs import (
    decrement_running_jobs,
    enqueue_job,
    get_completed_result,
    get_job,
    increment_running_jobs,
    mark_job_failed,
    mark_job_running,
)
from services.country_ai_research import CountryAIResearchService
from utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/country-research", tags=["country-research-ai"])


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


@router.post("/ai", response_model=AIResearchResponse)
async def queue_ai_research(request: AIResearchRequest) -> AIResearchResponse:
    if not getattr(settings, "country_ai_enabled", True):
        raise HTTPException(status_code=503, detail="Country AI research is disabled by configuration.")

    max_jobs = int(getattr(settings, "country_ai_max_concurrent_jobs", 5) or 5)
    running = increment_running_jobs()
    try:
        if running > max_jobs:
            decrement_running_jobs()
            raise HTTPException(status_code=429, detail="Too many concurrent AI research jobs. Try again later.")
    except Exception:
        pass

    country_code = (request.country_code or "").upper().strip()
    if not country_code:
        raise HTTPException(status_code=422, detail="country_code is required.")

    ttl = int(getattr(settings, "country_ai_cache_ttl_seconds", 86400) or 86400)
    job = enqueue_job(country_code, request.model_dump(), ttl_seconds=ttl)
    job_id = job["job_id"]

    _run_ai_job(job_id, request.model_dump(), ttl)
    return AIResearchResponse(**job)


@router.get("/ai/{job_id}", response_model=AIResearchResponse)
async def get_ai_research(job_id: str) -> AIResearchResponse:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    result = get_completed_result(job_id) if job.get("status") == "completed" else None
    return AIResearchResponse(
        job_id=job.get("job_id", job_id),
        country_code=job.get("country_code", ""),
        status=job.get("status", "unknown"),
        created_at_utc=job.get("created_at_utc", ""),
        updated_at_utc=job.get("updated_at_utc", ""),
        result=result,
        error=job.get("error"),
    )


def _run_ai_job(job_id: str, payload: Dict[str, Any], ttl: int) -> None:
    try:
        import threading

        thread = threading.Thread(target=_run_sync, args=(job_id, payload, ttl), daemon=True)
        thread.start()
    except Exception as exc:
        logger.exception("Failed to start AI research job %s: %s", job_id, exc)
        mark_job_failed(job_id, str(exc), ttl_seconds=ttl)
        try:
            decrement_running_jobs()
        except Exception:
            pass


def _run_sync(job_id: str, payload: Dict[str, Any], ttl: int) -> None:
    try:
        import asyncio

        mark_job_running(job_id, ttl_seconds=ttl)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_execute_job(payload))
            mark_job_completed(job_id, result, ttl_seconds=ttl)
        finally:
            loop.close()
    except Exception as exc:
        logger.exception("AI research job %s failed: %s", job_id, exc)
        mark_job_failed(job_id, str(exc), ttl_seconds=ttl)
    finally:
        try:
            decrement_running_jobs()
        except Exception:
            pass


async def _execute_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    service = CountryAIResearchService(
        country_name=payload.get("base_report", {}).get("module_01_country_identity", {}).get("official_name")
        or payload.get("country_code", ""),
        base_report=payload.get("base_report", {}),
        demographics=payload.get("demographics", {}),
        economy=payload.get("economy", {}),
        news=payload.get("news", []) or [],
        evidence=payload.get("evidence", {}) or {},
    )
    return await service.enrich()
