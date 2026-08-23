# ZOZI Backend — Domain Reorganization Migration Plan (v3)

## Critical Architecture Rules (from ARCHITECTURE_DIAGRAM.md)

### No Controllers
The architecture has **NO controllers**. The concept doesn't exist. Current `*_controller.py` files must be split:
- Router logic → `modules/{module}/routers/`
- Business logic → `domains/{domain}/services/`

### Routers Belong to Modules
All routers live in `modules/{module}/routers/`, NOT in domains. Current `*_controller__routers.py` and `*_router.py` files in `domains/` must move to `modules/`.

### Three Orthogonal Axes
| Axis | What | Where | Mechanism |
|------|------|-------|-----------|
| **Module** | WHO (actor) | `modules/{module}/` | auth + thin routers + serializers |
| **Domain** | WHAT (business) | `domains/{domain}/` | services + models + schemas + policies |
| **Feature** | MAY (permission) | `rbac/` + `domains/*/features.py` | permission atoms |

### Module Structure
```
modules/
├── admin/          ← actor: platform administrator
├── customer/       ← actor: end customer / buyer
├── employee/       ← actor: staff / HR
├── logistics/      ← actor: logistics partner
└── supplier/       ← actor: supplier / vendor
    ├── auth/           ← per-actor login/OTP/social
    ├── routers/        ← THIN routers (auth + require_feature + ONE service call)
    └── serializers/    ← per-actor view models
```

### Domain Structure
```
domains/
├── accounts/           ← business capability
├── analytics/
├── audit/
├── catalog/
├── comms/
├── country/
├── customers/
├── finance/
├── governance/
├── hr/
├── infrastructure/
├── logistics/
├── orders/
├── promotions/         ← NEW
├── security/
└── suppliers/
    ├── services/       ← business logic + DB access ONLY
    ├── models/         ← ORM models (one Postgres schema per domain)
    ├── schemas/        ← Pydantic schemas
    ├── policies/       ← domain policies
    ├── ports.py        ← SANCTIONED cross-domain READ
    ├── events.py       ← cross-domain WRITE bus
    ├── subscribers.py  ← cross-domain WRITE consumer
    ├── read_models/    ← CQRS-lite projections
    └── features.py     ← permission atoms
```

### Key Laws
1. **Arrows point down**: modules → domains → infrastructure
2. **Module routers stay thin**: auth + require_feature + ONE service call. No DB writes, no business rules.
3. **Cross-domain writes** only via events.py/subscribers.py
4. **Cross-domain reads** only via ports.py/read_models/
5. **No controllers**: this concept does not exist in the architecture

---

## Migration Principles

1. **NO FILE DELETION** — All files preserved. Old locations become deprecated stubs.
2. **CONTENT-AWARE MERGING** — Read all source files, identify overlaps, merge into canonical files.
3. **ARCHITECTURE_DIAGRAM.md COMPLIANT** — No controllers, routers in modules/, services in domains/.
4. **PROMOTION SPLIT** — Product-specific (flash-sales, discounts) → `catalog/pricing/`; Cart-level (coupons, coins, banners, BOGO) → `promotions/`.

---

## Phase 0: Preparation

### 0.1 Backup branch
```bash
git checkout -b chore/domain-reorganization-v3
```

### 0.2 Verify current state
```bash
python -c "import backend.main"
```

---

## Phase 1: Create `promotions/` Domain (NEW)

### 1.1 Domain Skeleton
```
domains/promotions/
├── __init__.py
├── events.py              # cross-domain write bus
├── features.py            # promotion permission atoms
├── ports.py               # cross-domain read interface
├── subscribers.py         # cross-domain write consumer
├── models/
│   └── __init__.py
├── policies/
│   └── __init__.py
├── read_models/
│   └── __init__.py
├── schemas/
│   └── __init__.py
└── services/
    ├── __init__.py
    ├── coupons/           # cart-level coupon management
    │   └── __init__.py
    ├── coins/             # zozi coins, referral coins
    │   └── __init__.py
    ├── banners/           # marketing banners
    │   └── __init__.py
    └── bogo/              # buy-one-get-one (cart-level)
        └── __init__.py
```

### 1.2 Content-Aware Merge: Coupon Services → `promotions/services/coupons/`

**Source files (read ALL and merge):**
| Source File | Current Location |
|-------------|------------------|
| `coupons_service.py` | orders/services/ |
| `coupons_read_service.py` | orders/services/ |
| `coupons_write_service.py` | orders/services/ |
| `commerce_coupons_read_service.py` | orders/services/ |
| `commerce_coupons_write_service.py` | orders/services/ |
| `customer_coupons_create_service.py` | orders/services/ |
| `customer_coupons_mgmt_service.py` | orders/services/ |
| `coupons_service.py` | catalog/services/ |
| `coupons_read_service.py` | catalog/services/ |
| `coupons_write_service.py` | catalog/services/ |
| `coupons_service.py` | customers/services/ |
| `coupons_read_service.py` | customers/services/ |
| `coupons_write_service.py` | customers/services/ |

**Router files (move to modules/, NOT services):**
| Source File | Current Location | Target Module |
|-------------|------------------|---------------|
| `coupons_controller.py` | orders/services/ | modules/customer/routers/ |
| `coupons_controller__routers.py` | orders/services/ | modules/customer/routers/ |
| `coupons_controller.py` | catalog/services/ | modules/admin/routers/ |
| `coupons_controller__routers.py` | catalog/services/ | modules/admin/routers/ |

**Merge process:**
1. Read ALL 13 source files
2. Identify duplicate functions (same queries, same business rules)
3. Merge into canonical files:
   - `domains/promotions/services/coupons/coupon_service.py` — core coupon CRUD + validation
   - `domains/promotions/services/coupons/customer_coupon_service.py` — customer-specific coupon logic
4. Router logic → thin routers in modules/
5. Create deprecated stubs at old locations

### 1.3 Content-Aware Merge: Coin Services → `promotions/services/coins/`

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `points_service.py` | catalog/services/ |
| `promotion_points_service.py` | orders/services/ |

**Merge target:** `domains/promotions/services/coins/coin_service.py`

### 1.4 Content-Aware Merge: Banner Services → `promotions/services/banners/`

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `banners_service.py` | catalog/services/ |
| `banner_service.py` | catalog/services/ |
| `banner_write_service.py` | catalog/services/ |
| `banners_service.py` | accounts/services/ |
| `admin_banners_service.py` | accounts/services/ |
| `banner_write_service.py` | orders/services/ |

**Router files (move to modules/):**
| Source File | Target Module |
|-------------|---------------|
| `banner_controller.py` (catalog) | modules/admin/routers/ |
| `admin_banners_service.py` (accounts) | modules/admin/routers/ |

**Merge target:** `domains/promotions/services/banners/banner_service.py`

### 1.5 Content-Aware Merge: BOGO Services → `promotions/services/bogo/`

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `bogo_service.py` | catalog/services/ |
| `promotion_bogo_service.py` | orders/services/ |

**Merge target:** `domains/promotions/services/bogo/bogo_service.py`

### 1.6 Content-Aware Merge: General Promotion Services → `promotions/services/`

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `promotion_service.py` | catalog/services/ |
| `promotion_service.py` | orders/services/ |
| `promotion_engine_service.py` | orders/services/ |
| `promotions_write_service.py` | orders/services/ |

**Router files (move to modules/):**
| Source File | Current Location | Target Module |
|-------------|------------------|---------------|
| `promotion_controller.py` (catalog) | catalog/services/ | modules/admin/routers/ |
| `promotion_controller__routers.py` (catalog) | catalog/services/ | modules/admin/routers/ |
| `promotion_admin_controller.py` (catalog) | catalog/services/ | modules/admin/routers/ |
| `promotion_admin_controller__routers.py` (catalog) | catalog/services/ | modules/admin/routers/ |
| `promotion_controller.py` (orders) | orders/services/ | modules/admin/routers/ |
| `promotion_controller__routers.py` (orders) | orders/services/ | modules/admin/routers/ |
| `promotion_admin_controller.py` (orders) | orders/services/ | modules/admin/routers/ |
| `promotion_admin_controller__routers.py` (orders) | orders/services/ | modules/admin/routers/ |

**Merge targets:**
- `domains/promotions/services/promotion_service.py` — core promotion logic
- `domains/promotions/services/promotion_engine_service.py` — rules engine

---

## Phase 2: Create `catalog/pricing/` Sub-domain

### 2.1 Sub-domain Skeleton
```
domains/catalog/services/pricing/
├── __init__.py
├── flash_sale_service.py
└── discount_service.py
```

### 2.2 Content-Aware Merge: Flash-Sale Services

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `flash_sale_service.py` | orders/services/ |
| `flash_sale_write_service.py` | orders/services/ |

**Router files (move to modules/):**
| Source File | Current Location | Target Module |
|-------------|------------------|---------------|
| `flash_sale_controller.py` | catalog/services/ | modules/admin/routers/ |
| `flash_sale_controller__routers.py` | catalog/services/ | modules/admin/routers/ |
| `flash_sale_controller_service.py` | catalog/services/ | modules/admin/routers/ |
| `flash_sale_controller.py` | orders/services/ | modules/admin/routers/ |
| `flash_sale_controller__routers.py` | orders/services/ | modules/admin/routers/ |
| `flash_sale_controller_service.py` | orders/services/ | modules/admin/routers/ |

**Merge target:** `domains/catalog/services/pricing/flash_sale_service.py`

### 2.3 Content-Aware Merge: Product Discount Services

**Source files:**
| Source File | Current Location |
|-------------|------------------|
| `discount_service.py` | catalog/services/ |
| `product_discount_service.py` | catalog/services/ |

**Merge target:** `domains/catalog/services/pricing/discount_service.py`

---

## Phase 3: Move `media/` to `providers/media/`

### 3.1 Target Structure
```
providers/media/
├── __init__.py
├── ai/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── automation_service.py
│   ├── bg_removal_service.py
│   ├── copy_jobs.py
│   ├── research_jobs.py
│   ├── search_service.py
│   ├── upload_service.py
│   ├── upload_write_service.py
│   └── variant_config.py
├── automation/
│   ├── __init__.py
│   ├── automation_read_service.py
│   └── automation_scheduler.py
├── bg_removal/
│   ├── __init__.py
│   ├── bg_removal_presets.py
│   └── bg_removal_service.py
├── ocr/
│   ├── __init__.py
│   └── ocr_parser.py
├── qr/
│   ├── __init__.py
│   └── qr_service.py
├── storage/
│   ├── __init__.py
│   ├── media_storage.py
│   └── storage.py
├── upload/
│   ├── __init__.py
│   └── upload_job_service.py
├── media_service.py
├── free_image_tools.py
├── image_ai_service.py
├── parcel_verification_service.py
├── visual_voice_search_service.py
└── write_helpers.py
```

### 3.2 Migration Process
- Read each file from `domains/media/services/`
- Move to appropriate sub-folder in `providers/media/`
- Create deprecated stub at old location that re-exports from new location

---

## Phase 4: Clean Up `orders/` Domain

### 4.1 Services to Merge Out (business logic → target domain)

| Service File | Target Domain | Target Path |
|--------------|---------------|-------------|
| `flash_sale_*.py` | catalog/ | services/pricing/ |
| `promotion_*.py` | promotions/ | services/ |
| `coupons_*.py` | promotions/ | services/coupons/ |
| `banner_write_service.py` | promotions/ | services/banners/ |
| `categories_service.py` | catalog/ | services/ |
| `admin_categories_service.py` | catalog/ | services/ |
| `search_service.py` | catalog/ | services/ |
| `fulfillment_service.py` | logistics/ | services/ |
| `supplier_documents_service.py` | suppliers/ | services/ |
| `addresses_service.py` | accounts/ | services/ |
| `admin_email_service.py` | comms/ | services/ |
| `wishlist_*.py` | customers/ | services/ |
| `reviews_*.py` | customers/ | services/ |
| `referrals_*.py` | customers/ | services/ |

### 4.2 Router/Controller Files to Move to modules/

| File | Target Module | Target Path |
|------|---------------|-------------|
| `cart_controller.py` | customer/ | modules/customer/routers/ |
| `cart_controller_service.py` | customer/ | modules/customer/routers/ |
| `cart_controller__routers.py` | customer/ | modules/customer/routers/ |
| `cart_controller_service__orders.py` | customer/ | modules/customer/routers/ |
| `coupons_controller.py` | customer/ | modules/customer/routers/ |
| `coupons_controller__routers.py` | customer/ | modules/customer/routers/ |
| `disputes_controller.py` | customer/ | modules/customer/routers/ |
| `disputes_controller__routers.py` | customer/ | modules/customer/routers/ |
| `flash_sale_controller.py` | admin/ | modules/admin/routers/ |
| `flash_sale_controller__routers.py` | admin/ | modules/admin/routers/ |
| `flash_sale_controller_service.py` | admin/ | modules/admin/routers/ |
| `logistics_controller.py` | logistics/ | modules/logistics/routers/ |
| `logistics_controller__routers.py` | logistics/ | modules/logistics/routers/ |
| `logistics_partner_controller.py` | logistics/ | modules/logistics/routers/ |
| `logistics_partner_controller__routers.py` | logistics/ | modules/logistics/routers/ |
| `orders_controller.py` | customer/ | modules/customer/routers/ |
| `orders_controller__routers.py` | customer/ | modules/customer/routers/ |
| `promotion_controller.py` | admin/ | modules/admin/routers/ |
| `promotion_controller__routers.py` | admin/ | modules/admin/routers/ |
| `promotion_admin_controller.py` | admin/ | modules/admin/routers/ |
| `promotion_admin_controller__routers.py` | admin/ | modules/admin/routers/ |
| `referrals_controller.py` | customer/ | modules/customer/routers/ |
| `referrals_controller__routers.py` | customer/ | modules/customer/routers/ |
| `returns_controller.py` | customer/ | modules/customer/routers/ |
| `returns_controller_service.py` | customer/ | modules/customer/routers/ |
| `returns_controller__routers.py` | customer/ | modules/customer/routers/ |
| `reviews_controller.py` | customer/ | modules/customer/routers/ |
| `reviews_controller__routers.py` | customer/ | modules/customer/routers/ |
| `wishlist_controller.py` | customer/ | modules/customer/routers/ |
| `wishlist_controller__routers.py` | customer/ | modules/customer/routers/ |

### 4.3 Remaining orders/ Services (canonical, no routers/controllers)
```
orders/services/
├── cart/
│   ├── cart_service.py
│   └── cart_write_service.py
├── checkout/
│   ├── commerce.py
│   ├── commerce_read_service.py
│   └── commerce_write_service.py
├── tracking/
│   ├── order_tracking_service.py
│   └── orders_order_tracking_service.py
├── disputes/
│   ├── disputes_service.py
│   └── disputes_write_service.py
├── returns/
│   ├── returns_service.py
│   └── returns_write_service.py
├── orders_service.py
├── orders_write_facade.py
├── orders_write_service.py
├── package_service.py
├── bulk_order_service.py
└── ghost_watchdog.py
```

---

## Phase 5: Clean Up `catalog/` Domain

### 5.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `flash_sale_*.py` | catalog/ → services/pricing/ |
| `promotion_*.py` | promotions/ |
| `coupons_*.py` | promotions/ |
| `bogo_service.py` | promotions/ |
| `points_service.py` | promotions/ |
| `banners_*.py` | promotions/ |
| `banner_*.py` | promotions/ |
| `supplier_products_service.py` | suppliers/ |
| `country_dropdown_service.py` | country/ |

### 5.2 Router/Controller Files to Move to modules/

| File | Target Module |
|------|---------------|
| `banner_controller.py` (catalog) | modules/admin/routers/ |
| `categories_controller.py` (catalog) | modules/admin/routers/ |
| `category_admin_controller.py` (catalog) | modules/admin/routers/ |
| `category_admin_controller__routers.py` (catalog) | modules/admin/routers/ |
| `coupons_controller.py` (catalog) | modules/admin/routers/ |
| `coupons_controller__routers.py` (catalog) | modules/admin/routers/ |
| `flash_sale_controller.py` (catalog) | modules/admin/routers/ |
| `flash_sale_controller__routers.py` (catalog) | modules/admin/routers/ |
| `flash_sale_controller_service.py` (catalog) | modules/admin/routers/ |
| `products_controller.py` (catalog) | modules/admin/routers/ |
| `products_controller__routers.py` (catalog) | modules/admin/routers/ |
| `promotion_controller.py` (catalog) | modules/admin/routers/ |
| `promotion_controller__routers.py` (catalog) | modules/admin/routers/ |
| `promotion_admin_controller.py` (catalog) | modules/admin/routers/ |
| `promotion_admin_controller__routers.py` (catalog) | modules/admin/routers/ |

### 5.3 Remaining catalog/ Services (canonical, sliced, NO routers)
```
catalog/services/
├── products/
│   ├── product_service.py
│   ├── products_write_service.py
│   ├── product_admin_read_service.py
│   ├── product_admin_write_service.py
│   ├── product_moderation_service.py
│   ├── product_verification_service.py
│   └── product_verification_write_service.py
├── categories/
│   ├── category_service.py
│   ├── category_admin_read_service.py
│   └── category_admin_write_service.py
├── search/
│   ├── search_service.py
│   ├── advanced_search_engine.py
│   ├── advanced_filter_service.py
│   └── visual_search_service.py
├── variants/
│   ├── variant_config_service.py
│   └── catalog_variant_config_service.py
└── pricing/
    ├── flash_sale_service.py
    └── discount_service.py
```

---

## Phase 6: Clean Up `accounts/` Domain

### 6.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `admin_banners_service.py` | promotions/ |
| `admin_categories_service.py` | catalog/ |
| `admin_chat_service.py` | comms/ |
| `admin_commission_service.py` | finance/ |
| `admin_email_service.py` | comms/ |
| `admin_logistics_service.py` | logistics/ |
| `admin_orders_service.py` | orders/ |
| `admin_payouts_service.py` | finance/ |
| `admin_products_service.py` | catalog/ |
| `admin_promotions_*.py` | promotions/ |
| `admin_suppliers_service.py` | suppliers/ |
| `admin_treasury_service.py` | finance/ |
| `admin_video_service.py` | providers/media/ |
| `banners_service.py` | promotions/ |
| `categories_service.py` | catalog/ |
| `commission_service.py` | finance/ |
| `country_*.py` | country/ |
| `customer_coupons_*.py` | promotions/ |
| `employees_service.py` | hr/ |
| `hr_service.py` | hr/ |
| `logistics_*.py` | logistics/ |
| `payroll_service.py` | hr/ |
| `search_service.py` | catalog/ |
| `supplier_*.py` | suppliers/ |
| `shipments_service.py` | logistics/ |
| `wishlist_service.py` | customers/ |
| `translation_service.py` | country/ |
| `translate_controller.py` | country/ |

### 6.2 Remaining accounts/ Services (canonical)
```
accounts/services/
├── identity/
│   ├── identity_service.py
│   ├── identity_admin_service.py
│   └── iam_service.py
├── auth/
│   ├── auth_service.py
│   ├── otp_service.py
│   └── session_service.py
├── users/
│   ├── users_service.py
│   ├── users_write_service.py
│   ├── user_read_service.py
│   └── user_write_ops.py
├── permissions/
│   ├── permissions_service.py
│   └── rbac_service.py
├── addresses_service.py
├── approval_matrix_service.py
├── social_service.py
├── export_service.py
└── export_controller.py
```

---

## Phase 7: Clean Up `governance/` Domain

### 7.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `orders_service.py` | orders/ |
| `flat_orders_service.py` | orders/ |
| `products_service.py` | catalog/ |
| `flat_products_service.py` | catalog/ |
| `suppliers_service.py` | suppliers/ |
| `suppliers_controller.py` | suppliers/ |
| `fraud_*.py` | finance/ |
| `payouts_*.py` | finance/ |
| `admin_finance_*.py` | finance/ |
| `admin_logistics_*.py` | logistics/ |
| `admin_catalog_*.py` | catalog/ |
| `admin_orders_*.py` | orders/ |
| `admin_supplier_*.py` | suppliers/ |
| `admin_commerce_*.py` | promotions/ |
| `admin_comms_*.py` | comms/ |
| `admin_media_*.py` | providers/media/ |
| `admin_security_*.py` | security/ |
| `admin_geography_*.py` | country/ |
| `country_*.py` | country/ |
| `addresses_service.py` | accounts/ |
| `users_*.py` | accounts/ |
| `identity_*.py` | accounts/ |
| `auth_*.py` | accounts/ |
| `permissions_*.py` | accounts/ |

### 7.2 Remaining governance/ Services (canonical)
```
governance/services/
├── admin/
│   ├── admin_service.py
│   ├── admin_controller.py
│   ├── admin_write_service.py
│   ├── admin_fallback_service.py
│   └── admin_support_service.py
├── analytics/
│   ├── analytics_service.py
│   └── analytics_fallback_service.py
├── audit/
│   ├── audit_service.py
│   ├── audit_query_service.py
│   └── audit_trail_service.py
├── auth/
│   ├── auth_service.py
│   └── auth_write_service.py
├── command_center/
│   └── command_center_service.py
├── compliance/
│   ├── compliance_engine.py
│   ├── data_residency.py
│   └── retention_service.py
├── fraud/
│   ├── fraud_service.py
│   └── fraud_detection.py
├── incident/
│   └── incident_service.py
├── permissions/
│   └── permissions_service.py
├── risk/
│   ├── risk_service.py
│   └── risk_controller.py
├── security/
│   ├── security_effective_permissions.py
│   └── security_fraud_admin_service.py
└── settings/
    ├── settings_service.py
    └── database_service.py
```

---

## Phase 8: Clean Up `customers/` Domain

### 8.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `cart_service.py` | orders/ |
| `cart_write_service.py` | orders/ |
| `commerce_read_service.py` | orders/ |
| `commerce_write_service.py` | orders/ |
| `coupons_*.py` | promotions/ |
| `search_service.py` | catalog/ |
| `user_read_service.py` | accounts/ |

### 8.2 Remaining customers/ Services (canonical)
```
customers/services/
├── customer_health_engine.py
├── customer_health_list_service.py
├── customer_health_service.py
├── customer_router_service.py
├── referrals_service.py
├── reviews_service.py
├── wishlist_read_service.py
├── wishlist_service.py
└── wishlist_write_service.py
```

---

## Phase 9: Clean Up `finance/` Domain

### 9.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `ai_*.py` | providers/media/ |
| `automation_*.py` | providers/media/ |
| `bg_removal_*.py` | providers/media/ |
| `ocr_parser.py` | providers/media/ |
| `parcel_verification_service.py` | providers/media/ |
| `import_service.py` | providers/media/ |
| `erp_*.py` | providers/media/ |
| `order_payment_functions.py` | orders/ |
| `disputes_*.py` | orders/ |
| `public_commerce_validation_service.py` | orders/ |

### 9.2 Remaining finance/ Services (canonical, sliced)
```
finance/services/
├── payments/
│   ├── payments.py
│   ├── payments_write_service.py
│   ├── payment_engine.py
│   ├── payment_orchestrator.py
│   ├── payment_event_handlers.py
│   ├── gateway_reconciliation_service.py
│   └── gateway_auto_enable.py
├── payouts/
│   ├── payout_engine.py
│   ├── payout_batch_service.py
│   ├── payout_dispatch_service.py
│   ├── payout_read_service.py
│   ├── payout_status_service.py
│   ├── payout_admin_service.py
│   ├── payout_admin_write_service.py
│   ├── payout_approval_controller.py
│   ├── payout_approval_read_service.py
│   ├── payout_approval_service.py
│   └── payout_approval_write_service.py
├── commissions/
│   ├── commission_service.py
│   ├── commission_engine.py
│   ├── commission_geography_service.py
│   └── commission_write_service.py
├── treasury/
│   ├── treasury.py
│   ├── treasury_service.py
│   ├── treasury_engine.py
│   ├── treasury_adapter.py
│   ├── treasury_query_service.py
│   ├── cash_management_service.py
│   ├── cash_management_controller.py
│   └── cash_management_write_service.py
├── ledger/
│   ├── general_ledger_service.py
│   ├── sub_ledger_service.py
│   ├── sub_ledger_controller.py
│   ├── accounting_controller.py
│   ├── invoice_service.py
│   ├── invoice_controller.py
│   └── invoice_write_service.py
├── tax/
│   ├── tax_service.py
│   └── vat_rates.py
└── reporting/
    ├── financial_reporting.py
    ├── financial_reports_service.py
    ├── finance_dashboard_service.py
    └── reporting_service.py
```

---

## Phase 10: Clean Up `logistics/` Domain

### 10.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `country_communication_service.py` | country/ |
| `geography_*.py` | country/ |
| `logistics_orders_*.py` | orders/ |

### 10.2 Remaining logistics/ Services (canonical, sliced)
```
logistics/services/
├── shipping/
│   ├── shipping_tier.py
│   └── shipment_service.py
├── fulfillment/
│   └── fulfillment_service.py
├── tracking/
│   └── live_tracking_service.py
├── partners/
│   ├── logistics_partner_service.py
│   ├── logistics_partner_pricing.py
│   ├── logistics_partner_verify_service.py
│   ├── logistics_partner_shipments_service.py
│   └── partner_geography_service.py
├── geo/
│   ├── geo_fence_service.py
│   ├── geo_resolver.py
│   └── map_service.py
├── health/
│   ├── logistics_health_service.py
│   └── logistics_health_engine.py
└── sla/
    └── logistics_sla_service.py
```

---

## Phase 11: Clean Up `suppliers/` Domain

### 11.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `supplier_finance_service.py` | finance/ |
| `supplier_payouts_service.py` | finance/ |
| `supplier_payout_service.py` | finance/ |
| `badge_billing_payment.py` | finance/ |
| `cash_management_controller_service.py` | finance/ |

### 11.2 Remaining suppliers/ Services (canonical, sliced)
```
suppliers/services/
├── profile/
│   ├── supplier_profile_service.py
│   ├── supplier_profile_create_service.py
│   └── supplier_profile_write_service.py
├── products/
│   ├── supplier_products_service.py
│   ├── supplier_products_upload_service.py
│   └── product_coordinator_service.py
├── documents/
│   ├── supplier_documents_service.py
│   └── supplier_document_service.py
├── onboarding/
│   ├── supplier_onboarding_service.py
│   └── onboarding_pipeline.py
├── orders/
│   ├── supplier_order_service.py
│   ├── supplier_orders_service.py
│   └── supplier_orders_verify_service.py
├── health/
│   ├── supplier_health_service.py
│   └── supplier_health_engine.py
├── badges/
│   ├── supplier_badge_service.py
│   └── supplier_badge_write_service.py
├── contracts/
│   └── supplier_legal_contract_service.py
└── analytics/
    └── supplier_analytics_service.py
```

---

## Phase 12: Clean Up `comms/` Domain

### 12.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `free_image_tools.py` | providers/media/ |
| `image_ai_service.py` | providers/media/ |
| `media_service.py` | providers/media/ |
| `media_storage.py` | providers/media/ |
| `storage.py` | providers/media/ |
| `asset_tracking.py` | hr/ |
| `qr_service.py` | providers/media/ |
| `upload_job_service.py` | providers/media/ |
| `import_service.py` | providers/media/ |
| `package_service.py` | orders/ |
| `payout_notification_service.py` | finance/ |

### 12.2 Remaining comms/ Services (canonical, sliced)
```
comms/services/
├── messaging/
│   ├── chat_system.py
│   ├── chat_read_service.py
│   ├── chat_write_service.py
│   ├── chatbot_service.py
│   ├── entity_chat_service.py
│   └── realtime_chat_service.py
├── email/
│   ├── email_service.py
│   ├── email_gateway.py
│   ├── email_management_service.py
│   ├── email_write_service.py
│   ├── email_event_service.py
│   ├── transactional_email.py
│   └── transactional_email_service.py
├── notifications/
│   ├── notification_service.py
│   ├── notification_engine.py
│   └── push_notifications_service.py
├── video/
│   ├── video_service.py
│   ├── video_conferencing.py
│   └── video_room_service.py
├── tickets/
│   └── tickets_service.py
└── marketing/
    └── campaign_geography_service.py
```

---

## Phase 13: Clean Up `country/` Domain

### 13.1 Services to Merge Out

| Service File | Target Domain |
|--------------|---------------|
| `supplier_finance_service.py` | finance/ |
| `supplier_payouts_service.py` | finance/ |

### 13.2 Remaining country/ Services (canonical, sliced)
```
country/services/
├── core/
│   ├── countries_service.py
│   ├── country_service.py
│   ├── country_read_service.py
│   └── country_write_service.py
├── localization/
│   └── localization_service.py
├── tax/
│   ├── country_tax_service.py
│   └── category_tax_profiles.py
├── cross_border/
│   ├── cross_border_service.py
│   ├── cross_border_detection.py
│   └── cross_border_tracker.py
├── geo/
│   ├── geo_resolver.py
│   ├── country_detection.py
│   └── country_dropdown_service.py
├── payouts/
│   └── country_payouts_service.py
├── research/
│   ├── country_research.py
│   ├── country_auto_populate.py
│   └── country_curated.py
├── restriction/
│   └── country_restriction_service.py
├── staff/
│   └── country_staff_service.py
└── versioning/
    └── country_versioning_service.py
```

---

## Phase 14: Clean Up `hr/` Domain

(Already well-structured, no changes needed)

---

## Phase 15: Distribute `_parked/` (Don't Delete)

### 15.1 Migrate All _parked/ Files

| File | Target Domain | Target Path | Type |
|------|---------------|-------------|------|
| `addresses_service.py` | accounts/ | services/ | service |
| `admin_categories_service.py` | catalog/ | services/ | service |
| `admin_promotions_write_service.py` | promotions/ | services/ | service |
| `admin_promotion_service.py` | promotions/ | services/ | service |
| `banner_write_service.py` | promotions/ | services/banners/ | service |
| `cart_controller_service__orders.py` | customer/ | modules/customer/routers/ | router |
| `cart_service__orders.py` | orders/ | services/ | service |
| `categories_service.py` | catalog/ | services/ | service |
| `commerce_coupons_read_service.py` | promotions/ | services/coupons/ | service |
| `commerce_coupons_write_service.py` | promotions/ | services/coupons/ | service |
| `coupons_legacy_write_service.py` | promotions/ | services/coupons/ | service |
| `customer_coupons_create_service.py` | promotions/ | services/coupons/ | service |
| `customer_coupons_mgmt_service.py` | promotions/ | services/coupons/ | service |
| `flash_sale_service.py` | catalog/ | services/pricing/ | service |
| `flash_sale_write_service.py` | catalog/ | services/pricing/ | service |
| `orders_package_service.py` | orders/ | services/ | service |
| `promotions_write_service.py` | promotions/ | services/ | service |
| `promotion_admin_write_service.py` | promotions/ | services/ | service |
| `promotion_bogo_service.py` | promotions/ | services/bogo/ | service |
| `promotion_engine_service.py` | promotions/ | services/ | service |
| `promotion_points_service.py` | promotions/ | services/coins/ | service |
| `referrals_controller__routers.py` | customer/ | modules/customer/routers/ | router |
| `search_service.py` | catalog/ | services/ | service |
| `supplier_documents_service.py` | suppliers/ | services/documents/ | service |

### 15.2 Keep _parked/ as Deprecated Stub Folder
- Leave folder with README explaining migration
- Add deprecated import stubs if needed

---

## Phase 16: Clean Up `infrastructure/` Domain

### 16.1 Move Infrastructure Tools from domains/ Root

| Source File | Target Path | Type |
|-------------|-------------|------|
| `domains/_async_workers.py` | infrastructure/services/workers/ | service |
| `domains/_image_tools.py` | providers/media/ | provider |
| `domains/_key_rotation.py` | infrastructure/services/ | service |
| `domains/_seed.py` | infrastructure/services/ | service |
| `domains/_service_registry.py` | infrastructure/services/ | service |

---

## Phase 17: Update Imports & Router Registration

### 17.1 Import Update Strategy
For each moved file:
1. Create new file at target location with merged content
2. At old location, create deprecated stub:
```python
# DEPRECATED: Moved to domains.promotions.services.coupons.coupon_service
# This stub exists for backward compatibility. See DOMAIN_ALLOWLIST.yaml.
from domains.promotions.services.coupons.coupon_service import *  # noqa: F401,F403
```

### 17.2 Update DOMAIN_ALLOWLIST.yaml
Track all temporary cross-domain imports that still need updating.

### 17.3 Update Router Registration
Update `backend/main.py` to register routers from modules/ only.

---

## Phase 18: Testing & Validation

### 18.1 Import Check
```bash
python -c "import backend.main"
```

### 18.2 Run Tests
```bash
pytest backend/tests/ -x -v
```

### 18.3 Verify No Broken Imports
```bash
grep -r "from domains\." backend/ --include="*.py" | grep -v "__pycache__" | grep -v "deprecated"
```

---

## Migration Order (Priority)

| Phase | Description | Risk | Effort |
|-------|-------------|------|--------|
| 0 | Preparation | Low | Low |
| 1 | Create promotions/ domain | Low | High (content merge) |
| 2 | Create catalog/pricing/ sub-domain | Low | Medium (content merge) |
| 3 | Move media/ to providers/ | Medium | High (content merge) |
| 4 | Clean up orders/ | High | High |
| 5 | Clean up catalog/ | Medium | Medium |
| 6 | Clean up accounts/ | High | High |
| 7 | Clean up governance/ | High | High |
| 8 | Clean up customers/ | Low | Low |
| 9 | Clean up finance/ | Medium | High |
| 10 | Clean up logistics/ | Medium | Medium |
| 11 | Clean up suppliers/ | Medium | Medium |
| 12 | Clean up comms/ | Medium | Medium |
| 13 | Clean up country/ | Low | Low |
| 14 | Clean up hr/ | Low | Low |
| 15 | Distribute _parked/ | Low | Medium |
| 16 | Clean up infrastructure/ | Low | Low |
| 17 | Update imports | High | High |
| 18 | Testing | High | High |

---

## Final Architecture

### Backend Package Layout
```
backend/
├── main.py
├── config.py
├── DOMAIN_ALLOWLIST.yaml
│
├── modules/                    # AXIS 1 — MODULE (who)
│   ├── admin/
│   │   ├── auth/
│   │   ├── routers/            # ALL admin routers live here
│   │   └── serializers/
│   ├── customer/
│   │   ├── auth/
│   │   ├── routers/            # ALL customer routers live here
│   │   └── serializers/
│   ├── employee/
│   │   ├── auth/
│   │   ├── routers/
│   │   └── serializers/
│   ├── logistics/
│   │   ├── auth/
│   │   ├── routers/
│   │   └── serializers/
│   └── supplier/
│       ├── auth/
│       ├── routers/
│       └── serializers/
│
├── domains/                    # AXIS 2 — DOMAIN (what)
│   ├── accounts/
│   │   ├── services/           # business logic ONLY (no routers)
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── policies/
│   │   ├── ports.py
│   │   ├── events.py
│   │   ├── subscribers.py
│   │   ├── read_models/
│   │   └── features.py
│   ├── analytics/
│   ├── audit/
│   ├── catalog/
│   │   └── services/
│   │       ├── products/
│   │       ├── categories/
│   │       ├── search/
│   │       ├── variants/
│   │       └── pricing/       # flash-sales, discounts
│   ├── comms/
│   ├── country/
│   ├── customers/
│   ├── finance/
│   │   └── services/
│   │       ├── payments/
│   │       ├── payouts/
│   │       ├── commissions/
│   │       ├── treasury/
│   │       ├── ledger/
│   │       ├── tax/
│   │       └── reporting/
│   ├── governance/
│   ├── hr/
│   ├── infrastructure/
│   ├── logistics/
│   ├── orders/
│   │   └── services/
│   │       ├── cart/
│   │       ├── checkout/
│   │       ├── tracking/
│   │       ├── disputes/
│   │       └── returns/
│   ├── promotions/             # NEW
│   │   └── services/
│   │       ├── coupons/
│   │       ├── coins/
│   │       ├── banners/
│   │       └── bogo/
│   ├── security/
│   └── suppliers/
│
├── rbac/                       # AXIS 3 — FEATURE (may)
├── kernel/                     # SHARED KERNEL
├── infrastructure/             # PLATFORM
├── providers/                  # 3rd-party/AI adapters
│   ├── ai/
│   ├── media/                  # moved from domains/media/
│   └── ...
├── jobs/
├── middleware/
├── alembic/
├── scripts/
└── tests/
```

---

## Risk Mitigation

1. **Git commits after each phase**
2. **Run tests after each phase**
3. **Content-aware merging** — read files before merging
4. **Deprecated stubs** — old locations re-export from new
5. **DOMAIN_ALLOWLIST.yaml** — track temporary cross-domain imports
6. **Update AGENTS.md** — document new structure
