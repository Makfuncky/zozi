# Browser Test Blockers — What Is Not Working

**Purpose:** hand-off document for the next engineer/agent. Every item below is an observed failure with the evidence that proves it. Nothing here is speculative.

- **Written:** 2026-10-05
- **Stack used:** backend `uvicorn` on `:8000`, frontend `next dev` on `:3000`, Valkey via Docker, Postgres = remote Neon dev DB
- **Suite:** `_browser_test/` — 70 specs, 314 tests load, `tsc --noEmit` = 0 errors
- **Evidence gallery:** `_browser_test/evidence/final/index.html` — 198 screenshots, 5 videos
- **Journey result:** **79 interactions attempted, 56 not completed (71 % failure)**

> **⚠️ Read first:** during this work, edits to tracked files in the working tree were repeatedly
> reverted by another process, and helper scripts were deleted. Confirm nothing else is writing to
> this tree before relying on any fix below. `_reapply_fixes.py` (repo root) re-applies the backend
> fixes in one pass and is idempotent.

---

## 1 · Headline: the frontend and backend disagree about every admin and supplier route

This is the single biggest cause of the empty dashboards.

| Check | Result |
|---|---|
| Backend routes matching top-level `/admin/*` | **0** |
| Backend routes matching top-level `/supplier/*` | **0** |
| Backend routes matching top-level `/logistics/shipments` | **0** |
| Backend routes matching `/hr/dashboard` | **0** |

Every admin and supplier page calls a path that does not exist:

| Page (`frontend/web_app/src/app/…`) | Calls | Backend reality |
|---|---|---|
| `admin/users/page.tsx` | `/admin/users?limit=…` | 404 |
| `admin/orders/page.tsx` | `/admin/orders?…` | 404 |
| `admin/audit-logs/page.tsx` | `/admin/audit-logs?…` | 404 |
| `admin/countries/page.tsx` | `/admin/countries`, `/admin/countries/{code}/…` (25 sub-paths) | 404 |
| `admin/commission/page.tsx` | `/admin/{code}/rates`, `/admin/{code}/badge-tiers` | 404 |
| `admin/hr/page.tsx` | `/hr/dashboard?…` | 404 |
| `supplier/products/page.tsx` | `/supplier/products?…` | 404 |
| `supplier/orders/page.tsx` | `/supplier/orders?…`, `/supplier/orders/{id}/parcel-proof` | 404 |

**Why it happens.** `src/lib/api/client.ts → resolveRequestUrl()` sends any path that is not
`/api`, `/auth` or `/admin` through `/__api`. Paths starting with `/admin` are passed through
unchanged, and `next.config.ts` rewrites `/admin/:path*` → `${apiUrl}/admin/:path*`. The backend
exposes admin functionality under `/api/v1/admin/*` instead, so every admin page 404s.

**Decision needed:** either add `/admin/*` and `/supplier/*` aliases on the backend, or fix
`resolveRequestUrl()` / `next.config.ts` to map admin pages onto `/api/v1/admin/*`. This is an
architecture decision, not a typo fix.

---

## 2 · Blockers by workflow

### 2.1 Admin — 15 of 17 interactions failed

Evidence: `evidence/final/admin/journeys.md`, `evidence/final/admin/068-command-center-after.png`

The Command Center **authenticates correctly** (sidebar shows "Admin / admin", Logout present) but
every panel is an empty skeleton: `ACTIVE SESSIONS 0`, `DB CONNS 0`, `REDIS HIT –`,
`INITIALISING…` at the page bottom.

| Step | Outcome |
|---|---|
| Command Center panels | 0 rows |
| Users list | 0 rows |
| Country ledger — select Oman (`[data-testid="country-ledger-row-OM"]`) | not found |
| Country tabs — Commission, Payouts, FX, Users, Governance | none found |
| Commission editor | not found |
| Orders / disputes / returns / tickets / treasury | 0 rows each |
| Audit log rows | 0 rows |

Root cause: §1. `audit_logs` itself has 840 rows in the database, so the empty table is purely the
missing route.

### 2.2 Customer — 17 of 27 failed

Evidence: `evidence/final/customer/journeys.md`

**Working:** session bootstrap, home (40 cards), catalogue (40 products), search, product detail,
**Add to Cart succeeded**, "Proceed to Checkout" clicked, `/checkout` reached, `/returns` reached.

**Broken:**

| Step | Problem |
|---|---|
| Cart shows 0 line items after Add to Cart | cart state does not persist to `/cart` |
| Cart quantity +/- , promo code, apply | controls not found (empty cart renders nothing) |
| Checkout street / city / phone fields | not found |
| Cash-on-Delivery option | not found |
| Place Order | not found |
| `/orders` list, order detail, tracking | 0 rows / not found |
| Wishlist, addresses | 0 rows |

**Two separate bugs here:**

1. **Frontend route contract** — `GET /api/v1/customer/orders/orders` returns **HTTP 500**:
   `AttributeError: 'Order' object has no attribute 'status'`. The column is `status_code`
   (see `chk_orders_status_valid`); `domains/orders/services/core/order_engine.py` reads and writes
   `order.status`. A patch was applied and then reverted by the working-tree revert — **it needs
   re-applying**.

2. **Cart design mismatch** — there are **no cart routes in the backend at all**. Cart is a
   client-side Zustand store (`useCartStore`), so the Add-to-Cart click cannot be expected to make
   `/cart` server-rendered. The journey and any regression test must either seed `localStorage`
   before visiting `/cart`, or assert on the Zustand badge (which the evidence shows incrementing to
   **1**, i.e. Add-to-Cart genuinely works).

### 2.3 Logistics — 8 of 10 failed

Evidence: `evidence/final/logistics/journeys.md`

| Check | Result |
|---|---|
| `GET /api/v1/logistics/logistics/shipments?limit=20` | **200, 5 items** (4 seeded + 1 pre-existing) |
| Page `/logistics-partner/shipments` | **0 rows** |
| `GET /api/v1/logistics/logistics/dashboard` | **500** |

So the shipments endpoint returns data but the page renders none — the fault is between the page and
the endpoint. Candidate causes to check: the `next.config.ts` rewrite I added
(`/__api/logistics-partner/:path*` → `/api/v1/logistics/logistics/:path*`) may not be reloaded, the
response envelope key may differ from what the page expects, or the page may filter by a partner id
the seeded partner does not have.

Parcel scan input, verify button, picked-up / in-transit / delivered transitions, and proof-of-delivery
were all not found — consistent with an empty table (no row to act on).

### 2.4 Employee — 6 of 8 failed

Evidence: `evidence/final/employee/journeys.md`

| Check | Result |
|---|---|
| `GET /api/v1/employee/accounts/leave/balance` | **500** — `relation "employees" does not exist` |
| `GET /api/v1/employee/accounts/attendance` | **500** — same |
| Page `/admin/hr` | 0 stat cards |

`hr.employee_attendances` has **10 seeded rows** and `hr.employee_leave_ledgers` / `employee_leave_requests`
have **3 each** — the data exists.

**Path mismatch:** the pages call `/api/v1/employee/hr/...`; the working routes are
`/api/v1/employee/accounts/...`:

| Page calls | Exists? |
|---|---|
| `/api/v1/employee/hr/attendance` | yes (but 500) |
| `/api/v1/employee/hr/leave/balance` | yes (but 500) |
| `/api/v1/employee/hr/leave/history` | yes |
| `/api/v1/employee/hr/leave/request` | yes |
| `/api/v1/employee/hr/schedule/clock-in` | **MISSING** |
| `/api/v1/employee/hr/schedule/clock-out` | **MISSING** |
| `/api/v1/employee/hr/workspace` | **MISSING** |
| `/api/v1/employee/hr/tasks/stats` | **MISSING** |
| `/api/v1/employee/hr/payroll/payslips` | **MISSING** |
| `/api/v1/employee/hr/performance/okrs` | **MISSING** |

The real routes that do exist are `/api/v1/employee/accounts/{attendance,leave/balance,leave/history,leave/request,okrs,org-chart,payslips,profile}`.

**The `relation "employees" does not exist` bug:** `infrastructure/database/database.py` computes a
`search_path` and registers an `event.listens_for(engine, "connect")` hook that runs
`SET search_path TO …`. Verified with a direct session: `SHOW search_path` returns the full list and
`SELECT count(*) FROM employees` returns **6**. But through HTTP the same query fails. The listener
is therefore not applying to the session `get_db()` hands to routes. Investigate whether
`SessionLocal` / `get_db` binds a different engine than the one the listener is attached to.

### 2.5 Supplier — 10 of 17 failed

Evidence: `evidence/final/supplier/journeys.md`

| Step | Outcome |
|---|---|
| Dashboard KPI cards | 0 rows |
| Catalogue ("my products") | 1 row — the only data-bearing surface |
| "Add product" button | not found |
| Product form fields (name, SKU, price, stock, description) | 0 of 5 found |
| Assigned orders, order detail, advance status | 0 rows / not found |
| Commission, payouts, analytics | 0 rows each |

Root cause: §1 (`/supplier/*` has no backend routes). The one row that renders comes from a
different, working path.

---

## 3 · Backend defects independent of the frontend

### 3.1 Missing `ports.py` re-exports (~98 names)

Many `domains/*/ports.py` modules are thin shims that no longer export the names other domains
import. A scan across 1 359 files found **~98 unresolved imports**. Import failures here abort
`_preload_all_models()` mid-walk, which leaves ORM mappers unconfigured — so a missing re-export in
one domain breaks logins for the whole application.

**10 names are implemented nowhere in the repository** (not merely un-exported):

```
domains.finance.ports   commission_engine
                        create_cash_account
                        create_cash_transaction
                        log_bank_transaction
                        run_scheduled_finance_cycle
                        run_scheduled_reconciliation_cycle
domains.hr.ports        log_comm_event
domains.comms.ports     auto_process_image
                        save_product_media
                        save_supplier_media
```

The other ~88 were re-exported lazily during this work; those edits were also reverted and need
re-applying. Verify with `_reapply_fixes.py` and the audit script referenced in §6.

### 3.2 Migration chain was wedged

`alembic_version.version_num` is `VARCHAR(32)`, but migrations `20261004_0015_backfill_worm_hash_columns`
and `…0016_encrypt_mfa_factor_secret` use 43-character revision ids. Every `alembic upgrade` failed
with `StringDataRightTruncationError`, leaving the database stuck at `20261004_0013`.

**Fixed during this work:** widened to `VARCHAR(255)`; migrations now run to `20261004_0017`.

### 3.3 `audit_logs.worm_hash` was never created

`AuditLog` maps `worm_hash` / `worm_prev_hash` (`String(128)`, nullable) and every login writes an
audit row, so `/auth/login` failed with `UndefinedColumn`. Migration `0015` only *backfills* those
columns and returns early when they are absent.

**Fixed:** new migration `2026_10_04_0017_add_audit_logs_worm_hash_columns.py` created.

---

## 4 · Environment / tooling gaps

| Item | Detail |
|---|---|
| `nanoid` missing | `frontend/web_app` — every page 500'd with `Module not found: Can't resolve 'nanoid'`. **Fixed** (`npm install nanoid --legacy-peer-deps`). Note a pre-existing peer conflict: `@stripe/react-stripe-js@6.9.0` wants `@stripe/stripe-js >=9.10.0 <10.0.0`. |
| Docker not running | `com.docker.service` was `Stopped`; started via `docker desktop start` (needs elevation). `docker-compose.yml` already defines `valkey:9.0-alpine` on `127.0.0.1:6379` — nothing to add. |
| Backend deps | `cryptography`, `pyjwt`, `twilio` were not installed although `infrastructure/security/encryption.py` and `domains/…/iam_service_accounts.py` import them. Missing `cryptography` caused the finance and orders routers to be **silently skipped** at startup. **Fixed and pinned in `requirements.txt`.** |
| Execution policy | `Set-ExecutionPolicy -Scope Process Bypass` is needed before dot-sourcing `config/stack.env.ps1`. |
| Frontend port | SPA serves on **:3000**, not :3100. Run with `WEB_BASE_URL=http://localhost:3000`. |

---

## 5 · Seed-data gaps (block assertions even after code fixes)

| Gap | Current |
|---|---|
| Countries | 3 (`AE`, `OM`, `SA`); `tests/database.spec.ts` expects 6 (`+BH`, `KW`, `QA`) |
| Product variants | **0**, despite 41 products |
| `catalog.inventory` | table does not exist |
| Orders | 1 order total |
| Shipments | 5, all seeded by me for this run |

A seeder exists: `backend/scripts/_seed_browser_journey_data.py` (idempotent — 10 attendance rows,
3 leave requests, 3 leave ledgers, 4 shipments + events).

---

## 6 · Verified working — do not re-investigate

| Check | Result |
|---|---|
| `GET /health` | `database: ok`, `valkey: ok` |
| Logins: admin, supplier, customer, logistics, employee | all **200 + access_token** |
| `GET /api/v1/customer/catalog/products?limit=5` | **200, 20 items** |
| `GET /api/v1/logistics/logistics/shipments?limit=20` | **200, 5 items** |
| Customer storefront: home, catalogue, search, PDP | **40 products render**, Add to Cart increments the badge to 1 |
| Alembic head | `20261004_0017`, single head |
| Suite | 70 specs / 314 tests load, `tsc` clean |

**Employee credentials (correct ones):**

| Role | Email | Password |
|---|---|---|
| admin | `admin@zozi.com` | `E2eAdmin#2026` |
| supplier | `supplier@zozi.com` | `E2eSupplier#2026` |
| customer | `customer@zozi.com` | `E2eCustomer#2026` |
| logistics | `logistics@zozi.com` | `E2eLogistics#2026` |
| employee | `ae.manager@zozi.com` | `DevSeed123!` |

There is **no `employee@zozi.com`** account, and no `E2eEmployee#2026` password. Employees are
seeded per country (`<cc>.manager@`, `<cc>.finance@`, `<cc>.support@` @zozi.com) sharing
`DevSeed123!`.

---

## 7 · Suggested fix order

1. **Re-apply reverted fixes** — run `backend/.venv/Scripts/python.exe _reapply_fixes.py` from the repo root; then re-verify with §8.
2. **`ports.py` re-exports** — biggest systemic blocker. Re-export the ~88 resolvable names; write the 10 unimplemented ones or remove their call sites.
3. **Admin / supplier route contract (§1)** — decide alias-vs-rewrite, then fix one actor end-to-end as a pilot.
4. **`search_path` not applying over HTTP (§2.4)** — small, high value; unlocks employee and any other unqualified raw SQL.
5. **`Order.status` → `status_code` (§2.2)** — unlocks customer orders, tracking and wishlist.
6. **Employee path mismatch (§2.4)** — point pages at `/api/v1/employee/accounts/*` or add the 6 missing `/hr/*` routes.
7. **Logistics page renders 0 rows despite 200 (§2.3)** — check the rewrite is live, then response envelope vs page expectation.
8. **Seed data (§5)** — countries, product variants, orders.
9. Re-run the journeys and rebuild the gallery.

---

## 8 · How to re-run and verify

```powershell
# stack
docker desktop start
docker compose up -d valkey
cd backend; .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning
cd ..\frontend\web_app; npm run dev          # serves :3000

# suite
cd ..\..\_browser_test
node scripts\preTestScan.mjs
npx tsc --noEmit
$env:WEB_BASE_URL="http://localhost:3000"; $env:API_BASE_URL="http://127.0.0.1:8000"; $env:RUN_ID="check"
npx playwright test tests/journeys --reporter=list --retries=0
node scripts\build-evidence-index.mjs check
```

Then read `evidence/check/<actor>/journeys.md` — the "not completed" count should fall from 56/79.

---

## 9 · Appendix — where the evidence is

```
_browser_test/evidence/final/index.html          gallery
_browser_test/evidence/final/<actor>/            before/after PNG per step + walkthrough.webm
_browser_test/evidence/final/<actor>/journeys.md interaction log (what was clicked, what was found)
_browser_test/tests/journeys/*.spec.ts           the 5 journey specs
_browser_test/src/journey.ts                     resilient selectors + JourneyLog
_browser_test/src/evidence.ts                    step()/settle()/diagnostics
_browser_test/tests/00-route-walk.spec.ts        walks all 155 routes by actor
```

**Note:** the 314 regression tests in `tests/auth/`, `tests/modules/*`, `tests/cross-cutting/`,
`preflight` and `database` have **never been executed** against a live stack — only `--list` was run.
Treat them as unverified.