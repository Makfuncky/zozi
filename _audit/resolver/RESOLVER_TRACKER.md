# RESOLVER TRACKER

Generated: 2026-10-01T00:48:46.546850+00:00
Time-box: Day 1 (start) -> Day 9 (dispatch freeze) -> Day 10 (final loop-back)

Total file blocks: 174
Resolved: 86
In flight: 0
Blocked: 0
Pending: 88

## File blocks

| FILE | Phase | Path | Depends on | Findings | Effort | Status | Contract | Agent | Browser Test | Evidence |
|------|-------|------|------------|----------|--------|--------|----------|-------|--------------|----------|
| FILE 1 | security | backend/domains/accounts/services/auth/public_security_registration_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 2 | logic | backend/domains/catalog/services/commission_service.py | none | 1 | S (1h) | PENDING | — | — | — | — |
| FILE 3 | arch | backend/domains/catalog/services/products/products_service.py | none | 2 | L (8h) | PENDING | — | — | — | — |
| FILE 4 | logic | backend/domains/finance/services/commission_read_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 5 | logic | backend/domains/finance/services/data_import_service.py | none | 1 | M (1.5h) | PENDING | — | — | — | — |
| FILE 6 | arch | backend/domains/finance/services/finance_service.py | none | 2 | M (3h) | PENDING | — | — | — | — |
| FILE 7 | db | backend/domains/finance/services/ledger/accounting_controller.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 8 | logic | backend/domains/finance/services/trading_service.py | none | 1 | M (2.5h) | PENDING | — | — | — | — |
| FILE 9 | db | backend/domains/finance/services/treasury/cash_management_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 10 | db | backend/domains/governance/services/settings/governance_package_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 11 | db | backend/domains/orders/services/orders_package_service.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 12 | defer | backend/domains/promotions/services/admin_promotion_ops_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 13 | defer | backend/domains/promotions/services/promotion_admin_write_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 14 | db | backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 15 | db | backend/domains/catalog/models/chart_of_categories.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 16 | db | backend/domains/catalog/models/commission.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 17 | db | backend/domains/catalog/models/products.py | none | 1 | M (1h) | PENDING | — | — | — | — |
| FILE 18 | db | backend/domains/comms/models/chat.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 19 | db | backend/domains/comms/models/communication_schema_models.py | none | 2 | M (2h) | PENDING | — | — | — | — |
| FILE 20 | emergency | backend/domains/comms/models/cross_country_session.py | none | 1 | S (0h) | PENDING | — | — | — | — |
| FILE 21 | db | backend/domains/comms/models/messaging.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 22 | db | backend/domains/comms/services/shared/chat_threads_query.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 23 | db | backend/domains/country/models/country_control.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 24 | db | backend/domains/country/models/country_enhancements.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 25 | db | backend/domains/country/models/delivery_zones.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 26 | db | backend/domains/customers/models/cross_country_session.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 27 | db | backend/domains/finance/models/general_ledger.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 28 | db | backend/domains/finance/models/invoices.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 29 | db | backend/domains/finance/models/payments.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 30 | db | backend/domains/finance/models/refunds.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 31 | db | backend/domains/finance/models/tax_rules.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 32 | db | backend/domains/payments/models/payment_gateways.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 33 | defer | backend/domains/payments/models/payment_models.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 34 | db | backend/domains/promotions/models/promotion_config.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 35 | db | backend/domains/promotions/models/promotion_ledger.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 36 | db | backend/domains/promotions/models/promotions.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 37 | tech | backend/domains/catalog/services/search_service.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 38 | logic | backend/domains/finance/services/payments/payment_engine.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 39 | logic | backend/domains/finance/services/payments/payment_orchestrator.py | none | 3 | — | PENDING | — | — | — | — |
| FILE 40 | db | backend/domains/hr/services/compliance_engine.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 41 | db | backend/domains/logistics/services/logistics_sla_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 42 | logic | backend/domains/logistics/services/shipping_label.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 43 | logic | backend/domains/orders/services/admin_orders_service.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 44 | logic | backend/domains/orders/services/admin_orders_status_service.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 45 | logic | backend/domains/orders/services/core/admin.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 46 | arch | backend/domains/orders/services/logistics_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 47 | logic | backend/domains/orders/services/orders_service.py | none | 0 | S (0h) — ALREADY_FIXED | RESOLVED | — | — | — | — |
| FILE 48 | logic | backend/domains/promotions/services/customer_coupons_create_service.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 49 | logic | backend/domains/suppliers/services/disputes_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 50 | arch | backend/domains/suppliers/services/supplier_service.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 51 | logic | backend/modules/customer/routers/orders.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 52 | logic | backend/domains/accounts/services/users/user_management_service.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 53 | frontend | frontend/mobile_app/app/(auth)/login.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 54 | frontend | app/_layout.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 55 | frontend | app/checkout.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 56 | tech | backend/DOMAIN_ALLOWLIST.yaml | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 57 | emergency | backend/domains/_mixin_compliance.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 58 | db | backend/domains/accounts/ports.py | none | 1 | S (0.5h) | PENDING | — | — | — | — |
| FILE 59 | db | backend/domains/accounts/schemas/user_schemas.py | none | 0 | S (0h) | RESOLVED | — | — | — | — |
| FILE 60 | security | backend/domains/accounts/services/auth/auth_service.py | none | 1 | M (1h) | PENDING | — | — | — | — |
| FILE 62 | arch | backend/domains/governance/subscribers.py | none | 0 | M (2h) | RESOLVED | — | — | — | — |
| FILE 63 | arch | backend/domains/suppliers/services/supplier_shared.py | none | 10 | M (2h) | PENDING | — | — | — | — |
| FILE 64 | arch | backend/infrastructure/database/seed/_common.py | none | 10 | M (2h) | PENDING | — | — | — | — |
| FILE 65 | tech | backend/infrastructure/ml/worker.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 66 | security | backend/infrastructure/security/dependencies.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 67 | tech | backend/infrastructure/storage/backup.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 68 | arch | backend/infrastructure/storage/storage.py | none | 3 | — | PENDING | — | — | — | — |
| FILE 69 | arch | backend/infrastructure/utils/category_tree.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 70 | arch | backend/infrastructure/utils/country_rls.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 71 | tech | backend/infrastructure/utils/currency_service.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 72 | arch | backend/infrastructure/utils/dependencies.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 73 | tech | backend/infrastructure/utils/free_image_tools.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 74 | tech | backend/infrastructure/utils/image_ai_service.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 75 | tech | backend/infrastructure/utils/media_service.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 76 | tech | backend/infrastructure/utils/media_storage.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 77 | tech | backend/kernel/currency.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 78 | tech | backend/middleware/country_context.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 79 | tech | backend/middleware/dependencies/auth.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 80 | tech | backend/middleware/dependencies/country_detection.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 81 | tech | backend/middleware/impossible_travel_middleware.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 82 | tech | backend/middleware/lifespan.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 83 | arch | backend/modules/admin/routers/staff.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 84 | tech | backend/providers/bg_removal/bg_removal_service.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 85 | tech | backend/providers/storage/storage_backend.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 86 | arch | backend/rbac/dependencies.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 87 | boot | backend/scripts/check_broken.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 88 | boot | backend/scripts/fix_misplaced.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 89 | frontend | components/AddressesScreen.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 90 | frontend | components/LocationPicker.tsx (frontend/mobile_app/components/LocationPicker.tsx) | none | 1 | — | PENDING | — | — | — | — |
| FILE 91 | frontend | components/ProductCard.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 92 | frontend | lib/api.ts | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 93 | frontend | lib/authStore.ts | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 94 | arch | (absent) | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 95 | arch | (absent); .github/workflows/ | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 96 | boot | .github/dependabot.yml | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 97 | tech | .github/workflows | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 98 | tech | .github/workflows/ci.yml | none | 2 | — | PENDING | — | — | — | — |
| FILE 99 | boot | .github/workflows/deploy.yml | none | 2 | — | PENDING | — | — | — | — |
| FILE 100 | boot | .github/workflows/e2e.yml | none | 3 | — | PENDING | — | — | — | — |
| FILE 101 | defer | .github/workflows/rollback.yml | none | 1 | — | PENDING | — | — | — | — |
| FILE 102 | boot | .github/workflows/schema-audit.yml | none | 2 | — | PENDING | — | — | — | — |
| FILE 103 | defer | .github/workflows/security.yml | none | 2 | — | PENDING | — | — | — | — |
| FILE 104 | boot | .pre-commit-config.yaml | none | 1 | — | PENDING | — | — | — | — |
| FILE 105 | emergency | SECURITY.md (root) | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 106 | emergency | SETUP.md (root) | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 107 | db | backend/alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py | none | 3 | M (2h) | PENDING | — | — | — | — |
| FILE 108 | emergency | backend/config.py | none | 5 | L (6h) | PENDING | — | — | — | — |
| FILE 109 | arch | backend/domains/comms/services/messaging/websocket_handlers.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 110 | arch | backend/domains/orders/subscribers.py | none | 1 | M (2h) | PENDING | — | — | — | — |
| FILE 111 | arch | backend/infrastructure/events/subscriber.py | none | 1 | M (2h) | PENDING | — | — | — | — |
| FILE 112 | arch | backend/infrastructure/messaging/events/event_bus.py | FILE-7 | 1 | L (6h) | PENDING | — | — | — | — |
| FILE 113 | arch | backend/infrastructure/messaging/events/event_publisher.py | FILE-8 | 1 | L (4h) | PENDING | — | — | — | — |
| FILE 114 | tech | backend/infrastructure/observability/retry.py | none | 1 | S (1h) | PENDING | — | — | — | — |
| FILE 115 | security | backend/infrastructure/security/encryption.py | none | 0 | S (1h) | RESOLVED | — | — | — | — |
| FILE 117 | tech | backend/infrastructure/valkey/client.py | none | 2 | M (2h) | PENDING | — | — | — | — |
| FILE 118 | tech | backend/jobs/ai_tasks.py | none | 1 | S (1h) | PENDING | — | — | — | — |
| FILE 119 | boot | backend/jobs/celery_app.py | none | 3 | L (6h) | PENDING | — | — | — | — |
| FILE 120 | tech | backend/jobs/email_tasks.py | none | 1 | S (1h) | PENDING | — | — | — | — |
| FILE 121 | arch | backend/jobs/event_workers.py | FILE-7, FILE-8 | 3 | L (4h) | PENDING | — | — | — | — |
| FILE 122 | tech | backend/jobs/payout_tasks.py | none | 0 | S (1h) | RESOLVED | — | — | — | — |
| FILE 123 | boot | backend/jobs/periodic_tasks.py | none | 3 | M (3h) | PENDING | — | — | — | — |
| FILE 124 | security | backend/middleware/authentication_middleware.py | none | 1 | S (1h) | PENDING | — | — | — | — |
| FILE 126 | security | backend/middleware/orchestrator.py | none | 0 | S (1h) | RESOLVED | — | — | — | — |
| FILE 127 | security | backend/middleware/request_timeout_middleware.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 128 | security | backend/middleware/security_headers.py | none | 0 | S (0.5h) | RESOLVED | — | — | — | — |
| FILE 129 | logic | backend/modules/admin/routers/accounts.py | none | 3 | M (2h) | PENDING | — | — | — | — |
| FILE 130 | defer | backend/modules/admin/routers/customers.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 131 | arch | backend/modules/admin/routers/finance.py | none | 0 | S (1h) | RESOLVED | — | — | — | — |
| FILE 133 | security | backend/modules/customer/routers/accounts.py | none | 1 | M (3h) | PENDING | — | — | — | — |
| FILE 134 | logic | backend/modules/customer/routers/catalog.py | none | 0 | M (2h) | RESOLVED | — | — | — | — |
| FILE 135 | defer | backend/modules/customer/routers/governance.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 136 | defer | backend/modules/customer/routers/hr.py | none | 0 | S (0.5h) | RESOLVED | — | — | — | — |
| FILE 137 | defer | backend/modules/customer/routers/promotions.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 138 | resolved | backend/modules/customer/routers/security.py | none | 0 | S (0.5h) | RESOLVED | — | — | — | — |
| FILE 139 | arch | backend/modules/employee/routers/hr.py | none | 0 | M (2h) | RESOLVED | — | — | — | — |
| FILE 140 | defer | backend/modules/employee/routers/hr/attendance.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 141 | defer | backend/modules/employee/routers/hr/lms.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 142 | defer | backend/modules/employee/routers/hr/offices.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 143 | defer | backend/modules/logistics/routers/accounts.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 144 | defer | backend/modules/logistics/routers/audit.py | none | 0 | — (0h) | RESOLVED | — | — | — | — |
| FILE 145 | arch | backend/modules/logistics/routers/finance.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 146 | arch | backend/modules/logistics/routers/orders.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 147 | arch | backend/modules/supplier/routers/suppliers.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 148 | tech | backend/providers/ai/image_ai_service.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 149 | tech | backend/providers/ai/zozi_mcp.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 150 | tech | backend/providers/config.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 151 | tech | backend/providers/payments/stripe_sdk.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 152 | frontend | frontend/mobile_app/app/supplier/bulk.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 153 | frontend | frontend/web_app/src/app/admin/hr/page.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 154 | frontend | frontend/web_app/src/app/admin/users/page.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 155 | frontend | frontend/web_app/src/app/employee/training/page.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 156 | frontend | frontend/web_app/src/app/profile/page.tsx | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 157 | defer | backend/alembic/versions/2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 159 | boot | backend/jobs/accrual_reversal.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 160 | boot | backend/jobs/background_tasks.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 161 | boot | backend/jobs/bank_statement_importer.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 163 | boot | backend/jobs/data_retention.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 166 | boot | backend/jobs/fraud_monitoring.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 167 | boot | backend/jobs/fx_revaluation.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 168 | boot | backend/jobs/ghost_order_detector.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 169 | boot | backend/jobs/mcp_server.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 170 | boot | backend/jobs/ml_worker.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 171 | boot | backend/jobs/payout_sweep.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 172 | boot | backend/jobs/payroll_run.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 174 | boot | backend/jobs/reconciliation_cron.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 175 | tech | backend/jobs/threat_feed_updater.py | none | 0 | — | RESOLVED | — | — | — | — |
| FILE 176 | emergency | backend/lifespan.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 177 | emergency | backend/main.py | none | 2 | — | PENDING | — | — | — | — |
| FILE 178 | arch | backend/tests/architecture/test_law271_through_law295.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 179 | tech | docker-compose.prod.yml | none | 2 | — | PENDING | — | — | — | — |
| FILE 180 | tech | monitoring/alerts.yml | none | 1 | — | PENDING | — | — | — | — |
| FILE 181 | tech | monitoring/docker-compose.monitoring.yml | none | 1 | — | PENDING | — | — | — | — |
| FILE 182 | arch | monitoring/fraud_monitoring.py | none | 1 | — | PENDING | — | — | — | — |
| FILE 183 | emergency | backend/providers/finance/bank_api.py | none | 0 | S (0.5h) | RESOLVED | — | — | — | — |

## By phase

| Phase | File blocks | Findings | Total effort |
|-------|-------------|----------|-------------|
| emergency | 4 | 9 | — |
| boot | 15 | 24 | — |
| tech | 19 | 25 | — |
| db | 16 | 21 | — |
| logic | 11 | 16 | — |
| arch | 17 | 42 | — |
| security | 3 | 3 | — |
| frontend | 1 | 1 | — |
| defer | 2 | 3 | — |
