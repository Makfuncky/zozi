# ZOZI CI/CD Pipeline

Complete continuous integration and deployment pipeline for the ZOZI marketplace platform.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PULL REQUEST / PUSH                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ci.yml (CI Pipeline)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Backend     │  │  Frontend    │  │  Frontend Type Check     │  │
│  │  Lint (ruff) │  │  Lint (ESLint│  │  (tsc)                   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│         │                  │                      │                 │
│         ▼                  ▼                      ▼                 │
│  ┌──────────────┐  ┌──────────────────────────────────────────┐    │
│  │  Backend     │  │  Frontend Unit Tests (Jest)              │    │
│  │  Tests       │  └──────────────────────────────────────────┘    │
│  │  (pytest)    │                                                 │
│  └──────────────┘                                                 │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CI Success Gate (all must pass)                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    (push to main/staging)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      build.yml (Build Pipeline)                     │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐  │
│  │  Build Backend Image    │  │  Build Frontend Image           │  │
│  │  (Dockerfile.prod)      │  │  (Dockerfile)                   │  │
│  │  → ghcr.io/zozi-backend │  │  → ghcr.io/zozi-frontend        │  │
│  └─────────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                          (release published)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     deploy.yml (Deploy Pipeline)                    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Pre-deploy Checks (architecture laws + critical path tests) │  │
│  └──────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  STAGING DEPLOYMENT                                          │  │
│  │  ├── Backend → Railway (staging) + Alembic migrations        │  │
│  │  └── Frontend → Vercel (preview)                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PRODUCTION DEPLOYMENT                                       │  │
│  │  ├── Backend → Railway (production) + Alembic migrations     │  │
│  │  └── Frontend → Vercel (production)                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Smoke Tests (health checks + critical API paths)            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow Files

| File | Trigger | Purpose |
|------|---------|---------|
| `.github/workflows/ci.yml` | PR to main/staging, push to main/staging | Lint, typecheck, unit tests, architecture tests |
| `.github/workflows/build.yml` | Push to main/staging, tags v*, manual | Build and push Docker images to GHCR |
| `.github/workflows/deploy.yml` | Push to main, release published, manual | Deploy to staging → production with smoke tests |
| `.github/workflows/e2e.yml` | PR to main, push to main, manual | Playwright E2E tests against local or staging |
| `.github/workflows/rollback.yml` | Manual only | Emergency rollback for backend and/or frontend |

---

## Environment Variables

### Repository Variables (Settings → Secrets and variables → Actions → Variables)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL_STAGING` | Backend API URL for staging | `https://staging-api.zozi.com` |
| `NEXT_PUBLIC_API_URL_PRODUCTION` | Backend API URL for production | `https://api.zozi.com` |

### Repository Secrets (Settings → Secrets and variables → Actions → Secrets)

| Secret | Description | Used By |
|--------|-------------|---------|
| `RAILWAY_TOKEN_STAGING` | Railway API token for staging | deploy.yml |
| `RAILWAY_TOKEN_PRODUCTION` | Railway API token for production | deploy.yml, rollback.yml |
| `RAILWAY_PROJECT_ID` | Railway project ID | deploy.yml, rollback.yml |
| `VERCEL_TOKEN` | Vercel API token | deploy.yml, rollback.yml |
| `VERCEL_ORG_ID` | Vercel organization ID | deploy.yml, rollback.yml |
| `VERCEL_PROJECT_ID` | Vercel project ID | deploy.yml, rollback.yml |
| `AUTH_SECRET` | JWT verification secret (must match backend SECRET_KEY) | deploy.yml |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | build.yml |
| `SENTRY_DSN` | Sentry error tracking DSN | deploy.yml (optional) |
| `SLACK_WEBHOOK_URL` | Slack notification webhook | deploy.yml (optional) |

### Environment Secrets (per environment in GitHub)

#### Staging Environment
| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | NEON connection string for staging |
| `VALKEY_URL` | Valkey connection string for staging |
| `SECRET_KEY` | JWT signing key for staging |
| `STRIPE_SECRET_KEY` | Stripe secret key for staging |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret for staging |

#### Production Environment
| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | NEON connection string for production |
| `VALKEY_URL` | Valkey connection string for production |
| `SECRET_KEY` | JWT signing key for production |
| `STRIPE_SECRET_KEY` | Stripe secret key for production |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret for production |
| `R2_BUCKET` | R2 bucket for file storage |
| `R2_REGION` | R2 region |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret key |

---

## Deployment Strategy

### Staging Deployment (Automatic on push to `main`)

1. **Trigger**: Every push to `main` branch
2. **Backend**: Railway auto-deploys from `main` branch
3. **Frontend**: Vercel creates a preview deployment
4. **Migrations**: Alembic migrations run automatically after backend deploy
5. **Health Check**: Automated health check against staging endpoints

### Production Deployment (Release-based)

1. **Trigger**: GitHub Release published (recommended) or manual workflow dispatch
2. **Pre-deploy Gates**:
   - Architecture law tests must pass
   - Critical path tests (accounts, orders, finance, catalog) must pass
3. **Backend Deploy**:
   - Railway production environment
   - Alembic migrations run before traffic switch
   - Health check verification
4. **Frontend Deploy**:
   - Vercel production deployment
   - Atomic swap (no downtime)
5. **Post-deploy Verification**:
   - Backend health check (5 retries, 10s interval)
   - Frontend health check (5 retries, 10s interval)
   - Critical API path verification

### Blue/Green Deployment Notes

- **Railway**: Supports native blue/green via environment promotion
- **Vercel**: Atomic deployments — new deployment goes live only after successful build
- **Database**: Alembic migrations are backward-compatible (additive only) to support rollback

---

## Rollback Procedure

### Automated Rollback (rollback.yml)

1. Navigate to **Actions → Rollback → Run workflow**
2. Select environment (staging/production)
3. Specify version to rollback to:
   - **Backend**: Git SHA or version tag (e.g., `sha-abc123` or `v1.2.3`)
   - **Frontend**: Vercel deployment URL
4. Provide reason for rollback
5. Workflow will:
   - Deploy the specified version
   - Run health checks
   - Create a GitHub issue documenting the incident

### Manual Rollback (if workflow fails)

#### Backend (Railway)
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login and select project
railway login
railway link --project <project-id>

# Rollback to previous deployment
railway rollback --environment production

# Or deploy a specific commit
railway up --environment production --commit <sha>
```

#### Frontend (Vercel)
```bash
# Install Vercel CLI
npm install -g vercel

# List deployments
vercel ls

# Promote a previous deployment
vercel promote <deployment-url>

# Or rollback
vercel rollback
```

#### Database Rollback
```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision-id>
```

---

## Required GitHub Configuration

### Branch Protection Rules (main)

1. Go to **Settings → Branches → Add rule**
2. Branch pattern: `main`
3. Settings:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Status checks: `CI Success Gate`, `Build Success Gate`
   - ✅ Require conversation resolution before merging
   - ✅ Include administrators

### Environment Protection Rules

1. Go to **Settings → Environments**
2. Create `staging` environment:
   - ✅ Required reviewers: 0 (auto-deploy)
   - Wait timer: 0 minutes
3. Create `production` environment:
   - ✅ Required reviewers: 1 (team lead approval)
   - Wait timer: 5 minutes
   - ✅ Deployment branches: `main`, `releases/*`

---

## Monitoring & Notifications

### Deployment Status

- GitHub Deployments API tracks all deployments
- Environment URLs configured for direct access
- Deployment history visible in GitHub Environments tab

### Failure Notifications

The pipeline creates GitHub Issues for:
- Rollback events (labeled `rollback`, `incident`)
- Failed deployments (via GitHub Actions notifications)

### Recommended Additions

1. **Sentry**: Error tracking with release tracking
2. **Datadog/New Relic**: APM and infrastructure monitoring
3. **PagerDuty/Opsgenie**: Incident management for production alerts
4. **Slack**: Deployment notifications via webhook

---

## Local Development

Run CI checks locally before pushing:

```bash
# Backend
cd backend
ruff check .
python -m pytest tests/architecture/ -v --timeout=60

# Frontend
cd frontend/web_app
npm run lint
npx tsc --noEmit --skipLibCheck
npm test

# E2E (requires running servers)
npx playwright test
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Architecture test fails | Run `python scripts/_gen_import_laws_baseline.py` after fixing imports |
| Railway deploy fails | Check `RAILWAY_TOKEN` and `RAILWAY_PROJECT_ID` secrets |
| Vercel deploy fails | Verify `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` |
| Migration fails | Ensure migrations are backward-compatible; check `alembic history` |
| Health check times out | Verify Railway/Vercel deployment URLs are correct |
| Docker build fails | Check `Dockerfile.prod` dependencies match `requirements.txt` |
