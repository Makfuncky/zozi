# COMPILER LOG

Generated: 2026-10-02T16:22:27+00:00
Run number: 8 (re-investigation after worklist schema regression)
Source commit: 6666d435
Spec: `_most_imp_docx/PROMPT_AUDIT_COMPILER.md`

## Why this run happened

The working-tree `_audit/TO_BE_RESOLVE.md` had been regenerated into a
per-path rollup that carried none of the file-block fields the resolver
dispatches on (`FILE <n>`, `Phase`, `Depends on`, the 11 subsections,
`Resolution status`). `PROMPT_RESOLUTION_ORCHESTRATOR.md` §0.0 declares
that schema invariant across re-runs, so the resolver stopped at §0.2.3
and escalated. This run rebuilt it.

A first format-tolerant parse of the 34 dimension files recovered
**1340 records** across **all 34 files** with zero dimensions
empty. A strict `## Findings` + 23-column parse recovered only 583 and
silently dropped 11 dimensions entirely.

## Files read

- `_audit/dimensions/00_boot_smoke_test.md` (8 records, 1 without a path)
- `_audit/dimensions/01_architectural.md` (17 records, 3 without a path)
- `_audit/dimensions/02_technological.md` (55 records, 7 without a path)
- `_audit/dimensions/03_logical.md` (28 records, 10 without a path)
- `_audit/dimensions/04_operational.md` (14 records, 6 without a path)
- `_audit/dimensions/05_wiring.md` (10 records, 2 without a path)
- `_audit/dimensions/06_database.md` (8 records, 2 without a path)
- `_audit/dimensions/07_CONTRADICTIONS.md` (41 records, 9 without a path)
- `_audit/dimensions/07_tables_fields.md` (275 records, 19 without a path)
- `_audit/dimensions/08_providers.md` (66 records, 1 without a path)
- `_audit/dimensions/09_laws.md` (204 records, 204 without a path)
- `_audit/dimensions/10_migrations.md` (70 records, 70 without a path)
- `_audit/dimensions/11_environmental.md` (28 records, 28 without a path)
- `_audit/dimensions/12_tests.md` (14 records, 4 without a path)
- `_audit/dimensions/12_tests_collection_verify.md` (5 records, 2 without a path)
- `_audit/dimensions/13_dev_to_prod.md` (19 records, 11 without a path)
- `_audit/dimensions/13_dev_to_prod_docker_verify.md` (24 records, 12 without a path)
- `_audit/dimensions/14_frontend_web.md` (22 records, 22 without a path)
- `_audit/dimensions/15_frontend_mobile.md` (12 records, 4 without a path)
- `_audit/dimensions/16_features.md` (46 records, 5 without a path)
- `_audit/dimensions/17_code_file_management.md` (18 records, 6 without a path)
- `_audit/dimensions/18_security.md` (16 records, 4 without a path)
- `_audit/dimensions/19_performance.md` (13 records, 4 without a path)
- `_audit/dimensions/20_observability_resilience.md` (25 records, 8 without a path)
- `_audit/dimensions/21_contradictions.md` (22 records, 22 without a path)
- `_audit/dimensions/22_anti_patterns.md` (170 records, 0 without a path)
- `_audit/dimensions/23_code_intent.md` (16 records, 0 without a path)
- `_audit/dimensions/24_browser_behavior.md` (10 records, 2 without a path)
- `_audit/dimensions/25_ai_drift.md` (14 records, 4 without a path)
- `_audit/dimensions/26_code_alignment.md` (14 records, 4 without a path)
- `_audit/dimensions/27_project_completion_blockers.md` (10 records, 4 without a path)
- `_audit/dimensions/28_supply_chain_security.md` (21 records, 10 without a path)
- `_audit/dimensions/config_verification.md` (20 records, 1 without a path)
- `_audit/dimensions/suppliers.md` (5 records, 5 without a path)

## Findings compiled

| Dimension | Records | REAL | INVALID | RESOLVED | BLOCKED |
|---|---|---|---|---|---|
| 00_boot_smoke_test | 8 | 2 | 6 | 0 | 0 |
| 01_architectural | 17 | 12 | 5 | 0 | 0 |
| 02_technological | 55 | 29 | 2 | 23 | 1 |
| 03_logical | 28 | 28 | 0 | 0 | 0 |
| 04_operational | 14 | 10 | 0 | 4 | 0 |
| 05_wiring | 10 | 9 | 0 | 1 | 0 |
| 06_database | 8 | 7 | 0 | 1 | 0 |
| 07_CONTRADICTIONS | 41 | 27 | 2 | 10 | 2 |
| 07_tables_fields | 275 | 251 | 23 | 1 | 0 |
| 08_providers | 66 | 60 | 0 | 6 | 0 |
| 09_laws | 204 | 54 | 6 | 144 | 0 |
| 10_migrations | 70 | 68 | 2 | 0 | 0 |
| 11_environmental | 28 | 27 | 0 | 1 | 0 |
| 12_tests | 14 | 6 | 4 | 4 | 0 |
| 12_tests_collection_verify | 5 | 0 | 0 | 5 | 0 |
| 13_dev_to_prod | 19 | 10 | 6 | 2 | 0 |
| 13_dev_to_prod_docker_verify | 24 | 10 | 9 | 3 | 2 |
| 14_frontend_web | 22 | 21 | 1 | 0 | 0 |
| 15_frontend_mobile | 12 | 9 | 2 | 0 | 1 |
| 16_features | 46 | 28 | 16 | 1 | 1 |
| 17_code_file_management | 18 | 13 | 1 | 4 | 0 |
| 18_security | 16 | 15 | 1 | 0 | 0 |
| 19_performance | 13 | 9 | 2 | 2 | 0 |
| 20_observability_resilience | 25 | 5 | 3 | 16 | 1 |
| 21_contradictions | 22 | 2 | 4 | 10 | 6 |
| 22_anti_patterns | 170 | 142 | 28 | 0 | 0 |
| 23_code_intent | 16 | 9 | 6 | 1 | 0 |
| 24_browser_behavior | 10 | 3 | 1 | 0 | 6 |
| 25_ai_drift | 14 | 11 | 3 | 0 | 0 |
| 26_code_alignment | 14 | 13 | 1 | 0 | 0 |
| 27_project_completion_blockers | 10 | 2 | 5 | 2 | 1 |
| 28_supply_chain_security | 21 | 3 | 14 | 3 | 1 |
| config_verification | 20 | 3 | 2 | 15 | 0 |
| suppliers | 5 | 4 | 0 | 1 | 0 |
| **TOTAL** | **1340** | **901** | **152** | **260** | **21** |

## Files indexed

| File | Findings | Phase | Subsection count |
|---|---|---|---|
| FILE 1 | `backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py` | emergency | 1 | M (3h) |
| FILE 2 | `backend/config.py` | emergency | 2 | Medium |
| FILE 3 | `backend/domains/analytics/services/aggregation/command_center_query_service.py` | emergency | 1 | M (3h) |
| FILE 4 | `backend/infrastructure/security/key_rotation.py` | emergency | 1 | M (3h) |
| FILE 5 | `backend/alembic.ini` | boot | 1 | S |
| FILE 6 | `.github/workflows/ci.yml` | tech | 1 | M (2h) |
| FILE 7 | `ai.ai` | tech | 3 | S (TBD) |
| FILE 8 | `ai.categorization` | tech | 1 | S (TBD) |
| FILE 9 | `ai.chatbot` | tech | 1 | S (TBD) |
| FILE 10 | `ai.finance` | tech | 1 | S (TBD) |
| FILE 11 | `ai.huggingface` | tech | 1 | S (TBD) |
| FILE 12 | `ai.image` | tech | 2 | S (TBD) |
| FILE 13 | `ai.openai` | tech | 1 | S (TBD) |
| FILE 14 | `ai.price` | tech | 1 | S (TBD) |
| FILE 15 | `ai.recommendation` | tech | 1 | S (TBD) |
| FILE 16 | `ai.search` | tech | 1 | S (TBD) |
| FILE 17 | `ai.sentiment` | tech | 1 | S (TBD) |
| FILE 18 | `analytics.analytics` | tech | 1 | S (TBD) |
| FILE 19 | `auth.apple` | tech | 1 | S (TBD) |
| FILE 20 | `auth.jwt` | tech | 1 | S (TBD) |
| FILE 21 | `auth.oauth` | tech | 1 | S (TBD) |
| FILE 22 | `auth.totp` | tech | 1 | S (TBD) |
| FILE 23 | `automation.scheduler` | tech | 1 | S (TBD) |
| FILE 24 | `backend/Dockerfile.prod` | tech | 4 | M (2h) |
| FILE 25 | `backend/jobs/celery_app.py` | tech | 1 | S (0.5h) |
| FILE 26 | `backend/requirements.txt` | tech | 24 | M (3h) |
| FILE 27 | `backend/scripts/_debug/_smoke.py` | tech | 1 | S (0.5h) |
| FILE 28 | `backend/tests/architecture/test_architecture_gates.py` | tech | 2 | S (0.5h) |
| FILE 29 | `backend/tests/system/test_import_direction_all_packages.py` | tech | 1 | S (1h) |
| FILE 30 | `barcode.barcode` | tech | 1 | S (TBD) |
| FILE 31 | `bg_removal.bg` | tech | 1 | S (TBD) |
| FILE 32 | `comms.email` | tech | 1 | S (TBD) |
| FILE 33 | `comms.sms` | tech | 1 | S (TBD) |
| FILE 34 | `comms.twilio` | tech | 1 | S (TBD) |
| FILE 35 | `comms.whatsapp` | tech | 1 | S (TBD) |
| FILE 36 | `docker-compose.prod.yml` | tech | 1 | S (1h) |
| FILE 37 | `docker-compose.yml` | tech | 1 | S (0.5h) |
| FILE 38 | `finance.bank` | tech | 1 | S (TBD) |
| FILE 39 | `finance.fx` | tech | 1 | S (TBD) |
| FILE 40 | `frontend/mobile_app/package.json` | tech | 1 | S (0.5h) |
| FILE 41 | `frontend/web_app/pnpm-lock.yaml` | tech | 2 | S (0.5h) |
| FILE 42 | `geography.country` | tech | 2 | S (TBD) |
| FILE 43 | `geography.geo` | tech | 1 | S (TBD) |
| FILE 44 | `geography.geoip` | tech | 1 | S (TBD) |
| FILE 45 | `geography.ip` | tech | 1 | S (TBD) |
| FILE 46 | `geography.map` | tech | 1 | S (TBD) |
| FILE 47 | `geography.rates` | tech | 1 | S (TBD) |
| FILE 48 | `image.free` | tech | 1 | S (TBD) |
| FILE 49 | `image.image` | tech | 1 | S (TBD) |
| FILE 50 | `news.rss` | tech | 1 | S (TBD) |
| FILE 51 | `ocr.ocr` | tech | 1 | S (TBD) |
| FILE 52 | `payments.base` | tech | 1 | S (TBD) |
| FILE 53 | `payments.config` | tech | 1 | S (TBD) |
| FILE 54 | `payments.generic` | tech | 1 | S (TBD) |
| FILE 55 | `payments.webhook` | tech | 1 | S (TBD) |
| FILE 56 | `payments.webhooks` | tech | 1 | S (TBD) |
| FILE 57 | `qr.parcel` | tech | 1 | S (TBD) |
| FILE 58 | `qr.qr` | tech | 1 | S (TBD) |
| FILE 59 | `scanner.scanner` | tech | 1 | S (TBD) |
| FILE 60 | `security.encryption` | tech | 1 | S (TBD) |
| FILE 61 | `security.threat` | tech | 1 | S (TBD) |
| FILE 62 | `security.watchlist` | tech | 1 | S (TBD) |
| FILE 63 | `shipping.shipping` | tech | 1 | S (TBD) |
| FILE 64 | `storage.r2` | tech | 1 | S (TBD) |
| FILE 65 | `storage.s3` | tech | 1 | S (TBD) |
| FILE 66 | `voice.voice` | tech | 1 | S (TBD) |
| FILE 67 | `backend/domains/catalog/models/commission.py` | db | 1 | L (8h) |
| FILE 68 | `backend/domains/catalog/models/products.py` | db | 2 | S (0.5h) |
| FILE 69 | `backend/domains/country/models/countries.py` | db | 2 | S (1h) |
| FILE 70 | `backend/domains/orders/models/order_entities.py` | db | 3 | — |
| FILE 71 | `backend/infrastructure/database/database.py` | db | 2 | M (3h) |
| FILE 72 | `backend/infrastructure/database/rls_interceptor.py` | db | 1 | M (2h) |
| FILE 73 | `backenddomainscatalogmodelsupload_job.py` | db | 1 | M |
| FILE 74 | `backenddomainscommsmodelschat.py` | db | 22 | M |
| FILE 75 | `backenddomainscommsmodelscommunication.py` | db | 25 | M |
| FILE 76 | `backenddomainscommsmodelscommunication_schema_models.py` | db | 9 | M |
| FILE 77 | `backenddomainscommsmodelsfraud.py` | db | 1 | M |
| FILE 78 | `backenddomainscommsmodelsincident.py` | db | 6 | M |
| FILE 79 | `backenddomainscommsmodelsmarketing.py` | db | 14 | M |
| FILE 80 | `backenddomainscommsmodelsmessage.py` | db | 1 | M |
| FILE 81 | `backenddomainscommsmodelsnews.py` | db | 1 | M |
| FILE 82 | `backenddomainscountrymodelscountries.py` | db | 2 | M |
| FILE 83 | `backenddomainscountrymodelscountry_basics.py` | db | 1 | M |
| FILE 84 | `backenddomainscountrymodelscountry_control.py` | db | 8 | M |
| FILE 85 | `backenddomainscountrymodelscountry_economics.py` | db | 1 | M |
| FILE 86 | `backenddomainscountrymodelscountry_enhancements.py` | db | 16 | M |
| FILE 87 | `backenddomainscountrymodelscountry_legal.py` | db | 1 | M |
| FILE 88 | `backenddomainscountrymodelscountry_tax.py` | db | 1 | M |
| FILE 89 | `backenddomainscustomersmodelscross_country_session.py` | db | 2 | M |
| FILE 90 | `backenddomainscustomersmodelscustomer_schema_models.py` | db | 2 | M |
| FILE 91 | `backenddomainsfinancemodelscommission.py` | db | 4 | M |
| FILE 92 | `backenddomainsfinancemodelsgeneral_ledger.py` | db | 40 | M |
| FILE 93 | `backenddomainsfinancemodelstax_rules.py` | db | 4 | M |
| FILE 94 | `backenddomainsgovernancemodelsadmin.py` | db | 2 | M |
| FILE 95 | `backenddomainshrmodelsemployee_models.py` | db | 4 | M |
| FILE 96 | `backenddomainslogisticsmodelslogistics_entities.py` | db | 8 | M |
| FILE 97 | `backenddomainslogisticsmodelslogistics_schema_models.py` | db | 1 | M |
| FILE 98 | `backenddomainslogisticsmodelsshipping_rules.py` | db | 1 | M |
| FILE 99 | `backenddomainsmediamodelsmedia_asset.py` | db | 1 | M |
| FILE 100 | `backenddomainsordersmodelsorder_entities.py` | db | 2 | M |
| FILE 101 | `backenddomainspromotionsmodelscoupon_usage.py` | db | 1 | M |
| FILE 102 | `backenddomainspromotionsmodelspromotion_config.py` | db | 1 | M |
| FILE 103 | `backenddomainssecuritymodelsfraud.py` | db | 27 | M |
| FILE 104 | `backenddomainssuppliersmodelssuppliers.py` | db | 8 | M |
| FILE 105 | `backend/domains/catalog/services/categories/admin_categories_service.py` | logic | 1 | M (2h) |
| FILE 106 | `backend/domains/catalog/services/products/products_service.py` | logic | 2 | M (2h) |
| FILE 107 | `backend/domains/finance/models/payments.py` | logic | 1 | L (8h) |
| FILE 108 | `backend/domains/finance/services/data_import_service.py` | logic | 1 | S (0.5h) |
| FILE 109 | `backend/domains/finance/services/finance_service.py` | logic | 1 | S (0.25h) |
| FILE 110 | `backend/domains/finance/services/payments/payment_engine.py` | logic | 4 | S (0.5h) |
| FILE 111 | `backend/domains/finance/services/payments/payment_orchestrator.py` | logic | 2 | S (0.25h) |
| FILE 112 | `backend/domains/finance/services/payouts/payout_batch_service.py` | logic | 3 | S (0.5h) |
| FILE 113 | `backend/domains/finance/services/trading_service.py` | logic | 1 | S (1h) |
| FILE 114 | `backend/domains/logistics/services/core/service.py` | logic | 1 | M (2h) |
| FILE 115 | `backend/domains/media/services/media_service.py` | logic | 1 | M (2h) |
| FILE 116 | `backend/domains/orders/services/core/logistics.py` | logic | 2 | S (0.5h) |
| FILE 117 | `backend/domains/orders/services/core/order_engine.py` | logic | 1 | S (0.25h) |
| FILE 118 | `backend/domains/orders/services/orders_service.py` | logic | 1 | S (0.5h) |
| FILE 119 | `backend/domains/orders/services/returns/service.py` | logic | 2 | S (0.5h) |
| FILE 120 | `backend/domains/promotions/services/promotions_write_service.py` | logic | 1 | M (3h) |
| FILE 121 | `backend/domains/security/services/fraud/fraud_detection_service.py` | logic | 1 | M (3h) |
| FILE 122 | `backend/domains/suppliers/services/supplier_kyc_service.py` | logic | 1 | M (3h) |
| FILE 123 | `backend/domains/suppliers/services/supplier_service.py` | logic | 1 | S (0.25h) |
| FILE 124 | `backend/modules/customer/routers/finance.py` | logic | 1 | — |
| FILE 125 | `backend/modules/customer/routers/orders.py` | logic | 6 | M (2h) |
| FILE 126 | `backend/modules/customer/routers/promotions.py` | logic | 1 | S (0.5h) |
| FILE 127 | `_most_imp_docx/FEATURES.md` | arch | 1 | S (TBD) |
| FILE 128 | `backend/domains/accounts/services/auth/auth_service.py` | arch | 2 | — |
| FILE 129 | `backend/domains/accounts/services/auth/public_security_registration_service.py` | arch | 1 | S (TBD) |
| FILE 130 | `backend/domains/accounts/services/identity/identity_admin_service.py` | arch | 1 | S (TBD) |
| FILE 131 | `backend/domains/customers/services/cart_service.py` | arch | 1 | S (TBD) |
| FILE 132 | `backend/domains/customers/services/coupons_read_service.py` | arch | 1 | S (TBD) |
| FILE 133 | `backend/domains/finance/ports.py` | arch | 1 | S (1h) |
| FILE 134 | `backend/domains/finance/services/ledger/general_ledger_service.py` | arch | 3 | L (8h) |
| FILE 135 | `backend/domains/governance/services/__init__.py` | arch | 1 | S (TBD) |
| FILE 136 | `backend/domains/governance/services/admin/admin_service.py` | arch | 1 | S (TBD) |
| FILE 137 | `backend/domains/governance/services/operations.py` | arch | 1 | S (TBD) |
| FILE 138 | `backend/domains/governance/services/settings/admin_service.py` | arch | 1 | S (TBD) |
| FILE 139 | `backend/domains/governance/services/settings/governance_package_service.py` | arch | 1 | S (TBD) |
| FILE 140 | `backend/domains/governance/subscribers.py` | arch | 1 | S (TBD) |
| FILE 141 | `backend/domains/hr/ports.py` | arch | 1 | S (TBD) |
| FILE 142 | `backend/domains/hr/services/employees/coi_service.py` | arch | 1 | S (TBD) |
| FILE 143 | `backend/domains/hr/services/hierarchy/hierarchy_service.py` | arch | 1 | S (TBD) |
| FILE 144 | `backend/domains/hr/services/payroll/payroll_engine.py` | arch | 1 | S (TBD) |
| FILE 145 | `backend/domains/hr/subscribers.py` | arch | 1 | S (TBD) |
| FILE 146 | `backend/domains/logistics/services/shipping/service.py` | arch | 1 | S (TBD) |
| FILE 147 | `backend/domains/logistics/services/tracking/service.py` | arch | 1 | S (TBD) |
| FILE 148 | `backend/domains/payments/__init__.py` | arch | 1 | L (8h) |
| FILE 149 | `backend/domains/promotions/services/coupons/commerce_coupons_read_service.py` | arch | 1 | S (TBD) |
| FILE 150 | `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py` | arch | 1 | S (TBD) |
| FILE 151 | `backend/health_test_al7665zt.py` | arch | 1 | S (30m) |
| FILE 152 | `backend/infrastructure/messaging/events/event_publisher.py` | arch | 1 | M (2h) |
| FILE 153 | `backend/infrastructure/messaging/realtime.py` | arch | 1 | S (TBD) |
| FILE 154 | `backend/infrastructure/observability/error_handler.py` | arch | 1 | S (1h) |
| FILE 155 | `backend/infrastructure/observability/logging_config.py` | arch | 1 | S (1h) |
| FILE 156 | `backend/infrastructure/storage/backup.py` | arch | 1 | S (1h) |
| FILE 157 | `backend/infrastructure/utils/background_jobs.py` | arch | 1 | S (TBD) |
| FILE 158 | `backend/infrastructure/utils/schema_audit.py` | arch | 1 | S (TBD) |
| FILE 159 | `backend/infrastructure/valkey/client.py` | arch | 1 | S (TBD) |
| FILE 160 | `backend/main.py` | arch | 1 | S (TBD) |
| FILE 161 | `backend/middleware/dependencies/auth.py` | arch | 1 | M (2h) |
| FILE 162 | `backend/middleware/dependencies/country_detection.py` | arch | 1 | M (1h) |
| FILE 163 | `backend/middleware/webhook_verification.py` | arch | 1 | S (TBD) |
| FILE 164 | `backend/modules/admin/routers/catalog.py` | arch | 1 | S (1h) |
| FILE 165 | `backend/modules/admin/routers/country.py` | arch | 1 | S (TBD) |
| FILE 166 | `backend/modules/admin/routers/orders.py` | arch | 1 | S (TBD) |
| FILE 167 | `backend/modules/customer/routers/accounts.py` | arch | 1 | S (1h) |
| FILE 168 | `backend/modules/customer/routers/catalog.py` | arch | 1 | M (3h) |
| FILE 169 | `backend/modules/employee/routers/hr.py` | arch | 1 | M (3h) |
| FILE 170 | `backend/modules/finance/__init__.py` | arch | 2 | M (2h) |
| FILE 171 | `backend/modules/supplier/routers/country.py` | arch | 1 | S (TBD) |
| FILE 172 | `backend/modules/supplier/routers/hr.py` | arch | 1 | S (TBD) |
| FILE 173 | `backend/modules/supplier/routers/promotions.py` | arch | 1 | S (TBD) |
| FILE 174 | `backend/providers/comms/sms.py` | arch | 1 | S (1h) |
| FILE 175 | `backend/providers/geography/geo.py` | arch | 1 | S (1h) |
| FILE 176 | `backend/providers/image/image.py` | arch | 1 | S (TBD) |
| FILE 177 | `backend/providers/observability/observability.py` | arch | 1 | S (TBD) |
| FILE 178 | `backend/providers/payments/base.py` | arch | 1 | S (TBD) |
| FILE 179 | `backend/providers/payments/config.py` | arch | 1 | M (3h) |
| FILE 180 | `backend/start_backend.ps1` | arch | 1 | S (0.5h) |
| FILE 181 | `frontend/shared/src/components/ui/GlassCard.native.tsx` | arch | 1 | S (TBD) |
| FILE 182 | `frontend/shared/src/permissions.ts` | arch | 1 | M (4h) |
| FILE 183 | `frontend/web_app/src//page.tsx` | arch | 3 | S (TBD) |
| FILE 184 | `frontend/web_app/src//register/page.tsx` | arch | 1 | S (TBD) |
| FILE 185 | `frontend/web_app/src/app/admin/analytics/page.tsx` | arch | 1 | S (TBD) |
| FILE 186 | `frontend/web_app/src/app/admin/audit-logs/page.tsx` | arch | 1 | S (TBD) |
| FILE 187 | `frontend/web_app/src/app/admin/barcode/page.tsx` | arch | 1 | S (TBD) |
| FILE 188 | `frontend/web_app/src/app/admin/catalog/page.tsx` | arch | 1 | S (TBD) |
| FILE 189 | `frontend/web_app/src/app/admin/categories/page.tsx` | arch | 1 | S (TBD) |
| FILE 190 | `frontend/web_app/src/app/admin/commission/page.tsx` | arch | 1 | S (TBD) |
| FILE 191 | `frontend/web_app/src/app/admin/comms-test/page.tsx` | arch | 1 | S (TBD) |
| FILE 192 | `frontend/web_app/src/app/admin/orders/page.tsx` | arch | 2 | L (8h) |
| FILE 193 | `frontend/web_app/src/app/api/auth/social-callback/route.ts` | arch | 1 | S (TBD) |
| FILE 194 | `frontend/web_app/src/app/api/z-rmbg/route.ts` | arch | 1 | S (TBD) |
| FILE 195 | `frontend/web_app/src/app/archive/page.tsx` | arch | 1 | S (TBD) |
| FILE 196 | `frontend/web_app/src/app/cart/page.tsx` | arch | 1 | S (TBD) |
| FILE 197 | `frontend/web_app/src/app/contact/page.tsx` | arch | 1 | S (TBD) |
| FILE 198 | `frontend/web_app/src/app/employee/attendance/page.tsx` | arch | 1 | S (TBD) |
| FILE 199 | `frontend/web_app/src/app/employee/dashboard/page.tsx` | arch | 1 | S (TBD) |
| FILE 200 | `frontend/web_app/src/app/employee/performance/page.tsx` | arch | 1 | S (TBD) |
| FILE 201 | `frontend/web_app/src/app/employee/profile/page.tsx` | arch | 1 | S (TBD) |
| FILE 202 | `frontend/web_app/src/app/employee/schedule/page.tsx` | arch | 1 | S (TBD) |
| FILE 203 | `frontend/web_app/src/app/employee/training/page.tsx` | arch | 1 | S (TBD) |
| FILE 204 | `frontend/web_app/src/app/employee/workspace/page.tsx` | arch | 1 | S (TBD) |
| FILE 205 | `frontend/web_app/src/app/invoice/page.tsx` | arch | 1 | S (TBD) |
| FILE 206 | `frontend/web_app/src/app/logistics-partner/analytics/page.tsx` | arch | 1 | S (TBD) |
| FILE 207 | `frontend/web_app/src/app/logistics-partners/page.tsx` | arch | 1 | S (TBD) |
| FILE 208 | `frontend/web_app/src/app/newsletter/preferences/page.tsx` | arch | 1 | S (TBD) |
| FILE 209 | `frontend/web_app/src/app/newsletter/unsubscribe/page.tsx` | arch | 1 | S (TBD) |
| FILE 210 | `frontend/web_app/src/app/products/category/page.tsx` | arch | 1 | S (TBD) |
| FILE 211 | `frontend/web_app/src/app/products/page.tsx` | arch | 1 | S (TBD) |
| FILE 212 | `frontend/web_app/src/app/verify-email/page.tsx` | arch | 1 | S (TBD) |
| FILE 213 | `frontend/web_app/src/app/wishlist/page.tsx` | arch | 1 | S (TBD) |
| FILE 214 | `frontend/web_app/src/components/ApprovalActionModal.tsx` | arch | 1 | S (TBD) |
| FILE 215 | `frontend/web_app/src/components/BackgroundJobCenter.tsx` | arch | 1 | S (TBD) |
| FILE 216 | `frontend/web_app/src/components/BannerCarousel.tsx` | arch | 1 | S (TBD) |
| FILE 217 | `frontend/web_app/src/components/FraudDetectionDashboard.tsx` | arch | 1 | S (TBD) |
| FILE 218 | `frontend/web_app/src/components/Header.tsx` | arch | 1 | S (TBD) |
| FILE 219 | `frontend/web_app/src/components/MobileSearchOverlay.tsx` | arch | 1 | S (TBD) |
| FILE 220 | `frontend/web_app/src/components/VideoScrollingRow.tsx` | arch | 1 | S (TBD) |
| FILE 221 | `frontend/web_app/src/components/admin/CreateCampaignForm.tsx` | arch | 1 | S (TBD) |
| FILE 222 | `frontend/web_app/src/components/admin/EmailProviderConfigManager.tsx` | arch | 1 | S (TBD) |
| FILE 223 | `frontend/web_app/src/components/admin/EmailSuppressionManager.tsx` | arch | 1 | S (TBD) |
| FILE 224 | `frontend/web_app/src/components/admin/EmailTemplateManager.tsx` | arch | 1 | S (TBD) |
| FILE 225 | `frontend/web_app/src/components/auth/GoogleSignInButton.tsx` | arch | 1 | S (TBD) |
| FILE 226 | `frontend/web_app/src/components/comms/Rail/EmailFolderTree.tsx` | arch | 1 | S (TBD) |
| FILE 227 | `frontend/web_app/src/components/comms/Rail/ThreadContextMenu.tsx` | arch | 1 | S (TBD) |
| FILE 228 | `frontend/web_app/src/components/country/CountryResearchPanel.tsx` | arch | 1 | S (TBD) |
| FILE 229 | `frontend/web_app/src/components/country/CountryStaffAssignmentModal.tsx` | arch | 1 | S (TBD) |
| FILE 230 | `frontend/web_app/src/components/country/GhostRowForm.tsx` | arch | 1 | S (TBD) |
| FILE 231 | `frontend/web_app/src/components/country/LegalContractGenerator.tsx` | arch | 1 | S (TBD) |
| FILE 232 | `frontend/web_app/src/components/country/ParcelTracker.tsx` | arch | 1 | S (TBD) |
| FILE 233 | `frontend/web_app/src/components/country/ShiftHandoverModal.tsx` | arch | 1 | S (TBD) |
| FILE 234 | `frontend/web_app/src/components/ems/ActivityTimeline.tsx` | arch | 1 | S (TBD) |
| FILE 235 | `frontend/web_app/src/components/ems/OrgChartTree.tsx` | arch | 1 | S (TBD) |
| FILE 236 | `frontend/web_app/src/components/ems/PayrollWorkflow.tsx` | arch | 1 | S (TBD) |
| FILE 237 | `frontend/web_app/src/hooks/useApprovalCheck.ts` | arch | 1 | S (TBD) |
| FILE 238 | `frontend/web_app/src/hooks/useCountryAutoPopulate.ts` | arch | 1 | S (TBD) |
| FILE 239 | `frontend/web_app/src/hooks/useCrossBorder.ts` | arch | 1 | S (TBD) |
| FILE 240 | `frontend/web_app/src/hooks/useSendMessage.ts` | arch | 1 | S (TBD) |
| FILE 241 | `frontend/web_app/src/hooks/useThreadMessages.ts` | arch | 1 | S (TBD) |
| FILE 242 | `frontend/web_app/src/hooks/useUnifiedInbox.ts` | arch | 1 | S (TBD) |
| FILE 243 | `frontend/web_app/src/lib/api/client.ts` | arch | 2 | S (TBD) |
| FILE 244 | `frontend/web_app/src/lib/api/country.ts` | arch | 1 | S (TBD) |
| FILE 245 | `frontend/web_app/src/lib/api/queryStates.ts` | arch | 1 | S (TBD) |
| FILE 246 | `frontend/web_app/src/lib/api/schema.d.ts` | arch | 1 | S (TBD) |
| FILE 247 | `frontend/web_app/src/lib/authCapabilities.ts` | arch | 1 | S (TBD) |
| FILE 248 | `frontend/web_app/src/lib/cartStore.ts` | arch | 1 | S (TBD) |
| FILE 249 | `frontend/web_app/src/lib/crossBorderService.ts` | arch | 1 | S (TBD) |
| FILE 250 | `frontend/web_app/src/lib/hierarchyApi.ts` | arch | 1 | S (TBD) |
| FILE 251 | `frontend/web_app/src/lib/payoutsApi.ts` | arch | 1 | S (TBD) |
| FILE 252 | `frontend/web_app/src/lib/uploadOrchestrator.ts` | arch | 1 | S (TBD) |
| FILE 253 | `frontend/web_app/src/lib/useAdminApi.ts` | arch | 1 | S (TBD) |
| FILE 254 | `frontend/web_app/src/lib/useAuth.tsx` | arch | 1 | S (TBD) |
| FILE 255 | `frontend/web_app/src/lib/useBgABTest.ts` | arch | 1 | S (TBD) |
| FILE 256 | `frontend/web_app/src/lib/useBgRecommendations.ts` | arch | 1 | S (TBD) |
| FILE 257 | `frontend/web_app/src/lib/wishlistStore.ts` | arch | 1 | S (TBD) |
| FILE 258 | `frontend/web_app/src/shared/api-core.ts` | arch | 1 | S (TBD) |
| FILE 259 | `frontend/web_app/src/shared/realtime.ts` | arch | 1 | S (TBD) |
| FILE 260 | `frontend/web_app/src/shared/returnsApi.ts` | arch | 1 | S (TBD) |
| FILE 261 | `package.json` | arch | 1 | S (1h) |
| FILE 262 | `.pre-commit-config.yaml` | security | 1 | S |
| FILE 263 | `backend/_tmp_check_setcookie.py` | security | 1 | S (1h) |
| FILE 264 | `backend/domains/audit/services/worm_audit.py` | security | 1 | M (3h) |
| FILE 265 | `backend/infrastructure/security/dependencies.py` | security | 1 | S (1h) |
| FILE 266 | `backend/modules/admin/routers/comms.py` | security | 1 | S (0.5h) |
| FILE 267 | `backend/rbac/models/permission_entities.py` | security | 1 | L (8h) |
| FILE 268 | `_browser_test/COVERAGE_GAPS.md` | frontend | 1 | S (1h) |
| FILE 269 | `frontend/mobile_app/app/_layout.tsx` | frontend | 1 | S (1h) |
| FILE 270 | `frontend/mobile_app/lib/api.ts` | frontend | 1 | M (3h) |
| FILE 271 | `frontend/web_app/next.config.ts` | frontend | 1 | S (1h) |
| FILE 272 | `frontend/web_app/package.json` | frontend | 1 | S (0.5h) |

## Findings marked INVALID

Counter-evidence only. Nothing deleted. Each of these was refuted by a
verification agent against live source.

**155 findings** marked INVALID. Full list with counter-evidence: `_audit/compiler/_excluded.json`.

## Findings marked RESOLVED (already fixed)

**260 findings** were already fixed in the current tree. Many are law-coverage attestations rather than defects: `09_laws` alone contributed 144 rows where the audit recorded no violation. Full list with verify output: `_audit/compiler/_excluded.json`.

## Cross-cutting findings moved to Codebase Implementation

Compiler §0.4 rule 15. These carry no single repo `File:Line`.

| Agent | Candidate | Why cross-cutting |
|---|---|---|
| `COMP-V31-00_boot_smoke_test` | `CG-01 / BOOT-007+BOOT-003 merged` | next.config.ts:6-8 ignoreBuildErrors:true suppresses 119 tsc errors across 29 files and makes `next build` exit 0. No single File:Line can describe it, it governs the entire web_ap |
| `COMP-V31-00_boot_smoke_test` | `BOOT-008` | Governs the whole codebase's testability, not one file. 24 documented command sites across 3 canonical prompt documents all name a `test/` tree that does not exist. Per CROSS_AGENT |
| `COMP-V31-00_boot_smoke_test` | `CG-02` | backend/main.py:99 imports `infrastructure.utils.tracing`; the module is at backend/infrastructure/observability/tracing.py:43. The entire OpenTelemetry stack (Law 93, TECHNOLOGY_S |
| `COMP-V31-00_boot_smoke_test` | `CG-04 / Law 217` | The no-auto-migrate guarantee (backend/lifespan.py:60-85 + backend/infrastructure/database/database.py:558-590) is a global boot-time invariant that must hold for every replica. It |
| `COMP-V31-00_boot_smoke_test` | `CG-06 / manifest drift` | backend/requirements.txt and backend/pyproject.toml disagree with each other AND with TECHNOLOGY_STACK.md on fastapi, starlette, prometheus-fastapi-instrumentator and uv. Both Dock |
| `COMP-V19-01_architectural` | `01_architectural-P1` | Applies to 168 files / 709 import edges across 15 domains. No single File:Line can carry it. This is the Codebase Implementation (Over All) item for Law 3. |
| `COMP-V19-01_architectural` | `01_architectural-P1 (Law 99 half)` | modules -> infrastructure = 254 import edges across 96 files (96 files confirmed exactly; the sibling's '252/96' is corroborated). Dominated by infrastructure.database (96 files) a |
| `COMP-V19-01_architectural` | `ARCH-013` | The `_LAZY_SERVICE_EXPORTS` + `__getattr__` service-locator appears in 3 ports.py files with 90 lazy exports total (finance 65, catalog 17, accounts 8) and defeats Law 155's thin-r |
| `COMP-V19-01_architectural` | `GATE-test_import_laws (no packet record)` | `backend/tests/architecture/test_import_laws.py` reports GREEN while enforcing nothing. It is the gate named by Law 212 for Laws 1/97/98 and it is the Test path cited by 4 of the 1 |
| `COMP-V19-01_architectural` | `LAW-12-13 (no packet record as a test)` | Law 12 (15 domains) and Law 13 (5 modules) are the only two structural laws with a trivially checkable invariant (a directory listing), and the repo has NO test for either. Both ar |
| `COMP-V06-02_technological` | `GAP-TECH-A` | GOVERNS 16 OF 55 RECORDS. Applies to no single File:Line - it is the structural cause behind TECH-001, TECH-002, TECH-003, TECH-004, TECH-008, TECH-009, TECH-016, TECH-017, TECH-01 |
| `COMP-V06-02_technological` | `GAP-TECH-C` | GOVERNS 7 OF 55 RECORDS + the mobile workspace. Applies to frontend/mobile_app/pnpm-lock.yaml as a whole (11,755 lines), not to a File:Line. The lockfile is STALE against its own m |
| `COMP-V06-02_technological` | `GAP-TECH-B` | INDEPENDENT VERIFICATION RESULT - THE BATCH-1 CLAIM IS A FALSE POSITIVE. Batch 1 asserted that `import providers` FAILS because `backend/providers/metrics.py:1` imports `Gauge` fro |
| `COMP-V06-02_technological` | `GAP-TECH-G` | pnpm MAJOR-VERSION CONTRADICTION ACROSS 3 FILES, not found by any record. frontend/web_app/package.json:5 declares `"packageManager": "pnpm@11.9.0"`; frontend/web_app/Dockerfile:17 |
| `COMP-V06-02_technological` | `GAP-TECH-I` | CI SUPPLY-CHAIN AND RUNTIME GAP covering .github/workflows/*.yml as a whole. My grep for syft|sbom|cyclonedx|trivy|cosign|gitleaks|pip-audit across all five workflow files (ci.yml, |
| `COMP-V06-02_technological` | `GAP-TECH-J` | UNVERIFIABLE TEST PATHS - 24 of 55 records cite a Test path that does not exist. Verified False: tests/domains/accounts/test_auth.py (cited by TECH-020, TECH-021, TECH-022, TECH-02 |
| `COMP-V06-02_technological` | `GAP-TECH-E` | EXTRA-SPECIFIER DRIFT between the two backend manifests, affecting a whole class of packages rather than one line. backend/requirements.txt:62 declares `sentry-sdk[fastapi]==2.68.1 |
| `COMP-V06-02_technological` | `GAP-TECH-D` | SECTION 4 CAPABILITY DECLARED BUT UNIMPLEMENTED - affects 4 records' blast radius. backend/requirements.txt declares `puremagic==2.2.0` (the SECTION 4 canonical replacement for pyt |
| `COMP-V09-03_logical` | `CLUSTER-stub-subscribers` | Applies to 17 files and has no single File:Line. Every domain ships a subscribers.py (accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logis |
| `COMP-V09-03_logical` | `CLUSTER-float-money` | Applies to ~265 files. My scan counts 1357 occurrences across 754 files in backend/domains and 1813 across 1778 files (excluding .venv) in the full backend. Per-domain: logistics 3 |
| `COMP-V09-03_logical` | `CLUSTER-idempotency` | Governs all four endpoint classes Law 239 names (payment, order creation, refund, webhook) plus the platform's cache-failure posture, spanning at least 8 files across 4 domains (fi |
| `COMP-V09-03_logical` | `CLUSTER-silent-except` | Governs the whole codebase and has no single File:Line. AST walk of backend/domains (754 files): 765 total except handlers, 48 pass-only handlers, 206 handlers with neither a log c |
| `COMP-V22-04_operational` | `XCC-OPS-01` | Governs the whole codebase via backend/config.py. Ops-004, Ops-005, Ops-006 and Ops-009 are one defect, not four: backend/config.py declares the typed field (config.py:206-208 cele |
| `COMP-V22-04_operational` | `XCC-OPS-02` | Governs the whole codebase via backend/jobs/celery_app.py. The Celery task-identity split (`jobs.*` vs `tasks.*`) is a single root cause with codebase-wide blast radius: it breaks  |
| `COMP-V22-04_operational` | `XCC-OPS-03` | Governs the whole codebase via .github/workflows/* — explicitly named in compiler §0.15 as a cross-cutting location. One root cause, four symptoms: (a) OPS-002's pipeline deploys t |
| `COMP-V22-04_operational` | `XCC-OPS-04` | Governs the whole codebase via backend/main.py — also explicitly named in compiler §0.15. The Law 81 health surface is one coherent, under-specified subsystem: three endpoints, one |
| `COMP-V28-05_wiring` | `WIRE-003` | Cross-cutting by every test in compiler 0.4 rule 15. Governs all 16 domain events.py files, all 117 publish_* helpers, the single event_bus.py, jobs/event_workers.py, and lifespan. |
| `COMP-V28-05_wiring` | `WIRE-002` | Cross-cutting and P0. `set_rls_context` is called from ~25 service files across catalog, finance, logistics, orders, promotions, hr, governance, seed and both module routers; the s |
| `COMP-V28-05_wiring` | `WIRE-007` | Has no single point of failure - it governs the whole request pipeline. `orchestrator.py` is the single registration point for all 17 middleware, so the CORS-not-in-a-layer finding |
| `COMP-V28-05_wiring` | `05_wiring-P1` | Same cross-cutting scope as WIRE-003 (all domains/*/events.py). Listed separately because it is the queue-level representation of that cluster and the orchestrator groups by file l |
| `COMP-V32-06_database` | `DB-001` | Governs the whole repository's deployability, not a single File:Line. The committed migration chain has 4 heads, 2 duplicate revision ids, 3 revisions that fail at import, and 28 o |
| `COMP-V32-06_database` | `DB-005` | No single File:Line governs this. Three mutually inconsistent RLS session-variable names are used across 4 mechanisms in 4 files (middleware/country_context.py:272, domains/account |
| `COMP-V32-06_database` | `DB-006` | Duplicate `def instrument_rls` + a non-existent import target (`_engine`) + a boot-time `install_rls_policies(engine)` defaulting to schema='public' means the country-isolation mec |
| `COMP-V32-06_database` | `DB-003` | 308 relationship() call sites across backend/domains — far above the >=5-files threshold in compiler §0.4, and its blast radius (F-003/F-004/F-005) spans checkout/cart/order/logist |
| `COMP-V32-06_database` | `DB-008` | Connection-config finding with repo-wide reach: the statement-cache omission exists on all three engines (sync database.py:129, async :221, replica :348), and the DB_STATEMENT_TIME |
| `COMP-V08-07_CONTRADICTIONS` | `07_CONTRADICTIONS-P1` | Aggregates 17 findings (CONTRAD-005..018, 035, 036) across the dependency manifests with no single File:Line, and it governs every backend import. It is a manifest-wide reconciliat |
| `COMP-V08-07_CONTRADICTIONS` | `07_CONTRADICTIONS-P0` | Governs the module and domain package trees wholesale (Law 12 + Law 13) and has no single File:Line. Touching backend/modules/ or backend/domains/ at all collides with it under res |
| `COMP-V08-07_CONTRADICTIONS` | `TT-01 (dev-database topology)` | Not in any packet. Governs docker-compose.yml, docker-compose.override.yml, backend/Dockerfile, backend/Dockerfile.prod, .env, .env.example and backend/.env simultaneously, and no  |
| `COMP-V08-07_CONTRADICTIONS` | `TT-02 (DEFAULT_COUNTRY)` | One env var, but its value flows into the Law 5 RLS session context, into localisation, and into tax rules, so it has no single File:Line scope. |
| `COMP-V01-07_tables_fields` | `TF-001` | Governs the whole codebase and has no resolvable single File:Line for its open half. backend/alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py:31 performs a bare `fro |
| `COMP-V01-07_tables_fields` | `TF-039` | Law 21 (server_default=func.now() on timestamps) is violated in 150 records spanning 25 files -- the single largest cluster in this dimension. backend/domains/comms/models/chat.py: |
| `COMP-V01-07_tables_fields` | `TF-058` | Law 5/20/23 (country_code on every user-facing table) is violated in 42 records across 12 files, and the runtime architecture test already quantifies it: `pytest tests/architecture |
| `COMP-V01-07_tables_fields` | `TF-002` | Has no single File:Line by construction -- File:Line is the bare string ':' in all 14 records (TF-002..TF-015), which is the compiler's definition of cross-cutting (rule 0.4-15). T |
| `COMP-V01-07_tables_fields` | `TF-016` | Law 55/152 (schema-per-domain) has exactly two offenders repo-wide, `payroll_records` and `employee_trainings` at backend/domains/hr/models/employee_models.py:542 and :572. Runtime |
| `COMP-V05-08_providers` | `Law 129 - no provider exposes health_check(), and /health/deps does not consume one` | Applies to 64 of 66 records (every module except payments/base and async_workers). Only providers/_base.py:34 and :68 define health_check; ZERO provider modules implement it and ZE |
| `COMP-V05-08_providers` | `Law 128 - providers/async_workers is effectively dead code` | backend/providers/async_workers.py exists (479 lines, HAS_ASYNC_WORKERS at :32, bounded ThreadPoolExecutor at :48-52) and is mandated by ARCHITECTURE_STACK section 3 and TECHNOLOGY |
| `COMP-V05-08_providers` | `HAS_<SDK> flag NAMES are inconsistent across the tree` | 18 of 66 records have a wrong or absent flag name: ai/{ai_research_jobs,ai_service,huggingface,categorization,chatbot,finance_ai,price_intelligence,recommendation,search,text,visio |
| `COMP-V05-08_providers` | `Circuit breakers use a non-canonical library (pybreaker declared, never imported)` | TECHNOLOGY_STACK section 5 mandates pybreaker 1.4.1. It is declared at backend/requirements.txt:76 but imported by zero first-party modules; all provider breakers use backend/infra |
| `COMP-V05-08_providers` | `Circuit-breaker / timeout / retry inventory columns are broadly STALE` | The 2026-09-30 inventory says circuit_breaker=No for all 66 records; in fact 8 provider modules now carry a breaker. It says timeout=No for all 66; in fact 20 modules set an explic |
| `COMP-V05-08_providers` | `Error mapping (Law 130) is claimed for 20 modules that define no exception class` | The inventory names an error_mapping exception for ai_research_jobs (AIResearchError), ai_service (AIServiceError), categorization, chatbot, finance_ai, price_intelligence, recomme |
| `COMP-V05-08_providers` | `test_mocks column is wrong in both directions across 15 records` | FALSE POSITIVES - claimed 'Yes (test_provider_health.py)' but test_provider_health.py contains zero references to the module: automation.scheduler, comms.email, news.rss_provider,  |
| `COMP-V02-09_laws` | `FIND-09-006` | Law 3 / 1 / 17 / 97. 698 cross-domain non-ports import statements across 165 files and 14 domains, with TWO currently-failing repository architecture tests (test_law3_cross_domain. |
| `COMP-V02-09_laws` | `FIND-09-011` | Law 44. Governs the entire codebase via .github/workflows/* and has no single File:Line. Named explicitly in my task brief as an expected cross-candidate. Causally upstream of the  |
| `COMP-V02-09_laws` | `FIND-09-003` | Law 27. 90 files (75 health_test_*.py + 15 _tmp_*.py) at backend/ root, which is a governed location under Law 18. One deletion sweep plus a root-hygiene test closes it and prevent |
| `COMP-V02-09_laws` | `09_laws-84` | Law 84 / 203. 94 raw os.getenv() calls across 27 non-test production files spanning providers, infrastructure, domains, middleware and jobs, with no test guarding it and no single  |
| `COMP-V02-09_laws` | `FIND-09-007` | Law 59. 389 unlogged except handlers spread across 15+ domain and infrastructure files, top concentration auth_service.py (16), fraud_detection_service.py (9), logistics/core/servi |
| `COMP-V02-09_laws` | `09_laws-6` | Law 6 / 55. Schema discipline governs every model file in backend/domains (333 models). Beyond the known media/payments sprawl it hides two models with NO schema declaration at all |
| `COMP-V02-09_laws` | `FIND-09-014` | Law 2 / 14 / 90. The violation is one 62-line function (modules/customer/routers/orders.py:135-196), but the ENFORCEMENT gap is cross-cutting: test_architecture_gates.py::test_no_n |
| `COMP-V02-09_laws` | `09_laws-99` | Law 99. 252 module->infrastructure imports across 96 module files (120 -> infrastructure.database, 79 -> infrastructure.security, 53 -> infrastructure.utils), with no test gating L |
| `COMP-V04-10_migrations` | `10_migrations-Runtime--alembic-heads` | The `alembic heads` failure is a single configuration defect (ini in the wrong directory + 8 migration files doing bare `from migration_helpers import`) that blocks every read-only |
| `COMP-V04-10_migrations` | `NAMING-CONVENTION-97pct` | Applies to 71 of 75 migration files. Renaming a migration file does not change its revision id (Alembic keys on the in-file `revision`), so this is mechanically fixable repo-wide,  |
| `COMP-V04-10_migrations` | `INCOMPLETE-DOWNGRADES` | 3 confirmed downgrade gaps across 3 files (10_migrations-11 accidental/lossy, 10_migrations-56 deliberate/WORM, plus the 5 CREATE EXTENSION statements in 10_migrations-05 left in p |
| `COMP-V10-11_environmental` | `ENV-01` | Governs >=5 files by construction and has no single File:Line that captures it. Applies to 59 production .py files / 156 raw call sites across backend/infrastructure/database/datab |
| `COMP-V10-11_environmental` | `11_environmental-2` | A single validator pair - _validate_production (:598-776) and _validate_required_secrets_in_non_production (:384-452) - governs every config record in this packet and every other f |
| `COMP-V10-11_environmental` | `11_environmental-1` | The Settings field surface (188 fields at backend/config.py:99-305) is the single source of truth for the whole backend's configuration and is the natural home for two codebase-wid |
| `COMP-V10-11_environmental` | `ENV-06` | Nominally one file, but the class of defect it represents - un-interpolated secret literals in committed config - spans monitoring/docker-compose.monitoring.yml (2 remaining: :72,  |
| `COMP-V23-12_tests` | `GREEN-ARCHITECTURE-GATE-IS-NOT-EVIDENCE` | Governs the whole codebase and is the single highest-leverage finding of this dimension. Nine architecture gates that PASS do so without enforcing anything: (1) test_law6_schema_di |
| `COMP-V23-12_tests` | `TESTS-VS-TEST-PATH-MISMATCH (corroborates T15)` | Repo-wide and dimensional. Two independent test trees exist - backend/tests/ (4728 collected) and root tests/ (1734 collected, 46 .py files) - and the benchmark specifies a single  |
| `COMP-V23-12_tests` | `PROVIDER-TEST-CASCADE-IS-PYTEST-SYSPATH-SHADOWING-NOT-CREDENTIALS` | Affects the whole provider test surface and refines CROSS_AGENT_FINDINGS T1. The reported cause ('leaked sk_test_dummy credentials breaking config assertions' + 'ModuleNotFoundErro |
| `COMP-V23-12_tests` | `LAW-209-ROLE-FIXTURES-ABSENT` | Governs the entire authorization test matrix, not one file. ARCHITECTURE_STACK.md:740 (Law 209) requires demo users admin@zozi.com, supplier@zozi.com, customer@zozi.com, logistics- |
| `COMP-V33-12_tests_collection_verify` | `GAP-01 · working-directory seam / path-convention ambiguity` | Applies to >=5 files and governs the whole codebase's test contract. No single File:Line can fix it: there is NO pytest configuration at the repo root, the only pytest config is ba |
| `COMP-V33-12_tests_collection_verify` | `GAP-08 · CI exercises 5.3% of the test suite` | Governs the whole codebase via .github/workflows/*.yml (5 files). 345 of 6469 collectable tests run in CI (23 in the architecture step, 322 in the domain step). ARCHITECTURE_STACK. |
| `COMP-V33-12_tests_collection_verify` | `GAP-07 · the Law 71 self-gate is vacuous` | backend/tests/architecture/test_law58_through_law74.py:225-239 `TestLaw71NoBrokenTestsInCI.test_all_test_files_are_importable` only `ast.parse()`s files in backend/tests/architectu |
| `COMP-V33-12_tests_collection_verify` | `GAP-03 · pytest configuration lives only in backend/pyproject.toml` | Governs the whole codebase (no root pyproject.toml / pytest.ini / tox.ini / setup.cfg). Consequences observed: (a) a bare `pytest` at the root has no `testpaths`, so it sweeps 7 sc |
| `COMP-V17-13_dev_to_prod` | `LAW-217-ROLLOUT-GATING-AND-ALEMBIC-INVOCATION` | Governs three separate concerns across 3 files (.github/workflows/deploy.yml, .github/workflows/rollback.yml, backend/alembic/alembic.ini) with no single File:Line anchor. Law 217  |
| `COMP-V17-13_dev_to_prod` | `CI-WORKFLOWS-SUBSTANTIVELY-EMPTY-OF-SECURITY-AND-FRONTEND` | No single File:Line; spans all 5 workflow files. The CI surface exists (refuting D2P-001/CLUSTER-missing-ci) but is hollow in ways no packet record captures: grep for `pip-audit|gi |
| `COMP-V17-13_dev_to_prod` | `GIT-CONVENTION-NOT-ENFORCED-ANYWHERE` | No single File:Line; spans .pre-commit-config.yaml, all workflows, and git history. Law 241 (conventional commits), Law 242 (PR-only, no direct main pushes) and Law 243 (pre-commit |
| `COMP-V17-13_dev_to_prod` | `RAILWAY-VS-COOLIFY-TOPOLOGY-SPLIT` | Governs the whole codebase's deployment story with no single line: railway.toml (tracked), deploy.yml (4 Railway jobs), rollback.yml (Railway + Vercel), vercel.json, ARCHITECTURE_D |
| `COMP-V12-13_dev_to_prod_docker_verify` | `GATE-DEPLOY-MIGRATION-BROKEN` | Governs the whole codebase and has no single File:Line as the defect site — it is a three-file path. The only migration step in the entire deploy pipeline fails. (1) The ONLY alemb |
| `COMP-V12-13_dev_to_prod_docker_verify` | `DEPLOY-TOPOLOGY-DOES-NOT-MATCH-LAW-216` | Whole-codebase config drift with no single File:Line, spanning Law 216 (production targets) and Law 220 (env promotion). Implemented: Railway for the backend (railway.toml:1-13, de |
| `COMP-V12-13_dev_to_prod_docker_verify` | `CI-WORKFLOW-SET-DOES-NOT-MATCH-TECHNOLOGY-STACK-19` | A workflow-directory-level gap affecting every CI gate, with no single File:Line. TECHNOLOGY_STACK.md:288 names five workflows: `ci.yml`, `schema-drift.yml`, `docs-drift.yml`, `e2e |
| `COMP-V12-13_dev_to_prod_docker_verify` | `PROD-COMPOSE-UNDEFINED-SERVICE-db` | A single-line defect that silently breaks the entire production data path, and the only claim in this packet that survives contact with `docker compose config`. docker-compose.prod |
| `COMP-V12-13_dev_to_prod_docker_verify` | `LAW-217-GUARD-IS-COMPLETE-AT-THE-CODE-LEVEL` | Recorded as a cross-cutting candidate because it is a whole-codebase property that had to be established by tracing every boot path, and because it is the dimension's primary bench |
| `COMP-V16b-17_dev_to_prod` | `LAW-44-NO-CI-SECURITY-SCANNING` | Governs the whole codebase and has no single File:Line. Zero hits for pip-audit|gitleaks|trivy|npm audit|dependabot|cosign|syft across all 5 workflows, and no .github/dependabot.ym |
| `COMP-V16b-17_dev_to_prod` | `LAW-216-DEPLOY-TARGET-MISMATCH` | No single File:Line; spans benchmark vs all CI workflows vs all compose files. Law 216 and TECHNOLOGY_STACK.md:271-274 mandate Hostinger VPS + Coolify + Cloudflare Pages. The repo  |
| `COMP-V16b-17_dev_to_prod` | `LAW-32-COMMITTED-SECRET-IN-CI-WORKFLOW` | Governs every workflow. A literal SECRET_KEY is committed in TWO tracked workflow files: .github/workflows/ci.yml:20 and .github/workflows/deploy.yml:48, both 51-char and 25-char l |
| `COMP-V16b-17_dev_to_prod` | `SUPPLY-CHAIN-UVLOCK-VS-REQUIREMENTS` | Governs every container build. Both Dockerfiles install from backend/requirements.txt, never from uv.lock: backend/Dockerfile.prod:16-17 (`COPY requirements.txt .` / `RUN pip insta |
| `COMP-V13-14_frontend_web` | `14_frontend_web-4` | frontend/web_app/tailwind.config.js is a single 235-line config file that governs the whole codebase's styling tokens, yet it is NEVER LOADED under Tailwind v4. Applies to >= 42 fi |
| `COMP-V13-14_frontend_web` | `14_frontend_web-14` | No observability instrumentation anywhere in frontend/web_app/src: no web-vitals / reportWebVitals / onLCP / onCLS / onINP (0 matches), no instrumentation.ts, and — discovered whil |
| `COMP-V13-14_frontend_web` | `14_frontend_web-P2` | Push-notification infrastructure is absent platform-wide: no push SDK in either package.json, no service worker anywhere in src, no manifest.json or sw.js in public/. Cross-cutting |
| `COMP-V13-14_frontend_web` | `14_frontend_web-14 (CSP/SRI)` | Laws 285 (CSP with nonces) and 286 (SRI integrity hashes) are unimplemented for the web app: no CSP header or nonce machinery, no integrity= attribute anywhere, and vercel.json set |
| `COMP-V13-14_frontend_web` | `14_frontend_web-15 (lockfile drift)` | frontend/web_app ships BOTH pnpm-lock.yaml and package-lock.json. The npm lockfile is the only record of the Law-171-forbidden @tanstack/react-query, so the two problems are one pr |
| `COMP-V27-15_frontend_mobile` | `MANIFEST-vs-LOCKFILE-DIVERGENCE (frontend/mobile_app)` | Governs the whole package, not one File:Line. frontend/mobile_app/pnpm-lock.yaml is a snapshot of a COMPLETELY DIFFERENT package.json - it is not merely stale on two pins, it descr |
| `COMP-V27-15_frontend_mobile` | `CONFIGURED-BUT-UNINSTALLED-DEPENDENCY-SET (frontend/mobile_app)` | Applies across 13 packages at once: expo-updates, expo-location, expo-notifications, lucide-react-native, @react-native-async-storage/async-storage, @stripe/stripe-react-native, @r |
| `COMP-V27-15_frontend_mobile` | `EAS-BUILD-ABSENT (Law 194)` | No eas.json anywhere (Test-Path frontend/mobile_app/eas.json = False); app.json declares no runtimeVersion and no extra.eas.projectId; .github/workflows has no mobile job. Law 194  |
| `COMP-V27-15_frontend_mobile` | `SHARED-MONEY-UNUSED (Law 19 / Law 195 / Law 263-equivalent)` | frontend/shared/src/money.ts (the §17-mandated Intl.NumberFormat helper) is imported by ZERO mobile files. Money is rendered by a mobile-local Intl.NumberFormat in lib/currencyStor |
| `COMP-V27-15_frontend_mobile` | `MOB-005 + MOB-006 (social sign-in)` | Three providers non-functional across two modules (lib/authStore.ts:107-136 and lib/socialAuth.ts:117-146). The fix necessarily spans both files plus package.json plus app.json plu |
| `COMP-V07-16_features` | `FEAT-008` | Governs every module, not one file. _ROLE_FEATURES (backend/rbac/dependencies.py:60-163) grants 4-35 atoms per role while the module routers declare 31-66 distinct gates per module |
| `COMP-V07-16_features` | `FEAT-019` | rbac/ is claimed in multiple dimensions (16_features here; Law 4/161/166 coverage elsewhere). The specific issue — WORM audit enforcement for permission changes — applies to every  |
| `COMP-V07-16_features` | `FEAT-042` | Playwright coverage is a whole-tree property (54 spec files across web_app/e2e/) with no single File:Line, and it is the verification surface for every money-path chain in _audit/1 |
| `COMP-V18-17_code_file_management` | `ROOT-TEMP-POLLUTION` | 118 of 121 files at backend/ root are non-canonical, of which 97 match temp/debug patterns (75 health_test_*.py, 15 _tmp_*.py, 7 check_*.py) plus alembic_chain.py/.txt, _audit_boot |
| `COMP-V18-17_code_file_management` | `LAW7-ALLOWLIST-ENFORCEMENT-IS-BROKEN` | Law 7's 'may only shrink' is not actually enforced anywhere, which makes the 20 dated entries in backend/DOMAIN_ALLOWLIST.yaml unenforceable debt. Three independent defects, each i |
| `COMP-V18-17_code_file_management` | `HR-SHADOWING-CLASS` | backend/modules/employee/routers/hr.py (1231 lines / 55921 bytes / 97 routes) is unreachable because the hr/ package shadows it - proven at runtime, not by inspection (importlib re |
| `COMP-V18-17_code_file_management` | `ARCHIVED-MODULE-LIABILITY` | 16 files inside domains/ (12 promotions, 1 catalog, 1 orders, 1 suppliers) carry the header 'Retained for reference only; this file is NOT part of the running application.' That he |
| `COMP-V18-17_code_file_management` | `ARCH-VS-REAL-DOMAIN-MODULE-COUNT` | ARCHITECTURE_STACK.md:538 (Law 12) fixes 15 domains and :539 (Law 13) fixes 5 modules. Reality: 17 domain packages (+media, +payments) and 6 modules (+finance). Neither extra is in |
| `COMP-V20-18_security` | `LAW-37-VALKEY-NOOP-CHAIN` | Governs the whole codebase rather than any single File:Line, and spans at least 6 files: infrastructure/valkey/client.py (44-102 _NoOpValkey/_NoOpValkeyPipeline, 159-167 fallback), |
| `COMP-V20-18_security` | `LAW-275-39-TOKEN-TYPE-AND-CIPHER-SPLIT` | No single canonical auth/encryption location is enforced. infrastructure/security/auth.py (canonical, 455 lines), infrastructure/utils/auth.py (4-line star-import shim), providers/ |
| `COMP-V20-18_security` | `LAW-34-FSTRING-SQL-SWEEP` | f-string SQL appears in at least 8 non-test backend files across 4 layers (alembic migrations, domains/analytics, infrastructure/security, backend/scripts, backend root) plus two r |
| `COMP-V20-18_security` | `LAW-43-NO-SECURITY-EVENT-LOGGING` | Auth failures are logged at WARNING (authentication_middleware.py:60-68) and webhook rejections at WARNING (webhook_verification.py:93), but 403 denials (rbac/dependencies.py:194-2 |
| `COMP-V26-19_performance` | `LAW45-CLASS-303` | Applies to 38 distinct model files (40 counting non-domain model modules), far above the >=5-file threshold, and has no single File:Line. My AST measurement over backend/domains/** |
| `COMP-V26-19_performance` | `LAW222-OFFSET-82` | Applies to 54 files / 82 real .offset() calls in the adoption layer (domains/, modules/, infrastructure/, middleware/), well past the >=5-file threshold, and is governed by a singl |
| `COMP-V26-19_performance` | `LAW47-LAW260-POOL` | backend/infrastructure/database/database.py governs connection pooling for the entire application and has no single defect line - it is a config-origin question. Verified actuals:  |
| `COMP-V26-19_performance` | `LAW48-LAW261-NO-READ-REPLICA` | Cross-cutting by construction: the wiring exists in exactly one file (backend/infrastructure/database/database.py:363 get_read_db) and the question is whether ANY service uses it.  |
| `COMP-V26-19_performance` | `LAW227-RLS-SET-LOCAL` | The Law 227 / Law 5 requirement - set_rls_context() executes SET LOCAL app.country_code = :cc inside the active transaction, session-level SET forbidden under the Neon pooler - is  |
| `COMP-V26-19_performance` | `LAW73-NO-PERF-TESTS` | Confirmed by direct observation, corroborating COMP-V23-12_tests. backend/tests/performance/ DOES NOT EXIST (Test-Path False) and neither does tests/performance/. A scan of both te |
| `COMP-V11-20_observability_resilience` | `20_observability_resilience-P1` | Governs the whole codebase: request_id correlation is a platform-wide invariant (Law 93) touching middleware, every domain service, the error handler, and the RFC 7807 response env |
| `COMP-V11-20_observability_resilience` | `OBS-106` | Applies to well over 5 files: 8 of 94 backend/providers modules have breakers, 86 do not, and the 86 span geography, comms/whatsapp, finance/bank-api, ai, barcode, ocr, qr and imag |
| `COMP-V11-20_observability_resilience` | `backend/infrastructure/observability/logging_config.py (Law 58 / Law 282 enforcement)` | Governs the entire codebase and has no single File:Line. Law 58 (no print()) and Law 282 (PII masking) are enforced ONLY by the structlog _scrub_pii processor at logging_config.py: |
| `COMP-V11-20_observability_resilience` | `backend/requirements.txt vs backend/pyproject.toml observability drift` | Both files govern dependency resolution for the whole codebase and they disagree on four observability rows (prometheus-fastapi-instrumentator 8.1.0 vs 7.1.0; sentry-sdk 2.68.1 vs  |
| `COMP-V11-20_observability_resilience` | `readiness_require_email / readiness_require_payments dead settings` | backend/config.py:33-35, 200-201 declares three readiness flags; only readiness_require_valkey is ever read, and only inside /health rather than /health/ready. /health/ready (main. |
| `COMP-V14-21_contradictions` | `21_contradictions-16` | The hr.py / hr/ package shadowing affects SIX records in this register (11, 12, 13, 14, 15, 16) and is not a single-file defect: it is a repository-wide class of hazard (any same-n |
| `COMP-V14-21_contradictions` | `21_contradictions-6` | Frontend dependency drift is a whole-class problem spanning frontend/web_app/package.json, frontend/shared/package.json and frontend/mobile_app/package.json against three separate  |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-88` | Systemic, 83 distinct files. Every one of the 97 "Empty handler" rows (minus 2 false positives and 12 duplicates) is the same construct - an unlogged `catch`/`.catch()` - spread ac |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-84` | Highest blast radius in the packet and it is a single file. backend/infrastructure/valkey/client.py:44-90 defines _NoOpValkey whose docstring states it "silently no-ops all operati |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-41` | Systemic dead-scaffolding cluster: 313 commented/TODO lines in backend/domains/governance/services/admin/admin_service.py alone, and 50 more in backend/domains/governance/subscribe |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-13` | Systemic `# TODO: Module not yet created` scaffolding across >=12 domain files (payout_batch_service 24 stubs, supplier_supplier_upload_service 5, logistics tracking 7, commerce_co |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-45` | Eight module router files are registered but empty: modules/supplier/routers/{security,promotions,hr,country}.py (rows 45-48 + duplicates 79-82) plus modules/admin/routers/country. |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-4` | Backend silent-except class spans 10 cited files and 132 empty-bodied except blocks in backend/ plus 19 more outside it. The packet names only infrastructure/middleware, but the sy |
| `COMP-V03-22_anti_patterns` | `22_anti_patterns-22` | Law 19 (float for money) is a codebase-wide rule violation, not a per-file one: `grep -c "float\(" backend` returns 978 occurrences. The packet names 7 files (of which 1 is a false |
| `COMP-V21-23_code_intent` | `23_code_intent-1` | backend/config.py governs the whole codebase (compiler §0.4 rule 3). Its raw os.environ.get calls at :23 and :808 are Law 84/203 violations but are the ONLY two in the file, and th |
| `COMP-V21-23_code_intent` | `23_code_intent-14` | The stale-architecture-doc problem is not confined to FEATURES.md: _most_imp_docx/ contains 16 documents, several of which (FEATURES.md 7,560 lines / 488KB, FEATURES_LIST.md 380KB, |
| `COMP-V21-23_code_intent` | `23_code_intent-4` | Package-shadows-module shadowing is a repo-wide hazard, not an hr.py quirk: backend/modules/employee/routers/ contains both hr.py and hr/ (both referenced by 4, 5 and 16), and back |
| `COMP-V21-23_code_intent` | `23_code_intent-12` | Two committed lockfiles (pnpm-lock.yaml AND package-lock.json in frontend/web_app) while package.json:5 declares packageManager pnpm@11.9.0 and TECHNOLOGY_STACK §12:183 says 'Do NO |
| `COMP-V29-24_browser_behavior` | `OWED-00` | The Playwright ESM/CommonJS harness defect governs all 65 browser specs and therefore every browser-nature finding in the whole audit. No single File:Line; it is a two-file config  |
| `COMP-V29-24_browser_behavior` | `GATE-UNCATALOGUED` | 7 uncatalogued gate literals span 4 files across 2 modules (admin/tickets.py, admin/disputes.py, admin/promotions.py, customer/reviews.py) and produce 403 for EVERY role. This is a |
| `COMP-V29-24_browser_behavior` | `GATE-CUSTOMER-ATOM-SET` | `_ROLE_FEATURES['customer']` in backend/rbac/dependencies.py:93-96 grants 6 atoms, while the customer's own routers gate on 51 distinct atoms of which 47 are unreachable. One array |
| `COMP-V29-24_browser_behavior` | `LAW-167-197-DRIFT` | Law 167/197 require permissions.ts to be GENERATED from /rbac/catalog. Because the backend catalog and the router literals disagree, the frontend cannot gate correctly no matter wh |
| `COMP-V29-24_browser_behavior` | `ROUTER-REGISTRATION` | 6 (+1 shadowed) router files are absent from their module `__init__.py` `_module_names` lists. The mechanism is identical in 5 separate `__init__.py` files, so a single structural  |
| `COMP-V29-24_browser_behavior` | `LAW-178-PARTIAL` | Per-route artefact sets exist for page/loading/error but not layout on cart, checkout, orders, returns, profile, and not at all for terms/privacy/cookies. Affects every route in th |
| `COMP-V24-25_ai_drift` | `DRIFT-007` | The `<module>_routes/health` double-nesting appears on FIVE admin routers, verified in the live route table: /api/v1/admin/orders/admin_orders_routes/health, /api/v1/admin/logistic |
| `COMP-V24-25_ai_drift` | `DRIFT-004` | The RFC 7807 bypass is a codebase-wide error-shape contract issue, not 18 isolated line fixes: 18 raw 500 raises plus 14 raw 401 raises across 16 files, all producing {"detail": .. |
| `COMP-V24-25_ai_drift` | `DRIFT-006` | Surfaced for completeness only, and it argues for INVALID: this record is a pure naming-preference claim whose stated Verify evidence is wrong by a factor of 7 (claims 2 hits of `a |
| `COMP-V25-26_code_alignment` | `PERMISSIONS-REGEN` | Governs permissions.ts (frontend/shared/src/), its byte-identical duplicate frontend/web_app/src/shared/permissions.ts, frontend/web_app/scripts/generate-permissions.mjs, frontend/ |
| `COMP-V25-26_code_alignment` | `URL-RESOLUTION-PIPELINE` | Frontend URL resolution is a two-stage pipeline (frontend/web_app/src/lib/api/client.ts:38-44 resolveRequestUrl, then frontend/web_app/next.config.ts:35-75 rewrites) and BOTH stage |
| `COMP-V25-26_code_alignment` | `DEAD-CODE-SURFACES` | Three distinct dead-code families, each invisible to a filename-based audit: (1) backend/modules/employee/routers/hr.py — 55921B, shadowed by the hr/ package, 97 declared routes, z |
| `COMP-V25-26_code_alignment` | `LAW-88-GATE-CATALOG` | 13 live require_feature() call sites across modules/*/routers/ name atoms absent from rbac/catalog.py, so they 403 for EVERY role including super_admin (proved by executing _resolv |
| `COMP-V25-26_code_alignment` | `ORDER-STATUS-NON-MAPPING` | backend/domains/orders/models/order_entities.py:24 declares status_code and NO status attribute. 66 sites across 20 files reference Order.status / order.status — 26 writes, 40 read |
| `COMP-V30-27_project_completion_blockers` | `CAND-01-order-status-not-mapped` | Order.status is read/written at 67 class-level and 143 instance-level sites in production code across 21 files (domains/orders/{ports.py:25 sites, services/core/logistics.py, servi |
| `COMP-V30-27_project_completion_blockers` | `CAND-02-gate-literals-uncatalogued` | An AST scan of every production `require_feature(...)` call in backend/modules/** finds 147 distinct literals, of which 7 are absent from rbac/catalog.py's 367 atoms / 19 namespace |
| `COMP-V30-27_project_completion_blockers` | `CAND-03-customer-role-feature-set` | _ROLE_FEATURES['customer'] holds only 6 atoms. Against the 51 distinct require_feature literals in modules/customer/routers/**, 47 are denied - including customers.cart.manage (6 c |
| `COMP-V30-27_project_completion_blockers` | `CAND-04-no-ci-security-scanning` | A grep for pip-audit|gitleaks|trivy|npm audit|dependabot|cosign|syft across all 5 files in .github/workflows/ returns ZERO hits and .github/dependabot.yml does not exist, while TEC |
| `COMP-V30-27_project_completion_blockers` | `CAND-05-prod-compose-cannot-boot` | docker-compose.prod.yml governs all 7 production services. Two independent defects: (1) the pgbouncer service points DATABASE_URL at `@db:5432` (:5) but no `db` service is defined  |
| `COMP-V30-27_project_completion_blockers` | `CAND-06-hf-token-hard-production-gate` | backend/config.py:723-725 makes HF_API_TOKEN a hard `raise ValueError` in _validate_production, contradicting ARCHITECTURE_STACK.md:645 (Law 119: 'OpenAI and HuggingFace are NOT us |
| `COMP-V30-27_project_completion_blockers` | `CAND-07-event-channel-inert` | Law 3's sanctioned cross-domain write channel does not exist in production. 17 domains ship a subscribers.py (accounts, analytics, audit, catalog, comms, country, customers, financ |
| `COMP-V30-27_project_completion_blockers` | `CAND-08-plaintext-payment-credentials` | domains/finance/models/payments.py:87,97,98,99 store gateway `credentials` (JSON), `public_key`, `secret_key` and `webhook_secret` as plaintext columns; the write path at domains/f |
| `COMP-V15-28_supply_chain_security` | `LAW44_NO_CI_CVE_SCANNING` | Governs the whole codebase, has no single File:Line, and is a config-level gap across all 5 workflows. Measured: grep for `pip-audit|gitleaks|trivy|npm audit|dependabot|cosign|syft |
| `COMP-V15-28_supply_chain_security` | `LAW44_LIVE_CVES` | I ran pip-audit 2.10.1 read-only against backend/requirements.txt: **52 known vulnerabilities in 3 packages** — pillow==12.2.0 (25 vulns), starlette==0.40.0 (14), pyjwt==2.13.0 (13 |
| `COMP-V15-28_supply_chain_security` | `LAW290_MANIFEST_SHADOWING` | Two committed Python manifests disagree about what ships: `backend/requirements.txt` (tracked, fastapi==0.141.0 at line 8) vs `backend/uv.lock` (tracked, fastapi 0.115.2 at line 39 |
| `COMP-V15-28_supply_chain_security` | `LAW275_VAULT_KMS_SHADOW_PATH` | Law 275 and ARCHITECTURE_STACK.md:477 are explicit — 'AES-256-GCM envelope encryption via infrastructure/security/field_encryption.py. Master key lives in a Coolify env var; per-re |
| `COMP-V15-28_supply_chain_security` | `LAW58_LAW282_PII_LOG` | Cited only, not adjudicated (another agent owns auth_service.py). Confirmed genuine: `backend/domains/accounts/services/auth/auth_service.py:2057-2058` — `import sys` then `print(f |
| `COMP-V16-config_verification` | `CFG-001` | `backend/config.py` is named in compiler §0.4 item 14 as a config file that governs the whole codebase, and Law 86's split touches every `settings.` consumer. `infrastructure/utils |
| `COMP-V16-config_verification` | `CFG-005` | Dev-default-leak-into-production (Law 86) is a PATTERN, not a single field. Verified across the Settings default set: `frontend_url` (`http://localhost:3000`, config.py:172), `back |
| `COMP-V16-config_verification` | `CFG-009` | Law 84 / Law 203 (no raw `os.getenv` in production code) is codebase-wide, not config.py-local. Reproducible count: 156 `os.getenv`/`os.environ` reads across 58 production files in |
| `COMP-V16-config_verification` | `CFG-025` | The 'production-only length floors' pattern spans three key fields and three environments. `_validate_key_lengths` (`backend/config.py:361-382`) is `mode="before"` and early-return |
| `COMP-V34-suppliers` | `SUP-003` | The module-level __getattr__ service-locator pattern is repo-wide, not local: 69 non-test definitions across 6 layers (15 domains/*/ports.py with 15 defs, 15 domains/*/__init__.py  |
| `COMP-V34-suppliers` | `SUP-002` | The referential-integrity defect is not confined to suppliers. Across the whole repo, FK constraints declared in the ORM are routinely absent from Alembic: `Select-String ForeignKe |
| `COMP-V34-suppliers` | `SUP-005` | The namespace-hygiene pattern (eager aggregators with duplicate bindings and no __all__) is structural, not local: domains/suppliers/services/__init__.py (83 names, 43 duplicated), |
| `COMP-V34-suppliers` | `SUP-004` | Listed for completeness only, NOT recommended as cross-cutting. The honest measurement is 5 commented-out import lines in 1 file out of a 70-file domain, and Law 149 (print) is cle |
| — | **168 candidates reported** | |

## Internal contradictions found

| Dimension | Finding IDs | Conflict |
|---|---|---|
| 00_boot_smoke_test | `BOOT-001`, `BOOT-002` | The packet's dependency graph is a 2-CYCLE: BOOT-001 'Blocks: BOOT-002' and BOOT-002 'Blocks: BOOT-001'. Neither can ever start. This is a DEPENDENCY_BROKEN condition (compiler rule 43) made visible by verification -- an |
| 00_boot_smoke_test | `BOOT-001`, `BOOT-008` | BOOT-008 'Blocks: BOOT-001', but BOOT-001 is ALREADY RESOLVED and BOOT-008 is itself only a documentation-path defect. A completed record cannot be blocked by an open one, and BOOT-008 blocks nothing physical. Same defec |
| 00_boot_smoke_test | `BOOT-003`, `BOOT-007` | BOOT-003 'Blocks: BOOT-004' and BOOT-004 'Blocks: BOOT-005' and BOOT-005 'Blocks: BOOT-006' and BOOT-006 'Blocks: BOOT-007' and BOOT-007 'Blocks: BOOT-008' -- a chain that asserts a frontend type error blocks a compose f |
| 01_architectural | `ARCH-005`, `ARCH-011` | ARCH-005's Fix ('add the finance functions to domains/finance/ports.py, then import from ports') and ARCH-011's Fix ('delete modules/finance/routers/cash_management.py') are partly mutually exclusive for the finance cash |
| 01_architectural | `ARCH-002`, `ARCH-014` | ARCH-002 Blocks ARCH-014 in the packet metadata. ARCH-014's Fix ('implement actual cross-domain write logic in finance subscribers, ensure events are emitted post-commit') requires the `payments.confirmed` / `payments.re |
| 01_architectural | `ARCH-013`, `ARCH-007` | ARCH-013's Fix ('replace lazy exports with explicit thin read-wrapper functions in ports.py') and ARCH-007's Fix ('add change_password/list_sessions/revoke_session to domains/accounts/ports.py') propose two different mec |
| 02_technological | `TECH-003`, `TECH-004`, `02_technological-P0` | SEVERE - mutually exclusive fixes with opposite blast radius. 02_technological-P0 and TECH-003/TECH-004 instruct 'remove backend/requirements.txt' and switch the container build to `uv sync --frozen`. But backend/pyproje |
| 02_technological | `TECH-043`, `TECH-044` | Mild, and self-resolving. TECH-043 says frontend/mobile_app/package.json declares expo ~57.0.9 (needs upgrade) while TECH-044 says the lockfile has expo 55.0.27 (needs upgrade). I measured that package.json ALREADY says  |
| 02_technological | `TECH-020`, `TECH-021` | The two records apply INVERSE logic to their own Targets. TECH-020 correctly reads a benchmark cell `0.141.x` as a target to move UP to. TECH-021 reads `0.35.0+` as a target to move DOWN to ('Pin uvicorn to 0.35.0'), whe |
| 02_technological | `TECH-029`, `TECH-030` | Not a contradiction between the two records (they agree, and TECH-030 names TECH-029 as its dependency) but a contradiction between the records and the FIXED reality: both instruct pinning starlette to `>=1.6.0,<1.7.0`,  |
| 02_technological | `TECH-051`, `TECH-050` | TECH-051 asks for `packageManager` to be added and (wrongly) as `pnpm@10.x`. TECH-050 confirms the Dockerfile uses pnpm. But the two files that now exist DISAGREE on the pnpm major: frontend/web_app/package.json:5 declar |
| 02_technological | `TECH-011`, `TECH-012`, `TECH-013` | TECH-011's Fix ('Remove prometheus-client, use prometheus-fastapi-instrumentator exclusively') is UNACHIEVABLE as stated, while TECH-012 and TECH-013 assume the same removal is possible. backend/uv.lock:908 shows prometh |
| 03_logical | `LOGIC-003`, `LOGIC-013` | The two members of CLUSTER-return-type-leak prescribe identically-worded but mutually incompatible fixes for the same problem: LOGIC-003 Fix = 'Return str(val) for Decimal fields or use Pydantic Json encoder' (Target als |
| 03_logical | `LOGIC-001`, `LOGIC-002` | Declared circular Blocks dependency: LOGIC-001 'Blocks': 'LOGIC-002' AND LOGIC-002 'Blocks': 'LOGIC-001'. Both are also 'Depends on': 'none' and both are Completion blocker: yes, both P0, both in the same file (finance_s |
| 03_logical | `LOGIC-006`, `CLUSTER-silent-except`, `CLUSTER-stub-subscribers` | The packet contradicts itself on cluster membership. CLUSTER-silent-except lists LOGIC-006 as a member ('Exception blocks that swallow errors without logging or re-raising'), but backend/domains/finance/subscribers.py co |
| 03_logical | `LOGIC-016`, `CLUSTER-float-money` | CLUSTER-float-money's Members list includes LOGIC-016 ('LOGIC-001, LOGIC-002, LOGIC-004, LOGIC-010, LOGIC-011, LOGIC-012, LOGIC-013, LOGIC-016'), but LOGIC-016's own Cluster field reads 'CLUSTER-state-machine' and the fi |
| 03_logical | `LOGIC-006`, `LOGIC-018` | Not mutually exclusive, but the two fixes are individually insufficient for the joint problem and were recorded against different files, risking a partial resolution. LOGIC-018's Fix proposes only 'Register subscribers i |
| 04_operational | `OPS-002`, `OPS-010`, `OPS-003` | STALE DEPENDENCY GRAPH (compiler §0.8 step 43 — DEPENDENCY_BROKEN). OPS-002 is Status RESOLVED / ALREADY_FIXED (deploy.yml + rollback.yml exist), yet OPS-010 declares `Depends on: OPS-002` and OPS-003 declares `Depends o |
| 04_operational | `OPS-007`, `04_operational-P2` | The two records fix the same line with DIFFERENT levels of specification: OPS-007's Fix says 'Add `--workers 4` ... aligned with docker-compose.prod.yml replicas=3 and background_job_workers=2', while 04_operational-P2's |
| 04_operational | `OPS-001`, `OPS-008` | Not a hard contradiction, but the two Targets pull in opposite directions and the resolver must choose. OPS-008's Fix asks to add an R2 probe to BOTH `/health` and `/health/deps`; OPS-001's Target requires `/health` to f |
| 05_wiring | `WIRE-003`, `WIRE-004` | Mutually exclusive remediation on the same code path. WIRE-003's Fix offers 'use event_bus stream with post-commit consumer' as the remedy for pre-commit emission. WIRE-004's Fix replaces the retry-loop `time.sleep` with |
| 05_wiring | `WIRE-005`, `WIRE-007` | Low-severity, recorded for completeness because both concern middleware registration state. WIRE-005's Target asserts rate limiting must 'fail closed when unavailable' and its verdict shows that is already implemented (r |
| 06_database | `DB-006`, `DB-005` | The two proposed fixes are mutually exclusive in direction and neither matches the benchmark. DB-006 says 'Deprecate pg_rls_policies.sql and standardize on install_rls_policies() OR remove interceptor and use raw SQL' (t |
| 06_database | `DB-005`, `DB-006` | Internal contradiction between the Law-227 citation and the shipped code: DB-005 cites Law 227 (`SET LOCAL app.country_code`) as the Target, but the codebase's own RLS interceptor (DB-006's subject) enforces country scop |
| 07_CONTRADICTIONS | `CONTRAD-024`, `CONTRAD-025` | MUTUALLY EXCLUSIVE REMEDY ORDERING, expressed as a dependency cycle. CONTRAD-024 declares `Blocks: CONTRAD-025` and CONTRAD-025 declares `Blocks: CONTRAD-024`. Under PROMPT_RESOLUTION_ORCHESTRATOR.md:1501-1506 the schedu |
| 07_CONTRADICTIONS | `CONTRAD-016`, `CONTRAD-036` | Mutually overlapping fixes on the same manifest region: 016 says REPLACE slowapi/limits WITH fastapi-limiter-valkey; 036 says merely ADD fastapi-limiter-valkey. Following both literally yields fastapi-limiter-valkey decl |
| 07_CONTRADICTIONS | `CONTRAD-016`, `CONTRAD-036` | CATEGORY MISLABEL IN THE REGISTER: _audit/07_CONTRADICTIONS.md:204 labels CONTRAD-016 `package_vs_import` while :465 labels the same package problem CONTRAD-036 `tech_target_vs_lockfile`. One package, two categories, and |
| 07_tables_fields | `TF-065`, `TF-113`, `TF-114` | TF-113 and TF-114 target the SAME table and the SAME migration (comms.ticket_attachments) and are closed by the SAME revision 20260930_0001 (backend/alembic/versions/2026_09_30_0001_add_ticket_attachment_audit_columns.py |
| 07_tables_fields | `TF-024`, `TF-215`, `TF-162` | Three records propose the OPPOSITE remedies for the same Law 6 model-vs-migration drift. TF-024's Fix is 'Add column to model or remove from DB' and TF-215's is the same; TF-162's Delta implies the opposite (the column d |
| 07_tables_fields | `TF-001`, `07_tables_fields-P0` | Both target Law 49 (linear migration history) but propose different work. TF-001's Fix is 'Merge 5 heads into 1'; 07_tables_fields-P0's Extra.Correction is 'Merge 5 Alembic heads into single linear head' (equivalent). Ho |
| 07_tables_fields | `TF-028`, `TF-029`, `TF-030` | Internal to the wishlist_items cluster, and it cuts the opposite way from the other drift records. TF-028/029/030 claim the columns 'exist in DB but not in model' and propose 'Add column to model or remove from DB'. Veri |
| 08_providers | `08_providers-payments.base`, `08_providers-payments.registry` | The two proposed module shapes are mutually exclusive. payments/base.py is presented as the abstract adapter contract ('N/A (abstract)', all-N/A capability row) yet it ALSO carries GatewayDefinition, a module-level _REGI |
| 08_providers | `08_providers-payments.stripe_sdk`, `08_providers-payments.connect` | stripe_sdk.py guards SDK availability with HAS_STRIPE (:14/:22) and degrades to {'id':'stub_refund','status':'succeeded'} when absent (:51), while connect.py imports `stripe` from it (:13) and never checks HAS_STRIPE, so |
| 08_providers | `08_providers-ai.text`, `08_providers-ai.vision` | Both declare a class named VariantConfig in the same package - providers/ai/ai_variant_config.py:319 and providers/ai/vision.py:49. providers/ai/__init__.py:1 imports VariantConfig from .vision, so the vision copy shadow |
| 09_laws | `09_laws-32`, `09_laws-27` | Law 32 and Law 27 both target the same 90 files at backend/ root (75 health_test_*.py + 15 _tmp_*.py). Law 27 proposes DELETING them; Law 32 proposes treating them as a secret-exposure incident. These are not strictly mu |
| 09_laws | `FIND-09-006`, `FIND-09-023` | FIND-09-006 (Law 3/97) proposes routing cross-domain access through ports.py and events.py. FIND-09-023 proposes the opposite direction for one specific class: it flags modules/finance/routers/cash_management.py:20 and m |
| 09_laws | `09_laws-59`, `09_laws-60` | Both law rows and their FIND twins assert Law 59/60 violations that the repository's own gates cannot see, because tests/architecture/test_law58_through_law74.py excludes "venv" while the directory on disk is ".venv". Th |
| 10_migrations | `10_migrations-49`, `10_migrations-50`, `10_migrations-51`, `10_migrations-56`, `10_migrations-57` | These five rows carry 'Naming OK: Yes' while the other 61 carry 'Naming OK: No'. Running the shipped linter (backend/alembic/check_migration_naming.py) on exactly these five filenames returns exit 1 with 'filename does n |
| 10_migrations | `10_migrations-30`, `10_migrations-54`, `10_migrations-46` | Each of these rows' 'Down Revision' cell contradicts the file it cites, and in all three cases the file's real parent is the OTHER branch of a fork the table does not represent. 10_migrations-30 claims parent 20260806_00 |
| 10_migrations | `10_migrations-55`, `10_migrations-64` | The table simultaneously asserts (a) that 10_migrations-55 'merges non-divergent heads' - an ANOMALY - and (b) that 10_migrations-64 is a 'merge' whose name is misleading because it 'is not a merge'. Both assertions are  |
| 11_environmental | `ENV-02`, `11_environmental-4` | Low-severity but genuine and worth surfacing because it touches the same variable from two directions. ENV-02's Fix offers the resolver a choice: 'allow empty CORS_ORIGINS in production, OR remove the production CORS req |
| 11_environmental | `ENV-01`, `11_environmental-7`, `11_environmental-2` | A three-way interaction between the raw-env finding and the two validators. _validate_required_secrets_in_non_production (config.py:384-452) requires ~51 settings to be non-empty OUTSIDE production, including DATABASE_UR |
| 12_tests | `ARCHTEST-001`, `ARCHTEST-003`, `ARCHTEST-007` | Three records (one NEW/P0, two RESOLVED) all attribute collection failures in backend/tests/architecture/ to the same single root cause - 'SECRET_KEY must be at least 64 characters' / 'SECRET_KEY validation error' - and  |
| 12_tests | `ARCHTEST-004`, `ARCHTEST-003` | ARCHTEST-004's Fix offers a binary: 'Add domains/media/features.py ... or exclude media from domain scan if intentional'. ARCHTEST-003's Fix requires all domain features to resolve in rbac.catalog (Law 4 single-sourcing) |
| 12_tests_collection_verify | `COLLECT-004`, `COMP-V23-12_tests-baseline` | COLLECT-004 claims 'backend/tests/ has 3 collection errors' and marks it a P0 completion blocker whose Delta cites PROMPT_FORENSIC_AUDIT.md §0.11. The same dimension's own baseline (corroborated by my own `4728 tests col |
| 12_tests_collection_verify | `COLLECT-001/002/003`, `12_tests_collection_verify-P0` | The records claim `ModuleNotFoundError` for modules that exist on disk, yet they are marked `Claim state: VERIFIED`, `Evidence strength: triangulated`, `Confidence: 5`. Triangulated + L1 + confidence 5 is not consistent  |
| 13_dev_to_prod | `D2P-006`, `D2P-008`, `D2P-011` | D2P-006 requires Coolify as the deployment layer; D2P-008 asserts 'all secrets passed as env vars from Coolify' and D2P-011 asserts GlitchTip is the required error tracker. But the implemented target is Railway + Vercel  |
| 13_dev_to_prod | `D2P-004`, `D2P-012` | D2P-012 lists `Blocks: D2P-004`, i.e. the pre-traffic health gate must land before the rolling-deploy rollback parameters. But D2P-004's requested Fix text is already present verbatim in the file (FALSE_POSITIVE) while D |
| 13_dev_to_prod | `D2P-010`, `CLUSTER-missing-runbooks` | Not a true conflict — recorded to prevent double-counting. Both concern operational readiness, and the periodic-restore-drill half of D2P-010 is arguably runbook material, but they touch disjoint files (backend/scripts/p |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-003`, `CLUSTER-missing-coolify-config` | Both say Coolify is the canonical deployment layer requiring a codified config artifact. But the repo's actual, live deployment layer is Railway (railway.toml:1-13, deploy.yml:91-213, rollback.yml:51-77) and its frontend |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-004`, `CLUSTER-local-postgres-in-dev` | Benchmark-vs-benchmark, not fix-vs-fix: the proposed fix ('Remove local db service; configure dev to use Neon branch via DATABASE_URL') is required by ARCHITECTURE_STACK.md:741 (Law 215, 'No local Postgres container', 'D |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-001`, `D2P-DOCKER-002` | Not a fix conflict, but a shared-fate one worth flagging: D2P-DOCKER-002 is listed as Depends on: D2P-DOCKER-001, and D2P-DOCKER-002 Blocks: D2P-DOCKER-003 while D2P-DOCKER-003 Blocks: D2P-DOCKER-004. Both D2P-DOCKER-001 |
| 13_dev_to_prod | `D2P-001`, `13_dev_to_prod-P0`, `CLUSTER-missing-ci` | All three assert CI does not exist, yet all three name .github/workflows as the target and D2P-001's Verify command ('ls .github/workflows/*.yml returns 6 files') is an existence assertion against a directory that alread |
| 13_dev_to_prod | `D2P-005`, `D2P-004`, `D2P-012` | Three records target docker-compose.prod.yml and Dockerfile.prod as the production deploy path, while .github/workflows/deploy.yml:94-214 deploys the backend to Railway. Under Railway, neither the compose file nor Docker |
| 13_dev_to_prod | `D2P-008`, `D2P-006` | D2P-008 states secrets are 'passed as env vars from Coolify' as an established fact; D2P-006 asserts Coolify is entirely absent. Both cannot hold. My evidence resolves the factual question (no Coolify anywhere; deploy.ym |
| 14_frontend_web | `14_frontend_web-13`, `14_frontend_web-14` | The same observation is classified UNVERIFIABLE in 13 and FAIL in 14. The audit asserts it cannot be verified in one row and is a hard failure in the adjacent row. Resolved by keeping 14 as the survivor; 13 is merged awa |
| 14_frontend_web | `14_frontend_web-4`, `14_frontend_web-6`, `14_frontend_web-3` | Records 3, 4 and 6 all treat frontend/web_app/tailwind.config.js as LIVE configuration governing theme.extend (maxWidth, fontSize) — 4 cites it as the breakpoint authority, 6 cites lines 72-88 as the source of the fluid  |
| 14_frontend_web | `14_frontend_web-12`, `14_frontend_web-11` | Row 12 asserts 'No orphan pages observed' as part of a PASS attestation, while row 11 asserts that alt text is correctly applied across the same navigational surfaces. Row 12's no-orphans claim is falsified (/terms, /pri |
| 15_frontend_mobile | `MOB-002`, `MOB-001`, `15_frontend_mobile-P1` | MOB-002 claims expo-updates is 'absent from frontend/mobile_app/package.json dependencies'; MOB-001's Delta repeats 'no expo-updates package in package.json'; 15_frontend_mobile-P1's Correction says 'Re-enable expo-updat |
| 15_frontend_mobile | `MOB-006`, `MOB-005` | Two different npm package names are proposed for the same Facebook Sign-In SDK. MOB-006's Target names `@react-native-fbsdk-next`; the sibling stub's own error text at lib/authStore.ts:123 and :132 names `@molgenmills/re |
| 15_frontend_mobile | `MOB-007`, `MOB-008` | The two records propose opposite terminal states for regional payments and are not jointly satisfiable as written. MOB-007's Fix offers 'wire native Stripe SDK OR remove native SDK dependency'. MOB-008's Fix offers 'inst |
| 16_features | `FEAT-004`, `FEAT-025` | Both propose 'wire claim_inventory in create_order', but the implemented design deliberately reserves inventory at PAYMENT CONFIRMATION, not order creation — documented in code at backend/domains/finance/services/payment |
| 16_features | `FEAT-012`, `FEAT-030` | Both propose tightening numeric comparisons in the commission/promotion money path (FEAT-012: `>` → `>=` on the commission cap; FEAT-030: enforce stacking_allowed in the discount engine) while FEAT-030's Target also requ |
| 17_code_file_management | `CFM-002`, `CFM-014` | Mutually exclusive fixes for the same path. CFM-002 Fix = 'Delete backend/test/ directory entirely' (rollback `git rm -r backend/test`). CFM-014 Fix = 'Rename backend/test/ to backend/tests/ if it contains tests, otherwi |
| 17_code_file_management | `CFM-007`, `CFM-011` | Both records carry Status=RESOLVED while their Current fields describe open, unfixed defects. CFM-007 is resolved-per-status but auth_service.py is 4513 lines (LARGER than the 4506 the audit recorded) and has not been sp |
| 17_code_file_management | `CFM-012`, `CFM-015` | Not logically contradictory, but a fix-execution conflict: both target the SAME 25 subscriber functions in backend/domains/governance/subscribers.py with overlapping but different edits. CFM-015 wants ticket references + |
| 17_code_file_management | `CFM-001`, `CFM-009` | Low severity, but worth recording. CFM-001's Target asserts 'Laws 14-18: canonical domains are ... ; _parked is not approved' and its rollback is `git rm backend/domains/_parked/orders_package_service.py`, while CFM-009' |
| 18_security | `SEC-011`, `SEC-012` | SEC-011 asks for CORS_ORIGINS to be required in all environments, while config.py:653-655 already requires it in production and :787-789 rejects localhost in staging. SEC-012's proposed default-flip ('change default to t |
| 18_security | `SEC-010`, `SEC-001` | SEC-010's Fix (demote the PCI-DSS audit log from INFO to debug) and SEC-001's Fix (encrypt gateway credentials at rest) are aimed at the same compliance surface but pull in opposite directions on auditability: dropping t |
| 18_security | `SEC-005`, `SEC-001` | SEC-005's Fix would wrap outbound gateway calls with require_safe_url(); SEC-001's Fix would encrypt the gateway credentials. payment_engine.py:3391-3395 currently attaches the (plaintext) secret_key as an `Authorization |
| 19_performance | `PERF-006`, `PERF-007` | MUTUAL DEPENDENCY CYCLE, and both edges are spurious. PERF-006 says 'Depends on: PERF-007' and PERF-007 says 'Depends on: PERF-006'. These cannot both be true. Neither edge is plausible on the merits either: PERF-006 is  |
| 19_performance | `PERF-004`, `PERF-005`, `PERF-006` | INVERTED DEPENDENCY CHAIN across three records. PERF-004 (a next.config.ts image-format change, Phase 'frontend') says 'Blocks: PERF-006' (a backend catalog pagination change, Phase 'db'). PERF-005 (a React component CLS |
| 19_performance | `PERF-002`, `PERF-009`, `19_performance-P0`, `19_performance-P1` | STALE DEPENDENCY CHAIN - both endpoints already fixed. PERF-002 declares 'Blocks: PERF-009'; PERF-009 declares 'Depends on: PERF-002'; and 19_performance-P0 rolls up PERF-002 + PERF-001 while 19_performance-P1 rolls up P |
| 19_performance | `PERF-006`, `PERF-007`, `19_performance-P2` | SHARED BENCHMARK MIS-CITATION (not a code contradiction, surfaced per compiler §0.3 rule 7). All three records cite 'Law 317' as the keyset/OFFSET authority. Law 317 (ARCHITECTURE_STACK.md:844) is 'Alerting tiers' - P1/P |
| 19_performance | `PERF-008` | BENCHMARK MIS-CITATION. The record's Sibling cites 'TECHNOLOGY_STACK.md:46 (pg_trgm available)' as if availability were the gap. Line 46 is correct, but the record then proposes creating a pg_trgm GIN index that ALREADY  |
| 20_observability_resilience | `OBS-001`, `OBS-007` | Soft, and now moot. OBS-007's Fix offers 'Define LOG_RETENTION_DAYS in config.py and enable file handler in setup_structlog', while OBS-001's Fix offers 'Pass log_file path to setup_structlog OR configure a centralized l |
| 20_observability_resilience | `OBS-102`, `OBS-103` | OBS-103 ('no active-passive failover') declares Depends on='OBS-102' (the DR runbook) and Blocks='yes', but OBS-103's own Target is 'provision secondary VPS' (infrastructure) while OBS-102's Target is 'create a DR runboo |
| 20_observability_resilience | `OBS-004`, `OBS-008` | Not a contradiction between the two fixes, but an unflagged interaction the audit missed. OBS-008's Fix says to 'align with PII_FIELD_PATTERNS from logging_middleware.py:13-16' - i.e. treat logging_middleware.py as the r |
| 21_contradictions | `21_contradictions-9`, `21_contradictions-19` | Identical findings (sharp), listed as two separate rows with different Category values: record 9 is tech_target_vs_lockfile, record 19 is package_vs_import. Mutually consistent in substance, but the register treats one d |
| 21_contradictions | `21_contradictions-3`, `21_contradictions-20` | Both assert the same backend/config.py duplicated `settings = Settings()` block at overlapping cited ranges (record 3 cites 783-828; record 20 cites 792-803 'duplicated at 813-828' — the second range is a subset of the f |
| 21_contradictions | `21_contradictions-11`, `21_contradictions-16` | Not a fix conflict, but a citation conflict inside the register: record 11 states the backend's training routes are 'POST /modules, POST /{employee_id}/assign, ...' with no /training prefix, which is identical to record  |
| 22_anti_patterns | `22_anti_patterns-30`, `22_anti_patterns-89` | Same file (frontend/web_app/src/app/checkout/page.tsx) but disjoint blast radii: row 30 cites the checkout-options/shipping-method fetches (218, 236, 254, 269, 425) while row 89 cites the payment-path catches (373 `catch |
| 22_anti_patterns | `22_anti_patterns-45`, `22_anti_patterns-79` | Two rows assert mutually exclusive remediations for the same registered-but-empty router: implement the endpoints (Law 151) versus remove the router from modules/supplier/routers/__init__.py _module_names (Law 135 "remov |
| 23_code_intent | `23_code_intent-4`, `23_code_intent-5` | Mutually exclusive remediation targets for the same ESS routes. 23_code_intent-4 (hr.py) presumes hr.py is live and asks for it to be refactored down to Law 64/90 — i.e. keep the routes in hr.py. 23_code_intent-5 (accoun |
| 24_browser_behavior | `BROWSER-002`, `BROWSER-004` | BROWSER-002 says routers fail to import so NO API endpoints are available; BROWSER-004's Fix is 'resolve backend preconditions then run the browser suite', which presupposes the suite can run and find endpoints. If BROWS |
| 24_browser_behavior | `BROWSER-004`, `BROWSER-007` | Both are marked 'Claim state: VERIFIED' / 'Truth level: L1' (asserted direct observation) yet both cite `_browser_test/BROWSER_TEST_LOG.md`, which does not exist. An L1 VERIFIED claim cannot rest on a non-existent file.  |
| 24_browser_behavior | `BROWSER-005`, `BROWSER-006` | Their Fixes instruct running `_browser_test/tests/money/payments.spec.ts` and `_browser_test/tests/security/rbac.spec.ts`; neither path exists, and neither directory (money/, security/) exists anywhere under `_browser_te |
| 25_ai_drift | `DRIFT-002`, `DRIFT-009` | Mutually dependent fixes with a shared, unstated ordering requirement. DRIFT-002's Fix moves the campaign routes from admin/routers/orders.py to admin/routers/comms.py; DRIFT-009's Fix changes the require_feature atoms o |
| 25_ai_drift | `DRIFT-002`, `DRIFT-007`, `DRIFT-009` | Three records propose edits to the same 79-line file (admin/routers/orders.py) with no ordering or merge guidance, and DRIFT-002 asserts the file 'must contain order management endpoints' while DRIFT-007 proposes renamin |
| 25_ai_drift | `DRIFT-004`, `DRIFT-005` | Both name the same non-existent Test path (tests/architecture/test_error_shape.py) and both propose normalising router-level raises, but they disagree on the mechanism: DRIFT-004 says remove the raw 500 raises and let th |
| 26_code_alignment | `ALIGN-005`, `ALIGN-010`, `26_code_alignment-P2`, `26_code_alignment-P3` | Two records prescribe overlapping-but-different remedies for the same URL-resolution pipeline, and applying both would double-apply the cart change. ALIGN-010/P3 say to EXPAND resolveRequestUrl so that /cart/ maps to /ap |
| 26_code_alignment | `ALIGN-005`, `ALIGN-007` | ALIGN-005's Fix changes only PATHS in cartStore.ts. ALIGN-007's Fix extracts a SHARED CartItem interface into frontend/shared/src/ so web and mobile agree. These are ordered, not exclusive — but ALIGN-007 as written woul |
| 26_code_alignment | `ALIGN-009`, `ALIGN-002` | ALIGN-009 (refuted) asserts frontend `total` and `payment_status` are 'not present in the backend Order model'. ALIGN-002 relies on the same reading of the backend order schema and accepts the frontend `total` alias as l |
| 27_project_completion_blockers | `BLOCKER-002`, `BLOCKER-004`, `BLOCKER-003` | Status/Completion-blocker contradiction inside dimension file 27. BLOCKER-002 Status=INVALID, BLOCKER-004 Status=INVALID, BLOCKER-003 Status=VALID, yet the file's Summary line 15 declares 'Completion blockers: 9 yes' and |
| 27_project_completion_blockers | `BLOCKER-007`, `BLOCKER-002`, `27_project_completion_blockers-P0` | _audit/04_REMEDIATION_PLAN.md:6-16 (PF-001..PF-006) prescribes config.py attribute renames ('Add DATABASE_URL to backend/config.py', 'Add VALKEY_URL'), an alembic.ini 'Add script_location' step and 'Merge divergent Alemb |
| 28_supply_chain_security | `SUP-007`, `SUP-008` | SUP-007 declares a P0 EMERGENCY ('Both files contain identical production-looking keys') while SUP-008 in the same dimension declares COMPLIANT ('No .env files were ever committed to git history'). I resolved this agains |
| 28_supply_chain_security | `SUP-001`, `CLUSTER-cve-scanning`, `SUP-005` | SUP-001 asserts COMPLIANT ('Three CVE scanners in CI … block PR merge via security-success gate') while its own cluster's Root cause concedes gaps and SUP-005 asserts a PARTIAL Trivy posture. All three describe `.github/ |
| 28_supply_chain_security | `SUP-003`, `SUP-002` | Not a logical conflict but a benchmark-misalignment worth surfacing: SUP-002 is correctly scoped as optional under Law 291 while SUP-003 (license) treats Law 292's 'CI-enforced' as mandatory and proposes tools (pip-licen |
| config_verification | `CFG-013`, `CFG-022` | Mutually exclusive Targets on the same field. CFG-013's Target is 'Add `min_length=32` to `secret_key`'; CFG-022's Target is 'Add `min_length=64` to `secret_key` Field'. Applying both is impossible — the second strictly  |
| config_verification | `CFG-005`, `CFG-006`, `CFG-021`, `CFG-027` | Tension between two fixes in the same file. CFG-005/CFG-006 propose emptying connection-URL defaults to `""` and relying on the production validator to enforce presence; CFG-021/CFG-027 propose ADDING production-validato |
| config_verification | `CFG-003`, `CFG-013`, `CFG-022`, `CFG-025`, `CFG-026` | The record set is internally inconsistent about the `secret=True` mechanism. CFG-003 asks for `Field(..., secret=True)` to mask secrets in `repr()`; CFG-013/CFG-022/CFG-025/CFG-026 all cite `secret=True` as if it were al |
| suppliers | `SUP-002`, `SUP-004` | Mild, not blocking. SUP-002's remedy requires ADDING is_deleted and updated_at to suppliers.supplier_disputes (Law 23/54) and restoring ~20 columns on the SupplierDispute ORM. SUP-004's remedy recommends DELETING backend |

**102 internal contradictions.** Those marked `CONTRADICTION_INTERNAL` are excluded from dispatch (compiler §0.6 rule 40). Those carried as `BLOCKED_BY_CONTRADICTION` are excluded from the resolver scheduler (resolver §0.14). **None were resolved by this compiler** — contradictions are resolved by the user.

## Duplicate findings merged

| Dimension | Surviving ID | Merged ID | Reason |
|---|---|---|---|
| 00_boot_smoke_test | `BOOT-007` | `BOOT-003` | Same File:Line (frontend/web_app/src/app/admin/analytics/page.tsx:12), same root cause (the frontend typecheck is broken), same Target ('Builds without error' / 'No type errors' ar |
| 01_architectural | `ARCH-001` | `01_architectural-P0` | Same target (backend/modules/finance/ as a 6th module, Law 13). ARCH-001 survives as the citable finding (exact path, Priority P0, Blast radius, Sibling, populated Fix/Verify/Test  |
| 01_architectural | `ARCH-002` | `01_architectural-P0` | Same target (backend/domains/payments/ as a 17th domain, Law 12). ARCH-002 survives because it names the exact path, the sibling, and the consumer list; the P0 correction row adds  |
| 01_architectural | `ARCH-012` | `01_architectural-P2` | Identical file, identical line (:595 wildcard in backend/domains/finance/ports.py), identical fix. ARCH-012 survives (triangulated evidence, runnable verify, populated fields); 01_ |
| 01_architectural | `01_architectural-P1` | `ARCH-005, ARCH-006, ARCH-007, ARCH-008` | All five describe the same class - cross-domain/service reads not routed through ports.py - and all five were refuted on the same benchmark ground (ARCHITECTURE_STACK.md:528 Law 2  |
| 01_architectural | `ARCH-013` | `01_architectural-P1 (partial overlap)` | The `_LAZY_SERVICE_EXPORTS` service-locator is the mechanism by which 'module routers import services through ports' already happens in catalog/ports.py and accounts/ports.py. ARCH |
| 02_technological | `TECH-003` | `TECH-004` | Same file family (backend/Dockerfile* at :1), same cluster CLUSTER-pip-instead-of-uv, same Target ('uv pip install' / `uv sync --frozen` per §19), overlapping Sibling field. Both a |
| 02_technological | `TECH-013` | `TECH-012` | Both in cluster CLUSTER-forbidden-prometheus-client, both P1, both Target 'prometheus-fastapi-instrumentator per §9'. TECH-013 (backend/infrastructure/observability/metrics.py) is  |
| 02_technological | `TECH-014` | `TECH-015` | Identical file (backend/providers/payments/paypal.py), adjacent lines (:33 and :37), identical Delta family ('paypal-payments-sdk is forbidden' / 'paypal-checkout-sdk is forbidden' |
| 02_technological | `TECH-016` | `TECH-017` | Same file (backend/requirements.txt:1), same cluster CLUSTER-forbidden-pytz-tzlocal, same Target (zoneinfo + tzdata 2025b per §8), same Fix wording. §8:123 forbids both in a single |
| 02_technological | `TECH-018` | `TECH-019` | Both in cluster CLUSTER-forbidden-python-magic, same file (backend/requirements.txt:1), same Target (puremagic==2.2.0 per §4). TECH-019 is the narrower and cleaner record ('declare |
| 02_technological | `TECH-029` | `TECH-030` | Same root cause (starlette unpinned at backend/requirements.txt:14 and backend/pyproject.toml:10), same Target (`>=1.6.0,<1.7.0` per §1), same Fix, and TECH-030's Depends-on field  |
| 02_technological | `TECH-044` | `TECH-046` | Both in frontend/mobile_app/pnpm-lock.yaml, both report a stale resolved version contradicting frontend/mobile_app/package.json, same Fix text pattern, same Test paths (tests/mobil |
| 02_technological | `TECH-052` | `TECH-053` | Both in cluster CLUSTER-sbom-absent, same P1, same Target (Syft/CycloneDX per SECTION 11). TECH-052 survives on strictly better evidence: it cites a concrete existing file (.github |
| 02_technological | `TECH-033` | `TECH-042` | Both resolve to `tests/frontend/test_animations.py` (which does not exist) and both target the §13 `motion (framer-motion) | 13.2.0+` row. TECH-033 covers the legacy `framer-motion |
| 02_technological | `TECH-020` | `TECH-027` | Not strictly duplicates, but they must be sequenced together and I flag the coupling here so the orchestrator does not order them independently: FastAPI 0.141.x (TECH-020) is what  |
| 03_logical | `LOGIC-001` | `03_logical-P0` | Identical defect: same file (backend/domains/finance/services/finance_service.py), same line (65-66), same correction (CodRemittanceRequest.amount: float -> Decimal). LOGIC-001 is  |
| 03_logical | `LOGIC-007` | `03_logical-P1` | Identical defect: returns/service.py:434-438, the get_event_loop/new_event_loop + run_until_complete pattern. LOGIC-007 survives as the full finding record (Verify, Test, Rollback, |
| 03_logical | `LOGIC-012` | `03_logical-P2` | Identical defect: orders/services/core/logistics.py:376, charge_amount = float(...). LOGIC-012 survives with full metadata and the wider scope analysis (six float parses, arithmeti |
| 03_logical | `LOGIC-017` | `03_logical-P3` | Identical defect: payment_orchestrator.py:403-409 _GENERIC_DEFAULT_SUCCESS_VALUES. LOGIC-017 survives as the full finding. Both are weak -- the constant is already named, Law 66 co |
| 04_operational | `OPS-001` | `04_operational-P0` | Identical correction ('/health/deps must return 503 when critical deps down', Blocking: yes) against the same target file backend/main.py. Survivor has Priority P0, Evidence streng |
| 04_operational | `OPS-004` | `04_operational-P1` | Identical correction ('Raw os.getenv() in payment provider config -> typed settings') against backend/providers/payments/config.py. Survivor is triangulated with a per-line evidenc |
| 04_operational | `OPS-007` | `04_operational-P2` | Identical correction ('Gunicorn --workers explicitly set in Dockerfile.prod') against backend/Dockerfile.prod:26. Survivor carries Sibling, Blast radius and a (transposed) Test pat |
| 04_operational | `OPS-010` | `04_operational-P3` | Identical correction ('Celery payout/reconciliation tasks lack per-task concurrency limit') against backend/jobs/celery_app.py:167-189. Survivor has a runtime-level verify and iden |
| 04_operational | `OPS-001` | `OPS-008` | PARTIAL OVERLAP ONLY — both target backend/main.py /health/deps and both are now ALREADY_FIXED, but they describe different problems (fail-closed status code vs R2 coverage in the  |
| 04_operational | `OPS-004` | `OPS-005 + OPS-006` | NOT MERGED — the three sit in three different provider files with three different sets of environment variables, so they are three separate file-block edits. They ARE however one r |
| 05_wiring | `WIRE-001` | `05_wiring-P0` | Same file, same line, same fix, same priority. Both target backend/modules/admin/routers/comms.py:138 websocket_user and both are P0 with the same remedy. WIRE-001 survives because |
| 05_wiring | `WIRE-003` | `05_wiring-P1` | Same cluster (CLUSTER-event-post-commit) and the same substance: Law 3 post-commit emission. Both cite backend/domains/orders/events.py:84 and both resolve to the identical conclus |
| 06_database | `DB-003` | `DB-004` | Same defect class (Law 45, relationship() without lazy=) at a nearby location; DB-004's cited line products.py:37 is one of the 308 sites counted by DB-003. Survivor DB-003 (P1, bl |
| 06_database | `DB-001` | `DB-002` | Not a true duplicate, but DB-002 is listed as 'Depends on: DB-001' and Blocks=yes: both are the same completion blocker (the migration chain cannot be loaded/applied from a clean c |
| 07_CONTRADICTIONS | `CONTRAD-016` | `CONTRAD-036` | Same file, same package, same target (TECHNOLOGY_STACK.md:89), same Production_impact. CONTRAD-016's fix is the superset - it names both the offending pins (slowapi/limits) and the |
| 07_CONTRADICTIONS | `CONTRAD-017` | `CONTRAD-006 (overlapping portion only)` | CONTRAD-006's Delta already asserts 'uvloop/httptools absent' at backend/requirements.txt:9, duplicating CONTRAD-017's dedicated claim over backend/requirements.txt:1-102. The two  |
| 07_tables_fields | `TF-024` | `TF-025` | Same defect, same table, same File:Line (backend/domains/accounts/models/user.py:25): the accounts.users ORM model omits columns the migration creates. TF-025 (referral_points) is  |
| 07_tables_fields | `TF-024` | `TF-026` | Third occurrence of the identical TF-024 defect at backend/domains/accounts/models/user.py:25 (phone, alongside referral_code and referral_points). All three are closed by one migr |
| 07_tables_fields | `TF-028` | `TF-029` | Same three-way occurrence at backend/domains/catalog/models/products.py:135 (WishlistItem must adopt AuditMixin/SoftDeleteMixin). TF-029 (updated_by_id) is the same occurrence as T |
| 07_tables_fields | `TF-028` | `TF-030` | Third occurrence of the identical TF-028 defect at products.py:135 (deleted_by_id, SoftDeleteMixin half). Survivor TF-028. FALSE_POSITIVE as written, same reasoning. |
| 07_tables_fields | `TF-065` | `TF-066` | Same defect on the same table at the same line (backend/domains/comms/models/communication_schema_models.py:115, comms.escalation_sla_rules): the model declares updated_at and is_d |
| 07_tables_fields | `TF-089` | `TF-090` | Identical occurrence pair on comms.internal_notices at backend/domains/comms/models/communication_schema_models.py:99 (updated_at + is_deleted missing from the migration). Survivor |
| 07_tables_fields | `TF-097` | `TF-098` | Identical occurrence pair on comms.news_sources at backend/domains/comms/models/communication_schema_models.py:83 (updated_at + is_deleted). Survivor TF-097. |
| 07_tables_fields | `TF-109` | `TF-110` | Identical occurrence pair on comms.support_ticket_replies at backend/domains/comms/models/communication_schema_models.py:53 (updated_at + is_deleted). Survivor TF-109. |
| 07_tables_fields | `TF-113` | `TF-114` | Same table, same line (backend/domains/comms/models/communication_schema_models.py:68, comms.ticket_attachments), but DIFFERENT resolution states and they must NOT be merged away f |
| 07_tables_fields | `TF-215` | `TF-216` | Same defect on the same table at the same line (backend/domains/hr/models/employee_models.py:128, hr.org_units): migration 20260726_1609 adds path and depth that the model omits. B |
| 07_tables_fields | `TF-228` | `TF-229` | Same defect on the same table at the same line (backend/domains/orders/models/order_entities.py:142, orders.return_requests): requested_by_id and approved_by_id are both in the mod |
| 07_tables_fields | `TF-002` | `TF-003` | TF-003..TF-015 are byte-identical to TF-002 in every field except ID (File:Line is the bare string ':' in all 14; Current/Delta/Fix/Verify/Test/Rollback are identical). They are 14 |
| 07_tables_fields | `TF-002` | `TF-004` | Byte-identical occurrence of TF-002 (orphan table with no ORM model, no File:Line). Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-005` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-006` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-007` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-008` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-009` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-010` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-011` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-012` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-013` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-014` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-002` | `TF-015` | Byte-identical occurrence of TF-002. Survivor TF-002. |
| 07_tables_fields | `TF-039` | `TF-040` | Same table, same class (DirectChatMessage at backend/domains/comms/models/chat.py:155). TF-040 (missing updated_at) is subsumed by TF-039 (created_at lacks server_default): once th |
| 07_tables_fields | `TF-056` | `TF-057` | Same class (EntityChatMessage at backend/domains/comms/models/chat.py:124). One AuditMixin adoption closes both the created_at server_default (TF-056) and the missing updated_at (T |
| 07_tables_fields | `TF-058` | `TF-056` | Same class (chat.py:124, EntityChatMessage) and the same single fix (adopt the canonical AuditMixin/TenantMixin/SoftDeleteMixin bundle, which supplies created_at+updated_at+country |
| 07_tables_fields | `TF-101` | `TF-102` | Same class (Notification at backend/domains/comms/models/communication.py:13). NOTE: both are FALSE_POSITIVE -- the class inherits TenantMixin, which supplies country_code (backend |
| 07_tables_fields | `TF-115` | `TF-116` | Same class (TicketMessage at backend/domains/comms/models/communication.py:40). TF-116 (missing country_code) is FALSE_POSITIVE -- TenantMixin supplies it. Survivor TF-115 for trac |
| 07_tables_fields | `TF-068` | `TF-069` | Same class (FAQ at backend/domains/comms/models/communication.py:79). TF-069 (missing country_code) is FALSE_POSITIVE -- TenantMixin supplies country_code. Survivor TF-068 for trac |
| 07_tables_fields | `TF-084` | `TF-085` | Same class (InternalEmail at backend/domains/comms/models/communication.py:384). TF-085 (missing country_code) is FALSE_POSITIVE -- TenantMixin supplies it. Survivor TF-084 for tra |
| 07_tables_fields | `TF-091` | `TF-092` | Same class (MaskedMessage at backend/domains/comms/models/communication.py:429). TF-092 (missing country_code) is FALSE_POSITIVE -- TenantMixin supplies it. Survivor TF-091 for tra |
| 07_tables_fields | `07_tables_fields-P0` | `TF-001` | The P0/P1/P2 placeholders (07_tables_fields-P0/P1/P2) carry no File:Line, no Current, no Delta and no Fix -- only Target='Linear migration history per Law 49' and an Extra.Correcti |
| 07_tables_fields | `07_tables_fields-P0` | `07_tables_fields-P1` | All-NOT_PROVIDED placeholder; no verifiable content. Survivor 07_tables_fields-P0 by priority label only. |
| 07_tables_fields | `07_tables_fields-P0` | `07_tables_fields-P2` | All-NOT_PROVIDED placeholder; no verifiable content. Survivor 07_tables_fields-P0 by priority label only. |
| 08_providers | `08_providers-payments.registry` | `08_providers-payments.base` | Both rows describe the same thing twice: a provider-code -> adapter lookup inside providers/payments/. payments/registry.py:16 PaymentGatewayRegistry (register/get/get_or_raise/lis |
| 08_providers | `08_providers-qr.parcel_verification_service` | `(none - routed to coverage_gaps)` | The inventory filed one provider under two module paths: qr.parcel_verification_service (this row) and image/parcel_verification (not in the packet). They are NOT duplicates in cod |
| 08_providers | `08_providers-comms.whatsapp` | `08_providers-comms.whatsapp_selfhosted` | Both define the SAME public flag name HAS_WHATSAPP - comms/whatsapp.py:91 (HAS_WHATSAPP = _HAVE_TWILIO, Twilio-backed) and comms/whatsapp_selfhosted.py:34 (self-hosted). These are  |
| 09_laws | `FIND-09-001` | `09_laws-12` | Both assert that backend/domains/ contains 17 domains vs the canonical 15, with media and payments extra. Identical evidence, identical conclusion. FIND-09-001 survives because it  |
| 09_laws | `FIND-09-001` | `09_laws-160` | Law 160 ("15 domains fixed") is the same assertion as Law 12 ("15 domains") and as FIND-09-001. Law 160 adds one thing worth keeping: it records the DOWNSTREAM consequence - domain |
| 09_laws | `FIND-09-006` | `09_laws-1` | Law 1 (Arrows point down) and FIND-09-006 (cross-domain imports) cite the SAME two files at the SAME lines (country_enhancements.py:10 and supplier_shared.py:31-38) and reach the s |
| 09_laws | `FIND-09-006` | `09_laws-3` | Law 3 (Cross-domain events/ports) and Law 97 (Import direction) and Law 1 are three restatements of one underlying condition - 698 cross-domain non-ports imports. Law 3 additionall |
| 09_laws | `FIND-09-006` | `09_laws-97` | Same violation set as Law 1 and Law 3. Law 97 does add four reverse-edge breaches the others miss (domains->rbac 5, infrastructure->domains 8, infrastructure->providers 6, middlewa |
| 09_laws | `FIND-09-006` | `09_laws-17` | Law 17's entire "Violations found" cell is the literal text "See Law 3" - it is a cross-reference, not an independent finding. It must not become a second resolver ticket. |
| 09_laws | `FIND-09-002` | `09_laws-13` | Same fact (6 module directories vs the canonical 5, finance extra). FIND-09-002 survives for the impact analysis and the reframing that modules/finance is a shared controller libra |
| 09_laws | `FIND-09-002` | `09_laws-138` | Law 138 ("5 modules fixed") duplicates Law 13 ("5 modules") and FIND-09-002. Law 138 adds the observation that no /finance/* route prefix is registered, so Law 139 is not violated  |
| 09_laws | `FIND-09-003` | `09_laws-27` | Both assert 75 health_test_*.py + 15 _tmp_*.py at backend/ root. The counts are identical and exact in both. Merged. |
| 09_laws | `FIND-09-003` | `09_laws-32` | Same 90 files, different law. Law 32 asserts they contain hardcoded secrets; I disproved that (all values are empty strings) and returned law row 32 FALSE_POSITIVE. The surviving c |
| 09_laws | `FIND-09-004` | `09_laws-32` | FIND-09-004 and law row 32 make the identical claim (hardcoded secrets in health_test_*.py) and are disproved by the same evidence (all 75 files assign the EMPTY STRING). Law row 3 |
| 09_laws | `FIND-09-006` | `FIND-09-023` | FIND-09-023 (Law 99, module routers importing domain services) cites backend/modules/finance/routers/cash_management.py:20 and backend/modules/customer/routers/finance.py:12 - both |
| 09_laws | `09_laws-99` | `FIND-09-023` | The two records reach the same conclusion about the same module layer from the same citations. The law row is the better-structured record (it measures the full 252-import / 96-fil |
| 09_laws | `FIND-09-011` | `09_laws-44` | Both assert zero dependency scanning in CI. Identical evidence (grep across all 5 workflows returns zero matches for pip-audit|trivy|bandit|snyk|dependabot). FIND-09-011 survives:  |
| 09_laws | `FIND-09-011` | `FIND-09-019` | FIND-09-019 (missing pip-audit CI step) is a strict subset of FIND-09-011. Its one unique contribution - that tests/architecture/test_precommit_pip_audit.py already exists and is e |
| 09_laws | `FIND-09-014` | `09_laws-2` | Both assert business logic in module routers, and both cite the same two files. The citations are WRONG in both. The real violation is at backend/modules/customer/routers/orders.py |
| 09_laws | `FIND-09-014` | `09_laws-14` | Law 14 (Business logic -> domains/) is the same claim as Law 2, citing the same (incorrect) files. No independent evidence. Merged. |
| 09_laws | `FIND-09-014` | `09_laws-90` | Law 90 (No business logic in routers) is the third restatement of the same claim with the same incorrect citation. Merged. |
| 09_laws | `FIND-09-007` | `09_laws-59` | Both assert unlogged except blocks. Same underlying 389 handlers. FIND-09-007 survives with the per-file distribution and the analysis of why the repo Law-59 gate is blind to all o |
| 09_laws | `FIND-09-015` | `FIND-09-007` | FIND-09-015 asserts silent except blocks in MIDDLEWARE; FIND-09-007 asserts them in domain services. I proved the middleware claim false (0 unlogged handlers in backend/middleware/ |
| 09_laws | `FIND-09-008` | `FIND-09-022` | Both are FALSE_POSITIVE on Law 60 and both rest on the same error - grepping for time.sleep/asyncio.run and asserting "in async" without an AST check on the enclosing function. The |
| 09_laws | `FIND-09-008` | `09_laws-60` | Law 60 and FIND-09-008 cite the same files (jobs/ai_tasks.py:124,185,235; circuit_breaker.py:36,73) and are disproved by the same AST sweep. Both returned FALSE_POSITIVE; they are  |
| 09_laws | `FIND-09-010` | `09_laws-46` | Both assert the same 2 SELECT * hits at the same file and lines. FIND-09-010 is the prose record and carries the Law 46 scope argument. Merged. |
| 09_laws | `FIND-09-012` | `09_laws-40` | Both assert the localhost CORS default at backend/config.py:122 (cited as :121). Same conclusion and the same runtime proof that CORSMiddleware is never registered. Merged. |
| 09_laws | `FIND-09-013` | `09_laws-19` | Both assert float for money, and both cite backend/config.py (lines drifted 204-206 -> 214-216) and backend/domains/suppliers/models/suppliers.py credibility_weight Float. Identica |
| 09_laws | `FIND-09-016` | `09_laws-64` | Both assert no test enforces Law 64 and cite auth_service.py as the worst offender (incorrectly - it is 4512 lines as a FILE, largest function 159 lines). One missing-test work ite |
| 09_laws | `09_laws-64` | `09_laws-66` | Law 64 and Law 66 are the same missing static-analysis gate. Law 66 adds the (incorrect) claim that auth.py:27/215/188 contain magic numbers - they are already named constants, and |
| 09_laws | `09_laws-64` | `09_laws-65` | Law 65 (indentation depth) concedes in its own cell that no automated check exists. Same missing-gate work item as Law 64; no independent evidence of its own. |
| 09_laws | `09_laws-64` | `09_laws-67` | Law 67 (DRY, no duplicate-block check) likewise concedes no automated check exists. Same missing-gate work item as Law 64. |
| 09_laws | `09_laws-64` | `FIND-09-017` | FIND-09-017 is the Law 66 prose twin. Both reduce to "add a baseline-gated static-analysis test covering Laws 64-67". Merged. |
| 09_laws | `FIND-09-018` | `09_laws-7` | Both assert the allowlist is not shrinking. Same 20 entries, same file, same conclusion. The extra detail from each (Law 7: the passing shrink gate proves it is stalled not growing |
| 09_laws | `FIND-09-020` | `09_laws-37` | Both assert the rate limiter does not fail closed, and both are wrong about the location. The single real defect is infrastructure/security/rate_limit_helpers.py:78-88. Merged. |
| 09_laws | `FIND-09-020` | `09_laws-110` | Law 110 is the most accurate statement of the rate-limit problem in the packet ("fails closed in some cases but not all") but adds no new evidence. Merged into FIND-09-020, which c |
| 09_laws | `FIND-09-021` | `09_laws-58` | Both assert print() in production and both cite the now-deleted backend/check_tablenames.py plus the same alembic analyse_chain files. The real violation (auth_service.py:2058, a P |
| 09_laws | `FIND-09-005` | `09_laws-70` | Both assert tests/architecture/{test_import_laws,test_architecture_gates,test_laws_complete}.py are MISSING. Both are disproved by the same --collect-only run (23 tests collected)  |
| 09_laws | `FIND-09-001` | `09_laws-6` | Law 6 (schema discipline) flags the same media/payments schemas as the extra domains, but from the schema angle and adds two NEW violations the domain rows do not contain: hr/model |
| 10_migrations | `10_migrations-Runtime--alembic-heads` | `10_migrations-alembic.ini-sqlalchemy.url` | Both describe the same broken `alembic heads` invocation. The runtime-crash record is the higher-priority survivor because it carries the reproducible traceback; the sqlalchemy.url |
| 10_migrations | `10_migrations-11` | `10_migrations-56` | Both are incomplete-downgrade findings and both cite Law 57. 10_migrations-11 is the survivor: its downgrade gap is ACCIDENTAL and silently corrupts schema state (7 UNIQUE INDEXes  |
| 10_migrations | `10_migrations-16` | `10_migrations-26` | Both create the same table ai.upload_jobs in the same linear chain (20260730_0003 and 20260806_0006). The second is idempotently guarded so it is a no-op, but two revisions owning  |
| 11_environmental | `ENV-02` | `11_environmental-10` | Identical defect, different record type. 11_environmental-10 asserts 'CORS_ORIGINS: empty in prod, correct in dev' with Status FAIL; ENV-02 alleges 'CORS_ORIGINS production require |
| 11_environmental | `ENV-01` | `11_environmental-7` | Same root cause, one is the finding and one is the umbrella checklist row. 11_environmental-7 is the FAIL row 'No raw os.getenv() in production code'; ENV-01 is the finding 'Raw os |
| 11_environmental | `11_environmental-2` | `(no duplicate - retained deliberately)` | Recorded for the reviewer because there IS a near-duplicate pair in this packet that I am explicitly NOT merging: 11_environmental-3 ('No default credentials in fallbacks') and 11_ |
| 12_tests | `ARCHTEST-001` | `12_tests-P0` | Identical premise ('backend/tests/architecture/test_schema_discipline.py' does not exist / Blocking: yes) and identical Target. ARCHTEST-001 survives because it carries the file:li |
| 12_tests | `ARCHTEST-008` | `12_tests-P1` | Same target file, same 3 failing tests, same proposed correction. ARCHTEST-008 survives as it carries File:Line 621-676, the Delta detail and the reproduction. I add the scope spli |
| 12_tests | `ARCHTEST-011` | `12_tests-P2` | Same correction ('Consolidate duplicate test_architecture_gates.py'), same two files. ARCHTEST-011 survives with the concrete diff evidence (143 diff lines, differing SHA256, diffe |
| 12_tests | `ARCHTEST-001` | `ARCHTEST-002` | Not a true duplicate - the two records describe two different files and were independent, but both are FALSE_POSITIVE on the same 'file does not exist' premise and both are now RES |
| 12_tests_collection_verify | `COLLECT-001` | `COLLECT-002` | Same cluster (CLUSTER-collection-import-failure), same record shape (Phase testing, Confidence 5, Evidence strength triangulated, Truth level L1, Completion blocker yes), and the s |
| 12_tests_collection_verify | `COLLECT-001` | `COLLECT-003` | Same cluster and shape as COLLECT-002. COLLECT-002 and COLLECT-003 share a byte-identical `Current` ('No module named domains.finance.services.payments'), a byte-identical `Fix`, a |
| 12_tests_collection_verify | `COLLECT-001` | `12_tests_collection_verify-P0` | The 'Corrections required (prioritized)' row is a restatement of COLLECT-001: `Extra.Correction` = 'Resolve missing infrastructure.utils.circuit_breaker import' and `Target` = 'tes |
| 13_dev_to_prod | `D2P-009` | `13_dev_to_prod-P2` | Identical Target (monitoring/alerts.yml) and identical Correction ('Add runbook_url annotations to all alert rules'). Survivor carries 5 exact line citations plus a passing 3/3 tes |
| 13_dev_to_prod | `D2P-007` | `13_dev_to_prod-P3` | Identical Target (backend/config.py) and Correction ('Ensure Coolify env vars override local .env in production'). Survivor provides the static refutation of the load_dotenv guard; |
| 13_dev_to_prod | `D2P-002` | `13_dev_to_prod-P1` | Identical Target (CHANGELOG.md) and Correction ('Create missing CHANGELOG.md'). Survivor cites a concrete path and supplies a runnable Verify command (Test-Path CHANGELOG.md). |
| 13_dev_to_prod | `D2P-002` | `CLUSTER-missing-changelog` | Cluster root cause is literally 'CHANGELOG.md not created' and its only member is D2P-002. Nothing to add beyond the member's evidence. |
| 13_dev_to_prod | `D2P-003` | `CLUSTER-missing-runbooks` | Cluster root cause 'No operational documentation exists' with sole member D2P-003. Survivor carries the filesystem search evidence. |
| 13_dev_to_prod | `D2P-001` | `CLUSTER-missing-ci` | Cluster root cause 'CI/CD pipelines never created' with sole member D2P-001 and the identical recommended fix. Survivor carries the 5-file listing and the needs: graph. |
| 13_dev_to_prod | `D2P-001` | `13_dev_to_prod-P0` | Both assert the .github/workflows/ directory is missing and propose the identical 6-file list. Survivor is the full finding row with Priority P0 and a Verify command; the duplicate |
| 13_dev_to_prod | `D2P-004` | `13_dev_to_prod_docker_verify / D2P-DOCKER-007 (sibling packet)` | Same file, same claim (rollback_config / stop_grace_period absent), same verbatim Fix. Two independent agents reached FALSE_POSITIVE on identical evidence — this is mutual corrobor |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-001` | `13_dev_to_prod_docker_verify-P0` | Identical claim ('no Celery workers, no Beat in docker-compose.prod.yml'), identical target file, identical recommended action. Survivor D2P-DOCKER-001 carries a concrete path:line |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-005` | `13_dev_to_prod_docker_verify-P1` | Identical claim (the three readiness_require_* settings), identical target file backend/config.py, identical recommended action. Survivor cites backend/config.py:199-201 and a Test |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-007` | `13_dev_to_prod_docker_verify-P2` | Identical claim (missing rolling-deploy parameters), identical target file docker-compose.prod.yml, identical recommended action. Survivor cites the path:line. Both resolve FALSE_P |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-012` | `13_dev_to_prod_docker_verify-P3` | Identical claim (missing multi-stage Docker builds). Survivor D2P-DOCKER-012 is the better-evidenced row and additionally distinguishes dev from prod image; this row names both Doc |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-004` | `CLUSTER-local-postgres-in-dev` | The cluster has exactly one member (D2P-DOCKER-004) and restates its claim and recommended fix without adding evidence. Both resolve BLOCKED_BY_CONTRADICTION. Survivor retained bec |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-001` | `CLUSTER-missing-celery-prod` | Single-member cluster (D2P-DOCKER-001) restating the same absence claim. Both resolve FALSE_POSITIVE. |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-002` | `CLUSTER-valkey-version-drift` | Single-member cluster (D2P-DOCKER-002) restating the same version-drift claim. Both resolve FALSE_POSITIVE. Note the cluster compounds the error: its Root cause asserts prod is on  |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-005` | `CLUSTER-healthcheck-fails-open` | Single-member cluster (D2P-DOCKER-005) restating the readiness-flags claim. Both resolve ALREADY_FIXED. The cluster is retained as the aggregation node because its Extra block is t |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-003` | `CLUSTER-missing-coolify-config` | Single-member cluster (D2P-DOCKER-003) restating the same absent-Coolify-config claim. Both resolve REAL. Survivor retained for the richer evidence set and the Railway-vs-Coolify o |
| 13_dev_to_prod_docker_verify | `D2P-DOCKER-006` | `CLUSTER-missing-graceful-shutdown` | Single-member cluster (D2P-DOCKER-006) restating the same graceful-shutdown claim. Both resolve REAL (partial). Survivor retained for the three-way sub-claim breakdown. |
| 13_dev_to_prod | `D2P-004` | `D2P-012` | Identical citation docker-compose.prod.yml:64-69 for both, and both are already satisfied: rollback_config at :59-60 and stop_grace_period at :79 (D2P-004's ask), healthcheck at :6 |
| 13_dev_to_prod | `D2P-002` | `13_dev_to_prod-P1` | Same absence (root CHANGELOG.md). D2P-002 is fully populated with Fix/Verify/Rollback/Blast radius; the P1 row is all NOT_PROVIDED except the Correction text. |
| 13_dev_to_prod | `D2P-003` | `D2P-009` | D2P-009's proposed fix (add runbook_url to all 5 rules) is already implemented at monitoring/alerts.yml:12,22,34,44,54. Its genuine residual - the 5 runbook_url targets do not exis |
| 13_dev_to_prod | `D2P-001` | `CLUSTER-missing-ci` | Cluster is a single-member wrapper (Members: D2P-001) around the identical 'CI does not exist' premise, which is false in both rows. |
| 13_dev_to_prod | `D2P-007` | `13_dev_to_prod-P3` | Both assert the Coolify-env-vs-local-.env risk; backend/config.py:24 gate + :26 override=False refutes both. D2P-007 carries the fuller evidence. |
| 14_frontend_web | `14_frontend_web-14` | `14_frontend_web-13` | Identical claim (no web-vitals / onLCP / onCLS / onINP instrumentation in the web app). Record 13 is UNVERIFIABLE while record 14 is FAIL on the same evidence, which is an internal |
| 15_frontend_mobile | `MOB-003` | `15_frontend_mobile-P2` | Identical subject, priority (P2), confidence (4), dependency set (@react-native-community/netinfo), and non-blocking status. The Corrections-register row ('Add offline detection an |
| 15_frontend_mobile | `MOB-004` | `15_frontend_mobile-P3` | Identical subject (push-token registration without connectivity retry), priority (P3), confidence (4), non-blocking status. Survivor MOB-004 because it cites app/_layout.tsx:153 an |
| 16_features | `FEAT-022` | `FEAT-005` | Same file (backend/domains/finance/models/payments.py), same PaymentGatewayConnection.credentials column, adjacent lines (FEAT-005 cites :34, FEAT-022 cites :88; both resolve to th |
| 16_features | `FEAT-009` | `FEAT-001` | Identical claim (float cart-totals subtotal, same expression `item.price * item.quantity`) and identical paired test (tests/domains/test_orders.py::test_cart_totals_decimal). FEAT- |
| 16_features | `FEAT-004` | `FEAT-025` | Both claim 'INVENTORY_HELD_STATUSES is defined but no claim/release flow exists'. FEAT-025 cites backend/domains/orders/services/orders_service.py:259, a file that contains no refe |
| 16_features | `FEAT-010` | `FEAT-040` | FEAT-040 ('tax calculation function signature accepts float', cites backend/domains/finance/services/ledger/general_ledger.py) is the Law-19 statement of the defect that FEAT-010 ( |
| 16_features | `FEAT-011` | `FEAT-023` | Not a true duplicate — FEAT-023 is the missing-test finding for FEAT-011's flow (`Depends on: FEAT-011`). Recorded here only so the assembler keeps the pairing: resolving FEAT-011  |
| 17_code_file_management | `CFM-011` | `17_code_file_management-P1` | Identical subject: the three unimplemented biometric validators in backend/domains/accounts/services/auth/auth_service.py. The correction row carries only Target + Extra.Correction |
| 17_code_file_management | `CFM-004` | `17_code_file_management-P2` | Identical subject and identical target directory: splitting the oversized ledger service in backend/domains/finance/services/ledger/. The correction row adds only Effort (L 8h) and |
| 17_code_file_management | `CFM-001` | `17_code_file_management-P3` | Identical subject, identical target and identical verdict (ALREADY_FIXED): backend/domains/_parked/orders_package_service.py. CFM-001 survives because it carries the full record pl |
| 17_code_file_management | `CFM-002` | `CFM-014` | Same path (backend/test), same blast radius (F-005), same sibling (backend/tests), same fix intent, and both are ALREADY_FIXED. They are two framings of one observation (dead direc |
| 18_security | `SEC-001` | `18_security-P0` | Identical problem (payment gateway credentials stored without encryption) and identical Priority P0, Confidence 5, Evidence strength 'triangulated'. SEC-001 survives as the technic |
| 18_security | `SEC-007` | `18_security-P1` | Identical problem (verify_captcha silently skips when TURNSTILE_SECRET_KEY is unset) and identical Priority P1 / Confidence 5 / Blocking 'partial'. SEC-007 survives as the technica |
| 18_security | `SEC-009` | `18_security-P2` | Identical problem (16 debug scripts in backend/ root) and identical Priority P2 / Confidence 5 / Blocking 'no'. SEC-009 survives as the technical survivor: it names all 16 files ex |
| 18_security | `SEC-012` | `18_security-P3` | Identical problem (rate limiting off by default) and identical Priority P3 / Confidence 3 / Blocking 'no'. SEC-012 survives as the technical survivor (has File:Line :24, :121 and t |
| 19_performance | `PERF-002` | `19_performance-P0` | 19_performance-P0's Correction is literally 'Add lazy="selectin" to Product.cart_items and Order.items', which is the union of PERF-001 (cart_items, products.py:107) and PERF-002 ( |
| 19_performance | `PERF-003` | `19_performance-P1` | 19_performance-P1 names Product.variants, Product.videos and ReturnRequest.order. Product.variants and Product.videos are both at products.py:108-112, which is exactly PERF-003's c |
| 19_performance | `PERF-007` | `19_performance-P2` | 19_performance-P2's Correction ('Switch customer order history to keyset cursor pagination') describes the same defect at the same location as PERF-007: order_engine.get_orders tak |
| 19_performance | `PERF-006` | `19_performance-P2` | Partial overlap only - 19_performance-P2's Target cites 'Law 317', the same mis-citation PERF-006 carries, and PERF-007's Depends-on points at PERF-006. Recorded so the orchestrato |
| 19_performance | `PERF-003` | `19_performance-P3` | 19_performance-P3's two named relationships (Review.product, WishlistItem.product) live in catalog/models/products.py:132 and :146, the same file PERF-003 cites at :108-112, and al |
| 20_observability_resilience | `OBS-101` | `20_observability_resilience-P0` | Identical problem, identical file, identical fix. Both concern the silent DLQ-failure swallow in backend/infrastructure/messaging/events/event_bus.py. The -P0 row is a shell/CSV-so |
| 20_observability_resilience | `OBS-002` | `20_observability_resilience-P1` | Identical problem and identical fix wording. OBS-002's Target is 'Single shared ContextVar for request_id across middleware and services' and its Fix is 'Consolidate to one request |
| 20_observability_resilience | `OBS-007` | `OBS-001` | Same defect seen from two ends: OBS-001 cites main.py:35 (the missing log_file argument) and OBS-007 cites logging_config.py:134-141 (the un-enabled RotatingFileHandler) plus the m |
| 20_observability_resilience | `OBS-007` | `20_observability_resilience-P2` | The -P2 correction ('Enable file handler in setup_structlog and add LOG_RETENTION_DAYS to config', Target backend/main.py + backend/config.py) is the union of OBS-001 and OBS-007 w |
| 20_observability_resilience | `OBS-007` | `20_observability_resilience-P3` | The -P3 correction ('Add log retention configuration', Target backend/config.py) is a strict subset of OBS-007's Delta. Survivor OBS-007. ALREADY_FIXED. Recommend collapsing all fo |
| 20_observability_resilience | `OBS-106` | `OBS-109` | PARTIAL overlap only - flagging so the orchestrator files them adjacently rather than merging. OBS-109's own Blast radius field names OBS-106, acknowledging the dependency. They ar |
| 21_contradictions | `21_contradictions-9` | `21_contradictions-19` | Both describe the identical sharp finding: version drift vs TECHNOLOGY_STACK.md:184 AND the 'not declared in package.json, only transitive' claim. Both are now ALREADY_FIXED (packa |
| 21_contradictions | `21_contradictions-16` | `21_contradictions-3 and 21_contradictions-20` | NOT a content duplicate — recorded as a RELATED finding. Records 3 and 20 are two views of the same backend/config.py double-instantiation defect and are mutual duplicates of each  |
| 22_anti_patterns | `22_anti_patterns-77` | `22_anti_patterns-19` | Same file logistics/services/tracking/service.py, same 438-451 window, and both records describe the same interleaved `# TODO: Module not yet created` + commented `domains.orders.s |
| 22_anti_patterns | `22_anti_patterns-67` | `22_anti_patterns-52` | Same file promotions/services/coupons/commerce_coupons_read_service.py, same 7-10 window as 67, same two interleaved TODO/commented-import pairs. 67 survives (correct enumeration); |
| 22_anti_patterns | `22_anti_patterns-14` | `22_anti_patterns-56` | Byte-for-byte the same file, range (13-148) and claim ("35+ # TODO: Module not yet created stubs") as 14, and both are false (zero TODO occurrences in that file). Merged into 14 so |
| 22_anti_patterns | `22_anti_patterns-18` | `22_anti_patterns-58` | Same file suppliers/services/orders/supplier_orders_verify_service.py, same 21-41 window and the same "10+ commented imports to modules not yet created" claim as 18, and both are f |
| 22_anti_patterns | `22_anti_patterns-13` | `22_anti_patterns-62` | Same file finance/services/payouts/payout_batch_service.py; the cited 1699-1860 range is a strict subset of 13's 7-1860 and both count the same `# TODO: Module not yet created` stu |
| 22_anti_patterns | `22_anti_patterns-15` | `22_anti_patterns-63` | Same file finance/services/__init__.py, same 7-14 window as 15; both are false (9-line file, three ACTIVE wildcard imports, no TODOs). Merged into 15. |
| 22_anti_patterns | `22_anti_patterns-43` | `22_anti_patterns-64` | Same file finance/ports.py, same phantom 827-867 range as 43; both are false (686-line file, zero commented imports). Merged into 43. |
| 22_anti_patterns | `22_anti_patterns-51` | `22_anti_patterns-66` | Same file governance/services/settings/governance_package_service.py, same 20-26 block as 51; 66 counts only the two `# TODO` markers (23, 25) while 51 counts the three commented i |
| 22_anti_patterns | `22_anti_patterns-54` | `22_anti_patterns-68` | Same file catalog/services/products/admin_products_service.py, same line 13 as 54; both are false (line 13 is an ACTIVE import of `_bump_product_cache_version`, not a commented one |
| 22_anti_patterns | `22_anti_patterns-53` | `22_anti_patterns-69` | Same file catalog/services/categories/admin_categories_service.py, same line 22 as 53; both are false (line 22 is a blank line, no commented import, no TODO). Merged into 53. |
| 22_anti_patterns | `22_anti_patterns-20` | `22_anti_patterns-70` | Same file security/services/detection/public_security_detection_service.py, same 15-18 window as 20; both are false (active imports, no TODOs). Merged into 20. |
| 22_anti_patterns | `22_anti_patterns-17` | `22_anti_patterns-71` | Same file suppliers/services/supplier_shared.py, same line 38 as 17; both are false (line 38 is an active import). Merged into 17. |
| 22_anti_patterns | `22_anti_patterns-55` | `22_anti_patterns-78` | Same file logistics/services/shipping/service.py, same two lines (187, 196) and the same claim as 55. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-45` | `22_anti_patterns-79` | Identical evidence to 22_anti_patterns-45 (same file backend/modules/supplier/routers/security.py:12, same literal `# TODO: Add endpoints as domain services are implemented`). The  |
| 22_anti_patterns | `22_anti_patterns-46` | `22_anti_patterns-80` | Identical evidence to 22_anti_patterns-46 (modules/supplier/routers/promotions.py:12). Category-label duplication only; same fix. |
| 22_anti_patterns | `22_anti_patterns-47` | `22_anti_patterns-81` | Identical evidence to 22_anti_patterns-47 (modules/supplier/routers/hr.py:12). Category-label duplication only; same fix. |
| 22_anti_patterns | `22_anti_patterns-48` | `22_anti_patterns-82` | Identical evidence to 22_anti_patterns-48 (modules/supplier/routers/country.py:12). Category-label duplication only; same fix. |
| 22_anti_patterns | `22_anti_patterns-21` | `22_anti_patterns-83` | Same file config.py, same range 77-259, same claim as 21 ("60+ required secrets default to `""` ... masking missing env config"), and both are disproven by the production/non-produ |
| 22_anti_patterns | `22_anti_patterns-33` | `22_anti_patterns-90` | Same file admin/orders/page.tsx; line 180 is one of the seven sites enumerated by 33 (which cited 187/212/225/249/284). 33 is the survivor as the wider, correct enumeration. |
| 22_anti_patterns | `22_anti_patterns-34` | `22_anti_patterns-91` | Same file admin/categories/page.tsx and the same six `.catch(() => ({}))` sites as 34 (91 cites the coarse range 69-169, 34 cites the six exact lines). 34 is the survivor: its line |
| 22_anti_patterns | `22_anti_patterns-38` | `22_anti_patterns-92` | Same file admin/catalog/page.tsx, overlapping cited lines (69/111/131 is a subset of 38's 76/111/131) and the same claim ("hides catalog admin failures"). 38 is the survivor becaus |
| 22_anti_patterns | `22_anti_patterns-35` | `22_anti_patterns-93` | Same file EmailTemplateManager.tsx, same three cited lines and same claim as 35. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-36` | `22_anti_patterns-94` | Same file EmailProviderConfigManager.tsx, same three cited lines and same claim as 36. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-37` | `22_anti_patterns-95` | Same file GhostRowForm.tsx, same two cited lines (74/121) and same claim as 37. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-40` | `22_anti_patterns-96` | Same file, same three cited lines (183/198/205) and the same "product detail API failure" claim as 22_anti_patterns-40, one row apart in the audit output. Both resolve to the same  |
| 22_anti_patterns | `22_anti_patterns-31` | `22_anti_patterns-97` | Same file products/page.tsx, same four cited lines (268/442/448/475) and same claim as 31. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-32` | `22_anti_patterns-98` | Same file Header.tsx, same three cited lines (355/384/461) and same claim as 32. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-29` | `22_anti_patterns-99` | Same file cart/page.tsx, same cited line 69 (actual 79), same claim as 29. Exact duplicate. |
| 22_anti_patterns | `22_anti_patterns-170` | `22_anti_patterns-111` | Same file employee/dashboard/page.tsx, same root defect as 170. 111 is additionally the weaker record: it cites `} catch (e) { }` at line 102, but the file has `} catch {` at 101 ( |
| 22_anti_patterns | `22_anti_patterns-145` | `22_anti_patterns-169` | Byte-for-byte the same `Current` text, `File:Line` and `Function / Line` as 145 (app/api/auth/social-callback/route.ts:20,75). Pure row duplication from the occurrence-table expans |
| 23_code_intent | `23_code_intent-11` | `23_code_intent-10` | Same defect at the same root: openapi.ts:16 imports paths from schema.d.ts:6, which is Record<string, never>. schema.d.ts is the cause (the generation pipeline does not exist — no  |
| 23_code_intent | `23_code_intent-4` | `23_code_intent-16` | Both cite backend/modules/employee/routers/hr.py and both are resolved by deleting that file. 4 states the whole-file defect (1230 lines, 97 routes, 29 inline BaseModel classes, un |
| 24_browser_behavior | `BROWSER-008` | `24_browser_behavior-P2` | Identical claim, identical cited file, identical absence. BROWSER-008 is the Findings-table row with File:Line and Verify populated; 24_browser_behavior-P2 is the Corrections-table |
| 24_browser_behavior | `BROWSER-005 + BROWSER-006 (joint survivor: BROWSER-004)` | `BROWSER-007` | All four are the same underlying defect - the browser suite cannot produce runtime evidence - differing only in the scope label ('critical paths' / 'money path' / 'security path' / |
| 25_ai_drift | `DRIFT-001` | `25_ai_drift-P0` | The 'Corrections required (prioritized)' row restates DRIFT-001 verbatim: same file, same line (client.ts:109 vs client.ts:109), same defect ('method' used before declaration), sam |
| 25_ai_drift | `DRIFT-004` | `25_ai_drift-P2` | The P2 correction row ('Remove raw 500 error messages from 9 router files', Target backend/modules/*/routers/*.py) is a summary of DRIFT-004, which carries the full 18-instance/9-f |
| 25_ai_drift | `DRIFT-007` | `25_ai_drift-P3` | The P3 correction row ('Fix health endpoint path in admin orders router', Target admin/orders.py:76) restates DRIFT-007. Same partial verdict: the double-nested /api/v1/admin/order |
| 25_ai_drift | `DRIFT-003` | `25_ai_drift-P1` | The P1 correction row ('Remove auto-generated warning from hand-written router file', Target customer/routers/orders.py:131) restates DRIFT-003. Both point at the same AUTO-GENERAT |
| 26_code_alignment | `ALIGN-001` | `26_code_alignment-P0` | Same defect, same target file, same priority, same prescribed fix: ALIGN-001's File:Line is frontend/web_app/src/app/admin/orders/page.tsx:178,205,218,238,273 and its Target/Extra  |
| 26_code_alignment | `ALIGN-003` | `ALIGN-002` | ALIGN-002 (types) and ALIGN-003 (pagination) describe the same PaginatedResponse/ListPage envelope gap from two angles: ALIGN-002 asserts `pages` is dropped, ALIGN-003 asserts the  |
| 26_code_alignment | `ALIGN-003` | `26_code_alignment-P1` | The P1 correction ('Align PaginatedResponse and ListPage shapes; add pages field') is a restatement of the ALIGN-002/ALIGN-003 finding with no new evidence — it cites the same two  |
| 26_code_alignment | `ALIGN-005` | `26_code_alignment-P2` | The P2 correction ('Update cartStore.ts API paths to match backend /api/v1/customer/orders/*') is identical in substance to ALIGN-005 (same file, same six call sites, same fix). AL |
| 26_code_alignment | `ALIGN-010` | `26_code_alignment-P3` | The P3 correction ('Expand resolveRequestUrl to handle all backend prefix patterns') restates ALIGN-010 (same function client.ts:38). ALIGN-010 survives because it additionally ide |
| 26_code_alignment | `ALIGN-005` | `ALIGN-007` | PARTIAL overlap only — retained separately, not deleted. ALIGN-007's distinct claim is the web/mobile CartItem shape divergence (line_id/cart_item_id vs mobile's narrower type), wh |
| 27_project_completion_blockers | `BLOCKER-001` | `27_project_completion_blockers-P0` | The 'Corrections required' row ('Fix backend package import path', target 'backend/__init__.py or CI commands') is the same claim as BLOCKER-001 in the same packet, at the same pat |
| 28_supply_chain_security | `SUP-004` | `CONTRAD-005 (in _audit/07_CONTRADICTIONS.md:59-68)` | Both describe the same fastapi 0.115.2 vs 0.141.x manifest drift. CONTRAD-005 is already a tracked contradiction with `Project completion blocker: yes`, so SUP-004 must resolve to  |
| 28_supply_chain_security | `SUP-009` | `28_supply_chain_security-P1` | Identical correction ('Add permissions: block to ci.yml and architecture-gate.yml') and identical fix. SUP-009 carries the full canonical field set; the P1 row has only `Extra.Corr |
| 28_supply_chain_security | `SUP-009` | `CLUSTER-workflow-permissions` | Single-member wrapper (Members: SUP-009) adding no information beyond the cluster's Root cause restatement. |
| 28_supply_chain_security | `SUP-007` | `28_supply_chain_security-P0 and CLUSTER-plaintext-secrets` | Both restate SUP-007's correction ('Rotate SECRET_KEY and remove .env files') and its `Blocking: yes` flag. SUP-007 survives as the record with verifiable citations and full counte |
| 28_supply_chain_security | `SUP-010` | `CLUSTER-hardcoded-secrets-workflows` | Single-member wrapper (Members: SUP-010), no additional File:Line. |
| 28_supply_chain_security | `SUP-002` | `28_supply_chain_security-P2, CLUSTER-sbom-missing, and TECH-052 (dimensions/02_technological.md)` | Four records for one optional control. SUP-002 survives because it carries the Law 291 citation. All four are benchmark-optional and none should be compiled. |
| 28_supply_chain_security | `SUP-011` | `CLUSTER-dependency-confusion` | Single-member wrapper (Members: SUP-011); both FALSE_POSITIVE. |
| 28_supply_chain_security | `SUP-001` | `CLUSTER-cve-scanning` | Single-member wrapper (Members: SUP-001); both FALSE_POSITIVE. SUP-001 survives as the record to correct, because its COMPLIANT status is actively misleading. |
| config_verification | `CFG-012` | `CFG-020` | Byte-for-byte identical record: same File:Line (`backend/config.py:86`), same Current, Target, Delta, Fix, Rollback, Blast radius, and the same Effort=Trivial / Priority=P2 / Confi |
| config_verification | `CFG-021` | `config_verification-P0` | The P0 correction row's entire Correction text is 'Add DATABASE_URL_DIRECT production validator' — the identical defect CFG-021 asks for, against the identical validator block (`ba |
| config_verification | `CFG-021` | `CFG-027` | Same field (`database_url_direct`), same validator block (`backend/config.py:638-647`), same benchmark citation (TECHNOLOGY_STACK.md:305). CFG-027 differs only in asking for a Fiel |
| config_verification | `CFG-013` | `CFG-022` | Both target `secret_key`'s length floor at `backend/config.py:105`. CFG-013 claims no constraint exists (FALSE — `min_length=32` is there); CFG-022 asks to raise it to 64 (ALREADY  |
| **TOTAL** | | | **228 merged** |

## Benchmark mismatches

| Finding | Benchmark rule | Conflict |
|---|---|---|
| `TECH-*` / Law 108 vs §2 | dev database | `ARCHITECTURE_STACK.md:634,741` says dev is a Neon branch with **no** local Postgres; `TECHNOLOGY_STACK.md:42,45,279` says local Postgres 16, **never** Neon. `TECHNOLOGY_STACK.md:291,305` also contradict `:42`. |
| `CFG-*` / `DEFAULT_COUNTRY` | default value | `TECHNOLOGY_STACK.md:392` says `US`, `:564` says `AE`; `config.py:289` is `"US"`. |
| `MOB-*` / `expo-secure-storage` | package name | `TECHNOLOGY_STACK.md:249` and §20 name `expo-secure-storage`, which returns 404 from the npm registry. The real package is `expo-secure-store`, correctly used at `mobile_app/package.json:27`. |
| `CFG-*` / `EXPO_PUBLIC_API_URL` | config namespace | §20 lists the mobile API URL as `NEXT_PUBLIC_API_URL`; the code reads `EXPO_PUBLIC_API_URL` (`mobile_app/lib/api.ts:206`). |
| `TECH-*` / `DRIFT-*` Law 119 | provider policy | `ARCHITECTURE_STACK.md` Law 119 says HuggingFace is NOT used; §20 marks `HF_API_TOKEN` optional, yet `config.py:723-725` raises without it in production and real inference call paths exist. |
| `D2P-*` Law 216 | deployment target | §18 mandates Coolify + Cloudflare Pages; `deploy.yml:114,198` targets Railway + Vercel. |
| `ARCH-*` Law 2 vs Law 3 | router dependency | §6 and Law 2 mandate router → domain service; the audit cites Law 3/17 to force router → ports. |

## Fix quality flags

| Flag | Count | Meaning |
|---|---|---|
| FIX_UNTESTABLE | see below | no runnable `Test` path — dominant defect class this run |
| FIX_VAGUE | agents reported | fix does not specify what to change into |
| FIX_MISALIGNED | agents reported | names a symbol or package that does not exist |
| FIX_DESTRUCTIVE | agents reported | proposes stub/disable/remove |

**FIX_UNTESTABLE is systemic, not incidental.** The audit's `Test` column points at a `test/architecture/`, `test/commerce/` and `test/security/` tree that does not exist; the real trees are `backend/tests/` (4,728 collectible, 0 collection errors) and root `tests/` (1,734, 6 collection errors). `tests/commerce/` exists in neither. Agents reported 24/55, 19/20 and 41/42 named test paths missing across three dimensions. **This is a documentation defect in the audit prompts themselves and it must be fixed before the resolver can close most file blocks** — the resolver's §19 completion criteria name those same non-existent paths.

## Dependency and phase issues

| Issue | Count | Detail |
|---|---|---|
| DEPENDENCY_BROKEN | 0 | not evaluated — see below |
| PHASE_ORDER_INVALID | 0 | no dependency graph exists to be invalid |
| SECURITY_ELEVATED | 0 | `18_security` findings already carry phase `security` |

**`Depends on` is `none` on every block, and that is honest, not lazy.** The
audit's `Depends on` column was `NOT_PROVIDED` on essentially every record
that survived as `REAL`. Compiler §0.3 rule 8 forbids re-deriving what the
audit did not supply. The resolver must derive dependencies from observed
import edges when it freezes each contract (§7 `behaviors_frozen` depends on
them). Two agents independently measured the import graph and their numbers
are recorded in the verdict files.

## State dependency (read this before acting on any number)

**Every quantitative finding in this run is working-tree-relative.** The
tree has ~342 modified, ~48 deleted and ~225 untracked paths against HEAD
`6666d435`. Consequences measured directly:

| Measure | Working tree | Committed HEAD |
|---|---|---|
| Alembic heads | 1 (`20261001_0001`) | **4** |
| Alembic duplicate revision ids | 0 | **2** |
| `alembic heads` exit code | 0 | **1 (ImportError)** |
| `uv.lock` package count | 107 | 96 |
| `uv.lock` sha256 hashes | 502 | 1240 |

At HEAD, `alembic heads` cannot complete: `2026_07_30_0005:11` and
`2026_08_01_0018:11` do `from sqlalchemy.sql import identifier`, which does
not exist in SQLAlchemy 2.0.52. **A clean clone cannot migrate.** Two
agents measured this independently and reached the same conclusion. Treat
every other count in this log as equally state-dependent until the tree is
committed or reset deliberately.

## Completeness gate

Run `_audit/compiler/completeness_gate.py`. Result: **10/10 pass**.

| Check | Result |
|---|---|
| All files indexed | pass |
| All file blocks have 11 subsections | pass (272/272) |
| All subsections carry Confirmation | pass (2731/2731) |
| All FAIL subsections have Problem + Solution | pass |
| All Problem entries cite a finding ID | pass |
| All Solution entries have verify + test | pass |
| All blocks declare Phase, Effort, Blast radius | pass |
| Codebase Implementation section complete | pass (11 headers) |
| Executive summary matches the blocks | pass |
| No finding missing | pass |

## Time-box status

| Phase | Budget | Status |
|---|---|---|
| 1. File index | 4h | on_time — format-tolerant parse written and run |
| 2. Re-investigate | 8h | on_time — 34 agents, 1,359 verdicts |
| 3. Write worklist | 6h | on_time — 272 blocks + SECTION 2 |
| 4. Update statuses | 2h | on_time |
| 5. Log | 1h | on_time |

## Final summary

- Records extracted from dimensions: 1340
- Verdicts written: 1359
- Compiled into file blocks: 901
- Marked INVALID with counter-evidence: 152
- Marked RESOLVED (already fixed): 260
- Blocked by contradiction: 21
- Duplicates merged: 228
- Internal contradictions: 102
- Cross-cutting candidates: 168
- File blocks written: 272
- Dimension status updates applied: 354

