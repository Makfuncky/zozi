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

## Phase 19: Router Restructuring — `modules/{m}/routers/{d}.py` (15 files per module)

### 19.1 Goal
Restructure all router files from the current flat/haphazard layout into a **consistent domain-per-file** pattern:
```
modules/{m}/routers/{d}.py
```
Where `{m}` = module (admin, customer, employee, logistics, supplier) and `{d}` = domain (15 domains).

**Result:** Exactly 15 router files per module × 5 modules = 75 router files total (down from 476).

### 19.2 The 15 Domain Routers (per module)
| # | Domain Router File | Covers |
|---|---|---|
| 1 | `accounts.py` | User accounts, identity, sessions, addresses |
| 2 | `analytics.py` | Analytics dashboards, reports |
| 3 | `audit.py` | Audit trails, compliance logs |
| 4 | `catalog.py` | Products, categories, search, variants, pricing, uploads |
| 5 | `comms.py` | Chat, email, notifications, tickets, video |
| 6 | `country.py` | Countries, localization, cross-border, tax |
| 7 | `customers.py` | Customer profiles, health, referrals, reviews, wishlist |
| 8 | `finance.py` | Payments, payouts, commissions, treasury, ledger, tax |
| 9 | `governance.py` | Admin, permissions, fraud, risk, compliance |
| 10 | `hr.py` | Employees, payroll, hierarchy, LMS, OKR, attendance |
| 11 | `logistics.py` | Shipping, fulfillment, tracking, partners, geo |
| 12 | `orders.py` | Cart, checkout, orders, disputes, returns |
| 13 | `promotions.py` | Coupons, coins, banners, BOGO, flash sales |
| 14 | `security.py` | Fraud detection, threat intel, auth policies |
| 15 | `suppliers.py` | Supplier profiles, products, documents, onboarding |

> **Note:** `media` is a **provider** (already in `providers/media/`), not a domain. `infrastructure` is a **platform layer**, not a domain. Neither gets a router file.

### 19.3 Migration Process
See detailed plan: **`backend/ROUTER_CORRECTION_PLAN.md`** (module-by-module mapping of 476 → 75 files).

1. **Fix 7 critical middleware blockers first** (so app can start)
2. **For each module** (admin, customer, employee, logistics, supplier):
   - Read all existing router files listed in `__init__.py`
   - Group endpoints by target domain (see plan for exact mapping)
   - Merge into the 15 canonical domain router files
   - Remove duplicate endpoints
   - Ensure thin-router pattern: auth + require_feature + ONE service call
3. **Update** `modules/{m}/routers/__init__.py` to import the 15 domain routers
4. **Create deprecated stubs** for old router files
5. **Test** all endpoints still register correctly

### 19.4 Benefits
- **Manageable at scale:** 75 files vs 476 — easier navigation for 100K+ user codebase
- **Domain clarity:** Each router file maps to exactly one business domain
- **Consistent structure:** Same 15 files exist in every module, only the actor changes
- **Easier onboarding:** New developers find endpoints by domain, not by module

---

## Phase 20: Fix All Broken Imports (Critical)

### 20.1 Critical Blockers (Prevent App Startup)
These broken imports prevent the app from starting at all:

| # | File | Broken Import | Fix |
|---|------|--------------|-----|
| 1 | `middleware/country_context.py:39` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 2 | `middleware/coi_middleware.py:10` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 3 | `middleware/dependencies/coi_dependency.py:10` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 4 | `middleware/impossible_travel_middleware.py:156` | `domains.governance.services.security.impossible_travel_write_service` | Function doesn't exist — implement or remove |
| 5 | `middleware/impossible_travel_middleware.py:349` | `domains.governance.services.fraud.fraud_detection_service` | → `domains.security.services.fraud_detection_service` |
| 6 | `middleware/device_binding_middleware.py:69-70` | `ServiceMeshSecurity()` / `NetworkPolicy()` | Classes don't exist — implement or remove |
| 7 | `middleware/dependencies/fraud_events.py:21` | `infrastructure.database.models.FraudEvent` | → `domains.governance.models.fraud.FraudEvent` |

### 20.2 High-Impact Router Import Errors (~1,789 occurrences)
Router files reference service modules that don't exist on disk. Top patterns:

| Pattern | Count | Fix Approach |
|---------|-------|-------------|
| `domains.governance.services.{domain}.{service}` | ~800 | Planned-but-unimplemented. Create stubs or redirect to actual service location |
| `domains.hr.services.{subdomain}.{service}` | ~200 | HR restructured into subpackages. Update imports to actual paths |
| `domains.comms.services.{subdomain}.{service}` | ~150 | Comms restructured. Update imports to actual paths |
| `domains.finance.services.{subdomain}.{service}` | ~200 | Finance restructured. Update imports to actual paths |
| `domains.country.services.{subdomain}.{service}` | ~100 | Country restructured. Update imports to actual paths |
| Flat files that never existed | ~300 | Either create the service or remove the import |

### 20.3 Domain Service Import Errors (~283 occurrences)
Cross-domain imports within services that reference non-existent modules.

### 20.4 Provider/Infrastructure Import Errors (174 occurrences)
Missing third-party packages and domain imports that reference unimplemented modules.

### 20.5 Fix Strategy
1. **Fix critical blockers first** (Phase 20.1) — app can't start without these
2. **Create missing service stubs** for planned-but-unimplemented modules
3. **Update import paths** for restructured domains (hr, comms, finance, country)
4. **Install missing third-party packages** (cv2, rembg, bcrypt, etc.)
5. **Remove dead imports** for functionality that will never be implemented

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
| 19 | Router restructuring (15 files/module) | Medium | High |
| 20 | Fix all broken imports | Critical | High |

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


-------------------------------------------------------------
-------------------------------------------------------------

## 🏗️ ZOZI E-Commerce — Proper Domain Architecture

### Provider Layer (`backend/providers/`)
**Tools/Services consumed by domains — NOT domains themselves**

| Provider | Purpose | Consumed By |
|----------|---------|-------------|
| `ai/` | Chatbot, Vision, Search, Text, Web Search, MCP | catalog, comms, suppliers, finance |
| `payments/` | Stripe, PayPal, PayTabs, Tap, Thawani, Paytrail | finance, orders |
| `image/` | BG Removal, OCR, Parcel Verification | suppliers, finance, catalog |
| `br_remover/` | Background removal models | suppliers (product images) |
| `comms/` | Email, Twilio, WhatsApp | comms, orders, customers |
| `geography/` | Country data, GeoIP, Maps, Rates | country, logistics, orders |
| `geo/` | Geolocation services | logistics, country |
| `finance/` | Bank API | finance |
| `auth/` | JWT, OAuth, Apple, TOTP | accounts, governance |
| `automation/` | Task scheduler | catalog, media, orders |
| `security/` | Encryption, Threat Intel, Watchlist | governance, security |
| `voice/` | Voice-to-text | comms |
| `storage/` | File storage | media, suppliers |
| `news/` | RSS feeds | catalog |
| `analytics/` | Analytics engine | analytics |

---

### Domain Layer (`backend/domains/`)

#### 1. `accounts/` — User Account Management
```
accounts/
├── sub-domains/
│   ├── identity/          — User identity, registration, login
│   ├── profile/           — User profiles, preferences
│   ├── addresses/         — User addresses
│   ├── sessions/          — Session management, tokens
│   └── approval/          — Approval matrix, user verification
├── features:
    ├── User registration & authentication
    ├── Profile management
    ├── Address book
    ├── Session management
    ├── Approval workflows
    ├── User CRUD operations
    └── Identity verification
```

#### 2. `catalog/` — Product Catalog & Discovery
```
catalog/
├── sub-domains/
│   ├── products/          — Product CRUD, variants, moderation
│   ├── categories/        — Category tree, taxonomy
│   ├── search/            — Advanced search, filters, sorting
│   ├── variants/          — Product variants, configurations
│   └── verification/      — Product verification, moderation
├── features:
    ├── Product management (CRUD)
    ├── Category management
    ├── Advanced search engine
    ├── Filtering & sorting
    ├── Product variants
    ├── Product moderation/verification
    ├── Bulk operations
    ├── Visual search
    └── Catalog analytics
```

#### 3. `promotions/` — Marketing Promotions & Incentives *(NEW — needs creation)*
```
promotions/
├── sub-domains/
│   ├── coupons/           — Coupon creation, validation, redemption
│   ├── discounts/         — Discount rules, placement
│   ├── points/            — Zozi coins, loyalty points
│   ├── referrals/         — Referral Zozi coins, referral tracking
│   ├── banners/           — Banner management
│   ├── flash-sales/       — Flash sale events
│   ├── bogo/              — Buy-one-get-one offers
│   └── engine/            — Promotion engine, rules evaluation
├── features:
    ├── Coupon management (CRUD)
    ├── Discount rules engine
    ├── Zozi coins (loyalty points)
    ├── Referral Zozi coins
    ├── Banner management
    ├── Flash sale management
    ├── BOGO promotions
    ├── Promotion validation
    ├── Customer-specific coupons
    └── Promotion analytics
```

#### 4. `orders/` — Order Management & Checkout
```
orders/
├── sub-domains/
│   ├── cart/              — Shopping cart management
│   ├── checkout/          — Checkout flow, payment orchestration
│   ├── tracking/          — Order tracking, status updates
│   ├── disputes/          — Order disputes, claims
│   ├── returns/           — Return requests, refunds
│   ├── fulfillment/       — Fulfillment coordination
│   └── commerce/          — Commerce read/write operations
├── features:
    ├── Cart management
    ├── Checkout process
    ├── Order lifecycle management
    ├── Order tracking
    ├── Dispute management
    ├── Returns & refunds
    ├── Fulfillment coordination
    ├── Package management
    ├── Bulk orders
    └── Order analytics
```

#### 5. `suppliers/` — Supplier Management
```
suppliers/
├── sub-domains/
│   ├── profile/           — Supplier profiles, onboarding
│   ├── products/          — Product upload, management, discount placement
│   ├── documents/         — Legal documents, verification
│   ├── finance/           — Supplier finance, payouts
│   ├── orders/            — Supplier order management
│   ├── analytics/         — Supplier analytics, performance
│   ├── health/            — Supplier health monitoring
│   ├── badges/            — Supplier badges, ratings
│   └── contracts/         — Legal contracts, compliance
├── features:
    ├── Supplier profile management
    ├── Supplier onboarding pipeline
    ├── Product upload & management
    ├── Supplier discount placement
    ├── Document management
    ├── Supplier finance/payouts
    ├── Supplier order verification
    ├── Supplier analytics
    ├── Health monitoring
    ├── Badge/billing system
    └── Contract management
```

#### 6. `finance/` — Financial Operations
```
domains/finance/
├── events.py                          (106)  ← domain events
├── features.py                        (38)   ← RBAC atoms
├── ports.py                           (607)  ← sanctioned cross-domain reads
├── subscribers.py                     (53)   ← event consumers
├── __init__.py                        (2)
│
├── models/
│   ├── __init__.py                    (4)    ← exports Base
│   ├── general_ledger.py              (1124) ← GL, journal, ledger, invoices, treasury accts
│   ├── commission.py                  (104)  ← commission agreements, rates, ledger
│   ├── erp.py                         (393)  ← PO, GRN, sales orders, stock movements
│   ├── payments.py                    (147)  ← Payment, Payout, LogisticsPartnerPayout
│   └── finance.py                     (96)   ← re-export shim
│
├── policies/
│   ├── __init__.py                    (4)
│   └── finance_policies.py            (16)
│
├── read_models/
│   └── __init__.py                    (5)
│
├── schemas/
│   ├── __init__.py                    (14)
│   └── finance_schemas.py             (23)
│
└── services/
    ├── __init__.py                    (2)    ← lazy delegator
    ├── finance.py                     (30)   ← lazy delegator
    ├── treasury.py                    (29)   ← lazy delegator alias
    ├── admin_cash_service.py          (54)   ← root-level (should move)
    ├── admin_treasury_service.py      (228)  ← root-level (should move)
    │
    ├── accounts/                      (4 files)
    │   ├── contractor_milestone_read_service.py  (26)
    │   ├── credit_control_service.py             (267)
    │   ├── trading_read_service.py               (33)
    │   └── trading_service.py                     (768)
    │
    ├── commission/                    (7 files)
    │   ├── commission_admin_write_service.py     (83)
    │   ├── commission_controller.py               (40)
    │   ├── commission_engine.py                   (450)
    │   ├── commission_geography_service.py        (88)
    │   ├── commission_service.py                  (809)
    │   ├── commission_write_service.py            (113)
    │   ├── supplier_finance_service.py            (443)
    │   └── supplier_payouts_service.py            (44)
    │
    ├── country/                       (9 files)
    │   ├── admin_cash_service.py                  (54)
    │   ├── admin_commission_service.py            (100)
    │   ├── admin_finance_creation_service.py      (62)
    │   ├── admin_finance_geography_service.py     (30)
    │   ├── admin_logistics_fallback_read_service.py (171)
    │   ├── country_ai_research.py                 (509)
    │   ├── finance_commission_geography_service.py (7)
    │   └── public_finance_creation_service.py     (39)
    │
    ├── ledger/                        (13 files)
    │   ├── accounting_controller.py               (129)
    │   ├── bank_transaction_service.py            (9)
    │   ├── expense_processing.py                  (103)
    │   ├── expense_routing.py                     (91)
    │   ├── finance_automation.py                  (483)
    │   ├── finance_automation_write_service.py    (62)
    │   ├── finance_erp_write_service.py           (61)
    │   ├── finance_transfer_service.py            (1000)
    │   ├── general_ledger_service.py              (955)
    │   ├── invoice_controller.py                  (17)
    │   ├── invoice_service.py                     (253)
    │   ├── invoice_write_service.py               (117)
    │   ├── je_reversal_service.py                 (83)
    │   ├── period_close_service.py                (262)
    │   ├── sub_ledger_controller.py               (139)
    │   └── sub_ledger_service.py                  (302)
    │
    ├── payments/                      (15 files)
    │   ├── base.py                                (75)  ← gateway base
    │   ├── base_models.py                         (33)  ← DTOs
    │   ├── disputes_controller.py                 (27)
    │   ├── disputes_service.py                    (321)
    │   ├── disputes_write_service.py              (151)
    │   ├── gateway_auto_enable.py                 (136)
    │   ├── gateway_reconciliation_service.py      (233)
    │   ├── payments.py                            (3820) ← MONOLITH
    │   ├── payments_write_service.py              (182)
    │   ├── payment_event_handlers.py              (120)
    │   ├── public_commerce_validation_service.py  (120)
    │   ├── registry.py                            (53)  ← gateway registry
    │   ├── webhook_models.py                      (46)
    │   └── webhook_processor.py                   (108)
    │
    ├── payouts/                       (17 files)
    │   ├── auto_payout_scheduler.py               (699)
    │   ├── badge_billing_payment.py               (169)
    │   ├── payments_gateway_service.py            (42)
    │   ├── payment_engine.py                      (170)
    │   ├── payment_orchestrator.py                (107)
    │   ├── payout_admin_service.py                (72)
    │   ├── payout_admin_write_service.py          (89)
    │   ├── payout_approval_controller.py          (51)
    │   ├── payout_approval_read_service.py        (192)
    │   ├── payout_approval_service.py             (159)
    │   ├── payout_approval_write_service.py       (283)
    │   ├── payout_batch_service.py                (244)
    │   ├── payout_dispatch_service.py             (81)
    │   ├── payout_engine.py                       (122)
    │   ├── payout_read_service.py                 (26)
    │   ├── payout_status_service.py               (86)
    │   └── refund_posting_service.py              (202)
    │
    ├── reporting/                     (9 files)
    │   ├── admin_reporting_service.py              (1058)
    │   ├── admin_treasury_read_service.py         (86)
    │   ├── admin_treasury_reporting_read_service.py (956)
    │   ├── admin_treasury_service.py              (1249)
    │   ├── admin_treasury_write_service.py        (324)
    │   ├── finance_dashboard_service.py           (198)
    │   ├── finance_read_service.py                (214)
    │   ├── financial_reporting.py                 (140)
    │   ├── financial_reports_service.py           (580)
    │   └── reporting_service.py                   (589)
    │
    ├── shared/                        (18 files)
    │   ├── ai_automation_service.py               (478)
    │   ├── ai_copy_jobs.py                        (70)
    │   ├── ai_research_jobs.py                    (78)
    │   ├── ai_search_service.py                   (165)
    │   ├── ai_service.py                          (950)
    │   ├── ai_upload_service.py                   (330)
    │   ├── ai_upload_write_service.py             (340)
    │   ├── ai_variant_config.py                   (1085)
    │   ├── automation_read_service.py             (104)
    │   ├── automation_scheduler.py                (481)
    │   ├── bg_removal_presets.py                  (525)
    │   ├── bg_removal_service.py                  (768)
    │   ├── downstream_wiring.py                   (153)
    │   ├── erp_finance_service.py                 (307)
    │   ├── erp_read_service.py                    (39)
    │   ├── finance_controller.py                  (27)
    │   ├── finance_package_service.py             (33)
    │   ├── import_service.py                      (603)
    │   ├── ocr_parser.py                          (148)
    │   ├── order_payment_functions.py             (25)
    │   └── parcel_verification_service.py         (43)
    │
    ├── tax/                           (2 files)
    │   ├── tax_service.py                         (90)
    │   └── vat_rates.py                           (55)
    │
    └── treasury/                      (12 files)
        ├── cash_flow_forecast_service.py           (117)
        ├── cash_management_controller.py           (63)
        ├── cash_management_controller_service.py   (862)
        ├── cash_management_service.py              (2310)
        ├── cash_management_write_controller.py     (164)
        ├── cash_management_write_service.py        (246)
        ├── cash_write_service.py                   (90)
        ├── treasurer.py                            (127)
        ├── treasury_adapter.py                     (109)
        ├── treasury_engine.py                      (373)
        ├── treasury_query_service.py               (379)
        ├── treasury_router_service.py              (80)
        └── treasury_service.py                     (318)
```

#### 7. `logistics/` — Logistics & Delivery
```
logistics/
├── sub-domains/
│   ├── shipping/          — Shipping tiers, rates, carriers
│   ├── fulfillment/       — Fulfillment centers, operations
│   ├── tracking/          — Live tracking, delivery status
│   ├── partners/          — Logistics partners, pricing
│   ├── geo/               — Geo-fencing, location services
│   └── sla/               — SLA monitoring, performance
├── features:
    ├── Shipping management
    ├── Fulfillment operations
    ├── Live delivery tracking
    ├── Partner management
    ├── Geo-fencing
    ├── SLA monitoring
    ├── Location management
    └── Logistics analytics
```

#### 8. `customers/` — Customer Relationship Management
```
customers/
├── sub-domains/
│   ├── profile/           — Customer profiles, health
│   ├── referrals/         — Referral program
│   ├── reviews/           — Product reviews
│   ├── wishlists/         — Wishlist management
│   └── coupons/           — Customer-specific coupons
├── features:
    ├── Customer profile management
    ├── Customer health monitoring
    ├── Referral program
    ├── Review management
    ├── Wishlist management
    └── Customer coupon assignment
```

#### 9. `comms/` — Communication & Messaging
```
comms/
├── sub-domains/
│   ├── messaging/         — Chat, real-time messaging
│   ├── email/             — Email campaigns, transactional
│   ├── notifications/     — Push notifications, alerts
│   ├── video/             — Video conferencing
│   ├── tickets/           — Support tickets
│   └── marketing/         — Marketing campaigns
├── features:
    ├── Real-time chat
    ├── Email management
    ├── Push notifications
    ├── Video conferencing
    ├── Ticket management
    ├── Marketing campaigns
    └── Communication audit
```

#### 10. `country/` — Localization & Geographic Operations
```
country/
├── sub-domains/
│   ├── localization/      — Translation, localization
│   ├── tax/               — Country-specific tax rules
│   ├── cross-border/      — Cross-border compliance
│   ├── geo/               — Geographic data, restrictions
│   ├── payouts/           — Country-specific payout rules
│   └── staff/             — Country staff management
├── features:
    ├── Localization/translation
    ├── Tax configuration
    ├── Cross-border compliance
    ├── Geographic restrictions
    ├── Payout configuration
    └── Staff management
```

#### 11. `governance/` — Platform Governance & Admin *(trimmed down)*
```
governance/
├── sub-domains/
│   ├── auth/              — Authorization, RBAC, permissions
│   ├── admin/             — Admin operations, settings
│   ├── risk/              — Risk scoring, management
│   ├── incident/          — Incident management
│   └── audit/             — Compliance, data residency
├── features:
    ├── RBAC & permissions
    ├── Admin dashboard
    ├── Risk management
    ├── Incident management
    ├── Compliance engine
    └── Settings management
```

#### 12. `hr/` — Human Resources
```
hr/
├── sub-domains/
│   ├── employees/         — Employee management, lifecycle
│   ├── attendance/        — Attendance tracking
│   ├── payroll/           — Payroll engine
│   ├── leave/             — Leave accrual, management
│   ├── performance/       — Performance reviews, OKRs
│   ├── learning/          — LMS, training
│   └── hierarchy/         — Org hierarchy, succession
├── features:
    ├── Employee management
    ├── Attendance tracking
    ├── Payroll processing
    ├── Leave management
    ├── Performance management
    ├── Learning management
    └── Org hierarchy
```

#### 13. `analytics/` — Business Analytics
```
analytics/
├── sub-domains/
│   ├── dashboards/        — Analytics dashboards
│   └── reporting/         — Report generation
├── features:
    ├── Dashboard analytics
    ├── Report generation
    └── Metrics aggregation
```

#### 14. `audit/` — Audit & Compliance
```
audit/
├── sub-domains/
│   └── logs/              — Audit logs, trails
├── features:
    ├── Audit logging
    ├── Compliance tracking
    └── Activity trails
```

#### 15. `security/` — Security Operations
```
security/
├── sub-domains/
│   ├── detection/         — Threat detection
│   ├── health/            — Security health monitoring
│   └── registration/      — Security registration
├── features:
    ├── Threat detection
    ├── Health monitoring
    └── Security registration
```

#### 16. `infrastructure/` — Platform Infrastructure
```
infrastructure/
├── sub-domains/
│   ├── workers/           — Async workers, background tasks
│   ├── storage/           — File storage management
│   └── tools/             — Shared tools, utilities
├── features:
    ├── Async task workers
    ├── Storage management
    └── Platform utilities
```

---

## 📋 Migration Summary

### New Domains to Create:
1. **`promotions/`** — Extract from `orders/`, `catalog/`, `governance/`, `_parked/`

### Domains to Depopulate (move out):
1. **`media/`** → Move to `providers/media/` (tools, not a domain)
2. **`governance/`** — Extract promotions, orders, logistics, catalog sub-domains to their proper domains
3. **`orders/`** — Move promotions, coupons, banners, flash-sales to `promotions/`
4. **`catalog/`** — Move promotions, coupons to `promotions/`
5. **`accounts/`** — Move supplier, logistics, HR services to their proper domains

### Domains to Absorb:
1. **`promotions/`** — Absorbs from `orders/`, `catalog/`, `governance/`, `_parked/`
2. **`suppliers/`** — Absorbs supplier-related services from `accounts/`, `orders/`
3. **`logistics/`** — Absorbs logistics services from `orders/`, `governance/`
4. **`finance/`** — Absorbs finance services from `accounts/`, `governance/`

---

## 🗺️ Visual Domain Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        ZOZI PLATFORM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐   ┌─────────┐           │
│  │ accounts│  │ catalog │  │promotions│   │ orders  │           │
│  └────┬────┘  └────┬────┘  └────┬─────┘   └────┬────┘           │
│       │            │            │              │                │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐    ┌────┴────┐           │
│  │suppliers│  │ finance │  │logistics│    │customers│           │
│  └────┬────┘  └────┬────┘  └────┬────┘    └────┬────┘           │
│       │            │            │              │                │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐    ┌────┴─────┐          │
│  │   comms │  │ country │  │   hr    │    │governance│          │
│  └─────────┘  └─────────┘  └─────────┘    └──────────┘          │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐        │
│  │analytics│  │  audit  │  │security │  │infrastructure│        │
│  └─────────┘  └─────────┘  └─────────┘  └──────────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     PROVIDERS (Tools)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌────────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│  │ ai  │ │image│ │payments│ │geo  │ │comms│ │auth │ │voice│     │
│  └─────┘ └─────┘ └────────┘ └─────┘ └─────┘ └─────┘ └─────┘     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                                │
│  │br_  │ │auto │ │secur│ │news │                                │
│  │remov│ │maton│ │ity  │ │     │                                │
│  └─────┘ └─────┘ └─────┘ └─────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔴 Key Actions Required

| Action | From | To | Priority |
|--------|------|-----|----------|
| Create `promotions/` domain | — | `domains/promotions/` | P0 |
| Move media tools to providers | `domains/media/` | `providers/media/` | P0 |
| Move coupon services | `orders/`, `catalog/` | `promotions/` | P0 |
| Move banner services | `orders/`, `catalog/` | `promotions/` | P0 |
| Move flash-sale services | `orders/`, `catalog/` | `promotions/` | P0 |
| Move Zozi coins services | `orders/`, `catalog/` | `promotions/` | P0 |
| Move referral services | `customers/`, `orders/` | `promotions/` | P0 |
| Move logistics services | `orders/`, `governance/` | `logistics/` | P1 |
| Move supplier services | `accounts/`, `orders/` | `suppliers/` | P1 |
| Move finance services | `accounts/`, `governance/` | `finance/` | P1 |
| Move _parked services | `_parked/` | respective domains | P1 |
| Move infrastructure tools | `domains/` root | `infrastructure/` | P2 |
| Trim governance | `governance/` | respective domains | P2 |

---

Want me to proceed with the reorganization? I can start by creating the `promotions/` domain structure and migrating files systematically.


You're raising a critical architectural question. Let me analyze the coupling problem:

## The Problem: Product ↔ Promotion Coupling

```
┌─────────────────────────────────────────────────────────┐
│                  CURRENT CONFUSION                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Product has:          Flash-Sale modifies:            │
│   • base_price          • product price temporarily     │
│   • category            • product availability          │
│   • variants            • product visibility            │
│                                                         │
│   Discount modifies:    Coupon modifies:                │
│   • product price       • cart/order total              │
│   • product visibility  • not product-specific          │
│                                                         │
│   So where do flash-sale and product discount live?     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Analysis by Coupling Type

| Feature | Product-Specific? | Cart/Order-Level? | Domain |
|---------|-------------------|-------------------|--------|
| **Flash Sale** | ✅ Yes (targets products) | ❌ No | catalog |
| **Product Discount** | ✅ Yes (supplier sets on product) | ❌ No | catalog |
| **Supplier Discount Placement** | ✅ Yes (supplier places on own product) | ❌ No | catalog/suppliers |
| **Coupon** | ❌ No | ✅ Yes (applied at checkout) | promotions |
| **Zozi Coins** | ❌ No | ✅ Yes (applied at checkout) | promotions |
| **Referral Coins** | ❌ No | ✅ Yes (applied at checkout) | promotions |
| **Banner** | ❌ No | ❌ No | promotions/marketing |
| **BOGO** | ✅ Can be either | ✅ Can be either | either |

---

## Two Valid Approaches

### Approach A: Split by Coupling (Recommended)

```
┌──────────────────────────────────────────────────────────────┐
│  catalog/                                                    │
│  ├── sub-domains/                                            │
│  │   ├── pricing/          ← Product-specific pricing        │
│  │   │   ├── flash-sales/  ← Time-limited price overrides    │
│  │   │   ├── discounts/    ← Product discount rules          │
│  │   │   └── supplier-discounts/  ← Supplier placed discounts│
│  │   ├── products/                                           │
│  │   ├── categories/                                         │
│  │   └── search/                                             │
│  │                                                           │
│  promotions/                                                 │
│  ├── sub-domains/                                            │
│  │   ├── coupons/          ← Cart/order-level coupons        │
│  │   ├── coins/            ← Zozi coins, referral coins      │
│  │   ├── banners/          ← Marketing banners               │
│  │   └── bogo/             ← Buy-one-get-one (cart-level)    │
│  │                                                           │
└──────────────────────────────────────────────────────────────┘
```

**Why this works:**
- Product-specific pricing stays with product
- Cart-level promotions stay separate
- No cross-domain coupling for product rendering

### Approach B: Event-Driven (More Complex, Scalable)

```
┌──────────────────────────────────────────────────────────────┐
│  catalog/                                                    │
│  ├── products/                                               │
│  ├── categories/                                             │
│  └── search/                                                 │
│         ▲                                                    │
│         │ subscribes to                                      │
│         │                                                    │
│  promotions/                                                 │
│  ├── flash-sales/     ──publishes──▶  ProductPriceChanged   │
│  ├── discounts/       ──publishes──▶  ProductDiscountSet    │
│  ├── coupons/                                                │
│  └── coins/                                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Why this works:**
- Promotions domain owns the promotion logic
- Catalog domain subscribes to price change events
- Each domain is independently deployable
- More complex but scales better

---

## Recommendation: Approach A (Split by Coupling)

For your current scale, Approach A is simpler and avoids unnecessary complexity:

```
catalog/
├── pricing/                    ← NEW: Product-specific pricing
│   ├── flash-sale-service.py
│   ├── discount-service.py
│   └── supplier-discount-service.py
├── products/
├── categories/
├── search/
└── variants/

promotions/                     ← Cart/order-level promotions only
├── coupons/
├── coins/
├── banners/
└── bogo/
```

**The rule is simple:**
- If it **directly modifies a product's price/visibility** → `catalog/pricing/`
- If it **modifies cart/order total at checkout** → `promotions/`

---

Does this approach work for your domain model? Want me to:
1. Proceed with Approach A and restructure accordingly?
2. Explore the event-driven Approach B?
3. Discuss a different split?