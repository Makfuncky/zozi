"""Tests for ai_research_jobs.py — Redis-backed job tracker."""
import pytest
from unittest.mock import MagicMock

from services.ai_research_jobs import (
    enqueue_job,
    get_job,
    mark_job_running,
    mark_job_completed,
    mark_job_failed,
    get_completed_result,
    count_running_jobs,
    increment_running_jobs,
    decrement_running_jobs,
    _in_memory_store,
)


@pytest.fixture(autouse=True)
def clear_in_memory_store():
    _in_memory_store.clear()
    yield


@pytest.fixture
def sample_payload():
    return {
        "country_code": "IN",
        "base_report": {"module_01_country_identity": {"official_name": "Republic of India"}},
        "demographics": {"population": 1400000000},
        "economy": {"gdp_usd": 3940000000000.0},
        "news": [],
        "evidence": {},
    }


class TestEnqueueJob:
    def test_enqueue_returns_job_with_id(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        assert "job_id" in job
        assert job["country_code"] == "IN"
        assert job["status"] == "queued"
        assert job["payload"] == sample_payload
        assert job["error"] is None

    def test_enqueue_sets_created_and_updated_timestamps(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        assert "created_at_utc" in job
        assert "updated_at_utc" in job
        assert job["created_at_utc"] == job["updated_at_utc"]


class TestGetJob:
    def test_get_job_returns_job_after_enqueue(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        retrieved = get_job(job["job_id"])
        assert retrieved is not None
        assert retrieved["job_id"] == job["job_id"]
        assert retrieved["status"] == "queued"

    def test_get_job_returns_none_for_missing_id(self):
        assert get_job("nonexistent") is None


class TestMarkJobRunning:
    def test_mark_job_running_updates_status(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        result = mark_job_running(job["job_id"], ttl_seconds=3600)
        assert result is True
        updated = get_job(job["job_id"])
        assert updated["status"] == "running"

    def test_mark_job_running_returns_false_for_missing_job(self):
        assert mark_job_running("nonexistent", ttl_seconds=3600) is False


class TestMarkJobCompleted:
    def test_mark_job_completed_updates_status_and_stores_result(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        result_data = {"module_01_country_identity": {"official_name": "Republic of India"}}
        result = mark_job_completed(job["job_id"], result_data, ttl_seconds=3600)
        assert result is True
        updated = get_job(job["job_id"])
        assert updated["status"] == "completed"
        assert updated.get("error") is None

        retrieved_result = get_completed_result(job["job_id"])
        assert retrieved_result == result_data

    def test_mark_job_completed_returns_false_for_missing_job(self):
        assert mark_job_completed("nonexistent", {}, ttl_seconds=3600) is False


class TestMarkJobFailed:
    def test_mark_job_failed_updates_status_and_stores_error(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        result = mark_job_failed(job["job_id"], "Something went wrong", ttl_seconds=3600)
        assert result is True
        updated = get_job(job["job_id"])
        assert updated["status"] == "failed"
        assert updated["error"] == "Something went wrong"

    def test_mark_job_failed_returns_false_for_missing_job(self):
        assert mark_job_failed("nonexistent", "error", ttl_seconds=3600) is False


class TestRunningJobsCounter:
    def test_increment_decrement_running_jobs(self):
        increment_running_jobs()
        count = count_running_jobs()
        assert isinstance(count, int)
        assert count >= 1
        decrement_running_jobs()
        final = count_running_jobs()
        assert final < count

    def test_decrement_running_jobs_does_not_go_negative(self):
        decrement_running_jobs()
        decrement_running_jobs()
        count = count_running_jobs()
        assert count >= 0


class TestGetCompletedResult:
    def test_get_completed_result_returns_none_for_non_completed_job(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        assert get_completed_result(job["job_id"]) is None

    def test_get_completed_result_returns_data_after_completion(self, sample_payload):
        job = enqueue_job("IN", sample_payload, ttl_seconds=3600)
        result_data = {"enriched": True}
        mark_job_completed(job["job_id"], result_data, ttl_seconds=3600)
        assert get_completed_result(job["job_id"]) == result_data