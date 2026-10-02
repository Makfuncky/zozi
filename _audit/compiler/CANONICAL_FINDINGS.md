# CANONICAL FINDINGS
*Compiled by the audit compiler — aggregated across all dimension files.*
*Source: `_audit/dimensions/07_CONTRADICTIONS.md` (37 findings)*

## Compilation Status

| Dimension | Findings | Compiled | Date |
|----|----------|----------|------|
| contradictions | 37 | 37 | 2026-10-01 |

## Compiled Findings (by file location)

### backend/Dockerfile
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-030 | contradictions | 1 | `FROM python:3.11-slim` | Python 3.13.x | partial |
| CONTRAD-037 | contradictions | 19,30 | `COPY requirements.txt .` + `CMD ["uvicorn", ...]` | Gunicorn with Uvicorn workers | no |

### backend/config.py
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-019 | contradictions | 279 | `default_country: str = Field(default="AE")` | DEFAULT_COUNTRY default US | partial |
| CONTRAD-020 | contradictions | 204-205 | `vat_rate: float` + `zozi_commission_rate: float` | Decimal/Numeric; Float FORBIDDEN (Law 19) | yes |

### backend/modules/finance/__init__.py
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-001 | contradictions | 1 | `modules/finance/` directory exists with `routers/cash_management.py` | 5 fixed modules (L-13) | yes |

### backend/modules/employee/routers/hr.py
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-034 | contradictions | 1 | Both `hr.py` (file) and `hr/` (package) exist; file shadowed | Remove orphaned hr.py; consolidate into hr/ package | yes |

### backend/domains/payments/__init__.py
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-002 | contradictions | 1 | `domains/payments/` full domain package | Payments is provider-only concern; 15 fixed domains (L-12) | yes |

### backend/domains/media/
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-003 | contradictions | (directory) | Full domain package (models, services, ports, etc.) | Canonical states media has no dedicated domain | partial |

### backend/providers/
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-004 | contradictions | (directory) | 5 extra providers: news, automation, scanner, voice, analytics | Canonical provider tree only (L-9/L-16) | no |

### backend/requirements.txt
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-005 | contradictions | 8 | `fastapi==0.115.2` | FastAPI 0.141.x | yes |
| CONTRAD-006 | contradictions | 9 | `uvicorn[standard]==0.51.0` | Uvicorn 0.35.0+ with uvloop/httptools | partial |
| CONTRAD-007 | contradictions | 15 | `alembic==1.18.5` | Alembic 1.19.1+ (L-49) | partial |
| CONTRAD-008 | contradictions | 40 | `pydantic-settings==2.7.1` | pydantic-settings 2.9.1+ | partial |
| CONTRAD-009 | contradictions | 63 | `prometheus-fastapi-instrumentator==7.1.0` | 8.1.0+ | partial |
| CONTRAD-010 | contradictions | 61 | `sentry-sdk==2.66.1` (no [fastapi]) | sentry-sdk[fastapi] 2.68.1 | partial |
| CONTRAD-011 | contradictions | 91 | `stripe==15.3.1` | stripe 15.5.1 | partial |
| CONTRAD-012 | contradictions | 48 | `python-magic==0.4.27` (forbidden) | puremagic 2.2.0 | no |
| CONTRAD-013 | contradictions | 17 | `psycopg2-binary==2.9.12` (forbidden) | asyncpg only; psycopg forbidden | no |
| CONTRAD-014 | contradictions | 79,80 | `pytz==2026.3.post1` + `tzlocal==5.4.4` (both forbidden) | zoneinfo-stdlib only | no |
| CONTRAD-015 | contradictions | 36 | `requests==2.34.2` (forbidden) | httpx async only; requests forbidden | no |
| CONTRAD-016 | contradictions | 73,74 | `slowapi==0.1.10` + `limits==5.8.0` | fastapi-limiter-valkey (TECHNOLOGY_STACK.md:89) | yes |
| CONTRAD-017 | contradictions | 1-102 | `uvloop` and `httptools` absent | uvloop 0.21.0 + httptools 0.7.0 | no |
| CONTRAD-018 | contradictions | 1-102 | `pybreaker` absent | pybreaker 1.4.1 | partial |
| CONTRAD-035 | contradictions | 14 | `sqlalchemy==2.0.51` | SQLAlchemy 2.0.52 (L-49) | no |
| CONTRAD-036 | contradictions | 1-102 | `fastapi-limiter-valkey` absent | fastapi-limiter-valkey latest stable | yes |

### backend/infrastructure/security/rate_limiter.py
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-016 | contradictions | 24 | Imports `fastapi_limiter_valkey` | Package should be in requirements.txt | yes |
| CONTRAD-036 | contradictions | 24 | Imports `fastapi_limiter_valkey` | Package absent from requirements.txt | yes |

### docker-compose.yml
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-031 | contradictions | 4 | `image: postgres:18-alpine` | PostgreSQL 16 (`postgres:16-alpine`) | partial |

### frontend/web_app/package.json
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-021 | contradictions | 34 | `"next": "16.3.4"` | Next.js 16.3.5 | no |
| CONTRAD-022 | contradictions | 29 | `"framer-motion": "^12.0.0"` | 13.2.0+ | no |
| CONTRAD-023 | contradictions | 44 | `"zustand": "^5.0.11"` | Zustand 5.0.14 | no |
| CONTRAD-024 | contradictions | 43 | `"zod": "^3.25.76"` | Zod 4.3.6 | yes |
| CONTRAD-025 | contradictions | 15 | `"@hookform/resolvers": "^5.9.1"` | 5.2.2 | partial |

### frontend/web_app/next.config.ts
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-029 | contradictions | 51-53 | rewrites `/hr/:path*` → `/hr/:path*` | No standalone hr module (5 fixed modules) | yes |

### frontend/web_app/src/app/
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-033 | contradictions | (directory) | Both `logistics-partner/` and `logistics-partners/` dirs | One route-tree per actor | no |

### frontend/mobile_app/package.json
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-026 | contradictions | 22 | `"expo": "~57.0.9"` | Expo SDK 57.0.20+ | partial |
| CONTRAD-027 | contradictions | 28 | `"react-native": "0.81.4"` | React Native 0.86.3 | partial |
| CONTRAD-028 | contradictions | 26 | `"react": "19.1.0"` | React 19.2.8 | partial |

### package.json (root)
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-032 | contradictions | 7-8 | `npm run` in scripts | pnpm exclusively (TECHNOLOGY_STACK.md:183) | partial |

### _most_imp_docx/ARCHITECTURE_STACK.md
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-001 | contradictions | 539 | "5 modules: admin, customer, employee, logistics, supplier" | `modules/finance/` must not exist | yes |
| CONTRAD-002 | contradictions | 88-103 | "providers/payments" | `domains/payments/` must not exist | yes |
| CONTRAD-003 | contradictions | 354 | "media has no dedicated domain" | `domains/media/` must be demoted or promoted | partial |
| CONTRAD-004 | contradictions | 88-103 | Canonical provider tree | 5 extra providers undocumented | no |
| CONTRAD-020 | contradictions | 546 | "No float for money — Monetary values MUST use Decimal or Numeric" | `config.py` uses float for vat_rate, zozi_commission_rate | yes |
| CONTRAD-029 | contradictions | 539 | "5 modules: admin, customer, employee, logistics, supplier" | `/hr/*` standalone rewrite exists | yes |
| CONTRAD-034 | contradictions | 186 | Route tree definition | Both hr.py and hr/ exist; file is unreachable | yes |

### _most_imp_docx/TECHNOLOGY_STACK.md
| ID | Source dimension | Line | Current | Target | Completion blocker |
|----|-----------------|------|---------|--------|-------------------|
| CONTRAD-005 | contradictions | 23 | "FastAPI 0.141.x" | `requirements.txt` has 0.115.2 | yes |
| CONTRAD-006 | contradictions | 25 | "Uvicorn 0.35.0+" | `requirements.txt` has 0.51.0 | partial |
| CONTRAD-007 | contradictions | 45 | "Alembic 1.19.1+" | `requirements.txt` has 1.18.5 | partial |
| CONTRAD-008 | contradictions | 31 | "pydantic-settings 2.9.1+" | `requirements.txt` has 2.7.1 | partial |
| CONTRAD-009 | contradictions | 136 | "prometheus-fastapi-instrumentator 8.1.0+" | `requirements.txt` has 7.1.0 | partial |
| CONTRAD-010 | contradictions | 134 | "sentry-sdk[fastapi] 2.68.1" | `requirements.txt` has 2.66.1 without [fastapi] | partial |
| CONTRAD-011 | contradictions | 99 | "stripe 15.5.1" | `requirements.txt` has 15.3.1 | partial |
| CONTRAD-012 | contradictions | 72 | "puremagic 2.2.0; python-magic forbidden" | `requirements.txt` locks python-magic, omits puremagic | no |
| CONTRAD-013 | contradictions | 43 | "psycopg forbidden in production" | `requirements.txt` locks psycopg2-binary | no |
| CONTRAD-014 | contradictions | 123 | "pytz/tzlocal forbidden" | `requirements.txt` locks both | no |
| CONTRAD-015 | contradictions | 98 | "requests forbidden" | `requirements.txt` locks requests | no |
| CONTRAD-016 | contradictions | 89 | "fastapi-limiter-valkey" | `requirements.txt` has slowapi/limits | yes |
| CONTRAD-017 | contradictions | 26-27 | "uvloop 0.21.0" + "httptools 0.7.0" | `requirements.txt` omits both | no |
| CONTRAD-018 | contradictions | 90 | "pybreaker 1.4.1" | `requirements.txt` omits it | partial |
| CONTRAD-019 | contradictions | 392 | "DEFAULT_COUNTRY default US" | `config.py` defaults to AE | partial |
| CONTRAD-021 | contradictions | 180 | "Next.js 16.3.5" | web_app has 16.3.4 | no |
| CONTRAD-022 | contradictions | 199 | "motion (framer-motion) 13.2.0+" | web_app and shared have ^12.0.0 | no |
| CONTRAD-023 | contradictions | 214 | "Zustand 5.0.14" | web_app has ^5.0.11 | no |
| CONTRAD-024 | contradictions | 217 | "Zod 4.3.6" | web_app has ^3.25.76 | yes |
| CONTRAD-025 | contradictions | 218 | "@hookform/resolvers 5.2.2" | web_app has ^5.9.1 | partial |
| CONTRAD-026 | contradictions | 245 | "Expo SDK 57.0.20+" | mobile_app has ~57.0.9 | partial |
| CONTRAD-027 | contradictions | 246 | "React Native 0.86.3" | mobile_app has 0.81.4 | partial |
| CONTRAD-028 | contradictions | 181 | "React 19.2.8" | mobile_app has 19.1.0 | partial |
| CONTRAD-030 | contradictions | 22 | "Python 3.13.x" | Dockerfile uses 3.11-slim | partial |
| CONTRAD-031 | contradictions | 42 | "PostgreSQL 16 | Dev" | docker-compose.yml uses postgres:18-alpine | partial |
| CONTRAD-032 | contradictions | 183 | "Do NOT use npm or yarn" | root package.json uses npm run | partial |
| CONTRAD-035 | contradictions | 44 | "SQLAlchemy 2.0.52" | requirements.txt has 2.0.51 | no |
| CONTRAD-036 | contradictions | 89 | "fastapi-limiter-valkey latest stable" | requirements.txt omits it entirely | yes |
| CONTRAD-037 | contradictions | 280 | "Docker Compose 2.40.0+ | Dev | Gunicorn + Uvicorn workers" | dev Dockerfile runs Uvicorn directly | no |

## Summary by Law

| Law | Implicated findings |
|-----|-------------------|
| L-12 (fixed 15 domains) | CONTRAD-002, CONTRAD-003 |
| L-13 (fixed 5 modules) | CONTRAD-001 |
| L-19 (no float for money) | CONTRAD-020 |
| L-9/L-16 (providers in providers/) | CONTRAD-004, CONTRAD-016, CONTRAD-036 |
| L-49 (single Alembic head) | CONTRAD-007, CONTRAD-035 |
| L-102a (env var policy) | — |

## Priority Breakdown

| Priority | Count | Completion blockers |
|----------|-------|-------------------|
| P0 | 9 | 9 yes |
| P1 | 7 | 0 yes, 7 partial |
| P2 | 14 | 0 yes, 0 partial, 14 no |
| P3 | 7 | 0 yes, 0 partial, 7 no |

## Clusters Identified

| Cluster ID | Phase | Root cause | Members | Recommended fix |
|---|---|---|---|---|
| CLUSTER-extra-layer | arch | Extra top-level packages/modules violating fixed laws | CONTRAD-001, CONTRAD-002, CONTRAD-003, CONTRAD-004, CONTRAD-034 | Delete/remove non-canonical packages; move code to canonical locations; remove orphaned files |
| CLUSTER-deps-mismatch | tech | requirements.txt does not match TECHNOLOGY_STACK.md | CONTRAD-005–011, CONTRAD-017, CONTRAD-018, CONTRAD-035 | Pin all deps to canonical versions; remove forbidden packages |
| CLUSTER-config-drift | config | config.py values contradict TECHNOLOGY_STACK.md | CONTRAD-019, CONTRAD-020 | Align DEFAULT_COUNTRY to US; change money fields to Decimal |
| CLUSTER-frontend-drift | frontend | Frontend package.json versions behind canonical | CONTRAD-021–028, CONTRAD-029, CONTRAD-033 | Bump all frontend packages to canonical versions; fix routing |
| CLUSTER-package-mismatch | build | Production imports don't match pinned requirements; npm misuse | CONTRAD-016, CONTRAD-032, CONTRAD-036 | Align requirements with imports; switch to pnpm |
| CLUSTER-dev-env-drift | docs | Dev containers/compose diverge from TECHNOLOGY_STACK.md | CONTRAD-030, CONTRAD-031, CONTRAD-037 | Align Dockerfile and compose to canonical Python 3.13, Postgres 16, Gunicorn |

## Over all

### Problem(s)
1. **Three structural law violations**: `modules/finance/` (6th module), `domains/payments/` (17th domain), and `domains/media/` (16th domain) all violate Laws 12 and 13. An orphaned `hr.py` file is shadowed by an `hr/` package.
2. **11 dependency version mismatches** — including one major gap (prometheus 7→8), two forbidden packages actively locked (`python-magic`, `psycopg2-binary`), and one forbidden import pair (`slowapi`/`limits` replacing canonical `fastapi-limiter-valkey`).
3. **6 frontend version drifts** — Zod is on a major version gap (3.x vs required 4.x); four packages are behind minor versions.
4. **Config drift in `config.py`** — `DEFAULT_COUNTRY` defaults to `AE` (canonical: `US`) and money fields are typed as `float` (Law 19 violation).
5. **Dev environment drift** — Python 3.11 in Dockerfile (canonical: 3.13); Postgres 18 in compose (canonical: 16); Uvicorn-only dev CMD without Gunicorn.
6. **Package manager violation** — root `package.json` uses `npm run` despite pnpm-only mandate (TECHNOLOGY_STACK.md:183).

### Solution(s)
1. Delete `modules/finance/`, `domains/payments/`, and either promote `domains/media/` to canonical or demote it; remove orphaned `hr.py`.
2. Align all 11 dependency mismatches in `requirements.txt` to TECHNOLOGY_STACK.md (bump versions, remove forbidden packages, add missing packages).
3. Fix `config.py`: change `DEFAULT_COUNTRY` to `US`, change money fields to `Decimal`.
4. Bump all 6 frontend packages to canonical versions; fix `/hr/*` rewrite; merge duplicate `logistics-partner`/`logistics-partners`.
5. Fix dev Dockerfile to `python:3.13-slim`; fix compose to `postgres:16-alpine`; add Gunicorn dev CMD.
6. Replace root `npm run` scripts with pnpm equivalents.

### Corrections Required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Delete `modules/finance/`, `domains/payments/`, `hr.py`; demote `domains/media/` | Law 12, 13 | yes | L (16h) | 5 |
| P0 | Bump FastAPI to 0.141.x | CONTRAD-005 | yes | M (2h) | 5 |
| P0 | Replace slowapi/limits→fastapi-limiter-valkey in requirements | CONTRAD-016, CONTRAD-036 | yes | M (2h) | 5 |
| P0 | Fix float-for-money in config.py | Law 19 | yes | S | 5 |
| P0 | Upgrade Zod 3→4 | CONTRAD-024 | yes | M (2h) | 5 |
| P0 | Fix /hr standalone rewrite | CONTRAD-029 | yes | S (1h) | 5 |
| P1 | 6 remaining dep version fixes (Alembic, pydantic-settings, prometheus, sentry, stripe, SQLAlchemy) | CONTRAD-007–011, 035 | partial | S | 5 |
| P1 | Remove 3 forbidden packages (python-magic, psycopg2-binary, requests) + 2 forbidden (pytz, tzlocal) | CONTRAD-012–015 | no | S | 5 |
| P1 | Add pybreaker, uvloop, httptools to requirements | CONTRAD-017, 018 | partial | S | 5 |
| P1 | Fix DEFAULT_COUNTRY to US | CONTRAD-019 | partial | S | 5 |
| P1 | Bump 4 frontend packages (Next.js, framer-motion, Zustand, Expo, RN, React) | CONTRAD-021–023, 026–028 | partial | M | 5 |
| P1 | Pin @hookform/resolvers to 5.2.2 | CONTRAD-025 | partial | S | 5 |
| P1 | Fix root package.json npm→pnpm | CONTRAD-032 | partial | S | 5 |
| P2 | Merge duplicate logistics-partner directories | CONTRAD-033 | no | S | 5 |
| P2 | Fix Dockerfile Python 3.11→3.13 | CONTRAD-030 | no | S | 5 |
| P2 | Fix compose Postgres 18→16 | CONTRAD-031 | no | S | 5 |
| P2 | Add Gunicorn dev CMD | CONTRAD-037 | no | S | 5 |
| P2 | Document or remove 5 extra providers | CONTRAD-004 | no | S | 5 |
| P3 | Resolve domains/media/ — promote or demote | CONTRAD-003 | no | L (4h) | 5 |
