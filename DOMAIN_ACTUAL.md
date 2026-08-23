
> `accounts/services` folder 

```
accounts/services/
├── __init__.py
├── audit_service.py                   # Cross-cutting audit service
├── export_controller.py               # Export controller
├── export_service.py                  # Export service
├── addresses/
│   ├── addresses_service.py           # Address management
│   ├── commerce_read_service.py       # Address read operations
│   └── commerce_write_service.py      # Address write operations
├── auth/
│   ├── auth_service.py                # Authentication
│   ├── otp_service.py                 # OTP verification
│   ├── session_service.py             # Session management
│   └── social_service.py              # Social login
├── iam/
│   └── iam_service.py                 # Identity & Access Management
├── identity/
│   ├── identity_admin_service.py      # Admin identity management
│   ├── identity_service.py            # Identity operations
│   ├── public_identity_operations_service.py
│   └── users_identity_admin_service.py
├── permissions/
│   ├── permissions_service.py         # Permission management
│   ├── public_permissions_validation_service.py
│   └── rbac_service.py                # Role-based access control
└── users/
    ├── approval_matrix_service.py     # Approval workflows
    ├── users_approval_matrix_service.py
    ├── users_service.py               # User management
    ├── users_write_service.py         # User write operations
    ├── user_read_service.py           # User read operations
    └── user_write_ops.py              # User write helpers
```

------------------------------------------------------------------------------------
> `catalog/services` folder

```
catalog/services/
├── categories/
│   └── category_service.py            # 299 lines: category CRUD + tree management
├── pricing/
│   ├── flash_sale_controller_service.py  # 163 lines: flash sale CRUD + caching
│   └── product_discount_service.py    # 110 lines: product discount pricing
├── products/
│   ├── products_service.py            # 1132+ lines: main product CRUD (merged)
│   ├── product_moderation_service.py  # 119 lines: country-level moderation
│   ├── product_verification_service.py # 216 lines: supply chain verification
│   └── bulk_ops_write_service.py      # 44 lines: bulk archive/restore/category-change
├── search/
│   ├── search_service.py              # 832 lines: natural-language search
│   ├── visual_search_service.py       # 56 lines: visual similarity search
│   ├── advanced_filter_service.py     # 339 lines: advanced filtering
│   └── advanced_search_engine.py      # 432 lines: search engine with fuzzy matching
└── variants/
    └── variant_config_service.py      # 176 lines: variant axis configuration
```    

------------------------------------------------------------------------------------
> `orders/services` folder

```
orders/services/
├── __init__.py
├── order_dtos.py                      # DTOs (shared within orders domain)
├── cart/
│   ├── __init__.py
│   ├── cart_service.py                # Cart operations + variant resolution
│   └── cart_write_service.py          # Cart DB writes
├── checkout/
│   └── __init__.py
├── disputes/
│   ├── __init__.py
│   └── disputes_service.py            # Disputes + notification prefs
├── order/
│   ├── __init__.py
│   ├── orders_service.py              # Main order service (create, retrieve, cancel)
│   └── write_service.py               # Write facade + ORM row writers
├── returns/
│   ├── __init__.py
│   └── returns_service.py             # Returns + refunds + notifications
└── tracking/
    ├── __init__.py
    └── order_tracking_service.py      # Lifecycle + QR codes
```    

------------------------------------------------------------------------------------
> `customers/services` folder

```
customers/services/
├── customer_health_engine.py          # Customer health score calculation
├── customer_health_list_service.py    # Customer health list
├── customer_health_service.py         # Customer health service
├── referrals/
│   ├── referrals_controller.py       # Referral controller
│   ├── referrals_controller__routers.py
│   └── referrals_service.py          # Referral operations
├── reviews/
│   ├── reviews_controller.py         # Review controller
│   ├── reviews_controller__routers.py
│   └── reviews_service.py            # Review persistence
└── wishlist/
    ├── wishlist_controller.py        # Wishlist controller
    ├── wishlist_controller__routers.py
    ├── wishlist_read_service.py      # Wishlist reads
    ├── wishlist_service.py           # Wishlist operations
    └── wishlist_write_service.py     # Wishlist writes
```

------------------------------------------------------------------------------------
> `finance/services` folder

```
finance/services/
├── finance.py                         # Lazy re-export delegator
├── cash_management/
│   └── cash_management_service.py
├── commission/                        # Commission operations
│   ├── commission_admin_write_service.py
│   ├── commission_controller.py
│   ├── commission_engine.py
│   ├── commission_geography_service.py
│   ├── commission_service.py
│   └── commission_write_service.py
├── ledger/                            # General ledger
│   ├── accounting_controller.py
│   ├── bank_transaction_service.py
│   ├── general_ledger_service.py
│   ├── invoice_service.py
│   └── ... (18 files total)
├── payments/                          # Payment processing
│   ├── payments.py
│   ├── payment_engine.py
│   ├── gateway_reconciliation_service.py
│   └── ... (20 files total)
├── payouts/                           # Payout operations
│   ├── payout_engine.py
│   ├── payout_batch_service.py
│   ├── payout_dispatch_service.py
│   └── ... (20 files total)
├── reporting/                         # Financial reporting
│   ├── financial_reporting.py
│   ├── finance_dashboard_service.py
│   └── ... (10 files total)
├── tax/                               # Tax operations
│   ├── tax_service.py
│   └── vat_rates.py
└── treasury/                          # Treasury operations
    ├── treasury_service.py
    ├── treasury_engine.py
    ├── cash_management_service.py
    └── ... (22 files total)
```

------------------------------------------------------------------------------------
> `logistics/services` folder

```
logistics/services/
├── fulfillment/
│   └── fulfillment_service.py          # Order fulfillment after payment
├── geo/
│   ├── api_geography_location_service.py  # In-app location API
│   ├── geo_fence_service.py            # Geo-fencing validation
│   ├── location_service.py             # Location write operations
│   ├── logistics_locations_create_service.py
│   ├── logistics_locations_service.py
│   └── map_service.py
├── health/
│   ├── logistics_analytics_service.py  # Analytics aggregation
│   ├── logistics_health_engine.py      # Health scoring
│   ├── logistics_health_list_service.py
│   ├── logistics_health_service.py
│   └── logistics_logistics_status_service.py
├── operations/
│   ├── live_tracking_service.py        # Live GPS tracking
│   ├── logistics_admin_operations_service.py
│   ├── logistics_controller.py
│   ├── logistics_engine.py
│   ├── logistics_sla_service.py
│   └── logistics_write_service.py
├── partners/
│   ├── logistics_partner_admin_write_service.py
│   ├── logistics_partner_controller.py
│   ├── logistics_partner_controller__routers.py
│   ├── logistics_partner_geography_service.py
│   ├── logistics_partner_service.py
│   └── logistics_partner_service__router_migration.py
└── shipments/
    ├── shipments_service.py            # Shipment operations
    └── shipping_tier.py                # Shipping tier resolution
```

------------------------------------------------------------------------------------
> `suppliers/services` folder

```
suppliers/services/
├── supplier_service.py (4714 lines - main controller)
├── analytics/
│   └── analytics_service.py
├── badges/
│   ├── badge_service.py
│   ├── badge_write_service.py
│   └── billing_payment.py
├── common/
│   ├── batch_write_service.py
│   └── controller.py
├── contracts/
│   └── legal_contract_service.py
├── documents/
│   ├── document_controller_service.py
│   ├── document_service.py
│   └── supplier_documents_service.py
├── finance/
│   ├── bank_account_service.py
│   └── finance_service.py
├── health/
│   ├── health_engine.py
│   ├── health_service.py
│   └── supplier_health_controller.py
├── onboarding/
│   ├── nonboarding_service.py
│   └── pipeline.py
├── orders/
│   ├── order_service.py
│   ├── orders_service.py
│   └── orders_verify_service.py
├── products/
│   ├── coordinator_service.py
│   ├── products_upload_service.py
│   └── supplier_products_service.py
└── profile/
    ├── profile_create_service.py
    ├── profile_write_service.py
    └── supplier_profile_service.py
```

------------------------------------------------------------------------------------
> `comms/services` folder

```
comms/services/
├── autobot/
│   ├── chatbot_controller.py
│   ├── chatbot_controller__routers.py
│   └── chatbot_service.py
├── channel/
│   └── internal_comms_channels_service.py
├── email/
│   ├── admin_email_service.py
│   └── email_service.py
├── marketing/
│   ├── campaign_geography_service.py
│   ├── email_enrichment.py
│   ├── email_event_service.py
│   ├── email_gateway.py
│   ├── email_management_service.py
│   ├── email_reputation.py
│   ├── email_write_service.py
│   ├── transactional_email.py
│   ├── transactional_email_service.py
│   └── whatsapp_service.py
├── messaging/
│   ├── admin_comms_messaging_service.py
│   ├── chat_enrichment_service.py
│   ├── flat_admin_comms_messaging_service.py
│   └── chat/ (12 files)
├── tickets/
│   └── tickets_controller.py
└── (root level files remain to be organized)
```

------------------------------------------------------------------------------------
> `country/services` folder

```
country/services/
├── core/ (8 files)
│   ├── countries_service.py
│   ├── country_config_admin_service.py
│   ├── country_config_write_service.py
│   ├── country_context_service.py
│   ├── country_controller.py
│   ├── country_read_service.py
│   ├── country_service.py (1734 lines - main service)
│   └── country_write_service.py
├── cross_border/ (4 files)
│   ├── cross_border_base.py
│   ├── cross_border_detection.py
│   ├── cross_border_service.py
│   └── cross_border_tracker.py
├── geo/ (2 files)
│   ├── country_dropdown_service.py
│   └── country_maps_service.py
├── localization/ (3 files)
│   ├── localization_service.py
│   ├── translate_controller.py
│   └── translation_service.py
├── payout/ (2 files)
│   ├── country_payouts_service.py
│   └── country_payout_write_service.py
├── research/ (8 files)
│   ├── country_ai_research.py
│   ├── country_auto_populate.py
│   ├── country_auto_populate_write_service.py
│   ├── country_curated.py
│   ├── country_data_orchestrator.py
│   ├── country_heuristic_engine.py
│   ├── country_research.py
│   └── curated_cities.py
├── restriction/ (1 file)
│   └── country_restriction_service.py
├── staff/ (4 files)
│   ├── country_admin_service.py
│   ├── country_admin_write_service.py
│   ├── country_staff_service.py
│   └── country_staff_write_service.py
├── tax/ (2 files)
│   ├── category_tax_profiles.py
│   └── country_tax_service.py
└── versioning/ (2 files)
    ├── country_versioning_controller.py
    └── country_versioning_service.py
```


------------------------------------------------------------------------------------
> `hr/services` folder

```
hr/services/
├── analytics/ (2 files)
├── communication/ (1 file)
├── compliance/ (6 files)
├── core/ (3 files)
├── employee/ (9 files)
├── ess/ (2 files)
├── ghost_watchdog/ (1 file)
├── hierarchy/ (5 files)
├── learning/ (7 files)
├── payroll/ (4 files)
├── performance/ (3 files)
├── shared/ (1 file)
├── shift/ (3 files)
├── succession/ (2 files)
└── travel/ (2 files)
```
