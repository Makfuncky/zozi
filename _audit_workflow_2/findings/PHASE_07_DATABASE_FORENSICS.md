# TASK 07 — DATABASE FORENSIC AUDIT

## Audit Scope
- **Repository:** D:\Projects\10- E-COMMERCE WEBSITE\zozi
- **Inspected paths:** backend/infrastructure/database/, backend/alembic/, backend/domains/, backend/modules/, backend/config.py, backend/.env
- **Date:** 2026-09-11

---

## 1. Database Technology

**Status: VERIFIED**

| Environment | Technology | Evidence |
|-------------|-----------|----------|
| Production | PostgreSQL (Neon) | backend/.env line 23: DATABASE_URL=postgresql://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require |
| Development | SQLite (fallback) | backend/infrastructure/database/database.py lines 36-48; backend/.env.example line 4 |

Production explicitly forbids SQLite:
- backend/infrastructure/database/database.py lines 37-42 raise ValueError if APP_ENV=production and DATABASE_URL starts with sqlite.

---

## 2. Database Version

**Status: UNKNOWN**

The exact PostgreSQL server version is not determinable from the repository. The health-check query SELECT current_database(), current_user, version() exists at backend/infrastructure/database/database.py line 476, but it is only executed at runtime and its result is not checked into source.

Client-side versions:
- SQLAlchemy 2.0.51 (backend/requirements.txt line 14)
- Alembic 1.18.5 (backend/requirements.txt line 15)
- asyncpg 0.31.0 (backend/requirements.txt line 16)
- psycopg2-binary 2.9.12 (backend/requirements.txt line 17)

---

## 3. ORM / Query Builder

**Status: VERIFIED**

- **ORM:** SQLAlchemy 2.0.51 (confirmed in backend/requirements.txt line 14 and backend/infrastructure/database/database.py line 10)
- **Query builder style:** Declarative Base with Mapped/mapped_column idiom in mixins (backend/infrastructure/database/mixins.py lines 63-67)
- **Async support:** Optional async engine via asyncpg (backend/infrastructure/database/database.py lines 14-25, 178-230)
- **Read layer:** Centralized read helpers in backend/infrastructure/database/db_read.py (functions: all_rows, first, one, count, scalar, rows, etc.)
- **Write layer:** Centralized write helpers in backend/infrastructure/database/db_write.py (functions: add, commit, flush, create, instantiate, etc.)

---

## 4. Database Connection Configuration

**Status: VERIFIED**

| Parameter | Source | Details |
|-----------|--------|---------|
| DATABASE_URL | backend/.env line 23 | PostgreSQL Neon connection string with SSL |
| DB_POOL_SIZE | backend/.env line 24 / backend/config.py line 44 | Default 50 |
| DB_MAX_OVERFLOW | backend/.env line 25 / backend/config.py line 45 | Default 100 |
| DB_POOL_RECYCLE | backend/.env line 26 / backend/config.py line 46 | Default 300s |
| DB_CONNECT_TIMEOUT | backend/.env line 27 / backend/config.py line 47 | Default 10s |
| DB_STATEMENT_TIMEOUT | backend/config.py line 48 | Default 60000ms (set but not visibly wired to engine execution_options) |
| DB_SSL_MODE | backend/.env line 28 | require |
| DATABASE_REPLICA_URL | backend/config.py line 40 | Optional; falls back to primary if empty |
| Search path | backend/infrastructure/database/database.py line 89 | public,analytics,audit,commerce,configuration,country,customer,finance,hr,logistics,media,security,supplier |

Connection pool implementation:
- PostgreSQL: QueuePool with pool_pre_ping=True, pool_recycle, pool_timeout (backend/infrastructure/database/database.py lines 68-75)
- SQLite: StaticPool with WAL pragmas (backend/infrastructure/database/database.py lines 53-56, 129-141)
- Read replica engine: Separate create_engine with same pool config (backend/infrastructure/database/database.py lines 288-354)

---

## 5. Models / Entities

**Status: VERIFIED**

Models are organized by domain under backend/domains/*/models/. Key model files:

| Domain | File | Key Models |
|--------|------|-----------|
| accounts | backend/domains/accounts/models/user.py | User, UserSession, UserLoginHistory, UserDevice, PasswordResetToken, EmailVerificationToken, RevokedToken |
| accounts | backend/domains/accounts/models/core.py | Address, Cart, CartItem, AuditLog, SupportTicket |
| catalog | backend/domains/catalog/models/products.py | Category, Product, ProductVariant, Review, WishlistItem, Wishlist, ProductVideo, ProductFilterMetadata, ProductFilterOption |
| orders | backend/domains/orders/models/order_entities.py | Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification |
| finance | backend/domains/finance/models/payments.py | Payment, Payout, LogisticsPartnerPayout, PaymentGatewayConnection, PaymentReconciliationRun |
| finance | backend/domains/finance/models/general_ledger.py | TransactionLedger, SupplierSettlement, JournalEntry, JournalEntryLine, Account, AccountGroup, AccountBalance, Invoice, RefundLedger, BankTransaction, etc. |
| logistics | backend/domains/logistics/models/logistics_entities.py | LogisticsPartner, Shipment, ShipmentEvent, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsVehicleRule |
| suppliers | backend/domains/suppliers/models/suppliers.py | SupplierProfile, SupplierDocument, etc. |
| customers | backend/domains/customers/models/customer_schema_models.py | Customer, Referral, ReferralPointEvent, CrossCountrySession |
| promotions | backend/domains/promotions/models/promotions.py | Banner, FlashSale, FlashSaleItem, Coupon, CouponUsage, PromotionLedgerEntry |
| hr | backend/domains/hr/models/employee_models.py | Employee, Office, etc. |
| country | backend/domains/country/models/countries.py | CountryConfig |
| comms | backend/domains/comms/models/communication_schema_models.py | SupportTicket, SupportTicketReply, TicketAttachment, etc. |
| audit | backend/domains/audit/models/audit_schema_models.py | AuditLog, CommandCenterView |
| governance | backend/domains/governance/models/core.py | SystemHealthEvent, UserBrowsingHistory, ShippingCarrier |

All models inherit from infrastructure.database.base.Base (backend/infrastructure/database/base.py).

---

## 6. Tables

**Status: VERIFIED**

The system uses PostgreSQL schemas to organize tables. The bounded-context migration maps tables to schemas. Key schemas and tables:

| Schema | Example Tables |
|--------|---------------|
| accounts | users, addresses, carts, cart_items, user_sessions, user_login_histories, user_devices, password_reset_tokens, email_verification_tokens, revoked_tokens |
| catalog | products, categories, product_variants, reviews, wishlist_items, wishlists, product_videos, product_filter_metadatas, product_filter_options |
| orders | orders, order_items, order_logistics_allocations, return_requests, order_notifications |
| finance | payments, payouts, logistics_partner_payouts, transaction_ledgers, supplier_settlements, journal_entries, journal_entry_lines, accounts, account_groups, account_balances, invoices, invoice_items, refund_ledgers, bank_transactions, vat_remittances, cash_accounts, cash_transactions, treasury_accounts, treasury_transactions, payout_batches, payout_batch_items |
| logistics | shipments, shipment_events, logistics_partners, logistics_partner_profiles, logistics_partner_service_areas, logistics_pricing_profiles, logistics_vehicle_rules, logistics_category_pricing_rules |
| suppliers | supplier_profiles, supplier_documents, supplier_bank_accounts, supplier_fraud_indicators, supplier_kyc_requirements, supplier_notification_preferences, supplier_disputes |
| comms | notifications, messages, email_templates, email_campaigns, email_campaign_logs, campaign_recipients, support_tickets, support_ticket_replies, ticket_attachments, direct_chat_rooms, direct_chat_messages, group_chat_rooms, group_chat_members, group_chat_messages, entity_chat_threads, entity_chat_messages, video_rooms, video_room_participants, video_room_recordings |
| hr | employees, offices, employee_attendance, employee_leave_requests, employee_work_logs, org_units, shift_handover_sessions, shift_handover_tasks |
| country | country_configs, country_cities, country_tax_rules, country_commission_rates, country_payout_rules, country_staff_assignments, country_gateway_configs, country_holiday_calendars, country_localization |
| security | fraud_alerts, fraud_cases, fraud_events, fraud_rules, fraud_scoring_logs, fraud_velocity_counters, kyc_verifications, document_verifications, device_fingerprints, credit_card_bins, alert_escalation_rules |
| audit | audit_logs, admin_activity_logs, admin_change_audit_logs, command_center_views, finance_audit_logs, finance_automation_logs, retention_job_runs, dlp_violations |
| analytics | executive_news, financial_reports, normalized_webhook_events, processed_webhook_events, outbox_events, event_dead_letter, event_retry_queue, inbox_events |
| media | media_assets, media_upload_sessions, product_videos, video_analytics, ocr_results |
| core | users, user_sessions, user_devices, user_login_histories, password_reset_tokens, email_verification_tokens, revoked_tokens, api_keys, permissions, permission_categories, role_permission_assignments, user_browsing_history, user_permission_overrides |
| configuration | system_settings, system_alerts, email_provider_configs, promotion_engine_configs, legal_contract_templates, country_feature_flags |
| ai | ai_generation_logs, ai_staging_products, ai_staging_variants, ai_upload_jobs, chatbot_query_events, predictive_simulations |
| treasury | payment_gateway_connections, payment_orchestrator_sync, payment_provider_configs, payment_reconciliation_runs, payouts, payout_rules, payout_rule_categories, payout_rule_products, cash_accounts, cash_transactions, treasury_accounts, treasury_transactions, cash_flow_forecasts, cash_position_snapshots, gateway_settlement_schedules, pending_journal_entries, payout_batches, payout_batch_items, finance_bank_accounts |
| customer | customers, addresses, cross_country_customer_sessions, referrals, referral_point_events, wishlists, wishlist_items |
| commerce | products, categories, product_variants, product_filter_metadatas, product_filter_options, orders, order_items, order_logistics_allocations, return_requests, coupons, coupon_usage, flash_sales, flash_sale_items, banners, commission_agreements, commission_ledger_entries, commission_badge_tiers, commission_global_configs, commission_category_rates, promotion_ledger_entries, promotion_order_tiers, product_commission_overrides, product_verifications, return_abuse_patterns, badge_tiers, badge_transactions, badge_billing_records |

---

## 7. Relationships

**Status: VERIFIED**

Key relationships traced (User -> Cart -> Order -> Payment -> Inventory):

| Source Table | Source Column | Target Table | Target Column | OnDelete | Evidence |
|--------------|---------------|--------------|---------------|----------|----------|
| users | id | addresses | user_id | SET NULL | backend/domains/accounts/models/core.py line 61 |
| users | id | carts | user_id | SET NULL | backend/domains/accounts/models/core.py line 86 |
| users | id | cart_items | user_id | SET NULL | backend/domains/accounts/models/core.py line 105 |
| catalog.products | id | cart_items | product_id | CASCADE | backend/domains/accounts/models/core.py line 109 |
| users | id | orders | user_id | RESTRICT | backend/domains/orders/models/order_entities.py line 23 |
| users | id | orders | customer_id | RESTRICT | backend/domains/orders/models/order_entities.py line 22 |
| orders | id | order_items | order_id | RESTRICT | backend/domains/orders/models/order_entities.py line 83 |
| catalog.products | id | order_items | product_id | RESTRICT | backend/domains/orders/models/order_entities.py line 84 |
| orders | id | payments | order_id | CASCADE | backend/domains/finance/models/payments.py line 50 |
| catalog.products | id | product_variants | product_id | CASCADE | backend/domains/catalog/models/products.py line 166 |
| catalog.products | id | reviews | product_id | CASCADE | backend/domains/catalog/models/products.py line 119 |
| catalog.products | id | wishlist_items | product_id | CASCADE | backend/domains/catalog/models/products.py line 140 |
| users | id | shipments | supplier_id | RESTRICT | backend/domains/logistics/models/logistics_entities.py line 234 |
| orders | id | shipments | order_id | RESTRICT | backend/domains/logistics/models/logistics_entities.py line 233 |
| logistics.logistics_partners | id | shipments | assigned_partner_id | RESTRICT | backend/domains/logistics/models/logistics_entities.py line 235 |
| shipments | id | shipment_events | shipment_id | RESTRICT | backend/domains/logistics/models/logistics_entities.py line 280 |
| orders | id | order_logistics_allocations | order_id | RESTRICT | backend/domains/orders/models/order_entities.py line 112 |
| accounts.users | id | order_logistics_allocations | supplier_id | RESTRICT | backend/domains/orders/models/order_entities.py line 113 |

---

## 8. Primary Keys

**Status: VERIFIED**

All inspected models use Integer auto-increment primary keys:

| Model | PK Column | Type | Evidence |
|-------|-----------|------|----------|
| User | id | Integer | backend/domains/accounts/models/user.py line 33 |
| Cart | id | Integer | backend/domains/accounts/models/core.py line 83 |
| CartItem | id | Integer | backend/domains/accounts/models/core.py line 102 |
| Order | id | Integer | backend/domains/orders/models/order_entities.py line 20 |
| OrderItem | id | Integer | backend/domains/orders/models/order_entities.py line 82 |
| Payment | id | Integer | backend/domains/finance/models/payments.py line 48 |
| Product | id | Integer | backend/domains/catalog/models/products.py line 49 |
| ProductVariant | id | Integer | backend/domains/catalog/models/products.py line 165 |
| Shipment | id | Integer | backend/domains/logistics/models/logistics_entities.py line 232 |
| SupplierProfile | id | Integer | (referenced in seed) |

No composite primary keys were observed in the core e-commerce flow. UUIDs are stored via a separate uuid column (GUID type) where needed.

---

## 9. Foreign Keys

**Status: VERIFIED**

Foreign keys are extensively used. Key examples:

- accounts.carts.user_id -> accounts.users.id (SET NULL)
- accounts.cart_items.user_id -> accounts.users.id (SET NULL)
- accounts.cart_items.product_id -> catalog.products.id (CASCADE)
- orders.orders.user_id -> accounts.users.id (RESTRICT)
- orders.orders.customer_id -> accounts.users.id (RESTRICT)
- orders.order_items.order_id -> orders.orders.id (RESTRICT)
- orders.order_items.product_id -> catalog.products.id (RESTRICT)
- finance.payments.order_id -> orders.orders.id (CASCADE)
- finance.payouts.order_id -> orders.orders.id (SET NULL)
- finance.payouts.supplier_id -> accounts.users.id (RESTRICT)
- logistics.shipments.order_id -> orders.orders.id (RESTRICT)
- logistics.shipments.supplier_id -> accounts.users.id (RESTRICT)
- logistics.shipments.assigned_partner_id -> logistics.logistics_partners.id (RESTRICT)
- country.country_configs.code is referenced by many tables via country_code FK

A large migration (2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py) added missing FK constraints.

---

## 10. Unique Constraints

**Status: VERIFIED**

| Table | Columns | Constraint Name | Evidence |
|-------|---------|-----------------|----------|
| users | email | uq_users_email (implicit via unique=True) | backend/domains/accounts/models/user.py line 34 |
| products | slug | unique | backend/domains/catalog/models/products.py line 51 |
| products | sku | unique | backend/domains/catalog/models/products.py line 55 |
| products | barcode | unique | backend/domains/catalog/models/products.py line 56 |
| products | slug_hash | unique | backend/domains/catalog/models/products.py line 97 |
| product_variants | (product_id, variant_key) | uq_product_variant_key | backend/domains/catalog/models/products.py line 194 |
| product_variants | sku | unique | backend/domains/catalog/models/products.py line 167 |
| product_variants | barcode | unique | backend/domains/catalog/models/products.py line 174 |
| categories | slug | unique | backend/domains/catalog/models/products.py line 18 |
| orders | order_number | unique | backend/domains/orders/models/order_entities.py line 21 |
| orders | tracking_number | unique (nullable) | backend/domains/orders/models/order_entities.py line 50 |
| logistics_partners | code | unique | backend/domains/logistics/models/logistics_entities.py line 27 |
| shipments | tracking_number | unique (nullable) | backend/domains/logistics/models/logistics_entities.py line 237 |
| finance.accounts | code | unique | backend/domains/finance/models/general_ledger.py line 175 |
| finance.account_groups | code | unique | backend/domains/finance/models/general_ledger.py line 198 |
| finance.journal_entries | reference_number | unique | backend/domains/finance/models/general_ledger.py line 118 |
| finance.payout_batches | batch_number | unique | backend/domains/finance/models/general_ledger.py line 661 |
| password_reset_tokens | token | unique | backend/domains/accounts/models/user.py line 198 |
| email_verification_tokens | token | unique | backend/domains/accounts/models/user.py line 227 |
| revoked_tokens | token | unique | backend/domains/accounts/models/user.py line 256 |

Note: PaymentGatewayConnection stores credentials, fee_config, and supported_methods as JSON columns with GIN indexes in PostgreSQL (backend/domains/finance/models/payments.py lines 25-36).

---

## 11. Check Constraints

**Status: VERIFIED**

Check constraints are applied via Alembic migrations and model declarations:

| Table | Constraint | Condition | Evidence |
|-------|-----------|-----------|----------|
| orders | chk_orders_status_valid | status_code IN (pending,confirmed,processing,shipped,delivered,cancelled,returned) | backend/domains/orders/models/order_entities.py line 19 |
| orders | chk_order_payment_status_valid | payment_status IN (pending,completed,failed,refunded) | backend/alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py line 27 |
| orders | chk_order_fraud_action_valid | fraud_action IN (allow,review,block) | same migration line 31 |
| return_requests | chk_return_requests_status_valid | status_code IN (requested,approved,rejected,completed,cancelled) | backend/domains/orders/models/order_entities.py line 151 |
| return_requests | chk_return_intent_valid | intent IN (return,exchange,refund) | migration line 37 |
| users | chk_user_role_valid | role IN (customer,supplier,admin,employee,logistics) | migration line 46 |
| referrals | chk_referral_status_valid | status IN (pending,completed,expired,cancelled) | migration line 52 |
| logistics_partners | chk_logistics_partners_status_valid | status_code IN (active,inactive,suspended,deleted) | backend/domains/logistics/models/logistics_entities.py line 23 |
| shipments | chk_shipments_status_valid | status_code IN (pending,confirmed,processing,shipped,delivered,cancelled,returned) | backend/domains/logistics/models/logistics_entities.py line 231 |
| support_tickets | chk_ticket_status_valid | status IN (open,in_progress,resolved,closed) | migration line 69 |
| notifications | chk_notification_status_valid | status IN (pending,delivered,read,failed) | migration line 75 |
| payments | chk_payment_amount_non_negative | amount >= 0 | backend/domains/finance/models/payments.py line 42 |
| payments | chk_payment_status_valid | status IN (pending,completed,failed,refunded) | backend/domains/finance/models/payments.py line 43 |
| finance.transaction_ledgers | chk_transaction_ledger_amount_non_negative | amount >= 0 | backend/domains/finance/models/general_ledger.py line 45 |
| finance.transaction_ledgers | chk_transaction_ledger_currency_valid | currency in allowed list | backend/domains/finance/models/general_ledger.py line 45 |
| finance.supplier_settlements | chk_supplier_settlement_gross_non_negative | gross_amount >= 0 | backend/domains/finance/models/general_ledger.py line 84 |
| finance.journal_entry_lines | chk_jel_amount_non_negative | amount >= 0 | backend/domains/finance/models/general_ledger.py line 147 |
| finance.journal_entry_lines | chk_jel_side_valid | side IN (debit,credit) | backend/domains/finance/models/general_ledger.py line 147 |
| finance.accounts | chk_account_normal_side_valid | normal_side IN (debit,credit) | backend/domains/finance/models/general_ledger.py line 172 |

---

## 12. Indexes

**Status: VERIFIED**

Indexes are declared in model __table_args__ and added via migrations.

Model-declared indexes (selected):
- users: ix_accounts_users_email, ix_accounts_users_country_code (backend/domains/accounts/models/user.py lines 28-29)
- user_sessions: ix_accounts_user_sessions_user_id, ix_accounts_user_sessions_token_jti (backend/domains/accounts/models/user.py lines 93-94)
- products: ix_products_supplier_active, ix_products_category_active, ix_products_created_sort, ix_products_country_status (backend/domains/catalog/models/products.py lines 43-46)
- orders: ix_orders_user_id, ix_orders_customer_id, ix_orders_status, ix_orders_country_created (backend/domains/orders/models/order_entities.py line 19)
- order_items: ix_order_items_order_id, ix_order_items_product_id, ix_order_items_country_created (backend/domains/orders/models/order_entities.py line 81)
- payments: ix_payments_order_id, ix_payments_status_created, ix_payments_provider_status (backend/domains/finance/models/payments.py lines 44-46)
- shipments: ix_shipments_order_id, ix_shipments_country_created (backend/domains/logistics/models/logistics_entities.py line 231)

Migration-added indexes (selected from 2026_07_28_19_30):
- ix_order_logistics_allocations_* (order_id, supplier_id, partner_id, service_area_id, shipment_id)
- ix_shipments_supplier_id, ix_shipments_assigned_partner_id, ix_shipments_carrier_id
- ix_commission_agreements_*, ix_commission_ledger_entries_*
- ix_transaction_ledgers_*, ix_supplier_settlements_*
- ix_products_category_active_deleted, ix_products_supplier_active_deleted
- ix_return_requests_order_id
- ix_invoices_shipment_id, ix_invoices_supplier_id
- ix_pgc_provider_country on payment_gateway_connections

Partitioned tables have per-partition indexes:
- audit_logs, notifications, shipment_events are range-partitioned by created_at with per-partition indexes on (id, created_at) (backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py)

---

## 13. Transactions

**Status: VERIFIED**

Transaction utilities are centralized:

| Utility | Location | Purpose |
|---------|----------|---------|
| db_transaction_context | backend/infrastructure/database/transaction.py lines 19-69 | Context manager with commit/rollback |
| atomic_transaction | backend/infrastructure/database/transaction.py lines 100-121 | All-or-nothing semantics |
| transactional | backend/infrastructure/database/transaction.py lines 124-154 | Decorator for transactional functions |
| get_transaction_context | backend/infrastructure/database/transaction.py lines 72-97 | DI-friendly context manager factory |

Session factories:
- SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False) (backend/infrastructure/database/database.py lines 143-148)
- Async: async_sessionmaker with expire_on_commit=False (backend/infrastructure/database/database.py lines 225-229)
- Replica: separate sessionmaker bound to _replica_engine (backend/infrastructure/database/database.py lines 348-353)

Note: get_db() yields a session but does NOT auto-commit; callers must commit explicitly (backend/infrastructure/database/database.py lines 380-401). The same applies to get_service_session and get_db_context.

---

## 14. Isolation Assumptions

**Status: INFERRED**

- **Default isolation level:** Not explicitly set on the main engine or session factory. PostgreSQL default (READ COMMITTED) is assumed.
- **AUTOCOMMIT** is used only for DDL in install_rls_policies (backend/infrastructure/database/rls_interceptor.py line 286) and in test conftest (backend/tests/conftest.py line 70).
- No REPEATABLE READ or SERIALIZABLE isolation levels are configured anywhere in the production code path.
- db_read.py provides locked_rows (SELECT ... FOR UPDATE) at line 422-430, but it is not visibly used in the core order/payment flow.

---

## 15. Migrations

**Status: VERIFIED**

| Migration File | Purpose |
|----------------|---------|
| backend/alembic/versions/2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py | Baseline: adds missing columns/indexes for existing tables |
| backend/alembic/versions/2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py | Creates communication tables |
| backend/alembic/versions/2026_07_26_22_00-e70b2cb9a90f_fix_internal_channels_fk.py | Fixes FK in internal_channels |
| backend/alembic/versions/2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py | Production PostgreSQL indexes |
| backend/alembic/versions/2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py | Adds CHECK constraints for enum-like columns |
| backend/alembic/versions/2026_07_28_0000_employee_hr_tables.py | Employee/HR tables |
| backend/alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py | Adds ~80 missing indexes and unique constraints |
| backend/alembic/versions/2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py | Adds missing FK constraints |
| backend/alembic/versions/2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py | Orphaned employee models |
| backend/alembic/versions/2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py | Schema drift check |
| backend/alembic/versions/2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py | Search vector trigger for products |
| backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py | Range partitioning for audit_logs, notifications, shipment_events |
| backend/alembic/versions/2026_07_30_0001-20260730_0001_create_user_points_table.py | User points |
| backend/alembic/versions/2026_07_30_0002-20260730_0002_create_points_transactions_table.py | Points transactions |
| backend/alembic/versions/2026_07_30_0003-20260730_0003_create_upload_jobs_table.py | Upload jobs |
| backend/alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py | Event tables |
| backend/alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py | Moves tables into bounded-context schemas |

Startup migration behavior:
- Production: auto-runs alembic upgrade head on startup (backend/lifespan.py lines 72-82)
- Non-production: skips auto-migration (backend/lifespan.py lines 83-84)
- Dev: uses Base.metadata.create_all guarded by _guard_dev_only (backend/infrastructure/database/database.py lines 570-578)

---

## 16. Seed Data

**Status: VERIFIED**

Seed infrastructure:
- backend/infrastructure/database/seed/_common.py - canonical seed logic
- backend/infrastructure/database/seed/seed_part1.py - re-exports _common
- backend/infrastructure/database/seed/models.py - lazy model registry
- backend/infrastructure/database/seed/_seed_constants.py - seed constants
- backend/infrastructure/database/seed/seed_part2.py, seed_part3.py - additional seed data
- backend/infrastructure/database/seed/logistics.py - logistics-specific seed

Seed behavior:
- Controlled by SEED_DATA_ON_STARTUP env var (backend/lifespan.py lines 207-221)
- Seeds countries (AE, SA, IN), demo users (admin, supplier, customer, logistics), categories, products, logistics partner, demo shipment
- Uses PRAGMA foreign_keys=OFF for SQLite during seed (backend/infrastructure/database/seed/_common.py lines 112-124)
- Idempotent: checks for existing records before inserting

Demo users seeded:
- admin@zozi.com, supplier@zozi.com, customer@zozi.com, logistics@zozi.com
- Test variants: admin@test.com, supplier@test.com, customer@test.com
- GCC variants: fashion.supplier@zozi.com, home.supplier@zozi.com, beauty.supplier@zozi.com, sara@customer.com, mohammed@customer.com, fatima@customer.com, khalid@customer.com, fast.delivery@zozi.com, gulf.shipping@zozi.com

Passwords are sourced from env vars (SEED_ADMIN_PASSWORD, etc.) with random fallback (backend/infrastructure/database/seed/_common.py lines 36-49).

---

## 17. Raw SQL

**Status: VERIFIED**

Raw SQL is used in specific, controlled contexts:

| Context | Location | Pattern |
|---------|----------|---------|
| Migrations | backend/alembic/versions/*.py | op.execute(sa.text(...)), op.execute(CREATE INDEX ...) |
| db_read helpers | backend/infrastructure/database/db_read.py lines 79-80, 100-101, 113-114, 127-128 | db.execute(text(sql), params or {}) |
| RLS interceptor | backend/infrastructure/database/rls_interceptor.py lines 271-272, 289-292 | session.execute(text(SET LOCAL app.country_scope = :country_scope)) |
| RLS policy installation | backend/infrastructure/database/rls_interceptor.py lines 286-294 | conn.execute(text(ALTER TABLE ... ENABLE ROW LEVEL SECURITY)) |
| RBAC permissions | backend/rbac/services/permissions_service.py lines 22-235 | Multiple db.execute(text(...)) calls for role/permission management |
| Health check | backend/infrastructure/database/database.py lines 473-478 | conn.execute(text(SELECT 1)), SELECT current_database(), current_user, version() |

No f-string SQL interpolation into execute() was found in the main codebase (a test test_security_findings.py explicitly checks for this violation).

---

## 18. N+1 Query Risks

**Status: VERIFIED (mitigated in core models)**

The project explicitly addresses N+1 via lazy="selectin" on high-traffic relationships:

| Model | Relationship | Loading Strategy | Evidence |
|-------|-------------|------------------|----------|
| User | addresses | selectin | backend/domains/accounts/models/user.py line 65 |
| User | cart | selectin | backend/domains/accounts/models/user.py line 66 |
| User | cart_items | selectin | backend/domains/accounts/models/user.py line 67 |
| User | sessions | selectin | backend/domains/accounts/models/user.py line 68 |
| User | login_history | selectin | backend/domains/accounts/models/user.py line 69 |
| User | devices | selectin | backend/domains/accounts/models/user.py line 72 |
| User | password_reset_tokens | selectin | backend/domains/accounts/models/user.py line 74 |
| User | email_verification_tokens | selectin | backend/domains/accounts/models/user.py line 77 |
| User | revoked_tokens | selectin | backend/domains/accounts/models/user.py line 80 |
| User | referrals_given | selectin | backend/domains/accounts/models/user.py line 82 |
| User | referred_by | selectin | backend/domains/accounts/models/user.py line 83 |
| User | products | selectin | backend/domains/accounts/models/user.py line 84 |
| User | reviews | selectin | backend/domains/accounts/models/user.py line 85 |
| User | wishlist_items | selectin | backend/domains/accounts/models/user.py line 86 |
| User | wishlists | selectin | backend/domains/accounts/models/user.py line 87 |

A dedicated test enforces selectin loading on Shipment relationships:
- backend/tests/domains/logistics/test_shipments_n_plus_one.py lines 18-60

Residual risk: Not all relationship models were inspected. Any relationship without explicit lazy="selectin" that is accessed in a list loop remains a potential N+1 source.

---

## 19. Unbounded Queries

**Status: VERIFIED (residual risk)**

Multiple code paths use .all() without explicit limit() on collections that could grow large:

| Location | Pattern | Risk |
|----------|---------|------|
| backend/domains/analytics/services/dashboards/command_center_service.py lines 90, 130, 195 | self.db.query(NewsSource).filter(...).all() | Low (reference data) |
| backend/domains/analytics/services/dashboards/command_center_service.py lines 290-314 | Multiple .count() on full tables | Medium (analytics dashboard; acceptable for small tables but could lag on large orders/users) |
| backend/domains/accounts/services/users/user_management_service.py line 334 | .limit(1000).all() | Bounded but large |
| backend/domains/accounts/services/users/user_management_service.py line 955 | .limit(1000).all() | Bounded but large |

The db_read.py layer supports limit/offset parameters, but callers must explicitly pass them.

---

## 20. Missing Pagination

**Status: INFERRED**

Pagination support exists in the infrastructure (db_read.py lines 147-148, 185-188, 199-200, 354-378), and middleware helpers (backend/middleware/router_helpers.py lines 40-41) implement offset/limit pagination.

However, not all list endpoints visibly apply pagination. Some services (e.g., command_center_service.py) call .all() directly on queries without limit/offset, which would return full result sets.

---

## 21. Missing Indexes

**Status: INFERRED (mostly mitigated)**

The migration 2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py added ~80 indexes. However:

| Potential Gap | Evidence |
|---------------|----------|
| carts table lacks explicit indexes beyond PK and user_id | backend/domains/accounts/models/core.py lines 82-92: only user_id is indexed |
| cart_items has ix_cart_items_user_product and ix_cart_items_created | Adequate for cart lookups |
| order_items has ix_order_items_order_id, ix_order_items_product_id | Adequate |
| payments has ix_payments_order_id, ix_payments_status_created, ix_payments_provider_status | Adequate |
| products has multiple composite indexes | Adequate |

The cart_items table is the most query-critical for the User->Cart->Order flow and appears adequately indexed.

---

## 22. Excessive Joins

**Status: INFERRED**

No explicit evidence of excessive joins in the core models was found. The db_read.py layer supports joins/outerjoins parameters, but the number of joins per query is caller-controlled.

The finance TransactionLedger model has 6 FK columns (user_id, supplier_id, logistics_partner_id, order_id, order_item_id, shipment_id), which could lead to wide joins if all are traversed simultaneously. However, no specific query path was found that joins all of them at once.

---

## 23. Duplicate Data

**Status: VERIFIED (intentional denormalization)**

| Duplicate Pattern | Tables/Columns | Evidence |
|-------------------|----------------|----------|
| Order totals stored in multiple columns | orders.subtotal, orders.subtotal_amount, orders.shipping_fee, orders.shipping_amount, orders.tax_amount, orders.vat_amount, orders.discount_amount, orders.total, orders.total_amount | backend/domains/orders/models/order_entities.py lines 30-38 |
| OrderItem prices | order_items.unit_price, order_items.price, order_items.total_price | backend/domains/orders/models/order_entities.py lines 88-90 |
| Product stock denormalized | products.stock (aggregated from variants) | backend/domains/catalog/models/products.py line 60; backend/domains/suppliers/services/ai_upload_service.py lines 196-224 |
| Product name/image snapshots in OrderItem | order_items.product_name, order_items.product_image | backend/domains/orders/models/order_entities.py lines 91-92 |
| Logistics partner name snapshots | order_logistics_allocations.partner_name_snapshot, partner_code_snapshot, service_area_label_snapshot | backend/domains/orders/models/order_entities.py lines 118-120 |

---

## 24. Denormalization

**Status: VERIFIED**

- **Order financial snapshot:** Order stores subtotal, subtotal_amount, shipping_fee, shipping_amount, tax_amount, vat_amount, discount_amount, total, total_amount - denormalized for audit and display.
- **Product.stock:** Aggregated from variants (backend/domains/suppliers/services/ai_upload_service.py lines 196-224).
- **OrderItem product snapshots:** product_name, product_image, selected_size, selected_color stored on the line item.
- **OrderLogisticsAllocation snapshots:** Partner, service area, and pricing details are snapshotted at allocation time.
- **Country code scope:** country_code is repeated on virtually every table rather than joined from a session context.

---

## 25. Data Integrity Risks

**Status: VERIFIED**

| Risk | Description | Evidence |
|------|-------------|----------|
| **Stock race condition** | products.stock and product_variants.stock are updated without pessimistic locking (SELECT ... FOR UPDATE). Concurrent checkouts could oversell. | backend/domains/suppliers/services/health/supplier_health.py lines 167-177: product.stock = int(new_stock) with no lock |
| **Soft-delete without cascade** | is_deleted flag is used extensively but FK constraints do not cascade on delete (most use RESTRICT or SET NULL). Orphan detection is application-level. | backend/domains/orders/models/order_entities.py line 23: ondelete='RESTRICT' |
| **Order total vs sum mismatch** | orders.total can diverge from SUM(order_items.total_price) if items are modified after order creation. No DB-level check enforces consistency. | backend/domains/orders/models/order_entities.py lines 30-38, 88-90 |
| **Nullable FKs with business meaning** | orders.customer_id is nullable (nullable=True) despite being semantically required (backend/domains/orders/models/order_entities.py line 22). user_id is non-null. |
| **Country code nullable on some tables** | orders.country_code is nullable (nullable=True) despite Law #5 stating country must be non-null on every row (backend/domains/orders/models/order_entities.py line 60). |
| **Payment status drift** | orders.payment_status and finance.payments.status are separate columns with no DB-level sync trigger. | backend/domains/orders/models/order_entities.py line 26; backend/domains/finance/models/payments.py line 54 |

---

## 26. Race-Condition Risks

**Status: VERIFIED**

| Risk | Description | Evidence |
|------|-------------|----------|
| **Inventory oversell** | Stock checks and updates are performed in application code without SELECT ... FOR UPDATE or atomic UPDATE ... WHERE stock >= ? patterns. | backend/domains/suppliers/services/health/supplier_health.py lines 167-177; backend/domains/suppliers/services/health/supplier_health.py lines 542-602 (bulk adjust) |
| **Duplicate order numbers** | order_number has a unique constraint, but generation is application-level. Concurrent requests could collide. | backend/domains/orders/models/order_entities.py line 21 |
| **Concurrent seed/data upserts** | Seed uses read-then-insert pattern (_ensure_demo_user, _upsert_demo_product) without locking, which could miss inserts under concurrency. | backend/infrastructure/database/seed/_common.py lines 52-87, 163-176 |

---

## 27. Soft-Delete Implementation

**Status: VERIFIED**

Soft-delete is implemented via SoftDeleteMixin (backend/infrastructure/database/mixins.py lines 23-41):

| Column | Type | Indexed |
|--------|------|---------|
| is_deleted | Boolean, default=False | Yes |
| deleted_at | DateTime, nullable | Yes |
| deleted_by_id | Integer, FK to accounts.users.id | No (except via relationship) |

Models using soft-delete (observed):
- User, UserSession, UserLoginHistory, UserDevice, PasswordResetToken, EmailVerificationToken, RevokedToken
- Cart, CartItem
- Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification
- Product, ProductVariant, Review, WishlistItem, Wishlist, ProductVideo, ProductFilterMetadata, ProductFilterOption
- Payment, PaymentReconciliationRun, PaymentGatewayConnection, Payout, LogisticsPartnerPayout
- Shipment, ShipmentEvent, LogisticsPartner, LogisticsPartnerProfile, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsVehicleRule, LogisticsCategoryPricingRule
- SupplierProfile, SupplierDocument
- JournalEntry, JournalEntryLine, Account, AccountGroup, AccountBalance, Invoice, InvoiceItem, RefundLedger, BankTransaction, VATRemittance, CashAccount, CashTransaction, TreasuryAccount, TreasuryTransaction, CashFlowForecast, CashPositionSnapshot, GatewaySettlementSchedule, PendingJournalEntry, PayoutBatch, PayoutBatchItem, BankMappingRule, BankStatementImport, BankStatementLine
- And many more across comms, hr, analytics, audit, security, governance

Note: Soft-delete does not cascade via DB-level ON DELETE. Application code must filter is_deleted=False explicitly. The db_read.py layer does not automatically inject is_deleted=False filters.

---

## 28. Audit / History Mechanisms

**Status: VERIFIED**

| Mechanism | Location | Description |
|-----------|----------|-------------|
| AuditMixin | backend/infrastructure/database/mixins.py lines 10-20 | Adds created_at, created_by_id, updated_at, updated_by_id |
| AuditLog model | re-exported from domains.audit.models.audit_schema_models | Dedicated audit log table in audit schema |
| worm_audit.py | backend/domains/audit/services/worm_audit.py | WORM (Write Once Read Many) audit trail |
| user_activity_tracker.py | backend/domains/audit/services/logs/user_activity_tracker.py | Tracks user actions with limit |
| retention_service.py | backend/domains/audit/services/retention_service.py | Data retention policy enforcement |
| Admin audit logs | audit.admin_activity_logs, audit.admin_change_audit_logs | Admin action tracking |
| Finance audit logs | audit.finance_audit_logs, audit.finance_automation_logs | Finance operation tracking |
| DLP violations | audit.dlp_violations | Data loss prevention events |
| Retention job runs | audit.retention_job_runs | Tracks when retention policies are applied |

No explicit temporal/history tables (e.g., SAMPLE or SYSTEM_VERSIONING) were found. Audit is append-only via dedicated log tables.

---

## 29. Tenant / Seller Isolation

**Status: VERIFIED**

Isolation is implemented via two mechanisms:

1. **Application-level RLS interceptor** (backend/infrastructure/database/rls_interceptor.py):
   - ContextVar-based country scope: rls_country_scope_ctx
   - before_execute event listener injects country_code IN (...) filters
   - COUNTRY_AWARE_TABLES registry auto-discovered from live DB columns
   - set_rls_context(scope, is_restricted=True/False) enables/disables filtering

2. **PostgreSQL RLS policies** (generated by generate_rls_policy_sql):
   - Creates auth.country_access_check(p_country_code) security-definer function
   - Applies CREATE POLICY ... FOR ALL USING (country_code IS NULL OR auth.country_access_check(...))
   - ALTER TABLE ... ENABLE ROW LEVEL SECURITY and FORCE ROW LEVEL SECURITY

3. **Middleware integration** (backend/middleware/country_context.py):
   - Sets RLS context per request based on user country access

Residual risk: RLS is only enforced when is_restricted=True. Background jobs and seed data explicitly set is_restricted=False (backend/infrastructure/database/seed/_common.py line 631). If any production path forgets to set the context, queries may return cross-country data or raise SecurityContextMissingError.

---

## 30. Sensitive Data Storage

**Status: VERIFIED**

| Data Type | Storage Mechanism | Evidence |
|-----------|-------------------|----------|
| Passwords | bcrypt via get_password_hash | backend/infrastructure/utils/auth.py (referenced in seed) |
| JWT secrets | SECRET_KEY / AUTH_SECRET env vars | backend/.env lines 8-9; backend/config.py lines 31-32 |
| Payment gateway credentials | AES-256-GCM via infrastructure.security.vault | backend/domains/finance/models/payments.py lines 94-106; backend/infrastructure/security/vault.py |
| Field-level PII | Fernet (AES-256-CBC+HMAC) via infrastructure.security.encryption | backend/infrastructure/security/encryption.py lines 41-67 |
| KMS master key | KMS_MASTER_KEY env var or field_encryption_key | backend/infrastructure/security/kms_encryption.py line 17 |
| S3/R2 credentials | Env vars (R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY) | backend/.env lines 52-53 |
| Stripe/Tap keys | Env vars | backend/.env lines 89-91, 55-56 |

Encryption is application-level (envelope encryption). Data is encrypted before storage and decrypted on read via SQLAlchemy TypeDecorator (backend/infrastructure/security/encryption.py lines 93-131).

Note: The .env file in the repository contains real-looking secrets (Neon DB password, R2 keys, Stripe test keys). This is a development environment file but should be verified as excluded from version control.

---

## Trace: User -> Cart -> Order -> Payment -> Inventory

**Status: VERIFIED**

User (accounts.users)
  -> Cart (accounts.carts) [1:1, user_id FK]
       -> CartItem (accounts.cart_items) [1:N, user_id + product_id FKs]
            -> Product (catalog.products) [N:1, product_id FK]
                 -> ProductVariant (catalog.product_variants) [1:N, product_id FK]
  -> Order (orders.orders) [1:N, user_id + customer_id FKs]
       -> OrderItem (orders.order_items) [1:N, order_id + product_id FKs]
            -> Product (catalog.products) [N:1, product_id FK]
       -> Payment (finance.payments) [1:N, order_id FK]
       -> Shipment (logistics.shipments) [1:N, order_id + supplier_id FKs]
            -> ShipmentEvent (logistics.shipment_events) [1:N, shipment_id FK]
       -> OrderLogisticsAllocation (orders.order_logistics_allocations) [1:N, order_id + supplier_id FKs]

Inventory equivalent: catalog.products.stock and catalog.product_variants.stock serve as the inventory ledger. There is no separate inventory table; stock is denormalized onto the product and variant rows.

Flow summary:
1. Customer adds Product/ProductVariant to CartItem
2. Checkout creates Order + OrderItem rows
3. Order.payment_status tracks payment state
4. Payment records the transaction against order_id
5. Shipment + ShipmentEvent track fulfillment
6. Product.stock is the inventory count (updated out-of-band)

---

## Summary of Key Findings

| # | Finding | Status | Impact | Confidence |
|---|---------|--------|--------|------------|
| 1 | PostgreSQL (Neon) in production; SQLite in dev | VERIFIED | - | High |
| 2 | SQLAlchemy 2.0 + Alembic with extensive migrations | VERIFIED | - | High |
| 3 | Soft-delete pervasive but no automatic query filter | VERIFIED | Medium | High |
| 4 | Stock updates lack pessimistic locking | VERIFIED | High | High |
| 5 | Order total denormalized without DB-level consistency check | VERIFIED | Medium | High |
| 6 | RLS country isolation implemented via interceptor + Postgres policies | VERIFIED | - | High |
| 7 | Application-level field encryption (Fernet/AES-256-GCM) for PII and payment credentials | VERIFIED | - | High |
| 8 | N+1 mitigated via lazy=selectin on User relationships; test enforced for Shipment | VERIFIED | - | High |
| 9 | Some unbounded .all() queries in analytics/command center | VERIFIED | Low-Medium | High |
| 10 | ~80 missing indexes added in migration e8efae30fc29 | VERIFIED | - | High |
| 11 | Check constraints enforce enum validity and non-negative amounts | VERIFIED | - | High |
| 12 | Three tables range-partitioned by created_at (audit_logs, notifications, shipment_events) | VERIFIED | - | High |
| 13 | orders.customer_id nullable despite semantic requirement | VERIFIED | Low | High |
| 14 | Seed data includes hardcoded demo users with passwords in env | VERIFIED | Low (dev only) | High |
| 15 | DATABASE_URL and secrets present in .env (should verify .gitignore) | VERIFIED | Medium if committed | High |

---

*End of forensic audit. No files were modified during this analysis.*
