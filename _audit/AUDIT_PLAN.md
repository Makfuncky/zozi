# ZOZI CODEBASE FORENSIC AUDIT — PLAN

Source of truth for the phases: `CODEBASE_AUDIT_BY_ASHER.md`
Governing rules: `_audit/MASTER_RULES.md`

## Orchestration model

- Each phase is executed by a dedicated **forensic subagent** with narrow scope.
- Subagents are **read-only** on the codebase; they only write their own report
  under `_audit/findings/` and return a structured **AGENT LOG** block.
- The orchestrator aggregates every AGENT LOG into `_audit/_logs/AUDIT_LOG.md`
  and `_audit/_logs/agent-tracking.json` after each wave (skeptical review).

## Verified stack context (grounding, still must be re-verified per phase)

- Backend: Python / FastAPI (`backend/main.py`), Celery workers, Alembic.
- DDD layout: `backend/domains/{accounts,analytics,audit,catalog,comms,country,
  customers,finance,governance,hr,logistics,orders,payments,promotions,security,
  suppliers}`, role APIs in `backend/modules/{admin,customer,employee,logistics,supplier}`,
  primitives in `backend/kernel/`, cross-cutting in `infrastructure/`, `providers/`, `rbac/`, `middleware/`, `jobs/`.
- Data: PostgreSQL 18, Valkey cache (docker-compose.yml).
- Frontend: Next.js `frontend/web_app` (TS, Playwright + Jest), `mobile_app`, `shared`.
- Infra: Docker Compose, Caddy, nginx, Railway, Vercel, Neon.

## Phase → report file → wave

| Phase | Task | Report file | Wave |
|------|------|-------------|------|
| 01 | Repository Inventory | findings/PHASE_01_REPOSITORY_INVENTORY.md | 1 |
| 02 | Technology / Framework / Library Inventory | findings/PHASE_02_TECHNOLOGY_STACK.md | 1 |
| 03 | Dependency Forensic Audit | findings/PHASE_03_DEPENDENCY_FORENSICS.md | 1 |
| 04 | Import / Module Dependency Map | findings/PHASE_04_IMPORT_MAP.md | 1 |
| 05 | Application Code Surface Map | findings/PHASE_05_CODE_SURFACE_MAP.md | 1 |
| 06 | E-commerce Business Domain Map | findings/PHASE_06_BUSINESS_DOMAIN_MAP.md | 1 |
| 07 | Database Forensic Audit | findings/PHASE_07_DATABASE_FORENSICS.md | 1 |
| 08 | API Forensic Audit | findings/PHASE_08_API_FORENSICS.md | 1 |
| 09 | Authentication / Authorization Security | findings/PHASE_09_AUTH_SECURITY.md | 1 |
| 10 | Payment System Forensic & Security | findings/PHASE_10_PAYMENT_SECURITY.md | 1 |
| 11 | Application Security Audit | findings/PHASE_11_APPLICATION_SECURITY.md | 2 |
| 12 | Performance / Computation Audit | findings/PHASE_12_PERFORMANCE.md | 2 |
| 13 | Dead Code / Unused Code Audit | findings/PHASE_13_DEAD_CODE.md | 2 |
| 14 | Bug / Contradiction / Inconsistency Audit | findings/PHASE_14_BUGS_CONTRADICTIONS.md | 2 |
| 15 | Testing Forensic Audit | findings/PHASE_15_TESTING.md | 2 |
| 16 | Deployment / Infrastructure Audit | findings/PHASE_16_INFRASTRUCTURE.md | 2 |
| 17 | Production Readiness Assessment (synthesis) | findings/PHASE_17_PRODUCTION_READINESS.md | 3 |
| 18 | Target Technology Evaluation (forward-looking) | findings/PHASE_18_TARGET_TECHNOLOGY.md | 3 |

- **Wave 1** — Phases 1–10 dispatched in parallel (independent forensic audits).
- **Wave 2** — Phases 11–16 dispatched in parallel (independent forensic audits).
- **Wave 3** — Phases 17–18 (synthesis; read Wave 1–2 reports as evidence).

## Deliverables

- 18 per-phase forensic reports under `_audit/findings/`.
- Chronological log: `_audit/_logs/AUDIT_LOG.md`.
- Machine-readable tracking: `_audit/_logs/agent-tracking.json`.
- Final: `_audit/EXECUTIVE_SUMMARY.md`.
