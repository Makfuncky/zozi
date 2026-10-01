# REMEDIATION PLAN

Generated: 2026-09-30T04:40:00Z
Run number: 1

## Completion blockers (fix before anything else)

| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Priority | Confidence | Verify | Test | Rollback | Blast radius | Unblocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PF-001 | boot | CLUSTER-preflight-env-missing | 27_project_completion_blockers | backend/config.py:340 | Add DATABASE_URL to backend/config.py | M | P0 | 5 | python -c "from backend.config import settings; print(settings.DATABASE_URL)" | tests/test_config.py | Revert config.py | All DB features | PF-003 |
| PF-002 | boot | CLUSTER-preflight-env-missing | 27_project_completion_blockers | backend/config.py:340 | Add VALKEY_URL to backend/config.py | M | P0 | 5 | python -c "from backend.config import settings; print(settings.VALKEY_URL)" | tests/test_config.py | Revert config.py | Sessions, cache, event bus | PF-001 |
| PF-003 | boot | CLUSTER-preflight-alembic | 27_project_completion_blockers | alembic.ini | Add script_location | S | P0 | 5 | alembic current | tests/test_migrations.py | Revert ini | All migrations | PF-001, PF-004 |
| PF-004 | infra | CLUSTER-preflight-docker | 27_project_completion_blockers | docker-compose | Set POSTGRES_PASSWORD | S | P0 | 5 | docker compose config | None | Remove var | Local dev | PF-001 |
| PF-005 | infra | CLUSTER-preflight-frontend | 27_project_completion_blockers | frontend/web_app | Resolve pnpm-lock.yaml | M | P0 | 4 | pnpm install --frozen-lockfile | None | Revert lockfile | Frontend build, CI | none |
| PF-006 | testing | CLUSTER-preflight-tests | 27_project_completion_blockers | tests/architecture/ | Create architecture tests | M | P1 | 5 | pytest test/architecture/ --collect-only | tests/architecture/* | Remove tests | CI checks | none |

## Priority matrix

|  | Low effort (S, <1h) | Medium effort (M, 1–4h) | High effort (L, >4h) |
|---|---|---|---|
| **High impact** | Fix now | Fix now | Schedule |
| **Medium impact** | Fix now | Schedule | Backlog |
| **Low impact** | Backlog | Backlog | Ignore |

## Phase execution order

| Phase | Day window | Example work |
|---|---|---|
| emergency | Day 0 | Rotate secrets, fix SQL injection, remove forbidden packages |
| boot | Day 0–1 | Fix undefined refs, missing columns that crash boot, unregistered middleware |
| tech | Day 1 | Remove forbidden packages, add missing lockfile entries |
| db | Day 1–2 | Add missing columns, linearize migration heads, RLS context |
| logic | Day 2–4 | float→Decimal, idempotency, silent excepts, transactions |
| arch | Day 4–6 | Cross-domain imports, ports, duplicates, router thinness |
| security | Day 6–8 | Auth hardening, rate limits, debug=False, TTL |
| payment | Day 6–8 | Payment gateway config, credential storage, webhook verification |
| compliance | Day 7–9 | PCI-DSS, GDPR, data residency, audit retention |
| frontend | Day 1–8 (parallel) | Web + mobile; parallel from tech complete |
| mobile | Day 1–8 (parallel) | Expo, native permissions, OTA, push |
| testing | Day 1–8 (parallel) | Test collection, browser tests, architecture tests |
| infra | Day 1–8 (parallel) | CI/CD, deployment, health checks |
| docs | Day 8–9 | Runbooks, API docs, CHANGELOG |
| defer | Day 10 | Everything not fixed; documented as known issues |

## P0 — Fix now

| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Unblocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PF-001 | boot | CLUSTER-preflight-env-missing | 27 | backend/config.py:340 | Add DATABASE_URL | M | 5 | python -c "...settings.DATABASE_URL" | tests/test_config.py | Revert config.py | All DB features | PF-003 | yes |
| PF-002 | boot | CLUSTER-preflight-env-missing | 27 | backend/config.py:340 | Add VALKEY_URL | M | 5 | python -c "...settings.VALKEY_URL" | tests/test_config.py | Revert config.py | Sessions, cache, event bus | PF-001 | yes |
| PF-003 | boot | CLUSTER-preflight-alembic | 27 | alembic.ini | Add script_location | S | 5 | alembic current | tests/test_migrations.py | Revert ini | All migrations | PF-001, PF-004 | yes |
| PF-004 | infra | CLUSTER-preflight-docker | 27 | docker-compose | Set POSTGRES_PASSWORD | S | 5 | docker compose config | None | Remove var | Local dev | PF-001 | yes |
| PF-005 | infra | CLUSTER-preflight-frontend | 27 | frontend/web_app | Resolve pnpm-lock.yaml | M | 4 | pnpm install --frozen-lockfile | None | Revert lockfile | Frontend build, CI | none | yes |

## P1 — Fix now (high impact, low effort)

| ID | Phase | Cluster | Dimension | File:Line | Fix | Effort | Confidence | Verify | Test | Rollback | Blast radius | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PF-006 | testing | CLUSTER-preflight-tests | 27 | tests/architecture/ | Create architecture tests | M | 5 | pytest test/architecture/ --collect-only | tests/architecture/* | Remove tests | CI checks | yes |

## P2 — Schedule (medium impact, medium effort)

No P2 findings yet — awaiting Pass 1 and Pass 2.

## P3 — Backlog (low impact, or blocked)

No P3 findings yet — awaiting Pass 1 and Pass 2.

## Ignore (low impact, high effort)

No ignored findings yet — awaiting Pass 1 and Pass 2.

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-preflight-env-missing | boot | — | Missing DATABASE_URL and VALKEY_URL in config | PF-001, PF-002 | Add both settings to backend/config.py | tests/test_config.py | yes |
| CLUSTER-preflight-alembic | boot | — | Alembic script_location missing | PF-003 | Add script_location to alembic.ini | tests/test_migrations.py | yes |
| CLUSTER-preflight-docker | infra | — | POSTGRES_PASSWORD missing in .env | PF-004 | Add POSTGRES_PASSWORD to root .env | None | yes |
| CLUSTER-preflight-frontend | infra | — | pnpm-lock.yaml absent | PF-005 | Generate lockfile via pnpm install | None | yes |
| CLUSTER-preflight-tests | testing | — | tests/architecture/ missing | PF-006 | Create directory with required test files | tests/architecture/* | yes |

## KEEP / HARDEN

No KEEP/HARDEN findings yet — awaiting Pass 1 and Pass 2.

## KEEP_HARDEN_CANDIDATE

No KEEP_HARDEN_CANDIDATE findings yet — awaiting Pass 1 and Pass 2.

## Contradictions requiring user decision

No contradictions yet — awaiting Pass 1 and Pass 2.

## Dependency graph (ordered)

1. PF-001 → PF-003 → PF-004
2. PF-002 → PF-001
3. PF-005 → none
4. PF-006 → none

## Estimated total effort

- P0: 7h
- P1: 4h
- P2: 0h
- Total: 11h

## Confidence distribution

- Confidence 5: 5 findings
- Confidence 4: 1 finding
- Confidence 3: 0 findings
- Confidence 2: 0 findings
- Confidence 1: 0 findings

## Cluster distribution

- Clusters of ≥ 10 members: 0
- Clusters of 3–9 members: 1
- Unclustered findings: 1

## Completion blocker distribution

- yes: 6 findings (must fix before deployment)
- partial: 0 findings (fix before specific user journeys)
- no: 0 findings (quality/maintainability)
