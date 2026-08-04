"""Tests for background job execution with idempotency and locking."""
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

os.environ["APP_ENV"] = "test"
os.environ["PYTEST_CURRENT_TEST"] = "1"

from utils.background_jobs import (
    enqueue_job,
    cancel_job,
    get_job,
    job_stats,
    get_running_jobs,
    enqueue_ml_job,
    enqueue_bulk_import_job,
    _compute_idempotency_key,
    _check_idempotency,
    JobKind,
)


def _dummy_func(result: str = "ok"):
    return result


def _failing_func():
    raise ValueError("simulated failure")


class TestEnqueueJob:
    def test_enqueue_job_returns_payload(self):
        job = enqueue_job(kind=JobKind.DEFAULT, func=_dummy_func)
        assert job["status"] == "completed"
        assert job["result"] == "ok"
        assert "id" in job
        assert job["kind"] == JobKind.DEFAULT

    def test_enqueue_job_with_metadata(self):
        job = enqueue_job(
            kind=JobKind.EMAIL,
            owner_user_id=42,
            owner_role="admin",
            metadata={"source": "test"},
            func=_dummy_func,
        )
        assert job["owner_user_id"] == 42
        assert job["owner_role"] == "admin"
        assert job["metadata"]["source"] == "test"

    def test_enqueue_job_failure(self):
        job = enqueue_job(kind=JobKind.DEFAULT, func=_failing_func)
        assert job["status"] == "failed"
        assert "simulated failure" in job["error"]

    def test_enqueue_job_retries(self):
        call_count = 0

        def _retry_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("transient failure")
            return "success"

        job = enqueue_job(kind=JobKind.DEFAULT, func=_retry_then_succeed, max_retries=2)
        assert job["status"] == "completed"
        assert job["result"] == "success"

    def test_enqueue_ml_job(self):
        job = enqueue_ml_job(func=_dummy_func)
        assert job["kind"] == JobKind.ML

    def test_enqueue_bulk_import_job(self):
        job = enqueue_bulk_import_job(func=_dummy_func)
        assert job["kind"] == JobKind.BULK_IMPORT


class TestIdempotency:
    def test_idempotency_key_deduplicates(self):
        job1 = enqueue_job(
            kind=JobKind.DEFAULT,
            func=_dummy_func,
            idempotency_key="test-dedup-1",
            lock_ttl=60,
        )
        assert job1["status"] == "completed"
        assert job1["dedup_key"] is not None

        job2 = enqueue_job(
            kind=JobKind.DEFAULT,
            func=_dummy_func,
            idempotency_key="test-dedup-1",
            lock_ttl=60,
        )
        assert job2["id"] == job1["id"]

    def test_idempotency_key_mismatch_allows_new(self):
        job1 = enqueue_job(
            kind=JobKind.DEFAULT,
            func=_dummy_func,
            idempotency_key="dedup-a",
        )
        job2 = enqueue_job(
            kind=JobKind.DEFAULT,
            func=_dummy_func,
            idempotency_key="dedup-b",
        )
        assert job1["id"] != job2["id"]

    def test_compute_idempotency_key(self):
        key = _compute_idempotency_key(JobKind.DEFAULT, {"idempotency_key": "hello"})
        assert key is not None
        assert len(key) == 64  # sha256 hex

        key2 = _compute_idempotency_key(JobKind.DEFAULT, None)
        assert key2 is None


class TestCancelJob:
    def test_cancel_queued_job(self):
        job = enqueue_job(
            kind=JobKind.DEFAULT,
            func=lambda: (_ for _ in ()).throw(Exception("never runs")),
            idempotency_key="cancel-test",
        )
        # The job is already completed (inline mode), can't cancel
        if job["status"] in ("completed", "failed"):
            result = cancel_job(job["id"])
            assert result is False
        else:
            result = cancel_job(job["id"])
            assert result is True

    def test_cancel_nonexistent_job(self):
        result = cancel_job("nonexistent-id")
        assert result is False


class TestJobStats:
    def test_job_stats(self):
        stats = job_stats()
        assert "running" in stats
        assert "max_concurrent" in stats
        assert "active_by_kind" in stats
        assert "kind_limits" in stats

    def test_get_running_jobs(self):
        running = get_running_jobs()
        assert isinstance(running, list)

    def test_get_running_jobs_by_kind(self):
        running = get_running_jobs(kind=JobKind.ML)
        assert isinstance(running, list)


class TestJobPersistence:
    def test_get_job_returns_payload(self):
        job = enqueue_job(kind=JobKind.DEFAULT, func=_dummy_func)
        retrieved = get_job(job["id"])
        assert retrieved is not None
        assert retrieved["id"] == job["id"]
        assert retrieved["status"] == "completed"

    def test_get_nonexistent_job(self):
        assert get_job("no-such-job") is None

    def test_job_has_dedup_key_field(self):
        job = enqueue_job(
            kind=JobKind.DEFAULT,
            func=_dummy_func,
            idempotency_key="dedup-field-test",
        )
        assert "dedup_key" in job

    def test_job_without_dedup(self):
        job = enqueue_job(kind=JobKind.DEFAULT, func=_dummy_func)
        assert job.get("dedup_key") is None
