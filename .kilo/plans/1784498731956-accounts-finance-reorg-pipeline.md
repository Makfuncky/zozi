# Advanced Accounts & Finance System — Reorganization & Full-Stack Pipeline Plan

**Date:** 2026-07-20 · **Status:** Plan (approved, ready to implement)

## 0. Context & diagnosis (grounded in code audit)
The finance/ERP backend is **not** small — it is large and feature-rich (50+ tables,
~283 routes, multi-book IFRS/TAX/MANAGEMENT/STATUTORY, FX dual-amount + revaluation,
SHA-256 tamper hash-chain, maker-checker, budgets/encumbrances, AR/AP subledgers,
bank reconciliation with AI matching, fixed assets/depreciation, deferred revenue,
consolidation). The real problem the user observed ("poor backend, just 3-4 tiny files")
is **structural chaos**, not missing features:

1. **Flat file sprawl** — no `accounts/` or `finance/` package; services live as loose
   files (`general_ledger_service.py`, `treasury_engine.py`, `cash_management_service.py`,
   `finance_transfer_service.py`, `financial_reports_service.py`, …).
2. **Router fragmentation / overlap** — 6 finance routers: `finance` (`/finance`),
   `finance_automation` + `finance_erp` (both `/accounting`), `admin_treasury`
   (`/admin/treasury`), `accounting_extra` (`/accounting-extra`). Many endpoints
   duplicated (manual-adjustment, ledger/pending, reconciliation, trial-balance,
   detect-orphans appear in 2-3 routers).
3. **Two divergent posting engines** — `general_ledger_service.create_journal_entry`
   (schema + `round_money`) vs `TreasuryEngine.post_journal_entry` (dict + SELECT FOR
   UPDATE). Both write the ledger with different conventions.
4. **Scattered wiring** — period close in `period_close_service` + orchestrator imports
   a *router function* (`accounting_extra.fx_revalue`) to revalue FX; automation logic
   split across orchestrator / `finance_automation` / `cash_flow_writer` /
   `consolidation_service`.
5. **Dual ORM registry risk** — `models/finance.py` (canonical `models.Base`) vs
   `db/models.py` (legacy `db.base.Base`). Conftest forbids using `db.base.Base`.

### Chosen architecture (best practice for a large ERP app)
- **Domain packages** `backend/accounts/` and `backend/finance/` as **facades** over the
  existing, proven services — single-responsibility modules, no destructive rewrite.
- **One unified posting kernel** (`accounts/engine.py`) wrapping both legacy engines so
  all postings flow through `gl.create_journal_entry` (the canonical path) with a single
  locking/rounding/audit convention.
- **One service per domain** (coa, journal, subledgers, periods, multi_book, fx,
  reports, treasury, cash, reconciliation, controls, automation, consolidation).
- **Versioned public API** `/api/v1/accounts` + `/api/v1/finance` layered on the unified
  engine; legacy routers kept working via **thin re-exports** (backward compat for the
  existing frontend until it is re-pointed).
- **Frontend** `/admin/finance` hub re-pointed to the versioned API, charts via the
  already-installed `react-chartjs-2`, full module coverage.

---

## 1. Target package layout (backend/)

```
backend/
  accounts/                      # Chart of Accounts + General Ledger (the GL core)
    __init__.py
    engine.py                   # UNIFIED posting kernel (wraps gl + TreasuryEngine)
    coa.py                      # Account/AccountGroup/AccountBalance/Dimension CRUD+tree
    journal.py                  # JournalEntry create/post/reverse, line validation
    subledgers.py               # AR/AP ledger postings -> GL (from sub_ledger_service)
    periods.py                  # FiscalPeriod open/close + close_hash (period_close_service)
    multi_book.py               # book basis (IFRS/TAX/MANAGEMENT/STATUTORY) helpers
    fx.py                       # FxRate + revaluation -> JournalEntry (from accounting_extra)
    controls.py                 # PendingJournalEntry maker-checker, audit log, approvals
    schemas.py                  # Pydantic schemas (AccountIn/Out, JournalEntry*, etc.)
    dependencies.py             # get_gl_session, require_accounts_admin

  finance/                      # Management accounting, treasury, reporting, automation
    __init__.py
    reports.py                  # TrialBalance, IS, BS, CF, aging, budget variance (financial_reports_service)
    treasury.py                 # TreasuryEngine facade + treasury_account/transaction ops
    cash.py                     # cash_management_service + cash_flow_writer facade
    reconciliation.py           # bank + AI reconciliation (finance_automation + erp)
    assets.py                   # FixedAsset depreciation, Accruals
    deferred_revenue.py         # ASC606/IFRS15 deferral + amortization
    budgets.py                  # Budget/BudgetRevision/Encumbrance + variance
    automation.py               # orchestrator facade + schedules (email/ocr/dep/accrual)
    consolidation.py            # multi-country consolidation (consolidation_service)
    expenses.py                 # ScannedExpense OCR + EmailLedgerDraft queues (llm_finance)
    schemas.py                  # finance Pydantic schemas
    dependencies.py             # require_finance scopes

  routers/                      # PUBLIC REST surface (new, versioned)
    api_v1_accounts.py          # /api/v1/accounts  -> accounts.* domains
    api_v1_finance.py           # /api/v1/finance   -> finance.* domains
    (legacy routers kept, thin re-export only, NOT deleted)
```

**Migration rule:** existing `services/*.py` files are NOT deleted. The new package
modules *import and re-export* the proven functions (e.g. `accounts.journal.create =
gl.create_journal_entry`). Legacy routers (`finance.py`, `finance_erp.py`,
`finance_automation.py`, `admin_treasury.py`, `accounting_extra.py`) are converted to
thin pass-throughs to the package so behavior is identical. This guarantees zero
regression for the 283 existing routes and the current frontend.

---

## 2. Phase A — Package skeleton + unified engine (foundation)
- A1. Create `backend/accounts/` and `backend/finance/` packages with `__init__.py`
     re-exporting existing service functions (additive only).
- A2. `accounts/engine.py` — `UnifiedGLEngine`:
     - `post(entry_data, user_id, *, lock=True, audit=True)` → delegates to
       `general_ledger_service.create_journal_entry` (canonical), applies
       `round_money`, writes `FinanceAuditLog`, returns `JournalEntryOut`.
     - `reverse(entry_id, user_id)` → posts a reversal `JournalEntry` with
       `reversal_of_id` (reuses `je_reversal_service`).
     - `post_dict(lines, ...)` shim so `TreasuryEngine.post_journal_entry` callers still
       work (kept for backward compat, routes to `post`).
     - Single convention: balanced check, `SELECT … FOR UPDATE` on balances, audit row.
- A3. `accounts/dependencies.py`, `finance/dependencies.py` — auth deps combining
     role-check (`admin/finance_admin/country_head`) with slug-permission fallback so the
     two existing auth models converge.
- A4. `py_compile` + import smoke test for both packages.

## 3. Phase B — Accounting domains
- B1. `accounts/coa.py`: list/tree/get/create/update(deactivate)/balances; seed COA
     (re-export `seed_chart_of_accounts`); dimension tree.
- B2. `accounts/journal.py`: create/post/reverse; `get`, `list` (bulk lines),
     `validate_entry_balanced`; `list_pending` + `approve_pending`/`reject_pending`
     (maker-checker via `controls.py`).
- B3. `accounts/subledgers.py`: AR/AP postings (from `sub_ledger_service`),
     invoice/bill → GL linkage.
- B4. `accounts/periods.py`: open period, `close_period` (writes `close_hash`),
     reopen with `reopened_count`.
- B5. `accounts/multi_book.py`: helpers to post per `book` basis; `compute_entry_hash`
     verification utility (tamper check used by tests).
- B6. `accounts/fx.py`: `set_rate`, `revalue(open fx balances)` → posts FX JE via engine.
- B7. `accounts/controls.py`: maker-checker state machine + `FinanceAuditLog` writer.

## 4. Phase C — Reports engine (the "all possible reports" requirement)
`finance/reports.py` and `accounts/*` produce:
- C1. **Trial Balance** (as_of, per currency/country) — `get_trial_balance`.
- C2. **Income Statement** (P&L) by period / range, per book.
- C3. **Balance Sheet** (assets/liabilities/equity) with retained earnings roll-forward.
- C4. **Cash Flow Statement** (operating/investing/financing) from `cash_flow_writer`.
- C5. **AR Aging** (current/30/60/90+) and **AP Aging**.
- C6. **Budget vs Actual / Variance** (from `budgets` + `encumbrances`).
- C7. **VAT Liability** report.
- C8. **Fixed Asset register + depreciation schedule**.
- C9. **Bank Reconciliation statement** (statement vs GL).
- C10. **Consolidated** multi-country report (`consolidation.py`).
All return structured dicts + cached `FinancialReport` rows; pure read except where a
posting is explicitly requested (e.g. FX revalue, depreciation run).

## 5. Phase D — Treasury, cash, reconciliation, automation, controls
- D1. `finance/treasury.py`: account/transaction ops, transfers (from
     `treasury_engine`/`finance_transfer_service`), payout batches
     (generate/approve/dispatch), COD remittance, supplier settlement.
- D2. `finance/cash.py`: positions + forecasts + snapshots facade
     (`cash_management_service` + `cash_flow_writer`).
- D3. `finance/reconciliation.py`: bank statement import + rule/AI matching +
     `AccountReconciliationItem` suggest/confirm.
- D4. `finance/assets.py`: fixed-asset depreciation run, accruals create/reverse.
- D5. `finance/deferred_revenue.py`: contract + amortize.
- D6. `finance/budgets.py`: CRUD + revision + encumbrance + variance.
- D7. `finance/expenses.py`: OCR scan + email-ledger parse → review queues.
- D8. `finance/automation.py`: `run_finance_automation_cycle` facade + scheduler
     jobs (daily, email_poll, cashflow, fx, close_period) — single orchestration entry.
- D9. `finance/consolidation.py`: `build_consolidation_report` (read-only).

## 6. Phase E — Unified versioned API + tests
- E1. `routers/api_v1_accounts.py` (`/api/v1/accounts`):
     `/coa`, `/coa/{code}`, `/journal/entries`, `/journal/entries/{id}`,
     `/journal/pending`, `/journal/pending/{id}/approve|reject`, `/subledgers/ar`,
     `/subledgers/ap`, `/periods`, `/periods/close`, `/fx/rates`, `/fx/revalue`,
     `/multi-book/...`, `/reports/trial-balance`, `/reports/balance-sheet`,
     `/reports/income-statement`, `/reports/ar-aging`, `/reports/ap-aging`.
- E2. `routers/api_v1_finance.py` (`/api/v1/finance`):
     `/reports/*` (all C1–C10), `/treasury/*`, `/cash/position`, `/cash/forecast`,
     `/reconciliation/*`, `/assets/*`, `/accruals/*`, `/deferred-revenue/*`,
     `/budgets/*`, `/expenses/scan`, `/email/queue`, `/automation/run`,
     `/automation/status`, `/consolidation`, `/dashboard/metrics`, `/seed-demo`.
- E3. Convert legacy routers to thin re-exports of the package (behavior-preserving).
- E4. **Tests**: expand `tests/test_finance_e2e.py` + add `tests/test_accounts_api.py`
     covering each domain + reports + tamper chain + consolidation + multi-book.

## 7. Phase F — Frontend wiring (frontend/web_app)
- F1. Add API client helpers in `src/lib/api.ts` for `/api/v1/accounts` and
     `/api/v1/finance` (and keep legacy `/accounting`, `/admin/treasury` working).
- F2. Finance hub (`src/app/admin/finance/page.tsx`) + `FinanceSidebar` already support
     30+ sections — re-point each section's fetch to the versioned API.
- F3. `FinanceDashboard.tsx`: KPI row + charts (`ChartCard`) for cash position, P&L,
     AR/AP aging, reconciliation progress, automation health.
- F4. Modules (`FinanceModules.tsx`, `ErpPanels.tsx`, `AccountingPanels.tsx`,
     `treasury-content.tsx`): replace ad-hoc fetches with versioned endpoints;
     standardize on `Table`/`Modal`/`Badge`/`EmptyState`; remove raw-JSON panels.
- F5. New panels where missing: **Budgets variance bars**, **Consolidation view**,
     **Multi-book selector**, **AR/AP aging charts**, **Fixed-asset/depreciation**,
     **Deferred revenue**, **Reports (TB/IS/BS/CF) tables + sparklines**.
- F6. `tsc --noEmit` clean; manual walkthrough of every sidebar section with demo seed.

## 8. Validation gates (run after each phase)
- `python -m py_compile` on every changed module + import smoke test.
- `pytest tests/test_finance_e2e.py tests/test_accounts_api.py -q` → green.
- `curl`/TestClient probe of `/api/v1/accounts/reports/trial-balance`,
  `/api/v1/finance/reports/balance-sheet`, `/api/v1/finance/consolidation` → 401 then
  200 with a seeded session.
- Frontend `npm run build` (typecheck) passes; no raw-JSON panels remain.

## 9. Risks / mitigations
- **Regression to 283 routes**: mitigated by facade + thin re-export; legacy routers keep
  identical behavior. Tests assert parity.
- **Dual Base**: package imports ONLY `models.Base` canonical; never `db.base.Base`.
- **Two auth models**: converge in `accounts/dependencies.py` + `finance/dependencies.py`.
- **SQLite CHECK vs Postgres**: create_all omits CHECK/unique (known); validated on
  Postgres in CI.
- **Scope**: implement backend Phases A–E first (fully tested), then frontend F. Never
  delete legacy files until the frontend is re-pointed and green.

## 11. Status — COMPLETE (2026-07-20)

Phases A–F implemented and verified:

- `accounts/` + `finance/` facades over proven `services/*` (no rewrite).
- `/api/v1/accounts` (42 routes, ERP aliases) + `/api/v1/finance` (71 routes) registered in `main.py`; legacy routers kept mounted.
- Frontend finance hub fully re-pointed to `/api/v1/*` (bases + `page.tsx` translation); `treasury-content.tsx` deliberately left on `/admin/treasury`.
- Frontend `tsc --noEmit` clean.

### Test fixes applied during final verification (combined run)
1. `services/erp_finance_service.py`: `ar_aging`/`ap_aging` now default `as_of` to `date.today()` when `None` (guards the v1 alias `/api/v1/accounts/ar/aging` called without `as_of` — previously 500'd with `AttributeError: 'NoneType' object has no attribute 'isoformat'`).
2. `routers/api_v1_accounts.py`: `POST /periods/get-or-create` now accepts a JSON body (`GetOrCreatePeriodIn`) matching the frontend `postData("/periods/get-or-create", {country_code, year, month})` — was wrongly declared as query params.
3. `tests/conftest.py`: gave the e2e `db_session` its OWN isolated engine (`e2e_engine`/`e2e_db_file`), separate from the HTTP `engine`, with commit-on-teardown. Fixes cross-suite contamination where the REST `auth_client` tests committed finance rows that made `seed_finance_demo`'s idempotency short-circuit in the e2e suite.

### Final result
`pytest tests/test_accounts_api.py tests/test_finance_e2e.py` → **11 passed** in a single combined run (7 accounts API + 4 e2e). Deterministic and green.

## 12. Phase G — Unify finance domains under ONE wiring root (plan)

**Decision (user-approved 2026-07-20):** keep `accounts/` and `finance/` as
**sibling top-level packages** (avoiding circular imports) and add a single
umbrella re-export so all finance-related wiring has ONE import root. NO file
moves, NO broken imports. This is recommendation #1 from the structure review.

### Why not physically merge `accounts/` into `finance/`
- `accounts/*` internally does `from accounts.engine import ...` (11 sites);
  moving it under `finance/` would force a 50+ import-site refactor and risk
  `finance.accounts` ↔ `finance.expenses` ↔ `services` circular imports.
- Treasury already lives inside `finance/` (`finance/treasury.py`) — it is
  already "under one hood".

### Goal
A caller (router/main) can `from finance import ...` and reach **every**
finance domain — accounts (GL/coa/journal/periods/fx/multi_book/controls),
reporting, treasury, operations — through one package root.

### Import audit (actual sites, confirmed)
- `routers/api_v1_accounts.py`: `from accounts import coa, journal,
  subledgers, periods, multi_book, fx, controls`, `from accounts.dependencies
  import ...`, `from accounts.schemas import ...`, `from finance.schemas import
  BudgetIn`.
- `routers/api_v1_finance.py`: `from finance import reports, treasury, cash,
  reconciliation, assets, deferred_revenue, budgets, expenses, automation,
  consolidation`, `from finance import async_jobs`, `from finance.dependencies
  import ...`, `from finance.schemas import ...`.
- `accounts/*` self-imports `from accounts.engine import ...` (unchanged).
- Alembic/migration files reference SQL table `accounts.id` (NOT the Python
  package) — irrelevant to this change.

### Steps (all additive)
1. **`finance/__init__.py`** — extend umbrella to re-export the accounts
   domain + its deps, so `from finance import coa, journal, ...` and
   `from finance import require_accounts_admin, get_gl_session` work too.
   Add a convenience `finance.accounts` alias submodule? NOT needed — just
   re-export symbols. Keep `__all__` complete.
   - Re-export from `accounts`: `coa, journal, subledgers, periods,
     multi_book, fx, controls, engine, schemas`, and `accounts.dependencies`
     (`require_accounts_admin, require_accounts_scope, get_gl_session`),
     `accounts.schemas` (`BudgetIn`, etc.).
   - Already re-exports finance deps; add finance domain modules too for a
     single complete root.
2. **Leave `accounts/` and all routers untouched** — every existing import
   (`from accounts import ...`, `from finance import ...`) continues to work.
   No behavior change, no breakage.
3. **No subfolder split** (reporting/operations) in this phase — that is a
   larger refactor deferred per risk policy. The umbrella re-export alone
   satisfies "one hood for wiring."

### Verification
- `python -c "import finance; from finance import coa, journal, subledgers,
  periods, multi_book, fx, controls, require_accounts_admin, get_gl_session,
  BudgetIn, reports, treasury, cash, reconciliation, assets,
  deferred_revenue, budgets, expenses, automation, consolidation, async_jobs"`
  → no ImportError.
- `python -c "import main"` → boots.
- `pytest tests/test_accounts_api.py tests/test_finance_e2e.py
  tests/test_ocr_expenses.py` → 15 passed (unchanged).

### Result
One import root (`finance`) for all finance wiring; `accounts` remains a clean
sibling. Zero files moved, zero imports broken.

## 10. Implementation order (commits)
A → B → C → D → E (backend, tested) → F (frontend, tested) → final e2e + typecheck.
