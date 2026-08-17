# Backend Scaffolding — ZOZI (Verified Map)

> **Purpose:** Accurate, verified map of the current backend layout so we can reason about structure, findability, and any domain-oriented migration.
> **Verified:** 2026-08-17 by direct filesystem scan of `backend/` (counts exclude `venv/`, `__pycache__/`, `.pytest_cache/`, `.hypothesis/`).
> **Scope:** ~1,600 application `.py` files. This is a *factual map*, not a recommendation.

---

## TL;DR

The backend is a **layered layout**: top-level directories split by *technical role* (`routers/`, `controllers/`, `services/`, `models/`, `utils/`, …). Three of those layers (`controllers/`, `services/`, `models/`) are **internally sub-foldered by domain**, but `routers/` is essentially **flat**. Cross-cutting/platform concerns live in their own top-level dirs (`db/`, `middleware/`, `providers/`, `events/`, `jobs/`, `tasks/`, `utils/`, …).

```
backend/
├── routers/          (225)  ← HTTP route registration   [FLAT, not domain-grouped]
├── controllers/      (371)  ← request shaping/validation [sub-foldered by domain]
├── services/         (575)  ← business logic             [sub-foldered by domain]
├── models/            (59)  ← SQLAlchemy ORM models      [sub-foldered by domain, consolidated]
├── db/                (13)  ← engine, session, schemas, alembic glue
├── middleware/        (19)  ← 6-layer security/observability pipeline
├── providers/         (78)  ← external integrations (payments, comms, ai, storage…)
├── utils/             (67)  ← large cross-cutting helper grab-bag
├── core/               (2)  ← route_contract
├── dependencies/       (4)  ┐
├── events/             (3)  │
├── jobs/               (7)  │  cross-cutting / platform
├── tasks/              (5)  │
├── tools/              (3)  ┘
├── alembic/           (37)  ← migrations (multi-schema)
├── scripts/           (41)  ← operational / setup scripts
├── tests/             (102) ← SEPARATE tree (playwright + unit); not co-located
└── main.py                  ← app factory + dynamic router loading
```

---

## Layer-by-layer breakdown

### `routers/` — 225 files · **FLAT**
- Only subdir is `generated/` (2 files). The remaining ~223 router files sit **directly in `routers/`**, not grouped by domain.
- `main.py` loads them via `_load_routers()`, which **recursively globs `routers/**/*.py`** and imports each module. The code comment already anticipates domain subfolders: *"Recurse so routers can live in domain subfolders (e.g. routers/logistics/...)"*.
- A few routers are hard-wired in `main.py` by literal name (e.g. `routers.logistics_partner_verify`, `routers.core_countries_routes`).

### `controllers/` — 371 files · sub-foldered by domain
| Group | Files | Notes |
|-------|------:|-------|
| core | 67 | cross-cutting request helpers |
| delegators | 95 | ambiguous grouping (delegation layer) |
| router_bridges | 57 | ambiguous grouping (bridge layer) |
| admin | 43 | |
| public | 16 | |
| commerce | 9 | |
| comms | 6 | |
| finance | 6 | |
| hr | 7 | |
| security | 5 | |
| logistics | 7 | |
| supplier | 8 | |
| orders | 6 | |
| catalog | 4 | |
| …others (ai, analytics, audit, customer, documents, gateway, geography, governance, identity, media, permissions, products, reporting, reviews, search, treasury, unknown, users) | 1–5 each | `unknown/` (4) = uncategorized |

### `services/` — 575 files · sub-foldered by domain (primary business layer)
Largest groups: `core` 68, `admin` 45, `comms` 44, `finance` 39, `geography` 37, `hr` 33, `security` 32, `supplier` 28, `treasury` 28, `logistics` 26, `commerce` 25, `orders` 18, `catalog` 17, `public` 20, `analytics` 4, `ai` 16, `media` 1, `search` 1, `reviews` 1, `promotions` 3, `products` 3, `customer` 5, `employee` 3, `identity` 3, `permissions` 1, `configuration` 1, `documents` 1, `reporting` 1, `hierarchy` 3, `governance` 4, `gateways` 11, `country` 3, `location_service` 3, `mcp` 2, `uploads` 1, `system` 5, `unknown` 2, `common` 19, `api` 2.

→ Already organized by **capability** (catalog, orders, logistics, supplier, finance…), not by actor. This is the good part.

### `models/` — 59 files · sub-foldered by domain, **consolidated**
- Far fewer files than `services`/`controllers` because each domain's tables live in **one consolidated module** (e.g. `models/catalog/` = 1 file, `models/geography/` = 7).
- Imports are often **flat package style**: `from models import Product` (484 occurrences repo-wide), not `from models.catalog import Product`. This is the trickiest part of any rename.

### Cross-cutting / platform
| Dir | Files | Role |
|-----|------:|------|
| `db/` | 13 | engine, `session`, `database`, `schemas`, `create_tables`, `seed`, `transaction`, `init_db`; `db/migrations/` subdir |
| `middleware/` | 19 | full security pipeline: `security_headers`, `csrf_middleware`, `rate_limit_middleware`, `zero_trust_auth`, `rls_*`, `pci_dss_compliance`, `impossible_travel`, `device_binding`, `webhook_*`, `orchestrator` |
| `providers/` | 78 | external integrations; subdirs: `ai`, `analytics`, `auth`, `automation`, `comms`, `finance`, `geography`, `image`, `legacy`, `media`, `news`, `payments`, `security`, `voice`; plus `_base`, `async_workers`, `config`, `http`, `observability`, `parcel_verification`, `storage` |
| `utils/` | 67 | **large grab-bag**: `datetime_utils`, `redis_client`, `encryption`/`kms_*`, `rls_*`, `cache`, `rate_limiter`, `websocket_manager`, `email_service`, `audit`, `slug`, `pagination`, `circuit_breaker`, `tracing`, `prometheus_setup`, `secrets_manager`/`vault`, `soft_delete`, `versioning`, `error_handler`, … |
| `core/` | 2 | `route_contract` |
| `dependencies/` | 4 | fastapi dependency injectors (`coi_dependency`, `country_detection`, `country_rls`, `fraud_events`) |
| `events/` | 3 | `event_publisher`, `payment_events` |
| `jobs/` | 7 | `background_tasks`, `fraud_monitoring`, `ghost_order_detector`, `mcp_server`, `seed_all`, `threat_feed_updater`; `jobs/ai/` subdir |
| `tasks/` | 5 | `ai_tasks`, `email_tasks`, `payout_tasks`, `periodic_tasks` |
| `tools/` | 3 | `extract_logic`, `migrate_router`, `triage_routers` (migration/aid scripts) |
| `alembic/` | 37 | migrations; multi-schema (public, analytics, audit, commerce, …) |
| `scripts/` | 41 | operational/setup scripts |

### `tests/` — 102 files · **separate tree**
- Lives at top level (`tests/playwright/` + unit tests), **not co-located** with the domains/features they exercise. This is the main auditability/test-locality gap.

---

## Notable observations (neutral facts)

1. **Three of four business layers are already domain-grouped** (`controllers/`, `services/`, `models/`). Only `routers/` is flat (~223 files directly in `routers/`).
2. **`routers/` is the inconsistency**, not the whole layout — and the loader already supports fixing it (recursive glob).
3. **`utils/` is a 67-file grab-bag** mixing infra (redis, db, encryption) with domain-ish helpers (audit, rls, geo). It predates the domain split and is a coupling hotspot.
4. **`controllers/` has ambiguous meta-groups** (`delegators` 95, `router_bridges` 57, `core` 67, `unknown` 4) that don't map to a business domain — likely cross-cutting or generated.
5. **`models/` uses flat-package imports** (`from models import X`) 484× — the single highest-effort item for any rename.
6. **Tests are separate from code** — testing a domain feature means leaving the domain tree.
7. **Imports are domain-namespaced for services/controllers**: `from services.<domain>.x` (1,229×), `from controllers.<domain>.x` (322×) — so a domain move is mostly a prefix rewrite there.

---

## What this map does NOT tell you
- Actual runtime coupling (fan-in/fan-out) — needs a dependency-graph audit, not a file listing.
- Which `services/` calls which `services/` across domains (boundary enforcement).
- Whether `delegators`/`router_bridges` duplicate logic found in `services/`.

These require the architecture/dependency audit referenced elsewhere — the file tree above is the structural baseline those audits run on.

---

# Target Scaffolding — IF we restructure domain-wise

> **Purpose:** Show the *proposed* structure if we convert the current layered layout into a **domain-oriented (modular monolith)** layout. All folder names are derived from the *actual* domains present in the current tree (see above), not invented.
> **Principle applied:** separate by **business capability**, not by actor. Actor boundaries (customer/admin/supplier/employee) become **route prefixes + auth scopes inside a domain**, not separate folder trees or servers.

## Target TL;DR

```
backend/
├── domains/                         ← PRIMARY AXIS: business capability
│   ├── catalog/                     (catalog, products, search, reviews, promotions, media)
│   │   ├── routers/                 ← actor subfiles: customer.py, admin.py, supplier.py …
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── models/
│   │   └── tests/                   ← CO-LOCATED with the domain
│   ├── orders/                      (orders, commerce)
│   ├── logistics/                   (logistics, geography, location_service)
│   ├── supplier/
│   ├── finance/                     (finance, treasury)
│   ├── identity/                    (identity, users, permissions, hr, employee, governance, hierarchy, security)
│   ├── comms/                       (comms, notifications)
│   ├── analytics/                   (analytics, reporting)
│   ├── ai/                          (ai, mcp, media inference)
│   └── platform/                    (core, api, common, configuration, system, country, gateways, unknown→triage)
│
├── platform/                        ← CROSS-CUTTING INFRA (extracted from utils/ + top-level)
│   ├── db/                          (moved from db/)
│   ├── middleware/                  (moved from middleware/)
│   ├── security/                    (encryption, kms_*, secrets_manager, vault, rls_* from utils/)
│   ├── cache/                       (redis_client, cache, rate_limiter from utils/)
│   ├── observability/               (tracing, prometheus_setup, metrics from utils/)
│   ├── messaging/                   (events/ + entity_messaging)
│   ├── jobs/  tasks/  providers/    (moved as-is)
│   └── http/  config/               (http, config helpers)
│
├── alembic/                         ← unchanged location (multi-schema)
├── scripts/  tools/                 ← unchanged
└── main.py                          ← loads domains/*/routers recursively (loader already supports this)
```

## Domain assignments (mapped from current code)

| Target domain | Absorbs current dirs |
|---------------|---------------------|
| `domains/catalog/` | `services/catalog`, `services/products`, `services/search`, `services/reviews`, `services/promotions`, `services/media`, `models/catalog`, `controllers/{catalog,products,search,reviews,promotions,media}` |
| `domains/orders/` | `services/orders`, `services/commerce`, `models/orders`, `controllers/{orders,commerce}` |
| `domains/logistics/` | `services/logistics`, `services/geography`, `services/location_service`, `models/logistics`, `models/geography`, `controllers/{logistics,geography}` |
| `domains/supplier/` | `services/supplier`, `services/uploads`, `models/supplier`, `controllers/supplier` |
| `domains/finance/` | `services/finance`, `services/treasury`, `models/finance`, `controllers/{finance,treasury}` |
| `domains/identity/` | `services/{identity,users,permissions,hr,employee,governance,hierarchy,security}`, `models/{identity,permissions,hr,security,supplier}`, `controllers/{admin,hr,identity,security,users,employee,governance,hierarchy}` |
| `domains/comms/` | `services/comms`, `models/comms`, `controllers/comms` (notifications) |
| `domains/analytics/` | `services/analytics`, `services/reporting`, `controllers/{analytics,reporting}` |
| `domains/ai/` | `services/ai`, `services/mcp`, `controllers/{ai,media}`, `jobs/ai/` |
| `domains/platform/` | `services/{core,api,common,configuration,system,country,gateways,unknown}`, `controllers/{core,public,router_bridges,delegators,unknown}`, `core/` |

> **Actor grouping note:** `controllers/admin` (43), `controllers/customer` (2), `controllers/public` (16) are *actor surfaces*, not domains. Under the target, actor-specific route files live **inside the owning domain** (e.g. `domains/orders/routers/admin.py`, `domains/orders/routers/customer.py`). This keeps the Order business logic in one place while still separating the customer vs admin API surface — exactly the "capability not actor" rule.

## Platform extraction (from `utils/` grab-bag)

`utils/` (67 files) is the biggest coupling hotspot. Under the target it is **split**, not moved wholesale:
- Infra → `platform/{db,middleware,security,cache,observability,http,config}`
- Domain-ish helpers (audit, geo, rls context) → into the relevant `domains/<cap>/`
- Remaining generic helpers → `platform/common`

## Current → Target migration mapping (high level)

| Current | Target |
|---------|--------|
| `routers/*.py` (flat, ~223) | `domains/<cap>/routers/` |
| `controllers/<domain>/` | `domains/<cap>/controllers/` |
| `services/<domain>/` | `domains/<cap>/services/` |
| `models/<domain>/` | `domains/<cap>/models/` |
| `tests/` (separate, 102) | `domains/<cap>/tests/` + keep `tests/e2e` or `tests/integration` at top for cross-domain |
| `utils/*` | split into `platform/*` + folded into domains |
| `db/ middleware/ providers/ events/ jobs/ tasks/` | `platform/` (same internal shape) |
| `alembic/ scripts/ tools/ main.py` | unchanged |

## Why this directly fixes your stated pains

- **Findability ("can't find files for domain+feature"):** every router/controller/service/model/test for `catalog` (or `orders`, `logistics`…) now lives under one folder.
- **Audit/testing difficulty:** tests move *into* `domains/<cap>/tests/`, so a domain is audited and tested in isolation; cross-domain behavior stays in a top-level `tests/integration`.
- **The flat `routers/` inconsistency is resolved** by simply grouping them into `domains/<cap>/routers/` — and `main.py`'s recursive loader already supports this, so no loader rewrite is needed.

## Risks / things that still need handling (accurate, not hand-waved)

1. **`models` flat imports** (`from models import X`, 484×) — the highest-effort item. Needs a compatibility shim (`models` re-exporting old paths) during transition, then gradual rewrite to `from domains.<cap>.models import X`.
2. **Hard-coded router imports in `main.py`** (`routers.logistics_partner_verify`, `routers.core_countries_routes`) — update per domain as they move.
3. **Alembic multi-schema** — moving model *files* must not change table/schema names; verify autogenerate still keys correctly after the move.
4. **`controllers/delegators` (95) and `controllers/router_bridges` (57)** — ambiguous meta-groups; must be triaged (likely platform-level or merged) before/while moving, not blindly dropped into a domain.
5. **`controllers/unknown` (4) and `services/unknown` (2)** — eliminate or reclassify during migration.
6. **`utils/` split** touches many files; do it via script + shim, not by hand.

## Execution note (not a rewrite)

This target is reached **domain-by-domain (strangler)**, not in one sweep: pilot one low-coupling domain (e.g. `catalog`), prove the import-rewrite script + `models` shim + co-located tests + alembic, then roll out. The current tree (above) is the before-state; this section is the after-state to plan against.
