# Database Constitution Implementation Plan

## Phase 0: Foundation (Current State Assessment)

### 0.1 Inventory Current State
- [x] 321 tables exist in SQLite
- [x] 268 tables have `country_code` (83%)
- [x] 313 tables have `is_deleted` (97%)
- [x] 310 tables have `created_at` (96%)
- [x] 145 tables have `uuid` (45%)
- [x] 146 tables have `version` (45%)
- [x] 0 NEON schemas (all in `public`)
- [x] 0 RLS policies (interceptor only)
- [x] JSON seed system implemented

### 0.2 Gap Analysis
| Requirement | Current | Target | Gap |
|---|---|---|---|
| NEON schemas | 0 | 16 | 16 |
| Tables with UUID | 45% | 100% | 55% |
| Tables with version | 45% | 100% | 55% |
| RLS policies | 0 | 268 | 268 |
| Standard columns | Partial | 100% | ~55% |

---

## Phase 1: Migration Pipeline Hardening

### 1.1 Gate `create_all` Behind Dev Environment
**File:** `backend/infrastructure/database/database.py`

```python
# BEFORE (current):
def create_tables():
    Base.metadata.create_all(bind=engine)

# AFTER (gated):
def create_tables():
    app_env = os.environ.get("APP_ENV", "development").lower()
    if app_env == "production":
        raise RuntimeError(
            "Base.metadata.create_all() is forbidden in production. "
            "Use Alembic migrations: alembic upgrade head"
        )
    Base.metadata.create_all(bind=engine)
```

### 1.2 Add Schema Declaration to All Models
**File:** All `domains/*/models/*.py`

```python
# BEFORE:
class Product(Base):
    __tablename__ = "products"

# AFTER:
class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "commerce"}
```

### 1.3 Create Schema Migration
**File:** `backend/alembic/versions/YYYYMMDD_HHMM-create_schemas.py`

```python
"""Create 16 NEON schemas"""

def upgrade():
    schemas = [
        "core", "commerce", "supplier", "customer",
        "logistics", "finance", "treasury", "hr",
        "country", "media", "ai", "communication",
        "audit", "security", "analytics", "configuration"
    ]
    for schema in schemas:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

def downgrade():
    schemas = [
        "core", "commerce", "supplier", "customer",
        "logistics", "finance", "treasury", "hr",
        "country", "media", "ai", "communication",
        "audit", "security", "analytics", "configuration"
    ]
    for schema in reversed(schemas):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
```

---

## Phase 2: Standard Column Set

### 2.1 Add UUID Column to Tables Missing It
**File:** `backend/alembic/versions/YYYYMMDD_HHMM-add_uuid_columns.py`

```python
"""Add uuid column to tables missing it"""

# Tables needing UUID (156 tables)
TABLES_NEEDING_UUID = [
    # commerce
    "products", "product_variants", "categories", "carts", "cart_items",
    "orders", "order_items",
    # ... (list all 156 tables)
]

def upgrade():
    for table in TABLES_NEEDING_UUID:
        op.execute(f"ALTER TABLE {table} ADD COLUMN uuid UUID")
        op.execute(f"UPDATE {table} SET uuid = gen_random_uuid() WHERE uuid IS NULL")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN uuid SET NOT NULL")
        op.execute(f"CREATE UNIQUE INDEX ix_{table}_uuid ON {table}(uuid)")

def downgrade():
    for table in reversed(TABLES_NEEDING_UUID):
        op.execute(f"ALTER TABLE {table} DROP COLUMN uuid")
```

### 2.2 Add Version Column for Optimistic Locking
**File:** `backend/alembic/versions/YYYYMMDD_HHMM-add_version_columns.py`

```python
"""Add version column to tables missing it"""

TABLES_NEEDING_VERSION = [
    "products", "orders", "order_items", "carts", "cart_items",
    "supplier_profiles", "logistics_partners", "employees",
    # ... (list all 156 tables)
]

def upgrade():
    for table in TABLES_NEEDING_VERSION:
        op.execute(f"ALTER TABLE {table} ADD COLUMN version INTEGER DEFAULT 1")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN version SET NOT NULL")

def downgrade():
    for table in reversed(TABLES_NEEDING_VERSION):
        op.execute(f"ALTER TABLE {table} DROP COLUMN version")
```

### 2.3 Add Missing Audit Columns
**File:** `backend/alembic/versions/YYYYMMDD_HHMM-add_audit_columns.py`

```python
"""Add missing audit columns (updated_at, created_by, updated_by)"""

def upgrade():
    # Add updated_at to tables missing it
    for table in TABLES_NEEDING_UPDATED_AT:
        op.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP")
    
    # Add created_by/updated_by to tables missing them
    for table in TABLES_NEEDING_AUDIT_COLS:
        op.execute(f"ALTER TABLE {table} ADD COLUMN created_by INTEGER")
        op.execute(f"ALTER TABLE {table} ADD COLUMN updated_by INTEGER")

def downgrade():
    # Reverse operations
    pass
```

---

## Phase 3: JSON Seed Data Governance

### 3.1 Seed Data Structure (Already Implemented)
```
backend/infrastructure/database/seed_data/
├── country_configs.json    # 5 countries
├── categories.json         # 10 categories
├── users.json              # 37 users
├── products.json           # 41 products
├── banners.json            # 6 banners
├── flash_sales.json        # 4 flash sales
├── flash_sale_items.json   # 9 items
├── coupons.json            # 8 coupons
├── employees.json          # 8 employees
├── supplier_profiles.json  # 8 suppliers
└── logistics_partners.json # 6 partners
```

### 3.2 Seed Loader (Already Implemented)
**File:** `backend/infrastructure/database/seed_loader.py`

Features:
- Idempotent loading (skips existing records)
- Foreign key resolution (user_email → user_id)
- Column filtering (matches DB schema)
- Ordered loading (respects FK dependencies)

### 3.3 Media Files (Already Implemented)
**File:** `backend/infrastructure/database/seed_media.py`

Generated 63 placeholder PNG files in `/uploads/seed/`

---

## Phase 4: NEON RLS Policies

### 4.1 Create RLS Policy Functions
**File:** `backend/data/pg_rls_policies.sql`

```sql
-- Enable RLS on all country-scoped tables
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- ... (repeat for all 268 tables)

-- Create policy for country isolation
CREATE POLICY country_isolation_policy ON products
    USING (country_code = current_setting('app.current_country_code', true));

-- Create bypass policy for admin role
CREATE POLICY admin_bypass_policy ON products
    USING (current_setting('app.current_role', true) = 'admin');
```

### 4.2 Set Session Context in Middleware
**File:** `backend/middleware/country_context.py`

```python
async def dispatch(self, request, call_next):
    # Set NEON session variable for RLS
    country_code = request.state.country_code
    db = SessionLocal()
    db.execute(f"SET app.current_country_code = '{country_code}'")
    # ... rest of middleware
```

---

## Phase 5: Implementation Order

### Immediate (This Session)
1. ✅ Update ARCHITECTURE_DIAGRAM.md with database constitution
2. ✅ Create implementation plan
3. Gate `create_all` behind dev environment
4. Add schema declarations to core models (users, products, orders)

### Next Session
5. Create Alembic migration for 16 NEON schemas
6. Add UUID columns to core tables
7. Add version columns to core tables
8. Create RLS policy SQL file

### Future Sessions
9. Extend to all 321 tables
10. Add CI schema-drift gate
11. Add contract tests for migrations
12. Production deployment with PgBouncer

---

## Appendix: Table-to-Schema Mapping

### Core Schema
- users, roles, sessions, devices, auth_tokens, refresh_token_families

### Commerce Schema
- products, product_variants, categories, carts, cart_items, product_videos, product_verifications

### Supplier Schema
- supplier_profiles, supplier_documents, supplier_kyc_requirements, supplier_settlements

### Customer Schema
- customers, addresses, wishlists, wishlist_items, user_points, points_transactions

### Logistics Schema
- logistics_partners, logistics_partner_documents, logistics_partner_service_areas,
  logistics_pricing_profiles, logistics_vehicle_rules, shipments, shipment_events

### Finance Schema
- accounts, account_groups, journal_entries, journal_entry_lines, ap_ledger_entries,
  ar_ledger_entries, invoices, invoice_items, payouts

### Treasury Schema
- treasury_accounts, treasury_transactions, cash_accounts, bank_accounts,
  bank_reconciliations, payout_batches

### HR Schema
- employees, employee_addresses, employee_attendances, employee_leave_requests,
  employee_shift_rosters, offices, org_units

### Country Schema
- country_configs, country_config_versions, country_cities, country_economics,
  country_taxes, country_legals, country_holiday_calendars

### Media Schema
- media_assets, ai_staging_products, ai_upload_jobs, ai_requests, ai_results, ai_embeddings

### AI Schema
- (merged with Media for now)

### Communication Schema
- chat_threads, chat_messages, chat_attachments, email_messages, email_folders,
  notifications, support_tickets, video_rooms

### Audit Schema
- audit_logs, admin_activity_logs, admin_change_audit_logs, worm_audit,
  communication_audit_trails, finance_audit_logs

### Security Schema
- api_keys, fraud_alerts, fraud_cases, fraud_rules, fraud_blacklists,
  ip_reputations, device_fingerprints, mfa_factors, otp_codes

### Analytics Schema
- admin_analytics_snapshots, admin_dashboard_service, daily/monthly snapshots

### Configuration Schema
- commission_rules, commission_category_rates, commission_badge_tiers,
  country_commission_rates, payout_rules, system_settings, feature_flags
