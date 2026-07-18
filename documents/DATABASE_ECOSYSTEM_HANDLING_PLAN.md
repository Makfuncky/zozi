# Database Ecosystem Handling Plan & Audit

> Scope: How to operate a **large, multi-country e-commerce ecosystem** whose data model will grow to
> hundreds of tables and **thousands of fields** in production. `zozi.db` is a seed/test database only —
> production will be larger. This document is the **architecture & governance plan**, not a schema dump.
> The schema dump (per-table) is generated automatically; see `backend/scripts/generate_data_dictionary.py`.

---

## 1. Executive Summary

The database is **not over-built** — it is the data backbone of an ecosystem (commerce + finance/treasury +
logistics + HR/workforce + supplier onboarding + communications + country governance + fraud/risk + media/AI).
The correct response to scale is **governed growth**, not consolidation. Reducing tables would collapse the
application because each domain (payouts, commissions, KYC, treasury, logistics SLA, country config) is an
independent, in-use subsystem.

**Verdict:** Keep all tables. Introduce (a) bounded-context schema separation, (b) a real migration pipeline,
(c) a metadata-driven extensibility pattern for the "thousands of fields", and (d) automated documentation +
CI schema-drift gates. Do **not** manually merge or drop tables.

---

## 2. Audit Findings (current state)

| Dimension | Finding | Source |
|---|---|---|
| ORM models | ~270 table models in `models/` package (+~10 in controllers/services) | `Base.metadata` introspection |
| Test DB tables | 262 tables in `zozi.db` (seed only; production will exceed this) | `sqlite_master` |
| Controllers / Services | 50 controllers, 110 services | `backend/` tree |
| Multi-tenancy | Row-level country scoping via `country_code`, enforced by `utils/rls_interceptor.py` (154 table mappings) | `rls_interceptor.py` |
| Engine | SQLite for dev; **PostgreSQL required for prod** (engine raises on SQLite in prod) | `db/database.py` |
| Migrations | Alembic present (141 files) but **broken** (import errors) — not a reliable source of truth | `AGENTS.md`, `alembic/` |
| Extensibility | No standardized pattern for domain/country-specific fields yet | code review |

**Observed domain families** (each is a real bounded context, not redundancy):

- **Core / Identity**: users, roles, permissions, addresses, countries
- **Commerce**: products, categories, orders, order_items, cart, wishlist, coupons, flash_sales, reviews, returns
- **Supplier**: suppliers, supplier_documents, supplier_kyc, supplier_health, public_suppliers
- **Finance / Treasury**: journal_entries, account_*, payouts, commissions, cash_management, treasury, sub_ledger
- **Logistics**: logistics_partner, shipments, parcel_tracking, shop_locations, logistics_zones, shipping_tier
- **HR / Workforce**: employees, attendance, leave, shifts, payroll, succession, okr, lms, travel, offboarding
- **Communications**: chat, messages, email, notifications, push, internal_channels, entity_chat, proxy_communication
- **Country Governance**: country_configs, country_*, country_staff, country_payouts, country_legal_contracts
- **Fraud / Risk / Compliance**: fraud_rules, fraud_*, risk, compliance, audit, ediscovery
- **Media / AI**: media_assets, video, ai_*, image_tools, translation
- **Audit / Governance**: admin_activity_logs, audit_*, worm_audit, permission_audit_log

The apparent "duplication" (multiple chat/audit/ticket tables) is **functional separation across bounded
contexts** (e.g. customer chat vs entity chat vs internal channels vs proxy communication), not true redundancy.
They must stay separate.

---

## 3. Design Principles

1. **Scale is a feature, not a bug.** Hundreds of tables + thousands of fields is expected for an ecosystem.
2. **No silent table merges.** Every table maps to a subsystem with its own lifecycle and owners.
3. **Separate by bounded context, not by size.** Logical separation (schemas/namespaces) gives clarity without
   rewriting code.
4. **Country isolation is a first-class concern.** Keep row-level RLS; add physical partitioning for hot tables.
5. **Make the schema machine-documented.** Never hand-maintain a dictionary for thousands of fields.
6. **Every schema change is a reviewed migration + contract test.** No ad-hoc `ALTER`.

---

## 4. Recommended Architecture

### 4.1 Bounded-context schemas (PostgreSQL schemas)
Map the 270+ models into PostgreSQL **schemas** (namespaces). This is a metadata-only change; tables keep their
names and the app keeps working. Each schema is owned by a team.

| Schema | Tables (examples) | Owner |
|---|---|---|
| `core` | users, roles, permissions, addresses, countries | Platform |
| `commerce` | products, categories, orders, order_items, cart, coupons, reviews, returns | Commerce |
| `supplier` | suppliers, supplier_documents, supplier_kyc, public_suppliers | Supplier |
| `finance` | journal_entries, account_*, payouts, commissions, sub_ledger | Finance |
| `treasury` | treasury_*, cash_management_*, country_payouts | Treasury |
| `logistics` | logistics_partner, shipments, parcel_tracking, shop_locations | Logistics |
| `hr` | employees, attendance, leave, shifts, payroll, lms, okr | People |
| `comms` | chat, messages, email, notifications, internal_channels, entity_chat | Comms |
| `country` | country_configs, country_*, country_staff, country_legal_contracts | Country Ops |
| `risk` | fraud_rules, fraud_*, risk, compliance, audit, ediscovery | Risk |
| `media` | media_assets, video, ai_*, image processing | Media/AI |
| `audit` | admin_activity_logs, audit_*, worm_audit, permission_audit_log | Governance |

### 4.2 Multi-tenancy (country scoping)
- **Keep** the existing `country_code` row-level RLS interceptor (`utils/rls_interceptor.py`). It already scopes
  154 tables correctly. Extend the registry as new country-aware tables are added (make it a CI-enforced list).
- **Add declarative partitioning** on the largest/hottest tables:
  - `journal_entries`, `audit_*`, `chat`/`messages`, `order_items` → partition by `country_code` (LIST) or by
    time range (for logs/history). This bounds index size per country and speeds pruning.
- **Future option (extreme scale):** per-country physical databases behind a routing layer. Not needed yet;
  RLS + partitioning covers current volume.

### 4.3 Extensibility for "thousands of fields"
Do **not** add thousands of nullable columns to core tables. Use a typed extension pattern:

- **JSONB extension column** on core tables: e.g. `products.extra_attributes JSONB`, `users.profile_json JSONB`,
  `country_configs.settings JSONB`. One column absorbs dozens of optional, country/domain-specific fields.
- **EAV only where truly dynamic**: product attributes, per-country KYC requirements, per-country tax rules.
  These already exist as `supplier_kyc_requirements`, `tax_rules`, `country_category_tax_rates` — keep them as
  structured tables, not free-form, because they are queried/filtered.
- **Country config as versioned JSON**: `country_configs` + `country_config_versions` already support this.
  Extend the pattern rather than widening columns.
- Convention: any field needed by **one** country/domain → JSONB; any field needed by **all** → real column
  with migration.

### 4.4 Read/write separation
- OLTP (orders, payments, chat) on primary.
- Reporting/analytics (financial_reporting, admin_analytics, audit history) on **read replicas** / a warehouse.
  The existing `*_reporting` / `*_analytics` services already imply this split — formalize it.

### 4.5 Catalog: categories, variants, and AI-generated data (the real "big table" problem)
This is the fastest-growing area and was under-specified. Current model (`models/products.py`):

- **Categories**: a single self-referential `categories` table (`parent_id → categories.id`). N-level
  category → sub-category → sub-sub is **already supported by the tree** — no separate sub_category table is
  needed.
  - *Smell*: `products.category` (string) and `products.subcategory` (string) duplicate the category tree.
    Derive sub-category from the `category_id` relationship; deprecate the free-text columns to avoid drift.
- **Products**: a wide table (~50 columns) that **already uses JSON extension columns** (`attributes`,
  `materials`, `sizes`, `tags`, `images`, `filter_attributes`, `variant_axes`, `search_vector`). This is the
  correct pattern — keep it; do not widen the table with thousands of columns.
- **Variants**: `product_variants` is a separate 1:N table (size/color/material/pattern/gender +
  `attributes_json`). For a large catalog this is the **true big table** — combinatorially it can reach
  tens to hundreds of millions of rows.

Scaling rules for the catalog:
1. **Variants are the partition target.** Partition `product_variants` by `country_code` (LIST) and/or hash on
   `product_id`. Never let it become one unpartitioned heap.
2. **Deterministic variant identity.** Enforce a composite unique key `(product_id, size, color, material,
   pattern, gender)` or a hashed `variant_key`, so repeated AI uploads / re-syncs don't create duplicate
   variant rows.
3. **Searchable vs non-searchable attributes.** Typed, filterable attributes belong in
   `product_filter_metadata` / `product_filter_options` (per-category EAV) or a proper `product_attributes`
   table — these are queried/filtered. AI free-text and bulk attributes belong in JSONB (`attributes`,
   `variant_axes`). Do **not** put filterable attributes in JSON only.
4. **JSONB + GIN indexes (Postgres).** The product JSON columns must get `USING gin` indexes so AI-generated
   attribute queries don't full-scan. This is the single most important catalog performance action.
5. **Category path caching.** Pre-compute a `category_path` column or materialized view (category →
   sub-category → leaf) so listing filters don't walk the tree per row.

### 4.6 AI product-upload pipeline (multiplies table writes)
The AI upload system generates product data (descriptions, attributes, categories, variants, media). Findings:
- `products` already has `ai_description`; AI output lands in JSON columns and media tables.
- There is **no dedicated AI job/audit table today** (no `ai_upload_jobs`, `ai_generation_logs`). Pipeline
  state is implicit in `media_assets`, `media_upload_sessions`, and product columns — a gap at scale.

Scaling rules for the AI pipeline:
1. **Add `ai_upload_jobs`** (status, model used, prompt hash, token/cost, source media, created `product_id`,
   error, `country_code`). Needed for traceability, cost/billing, retries, and rate-limiting — one row per
   upload session.
2. **Add `ai_generation_logs`** for per-field generations (description, attributes, variant suggestions) to
   support human-in-the-loop review and model evaluation. Country-scoped.
3. **Media belongs in `media_assets`, not inline.** AI image processing (`free_image_tools`,
   `image_ai_service`) should write outputs as `media_assets` rows referenced by URL, not base64/JSON blobs on
   the product.
4. **Idempotency.** AI re-runs must upsert, not duplicate. Use the deterministic variant key (§4.5.2) and a
   content hash on the source media.
5. **Async + durable queue.** AI upload is long-running; persist job state *before* calling the model so a
   crash is resumable (status-driven, not in-memory).

---

## 5. Migration & Versioning Governance

Alembic is currently broken. Establish a reliable pipeline:

1. **Fix Alembic env** so `alembic revision --autogenerate` works against `Base.metadata`.
2. **One migration per PR.** Autogenerate → human review → squash periodically.
3. **No column drops without a deprecation window.** Mark `deprecated_*` + nullable, drop in a later release.
4. **RLS policies as code** (`backend/data/pg_rls_policies.sql`) applied in the same migration that adds a
   country-aware table.
5. **Migration tests**: spin up a throwaway Postgres, apply all migrations, assert `Base.metadata` matches DB.

---

## 6. Automation (so thousands of fields don't need hand work)

- **`backend/scripts/generate_data_dictionary.py`** — introspects `Base.metadata` and emits a markdown data
  dictionary (table → columns, types, nullability, PK, FKs, inferred domain). Run in CI; commit the output or
  publish to docs. This replaces manual `DATABASE_TABLE.md` maintenance.
- **CI schema-drift gate**: compare `Base.metadata.tables` against the migration-applied DB; fail the build on
  mismatch.
- **Naming lint**: every table must start with its schema/domain prefix (`commerce_`, `finance_`, `hr_`, ...).
  Block PRs violating the prefix.
- **RLS registry lint**: every table with a `country_code` column must be in `COUNTRY_AWARE_TABLES`.

---

## 7. Physical Scaling Roadmap

| Stage | Action |
|---|---|
| Now | PostgreSQL in prod; fix Alembic; add CI drift gate + data-dictionary generator |
| Near | Partition hot tables by country/time; JSONB extension columns for optional fields |
| Mid | Read replicas for reporting; connection pooling (already `QueuePool`); archive cold partitions |
| Far | Optional per-country databases behind a routing layer if a single cluster saturates |

---

## 8. Ownership & Naming Conventions

- Every table: `<domain>_<entity>` (e.g. `finance_payout_batch`, `hr_employee`, `comms_message`).
- Every country-aware table: has `country_code` and is registered in `COUNTRY_AWARE_TABLES`.
- Every migration: references the owning schema/team in the message.
- Each schema has a named owner team accountable for its models and migrations.

---

## 9. Risks If Ignored

- **Manual `ALTER`s / broken Alembic** → schema drift between code and DB → runtime 500s (this already happened
  on several admin endpoints, now patched).
- **Adding thousands of nullable columns to core tables** → unqueryable, slow, unmaintainable schema.
- **`product_variants` left unpartitioned** → at catalog scale it becomes a hundreds-of-millions-row heap
  that kills listing/filter performance and blocks migrations.
- **AI upload with no job/audit table** → duplicate products/variants on re-run, no cost tracking, no
  resumability after a crash, no way to evaluate which model/prompt produced which data.
- **No CI drift gate** → a model change ships without a migration and silently breaks in prod.
- **No ownership** → tables grow without accountability; the "too many tables" feeling returns.

---

## 10. Immediate Next Actions

1. Run `backend/scripts/generate_data_dictionary.py` to produce the live dictionary (replaces hand edits).
2. Fix Alembic env + land one clean baseline migration against a fresh Postgres.
3. Add CI checks: schema-drift gate, naming lint, RLS-registry lint.
4. Introduce JSONB `extra_attributes` on the 3–5 highest-churn core tables.
5. Assign schema owners from the table in §4.1.
6. **Catalog at scale**: partition `product_variants`; add GIN indexes on product JSON columns; replace
   `products.subcategory` free-text with the `category_id` tree relationship; enforce a deterministic variant key.
7. **AI upload pipeline**: add `ai_upload_jobs` + `ai_generation_logs`; make AI writes idempotent and async
   with durable job state; route AI media to `media_assets`.

---

### Appendix: why we do NOT reduce tables
Each table is an independent subsystem with its own lifecycle, owners, and country-scoping. Merging them would
require rewriting controllers/services/RLS and would couple unrelated domains (e.g. customer chat with internal
comms, or payouts with treasury). The cost/risk is far higher than governing the scale. Growth is handled by
**separation + automation**, not by deletion.


---


# Database & System Handling Plan

> Scope: the live schema (`backend/zozi.db`) has **262 tables**. This plan defines how to
> classify, consolidate, govern, and eventually migrate that surface area without breaking
> the running system. It is a *handling* plan, not an immediate drop-everything order.

---

## 1. Reality Check — Is 262 Too Many?

Yes and no.

- **262 tables is high** for a single SQLite file, but defensible for a **country-scoped
  marketplace that also bundles internal ERP** (HR, finance, treasury, logistics, fraud,
  comms). Most large SaaS platforms split this across multiple services; here it is one DB.
- **230 of 262 tables are empty** (0 rows). This is a development/seed database. The risk
  today is *schema sprawl and duplication*, not storage or query performance.
- The genuine problem is **overlap**: the same concept is modeled 3–8 times
  (chat, audit, KYC, tickets, payout rules, tokens, webhooks).

**Verdict:** Keep the breadth, but (a) collapse the duplicated families, (b) tier every
table by lifecycle, and (c) enforce governance so it does not keep growing. Target: **~150–170
tables** after consolidation, with clear ownership.

---

## 2. Bounded Contexts (262 → 10 Domains)

From analyzing the live schema:

| Domain | Tables | Role |
|--------|-------|------|
| COUNTRY / Config | 19 | Country master, tax, commissions, gateways, staff, localization |
| COMMERCE | 25 | Products, orders, carts, coupons, banners, media, reviews, wishlist |
| FINANCE / TREASURY | 35 | Invoices, ledgers, payouts, journal, cash, reconciliation, VAT/COD |
| LOGISTICS | 14 | Partners, service areas, pricing, settlements, vehicles, zones |
| HR / WORKFORCE | 24 | Employees, attendance, leave, expenses, assets, travel, offboarding |
| SUPPLIER / ONBOARDING | 14 | KYC, pipelines, OCR, supplier docs, disputes, notifications |
| FRAUD / SECURITY | 12 | Rules, cases, scoring, blacklists, device/IP reputation |
| COMMS / NOTIFY | 36 | Chat, email, messages, notifications, news, escalations, proxy |
| ADMIN / GOV | 11 | Audit logs, analytics, incidents, meetings, permissions, DEI |
| CORE + OTHER | ~24 | users, orders, products, permissions, tickets, video, shifts, geo… |

COMMS (36), FINANCE (35), and HR (24) are the heaviest and the most duplicated.

---

## 3. Table Tiering Model

Every table gets exactly one tier. This drives migration, backup, retention, and review rigor.

| Tier | Meaning | Handling |
|------|---------|----------|
| **T0 Core** | Users, orders, products, payments, country_configs | Strict Alembic migrations; never auto-create; reviewed by lead |
| **T1 Operational** | Shipments, invoices, payouts, ledger, tickets, chat | Normal migrations; soft-delete standard |
| **T2 Config / Reference** | country_*, tax_rules, commission_*, feature flags | Seed/migration-managed; versioned |
| **T3 Audit & History** | audit_logs, journal_entries, webhook events, login history | Write-once; archived; not part of OLTP hot path |
| **T4 Ephemeral** | sessions, OTP/reset tokens, cached webhook raw, push tokens | TTL + cleanup job; safe to drop on expiry |
| **T5 Deprecated** | Overlapping duplicates marked for removal | `is_active=0` + doc note, then dropped on next major |

**Standard columns** every T0–T3 table must have: `id`, `created_at`, `updated_at`,
`country_code` (if country-aware), and `is_deleted`/`deleted_at` for soft delete.

---

## 4. Consolidation Opportunities (the real fix)

These are the highest-value merges. **Verify no code reference before dropping** (grep
`routers/`, `models/`, `services/`); then migrate data → new table → delete old.

### 4.1 Messaging → one conversation model (8+ tables → 3)
`direct_chat_rooms`, `direct_chat_messages`, `group_chat_rooms`, `group_chat_members`,
`group_chat_messages`, `internal_channels`, `internal_channel_members`, `internal_messages`,
`entity_chat_threads`, `entity_chat_messages`, `country_communications`,
`country_communication_threads`, `employee_communication_threads`, `messages`
→ **`conversations`** + **`conversation_messages`** + **`conversation_participants`**
with a `channel_type` enum (direct | group | internal | entity | country). One masked/B2B
layer sits on top via `proxy_*`.

### 4.2 Audit logs → single ledger (5 → 1)
`audit_logs`, `admin_change_audit_logs`, `admin_activity_logs`, `permission_audit_log`,
`communication_audit_trail` → **`audit_logs`** with `scope` + `actor_type` + `entity_type`.
Keep `admin_change_audit_logs` only if field-level diffing is required (otherwise a column).

### 4.3 KYC → generic verification (3 → 2)
`kyc_verifications`, `supplier_kyc_requirements`, `logistics_partner_kyc_requirements`
→ **`kyc_requirements`** (per entity_type) + **`kyc_verifications`** (per entity).

### 4.4 Tickets → one support model (5 → 3)
`support_tickets`, `support_ticket_replies`, `ticket_replies`, `ticket_messages`,
`ticket_attachments` → **`tickets`** + **`ticket_messages`** + **`ticket_attachments`**
(`ticket_replies`/`support_ticket_replies` are duplicates of `ticket_messages`).

### 4.5 Auth tokens → one table (5 → 1)
`email_verification_tokens`, `password_reset_tokens`, `revoked_tokens`, `user_sessions`,
`push_notification_tokens` → **`auth_tokens`** with `token_type`
(verify_email | reset_password | session | push | revoke).

### 4.6 Payout / commission rules → 2 tables
`payout_rules`, `payout_rule_categories`, `payout_rule_products`, `country_payout_rules`,
`product_commission_overrides`, `commission_agreements`, `commission_category_rates`,
`commission_global_configs`, `country_commission_rates`, `country_commission_rate_history`,
`supplier_country_commissions` → **`commission_rules`** + **`payout_rules`**, both
country-scoped, with `applies_to` (category | product | tier | global).

### 4.7 Webhook events → 1 (2 → 1)
`normalized_webhook_events`, `processed_webhook_events` → **`webhook_events`** with `status`.

### 4.8 Shift handover → 1 (3 → 1)
`shift_handover_logs`, `shift_handover_sessions`, `shift_handover_tasks`
→ **`handover_sessions`** with JSON `tasks`.

### 4.9 Ledgers → one double-entry core
Keep **`journal_entries`** + **`journal_entry_lines`** as the single source of truth.
`ap_ledger_entries`, `ar_ledger_entries`, `transaction_ledgers`, `promotion_ledger_entries`,
`commission_ledger_entries`, `bank_transactions`, `cash_transactions` become *views/reporting*
layers (or narrow tables) fed by journal entries — not parallel ledgers.

**Result:** removing only the clear duplicates above takes the surface from 262 → ~200;
with view-based ledgers and full chat/token unification, ~150–170 is realistic.

---

## 5. Lifecycle & Retention Policy

- **Soft delete** (`is_deleted`/`deleted_at`) is already standardized — enforce it in the
  base model; never hard-DELETE in T0–T3.
- **T3 (audit/history):** archive by `created_at` older than 12 months into a cold schema
  / Parquet export; keep 90 days hot. This bounds growth of `audit_logs`, `journal_entries`,
  `webhook_events`, `login_history`.
- **T4 (ephemeral):** Redis TTL already exists for some; add a nightly DB cleanup job for
  expired `auth_tokens`, `user_sessions`, `normalized/processed_webhook_events` raw copies.
- **T5 (deprecated):** set `is_active=0`, add a `deprecated_in` note column or doc entry,
  keep 1 release for rollback, then drop.

---

## 6. Country-Scoping & RLS

- The `rls_interceptor` + `COUNTRY_AWARE_TABLES` registry works, but maintaining it by hand
  drifts (it has already needed fixes). **Auto-derive** country-aware tables from
  "has a `country_code` column" at startup, then diff against the registry and warn on drift.
- Keep `country_code` as `VARCHAR(3)` (or `(10)` where ISO+sub-region) consistently — the
  schema currently mixes `(3)` and `(10)`; standardize on `(10)` to avoid join-type issues.
- KMS field-level encryption for PII columns stays; document exactly which columns are
  encrypted (keep a `data_residency_encrypted` / column-level map).

---

## 7. Schema Governance

- **Alembic first.** The broken migration (`Union` import) must be fixed; no new table ships
  without a migration. Ban ORM `Base.metadata.create_all` in production (dev seed only).
- **Naming convention (lint in CI):** `snake_case`, plural table names, `<thing>_id` FKs,
  `created_at`/`updated_at`, `country_code` for scoped tables, `is_deleted` for soft delete.
- **Schema-drift gate (currently "not verified"):** run `scripts/analyze_tables.py` + a
  columns diff in CI; fail build if a T0/T1 table changed without a migration.
- **Ownership matrix:** each bounded context has a named owner (see §9). Untriaged tables
  block merge.
- **Documentation:** `DATABASE_TABLE.md` already holds the full per-table schema — keep it
  generated from the DB (re-run the extractor) so it never rots.

---

## 8. Migration to PostgreSQL (already scaffolded)

The existing `pg_*` migration scripts are the right direction. Use **Postgres schemas** to
replace the "one big file" problem:

| Postgres schema | Source domains |
|-----------------|----------------|
| `country` | COUNTRY / Config |
| `commerce` | COMMERCE |
| `finance` | FINANCE / TREASURY |
| `logistics` | LOGISTICS |
| `hr` | HR / WORKFORCE |
| `supplier` | SUPPLIER / ONBOARDING |
| `fraud` | FRAUD / SECURITY |
| `comms` | COMMS / NOTIFY |
| `admin` | ADMIN / GOV |

- Move T3 (audit/history) to a `history` schema or separate analytics DB.
- Move T4 (ephemeral) to Redis/short-TTL; don't persist long-term.
- Enforce RLS **in Postgres** (the `pg_rls_policies.sql` already generated) instead of the
  Python interceptor — more robust and off the request path.

---

## 9. Ownership Matrix

| Context | Owner | On-call |
|---------|-------|---------|
| country | Platform/Config lead | country staff |
| commerce | Commerce squad | — |
| finance | Finance/Treasury squad | finance admin |
| logistics | Logistics squad | — |
| hr | People-ops eng | HR admin |
| supplier | Supplier squad | — |
| fraud | Trust & Safety | fraud analyst |
| comms | Comms squad | — |
| admin | Platform lead | admin |

---

## 10. Action Plan (ordered)

1. **Freeze + inventory** — done: 262 tables catalogued in `DATABASE_TABLE.md`;
   `scripts/analyze_tables.py` produces live domain/empty/overlap reports.
2. **Fix Alembic** — repair the `Union` import so migrations run; ban `create_all` in prod.
3. **Auto-derive RLS registry** from `country_code` columns; alert on drift.
4. **Consolidate chat** (§4.1) — highest duplication, biggest win (8→3).
5. **Consolidate audit logs** (§4.2) and **auth tokens** (§4.5) — low-risk, high-clarity.
6. **Unify KYC / tickets / webhooks / handover** (§4.3–4.8).
7. **Single double-entry ledger** (§4.9) — finance correctness, not just cleanup.
8. **Tier every remaining table** (§3); set retention jobs for T3/T4.
9. **CI schema-drift gate** using the analyzer.
10. **Postgres split by schema** (§8) for production; keep SQLite only for local dev.

---

## 11. Risk Notes

- **Do not drop empty tables blindly.** 230 are empty now, but several are referenced by
  routers/models (e.g., `entity_chat_threads`, `journal_entries`). Grep for references and
  run the test suite (`test_database.py`, 33 tests) after each consolidation.
- **Country-code length mismatch** (`VARCHAR(3)` vs `(10)`) must be resolved *before* joins,
  not during — fix in the migration that introduces the unified tables.
- Keep one release of deprecated tables (T5) for rollback; never drop in a patch.


---


read all files and below things and suggest a better plan in detail. and do the deep work.


---

Most important product which have category + sub-category + variants which are really big table and we didn't discuss about that. and also we are using AI for uploading product and it's data so I am sure there is AI upload system also will increase table size.

---

Based on the comprehensive architecture we have designed for the **Zozi Global E-Commerce Platform** (including the Country Control Plane, Employee IAM, Double-Entry Treasury, Logistics, and Supplier modules), here is the complete **Database Audit and Optimization Guide**.

While a highly normalized database is good for data integrity, **over-normalization** in a complex multi-tenant system leads to massive `JOIN` overhead, slow queries, and maintenance nightmares. 

Here is the strategic plan to reduce table count, eliminate redundancy, and optimize performance.

---

### 🚨 1. Executive Audit Summary
Your current schema (based on our architectural blueprints) has approximately **60-70 tables**. 
- **The Good:** Strict separation of concerns (e.g., GL vs. Operational Ledger).
- **The Bad:** Severe redundancy in "Partner" entities (Supplier vs. Logistics), overlapping audit logs, and fragmented configuration tables.
- **The Fix:** We will reduce the table count by **~20%** by implementing **Polymorphic Associations** (unifying similar entities) and **JSONB Aggregation** (for flexible configs), without losing relational integrity.

---

### 🔄 2. Tables to MERGE (The "Redundancy Kill List")

These tables store identical or highly similar data for different entities. We will merge them using a `entity_type` and `entity_id` pattern.

#### A. Unified Bank Accounts (Financial Routing)
*   **Current:** `supplier_bank_accounts`, `logistics_partner_bank_accounts`, `employee_bank_accounts`.
*   **Problem:** Three tables with identical columns (`bank_name`, `account_number`, `iban`, `swift`).
*   **Solution:** Merge into **`partner_bank_accounts`**.
    *   *Columns:* `id`, `entity_type` (ENUM: 'supplier', 'logistics', 'employee'), `entity_id` (UUID), `bank_details_json` (Encrypted), `is_primary`, `status`.

#### B. Unified Documents & Credentials (KYC/Compliance)
*   **Current:** `supplier_documents`, `logistics_partner_documents`, `employee_documents`, `employee_certifications`.
*   **Problem:** Four tables storing file URLs, expiry dates, and verification statuses.
*   **Solution:** Merge into **`entity_credentials`**.
    *   *Columns:* `id`, `entity_type`, `entity_id`, `credential_type` (ENUM: 'trade_license', 'vat_cert', 'driving_license', 'passport', 'nda'), `file_url`, `expiry_date`, `verification_status`, `verified_by`.

#### C. Unified Audit Logs (Forensics)
*   **Current:** `audit_logs` (System/Auth), `admin_change_audit_logs` (Financial/Config changes).
*   **Problem:** Admins have to query two different tables to see a complete timeline of an event.
*   **Solution:** Merge into a single **`system_audit_logs`** table.
    *   *Columns:* `id`, `actor_type` (admin, supplier, system), `actor_id`, `action` (login, update_commission, approve_payout), `entity_type`, `entity_id`, `old_value_json`, `new_value_json`, `ip_address`, `created_at`.
    *   *Optimization:* Partition this table by `created_at` (monthly) because it will grow to millions of rows.

#### D. Unified Communications (Internal & B2B)
*   **Current:** `country_communications`, `support_tickets`, `ticket_replies`.
*   **Problem:** Internal staff messaging and external customer support are using different schemas but serve the same purpose (threaded messaging).
*   **Solution:** Merge into **`communications`** and **`communication_messages`**.
    *   *Columns (Thread):* `id`, `channel_type` (internal, supplier_b2b, customer_support), `country_code`, `linked_entity_type` (order, supplier), `linked_entity_id`.
    *   *Columns (Message):* `id`, `thread_id`, `sender_id`, `body`, `is_read`.

---

###  3. Tables to REDUCE (JSONB vs. Relational)

Some tables are too granular. If the data is only ever read/written as a single unit, it should be a JSONB column in the parent table.

#### A. Country Feature Flags
*   **Current:** `country_feature_flags` (`country_code`, `feature_key`, `is_enabled`).
*   **Problem:** Requires a `JOIN` every time the frontend checks if a feature (e.g., `bnpl_enabled`) is active for a country.
*   **Solution:** **DELETE this table.** Add a `feature_flags_json` JSONB column to the `country_configs` table.
    *   *Data:* `{"bnpl_enabled": true, "ai_chatbot": false}`.

#### B. Promotion Rules & Tiers
*   **Current:** `promotion_engine_configs`, `promotion_order_tiers`.
*   **Problem:** Overly complex relational mapping for rules that change frequently and have varying structures.
*   **Solution:** Merge into **`promotion_rules`** attached to the `promotions` table.
    *   *Column:* `rules_json` (Stores conditions, tiers, and eligibility logic).

#### C. Employee Address Matrix
*   **Current:** Separate tables or highly fragmented rows for Legal, Residential, and Tax addresses.
*   **Solution:** Keep **`employee_addresses`** as a single table, but use an `address_type` ENUM (`legal`, `residential`, `permanent`, `tax`). Do not create separate tables for each type.

---

### 🏦 4. The "Dual Ledger" Problem (Critical Architectural Fix)

*   **Current:** You have `accounts` / `journal_entries` (The GL) AND `treasury_accounts` / `treasury_transactions` (The Cash Pool).
*   **The Risk:** If these two systems are not perfectly synchronized, your "Bank Balance" will not match your "Accounting Balance."
*   **The Solution:** **`treasury_accounts` should NOT be a separate ledger.** 
    *   A Treasury Account (e.g., "Emirates NBD Operating Account") is simply an **Asset Account** in your GL (e.g., Account Code `1010`).
    *   **Action:** Add a `treasury_metadata_json` column to the `accounts` table to store bank routing numbers, IBANs, and physical bank details. 
    *   **Result:** All money movements are recorded *once* in `journal_entries`. You eliminate the need for `treasury_transactions` entirely.

---

### 🗺️ 5. Final Optimized Schema Blueprint (The Target State)

Here is the consolidated list of tables you should aim for:

#### **Core & Identity**
1. `users` (Customers, Admins, Staff base auth)
2. `employees` (HR profiles, linked to users)
3. `partner_bank_accounts` (Unified for Suppliers, Logistics, Employees)
4. `entity_credentials` (Unified KYC, Visas, Licenses, Documents)

#### **Country Control Plane**
5. `country_configs` (Master config + Feature Flags JSONB)
6. `country_cities` (Relational for dropdowns/logistics)
7. `country_category_tax_rates` (Specific tax overrides)
8. `country_staff_assignments` (RLS enforcement)

#### **Catalog & Commerce**
9. `products` (Includes `promotion_rules_json`)
10. `categories`
11. `product_media` (Unified Images & Videos)
12. `orders` & `order_items`
13. `carts` & `cart_items`

#### **Logistics & Fulfillment**
14. `shipments` (Linked to orders, tracks physical parcels)
15. `logistics_zones`

#### **Finance (The Single Source of Truth)**
16. `account_groups` & `accounts` (Includes Treasury metadata)
17. `journal_entries` & `journal_entry_lines` (The ONLY place money moves)
18. `account_balances` (Materialized cache for fast dashboard loading)
19. `commission_ledger_entries` (Tracks supplier payouts before they hit the GL)

#### **Engagement & Support**
20. `communications` & `communication_messages` (Unified Chat/Tickets)
21. `reviews`
22. `news_articles` & `news_sources`

#### **System & Audit**
23. `system_audit_logs` (Unified, partitioned by month)
24. `processed_webhook_events` (Idempotency)

---

### 🛠️ 6. Implementation Guide: How to Handle the Migration

Do not just delete tables. Follow this 4-step protocol to ensure zero downtime and no data loss.

#### Step 1: Create the Unified Tables
Create the new merged tables (e.g., `partner_bank_accounts`) alongside the old ones. Do not drop the old tables yet.

#### Step 2: Write Data Migration Scripts
Write a Python/Alembic script that:
1. Reads from `supplier_bank_accounts`.
2. Inserts into `partner_bank_accounts` with `entity_type = 'supplier'`.
3. Reads from `logistics_partner_bank_accounts`.
4. Inserts into `partner_bank_accounts` with `entity_type = 'logistics'`.

#### Step 3: Update the ORM Models (FastAPI/SQLAlchemy)
Update your `models.py` to point to the new unified tables. 
*   *Crucial:* Use **Polymorphic Identity** in SQLAlchemy or simple `if/else` logic in your services to handle the `entity_type`.
*   *Example:* When fetching bank details for a supplier, query `partner_bank_accounts` where `entity_type == 'supplier' AND entity_id == supplier.id`.

#### Step 4: Deprecate and Drop
1. Run the application and verify all features (Payouts, KYC, Chat) work with the new tables.
2. Once verified in production, create a final Alembic migration to `op.drop_table('supplier_bank_accounts')`, etc.

### 💡 Summary Recommendation
**Yes, you should absolutely reduce and merge tables.** 
By implementing the **Unified Partner Tables** (Bank, Documents) and **Unified Audit/Comms Tables**, you will reduce database complexity by ~20%, speed up your Admin Dashboard queries (fewer JOINs), and make your backend code significantly cleaner and easier to maintain.

---


Based on a deep forensic analysis of the three provided documents (`DATABASE_ECOSYSTEM_HANDLING_PLAN.md`, `GENERATED_DATA_DICTIONARY.md`, and `DATABASE_TABLE.md`), here is a comprehensive, CTO-level architectural review and detailed strategic suggestions for the Zozi database ecosystem.

### 🚨 Executive Summary: The Current State
Your database has grown to **260 tables**, which is massive for a monolithic ORM. While the domain coverage is impressive (Logistics, HR, Finance, Country Governance, etc.), the architecture is suffering from "Flat Namespace Fatigue." 
*   **The Good:** You have a robust Double-Entry Ledger (`journal_entries`, `ap_ledger`, `ar_ledger`), a mature Logistics Handoff system (`shipment_confirmations`), and a Zero-Trust HR system (`employee_biometrics`, `user_devices`).
*   **The Bad:** 100 tables (38% of your DB) are dumped into the **"other"** domain. This indicates a lack of strict bounded contexts in the current SQLAlchemy models.
*   **The Solution:** You must transition from a flat `public` schema to **PostgreSQL Bounded-Context Schemas** immediately, as proposed in your handling plan.

Here is the detailed, step-by-step strategic plan to optimize, organize, and scale this ecosystem.

---

### ️ Strategy 1: Implement PostgreSQL Bounded-Context Schemas
*Reference: `DATABASE_ECOSYSTEM_HANDLING_PLAN.md` & `GENERATED_DATA_DICTIONARY.md`*

Having 260 tables in the default `public` schema makes development, debugging, and DBA tasks a nightmare. PostgreSQL allows you to create logical namespaces (schemas) without changing your application logic.

**Action Plan:**
1.  **Define the Schemas:** Map your domains to PostgreSQL schemas.
    *   `core` (users, roles, sessions, user_devices)
    *   `commerce` (products, categories, orders, carts, wishlists)
    *   `finance` (accounts, journal_entries, ap_ledger, ar_ledger, cash_position_snapshots)
    *   `logistics` (shipments, shipment_confirmations, logistics_partners, logistics_zones)
    *   `hr` (employees, employee_attendance, employee_biometrics, employee_shift_rosters)
    *   `country` (country_configs, country_cities, country_feature_flags)
    *   `comms` (messages, entity_chat_threads, internal_notices)
    *   `risk` (fraud_rules, audit_logs, coi_reports)
2.  **SQLAlchemy Integration:** Update your ORM models to use the `__table_args__` parameter.
    *   *Example:* `__table_args__ = {"schema": "hr"}` on the `Employee` model.
3.  **Migration Strategy:** Write an Alembic migration that creates the schemas (`CREATE SCHEMA hr;`) and moves the existing tables into them (`ALTER TABLE employees SET SCHEMA hr;`). This is a metadata-only change and requires zero downtime.

---

### 🧹 Strategy 2: Tame the "Other" Domain (100 Tables)
*Reference: `GENERATED_DATA_DICTIONARY.md`*

The Data Dictionary shows **100 tables in the "other" domain**. This is a critical technical debt. These tables likely contain legacy features, abandoned experiments, or poorly categorized entities.

**Action Plan:**
1.  **Audit & Categorize:** Write a script to query the `information_schema` for these 100 tables. Check their last `updated_at` timestamp or query logs.
2.  **Delete or Archive:** If a table hasn't been written to in 6 months, drop it or move it to an `archive` schema.
3.  **Reclassify:** Move the active tables into their correct bounded contexts (e.g., if `banners` is in "other", move it to `commerce` or `marketing`).
4.  **Target:** Reduce the "other" domain to **< 10 tables** (reserved for truly cross-domain utility tables).

---

### 🛡️ Strategy 3: Multi-Tenancy & Row-Level Security (RLS)
*Reference: `DATABASE_TABLE.md`*

Almost every table in `DATABASE_TABLE.md` has a `country_code` column. This is excellent for multi-tenancy, but querying it manually in every API endpoint is prone to developer error (leading to data leaks).

**Action Plan:**
1.  **Enable PostgreSQL RLS:** Instead of relying solely on SQLAlchemy `WHERE country_code = :code`, enable Row-Level Security at the database level for sensitive tables (e.g., `orders`, `journal_entries`, `employees`).
2.  **Create RLS Policies:** 
    *   *Example:* `CREATE POLICY country_isolation ON orders USING (country_code = current_setting('app.current_country_code'));`
3.  **Session Context:** When a user logs in via FastAPI, set the country context in the Postgres session: `SET app.current_country_code = 'OM';`. This guarantees that even if a developer forgets the `WHERE` clause, the database physically prevents cross-country data leaks.

---

### 💰 Strategy 4: Financial Ledger & Sub-Ledger Reconciliation
*Reference: `DATABASE_TABLE.md` (ap_ledger_entries, ar_ledger_entries, pending_journal_entries)*

You have a sophisticated financial setup. `ap_ledger_entries` (Accounts Payable) and `ar_ledger_entries` (Accounts Receivable) act as sub-ledgers, while `pending_journal_entries` acts as a Maker-Checker staging area.

**Action Plan:**
1.  **Strict Reconciliation:** Ensure that the sum of all `ap_ledger_entries` and `ar_ledger_entries` perfectly matches the control accounts in the main `journal_entries` table. Run a nightly cron job to verify this.
2.  **Maker-Checker Workflow:** Use `pending_journal_entries` strictly as a temporary staging table. Once the `approved_by` field is populated, a background worker must atomically move the data into `journal_entries` and `journal_entry_lines`, then delete the pending row. Never allow `pending_journal_entries` to grow indefinitely.
3.  **Cash Position Snapshots:** The `cash_position_snapshots` table is great for the Command Center dashboard. Ensure this is updated via an asynchronous event listener whenever a `journal_entry` affecting a `1000` (Asset) account is posted, rather than calculating it on the fly.

---

### 🚚 Strategy 5: Logistics State Machine & Immutable Audit
*Reference: `DATABASE_TABLE.md` (shipment_confirmations)*

The `shipment_confirmations` table is highly detailed, including `delivery_signature_data_url`, `confirmation_code`, and `current_hub`. This is the backbone of your Proof of Delivery (POD).

**Action Plan:**
1.  **Treat as an Event Log, Not a State Table:** `shipment_confirmations` should be an **append-only** table. Every time a package moves (Picked Up -> Hub -> Out for Delivery -> Delivered), insert a *new* row. Do not `UPDATE` existing rows.
2.  **State Machine in Backend:** The actual `shipments` table should only hold the *current* state (e.g., `status = 'IN_TRANSIT'`). The backend must use a strict state machine pattern to validate transitions (e.g., a package cannot go from `DELIVERED` back to `IN_TRANSIT` without a formal `RETURN` workflow).
3.  **Signature Verification:** Ensure `delivery_signature_data_url` points to a secure, time-limited CDN link, and the signature capture is timestamped and geo-tagged (using the driver's GPS at the moment of signing) to prevent fraud.

---

### 🕵️ Strategy 6: Zero-Trust HR & Device Fingerprinting
*Reference: `DATABASE_TABLE.md` (employee_biometrics, user_devices, employee_attendance)*

You are building a highly secure HR system. The presence of `user_devices` (with `is_trusted` flags) and `employee_biometrics` shows you are moving toward Zero-Trust.

**Action Plan:**
1.  **Device Binding:** When an employee logs in, check the `user_devices` table. If the `device_id` (fingerprint) is not present or `is_trusted = False`, force a 2FA challenge or block the login entirely.
2.  **Biometric Attendance:** Tie `employee_biometrics` directly to `employee_attendance`. When a QR code is scanned at the office kiosk, require a secondary biometric match (fingerprint/face) from the `employee_biometrics` table to prevent "buddy punching" (one employee scanning another's QR code).
3.  **Geo-Fencing Validation:** In `employee_attendance`, you have `location_lat` and `location_long`. Implement a backend validation step that calculates the Haversine distance between the scan location and the `offices` table coordinates. If it's > 50 meters, flag `is_anomaly = True`.

---

### 🗺️ Implementation Roadmap

To execute this without breaking the live system, follow this sequence:

1.  **Phase 1: Cleanup (Week 1)**
    *   Identify and drop/archive the 100 "other" tables.
    *   Add missing composite indexes (e.g., `(country_code, created_at)`) to high-volume tables like `orders` and `journal_entries`.
2.  **Phase 2: Schema Migration (Week 2)**
    *   Create PostgreSQL schemas (`hr`, `finance`, `logistics`, etc.).
    *   Update SQLAlchemy models with `__table_args__`.
    *   Run Alembic migration to move tables into schemas.
3.  **Phase 3: Security & RLS (Week 3)**
    *   Enable Row-Level Security on critical multi-tenant tables.
    *   Implement the session context setting in the FastAPI middleware.
4.  **Phase 4: Financial & Logistics Hardening (Week 4)**
    *   Implement the nightly sub-ledger reconciliation cron job.
    *   Refactor `shipment_confirmations` to be strictly append-only.
    *   Wire `user_devices` into the login and attendance flows.

By implementing these strategies, you will transform a chaotic 260-table monolith into a highly organized, secure, and scalable enterprise database architecture.

---

This is the most critical missing piece of the puzzle. In e-commerce, the **Product Catalog (Categories, Variants, and AI Uploads)** is the highest-volume, most complex part of the database. If you get this wrong, your storefront will lag, filters will break, and AI costs will spiral out of control.

Here is the **Deep Work Architectural Plan** specifically for the **Product Catalog & AI Upload System**, designed to handle millions of variants and high-throughput AI ingestion.

---

###  1. The "Variant Explosion" Problem & Solution
**The Problem:** If a supplier uploads a T-shirt with 5 sizes and 4 colors, that’s 20 variants. If they upload 1,000 products, that’s 20,000 variants. At scale, `product_variants` becomes a 100-million-row table. Standard `JOIN` queries for filtering ("Show me Red, Size M, under $50") will crash the database.

**The Solution: Hybrid Relational + JSONB Model with Partitioning.**

#### A. Category & Sub-Category Architecture (Materialized Path)
Do not use standard `parent_id` recursion for categories; it’s too slow for deep trees. Use a **Materialized Path** (`category_path`).

*   **Table:** `categories`
*   **Key Columns:**
    *   `id` (PK)
    *   `name` (e.g., "Electronics")
    *   `slug` (e.g., "electronics")
    *   `parent_id` (FK to self)
    *   `category_path` (String: `/1/15/42/` - represents the full hierarchy path).
    *   `lft` / `rgt` (Integer: Nested set boundaries for instant "all sub-categories" queries).
*   **Why:** To find all sub-categories of "Electronics", you simply query `WHERE category_path LIKE '/1/%'`. No recursive CTEs required. Instant execution.

#### B. The Variant Table (Optimized for Scale)
*   **Table:** `product_variants`
*   **Key Columns:**
    *   `id` (PK, BigInt)
    *   `product_id` (FK)
    *   `sku` (Unique String)
    *   `variant_key` (String: A hash of the attributes, e.g., `sha256("Red-M-Cotton")`. **Crucial for AI uploads to prevent duplicates**).
    *   `price`, `stock`, `weight` (Standard scalars).
    *   `attributes_json` (JSONB: `{"color": "Red", "size": "M", "material": "Cotton"}`).
*   **Optimization:**
    *   **GIN Index:** `CREATE INDEX idx_variant_attrs ON product_variants USING GIN (attributes_json);` (Allows instant filtering on any attribute).
    *   **Partitioning:** Partition this table by `product_id` (Hash) or `created_at` (Range) once it exceeds 10 million rows.

---

### 🤖 2. The AI Upload System Architecture (Preventing Database Bloat)
**The Problem:** AI is messy. It might hallucinate attributes, create duplicate variants, or fail halfway through a bulk upload. If AI writes directly to `products` and `product_variants`, your database becomes a garbage dump of failed experiments, and you have no audit trail for API costs.

**The Solution: The "Staging & Commit" Pipeline.**

#### A. New Tables for AI Governance
You must add these two tables to manage AI uploads safely:

1.  **`ai_upload_jobs`** (The Audit & Cost Tracker)
    *   `id` (PK)
    *   `supplier_id` (FK)
    *   `status` (ENUM: 'pending', 'processing', 'review', 'completed', 'failed')
    *   `model_used` (String: e.g., 'gpt-4o', 'rembg-v1')
    *   `prompt_hash` (String: To cache results and avoid re-running identical prompts).
    *   `tokens_used` (Integer: For cost tracking).
    *   `error_log` (Text)

2.  **`ai_staging_products` & `ai_staging_variants`** (The Sandbox)
    *   AI writes its generated data *here* first, not to the live tables.
    *   Includes a `confidence_score` (Float: 0.0 to 1.0) generated by the AI.
    *   Includes `requires_human_review` (Boolean).

#### B. The AI Upload Workflow
1.  **Ingest:** Supplier uploads 50 images and a CSV.
2.  **Process:** System creates an `ai_upload_job`. AI processes images (background removal) and generates descriptions/variants, saving them to `ai_staging_products`.
3.  **Validate:** System runs a "Duplicate Check" against `variant_key`. If a variant already exists, it flags it.
4.  **Commit:** Supplier reviews the "Staging" dashboard. Upon clicking "Publish", a background worker atomically moves data from `ai_staging_*` to `products` and `product_variants`.
5.  **Archive:** The staging data is archived or deleted, keeping the main tables clean.

---

### 🔍 3. Search & Filtering (The "Amazon" Experience)
To make filtering millions of variants fast without adding Elasticsearch immediately, use **PostgreSQL Native Search**.

*   **Full-Text Search:** Add a `search_vector` (tsvector) column to `products`.
    *   *Update Trigger:* Automatically update this vector whenever the title, description, or tags change.
    *   *Query:* `SELECT * FROM products WHERE search_vector @@ to_tsquery('nike & shoes');`
*   **Faceted Filtering (The Sidebar):**
    *   Do not calculate filters on the fly.
    *   Use **Materialized Views** for top-level categories (e.g., `mv_electronics_filters`) that refresh every 15 minutes via a cron job.
    *   For real-time filtering, rely on the GIN index on `attributes_json`.

---

### 🛠️ 4. Implementation Plan: Step-by-Step

#### Phase 1: Schema Refactoring (Week 1)
1.  **Alter Categories:** Add `category_path` and `lft/rgt` columns. Write a script to backfill existing categories.
2.  **Optimize Variants:** Add `variant_key` and `attributes_json` to `product_variants`. Create the GIN index.
3.  **Create AI Tables:** Deploy `ai_upload_jobs` and `ai_staging_*` tables.

#### Phase 2: AI Pipeline Integration (Week 2)
1.  **Update AI Service:** Modify `image_processor.py` and your LLM service to write to `ai_staging_products` instead of `products`.
2.  **Duplicate Prevention:** Implement the `variant_key` hashing logic (e.g., `hashlib.sha256(f"{product_id}-{color}-{size}".encode()).hexdigest()`).
3.  **Cost Tracking:** Ensure every AI API call logs its token usage to `ai_upload_jobs`.

#### Phase 3: Search & Performance (Week 3)
1.  **Enable tsvector:** Add the `search_vector` column and create the update trigger.
2.  **Partitioning:** If `product_variants` > 5M rows, implement declarative partitioning by `product_id`.
3.  **Caching:** Implement Redis caching for the Category Tree and Top-Level Filters.

---

### 💡 Summary of the "Deep Work"

| Feature | Old Approach (Risky) | New Approach (Enterprise) |
| :--- | :--- | :--- |
| **Categories** | Recursive `parent_id` (Slow) | **Materialized Path** (`/1/15/42/`) (Instant) |
| **Variants** | Flat columns (`color`, `size`) | **JSONB Attributes** + **GIN Index** (Flexible & Fast) |
| **AI Uploads** | Direct write to `products` | **Staging Tables** + **Commit Workflow** (Clean & Safe) |
| **AI Audit** | None | **`ai_upload_jobs`** (Tracks cost, model, & errors) |
| **Search** | `LIKE '%keyword%'` (Crashes DB) | **tsvector** + **GIN Indexes** (Millisecond response) |

This plan ensures that as you scale to 100,000 products and 1,000,000 variants, your database remains fast, your AI costs are tracked, and your catalog data remains clean and duplicate-free.


--------------------------------------------------------------------------------------------------------------


After reviewing the database architecture you've been building, my recommendation is **not** to continue adding tables organically. The platform has reached a level where the database itself should become a **governed ecosystem**.

From the audit, you already have roughly **263 tables**, country configuration/versioning, ledgers, logistics, KYC, audit logs, feature flags, cross-border support, AI onboarding, treasury foundations, etc. 

At this size, the biggest future risk is **complexity**, not missing tables.

---

# My Biggest Recommendation

## Don't build a database.

## Build a Database Ecosystem.

Think of ZoZI as SAP, Oracle Netsuite or Microsoft Dynamics.

Every table should belong to exactly one module.

Never create "random" tables.

---

# My Suggested Structure

```
DATABASE
│
├── Core System
│
├── User Ecosystem
│
├── Marketplace Ecosystem
│
├── Order Ecosystem
│
├── Logistics Ecosystem
│
├── Finance Ecosystem
│
├── Treasury Ecosystem
│
├── AI Ecosystem
│
├── Country Ecosystem
│
├── Security Ecosystem
│
├── Communication Ecosystem
│
├── Analytics Ecosystem
│
├── Configuration Ecosystem
│
└── Audit Ecosystem
```

Every future table must belong to one ecosystem.

---

# 1. Core Ecosystem

This should never exceed around 20 tables.

Examples

```
Users

Roles

Permissions

Countries

Cities

Languages

Currencies

Settings

Feature Flags

Audit

System Logs

Files

Media

Notifications
```

This module becomes the foundation.

---

# 2. User Ecosystem

Never mix supplier/customer fields.

Instead

```
User

↓

Profile

↓

Customer Profile

Supplier Profile

Employee Profile

Driver Profile

Admin Profile
```

Instead of

```
users

500 columns
```

---

# 3. Marketplace Ecosystem

Contains only commerce.

```
Products

Categories

Brands

Variants

Attributes

SKU

Inventory

Collections

Reviews

Wishlist

Coupons

Campaigns
```

Nothing else.

---

# 4. Order Ecosystem

Only order lifecycle.

```
Cart

Checkout

Orders

Order Items

Returns

Refunds

Invoices

Order History

QR

Status

Tracking
```

---

# 5. Logistics Ecosystem

Separate completely.

```
Logistics Partners

Fleet

Vehicle

Drivers

Pickup

Drop

Routes

Distance Matrix

Charges

Settlement

Proof of Delivery

QR Handover

GPS

Delivery SLA
```

Never mix logistics with orders.

---

# 6. Finance Ecosystem

This should become your strongest module.

Separate

```
Accounts

Journal

Ledger

AR

AP

Invoice

Payment

Wallet

Commission

Revenue

Expense

Tax

Bank

Reconciliation

Budget

Cashbook
```

Never store calculations inside application logic.

Store accounting events.

---

# 7. Treasury Ecosystem

I strongly recommend separating Treasury.

```
Payout

Settlement

COD

Reserve

Escrow

Cash Position

Cash Forecast

Liquidity

Loan

Investment

Interest

Bank Accounts

Payment Gateway
```

Treasury is not accounting.

---

# 8. AI Ecosystem

Currently AI is scattered.

Create

```
AI Jobs

AI Prompt

AI Response

AI Moderation

AI OCR

AI Embedding

AI Recommendation

AI Pricing

AI Fraud

AI Translation
```

Everything AI belongs here.

---

# 9. Country Ecosystem

You already designed this very well.

Keep it isolated.

```
Country Config

Country Tax

Country Currency

Country Logistics

Country Holidays

Country Features

Country Payment

Country Category Rules

Country Cities

Country Version
```

This is one of the strongest parts of your architecture. 

---

# 10. Security Ecosystem

Never scatter security.

```
API Keys

Permissions

Sessions

MFA

OTP

OAuth

Device

Risk

Fraud

Blocked IP

Blacklist

Whitelist

Encryption Keys
```

---

# 11. Communication Ecosystem

```
Email

SMS

Push

Chat

Internal Notes

Ticket

Support

War Room

Announcement

Notification Queue
```

---

# 12. Analytics Ecosystem

Never calculate everything live.

Create

```
Daily Snapshot

Monthly Snapshot

Supplier KPI

Customer KPI

Revenue KPI

Product KPI

Country KPI

Logistics KPI

Finance KPI
```

Use snapshots.

---

# 13. Configuration Ecosystem

Very important.

Instead of hardcoding

```
Commission %

Delivery Fee

Refund %

Reward %

```

Store everything here.

```
System Config

Country Config

Business Rules

Threshold

Feature Toggle

Workflow Config

AI Config

Notification Config
```

---

# My Biggest Suggestion

## Don't Let Every Table Reference Every Table

Current problem in many ERP systems:

```
Order

↓

Customer

↓

Supplier

↓

Driver

↓

Warehouse

↓

Country

↓

Payment

↓

Invoice

↓

Ledger

↓

Shipment

↓

Returns

↓

Complaint

↓

Review
```

One table ends up with 20 foreign keys.

Instead

```
Order

↓

Order ID

↓

Event

↓

Services consume event
```

Much cleaner.

---

# Introduce an Event-Based Architecture

Instead of:

```
Order

↓

Update 17 tables
```

Use

```
Order Created

↓

Inventory

↓

Finance

↓

Treasury

↓

Logistics

↓

Notification

↓

Analytics

↓

AI

↓

Supplier
```

This dramatically reduces coupling.

---

# Separate Master Data and Transaction Data

Many projects mix them.

Wrong

```
Products

Orders

Countries

Users

Ledger
```

Better

Master Data

```
Country

Currency

Category

Brand

Tax

Payment Gateway

Cities
```

Transactional Data

```
Orders

Payments

Invoices

Refunds

Shipments

Ledger

Returns
```

---

# Add Reference Tables

Instead of repeating values

```
Pending

Completed

Rejected

Cancelled

```

100 tables.

Create

```
status_master

workflow_master

country_master

currency_master

payment_method_master

vehicle_master

document_type_master

tax_type_master

charge_type_master

```

---

# Build a Metadata Layer

This is something most startups skip.

Instead of hardcoding:

```
Supplier Badge

```

Create

```
entity_metadata

field_metadata

validation_rules

dynamic_forms

custom_attributes

```

Then new countries and business types require less code.

---

# Naming Standards

One convention only.

For example:

* Singular or plural consistently (choose one)
* `created_at`, `updated_at`, `deleted_at` everywhere
* `country_code` on all country-specific tables
* Soft deletes via `is_deleted` + `deleted_at`
* UUID/public IDs for external APIs; integer IDs can remain internal if preferred
* Standard audit columns on all transactional tables

---

# My Overall Recommendation

From everything I've reviewed, I would **stop thinking in terms of "How many tables do I need?"** and instead think in terms of **bounded business domains**.

Your architecture already has the foundations of a large enterprise system. The next step is to enforce discipline:

* Every table belongs to one ecosystem.
* Every ecosystem has a clearly defined owner and purpose.
* Cross-ecosystem communication happens through well-defined services/events, not arbitrary foreign-key chains.
* Master data, configuration, and transactions are separated.
* New features should extend an existing ecosystem before creating new ones.

That approach will make ZoZI much easier to maintain as it grows across Oman and later into multiple GCC countries, while avoiding the complexity that often accumulates in large marketplace platforms.




After reviewing your database architecture, our previous discussions, and especially the direction described in **DATABASE_ECOSYSTEM_HANDLING_PLAN**, my recommendation is this:

> **Do not optimize for "few tables". Optimize for "domain-driven, modular, and maintainable architecture".**

Many founders worry when they see 250–400 tables. For a serious marketplace with ERP, logistics, treasury, finance, HR, and multi-country support, that number is not inherently a problem. The real question is whether the schema is organized so developers and the database can manage it efficiently.

### My recommendations

* **Adopt a Domain-Driven Database Architecture.** Organize tables into clear business domains instead of treating them as one large database. For example:

  * Identity & Access
  * Customer
  * Supplier
  * Products & Catalog
  * Orders
  * Logistics
  * Finance & Treasury
  * Accounting
  * HR
  * CRM
  * AI
  * Country Configuration
  * System Configuration
  * Audit & Security

* **Use one PostgreSQL database initially**, not multiple databases. Use schemas/modules for separation. Multiple databases increase operational complexity and reporting difficulty before you truly need them.

* **Keep strong normalization for transactional data.** Tables such as orders, payments, settlements, ledger entries, and inventory should remain normalized. Avoid denormalizing them prematurely.

* **Allow JSONB only for dynamic configuration**, not transactional records. Good uses include:

  * Country configuration
  * Feature flags
  * UI configuration
  * AI settings
  * Payment gateway metadata
  * Logistics provider capabilities

  Avoid storing orders, invoices, or financial records in JSON.

* **Create master tables for reusable concepts** instead of duplicating information:

  * Countries
  * Cities
  * Currencies
  * Units
  * Tax rates
  * Product attributes
  * Payment methods
  * Logistics methods

* **Introduce clear naming conventions.** Every table should immediately indicate its domain, for example:

  * `customer_addresses`
  * `supplier_payouts`
  * `finance_bank_transactions`
  * `logistics_delivery_assignments`

* **Separate operational tables from accounting tables.** For example:

  * Operational order status
  * Financial ledger entries
  * Bank reconciliation
  * Settlement history

  These should not be mixed.

* **Implement soft deletion consistently.** Every major transactional table should include:

  * `is_deleted`
  * `deleted_at`
  * `deleted_by`

  Keep audit logs immutable.

* **Add versioning where configuration changes matter.** Country configuration already follows this idea. Extend it where appropriate to:

  * Commission rules
  * Logistics pricing rules
  * Tax rules
  * Payment gateway settings

* **Avoid table explosion for similar entities.** If two tables differ only slightly, consider whether a shared structure with a type discriminator is more maintainable. Conversely, don't force unrelated concepts into one generic table.

* **Design for country isolation from day one.** Every business table should consistently include `country_code` (or equivalent tenant identifier) so expansion doesn't require schema changes.

* **Index intentionally.** Index:

  * Foreign keys
  * Search fields
  * Frequently filtered columns (status, country, created_at)
  * Composite indexes for common queries

  Avoid indexing every column.

* **Use partitioning only when needed.** Tables like audit logs, ledger entries, and order history can be partitioned by date or country once they reach significant size. There's no need to partition everything from the start.

* **Introduce read models/materialized views** for dashboards rather than running heavy analytical queries on transactional tables.

* **Create a unified reference numbering service.** Orders, invoices, payouts, settlements, refunds, etc., should all use centralized, configurable numbering logic.

* **Separate configuration from transactions.** Tables defining commission rules, logistics pricing, taxes, payment gateways, etc., should never contain transaction history.

* **Plan a data retention strategy.** Not every log needs to remain in the primary database forever. Archive old logs while keeping financial records according to legal requirements.

### Areas I would improve

From what I've seen, I'd focus on these architectural refinements:

* Standardize naming conventions across all modules.
* Review for duplicate or overlapping tables as features evolved.
* Ensure every financial movement ultimately links into a unified ledger.
* Formalize document storage (images, KYC documents, invoices) so the database stores metadata while object storage holds the files.
* Add architecture documentation showing relationships between modules, not just individual tables.

### What I would not change

I would **not** try to reduce the number of tables simply to make the schema look smaller. With the scope of ZoZI—a multi-country marketplace including logistics, finance, treasury, accounting, AI, HR, and administration—a few hundred well-designed tables are entirely reasonable.

The goal is not a small schema. The goal is a schema that is:

* Easy to understand.
* Easy to extend.
* Consistent.
* Highly auditable.
* Scalable across GCC markets.
* Friendly to developers.

If those goals are met, the table count becomes far less important than the quality of the design.

------------------------------------------------------------------------------------------------------------------


After reviewing the database architecture you've been building over the past months and the database audit, my recommendation is **do not continue growing the database organically by simply adding tables whenever a new feature is added**.

For a platform like ZoZI—which is intended to become a multi-country marketplace with finance, logistics, treasury, HR, CRM, AI, and compliance—you need to treat the database as an **Enterprise Data Platform**, not just an application database.

The audit already shows you have roughly **263 tables**, with strong foundations in country configuration, finance, logistics, audit logging, and security. 

## My Overall Recommendation

I would redesign the database around **Domain-Driven Design (DDD)** with clear module ownership instead of thinking in terms of individual tables.

Instead of:

```
263 random tables
```

Think:

```
Platform
│
├── Customer Domain
├── Supplier Domain
├── Marketplace Domain
├── Order Domain
├── Logistics Domain
├── Finance Domain
├── Treasury Domain
├── Security Domain
├── Country Domain
├── AI Domain
├── Analytics Domain
└── System Domain
```

---

# 1. Every Table Must Belong to a Domain

Every table should have exactly one owner.

Example:

## Customer Domain

```
customers
customer_addresses
customer_devices
customer_preferences
customer_wallets
customer_loyalty
customer_verifications
customer_notifications
```

No other module should modify these tables directly.

---

## Supplier Domain

```
suppliers
supplier_shops
supplier_kyc
supplier_documents
supplier_payouts
supplier_ratings
supplier_badges
supplier_categories
supplier_contracts
```

---

## Logistics Domain

```
logistics_partner
driver
vehicle
delivery
delivery_route
parcel_tracking
delivery_assignment
delivery_scan
delivery_sla
delivery_settlement
```

---

Everything becomes much easier to understand.

---

# 2. Build a Database Naming Standard

Right now I noticed names like

```
country_configs

country_feature_flags

admin_change_audit_logs

badge_transactions

bank_transactions
```

Some are singular.

Some plural.

Some start with admin.

Some start with country.

I recommend one standard.

For example

```
customer_addresses

customer_orders

supplier_products

supplier_settlements

logistics_deliveries

finance_transactions

finance_ledgers

treasury_accounts

country_configs

country_cities
```

Immediately you know where every table belongs.

---

# 3. Create a Database Layer Hierarchy

Never mix configuration with transactions.

Example

Configuration

```
country

currency

tax

payment_gateway

logistics_rate

category

brand

```

Master Data

```
customer

supplier

shop

warehouse

employee

```

Transactions

```
order

invoice

payment

refund

delivery

return

settlement

```

Ledger

```
journal

ledger

balance

account

treasury

```

Analytics

```
daily_summary

monthly_summary

analytics_snapshot

```

This separation makes maintenance much easier.

---

# 4. Soft Delete Everywhere

Every business table should have:

```
is_deleted

deleted_at

deleted_by

delete_reason
```

This is especially important for financial, supplier, and order records.

---

# 5. Never Delete Financial Records

Instead:

```
Cancelled

Voided

Archived

Superseded
```

This preserves auditability.

---

# 6. Introduce a Global UUID

Keep the integer primary key for performance.

Add a UUID for external references.

```
id = 125

uuid = 2f1c...
```

Benefits:

* Safer public APIs
* Easier integration
* Better data migration

---

# 7. Standard Audit Columns

Every table should contain the same metadata.

```
id

uuid

created_at

updated_at

created_by

updated_by

country_code

is_active

is_deleted

deleted_at

deleted_by

version
```

Consistency reduces development errors.

---

# 8. Introduce Table Versioning

For critical entities like products, suppliers, country configuration, and financial settings, store versions rather than overwriting values. Your country configuration versioning is already a good example. 

---

# 9. Separate Operational and Analytical Data

Don't let reporting queries hit operational tables directly.

Use summary tables or materialized views for dashboards.

---

# 10. Introduce Event Tables

Instead of updating the same row repeatedly:

```
Order Created

↓

Order Accepted

↓

Packed

↓

Picked

↓

Delivered

↓

Completed
```

Store every event.

Advantages:

* Perfect audit trail
* Easier debugging
* Better analytics

---

# 11. Build a Central Reference System

Many tables repeat values like:

```
status

type

priority

category
```

Centralize these where practical so new statuses can be configured without code changes.

---

# 12. Media Storage

Avoid storing images directly in business tables.

Instead:

```
media

media_versions

media_tags

media_usage
```

Then link media to:

* Product
* Supplier
* Customer
* Brand
* Banner

This makes media management much cleaner.

---

# 13. Multi-Country Strategy

The audit already shows a strong country configuration framework with country configs, cities, feature flags, and versioning. 

I recommend every transactional table also consistently include:

```
country_code

currency

timezone
```

This simplifies reporting and future regional deployments.

---

# 14. Security

Separate sensitive information.

Example:

```
user

↓

user_security

↓

user_devices

↓

user_sessions

↓

user_tokens

↓

user_mfa

↓

user_login_history
```

Do not mix authentication data with profile information.

---

# 15. AI Module

Create dedicated AI tables rather than embedding AI outputs into business tables.

```
ai_requests

ai_results

ai_embeddings

ai_training_feedback

ai_recommendations
```

---

# 16. Finance

Finance should be the strictest domain.

```
Chart of Accounts

↓

Journal

↓

Ledger

↓

Balance

↓

Trial Balance

↓

Income Statement

↓

Balance Sheet

↓

Cash Flow
```

Everything else should feed into the ledger rather than maintaining separate financial truths.

---

# 17. Never Duplicate Business Data

Instead of copying supplier names into orders:

```
supplier_id
```

Retrieve names through relationships.

Duplicate only immutable snapshots where legally or operationally required (for example, invoice recipient details).

---

# 18. Build a Database Governance Document

Document every table with:

| Item           | Description                    |
| -------------- | ------------------------------ |
| Purpose        | Why it exists                  |
| Owner Module   | Which domain owns it           |
| Relationships  | Connected tables               |
| Business Rules | Constraints                    |
| CRUD           | Who can create, update, delete |
| APIs           | Services using it              |
| Indexes        | Performance notes              |
| Retention      | Archive/delete policy          |

This becomes invaluable as the platform grows.

---

# 19. Table Count

Having around 263 tables is **not a problem** for a platform of ZoZI's intended scope. Large ERP and marketplace systems often have several hundred tables.

The important question is whether the schema remains understandable.

A well-organized 300-table database is preferable to a poorly structured 100-table database.

---

# Final Recommendation

If I were acting as CTO, I would not spend time trying to reduce the number of tables. I would focus on making the ecosystem easier to reason about.

My priorities would be:

1. Organize every table into a clear business domain.
2. Enforce consistent naming and metadata conventions.
3. Separate configuration, master, transactional, financial, and analytical data.
4. Ensure finance has a single authoritative ledger.
5. Move reporting workloads off transactional tables.
6. Introduce governance documentation for every table and domain.

Those changes will have a much greater impact on maintainability and long-term scalability than simply adding or removing tables. They also make it easier for new engineers—and AI coding assistants—to understand and extend the system without introducing inconsistencies.


------------------------------------------------------------------------------------------------------------------


I read the database ecosystem plan, the database tables, and the audit carefully. I think the architecture is already well above what most startups build. The challenge is no longer "How many tables should we have?" The challenge is **how to keep the ecosystem manageable over the next 10 years**.

My recommendation is **do not redesign the database again**. Instead, redesign the **database governance**.

---

# My Overall Recommendation

I would **not reduce the database further**.

Instead I would convert ZoZI into a **Domain Driven Database Ecosystem**.

Think of it as:

```
ZOZI Platform

├── Core
├── Commerce
├── Supplier
├── Customer
├── Logistics
├── Finance
├── Treasury
├── HR
├── Country
├── Media
├── AI
├── Communication
├── Audit
├── Security
├── Analytics
```

Exactly the direction described in your handling plan using PostgreSQL schemas and bounded contexts. 

---

# Biggest Missing Piece

While reading the plan I noticed one subsystem that still deserves to become a first-class citizen:

# Media Ecosystem

Currently media exists, upload sessions exist, banners have video URLs, and product media is present.   

But I think it needs to become its **own platform**.

Not

```
Product

↓

Images
```

Instead

```
Media Platform

↓

Products

↓

Chat

↓

Supplier

↓

Customer

↓

Support

↓

HR

↓

Marketing

↓

AI

↓

News

↓

Training
```

---

# I would create one Media Service

```
media_assets
```

One table.

Everything stores into this.

```
Product Images

Supplier Logo

Supplier Documents

Videos

Training Videos

Chat Images

Chat Videos

Customer Images

Invoices PDF

Profile Photos

QR Images

Marketing Banner

AI Generated Images

AI Generated Videos

Complaint Photos

Return Images

Delivery Proof

Warehouse Photos

Employee Documents

Meeting Attachments

News Media

Knowledge Base Media

Voice Notes
```

Everything.

---

Then

```
media_asset_links
```

```
media_id

entity_type

entity_id

purpose

display_order
```

Example

```
media_id = 1254

entity_type = product

entity_id = 55

purpose = gallery
```

---

Another example

```
entity_type = supplier

entity_id = 22

purpose = logo
```

---

Another

```
entity_type = order

entity_id = 1452

purpose = delivery_proof
```

Now you never create

```
product_images

supplier_images

employee_images

driver_images

complaint_images
```

Everything uses one media platform.

---

# Chat Ecosystem

Right now there are chat tables.

I would redesign slightly.

```
conversation

↓

participant

↓

message

↓

attachment

↓

reaction

↓

read_receipt

↓

typing_status

↓

message_event
```

Never

```
supplier_chat

customer_chat

admin_chat

```

One chat engine.

Every entity can use it.

---

Supported chats

```
Customer ↔ Supplier

Customer ↔ Admin

Supplier ↔ Admin

Supplier ↔ Logistics

Employee ↔ Employee

Finance

HR

Support Ticket

Incident War Room

Group Chat
```

The existing unified communications direction already points toward this. 

---

# Notification Engine

Don't let every module send notifications.

Instead

```
notification_event

↓

notification_queue

↓

notification_channel

↓

notification_delivery

↓

notification_log
```

Channels

```
Email

SMS

Push

WhatsApp

In-App

Slack

Teams
```

---

# AI Platform

AI is currently attached to products.

I would separate it.

```
ai_jobs

↓

ai_prompts

↓

ai_responses

↓

ai_costs

↓

ai_models

↓

ai_media

↓

ai_tokens

↓

ai_logs
```

Then

Every AI service uses this.

Exactly like the upload pipeline concept but for all AI.

---

# Country Platform

Already excellent.

I wouldn't change much.

Maybe

```
country_features

country_languages

country_holidays

country_currency

country_shipping

country_ai_rules

country_storage_rules
```

Everything configurable.

---

# File Storage

Very important.

Never

```
uploads/

products/

supplier/

chat/

employee/
```

Instead

```
Country

↓

Module

↓

Entity

↓

Year

↓

Month

↓

Hash

↓

Original
```

Example

```
OM/

commerce/

product/

2026/

07/

ab8d92/

shoe.webp
```

---

# Media Metadata

Every media should contain

```
id

storage_provider

bucket

folder

path

thumbnail

preview

blur_hash

checksum

sha256

mime

width

height

duration

bitrate

fps

codec

country

owner

entity

visibility

retention

virus_scan

ai_generated

ocr_completed

face_detected

duplicate_hash

deleted_at
```

Then you never scan files twice.

---

# Search Engine

Don't search directly on products.

Build

```
search_documents

↓

entity

↓

search_vector

↓

keywords

↓

embedding

↓

language

↓

country
```

Then

Products

News

Suppliers

Videos

Documents

FAQ

Everything searchable.

---

# Event Platform

I think this is the biggest missing architecture.

Every module should publish events.

```
Order Created

↓

Inventory Updated

↓

Commission Calculated

↓

Supplier Notification

↓

Customer Notification

↓

Accounting Entry

↓

Analytics Updated

↓

Email

↓

Push Notification
```

Nothing directly calls another module.

Instead

Everything publishes events.

---

# Analytics

Never calculate dashboard from live tables.

Instead

```
daily_metrics

hourly_metrics

supplier_metrics

customer_metrics

country_metrics

finance_metrics

inventory_metrics
```

Materialize.

Dashboard loads instantly.

---

# Audit

One unified audit.

Already recommended.

I fully agree.

Append only.

Partition monthly.

---

# Soft Delete

Every important table should contain

```
is_deleted

deleted_at

deleted_by

delete_reason
```

Not just some tables.

---

# Versioning

Products

Country Config

Promotions

Supplier Profile

Terms

Commission

Tax

Should all support

```
draft

approved

published

archived
```

---

# Storage Providers

Never couple storage.

```
Local

MinIO

S3

Azure

Google

Cloudflare R2

Backblaze
```

Storage should be configurable.

---

# Future Ready

I would prepare today for these future modules, even if they are not implemented immediately:

* Live streaming (supplier product showcases)
* Short videos / reels
* Voice messages in chat
* Video calling between customer and supplier
* AI image search
* AI visual duplicate detection
* AI document extraction
* AI moderation for images/videos
* CDN optimization
* Digital products (PDFs, software licenses)
* Subscription content
* Knowledge base and training academy
* Warehouse CCTV metadata (store references, not video in the database)
* IoT events (warehouse sensors, smart lockers)
* Event bus and webhook subscriptions

These don't require immediate implementation, but having a storage and entity model that can support them prevents future redesigns.

---

## Final Recommendation

After reviewing the architecture, I **would not perform another large-scale database redesign**. The foundation—bounded contexts, country-aware partitioning, unified finance, and governance—is sound.

If I were acting as CTO, I would spend the next phase on four priorities:

1. **Build a unified Media Platform** so every image, video, PDF, and attachment is managed consistently across all modules.
2. **Promote Chat, Notifications, AI, and Search into platform services** that every business module can reuse instead of creating module-specific implementations.
3. **Adopt an event-driven architecture** so commerce, logistics, finance, treasury, and analytics communicate through durable events rather than direct coupling.
4. **Invest in governance over growth**: automated schema documentation, migration discipline, partitioning, RLS enforcement, CI schema validation, and clear ownership for each database domain.

With those changes, I believe ZoZI's database would not only be capable of supporting Oman and the GCC, but would also remain maintainable as the platform expands into additional products and services over the next decade.
