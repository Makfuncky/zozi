"""Tests for ai_research.py router endpoints."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from data.routers_ai_research import router as ai_research_router

app = FastAPI()
app.include_router(ai_research_router)

client = TestClient(app)


class TestQueueAIResearch:
    def test_queue_ai_research_returns_job_id(self):
        with patch("utils.auth._get_redis", return_value=None), \
             patch("services.country_ai_research.CountryAIResearchService.enrich", new_callable=AsyncMock) as mock_enrich, \
             patch("routers.ai_research._run_ai_job") as mock_run:
            mock_enrich.return_value = {"module_01_country_identity": {"official_name": "India"}}
            payload = {
                "country_code": "IN",
                "base_report": {"module_01_country_identity": {"official_name": "Republic of India"}},
                "demographics": {"population": 1400000000},
                "economy": {"gdp_usd": 3940000000000.0},
                "news": [],
                "evidence": {},
            }
            response = client.post("/country-research/ai", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["country_code"] == "IN"
            assert data["status"] == "queued"

    def test_queue_ai_research_requires_country_code(self):
        with patch("utils.auth._get_redis", return_value=None):
            payload = {
                "country_code": "",
                "base_report": {},
                "demographics": {},
                "economy": {},
            }
            response = client.post("/country-research/ai", json=payload)
            assert response.status_code == 422

    def test_queue_ai_research_returns_503_when_disabled(self):
        with patch("routers.ai_research.settings") as mock_settings, \
             patch("utils.auth._get_redis", return_value=None):
            mock_settings.country_ai_enabled = False
            payload = {
                "country_code": "IN",
                "base_report": {},
                "demographics": {},
                "economy": {},
            }
            response = client.post("/country-research/ai", json=payload)
            assert response.status_code == 503


class TestGetAIResearchJob:
    def test_get_job_returns_404_for_missing_id(self):
        response = client.get("/country-research/ai/nonexistent-job-id")
        assert response.status_code == 404

    def test_get_job_returns_queued_status(self):
        from data.services_ai_research_jobs import enqueue_job
        job = enqueue_job("IN", {"country_code": "IN"}, ttl_seconds=3600)
        response = client.get(f"/country-research/ai/{job['job_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["job_id"] == job["job_id"]
        assert data["country_code"] == "IN"

    def test_get_job_returns_completed_status_with_result(self):
        from data.services_ai_research_jobs import enqueue_job, mark_job_completed
        job = enqueue_job("IN", {"country_code": "IN"}, ttl_seconds=3600)
        mark_job_completed(job["job_id"], {"module_01_country_identity": {"official_name": "India"}}, ttl_seconds=3600)
        response = client.get(f"/country-research/ai/{job['job_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] is not None

    def test_get_job_returns_failed_status(self):
        from data.services_ai_research_jobs import enqueue_job, mark_job_failed
        job = enqueue_job("IN", {"country_code": "IN"}, ttl_seconds=3600)
        mark_job_failed(job["job_id"], "Test error", ttl_seconds=3600)
        response = client.get(f"/country-research/ai/{job['job_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Test error"