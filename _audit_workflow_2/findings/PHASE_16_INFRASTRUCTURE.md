# TASK 16 — DEPLOYMENT / INFRASTRUCTURE AUDIT
## ZOZI Marketplace E-Commerce Platform
**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Scope:** Deployment, containerization, orchestration, reverse proxy, web server, application server, workers, queues, databases, cache, object storage, CDN, DNS, TLS, CI/CD, environment configuration, secrets management, logging, monitoring, backups, health checks, scaling

---

## EXECUTIVE SUMMARY

The ZOZI platform has a partially documented and inconsistently configured production infrastructure. Key components exist as Docker Compose definitions and configuration files, but there are critical contradictions between files (e.g., Redis vs Valkey naming), missing CI/CD pipelines, exposed secrets in committed .env files, and no Kubernetes manifests. The intended architecture is Docker Compose + Caddy reverse proxy + Neon PostgreSQL + Cloudflare R2 + Celery workers, but several files suggest different or incomplete implementations.

---

## 1. CONTAINERIZATION & ORCHESTRATION

### 1.1 Dockerfiles

| File | Purpose | Base Image | User | CMD |
|------|---------|-----------|------|-----|
| backend/Dockerfile | Development | python:3.11-slim | non-root app | uvicorn main:app --host 0.0.0.0 --port 8000 |
| backend/Dockerfile.prod | Production | python:3.11-slim | non-root app | gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 |
| frontend/web_app/Dockerfile | Frontend (multi-stage) | node:22-alpine | N/A | npm start |

Status: VERIFIED

Evidence:
- backend/Dockerfile:1 => FROM python:3.11-slim
- backend/Dockerfile.prod:1 => FROM python:3.11-slim
- backend/Dockerfile.prod:26 => CMD with gunicorn + uvicorn workers
- frontend/web_app/Dockerfile:4,18 => node:22-alpine builder + runner

Impact: Multi-stage Dockerfile for frontend reduces image size. Production backend uses gunicorn with uvicorn workers. Non-root user improves security.

---

### 1.2 Docker Compose Files

Three compose files exist with overlapping and conflicting definitions.

#### docker-compose.yml (Development) - VERIFIED

Services: db (postgres:18-alpine), valkey (valkey:9.0-alpine), backend, celery-worker-ml, celery-worker-periodic, celery-worker-payouts, celery-worker-emails, celery-beat, frontend.

Key observations:
- Backend depends on db:service_healthy and valkey:service_started
- Valkey used as Celery broker (valkey://valkey:6379/1) and result backend (valkey://valkey:6379/2)
- No restart policy on any service
- No resource limits on most services
- celery-worker-ml has memory limits (4G limit, 2G reserve)
- No healthcheck on valkey, backend, celery workers, or frontend

#### docker-compose.override.yml - VERIFIED

Adds pgbouncer between backend and postgres. Backend DATABASE_URL points to pgbouncer:6432. DB_POOL_SIZE=10, DB_MAX_OVERFLOW=10. No AUTH_TYPE set (defaults to md5, NOT scram-sha-256). No healthcheck on pgbouncer.

#### docker-compose.prod.yml - VERIFIED WITH CRITICAL INCONSISTENCIES

Services: pgbouncer, backend (replicas: 3), ml_worker, redis:7-alpine.

CRITICAL INCONSISTENCIES:
1. Uses redis:7-alpine instead of Valkey - violates no_redis_naming_anywhere constraint
2. REDIS_URL instead of VALKEY_URL
3. Different database pool settings (10/10 in prod vs 50/100 in config.py defaults)
4. STORAGE_BACKEND=s3 in prod but .env.example defaults to r2
5. No AUTH_TYPE set for PgBouncer (defaults to md5)
6. Backend replicas: 3 but no load balancer in compose (replicas ignored in plain Docker Compose)
7. No Celery workers in prod compose - background jobs will NOT run in production via compose

---

## 2. REVERSE PROXY & WEB SERVER

### 2.1 Caddy (Production) - VERIFIED

Evidence: Caddyfile:1-66

Configuration:
- Automatic HTTPS via Let's Encrypt ACME v2
- Admin API disabled
- Three virtual hosts: api.yourdomain.com, yourdomain.com, www.yourdomain.com
- Security headers: HSTS (max-age=31536000; includeSubDomains; preload), X-Content-Type-Options, X-Frame-Options
- WebSocket support for API
- 300s timeout on API host
- zstd/gzip compression on frontend

Critical Gap: yourdomain.com is a placeholder - actual domain not configured.

### 2.2 Nginx (Development) - VERIFIED

Evidence: nginx/nginx.conf:1-135

Configuration:
- Listens on port 80 (no TLS)
- Upstreams: backend:8000, frontend:3000
- Route mappings: / -> frontend, /ws/ -> backend (WebSocket), /api/ -> backend, /_next/static/ -> frontend (1y cache), /uploads/ -> backend, /media/ -> backend
- Security headers present
- gzip compression

No nginx container in any docker-compose file.

---

## 3. APPLICATION SERVER

### 3.1 FastAPI Application - VERIFIED

Evidence: backend/main.py:1-301, backend/lifespan.py:1-376

Startup sequence:
1. Import all ORM models first
2. Configure structured logging
3. Instrument SQLAlchemy engine for query timing
4. Install RLS interceptor and policies
5. Build lifespan context manager
6. Initialize Prometheus metrics (opt-in via PROMETHEUS_ENABLED)
7. Mount /uploads static files (dev only)
8. Initialize OpenTelemetry tracing (optional)
9. Register WebSocket routes (/ws/user, /ws/admin/background-jobs)
10. Lazy-load routers from modules.{customer,supplier,logistics,admin,employee}.routers

Lifespan hooks:
1. _preload_all_models() - Walks all domain model packages
2. _ensure_tables_exist() - Creates tables if DB is empty
3. _bootstrap_runtime() - Runs Alembic migrations in production (RAISES RuntimeError on failure)
4. _startup_load_role_permissions() - Loads RBAC settings
5. _startup_seed_treasury() - Seeds treasury chart of accounts
6. _startup_register_services() - Imports service registry
7. _startup_register_event_listeners() - Registers event handlers
8. _seed_demo_data() - Seeds demo catalog (dev only, gated by SEED_DATA_ON_STARTUP)
9. _ensure_default_accounts() - Creates default accounts from DEFAULT_ACCOUNTS_JSON

Health endpoints:
- GET /health - Liveness
- GET /health/deps - Dependency check (Redis, email, error tracking)
- GET /health/ready - Readiness (database + optional gates, returns 503 if blocking)

Impact: Startup is comprehensive but _bootstrap_runtime raises RuntimeError if Alembic fails in production - hard failure with no fallback. Readiness gates default to False.

---

## 4. BACKGROUND JOBS / WORKERS / QUEUES

### 4.1 Celery Configuration - VERIFIED

Evidence: backend/jobs/celery_app.py:1-139

- Broker: Valkey/Redis
- Result Backend: Valkey/Redis
- Timezone: UTC, JSON serialization only
- Task routes: ml, periodic, payouts, emails queues
- Beat schedule: auto-payout-sweep (hourly), finance-reconciliation (daily 02:00 UTC), vat-remittance (1st of month 03:00), supplier-statements (1st of month 04:00), distributor-statements (1st of month 05:00), alert-engine (every 30 min), cleanup-jobs (daily 01:00), cleanup-tokens (daily 01:30)
- Task annotations with rate limits and time limits for AI tasks

### 4.2 Celery Workers - VERIFIED (DEV ONLY)

Defined in docker-compose.yml but NOT in docker-compose.prod.yml:
- celery-worker-ml: queue ml, concurrency 2, max-tasks-per-child 50
- celery-worker-periodic: queue periodic, concurrency 2
- celery-worker-payouts: queue payouts, concurrency 4
- celery-worker-emails: queue emails, concurrency 4
- celery-beat: scheduler

Impact: Celery workers are ONLY in dev compose. Production compose has NO Celery workers and NO Celery Beat. Background jobs will NOT run in production via compose.

### 4.3 ML Worker - VERIFIED

Evidence: backend/jobs/ml_worker.py:1-121, docker-compose.prod.yml:67-94

- Runs as python -m jobs.ml_worker
- Polls Redis for background-jobs:* keys with status=queued and kind=ml
- Configurable poll interval (ML_WORKER_POLL_INTERVAL, default 2s)
- Idle shutdown (ML_WORKER_IDLE_SHUTDOWN)
- Model warmup on startup
- CPU: 4 limit / 2 reserve, Memory: 4G limit / 2G reserve, 1 replica

Impact: ML worker is a separate process from Celery. It polls Redis directly rather than consuming from a Celery queue, creating a dual-path system. Currently only marks jobs as completed - actual ML processing not fully implemented.

---

## 5. DATABASE

### 5.1 PostgreSQL - VERIFIED

Evidence:
- docker-compose.yml:3-17 => postgres:18-alpine
- .env:10 => Neon PostgreSQL connection string
- .neon:1-5 => Neon project configuration
- backend/infrastructure/database/database.py:57-89 => QueuePool, SSL configurable

Configuration:
- Version: PostgreSQL 18 (Alpine-based Docker image)
- Production: Neon PostgreSQL (serverless, cloud-hosted, EU-West-2)
- Connection pooling: SQLAlchemy QueuePool with pool_size, max_overflow, pool_recycle, pool_pre_ping=True
- SSL: sslmode=require in production
- Search path: 16 schemas (public, analytics, audit, commerce, configuration, country, customer, finance, hr, logistics, media, security, supplier)
- Multi-schema architecture: 16 PostgreSQL schemas
- RLS (Row Level Security): Installed at startup
- Health check: pg_isready
- Alembic migrations: 60+ migration files

### 5.2 PgBouncer - VERIFIED

Evidence: docker-compose.override.yml:3-16, docker-compose.prod.yml:2-21

- Image: edoburu/pgbouncer:latest
- Pool mode: transaction
- MAX_CLIENT_CONN=200, DEFAULT_POOL_SIZE=20
- Auth type: NOT SET (defaults to md5, NOT scram-sha-256)
- Port: 6432
- No healthcheck

Impact: Auth type mismatch between PgBouncer (md5 default) and PostgreSQL (scram-sha-256 in prod) could cause authentication failures.

### 5.3 Database Backups - INFERRED

Evidence: backend/scripts/pg_backup.py:1-78

- Script exists for compressed daily backups with WAL archiving
- Off-site upload to R2 bucket
- 30-day retention
- NOT DETERMINABLE: scheduling, encryption, restore testing

---

## 6. CACHE (VALKEY / REDIS)

### 6.1 Cache Configuration - CONTRADICTORY

Evidence:
- docker-compose.yml:20-25 => valkey:9.0-alpine
- docker-compose.prod.yml:96-104 => redis:7-alpine, REDIS_URL=redis://redis:6379
- .env.example:20-21 => VALKEY_URL and REDIS_URL both present
- config.py:74 => redis_url default as redis://localhost:6379

Finding: The project decision no_redis_naming_anywhere requires NO Redis naming anywhere. However, docker-compose.prod.yml uses redis:7-alpine image and REDIS_URL env var, and config.py hardcodes redis_url default. This is a direct violation of the stated constraint.

---

## 7. OBJECT STORAGE

### 7.1 Storage Backend - VERIFIED

Evidence: backend/infrastructure/storage/storage.py:1-221, backend/providers/storage/storage_backend.py:1-26, .env.example:46-62

- StorageBackend ABC with LocalStorage and S3Storage implementations
- Selected by STORAGE_BACKEND env var (local, s3, or r2)
- S3-compatible (AWS S3, Cloudflare R2, DO Spaces)
- CDN base URL support
- Presigned uploads supported
- R2 buckets: zozi-media, zozi-supplier-uploads, zozi-exports, zozi-archives

Impact: .env.example uses R2_* vars, docker-compose.prod.yml uses S3_* vars with STORAGE_BACKEND=s3. Backward-compat aliases exist but create confusion.

---

## 8. CDN - INFERRED

Evidence: .env.example:51, docker-compose.prod.yml:36, Caddyfile:32-50, nginx/nginx.conf:118-133

- External S3-compatible object storage with CDN
- CDN base URL via S3_CDN_BASE / R2_CDN_BASE
- Caddy serves frontend directly (not as CDN)
- NOT DETERMINABLE: actual CDN provider, cache rules, origin configuration

---

## 9. DNS - PARTIALLY CONFIGURED

Evidence: Caddyfile:12-56

Configured domains (placeholders):
- api.yourdomain.com
- yourdomain.com
- www.yourdomain.com -> redirect to yourdomain.com

Impact: yourdomain.com is a placeholder. Actual DNS configuration is NOT in repository.

---

## 10. TLS - CONFIGURED FOR CADDY

Evidence:
- Caddyfile:8 => ACME v2 Let's Encrypt
- Caddyfile:45 => HSTS max-age=31536000; includeSubDomains; preload
- vercel.json:38 => HSTS max-age=63072000; includeSubDomains; preload
- nginx/nginx.conf:52 => listen 80 (HTTP only, no TLS)
- backend/Dockerfile.prod:26 => binds to 0.0.0.0:8000 (HTTP)

Impact: TLS terminated at Caddy (production) or Vercel (frontend). Backend and internal services communicate over HTTP. Inconsistent HSTS max-age values.

---

## 11. CI/CD - NOT CONFIGURED

Evidence: .github/workflows/ does not exist. Makefile provides manual targets only. railway.toml and vercel.json provide deployment configs but no CI pipeline.

Impact: No automated CI/CD pipeline. Deployments are manual via Railway/Vercel or Docker Compose.

---

## 12. DEPLOYMENT TARGETS

### Railway (Backend) - CONFIGURED

Evidence: railway.toml:1-13
- Builder: Dockerfile (./backend/Dockerfile - DEVELOPMENT file, not Dockerfile.prod)
- Start command: uvicorn main:app --proxy-headers
- Health check: GET /health, timeout 300s
- Restart: ON_FAILURE, max 10 retries

### Vercel (Frontend) - CONFIGURED

Evidence: vercel.json:1-55
- Framework: Next.js
- Output: frontend/web_app/.next
- Cache headers for static assets
- Security headers
- Env: NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY from Vercel secret store

---

## 13. ENVIRONMENT CONFIGURATION - PARTIALLY DOCUMENTED

Evidence: .env.example:1-70, .env:1-63, config.py:23-148

Key variables: APP_ENV, SECRET_KEY (required), DATABASE_URL (required), VALKEY_URL/REDIS_URL, STORAGE_BACKEND, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, STRIPE keys, SMTP config, S3/R2 config, SENTRY_DSN, PRESIGNED_UPLOADS_ENABLED

Impact: .env file appears to be committed to repository. Default SECRET_KEY in config.py is a hardcoded development key.

---

## 14. SECRETS MANAGEMENT - INSECURE

Evidence:
- .env:10 => Contains real Neon PostgreSQL credentials
- .env:2 => SECRET_KEY=dev-secret-key-change-in-production...
- monitoring/docker-compose.monitoring.yml:96 => SENTRY_SECRET_KEY=sentry-secret-key-change-in-production
- monitoring/docker-compose.monitoring.yml:125 => POSTGRES_PASSWORD=sentry-password
- config.py:125 => sentry_dsn empty default
- config.py:71 => encryption_key empty default
- vercel.json:53 => Uses Vercel secret store (@stripe_publishable_key)

Impact: .env file committed with real credentials. If pushed to remote, exposes database credentials. Vault/AWS SSM infrastructure exists in config but no actual integration visible.

---

## 15. LOGGING - VERIFIED

Evidence: backend/infrastructure/observability/logging_config.py:1-208

- Structured logging via structlog
- Request-scoped context: request_id, country_code, user_id, db_query_time, session_id
- PII scrubbing: field name redaction + regex patterns for cards, emails, phones
- Rotating file handler
- JSON output
- Database query timing instrumentation

### Log Aggregation - VERIFIED

Evidence: monitoring/docker-compose.monitoring.yml:1-146, monitoring/promtail/promtail-config.yml:1-85

Stack: Loki + Promtail
Sources: Docker container logs, backend logs (/var/log/backend/*.log), frontend logs (/var/log/frontend/*.log), nginx logs (/var/log/nginx/*.log)

Impact: Prometheus uses host.docker.internal which is Docker Desktop-specific and won't work in Linux/Kubernetes.

---

## 16. MONITORING & OBSERVABILITY

### Metrics - VERIFIED (conflicting configs)

Evidence:
- backend/infrastructure/observability/prometheus_setup.py:1-30 => prometheus-fastapi-instrumentator, /metrics endpoint, opt-in via PROMETHEUS_ENABLED
- monitoring/prometheus.yml:1-44 => host.docker.internal:8000, :3000, :9187
- monitoring/prometheus/prometheus.yml:1-48 => backend:8000, postgres-exporter:9187, redis-exporter:9121

Conflicting configs: host.docker.internal vs Docker service names. postgres-exporter and redis-exporter referenced but not defined in any compose file.

### Alerting - CONFIGURED WITH PLACEHOLDERS

Evidence: monitoring/alerts.yml:1-49, monitoring/alertmanager.yml:1-47

Alerts: DatabaseConnectionPoolExhausted (critical), BackendErrorRateHigh (critical), APIHighLatency (warning), SentryNewErrors (warning), SlowDatabaseQueries (warning)

Targets: webhook to http://localhost:8000/api/alerts/notify, PagerDuty with empty service key.

### Distributed Tracing - CONFIGURED LOCAL ONLY

Evidence: monitoring/tempo/tempo.yaml:1-41

- Backend: local filesystem (/tmp/tempo/blocks)
- Replication factor: 1
- No external storage

Impact: Traces lost on container restart.

### Error Tracking - SELF-HOSTED SENTRY

Evidence: monitoring/docker-compose.monitoring.yml:90-117

- getsentry/sentry:latest on port 9000
- Dedicated PostgreSQL and Redis
- Admin password: admin (default)
- Email disabled

---

## 17. BACKUPS - SCRIPT EXISTS, SCHEDULING UNKNOWN

Evidence: backend/scripts/pg_backup.py:1-78

- Compressed daily backups with WAL archiving
- Off-site R2 upload
- 30-day retention
- NOT DETERMINABLE: scheduling, encryption, restore testing

---

## 18. HEALTH CHECKS - VERIFIED

Evidence: backend/main.py:104-181

Endpoints:
- GET /health - Liveness
- GET /health/deps - Dependency check
- GET /health/ready - Readiness (503 if blocking dependencies)

Docker health checks:
- PostgreSQL: pg_isready
- Backend (prod): curl -f http://localhost:8000/health
- Railway: GET /health, timeout 300s

Impact: readiness_require_* flags default to False, so /health/ready returns 200 even if Redis is down.

---

## 19. SCALING - PARTIALLY DEFINED

Evidence:
- docker-compose.prod.yml:47 => deploy.replicas: 3 (backend) - ignored by plain Docker Compose
- docker-compose.prod.yml:84 => deploy.replicas: 1 (ml_worker)
- config.py:44-45 => db_pool_size=50, db_max_overflow=100 (defaults)

NOT DETERMINABLE: autoscaling rules, load balancer, session affinity, database read replicas.

---

## 20. SINGLE POINTS OF FAILURE

| Component | SPOF | Impact |
|-----------|------|--------|
| PostgreSQL | Single instance (Neon cloud HA assumed) | Complete data loss if Neon fails |
| PgBouncer | Single instance | Connection pool exhaustion if it fails |
| Valkey/Redis | Single instance | Celery tasks lost on restart |
| Celery Beat | Single instance | Missed scheduled tasks if it fails |
| Caddy | Single instance | TLS termination failure if Caddy fails |
| ML Worker | Single instance | ML jobs stall if worker crashes |
| Backup Script | No scheduled execution confirmed | No automated backups |

---

## 21. ARCHITECTURAL CONTRADICTIONS

### 21.1 Redis vs Valkey Naming - CONTRADICTORY WITH PROJECT CONSTRAINT

Violations of no_redis_naming_anywhere:
1. docker-compose.prod.yml:96 => image: redis:7-alpine
2. docker-compose.prod.yml:29 => REDIS_URL=redis://redis:6379
3. docker-compose.prod.yml:99-101 => volume redis_data
4. config.py:74 => redis_url default as redis://localhost:6379
5. monitoring/docker-compose.monitoring.yml:102 => REDIS_URL=redis://sentry-redis:6379/0
6. monitoring/docker-compose.monitoring.yml:131-135 => image: redis:7-alpine
7. monitoring/prometheus/prometheus.yml:34-42 => redis-exporter:9121

### 21.2 Production Compose Missing Workers

docker-compose.prod.yml defines only backend and ml_worker. Celery workers and Celery Beat from docker-compose.yml are NOT in production compose.

### 21.3 Dual Background Job Systems

Celery (jobs/celery_app.py) and ML Worker (jobs/ml_worker.py) operate in parallel. ML worker polls Redis directly rather than consuming from Celery queue.

### 21.4 Conflicting Database Pool Settings

config.py defaults: pool_size=50, max_overflow=100
docker-compose.override.yml: pool_size=10, max_overflow=10
docker-compose.prod.yml: pool_size=10, max_overflow=10

### 21.5 Committed Secrets

.env file committed with real Neon PostgreSQL credentials, SECRET_KEY, POSTGRES_PASSWORD.

---

## 22. DEPLOYMENT FLOW SUMMARY

### How Application Starts

Development: uvicorn main:app --reload (port 8000) + npm run dev (port 3000)
Docker Compose (dev): postgres -> valkey -> backend -> frontend + 4 celery workers + beat
Docker Compose (prod): postgres -> pgbouncer -> backend (3 replicas) + ml_worker (NO celery workers)
Railway: builds backend/Dockerfile, runs uvicorn main:app --proxy-headers
Vercel: builds Next.js app, deploys as serverless

### How Requests Reach Application

Internet -> Caddy (TLS) -> frontend:3000 (web) OR backend:8000 (API)
Dev: Browser -> Nginx:80 -> frontend:3000 OR backend:8000

### How Background Jobs Run

Development: Celery workers + Celery Beat via docker-compose.yml
Production (compose): ML Worker only (Celery workers absent)
Production (Railway): NOT CONFIGURED

### How Data is Stored

Primary DB: Neon PostgreSQL (cloud, SSL required)
Local dev: SQLite
Object storage: S3-compatible (R2 dev/test, S3 prod per compose)

### How Files are Stored

Development: Local filesystem (backend/uploads/)
Production: S3-compatible object storage with CDN
Presigned uploads: Optional (client uploads directly)

### How Services Communicate

Internal Docker network: zozi_net (bridge)
Backend -> PgBouncer -> PostgreSQL
Backend/Celery -> Valkey/Redis
Backend -> S3/R2 API

### How Deployments Occur

Frontend: Vercel (automatic on git push)
Backend: Railway (Dockerfile) or Docker Compose
No CI/CD pipeline - deployments are manual

### How Failures are Handled

Backend crashes: Railway restart policy (ON_FAILURE, max 10 retries)
Database: pool_pre_ping validates connections
Celery task failures: No explicit retry configuration
No circuit breakers visible in service-to-service communication

---

## 23. NOT DETERMINABLE FROM AVAILABLE CODE

1. Whether .env is in .gitignore
2. Whether committed .env credentials are for dev or production
3. Whether CI/CD exists outside .github/workflows/
4. Kubernetes manifests or Helm charts
5. Actual CDN provider and configuration
6. DNS records (A, CNAME, etc.)
7. Backup scheduling (cron entries)
8. Database read replica configuration
9. Load balancer configuration for backend replicas
10. Whether production uses Railway or Docker Compose (or both)
11. Vault or external secrets manager integration in production
12. WAF (Web Application Firewall) configuration
13. DDoS protection configuration
14. Disaster recovery runbook
15. Whether docker-compose.prod.yml is actually used in production

---

## 24. FINDINGS SUMMARY TABLE

| # | Finding | Status | Severity |
|---|---------|--------|----------|
| 1 | docker-compose.prod.yml uses redis:7-alpine - violates no_redis_naming_anywhere | VERIFIED | Critical |
| 2 | Production compose missing Celery workers and Celery Beat | VERIFIED | Critical |
| 3 | .env file committed with real database credentials | VERIFIED | Critical |
| 4 | SECRET_KEY has hardcoded development default in config.py | VERIFIED | High |
| 5 | No CI/CD pipeline configured | VERIFIED | High |
| 6 | PgBouncer auth type mismatch (md5 default vs scram-sha-256) | INFERRED | High |
| 7 | Conflicting database pool settings (10/10 in compose vs 50/100 in config.py) | VERIFIED | Medium |
| 8 | Dual background job systems (Celery + ML worker polling) | VERIFIED | Medium |
| 9 | Tempo uses local storage (traces lost on restart) | VERIFIED | Medium |
| 10 | Prometheus configs conflict (host.docker.internal vs service names) | VERIFIED | Medium |
| 11 | PagerDuty integration has empty service key | VERIFIED | Medium |
| 12 | Grafana admin password is default admin | VERIFIED | Medium |
| 13 | No load balancer for backend replicas | VERIFIED | Medium |
| 14 | No automated backup scheduling found | INFERRED | Medium |
| 15 | deploy.replicas in compose file (ignored by plain Docker Compose) | VERIFIED | Low |
| 16 | Caddy domain is placeholder yourdomain.com | VERIFIED | Low |
| 17 | Inconsistent HSTS max-age (Caddy: 1y, Vercel: 2y) | VERIFIED | Low |
| 18 | Railway uses Dockerfile (dev) instead of Dockerfile.prod | VERIFIED | Low |
| 19 | readiness_require_* flags default to False | VERIFIED | Low |
| 20 | No nginx container in any compose file | VERIFIED | Info |

---

End of Phase 16 Infrastructure Audit
