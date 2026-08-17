# File Shift Plan - controllers / services / modules to new structure

> **STATUS: RECONCILED & RE-DERIVED (2026-08-17).** Router mapping (Section 0) now reflects the REAL
> source `backend/routers/` (330 files). No files were relocated during reconciliation - only 79 byte-identical
> duplicate copies were removed from the untracked `backend/modules/admin/routers/`. Execution (relocation +
> `main.py` rewiring) is pending re-approval.

## 0. Router actor-mapping (how the REAL `backend/routers/*` is split)

> **REALITY CHECK (2026-08-17, post-reconciliation).** The previously approved draft assumed a flat
> `backend/modules/routers/` (396 files). That path **does not exist**. Verified ground truth:
> - **Authoritative source = `backend/routers/` = 330 files, git-tracked**, loaded by `main.py:_load_routers()`
>   via `import_module("routers.{modname}")`.
> - `backend/modules/` is **100% untracked** (0 git-tracked files) - a scratch tree from a prior failed
>   transfer. `backend/modules/admin/routers/` held 527 files: 79 byte-identical copies of the flat routers
>   (deleted during reconciliation), 248 content-divergent copies, and 200 admin-only files. All kept for review.
> - `main.py:170` imports `modules.routers.public_comms_status` - a **non-existent** path - so the app currently
>   **fails to import/boot**. This must be fixed (point it at `routers.public_comms_status`) before any execution
>   can be verified. It is independent of the re-home and is a prerequisite, not part of it.
> - `backend/controllers/` referenced by the old Sections 1+ **no longer exists**; its `*_controller.py` files now
>   live inside `backend/modules/*/routers/` (untracked). Those sections are STALE and will be re-derived in the
>   NEW_STRUCTURE router-phase, not here.

`NEW_STRUCTURE.md` section 3 requires the flat `routers/` to be **split per actor** into
`modules/{customer,supplier,logistics,admin,employee}/routers/`. This plan classifies each router by
**filename ownership token** (the original authors already named routers by actor), with content-derived sub-rules.

**Classification (the "crack")**
1. **Filename leading token -> actor** (authors' intent): `customer_*`->customer, `supplier_*`->supplier,
   `logistics_*`->logistics, `employee_*`/`ess_*`/`hr_*`->employee, `admin_*`->admin.
2. **Shared / reference -> `admin`, tagged `public`.** `public_*`, `core_*`, and reference master-data
   (`country_*`, `countries_*`, currency, language, category, categories, tax, unit, region, brand, attribute, geo,
   location, shop, api...) live in `modules/admin/routers/` but are mounted **read-only under every module** via the
   `public_router` convention, so they "apply to all modules". Not a separate actor bucket.
3. **Back-office -> `employee`.** `finance_*`, `accounting_*`, `treasury_*`, `payroll_*`, `employees_*`, `cash_management`,
   `commission`, `expenses`, `invoices`, `hr`, `performance`, `okr`, `succession`, `trading`, `chat`/`comms`/`notifications`
   are internal finance / workforce surfaces (rule: finance & employees belong to the employee module).
4. **Domain routers -> owner.** `products_*`/`catalog_*`/`inventory_*`->supplier; `shipment_*`/`carrier_*`/`tracking_*`/
   `parcel_*`->logistics; `cart_*`/`coupon_*`/`review_*`/`checkout_*`/`wishlist_*`/`addresses`/`payments`/`returns`->customer.
5. **Manual review** for `store_*` / `search_*` (cross-cutting merchant storefront - assign per endpoint). Defaulted to
   `admin` pending review.

| Actor | Routers (token-based, of 330 real files) |
|---|---|
| admin (incl. shared-public) | 226 |
| employee | 49 |
| supplier | 28 |
| customer | 14 |
| logistics | 12 |
| **manual review** | 10 (`store_*`, `search_*`) |

> `auto_router.py` / `AUTO_ROUTER.md` (the generator) stay in `routers/generated/`; the generator is later retargeted
> to emit per-module (see `NEW_STRUCTURE.md` section 3).

### 0.1 Full mapping (330 routers)

| sno | source | target (modules/{actor}/routers) |
|---|---|---
| 1 | `backend/routers/accounting.py` | `backend/modules/employee/routers/accounting.py` |
| 2 | `backend/routers/addresses.py` | `backend/modules/customer/routers/addresses.py` |
| 3 | `backend/routers/admin.py` | `backend/modules/admin/routers/admin.py` |
| 4 | `backend/routers/admin_admin_analytics.py` | `backend/modules/admin/routers/admin_admin_analytics.py` |
| 5 | `backend/routers/admin_admin_audit.py` | `backend/modules/admin/routers/admin_admin_audit.py` |
| 6 | `backend/routers/admin_admin_bank_accounts.py` | `backend/modules/admin/routers/admin_admin_bank_accounts.py` |
| 7 | `backend/routers/admin_admin_coupons.py` | `backend/modules/admin/routers/admin_admin_coupons.py` |
| 8 | `backend/routers/admin_admin_misc.py` | `backend/modules/admin/routers/admin_admin_misc.py` |
| 9 | `backend/routers/admin_admin_orders.py` | `backend/modules/admin/routers/admin_admin_orders.py` |
| 10 | `backend/routers/admin_admin_payouts.py` | `backend/modules/admin/routers/admin_admin_payouts.py` |
| 11 | `backend/routers/admin_admin_permissions.py` | `backend/modules/admin/routers/admin_admin_permissions.py` |
| 12 | `backend/routers/admin_admin_products.py` | `backend/modules/admin/routers/admin_admin_products.py` |
| 13 | `backend/routers/admin_admin_suppliers.py` | `backend/modules/admin/routers/admin_admin_suppliers.py` |
| 14 | `backend/routers/admin_admin_tickets.py` | `backend/modules/admin/routers/admin_admin_tickets.py` |
| 15 | `backend/routers/admin_admin_users_admin.py` | `backend/modules/admin/routers/admin_admin_users_admin.py` |
| 16 | `backend/routers/admin_analytics_fallback_dashboard.py` | `backend/modules/admin/routers/admin_analytics_fallback_dashboard.py` |
| 17 | `backend/routers/admin_analytics_routes.py` | `backend/modules/admin/routers/admin_analytics_routes.py` |
| 18 | `backend/routers/admin_banners.py` | `backend/modules/admin/routers/admin_banners.py` |
| 19 | `backend/routers/admin_banners_routes.py` | `backend/modules/admin/routers/admin_banners_routes.py` |
| 20 | `backend/routers/admin_cash.py` | `backend/modules/admin/routers/admin_cash.py` |
| 21 | `backend/routers/admin_cash_routes.py` | `backend/modules/admin/routers/admin_cash_routes.py` |
| 22 | `backend/routers/admin_catalog_category_admin.py` | `backend/modules/admin/routers/admin_catalog_category_admin.py` |
| 23 | `backend/routers/admin_catalog_operations.py` | `backend/modules/admin/routers/admin_catalog_operations.py` |
| 24 | `backend/routers/admin_catalog_orders.py` | `backend/modules/admin/routers/admin_catalog_orders.py` |
| 25 | `backend/routers/admin_categories.py` | `backend/modules/admin/routers/admin_categories.py` |
| 26 | `backend/routers/admin_categories_routes.py` | `backend/modules/admin/routers/admin_categories_routes.py` |
| 27 | `backend/routers/admin_chat.py` | `backend/modules/admin/routers/admin_chat.py` |
| 28 | `backend/routers/admin_chat_routes.py` | `backend/modules/admin/routers/admin_chat_routes.py` |
| 29 | `backend/routers/admin_commerce_configuration.py` | `backend/modules/admin/routers/admin_commerce_configuration.py` |
| 30 | `backend/routers/admin_commerce_geography.py` | `backend/modules/admin/routers/admin_commerce_geography.py` |
| 31 | `backend/routers/admin_commerce_promotion_admin.py` | `backend/modules/admin/routers/admin_commerce_promotion_admin.py` |
| 32 | `backend/routers/admin_commission.py` | `backend/modules/admin/routers/admin_commission.py` |
| 33 | `backend/routers/admin_commission_routes.py` | `backend/modules/admin/routers/admin_commission_routes.py` |
| 34 | `backend/routers/admin_comms_geography.py` | `backend/modules/admin/routers/admin_comms_geography.py` |
| 35 | `backend/routers/admin_comms_messaging.py` | `backend/modules/admin/routers/admin_comms_messaging.py` |
| 36 | `backend/routers/admin_comms_unified.py` | `backend/modules/admin/routers/admin_comms_unified.py` |
| 37 | `backend/routers/admin_configuration_operations.py` | `backend/modules/admin/routers/admin_configuration_operations.py` |
| 38 | `backend/routers/admin_core_routes.py` | `backend/modules/admin/routers/admin_core_routes.py` |
| 39 | `backend/routers/admin_email.py` | `backend/modules/admin/routers/admin_email.py` |
| 40 | `backend/routers/admin_email_routes.py` | `backend/modules/admin/routers/admin_email_routes.py` |
| 41 | `backend/routers/admin_fallback.py` | `backend/modules/admin/routers/admin_fallback.py` |
| 42 | `backend/routers/admin_fallback_routes.py` | `backend/modules/admin/routers/admin_fallback_routes.py` |
| 43 | `backend/routers/admin_finance_accounting.py` | `backend/modules/admin/routers/admin_finance_accounting.py` |
| 44 | `backend/routers/admin_finance_creation.py` | `backend/modules/admin/routers/admin_finance_creation.py` |
| 45 | `backend/routers/admin_finance_geography.py` | `backend/modules/admin/routers/admin_finance_geography.py` |
| 46 | `backend/routers/admin_finance_sub_ledger.py` | `backend/modules/admin/routers/admin_finance_sub_ledger.py` |
| 47 | `backend/routers/admin_geography_audit.py` | `backend/modules/admin/routers/admin_geography_audit.py` |
| 48 | `backend/routers/admin_geography_configuration.py` | `backend/modules/admin/routers/admin_geography_configuration.py` |
| 49 | `backend/routers/admin_geography_country_versioning.py` | `backend/modules/admin/routers/admin_geography_country_versioning.py` |
| 50 | `backend/routers/admin_governance_command_center.py` | `backend/modules/admin/routers/admin_governance_command_center.py` |
| 51 | `backend/routers/admin_identity_operations.py` | `backend/modules/admin/routers/admin_identity_operations.py` |
| 52 | `backend/routers/admin_identity_operations_api.py` | `backend/modules/admin/routers/admin_identity_operations_api.py` |
| 53 | `backend/routers/admin_logistics.py` | `backend/modules/admin/routers/admin_logistics.py` |
| 54 | `backend/routers/admin_logistics_fallback.py` | `backend/modules/admin/routers/admin_logistics_fallback.py` |
| 55 | `backend/routers/admin_logistics_geography.py` | `backend/modules/admin/routers/admin_logistics_geography.py` |
| 56 | `backend/routers/admin_logistics_imports.py` | `backend/modules/admin/routers/admin_logistics_imports.py` |
| 57 | `backend/routers/admin_logistics_operations.py` | `backend/modules/admin/routers/admin_logistics_operations.py` |
| 58 | `backend/routers/admin_logistics_routes.py` | `backend/modules/admin/routers/admin_logistics_routes.py` |
| 59 | `backend/routers/admin_media_geography.py` | `backend/modules/admin/routers/admin_media_geography.py` |
| 60 | `backend/routers/admin_orders.py` | `backend/modules/admin/routers/admin_orders.py` |
| 61 | `backend/routers/admin_orders_routes.py` | `backend/modules/admin/routers/admin_orders_routes.py` |
| 62 | `backend/routers/admin_orders_status.py` | `backend/modules/admin/routers/admin_orders_status.py` |
| 63 | `backend/routers/admin_payouts.py` | `backend/modules/admin/routers/admin_payouts.py` |
| 64 | `backend/routers/admin_payouts_routes.py` | `backend/modules/admin/routers/admin_payouts_routes.py` |
| 65 | `backend/routers/admin_permissions_validation.py` | `backend/modules/admin/routers/admin_permissions_validation.py` |
| 66 | `backend/routers/admin_products.py` | `backend/modules/admin/routers/admin_products.py` |
| 67 | `backend/routers/admin_products_routes.py` | `backend/modules/admin/routers/admin_products_routes.py` |
| 68 | `backend/routers/admin_promotions.py` | `backend/modules/admin/routers/admin_promotions.py` |
| 69 | `backend/routers/admin_promotions_routes.py` | `backend/modules/admin/routers/admin_promotions_routes.py` |
| 70 | `backend/routers/admin_security_detection.py` | `backend/modules/admin/routers/admin_security_detection.py` |
| 71 | `backend/routers/admin_security_health.py` | `backend/modules/admin/routers/admin_security_health.py` |
| 72 | `backend/routers/admin_security_operations.py` | `backend/modules/admin/routers/admin_security_operations.py` |
| 73 | `backend/routers/admin_security_registration.py` | `backend/modules/admin/routers/admin_security_registration.py` |
| 74 | `backend/routers/admin_settings.py` | `backend/modules/admin/routers/admin_settings.py` |
| 75 | `backend/routers/admin_settings_routes.py` | `backend/modules/admin/routers/admin_settings_routes.py` |
| 76 | `backend/routers/admin_supplier_reviews.py` | `backend/modules/admin/routers/admin_supplier_reviews.py` |
| 77 | `backend/routers/admin_supplier_trading.py` | `backend/modules/admin/routers/admin_supplier_trading.py` |
| 78 | `backend/routers/admin_suppliers.py` | `backend/modules/admin/routers/admin_suppliers.py` |
| 79 | `backend/routers/admin_suppliers_routes.py` | `backend/modules/admin/routers/admin_suppliers_routes.py` |
| 80 | `backend/routers/admin_treasury.py` | `backend/modules/admin/routers/admin_treasury.py` |
| 81 | `backend/routers/admin_treasury_cash_management_write.py` | `backend/modules/admin/routers/admin_treasury_cash_management_write.py` |
| 82 | `backend/routers/admin_treasury_cash_position.py` | `backend/modules/admin/routers/admin_treasury_cash_position.py` |
| 83 | `backend/routers/admin_treasury_identity.py` | `backend/modules/admin/routers/admin_treasury_identity.py` |
| 84 | `backend/routers/admin_treasury_payments.py` | `backend/modules/admin/routers/admin_treasury_payments.py` |
| 85 | `backend/routers/admin_treasury_payout_approval.py` | `backend/modules/admin/routers/admin_treasury_payout_approval.py` |
| 86 | `backend/routers/admin_treasury_reporting.py` | `backend/modules/admin/routers/admin_treasury_reporting.py` |
| 87 | `backend/routers/admin_treasury_routes.py` | `backend/modules/admin/routers/admin_treasury_routes.py` |
| 88 | `backend/routers/admin_treasury_status.py` | `backend/modules/admin/routers/admin_treasury_status.py` |
| 89 | `backend/routers/admin_users.py` | `backend/modules/admin/routers/admin_users.py` |
| 90 | `backend/routers/admin_users_routes.py` | `backend/modules/admin/routers/admin_users_routes.py` |
| 91 | `backend/routers/admin_video.py` | `backend/modules/admin/routers/admin_video.py` |
| 92 | `backend/routers/admin_video_routes.py` | `backend/modules/admin/routers/admin_video_routes.py` |
| 93 | `backend/routers/ai.py` | `backend/modules/admin/routers/ai.py` |
| 94 | `backend/routers/ai_image.py` | `backend/modules/admin/routers/ai_image.py` |
| 95 | `backend/routers/ai_research.py` | `backend/modules/admin/routers/ai_research.py` |
| 96 | `backend/routers/ai_upload.py` | `backend/modules/admin/routers/ai_upload.py` |
| 97 | `backend/routers/api_geography_location.py` | `backend/modules/admin/routers/api_geography_location.py` |
| 98 | `backend/routers/audit.py` | `backend/modules/admin/routers/audit.py` |
| 99 | `backend/routers/auth.py` | `backend/modules/admin/routers/auth.py` |
| 100 | `backend/routers/automation.py` | `backend/modules/admin/routers/automation.py` |
| 101 | `backend/routers/banners.py` | `backend/modules/admin/routers/banners.py` |
| 102 | `backend/routers/batch_upload.py` | `backend/modules/admin/routers/batch_upload.py` |
| 103 | `backend/routers/cart.py` | `backend/modules/customer/routers/cart.py` |
| 104 | `backend/routers/cash_management.py` | `backend/modules/employee/routers/cash_management.py` |
| 105 | `backend/routers/categories.py` | `backend/modules/admin/routers/categories.py` |
| 106 | `backend/routers/chat.py` | `backend/modules/employee/routers/chat.py` |
| 107 | `backend/routers/chat_api.py` | `backend/modules/employee/routers/chat_api.py` |
| 108 | `backend/routers/chat_enrichment.py` | `backend/modules/employee/routers/chat_enrichment.py` |
| 109 | `backend/routers/chatbot.py` | `backend/modules/employee/routers/chatbot.py` |
| 110 | `backend/routers/comm.py` | `backend/modules/employee/routers/comm.py` |
| 111 | `backend/routers/command_center.py` | `backend/modules/admin/routers/command_center.py` |
| 112 | `backend/routers/command_center_api.py` | `backend/modules/admin/routers/command_center_api.py` |
| 113 | `backend/routers/command_center_controller.py` | `backend/modules/admin/routers/command_center_controller.py` |
| 114 | `backend/routers/commission.py` | `backend/modules/supplier/routers/commission.py` |
| 115 | `backend/routers/comms_chat.py` | `backend/modules/employee/routers/comms_chat.py` |
| 116 | `backend/routers/comms_unified.py` | `backend/modules/employee/routers/comms_unified.py` |
| 117 | `backend/routers/comms_video.py` | `backend/modules/employee/routers/comms_video.py` |
| 118 | `backend/routers/compliance.py` | `backend/modules/admin/routers/compliance.py` |
| 119 | `backend/routers/contact.py` | `backend/modules/admin/routers/contact.py` |
| 120 | `backend/routers/core_accounting_routes.py` | `backend/modules/admin/routers/core_accounting_routes.py` |
| 121 | `backend/routers/core_addresses_routes.py` | `backend/modules/admin/routers/core_addresses_routes.py` |
| 122 | `backend/routers/core_ai_routes.py` | `backend/modules/admin/routers/core_ai_routes.py` |
| 123 | `backend/routers/core_auth_routes.py` | `backend/modules/admin/routers/core_auth_routes.py` |
| 124 | `backend/routers/core_automation_routes.py` | `backend/modules/admin/routers/core_automation_routes.py` |
| 125 | `backend/routers/core_chatbot_routes.py` | `backend/modules/admin/routers/core_chatbot_routes.py` |
| 126 | `backend/routers/core_comm_routes.py` | `backend/modules/admin/routers/core_comm_routes.py` |
| 127 | `backend/routers/core_commission_routes.py` | `backend/modules/admin/routers/core_commission_routes.py` |
| 128 | `backend/routers/core_compliance_routes.py` | `backend/modules/admin/routers/core_compliance_routes.py` |
| 129 | `backend/routers/core_countries_routes.py` | `backend/modules/admin/routers/core_countries_routes.py` |
| 130 | `backend/routers/core_ediscovery_routes.py` | `backend/modules/admin/routers/core_ediscovery_routes.py` |
| 131 | `backend/routers/core_email_routes.py` | `backend/modules/admin/routers/core_email_routes.py` |
| 132 | `backend/routers/core_ess_routes.py` | `backend/modules/admin/routers/core_ess_routes.py` |
| 133 | `backend/routers/core_export_routes.py` | `backend/modules/admin/routers/core_export_routes.py` |
| 134 | `backend/routers/core_hierarchy_routes.py` | `backend/modules/admin/routers/core_hierarchy_routes.py` |
| 135 | `backend/routers/core_iam_routes.py` | `backend/modules/admin/routers/core_iam_routes.py` |
| 136 | `backend/routers/core_imports_routes.py` | `backend/modules/admin/routers/core_imports_routes.py` |
| 137 | `backend/routers/core_incident_routes.py` | `backend/modules/admin/routers/core_incident_routes.py` |
| 138 | `backend/routers/core_invoices_routes.py` | `backend/modules/admin/routers/core_invoices_routes.py` |
| 139 | `backend/routers/core_jobs_routes.py` | `backend/modules/admin/routers/core_jobs_routes.py` |
| 140 | `backend/routers/core_lms_routes.py` | `backend/modules/admin/routers/core_lms_routes.py` |
| 141 | `backend/routers/core_messaging_routes.py` | `backend/modules/admin/routers/core_messaging_routes.py` |
| 142 | `backend/routers/core_okr_routes.py` | `backend/modules/admin/routers/core_okr_routes.py` |
| 143 | `backend/routers/core_onboarding_routes.py` | `backend/modules/admin/routers/core_onboarding_routes.py` |
| 144 | `backend/routers/core_payroll_routes.py` | `backend/modules/admin/routers/core_payroll_routes.py` |
| 145 | `backend/routers/core_performance_routes.py` | `backend/modules/admin/routers/core_performance_routes.py` |
| 146 | `backend/routers/core_permissions_routes.py` | `backend/modules/admin/routers/core_permissions_routes.py` |
| 147 | `backend/routers/core_risk_routes.py` | `backend/modules/admin/routers/core_risk_routes.py` |
| 148 | `backend/routers/core_succession_routes.py` | `backend/modules/admin/routers/core_succession_routes.py` |
| 149 | `backend/routers/core_tickets_routes.py` | `backend/modules/admin/routers/core_tickets_routes.py` |
| 150 | `backend/routers/core_trading_routes.py` | `backend/modules/admin/routers/core_trading_routes.py` |
| 151 | `backend/routers/core_travel_routes.py` | `backend/modules/admin/routers/core_travel_routes.py` |
| 152 | `backend/routers/core_treasury_routes.py` | `backend/modules/admin/routers/core_treasury_routes.py` |
| 153 | `backend/routers/core_upload_routes.py` | `backend/modules/admin/routers/core_upload_routes.py` |
| 154 | `backend/routers/core_users_routes.py` | `backend/modules/admin/routers/core_users_routes.py` |
| 155 | `backend/routers/core_video_routes.py` | `backend/modules/admin/routers/core_video_routes.py` |
| 156 | `backend/routers/core_workflows_routes.py` | `backend/modules/admin/routers/core_workflows_routes.py` |
| 157 | `backend/routers/countries.py` | `backend/modules/admin/routers/countries.py` |
| 158 | `backend/routers/country_admin.py` | `backend/modules/admin/routers/country_admin.py` |
| 159 | `backend/routers/country_admin_routes.py` | `backend/modules/admin/routers/country_admin_routes.py` |
| 160 | `backend/routers/country_auto_populate.py` | `backend/modules/admin/routers/country_auto_populate.py` |
| 161 | `backend/routers/country_communications.py` | `backend/modules/admin/routers/country_communications.py` |
| 162 | `backend/routers/country_dropdown.py` | `backend/modules/admin/routers/country_dropdown.py` |
| 163 | `backend/routers/country_maps.py` | `backend/modules/admin/routers/country_maps.py` |
| 164 | `backend/routers/country_payouts.py` | `backend/modules/admin/routers/country_payouts.py` |
| 165 | `backend/routers/country_payouts_routes.py` | `backend/modules/admin/routers/country_payouts_routes.py` |
| 166 | `backend/routers/country_research.py` | `backend/modules/admin/routers/country_research.py` |
| 167 | `backend/routers/country_staff.py` | `backend/modules/admin/routers/country_staff.py` |
| 168 | `backend/routers/country_staff_routes.py` | `backend/modules/admin/routers/country_staff_routes.py` |
| 169 | `backend/routers/country_versioning.py` | `backend/modules/admin/routers/country_versioning.py` |
| 170 | `backend/routers/coupons.py` | `backend/modules/customer/routers/coupons.py` |
| 171 | `backend/routers/cross_border.py` | `backend/modules/admin/routers/cross_border.py` |
| 172 | `backend/routers/csp_reporting.py` | `backend/modules/admin/routers/csp_reporting.py` |
| 173 | `backend/routers/currency.py` | `backend/modules/admin/routers/currency.py` |
| 174 | `backend/routers/customer_coupons_create.py` | `backend/modules/customer/routers/customer_coupons_create.py` |
| 175 | `backend/routers/customer_coupons_mgmt.py` | `backend/modules/customer/routers/customer_coupons_mgmt.py` |
| 176 | `backend/routers/customer_health.py` | `backend/modules/customer/routers/customer_health.py` |
| 177 | `backend/routers/customer_health_list.py` | `backend/modules/customer/routers/customer_health_list.py` |
| 178 | `backend/routers/customer_orders.py` | `backend/modules/customer/routers/customer_orders.py` |
| 179 | `backend/routers/ediscovery.py` | `backend/modules/admin/routers/ediscovery.py` |
| 180 | `backend/routers/email.py` | `backend/modules/employee/routers/email.py` |
| 181 | `backend/routers/email_controller.py` | `backend/modules/employee/routers/email_controller.py` |
| 182 | `backend/routers/email_enrichment.py` | `backend/modules/employee/routers/email_enrichment.py` |
| 183 | `backend/routers/employees.py` | `backend/modules/employee/routers/employees.py` |
| 184 | `backend/routers/entity_chat.py` | `backend/modules/employee/routers/entity_chat.py` |
| 185 | `backend/routers/entity_communication.py` | `backend/modules/employee/routers/entity_communication.py` |
| 186 | `backend/routers/escalation.py` | `backend/modules/admin/routers/escalation.py` |
| 187 | `backend/routers/ess.py` | `backend/modules/employee/routers/ess.py` |
| 188 | `backend/routers/expense_controller.py` | `backend/modules/employee/routers/expense_controller.py` |
| 189 | `backend/routers/expenses.py` | `backend/modules/employee/routers/expenses.py` |
| 190 | `backend/routers/export.py` | `backend/modules/admin/routers/export.py` |
| 191 | `backend/routers/finance.py` | `backend/modules/employee/routers/finance.py` |
| 192 | `backend/routers/finance_automation.py` | `backend/modules/employee/routers/finance_automation.py` |
| 193 | `backend/routers/finance_erp.py` | `backend/modules/employee/routers/finance_erp.py` |
| 194 | `backend/routers/finance_package.py` | `backend/modules/employee/routers/finance_package.py` |
| 195 | `backend/routers/flash_sales.py` | `backend/modules/admin/routers/flash_sales.py` |
| 196 | `backend/routers/fraud_detection.py` | `backend/modules/admin/routers/fraud_detection.py` |
| 197 | `backend/routers/frontend_errors.py` | `backend/modules/admin/routers/frontend_errors.py` |
| 198 | `backend/routers/geo.py` | `backend/modules/admin/routers/geo.py` |
| 199 | `backend/routers/governance_package.py` | `backend/modules/admin/routers/governance_package.py` |
| 200 | `backend/routers/hierarchy.py` | `backend/modules/employee/routers/hierarchy.py` |
| 201 | `backend/routers/hr.py` | `backend/modules/employee/routers/hr.py` |
| 202 | `backend/routers/hr_dashboard.py` | `backend/modules/employee/routers/hr_dashboard.py` |
| 203 | `backend/routers/iam.py` | `backend/modules/admin/routers/iam.py` |
| 204 | `backend/routers/imports.py` | `backend/modules/admin/routers/imports.py` |
| 205 | `backend/routers/incident.py` | `backend/modules/admin/routers/incident.py` |
| 206 | `backend/routers/internal_channels.py` | `backend/modules/employee/routers/internal_channels.py` |
| 207 | `backend/routers/internal_comms_channels.py` | `backend/modules/employee/routers/internal_comms_channels.py` |
| 208 | `backend/routers/invoices.py` | `backend/modules/employee/routers/invoices.py` |
| 209 | `backend/routers/jobs.py` | `backend/modules/employee/routers/jobs.py` |
| 210 | `backend/routers/lms.py` | `backend/modules/employee/routers/lms.py` |
| 211 | `backend/routers/location_api.py` | `backend/modules/admin/routers/location_api.py` |
| 212 | `backend/routers/logistics.py` | `backend/modules/logistics/routers/logistics.py` |
| 213 | `backend/routers/logistics_health.py` | `backend/modules/logistics/routers/logistics_health.py` |
| 214 | `backend/routers/logistics_health_list.py` | `backend/modules/logistics/routers/logistics_health_list.py` |
| 215 | `backend/routers/logistics_locations.py` | `backend/modules/logistics/routers/logistics_locations.py` |
| 216 | `backend/routers/logistics_locations_create.py` | `backend/modules/logistics/routers/logistics_locations_create.py` |
| 217 | `backend/routers/logistics_logistics_status.py` | `backend/modules/logistics/routers/logistics_logistics_status.py` |
| 218 | `backend/routers/logistics_orders_list.py` | `backend/modules/logistics/routers/logistics_orders_list.py` |
| 219 | `backend/routers/logistics_orders_v2.py` | `backend/modules/logistics/routers/logistics_orders_v2.py` |
| 220 | `backend/routers/logistics_partner.py` | `backend/modules/logistics/routers/logistics_partner.py` |
| 221 | `backend/routers/logistics_partner_verify.py` | `backend/modules/logistics/routers/logistics_partner_verify.py` |
| 222 | `backend/routers/messaging.py` | `backend/modules/employee/routers/messaging.py` |
| 223 | `backend/routers/mobile_controller.py` | `backend/modules/admin/routers/mobile_controller.py` |
| 224 | `backend/routers/notifications.py` | `backend/modules/employee/routers/notifications.py` |
| 225 | `backend/routers/okr.py` | `backend/modules/employee/routers/okr.py` |
| 226 | `backend/routers/onboarding.py` | `backend/modules/supplier/routers/onboarding.py` |
| 227 | `backend/routers/operational_controller.py` | `backend/modules/admin/routers/operational_controller.py` |
| 228 | `backend/routers/orders.py` | `backend/modules/customer/routers/orders.py` |
| 229 | `backend/routers/parcel_tracking.py` | `backend/modules/logistics/routers/parcel_tracking.py` |
| 230 | `backend/routers/payments.py` | `backend/modules/customer/routers/payments.py` |
| 231 | `backend/routers/payout_approval.py` | `backend/modules/admin/routers/payout_approval.py` |
| 232 | `backend/routers/payroll.py` | `backend/modules/employee/routers/payroll.py` |
| 233 | `backend/routers/performance.py` | `backend/modules/employee/routers/performance.py` |
| 234 | `backend/routers/permissions.py` | `backend/modules/admin/routers/permissions.py` |
| 235 | `backend/routers/product_moderation.py` | `backend/modules/supplier/routers/product_moderation.py` |
| 236 | `backend/routers/product_verification.py` | `backend/modules/supplier/routers/product_verification.py` |
| 237 | `backend/routers/product_videos.py` | `backend/modules/supplier/routers/product_videos.py` |
| 238 | `backend/routers/products.py` | `backend/modules/supplier/routers/products.py` |
| 239 | `backend/routers/proxy_communication.py` | `backend/modules/employee/routers/proxy_communication.py` |
| 240 | `backend/routers/public_auth_access.py` | `backend/modules/admin/routers/public_auth_access.py` |
| 241 | `backend/routers/public_commerce_referrals.py` | `backend/modules/admin/routers/public_commerce_referrals.py` |
| 242 | `backend/routers/public_commerce_reviews.py` | `backend/modules/admin/routers/public_commerce_reviews.py` |
| 243 | `backend/routers/public_commerce_validation.py` | `backend/modules/admin/routers/public_commerce_validation.py` |
| 244 | `backend/routers/public_commerce_wishlist.py` | `backend/modules/admin/routers/public_commerce_wishlist.py` |
| 245 | `backend/routers/public_comms_status.py` | `backend/modules/admin/routers/public_comms_status.py` |
| 246 | `backend/routers/public_comms_unified.py` | `backend/modules/admin/routers/public_comms_unified.py` |
| 247 | `backend/routers/public_core_ai_upload.py` | `backend/modules/admin/routers/public_core_ai_upload.py` |
| 248 | `backend/routers/public_core_export.py` | `backend/modules/admin/routers/public_core_export.py` |
| 249 | `backend/routers/public_core_translate.py` | `backend/modules/admin/routers/public_core_translate.py` |
| 250 | `backend/routers/public_country_auto_populate_access.py` | `backend/modules/admin/routers/public_country_auto_populate_access.py` |
| 251 | `backend/routers/public_effective_permissions_access.py` | `backend/modules/admin/routers/public_effective_permissions_access.py` |
| 252 | `backend/routers/public_finance_creation.py` | `backend/modules/admin/routers/public_finance_creation.py` |
| 253 | `backend/routers/public_geography_configuration.py` | `backend/modules/admin/routers/public_geography_configuration.py` |
| 254 | `backend/routers/public_hr.py` | `backend/modules/admin/routers/public_hr.py` |
| 255 | `backend/routers/public_hr_hierarchy.py` | `backend/modules/admin/routers/public_hr_hierarchy.py` |
| 256 | `backend/routers/public_identity_operations.py` | `backend/modules/admin/routers/public_identity_operations.py` |
| 257 | `backend/routers/public_permission_primitives_access.py` | `backend/modules/admin/routers/public_permission_primitives_access.py` |
| 258 | `backend/routers/public_permissions_validation.py` | `backend/modules/admin/routers/public_permissions_validation.py` |
| 259 | `backend/routers/public_security_detection.py` | `backend/modules/admin/routers/public_security_detection.py` |
| 260 | `backend/routers/public_security_health.py` | `backend/modules/admin/routers/public_security_health.py` |
| 261 | `backend/routers/public_security_operations.py` | `backend/modules/admin/routers/public_security_operations.py` |
| 262 | `backend/routers/public_security_registration.py` | `backend/modules/admin/routers/public_security_registration.py` |
| 263 | `backend/routers/public_suppliers.py` | `backend/modules/admin/routers/public_suppliers.py` |
| 264 | `backend/routers/public_suppliers_routes.py` | `backend/modules/admin/routers/public_suppliers_routes.py` |
| 265 | `backend/routers/public_treasury_api_access.py` | `backend/modules/admin/routers/public_treasury_api_access.py` |
| 266 | `backend/routers/public_treasury_cash_position.py` | `backend/modules/admin/routers/public_treasury_cash_position.py` |
| 267 | `backend/routers/public_treasury_payments.py` | `backend/modules/admin/routers/public_treasury_payments.py` |
| 268 | `backend/routers/push_notifications.py` | `backend/modules/employee/routers/push_notifications.py` |
| 269 | `backend/routers/referrals.py` | `backend/modules/customer/routers/referrals.py` |
| 270 | `backend/routers/returns.py` | `backend/modules/customer/routers/returns.py` |
| 271 | `backend/routers/reviews.py` | `backend/modules/customer/routers/reviews.py` |
| 272 | `backend/routers/risk.py` | `backend/modules/employee/routers/risk.py` |
| 273 | `backend/routers/search.py` | `backend/modules/admin/routers/search.py` |  _(manual: store/search)_
| 274 | `backend/routers/shift_handover.py` | `backend/modules/employee/routers/shift_handover.py` |
| 275 | `backend/routers/shipments.py` | `backend/modules/logistics/routers/shipments.py` |
| 276 | `backend/routers/shop_locations.py` | `backend/modules/admin/routers/shop_locations.py` |
| 277 | `backend/routers/store_banners_routes.py` | `backend/modules/admin/routers/store_banners_routes.py` |  _(manual: store/search)_
| 278 | `backend/routers/store_cart_routes.py` | `backend/modules/admin/routers/store_cart_routes.py` |  _(manual: store/search)_
| 279 | `backend/routers/store_currency_routes.py` | `backend/modules/admin/routers/store_currency_routes.py` |  _(manual: store/search)_
| 280 | `backend/routers/store_orders_routes.py` | `backend/modules/admin/routers/store_orders_routes.py` |  _(manual: store/search)_
| 281 | `backend/routers/store_payments_routes.py` | `backend/modules/admin/routers/store_payments_routes.py` |  _(manual: store/search)_
| 282 | `backend/routers/store_products_routes.py` | `backend/modules/admin/routers/store_products_routes.py` |  _(manual: store/search)_
| 283 | `backend/routers/store_referrals_routes.py` | `backend/modules/admin/routers/store_referrals_routes.py` |  _(manual: store/search)_
| 284 | `backend/routers/store_returns_routes.py` | `backend/modules/admin/routers/store_returns_routes.py` |  _(manual: store/search)_
| 285 | `backend/routers/store_shipments_routes.py` | `backend/modules/admin/routers/store_shipments_routes.py` |  _(manual: store/search)_
| 286 | `backend/routers/succession.py` | `backend/modules/employee/routers/succession.py` |
| 287 | `backend/routers/supplier.py` | `backend/modules/supplier/routers/supplier.py` |
| 288 | `backend/routers/supplier_analytics.py` | `backend/modules/supplier/routers/supplier_analytics.py` |
| 289 | `backend/routers/supplier_analytics_analytics.py` | `backend/modules/supplier/routers/supplier_analytics_analytics.py` |
| 290 | `backend/routers/supplier_bg_ab_test.py` | `backend/modules/supplier/routers/supplier_bg_ab_test.py` |
| 291 | `backend/routers/supplier_core_routes.py` | `backend/modules/supplier/routers/supplier_core_routes.py` |
| 292 | `backend/routers/supplier_documents.py` | `backend/modules/supplier/routers/supplier_documents.py` |
| 293 | `backend/routers/supplier_documents_review.py` | `backend/modules/supplier/routers/supplier_documents_review.py` |
| 294 | `backend/routers/supplier_finance.py` | `backend/modules/supplier/routers/supplier_finance.py` |
| 295 | `backend/routers/supplier_finance_status.py` | `backend/modules/supplier/routers/supplier_finance_status.py` |
| 296 | `backend/routers/supplier_health.py` | `backend/modules/supplier/routers/supplier_health.py` |
| 297 | `backend/routers/supplier_health_list.py` | `backend/modules/supplier/routers/supplier_health_list.py` |
| 298 | `backend/routers/supplier_orders.py` | `backend/modules/supplier/routers/supplier_orders.py` |
| 299 | `backend/routers/supplier_orders_verify.py` | `backend/modules/supplier/routers/supplier_orders_verify.py` |
| 300 | `backend/routers/supplier_payouts.py` | `backend/modules/supplier/routers/supplier_payouts.py` |
| 301 | `backend/routers/supplier_payouts_pay.py` | `backend/modules/supplier/routers/supplier_payouts_pay.py` |
| 302 | `backend/routers/supplier_products.py` | `backend/modules/supplier/routers/supplier_products.py` |
| 303 | `backend/routers/supplier_products_upload.py` | `backend/modules/supplier/routers/supplier_products_upload.py` |
| 304 | `backend/routers/supplier_profile.py` | `backend/modules/supplier/routers/supplier_profile.py` |
| 305 | `backend/routers/supplier_profile_create.py` | `backend/modules/supplier/routers/supplier_profile_create.py` |
| 306 | `backend/routers/supplier_supplier_supplier_health.py` | `backend/modules/supplier/routers/supplier_supplier_supplier_health.py` |
| 307 | `backend/routers/supplier_supplier_sync.py` | `backend/modules/supplier/routers/supplier_supplier_sync.py` |
| 308 | `backend/routers/supplier_supplier_upload.py` | `backend/modules/supplier/routers/supplier_supplier_upload.py` |
| 309 | `backend/routers/system_ai_country_research.py` | `backend/modules/admin/routers/system_ai_country_research.py` |
| 310 | `backend/routers/system_ai_media.py` | `backend/modules/admin/routers/system_ai_media.py` |
| 311 | `backend/routers/system_ai_messaging.py` | `backend/modules/admin/routers/system_ai_messaging.py` |
| 312 | `backend/routers/system_ai_reporting.py` | `backend/modules/admin/routers/system_ai_reporting.py` |
| 313 | `backend/routers/system_ai_sync.py` | `backend/modules/admin/routers/system_ai_sync.py` |
| 314 | `backend/routers/system_ai_upload.py` | `backend/modules/admin/routers/system_ai_upload.py` |
| 315 | `backend/routers/system_comms_status.py` | `backend/modules/admin/routers/system_comms_status.py` |
| 316 | `backend/routers/tickets.py` | `backend/modules/employee/routers/tickets.py` |
| 317 | `backend/routers/trading.py` | `backend/modules/employee/routers/trading.py` |
| 318 | `backend/routers/translate.py` | `backend/modules/admin/routers/translate.py` |
| 319 | `backend/routers/travel.py` | `backend/modules/employee/routers/travel.py` |
| 320 | `backend/routers/treasury.py` | `backend/modules/employee/routers/treasury.py` |
| 321 | `backend/routers/treasury_api.py` | `backend/modules/employee/routers/treasury_api.py` |
| 322 | `backend/routers/upload.py` | `backend/modules/admin/routers/upload.py` |
| 323 | `backend/routers/upload_jobs.py` | `backend/modules/admin/routers/upload_jobs.py` |
| 324 | `backend/routers/users.py` | `backend/modules/admin/routers/users.py` |
| 325 | `backend/routers/video.py` | `backend/modules/employee/routers/video.py` |
| 326 | `backend/routers/video_controller.py` | `backend/modules/employee/routers/video_controller.py` |
| 327 | `backend/routers/wishlist.py` | `backend/modules/customer/routers/wishlist.py` |
| 328 | `backend/routers/workflows.py` | `backend/modules/admin/routers/workflows.py` |
| 329 | `backend/routers/ws_chat.py` | `backend/modules/employee/routers/ws_chat.py` |
## 1. CONTROLLERS (backend/controllers/*)

| sno | source | domains | modules | infrastructure | rbac | kernel |
|---|---|---|---|---|---|---|
| 1 | `backend/controllers/admin/admin_controller.py` |  | modules/admin/routers/admin_controller.py |  |  |  |
| 2 | `backend/controllers/admin/analytics_controller.py` |  | modules/admin/routers/analytics_controller.py |  |  |  |
| 3 | `backend/controllers/admin/analytics_fallback_controller.py` |  | modules/admin/routers/analytics_fallback_controller.py |  |  |  |
| 4 | `backend/controllers/admin/audit_controller.py` |  | modules/admin/routers/audit_controller.py |  |  |  |
| 5 | `backend/controllers/admin/auth.py` |  | modules/admin/routers/auth.py |  |  |  |
| 6 | `backend/controllers/admin/bank_accounts_controller.py` |  | modules/admin/routers/bank_accounts_controller.py |  |  |  |
| 7 | `backend/controllers/admin/coupons_controller.py` |  | modules/admin/routers/coupons_controller.py |  |  |  |
| 8 | `backend/controllers/admin/misc_controller.py` |  | modules/admin/routers/misc_controller.py |  |  |  |
| 9 | `backend/controllers/admin/orders_controller.py` |  | modules/admin/routers/orders_controller.py |  |  |  |
| 10 | `backend/controllers/admin/payouts_controller.py` |  | modules/admin/routers/payouts_controller.py |  |  |  |
| 11 | `backend/controllers/admin/permissions_controller.py` |  | modules/admin/routers/permissions_controller.py |  |  |  |
| 12 | `backend/controllers/admin/products_controller.py` |  | modules/admin/routers/products_controller.py |  |  |  |
| 13 | `backend/controllers/admin/suppliers_controller.py` |  | modules/admin/routers/suppliers_controller.py |  |  |  |
| 14 | `backend/controllers/admin/tickets_controller.py` |  | modules/admin/routers/tickets_controller.py |  |  |  |
| 15 | `backend/controllers/admin/users_admin_controller.py` |  | modules/admin/routers/users_admin_controller.py |  |  |  |
| 16 | `backend/controllers/catalog/banner_controller.py` | domains/catalog/services/banner_controller.py |  |  |  |  |
| 17 | `backend/controllers/catalog/categories_controller.py` | domains/catalog/services/categories_controller.py |  |  |  |  |
| 18 | `backend/controllers/catalog/category_admin_controller.py` | domains/catalog/services/category_admin_controller.py |  |  |  |  |
| 19 | `backend/controllers/commerce/cart_controller.py` | domains/orders/services/cart_controller.py |  |  |  |  |
| 20 | `backend/controllers/commerce/coupons_controller.py` | domains/orders/services/coupons_controller.py |  |  |  |  |
| 21 | `backend/controllers/commerce/flash_sale_controller.py` | domains/orders/services/flash_sale_controller.py |  |  |  |  |
| 22 | `backend/controllers/commerce/promotion_admin_controller.py` | domains/orders/services/promotion_admin_controller.py |  |  |  |  |
| 23 | `backend/controllers/commerce/promotion_controller.py` | domains/orders/services/promotion_controller.py |  |  |  |  |
| 24 | `backend/controllers/commerce/referrals_controller.py` | domains/orders/services/referrals_controller.py |  |  |  |  |
| 25 | `backend/controllers/commerce/reviews_controller.py` | domains/orders/services/reviews_controller.py |  |  |  |  |
| 26 | `backend/controllers/commerce/wishlist_controller.py` | domains/orders/services/wishlist_controller.py |  |  |  |  |
| 27 | `backend/controllers/comms/chat_write_controller.py` | domains/comms/services/chat_write_controller.py |  |  |  |  |
| 28 | `backend/controllers/comms/chatbot_controller.py` | domains/comms/services/chatbot_controller.py |  |  |  |  |
| 29 | `backend/controllers/comms/comm_controller.py` | domains/comms/services/comm_controller.py |  |  |  |  |
| 30 | `backend/controllers/core/ai_controller.py` |  | modules/admin/routers/ai_controller.py |  |  |  |
| 31 | `backend/controllers/core/ai_upload_controller.py` |  | modules/admin/routers/ai_upload_controller.py |  |  |  |
| 32 | `backend/controllers/core/export_controller.py` |  | modules/admin/routers/export_controller.py |  |  |  |
| 33 | `backend/controllers/customer/users.py` |  | modules/customer/routers/users.py |  |  |  |
| 34 | `backend/controllers/delegators/admin.py` | domains/governance/services/admin.py |  |  |  |  |
| 35 | `backend/controllers/delegators/admin_admin_fallback_service.py` | domains/governance/services/admin_admin_fallback_service.py |  |  |  |  |
| 36 | `backend/controllers/delegators/admin_admin_write_service.py` | domains/governance/services/admin_admin_write_service.py |  |  |  |  |
| 37 | `backend/controllers/delegators/ai.py` | domains/media/services/ai.py |  |  |  |  |
| 38 | `backend/controllers/delegators/ai_ai_automation_service.py` | domains/media/services/ai_ai_automation_service.py |  |  |  |  |
| 39 | `backend/controllers/delegators/ai_ai_copy_jobs.py` | domains/media/services/ai_ai_copy_jobs.py |  |  |  |  |
| 40 | `backend/controllers/delegators/ai_ai_research_jobs.py` | domains/media/services/ai_ai_research_jobs.py |  |  |  |  |
| 41 | `backend/controllers/delegators/ai_ai_variant_config.py` | domains/media/services/ai_ai_variant_config.py |  |  |  |  |
| 42 | `backend/controllers/delegators/ai_bg_removal_service.py` | domains/media/services/ai_bg_removal_service.py |  |  |  |  |
| 43 | `backend/controllers/delegators/ai_country_ai_research.py` | domains/media/services/ai_country_ai_research.py |  |  |  |  |
| 44 | `backend/controllers/delegators/ai_parcel_verification_service.py` | domains/media/services/ai_parcel_verification_service.py |  |  |  |  |
| 45 | `backend/controllers/delegators/audit_audit_trail_service.py` | domains/governance/services/audit_audit_trail_service.py |  |  |  |  |
| 46 | `backend/controllers/delegators/audit_compliance_engine.py` | domains/governance/services/audit_compliance_engine.py |  |  |  |  |
| 47 | `backend/controllers/delegators/catalog_product_admin_read_service.py` | domains/catalog/services/catalog_product_admin_read_service.py |  |  |  |  |
| 48 | `backend/controllers/delegators/catalog_product_admin_write_service.py` | domains/catalog/services/catalog_product_admin_write_service.py |  |  |  |  |
| 49 | `backend/controllers/delegators/catalog_variant_config_service.py` | domains/catalog/services/catalog_variant_config_service.py |  |  |  |  |
| 50 | `backend/controllers/delegators/commerce.py` | domains/orders/services/commerce.py |  |  |  |  |
| 51 | `backend/controllers/delegators/commerce_coupons_read_service.py` | domains/orders/services/commerce_coupons_read_service.py |  |  |  |  |
| 52 | `backend/controllers/delegators/commerce_coupons_write_service.py` | domains/orders/services/commerce_coupons_write_service.py |  |  |  |  |
| 53 | `backend/controllers/delegators/common.py` |  |  | infrastructure/utils/common.py |  |  |
| 54 | `backend/controllers/delegators/common_asset_tracking.py` |  |  | infrastructure/utils/common_asset_tracking.py |  |  |
| 55 | `backend/controllers/delegators/common_storage.py` |  |  | infrastructure/utils/common_storage.py |  |  |
| 56 | `backend/controllers/delegators/comms_campaign_geography_service.py` | domains/comms/services/comms_campaign_geography_service.py |  |  |  |  |
| 57 | `backend/controllers/delegators/comms_chat_system.py` | domains/comms/services/comms_chat_system.py |  |  |  |  |
| 58 | `backend/controllers/delegators/comms_content_service.py` | domains/comms/services/comms_content_service.py |  |  |  |  |
| 59 | `backend/controllers/delegators/comms_entity_chat_service.py` | domains/comms/services/comms_entity_chat_service.py |  |  |  |  |
| 60 | `backend/controllers/delegators/comms_internal_communication.py` | domains/comms/services/comms_internal_communication.py |  |  |  |  |
| 61 | `backend/controllers/delegators/comms_realtime_chat_service.py` | domains/comms/services/comms_realtime_chat_service.py |  |  |  |  |
| 62 | `backend/controllers/delegators/comms_unified_inbox_service.py` | domains/comms/services/comms_unified_inbox_service.py |  |  |  |  |
| 63 | `backend/controllers/delegators/comms_video_conferencing.py` | domains/comms/services/comms_video_conferencing.py |  |  |  |  |
| 64 | `backend/controllers/delegators/comms_video_room_service.py` | domains/comms/services/comms_video_room_service.py |  |  |  |  |
| 65 | `backend/controllers/delegators/communication_package_service.py` | domains/comms/services/communication_package_service.py |  |  |  |  |
| 66 | `backend/controllers/delegators/country_country_communications_read_service.py` | domains/country/services/country_country_communications_read_service.py |  |  |  |  |
| 67 | `backend/controllers/delegators/customer_customer_health_engine.py` | domains/customers/services/customer_customer_health_engine.py |  |  |  |  |
| 68 | `backend/controllers/delegators/finance.py` | domains/finance/services/finance.py |  |  |  |  |
| 69 | `backend/controllers/delegators/finance_commission_geography_service.py` | domains/finance/services/finance_commission_geography_service.py |  |  |  |  |
| 70 | `backend/controllers/delegators/finance_contractor_milestone_read_service.py` | domains/finance/services/finance_contractor_milestone_read_service.py |  |  |  |  |
| 71 | `backend/controllers/delegators/finance_credit_control_service.py` | domains/finance/services/finance_credit_control_service.py |  |  |  |  |
| 72 | `backend/controllers/delegators/finance_expense_processing.py` | domains/finance/services/finance_expense_processing.py |  |  |  |  |
| 73 | `backend/controllers/delegators/finance_expense_routing.py` | domains/finance/services/finance_expense_routing.py |  |  |  |  |
| 74 | `backend/controllers/delegators/finance_financial_reporting.py` | domains/finance/services/finance_financial_reporting.py |  |  |  |  |
| 75 | `backend/controllers/delegators/finance_je_reversal_service.py` | domains/finance/services/finance_je_reversal_service.py |  |  |  |  |
| 76 | `backend/controllers/delegators/finance_period_close_service.py` | domains/finance/services/finance_period_close_service.py |  |  |  |  |
| 77 | `backend/controllers/delegators/finance_refund_posting_service.py` | domains/finance/services/finance_refund_posting_service.py |  |  |  |  |
| 78 | `backend/controllers/delegators/gateways_gateway_reconciliation_service.py` |  |  | providers/payments/gateways_gateway_reconciliation_service.py |  |  |
| 79 | `backend/controllers/delegators/gateways_payments.py` |  |  | providers/payments/gateways_payments.py |  |  |
| 80 | `backend/controllers/delegators/geography_country_audit_admin_service.py` | domains/country/services/geography_country_audit_admin_service.py |  |  |  |  |
| 81 | `backend/controllers/delegators/geography_country_config_admin_service.py` | domains/country/services/geography_country_config_admin_service.py |  |  |  |  |
| 82 | `backend/controllers/delegators/governance_command_center_service.py` | domains/governance/services/governance_command_center_service.py |  |  |  |  |
| 83 | `backend/controllers/delegators/hierarchy_hierarchy_service.py` | domains/hr/services/hierarchy_hierarchy_service.py |  |  |  |  |
| 84 | `backend/controllers/delegators/hr_leave_accrual.py` | domains/hr/services/hr_leave_accrual.py |  |  |  |  |
| 85 | `backend/controllers/delegators/hr_payroll_engine.py` | domains/hr/services/hr_payroll_engine.py |  |  |  |  |
| 86 | `backend/controllers/delegators/location_service_geo_resolver.py` | domains/UNMAPPED/services/location_service_geo_resolver.py |  |  |  |  |
| 87 | `backend/controllers/delegators/logistics_admin_operations_service.py` | domains/logistics/services/logistics_admin_operations_service.py |  |  |  |  |
| 88 | `backend/controllers/delegators/logistics_logistics_health_service.py` | domains/logistics/services/logistics_logistics_health_service.py |  |  |  |  |
| 89 | `backend/controllers/delegators/logistics_logistics_partner_write_service.py` | domains/logistics/services/logistics_logistics_partner_write_service.py |  |  |  |  |
| 90 | `backend/controllers/delegators/logistics_partner_geography_service.py` | domains/logistics/services/logistics_partner_geography_service.py |  |  |  |  |
| 91 | `backend/controllers/delegators/logistics_partner_shipments_service.py` | domains/logistics/services/logistics_partner_shipments_service.py |  |  |  |  |
| 92 | `backend/controllers/delegators/logistics_shipment_service.py` | domains/logistics/services/logistics_shipment_service.py |  |  |  |  |
| 93 | `backend/controllers/delegators/logistics_shipping_tier.py` | domains/logistics/services/logistics_shipping_tier.py |  |  |  |  |
| 94 | `backend/controllers/delegators/orders_admin_orders_read_service.py` | domains/orders/services/orders_admin_orders_read_service.py |  |  |  |  |
| 95 | `backend/controllers/delegators/orders_admin_orders_write_service.py` | domains/orders/services/orders_admin_orders_write_service.py |  |  |  |  |
| 96 | `backend/controllers/delegators/orders_order_tracking_service.py` | domains/orders/services/orders_order_tracking_service.py |  |  |  |  |
| 97 | `backend/controllers/delegators/security.py` |  |  |  | rbac/security.py |  |
| 98 | `backend/controllers/delegators/security_auth_write_service.py` |  |  |  | rbac/security_auth_write_service.py |  |
| 99 | `backend/controllers/delegators/security_effective_permissions.py` |  |  |  | rbac/security_effective_permissions.py |  |
| 100 | `backend/controllers/delegators/security_fraud_admin_service.py` |  |  |  | rbac/security_fraud_admin_service.py |  |
| 101 | `backend/controllers/delegators/security_fraud_detection_service.py` |  |  |  | rbac/security_fraud_detection_service.py |  |
| 102 | `backend/controllers/delegators/security_incident_service.py` |  |  |  | rbac/security_incident_service.py |  |
| 103 | `backend/controllers/delegators/security_risk_service.py` |  |  |  | rbac/security_risk_service.py |  |
| 104 | `backend/controllers/delegators/supplier_legal_contract_service.py` | domains/suppliers/services/supplier_legal_contract_service.py |  |  |  |  |
| 105 | `backend/controllers/delegators/supplier_supplier_analytics_service.py` | domains/suppliers/services/supplier_supplier_analytics_service.py |  |  |  |  |
| 106 | `backend/controllers/delegators/supplier_supplier_document_service.py` | domains/suppliers/services/supplier_supplier_document_service.py |  |  |  |  |
| 107 | `backend/controllers/delegators/supplier_supplier_finance_service.py` | domains/suppliers/services/supplier_supplier_finance_service.py |  |  |  |  |
| 108 | `backend/controllers/delegators/supplier_supplier_health_service.py` | domains/suppliers/services/supplier_supplier_health_service.py |  |  |  |  |
| 109 | `backend/controllers/delegators/supplier_supplier_order_service.py` | domains/suppliers/services/supplier_supplier_order_service.py |  |  |  |  |
| 110 | `backend/controllers/delegators/supplier_supplier_payout_service.py` | domains/suppliers/services/supplier_supplier_payout_service.py |  |  |  |  |
| 111 | `backend/controllers/delegators/supplier_supplier_products_upload_service.py` | domains/suppliers/services/supplier_supplier_products_upload_service.py |  |  |  |  |
| 112 | `backend/controllers/delegators/supplier_supplier_profile_write_service.py` | domains/suppliers/services/supplier_supplier_profile_write_service.py |  |  |  |  |
| 113 | `backend/controllers/delegators/suppliers.py` | domains/suppliers/services/suppliers.py |  |  |  |  |
| 114 | `backend/controllers/delegators/system_ai_upload_service.py` | domains/media/services/system_ai_upload_service.py |  |  |  |  |
| 115 | `backend/controllers/delegators/treasury.py` | domains/finance/services/treasury.py |  |  |  |  |
| 116 | `backend/controllers/delegators/treasury_admin_treasury_write_service.py` | domains/finance/services/treasury_admin_treasury_write_service.py |  |  |  |  |
| 117 | `backend/controllers/delegators/treasury_auto_payout_scheduler.py` | domains/finance/services/treasury_auto_payout_scheduler.py |  |  |  |  |
| 118 | `backend/controllers/delegators/treasury_cash_flow_forecast_service.py` | domains/finance/services/treasury_cash_flow_forecast_service.py |  |  |  |  |
| 119 | `backend/controllers/delegators/treasury_cash_read_service.py` | domains/finance/services/treasury_cash_read_service.py |  |  |  |  |
| 120 | `backend/controllers/delegators/treasury_cash_write_service.py` | domains/finance/services/treasury_cash_write_service.py |  |  |  |  |
| 121 | `backend/controllers/delegators/treasury_payout_approval_read_service.py` | domains/finance/services/treasury_payout_approval_read_service.py |  |  |  |  |
| 122 | `backend/controllers/delegators/treasury_payout_approval_write_service.py` | domains/finance/services/treasury_payout_approval_write_service.py |  |  |  |  |
| 123 | `backend/controllers/delegators/treasury_payout_batch_service.py` | domains/finance/services/treasury_payout_batch_service.py |  |  |  |  |
| 124 | `backend/controllers/delegators/treasury_treasury_adapter.py` | domains/finance/services/treasury_treasury_adapter.py |  |  |  |  |
| 125 | `backend/controllers/delegators/treasury_treasury_service.py` | domains/finance/services/treasury_treasury_service.py |  |  |  |  |
| 126 | `backend/controllers/delegators/users_approval_matrix_service.py` | domains/accounts/services/users_approval_matrix_service.py |  |  |  |  |
| 127 | `backend/controllers/delegators/users_identity_admin_service.py` | domains/accounts/services/users_identity_admin_service.py |  |  |  |  |
| 128 | `backend/controllers/finance/accounting_controller.py` | domains/finance/services/accounting_controller.py |  |  |  |  |
| 129 | `backend/controllers/finance/commission_controller.py` | domains/finance/services/commission_controller.py |  |  |  |  |
| 130 | `backend/controllers/finance/invoice_controller.py` | domains/finance/services/invoice_controller.py |  |  |  |  |
| 131 | `backend/controllers/finance/sub_ledger_controller.py` | domains/finance/services/sub_ledger_controller.py |  |  |  |  |
| 132 | `backend/controllers/geography/country_controller.py` | domains/country/services/country_controller.py |  |  |  |  |
| 133 | `backend/controllers/geography/country_versioning_controller.py` | domains/country/services/country_versioning_controller.py |  |  |  |  |
| 134 | `backend/controllers/governance/command_center_controller.py` | domains/governance/services/command_center_controller.py |  |  |  |  |
| 135 | `backend/controllers/hr/employees_controller.py` | domains/hr/services/employees_controller.py |  |  |  |  |
| 136 | `backend/controllers/hr/hierarchy_controller.py` | domains/hr/services/hierarchy_controller.py |  |  |  |  |
| 137 | `backend/controllers/hr/lms_controller.py` | domains/hr/services/lms_controller.py |  |  |  |  |
| 138 | `backend/controllers/identity/iam_controller.py` |  |  |  | rbac/iam_controller.py |  |
| 139 | `backend/controllers/orders/disputes_controller.py` | domains/orders/services/disputes_controller.py |  |  |  |  |
| 140 | `backend/controllers/orders/logistics_controller.py` | domains/orders/services/logistics_controller.py |  |  |  |  |
| 141 | `backend/controllers/orders/logistics_partner_controller.py` | domains/orders/services/logistics_partner_controller.py |  |  |  |  |
| 142 | `backend/controllers/orders/orders_controller.py` | domains/orders/services/orders_controller.py |  |  |  |  |
| 143 | `backend/controllers/orders/returns_controller.py` | domains/orders/services/returns_controller.py |  |  |  |  |
| 144 | `backend/controllers/products/products_controller.py` | domains/catalog/services/products_controller.py |  |  |  |  |
| 145 | `backend/controllers/security/admin_users.py` |  |  |  | rbac/admin_users.py |  |
| 146 | `backend/controllers/security/auth_controller.py` |  |  |  | rbac/auth_controller.py |  |
| 147 | `backend/controllers/security/risk_controller.py` |  |  |  | rbac/risk_controller.py |  |
| 148 | `backend/controllers/supplier/supplier_controller.py` |  | modules/supplier/routers/supplier_controller.py |  |  |  |
| 149 | `backend/controllers/supplier/supplier_document_controller.py` |  | modules/supplier/routers/supplier_document_controller.py |  |  |  |
| 150 | `backend/controllers/supplier/supplier_health_controller.py` |  | modules/supplier/routers/supplier_health_controller.py |  |  |  |
| 151 | `backend/controllers/treasury/cash_management_controller.py` | domains/finance/services/cash_management_controller.py |  |  |  |  |
| 152 | `backend/controllers/treasury/cash_management_write_controller.py` | domains/finance/services/cash_management_write_controller.py |  |  |  |  |
| 153 | `backend/controllers/treasury/payout_approval_controller.py` | domains/finance/services/payout_approval_controller.py |  |  |  |  |

**Column totals:** domains=115 modules=22 infrastructure=5 rbac=11 kernel=0

### NEEDS MANUAL REVIEW (1)
- `backend/controllers/delegators/location_service_geo_resolver.py` -> `domains/UNMAPPED/services/location_service_geo_resolver.py`

---

## 2. SERVICES (backend/services/*)

| sno | source | domains | modules | infrastructure | rbac | kernel |
|---|---|---|---|---|---|---|
| 1 | `backend/services/_registry.py` |  |  | infrastructure/utils/_registry.py |  |  |
| 2 | `backend/services/admin/admin_catalog_operations_service.py` | domains/governance/services/admin_catalog_operations_service.py |  |  |  |  |
| 3 | `backend/services/admin/admin_catalog_orders_service.py` | domains/governance/services/admin_catalog_orders_service.py |  |  |  |  |
| 4 | `backend/services/admin/admin_commerce_configuration_service.py` | domains/governance/services/admin_commerce_configuration_service.py |  |  |  |  |
| 5 | `backend/services/admin/admin_comms_messaging_service.py` | domains/governance/services/admin_comms_messaging_service.py |  |  |  |  |
| 6 | `backend/services/admin/admin_comms_unified_service.py` | domains/governance/services/admin_comms_unified_service.py |  |  |  |  |
| 7 | `backend/services/admin/admin_fallback_service.py` | domains/governance/services/admin_fallback_service.py |  |  |  |  |
| 8 | `backend/services/admin/admin_finance_creation_service.py` | domains/governance/services/admin_finance_creation_service.py |  |  |  |  |
| 9 | `backend/services/admin/admin_geography_configuration_service.py` | domains/governance/services/admin_geography_configuration_service.py |  |  |  |  |
| 10 | `backend/services/admin/admin_identity_operations_api_service.py` | domains/governance/services/admin_identity_operations_api_service.py |  |  |  |  |
| 11 | `backend/services/admin/admin_identity_operations_service.py` | domains/governance/services/admin_identity_operations_service.py |  |  |  |  |
| 12 | `backend/services/admin/admin_logistics_fallback_service.py` | domains/governance/services/admin_logistics_fallback_service.py |  |  |  |  |
| 13 | `backend/services/admin/admin_logistics_imports_service.py` | domains/governance/services/admin_logistics_imports_service.py |  |  |  |  |
| 14 | `backend/services/admin/admin_logistics_operations_service.py` | domains/governance/services/admin_logistics_operations_service.py |  |  |  |  |
| 15 | `backend/services/admin/admin_orders_status_service.py` | domains/governance/services/admin_orders_status_service.py |  |  |  |  |
| 16 | `backend/services/admin/admin_permissions_validation_service.py` | domains/governance/services/admin_permissions_validation_service.py |  |  |  |  |
| 17 | `backend/services/admin/admin_security_detection_service.py` | domains/governance/services/admin_security_detection_service.py |  |  |  |  |
| 18 | `backend/services/admin/admin_security_health_service.py` | domains/governance/services/admin_security_health_service.py |  |  |  |  |
| 19 | `backend/services/admin/admin_security_operations_service.py` | domains/governance/services/admin_security_operations_service.py |  |  |  |  |
| 20 | `backend/services/admin/admin_security_registration_service.py` | domains/governance/services/admin_security_registration_service.py |  |  |  |  |
| 21 | `backend/services/admin/admin_supplier_reviews_service.py` | domains/governance/services/admin_supplier_reviews_service.py |  |  |  |  |
| 22 | `backend/services/admin/admin_supplier_trading_service.py` | domains/governance/services/admin_supplier_trading_service.py |  |  |  |  |
| 23 | `backend/services/admin/admin_treasury_identity_service.py` | domains/governance/services/admin_treasury_identity_service.py |  |  |  |  |
| 24 | `backend/services/admin/admin_treasury_payments_service.py` | domains/governance/services/admin_treasury_payments_service.py |  |  |  |  |
| 25 | `backend/services/admin/admin_treasury_reporting_service.py` | domains/governance/services/admin_treasury_reporting_service.py |  |  |  |  |
| 26 | `backend/services/admin/admin_treasury_status_service.py` | domains/governance/services/admin_treasury_status_service.py |  |  |  |  |
| 27 | `backend/services/admin/admin_write_service.py` | domains/governance/services/admin_write_service.py |  |  |  |  |
| 28 | `backend/services/admin/analytics_fallback_service.py` | domains/governance/services/analytics_fallback_service.py |  |  |  |  |
| 29 | `backend/services/admin/analytics_service.py` | domains/governance/services/analytics_service.py |  |  |  |  |
| 30 | `backend/services/admin/bulk_ops_service.py` | domains/governance/services/bulk_ops_service.py |  |  |  |  |
| 31 | `backend/services/admin/coupons_service.py` | domains/governance/services/coupons_service.py |  |  |  |  |
| 32 | `backend/services/admin/database_service.py` | domains/governance/services/database_service.py |  |  |  |  |
| 33 | `backend/services/admin/misc_service.py` | domains/governance/services/misc_service.py |  |  |  |  |
| 34 | `backend/services/admin/orders_service.py` | domains/governance/services/orders_service.py |  |  |  |  |
| 35 | `backend/services/admin/payouts_service.py` | domains/governance/services/payouts_service.py |  |  |  |  |
| 36 | `backend/services/admin/permissions_service.py` | domains/governance/services/permissions_service.py |  |  |  |  |
| 37 | `backend/services/admin/products_service.py` | domains/governance/services/products_service.py |  |  |  |  |
| 38 | `backend/services/admin/suppliers_service.py` | domains/governance/services/suppliers_service.py |  |  |  |  |
| 39 | `backend/services/admin/tickets_service.py` | domains/governance/services/tickets_service.py |  |  |  |  |
| 40 | `backend/services/admin/users_service.py` | domains/governance/services/users_service.py |  |  |  |  |
| 41 | `backend/services/ai/ai_automation_service.py` | domains/media/services/ai_automation_service.py |  |  |  |  |
| 42 | `backend/services/ai/ai_copy_jobs.py` | domains/media/services/ai_copy_jobs.py |  |  |  |  |
| 43 | `backend/services/ai/ai_research_jobs.py` | domains/media/services/ai_research_jobs.py |  |  |  |  |
| 44 | `backend/services/ai/ai_search_service.py` | domains/media/services/ai_search_service.py |  |  |  |  |
| 45 | `backend/services/ai/ai_service.py` | domains/media/services/ai_service.py |  |  |  |  |
| 46 | `backend/services/ai/ai_upload_write_service.py` | domains/media/services/ai_upload_write_service.py |  |  |  |  |
| 47 | `backend/services/ai/ai_variant_config.py` | domains/media/services/ai_variant_config.py |  |  |  |  |
| 48 | `backend/services/ai/automation_read_service.py` | domains/media/services/automation_read_service.py |  |  |  |  |
| 49 | `backend/services/ai/automation_scheduler.py` | domains/media/services/automation_scheduler.py |  |  |  |  |
| 50 | `backend/services/ai/bg_removal_presets.py` | domains/media/services/bg_removal_presets.py |  |  |  |  |
| 51 | `backend/services/ai/bg_removal_service.py` | domains/media/services/bg_removal_service.py |  |  |  |  |
| 52 | `backend/services/ai/country_ai_research.py` | domains/media/services/country_ai_research.py |  |  |  |  |
| 53 | `backend/services/ai/ocr_parser.py` | domains/media/services/ocr_parser.py |  |  |  |  |
| 54 | `backend/services/ai/parcel_verification_service.py` | domains/media/services/parcel_verification_service.py |  |  |  |  |
| 55 | `backend/services/analytics/admin_analytics_service.py` | domains/governance/services/admin_analytics_service.py |  |  |  |  |
| 56 | `backend/services/analytics/analytics_service.py` | domains/governance/services/analytics_service.py |  |  |  |  |
| 57 | `backend/services/analytics/confidence_scoring.py` | domains/governance/services/confidence_scoring.py |  |  |  |  |
| 58 | `backend/services/api/api_geography_location_service.py` | domains/country/services/api_geography_location_service.py |  |  |  |  |
| 59 | `backend/services/audit/audit_query_service.py` | domains/governance/services/audit_query_service.py |  |  |  |  |
| 60 | `backend/services/audit/audit_service.py` | domains/governance/services/audit_service.py |  |  |  |  |
| 61 | `backend/services/audit/audit_trail_service.py` | domains/governance/services/audit_trail_service.py |  |  |  |  |
| 62 | `backend/services/audit/compliance_engine.py` | domains/governance/services/compliance_engine.py |  |  |  |  |
| 63 | `backend/services/audit/ediscovery.py` | domains/governance/services/ediscovery.py |  |  |  |  |
| 64 | `backend/services/audit/worm_audit.py` | domains/governance/services/worm_audit.py |  |  |  |  |
| 65 | `backend/services/catalog/advanced_filter_service.py` | domains/catalog/services/advanced_filter_service.py |  |  |  |  |
| 66 | `backend/services/catalog/advanced_search_engine.py` | domains/catalog/services/advanced_search_engine.py |  |  |  |  |
| 67 | `backend/services/catalog/banner_service.py` | domains/catalog/services/banner_service.py |  |  |  |  |
| 68 | `backend/services/catalog/banner_write_service.py` | domains/catalog/services/banner_write_service.py |  |  |  |  |
| 69 | `backend/services/catalog/bulk_ops_write_service.py` | domains/catalog/services/bulk_ops_write_service.py |  |  |  |  |
| 70 | `backend/services/catalog/category_admin_read_service.py` | domains/catalog/services/category_admin_read_service.py |  |  |  |  |
| 71 | `backend/services/catalog/category_admin_write_service.py` | domains/catalog/services/category_admin_write_service.py |  |  |  |  |
| 72 | `backend/services/catalog/category_service.py` | domains/catalog/services/category_service.py |  |  |  |  |
| 73 | `backend/services/catalog/product_admin_read_service.py` | domains/catalog/services/product_admin_read_service.py |  |  |  |  |
| 74 | `backend/services/catalog/product_admin_write_service.py` | domains/catalog/services/product_admin_write_service.py |  |  |  |  |
| 75 | `backend/services/catalog/product_moderation_service.py` | domains/catalog/services/product_moderation_service.py |  |  |  |  |
| 76 | `backend/services/catalog/product_service.py` | domains/catalog/services/product_service.py |  |  |  |  |
| 77 | `backend/services/catalog/product_verification_write_service.py` | domains/catalog/services/product_verification_write_service.py |  |  |  |  |
| 78 | `backend/services/catalog/products_write_service.py` | domains/catalog/services/products_write_service.py |  |  |  |  |
| 79 | `backend/services/catalog/variant_config_service.py` | domains/catalog/services/variant_config_service.py |  |  |  |  |
| 80 | `backend/services/catalog/visual_search_service.py` | domains/catalog/services/visual_search_service.py |  |  |  |  |
| 81 | `backend/services/commerce/admin_promotion_service.py` | domains/orders/services/admin_promotion_service.py |  |  |  |  |
| 82 | `backend/services/commerce/banner_write_service.py` | domains/orders/services/banner_write_service.py |  |  |  |  |
| 83 | `backend/services/commerce/cart_controller_service.py` | domains/orders/services/cart_controller_service.py |  |  |  |  |
| 84 | `backend/services/commerce/cart_service.py` | domains/orders/services/cart_service.py |  |  |  |  |
| 85 | `backend/services/commerce/commerce_read_service.py` | domains/orders/services/commerce_read_service.py |  |  |  |  |
| 86 | `backend/services/commerce/commerce_write_service.py` | domains/orders/services/commerce_write_service.py |  |  |  |  |
| 87 | `backend/services/commerce/coupons_legacy_write_service.py` | domains/orders/services/coupons_legacy_write_service.py |  |  |  |  |
| 88 | `backend/services/commerce/coupons_read_service.py` | domains/orders/services/coupons_read_service.py |  |  |  |  |
| 89 | `backend/services/commerce/coupons_service.py` | domains/orders/services/coupons_service.py |  |  |  |  |
| 90 | `backend/services/commerce/coupons_write_service.py` | domains/orders/services/coupons_write_service.py |  |  |  |  |
| 91 | `backend/services/commerce/customer_router_service.py` | domains/orders/services/customer_router_service.py |  |  |  |  |
| 92 | `backend/services/commerce/flash_sale_controller_service.py` | domains/orders/services/flash_sale_controller_service.py |  |  |  |  |
| 93 | `backend/services/commerce/flash_sale_service.py` | domains/orders/services/flash_sale_service.py |  |  |  |  |
| 94 | `backend/services/commerce/flash_sale_write_service.py` | domains/orders/services/flash_sale_write_service.py |  |  |  |  |
| 95 | `backend/services/commerce/package_service.py` | domains/orders/services/package_service.py |  |  |  |  |
| 96 | `backend/services/commerce/promotion_bogo_service.py` | domains/orders/services/promotion_bogo_service.py |  |  |  |  |
| 97 | `backend/services/commerce/promotion_engine_service.py` | domains/orders/services/promotion_engine_service.py |  |  |  |  |
| 98 | `backend/services/commerce/promotion_points_service.py` | domains/orders/services/promotion_points_service.py |  |  |  |  |
| 99 | `backend/services/commerce/promotion_service.py` | domains/orders/services/promotion_service.py |  |  |  |  |
| 100 | `backend/services/commerce/promotions_write_service.py` | domains/orders/services/promotions_write_service.py |  |  |  |  |
| 101 | `backend/services/commerce/referrals_service.py` | domains/orders/services/referrals_service.py |  |  |  |  |
| 102 | `backend/services/commerce/reviews_service.py` | domains/orders/services/reviews_service.py |  |  |  |  |
| 103 | `backend/services/commerce/wishlist_read_service.py` | domains/orders/services/wishlist_read_service.py |  |  |  |  |
| 104 | `backend/services/commerce/wishlist_write_service.py` | domains/orders/services/wishlist_write_service.py |  |  |  |  |
| 105 | `backend/services/common/asset_tracking.py` |  |  | infrastructure/utils/asset_tracking.py |  |  |
| 106 | `backend/services/common/command_center_background.py` |  |  | infrastructure/utils/command_center_background.py |  |  |
| 107 | `backend/services/common/command_center_service.py` |  |  | infrastructure/utils/command_center_service.py |  |  |
| 108 | `backend/services/common/db_read.py` |  |  | infrastructure/utils/db_read.py |  |  |
| 109 | `backend/services/common/db_write.py` |  |  | infrastructure/utils/db_write.py |  |  |
| 110 | `backend/services/common/downstream_hooks.py` |  |  | infrastructure/utils/downstream_hooks.py |  |  |
| 111 | `backend/services/common/downstream_wiring.py` |  |  | infrastructure/utils/downstream_wiring.py |  |  |
| 112 | `backend/services/common/event_bus.py` |  |  | infrastructure/utils/event_bus.py |  |  |
| 113 | `backend/services/common/free_image_tools.py` |  |  | infrastructure/utils/free_image_tools.py |  |  |
| 114 | `backend/services/common/image_ai_service.py` |  |  | infrastructure/utils/image_ai_service.py |  |  |
| 115 | `backend/services/common/import_service.py` |  |  | infrastructure/utils/import_service.py |  |  |
| 116 | `backend/services/common/media_service.py` |  |  | infrastructure/utils/media_service.py |  |  |
| 117 | `backend/services/common/media_storage.py` |  |  | infrastructure/utils/media_storage.py |  |  |
| 118 | `backend/services/common/misc_write_service.py` |  |  | infrastructure/utils/misc_write_service.py |  |  |
| 119 | `backend/services/common/qr_service.py` |  |  | infrastructure/utils/qr_service.py |  |  |
| 120 | `backend/services/common/run_py.py` |  |  | infrastructure/utils/run_py.py |  |  |
| 121 | `backend/services/common/script1.py` |  |  | infrastructure/utils/script1.py |  |  |
| 122 | `backend/services/common/storage.py` |  |  | infrastructure/utils/storage.py |  |  |
| 123 | `backend/services/common/template.py` |  |  | infrastructure/utils/template.py |  |  |
| 124 | `backend/services/common/upload_job_service.py` |  |  | infrastructure/utils/upload_job_service.py |  |  |
| 125 | `backend/services/common/write_files_script.py` |  |  | infrastructure/utils/write_files_script.py |  |  |
| 126 | `backend/services/common/write_help.py` |  |  | infrastructure/utils/write_help.py |  |  |
| 127 | `backend/services/common/write_helpers.py` |  |  | infrastructure/utils/write_helpers.py |  |  |
| 128 | `backend/services/comms/campaign_geography_service.py` | domains/comms/services/campaign_geography_service.py |  |  |  |  |
| 129 | `backend/services/comms/chat_enrichment.py` | domains/comms/services/chat_enrichment.py |  |  |  |  |
| 130 | `backend/services/comms/chat_read_service.py` | domains/comms/services/chat_read_service.py |  |  |  |  |
| 131 | `backend/services/comms/chat_system.py` | domains/comms/services/chat_system.py |  |  |  |  |
| 132 | `backend/services/comms/chat_write_service.py` | domains/comms/services/chat_write_service.py |  |  |  |  |
| 133 | `backend/services/comms/chatbot_service.py` | domains/comms/services/chatbot_service.py |  |  |  |  |
| 134 | `backend/services/comms/comm_service.py` | domains/comms/services/comm_service.py |  |  |  |  |
| 135 | `backend/services/comms/comm_write_service.py` | domains/comms/services/comm_write_service.py |  |  |  |  |
| 136 | `backend/services/comms/command_center_query_service.py` | domains/comms/services/command_center_query_service.py |  |  |  |  |
| 137 | `backend/services/comms/communication_audit.py` | domains/comms/services/communication_audit.py |  |  |  |  |
| 138 | `backend/services/comms/communication_read_service.py` | domains/comms/services/communication_read_service.py |  |  |  |  |
| 139 | `backend/services/comms/communication_write_service.py` | domains/comms/services/communication_write_service.py |  |  |  |  |
| 140 | `backend/services/comms/content_service.py` | domains/comms/services/content_service.py |  |  |  |  |
| 141 | `backend/services/comms/email_enrichment.py` | domains/comms/services/email_enrichment.py |  |  |  |  |
| 142 | `backend/services/comms/email_event_service.py` | domains/comms/services/email_event_service.py |  |  |  |  |
| 143 | `backend/services/comms/email_gateway.py` | domains/comms/services/email_gateway.py |  |  |  |  |
| 144 | `backend/services/comms/email_management_service.py` | domains/comms/services/email_management_service.py |  |  |  |  |
| 145 | `backend/services/comms/email_reputation.py` | domains/comms/services/email_reputation.py |  |  |  |  |
| 146 | `backend/services/comms/email_write_service.py` | domains/comms/services/email_write_service.py |  |  |  |  |
| 147 | `backend/services/comms/entity_chat_service.py` | domains/comms/services/entity_chat_service.py |  |  |  |  |
| 148 | `backend/services/comms/entity_messaging.py` | domains/comms/services/entity_messaging.py |  |  |  |  |
| 149 | `backend/services/comms/escalation_sla.py` | domains/comms/services/escalation_sla.py |  |  |  |  |
| 150 | `backend/services/comms/external_contact.py` | domains/comms/services/external_contact.py |  |  |  |  |
| 151 | `backend/services/comms/fix_chat.py` | domains/comms/services/fix_chat.py |  |  |  |  |
| 152 | `backend/services/comms/internal_communication.py` | domains/comms/services/internal_communication.py |  |  |  |  |
| 153 | `backend/services/comms/notification_engine.py` | domains/comms/services/notification_engine.py |  |  |  |  |
| 154 | `backend/services/comms/notification_service.py` | domains/comms/services/notification_service.py |  |  |  |  |
| 155 | `backend/services/comms/notification_worker.py` | domains/comms/services/notification_worker.py |  |  |  |  |
| 156 | `backend/services/comms/payout_notification_service.py` | domains/comms/services/payout_notification_service.py |  |  |  |  |
| 157 | `backend/services/comms/proxy_communication.py` | domains/comms/services/proxy_communication.py |  |  |  |  |
| 158 | `backend/services/comms/push_notifications_service.py` | domains/comms/services/push_notifications_service.py |  |  |  |  |
| 159 | `backend/services/comms/realtime_chat_service.py` | domains/comms/services/realtime_chat_service.py |  |  |  |  |
| 160 | `backend/services/comms/tickets_write_service.py` | domains/comms/services/tickets_write_service.py |  |  |  |  |
| 161 | `backend/services/comms/transactional_email_service.py` | domains/comms/services/transactional_email_service.py |  |  |  |  |
| 162 | `backend/services/comms/translation_service.py` | domains/comms/services/translation_service.py |  |  |  |  |
| 163 | `backend/services/comms/unified_inbox_service.py` | domains/comms/services/unified_inbox_service.py |  |  |  |  |
| 164 | `backend/services/comms/video_conferencing.py` | domains/comms/services/video_conferencing.py |  |  |  |  |
| 165 | `backend/services/comms/video_room_service.py` | domains/comms/services/video_room_service.py |  |  |  |  |
| 166 | `backend/services/comms/video_room_write_service.py` | domains/comms/services/video_room_write_service.py |  |  |  |  |
| 167 | `backend/services/comms/video_service.py` | domains/comms/services/video_service.py |  |  |  |  |
| 168 | `backend/services/comms/websocket_chat.py` | domains/comms/services/websocket_chat.py |  |  |  |  |
| 169 | `backend/services/comms/websocket_manager.py` | domains/comms/services/websocket_manager.py |  |  |  |  |
| 170 | `backend/services/comms/write_chat.py` | domains/comms/services/write_chat.py |  |  |  |  |
| 171 | `backend/services/communication/package_service.py` | domains/comms/services/package_service.py |  |  |  |  |
| 172 | `backend/services/core/chatbot_service.py` | domains/UNMAPPED/services/chatbot_service.py |  |  |  |  |
| 173 | `backend/services/core/export_read_service.py` | domains/UNMAPPED/services/export_read_service.py |  |  |  |  |
| 174 | `backend/services/core/export_service.py` | domains/UNMAPPED/services/export_service.py |  |  |  |  |
| 175 | `backend/services/core/search_service.py` | domains/UNMAPPED/services/search_service.py |  |  |  |  |
| 176 | `backend/services/core/user_read_service.py` | domains/UNMAPPED/services/user_read_service.py |  |  |  |  |
| 177 | `backend/services/country/country_communications_read_service.py` | domains/country/services/country_communications_read_service.py |  |  |  |  |
| 178 | `backend/services/country/country_communications_service.py` | domains/country/services/country_communications_service.py |  |  |  |  |
| 179 | `backend/services/customer/customer_coupons_create_service.py` | domains/customers/services/customer_coupons_create_service.py |  |  |  |  |
| 180 | `backend/services/customer/customer_health_engine.py` | domains/customers/services/customer_health_engine.py |  |  |  |  |
| 181 | `backend/services/customer/customer_health_list_service.py` | domains/customers/services/customer_health_list_service.py |  |  |  |  |
| 182 | `backend/services/customer/retention_service.py` | domains/customers/services/retention_service.py |  |  |  |  |
| 183 | `backend/services/employee/attendance_service.py` | domains/hr/services/attendance_service.py |  |  |  |  |
| 184 | `backend/services/employee/background_check.py` | domains/hr/services/background_check.py |  |  |  |  |
| 185 | `backend/services/finance/auto_payout_scheduler.py` | domains/finance/services/auto_payout_scheduler.py |  |  |  |  |
| 186 | `backend/services/finance/badge_billing_payment.py` | domains/finance/services/badge_billing_payment.py |  |  |  |  |
| 187 | `backend/services/finance/bank_transaction_service.py` | domains/finance/services/bank_transaction_service.py |  |  |  |  |
| 188 | `backend/services/finance/cash_flow_forecast_service.py` | domains/finance/services/cash_flow_forecast_service.py |  |  |  |  |
| 189 | `backend/services/finance/cash_management_service.py` | domains/finance/services/cash_management_service.py |  |  |  |  |
| 190 | `backend/services/finance/cash_management_write_service.py` | domains/finance/services/cash_management_write_service.py |  |  |  |  |
| 191 | `backend/services/finance/commission_admin_write_service.py` | domains/finance/services/commission_admin_write_service.py |  |  |  |  |
| 192 | `backend/services/finance/commission_engine.py` | domains/finance/services/commission_engine.py |  |  |  |  |
| 193 | `backend/services/finance/commission_geography_service.py` | domains/finance/services/commission_geography_service.py |  |  |  |  |
| 194 | `backend/services/finance/commission_service.py` | domains/finance/services/commission_service.py |  |  |  |  |
| 195 | `backend/services/finance/commission_write_service.py` | domains/finance/services/commission_write_service.py |  |  |  |  |
| 196 | `backend/services/finance/contractor_milestone_read_service.py` | domains/finance/services/contractor_milestone_read_service.py |  |  |  |  |
| 197 | `backend/services/finance/credit_control_service.py` | domains/finance/services/credit_control_service.py |  |  |  |  |
| 198 | `backend/services/finance/erp_finance_service.py` | domains/finance/services/erp_finance_service.py |  |  |  |  |
| 199 | `backend/services/finance/erp_read_service.py` | domains/finance/services/erp_read_service.py |  |  |  |  |
| 200 | `backend/services/finance/expense_processing.py` | domains/finance/services/expense_processing.py |  |  |  |  |
| 201 | `backend/services/finance/expense_routing.py` | domains/finance/services/expense_routing.py |  |  |  |  |
| 202 | `backend/services/finance/finance_automation.py` | domains/finance/services/finance_automation.py |  |  |  |  |
| 203 | `backend/services/finance/finance_automation_write_service.py` | domains/finance/services/finance_automation_write_service.py |  |  |  |  |
| 204 | `backend/services/finance/finance_erp_write_service.py` | domains/finance/services/finance_erp_write_service.py |  |  |  |  |
| 205 | `backend/services/finance/finance_package_service.py` | domains/finance/services/finance_package_service.py |  |  |  |  |
| 206 | `backend/services/finance/finance_transfer_service.py` | domains/finance/services/finance_transfer_service.py |  |  |  |  |
| 207 | `backend/services/finance/financial_reporting.py` | domains/finance/services/financial_reporting.py |  |  |  |  |
| 208 | `backend/services/finance/financial_reports_service.py` | domains/finance/services/financial_reports_service.py |  |  |  |  |
| 209 | `backend/services/finance/general_ledger_service.py` | domains/finance/services/general_ledger_service.py |  |  |  |  |
| 210 | `backend/services/finance/invoice_service.py` | domains/finance/services/invoice_service.py |  |  |  |  |
| 211 | `backend/services/finance/invoice_write_service.py` | domains/finance/services/invoice_write_service.py |  |  |  |  |
| 212 | `backend/services/finance/je_reversal_service.py` | domains/finance/services/je_reversal_service.py |  |  |  |  |
| 213 | `backend/services/finance/order_payment_functions.py` | domains/finance/services/order_payment_functions.py |  |  |  |  |
| 214 | `backend/services/finance/payments_gateway_service.py` | domains/finance/services/payments_gateway_service.py |  |  |  |  |
| 215 | `backend/services/finance/payout_admin_write_service.py` | domains/finance/services/payout_admin_write_service.py |  |  |  |  |
| 216 | `backend/services/finance/period_close_service.py` | domains/finance/services/period_close_service.py |  |  |  |  |
| 217 | `backend/services/finance/refund_posting_service.py` | domains/finance/services/refund_posting_service.py |  |  |  |  |
| 218 | `backend/services/finance/sub_ledger_service.py` | domains/finance/services/sub_ledger_service.py |  |  |  |  |
| 219 | `backend/services/finance/supplier_finance_service.py` | domains/finance/services/supplier_finance_service.py |  |  |  |  |
| 220 | `backend/services/finance/tax_service.py` | domains/finance/services/tax_service.py |  |  |  |  |
| 221 | `backend/services/finance/trading_service.py` | domains/finance/services/trading_service.py |  |  |  |  |
| 222 | `backend/services/gateways/base.py` |  |  | providers/payments/base.py |  |  |
| 223 | `backend/services/gateways/base_models.py` |  |  | providers/payments/base_models.py |  |  |
| 224 | `backend/services/gateways/gateway_auto_enable.py` |  |  | providers/payments/gateway_auto_enable.py |  |  |
| 225 | `backend/services/gateways/gateway_reconciliation_service.py` |  |  | providers/payments/gateway_reconciliation_service.py |  |  |
| 226 | `backend/services/gateways/payment_event_handlers.py` |  |  | providers/payments/payment_event_handlers.py |  |  |
| 227 | `backend/services/gateways/payments.py` |  |  | providers/payments/payments.py |  |  |
| 228 | `backend/services/gateways/payments_write_service.py` |  |  | providers/payments/payments_write_service.py |  |  |
| 229 | `backend/services/gateways/registry.py` |  |  | providers/payments/registry.py |  |  |
| 230 | `backend/services/gateways/webhook_models.py` |  |  | providers/payments/webhook_models.py |  |  |
| 231 | `backend/services/gateways/webhook_processor.py` |  |  | providers/payments/webhook_processor.py |  |  |
| 232 | `backend/services/geography/category_tax_profiles.py` | domains/country/services/category_tax_profiles.py |  |  |  |  |
| 233 | `backend/services/geography/country_admin_write_service.py` | domains/country/services/country_admin_write_service.py |  |  |  |  |
| 234 | `backend/services/geography/country_audit_admin_service.py` | domains/country/services/country_audit_admin_service.py |  |  |  |  |
| 235 | `backend/services/geography/country_auto_populate.py` | domains/country/services/country_auto_populate.py |  |  |  |  |
| 236 | `backend/services/geography/country_auto_populate_write_service.py` | domains/country/services/country_auto_populate_write_service.py |  |  |  |  |
| 237 | `backend/services/geography/country_communication_service.py` | domains/country/services/country_communication_service.py |  |  |  |  |
| 238 | `backend/services/geography/country_config_admin_service.py` | domains/country/services/country_config_admin_service.py |  |  |  |  |
| 239 | `backend/services/geography/country_config_write_service.py` | domains/country/services/country_config_write_service.py |  |  |  |  |
| 240 | `backend/services/geography/country_curated.py` | domains/country/services/country_curated.py |  |  |  |  |
| 241 | `backend/services/geography/country_data_orchestrator.py` | domains/country/services/country_data_orchestrator.py |  |  |  |  |
| 242 | `backend/services/geography/country_detection.py` | domains/country/services/country_detection.py |  |  |  |  |
| 243 | `backend/services/geography/country_dropdown_service.py` | domains/country/services/country_dropdown_service.py |  |  |  |  |
| 244 | `backend/services/geography/country_heuristic_engine.py` | domains/country/services/country_heuristic_engine.py |  |  |  |  |
| 245 | `backend/services/geography/country_maps_service.py` | domains/country/services/country_maps_service.py |  |  |  |  |
| 246 | `backend/services/geography/country_payout_write_service.py` | domains/country/services/country_payout_write_service.py |  |  |  |  |
| 247 | `backend/services/geography/country_read_service.py` | domains/country/services/country_read_service.py |  |  |  |  |
| 248 | `backend/services/geography/country_research.py` | domains/country/services/country_research.py |  |  |  |  |
| 249 | `backend/services/geography/country_restriction_service.py` | domains/country/services/country_restriction_service.py |  |  |  |  |
| 250 | `backend/services/geography/country_rls_service.py` | domains/country/services/country_rls_service.py |  |  |  |  |
| 251 | `backend/services/geography/country_router_service.py` | domains/country/services/country_router_service.py |  |  |  |  |
| 252 | `backend/services/geography/country_service.py` | domains/country/services/country_service.py |  |  |  |  |
| 253 | `backend/services/geography/country_staff_service.py` | domains/country/services/country_staff_service.py |  |  |  |  |
| 254 | `backend/services/geography/country_staff_write_service.py` | domains/country/services/country_staff_write_service.py |  |  |  |  |
| 255 | `backend/services/geography/country_tax_service.py` | domains/country/services/country_tax_service.py |  |  |  |  |
| 256 | `backend/services/geography/country_versioning_service.py` | domains/country/services/country_versioning_service.py |  |  |  |  |
| 257 | `backend/services/geography/country_write_service.py` | domains/country/services/country_write_service.py |  |  |  |  |
| 258 | `backend/services/geography/cross_border_detection.py` | domains/country/services/cross_border_detection.py |  |  |  |  |
| 259 | `backend/services/geography/cross_border_service.py` | domains/country/services/cross_border_service.py |  |  |  |  |
| 260 | `backend/services/geography/cross_border_tracker.py` | domains/country/services/cross_border_tracker.py |  |  |  |  |
| 261 | `backend/services/geography/curated_cities.py` | domains/country/services/curated_cities.py |  |  |  |  |
| 262 | `backend/services/geography/geo_service.py` | domains/country/services/geo_service.py |  |  |  |  |
| 263 | `backend/services/geography/localization_service.py` | domains/country/services/localization_service.py |  |  |  |  |
| 264 | `backend/services/geography/travel_detector.py` | domains/country/services/travel_detector.py |  |  |  |  |
| 265 | `backend/services/geography/travel_service.py` | domains/country/services/travel_service.py |  |  |  |  |
| 266 | `backend/services/geography/vat_rates.py` | domains/country/services/vat_rates.py |  |  |  |  |
| 267 | `backend/services/governance/command_center_service.py` | domains/governance/services/command_center_service.py |  |  |  |  |
| 268 | `backend/services/governance/governance_package_service.py` | domains/governance/services/governance_package_service.py |  |  |  |  |
| 269 | `backend/services/governance/incident_admin_read_service.py` | domains/governance/services/incident_admin_read_service.py |  |  |  |  |
| 270 | `backend/services/hierarchy/hierarchy_service.py` | domains/hr/services/hierarchy_service.py |  |  |  |  |
| 271 | `backend/services/hierarchy/org_hierarchy_write_service.py` | domains/hr/services/org_hierarchy_write_service.py |  |  |  |  |
| 272 | `backend/services/hr/attendance_service.py` | domains/hr/services/attendance_service.py |  |  |  |  |
| 273 | `backend/services/hr/background_check.py` | domains/hr/services/background_check.py |  |  |  |  |
| 274 | `backend/services/hr/coi_engine.py` | domains/hr/services/coi_engine.py |  |  |  |  |
| 275 | `backend/services/hr/coi_service.py` | domains/hr/services/coi_service.py |  |  |  |  |
| 276 | `backend/services/hr/dei_auditor.py` | domains/hr/services/dei_auditor.py |  |  |  |  |
| 277 | `backend/services/hr/employee_activity_logger.py` | domains/hr/services/employee_activity_logger.py |  |  |  |  |
| 278 | `backend/services/hr/employee_communication_service.py` | domains/hr/services/employee_communication_service.py |  |  |  |  |
| 279 | `backend/services/hr/employee_lifecycle_service.py` | domains/hr/services/employee_lifecycle_service.py |  |  |  |  |
| 280 | `backend/services/hr/employee_write_service.py` | domains/hr/services/employee_write_service.py |  |  |  |  |
| 281 | `backend/services/hr/employees_controller_service.py` | domains/hr/services/employees_controller_service.py |  |  |  |  |
| 282 | `backend/services/hr/employees_service.py` | domains/hr/services/employees_service.py |  |  |  |  |
| 283 | `backend/services/hr/ess_write_service.py` | domains/hr/services/ess_write_service.py |  |  |  |  |
| 284 | `backend/services/hr/hr_dashboard_service.py` | domains/hr/services/hr_dashboard_service.py |  |  |  |  |
| 285 | `backend/services/hr/hr_service.py` | domains/hr/services/hr_service.py |  |  |  |  |
| 286 | `backend/services/hr/hr_write_service.py` | domains/hr/services/hr_write_service.py |  |  |  |  |
| 287 | `backend/services/hr/hse_manager.py` | domains/hr/services/hse_manager.py |  |  |  |  |
| 288 | `backend/services/hr/learning_write_service.py` | domains/hr/services/learning_write_service.py |  |  |  |  |
| 289 | `backend/services/hr/leave_accrual.py` | domains/hr/services/leave_accrual.py |  |  |  |  |
| 290 | `backend/services/hr/lms.py` | domains/hr/services/lms.py |  |  |  |  |
| 291 | `backend/services/hr/lms_permission_lock.py` | domains/hr/services/lms_permission_lock.py |  |  |  |  |
| 292 | `backend/services/hr/lms_service.py` | domains/hr/services/lms_service.py |  |  |  |  |
| 293 | `backend/services/hr/lms_write_service.py` | domains/hr/services/lms_write_service.py |  |  |  |  |
| 294 | `backend/services/hr/offboarding.py` | domains/hr/services/offboarding.py |  |  |  |  |
| 295 | `backend/services/hr/okr_engine.py` | domains/hr/services/okr_engine.py |  |  |  |  |
| 296 | `backend/services/hr/payroll_engine.py` | domains/hr/services/payroll_engine.py |  |  |  |  |
| 297 | `backend/services/hr/payroll_read_service.py` | domains/hr/services/payroll_read_service.py |  |  |  |  |
| 298 | `backend/services/hr/payroll_service.py` | domains/hr/services/payroll_service.py |  |  |  |  |
| 299 | `backend/services/hr/performance_service.py` | domains/hr/services/performance_service.py |  |  |  |  |
| 300 | `backend/services/hr/shift_handover.py` | domains/hr/services/shift_handover.py |  |  |  |  |
| 301 | `backend/services/hr/shift_roster_service.py` | domains/hr/services/shift_roster_service.py |  |  |  |  |
| 302 | `backend/services/hr/shift_scheduling.py` | domains/hr/services/shift_scheduling.py |  |  |  |  |
| 303 | `backend/services/hr/succession_service.py` | domains/hr/services/succession_service.py |  |  |  |  |
| 304 | `backend/services/identity/iam_service.py` |  |  |  | rbac/iam_service.py |  |
| 305 | `backend/services/identity/identity_admin_service.py` |  |  |  | rbac/identity_admin_service.py |  |
| 306 | `backend/services/location_service/geo_resolver.py` | domains/country/services/geo_resolver.py |  |  |  |  |
| 307 | `backend/services/location_service/main.py` | domains/country/services/main.py |  |  |  |  |
| 308 | `backend/services/logistics/admin_operations_service.py` | domains/logistics/services/admin_operations_service.py |  |  |  |  |
| 309 | `backend/services/logistics/geo_fence_service.py` | domains/logistics/services/geo_fence_service.py |  |  |  |  |
| 310 | `backend/services/logistics/live_tracking_service.py` | domains/logistics/services/live_tracking_service.py |  |  |  |  |
| 311 | `backend/services/logistics/location_service.py` | domains/logistics/services/location_service.py |  |  |  |  |
| 312 | `backend/services/logistics/logistics_analytics_service.py` | domains/logistics/services/logistics_analytics_service.py |  |  |  |  |
| 313 | `backend/services/logistics/logistics_engine.py` | domains/logistics/services/logistics_engine.py |  |  |  |  |
| 314 | `backend/services/logistics/logistics_health_engine.py` | domains/logistics/services/logistics_health_engine.py |  |  |  |  |
| 315 | `backend/services/logistics/logistics_health_list_service.py` | domains/logistics/services/logistics_health_list_service.py |  |  |  |  |
| 316 | `backend/services/logistics/logistics_health_service.py` | domains/logistics/services/logistics_health_service.py |  |  |  |  |
| 317 | `backend/services/logistics/logistics_locations_create_service.py` | domains/logistics/services/logistics_locations_create_service.py |  |  |  |  |
| 318 | `backend/services/logistics/logistics_logistics_status_service.py` | domains/logistics/services/logistics_logistics_status_service.py |  |  |  |  |
| 319 | `backend/services/logistics/logistics_orders_list_service.py` | domains/logistics/services/logistics_orders_list_service.py |  |  |  |  |
| 320 | `backend/services/logistics/logistics_orders_v2_service.py` | domains/logistics/services/logistics_orders_v2_service.py |  |  |  |  |
| 321 | `backend/services/logistics/logistics_partner_admin_write_service.py` | domains/logistics/services/logistics_partner_admin_write_service.py |  |  |  |  |
| 322 | `backend/services/logistics/logistics_partner_pricing.py` | domains/logistics/services/logistics_partner_pricing.py |  |  |  |  |
| 323 | `backend/services/logistics/logistics_partner_verify_service.py` | domains/logistics/services/logistics_partner_verify_service.py |  |  |  |  |
| 324 | `backend/services/logistics/logistics_partner_write_service.py` | domains/logistics/services/logistics_partner_write_service.py |  |  |  |  |
| 325 | `backend/services/logistics/logistics_service.py` | domains/logistics/services/logistics_service.py |  |  |  |  |
| 326 | `backend/services/logistics/logistics_sla_service.py` | domains/logistics/services/logistics_sla_service.py |  |  |  |  |
| 327 | `backend/services/logistics/logistics_write_service.py` | domains/logistics/services/logistics_write_service.py |  |  |  |  |
| 328 | `backend/services/logistics/map_service.py` | domains/logistics/services/map_service.py |  |  |  |  |
| 329 | `backend/services/logistics/partner_blocker_service.py` | domains/logistics/services/partner_blocker_service.py |  |  |  |  |
| 330 | `backend/services/logistics/partner_geography_service.py` | domains/logistics/services/partner_geography_service.py |  |  |  |  |
| 331 | `backend/services/logistics/partner_shipments_service.py` | domains/logistics/services/partner_shipments_service.py |  |  |  |  |
| 332 | `backend/services/logistics/shipment_service.py` | domains/logistics/services/shipment_service.py |  |  |  |  |
| 333 | `backend/services/logistics/shipping_tier.py` | domains/logistics/services/shipping_tier.py |  |  |  |  |
| 334 | `backend/services/mcp/zozi_mcp.py` |  |  | providers/ai/zozi_mcp.py |  |  |
| 335 | `backend/services/orders/admin_orders_read_service.py` | domains/orders/services/admin_orders_read_service.py |  |  |  |  |
| 336 | `backend/services/orders/admin_orders_write_service.py` | domains/orders/services/admin_orders_write_service.py |  |  |  |  |
| 337 | `backend/services/orders/bulk_order_service.py` | domains/orders/services/bulk_order_service.py |  |  |  |  |
| 338 | `backend/services/orders/cart_controller_service.py` | domains/orders/services/cart_controller_service.py |  |  |  |  |
| 339 | `backend/services/orders/cart_service.py` | domains/orders/services/cart_service.py |  |  |  |  |
| 340 | `backend/services/orders/cart_write_service.py` | domains/orders/services/cart_write_service.py |  |  |  |  |
| 341 | `backend/services/orders/disputes_service.py` | domains/orders/services/disputes_service.py |  |  |  |  |
| 342 | `backend/services/orders/disputes_write_service.py` | domains/orders/services/disputes_write_service.py |  |  |  |  |
| 343 | `backend/services/orders/fulfillment_service.py` | domains/orders/services/fulfillment_service.py |  |  |  |  |
| 344 | `backend/services/orders/ghost_watchdog.py` | domains/orders/services/ghost_watchdog.py |  |  |  |  |
| 345 | `backend/services/orders/logistics_partner_service.py` | domains/orders/services/logistics_partner_service.py |  |  |  |  |
| 346 | `backend/services/orders/logistics_service.py` | domains/orders/services/logistics_service.py |  |  |  |  |
| 347 | `backend/services/orders/order_tracking_service.py` | domains/orders/services/order_tracking_service.py |  |  |  |  |
| 348 | `backend/services/orders/orders_service.py` | domains/orders/services/orders_service.py |  |  |  |  |
| 349 | `backend/services/orders/orders_write_service.py` | domains/orders/services/orders_write_service.py |  |  |  |  |
| 350 | `backend/services/orders/returns_controller_service.py` | domains/orders/services/returns_controller_service.py |  |  |  |  |
| 351 | `backend/services/orders/returns_service.py` | domains/orders/services/returns_service.py |  |  |  |  |
| 352 | `backend/services/orders/returns_write_service.py` | domains/orders/services/returns_write_service.py |  |  |  |  |
| 353 | `backend/services/products/product_verification_service.py` | domains/catalog/services/product_verification_service.py |  |  |  |  |
| 354 | `backend/services/products/products_service.py` | domains/catalog/services/products_service.py |  |  |  |  |
| 355 | `backend/services/promotions/admin_promotions_write_service.py` | domains/catalog/services/admin_promotions_write_service.py |  |  |  |  |
| 356 | `backend/services/promotions/promotion_admin_write_service.py` | domains/catalog/services/promotion_admin_write_service.py |  |  |  |  |
| 357 | `backend/services/public/public_commerce_validation_service.py` | domains/governance/services/public_commerce_validation_service.py |  |  |  |  |
| 358 | `backend/services/public/public_comms_status_service.py` | domains/governance/services/public_comms_status_service.py |  |  |  |  |
| 359 | `backend/services/public/public_comms_unified_service.py` | domains/governance/services/public_comms_unified_service.py |  |  |  |  |
| 360 | `backend/services/public/public_finance_creation_service.py` | domains/governance/services/public_finance_creation_service.py |  |  |  |  |
| 361 | `backend/services/public/public_geography_configuration_service.py` | domains/governance/services/public_geography_configuration_service.py |  |  |  |  |
| 362 | `backend/services/public/public_identity_operations_service.py` | domains/governance/services/public_identity_operations_service.py |  |  |  |  |
| 363 | `backend/services/public/public_permissions_validation_service.py` | domains/governance/services/public_permissions_validation_service.py |  |  |  |  |
| 364 | `backend/services/public/public_security_detection_service.py` | domains/governance/services/public_security_detection_service.py |  |  |  |  |
| 365 | `backend/services/public/public_security_health_service.py` | domains/governance/services/public_security_health_service.py |  |  |  |  |
| 366 | `backend/services/public/public_security_operations_service.py` | domains/governance/services/public_security_operations_service.py |  |  |  |  |
| 367 | `backend/services/public/public_security_registration_service.py` | domains/governance/services/public_security_registration_service.py |  |  |  |  |
| 368 | `backend/services/public/public_treasury_payments_service.py` | domains/governance/services/public_treasury_payments_service.py |  |  |  |  |
| 369 | `backend/services/security/admin_security_operations_service.py` |  |  |  | rbac/admin_security_operations_service.py |  |
| 370 | `backend/services/security/approval_matrix_service.py` |  |  |  | rbac/approval_matrix_service.py |  |
| 371 | `backend/services/security/auth_controller_service.py` |  |  |  | rbac/auth_controller_service.py |  |
| 372 | `backend/services/security/auth_service.py` |  |  |  | rbac/auth_service.py |  |
| 373 | `backend/services/security/auth_write_service.py` |  |  |  | rbac/auth_write_service.py |  |
| 374 | `backend/services/security/behavioral_analytics.py` |  |  |  | rbac/behavioral_analytics.py |  |
| 375 | `backend/services/security/biometric_auth.py` |  |  |  | rbac/biometric_auth.py |  |
| 376 | `backend/services/security/country_context_service.py` |  |  |  | rbac/country_context_service.py |  |
| 377 | `backend/services/security/data_residency.py` |  |  |  | rbac/data_residency.py |  |
| 378 | `backend/services/security/data_residency_service.py` |  |  |  | rbac/data_residency_service.py |  |
| 379 | `backend/services/security/effective_permissions.py` |  |  |  | rbac/effective_permissions.py |  |
| 380 | `backend/services/security/fraud_admin_controller_service.py` |  |  |  | rbac/fraud_admin_controller_service.py |  |
| 381 | `backend/services/security/fraud_admin_service.py` |  |  |  | rbac/fraud_admin_service.py |  |
| 382 | `backend/services/security/fraud_detection.py` |  |  |  | rbac/fraud_detection.py |  |
| 383 | `backend/services/security/fraud_detection_service.py` |  |  |  | rbac/fraud_detection_service.py |  |
| 384 | `backend/services/security/fraud_service.py` |  |  |  | rbac/fraud_service.py |  |
| 385 | `backend/services/security/iam_service.py` |  |  |  | rbac/iam_service.py |  |
| 386 | `backend/services/security/iam_write_service.py` |  |  |  | rbac/iam_write_service.py |  |
| 387 | `backend/services/security/impossible_travel_write_service.py` |  |  |  | rbac/impossible_travel_write_service.py |  |
| 388 | `backend/services/security/incident_service.py` |  |  |  | rbac/incident_service.py |  |
| 389 | `backend/services/security/kms_encryption.py` |  |  |  | rbac/kms_encryption.py |  |
| 390 | `backend/services/security/maker.py` |  |  |  | rbac/maker.py |  |
| 391 | `backend/services/security/mobile_auth_service.py` |  |  |  | rbac/mobile_auth_service.py |  |
| 392 | `backend/services/security/permission_primitive_write_service.py` |  |  |  | rbac/permission_primitive_write_service.py |  |
| 393 | `backend/services/security/permission_service.py` |  |  |  | rbac/permission_service.py |  |
| 394 | `backend/services/security/permissions_write_service.py` |  |  |  | rbac/permissions_write_service.py |  |
| 395 | `backend/services/security/risk_service.py` |  |  |  | rbac/risk_service.py |  |
| 396 | `backend/services/security/risk_write_service.py` |  |  |  | rbac/risk_write_service.py |  |
| 397 | `backend/services/security/siem_engine.py` |  |  |  | rbac/siem_engine.py |  |
| 398 | `backend/services/security/triple_auth.py` |  |  |  | rbac/triple_auth.py |  |
| 399 | `backend/services/supplier/admin_supplier_write_service.py` | domains/suppliers/services/admin_supplier_write_service.py |  |  |  |  |
| 400 | `backend/services/supplier/badge_billing_payment.py` | domains/suppliers/services/badge_billing_payment.py |  |  |  |  |
| 401 | `backend/services/supplier/cash_management_controller_service.py` | domains/suppliers/services/cash_management_controller_service.py |  |  |  |  |
| 402 | `backend/services/supplier/legal_contract_service.py` | domains/suppliers/services/legal_contract_service.py |  |  |  |  |
| 403 | `backend/services/supplier/onboarding_pipeline.py` | domains/suppliers/services/onboarding_pipeline.py |  |  |  |  |
| 404 | `backend/services/supplier/supplier_analytics_service.py` | domains/suppliers/services/supplier_analytics_service.py |  |  |  |  |
| 405 | `backend/services/supplier/supplier_badge_service.py` | domains/suppliers/services/supplier_badge_service.py |  |  |  |  |
| 406 | `backend/services/supplier/supplier_badge_write_service.py` | domains/suppliers/services/supplier_badge_write_service.py |  |  |  |  |
| 407 | `backend/services/supplier/supplier_bank_account_service.py` | domains/suppliers/services/supplier_bank_account_service.py |  |  |  |  |
| 408 | `backend/services/supplier/supplier_batch_write_service.py` | domains/suppliers/services/supplier_batch_write_service.py |  |  |  |  |
| 409 | `backend/services/supplier/supplier_document_controller_service.py` | domains/suppliers/services/supplier_document_controller_service.py |  |  |  |  |
| 410 | `backend/services/supplier/supplier_document_service.py` | domains/suppliers/services/supplier_document_service.py |  |  |  |  |
| 411 | `backend/services/supplier/supplier_finance_service.py` | domains/suppliers/services/supplier_finance_service.py |  |  |  |  |
| 412 | `backend/services/supplier/supplier_health_engine.py` | domains/suppliers/services/supplier_health_engine.py |  |  |  |  |
| 413 | `backend/services/supplier/supplier_health_service.py` | domains/suppliers/services/supplier_health_service.py |  |  |  |  |
| 414 | `backend/services/supplier/supplier_onboarding_service.py` | domains/suppliers/services/supplier_onboarding_service.py |  |  |  |  |
| 415 | `backend/services/supplier/supplier_order_service.py` | domains/suppliers/services/supplier_order_service.py |  |  |  |  |
| 416 | `backend/services/supplier/supplier_orders_verify_service.py` | domains/suppliers/services/supplier_orders_verify_service.py |  |  |  |  |
| 417 | `backend/services/supplier/supplier_payout_service.py` | domains/suppliers/services/supplier_payout_service.py |  |  |  |  |
| 418 | `backend/services/supplier/supplier_products_upload_service.py` | domains/suppliers/services/supplier_products_upload_service.py |  |  |  |  |
| 419 | `backend/services/supplier/supplier_profile_write_service.py` | domains/suppliers/services/supplier_profile_write_service.py |  |  |  |  |
| 420 | `backend/services/supplier/supplier_service.py` | domains/suppliers/services/supplier_service.py |  |  |  |  |
| 421 | `backend/services/supplier/supplier_supplier_sync_service.py` | domains/suppliers/services/supplier_supplier_sync_service.py |  |  |  |  |
| 422 | `backend/services/supplier/supplier_supplier_upload_service.py` | domains/suppliers/services/supplier_supplier_upload_service.py |  |  |  |  |
| 423 | `backend/services/supplier/suppliers_service.py` | domains/suppliers/services/suppliers_service.py |  |  |  |  |
| 424 | `backend/services/supplier/suppliers_write_service.py` | domains/suppliers/services/suppliers_write_service.py |  |  |  |  |
| 425 | `backend/services/suppliers/admin_supplier_review_service.py` | domains/suppliers/services/admin_supplier_review_service.py |  |  |  |  |
| 426 | `backend/services/system/ai_upload_service.py` | domains/media/services/ai_upload_service.py |  |  |  |  |
| 427 | `backend/services/system/system_ai_country_research_service.py` | domains/media/services/system_ai_country_research_service.py |  |  |  |  |
| 428 | `backend/services/system/system_ai_messaging_service.py` | domains/media/services/system_ai_messaging_service.py |  |  |  |  |
| 429 | `backend/services/system/system_ai_upload_service.py` | domains/media/services/system_ai_upload_service.py |  |  |  |  |
| 430 | `backend/services/treasury/admin_reporting_service.py` | domains/finance/services/admin_reporting_service.py |  |  |  |  |
| 431 | `backend/services/treasury/admin_treasury_read_service.py` | domains/finance/services/admin_treasury_read_service.py |  |  |  |  |
| 432 | `backend/services/treasury/admin_treasury_write_service.py` | domains/finance/services/admin_treasury_write_service.py |  |  |  |  |
| 433 | `backend/services/treasury/auto_payout_scheduler.py` | domains/finance/services/auto_payout_scheduler.py |  |  |  |  |
| 434 | `backend/services/treasury/bank_transaction_service.py` | domains/finance/services/bank_transaction_service.py |  |  |  |  |
| 435 | `backend/services/treasury/cash_flow_forecast_service.py` | domains/finance/services/cash_flow_forecast_service.py |  |  |  |  |
| 436 | `backend/services/treasury/cash_management_controller_service.py` | domains/finance/services/cash_management_controller_service.py |  |  |  |  |
| 437 | `backend/services/treasury/cash_management_service.py` | domains/finance/services/cash_management_service.py |  |  |  |  |
| 438 | `backend/services/treasury/cash_read_service.py` | domains/finance/services/cash_read_service.py |  |  |  |  |
| 439 | `backend/services/treasury/cash_write_service.py` | domains/finance/services/cash_write_service.py |  |  |  |  |
| 440 | `backend/services/treasury/payment_engine.py` | domains/finance/services/payment_engine.py |  |  |  |  |
| 441 | `backend/services/treasury/payment_orchestrator.py` | domains/finance/services/payment_orchestrator.py |  |  |  |  |
| 442 | `backend/services/treasury/payout_admin_service.py` | domains/finance/services/payout_admin_service.py |  |  |  |  |
| 443 | `backend/services/treasury/payout_approval_read_service.py` | domains/finance/services/payout_approval_read_service.py |  |  |  |  |
| 444 | `backend/services/treasury/payout_approval_write_service.py` | domains/finance/services/payout_approval_write_service.py |  |  |  |  |
| 445 | `backend/services/treasury/payout_batch_service.py` | domains/finance/services/payout_batch_service.py |  |  |  |  |
| 446 | `backend/services/treasury/payout_dispatch_service.py` | domains/finance/services/payout_dispatch_service.py |  |  |  |  |
| 447 | `backend/services/treasury/payout_engine.py` | domains/finance/services/payout_engine.py |  |  |  |  |
| 448 | `backend/services/treasury/payout_read_service.py` | domains/finance/services/payout_read_service.py |  |  |  |  |
| 449 | `backend/services/treasury/payout_status_service.py` | domains/finance/services/payout_status_service.py |  |  |  |  |
| 450 | `backend/services/treasury/reporting_service.py` | domains/finance/services/reporting_service.py |  |  |  |  |
| 451 | `backend/services/treasury/treasurer.py` | domains/finance/services/treasurer.py |  |  |  |  |
| 452 | `backend/services/treasury/treasury_adapter.py` | domains/finance/services/treasury_adapter.py |  |  |  |  |
| 453 | `backend/services/treasury/treasury_engine.py` | domains/finance/services/treasury_engine.py |  |  |  |  |
| 454 | `backend/services/treasury/treasury_query_service.py` | domains/finance/services/treasury_query_service.py |  |  |  |  |
| 455 | `backend/services/treasury/treasury_router_service.py` | domains/finance/services/treasury_router_service.py |  |  |  |  |
| 456 | `backend/services/treasury/treasury_service.py` | domains/finance/services/treasury_service.py |  |  |  |  |
| 457 | `backend/services/users/approval_matrix_service.py` | domains/accounts/services/approval_matrix_service.py |  |  |  |  |
| 458 | `backend/services/users/identity_admin_service.py` | domains/accounts/services/identity_admin_service.py |  |  |  |  |
| 459 | `backend/services/users/identity_service.py` | domains/accounts/services/identity_service.py |  |  |  |  |
| 460 | `backend/services/users/rbac_service.py` | domains/accounts/services/rbac_service.py |  |  |  |  |
| 461 | `backend/services/users/user_write_ops.py` | domains/accounts/services/user_write_ops.py |  |  |  |  |
| 462 | `backend/services/users/users_write_service.py` | domains/accounts/services/users_write_service.py |  |  |  |  |
| 463 | `backend/services/users/workflow_engine.py` | domains/accounts/services/workflow_engine.py |  |  |  |  |

**Column totals:** domains=396 modules=0 infrastructure=35 rbac=32 kernel=0

### NEEDS MANUAL REVIEW (5)
- `backend/services/core/chatbot_service.py` -> `domains/UNMAPPED/services/chatbot_service.py`
- `backend/services/core/export_read_service.py` -> `domains/UNMAPPED/services/export_read_service.py`
- `backend/services/core/export_service.py` -> `domains/UNMAPPED/services/export_service.py`
- `backend/services/core/search_service.py` -> `domains/UNMAPPED/services/search_service.py`
- `backend/services/core/user_read_service.py` -> `domains/UNMAPPED/services/user_read_service.py`

---

## 3. CURRENT backend/modules/* (VIOLATING - rehome to correct axis)

| sno | source | domains | modules | infrastructure | rbac | kernel |
|---|---|---|---|---|---|---|
| 1 | `backend/modules/admin/routers/admin_catalog_operations_controller.py` |  | modules/admin/routers/admin_catalog_operations_controller.py |  |  |  |
| 2 | `backend/modules/admin/routers/admin_catalog_orders_controller.py` |  | modules/admin/routers/admin_catalog_orders_controller.py |  |  |  |
| 3 | `backend/modules/admin/routers/admin_commerce_configuration_controller.py` |  | modules/admin/routers/admin_commerce_configuration_controller.py |  |  |  |
| 4 | `backend/modules/admin/routers/admin_commerce_geography_controller.py` |  | modules/admin/routers/admin_commerce_geography_controller.py |  |  |  |
| 5 | `backend/modules/admin/routers/admin_comms_geography_controller.py` |  | modules/admin/routers/admin_comms_geography_controller.py |  |  |  |
| 6 | `backend/modules/admin/routers/admin_comms_messaging_controller.py` |  | modules/admin/routers/admin_comms_messaging_controller.py |  |  |  |
| 7 | `backend/modules/admin/routers/admin_comms_unified_controller.py` |  | modules/admin/routers/admin_comms_unified_controller.py |  |  |  |
| 8 | `backend/modules/admin/routers/admin_controller.py` |  | modules/admin/routers/admin_controller.py |  |  |  |
| 9 | `backend/modules/admin/routers/admin_dashboard_controller.py` |  | modules/admin/routers/admin_dashboard_controller.py |  |  |  |
| 10 | `backend/modules/admin/routers/admin_finance_geography_controller.py` |  | modules/admin/routers/admin_finance_geography_controller.py |  |  |  |
| 11 | `backend/modules/admin/routers/admin_geography_audit_controller.py` |  | modules/admin/routers/admin_geography_audit_controller.py |  |  |  |
| 12 | `backend/modules/admin/routers/admin_geography_configuration_controller.py` |  | modules/admin/routers/admin_geography_configuration_controller.py |  |  |  |
| 13 | `backend/modules/admin/routers/admin_identity_operations_api_controller.py` |  | modules/admin/routers/admin_identity_operations_api_controller.py |  |  |  |
| 14 | `backend/modules/admin/routers/admin_identity_operations_controller.py` |  | modules/admin/routers/admin_identity_operations_controller.py |  |  |  |
| 15 | `backend/modules/admin/routers/admin_logistics_geography_controller.py` |  | modules/admin/routers/admin_logistics_geography_controller.py |  |  |  |
| 16 | `backend/modules/admin/routers/admin_logistics_operations_controller.py` |  | modules/admin/routers/admin_logistics_operations_controller.py |  |  |  |
| 17 | `backend/modules/admin/routers/admin_media_geography_controller.py` |  | modules/admin/routers/admin_media_geography_controller.py |  |  |  |
| 18 | `backend/modules/admin/routers/admin_orders_status_controller.py` |  | modules/admin/routers/admin_orders_status_controller.py |  |  |  |
| 19 | `backend/modules/admin/routers/admin_permissions_validation_controller.py` |  | modules/admin/routers/admin_permissions_validation_controller.py |  |  |  |
| 20 | `backend/modules/admin/routers/admin_security_detection_controller.py` |  | modules/admin/routers/admin_security_detection_controller.py |  |  |  |
| 21 | `backend/modules/admin/routers/admin_security_operations_controller.py` |  | modules/admin/routers/admin_security_operations_controller.py |  |  |  |
| 22 | `backend/modules/admin/routers/admin_security_registration_controller.py` |  | modules/admin/routers/admin_security_registration_controller.py |  |  |  |
| 23 | `backend/modules/admin/routers/admin_supplier_reviews_controller.py` |  | modules/admin/routers/admin_supplier_reviews_controller.py |  |  |  |
| 24 | `backend/modules/admin/routers/admin_supplier_trading_controller.py` |  | modules/admin/routers/admin_supplier_trading_controller.py |  |  |  |
| 25 | `backend/modules/admin/routers/admin_treasury_identity_controller.py` |  | modules/admin/routers/admin_treasury_identity_controller.py |  |  |  |
| 26 | `backend/modules/admin/routers/admin_treasury_payments_controller.py` |  | modules/admin/routers/admin_treasury_payments_controller.py |  |  |  |
| 27 | `backend/modules/admin/routers/admin_treasury_reporting_controller.py` |  | modules/admin/routers/admin_treasury_reporting_controller.py |  |  |  |
| 28 | `backend/modules/admin/routers/admin_treasury_status_controller.py` |  | modules/admin/routers/admin_treasury_status_controller.py |  |  |  |
| 29 | `backend/modules/admin/routers/analytics_controller.py` |  | modules/admin/routers/analytics_controller.py |  |  |  |
| 30 | `backend/modules/admin/routers/analytics_dashboard_controller.py` |  | modules/admin/routers/analytics_dashboard_controller.py |  |  |  |
| 31 | `backend/modules/admin/routers/analytics_fallback_controller.py` |  | modules/admin/routers/analytics_fallback_controller.py |  |  |  |
| 32 | `backend/modules/admin/routers/audit_controller.py` |  | modules/admin/routers/audit_controller.py |  |  |  |
| 33 | `backend/modules/admin/routers/auth.py` |  | modules/admin/routers/auth.py |  |  |  |
| 34 | `backend/modules/admin/routers/bank_accounts_controller.py` |  | modules/admin/routers/bank_accounts_controller.py |  |  |  |
| 35 | `backend/modules/admin/routers/coupons_controller.py` |  | modules/admin/routers/coupons_controller.py |  |  |  |
| 36 | `backend/modules/admin/routers/misc_controller.py` |  | modules/admin/routers/misc_controller.py |  |  |  |
| 37 | `backend/modules/admin/routers/orders_controller.py` |  | modules/admin/routers/orders_controller.py |  |  |  |
| 38 | `backend/modules/admin/routers/payouts_controller.py` |  | modules/admin/routers/payouts_controller.py |  |  |  |
| 39 | `backend/modules/admin/routers/permissions_controller.py` |  | modules/admin/routers/permissions_controller.py |  |  |  |
| 40 | `backend/modules/admin/routers/products_controller.py` |  | modules/admin/routers/products_controller.py |  |  |  |
| 41 | `backend/modules/admin/routers/suppliers_controller.py` |  | modules/admin/routers/suppliers_controller.py |  |  |  |
| 42 | `backend/modules/admin/routers/tickets_controller.py` |  | modules/admin/routers/tickets_controller.py |  |  |  |
| 43 | `backend/modules/admin/routers/users_admin_controller.py` |  | modules/admin/routers/users_admin_controller.py |  |  |  |
| 44 | `backend/modules/catalog/routers/category_admin_controller.py` | domains/catalog/services/category_admin_controller.py |  |  |  |  |
| 45 | `backend/modules/commerce/routers/cart_controller.py` | domains/orders/services/cart_controller.py |  |  |  |  |
| 46 | `backend/modules/commerce/routers/coupons_controller.py` | domains/orders/services/coupons_controller.py |  |  |  |  |
| 47 | `backend/modules/commerce/routers/flash_sale_controller.py` | domains/orders/services/flash_sale_controller.py |  |  |  |  |
| 48 | `backend/modules/commerce/routers/promotion_admin_controller.py` | domains/orders/services/promotion_admin_controller.py |  |  |  |  |
| 49 | `backend/modules/commerce/routers/promotion_controller.py` | domains/orders/services/promotion_controller.py |  |  |  |  |
| 50 | `backend/modules/commerce/routers/referrals_controller.py` | domains/orders/services/referrals_controller.py |  |  |  |  |
| 51 | `backend/modules/commerce/routers/reviews_controller.py` | domains/orders/services/reviews_controller.py |  |  |  |  |
| 52 | `backend/modules/commerce/routers/wishlist_controller.py` | domains/orders/services/wishlist_controller.py |  |  |  |  |
| 53 | `backend/modules/comms/routers/chat_write_controller.py` | domains/comms/services/chat_write_controller.py |  |  |  |  |
| 54 | `backend/modules/comms/routers/chatbot_controller.py` | domains/comms/services/chatbot_controller.py |  |  |  |  |
| 55 | `backend/modules/comms/routers/comm_controller.py` | domains/comms/services/comm_controller.py |  |  |  |  |
| 56 | `backend/modules/comms/routers/communication_audit_controller.py` | domains/comms/services/communication_audit_controller.py |  |  |  |  |
| 57 | `backend/modules/comms/routers/notification_controller.py` | domains/comms/services/notification_controller.py |  |  |  |  |
| 58 | `backend/modules/core/routers/addresses_controller.py` |  | modules/admin/routers/addresses_controller.py |  |  |  |
| 59 | `backend/modules/core/routers/admin_banners_controller.py` |  | modules/admin/routers/admin_banners_controller.py |  |  |  |
| 60 | `backend/modules/core/routers/admin_cash_controller.py` |  | modules/admin/routers/admin_cash_controller.py |  |  |  |
| 61 | `backend/modules/core/routers/admin_categories_controller.py` |  | modules/admin/routers/admin_categories_controller.py |  |  |  |
| 62 | `backend/modules/core/routers/admin_chat_controller.py` |  | modules/admin/routers/admin_chat_controller.py |  |  |  |
| 63 | `backend/modules/core/routers/admin_commission_controller.py` |  | modules/admin/routers/admin_commission_controller.py |  |  |  |
| 64 | `backend/modules/core/routers/admin_controller.py` |  | modules/admin/routers/admin_controller.py |  |  |  |
| 65 | `backend/modules/core/routers/admin_email_controller.py` |  | modules/admin/routers/admin_email_controller.py |  |  |  |
| 66 | `backend/modules/core/routers/admin_logistics_controller.py` |  | modules/admin/routers/admin_logistics_controller.py |  |  |  |
| 67 | `backend/modules/core/routers/admin_orders_controller.py` |  | modules/admin/routers/admin_orders_controller.py |  |  |  |
| 68 | `backend/modules/core/routers/admin_payouts_controller.py` |  | modules/admin/routers/admin_payouts_controller.py |  |  |  |
| 69 | `backend/modules/core/routers/admin_products_controller.py` |  | modules/admin/routers/admin_products_controller.py |  |  |  |
| 70 | `backend/modules/core/routers/admin_promotions_controller.py` |  | modules/admin/routers/admin_promotions_controller.py |  |  |  |
| 71 | `backend/modules/core/routers/admin_suppliers_controller.py` |  | modules/admin/routers/admin_suppliers_controller.py |  |  |  |
| 72 | `backend/modules/core/routers/admin_treasury_controller.py` |  | modules/admin/routers/admin_treasury_controller.py |  |  |  |
| 73 | `backend/modules/core/routers/admin_users_controller.py` |  | modules/admin/routers/admin_users_controller.py |  |  |  |
| 74 | `backend/modules/core/routers/admin_video_controller.py` |  | modules/admin/routers/admin_video_controller.py |  |  |  |
| 75 | `backend/modules/core/routers/ai_controller.py` |  | modules/admin/routers/ai_controller.py |  |  |  |
| 76 | `backend/modules/core/routers/ai_upload_controller.py` |  | modules/admin/routers/ai_upload_controller.py |  |  |  |
| 77 | `backend/modules/core/routers/auth_controller.py` |  | modules/admin/routers/auth_controller.py |  |  |  |
| 78 | `backend/modules/core/routers/banners_controller.py` |  | modules/admin/routers/banners_controller.py |  |  |  |
| 79 | `backend/modules/core/routers/cart_controller.py` |  | modules/admin/routers/cart_controller.py |  |  |  |
| 80 | `backend/modules/core/routers/cash_management_controller.py` |  | modules/admin/routers/cash_management_controller.py |  |  |  |
| 81 | `backend/modules/core/routers/categories_controller.py` |  | modules/admin/routers/categories_controller.py |  |  |  |
| 82 | `backend/modules/core/routers/chat_enrichment_controller.py` |  | modules/admin/routers/chat_enrichment_controller.py |  |  |  |
| 83 | `backend/modules/core/routers/commission_controller.py` |  | modules/admin/routers/commission_controller.py |  |  |  |
| 84 | `backend/modules/core/routers/comms_unified_controller.py` |  | modules/admin/routers/comms_unified_controller.py |  |  |  |
| 85 | `backend/modules/core/routers/countries_controller.py` |  | modules/admin/routers/countries_controller.py |  |  |  |
| 86 | `backend/modules/core/routers/country_admin_controller.py` |  | modules/admin/routers/country_admin_controller.py |  |  |  |
| 87 | `backend/modules/core/routers/country_dropdown_controller.py` |  | modules/admin/routers/country_dropdown_controller.py |  |  |  |
| 88 | `backend/modules/core/routers/country_maps_controller.py` |  | modules/admin/routers/country_maps_controller.py |  |  |  |
| 89 | `backend/modules/core/routers/country_payouts_controller.py` |  | modules/admin/routers/country_payouts_controller.py |  |  |  |
| 90 | `backend/modules/core/routers/country_staff_controller.py` |  | modules/admin/routers/country_staff_controller.py |  |  |  |
| 91 | `backend/modules/core/routers/coupons_controller.py` |  | modules/admin/routers/coupons_controller.py |  |  |  |
| 92 | `backend/modules/core/routers/customer_health_controller.py` |  | modules/admin/routers/customer_health_controller.py |  |  |  |
| 93 | `backend/modules/core/routers/email_controller.py` |  | modules/admin/routers/email_controller.py |  |  |  |
| 94 | `backend/modules/core/routers/employees_controller.py` |  | modules/admin/routers/employees_controller.py |  |  |  |
| 95 | `backend/modules/core/routers/ess_controller.py` |  | modules/admin/routers/ess_controller.py |  |  |  |
| 96 | `backend/modules/core/routers/export_controller.py` |  | modules/admin/routers/export_controller.py |  |  |  |
| 97 | `backend/modules/core/routers/geo_controller.py` |  | modules/admin/routers/geo_controller.py |  |  |  |
| 98 | `backend/modules/core/routers/hierarchy_controller.py` |  | modules/admin/routers/hierarchy_controller.py |  |  |  |
| 99 | `backend/modules/core/routers/hr_controller.py` |  | modules/admin/routers/hr_controller.py |  |  |  |
| 100 | `backend/modules/core/routers/incident_controller.py` |  | modules/admin/routers/incident_controller.py |  |  |  |
| 101 | `backend/modules/core/routers/internal_channels_controller.py` |  | modules/admin/routers/internal_channels_controller.py |  |  |  |
| 102 | `backend/modules/core/routers/logistics_controller.py` |  | modules/admin/routers/logistics_controller.py |  |  |  |
| 103 | `backend/modules/core/routers/logistics_health_controller.py` |  | modules/admin/routers/logistics_health_controller.py |  |  |  |
| 104 | `backend/modules/core/routers/logistics_locations_controller.py` |  | modules/admin/routers/logistics_locations_controller.py |  |  |  |
| 105 | `backend/modules/core/routers/logistics_partner_controller.py` |  | modules/admin/routers/logistics_partner_controller.py |  |  |  |
| 106 | `backend/modules/core/routers/payroll_controller.py` |  | modules/admin/routers/payroll_controller.py |  |  |  |
| 107 | `backend/modules/core/routers/performance_controller.py` |  | modules/admin/routers/performance_controller.py |  |  |  |
| 108 | `backend/modules/core/routers/permissions_controller.py` |  | modules/admin/routers/permissions_controller.py |  |  |  |
| 109 | `backend/modules/core/routers/referrals_controller.py` |  | modules/admin/routers/referrals_controller.py |  |  |  |
| 110 | `backend/modules/core/routers/returns_controller.py` |  | modules/admin/routers/returns_controller.py |  |  |  |
| 111 | `backend/modules/core/routers/reviews_controller.py` |  | modules/admin/routers/reviews_controller.py |  |  |  |
| 112 | `backend/modules/core/routers/shipments_controller.py` |  | modules/admin/routers/shipments_controller.py |  |  |  |
| 113 | `backend/modules/core/routers/supplier_documents_controller.py` |  | modules/admin/routers/supplier_documents_controller.py |  |  |  |
| 114 | `backend/modules/core/routers/supplier_finance_controller.py` |  | modules/admin/routers/supplier_finance_controller.py |  |  |  |
| 115 | `backend/modules/core/routers/supplier_health_controller.py` |  | modules/admin/routers/supplier_health_controller.py |  |  |  |
| 116 | `backend/modules/core/routers/supplier_orders_controller.py` |  | modules/admin/routers/supplier_orders_controller.py |  |  |  |
| 117 | `backend/modules/core/routers/supplier_payouts_controller.py` |  | modules/admin/routers/supplier_payouts_controller.py |  |  |  |
| 118 | `backend/modules/core/routers/supplier_products_controller.py` |  | modules/admin/routers/supplier_products_controller.py |  |  |  |
| 119 | `backend/modules/core/routers/supplier_profile_controller.py` |  | modules/admin/routers/supplier_profile_controller.py |  |  |  |
| 120 | `backend/modules/core/routers/tickets_controller.py` |  | modules/admin/routers/tickets_controller.py |  |  |  |
| 121 | `backend/modules/core/routers/translate_controller.py` |  | modules/admin/routers/translate_controller.py |  |  |  |
| 122 | `backend/modules/core/routers/users_controller.py` |  | modules/admin/routers/users_controller.py |  |  |  |
| 123 | `backend/modules/core/routers/wishlist_controller.py` |  | modules/admin/routers/wishlist_controller.py |  |  |  |
| 124 | `backend/modules/customer/routers/users.py` |  | modules/customer/routers/users.py |  |  |  |
| 125 | `backend/modules/employee/routers/employees_controller.py` |  | modules/employee/routers/employees_controller.py |  |  |  |
| 126 | `backend/modules/employee/routers/hierarchy_controller.py` |  | modules/employee/routers/hierarchy_controller.py |  |  |  |
| 127 | `backend/modules/employee/routers/hr_controller.py` |  | modules/employee/routers/hr_controller.py |  |  |  |
| 128 | `backend/modules/employee/routers/lms_controller.py` |  | modules/employee/routers/lms_controller.py |  |  |  |
| 129 | `backend/modules/employee/routers/okr_controller.py` |  | modules/employee/routers/okr_controller.py |  |  |  |
| 130 | `backend/modules/employee/routers/succession_controller.py` |  | modules/employee/routers/succession_controller.py |  |  |  |
| 131 | `backend/modules/finance/routers/accounting_controller.py` | domains/finance/services/accounting_controller.py |  |  |  |  |
| 132 | `backend/modules/finance/routers/commission_controller.py` | domains/finance/services/commission_controller.py |  |  |  |  |
| 133 | `backend/modules/finance/routers/finance_controller.py` | domains/finance/services/finance_controller.py |  |  |  |  |
| 134 | `backend/modules/finance/routers/invoice_controller.py` | domains/finance/services/invoice_controller.py |  |  |  |  |
| 135 | `backend/modules/finance/routers/sub_ledger_controller.py` | domains/finance/services/sub_ledger_controller.py |  |  |  |  |
| 136 | `backend/modules/hr/routers/employees_controller.py` | domains/hr/services/employees_controller.py |  |  |  |  |
| 137 | `backend/modules/hr/routers/hierarchy_controller.py` | domains/hr/services/hierarchy_controller.py |  |  |  |  |
| 138 | `backend/modules/hr/routers/hr_controller.py` | domains/hr/services/hr_controller.py |  |  |  |  |
| 139 | `backend/modules/hr/routers/lms_controller.py` | domains/hr/services/lms_controller.py |  |  |  |  |
| 140 | `backend/modules/hr/routers/okr_controller.py` | domains/hr/services/okr_controller.py |  |  |  |  |
| 141 | `backend/modules/hr/routers/succession_controller.py` | domains/hr/services/succession_controller.py |  |  |  |  |
| 142 | `backend/modules/logistics/routers/logistics_health_list_controller.py` |  | modules/logistics/routers/logistics_health_list_controller.py |  |  |  |
| 143 | `backend/modules/logistics/routers/logistics_locations_create_controller.py` |  | modules/logistics/routers/logistics_locations_create_controller.py |  |  |  |
| 144 | `backend/modules/logistics/routers/logistics_logistics_status_controller.py` |  | modules/logistics/routers/logistics_logistics_status_controller.py |  |  |  |
| 145 | `backend/modules/logistics/routers/logistics_orders_list_controller.py` |  | modules/logistics/routers/logistics_orders_list_controller.py |  |  |  |
| 146 | `backend/modules/logistics/routers/logistics_orders_v2_controller.py` |  | modules/logistics/routers/logistics_orders_v2_controller.py |  |  |  |
| 147 | `backend/modules/logistics/routers/logistics_partner_verify_controller.py` |  | modules/logistics/routers/logistics_partner_verify_controller.py |  |  |  |
| 148 | `backend/modules/orders/routers/disputes_controller.py` | domains/orders/services/disputes_controller.py |  |  |  |  |
| 149 | `backend/modules/orders/routers/logistics_controller.py` | domains/orders/services/logistics_controller.py |  |  |  |  |
| 150 | `backend/modules/orders/routers/logistics_partner_controller.py` | domains/orders/services/logistics_partner_controller.py |  |  |  |  |
| 151 | `backend/modules/orders/routers/orders_controller.py` | domains/orders/services/orders_controller.py |  |  |  |  |
| 152 | `backend/modules/orders/routers/returns_controller.py` | domains/orders/services/returns_controller.py |  |  |  |  |
| 153 | `backend/modules/products/routers/products_controller.py` | domains/catalog/services/products_controller.py |  |  |  |  |
| 154 | `backend/modules/public/routers/admin_promotions_routes_controller.py` |  | modules/admin/routers/admin_promotions_routes_controller.py |  |  |  |
| 155 | `backend/modules/public/routers/customer_coupons_create_controller.py` |  | modules/admin/routers/customer_coupons_create_controller.py |  |  |  |
| 156 | `backend/modules/public/routers/customer_coupons_mgmt_controller.py` |  | modules/admin/routers/customer_coupons_mgmt_controller.py |  |  |  |
| 157 | `backend/modules/public/routers/customer_health_list_controller.py` |  | modules/admin/routers/customer_health_list_controller.py |  |  |  |
| 158 | `backend/modules/public/routers/internal_comms_channels_controller.py` |  | modules/admin/routers/internal_comms_channels_controller.py |  |  |  |
| 159 | `backend/modules/public/routers/public_commerce_validation_controller.py` |  | modules/admin/routers/public_commerce_validation_controller.py |  |  |  |
| 160 | `backend/modules/public/routers/public_comms_unified_controller.py` |  | modules/admin/routers/public_comms_unified_controller.py |  |  |  |
| 161 | `backend/modules/public/routers/public_geography_configuration_controller.py` |  | modules/admin/routers/public_geography_configuration_controller.py |  |  |  |
| 162 | `backend/modules/public/routers/public_identity_operations_controller.py` |  | modules/admin/routers/public_identity_operations_controller.py |  |  |  |
| 163 | `backend/modules/public/routers/public_permissions_validation_controller.py` |  | modules/admin/routers/public_permissions_validation_controller.py |  |  |  |
| 164 | `backend/modules/public/routers/public_security_detection_controller.py` |  | modules/admin/routers/public_security_detection_controller.py |  |  |  |
| 165 | `backend/modules/public/routers/public_security_operations_controller.py` |  | modules/admin/routers/public_security_operations_controller.py |  |  |  |
| 166 | `backend/modules/public/routers/public_security_registration_controller.py` |  | modules/admin/routers/public_security_registration_controller.py |  |  |  |
| 167 | `backend/modules/public/routers/public_treasury_payments_controller.py` |  | modules/admin/routers/public_treasury_payments_controller.py |  |  |  |
| 168 | `backend/modules/public/routers/system_ai_upload_controller.py` |  | modules/admin/routers/system_ai_upload_controller.py |  |  |  |
| 169 | `backend/modules/public/routers/system_comms_status_controller.py` |  | modules/admin/routers/system_comms_status_controller.py |  |  |  |
| 170 | `backend/modules/routers/accounting.py` |  | modules/employee/routers/accounting.py|  |  |  |
| 171 | `backend/modules/routers/addresses.py` |  | modules/customer/routers/addresses.py|  |  |  |
| 172 | `backend/modules/routers/admin.py` |  | modules/admin/routers/admin.py|  |  |  |
| 173 | `backend/modules/routers/admin_admin_analytics.py` |  | modules/admin/routers/admin_admin_analytics.py|  |  |  |
| 174 | `backend/modules/routers/admin_admin_audit.py` |  | modules/admin/routers/admin_admin_audit.py|  |  |  |
| 175 | `backend/modules/routers/admin_admin_bank_accounts.py` |  | modules/admin/routers/admin_admin_bank_accounts.py|  |  |  |
| 176 | `backend/modules/routers/admin_admin_coupons.py` |  | modules/admin/routers/admin_admin_coupons.py|  |  |  |
| 177 | `backend/modules/routers/admin_admin_misc.py` |  | modules/admin/routers/admin_admin_misc.py|  |  |  |
| 178 | `backend/modules/routers/admin_admin_orders.py` |  | modules/admin/routers/admin_admin_orders.py|  |  |  |
| 179 | `backend/modules/routers/admin_admin_permissions.py` |  | modules/admin/routers/admin_admin_permissions.py|  |  |  |
| 180 | `backend/modules/routers/admin_admin_products.py` |  | modules/admin/routers/admin_admin_products.py|  |  |  |
| 181 | `backend/modules/routers/admin_admin_suppliers.py` |  | modules/admin/routers/admin_admin_suppliers.py|  |  |  |
| 182 | `backend/modules/routers/admin_admin_tickets.py` |  | modules/admin/routers/admin_admin_tickets.py|  |  |  |
| 183 | `backend/modules/routers/admin_admin_users_admin.py` |  | modules/admin/routers/admin_admin_users_admin.py|  |  |  |
| 184 | `backend/modules/routers/admin_analytics.py` |  | modules/admin/routers/admin_analytics.py|  |  |  |
| 185 | `backend/modules/routers/admin_analytics_dashboard.py` |  | modules/admin/routers/admin_analytics_dashboard.py|  |  |  |
| 186 | `backend/modules/routers/admin_analytics_fallback_dashboard.py` |  | modules/admin/routers/admin_analytics_fallback_dashboard.py|  |  |  |
| 187 | `backend/modules/routers/admin_analytics_routes.py` |  | modules/admin/routers/admin_analytics_routes.py|  |  |  |
| 188 | `backend/modules/routers/admin_audit.py` |  | modules/admin/routers/admin_audit.py|  |  |  |
| 189 | `backend/modules/routers/admin_bank_accounts.py` |  | modules/admin/routers/admin_bank_accounts.py|  |  |  |
| 190 | `backend/modules/routers/admin_banners.py` |  | modules/admin/routers/admin_banners.py|  |  |  |
| 191 | `backend/modules/routers/admin_banners_routes.py` |  | modules/admin/routers/admin_banners_routes.py|  |  |  |
| 192 | `backend/modules/routers/admin_cash.py` |  | modules/admin/routers/admin_cash.py|  |  |  |
| 193 | `backend/modules/routers/admin_cash_routes.py` |  | modules/admin/routers/admin_cash_routes.py|  |  |  |
| 194 | `backend/modules/routers/admin_catalog_category_admin.py` |  | modules/admin/routers/admin_catalog_category_admin.py|  |  |  |
| 195 | `backend/modules/routers/admin_catalog_operations.py` |  | modules/admin/routers/admin_catalog_operations.py|  |  |  |
| 196 | `backend/modules/routers/admin_catalog_orders.py` |  | modules/admin/routers/admin_catalog_orders.py|  |  |  |
| 197 | `backend/modules/routers/admin_categories.py` |  | modules/admin/routers/admin_categories.py|  |  |  |
| 198 | `backend/modules/routers/admin_categories_routes.py` |  | modules/admin/routers/admin_categories_routes.py|  |  |  |
| 199 | `backend/modules/routers/admin_chat.py` |  | modules/admin/routers/admin_chat.py|  |  |  |
| 200 | `backend/modules/routers/admin_chat_routes.py` |  | modules/admin/routers/admin_chat_routes.py|  |  |  |
| 201 | `backend/modules/routers/admin_commerce_configuration.py` |  | modules/admin/routers/admin_commerce_configuration.py|  |  |  |
| 202 | `backend/modules/routers/admin_commerce_geography.py` |  | modules/admin/routers/admin_commerce_geography.py|  |  |  |
| 203 | `backend/modules/routers/admin_commerce_promotion_admin.py` |  | modules/admin/routers/admin_commerce_promotion_admin.py|  |  |  |
| 204 | `backend/modules/routers/admin_commission.py` |  | modules/admin/routers/admin_commission.py|  |  |  |
| 205 | `backend/modules/routers/admin_commission_routes.py` |  | modules/admin/routers/admin_commission_routes.py|  |  |  |
| 206 | `backend/modules/routers/admin_comms_geography.py` |  | modules/admin/routers/admin_comms_geography.py|  |  |  |
| 207 | `backend/modules/routers/admin_comms_messaging.py` |  | modules/admin/routers/admin_comms_messaging.py|  |  |  |
| 208 | `backend/modules/routers/admin_comms_unified.py` |  | modules/admin/routers/admin_comms_unified.py|  |  |  |
| 209 | `backend/modules/routers/admin_configuration_operations.py` |  | modules/admin/routers/admin_configuration_operations.py|  |  |  |
| 210 | `backend/modules/routers/admin_core_routes.py` |  | modules/admin/routers/admin_core_routes.py|  |  |  |
| 211 | `backend/modules/routers/admin_coupons.py` |  | modules/admin/routers/admin_coupons.py|  |  |  |
| 212 | `backend/modules/routers/admin_email.py` |  | modules/admin/routers/admin_email.py|  |  |  |
| 213 | `backend/modules/routers/admin_email_routes.py` |  | modules/admin/routers/admin_email_routes.py|  |  |  |
| 214 | `backend/modules/routers/admin_fallback.py` |  | modules/admin/routers/admin_fallback.py|  |  |  |
| 215 | `backend/modules/routers/admin_fallback_routes.py` |  | modules/admin/routers/admin_fallback_routes.py|  |  |  |
| 216 | `backend/modules/routers/admin_finance_creation.py` |  | modules/admin/routers/admin_finance_creation.py|  |  |  |
| 217 | `backend/modules/routers/admin_finance_geography.py` |  | modules/admin/routers/admin_finance_geography.py|  |  |  |
| 218 | `backend/modules/routers/admin_finance_sub_ledger.py` |  | modules/admin/routers/admin_finance_sub_ledger.py|  |  |  |
| 219 | `backend/modules/routers/admin_geography_audit.py` |  | modules/admin/routers/admin_geography_audit.py|  |  |  |
| 220 | `backend/modules/routers/admin_geography_configuration.py` |  | modules/admin/routers/admin_geography_configuration.py|  |  |  |
| 221 | `backend/modules/routers/admin_geography_country_versioning.py` |  | modules/admin/routers/admin_geography_country_versioning.py|  |  |  |
| 222 | `backend/modules/routers/admin_governance_command_center.py` |  | modules/admin/routers/admin_governance_command_center.py|  |  |  |
| 223 | `backend/modules/routers/admin_identity_operations.py` |  | modules/admin/routers/admin_identity_operations.py|  |  |  |
| 224 | `backend/modules/routers/admin_identity_operations_api.py` |  | modules/admin/routers/admin_identity_operations_api.py|  |  |  |
| 225 | `backend/modules/routers/admin_logistics.py` |  | modules/admin/routers/admin_logistics.py|  |  |  |
| 226 | `backend/modules/routers/admin_logistics_fallback.py` |  | modules/admin/routers/admin_logistics_fallback.py|  |  |  |
| 227 | `backend/modules/routers/admin_logistics_geography.py` |  | modules/admin/routers/admin_logistics_geography.py|  |  |  |
| 228 | `backend/modules/routers/admin_logistics_imports.py` |  | modules/admin/routers/admin_logistics_imports.py|  |  |  |
| 229 | `backend/modules/routers/admin_logistics_operations.py` |  | modules/admin/routers/admin_logistics_operations.py|  |  |  |
| 230 | `backend/modules/routers/admin_logistics_routes.py` |  | modules/admin/routers/admin_logistics_routes.py|  |  |  |
| 231 | `backend/modules/routers/admin_media_geography.py` |  | modules/admin/routers/admin_media_geography.py|  |  |  |
| 232 | `backend/modules/routers/admin_misc.py` |  | modules/admin/routers/admin_misc.py|  |  |  |
| 233 | `backend/modules/routers/admin_orders.py` |  | modules/admin/routers/admin_orders.py|  |  |  |
| 234 | `backend/modules/routers/admin_orders_routes.py` |  | modules/admin/routers/admin_orders_routes.py|  |  |  |
| 235 | `backend/modules/routers/admin_orders_status.py` |  | modules/admin/routers/admin_orders_status.py|  |  |  |
| 236 | `backend/modules/routers/admin_payouts.py` |  | modules/admin/routers/admin_payouts.py|  |  |  |
| 237 | `backend/modules/routers/admin_payouts_routes.py` |  | modules/admin/routers/admin_payouts_routes.py|  |  |  |
| 238 | `backend/modules/routers/admin_permissions.py` |  | modules/admin/routers/admin_permissions.py|  |  |  |
| 239 | `backend/modules/routers/admin_permissions_validation.py` |  | modules/admin/routers/admin_permissions_validation.py|  |  |  |
| 240 | `backend/modules/routers/admin_products.py` |  | modules/admin/routers/admin_products.py|  |  |  |
| 241 | `backend/modules/routers/admin_products_routes.py` |  | modules/admin/routers/admin_products_routes.py|  |  |  |
| 242 | `backend/modules/routers/admin_promotions.py` |  | modules/admin/routers/admin_promotions.py|  |  |  |
| 243 | `backend/modules/routers/admin_promotions_routes.py` |  | modules/admin/routers/admin_promotions_routes.py|  |  |  |
| 244 | `backend/modules/routers/admin_security_detection.py` |  | modules/admin/routers/admin_security_detection.py|  |  |  |
| 245 | `backend/modules/routers/admin_security_health.py` |  | modules/admin/routers/admin_security_health.py|  |  |  |
| 246 | `backend/modules/routers/admin_security_operations.py` |  | modules/admin/routers/admin_security_operations.py|  |  |  |
| 247 | `backend/modules/routers/admin_security_registration.py` |  | modules/admin/routers/admin_security_registration.py|  |  |  |
| 248 | `backend/modules/routers/admin_security_risk.py` |  | modules/admin/routers/admin_security_risk.py|  |  |  |
| 249 | `backend/modules/routers/admin_settings.py` |  | modules/admin/routers/admin_settings.py|  |  |  |
| 250 | `backend/modules/routers/admin_settings_routes.py` |  | modules/admin/routers/admin_settings_routes.py|  |  |  |
| 251 | `backend/modules/routers/admin_supplier_reviews.py` |  | modules/admin/routers/admin_supplier_reviews.py|  |  |  |
| 252 | `backend/modules/routers/admin_supplier_trading.py` |  | modules/admin/routers/admin_supplier_trading.py|  |  |  |
| 253 | `backend/modules/routers/admin_suppliers.py` |  | modules/admin/routers/admin_suppliers.py|  |  |  |
| 254 | `backend/modules/routers/admin_suppliers_routes.py` |  | modules/admin/routers/admin_suppliers_routes.py|  |  |  |
| 255 | `backend/modules/routers/admin_tickets.py` |  | modules/admin/routers/admin_tickets.py|  |  |  |
| 256 | `backend/modules/routers/admin_treasury.py` |  | modules/admin/routers/admin_treasury.py|  |  |  |
| 257 | `backend/modules/routers/admin_treasury_cash_management_write.py` |  | modules/admin/routers/admin_treasury_cash_management_write.py|  |  |  |
| 258 | `backend/modules/routers/admin_treasury_cash_position.py` |  | modules/admin/routers/admin_treasury_cash_position.py|  |  |  |
| 259 | `backend/modules/routers/admin_treasury_identity.py` |  | modules/admin/routers/admin_treasury_identity.py|  |  |  |
| 260 | `backend/modules/routers/admin_treasury_payments.py` |  | modules/admin/routers/admin_treasury_payments.py|  |  |  |
| 261 | `backend/modules/routers/admin_treasury_payout_approval.py` |  | modules/admin/routers/admin_treasury_payout_approval.py|  |  |  |
| 262 | `backend/modules/routers/admin_treasury_reporting.py` |  | modules/admin/routers/admin_treasury_reporting.py|  |  |  |
| 263 | `backend/modules/routers/admin_treasury_routes.py` |  | modules/admin/routers/admin_treasury_routes.py|  |  |  |
| 264 | `backend/modules/routers/admin_treasury_status.py` |  | modules/admin/routers/admin_treasury_status.py|  |  |  |
| 265 | `backend/modules/routers/admin_users.py` |  | modules/admin/routers/admin_users.py|  |  |  |
| 266 | `backend/modules/routers/admin_users_admin.py` |  | modules/admin/routers/admin_users_admin.py|  |  |  |
| 267 | `backend/modules/routers/admin_users_routes.py` |  | modules/admin/routers/admin_users_routes.py|  |  |  |
| 268 | `backend/modules/routers/admin_video.py` |  | modules/admin/routers/admin_video.py|  |  |  |
| 269 | `backend/modules/routers/admin_video_routes.py` |  | modules/admin/routers/admin_video_routes.py|  |  |  |
| 270 | `backend/modules/routers/ai.py` |  | modules/admin/routers/ai.py|  |  |  |
| 271 | `backend/modules/routers/ai_image.py` |  | modules/admin/routers/ai_image.py|  |  |  |
| 272 | `backend/modules/routers/ai_research.py` |  | modules/admin/routers/ai_research.py|  |  |  |
| 273 | `backend/modules/routers/ai_upload.py` |  | modules/admin/routers/ai_upload.py|  |  |  |
| 274 | `backend/modules/routers/api_geography_location.py` |  | modules/admin/routers/api_geography_location.py|  |  |  |
| 275 | `backend/modules/routers/audit.py` |  | modules/admin/routers/audit.py|  |  |  |
| 276 | `backend/modules/routers/auth.py` |  | modules/admin/routers/auth.py|  |  |  |
| 277 | `backend/modules/routers/automation.py` |  | modules/admin/routers/automation.py|  |  |  |
| 278 | `backend/modules/routers/banners.py` |  | modules/admin/routers/banners.py|  |  |  |
| 279 | `backend/modules/routers/batch_upload.py` |  | modules/admin/routers/batch_upload.py|  |  |  |
| 280 | `backend/modules/routers/cart.py` |  | modules/customer/routers/cart.py|  |  |  |
| 281 | `backend/modules/routers/cash_management.py` |  | modules/employee/routers/cash_management.py|  |  |  |
| 282 | `backend/modules/routers/categories.py` |  | modules/admin/routers/categories.py|  |  |  |
| 283 | `backend/modules/routers/chat.py` |  | modules/employee/routers/chat.py|  |  |  |
| 284 | `backend/modules/routers/chat_api.py` |  | modules/employee/routers/chat_api.py|  |  |  |
| 285 | `backend/modules/routers/chat_enrichment.py` |  | modules/employee/routers/chat_enrichment.py|  |  |  |
| 286 | `backend/modules/routers/chatbot.py` |  | modules/employee/routers/chatbot.py|  |  |  |
| 287 | `backend/modules/routers/comm.py` |  | modules/employee/routers/comm.py|  |  |  |
| 288 | `backend/modules/routers/comm_ws.py` |  | modules/employee/routers/comm_ws.py|  |  |  |
| 289 | `backend/modules/routers/command_center.py` |  | modules/admin/routers/command_center.py|  |  |  |
| 290 | `backend/modules/routers/command_center_api.py` |  | modules/admin/routers/command_center_api.py|  |  |  |
| 291 | `backend/modules/routers/command_center_controller.py` |  | modules/admin/routers/command_center_controller.py|  |  |  |
| 292 | `backend/modules/routers/commission.py` |  | modules/supplier/routers/commission.py|  |  |  |
| 293 | `backend/modules/routers/comms_chat.py` |  | modules/employee/routers/comms_chat.py|  |  |  |
| 294 | `backend/modules/routers/comms_unified.py` |  | modules/employee/routers/comms_unified.py|  |  |  |
| 295 | `backend/modules/routers/comms_video.py` |  | modules/employee/routers/comms_video.py|  |  |  |
| 296 | `backend/modules/routers/compliance.py` |  | modules/admin/routers/compliance.py|  |  |  |
| 297 | `backend/modules/routers/contact.py` |  | modules/admin/routers/contact.py|  |  |  |
| 298 | `backend/modules/routers/core_accounting_routes.py` |  | modules/admin/routers/core_accounting_routes.py|  |  |  |
| 299 | `backend/modules/routers/core_addresses_routes.py` |  | modules/admin/routers/core_addresses_routes.py|  |  |  |
| 300 | `backend/modules/routers/core_ai_routes.py` |  | modules/admin/routers/core_ai_routes.py|  |  |  |
| 301 | `backend/modules/routers/core_auth_routes.py` |  | modules/admin/routers/core_auth_routes.py|  |  |  |
| 302 | `backend/modules/routers/core_automation_routes.py` |  | modules/admin/routers/core_automation_routes.py|  |  |  |
| 303 | `backend/modules/routers/core_chatbot_routes.py` |  | modules/admin/routers/core_chatbot_routes.py|  |  |  |
| 304 | `backend/modules/routers/core_comm_routes.py` |  | modules/admin/routers/core_comm_routes.py|  |  |  |
| 305 | `backend/modules/routers/core_commission_routes.py` |  | modules/admin/routers/core_commission_routes.py|  |  |  |
| 306 | `backend/modules/routers/core_compliance_routes.py` |  | modules/admin/routers/core_compliance_routes.py|  |  |  |
| 307 | `backend/modules/routers/core_countries_routes.py` |  | modules/admin/routers/core_countries_routes.py|  |  |  |
| 308 | `backend/modules/routers/core_ediscovery_routes.py` |  | modules/admin/routers/core_ediscovery_routes.py|  |  |  |
| 309 | `backend/modules/routers/core_email_routes.py` |  | modules/admin/routers/core_email_routes.py|  |  |  |
| 310 | `backend/modules/routers/core_ess_routes.py` |  | modules/admin/routers/core_ess_routes.py|  |  |  |
| 311 | `backend/modules/routers/core_export_routes.py` |  | modules/admin/routers/core_export_routes.py|  |  |  |
| 312 | `backend/modules/routers/core_hierarchy_routes.py` |  | modules/admin/routers/core_hierarchy_routes.py|  |  |  |
| 313 | `backend/modules/routers/core_iam_routes.py` |  | modules/admin/routers/core_iam_routes.py|  |  |  |
| 314 | `backend/modules/routers/core_imports_routes.py` |  | modules/admin/routers/core_imports_routes.py|  |  |  |
| 315 | `backend/modules/routers/core_incident_routes.py` |  | modules/admin/routers/core_incident_routes.py|  |  |  |
| 316 | `backend/modules/routers/core_invoices_routes.py` |  | modules/admin/routers/core_invoices_routes.py|  |  |  |
| 317 | `backend/modules/routers/core_jobs_routes.py` |  | modules/admin/routers/core_jobs_routes.py|  |  |  |
| 318 | `backend/modules/routers/core_lms_routes.py` |  | modules/admin/routers/core_lms_routes.py|  |  |  |
| 319 | `backend/modules/routers/core_messaging_routes.py` |  | modules/admin/routers/core_messaging_routes.py|  |  |  |
| 320 | `backend/modules/routers/core_okr_routes.py` |  | modules/admin/routers/core_okr_routes.py|  |  |  |
| 321 | `backend/modules/routers/core_onboarding_routes.py` |  | modules/admin/routers/core_onboarding_routes.py|  |  |  |
| 322 | `backend/modules/routers/core_payroll_routes.py` |  | modules/admin/routers/core_payroll_routes.py|  |  |  |
| 323 | `backend/modules/routers/core_performance_routes.py` |  | modules/admin/routers/core_performance_routes.py|  |  |  |
| 324 | `backend/modules/routers/core_permissions_routes.py` |  | modules/admin/routers/core_permissions_routes.py|  |  |  |
| 325 | `backend/modules/routers/core_risk_routes.py` |  | modules/admin/routers/core_risk_routes.py|  |  |  |
| 326 | `backend/modules/routers/core_succession_routes.py` |  | modules/admin/routers/core_succession_routes.py|  |  |  |
| 327 | `backend/modules/routers/core_tickets_routes.py` |  | modules/admin/routers/core_tickets_routes.py|  |  |  |
| 328 | `backend/modules/routers/core_trading_routes.py` |  | modules/admin/routers/core_trading_routes.py|  |  |  |
| 329 | `backend/modules/routers/core_travel_routes.py` |  | modules/admin/routers/core_travel_routes.py|  |  |  |
| 330 | `backend/modules/routers/core_treasury_routes.py` |  | modules/admin/routers/core_treasury_routes.py|  |  |  |
| 331 | `backend/modules/routers/core_upload_routes.py` |  | modules/admin/routers/core_upload_routes.py|  |  |  |
| 332 | `backend/modules/routers/core_users_routes.py` |  | modules/admin/routers/core_users_routes.py|  |  |  |
| 333 | `backend/modules/routers/core_video_routes.py` |  | modules/admin/routers/core_video_routes.py|  |  |  |
| 334 | `backend/modules/routers/core_workflows_routes.py` |  | modules/admin/routers/core_workflows_routes.py|  |  |  |
| 335 | `backend/modules/routers/countries.py` |  | modules/admin/routers/countries.py|  |  |  |
| 336 | `backend/modules/routers/country_admin.py` |  | modules/admin/routers/country_admin.py|  |  |  |
| 337 | `backend/modules/routers/country_admin_routes.py` |  | modules/admin/routers/country_admin_routes.py|  |  |  |
| 338 | `backend/modules/routers/country_auto_populate.py` |  | modules/admin/routers/country_auto_populate.py|  |  |  |
| 339 | `backend/modules/routers/country_communications.py` |  | modules/admin/routers/country_communications.py|  |  |  |
| 340 | `backend/modules/routers/country_dropdown.py` |  | modules/admin/routers/country_dropdown.py|  |  |  |
| 341 | `backend/modules/routers/country_maps.py` |  | modules/admin/routers/country_maps.py|  |  |  |
| 342 | `backend/modules/routers/country_payouts.py` |  | modules/admin/routers/country_payouts.py|  |  |  |
| 343 | `backend/modules/routers/country_payouts_routes.py` |  | modules/admin/routers/country_payouts_routes.py|  |  |  |
| 344 | `backend/modules/routers/country_research.py` |  | modules/admin/routers/country_research.py|  |  |  |
| 345 | `backend/modules/routers/country_staff.py` |  | modules/admin/routers/country_staff.py|  |  |  |
| 346 | `backend/modules/routers/country_staff_routes.py` |  | modules/admin/routers/country_staff_routes.py|  |  |  |
| 347 | `backend/modules/routers/country_versioning.py` |  | modules/admin/routers/country_versioning.py|  |  |  |
| 348 | `backend/modules/routers/coupons.py` |  | modules/customer/routers/coupons.py|  |  |  |
| 349 | `backend/modules/routers/cross_border.py` |  | modules/admin/routers/cross_border.py|  |  |  |
| 350 | `backend/modules/routers/csp_reporting.py` |  | modules/admin/routers/csp_reporting.py|  |  |  |
| 351 | `backend/modules/routers/currency.py` |  | modules/admin/routers/currency.py|  |  |  |
| 352 | `backend/modules/routers/customer_coupons_create.py` |  | modules/customer/routers/customer_coupons_create.py|  |  |  |
| 353 | `backend/modules/routers/customer_coupons_mgmt.py` |  | modules/customer/routers/customer_coupons_mgmt.py|  |  |  |
| 354 | `backend/modules/routers/customer_health.py` |  | modules/customer/routers/customer_health.py|  |  |  |
| 355 | `backend/modules/routers/customer_health_list.py` |  | modules/customer/routers/customer_health_list.py|  |  |  |
| 356 | `backend/modules/routers/customer_orders.py` |  | modules/customer/routers/customer_orders.py|  |  |  |
| 357 | `backend/modules/routers/customer_orders_orders.py` |  | modules/customer/routers/customer_orders_orders.py|  |  |  |
| 358 | `backend/modules/routers/ediscovery.py` |  | modules/admin/routers/ediscovery.py|  |  |  |
| 359 | `backend/modules/routers/email.py` |  | modules/employee/routers/email.py|  |  |  |
| 360 | `backend/modules/routers/email_controller.py` |  | modules/employee/routers/email_controller.py|  |  |  |
| 361 | `backend/modules/routers/email_enrichment.py` |  | modules/employee/routers/email_enrichment.py|  |  |  |
| 362 | `backend/modules/routers/employees.py` |  | modules/employee/routers/employees.py|  |  |  |
| 363 | `backend/modules/routers/entity_chat.py` |  | modules/employee/routers/entity_chat.py|  |  |  |
| 364 | `backend/modules/routers/entity_communication.py` |  | modules/employee/routers/entity_communication.py|  |  |  |
| 365 | `backend/modules/routers/escalation.py` |  | modules/admin/routers/escalation.py|  |  |  |
| 366 | `backend/modules/routers/ess.py` |  | modules/employee/routers/ess.py|  |  |  |
| 367 | `backend/modules/routers/expense_controller.py` |  | modules/employee/routers/expense_controller.py|  |  |  |
| 368 | `backend/modules/routers/expenses.py` |  | modules/employee/routers/expenses.py|  |  |  |
| 369 | `backend/modules/routers/export.py` |  | modules/admin/routers/export.py|  |  |  |
| 370 | `backend/modules/routers/finance.py` |  | modules/employee/routers/finance.py|  |  |  |
| 371 | `backend/modules/routers/finance_automation.py` |  | modules/employee/routers/finance_automation.py|  |  |  |
| 372 | `backend/modules/routers/finance_erp.py` |  | modules/employee/routers/finance_erp.py|  |  |  |
| 373 | `backend/modules/routers/finance_package.py` |  | modules/employee/routers/finance_package.py|  |  |  |
| 374 | `backend/modules/routers/flash_sales.py` |  | modules/admin/routers/flash_sales.py|  |  |  |
| 375 | `backend/modules/routers/fraud_detection.py` |  | modules/admin/routers/fraud_detection.py|  |  |  |
| 376 | `backend/modules/routers/frontend_errors.py` |  | modules/admin/routers/frontend_errors.py|  |  |  |
| 377 | `backend/modules/routers/generated/AUTO_ROUTER.md` |  | modules/admin/routers/AUTO_ROUTER.md|  |  |  |
| 378 | `backend/modules/routers/generated/auto_router.py` |  | modules/admin/routers/auto_router.py|  |  |  |
| 379 | `backend/modules/routers/geo.py` |  | modules/admin/routers/geo.py|  |  |  |
| 380 | `backend/modules/routers/governance_package.py` |  | modules/admin/routers/governance_package.py|  |  |  |
| 381 | `backend/modules/routers/hierarchy.py` |  | modules/employee/routers/hierarchy.py|  |  |  |
| 382 | `backend/modules/routers/hr.py` |  | modules/employee/routers/hr.py|  |  |  |
| 383 | `backend/modules/routers/hr_dashboard.py` |  | modules/employee/routers/hr_dashboard.py|  |  |  |
| 384 | `backend/modules/routers/iam.py` |  | modules/admin/routers/iam.py|  |  |  |
| 385 | `backend/modules/routers/imports.py` |  | modules/admin/routers/imports.py|  |  |  |
| 386 | `backend/modules/routers/incident.py` |  | modules/admin/routers/incident.py|  |  |  |
| 387 | `backend/modules/routers/internal_channels.py` |  | modules/employee/routers/internal_channels.py|  |  |  |
| 388 | `backend/modules/routers/internal_comms_channels.py` |  | modules/employee/routers/internal_comms_channels.py|  |  |  |
| 389 | `backend/modules/routers/invoices.py` |  | modules/employee/routers/invoices.py|  |  |  |
| 390 | `backend/modules/routers/jobs.py` |  | modules/employee/routers/jobs.py|  |  |  |
| 391 | `backend/modules/routers/lms.py` |  | modules/employee/routers/lms.py|  |  |  |
| 392 | `backend/modules/routers/location_api.py` |  | modules/admin/routers/location_api.py|  |  |  |
| 393 | `backend/modules/routers/logistics.py` |  | modules/logistics/routers/logistics.py|  |  |  |
| 394 | `backend/modules/routers/logistics_health.py` |  | modules/logistics/routers/logistics_health.py|  |  |  |
| 395 | `backend/modules/routers/logistics_health_list.py` |  | modules/logistics/routers/logistics_health_list.py|  |  |  |
| 396 | `backend/modules/routers/logistics_locations.py` |  | modules/logistics/routers/logistics_locations.py|  |  |  |
| 397 | `backend/modules/routers/logistics_locations_create.py` |  | modules/logistics/routers/logistics_locations_create.py|  |  |  |
| 398 | `backend/modules/routers/logistics_logistics_status.py` |  | modules/logistics/routers/logistics_logistics_status.py|  |  |  |
| 399 | `backend/modules/routers/logistics_orders_list.py` |  | modules/logistics/routers/logistics_orders_list.py|  |  |  |
| 400 | `backend/modules/routers/logistics_orders_v2.py` |  | modules/logistics/routers/logistics_orders_v2.py|  |  |  |
| 401 | `backend/modules/routers/logistics_partner.py` |  | modules/logistics/routers/logistics_partner.py|  |  |  |
| 402 | `backend/modules/routers/logistics_partner_verify.py` |  | modules/logistics/routers/logistics_partner_verify.py|  |  |  |
| 403 | `backend/modules/routers/messaging.py` |  | modules/employee/routers/messaging.py|  |  |  |
| 404 | `backend/modules/routers/mobile_controller.py` |  | modules/admin/routers/mobile_controller.py|  |  |  |
| 405 | `backend/modules/routers/notifications.py` |  | modules/employee/routers/notifications.py|  |  |  |
| 406 | `backend/modules/routers/okr.py` |  | modules/employee/routers/okr.py|  |  |  |
| 407 | `backend/modules/routers/onboarding.py` |  | modules/supplier/routers/onboarding.py|  |  |  |
| 408 | `backend/modules/routers/operational_controller.py` |  | modules/admin/routers/operational_controller.py|  |  |  |
| 409 | `backend/modules/routers/orders.py` |  | modules/customer/routers/orders.py|  |  |  |
| 410 | `backend/modules/routers/parcel_tracking.py` |  | modules/logistics/routers/parcel_tracking.py|  |  |  |
| 411 | `backend/modules/routers/payments.py` |  | modules/customer/routers/payments.py|  |  |  |
| 412 | `backend/modules/routers/payout_approval.py` |  | modules/employee/routers/payout_approval.py|  |  |  |
| 413 | `backend/modules/routers/payroll.py` |  | modules/employee/routers/payroll.py|  |  |  |
| 414 | `backend/modules/routers/performance.py` |  | modules/employee/routers/performance.py|  |  |  |
| 415 | `backend/modules/routers/permissions.py` |  | modules/admin/routers/permissions.py|  |  |  |
| 416 | `backend/modules/routers/product_moderation.py` |  | modules/supplier/routers/product_moderation.py|  |  |  |
| 417 | `backend/modules/routers/product_verification.py` |  | modules/supplier/routers/product_verification.py|  |  |  |
| 418 | `backend/modules/routers/product_videos.py` |  | modules/supplier/routers/product_videos.py|  |  |  |
| 419 | `backend/modules/routers/products.py` |  | modules/supplier/routers/products.py|  |  |  |
| 420 | `backend/modules/routers/proxy_communication.py` |  | modules/employee/routers/proxy_communication.py|  |  |  |
| 421 | `backend/modules/routers/public_admin_promotions_routes.py` |  | modules/admin/routers/public_admin_promotions_routes.py|  |  |  |
| 422 | `backend/modules/routers/public_auth_access.py` |  | modules/admin/routers/public_auth_access.py|  |  |  |
| 423 | `backend/modules/routers/public_commerce_referrals.py` |  | modules/admin/routers/public_commerce_referrals.py|  |  |  |
| 424 | `backend/modules/routers/public_commerce_reviews.py` |  | modules/admin/routers/public_commerce_reviews.py|  |  |  |
| 425 | `backend/modules/routers/public_commerce_validation.py` |  | modules/admin/routers/public_commerce_validation.py|  |  |  |
| 426 | `backend/modules/routers/public_commerce_wishlist.py` |  | modules/admin/routers/public_commerce_wishlist.py|  |  |  |
| 427 | `backend/modules/routers/public_comms_comm.py` |  | modules/admin/routers/public_comms_comm.py|  |  |  |
| 428 | `backend/modules/routers/public_comms_notification.py` |  | modules/admin/routers/public_comms_notification.py|  |  |  |
| 429 | `backend/modules/routers/public_comms_status.py` |  | modules/admin/routers/public_comms_status.py|  |  |  |
| 430 | `backend/modules/routers/public_comms_unified.py` |  | modules/admin/routers/public_comms_unified.py|  |  |  |
| 431 | `backend/modules/routers/public_core_admin.py` |  | modules/admin/routers/public_core_admin.py|  |  |  |
| 432 | `backend/modules/routers/public_core_admin_categories.py` |  | modules/admin/routers/public_core_admin_categories.py|  |  |  |
| 433 | `backend/modules/routers/public_core_admin_orders.py` |  | modules/admin/routers/public_core_admin_orders.py|  |  |  |
| 434 | `backend/modules/routers/public_core_admin_products.py` |  | modules/admin/routers/public_core_admin_products.py|  |  |  |
| 435 | `backend/modules/routers/public_core_admin_suppliers.py` |  | modules/admin/routers/public_core_admin_suppliers.py|  |  |  |
| 436 | `backend/modules/routers/public_core_ai_upload.py` |  | modules/admin/routers/public_core_ai_upload.py|  |  |  |
| 437 | `backend/modules/routers/public_core_cart.py` |  | modules/admin/routers/public_core_cart.py|  |  |  |
| 438 | `backend/modules/routers/public_core_categories.py` |  | modules/admin/routers/public_core_categories.py|  |  |  |
| 439 | `backend/modules/routers/public_core_commission.py` |  | modules/admin/routers/public_core_commission.py|  |  |  |
| 440 | `backend/modules/routers/public_core_countries.py` |  | modules/admin/routers/public_core_countries.py|  |  |  |
| 441 | `backend/modules/routers/public_core_country_admin.py` |  | modules/admin/routers/public_core_country_admin.py|  |  |  |
| 442 | `backend/modules/routers/public_core_country_dropdown.py` |  | modules/admin/routers/public_core_country_dropdown.py|  |  |  |
| 443 | `backend/modules/routers/public_core_country_maps.py` |  | modules/admin/routers/public_core_country_maps.py|  |  |  |
| 444 | `backend/modules/routers/public_core_country_payouts.py` |  | modules/admin/routers/public_core_country_payouts.py|  |  |  |
| 445 | `backend/modules/routers/public_core_country_staff.py` |  | modules/admin/routers/public_core_country_staff.py|  |  |  |
| 446 | `backend/modules/routers/public_core_coupons.py` |  | modules/admin/routers/public_core_coupons.py|  |  |  |
| 447 | `backend/modules/routers/public_core_customer_health.py` |  | modules/admin/routers/public_core_customer_health.py|  |  |  |
| 448 | `backend/modules/routers/public_core_email.py` |  | modules/admin/routers/public_core_email.py|  |  |  |
| 449 | `backend/modules/routers/public_core_employees.py` |  | modules/admin/routers/public_core_employees.py|  |  |  |
| 450 | `backend/modules/routers/public_core_ess.py` |  | modules/admin/routers/public_core_ess.py|  |  |  |
| 451 | `backend/modules/routers/public_core_export.py` |  | modules/admin/routers/public_core_export.py|  |  |  |
| 452 | `backend/modules/routers/public_core_geo.py` |  | modules/admin/routers/public_core_geo.py|  |  |  |
| 453 | `backend/modules/routers/public_core_hierarchy.py` |  | modules/admin/routers/public_core_hierarchy.py|  |  |  |
| 454 | `backend/modules/routers/public_core_hr.py` |  | modules/admin/routers/public_core_hr.py|  |  |  |
| 455 | `backend/modules/routers/public_core_incident.py` |  | modules/admin/routers/public_core_incident.py|  |  |  |
| 456 | `backend/modules/routers/public_core_internal_channels.py` |  | modules/admin/routers/public_core_internal_channels.py|  |  |  |
| 457 | `backend/modules/routers/public_core_logistics.py` |  | modules/admin/routers/public_core_logistics.py|  |  |  |
| 458 | `backend/modules/routers/public_core_logistics_health.py` |  | modules/admin/routers/public_core_logistics_health.py|  |  |  |
| 459 | `backend/modules/routers/public_core_logistics_locations.py` |  | modules/admin/routers/public_core_logistics_locations.py|  |  |  |
| 460 | `backend/modules/routers/public_core_payroll.py` |  | modules/admin/routers/public_core_payroll.py|  |  |  |
| 461 | `backend/modules/routers/public_core_performance.py` |  | modules/admin/routers/public_core_performance.py|  |  |  |
| 462 | `backend/modules/routers/public_core_permissions.py` |  | modules/admin/routers/public_core_permissions.py|  |  |  |
| 463 | `backend/modules/routers/public_core_referrals.py` |  | modules/admin/routers/public_core_referrals.py|  |  |  |
| 464 | `backend/modules/routers/public_core_returns.py` |  | modules/admin/routers/public_core_returns.py|  |  |  |
| 465 | `backend/modules/routers/public_core_reviews.py` |  | modules/admin/routers/public_core_reviews.py|  |  |  |
| 466 | `backend/modules/routers/public_core_shipments.py` |  | modules/admin/routers/public_core_shipments.py|  |  |  |
| 467 | `backend/modules/routers/public_core_supplier_documents.py` |  | modules/admin/routers/public_core_supplier_documents.py|  |  |  |
| 468 | `backend/modules/routers/public_core_supplier_finance.py` |  | modules/admin/routers/public_core_supplier_finance.py|  |  |  |
| 469 | `backend/modules/routers/public_core_supplier_health.py` |  | modules/admin/routers/public_core_supplier_health.py|  |  |  |
| 470 | `backend/modules/routers/public_core_supplier_payouts.py` |  | modules/admin/routers/public_core_supplier_payouts.py|  |  |  |
| 471 | `backend/modules/routers/public_core_supplier_profile.py` |  | modules/admin/routers/public_core_supplier_profile.py|  |  |  |
| 472 | `backend/modules/routers/public_core_tickets.py` |  | modules/admin/routers/public_core_tickets.py|  |  |  |
| 473 | `backend/modules/routers/public_core_translate.py` |  | modules/admin/routers/public_core_translate.py|  |  |  |
| 474 | `backend/modules/routers/public_core_users.py` |  | modules/admin/routers/public_core_users.py|  |  |  |
| 475 | `backend/modules/routers/public_core_wishlist.py` |  | modules/admin/routers/public_core_wishlist.py|  |  |  |
| 476 | `backend/modules/routers/public_country_auto_populate_access.py` |  | modules/admin/routers/public_country_auto_populate_access.py|  |  |  |
| 477 | `backend/modules/routers/public_customer_coupons_create.py` |  | modules/admin/routers/public_customer_coupons_create.py|  |  |  |
| 478 | `backend/modules/routers/public_customer_health_list.py` |  | modules/admin/routers/public_customer_health_list.py|  |  |  |
| 479 | `backend/modules/routers/public_effective_permissions_access.py` |  | modules/admin/routers/public_effective_permissions_access.py|  |  |  |
| 480 | `backend/modules/routers/public_finance_creation.py` |  | modules/admin/routers/public_finance_creation.py|  |  |  |
| 481 | `backend/modules/routers/public_geography_configuration.py` |  | modules/admin/routers/public_geography_configuration.py|  |  |  |
| 482 | `backend/modules/routers/public_geography_travel.py` |  | modules/admin/routers/public_geography_travel.py|  |  |  |
| 483 | `backend/modules/routers/public_hr.py` |  | modules/admin/routers/public_hr.py|  |  |  |
| 484 | `backend/modules/routers/public_hr_hierarchy.py` |  | modules/admin/routers/public_hr_hierarchy.py|  |  |  |
| 485 | `backend/modules/routers/public_hr_hr.py` |  | modules/admin/routers/public_hr_hr.py|  |  |  |
| 486 | `backend/modules/routers/public_hr_lms.py` |  | modules/admin/routers/public_hr_lms.py|  |  |  |
| 487 | `backend/modules/routers/public_hr_okr.py` |  | modules/admin/routers/public_hr_okr.py|  |  |  |
| 488 | `backend/modules/routers/public_hr_succession.py` |  | modules/admin/routers/public_hr_succession.py|  |  |  |
| 489 | `backend/modules/routers/public_identity_iam.py` |  | modules/admin/routers/public_identity_iam.py|  |  |  |
| 490 | `backend/modules/routers/public_identity_operations.py` |  | modules/admin/routers/public_identity_operations.py|  |  |  |
| 491 | `backend/modules/routers/public_internal_comms_channels.py` |  | modules/admin/routers/public_internal_comms_channels.py|  |  |  |
| 492 | `backend/modules/routers/public_permission_primitives_access.py` |  | modules/admin/routers/public_permission_primitives_access.py|  |  |  |
| 493 | `backend/modules/routers/public_permissions_validation.py` |  | modules/admin/routers/public_permissions_validation.py|  |  |  |
| 494 | `backend/modules/routers/public_security_detection.py` |  | modules/admin/routers/public_security_detection.py|  |  |  |
| 495 | `backend/modules/routers/public_security_health.py` |  | modules/admin/routers/public_security_health.py|  |  |  |
| 496 | `backend/modules/routers/public_security_operations.py` |  | modules/admin/routers/public_security_operations.py|  |  |  |
| 497 | `backend/modules/routers/public_security_registration.py` |  | modules/admin/routers/public_security_registration.py|  |  |  |
| 498 | `backend/modules/routers/public_suppliers.py` |  | modules/admin/routers/public_suppliers.py|  |  |  |
| 499 | `backend/modules/routers/public_suppliers_routes.py` |  | modules/admin/routers/public_suppliers_routes.py|  |  |  |
| 500 | `backend/modules/routers/public_system_ai_upload.py` |  | modules/admin/routers/public_system_ai_upload.py|  |  |  |
| 501 | `backend/modules/routers/public_treasury_api_access.py` |  | modules/admin/routers/public_treasury_api_access.py|  |  |  |
| 502 | `backend/modules/routers/public_treasury_cash_position.py` |  | modules/admin/routers/public_treasury_cash_position.py|  |  |  |
| 503 | `backend/modules/routers/public_treasury_payments.py` |  | modules/admin/routers/public_treasury_payments.py|  |  |  |
| 504 | `backend/modules/routers/public_users_workflow.py` |  | modules/admin/routers/public_users_workflow.py|  |  |  |
| 505 | `backend/modules/routers/push_notifications.py` |  | modules/employee/routers/push_notifications.py|  |  |  |
| 506 | `backend/modules/routers/referrals.py` |  | modules/customer/routers/referrals.py|  |  |  |
| 507 | `backend/modules/routers/returns.py` |  | modules/customer/routers/returns.py|  |  |  |
| 508 | `backend/modules/routers/reviews.py` |  | modules/customer/routers/reviews.py|  |  |  |
| 509 | `backend/modules/routers/risk.py` |  | modules/employee/routers/risk.py|  |  |  |
| 510 | `backend/modules/routers/search.py` |  | modules/admin/routers/search.py|  |  |  |
| 511 | `backend/modules/routers/shift_handover.py` |  | modules/employee/routers/shift_handover.py|  |  |  |
| 512 | `backend/modules/routers/shipments.py` |  | modules/logistics/routers/shipments.py|  |  |  |
| 513 | `backend/modules/routers/shop_locations.py` |  | modules/admin/routers/shop_locations.py|  |  |  |
| 514 | `backend/modules/routers/store_banners_routes.py` |  | modules/admin/routers/store_banners_routes.py|  |  |  |
| 515 | `backend/modules/routers/store_cart_routes.py` |  | modules/admin/routers/store_cart_routes.py|  |  |  |
| 516 | `backend/modules/routers/store_currency_routes.py` |  | modules/admin/routers/store_currency_routes.py|  |  |  |
| 517 | `backend/modules/routers/store_orders_routes.py` |  | modules/admin/routers/store_orders_routes.py|  |  |  |
| 518 | `backend/modules/routers/store_payments_routes.py` |  | modules/admin/routers/store_payments_routes.py|  |  |  |
| 519 | `backend/modules/routers/store_products_routes.py` |  | modules/admin/routers/store_products_routes.py|  |  |  |
| 520 | `backend/modules/routers/store_referrals_routes.py` |  | modules/admin/routers/store_referrals_routes.py|  |  |  |
| 521 | `backend/modules/routers/store_returns_routes.py` |  | modules/admin/routers/store_returns_routes.py|  |  |  |
| 522 | `backend/modules/routers/store_shipments_routes.py` |  | modules/admin/routers/store_shipments_routes.py|  |  |  |
| 523 | `backend/modules/routers/succession.py` |  | modules/employee/routers/succession.py|  |  |  |
| 524 | `backend/modules/routers/supplier.py` |  | modules/supplier/routers/supplier.py|  |  |  |
| 525 | `backend/modules/routers/supplier_analytics.py` |  | modules/supplier/routers/supplier_analytics.py|  |  |  |
| 526 | `backend/modules/routers/supplier_analytics_analytics.py` |  | modules/supplier/routers/supplier_analytics_analytics.py|  |  |  |
| 527 | `backend/modules/routers/supplier_bg_ab_test.py` |  | modules/supplier/routers/supplier_bg_ab_test.py|  |  |  |
| 528 | `backend/modules/routers/supplier_core_routes.py` |  | modules/supplier/routers/supplier_core_routes.py|  |  |  |
| 529 | `backend/modules/routers/supplier_documents.py` |  | modules/supplier/routers/supplier_documents.py|  |  |  |
| 530 | `backend/modules/routers/supplier_documents_review.py` |  | modules/supplier/routers/supplier_documents_review.py|  |  |  |
| 531 | `backend/modules/routers/supplier_finance.py` |  | modules/supplier/routers/supplier_finance.py|  |  |  |
| 532 | `backend/modules/routers/supplier_finance_status.py` |  | modules/supplier/routers/supplier_finance_status.py|  |  |  |
| 533 | `backend/modules/routers/supplier_health.py` |  | modules/supplier/routers/supplier_health.py|  |  |  |
| 534 | `backend/modules/routers/supplier_health_list.py` |  | modules/supplier/routers/supplier_health_list.py|  |  |  |
| 535 | `backend/modules/routers/supplier_orders.py` |  | modules/supplier/routers/supplier_orders.py|  |  |  |
| 536 | `backend/modules/routers/supplier_orders_verify.py` |  | modules/supplier/routers/supplier_orders_verify.py|  |  |  |
| 537 | `backend/modules/routers/supplier_payouts.py` |  | modules/supplier/routers/supplier_payouts.py|  |  |  |
| 538 | `backend/modules/routers/supplier_payouts_pay.py` |  | modules/supplier/routers/supplier_payouts_pay.py|  |  |  |
| 539 | `backend/modules/routers/supplier_products.py` |  | modules/supplier/routers/supplier_products.py|  |  |  |
| 540 | `backend/modules/routers/supplier_products_upload.py` |  | modules/supplier/routers/supplier_products_upload.py|  |  |  |
| 541 | `backend/modules/routers/supplier_profile.py` |  | modules/supplier/routers/supplier_profile.py|  |  |  |
| 542 | `backend/modules/routers/supplier_profile_create.py` |  | modules/supplier/routers/supplier_profile_create.py|  |  |  |
| 543 | `backend/modules/routers/supplier_supplier_sync.py` |  | modules/supplier/routers/supplier_supplier_sync.py|  |  |  |
| 544 | `backend/modules/routers/supplier_supplier_upload.py` |  | modules/supplier/routers/supplier_supplier_upload.py|  |  |  |
| 545 | `backend/modules/routers/system_ai_country_research.py` |  | modules/admin/routers/system_ai_country_research.py|  |  |  |
| 546 | `backend/modules/routers/system_ai_media.py` |  | modules/admin/routers/system_ai_media.py|  |  |  |
| 547 | `backend/modules/routers/system_ai_messaging.py` |  | modules/admin/routers/system_ai_messaging.py|  |  |  |
| 548 | `backend/modules/routers/system_ai_reporting.py` |  | modules/admin/routers/system_ai_reporting.py|  |  |  |
| 549 | `backend/modules/routers/system_ai_sync.py` |  | modules/admin/routers/system_ai_sync.py|  |  |  |
| 550 | `backend/modules/routers/system_ai_upload.py` |  | modules/admin/routers/system_ai_upload.py|  |  |  |
| 551 | `backend/modules/routers/system_comms_status.py` |  | modules/admin/routers/system_comms_status.py|  |  |  |
| 552 | `backend/modules/routers/tickets.py` |  | modules/employee/routers/tickets.py|  |  |  |
| 553 | `backend/modules/routers/trading.py` |  | modules/employee/routers/trading.py|  |  |  |
| 554 | `backend/modules/routers/translate.py` |  | modules/admin/routers/translate.py|  |  |  |
| 555 | `backend/modules/routers/travel.py` |  | modules/employee/routers/travel.py|  |  |  |
| 556 | `backend/modules/routers/treasury.py` |  | modules/employee/routers/treasury.py|  |  |  |
| 557 | `backend/modules/routers/treasury_api.py` |  | modules/employee/routers/treasury_api.py|  |  |  |
| 558 | `backend/modules/routers/upload.py` |  | modules/admin/routers/upload.py|  |  |  |
| 559 | `backend/modules/routers/upload_jobs.py` |  | modules/admin/routers/upload_jobs.py|  |  |  |
| 560 | `backend/modules/routers/users.py` |  | modules/admin/routers/users.py|  |  |  |
| 561 | `backend/modules/routers/video.py` |  | modules/employee/routers/video.py|  |  |  |
| 562 | `backend/modules/routers/video_controller.py` |  | modules/employee/routers/video_controller.py|  |  |  |
| 563 | `backend/modules/routers/wishlist.py` |  | modules/customer/routers/wishlist.py|  |  |  |
| 564 | `backend/modules/routers/workflows.py` |  | modules/admin/routers/workflows.py|  |  |  |
| 565 | `backend/modules/routers/ws_chat.py` |  | modules/employee/routers/ws_chat.py|  |  |  |
| 566 | `backend/modules/supplier/routers/supplier_analytics_controller.py` |  | modules/supplier/routers/supplier_analytics_controller.py |  |  |  |
| 567 | `backend/modules/supplier/routers/supplier_controller.py` |  | modules/supplier/routers/supplier_controller.py |  |  |  |
| 568 | `backend/modules/supplier/routers/supplier_document_controller.py` |  | modules/supplier/routers/supplier_document_controller.py |  |  |  |
| 569 | `backend/modules/supplier/routers/supplier_health_controller.py` |  | modules/supplier/routers/supplier_health_controller.py |  |  |  |
| 570 | `backend/modules/supplier/routers/supplier_orders_verify_controller.py` |  | modules/supplier/routers/supplier_orders_verify_controller.py |  |  |  |
| 571 | `backend/modules/supplier/routers/supplier_products_upload_controller.py` |  | modules/supplier/routers/supplier_products_upload_controller.py |  |  |  |
| 572 | `backend/modules/supplier/routers/supplier_profile_create_controller.py` |  | modules/supplier/routers/supplier_profile_create_controller.py |  |  |  |
| 573 | `backend/modules/treasury/routers/cash_management_controller.py` | domains/finance/services/cash_management_controller.py |  |  |  |  |
| 574 | `backend/modules/treasury/routers/cash_management_write_controller.py` | domains/finance/services/cash_management_write_controller.py |  |  |  |  |
| 575 | `backend/modules/treasury/routers/payout_approval_controller.py` | domains/finance/services/payout_approval_controller.py |  |  |  |  |
| 576 | `backend/modules/unknown/routers/onboarding_controller.py` |  | modules/admin/routers/onboarding_controller.py |  |  |  |
| 577 | `backend/modules/unknown/routers/payments_controller.py` |  | modules/admin/routers/payments_controller.py |  |  |  |
| 578 | `backend/modules/unknown/routers/payments_read_controller.py` |  | modules/admin/routers/payments_read_controller.py |  |  |  |

**Column totals:** domains=34 modules=544 infrastructure=0 rbac=0 kernel=0
> Router re-home (flat `backend/modules/routers/*` -> `modules/<actor>/routers/`): admin=303 customer=32 supplier=27 logistics=12 employee=22
