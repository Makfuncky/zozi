# Plan: Make Zozi Finance / Treasury / Cash Management Automated & Usable

**Date:** 2026-07-20 · **Scope:** Account, Finance, Treasury, Payment, Cash Management (backend + admin frontend)
**Mode:** Planning only — no source edits here. Hand to an implementation-capable agent.

---

## 0. Context & Reality Check (verified, not assumed)

The codebase **already contains** a large finance/treasury surface (per `documents/` and live code):
- Double-entry engine `services/treasury_engine.py` + `services/general_ledger_service.py` (Golden Rule enforced, row locks).
- Settlement auto-creation on delivery (`cash_management_service.create_settlements_on_delivery` → journals).
- A background scheduler (`services/command_center_background.py`) calls `run_scheduled_reconciliation_cycle` + payout processing.
- Rich admin UI: 28-tab `/admin/finance`, treasury hub in `treasury-content.tsx`.

**But the user's complaint ("too basic and not automatic") is correct.** Evidence from live code + dev DB:

| Symptom | Evidence |
|---|---|
| Automation machinery exists but is **dormant** | Scheduler jobs exist (`command_center_background.py:358-411`) calling `run_scheduled_finance_cycle` + `run_scheduled_reconciliation_cycle`, gated by `finance_scheduler_enabled=False` (`config.py:91`). Delivery→settlement **is** wired: `create_settlements_on_delivery` is called from `orders_controller.py:1421` and `logistics_partner_controller.py:3210` on the "delivered" event. The dev-DB emptiness (`supplier_settlements=0`, `bank_transactions=0`) is because **no order has actually been marked delivered** in dev (only `transaction_ledgers=1`) — not because the chain is broken. |
| Automation has **no live data to act on** | dev DB: `supplier_settlements=0`, `logistics_settlements=0`, `bank_transactions=0`, `treasury_transactions=0`, `transaction_ledgers=1`. The chain fires only after a real "delivered" event + a finance cycle run. |
| **`accounting_extra` router is unmounted** | `backend/main.py` `router_names` (lines 346–465) has no `accounting_extra`. So `FxPanel`, `DeferredRevenuePanel`, `EmailLedgerPanel`, `AiReconcilePanel` tabs call `/accounting/...` routes that **do not exist** → silently empty/fail. |
| **Backend RBAC is half-built & self-inconsistent** | `FINANCE_ROLES`/`TREASURY_ROLES` (`utils/constants.py:22-23`) and `require_finance_admin` (`routers/_finance_guards.py:19`) **already** accept `finance_admin`. BUT `finance_admin` is **not** in `STAFF_ROLES` (`constants.py:19`), `VALID_USER_ROLES` (`admin_controller.py:193`), or `DEFAULT_ROLE_PERMISSION_MAP` (`staff_permissions.py:60`) → a user **cannot actually be assigned** the `finance_admin` role, and it has no granular permissions. `super_admin` has the same gap. So finance access is currently over-broad (admin-only gate) or missing. |
| **Frontend doesn't know the role** | `frontend/shared/src/adminPermissions.ts` `AdminStaffRole` union (line 1) = only 6 roles, **no `finance_admin`/`super_admin`**, and there is **no `isFinanceAdminRole`** (grep across frontend = 0 matches). Finance tabs are gated by broad `isAdminStaffRole` (incl. `moderator`/`support`). Audit doc claimed #12 "RESOLVED" — **false in live code**. |
| Two `/accounting` routers collide | `accounting`, `finance_automation`, `finance_erp` all mount at `/accounting`; `accounting_extra` would collide further and is the reason it was likely left unmounted. |
| Audit doc's "RESOLVED" claims are stale | Frontend RBAC fix and `accounting_extra` mount are not present. Trust audit doc with caution. |
| Treasury UI is one giant file | `treasury-content.tsx` holds whole treasury hub; hard to extend, no separation of reconciliation/payout controls. |

**Root cause of "basic/not automatic":** the machinery is built but (a) the scheduler is disabled so cycles never run, (b) the autopilot endpoints (`accounting_extra`, AI reconcile) are unreachable (unmounted/colliding prefix), (c) the `finance_admin` role is referenced by guards but undefined in the canonical role registries and unknown to the frontend, so finance access is over-broad (admin-only) or missing, and (d) dev has no delivered orders, so the delivery→settlement→payout→reconcile chain has never been exercised end-to-end. The user's "too basic" perception comes mostly from (b)+(c): dead tabs + no real finance role.

---

## 1. Goals

1. **Turn on safe automation** — order→delivery→settlement→payout→reconcile runs automatically (not manual).
2. **Wire the dead endpoints** — `accounting_extra` (FX, deferred revenue, email-to-ledger, AI reconcile) reachable; no empty tabs.
3. **Real finance RBAC** — `isFinanceAdminRole` + permission-scoped access, replacing blanket `isAdminStaffRole` for finance.
4. **Make the UI actually usable** — working reconciliation autopilot, payout batches, COD remittance, VAT remittance, cash position, with clear pending/exception states.
5. **Verify end-to-end** — a real order flows through to a settled payout and a reconciled bank transaction.

---

## 2. Decisions (CONFIRMED with user 2026-07-20)

- **Autopilot / scheduler:** `finance_scheduler_enabled = True` in **dev** to prove the order→settlement→payout→reconcile chain works on real data; stay **OFF in prod** until dry-run validation passes (matches `CASH_MANAGEMENT_SYSTEM.md` rollout guidance). Ship a **"Run Automation Now"** admin action + **dry-run mode** regardless, so finance can trigger/inspect on demand.
- **`accounting_extra` mount:** Mount it at a **distinct prefix `/accounting-extra`** (not `/accounting`) to avoid collision with the three existing `/accounting` routers. Update frontend `ACCOUNT_BASE` per-panel accordingly.
- **Finance RBAC:** The `finance_admin` role **already exists** in the backend (`constants.py` `FINANCE_ROLES`/`TREASURY_ROLES`, `_finance_guards.require_finance_admin`, `rls_middleware`). It is **not** in the canonical role registries (`VALID_USER_ROLES`, `STAFF_ROLES`, `DEFAULT_ROLE_PERMISSION_MAP`), so it can't be assigned and has no perms. Plan = **canonicalize the existing role** (add to those 3 registries + `super_admin`), add a `finance_admin` permission group, and add `isFinanceAdminRole` on the frontend. No new role enum needed (the `User.role` column is a free `String`).
- **Build order (confirmed):** **Dead tabs + RBAC first**, then the autopilot UI. Phase C (UI) is split: C1 = fix 4 dead panels + RBAC guard swap (quick wins); C2 = autopilot/reconciliation UI.
- **Single source of truth for posting:** keep `general_ledger_service` / `treasury_engine` as the only posting paths (already the case). Do **not** add a 4th path.
- **Scope cut:** Do NOT rebuild the schema (models exist). Do NOT do true multi-country COA re-architecture here (DB agent's country-table work). Focus on wiring, RBAC, and UI glue.

---

## 3. Implementation Tasks (ordered)

### Phase A — Wire the dead automation (backend)
1. **Mount `accounting_extra`** at `/accounting-extra` in `backend/main.py` `router_names`; confirm `finance_erp`/`finance_automation` paths don't collide (they're under `/accounting`; `/accounting-extra` is separate). Verify `POST /accounting-extra/reconciliation/{id}/auto-ai` returns 200/404 not 500.
2. **Enable & harden the autopilot**: in `command_center_background.py`, wire the existing scheduler jobs (reconciliation cycle + payout processing) behind `finance_scheduler_enabled`. Add an admin-triggerable single-run endpoint (`POST /admin/treasury/automation/run-once?dry_run=true`) that calls `run_scheduled_reconciliation_cycle` + `process_supplier_payout_batch` so finance can run automation on demand.
3. **Verify delivery→settlement trigger**: `create_settlements_on_delivery` is **already** called from `orders_controller.py:1421` (order "delivered") and `logistics_partner_controller.py:3210` (shipment "delivered"). Confirm it runs and posts the delivery-revenue journal. The dev-DB `supplier_settlements=0` is because no order has been marked delivered in dev — not a wiring bug. Use the Phase D seeded order to prove it fires.
4. **COD remittance → ledger:** confirm `post_logistics_cod_remittance_journal` is called from the COD remittance endpoint so `1030 COD Receivable` clears and `bank_transactions` get created. Currently `bank_transactions=0`.

### Phase B — Finance RBAC (backend canonicalization + frontend awareness)
The backend *gate* `require_finance_admin` already exists and is correct; the problem is the role `finance_admin` is undefined in the canonical role registries, so it can't be assigned and the frontend doesn't know it. Fix both sides so the role is real and usable.

**B1 — Backend: make `finance_admin` (and `super_admin`) first-class roles**
5. Add `"finance_admin"` (and `"super_admin"`) to `VALID_USER_ROLES` in `controllers/admin_controller.py:193` so users can be assigned the role (role-assignment validation at `admin_controller.py:680`/`:1595`).
6. Add `"finance_admin"` to `STAFF_ROLES` in `utils/constants.py:19` (keep `country_head`/`country_manager`; ensure `super_admin` is also recognized where staff logic applies — confirm `super_admin` handling in `dependencies.require_super_admin`/`_require_role` already covers it).
7. Add a `finance_admin` entry to `DEFAULT_ROLE_PERMISSION_MAP` (`utils/staff_permissions.py:60`) carrying finance-relevant permissions: `countries.finance`, `payouts.verify`, plus a new `finance.view` / `finance.ledger` / `finance.reconciliation` set. This makes `default_permissions_for_role("finance_admin")` return real perms (currently undefined → empty). Ensure these permission strings are added to `STAFF_PERMISSION_GROUPS` / `KNOWN_ROLE_PERMISSIONS` so `sanitize_staff_permissions` accepts them.
8. Confirm `require_finance_admin` (`_finance_guards.py`) already covers `finance_admin` (it does via `FINANCE_ROLES`). Apply `require_finance_admin` (or the existing `require_finance_permission`) to the new `/accounting-extra/*` and `/admin/treasury/automation/*` routes. Maker-Checker (`created_by != approver_id`) stays enforced.

**B2 — Frontend: know & use the role**
9. Extend `AdminStaffRole` in `frontend/shared/src/adminPermissions.ts:1` to include `"finance_admin"` (and `"super_admin"`). Add `isFinanceAdminRole(role)` = `admin | super_admin | finance_admin | country_head` (mirrors backend `FINANCE_ROLES`).
10. Add a `finance_admin` row to `ADMIN_PERMISSION_MAP` (and `STAFF_PERMISSION_GROUPS` if needed) granting `countries.finance`, `payouts.verify`, finance view perms, so the permission matrix is consistent.
11. **Swap guards**: in `finance/page.tsx` and `treasury-content.tsx`, replace `isAdminStaffRole(...)` → `isFinanceAdminRole(...)`. This is the audit's claimed-but-missing fix #12. After this, `moderator`/`support` are correctly blocked from finance.

### Phase C — Make the UI usable (frontend)
**C1 — Quick wins (do first, per confirmed build order):**
- **C1.1 Fix the 4 dead tabs**: point `FxPanel`, `DeferredRevenuePanel`, `EmailLedgerPanel`, `AiReconcilePanel` (in `FinanceModules.tsx`) at `/accounting-extra/...` so they no longer call missing routes. Confirm each returns data or a clean empty state (no silent failure).
- **C1.2 RBAC guard swap**: replace `isAdminStaffRole` with `isFinanceAdminRole` in `finance/page.tsx` and `treasury-content.tsx` (the audit claimed this was done; it was not).

**C2 — Autopilot / reconciliation UI (after C1):**
- **C2.1 Reconciliation autopilot UI**: in `treasury-content.tsx` / `ErpPanels.BankReconciliationPanel`, surface `POST /accounting-extra/reconciliation/{id}/auto-ai` with a one-click "Auto-reconcile" + exception list. Today the AI path is unreachable.
- **C2.2 "Run Automation" control**: add a button in the treasury dashboard calling `POST /admin/treasury/automation/run-once?dry_run=true` then live; show a result summary (settlements created, payouts processed, matched/unmatched bank lines).
- **C2.3 Cash position & payables clarity**: ensure `CashPositionView` shows `free_cash`, reserves, and **pending** supplier/logistics payables with clear "eligible vs on-hold" state (hold-window, unverified bank account). Hide raw zeros; show "no activity yet" states.
- **C2.4 Split `treasury-content.tsx`** into smaller views (Dashboard, CashPosition, Payouts, Reconciliation, COD, VAT, Payments) — at minimum extract reconciliation + payouts into components so they're maintainable. (Nice-to-have; follow-up if time-boxed.)

### Phase D — Verify end-to-end
13. **Seed/scripted order**: create an order (COD + Card), mark delivered, run automation-once, then assert:
    - `supplier_settlements > 0`, `logistics_settlements > 0`
    - corresponding `journal_entries` (delivery revenue split) exist and `SUM(debits)=SUM(credits)`
    - `bank_transactions` created for COD remittance / payout
    - trial balance stays balanced; cash position moves.
14. **Endpoint sweep** (authed finance role): `/finance/dashboard/metrics`, `/treasury/cash-position`, `/admin/treasury/[cc]/payouts/batches`, `/accounting-extra/fx/rates`, `/accounting-extra/reconciliation/{id}/auto-ai`, `/cash-management/admin/bank-accounts/pending`. All 200, no 404s on finance tabs.
15. **RBAC check**: a `moderator`/`support` role should be blocked from finance tabs after the guard swap; a `finance_admin`/`country_head` allowed.

---

## 4. Files to Touch (summary)

**Backend**
- `backend/main.py` — add `("accounting_extra", "/accounting-extra")` to `router_names`.
- `backend/services/command_center_background.py` — scheduler jobs already call `run_scheduled_finance_cycle` + `run_scheduled_reconciliation_cycle`; no change needed beyond the `finance_scheduler_enabled` dev flag.
- `backend/routers/admin_treasury.py` (or new small router) — add `POST /admin/treasury/automation/run-once?dry_run=`.
- `backend/controllers/admin_controller.py` — add `"finance_admin"` (and `"super_admin"`) to `VALID_USER_ROLES` (line 193) so the role is assignable; role-assignment validation at lines 680/1595.
- `backend/utils/constants.py` — add `"finance_admin"` to `STAFF_ROLES` (line 19); `FINANCE_ROLES`/`TREASURY_ROLES` already include it.
- `backend/utils/staff_permissions.py` — add a `finance_admin` entry to `DEFAULT_ROLE_PERMISSION_MAP` (line 60) with `countries.finance`, `payouts.verify`, and new `finance.*` perms; add those permission strings to `STAFF_PERMISSION_GROUPS` / `KNOWN_ROLE_PERMISSIONS` (line 164) so they validate.
- `backend/routers/_finance_guards.py` — `require_finance_admin` already covers `finance_admin`; apply it (+ `require_finance_permission`) to the new `/accounting-extra/*` and `/admin/treasury/automation/*` routes.

**Frontend**
- `frontend/shared/src/adminPermissions.ts` — extend `AdminStaffRole` union with `"finance_admin"`/`"super_admin"`; add `isFinanceAdminRole`; add `finance_admin` row to `ADMIN_PERMISSION_MAP`.
- `frontend/web_app/src/app/admin/finance/page.tsx` — guard swap → `isFinanceAdminRole`.
- `frontend/web_app/src/app/admin/treasury/treasury-content.tsx` — guard swap; add automation control + split views.
- `frontend/web_app/src/app/admin/finance/FinanceModules.tsx` — repoint 4 panels to `/accounting-extra`.
- `frontend/web_app/src/app/admin/finance/ErpPanels.tsx` — wire AI auto-reconcile.

---

## 5. Risks / Caveats

- **`accounting_extra` collision:** mounting at `/accounting` would clash with 3 existing routers; use `/accounting-extra`. Confirm `finance_erp`'s `reconciliation/{id}/auto-ai` vs `accounting_extra`'s `reconciliation/{id}/auto-ai` don't both resolve — different prefixes avoids this.
- **Scheduler safety:** never enable `finance_scheduler_enabled=True` in prod until dry-run matches expectations (per `CASH_MANAGEMENT_SYSTEM.md` rollout step 5).
- **Role-registry inconsistency:** `VALID_USER_ROLES` (admin_controller.py:193) and `STAFF_ROLES` (constants.py:19) disagree (former lacks `country_head`/`country_manager`/`finance_admin`/`super_admin`; latter lacks `finance_admin`/`super_admin`). Adding `finance_admin` to both closes the assignability gap. Also normalize `super_admin` consistently. Keep the change minimal and additive — do not remove existing roles.
- **Permission-string validation:** new `finance.*` permission strings must be whitelisted in `KNOWN_ROLE_PERMISSIONS` (`staff_permissions.py:164`) or `sanitize_staff_permissions` rejects them for users with custom permission overrides.
- **DB FK orphans** (`transaction_ledgers`, `accruals`) remain with the DB agent; finance reports that join them may show wrong numbers until fixed. Flag, don't block.
- **Multi-country:** country-scoped `/{country_code}/...` routes still depend on the `countries` table fix (DB agent). Until then those routes 404.

---

## 6. Open Questions — RESOLVED (2026-07-20, see Section 2)

1. ✅ Scheduler: ON in dev, OFF in prod; ship manual "Run Automation" + dry-run.
2. ✅ RBAC: add `finance_admin` role + permission group.
3. ✅ Build order: dead tabs + RBAC (C1) first, then autopilot UI (C2).

---

## 7. Validation Checklist (definition of done)
- [ ] `accounting_extra` mounted; its 4 panels return real data (no 404).
- [ ] `isFinanceAdminRole` exists; finance tabs blocked for `moderator`/`support`.
- [ ] A scripted order → delivered → "Run Automation" yields `supplier_settlements>0`, `bank_transactions>0`, balanced trial balance.
- [ ] Reconciliation autopilot one-click works and routes exceptions to a review list.
- [ ] Endpoint sweep 200s; no silent empty finance tabs.
