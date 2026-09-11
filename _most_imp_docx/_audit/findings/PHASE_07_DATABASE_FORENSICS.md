```
=== AGENT LOG ===
PHASE: 07 — Database Forensic Audit (DB architecture & data access)
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_07_DATABASE_FORENSICS.md
SCOPE_COVERED: backend/config.py; backend/infrastructure/database/* (database.py, base.py, mixins.py, types.py, transaction.py, create_tables.py, init_db.py, rls_interceptor.py); backend/kernel/mixins.py; backend/domains/*/models/* (accounts, catalog, orders, finance, payments, logistics, audit, general_ledger); backend/alembic/env.py + versions/*; core commerce-flow services (order_engine, payment_engine, products_service); backend/requirements.txt; backend/main.py.
FILES_EXAMINED: ~40 read in full/part + ~10 workspace-wide greps (86 model files & 64 migrations enumerated)
EVIDENCE_ITEMS: ~70 file:line citations
FINDINGS_TOTAL: 24  (VERIFIED: 19 / INFERRED: 4 / UNKNOWN: 1)
SEVERITY_BREAKDOWN: BLOCKER: 1 / HIGH: 6 / MEDIUM: 9 / LOW: 4 / INFO: 4
TOP_FINDINGS:
  1. Non-atomic inventory decrement on payment-success path (read-modify-write, no lock) — backend/domains/finance/services/payments/payment_engine.py:4180-4262
  2. Runtime SQLite engine never sets PRAGMA foreign_keys=ON → FKs UNENFORCED in dev (docs claim enforced) — backend/infrastructure/database/database.py:133-146
  3. FK ondelete='SET NULL' on NOT NULL columns (carts/cart_items/addresses.user_id) — backend/domains/accounts/models/core.py:60,86,110
  4. Model vs migration CHECK-constraint drift (orders: status_code+'returned' vs status+'refunded') — order_entities.py:19 vs alembic/versions/2026_07_27_09_08-...add_check_constraints...py:20-31
  5. Tenant isolation is APP-LEVEL and FAIL-OPEN unless session is_restricted; DB-level RLS policy state contradicts docs — rls_interceptor.py:191-215; main.py:44-48; documents/02_DATABASE_IMPLEMENTATION_PLAN.md:13,22
  6. Dual schema source of truth: dev=create_all(models), prod=Alembic; baseline migration creates NO core tables — alembic/versions/...b81bfc888610_baseline...py:19-31
GAPS / NOT DETERMINABLE: Live PostgreSQL server version (docs say Neon PG18, unverified in code); whether Postgres native RLS policies are actually active in the live DB (no DB access permitted); actual runtime value of populated COUNTRY_AWARE_TABLES.
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 07 — DATABASE FORENSIC AUDIT

> Forensic, evidence-based, skeptical. READ-ONLY on the codebase. No live DB was
> queried. Application-level checks are explicitly distinguished from
> database-level enforcement. Secret **values** are never reproduced — only their
> location is cited.

---

## 0. Summary of the data layer (what it IS)

| # | Question | Answer | Status | Evidence |
|---|----------|--------|--------|----------|
| 1 | DB technology | **SQLite** (development/test) and **PostgreSQL** (production) — the same ORM targets both | VERIFIED | [backend/infrastructure/database/database.py](backend/infrastructure/database/database.py#L35-L52) |
| 2 | Version | Client libs pinned: SQLAlchemy 2.0.51, Alembic 1.18.5, asyncpg 0.31.0, psycopg2-binary 2.9.12. **PostgreSQL server version NOT pinned in code** (docs claim Neon PG18, unverified) | VERIFIED (libs) / UNKNOWN (server) | [backend/requirements.txt](backend/requirements.txt#L14-L17) |
| 3 | ORM / query builder | **SQLAlchemy 2.0** ORM (`DeclarativeBase`), sync + optional async engine; Alembic for migrations | VERIFIED | [base.py](backend/infrastructure/database/base.py#L5); [database.py](backend/infrastructure/database/database.py#L16-L26) |
| 4 | Connection config | `DATABASE_URL` env; QueuePool (PG, pool_size 50 / overflow 100 / recycle 1800 / pre_ping) ; StaticPool (SQLite); optional read replica + async engine | VERIFIED | [config.py](backend/config.py#L37-L47); [database.py](backend/infrastructure/database/database.py#L54-L90) |
| 5 | Models/entities | ~282 ORM classes across 86 model files in 16 domain packages | VERIFIED | file enumeration `backend/domains/*/models/**` |
| 13 | Transactions | Per-request `get_db()` session (autoflush off, expire_on_commit off); `db_transaction_context` / `atomic_transaction` helpers | VERIFIED | [database.py](backend/infrastructure/database/database.py#L148-L156); [transaction.py](backend/infrastructure/database/transaction.py#L20-L67) |
| 14 | Isolation assumptions | **No explicit isolation level set** anywhere → relies on DB defaults (PostgreSQL READ COMMITTED). Concurrency safety depends on `SELECT ... FOR UPDATE`, which is a **no-op on SQLite** | VERIFIED (absence) | no `isolation_level=` in [database.py](backend/infrastructure/database/database.py#L122-L133) |
| 15 | Migrations | Alembic; 64 version files; multiple historical merge heads; `batch_alter_table` for SQLite | VERIFIED | `backend/alembic/versions/*` |
| 16 | Seed data | `infrastructure/database/seed/` + `init_db.py --seed` | VERIFIED | [init_db.py](backend/infrastructure/database/init_db.py#L82-L92) |

---

## 1. Connection & engine configuration (VERIFIED)

- `DATABASE_URL` is required; empty raises at import ([database.py:31-33](backend/infrastructure/database/database.py#L31-L33)). Local default falls back to SQLite via `config.py`; Docker/prod override to PostgreSQL (repo memory `db-setup.md`).
- **Production guards (app-level, VERIFIED):** production refuses empty `DATABASE_URL`, refuses `sqlite`, bounds `DB_POOL_SIZE` 1–100, and forbids `localhost` in CORS — [config.py:267-282](backend/config.py#L267-L282); duplicate SQLite-in-prod guard at [database.py:37-41](backend/infrastructure/database/database.py#L37-L41).
- **Pooling:** PostgreSQL → `QueuePool` with `pool_pre_ping=True`; SQLite → `StaticPool` with `check_same_thread=False` ([database.py:54-90](backend/infrastructure/database/database.py#L54-L90)).
- **SQLite PRAGMAs on connect:** `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000`, `cache_size`, `temp_store=MEMORY`, `mmap_size` — [database.py:133-146](backend/infrastructure/database/database.py#L133-L146). **`PRAGMA foreign_keys=ON` is NOT among them** (see Finding H-2).
- **Async engine** built lazily from the sync URL (asyncpg / aiosqlite); `aiosqlite` is **not pinned** in requirements, so async on SQLite would fail if attempted ([database.py:158-244](backend/infrastructure/database/database.py#L158-L244); [requirements.txt:14-17](backend/requirements.txt#L14-L17)).
- **Read replica** engine (`get_read_db`) falls back to primary when `DATABASE_REPLICA_URL` is empty ([database.py:300-380](backend/infrastructure/database/database.py#L300-L380)).
- **SSL** connect args driven by `DB_SSL_MODE`/`DB_SSL_CERT`/… env for PostgreSQL ([database.py:57-66](backend/infrastructure/database/database.py#L57-L66)).

---

## 2. Schema architecture & source of truth

**VERIFIED — dual, divergent source of truth:**

- **Dev (SQLite):** schema is produced by `Base.metadata.create_all()`, with per-domain schemas **stripped** (`table.schema = None`) — [create_tables.py:570-579](backend/infrastructure/database/database.py#L570-L579); [init_db.py:57-66](backend/infrastructure/database/init_db.py#L57-L66). So in dev the **ORM models ARE the schema**.
- **Prod (PostgreSQL):** schema is produced by Alembic migrations. The **baseline migration `b81bfc888610` (down_revision=None) does NOT create the core tables** — it only patches `org_units`, `sales_order_lines`, `internal_messages`, and its own comment states *"Columns added previously by `Base.metadata.create_all()` are skipped"* — [b81bfc888610_baseline...py:19-31](backend/alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py#L19-L31).
- Many later migrations branch on dialect: *"On SQLite (dev) the ORM + `create_all` already produce the table; on Postgres this migration creates it"* (e.g. otp_codes, employee_activity_logs, split_commerce_schema). This confirms the two paths can and do **drift** (see Findings H-4, M-6).
- `create_all`/`drop_all` are **guarded** against Postgres/production (`_guard_dev_only` raises) — [database.py:551-566](backend/infrastructure/database/database.py#L551-L566). Startup bootstrap flags default **off**: `bootstrap_schema_on_startup=False`, `run_legacy_migrations_on_startup=False` ([config.py:94-95](backend/config.py#L94-L95)).
- **Per-domain PostgreSQL schemas** (`catalog`, `orders`, `finance`, `accounts`, `country`, `logistics`, `audit`, …) declared via `__table_args__ = {"schema": ...}`. On SQLite they are collapsed to flat tables via a **`schema_translate_map`** that maps every domain schema → `None` ([database.py:96-133](backend/infrastructure/database/database.py#L96-L133)). This map must be manually kept in sync with the models — a comment says so — which is itself a drift surface.

---

## 3. Mixins / shared column contracts (VERIFIED)

| Mixin | Columns | File |
|-------|---------|------|
| `TimestampMixin` (kernel) | created_at (indexed), updated_at, DB-side defaults | [kernel/mixins.py:4-16](backend/kernel/mixins.py#L4-L16) |
| `AuditMixin` | created_at, created_by_id→accounts.users.id, updated_at, updated_by_id | [infrastructure/database/mixins.py:11-22](backend/infrastructure/database/mixins.py#L11-L22) |
| `SoftDeleteMixin` | is_deleted, deleted_at, deleted_by_id + `soft_delete()/restore()` | [mixins.py:24-45](backend/infrastructure/database/mixins.py#L24-L45) |
| `TenantMixin` | country_code String(2) NOT NULL, indexed (Law 5) | [mixins.py:47-56](backend/infrastructure/database/mixins.py#L47-L56) |
| `VersionMixin` | version Integer NOT NULL default 1 (optimistic lock) | [mixins.py:58-72](backend/infrastructure/database/mixins.py#L58-L72) |
| `GUID` type | Postgres UUID native / CHAR(32) on SQLite | [types.py:14-42](backend/infrastructure/database/types.py#L14-L42) |

Note: many models **inline** `is_deleted`/`version`/`country_code`/audit columns rather than composing the mixins (e.g. `Order`, `OrderItem`, `Product`), so the contract is duplicated by hand and enforced only by convention.

---

## 4. Core commerce-flow trace: User → Cart → Order → Payment → Inventory

```
accounts.users (User)
  ├─ carts.user_id ─────────────► FK accounts.users.id  ondelete=SET NULL  [col NOT NULL — see H-3]
  ├─ cart_items.user_id ────────► FK accounts.users.id  ondelete=SET NULL  [col NOT NULL — see H-3]
  │    └─ cart_items.product_id ► FK catalog.products.id ondelete=CASCADE   [no UNIQUE(user_id,product_id) — see M-7]
  ├─ orders.orders.user_id ─────► FK accounts.users.id  ondelete=RESTRICT
  │    orders.orders.customer_id► FK accounts.users.id  ondelete=RESTRICT
  │    (NO FK from order → cart; cart→order is application logic only)
  │    └─ order_items.order_id ─► FK orders.orders.id   ondelete=RESTRICT
  │         order_items.product_id► FK catalog.products.id ondelete=RESTRICT
  │         order_items.variant_id  Integer, NO FK  [see L-3]
  ├─ finance.payments.order_id ─► FK orders.orders.id  ondelete=CASCADE
  └─ payments.payment_intents.order_id ► FK orders.orders.id ondelete=CASCADE
Inventory = catalog.products.stock (Integer column). NO dedicated inventory table.
```

**Inventory model reality (VERIFIED):**
- Stock is a plain integer column on `catalog.products.stock` (default 0) and `catalog.product_variants.stock`; there is **no `Inventory`/`StockReservation` entity** ([products.py:59, 189](backend/domains/catalog/models/products.py#L59)).
- A `logistics.stock_movements` ledger table exists ([erp.py:240-264](backend/domains/logistics/models/erp.py#L240-L264)) **but is not written by the checkout/payment path** — grep for `StockMovement(` returns only the class definition, no instantiation. So inventory changes during checkout have **no audit/history ledger**.
- Order creation locks product rows with `.with_for_update()` and validates availability, but **does not decrement**; a code comment defers decrement to payment confirmation — [order_engine.py:225-231](backend/domains/orders/services/core/order_engine.py#L225-L231) and [order_engine.py:827](backend/domains/orders/services/core/order_engine.py#L827). The FOR UPDATE lock is released at the order-create commit, so it does **not** span the later decrement (check-then-act gap → B-1).

---

## 5. Major table / model matrix

| Model / Table | Purpose | Relationships (FK → ondelete) | Important Constraints | Indexes | Evidence |
|---|---|---|---|---|---|
| `accounts.users` (User) | Identity for all roles (customer/supplier/admin/employee/logistics) | self-FK referred_by_user_id→users (SET NULL) | email UNIQUE, hashed_password NOT NULL, role default 'customer', country_code NOT NULL; role CHECK **only in migration** | ix email, ix country_code | [user.py:29-90](backend/domains/accounts/models/user.py#L29-L90); [20260727_0908 migration:43-48](backend/alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py#L43-L48) |
| `accounts.carts` (Cart) | One cart per user | user_id→users **SET NULL** (col NOT NULL) | is_deleted; country_code NOT NULL | ix user_id, ix country_code | [core.py:80-92](backend/domains/accounts/models/core.py#L80-L92) |
| `accounts.cart_items` (CartItem) | Cart line items | user_id→users SET NULL (NOT NULL); product_id→products CASCADE | **no UNIQUE(user_id,product_id)** | ix_cart_items_user_product (non-unique), ix_cart_items_created | [core.py:95-121](backend/domains/accounts/models/core.py#L95-L121) |
| `accounts.addresses` (Address) | Shipping/billing addresses (PII) | user_id→users SET NULL (NOT NULL) | country_code NOT NULL | ix user_id, ix country_code | [core.py:53-77](backend/domains/accounts/models/core.py#L53-L77) |
| `catalog.products` (Product) | Catalog + **inventory counter** | supplier_id→users SET NULL; category_id→categories RESTRICT; country_code→country_configs.code RESTRICT | slug/sku/barcode/slug_hash UNIQUE; **no CHECK stock>=0**; price NUMERIC(10,2) | ix_products_supplier_active, _category_active, _created_sort, _country_status | [products.py:39-115](backend/domains/catalog/models/products.py#L39-L115) |
| `catalog.product_variants` | Per-variant stock/price | product_id→products CASCADE; country_code→country_configs RESTRICT | UNIQUE(product_id, variant_key); sku/barcode UNIQUE | ix size/color/material/pattern/gender/variant_key | [products.py:167-197](backend/domains/catalog/models/products.py#L167-L197) |
| `orders.orders` (Order) | Order aggregate | user_id/customer_id→users RESTRICT; country_code→country_configs RESTRICT | order_number/tracking_number UNIQUE; **CHECK chk_orders_status_valid on `status_code`** (model); duplicate money cols (subtotal/subtotal_amount, total/total_amount); currency default 'USD' | ix user_id, customer_id, status_code, country+created | [order_entities.py:14-70](backend/domains/orders/models/order_entities.py#L14-L70) |
| `orders.order_items` (OrderItem) | Order line snapshot | order_id→orders RESTRICT; product_id→products RESTRICT; **variant_id no FK** | version col | ix order_id, product_id, country+created | [order_entities.py:72-104](backend/domains/orders/models/order_entities.py#L72-L104) |
| `orders.return_requests` | Returns/exchanges | order_id→orders RESTRICT; customer_id→users RESTRICT | **CHECK chk_return_requests_status_valid on `status_code`** (model) | ix country+created | [order_entities.py:135-176](backend/domains/orders/models/order_entities.py#L135-L176) |
| `finance.payments` (Payment) | Customer payment for order | order_id→orders CASCADE; country_code→country_configs SET NULL | CHECK amount>=0; CHECK status IN(...); amount NUMERIC(10,2) | ix order_id, status+created, provider+status | [payments.py:43-68](backend/domains/finance/models/payments.py#L43-L68) |
| `finance.payouts` (Payout) | Platform→supplier payout | supplier_id→users RESTRICT; order_id→orders SET NULL; country_code SET NULL | amount NUMERIC(12,2) | ix supplier_id, order_id | [payments.py:135-166](backend/domains/finance/models/payments.py#L135-L166) |
| `finance.payment_gateway_connections` | Gateway config incl. **secrets** | updated_by_id→users SET NULL | secret_key/webhook_secret plain String; credentials JSON; GIN indexes **Postgres-only** | idx GIN (PG only) | [payments.py:88-133](backend/domains/finance/models/payments.py#L88-L133) |
| `finance.transaction_ledgers` | Money split per order (commission/VAT/net) | user/supplier/order/order_item/shipment/logistics_partner → RESTRICT | CHECK amount>=0; CHECK currency IN(10-currency list); NUMERIC(12,2) | ix country, country+created | [general_ledger.py:39-78](backend/domains/finance/models/general_ledger.py#L39-L78) |
| `finance.journal_entries` / `_lines` | Double-entry GL | line→entry CASCADE; period/reversal self-FK RESTRICT | reference_number UNIQUE; **balance (debits=credits) is app-enforced, no cross-row DB CHECK** | ix entry_date, ref, country | [general_ledger.py:105-140](backend/domains/finance/models/general_ledger.py#L105-L140) |
| `payments.payment_intents` | PSP-agnostic intent | order_id→orders CASCADE; user_id→users CASCADE; finance_payment_id→payments SET NULL | UNIQUE(provider,provider_intent_id); CHECK status IN(...); CHECK amount>0; **amount NUMERIC(18,4)** | ix order, user | [payment_models.py:157-210](backend/domains/payments/models/payment_models.py#L157-L210) |
| `payments.payment_attempts` | Idempotent retry record | payment_id→finance.payments CASCADE | UNIQUE(payment_id,attempt_no); CHECK attempt_no>=1; CHECK status IN(...) | ix payment_id, attempted_at | [payment_models.py:72-107](backend/domains/payments/models/payment_models.py#L72-L107) |
| `payments.refunds` | Refund record | payment_id→finance.payments CASCADE; requested_by/approved_by→users | CHECK amount>0; CHECK status IN(...); NUMERIC(18,4) | ix_refunds_payment | [payment_models.py:110-145](backend/domains/payments/models/payment_models.py#L110-L145) |
| `logistics.stock_movements` | Inventory ledger (**unused in checkout**) | product_id→products RESTRICT; warehouse_id→warehouses RESTRICT | quantity_change/after NUMERIC(14,2) | ix country+created | [erp.py:240-264](backend/domains/logistics/models/erp.py#L240-L264) |
| `audit.audit_logs` (AuditLog) | Action audit trail | user_id→users SET NULL; country_code→country_configs | **has `is_deleted` (soft-deletable)** — contradicts "immutable audit"; no hash column in model | ix user_id, is_deleted, country | [audit_schema_models.py:12-27](backend/domains/audit/models/audit_schema_models.py#L12-L27) |

---

## 6. FINDINGS (severity-ordered)

### B-1 (BLOCKER) — Inventory decrement on payment success is non-atomic (oversell race)
- **Status:** VERIFIED. On payment success, the finalizer loads products with a plain `db.query(Product).filter(Product.id.in_(...)).all()` (**no `with_for_update`, no lock**), checks `stock < requested`, then does an ORM read-modify-write `new_stock = stock - requested_quantity; setattr(product,"stock",new_stock)` — [payment_engine.py:4180-4262](backend/domains/finance/services/payments/payment_engine.py#L4180-L4262).
- Two concurrent payment confirmations for the same product can both read the same `stock` and both write a decrement → **oversell / negative stock**. The `version` optimistic-lock column exists but is **not checked or bumped** in this path.
- **Contradiction:** a correct atomic implementation exists (`atomic_stock_decrement`, `finalize_inventory_atomic`) using a conditional `UPDATE ... SET stock = stock - :qty WHERE ... AND stock >= :qty` ([products_service.py:444-486](backend/domains/catalog/services/products/products_service.py#L444-L486)) but the payment-success path uses the unsafe ORM version instead. Report both; do not assume they are reconciled.
- **Impact:** data-integrity / financial (paid orders that cannot be fulfilled). Confidence: High.

### H-2 (HIGH) — SQLite runtime never enables foreign keys → FKs unenforced in dev
- **Status:** VERIFIED. The `@event.listens_for(engine,"connect")` PRAGMA handler sets WAL/synchronous/busy_timeout/cache/temp/mmap but **omits `PRAGMA foreign_keys=ON`** — [database.py:133-146](backend/infrastructure/database/database.py#L133-L146). SQLite defaults FK enforcement OFF per-connection. `foreign_keys=ON` appears only in debug/seed/test scripts, never in the runtime engine (grep). 
- **Contradiction with docs:** `documents/CODEBASE_STATUS_MATRIX.md:1618` claims *"Foreign Keys ✅ Enforced; SQLite PRAGMA foreign_keys=ON"*. Not true at runtime.
- **Impact:** In dev/test every `ondelete` rule (RESTRICT/CASCADE/SET NULL) and referential integrity is silently unenforced; bugs that Postgres would reject pass in dev. Confidence: High.

### H-3 (HIGH) — `ondelete='SET NULL'` declared on `NOT NULL` columns (self-contradictory FK)
- **Status:** VERIFIED. `carts.user_id`, `cart_items.user_id`, `addresses.user_id` are `nullable=False` yet `ForeignKey(..., ondelete='SET NULL')` — [core.py:60, 86, 110](backend/domains/accounts/models/core.py#L60). Same pattern on `products.supplier_id` is fine (nullable) but the three accounts tables are NOT NULL.
- **Impact:** On PostgreSQL, deleting a referenced user makes the DB attempt `SET NULL` on a NOT NULL column → the delete **fails** (or, if a different path is taken, integrity error). On SQLite it is moot because FKs are off (H-2). Confidence: High.

### H-4 (HIGH) — Model CHECK constraints disagree with migration CHECK constraints
- **Status:** VERIFIED. Orders:
  - Model: `CheckConstraint("status_code IN ('pending','confirmed','processing','shipped','delivered','cancelled','returned')", name='chk_orders_status_valid')` on column **`status_code`** — [order_entities.py:19](backend/domains/orders/models/order_entities.py#L19).
  - Migration: `chk_order_status_valid` on column **`status`** with values `('pending','processing','confirmed','shipped','delivered','cancelled','refunded')` — [migration:20-24](backend/alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py#L20-L24).
  - Different **column** (`status_code` vs `status`), different **constraint name**, different **value set** ('returned' vs 'refunded'). The Order model does not even define a `status` column.
- Same divergence for `return_requests` (model `chk_return_requests_status_valid` on `status_code` includes `'cancelled'`; migration `chk_return_status_valid` on `status` omits it).
- **Impact:** On SQLite (create_all) the model constraint applies; on Postgres (migration) a different constraint on a possibly-legacy column applies. Runtime validation differs by environment. Confidence: High.

### H-5 (HIGH) — Tenant/country isolation is application-level and FAIL-OPEN; DB-level RLS state contradicts docs
- **Status:** VERIFIED (mechanism) / UNKNOWN (live PG policy state).
- Isolation is implemented as a SQLAlchemy `before_execute` interceptor that injects `WHERE country_code IN (...)` for tables in `COUNTRY_AWARE_TABLES` — [rls_interceptor.py:191-215](backend/infrastructure/database/rls_interceptor.py#L191-L215). It is registered in `main.py` via `instrument_rls(engine)` and `install_rls_policies(engine)` — [main.py:44-52](backend/main.py#L44-L52).
- **Fail-open:** `if not is_restricted: return clause` — the context var `rls_is_restricted_ctx` defaults to **False**, so any session that is not explicitly marked restricted (background jobs, workers, seeds, or any request the middleware didn't tag) executes **unscoped across all countries** — [rls_interceptor.py:195-197, 10-11](backend/infrastructure/database/rls_interceptor.py#L195-L197). Only restricted sessions get filtered, and only they fail-closed when scope is missing.
- **Contradictions to report (do not resolve):** `documents/02_DATABASE_IMPLEMENTATION_PLAN.md:13,22` states *"0 RLS policies (interceptor only)"*, yet `main.py:48` calls `install_rls_policies(engine)` (which emits `CREATE POLICY` SQL via `generate_rls_policy_sql`). `.kilo/context/summary.md:14,58` states *"RLS is a runtime no-op (`instrument_rls` never called)"*, yet `main.py:44` calls it. These are direct source/doc contradictions; the **actual live policy state is not determinable without DB access**.
- **Impact:** Multi-tenant (country) data-leak risk on any unscoped code path. Confidence: High (mechanism) / Low (live effect).

### H-6 (HIGH) — `atomic_stock_decrement` raw SQL is PostgreSQL-only and would fail on SQLite
- **Status:** VERIFIED. `UPDATE catalog.products SET stock = stock - :qty, updated_at = NOW() WHERE ...` — [products_service.py:448, 477](backend/domains/catalog/services/products/products_service.py#L448-L477). Uses `NOW()` (undefined function on SQLite) and the **schema-qualified `catalog.products`** (SQLite has flat `products`, no `catalog` schema). This safe path therefore cannot run in dev/SQLite, leaving only the unsafe ORM decrement (B-1) exercised there.
- **Impact:** The one correct concurrency-safe decrement is environment-locked to Postgres; behavior diverges by DB. Confidence: High.

### M-6 (MEDIUM) — Schema drift risk from dual source of truth
See §2. Baseline migration creates no core tables; dev relies on `create_all`. Any column/constraint present in models but never migrated will exist in dev and be **absent in prod** (and vice-versa). Evidence: [b81bfc888610:19-31](backend/alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py#L19-L31) + dialect-branching migrations. Confidence: High.

### M-7 (MEDIUM) — `cart_items` has no UNIQUE(user_id, product_id)
- **Status:** VERIFIED (absence). Only a **non-unique** index `ix_cart_items_user_product` exists ([core.py:97-101](backend/domains/accounts/models/core.py#L97-L101)); grep for a cart uniqueness constraint returns nothing. Concurrent "add to cart" can create duplicate rows; correctness depends on app-level upsert logic. Confidence: High.

### M-8 (MEDIUM) — Money precision is inconsistent across the ledger
- **Status:** VERIFIED. `NUMERIC(10,2)` on orders/payments ([order_entities.py:34-40](backend/domains/orders/models/order_entities.py#L34-L40); [payments.py:56](backend/domains/finance/models/payments.py#L56)); `NUMERIC(12,2)` on transaction_ledgers/payouts; `NUMERIC(18,4)` on payments-domain intents/refunds ([payment_models.py:131,187](backend/domains/payments/models/payment_models.py#L131)); `NUMERIC(14,2)` on stock_movements. Mixed scale (2 vs 4 dp) across tables that exchange money → rounding/loss-of-precision risk at boundaries. Confidence: High.

### M-9 (MEDIUM) — Duplicate `instrument_rls` definitions (symbol shadowing)
- **Status:** VERIFIED. Two defs: the full version that populates `COUNTRY_AWARE_TABLES` at [rls_interceptor.py:49](backend/infrastructure/database/rls_interceptor.py#L49) and a bare `event.listen`-only version at [rls_interceptor.py:218-220](backend/infrastructure/database/rls_interceptor.py#L218-L220). The later definition **shadows** the earlier, so the one `main.py` calls does **not** repopulate the country-aware registry (a test, `test_rls_runtime.py:100-104`, exists precisely to forbid this). Confidence: High.

### M-10 (MEDIUM) — Audit log is soft-deletable; WORM hash only in migration (model/migration drift)
- **Status:** VERIFIED. `audit_logs` model carries `is_deleted` and no hash/chain column ([audit_schema_models.py:24](backend/domains/audit/models/audit_schema_models.py#L24)); a separate migration `20260827_audit_logs_worm_hash` adds WORM hashing on Postgres. So the "immutable/append-only audit" property is (a) not represented in the ORM model and (b) contradicted by a soft-delete flag. Confidence: High.

### M-11 (MEDIUM) — Optimistic-lock `version` present but not enforced on hot writes
- **Status:** INFERRED. `VersionMixin`/inline `version` columns exist widely, but the inventory decrement (B-1) and `update_stock` ([products_service.py:420-441](backend/domains/catalog/services/products/products_service.py#L420-L441)) mutate rows without a `version`-guarded UPDATE. No `version_id_col` mapper config observed. Confidence: Medium.

### M-12 (MEDIUM) — `stock_movements` inventory ledger is defined but not written on checkout
- **Status:** VERIFIED (absence of instantiation). Inventory changes on `products.stock` leave no movement/audit row in the checkout/payment path (grep `StockMovement(` → class def only). Confidence: High.

### M-13 (MEDIUM) — No explicit transaction isolation level; concurrency safety leans on FOR UPDATE (SQLite no-op)
- **Status:** VERIFIED. No `isolation_level` set on any engine ([database.py:122-133](backend/infrastructure/database/database.py#L122-L133)). `with_for_update()` is used in only 3 places (order_engine, coupon_service, db_read) and is a **no-op on SQLite**. Confidence: High.

### M-14 (MEDIUM) — GIN / partitioning / search-vector features are Postgres-only, absent in dev schema
- **Status:** VERIFIED. `_get_table_args()` adds GIN indexes only when `DATABASE_URL` starts with postgres ([payments.py:29-39](backend/domains/finance/models/payments.py#L29-L39)); migrations add range partitioning, materialized views, `products` search-vector trigger — all Postgres-only. Dev (SQLite) runs a structurally different schema. Confidence: High.

### L-1 (LOW) — Sensitive data at rest: encryption is application-level, not a DB column type
- **Status:** VERIFIED. `payment_gateway_connections.secret_key/webhook_secret/public_key` are plain `String` and `credentials` is `JSON` ([payments.py:112-116, 101](backend/domains/finance/models/payments.py#L101-L116)). Confidentiality relies on app-level `encrypt_secret`/`decrypt_secret` ([payment_engine.py:1834-1974](backend/domains/finance/services/payments/payment_engine.py#L1834-L1974); [gateway_paypal.py:15,434](backend/domains/finance/services/payments/gateway_paypal.py#L15)). There is **no encrypted SQLAlchemy type** (types.py has only `GUID`), so the DB stores whatever the app writes; any code path that forgets to encrypt writes plaintext. Secret values not reproduced. Confidence: High.

### L-2 (LOW) — PII stored in plaintext columns
- **Status:** VERIFIED. `addresses` (full_name/phone/address lines), `orders` (customer_phone/shipping_*), `user_sessions`/`user_login_histories` (ip_address, user_agent) are plaintext ([core.py:53-77](backend/domains/accounts/models/core.py#L53-L77); [user.py:104-160](backend/domains/accounts/models/user.py#L104-L160)). Passwords are hashed (`hashed_password`, [user.py:37](backend/domains/accounts/models/user.py#L37)); hashing algorithm is set elsewhere (not in models). Confidence: High.

### L-3 (LOW) — `order_items.variant_id` and `order.selected_partner_id/service_area_id` are FK-less integers
- **Status:** VERIFIED. `order_items.variant_id = Column(Integer, nullable=True)` with no ForeignKey ([order_entities.py:88](backend/domains/orders/models/order_entities.py#L88)); `Order.selected_partner_id/selected_service_area_id` likewise ([order_entities.py:52-53](backend/domains/orders/models/order_entities.py#L52-L53)). Dangling references are possible; integrity is app-only. Confidence: High.

### L-4 (LOW) — Duplicate/denormalized money columns on `orders`
- **Status:** VERIFIED. `orders` carries both `subtotal`+`subtotal_amount`, `total`+`total_amount`, `shipping_fee`+`shipping_amount`, `tax_amount`+`vat_amount` ([order_entities.py:33-41](backend/domains/orders/models/order_entities.py#L33-L41)). Two columns for the same quantity risk divergence with no DB constraint keeping them equal. Confidence: High.

### INFO
- **I-1 Soft delete is manual, not global.** Reads filter `is_deleted == False` per query (e.g. [products_service.py:244](backend/domains/catalog/services/products/products_service.py#L244), search services). No global event/filter; any query that omits the predicate returns deleted rows. VERIFIED.
- **I-2 Pagination infrastructure exists and is used.** Keyset helpers `cursor_paginate_asc/desc` wired through each domain's `ports.py` `_keyset_page` ([pagination.py](backend/infrastructure/utils/pagination.py); e.g. [orders/ports.py:51](backend/domains/orders/ports.py#L51)). However many service queries still terminate in `.all()` without a cursor (search/recommendation services), so coverage is **not universal** → residual unbounded-query risk. VERIFIED / INFERRED.
- **I-3 Raw SQL is parameterized.** `text()` usage (stock decrement, db_read, rls SQL generation) uses bound params, not string interpolation → no SQL-injection surface found in the DB layer. VERIFIED.
- **I-4 Relationship eager-loading is partial.** `User` relationships use `lazy="selectin"` (mitigates N+1); `Order.items/shipments` are default-lazy. A dedicated `test_shipments_no_n_plus_1` exists, implying N+1 has been a concern. General N+1 risk on order/shipment iteration is INFERRED.

---

## 7. Data-integrity & race-condition summary

| Risk | Enforcement reality | Evidence |
|------|--------------------|----------|
| Oversell | App-level FOR UPDATE at order-create only; **non-atomic ORM decrement at payment** | B-1, order_engine.py:225-231/827, payment_engine.py:4180-4262 |
| Referential integrity | Postgres FKs only; **SQLite FKs OFF at runtime** | H-2 |
| User deletion | `SET NULL` on `NOT NULL` cart/address columns → PG delete fails | H-3 |
| Status validity | **Different** CHECK sets in model vs migration | H-4 |
| Tenant leak | App interceptor, **fail-open** unless is_restricted; native RLS state unverified | H-5 |
| Duplicate cart rows | No UNIQUE(user_id,product_id) | M-7 |
| Ledger balance | Double-entry balancing is **app-enforced only** (no cross-row DB CHECK) | §5 journal_entries |

---

## 8. Skepticism / gaps

- No live database was queried (hard constraint). All statements about **runtime** SQLite behavior are derived from the connect-event code, not observed.
- Whether PostgreSQL native RLS policies are actually present/enabled in the deployed DB is **NOT DETERMINABLE FROM AVAILABLE CODE** — code both installs them (`install_rls_policies`) and is documented as having "0 policies"; reported as a contradiction, not resolved.
- PostgreSQL **server** version is not pinned in the repo; the "Neon PG18" claim lives only in narrative docs.
- I did not exhaustively open all 86 model files; domain models outside the User→Cart→Order→Payment→Inventory trace (analytics, comms, hr, country, promotions) were sampled, not fully audited. Their constraint/FK posture is **UNKNOWN** beyond what the greps surfaced.
- App-level validators (Pydantic schemas, service guards) were treated as **application-level** and never counted as DB enforcement, per MASTER_RULES.
```
