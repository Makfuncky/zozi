
Below is the **target structure** — the clean end‑state that the audit script's `INTENDED` model + the constitution (`01_DATABASE.md` §2.2/§2.5) converge on. It is **not** your current tree (you have that in `PROJECT_SCAFFOLDING.md`); it is the *after‑cleanup* tree, i.e. the hierarchy the script will report as **green** once every `[RED]`/`[YEL]` finding is resolved.

Two design calls are baked into this tree and are the most important thing to internalize, because they answer your "what about `database` and `security` folders?" question directly:

> **`database` and `security` are *logical domains*, not top‑level folders.** Physically they live *inside* `backend/` (`backend/{db,alembic,models}` = the database domain; `backend/{middleware,dependencies,SECURITY_CONFIG.ini}` = the security domain). The script validates them *as domains* but will never tell you to create top‑level `database/` or `security/` dirs — doing so would fragment the backend and contradict the constitution (extend, don't duplicate). The overlay diagram in §3 makes this explicit.

### Legend
- `[K]` **keep as‑is** — already correct, the script leaves it alone.
- `[N]` **new** — a folder/file that does not exist yet and must be *created* (mostly the `services/<domain>/` regrouping and the missing governance files).
- `[M]` **moved‑in** — a file that exists today in the *wrong* place and is relocated here.
- Items that must **leave** the tree are **not** shown inside it; they are listed in §2 (the "exits" list) with their destination and the rule code that catches them.

---

## 1. The TARGET tree (clean end‑state)

```text
zozi/                                                                  [repo root]
│
├── .gitignore                                                         [N]  strict root ignore (closes G0/F4/F5/NM)
├── .env.example                                                       [N]  no real secrets; .env stays gitignored
├── .aiignore  (or context-exclusion list)                             [N]  keeps generated/scratch out of AI context
├── README.md                                                          [N]  points to documents/scope/00 first
├── docker-compose.yml                                                 [N]  one-command local stack (replaces run_zozi.bat races)
├── Makefile  (or justfile)                                            [N]  dev/test/audit entrypoints
├── railway.toml                                                       [K]
│
├── backend/                                                           [K]  app code
│   ├── main.py                                                        [K]  single router-registry lives here
│   ├── lifespan.py                                                    [K]
│   ├── alembic.ini                                                    [K]
│   ├── SECURITY_CONFIG.ini                                            [K]  ← security domain (logical)
│   │
│   ├── routers/                          ← entrypoints, NO db writes    [K]
│   │   ├── __init__.py                                                [K]
│   │   ├── search.py                                                  [K]  (hybrid search per 02_SEARCH)
│   │   ├── admin_*.py  (orders, payouts, treasury, products, …)       [K]
│   │   ├── country_communications.py                                  [M]  ← moved in from backend/api/ (R1)
│   │   └── …                                                          [K]
│   │   # admin_fallback.py → inspected; removed or made a structured 404 (rule #16)
│   │
│   ├── controllers/                      ← orchestrate, NO db writes   [K]
│   │   ├── chat_controller.py            (wishlist write → service)   [M-behavioral]  (W1)
│   │   └── …                                                          [K]
│   │   # cache_utils.py → moved to utils/ ; audit_controller.py → services/audit/ (W2)
│   │
│   ├── services/                         ← the ONLY writers            [K]  (regrouped: S1)
│   │   ├── finance/                      [N]  ledger, sub_ledger, tax, invoice
│   │   ├── treasury/                     [N]  treasury_engine+service+adapter+treasurer → roles documented (ADR)
│   │   ├── hr/                           [N]  shift_*, retention, succession, travel_*
│   │   ├── logistics/                    [N]  shipping_tier, dispatch, settlement
│   │   ├── supplier/                     [N]  onboarding, health_engine
│   │   ├── ai/                           [N]  ai_search, bg_removal, ai_variant_config, ocr
│   │   ├── comms/                        [N]  transactional_email, translation, entity_chat
│   │   ├── catalog/                      [N]  advanced_filter, product draft
│   │   ├── audit/                        [N]  ← audit_controller logic lands here (W2)
│   │   └── … (flat files migrate into the matching domain over time)  [M]
│   │
│   ├── models/                           ← ONLY ORM models             [K]
│   │   ├── core.py  user.py  products.py  orders.py  payments.py      [K]
│   │   ├── employee_models.py                                          [M]  ← moved in from db/ (M1) + add __table_args__ schema
│   │   └── … (each declares __table_args__={"schema":"<context>"})    [K]
│   │
│   ├── middleware/                       ← security domain (logical)   [K]
│   │   ├── rls_interceptor.py            ← the ONE canonical enforcer  [K]  (L1: pick one)
│   │   ├── security_headers.py                                         [K]
│   │   └── …  # rls_middleware.py → aliased to or deleted (ADR)        [M/D]
│   │
│   ├── dependencies/                     ← security domain (logical)   [K]
│   ├── providers/                        ← AI/external adapters        [K]
│   ├── events/  jobs/                    ← outbox relay + crons        [K]
│   ├── utils/                            ← incl. cache_utils (moved)   [K/M]
│   │   └── config.py                     ← single settings source      [K]
│   │
│   ├── db/                               ← database domain (logical)   [K]
│   │   ├── base.py  database.py  mixins.py  schemas.py                [K]
│   │   ├── seed.py  treasury_seeder.py  create_tables.py              [K]
│   │   # employee_models.py → OUT to models/ (M1)
│   │   # migrations/ → DELETED; fold new_tables.py into Alembic (G1)
│   │
│   ├── alembic/                          ← the ONLY migrations home    [K]
│   │   ├── env.py                                                       [K]
│   │   ├── versions/                  (clean single head)              [K]
│   │   └── versions_archive/          (retired/merged heads)           [K]
│   │   # _graph_analysis.py / _diagnose_tree.py → OUT to scripts/ (A1)
│   │   # *stub* revisions → stop creating; archive (A1)
│   │
│   ├── data/                             ← config-as-data (ADR-009)     [K]
│   │   ├── zozi_variant_config.py  category_tax_profiles.py           [K]
│   │   ├── country_curated.py  curated_cities.py  vat_rates.py        [K]
│   │   └── pg_rls_policies.sql         (RLS as code)                  [K]
│   │
│   ├── tests/                            ← unit/integration/contract   [K]
│   │   └── test_database.py  (+ migration/RLS/contract tests)         [K/N]
│   │
│   ├── scripts/                          ← ops/dev scripts (one home)  [K]
│   │   ├── generate_data_dictionary.py   (+ ERD extension §6.4)       [K/N]
│   │   ├── analyze_tables.py  seed  maintenance  reconciliation       [K]
│   │   ├── repo_layout_audit.py          (the auditor)                [N]
│   │   └── backend_layout_audit.py                                     [N]
│   │   # receives the _*.py diagnostics moved out of alembic/ (A1)
│   │
│   ├── monitoring/  docs/                                              [K]
│   └── (NO zozi.db, NO *.log, NO *.db-wal here — gitignored)          [D-out]
│
├── frontend/                                                          [K]
│   ├── web_app/                                                       [K]
│   │   ├── src/  (app · components · lib · styles)                    [K]
│   │   ├── e2e/  __tests__/  public/                                  [K]
│   │   ├── playwright.config.ts                                       [K]
│   │   └── (NO countDivs*.js / fixTailwind*.js / *.bak / *.tsbuildinfo) [D-out]
│   ├── mobile_app/  (app · assets · components)                       [K]
│   └── shared/  (src/ → dist/ built & gitignored)                     [K]
│       # one lockfile per workspace only (F3)
│
├── documents/                                                         [K]
│   ├── scope/                          ← AUTHORITATIVE specs ONLY     [K]
│   │   ├── 00_SCOPE_BINDING.md                                        [K]
│   │   ├── 01_DATABASE.md              (the constitution, v2.1)       [K]
│   │   ├── 02_SEARCH.md … 10_ANALYTICS.md                             [K/N]
│   │   └── 00_REPO_STRUCTURE.md        (publishes this tree)          [N]
│   └── archive/                        ← everything else moves here   [N]
│       # CODEBASE_AUDIT / SECURITY_*_REPORT / CASH_* / DATABASE_* /
│       # GENERATED_DATA_DICTIONARY / To_Do_List … → archive or delete (F8)
│
├── infra/   (optional consolidation; otherwise keep at root)          [K/N]
│   ├── monitoring/   (prometheus · grafana · promtail · tempo)        [K]
│   └── nginx/                                                         [K]
│
├── experiments/                       ← gitignored outputs            [N]
│   ├── Working_API/   (after removing the ai_variant_config fallback) [M]
│   └── provider_test/                                                 [M]
│
├── design/                            ← logo source + zips            [N]
│   ├── zozi-logo-app/  stitch_zozi.zip  zozi-logo-app.zip             [M]
│
└── scripts/   (repo-level; distinct from backend/scripts)             [K]
    # the GHOST scripts/backend/ (own main.py + db/database.py) → DELETED or
    #   scripts/templates/ renamed so it cannot be imported (X1)
```

---

## 2. The "exits" list — what leaves the tree (the damage the script catches)

These are **not** in the target tree above. Each row is grounded in a real file from your scaffolding/codebase, tagged with the rule that flags it and where it goes.

| Rule | What (grounded) | Action | Destination / reason |
|---|---|---|---|
| **F1** | `frontend/countDivs.js`, `countDivs2.js`, `linenums.js`, `listDivs.js`, `verify-tmp.js`, the `fixTailwind*.js` patch (bakes `d:/Projects/...`) | **delete** | one‑off debug; the patch also leaks a local path (F2) |
| **F2** | any source line with `d:/Projects/10- E-COMMERCE WEBSITE/...` | **fix** | repo‑relative paths / config only |
| **F8** | `documents/` root: `CODEBASE_AUDIT.md`, `CODEBASE_FILE_INDEX.md`, `SECURITY_AUDIT_REPORT.md`, `SECURITY_FINAL_REPORT.md`, `SECURITY_IMPLEMENTATION*.md`, `ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md`, `CASH_MANAGEMENT_SYSTEM.md`, `CASH_PAYMENT_CYCLE_AUDIT.md`, `WORKFLOW_STATUS_SUMMARY.md`, `DATABASE_*.md`, `GENERATED_DATA_DICTIONARY.md`, `To_Do_List.md` … | **move** | `documents/archive/` (or delete); only `scope/` is authoritative |
| **F9** | repo root: `Working_API/`, `provider_test/`, `_trash/`, `backup_20260729/`, `image/`, `zozi-logo-app/`, `stitch_zozi.zip`, `zozi-logo-app.zip`, `login_form.yml` | **move/delete** | `experiments/` (gitignore outputs), `design/`, or delete; backups → object storage, never VCS |
| **M1** | `backend/db/employee_models.py` | **move** | `backend/models/` + add `__table_args__` schema |
| **G1** | `backend/db/migrations/` (second migrations home) | **delete** | fold `new_tables.py` into an Alembic revision |
| **A1** | `backend/alembic/_graph_analysis.py`, `_diagnose_tree.py`, `*stub*` revisions | **move/archive** | diagnostics → `backend/scripts/`; stubs → `versions_archive/` |
| **R1** | `backend/api/country_communications.py` | **move** | `backend/routers/` |
| **W1** | `chat_controller.py` doing `db.query(Wishlist).delete(); db.commit()` | **move write** | into a `wishlist_service`/`chat_service` method |
| **W2** | `audit_controller.py`, `cache_utils.py` inside `controllers/` | **move** | audit logic → `services/audit/`; cache_utils → `utils/` |
| **L1** | `rls_middleware.py` (duplicate of `rls_interceptor.py`) | **alias/delete** | keep ONE canonical RLS enforcer (ADR) |
| **X1** | `scripts/backend/` (ghost: own `main.py` + `db/database.py`) | **delete** | or `scripts/templates/` renamed so it can't import |
| **P1** | backend‑root scratch: `employee_active_tasks.py`, `employee_audit_timeline.py`, `verify_all_automation.py`, `_import_test_out.txt`, `alembic_test.json`, `backend.log`, `dev.db` | **move/delete** | scripts/ or tests/, or delete; logs/db gitignored |
| **K1/F4** | committed `*.log`, `*.db-shm`, `*.db-wal`, `.ruff_cache/`, `.tsbuildinfo`, `schema-audit-report.json`, `vision_cache.json` | **delete** | + add to `.gitignore` |
| **F3** | dual lockfiles in a workspace (`package-lock.json` + `pnpm-lock.yaml`) | **delete one** | one package manager / one lockfile per workspace |
| **F5** | `token.tmp`‑class secret files, committed `.env` | **delete** | load via env/Vault; keep only `.env.example` |

---

## 3. The "logical domain" overlay (how `database` & `security` map onto `backend/`)

The script tags findings with a *domain* even though the folders are physical. This is the mental map:

```text
LOGICAL DOMAIN          PHYSICAL HOME (inside backend/)            SCRIPT domain tag
─────────────────────   ────────────────────────────────────────   ─────────────────
database                db/ · alembic/ · models/                   "database"
security                middleware/ · dependencies/ ·              "security"
                          SECURITY_CONFIG.ini
backend (app)           routers/ · controllers/ · services/ ·      "backend"
                          providers/ · utils/ · events/ · jobs/
```

So when the auditor prints `[security] L1 two RLS modules` or `[database] M1 model outside models/`, it is pointing at files *inside* `backend/` — there is no top‑level `security/` or `database/` folder, by design.

---

## 4. Rule → what it enforces in *this* tree

| Code | Enforces (in the tree above) |
|---|---|
| **W1/W2/Q1** | `controllers/` & `routers/` contain **no** `db.commit/add/delete/query`; all writes live in `services/<domain>/` |
| **M1** | `models/` is the **only** ORM home; `db/` holds infra only |
| **R1** | `routers/` is the **only** place an `APIRouter` is instantiated |
| **G1/A1** | `alembic/` is the **only** migrations home; no diagnostics or stubs inside it |
| **S1/S2** | `services/` is grouped into `services/<domain>/`; overlapping stems (`treasury_*`, `shift_*`) are merged or ADR‑documented |
| **L1** | exactly **one** RLS enforcer in `middleware/` |
| **F1/F2** | `frontend/` package roots hold **no** scratch `.js` and **no** baked local paths |
| **F8** | `documents/scope/` is the **only** authoritative doc set; the rest is in `archive/` |
| **F9/X1** | repo root holds **no** experiments/backups/ghost‑backend |
| **G0/F4/F5/NM** | root `.gitignore` excludes logs, `*.db*`, caches, `node_modules`, `.env`, backups |
| **F3** | one lockfile per frontend workspace |

---

## 5. Order to reach this tree safely (so the move doesn't *become* drift)

1. **Add the hygiene net first:** root `.gitignore` + `.aiignore` (closes G0/F4/F5/NM/F8 at the source). Zero risk.
2. **Delete pure trash** (§2 rows F1, K1, the `_trash/`/`backup_*/`/`image/`/zips). Grep first; these have no imports.
3. **Structural moves** (M1, G1, R1, A1, the `services/` regrouping S1) — file relocations; grep every import + run the suite after each batch.
4. **Behavioral moves behind a test** (W1 controller‑write, L1 RLS consolidation) — write the test *first*, then move.
5. **Docs curation** (F8) — move the graveyard to `archive/`, publish `documents/scope/00_REPO_STRUCTURE.md` = *this* tree.
6. **Wire the auditor into CI** (`repo_layout_audit.py --json`, exit‑code gate) so any regression — a new scratch script, a controller that commits, a stray model — fails the build.

---

### The one thing to remember
This tree is the **goal the script scores against**. Today the script will light up red/yellow on exactly the §2 "exits" list; after you process that list, the same script reports green — and, because it's in CI, *stays* green. That closed loop (target tree + mechanical auditor + gate) is what actually binds the scope and stops the AI from re‑drifting the structure.

Want me to generate the matching **`documents/scope/00_REPO_STRUCTURE.md`** (this tree, human‑readable, signed) and the **strict root `.gitignore`** next, so the target is both *published* and *enforced*? Those two turn the auditor's findings into *prevented* findings.

______________________________________________________________________________
______________________________________________________________________________

I am thinking it should be like module to module in the sub-folders for example:
backend/services/admin/**
backend/controller/admin/**
---
and below also.


---


I think the **idea is excellent**, but I would **not merge it into your production repository as-is**.

The script is solving a real problem you have:

> **"AI keeps destroying the architecture because there is no mechanical enforcement of the architecture."**

That is exactly what an architectural auditor should solve.

However, after reading it carefully, I see several things I would change before making it part of ZOZI.

---

# Overall Score

| Category        |  Score |
| --------------- | -----: |
| Idea            |  10/10 |
| Architecture    | 9.8/10 |
| Scalability     |   9/10 |
| Maintainability |   8/10 |
| Long Term       | 7.5/10 |

Overall:

> **9/10**

It is very good.

But it is not what I would use as the permanent architecture governor.

---

# What I Like

The biggest improvement over typical audit scripts is this:

Instead of saying

```
Wrong
```

it says

```
Wrong

↓

Move here

↓

Because...
```

That is extremely valuable.

This part is excellent.

---

# The Domain Concept

This is also correct.

Instead of

```
backend
frontend
database
security
```

it creates logical domains.

That is exactly how enterprise architecture documentation works.

Good.

---

# The Intended Tree

This is probably the best part.

Instead of

```
Check files
```

it says

```
THIS
is
the
official
structure.
```

That is what AI needs.

---

# But here is what I would change

This is where my opinion differs.

---

# 1.

It mixes

Architecture

with

Quality

with

Security

with

Git

with

Code Style

into one giant script.

Those are different responsibilities.

Example:

```
F2
Hardcoded paths
```

is not architecture.

That is code quality.

---

```
F5
Secrets
```

is security.

---

```
F3
Lockfiles
```

is repository management.

---

```
W1
Controller writing DB
```

is architecture.

---

Those should not be in one file.

Instead

```
Architecture Auditor

Repository Auditor

Security Auditor

Code Quality Auditor

Dependency Auditor

Performance Auditor
```

Much cleaner.

---

# 2.

The INTENDED structure is hardcoded.

This becomes dangerous.

Imagine later

```
frontend/admin_panel

frontend/customer_app

frontend/supplier_app
```

Now the Python script itself must change.

That is wrong.

Instead

```
documents/scope/

repo_structure.yaml
```

should define

```
allowed folders

allowed layers

allowed files

dependencies

ownership

```

Then

Python

reads

YAML.

That makes the auditor generic.

---

# 3.

Too many Regex rules

Example

```
fixTailwind

countDivs

printLines

```

Those are project-specific.

Eventually

```
400 regex rules

```

become impossible.

Instead

```
Temporary Scripts

Developer Utilities

Migration Scripts

```

should be categories.

---

# 4.

Architecture knowledge belongs inside Scope.

Not inside Python.

The script currently knows

```
backend/controllers

backend/services

backend/models

```

That means

the architecture exists twice.

One copy

inside Python

One copy

inside documentation

Eventually

they drift.

Instead

```
00_PROJECT_SCOPE.md

↓

REPO_STRUCTURE.yaml

↓

Architecture Auditor

```

Only one source.

---

# 5.

Too much logic.

This file is almost

3000+

lines.

Eventually

nobody will understand it.

Split.

```
architecture.py

security.py

quality.py

frontend.py

database.py

reporter.py

```

Much easier.

---

# 6.

Missing dependency graph

This is probably the biggest missing feature.

Imagine

```
Controller

↓

Service

↓

Repository

↓

Database
```

Good.

Now imagine

```
Controller

↓

Database
```

Bad.

Imagine

```
Frontend

↓

Database
```

Bad.

Imagine

```
Controller

↓

Controller
```

Bad.

The auditor should detect

illegal dependency edges.

Example

```
Allowed

Frontend
↓

Router
↓

Controller
↓

Service
↓

Repository
↓

Database

```

Forbidden

```
Controller
↓

Database

```

Forbidden

```
Service
↓

Router

```

Forbidden

```
Model
↓

Router

```

This is MUCH stronger than regex.

---

# 7.

Missing feature ownership

For example

```
Orders

Inventory

Payments

Products

Reviews

Users
```

Every folder should belong to one feature.

The auditor should detect

```
Orders importing Inventory internals

```

Instead

through

```
Inventory Service

```

---

# 8.

No architecture version

Your project is going to evolve.

Need

```
Architecture Version

1.0

2.0

3.0

```

Auditor checks

```
Repository

↓

Architecture Version

↓

Migration Rules

```

Otherwise

old folders remain forever.

---

# 9.

Missing Layer Contracts

Instead of

```
controllers

services

models

```

Define

```
Controller

CAN

↓

Validate

↓

Call Service

↓

Return Response

```

Cannot

```
Database

Filesystem

Redis

MQ

SQL

```

Likewise

Service

CAN

```
Repository

Providers

Cache

```

Cannot

```
FastAPI

Request

Response

```

Now AI knows exactly what code belongs where.

---

# 10.

Missing Feature Manifest

Every feature should have

```
feature.yaml
```

Example

```
Orders

Owner

Dependencies

Database Tables

API

Permissions

Tests

Documents

```

Then

Auditor

validates everything automatically.

---

# What I would build instead

Rather than one huge audit script, I would create an **Architecture Governance System** with clear separation of responsibilities.

```
documents/
    scope/
        00_PROJECT_SCOPE.md
        01_REPOSITORY_STRUCTURE.md
        02_LAYER_RULES.md
        03_DEPENDENCY_RULES.md
        04_FEATURE_MANIFEST.md
        05_DATABASE.md
        06_FRONTEND.md
        07_SECURITY.md
```

```
governance/

    architecture_auditor.py
    dependency_auditor.py
    security_auditor.py
    repository_auditor.py
    quality_auditor.py
    documentation_auditor.py
```

```
governance/

    repo_structure.yaml
    layer_rules.yaml
    dependency_rules.yaml
    feature_manifest.yaml
```

Then the Python code becomes generic:

```
Read YAML

↓

Build Rules

↓

Scan Repository

↓

Report Violations
```

No architecture is hardcoded inside Python.

---

## My recommendation

The script you posted is a **very strong foundation**, and it addresses a real pain point you've experienced. I would not adopt it unchanged, though. I would evolve it into a governance system where:

* The **scope documents are the single source of truth**.
* The auditor **reads rules from configuration (YAML/JSON)** instead of embedding them in code.
* Architecture, security, repository hygiene, dependency analysis, and code quality are **separate auditors** that can be run independently or together.
* The most important capability to add is a **dependency graph validator**, because preventing illegal dependencies protects the architecture far more effectively than accumulating more regex-based checks.

That approach scales much better as ZOZI grows into a large codebase with hundreds of features and multiple contributors.



___________________________________________________________
___________________________________________________________
___________________________________________________________

Short verdict on your new idea first, because it's the load‑bearing question: **yes to "module per sub‑folder" — but the module name must be a *domain*, not a *role*, and that single distinction is the difference between fixing the flat‑folder disease and recreating it one level deeper.** Then I'll reconcile the 9/10 review honestly (it's mostly right; it over‑reaches in two places for *your* stage), and show the one upgrade that matters more than all the regex rules combined.

---

## 1. Your sub‑folder idea — refined (the domain‑vs‑surface trap)

You wrote `backend/services/admin/**` + `backend/controllers/admin/**`. The instinct — *stop dumping everything flat, group by module* — is exactly right and matches what the constitution already implies (`services/<domain>/`). **But `admin` is the wrong axis for the service and controller layers.** `admin` is *who uses it* (a surface/role), not *what it is* (a domain). The admin panel touches finance, orders, catalog, HR, country — so a `services/admin/` folder becomes a gravity well that swallows *every* domain the admin touches, and you're back to a 100‑file flat folder, just nested.

The proof is already in your own tree. Look at the two layers side by side — they are *already* using different axes, and the service axis is the correct one:

| Router file (surface axis = `admin_*`) | The service it actually calls (domain axis) | Correct sub‑folder |
|---|---|---|
| `routers/admin_payouts.py`, `admin_treasury.py` | `treasury_*`, `sub_ledger_service`, `cash_management_service` | `services/treasury/`, `services/finance/` |
| `routers/admin_orders.py` | order / commerce services | `services/orders/` |
| `routers/admin_products.py`, `admin_categories.py` | `advanced_filter_service`, catalog services | `services/catalog/` |
| `routers/admin_suppliers.py` | `supplier_onboarding_service`, `supplier_health_engine` | `services/supplier/` |
| `routers/admin_logistics.py` | `shipping_tier`, dispatch/settlement services | `services/logistics/` |
| `routers/admin_commission.py` | commission / ledger services | `services/finance/` |
| `routers/admin_email.py`, `admin_chat.py`, `admin_video.py` | `transactional_email_service`, chat/video services | `services/comms/` |
| `routers/admin_users.py` | auth / identity services | `services/core/` |
| `routers/admin_promotions.py` | promotion services | `services/commerce/` |

Notice: **your services are already named by domain/capability, not by `admin_`.** Forcing them under `services/admin/` would mean renaming ~110 correctly‑named services into a bucket that means nothing at the service layer. So the refined rule is:

> **Sub‑folder axis = *domain* at every layer, *except* `routers/`, where a *surface* grouping is allowed** — because routers are thin entrypoints and the surface (`admin`, `supplier`, `customer`, `public`, `webhook`) *is* their reason to exist.

```text
backend/
├── routers/                 # surface grouping OK here (thin entrypoints)
│   ├── admin/               ✅  admin_orders.py, admin_payouts.py, …  (orchestrate only)
│   ├── supplier/            ✅
│   ├── customer/            ✅
│   ├── public/              ✅  search, cart, checkout
│   └── webhooks/            ✅
├── controllers/             # domain grouping (NOT admin/)
│   ├── finance/  orders/  catalog/  supplier/  logistics/  comms/  hr/  core/
├── services/                # domain grouping (NOT admin/)  ← the only writers
│   ├── finance/  treasury/  orders/  catalog/  supplier/  logistics/  comms/  hr/  ai/  core/
└── models/                  # domain grouping, each file declares __table_args__ schema
    └── (same domains)
```

So `routers/admin/**` = ✅ (your idea, kept). `services/admin/**` / `controllers/admin/**` = ❌ → use `services/<domain>/**`. That one correction is what keeps the sub‑folder move from becoming the next flat‑folder.

---

## 2. The 9/10 review — point‑by‑point, with my honest agree / push‑back

The reviewer is **right on the substance** of almost every point. Where I push back, it's not on *correctness* but on *timing* — your real pain is "regain control now," and some of these are mature‑team ceremony that, adopted today, become the *next* set of files that rot. So: adopt the cheap structural wins immediately; defer the heavy per‑feature ceremony behind a trigger.

| # | Reviewer point | My verdict | When |
|---|---|---|---|
| 1 | Split arch / security / quality / git / style into separate auditors | **Agree.** `W1` (arch) ≠ `F5` (security) ≠ `F3` (repo) ≠ `F2` (quality). One file conflates four jobs. | **Now** — cheap, I'll split it. |
| 2 | `INTENDED` hardcoded in Python → move to `repo_structure.yaml` | **Agree, strongly.** This is your core fear (two copies of the truth → drift). The auditor must *read* the structure, not *be* it. | **Now** — highest‑leverage fix. |
| 3 | Too many project‑specific regex (`fixTailwind`, `countDivs`) | **Agree.** Replace deny‑lists with *categories* (temp scripts / dev utils / migration scripts) + a "nothing scratch at layer roots" rule. | **Now.** |
| 4 | Architecture knowledge lives in scope docs, not Python | **Agree.** YAML = machine truth; the auditor reads it; narrative/ADR *why* stays in MD by hand (you can't generate rationale). | **Now** (pairs with #2). |
| 5 | 3000+ lines → split into `architecture/security/quality/...py` | **Agree**, but keep **one entrypoint** (`governance/audit.py`) that composes them — you still run one command. | **Now.** |
| 6 | **Dependency‑graph validator** (illegal edges) | **Agree — this is the headline.** More durable than all the regex combined; catches your *actual* current bugs. | **Now** (see §4). |
| 7 | Feature ownership / no cross‑feature internal imports | **Agree in spirit**, implement *via the graph* (forbid `featureA` importing `featureB`'s internals; allow only via `featureB`'s service). | **Now**, as a graph rule, not manifests. |
| 8 | Architecture versioning (1.0→2.0 + migration rules) | **Correct but premature.** Adds a versioning tax you don't yet need. | **Defer** until a real breaking restructure happens; the seam is there. |
| 9 | Layer *contracts* (Controller CAN validate+call service+return; CANNOT touch DB/FS/Redis/SQL) | **Agree — and this *is* the dependency graph** expressed as allow/forbid matrices. | **Now** (it's #6 formalized). |
| 10 | Per‑feature `feature.yaml` manifest (owner, tables, API, perms, tests, docs) | **Correct but premature.** Across hundreds of features this is a maintenance tax that *will* rot — your entire trauma is rotting docs. | **Defer** until you have ≥2 contributors or ≥2 features colliding in one domain. |

Net: **8 of 10 are "do now," 2 are "right idea, wrong season."** The reviewer is describing the *mature* end‑state of a governed platform; you're at the *founding‑governance* stage. Both are correct for their stage — my job is the bridge, not to make you build the 10‑year version on a Tuesday.

---

## 3. The reconciled architecture (minimal‑first, with seams to grow)

```text
documents/scope/                       ← single source of truth (human + machine)
├── 00_PROJECT_SCOPE.md                ← narrative + the binding contract (App. A)
├── 01_DATABASE.md                     ← the constitution (already signed‑ready)
├── repo_structure.yaml                ← MACHINE truth: allowed folders/layers/owners   [#2,#4]
├── layer_rules.yaml                   ← MACHINE truth: allow/forbid dependency matrix  [#6,#9]
└── (02_SEARCH … 10_ANALYTICS)         ← feature scopes, cite 01, never contradict it

governance/                            ← the auditors (read the YAML, never hardcode arch)
├── audit.py                           ← ONE entrypoint: composes the sub‑auditors
├── structure_auditor.py               ← reads repo_structure.yaml  (replaces hardcoded INTENDED)
├── dependency_auditor.py              ← builds import graph, checks layer_rules.yaml  [#6]
├── security_auditor.py                ← secrets / RLS / raw‑env  (F5,F7,L1)
├── repository_auditor.py              ← gitignore / caches / lockfiles / artifacts  (F3,F4,G0,NM)
├── quality_auditor.py                 ← hardcoded paths / scratch categories  (F1,F2,P1)
└── reporter.py                        ← scorecard + DAMAGE HOTLIST + MD/JSON output
```

Two discipline rules that make this *bind* instead of *advise*:
- **Direction of truth:** YAML is the machine source; the auditor reads it; the overlapping parts of the `.md` docs are *cross‑checked* against the YAML by `structure_auditor` (so doc and code can't disagree — that's the reviewer's "documentation auditor," folded in cheaply). Pure prose (the *why*, ADRs) stays hand‑written in MD — don't try to generate rationale.
- **CI gate:** `governance/audit.py --ci` exits non‑zero on any `[RED]`. Once reds are cleared, a new illegal import or scratch file *fails the build*. That closed loop is what actually stops the AI from re‑drifting.

---

## 4. The headline upgrade — the dependency‑graph validator (and it already catches your real bugs)

This is the one I'd build before anything else, because it replaces a dozen fragile regex rules with **one structural rule** and, crucially, it flags violations you *currently have*. The layer contract, expressed as an allowed‑edge matrix (`layer_rules.yaml`):

```yaml
# governance/layer_rules.yaml  —  rows = caller layer, values = layers it MAY import
layers:
  routers:      { may_import: [controllers, services, utils, dependencies, models_readonly] }
  controllers:  { may_import: [services, utils] }            # NEVER db / models‑write / providers
  services:     { may_import: [models, providers, utils, events] }   # the only writers
  models:       { may_import: [db, utils] }                  # NEVER routers/controllers/services
  providers:    { may_import: [utils] }                      # NEVER db / models / services
forbid_symbols:
  controllers:  [db.commit, db.add, db.delete, db.merge, db.flush, session.commit]   # = your W1
  routers:      [db.commit, db.add, db.delete]
cross_domain:   forbid_internal_imports   # featureA may not import featureB's _helpers; only its service
```

How it's built (stdlib `ast`, no app import — same safety as before): parse every `.py`, record `import`/`from … import` edges as `caller_module → callee_module`, classify each module into a layer by its path (`…/controllers/finance/x.py` → `controllers`), then **reject any edge not in the matrix**. That single mechanism catches, mechanically and forever:

- **`chat_controller.py` doing `db.query(Wishlist).delete(); db.commit()`** → a `controllers → db` write edge = forbidden. (Your current W1, but now a *graph* rule, not a spot AST check.)
- **`from controllers.audit_controller import audit_log` used by other controllers *and* services** → a `services → controllers` edge = forbidden direction. This is a real one in your tree (`sub_ledger`‑style controllers import `controllers.audit_controller`); the audit helper is mis‑housed — it belongs in `services/audit/` or `utils/`, exactly the W2 finding, now proven by the graph.
- **Any future "model imports a router" or "service imports FastAPI Request"** → forbidden, caught at PR time.

That's the entropy‑reducing move the reviewer is pointing at: stop accumulating *symptom* regex (`fixTailwind`, `countDivs`); encode the *structure* once and let the graph surface every symptom of its violation.

---

## 5. Phased plan — cheap now, ceremony later

| Phase | Do | Closes | Effort |
|---|---|---|---|
| **P0** | Extract `INTENDED` → `repo_structure.yaml`; `structure_auditor` reads it. Split the monolith into the 6 sub‑auditors + 1 entrypoint. | review #1,#2,#4,#5 | small |
| **P1** | Add `dependency_auditor` + `layer_rules.yaml` (the graph + matrix above). Replace scratch deny‑lists with categories. | review #3,#6,#7,#9 + your W1/W2 | medium, **highest value** |
| **P2** | Apply the sub‑folder move with the *domain* axis (§1): `routers/admin/` ✅; `services/<domain>/`, `controllers/<domain>/`, `models/<domain>/`. Grep‑before‑move, suite after each batch. | your original idea, done safely | medium |
| **P3** | Wire `governance/audit.py --ci` as a required gate; cross‑check docs vs YAML. | binding + drift‑proof | small |
| **Defer** | Architecture versioning (#8) and per‑feature `feature.yaml` manifests (#10). | — | **trigger:** ≥2 contributors, or a real breaking restructure, or 2 features colliding in one domain |

I'm deliberately *not* handing you the 7‑YAML + per‑feature‑manifest framework today. It's the right *shape* to grow into, and P0/P1 leave the exact seams for it — but building it now, before the team/feature count justifies the upkeep, would hand you a fresh set of files to keep in sync, which is the disease you're curing.

---

## 6. How this stays *binding* (not advisory)

None of the above helps unless the AI is forced to read it. So: `00_PROJECT_SCOPE.md` Appendix A (the paste‑in contract) gains three lines — *"before any change, read `repo_structure.yaml` + `layer_rules.yaml`; place new files per the domain axis; never add a dependency edge outside the matrix; if a change needs a new edge, add it to the YAML and record an ADR, don't just write the import."* That turns the graph from a linter into a **contract the next session can't quietly violate** — which is the whole point of the last several turns.

---

### Bottom line
- Your sub‑folder idea: **adopt it**, with the correction *domain axis everywhere except `routers/`* (and your own filenames already prove that's the right split).
- The review: **8/10 do now, 2 defer** — it's a mature‑team target; you take the structural wins today and leave the seams for the rest.
- The single biggest win: **the dependency‑graph validator**, because it encodes the architecture once and catches your *current* `chat_controller` write and the mis‑housed `audit_controller` import as forbidden edges — not as one‑off regex hits.

Want me to produce, as the next concrete artifact, the **`repo_structure.yaml` + `layer_rules.yaml`** pair *and* the split `governance/` auditor with the import‑graph validator wired in (reading those YAMLs, one `audit.py` entrypoint, CI‑gate flag)? That lands P0+P1 in one shot and immediately makes your two real violations fail the build. Or, if you'd rather move the folders first, I'll generate the **domain‑axis move‑map** (`routers/admin/` + `services/<domain>/` + `controllers/<domain>/`) with the grep‑before‑you‑move checklist. Your call — graph‑first or move‑first.

---

```python

# backend\scripts\backend_layout_audit.py
"""
backend_layout_audit.py  —  READ-ONLY, repo-WIDE structural + dependency auditor.
v2.2 — incorporates the governance discussion: dependency-graph / layer-contract
validator, domain-vs-surface sub-folder rule, and YAML-driven rules (scope = single
source of truth; the embedded model below is a FROZEN fallback used only when the
YAML is absent).

LOGICAL SUB-AUDITORS (kept in one file for "drop-in-and-run"; each section maps 1:1
to a future physical split, so the seam the review asked for already exists):
  structure_auditor  -> check_intended_violations / check_backend_root_modules /
                        check_doc_and_root_allowlists / check_scratch_scripts
  dependency_auditor -> check_dependency_graph  (the headline; layer contracts)
  security_auditor   -> check_secrets_on_disk / check_raw_env_in_middleware / check_rls_cluster
  repository_auditor -> check_gitignore / check_cache_dirs / check_node_modules /
                        check_lockfiles / check_ghost_backend
  quality_auditor    -> check_hardcoded_local_paths / check_media_on_disk /
                        check_duplicate_basenames
  backend_auditor    -> check_layer_writes / check_router_outside / check_services_shape

DESIGN CALLS (do not "fix" by contradicting these)
  * "database" and "security" are LOGICAL domains inside backend/ — never top-level dirs.
  * Sub-folder axis = SURFACE in routers/ & controllers/ (admin/supplier/customer/...),
    DOMAIN in services/ & models/ (finance/orders/catalog/...).  A surface sub-package
    is fine; a basename shadow (D1) is not.
  * Read-only.  Imports no app code (stdlib + ast; pyyaml is a SOFT dependency).

SEVERITY  [RED] VIOLATION  [YEL] ADVISORY  [GRN] INFO
OUTPUT    stdout scorecard + DAMAGE HOTLIST + per-domain + INTENDED tree;
          ephemeral <repo>/REPO_LAYOUT_AUDIT_REPORT.md (gitignore it; NOT in scope/);
          optional --json for CI.
EXIT      1 if any [RED] (CI gate); --no-fail to always exit 0.

USAGE
  python backend/scripts/backend_layout_audit.py --no-fail --show-intended
  python backend/scripts/backend_layout_audit.py --rules-dir documents/scope
  python backend/scripts/backend_layout_audit.py --json out/findings.json
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ============================================================================
# 1. EMBEDDED FALLBACK RULES  (frozen at v2.2 — authoritative edits go in the YAML)
#    Used ONLY when documents/scope/{repo_structure,layer_rules}.yaml are missing.
#    When the YAML is present it overrides these (see load_rules).
# ============================================================================
IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", "htmlcov", ".next", ".expo",
    ".kotlin", "gradle", "android", "ios", ".idea", ".vscode",
    "test-results", ".playwright-artifacts-0", "playwright-out",
    "static-tmp", ".web-build-test", "artifacts", "uploads", ".turbo",
}
CACHE_DIR_NAMES = {
    ".ruff_cache", ".mypy_cache", ".pytest_cache", ".next", ".expo", "dist",
    "build", "coverage", "htmlcov", ".turbo", "web-dist",
    ".playwright-artifacts-0", "test-results",
}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yml", ".yaml",
            ".md", ".ini", ".toml", ".css", ".html", ".sh", ".bat", ".ps1", ".cjs", ".mjs"}
SOURCE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".bat", ".ps1"}  # F2 scans these only
MAX_READ_BYTES = 2_000_000

# Scratch detection = categories, not a 400-regex treadmill.
# PHRASES = specific substrings (safe to match anywhere).
EMBEDDED_SCRATCH_PHRASES = [
    "countdivs", "stackdivs", "printlines", "linenums", "fixtailwind",
    "patch-vars", "patch_vars", "verify-tmp", "verify_tmp", "impmain",
    "client_tmp", "reset_tmp",
]
# BROAD tokens = applied to backend-root .py only (a one-off script name segment).
EMBEDDED_SCRATCH_TOKENS = [
    "tmp", "temp", "scratch", "debug", "test", "check", "write", "list",
    "reset", "verify", "run", "script", "probe",
]
# For the cross-tree .js/.cjs scan we NARROW to these (avoid flagging ops scripts
# like scripts/validation/check_db.py): phrases + a tiny safe token subset.
_SCRIPTS_SAFE_TOKENS = {"tmp", "temp", "scratch", "debug"}

# backend-root .py that are LEGIT (everything else .py at backend/ root is flagged).
BACKEND_ROOT_ALLOW = {"__init__.py", "main.py", "lifespan.py", "run_server.py", "start_server.py"}
# .md allowed at repo root; everything else .md / any .txt at root -> F9.
EMBEDDED_ALLOW_ROOT_MD = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md",
                          "SECURITY.md", "LICENSE.md", "LICENSE"}
# entries allowed at documents/ root; everything else -> F8 (scope/ is authoritative).
EMBEDDED_ALLOW_DOCS_ROOT = {"scope", "archive", "README.md", "DOCUMENTATION_INDEX.md", "INDEX.md"}

# Embedded intended-structure forbidden patterns (regex).  NOTE: .py at backend root,
# scratch .js, and documents/root .md/.txt are NOT here — they are handled by the
# allow-list / category functions (single principled rule each).
EMBEDDED_FORBIDDEN_ROOT = {
    "backend": [r".*\.(log|db|db-shm|db-wal)$", r"^token\.tmp$", r"^.*\.(json|txt)$"],
    "backend/alembic": [r"^_.*\.py$"],
    "frontend": [r".*\.(log|tsbuildinfo)$"],
    "frontend/web_app": [r".*\.bak$", r"\.tsbuildinfo$", r"^build_final.*$",
                         r"^_audit_.*\.cjs$", r".*\.(png|jpe?g)$"],
    ".": [r"^Working_API$", r"^provider_test$", r"^_trash$", r"^backup_\d+",
          r"^image$", r"^zozi-logo-app$", r".*\.zip$", r"^login_form\.yml$",
          r"^zozi\.db(-shm|-wal)?$", r"^dev\.db$", r"^.*\.log$"],
    "documents": [],  # owned by the allow-list function
}
EMBEDDED_FORBIDDEN_ANY = {
    "backend": [r"/db/migrations/", r"(^|/)employee_models\.py$"],
    "backend/db": [r"/migrations/", r"(^|/)employee_models\.py$"],
    "backend/alembic": [r"/versions/.*stub.*\.py$"],
}

# Embedded layer contract (overridden by layer_rules.yaml when present).
EMBEDDED_FORBIDDEN_EDGES = {
    "controllers": ["db.database", "db.create_tables", "db.init_db"],
    "services": ["routers", "controllers"],
    "models": ["routers", "controllers", "services"],
    "providers": ["routers", "controllers", "services"],
}
# Controllers that actually hold service/util logic (grounded: audit_log/AuditAction,
# _order_holds_inventory/apply_order_status_change, cache_utils are imported across layers).
EMBEDDED_MIS_HOUSED_CONTROLLERS = ["audit_controller", "payments_controller", "cache_utils"]

# --- content-scan patterns (security / quality) ---
WRITE_VERBS = {"add", "commit", "delete", "merge", "flush", "refresh"}
READ_VERBS = {"query"}
KNOWN_WRITER_CONTROLLERS = {"audit_controller.py"}  # W2: relocate, not a logic bug
SECRET_FILE_PATTERNS = [
    re.compile(r"(^|/)token\.tmp$"),
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/).*\.(key|pem|p12|pfx|secret)$", re.I),
    re.compile(r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$"),
    re.compile(r"(^|/).*credentials.*\.(json|ya?ml)$", re.I),
]
ENV_SECRET_KEYS = re.compile(
    r"""os\.environ\.(?:get\(\s*|[\[])\s*["']"""
    r"""(APP_ENV|SECRET_KEY|JWT_SECRET|DATABASE_URL|DB_PASSWORD|REDIS_URL|"""
    r"""HF_API_TOKEN|STRIPE_SECRET|AWS_SECRET|ENCRYPTION_KEY|TOKEN|PASSWORD)""", re.I)
LOCAL_PATH = re.compile(
    r"""[A-Za-z]:[\\/](?:Users|Projects|home|Documents|Desktop|recovery_recuva)[\\/]"""
    r"""|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/""")
MEDIA_DISK_WRITE = re.compile(r"""open\(\s*(?:f?["'][^"']*uploads/|.*upload_dir)""")
MEDIA_DISK_URL = re.compile(r"""image_url\s*=\s*f?["']\{?\s*upload_dir""")
DUP_IGNORE_BASENAMES = {"__init__", "conftest"}
ARTIFACT_EXTS = {".log", ".db-shm", ".db-wal", ".tsbuildinfo"}
ARTIFACT_NAMES = {"schema-audit-report.json", "vision_cache.json", "alembic_test.json",
                  "_import_test_out.txt", "playwright-results.txt", "backend.log",
                  "server_stderr.log", "server_stdout.log", "run_log.txt"}
LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"}
# canonical home, for D1 "intended" messages on the known shadows
CANONICAL_HOME = {
    "database.py": "db/database.py", "schemas.py": "db/schemas.py",
    "config.py": "utils/config.py", "auth.py": "utils/auth.py",
    "email_service.py": "utils/email_service.py",
}

# ============================================================================
# 2. DATA MODEL
# ============================================================================
RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"
SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}
SEV_TAG = {RED: "[RED]", YEL: "[YEL]", GRN: "[GRN]"}
HOTLIST_RULES = {"W1", "M1", "R1", "G1", "X1", "F1", "F2", "F5", "F6", "F8", "F9",
                 "G0", "DG", "W3"}
RULE_MEANING = {
    "W1": "controller/router writes to DB (must be a service)",
    "W2": "misnamed writer-controller -> relocate to services/",
    "W3": "imports a mis-housed controller (logic belongs in services/utils)",
    "W4": "controller imports another controller (shared logic -> service/util)",
    "Q1": "controller/router reads via db.query (delegate)",
    "M1": "ORM model outside models/ package",
    "R1": "APIRouter instantiated outside routers/",
    "G1": "second migrations home / dual schema-creator",
    "X1": "ghost/duplicate backend skeleton",
    "D1": "duplicate module basename within a domain (import-shadow)",
    "D2": "duplicate module basename across top dirs",
    "S1": "services/ is flat (needs domain sub-packages)",
    "S2": "overlapping service stems (ownership ambiguity)",
    "L1": "multiple RLS enforcers (fail-open risk)",
    "A1": "alembic diagnostics / stubs / fractured heads",
    "P1": "scratch script at backend root (delete / scripts/)",
    "P2": "controller file outside controllers/",
    "P3": "module at backend root (belongs in a layer package)",
    "H1": "sys.path.insert/append (import-resolution footgun)",
    "F1": "scratch/debug script (delete; ops scripts -> scripts/maintenance|validation)",
    "F2": "hardcoded developer-local absolute path in source",
    "F3": "dual/triple lockfiles (drift)",
    "F4": "committed cache/build/artifact present (bloat)",
    "F5": "secret material on disk (security)",
    "F6": "media written to / served from local disk (P0-A scale killer)",
    "F7": "raw os.environ secret read in middleware (use settings)",
    "F8": "documents/ root entry outside allow-list (only scope/ is authoritative)",
    "F9": "repo-root note outside allow-list / banned dir (-> documents/ or experiments/)",
    "G0": "missing/weak root .gitignore (root cause of committed artifacts)",
    "DG": "forbidden dependency-graph edge (layer contract violated)",
    "NM": "node_modules present (confirm gitignored; #1 context-bloat source)",
    "I1": "structure summary",
    "I2": "rules source (yaml vs embedded fallback)",
}


@dataclass
class Finding:
    sev: str; code: str; domain: str; path: str; message: str
    intended: str = ""; line: int | None = None
    def loc(self) -> str:
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    def add(self, sev, code, domain, path, message, intended="", line=None):
        self.findings.append(Finding(sev, code, domain, path, message, intended, line))
        self.counters[code] += 1


# ============================================================================
# 3. RULE LOADING  (YAML preferred -> JSON -> embedded fallback)
# ============================================================================
def _compile(patterns):
    return [re.compile(p) for p in (patterns or [])]


def _merge_dict_of_lists(base, overlay):
    out = {k: list(v) for k, v in base.items()}
    for k, v in (overlay or {}).items():
        out[k] = list(v)  # yaml key fully replaces embedded for that key
    return out


def load_rules(repo: Path, rules_dir: Path | None) -> dict:
    """Return the effective rule-set + a from_yaml flag."""
    eff = {
        "forbidden_root": _merge_dict_of_lists(EMBEDDED_FORBIDDEN_ROOT, {}),
        "forbidden_any": _merge_dict_of_lists(EMBEDDED_FORBIDDEN_ANY, {}),
        "allow_root_md": set(EMBEDDED_ALLOW_ROOT_MD),
        "allow_docs_root": set(EMBEDDED_ALLOW_DOCS_ROOT),
        "scratch_phrases": list(EMBEDDED_SCRATCH_PHRASES),
        "scratch_tokens": list(EMBEDDED_SCRATCH_TOKENS),
        "forbidden_edges": {k: list(v) for k, v in EMBEDDED_FORBIDDEN_EDGES.items()},
        "mis_housed_controllers": set(EMBEDDED_MIS_HOUSED_CONTROLLERS),
        "forbidden_controller_to_controller": True,
        "from_yaml": False,
    }
    candidates = []
    if rules_dir:
        candidates.append(Path(rules_dir))
    candidates += [repo / "documents" / "scope", repo / "governance"]
    struct = layer = None
    for d in candidates:
        if not d or not d.is_dir():
            continue
        struct = _read_cfg(d / "repo_structure.yaml") or _read_cfg(d / "repo_structure.json")
        layer = _read_cfg(d / "layer_rules.yaml") or _read_cfg(d / "layer_rules.json")
        if struct or layer:
            eff["from_yaml"] = True
            break
    if struct:
        eff["forbidden_root"] = _merge_dict_of_lists(eff["forbidden_root"], struct.get("forbidden_root"))
        eff["forbidden_any"] = _merge_dict_of_lists(eff["forbidden_any"], struct.get("forbidden_any"))
        if struct.get("allow_root_md"):
            eff["allow_root_md"] = set(struct["allow_root_md"])
        if struct.get("allow_docs_root"):
            eff["allow_docs_root"] = set(struct["allow_docs_root"])
        if struct.get("scratch_phrases"):
            eff["scratch_phrases"] = [str(x).lower() for x in struct["scratch_phrases"]]
        if struct.get("scratch_tokens"):
            eff["scratch_tokens"] = [str(x).lower() for x in struct["scratch_tokens"]]
    if layer:
        if layer.get("forbidden_edges"):
            eff["forbidden_edges"] = {k: list(v) for k, v in layer["forbidden_edges"].items()}
        if layer.get("mis_housed_controllers"):
            eff["mis_housed_controllers"] = set(layer["mis_housed_controllers"])
        if "forbidden_controller_to_controller" in layer:
            eff["forbidden_controller_to_controller"] = bool(layer["forbidden_controller_to_controller"])
    # precompile regexes
    eff["forbidden_root_c"] = {k: _compile(v) for k, v in eff["forbidden_root"].items()}
    eff["forbidden_any_c"] = {k: _compile(v) for k, v in eff["forbidden_any"].items()}
    return eff


def _read_cfg(path: Path):
    if not path or not path.exists():
        return None
    txt = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            return json.loads(txt)
        except Exception:
            return None
    try:
        import yaml  # soft dependency (alembic/monitoring usually bring it)
        return yaml.safe_load(txt) or {}
    except Exception:
        return None  # pyyaml missing -> caller falls back to embedded


# ============================================================================
# 4. HELPERS
# ============================================================================
def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def walk_dirs(root: Path):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError):
            continue
        for e in entries:
            if e.is_dir() and e.name not in IGNORE_DIRS:
                stack.append(e)
        yield d, entries


def iter_text_files(root: Path) -> Iterable[Path]:
    for d, entries in walk_dirs(root):
        for e in entries:
            if e.is_file() and e.suffix.lower() in TEXT_EXT:
                try:
                    if e.stat().st_size <= MAX_READ_BYTES:
                        yield e
                except OSError:
                    pass


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def parse_safe(p: Path) -> ast.Module | None:
    t = read_text(p)
    if t is None:
        return None
    try:
        return ast.parse(t)
    except (SyntaxError, ValueError):
        return None


def in_parts(path: Path, *names: str) -> bool:
    parts = {x.lower() for x in path.parts}
    return any(n.lower() in parts for n in names)


def domain_of(path_rel: str) -> str:
    parts = [p.lower() for p in Path(path_rel).parts]
    base = parts[-1] if parts else ""
    if "alembic" in parts or "db" in parts or "models" in parts:
        return "database"
    if "middleware" in parts or "dependencies" in parts or base == "security_config.ini":
        return "security"
    if parts and parts[0] == "frontend":
        return "frontend"
    if parts and parts[0] == "documents":
        return "docs"
    if parts and parts[0] in ("monitoring", "nginx", "infra"):
        return "infra"
    if parts and parts[0] == "backend":
        return "backend"
    return "repo"


def is_scratch_name(stem: str, eff: dict, broad: bool) -> bool:
    low = stem.lower()
    for ph in eff["scratch_phrases"]:
        if ph and ph in low:
            return True
    tokens = {t.lower() for t in re.split(r"[-_.]+", low) if t}
    token_set = eff["scratch_tokens"] if broad else _SCRIPTS_SAFE_TOKENS
    return bool(tokens & token_set)


def layer_of(path_rel: str) -> str:
    parts = [p.lower() for p in Path(path_rel).parts]
    if not parts or parts[0] != "backend":
        return ""
    if len(parts) < 2:
        return ""
    return parts[1]  # routers / controllers / services / models / providers / utils / db / ...


# ============================================================================
# 5. CHECKS
# ============================================================================
def check_intended_violations(repo: Path, rep: Report, eff: dict) -> None:
    for key, frx in eff["forbidden_root_c"].items():
        base = repo if key == "." else repo / key
        if not base.exists() or not frx:
            continue
        dom = "repo" if key == "." else domain_of(key)
        try:
            children = list(base.iterdir())
        except OSError:
            children = []
        for c in children:
            for rx in frx:
                if rx.search(c.name):
                    sev = RED if c.suffix in (".db",) else YEL
                    rep.add(sev, _code_for_root(key, c), dom, rel(c, repo),
                            f"must not sit at {key or 'repo root'} (damages structure/scale)",
                            intended=_intended_for(key, c))
                    break
    for key, fax in eff["forbidden_any_c"].items():
        base = repo if key == "." else repo / key
        if not base.exists() or not fax:
            continue
        for f in iter_text_files(base):
            rp = rel(f, repo).replace("\\", "/")
            for rx in fax:
                if rx.search("/" + rp) or rx.search(rp):
                    rep.add(YEL, _code_for_any(f), domain_of(rp), rel(f, repo),
                            f"forbidden under {key}", intended=_intended_for_any(f))
                    break


def _code_for_root(key: str, c: Path) -> str:
    if key == "." and (c.name.startswith("backup_") or c.name in
                       {"Working_API", "provider_test", "_trash", "image", "zozi-logo-app"}
                       or c.suffix == ".zip"):
        return "F9"
    if c.name in ARTIFACT_NAMES or c.suffix in ARTIFACT_EXTS or c.suffix in (".db",):
        return "F4"
    if key == "backend/alembic":
        return "A1"
    return "F4"


def _code_for_any(f: Path) -> str:
    if "migrations" in f.parts and "alembic" not in f.parts:
        return "G1"
    if f.name == "employee_models.py":
        return "M1"
    if "stub" in f.name:
        return "A1"
    return "G1"


def _intended_for(key: str, c: Path) -> str:
    if c.name.startswith("backup_") or c.suffix == ".zip":
        return "remove from VCS (backups -> object storage; design -> design/)"
    if c.name in {"Working_API", "provider_test"}:
        return "move to experiments/ and gitignore outputs (remove Working_API fallback first)"
    if c.name == "_trash":
        return "delete from repo"
    if c.name in ARTIFACT_NAMES or c.suffix in ARTIFACT_EXTS or c.suffix in (".db", ".db-shm", ".db-wal"):
        return "delete + add to .gitignore"
    return "relocate per scope/repo_structure.yaml or delete"


def _intended_for_any(f: Path) -> str:
    if "migrations" in f.parts and "alembic" not in f.parts:
        return "fold into an Alembic revision or delete (no second migrations home)"
    if f.name == "employee_models.py":
        return "move into backend/models/ and add __table_args__ schema"
    return "relocate per scope/repo_structure.yaml"


def check_backend_root_modules(repo: Path, rep: Report, eff: dict) -> None:
    """P1 scratch / P3 misplaced .py at backend/ root (allow-list based)."""
    be = repo / "backend"
    if not be.exists():
        return
    for c in sorted(be.iterdir()):
        if not c.is_file() or c.suffix != ".py":
            continue
        if c.name in BACKEND_ROOT_ALLOW:
            continue
        rp = rel(c, repo)
        if is_scratch_name(c.stem, eff, broad=True):
            rep.add(YEL, "P1", "backend", rp,
                    "scratch/one-off script at backend root",
                    intended="delete, or move to scripts/ (ops) / tests/")
        else:
            home = CANONICAL_HOME.get(c.name, "a layer package (routers/controllers/services/utils/db)")
            rep.add(YEL, "P3", "backend", rp,
                    f"module at backend root (shadows the canonical home or is mis-placed)",
                    intended=f"move to {home}; backend/ root holds only main/lifespan/run_server")


def check_scratch_scripts(repo: Path, rep: Report, eff: dict) -> None:
    """F1 scratch/debug .js/.cjs/.mjs under frontend/ + scripts/ + repo root."""
    roots = [repo / "frontend", repo / "scripts", repo]
    seen: set[str] = set()
    for r in roots:
        if not r.exists():
            continue
        for f in iter_text_files(r):
            if f.suffix.lower() not in (".js", ".cjs", ".mjs"):
                continue
            rp = rel(f, repo)
            if rp in seen:
                continue
            if is_scratch_name(f.stem, eff, broad=False):
                seen.add(rp)
                rep.add(YEL, "F1", domain_of(rp), rp,
                        "scratch/debug script (one-off; not an ops/maintenance script)",
                        intended="delete; ops scripts live in scripts/maintenance or scripts/validation")


def check_doc_and_root_allowlists(repo: Path, rep: Report, eff: dict) -> None:
    """F8 (documents/) + F9 (repo root) via ALLOW-lists (one rule each)."""
    docs = repo / "documents"
    if docs.exists():
        allow = eff["allow_docs_root"]
        for c in sorted(docs.iterdir()):
            if c.name in allow:
                continue
            kind = "dir" if c.is_dir() else "file"
            rep.add(YEL, "F8", "docs", rel(c, repo),
                    f"{kind} at documents/ root outside the allow-list",
                    intended="documents/scope/ is authoritative; move this to documents/archive/ (or delete)")
    allow_md = eff["allow_root_md"]
    for c in sorted(repo.iterdir()):
        if not c.is_file():
            continue
        if c.suffix == ".txt":
            rep.add(YEL, "F9", "repo", rel(c, repo),
                    "design/plan note (.txt) at repo root",
                    intended="move to documents/ (spec) or experiments/ (scratch); never commit at root")
        elif c.suffix == ".md" and c.name not in allow_md:
            rep.add(YEL, "F9", "repo", rel(c, repo),
                    "doc at repo root outside the allow-list",
                    intended="move to documents/scope/ (authoritative) or documents/archive/")


def check_layer_writes(repo: Path, rep: Report) -> None:
    """W1 / W2 / Q1: presentation layer must not hold a write session (AST)."""
    for layer in ("controllers", "routers"):
        d = repo / "backend" / layer
        if not d.exists():
            continue
        for f in iter_text_files(d):
            if f.suffix != ".py" or in_parts(f, "tests"):
                continue
            tree = parse_safe(f)
            if tree is None:
                continue
            r = rel(f, repo)
            known = f.name in KNOWN_WRITER_CONTROLLERS
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                v = node.func.attr
                if v in WRITE_VERBS:
                    if known:
                        rep.add(YEL, "W2", "backend", r,
                                f"misnamed service-helper writes here (.{v}()); relocate file to services/",
                                intended="services/<domain>/", line=node.lineno)
                    else:
                        rep.add(RED, "W1", "backend", r,
                                f"{layer}/ must not call session write .{v}(); move write into a service",
                                intended="a services/<domain>/*_service.py method", line=node.lineno)
                elif v in READ_VERBS:
                    rep.add(YEL, "Q1", "backend", r,
                            f"{layer}/ reads via .{v}(); delegate to a service",
                            intended="service layer", line=node.lineno)


def check_router_outside(repo: Path, rep: Report) -> None:
    for f in iter_text_files(repo / "backend"):
        if f.suffix != ".py" or in_parts(f, "routers", "tests", "alembic"):
            continue
        tree = parse_safe(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
                if nm == "APIRouter":
                    rep.add(RED, "R1", "backend", rel(f, repo),
                            "APIRouter outside routers/ -> endpoint mis-registered/shadowed",
                            intended="backend/routers/", line=node.lineno)
                    break


def check_dependency_graph(repo: Path, rep: Report, eff: dict) -> None:
    """DG / W3 / W4: enforce the layer contract via the import graph (stdlib ast)."""
    be = repo / "backend"
    if not be.exists():
        return
    edges = eff["forbidden_edges"]
    mis = eff["mis_housed_controllers"]
    forbid_cc = eff["forbidden_controller_to_controller"]
    for f in iter_text_files(be):
        if f.suffix != ".py" or in_parts(f, "tests", "test"):
            continue
        caller = layer_of(rel(f, be.parent))
        if caller not in edges and not (forbid_cc and caller == "controllers"):
            # still need W3/W4 for any layer that imports controllers.*
            pass
        tree = parse_safe(f)
        if tree is None:
            continue
        rp = rel(f, repo)
        pkg = list(Path(rel(f, be)).parts)[:-1]  # package dirs of this file under backend/
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom):
                mod = _resolve_import(node.level, node.module, pkg)
            elif isinstance(node, ast.Import):
                mod = node.names[0].name if node.names else None
            if not mod:
                continue
            leaf = mod.rsplit(".", 1)[-1]
            # W3: importing a mis-housed controller (most actionable)
            if leaf in mis and mod.startswith("controllers"):
                rep.add(RED, "W3", "backend", rp,
                        f"imports mis-housed controller '{mod}' (it holds service/util logic)",
                        intended="import from its services/<domain>/ (or utils/) home once relocated",
                        line=node.lineno)
                continue
            # W4: controller -> controller internals
            if forbid_cc and caller == "controllers" and mod.startswith("controllers.") and mod != "controllers":
                rep.add(YEL, "W4", "backend", rp,
                        f"controller imports another controller ('{mod}')",
                        intended="extract the shared logic into a service or util; controllers stay thin",
                        line=node.lineno)
                continue
            # DG: forbidden edge for this caller layer
            for pref in edges.get(caller, []):
                if mod == pref or mod.startswith(pref + "."):
                    rep.add(RED, "DG", "backend", rp,
                            f"forbidden dependency edge: {caller} -> {mod}",
                            intended=f"layer contract: {caller} may not depend on {pref}; route via services/",
                            line=node.lineno)
                    break


def _resolve_import(level: int, module: str | None, pkg: list[str]) -> str | None:
    if level == 0:
        return module
    try:
        base = pkg[: max(0, len(pkg) - (level - 1))] if level >= 1 else pkg
        if level > len(pkg) + 1:
            return None
    except Exception:
        return None
    parts = base + ([module] if module else [])
    return ".".join(parts) if parts else None


def check_ghost_backend(repo: Path, rep: Report) -> None:
    for cand in ("scripts/backend", "Working_API"):
        c = repo / cand
        if (c / "main.py").exists() or (c / "db" / "database.py").exists():
            rep.add(RED, "X1", "repo", cand,
                    "ghost backend (own main.py / db/database.py) -> two main.py & two database.py",
                    intended="delete, or scripts/templates/ renamed so it can't import")


def check_duplicate_basenames(repo: Path, rep: Report) -> None:
    by: dict[str, list[str]] = defaultdict(list)
    for f in iter_text_files(repo / "backend"):
        if f.suffix != ".py" or f.stem in DUP_IGNORE_BASENAMES:
            continue
        by[f.name].append(rel(f, repo))
    for name, paths in by.items():
        dirs = {Path(p).parent for p in paths}
        if len(dirs) > 1:
            home = CANONICAL_HOME.get(name, "one canonical package")
            rep.add(YEL, "D1", "backend", name,
                    f"same module name in {len(dirs)} dirs (import-shadow): " + ", ".join(paths[:5]),
                    intended=f"keep the canonical copy ({home}); delete the shadows")
    cross: dict[str, list[str]] = defaultdict(list)
    for top in ("backend", "monitoring", "scripts"):
        d = repo / top
        if not d.exists():
            continue
        for f in iter_text_files(d):
            if f.suffix != ".py" or f.stem in DUP_IGNORE_BASENAMES:
                continue
            cross[f.name].append(rel(f, repo))
    for name, paths in cross.items():
        tops = {Path(p).parts[0] for p in paths}
        if len(tops) > 1:
            rep.add(YEL, "D2", "repo", name,
                    f"same module name across {sorted(tops)} (duplicated detector / ghost backend): "
                    + ", ".join(paths[:5]),
                    intended="keep ONE owner; the other is drift")


def check_services_shape(repo: Path, rep: Report) -> None:
    svc = repo / "backend" / "services"
    if not svc.exists():
        return
    direct = [p for p in svc.glob("*.py") if p.name != "__init__.py"]
    subpkgs = [p.name for p in svc.iterdir() if p.is_dir() and (p / "__init__.py").exists()]
    if not subpkgs and len(direct) > 30:
        rep.add(YEL, "S1", "backend", rel(svc, repo),
                f"services/ FLAT ({len(direct)} files, 0 domain sub-packages)",
                intended="services/<domain>/ per bounded contexts (finance/orders/catalog/...)")
    stems = sorted({p.stem for p in direct})
    used: set[str] = set()
    for i, a in enumerate(stems):
        if a in used:
            continue
        grp = [a]
        for b in stems[i + 1:]:
            if b in used:
                continue
            n = 0
            while n < len(a) and n < len(b) and a[n] == b[n]:
                n += 1
            if n >= 6:
                grp.append(b)
        if len(grp) >= 2:
            used.update(grp)
            rep.add(YEL, "S2", "backend", rel(svc, repo),
                    f"overlapping stems '{a[:6].rstrip('_')}*' ({len(grp)}) -> ambiguous ownership",
                    intended="merge or document each role in an ADR: " + ", ".join(grp[:6]))


def check_rls_cluster(repo: Path, rep: Report) -> None:
    hits = [rel(f, repo) for f in iter_text_files(repo / "backend")
            if f.suffix == ".py" and (f.stem.startswith("rls_") or f.stem == "country_rls")]
    if len(hits) >= 2:
        rep.add(YEL, "L1", "security", "middleware/ + dependencies/",
                f"{len(hits)} RLS modules -> two enforcers = fail-open risk",
                intended="pick ONE canonical enforcer (ADR); alias/delete rest: " + ", ".join(hits))


def check_secrets_on_disk(repo: Path, rep: Report) -> None:
    for d, entries in walk_dirs(repo):
        for e in entries:
            if not e.is_file():
                continue
            rp = rel(e, repo)
            for rx in SECRET_FILE_PATTERNS:
                if rx.search("/" + rp.replace("\\", "/")) or rx.search(rp.replace("\\", "/")):
                    rep.add(RED, "F5", "security", rp, "secret/credential material on disk",
                            intended="remove from VCS; load via env/Vault; keep only .env.example")
                    break


def check_raw_env_in_middleware(repo: Path, rep: Report) -> None:
    mw = repo / "backend" / "middleware"
    if not mw.exists():
        return
    for f in iter_text_files(mw):
        if f.suffix != ".py":
            continue
        t = read_text(f)
        if not t:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if ENV_SECRET_KEYS.search(line):
                rep.add(YEL, "F7", "security", rel(f, repo),
                        "raw os.environ secret read in middleware",
                        intended="read via utils/config settings (single source of truth)", line=i)
                break


def check_hardcoded_local_paths(repo: Path, rep: Report) -> None:
    for top in ("backend", "frontend"):
        d = repo / top
        if not d.exists():
            continue
        for f in iter_text_files(d):
            if f.suffix.lower() not in SOURCE_EXT:
                continue
            t = read_text(f)
            if not t:
                continue
            for i, line in enumerate(t.splitlines(), 1):
                if LOCAL_PATH.search(line):
                    rep.add(YEL, "F2", domain_of(rel(f, repo)), rel(f, repo),
                            "hardcoded developer-local absolute path (portability + leak)",
                            intended="use repo-relative paths / config; never commit C:/d:/F:/home paths",
                            line=i)
                    break


def check_media_on_disk(repo: Path, rep: Report) -> None:
    for layer in ("controllers", "services", "routers"):
        d = repo / "backend" / layer
        if not d.exists():
            continue
        for f in iter_text_files(d):
            if f.suffix != ".py":
                continue
            t = read_text(f)
            if not t:
                continue
            for i, line in enumerate(t.splitlines(), 1):
                if MEDIA_DISK_WRITE.search(line) or MEDIA_DISK_URL.search(line):
                    rep.add(YEL, "F6", "backend", rel(f, repo),
                            "media written to / referenced from local disk",
                            intended="storage abstraction -> object storage + CDN (ADR-010); DB stores metadata only",
                            line=i)
                    break


def check_lockfiles(repo: Path, rep: Report) -> None:
    for top in ("frontend", "frontend/web_app", "frontend/mobile_app", "frontend/shared", "."):
        d = repo if top == "." else repo / top
        if not d.exists():
            continue
        present = [lf for lf in LOCKFILES if (d / lf).exists()]
        if len(present) >= 2:
            rep.add(YEL, "F3", "repo" if top == "." else "frontend", rel(d, repo),
                    f"multiple lockfiles ({', '.join(present)}) -> install drift",
                    intended="keep ONE package manager / one lockfile per workspace")


def check_cache_dirs(repo: Path, rep: Report) -> None:
    seen: set[str] = set()
    for d, entries in walk_dirs(repo):
        for e in entries:
            if e.is_dir() and e.name in CACHE_DIR_NAMES and e.name not in seen:
                seen.add(e.name)
                rep.add(YEL, "F4", domain_of(rel(e, repo)), rel(e, repo),
                        f"cache/build dir '{e.name}' present in tree (bloats repo & context)",
                        intended="delete + ensure in .gitignore")


def check_node_modules(repo: Path, rep: Report) -> None:
    for d, entries in walk_dirs(repo):
        for e in entries:
            if e.is_dir() and e.name == "node_modules":
                rep.add(GRN, "NM", domain_of(rel(e, repo)), rel(e, repo),
                        "node_modules present (local-only is fine)",
                        intended="CONFIRM gitignored; a COMMITTED node_modules is the #1 bloat source")


def check_gitignore(repo: Path, rep: Report) -> None:
    gi = repo / ".gitignore"
    if not gi.exists():
        rep.add(RED, "G0", "repo", ".gitignore",
                "no root .gitignore -> artifacts/caches/secrets get committed",
                intended="add strict root .gitignore (logs, *.db*, caches, node_modules, .env, backups)")
        return
    t = read_text(gi) or ""
    missing = [m for m in ["*.db", "node_modules", "__pycache__", ".env", "*.log"] if m not in t]
    if missing:
        rep.add(YEL, "G0", "repo", ".gitignore",
                f".gitignore missing key patterns: {', '.join(missing)}",
                intended="add the missing patterns so artifacts stop being committed")


def collect_info(repo: Path, rep: Report, eff: dict) -> None:
    def n(sub):
        d = repo / "backend" / sub
        return sum(1 for x in d.rglob("*.py") if x.is_file()) if d.exists() else 0
    rep.add(GRN, "I1", "repo", rel(repo, repo),
            f"backend models={n('models')} routers={n('routers')} controllers={n('controllers')} "
            f"services={n('services')} middleware={n('middleware')}")
    src = "scope YAML (single source of truth)" if eff["from_yaml"] \
        else "EMBEDDED FALLBACK (create documents/scope/*.yaml to make scope authoritative)"
    rep.add(GRN, "I2", "repo", "documents/scope/", f"rules loaded from: {src}")


# ============================================================================
# 6. RENDER
# ============================================================================
def render_intended_tree() -> str:
    out = ["# INTENDED ZOZI STRUCTURE  (target — derived from the audit's model)",
           "Logical domains `database` & `security` live INSIDE backend/ by design.",
           "Sub-folder axis: SURFACE in routers/ & controllers/ (admin/supplier/...);",
           "                 DOMAIN  in services/ & models/ (finance/orders/...).", "```",
           "zozi/",
           "├── backend/",
           "│   ├── routers/        (admin/ supplier/ customer/ public/ webhooks/  = surface OK)",
           "│   ├── controllers/    (admin/ supplier/ ... surface OK; thin orchestration)",
           "│   ├── services/       (finance/ orders/ catalog/ supplier/ logistics/ comms/ hr/ ai/  = domain REQUIRED)",
           "│   ├── models/         (same domain sub-packages; each file declares __table_args__ schema)",
           "│   ├── middleware/  dependencies/  providers/  utils/  events/  jobs/  data/",
           "│   ├── db/  alembic/   (= the 'database' logical domain; ONLY migrations home)",
           "│   └── tests/  scripts/",
           "├── frontend/   (web_app · mobile_app · shared)",
           "├── documents/",
           "│   ├── scope/          (AUTHORITATIVE specs + repo_structure.yaml + layer_rules.yaml)",
           "│   └── archive/        (everything else)",
           "├── monitoring/  nginx/  (infra)",
           "├── experiments/  design/   (gitignored outputs / logo source)",
           "└── .gitignore  .env.example  README.md  docker-compose.yml  railway.toml",
           "```"]
    return "\n".join(out)


def render_stdout(repo: Path, rep: Report, show_intended: bool) -> int:
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)
    print("=" * 76)
    print("  ZOZI REPO LAYOUT + DEPENDENCY AUDIT  (read-only, repo-wide, by domain)")
    print("=" * 76)
    print(f"  repo: {repo}")
    print(f"  [RED] VIOLATIONS : {n_red}    [YEL] ADVISORIES : {n_yel}    [GRN] INFO : {n_grn}")
    print("  by rule: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.counters.items())))

    hot = [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED]
    hot.sort(key=lambda f: (0 if f.sev == RED else 1, f.code, f.path))
    print("-" * 76)
    print(f"  DAMAGE HOTLIST  ({len(hot)} items actively harming structure/scale)")
    print("-" * 76)
    for f in hot[:70]:
        print(f"  {SEV_ICON[f.sev]} {f.code:<3} [{f.domain:<8}] {f.loc()}")
        print(f"        {f.message}")
        if f.intended:
            print(f"        -> intended: {f.intended}")
    if len(hot) > 70:
        print(f"  ... +{len(hot) - 70} more (see report)")

    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)
    for dom in ["repo", "backend", "database", "frontend", "security", "docs", "infra"]:
        items = by_dom.get(dom, [])
        if not items:
            continue
        print("\n" + "=" * 76)
        print(f"  DOMAIN: {dom.upper()}  ({len(items)} finding(s))")
        print("=" * 76)
        for sev in (RED, YEL, GRN):
            for f in [x for x in items if x.sev == sev]:
                print(f"  {SEV_TAG[sev]} {f.code}  {f.loc()}")
                print(f"        {f.message}")
                if f.intended:
                    print(f"        -> {f.intended}")
    if show_intended:
        print("\n" + render_intended_tree())
    print("\n" + "=" * 76)
    return n_red


def render_markdown(repo: Path, rep: Report, out: Path) -> None:
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)
    L = ["# Repo Layout + Dependency Audit Report (GENERATED — do not hand-edit)", "",
         f"**Repo:** `{repo}`  ",
         f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn}  ",
         "**Ephemeral. Add to `.gitignore`. NOT an authoritative spec (those live in `documents/scope/`).**",
         "", render_intended_tree(), "",
         "## Scorecard", "", "| Code | Count | Sev | Meaning |", "|---|---|---|---|"]
    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |")
    hot = sorted([f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED],
                 key=lambda f: (0 if f.sev == RED else 1, f.code))
    L += ["", "## 🔥 Damage Hotlist (fix these first)", "",
          "| Sev | Rule | Domain | Location | Problem | Intended home / action |",
          "|---|---|---|---|---|---|"]
    for f in hot:
        L.append(f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} | `{f.loc()}` | {f.message} | {f.intended or '-'} |")
    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)
    for dom in ["repo", "backend", "database", "frontend", "security", "docs", "infra"]:
        items = by_dom.get(dom, [])
        if not items:
            continue
        L += ["", f"## Domain: {dom}", ""]
        for f in items:
            L.append(f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                     + (f" → *{f.intended}*" if f.intended else ""))
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


# ============================================================================
# 7. MAIN
# ============================================================================
def find_repo(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    cur = Path(__file__).resolve().parent
    for cand in (cur, cur.parent, cur.parent.parent, cur.parent.parent.parent):
        if (cand / "backend").is_dir() and (cand / "frontend").is_dir():
            return cand
    return Path.cwd().resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only repo-wide ZOZI layout + dependency audit.")
    ap.add_argument("--root", default=None, help="repo root (default: auto-detect)")
    ap.add_argument("--rules-dir", default=None,
                    help="dir holding repo_structure.yaml + layer_rules.yaml (default: documents/scope)")
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write findings JSON here (tooling/CI)")
    ap.add_argument("--no-write", action="store_true", help="do not write the .md report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--show-intended", action="store_true", help="also print the target tree")
    args = ap.parse_args()

    repo = find_repo(args.root)
    if not repo.is_dir():
        print(f"[FATAL] repo root not found: {repo}", file=sys.stderr)
        return 2

    eff = load_rules(repo, Path(args.rules_dir) if args.rules_dir else None)
    rep = Report()
    print(f"Scanning {repo} ...  (rules: {'YAML' if eff['from_yaml'] else 'embedded fallback'})")

    check_gitignore(repo, rep)
    check_lockfiles(repo, rep)
    check_cache_dirs(repo, rep)
    check_node_modules(repo, rep)
    check_hardcoded_local_paths(repo, rep)
    check_ghost_backend(repo, rep)
    check_duplicate_basenames(repo, rep)
    check_secrets_on_disk(repo, rep)
    check_intended_violations(repo, rep, eff)
    check_backend_root_modules(repo, rep, eff)
    check_scratch_scripts(repo, rep, eff)
    check_doc_and_root_allowlists(repo, rep, eff)
    check_layer_writes(repo, rep)
    check_router_outside(repo, rep)
    check_dependency_graph(repo, rep, eff)
    check_services_shape(repo, rep)
    check_rls_cluster(repo, rep)
    check_raw_env_in_middleware(repo, rep)
    check_media_on_disk(repo, rep)
    collect_info(repo, rep, eff)

    n_red = render_stdout(repo, rep, args.show_intended)

    if not args.no_write:
        out = Path(args.out).resolve() if args.out else (repo / "REPO_LAYOUT_AUDIT_REPORT.md")
        render_markdown(repo, rep, out)
        print(f"\nReport written: {out}  (generated -> .gitignore it; NOT under documents/scope/)")
    if args.json:
        jp = Path(args.json).resolve()
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(
            [{"sev": f.sev, "code": f.code, "domain": f.domain, "path": f.path,
              "line": f.line, "message": f.message, "intended": f.intended}
             for f in rep.findings], indent=2), encoding="utf-8")
        print(f"JSON written:   {jp}")
    return 1 if (n_red and not args.no_fail) else 0


if __name__ == "__main__":
    sys.exit(main())

```

---



```yaml

# documents\layer_rules.yaml
# AUTHORITATIVE layer contract.  Read by the dependency-graph validator in
# backend/scripts/backend_layout_audit.py (check_dependency_graph).
# forbidden_edges: caller_layer -> list of callee module-prefixes that are ILLEGAL.
# (An import matches if it equals the prefix or starts with "<prefix>.".)

forbidden_edges:
  controllers:
    - db.database          # the session/engine: controllers must not touch the DB
    - db.create_tables
    - db.init_db
  services:
    - routers              # upward dependency
    - controllers          # upward dependency
  models:
    - routers              # models are the floor: depend on nothing app-level
    - controllers
    - services
  providers:
    - routers              # adapters don't depend on app layers
    - controllers
    - services

# Controllers that actually hold service/util logic (grounded in the tree:
# audit_log/AuditAction, _order_holds_inventory/apply_order_status_change, cache_utils
# are imported across layers).  Importing them -> W3 (relocate the source first).
mis_housed_controllers:
  - audit_controller
  - payments_controller
  - cache_utils

# A controller importing another controller's internals -> W4 (shared logic must be
# a service/util).  Set false to silence once everything is relocated.
forbidden_controller_to_controller: true

```

---

```yaml


# documents\repo_structure.yaml
# AUTHORITATIVE structure rules for ZOZI.  Read by backend/scripts/backend_layout_audit.py.
# Edit HERE, not in the Python file (the Python embedded model is only a frozen fallback).
# All values are regexes unless noted.  A key fully replaces the embedded default for that key.

forbidden_root:
  backend:
    - '.*\.(log|db|db-shm|db-wal)$'
    - '^token\.tmp$'
    - '^.*\.(json|txt)$'
  backend/alembic:
    - '^_.*\.py$'                 # diagnostics must not sit in alembic/ (detected as revisions)
  frontend:
    - '.*\.(log|tsbuildinfo)$'
  frontend/web_app:
    - '.*\.bak$'
    - '\.tsbuildinfo$'
    - '^build_final.*$'
    - '^_audit_.*\.cjs$'
    - '.*\.(png|jpe?g)$'          # committed screenshots at package root = artifacts
  ".":
    - '^Working_API$'
    - '^provider_test$'
    - '^_trash$'
    - '^backup_\d+'
    - '^image$'
    - '^zozi-logo-app$'
    - '.*\.zip$'
    - '^login_form\.yml$'
    - '^zozi\.db(-shm|-wal)?$'
    - '^dev\.db$'
    - '^.*\.log$'

forbidden_any:
  backend:
    - '/db/migrations/'           # no second migrations home
    - '(^|/)employee_models\.py$' # models live only in backend/models/
  backend/db:
    - '/migrations/'
    - '(^|/)employee_models\.py$'
  backend/alembic:
    - '/versions/.*stub.*\.py$'

# .md allowed at repo root; any other .md or any .txt at root -> F9.
allow_root_md:
  - README.md
  - AGENTS.md
  - CONTRIBUTING.md
  - CHANGELOG.md
  - SECURITY.md
  - LICENSE.md
  - LICENSE

# entries allowed at documents/ root; anything else -> F8 (scope/ is authoritative).
allow_docs_root:
  - scope
  - archive
  - README.md
  - DOCUMENTATION_INDEX.md
  - INDEX.md

# Scratch detection = categories (substring phrases + name-segment tokens).
scratch_phrases:
  - countdivs
  - stackdivs
  - printlines
  - linenums
  - fixtailwind
  - patch-vars
  - patch_vars
  - verify-tmp
  - verify_tmp
  - impmain
  - client_tmp
  - reset_tmp
# broad tokens applied to backend-root .py only (the cross-tree .js scan uses a
# hard-coded safe subset {tmp,temp,scratch,debug} + the phrases, to avoid flagging
# legit ops scripts like scripts/validation/check_db.py).
scratch_tokens:
  - tmp
  - temp
  - scratch
  - debug
  - test
  - check
  - write
  - list
  - reset
  - verify
  - run
  - script
  - probe

```


-------------------------------------------------------------------

This is a substantial improvement over the previous version. Looking at it as a code auditor rather than an author, I'd rate it approximately **9.5/10** for its intended purpose (a read-only architecture governance tool). The biggest improvement is that it now validates **architectural contracts**, not just filesystem layout.

Here are the main strengths and the remaining issues I'd address before calling it "production governance."

---

# What became significantly better

## 1. Dependency graph (DG)

This is the biggest improvement.
Previously the auditor only asked:
> "Where is this file?"
Now it also asks:
> "Who is allowed to depend on whom?"
That is a much stronger architectural invariant.

For example,

```
services
    ↓
controllers
```

is fundamentally different from

```
controllers
    ↓
services
```

and your graph validator finally catches that.
That is exactly what enterprise architecture governance tools do.

---

## 2. YAML becoming authoritative

Excellent decision.

Instead of

```
Python
 ├── embedded rules
 ├── hardcoded regex
 ├── another hardcoded list
```

you now have

```
repo_structure.yaml
layer_rules.yaml

↓

Python engine
```

which separates
* policy
from
* implementation.
That is a very large improvement.

---

## 3. Layer contracts

Instead of simply saying

```
services imports controllers
```

you now say

```
services
↓

controllers

ILLEGAL
```

That makes the report much more actionable.

---

## 4. Allow-list philosophy

Huge improvement.

Instead of

```
40 forbidden filenames
```

you switched to

```
5 allowed names

everything else fails
```

Allow-lists age much more slowly than deny-lists.

---

## 5. Domain vs surface

I agree with your decision.

```
routers/
controllers/

↓

surface grouping

admin/
supplier/
customer/
```

while

```
services/
models/

↓

domain grouping

orders/
finance/
inventory/
```

matches DDD much better.

---

# Things I still recommend improving

These are the remaining architectural weaknesses.

---

# 1. Import resolution is still approximate

Currently you resolve imports like

```
from ..services.orders import x
```

using

```
_resolve_import()
```

but Python imports are much more complicated.

Examples:

```
from . import database
from .. import database
from ...services import inventory
import backend.services.orders
```

or

```
if TYPE_CHECKING:
    from ...
```

or

```
importlib.import_module(...)
```

Your resolver only handles about 80–85% of legal imports.
For governance that's acceptable, but for CI enforcement I'd recommend building a proper module graph.

---

# 2. No cycle detection

You validate forbidden edges.
But you don't detect

```
services/orders

↓

services/payment

↓

services/inventory

↓

services/orders
```

which is often worse.

A simple graph plus DFS would detect:

```
orders

↓

payment

↓

inventory

↓

orders
```

That would become

```
DG2
Circular dependency
```

I consider this the single biggest missing feature.

---

# 3. No ownership validation

Example

```
services/orders/
```

imports

```
services/payments/
```

Maybe legal.

Maybe not.

Right now there is no concept of

```
ownership boundary
```

It would be useful to declare in YAML something like

```yaml
domains:

 orders:
     may_import:
         - finance
         - inventory

 inventory:
     may_import:
         - catalog
```

instead of

```
all services can import all services
```

---

# 4. No dead-code graph

You know every import.

Therefore you know

```
who imports what
```

which means you can also know

```
who imports nothing
```

Unused services

Unused utilities

Unused controllers

Unused providers

Unused middleware

can all be detected automatically.

That is valuable.

---

# 5. No architectural metrics

Since you're already parsing every Python file, you can compute useful metrics such as:

* Layer fan-in
* Layer fan-out
* Instability
* Afferent coupling
* Efferent coupling

For example:

```
orders_service

Fan In: 18

Fan Out: 3

Stable
```

versus

```
utils.py

Fan Out: 42

Warning:
God module
```

These metrics help identify architectural hotspots.

---

# 6. No package validation

Suppose someone creates

```
services/orders/

    __init__.py

    foo.py
```

but forgets

```
service.py
```

or omits expected exports.

The auditor currently doesn't enforce package completeness.

---

# 7. Duplicate class detection

You detect duplicate module names.

You don't detect duplicate classes.

Example

```
OrderService
```

exists in

```
orders_service.py

inventory_service.py

legacy_orders.py
```

which causes confusion.

AST parsing already gives you class definitions, so this is straightforward.

---

# 8. No architectural trend reporting

Right now you produce a snapshot.

Over time, it would be useful to compare audits:

```
Last month

DG:
12

Today

DG:
5
```

or

```
Services

43

↓

58

↓

92
```

Trend reporting is extremely useful for governance.

---

# 9. Some rules could be configurable

These values are currently embedded:

```
WRITE_VERBS
READ_VERBS
KNOWN_WRITER_CONTROLLERS
SECRET_FILE_PATTERNS
CACHE_DIR_NAMES
LOCKFILES
```

If the goal is to make YAML the single source of truth, consider moving these policy-level constants into configuration as well. The Python file would then become almost entirely an execution engine.

---

# Overall assessment

From an architectural governance perspective, this is a major step forward over the previous version.
Compared to the earlier script:

* ✅ Filesystem governance is stronger.
* ✅ Layer contracts are explicitly enforced.
* ✅ Policy is externalized into YAML.
* ✅ Surface-vs-domain organization is well defined.
* ✅ Reports are more actionable.

To reach the next level, I'd prioritize these enhancements:

1. **DG2:** Detect dependency cycles.
2. **DG3:** Enforce domain ownership (bounded-context imports).
3. **A1:** Build a complete module graph with fan-in/fan-out metrics.
4. **A2:** Report dead or orphaned modules.
5. **A3:** Move remaining policy constants into YAML.

With those additions, the auditor would evolve from a **repository layout validator** into a **full architectural governance and dependency analysis tool**, comparable in capability to many commercial architecture validation systems while remaining lightweight and read-only.
