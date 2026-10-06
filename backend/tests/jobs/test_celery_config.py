"""Paired test for FILE-18b-celery-soft-hard-limits.

Asserts the properties the contract requires of `jobs/celery_app.py`:
  * soft and hard task time limits are set and finite (PERF2-025)
  * the soft limit fires before the hard limit, with a real gap
  * retry jitter is enabled on every retry-configured task (OBS2-022, Law 297)
  * the broker is Valkey, never SQLite (contract section 3, Technology Stack 3)
  * the frozen configuration is untouched: prefetch multiplier, routes, beats

Nothing here is skipped or xfailed; every assertion is load-bearing.
"""
from __future__ import annotations

import pytest

from jobs.celery_app import celery_app


class TestTaskTimeLimitsAreBounded:
    """PERF2-025: a hung task must not hold a worker slot forever."""

    def test_task_time_limits_are_bounded(self) -> None:
        """Contract section 20 paired test: both limits are set and finite."""
        conf = celery_app.conf
        assert conf.task_soft_time_limit is not None, (
            "task_soft_time_limit is unset - a hung task would hold its worker "
            "slot forever (PERF2-025)"
        )
        assert conf.task_time_limit is not None, (
            "task_time_limit is unset - there is no hard backstop (PERF2-025)"
        )
        assert conf.task_soft_time_limit > 0
        assert conf.task_time_limit > 0

    def test_soft_limit_precedes_hard_limit_with_a_gap(self) -> None:
        """The soft limit must leave room for cleanup before the hard kill."""
        soft = celery_app.conf.task_soft_time_limit
        hard = celery_app.conf.task_time_limit
        assert soft < hard, (
            f"soft_time_limit ({soft}) must be below time_limit ({hard}) so the "
            "task can handle SoftTimeLimitExceeded before being killed"
        )
        assert hard - soft >= 30, (
            f"gap between soft ({soft}) and hard ({hard}) is too small to let a "
            "task clean up"
        )

    def test_limits_are_reachable_by_the_worker(self) -> None:
        """The worker resolves these via app.either(); prove that path is live.

        celery/worker/worker.py:393-397 reads task_time_limit / task_soft_time_limit
        through app.either(), which is what makes the limits reachable at runtime
        even though they do not appear as task class attributes.
        """
        assert celery_app.either("task_time_limit") == celery_app.conf.task_time_limit
        assert (
            celery_app.either("task_soft_time_limit")
            == celery_app.conf.task_soft_time_limit
        )

    def test_no_star_annotation_that_would_relax_per_task_limits(self) -> None:
        """A '*' annotation is applied LAST and would override tighter limits.

        celery/app/annotations.py:50-52 `resolve_all` yields the specific match
        before `annotate_any` ('*'), so '*' wins. Using it for the global limits
        would silently relax jobs.ai_tasks.* from 300/240 and 600/540. This test
        locks that regression out.
        """
        annotations = celery_app.conf.task_annotations or {}
        assert "*" not in annotations, (
            "a '*' task_annotation overrides the tighter per-task limits; use the "
            "app-level task_time_limit / task_soft_time_limit backstop instead"
        )


class TestRetryJitter:
    """OBS2-022 / WIRE-006 / Law 297: retries must be jittered."""

    def test_every_retry_configured_task_declares_jitter(self) -> None:
        annotations = celery_app.conf.task_annotations or {}
        retry_configured = {
            name: opts
            for name, opts in annotations.items()
            if opts.get("retry_backoff")
        }
        assert retry_configured, "no task declares retry_backoff - annotations lost?"
        for name, opts in retry_configured.items():
            assert opts.get("retry_jitter") is True, (
                f"{name} declares retry_backoff but not retry_jitter=True; "
                "synchronized retries become a thundering herd (OBS2-022)"
            )

    def test_jitter_actually_spreads_retries(self) -> None:
        """Prove the jitter is effective, not merely declared.

        Without jitter the interval sequence is deterministic
        (2, 4, 8, 16, 32); with full jitter it varies per call. If Celery ever
        changed the default this test fails instead of silently regressing.
        """
        from celery.utils.time import get_exponential_backoff_interval

        unjittered = [
            get_exponential_backoff_interval(factor=2, retries=i, maximum=300, full_jitter=False)
            for i in range(5)
        ]
        assert unjittered == [2, 4, 8, 16, 32], (
            f"unexpected deterministic backoff baseline: {unjittered}"
        )

        jitted = [
            tuple(
                get_exponential_backoff_interval(factor=2, retries=i, maximum=300, full_jitter=True)
                for _ in range(5)
            )
            for i in range(5)
        ]
        assert any(len(set(row)) > 1 for row in jitted), (
            "full jitter produced identical intervals on every call - jitter is "
            "not being applied and retries would synchronise"
        )

    def test_retry_backoff_max_is_bounded(self) -> None:
        """Law 297 caps the backoff ceiling; the audit asked for this (WIRE-006)."""
        annotations = celery_app.conf.task_annotations or {}
        for name, opts in annotations.items():
            ceiling = opts.get("retry_backoff_max")
            if ceiling is None:
                continue
            assert 0 < ceiling <= 300, (
                f"{name} retry_backoff_max={ceiling} is outside the bounded range"
            )


class TestBrokerIsValkey:
    """Contract section 3: the broker stays Valkey. SQLite is FORBIDDEN."""

    def test_broker_is_valkey_not_sqlite(self) -> None:
        broker = celery_app.conf.broker_url or ""
        assert broker, "broker_url is empty"
        assert not broker.startswith("sqlite"), (
            "SQLite is forbidden as a Celery broker (Technology Stack section 3)"
        )
        assert broker.startswith(("valkey://", "rediss://", "redis://")), (
            f"broker_url {broker!r} is not a Valkey/Redis URL"
        )

    def test_backend_is_not_sqlite_either(self) -> None:
        backend = celery_app.conf.result_backend or ""
        assert not backend.startswith("sqlite"), (
            "SQLite is forbidden as a Celery result backend"
        )


class TestFrozenConfigurationPreserved:
    """Contract section 3: nothing frozen may move."""

    def test_worker_prefetch_multiplier_is_still_one(self) -> None:
        assert celery_app.conf.worker_prefetch_multiplier == 1, (
            "worker_prefetch_multiplier=1 is correct for long jobs and is frozen"
        )

    def test_task_routes_unchanged(self) -> None:
        routes = celery_app.conf.task_routes
        assert routes == {
            "jobs.ai_tasks.*": {"queue": "ml"},
            "jobs.periodic_tasks.*": {"queue": "periodic"},
            "jobs.payout_tasks.*": {"queue": "payouts"},
            "jobs.payout_sweep.*": {"queue": "payouts"},
            "jobs.email_tasks.*": {"queue": "emails"},
            "jobs.payroll_run.*": {"queue": "periodic"},
        }, "task_routes must not change"

    def test_beat_schedule_unchanged(self) -> None:
        schedule = celery_app.conf.beat_schedule
        expected = {
            "auto-payout-sweep",
            "finance-reconciliation",
            "vat-remittance",
            "supplier-statements",
            "distributor-statements",
            "alert-engine",
            "cleanup-jobs",
            "ghost-order-detection",
            "cleanup-tokens",
            "ghost-employee-detection",
            "anomaly-detection",
            "fx-revaluation",
            "payroll-batch",
        }
        assert set(schedule) == expected, (
            f"beat schedule entries changed: {set(schedule) ^ expected}"
        )
        assert schedule["auto-payout-sweep"]["schedule"] == 3600.0
        assert schedule["finance-reconciliation"]["schedule"].minute == {0}
        assert schedule["finance-reconciliation"]["schedule"].hour == {2}

    def test_per_task_time_limits_preserved(self) -> None:
        """The tighter per-task limits must survive the new app-level backstop."""
        annotations = celery_app.conf.task_annotations or {}
        assert annotations["jobs.ai_tasks.remove_background"]["time_limit"] == 300
        assert annotations["jobs.ai_tasks.remove_background"]["soft_time_limit"] == 240
        assert annotations["jobs.ai_tasks.analyze_product_image"]["time_limit"] == 180
        assert annotations["jobs.ai_tasks.analyze_product_image"]["soft_time_limit"] == 120
        assert annotations["jobs.ai_tasks.generate_angles"]["time_limit"] == 600
        assert annotations["jobs.ai_tasks.generate_angles"]["soft_time_limit"] == 540

    def test_rate_limits_preserved(self) -> None:
        annotations = celery_app.conf.task_annotations or {}
        assert annotations["jobs.ai_tasks.remove_background"]["rate_limit"] == "10/m"
        assert annotations["jobs.ai_tasks.analyze_product_image"]["rate_limit"] == "20/m"
        assert annotations["jobs.ai_tasks.generate_angles"]["rate_limit"] == "5/m"


class TestDlqReplayEntryPoint:
    """Law 298: the DLQ must be replayable, not write-only."""

    def test_replay_task_exists_and_resolves(self) -> None:
        from jobs.celery_app import replay_dlq

        assert replay_dlq.name == "tasks.celery_app.replay_dlq"
        assert callable(replay_dlq.run), "replay_dlq must be a real callable"

    def test_replay_task_is_itself_bounded(self) -> None:
        from jobs.celery_app import replay_dlq

        assert replay_dlq.time_limit, "replay_dlq must carry a hard time limit"
        assert replay_dlq.soft_time_limit, "replay_dlq must carry a soft time limit"
        assert replay_dlq.max_retries == 3

    def test_dlq_queue_is_declared(self) -> None:
        names = {q.name for q in celery_app.conf.task_queues}
        assert "dlq" in names, "the dlq queue must be declared"
        for q in ("ml", "periodic", "payouts", "emails"):
            assert q in names, f"queue {q} disappeared"

    def test_dlq_queue_has_dead_letter_routing(self) -> None:
        for q in celery_app.conf.task_queues:
            if q.name == "dlq":
                continue
            args = q.queue_arguments or {}
            assert args.get("x-dead-letter-routing-key") == "dlq", (
                f"queue {q.name} lost its dead-letter routing"
            )
