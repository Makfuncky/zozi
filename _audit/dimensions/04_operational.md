# DIMENSION: Operational

## Summary
- Confirmation: ❌
- Files inspected: 18
- Files compliant: 6
- Files with findings: 12
- Laws implicated: [L-217, L-219, L-248, L-311, L-30]
- Findings: 10
- P0: 2  P1: 3  P2: 3  P3: 2
- Clusters: 2
- Average confidence: 4.5/5
- Average evidence strength: multiple
- Status: NEW: 10 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 0 partial · 8 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| OPS-001 | infra | RESOLVED | CLUSTER-health-no-fail-closed | backend/main.py:149-182 | `/health/deps` returns 200 with dependency dict even when DB/Valkey/email/payments are down | `/health/deps` must return 503 (or equivalent non-200) when any critical dependency is down, matching `/health/ready` behavior | `/health/deps` never fails closed; always returns HTTP 200 regardless of dependency health | Add `status_code=503` to `JSONResponse` when any critical dep status is `failed`/`unavailable` | S (1h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/main.py:129-138 (`/health` fails closed correctly) | `curl -f http://localhost:8000/health/deps` returns 200 when DB down | `tests/observability/test_health_checks.py::test_health_deps_fails_closed_when_db_down` | `git revert <commit>` | F-004, CHAIN-005 | none | OPS-002 | yes |
| OPS-002 | infra | RESOLVED | CLUSTER-no-ci-cd | N/A | No `.github/workflows/` directory; no CI/CD pipeline exists | CI/CD pipeline with pre-deploy migration step, health-check gate, and rollback trigger per ARCHITECTURE_STACK.md L-217/L-219 | Zero CI/CD automation; migrations and rollback are manual only | Create `.github/workflows/deploy.yml` with pre-deploy `alembic upgrade head`, `/health/ready` gate, and rollback on failure | L (8h) | P0 | 5 | triangulated | L0 | VERIFIED | `documents/01_DATABASE.md:323` (references CI/CD pre-deploy step) | `ls .github/workflows/` returns deployment workflow | `test_ci_cd_pipeline.py` (new) | `git revert <commit>` | CHAIN-001 through CHAIN-007 | none | OPS-010 | yes |
| OPS-003 | docs | INVALID | CLUSTER-no-ci-cd | docs/runbooks/: directory exists | 5 runbooks exist (slow DB, backend errors, API latency, DB pool, Sentry) | Runbooks per alert including deployment, rollback, and incident response per ARCHITECTURE_STACK.md L-248 | Missing deployment, rollback, and migration-on-deploy runbooks | Create `docs/runbooks/deployment.md`, `docs/runbooks/rollback.md`, `docs/runbooks/migration_on_deploy.md` | M (3h) | P1 | 5 | single | L0 | VERIFIED | docs/runbooks/backend_error_rate_high.md (existing runbook pattern) | `ls docs/runbooks/deployment.md docs/runbooks/rollback.md` | `test_runbooks_exist.py` (new) | `git revert <commit>` | CHAIN-005 | OPS-002 | OPS-010 | no |
| OPS-004 | infra | COMPILED | CLUSTER-raw-os-getenv-flags | backend/providers/payments/config.py:42-138 | Raw `os.getenv("STRIPE_SECRET_KEY")`, `os.getenv("TAP_SECRET_KEY")`, etc. in payment provider config | All feature flags and config values read via typed pydantic-settings `Settings` object per PROMPT_FORENSIC_AUDIT.md §7.4 | Payment provider config bypasses typed settings; reads env vars directly via `os.getenv()` | Refactor `providers/payments/config.py` to accept `settings: Settings` and use `settings.stripe_secret_key` etc. | M (3h) | P1 | 5 | triangulated | L0 | VERIFIED | backend/config.py:92-926 (typed Settings class) | `grep -rn "os.getenv" backend/providers/payments/config.py` returns zero matches | `tests/providers/test_payment_config.py::test_no_raw_os_getenv` | `git revert <commit>` | F-006, F-007, F-008 | OPS-005 | none | no |
| OPS-005 | infra | COMPILED | CLUSTER-raw-os-getenv-flags | backend/providers/geography/geo.py:144-146 | Raw `os.getenv("LOCATION_HTTP_TIMEOUT")`, `os.getenv("LOCATION_CACHE_TTL")`, `os.getenv("LOCATION_USER_AGENT")` | All config via typed pydantic-settings | Geography provider bypasses typed settings with raw `os.getenv()` | Refactor `providers/geography/geo.py` to use `settings.location_http_timeout`, `settings.location_cache_ttl`, `settings.location_user_agent` | S (1h) | P1 | 5 | single | L0 | VERIFIED | backend/config.py:280-282 (typed fields exist) | `grep -rn "os.getenv" backend/providers/geography/geo.py` returns zero matches | `tests/providers/test_geo_provider.py::test_no_raw_os_getenv` | `git revert <commit>` | F-009 | OPS-004 | none | no |
| OPS-006 | infra | COMPILED | CLUSTER-raw-os-getenv-flags | backend/providers/comms/sms.py:38-46 | Raw `os.getenv("SMS_MODE")`, `os.getenv("SMS_SERIAL_PORT")`, `os.getenv("SMS_SERIAL_BAUD")` | All config via typed pydantic-settings | SMS provider bypasses typed settings with raw `os.getenv()` | Refactor `providers/comms/sms.py` to use `settings.sms_mode`, `settings.sms_serial_port`, `settings.sms_serial_baud` | S (1h) | P1 | 5 | single | L0 | VERIFIED | backend/config.py:283-288 (typed fields exist) | `grep -rn "os.getenv" backend/providers/comms/sms.py` returns zero matches | `tests/providers/test_sms_provider.py::test_no_raw_os_getenv` | `git revert <commit>` | F-010 | OPS-004 | none | no |
| OPS-007 | infra | COMPILED | CLUSTER-gunicorn-no-worker-count | backend/Dockerfile.prod:26 | `CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]` — no `--workers` flag | Gunicorn `--workers` explicitly set (e.g., `--workers 4`) to match `background_job_workers` and production replica count | Gunicorn defaults to 1 worker per CPU core; un explicit count prevents scaling surprises | Add `--workers 4` to gunicorn CMD, aligned with `docker-compose.prod.yml` replicas=3 and `background_job_workers=2` | S (1h) | P2 | 5 | single | L0 | VERIFIED | docker-compose.prod.yml:54 (`replicas: 3`) | `docker inspect <container> | grep CMD` shows `--workers 4` | `tests/infrastructure/test_docker_compose_prod.py::test_gunicorn_has_workers_flag` | `git revert <commit>` | CHAIN-005 | none | none | no |
| OPS-008 | infra | RESOLVED | CLUSTER-health-missing-r2 | backend/main.py:106-146 | `/health` checks only `database` and `valkey` deps; `/health/deps` checks DB, Valkey, email, payments, error_tracking, circuit_breakers | Health checks include R2 (`r2_bucket`, `r2_endpoint_url`) as a critical dependency per TECHNOLOGY_STACK.md (R2 is a production storage backend) | R2/storage backend is not checked in any health endpoint; media uploads would fail silently if R2 is down | Add R2 health check (`r2_bucket` reachable, list operation) to `/health` and `/health/deps` endpoints | M (2h) | P2 | 4 | single | L0 | VERIFIED | backend/config.py:222-229 (R2 settings exist) | `curl /health/deps` shows `storage`/`r2` key with status | `tests/observability/test_health_checks.py::test_health_checks_r2` | `git revert <commit>` | F-011, CHAIN-005 | OPS-001 | none | no |
| OPS-009 | infra | COMPILED |  | backend/infrastructure/observability/logging_config.py:138-142 | `RotatingFileHandler` with `maxBytes=10MB`, `backupCount=5` — rotates by size only | Log rotation also enforces `log_retention_days` (config.py:292, default=30) via `TimedRotatingFileHandler` or manual cleanup | Size-based rotation only; `log_retention_days` setting is defined but never applied, so old logs can accumulate beyond 30 days | Replace `RotatingFileHandler` with `TimedRotatingFileHandler(when='midnight', backupCount=30)` or add daily cleanup job | S (1h) | P2 | 4 | single | L0 | VERIFIED | backend/config.py:292 (`log_retention_days: int = Field(default=30)`) | Log files older than 30 days are absent after 30+ days of runtime | `tests/infrastructure/test_logging_config.py::test_log_retention_enforced` | `git revert <commit>` | CHAIN-005 | none | none | no |
| OPS-010 | infra | COMPILED |  | backend/jobs/celery_app.py:86-88; docker-compose.prod.yml:54-84 | Celery retry config uses `retry_backoff=True`, `retry_backoff_max=300` globally; no per-task concurrency limit beyond `worker_concurrency=4` | Per-task `rate_limit` and `concurrency_limit` annotations for money/payment tasks (payouts, reconciliation) to prevent concurrent payout sweeps from overdrawing | Payout and reconciliation tasks lack per-task concurrency limits; concurrent Celery workers could run duplicate payout sweeps simultaneously | Add `task_annotations` with `rate_limit` and `concurrency_limit` for `tasks.periodic_tasks.run_auto_payout_sweep` and `tasks.reconciliation_cron.run_reconciliation_cron` | M (2h) | P3 | 4 | single | L0 | VERIFIED | backend/jobs/celery_app.py:167-189 (existing task_annotations for AI tasks) | `grep -A5 "run_auto_payout_sweep" backend/jobs/celery_app.py` shows no annotation | `tests/jobs/test_celery_config.py::test_payout_task_concurrency_limit` | `git revert <commit>` | F-012, CHAIN-002 | OPS-002 | none | no |

## Over all

### Problem(s)
1. `/health/deps` never fails closed (always HTTP 200), breaking load-balancer and orchestrator health gates.
2. No CI/CD pipeline exists, so migrations, rollback, and deployment health checks are entirely manual.
3. No deployment/rollback/migration-on-deploy runbooks exist, leaving incident response undocumented.
4. Feature flags in payment, geography, and SMS providers bypass typed pydantic-settings via raw `os.getenv()`.
5. Gunicorn worker count is implicit (defaults to CPU count), making scaling unpredictable.
6. R2 storage backend is not checked in any health endpoint.
7. Log rotation ignores the configured `log_retention_days` setting; only size-based rotation is active.
8. Celery payout/reconciliation tasks lack per-task concurrency limits, risking duplicate financial operations.

### Solution(s)
1. Add `status_code=503` to `/health/deps` when any critical dep is down.
2. Create `.github/workflows/deploy.yml` with pre-deploy migrations, health gate, and rollback.
3. Write deployment, rollback, and migration-on-deploy runbooks in `docs/runbooks/`.
4. Refactor all `os.getenv()` feature-flag reads in providers to use typed `settings.*`.
5. Add `--workers 4` to gunicorn CMD in `Dockerfile.prod`.
6. Add R2 health check to `/health` and `/health/deps`.
7. Switch to `TimedRotatingFileHandler` or enforce `log_retention_days` via cleanup job.
8. Add `task_annotations` with `rate_limit`/`concurrency_limit` for payout/reconciliation tasks.

### Suggestion(s)
1. Add `/health/startup` endpoint for liveness with startup-probe semantics.
2. Centralize all provider config in `backend/config.py` typed fields; enforce via architecture test.
3. Add `test_health_checks_fail_closed` to CI pipeline to prevent regression.
4. Document tested rollback procedure in `docs/runbooks/rollback.md` with exact `alembic downgrade` steps.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | `/health/deps` must return 503 when critical deps down | backend/main.py:149-182 | yes | S | 5 |
| P0 | CI/CD pipeline with pre-deploy migrations and rollback | .github/workflows/ | yes | L | 5 |
| P1 | Raw `os.getenv()` in payment provider config → typed settings | backend/providers/payments/config.py | no | M | 5 |
| P1 | Raw `os.getenv()` in geography provider → typed settings | backend/providers/geography/geo.py | no | S | 5 |
| P1 | Raw `os.getenv()` in SMS provider → typed settings | backend/providers/comms/sms.py | no | S | 5 |
| P2 | Gunicorn `--workers` explicitly set in Dockerfile.prod | backend/Dockerfile.prod:26 | no | S | 5 |
| P2 | R2 health check missing from `/health` and `/health/deps` | backend/main.py:106-182 | no | M | 4 |
| P2 | `log_retention_days` not enforced; size-only rotation | backend/infrastructure/observability/logging_config.py:138-142 | no | S | 4 |
| P3 | Celery payout/reconciliation tasks lack per-task concurrency limit | backend/jobs/celery_app.py:86-189 | no | M | 4 |
