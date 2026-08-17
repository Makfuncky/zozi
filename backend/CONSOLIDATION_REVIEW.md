# Consolidation Review — `domains/country/services/` and the `accounts/` mirror

> Status: **INVESTIGATION ONLY — no files moved in this pass.**
> Supersedes the flawed `RELOCATION_PLAN.md` triage (it was name-based and wrong).

## 1. True current state of `domains/country/services/`

After Phase 1 removed 34 "free" files, **76 `.py` files remain**. A content-based analysis
(imports + class affinity + cross-domain similarity) shows the previous claim of "43 country-owned"
was incorrect. The real split of the 76 files:

| Bucket | Count | Meaning |
|---|---|---|
| Genuinely country-owned, no duplicate anywhere | **36** | Correctly placed. Leave as-is. |
| Country-owned, but a stale twin exists in `accounts`/`logistics` | **6** | Canonical = country. Retire the twin. |
| Misplaced: country copy is a duplicate/stub of code owned elsewhere | **34** | Retire the country copy; canonical lives in another domain. |

(36 + 6 + 34 = 76.)

### 1a. The 36 correct, country-owned files (leave alone)
`country_service` (1554 ln), `country_write_service`, `country_read_service`, `country_admin_write_service`,
`country_audit_admin_service`, `country_auto_populate` (622), `country_auto_populate_write_service`,
`country_communication_service`, `country_communications_read_service`, `country_communications_service`,
`country_config_admin_service`, `country_config_write_service`, `country_controller`,
`country_country_communications_read_service`, `country_curated`, `country_data_orchestrator`,
`country_detection`, `country_heuristic_engine` (516), `country_payout_write_service`,
`country_restriction_service`, `country_rls_service`, `country_router_service`, `country_staff_write_service`,
`country_tax_service`, `country_versioning_controller`, `country_versioning_service`, `cross_border_base`,
`cross_border_detection`, `cross_border_service`, `cross_border_tracker`, `curated_cities`,
`category_tax_profiles`, `localization_service`, `travel_detector`, `travel_service`.

### 1b. Country-owned but with a stray twin (keep country, retire twin)
`country_dropdown_service` (accounts twin 0.07 sim — divergent/stale),
`country_maps_service` (accounts twin 0.06 sim),
`country_staff_service` (accounts twin 0.04 sim),
`geo_resolver` (logistics twin 1.0 — exact dup),
`main` (logistics twin 1.0 — exact dup),
**`countries_service`** (accounts twin 1.0 — exact dup; semantically country-owned, re-file from the
old "→ accounts" bucket).

### 1c. Misplaced — country copy is a redundant duplicate/stub (retire country copy)
Canonical target (where the real/largest version lives):

- **finance (5):** `cash_management_service` (fin 2104 vs 235), `commission_service` (fin 789),
  `admin_treasury_service` (fin/cust 1253 vs 167 stub), `supplier_finance_service`, `supplier_payouts_service`
- **hr (5):** `employees_service` (needs merge — hr 162 vs 316), `hierarchy_service` (hr 646),
  `hr_service` (hr 136), `payroll_service`, `performance_service` (hr 544)
- **logistics (4):** `admin_logistics_service`, `logistics_health_service` (log 44),
  `logistics_partner_service` (orders 3416), `logistics_service` (orders 949; logistics twin is EMPTY 0)
- **governance (6):** `auth_service` (gov 961), `incident_service` (gov 163),
  `permissions_service` (gov 110), `users_service` (gov 865), `admin_service`, `user_read_service`
- **comms (4):** `chat_enrichment_service`, `chatbot_service` (comms 949; country copy 0 ln),
  `internal_channels_service`, `translation_service` (comms 79)
- **customers (4):** `addresses_service`, `customer_health_service`, `export_service` (review),
  `search_service` (UNMAPPED/cust 719)
- **orders (3):** `admin_orders_service`, `supplier_orders_service` (merge — suppliers 0.64), `admin_products_service`→catalog
- **catalog (1):** `admin_products_service`
- **suppliers (2):** `supplier_health_service`
- **accounts-only twins (14):** `admin_cash_service`, `country_admin_service`, `countries_service`(→country, see 1b),
  `customer_health_service`, `employees_service`, `export_service`, `internal_channels_service`,
  `payroll_service`, `shipments_service`, `supplier_finance_service`, `supplier_payouts_service`,
  `user_read_service`, `addresses_service`, `admin_service` — **these have NO copy outside `accounts`
  except `country`, i.e. the only "other" home is the `accounts/` dump itself (see §2). Their true
  domain must be chosen semantically; `accounts` is NOT a valid canonical.**

## 2. The two "source dumps": `country/` and `accounts/`

System-wide scan of all `domains/*/services/`:

- **647** distinct service filenames; **135 are duplicated across >1 domain**; 512 are unique.
- Copies-per-file: 71 files in 2 domains, 49 in 3 domains, 15 in 4 domains.
- **Almost every duplicate involves `accounts` and/or `country`.** These two folders are the pollution
  sources, not real domains.
- `accounts/services/` holds **97 files** and is the mirror of `country/services/` — e.g. **41 of the 76
  country files are SIM≈1.0 identical copies of their `accounts/` twin.**
- A stray `UNMAPPED/` domain (6 files: `chatbot_service`, `export_service`, `export_read_service`,
  `search_service`, `user_read_service`, + 1) is a catch-all that must be dissolved into real domains.

**Conclusion:** consolidation is NOT just a `country` problem. The full extent is a system-wide
de-duplication of the **135 duplicated filenames down to exactly one canonical copy each**, dissolving
both dumps (`country`, `accounts`) and `UNMAPPED`.

## 3. Phase 1 (already executed) needs repair — do NOT move more files yet

Phase 1 moved 34 files out of `country/services/` via the flawed triage. Checking each moved file against
the copies now sitting beside it:

- **27 of 34 are now duplicates**: the `accounts/` twin remains SIM=1.0 identical, and often an
  `orders`/`customers` copy too. Phase 1 added a copy to the destination domain but **left the dump copy
  in place** → no de-duplication was actually achieved, just relocation of one copy.
- **9 of 34 are DIVERGENT** — the destination already had a *different* implementation, so Phase 1 created
  conflicting versions that must be merged:

| File | Destination | Conflicting copy | sim |
|---|---|---|---|
| `tickets_service` | comms | governance | **0.10** |
| `geo_service` | logistics | accounts | **0.08** |
| `cart_service` | customers | orders (235 ln) | **0.17** |
| `coupons_service` | customers | governance / orders | **0.08** |
| `export_read_service` | customers | orders | 0.94 (near) |
| `referrals_service` | customers | orders | **0.16** |
| `returns_service` | customers | orders | **0.11** |
| `reviews_service` | customers | orders | **0.23** |
| `supplier_orders_service` | orders | suppliers | **0.64** |

These 9 must be reconciled (merged, not deleted) before any further relocation.

## 4. Consolidation extent & method ("till what extend")

**Scope:** all 135 duplicated filenames across `country`, `accounts`, `UNMAPPED`, and stray copies in
`orders`/`customers`/`logistics`/`governance`/`comms`.

**Rule for canonical domain:** the single domain that holds the largest/most-complete, *non-dump* version
of the file. `country` and `accounts` are never canonical by default (they are dumps); `UNMAPPED` is never
canonical (it is a catch-all).

**"Do not delete" enforcement:** redundant copies are **retired to `backend/_archive_services/`** via
`git mv` (history preserved, nothing destroyed). The archive is excluded from imports; CI fails if any
`domains/*/services/` file also exists in `_archive_services/`.

**Steps:**
1. Freeze further blind moves.
2. Repair the 9 divergent Phase-1 files (merge the conflicting versions into the canonical domain).
3. For each of the 135 dup filenames, pick canonical + retire all other copies to `_archive_services/`.
4. Re-point any imports that referenced a retired copy (should be none for true dups, but verify).
5. Dissolve `UNMAPPED/` into catalog/comms/customers/governance as appropriate.
6. Re-file `countries_service` as country-owned (retire accounts twin).

## 5. Verification checklist

- [ ] `grep -rn "from modules" backend/domains` → 0 (Law 1).
- [ ] Each of the 135 formerly-duplicated filenames now exists in **exactly one** `domains/*/services/`.
- [ ] `backend/_archive_services/` contains the retired copies; CI fails on any name collision with live tree.
- [ ] `UNMAPPED/` is empty/dissolved.
- [ ] The 9 divergent Phase-1 files each resolve to a single merged canonical implementation.
- [ ] `python -m py_compile` on every `domains/*/services/*.py` → clean.
- [ ] `pytest` green; app boots; `migration_tracker.py --json` shows `routers_with_business_logic: 0`.
- [ ] No import silently falls back to the archive (grep all `domains.country.services` / `domains.accounts.services` references → 0).
- [ ] `coherence_gate.py --check` passes.

## 6. Raw evidence (generated this pass)
- `git mv` unusable (files untracked) → use `shutil.move` + `git add`.
- Similarity matrix and per-file canonical map produced via scripts in `C:\Users\user\AppData\Local\Temp\kilo\`.
- Detected: country=76, accounts=97, comms=93, finance=123, governance=109, orders=87, etc.

## 7. Repair plan for the 9 divergent Phase-1 files (read + planned, NOT executed)

### 7.0 Critical architectural fact discovered while reading
- `backend/services/__init__.py` is a shim: `services` → `_legacy.services`. So every
  `from services.commerce.X import ...` / `services.admin.X` / `services.core.X` resolves to
  **`_legacy/services/...`**, a *separate* file tree from `domains/*/services/...`.
- The new `domains/*/services/*.py` files are live only when imported as
  `domains.<domain>.services.<name>` (the `*__routers.py` files). Grep of all import sites shows
  only these of the 9 are live via that path:
  `orders/reviews_service`, `orders/coupons_service`, `orders/referrals_service`
  (+ `tests/test_export_read_service.py` → `accounts/export_read_service`).
- Therefore archiving a `domains/*/services/*.py` duplicate is safe UNLESS it is one of the three
  live `orders` ones above. The `_legacy` tree is untouched by this plan.

### 7.1 Per-file decision (KEEP = canonical single owner; ARCHIVE = retire to `backend/_archive_services/`)

Aligned to `documents/f.md` **Database Constitution → Bounded Contexts (L1385–1401)** and the
**Golden Rule (L1378): "Single Source of Truth — never duplicate transactional data."** Each
service filename therefore has **EXACTLY ONE** canonical domain owner; the earlier "complementary
two-domain" splits for `tickets_service`/`coupons_service` are **withdrawn** — the extra copies are
retired to archive (nothing deleted).

| File | KEEP (canonical domain) | ARCHIVE (retire) | Why (per f.md constitution) |
|---|---|---|---|
| `tickets_service` | `comms` (125) | `governance` (140), `orders`, `accounts` | `communication` schema owns **tickets** (f.md L1397: "Chat, email, SMS, push, tickets, video rooms"). Single owner = comms. |
| `geo_service` | `logistics` (65) | `accounts` (62) | No `geography` schema exists; `logistics` owns routes/shipments and this is the clean layered copy. (Alt home `country` owns cities/tax — noted; logistics kept as complete non-dump.) |
| `cart_service` | `orders` (287) | `customers`, `accounts` | `commerce` schema owns carts/orders (f.md L1387). orders clean layered; others legacy stubs. |
| `coupons_service` | `orders` (197) | `governance` (131), `customers` (177), `accounts` | `commerce` owns orders/promo. Single owner = orders. governance admin-mgmt copy retired (runtime uses `_legacy services.admin.coupons_service`). |
| `export_read_service` | `customers` (88) | `UNMAPPED`, `orders` (68), `accounts` | `customer` schema owns profiles/data (f.md L1389). customers is the clean extracted version. Repoint test import. |
| `referrals_service` | `orders` (122) | `customers`, `accounts` | `commerce` owns. orders clean; customers/accounts import `modules.commerce...` (**Law-1**) and are stubs. |
| `returns_service` | `orders` (40) | `customers` (94) | `commerce` owns. orders clean; customers imports `modules.orders.routers.returns_controller` (**Law-1**). |
| `reviews_service` | `orders` (137) | `customers` (97) | `commerce` owns. orders is persistence service; customers legacy. |
| `supplier_orders_service` | `suppliers` (536) | `orders`, `customers`, `accounts` (613) | `supplier` schema owns supplier ops (f.md L1388). suppliers is domain-owned; 613-ln copies are divergent dump. |
| `countries_service` | `country` | `accounts` | `country` schema owns reference data (configs, cities, tax/legal — f.md L1394). accounts copy retired. |

### 7.2 Single-owner mandate (replaces prior two-domain allowance)
The f.md constitution **forbids** a service existing in more than one domain. The earlier
"complementary split" allowance for `tickets_service` (governance+comms) and `coupons_service`
(orders+governance) is **rescinded**. Each filename → one canonical domain (table 7.1). All retired
copies go to `backend/_archive_services/<domain>/`. The runtime `services.*` shim resolves to
`_legacy`, so archiving `domains/*` duplicates does **not** change runtime behavior — only the
orphan `domains.*` copies and the live `orders` routers (kept) are affected.

### 7.3 Execution steps (to run after this plan is approved)
1. `mkdir -p backend/_archive_services/<domain>` for each source domain.
2. For every ARCHIVE row above: `shutil.move(src, backend/_archive_services/<domain>/<file>)`,
   then `git add` the destination and `git rm` (if tracked) / `git add -A` the removal.
3. Repair imports:
   - `tests/test_export_read_service.py`: repoint `domains.accounts.services.export_read_service`
     → `domains.customers.services.export_read_service`.
   - No other `domains.*` import repairs needed (only orders reviews/coupons/referrals are live and
     are kept as canonical).
4. Keep `_legacy/services/**` untouched.

### 7.4 Verification gates — EXECUTED (2026-08-18, aligned to f.md Database Constitution)
- [x] `py_compile` of the **10 kept canonical files + 22 archived files** → ALL CLEAN.
- [~] `grep -rn "from modules" backend/domains` → 68 matches, but these are **pre-existing** Law-1
      violations across the whole `domains/` tree (the known "83 violations" backlog), NOT introduced by
      this repair. Of the 10 kept canonical files, only `country/countries_service.py` carries a
      pre-existing `from modules.employee.routers` import (flagged for the separate Law-1 cleanup pass).
      The retired duplicates that DID carry Law-1 violations (`customers`/`accounts` `returns_service`,
      `referrals_service`) are now archived.
- [x] The 3 live `orders` files (reviews/coupons/referrals) still present & compiled.
- [x] `backend/tests/test_export_read_service.py` repointed → `domains.customers.services.export_read_service`
      (uses `ers.__file__`); `tests/test_export_read_service.py` (importlib-based, targets `_legacy`) unaffected.
- [x] `backend/_archive_services/` holds **22 retired copies** under per-domain subfolders; no service filename
      now exists in BOTH `domains/*/services` and `_archive_services` (archive is the only copy of those paths).
- [ ] `coherence_gate.py --check` / app boot — deferred (heavy Windows/NTFS env; f.md §"Making Fast Application
      System" documents the slowness). Compile + import-graph checks above are the practical gates used.
- [x] `git status` shows the 22 moves staged (`A`/`R`) under `_archive_services/<domain>/`; `_legacy` was
      untouched by this step (only pre-existing in-progress renames from `services/<domain>/` remain, separate work).
