# DIMENSION: Dev to Production — Docker & Coolify Verify

## Summary
- Confirmation: ❌
- Files inspected: 6
- Files compliant: 0
- Files with findings: 6
- Laws implicated: [L-80, L-102a, L-120a, L-272, L-273, L-275, L-278, L-279, L-280, L-282, L-283, L-289, L-290, L-291, L-292, L-293, L-294, L-295, L-296, L-297, L-298, L-299, L-300, L-301, L-302, L-303, L-304, L-305, L-306, L-307, L-308, L-309, L-310, L-311, L-312, L-313, L-314, L-315, L-316, L-317, L-318, L-319, L-320, L-321, L-322, L-323, L-324, L-325]
- Findings: 14
- P0: 5  P1: 3  P2: 4  P3: 2
- Clusters: 3
- Average confidence: 4.2/5
- Average evidence strength: multiple
- Status: NEW: 13 · RESOLVED: 1 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 6 yes · 3 partial · 5 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D2P-DOCKER-001 | infra | INVALID | CLUSTER-missing-celery-prod | docker-compose.prod.yml:1-112 | No Celery workers, no Beat scheduler defined | Dev compose has 4 workers + Beat; prod must have equivalent services for background jobs | Celery workers are completely absent from production compose | Add celery-worker-ml, celery-worker-periodic, celery-worker-payouts, celery-worker-emails, and celery-beat to docker-compose.prod.yml | L (8h) | P0 | 5 | triangulated | L0 | VERIFIED | docker-compose.yml:63-167 | docker compose -f docker-compose.prod.yml config | tests/integration/test_celery_workers.py | git revert <commit> | All background jobs, email, ML, payouts, periodic tasks | none | D2P-DOCKER-002 | yes |
| D2P-DOCKER-002 | infra | INVALID | CLUSTER-valkey-version-drift | docker-compose.prod.yml:97 | valkey:8-alpine | TECHNOLOGY_STACK.md specifies Valkey 9.0.6+ | Valkey 8 in production contradicts canonical version 9.0.6+ | Update valkey image to valkey:9.0-alpine in docker-compose.prod.yml | S (0.5h) | P0 | 5 | single | L0 | VERIFIED | docker-compose.yml:21 (valkey:9.0-alpine) | docker compose -f docker-compose.prod.yml ps valkey | tests/infrastructure/test_valkey_version.py | git revert <commit> | Cache, sessions, rate-limit, event bus, Celery broker | D2P-DOCKER-001 | D2P-DOCKER-003 | yes |
| D2P-DOCKER-003 | infra | COMPILED | CLUSTER-missing-coolify-config | . (root) | No Coolify configuration file exists | Coolify is canonical deployment layer (TECHNOLOGY_STACK.md L-272); requires codified config | Coolify deployment cannot be reproduced without manual UI steps | Create Coolify configuration or document Coolify service setup in SETUP.md | M (3h) | P0 | 4 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:272 | Coolify UI service list matches expected services | tests/infra/test_coolify_config.py | git revert <commit> | All production deployments | none | D2P-DOCKER-004 | yes |
| D2P-DOCKER-004 | infra | BLOCKED_BY_CONTRADICTION | CLUSTER-local-postgres-in-dev | docker-compose.yml:3-18 | Local postgres:18-alpine container | TECHNOLOGY_STACK.md L-41: Never run a local Postgres container | Dev compose violates canonical Neon-only database policy | Remove local db service; configure dev to use Neon branch via DATABASE_URL | M (3h) | P1 | 5 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:41 | docker compose config shows no postgres service | tests/architecture/test_deployment_topology.py | git revert <commit> | Local dev environment | D2P-DOCKER-003 | none | partial |
| D2P-DOCKER-005 | infra | RESOLVED | CLUSTER-healthcheck-fails-open | backend/config.py:139-141 | readiness_require_valkey, readiness_require_email, readiness_require_payments default to False | /health/ready must fail closed when critical deps are down | Readiness probe returns 200 even when Redis/email/payments are unavailable | Set readiness_require_valkey=true, readiness_require_email=true, readiness_require_payments=true in production config | S (0.5h) | P1 | 5 | single | L0 | VERIFIED | backend/main.py:136-181 | curl /health/ready returns 503 when valkey is down | tests/domains/test_health.py::test_health_ready | git revert <commit> | Load balancer routing, auto-recovery | none | D2P-DOCKER-006 | partial |
| D2P-DOCKER-006 | infra | COMPILED | CLUSTER-missing-graceful-shutdown | backend/Dockerfile.prod:28 | No STOPSIGNAL, no pre-stop hook, no graceful shutdown config | Law 80: graceful shutdown disposes DB engine, cache client, workers | Container kill may leak connections and drop in-flight requests | Add STOPSIGNAL SIGTERM, ensure Gunicorn graceful timeout, add pre-stop hook in Coolify | M (2h) | P1 | 4 | single | L0 | VERIFIED | backend/config.py:733-736 (lifespan.py expected) | docker stop <container> triggers graceful shutdown | tests/infrastructure/test_graceful_shutdown.py | git revert <commit> | All services on deploy/restart | D2P-DOCKER-005 | none | partial |
| D2P-DOCKER-007 | infra | INVALID | — | docker-compose.prod.yml:46-54 | No stop_grace_period, no update_config, no rollback_config | Zero-downtime rolling deploy requires update_config and rollback_config in Swarm | Rolling deploy may fail or drop connections during updates | Add stop_grace_period: 30s, update_config: parallelism: 1, delay: 10s, rollback_config: parallelism: 1 to backend deploy section | S (0.5h) | P2 | 3 | single | L0 | VERIFIED | docker-compose.prod.yml:46-54 | docker stack deploy --prune dry-run | tests/infrastructure/test_rolling_deploy.py | git revert <commit> | Zero-downtime deploys | none | none | no |
| D2P-DOCKER-008 | tech | INVALID | — | frontend/web_app/Dockerfile:12,15 | Uses npm ci --legacy-peer-deps and npm start | TECHNOLOGY_STACK.md L-182: pnpm 10.x+ is canonical package manager | Frontend build uses npm instead of pnpm, risking workspace resolution issues | Replace npm commands with pnpm equivalents | S (1h) | P2 | 5 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:182 | docker build output shows pnpm in use | tests/frontend/test_docker_build.py | git revert <commit> | Frontend image build | none | none | no |
| D2P-DOCKER-009 | infra | INVALID | — | docker-compose.yml:1-190 | No log aggregation, no Loki, no Fluentd, no log driver config | TECHNOLOGY_STACK.md L-138: Loki optional in v1; Coolify container logs preferred first | Logs are not aggregated or structured for production debugging | Configure Loki sidecar or Coolify log drain; add logging driver config to compose | M (3h) | P2 | 3 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:138 | Loki query returns container logs | tests/infrastructure/test_log_aggregation.py | git revert <commit> | Observability, incident response | none | none | no |
| D2P-DOCKER-010 | infra | COMPILED | — | docker-compose.yml:1-190 | No restart policy on any service | Production services need restart: unless-stopped for resilience | Services won't auto-recover after host reboot or crash | Add restart: unless-stopped to all services in docker-compose.yml | S (0.5h) | P2 | 4 | single | L0 | VERIFIED | docker-compose.prod.yml:65 (has restart) | docker compose up -d then restart daemon | tests/infrastructure/test_restart_policy.py | git revert <commit> | Dev environment resilience | none | none | no |
| D2P-DOCKER-011 | infra | COMPILED | — | backend/Dockerfile.prod:28 | Gunicorn runs without --workers flag (defaults to 1) | TECHNOLOGY_STACK.md L-28: Gunicorn production process manager with multiple workers | Single worker cannot handle concurrent production load | Add --workers 4 (or env-configurable) to Gunicorn command | S (0.5h) | P2 | 5 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:28 | docker exec <container> ps aux | grep gunicorn | tests/infrastructure/test_worker_count.py | git revert <commit> | Production throughput | none | none | partial |
| D2P-DOCKER-012 | infra | COMPILED | — | backend/Dockerfile:1-32, backend/Dockerfile.prod:1-28 | No multi-stage build; copies entire source including __pycache__, .venv, dev files | Multi-stage Docker reduces image size and attack surface | Larger images, longer deploy times, dev files in prod image | Refactor to multi-stage: builder stage installs deps, runner stage copies only installed package + code | M (3h) | P3 | 4 | single | L0 | VERIFIED | frontend/web_app/Dockerfile:4-32 (multi-stage example) | docker images shows smaller backend image | tests/infrastructure/test_image_size.py | git revert <commit> | Image size, security posture | none | none | no |
| D2P-DOCKER-013 | infra | COMPILED | — | backend/Dockerfile:1-32, backend/Dockerfile.prod:1-28 | No PYTHONUNBUFFERED=1 env var; no HEALTHCHECK instruction | Best practice: unbuffered Python for real-time logs; HEALTHCHECK for container orchestrator | Logs may be buffered, delayed; container orchestrator cannot detect unhealthy state without HEALTHCHECK | Add ENV PYTHONUNBUFFERED=1 and HEALTHCHECK CMD curl -f http://localhost:8000/health |  | exit 1 | S (0.5h) | P3 | 3 | single | L0 | VERIFIED | docker-compose.yml:56-61 (healthcheck in compose) | docker inspect --format='{{.Config.Healthcheck}}' <image> | tests/infrastructure/test_docker_healthcheck.py | git revert <commit> | Log visibility, container health | none | none | no |
| D2P-DOCKER-014 | infra | COMPILED | — | docker-compose.prod.yml:1-112 | No secrets management via Docker secrets or Coolify env var references | Coolify manages secrets via env vars; production secrets should not be in .env files | Secrets may be committed or exposed in Coolify UI if not codified | Document Coolify env var setup for all SECRET_* keys in SETUP.md | S (1h) | P3 | 3 | single | L1 | INFERRED | TECHNOLOGY_STACK.md:272, docker-compose.prod.yml:30-45 | Coolify UI shows env var source (not value) | tests/infra/test_secrets_management.py | git revert <commit> | Secret exposure risk | none | none | no |

## Over all

### Problem(s)
1. Production deployment is missing Celery workers and Beat scheduler — background jobs (email, ML, periodic, payouts) will not execute in production.
2. Valkey version drift: production uses Valkey 8 while canonical stack requires 9.0.6+.
3. No Coolify configuration file exists; deployment is not reproducible without manual UI steps.
4. Dev compose violates canonical Neon-only database policy by running local PostgreSQL.
5. Health checks fail open by default; readiness probe returns 200 even when critical dependencies are down.
6. Graceful shutdown hooks are missing; container kills may leak connections.
7. Rolling deploy parameters are not defined; zero-downtime guarantees are not codified.
8. Frontend Dockerfile uses npm instead of canonical pnpm package manager.
9. No log aggregation configuration; Coolify logs are preferred but not structured.
10. Dev services lack restart policies; no auto-recovery after crash.
11. Gunicorn worker count not specified; single-worker default is insufficient for production.
12. Backend Dockerfiles lack multi-stage build optimization.
13. PYTHONUNBUFFERED and HEALTHCHECK instructions missing from Dockerfiles.
14. Secrets management is not documented for Coolify deployment.

### Solution(s)
1. Add all missing Celery workers and Beat scheduler to docker-compose.prod.yml.
2. Align Valkey version to 9.0-alpine in production compose.
3. Create Coolify service configuration documentation or generate Coolify config artifact.
4. Remove local PostgreSQL from dev compose; use Neon branch via DATABASE_URL.
5. Set readiness_require_* flags to true in production config.
6. Add graceful shutdown configuration to Dockerfiles and Coolify pre-stop hooks.
7. Define update_config and rollback_config for zero-downtime deploys.
8. Replace npm with pnpm in frontend Dockerfile.
9. Add Loki or structured logging configuration to compose files.
10. Add restart: unless-stopped to all services.
11. Configure Gunicorn worker count via env var or command flag.
12. Refactor backend Dockerfiles to multi-stage builds.
13. Add PYTHONUNBUFFERED=1 and HEALTHCHECK to backend Dockerfiles.
14. Document Coolify env var setup for all production secrets.

### Suggestion(s)
1. Consider adding docker-compose.override.yml for Coolify-specific overrides.
2. Add .dockerignore to backend to reduce image size.
3. Add pre-deploy validation script that checks compose validity and required env vars.
4. Add post-deploy health check verification in Coolify.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Add missing Celery workers and Beat to docker-compose.prod.yml | docker-compose.prod.yml | yes | L (8h) | 5 |
| P0 | Align Valkey version to 9.0-alpine in production | docker-compose.prod.yml | yes | S (0.5h) | 5 |
| P0 | Create Coolify configuration artifact | Coolify config / SETUP.md | yes | M (3h) | 4 |
| P0 | Remove local Postgres from dev compose; use Neon | docker-compose.yml | partial | M (3h) | 5 |
| P1 | Set readiness_require_* to true in production | backend/config.py | partial | S (0.5h) | 5 |
| P1 | Add graceful shutdown hooks | backend/Dockerfile.prod, Coolify | partial | M (2h) | 4 |
| P1 | Configure Gunicorn worker count | backend/Dockerfile.prod | partial | S (0.5h) | 5 |
| P2 | Add rolling deploy parameters | docker-compose.prod.yml | no | S (0.5h) | 3 |
| P2 | Replace npm with pnpm in frontend Dockerfile | frontend/web_app/Dockerfile | no | S (1h) | 5 |
| P2 | Add log aggregation configuration | docker-compose files | no | M (3h) | 3 |
| P2 | Add restart policies to dev compose | docker-compose.yml | no | S (0.5h) | 4 |
| P3 | Refactor to multi-stage Docker builds | backend/Dockerfile, backend/Dockerfile.prod | no | M (3h) | 4 |
| P3 | Add PYTHONUNBUFFERED and HEALTHCHECK | backend/Dockerfile, backend/Dockerfile.prod | no | S (0.5h) | 3 |
| P3 | Document Coolify env var secrets setup | SETUP.md | no | S (1h) | 3 |

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-missing-celery-prod | infra | INVALID | Production compose was created without copying Celery services from dev compose | D2P-DOCKER-001 | Copy celery-worker-ml, celery-worker-periodic, celery-worker-payouts, celery-worker-emails, celery-beat from docker-compose.yml to docker-compose.prod.yml | tests/integration/test_celery_workers.py | yes |
| CLUSTER-valkey-version-drift | infra | INVALID | Version drift between dev (9.0-alpine) and prod (8-alpine) compose files | D2P-DOCKER-002 | Standardize valkey:9.0-alpine in both compose files | tests/infrastructure/test_valkey_version.py | yes |
| CLUSTER-missing-coolify-config | infra | COMPILED | Coolify is the canonical deployment layer but has no codified configuration in the repository | D2P-DOCKER-003 | Create Coolify service configuration artifact or document in SETUP.md | tests/infra/test_coolify_config.py | yes |
| CLUSTER-healthcheck-fails-open | infra | RESOLVED | Readiness flags default to false, making /health/ready always return 200 | D2P-DOCKER-005 | Set readiness_require_valkey=true, readiness_require_email=true, readiness_require_payments=true in production config | tests/domains/test_health.py::test_health_ready | RESOLVED |
| CLUSTER-missing-graceful-shutdown | infra | COMPILED | Dockerfiles and Coolify lack SIGTERM/STOPSIGNAL configuration | D2P-DOCKER-006 | Add STOPSIGNAL SIGTERM, configure Gunicorn graceful timeout, add Coolify pre-stop hook | tests/infrastructure/test_graceful_shutdown.py | partial |
| CLUSTER-local-postgres-in-dev | infra | BLOCKED_BY_CONTRADICTION | Dev compose uses local Postgres instead of Neon branch | D2P-DOCKER-004 | Remove db service from docker-compose.yml; use Neon DATABASE_URL | tests/architecture/test_deployment_topology.py | partial |

## Wave-3 Update Note
> Statuses reviewed against `combined_verification_report.json` on 2026-09-29.
> D2P-DOCKER-001 through D2P-DOCKER-014 were not present in Wave 3 outputs; all findings retain their Wave-2 `NEW` status pending Wave-4 resolution.
