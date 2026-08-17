# NEW_STRUCTURE Migration Map (authoritative, evidence-based)

> Derived from a direct scan of `backend/` (Aug 2026): 223 generated routers, 371
> controllers, 575 services, 27 flat model files, `db/schemas.py` (2227 lines), and the
> 15 live Postgres schemas declared via `__table_args__ = {"schema": ...}` in `models/`.
> This map is the input to every later phase. Items marked **TBD** need manual triage
> before the files in that pile are moved.

## 1 · The real bounded contexts (Postgres schemas) = the real domains

`models/` declares exactly 15 schemas. These — not the folder guesses in the chat
draft — are the source of truth for `domains/{d}/`.

| Real schema | NEW_STRUCTURE domain | Disposition |
|---|---|---|
| `finance` | `finance` | → `domains/finance` (root slice) |
| `treasury` | `finance` | → `domains/finance/treasury/` slice |
| `commerce` | `catalog` + `orders` | products/categories/coupons/reviews → `catalog`; cart/orders/returns → `orders` |
| `communication` | `comms` | → `domains/comms` |
| `customer` | `customers` | → `domains/customers` |
| `supplier` | `suppliers` | → `domains/suppliers` (incl. KYC, invoices, payouts) |
| `logistics` | `logistics` | → `domains/logistics` |
| `hr` | `hr` | → `domains/hr` (incl. hierarchy, payroll, attendance, leave, employees) |
| `media` | `media` | → `domains/media` (incl. AI image pipeline) |
| `security` | `infrastructure/security` + identity | JWT/hashing/zero-trust → `infrastructure/security`; accounts/identity → module `auth/` + owning domain |
| `audit` | `governance` | → `domains/governance` |
| `analytics` | `governance` (read_models) | snapshots/reporting → `domains/governance/read_models/` |
| `ai` | `providers/ai` | AI is a **provider**, not a domain (matches NEW_STRUCTURE `providers/ai`) |
| `configuration` | `country` | country_configs / category tax rates → `domains/country` |
| `core` | **TBD** | cross-domain pile → `kernel/` + `infrastructure/` + specific domains (see §3) |

## 2 · Surfaces (controller/router filename prefix) → Modules

Controller filename first token and router filename first token both encode the
**surface** (who acts). They collapse to the 5 NEW_STRUCTURE modules:

| Surface token(s) | Module |
|---|---|
| `admin` (45 ctrl / 78 rtr) | `modules/admin` |
| `supplier`, `suppliers`, `onboarding`, `payouts`, `disputes`, `invoice` | `modules/supplier` |
| `logistics`, `shipments`, `geo` | `modules/logistics` |
| `customer`, `wishlist`, `cart`, `coupons`, `returns`, `referrals`, `addresses`, `reviews`, `chatbot`, `tracking` | `modules/customer` |
| `employee`, `employees`, `ess`, `hr`, `payroll`, `attendance`, `hierarchy`, `performance`, `succession`, `lms`, `okr` | `modules/employee` |
| `public` (9 ctrl / 72 rtr) | unauthenticated customer-facing → `modules/customer` `public_router` (webhooks/storefront) |
| `country`, `countries`, `command`, `analytics`, `audit`, `permissions`, `users`, `tickets`, `banners`, `promotion`, `categories` | `modules/admin` (back-office) |
| `internal`, `comms`, `chat`, `notification`, `comm`, `communication` | `modules/employee` or `modules/admin` by caller |
| `auth` | module `auth/` (login/session) per module |

## 3 · Cross-cutting piles — disposition

| Pile (real folder) | Size | Target |
|---|---|---|
| `services/admin/*` | 45 | thinned: shell → `modules/admin/routers/*`; logic moved into the owning domain service |
| `services/core/*` | 68 | split: business rules → owning `domains/*/services`; pure helpers → `kernel/`; platform → `infrastructure/` |
| `controllers/core/*` | 67 | **TBD triage** — route shells → module routers; orchestration → domains |
| `controllers/delegators/*` | 95 | **TBD triage** — cross-module delegation shims; logic → domains, shell → modules |
| `controllers/router_bridges/*` | 57 | **TBD triage** — adapter layer; becomes `ports.py` or module routers |
| `services/gateways/*` | 11 | → `domains/payments` (gateway connections/settlements) + `providers/payments` |
| `services/common/*` | 19 | → `kernel/` + `infrastructure/utils` |
| `services/unknown/*` | 2 | (incl. `_registry`) → `infrastructure` boot wiring; resolve at module load |
| `utils/*` | 67 | split → `infrastructure/{security,redis,observability,utils}` + `kernel/` |
| `db/schemas.py` | 2227 ln | split → `domains/*/schemas/` (one slice per domain) |
| `middleware/*` | 19 | unchanged (flat) — keep in `middleware/` (or fold into `infrastructure`) |
| `providers/*` | 15 | unchanged — already matches NEW_STRUCTURE `providers/` |
| `jobs/*` | 7 | unchanged — `jobs/` |

## 4 · Boot anchors that MUST keep resolving during migration

Preserved via `_legacy/` shims until their owning slice is green:
- `import models` (registers ORM in `Base.metadata`)
- `services.admin.permissions_service.load_role_permission_settings`
- `services.unknown._registry`
- `services.gateways.payments._event_publisher` + `events.PaymentConfirmedEvent` + `services.orders.fulfillment_service`
- `db.treasury_seeder.seed_treasury_system`, `db.seed.seed_data`
- `main.py`: `middleware.orchestrator`, `utils.*`, `db.*`, `routers.public_comms_status`, `routers.logistics_partner_verify`, `routers.core_countries_routes`

## 5 · Import-fan-in risk (drives the rewrite order)

| Pattern | Count | Strategy |
|---|---|---|
| `from models import` (flat) | 1027 | `_legacy/models` re-export shim + rewrite to `domains.<d>.models` after move |
| `from services.<d> import` | 1657 | rewrite to `domains.<d>.services` per wave |
| `from controllers.<d> import` | 399 | delete after controllers split to module routers + domain services |
| `from models.<d> import` | 338 | rewrite to `domains.<d>.models` |

## 6 · Phase order (from the implementation plan)

1. **Phase 1** — this map + skeleton + `_legacy` shims + retarget `auto_router` + `db→infrastructure` + CI. App boots identically.
2. **Phase 2** — relocate per wave (foundation `kernel`/`infrastructure`/`rbac` → domains smallest-first → controllers split → retire 223 flat routers), each wave with AST import-rewrite.
3. **Phase 3** — per-feature consolidation (`ports.py`, `policies/`, `features.py`, `read_models/`, test co-location).
4. **Phase 4** — law enforcement (import-linter), RBAC swap, country 4th axis, frontend `rbac.ts` + generated `permissions.ts`, delete `_legacy`.

## 7 · Pilot

Prove the full loop on **`country`** (small: `configuration` schema + RLS = the 4th axis)
or **`finance`** (high value, `finance`+`treasury` slices). Then repeat Waves per domain.
Do **not** split module auth stores until domains are settled.
