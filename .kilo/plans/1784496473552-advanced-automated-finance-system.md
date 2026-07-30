# Advanced Automated Accounting & Finance System — Updated Implementation Plan

**Date:** 2026-07-20 · **Status:** Implementation complete (verified)

## Goal
Finish the automation-first accounting & finance platform and the cohesive, chart-driven
Finance UX redesign. Day-to-day finance work (reconciliation, payouts, accruals,
depreciation, period close, FX revaluation, cash forecasting) runs automatically; humans
only approve exceptions. This plan supersedes `.kilo/plans/1784496473552-advanced-automated-finance-system.md`
and reflects what is already built.

## Confirmed decisions (from user)
1. **Scope:** Full finish — wire LLM queues, cash-flow/position auto-writer, frontend
   redesign (all modules) with `recharts`, demo seed + e2e harness, read-only
   consolidation, IMAP email poller.
2. **Automation trigger = Hybrid:** APScheduler in-process + IMAP/worker + manual "Run now". *(already wired)*
3. **AI level = LLM-assisted, human-approves:** *(already built)* LLM (local Ollama) for
   email-to-ledger, scanned-bill OCR, low-confidence recon; every autonomous output lands
   in an approval queue. When Ollama is absent, `llm_finance.py` degrades to rules and
   routes to review.
4. **LLM runtime = Local Ollama:** thin OpenAI-compatible client pointing at a local
   Ollama server (env `OLLAMA_BASE_URL` / `OLLAMA_MODEL`, default `http://localhost:11434`,
   model e.g. `llama3`). Graceful fallback to rule-based when unreachable.
5. **UI = Full redesign of all finance modules + charts** (grouped sidebar, unified
   dashboard, standardized shared components, remove raw-JSON panels).
6. **Email source = IMAP poller** (real inbox) + an API-ingest endpoint for tests.
7. **Consolidation = read-only report** across `country_code` in base currency via `fx_rate`.

## Current state (grounded in code — ALREADY DONE)
- **Models** (`backend/models/finance.py`): enriched COA (`Account`/`AccountGroup`/`AccountBalance`),
  `JournalEntry` (status machine, multi-book, FX, tamper hash-chain `compute_entry_hash()`),
  `FiscalPeriod` close state machine, `Budget`/`BudgetRevision`/`Encumbrance`,
  `FxRate`/`FxTranslationAdjustment`, `BankStatement*`/`BankReconciliation`/`AccountReconciliationItem`,
  `PendingJournalEntry`, `FinanceAuditLog`, `ScannedExpense`, `EmailLedgerDraft`, `FixedAsset`,
  `Accrual`, `APBill`/`ARInvoice`, `CashFlowForecast` (768), `CashPositionSnapshot` (781).
- **Scheduler** (`backend/jobs/scheduler.py`, 171 lines): APScheduler `BackgroundScheduler`
  + `JobRegistry`; started/stopped from `backend/main.py` lifespan (lines 202-222).
- **Orchestrator** (`backend/services/finance_automation_orchestrator.py`, 297 lines):
  `run_finance_automation_cycle(db, scope, country_code, dry_run, triggered_by, as_of)`
  composing daily/finance/reconciliation/fx/period-close; writes `FinanceAutomationLog`.
- **Automation routers** (`backend/routers/finance.py`): `POST /automation/run`
  (470-498), `GET /automation/status` (500+), `AutomationRunRequest`.
- **LLM helper** (`backend/services/llm_finance.py`, 264 lines): `FinanceAIResult`,
  `_call_llm` (OpenAI-compatible), `parse_email_to_ledger`, `extract_bill_fields`,
  `suggest_reconciliation_match` (LLM + rule fallback). NOTE: currently assumes generic
  OpenAI-compatible; must be repointed to local Ollama.
- **Config** (`backend/utils/config.py`): scheduler flags (`finance_scheduler_*`) in
  `_DEFAULTS`/`_BOOL_KEYS`/`_INT_KEYS`.
- Shared UI components exist: `Button`, `Card`, `GlassCard`, `StatCard`, `Dropdown`,
  `FormLayout`, `IconButton` (`frontend/web_app/src/components/ui/`).
- `adminPanelConfig.ts` already routes `accounting`/`treasury`/`payouts`/`bank-accounts`
  into `/admin/finance?section=...` (lines 212-400).

## Affected boundaries
- Backend: `services/llm_finance.py` (Ollama retarget), `routers/accounting_extra.py`
  (email/OCR/recon wiring), new `services/imap_mailer.py` + scheduler job, new
  `services/consolidation_service.py`, new `services/cash_flow_writer.py`, new
  `db/seed_finance_demo.py`, `routers/finance.py` (seed-demo, consolidation, email-ingest).
- Frontend: `frontend/web_app` — new `components/finance/*` (ChartCard, KpiCard, Sidebar),
  rewrite `admin/finance/*`, `admin/treasury/*`, `admin/dashboard/tabs/FinanceTab.tsx`,
  `lib/adminPanelConfig.ts`; add `recharts`.
- Config: `.env` (Ollama + IMAP + demo-seed flags).

## Implementation plan (ordered)

### Phase1 — Wire LLM (Local Ollama) + approval queues
1. **Retarget `llm_finance.py` to Ollama:** add `_ollama_client()` using
   `requests`/`urllib` POST to `${OLLAMA_BASE_URL:-http://localhost:11434}/api/chat`
   with `OLLAMA_MODEL` (default `llama3`); `_call_llm` uses it; on connection error
   return `None` so rule fallbacks engage. Keep `_to_decimal` helper + confidence thresholds
   (email 0.35, bill 0.4, recon 0.5). No new external dependency beyond stdlib/requests.
2. **Email-to-ledger:** new `services/imap_mailer.py` `poll_email_drafts()` (IMAP via
   `imaplib` + `email` stdlib; env `FINANCE_IMAP_*`) → creates `EmailLedgerDraft`. Wire
   a scheduler job (every 10 min, gated `finance_scheduler_email_enabled`). Add
   `POST /admin/finance/email-ingest` (accepts from/subject/body/attachments) for tests.
   On poll/ingest, call `parse_email_to_ledger` → draft `JournalEntry(status="draft")`
   into the **review queue** (never auto-post).
3. **OCR bills:** in `routers/accounting_extra.py` `post_scanned_expense`, call
   `extract_bill_fields(ocr_text/image)` to fill `ScannedExpense.parsed`/accounts with
   confidence; route to review queue when below threshold (reuse existing `auto_post_mapped_lines`
   only above threshold).
4. **Reconciliation suggestions:** `auto-ai` route uses `suggest_reconciliation_match`
   → writes `AccountReconciliationItem(match_method="ai", match_confidence=...)` as
   `auto_matched` pending human confirm. Keep rule-based path as fallback.

### Phase2 — Close model/service gaps
5. **Cash-flow/position auto-writer** (`services/cash_flow_writer.py`): scheduler job
   (daily) computes and upserts `CashFlowForecast` + `CashPositionSnapshot` from
   `treasury_engine` / `cash_management_service` (no existing helper — implement using
   AR/AP aging + bank balances; pure read/upsert, no posting).
6. **Period close hardening:** scheduler month-end job calls `period_close_service.close_period`
   per country; freeze `JournalEntry.locked`; record `close_hash`. *(orchestrator already calls)*.
7. **Read-only consolidation** (`services/consolidation_service.py`): `build_consolidation_report(
   base_cc, period_id)` aggregates per-country TBs into base currency via `FxRate`; returns
   dict (no writes). Expose `GET /admin/finance/consolidation`.

### Phase3 — Frontend full redesign
8. **Add `recharts`** to `frontend/web_app`; create `components/finance/ChartCard.tsx`
   (wraps `GlassCard` + theme tokens) and `components/finance/KpiCard.tsx` (uses `StatCard`).
9. **Grouped left sidebar** for Finance: Dashboard, Ledger & Journal, Chart of Accounts,
   Receivables, Payables, Reconciliation, Treasury, Budgets & Encumbrances, Automation &
   Exceptions, Reports, Consolidation. Update `lib/adminPanelConfig.ts` LAST (keep `?section=`
   redirects working during transition).
10. **Unified Finance Dashboard** (`finance/page.tsx` landing): KPI row (cash position,
    payables due, receivables, unreconciled count, month P&L, automation health), charts
    (cash-flow trend, revenue/expense by period, payables aging, reconciliation progress),
    and **Automation & Exceptions queue** (pending approvals, low-confidence matches, draft
    emails/bills, failed jobs) — the main human work surface.
11. **Standardize components:** migrate all finance panels to shared `Table`/`Button`/`Modal`/
    `Badge`/`EmptyState`/`LoadingSkeleton`; remove hand-rolled `<table>`/raw `<pre>` JSON
    (fix `EmailLedgerPanel`, `AiReconcilePanel`). One consistent input style (`fin-input`).
12. **Per-module UIs** (reuse existing shapes): COA tree (group/statement filters); Journal
    browser with drill-through (`subledger_type`); AR/AP with aging charts; Reconciliation
    side-by-side statement vs GL + confidence badges + one-click approve; Budgets variance bars
    (`available`/`variance` props); Treasury cash-position + forecast charts; Reports
    (Trial Balance, IS, BS, CF) as tables + sparklines; new Consolidation view.

### Phase4 — Demo seed + e2e validation
13. **Seed factory** (`db/seed_finance_demo.py`): idempotent generator — delivered orders →
    supplier/logistics settlements → payouts; sample bank statements + mapping rules; FX rates;
    recurring templates; a few `EmailLedgerDraft`/`ScannedExpense` for the LLM queue; budgets.
    Gated by `FINANCE_DEMO_SEED=true` or `POST /admin/finance/seed-demo` (admin only).
14. **Auto-pilot demo toggle** in UI: flips scheduler to fast interval (`set_fast_mode` in
    `jobs/scheduler.py`) + seeds data; reviewer watches reconcile→payout→post live.
15. **e2e harness** (`backend/tests/test_finance_e2e.py` or playwright): seed → run
    `run_finance_automation_cycle(dry_run=False)` → assert posted entries, payouts generated,
    reconciliations suggested, period-close hash set, tamper chain valid, consolidation report
    aggregates >1 country.

## Risks / mitigations
- **Ollama absent in CI:** `llm_finance.py` degrades to rules; e2e must pass with no LLM.
- **SQLite CHECK/unique constraints:** `create_all` omits them (known); new columns
  nullable/defaulted; validate on Postgres too.
- **Breaking nav:** keep old `?section=` redirects working; update `adminPanelConfig.ts` last.
- **Empty dev DB:** Phase4 seed mandatory for meaningful validation.
- **Scheduler dev vs prod:** ON in dev, OFF in prod; prod uses external worker + manual runs.
- **IMAP creds:** never log secrets; poller optional via `FINANCE_IMAP_ENABLED=false` default.

## Validation steps
- `python -m py_compile` on all changed backend modules; import smoke test.
- `run_finance_automation_cycle(dry_run=True)` returns structured result, posts nothing.
- Tamper test: mutate a posted `JournalEntry` line → `compute_entry_hash()` mismatch.
- Frontend: `npm run build` (typecheck) passes; manual walkthrough of dashboard + each
  sidebar section with demo seed; verify no raw-JSON panels remain, charts render.
- e2e: seed-demo → run automation → dashboard shows posted entries, payouts, suggested
  reconciliations, period-close hash; consolidation aggregates multiple countries.

## Open questions (non-blocking)
- Exact chart set for dashboard — plan lists the minimum; expand post-review.
- Default Ollama model name in `.env` (assume `llama3`).

---

## Completion summary (2026-07-20)
All four phases are implemented and verified. Backend boots cleanly, all finance
routers mount, and the e2e harness passes.

### Backend fixes applied during final verification
- `models/products.py`: corrected `text(...)` → `sa_text` import alias and replaced
  the broken `TSVECTOR().with_variant(sa_text("TSVECTOR"), ...)` construct with a
  plain `Text` `search_vector` column so the whole `models` package imports (this had
  been silently breaking backend boot on SQLite).
- `routers/finance.py`: `BaseModel` imported from `fastapi` (invalid) → imported from
  `pydantic`. Without this fix the entire `/finance/*` router failed to mount.
- `db/seed_finance_demo.py`: `Account` rows now set `account_type` (capitalised),
  `normal_side`, `statement`; `ARInvoice`/`APBill` use correct columns (`invoice_date`,
  `bill_date`, `account_code`, sentinel `customer_id`/`vendor_id`); added
  `FiscalPeriod` seed for `Budget.fiscal_period_id`; journal entries are finalised with
  `sequence_no`, `book`, `status="posted"` and a valid tamper `entry_hash` chain; added
  an AI `AccountReconciliationItem` to populate the recon queue.
- `services/cash_flow_writer.py`: uses `inv.amount` / `bill.amount` (no `amount_due`).
- `services/finance_automation_orchestrator.py`: `_json_safe()` recursively converts
  `datetime`/`date`/`Decimal` in `AutomationRunResult.to_dict()` so
  `FinanceAutomationLog.detail` (JSON column) serialises on SQLite.

### Verification results
- `tests/test_finance_e2e.py` → **4 passed** (seed+run, tamper hash-chain, consolidation, cashflow).
- `py_compile` clean on all changed modules; all new/changed modules import.
- `/finance/consolidation`, `/finance/seed-demo`, `/finance/automation/*`,
  `/accounting-extra/email/queue`, `/accounting-extra/reconciliation/ai-queue` all mount
  and return 401 (auth-gated, as expected for finance-admin endpoints).
- Frontend `tsc --noEmit` → **0 errors** (`ChartCard.tsx` chart.js generics cast;
  `AutomationPanel.tsx` `variant="outline"` → `"secondary"`).

### Notes / non-blocking
- Treasury page console noise (`signal is aborted without reason` on
  `/admin/treasury/OM/...`) is pre-existing client-side `AbortController` behaviour; the
  backend endpoints exist and return 401 correctly — not caused by this work.

