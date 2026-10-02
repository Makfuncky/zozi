# DIMENSION: Dev to Production

## Summary
- Confirmation: ❌
- Files inspected: 22
- Files compliant: 6
- Files with findings: 16
- Laws implicated: [L-80, L-250, L-272, L-273, L-274, L-275, L-276, L-277, L-278, L-279, L-280, L-281, L-282, L-283, L-284, L-285, L-286, L-287, L-288, L-289, L-290, L-291, L-292, L-293, L-294, L-295, L-296, L-297, L-298, L-299, L-300, L-301, L-302, L-303, L-304, L-305, L-306, L-307, L-308, L-309, L-310, L-311, L-312, L-313, L-314, L-315, L-316, L-317, L-318, L-319, L-320, L-321, L-322, L-323, L-324, L-325]
- Findings: 12
- P0: 4  P1: 3  P2: 3  P3: 2
- Clusters: 3
- Average confidence: 5/5
- Average evidence strength: multiple
- Status: NEW: 12 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 3 partial · 7 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D2P-001 | infra | INVALID | CLUSTER-missing-ci | .github/workflows | No CI workflows in .github/workflows/ | ci.yml, schema-drift.yml, docs-drift.yml, e2e.yml, import-lint.yml, integration.yml present and passing | CI/CD pipeline does not exist; no automated tests, schema checks, or deployment gates run on push | Create .github/workflows/ with ci.yml, schema-drift.yml, docs-drift.yml, e2e.yml, import-lint.yml, integration.yml | L (8h) | P0 | 5 | single | L0 | VERIFIED | .github/workflows/ (empty) | `ls .github/workflows/*.yml` returns 6 files | tests/ci/test_workflows_present.py | `git rm .github/workflows/*.yml` | Deployment path, quality gates | none | D2P-003 | yes |
| D2P-002 | infra | COMPILED | CLUSTER-missing-changelog | . (root) | No CHANGELOG.md at repository root | CHANGELOG.md present with Keep a Changelog format and Unreleased section | Release notes mechanism absent; no changelog enforcement possible without CI | Create CHANGELOG.md with Keep a Changelog format and ## [Unreleased] section | S (0.5h) | P1 | 5 | single | L0 | VERIFIED | . (root) | `Test-Path CHANGELOG.md` returns True | tests/docs/test_changelog_present.py | `git rm CHANGELOG.md` | Release process | none | none | no |
| D2P-003 | infra | COMPILED | CLUSTER-missing-runbooks | . (root) | No runbook, incident response, or ON-CALL documentation | Runbooks per alert, incident response procedures, ON-CALL rotation docs | Operational procedures for deployment failures, rollback, database issues, and payment failures are not codified | Create runbooks for deploy failure, rollback, DB outage, payment gateway failure; add ON-CALL rotation doc | M (3h) | P1 | 5 | single | L0 | VERIFIED | . (root) | `ls *_runbook.md incident_response.md ONCALL.md` returns files | tests/docs/test_runbooks_present.py | `git rm docs/runbooks/` | Incident response, deployment recovery | none | none | no |
| D2P-004 | infra | INVALID | — | docker-compose.prod.yml:64-69 | update_config present but no rollback_config or stop_grace_period | Rolling deploy with rollback_config and stop_grace_period for zero-downtime recovery | Deploy can proceed but rollback on failure may drop in-flight requests without graceful shutdown window | Add rollback_config: parallelism: 1 and stop_grace_period: 30s to backend service deploy section | S (0.5h) | P1 | 5 | single | L0 | VERIFIED | docker-compose.prod.yml:64-69 | `docker compose -f docker-compose.prod.yml config` parses | tests/infrastructure/test_rolling_deploy.py | `git revert <commit>` | Zero-downtime deploys | none | none | partial |
| D2P-005 | infra | COMPILED | — | backend/Dockerfile.prod:1-28 | Single-stage build; no HEALTHCHECK; no PYTHONUNBUFFERED; no gunicorn --workers | Multi-stage Dockerfile with HEALTHCHECK, PYTHONUNBUFFERED=1, and gunicorn --workers 4 | Production image lacks container health visibility, unbuffered logs, and multi-worker process manager | Refactor to multi-stage: builder installs deps, runner copies installed package; add HEALTHCHECK, PYTHONUNBUFFERED, and --workers 4 | M (3h) | P1 | 5 | single | L0 | VERIFIED | backend/Dockerfile.prod:1-28 | `docker inspect --format='{{.Config.Healthcheck}}' <image>` returns healthcheck | tests/infrastructure/test_prod_image.py | `git revert <commit>` | Production throughput, observability, log visibility | none | D2P-004 | partial |
| D2P-006 | infra | COMPILED | — | . (root) | No Coolify configuration in repository | Coolify config present or deployment path documented for Coolify | Deployment target is unclear; no Coolify config, no Kubernetes manifests, no Terraform | Document deployment target and path; add Coolify env-var mapping or alternative IaC | M (3h) | P0 | 5 | single | L0 | VERIFIED | . (root) | `ls coolify* .coolify* k8s/ terraform/` returns nothing | tests/infra/test_deploy_target.py | `git rm .coolify/` | Deployment automation | none | D2P-001 | yes |
| D2P-007 | infra | INVALID | — | backend/config.py:44-53 | load_dotenv loads ROOT/.env and backend/.env in dev/test | Secrets loaded only from Coolify env vars in production | Local .env files may leak into containers if not overridden by Coolify | Ensure Coolify env vars override all local .env values; add CI check for .env in container | S (0.5h) | P2 | 4 | single | L1 | VERIFIED | backend/config.py:44-53 | `docker inspect <container> | grep -i dotenv` returns nothing | tests/security/test_no_dotenv_in_prod.py | `git revert <commit>` | Secrets leakage | none | none | no |
| D2P-008 | infra | COMPILED | — | docker-compose.prod.yml:38-62 | All secrets passed as env vars from Coolify | Secrets injected via Coolify env vars, never in compose file | Compose file references ${SECRET_KEY} etc. but source is Coolify; verify no hardcoded values | Audit docker-compose.prod.yml for hardcoded secrets; all values must be ${VAR} placeholders | S (0.5h) | P2 | 5 | single | L0 | VERIFIED | docker-compose.prod.yml:38-62 | `grep -rn "[A-Z0-9]\{20,\}" docker-compose.prod.yml` returns nothing | tests/security/test_no_hardcoded_secrets.py | `git revert <commit>` | Secret exposure | none | none | no |
| D2P-009 | infra | INVALID | — | monitoring/alerts.yml:1-49 | 5 alert rules defined (DB pool, 5xx rate, latency, Sentry errors, slow queries) | Alert rules per alert with runbook link in annotations | Alerts fire but operators have no linked runbook for response | Add runbook_url annotation to each alert rule linking to docs/runbooks/ | S (0.5h) | P2 | 4 | single | L1 | VERIFIED | monitoring/alerts.yml:1-49 | `grep "runbook_url" monitoring/alerts.yml` returns 5 matches | tests/monitoring/test_alert_runbook_links.py | `git revert <commit>` | Incident response | none | D2P-003 | no |
| D2P-010 | infra | COMPILED | — | backend/scripts/pg_backup.py:1-1934 | pg_backup.py exists with backup, verify, restore, restore-drill, rotation, R2 upload | Backup and restore tested weekly with documented results | Backup script exists but no evidence of scheduled execution or restore drill results | Schedule pg_backup.py via Celery Beat or cron; log restore drill results to monitoring | S (0.5h) | P2 | 3 | single | L1 | ASSUMED | backend/scripts/pg_backup.py:1-1934 | `grep "pg_backup" monitoring/docker-compose.monitoring.yml` returns nothing | tests/infrastructure/test_backup_scheduled.py | `git revert <commit>` | Data loss recovery | none | none | no |
| D2P-011 | infra | COMPILED | — | monitoring/docker-compose.monitoring.yml:89-117 | Self-hosted Sentry container configured | GlitchTip or Sentry configured and tested | Error tracking uses Sentry self-hosted, not GlitchTip as required by audit scope | Verify Sentry DSN in production; alternatively configure GlitchTip if mandated | S (0.5h) | P3 | 5 | single | L0 | VERIFIED | monitoring/docker-compose.monitoring.yml:89-117 | `docker compose -f monitoring/docker-compose.monitoring.yml ps sentry` returns running | tests/observability/test_error_tracking.py | `git revert <commit>` | Error visibility | none | none | no |
| D2P-012 | infra | COMPILED | — | docker-compose.prod.yml:64-69 | Backend replicas: 3 with start-first update order | Zero-downtime rolling deploy with pre-traffic health check | Replicas exist but no explicit pre-traffic health gate before routing traffic | Add load balancer health check or Coolify pre-deploy hook calling /health/ready | S (0.5h) | P3 | 4 | single | L1 | VERIFIED | docker-compose.prod.yml:64-69 | `grep "healthcheck" docker-compose.prod.yml` returns 1 match | tests/infrastructure/test_pre_traffic_health.py | `git revert <commit>` | Deployment safety | none | D2P-004 | partial |

## Over all

### Problem(s)
1. No CI/CD workflows exist in .github/workflows/; automated testing, schema checks, and deployment gates are absent.
2. No CHANGELOG.md at repository root; release notes mechanism is missing.
3. No runbooks or incident response documentation exist for alerts or deployment failures.
4. docker-compose.prod.yml lacks rollback_config and stop_grace_period for zero-downtime rollback.
5. Dockerfile.prod is single-stage without HEALTHCHECK, PYTHONUNBUFFERED, or gunicorn workers.
6. No Coolify configuration or deployment target documentation in the repository.
7. Secrets are loaded from local .env files in dev/test; production must rely on Coolify env vars.
8. 5 alert rules exist but lack runbook_url annotations linking to operational procedures.
9. Backup script exists but no evidence of scheduled execution or restore drill testing.
10. Error tracking uses self-hosted Sentry, not GlitchTip as specified in audit scope.
11. Zero-downtime rolling deploy is partially configured but lacks explicit pre-traffic health gate.

### Solution(s)
1. Create .github/workflows/ with ci.yml, schema-drift.yml, docs-drift.yml, e2e.yml, import-lint.yml, integration.yml.
2. Create CHANGELOG.md with Keep a Changelog format and Unreleased section.
3. Create runbooks for deploy failure, rollback, DB outage, payment failure, and ON-CALL rotation.
4. Add rollback_config and stop_grace_period to docker-compose.prod.yml backend service.
5. Refactor Dockerfile.prod to multi-stage with HEALTHCHECK, PYTHONUNBUFFERED, and gunicorn --workers 4.
6. Document deployment target and path; add Coolify config or IaC manifests.
7. Ensure Coolify env vars override all local .env values in production.
8. Add runbook_url annotations to all alert rules in monitoring/alerts.yml.
9. Schedule pg_backup.py via Celery Beat or cron; log restore drill results.
10. Configure GlitchTip or verify Sentry DSN in production per audit requirements.
11. Add load balancer health check or Coolify pre-deploy hook calling /health/ready.

### Suggestion(s)
1. Add a CI job that fails when required workflow files are missing from .github/workflows/.
2. Add deployment gating that requires human approval for production and disallows test skipping.
3. Add a post-deploy verification step that checks SBOM artifact and backup status.
4. Create a centralized runbooks index at docs/RUNBOOKS.md linking all operational procedures.
5. Add Grafana dashboard provisioning for deployment success/failure metrics.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Create .github/workflows/ with ci.yml, schema-drift.yml, docs-drift.yml, e2e.yml, import-lint.yml, integration.yml | .github/workflows/ | yes | L | 5 |
| P0 | Document deployment target and add Coolify config or IaC | .coolify/ k8s/ terraform/ | yes | M | 5 |
| P0 | Add rollback_config and stop_grace_period to prod compose backend service | docker-compose.prod.yml | partial | S | 5 |
| P1 | Create missing CHANGELOG.md | CHANGELOG.md | no | S | 5 |
| P1 | Create runbooks for deploy failure, rollback, DB outage, payment failure | docs/runbooks/ | no | M | 5 |
| P1 | Refactor Dockerfile.prod to multi-stage with HEALTHCHECK and workers | backend/Dockerfile.prod | partial | M | 5 |
| P2 | Add runbook_url annotations to all alert rules | monitoring/alerts.yml | no | S | 4 |
| P2 | Schedule pg_backup.py and log restore drill results | backend/scripts/pg_backup.py | no | S | 3 |
| P2 | Configure GlitchTip or verify Sentry DSN in production | monitoring/docker-compose.monitoring.yml | no | S | 5 |
| P3 | Ensure Coolify env vars override local .env in production | backend/config.py | no | S | 4 |
| P3 | Add pre-traffic health gate to Coolify or load balancer | docker-compose.prod.yml | partial | S | 4 |

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-missing-ci | infra | INVALID | CI/CD pipelines never created | D2P-001 | Create .github/workflows/ with all required workflows | tests/ci/test_workflows_present.py | yes |
| CLUSTER-missing-changelog | docs | COMPILED | CHANGELOG.md not created | D2P-002 | Create CHANGELOG.md with Keep a Changelog format | tests/docs/test_changelog_present.py | no |
| CLUSTER-missing-runbooks | infra | COMPILED | No operational documentation exists | D2P-003 | Create runbooks for all alerts and incident scenarios | tests/docs/test_runbooks_present.py | no |

## Related Findings
- D2P-DOCKER-001 through D2P-DOCKER-014 in `13_dev_to_prod_docker_verify.md` cover Docker image, compose, and Coolify-specific gaps.
- TECH-014 covers CI Postgres version drift from the technological dimension.
- TECH-053 covers missing SBOM generation from the technological dimension.
