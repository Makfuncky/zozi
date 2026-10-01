# RESOLVER PLAN

Generated: 2026-10-01T00:48:46.548315+00:00
Time-box: Day 1 -> Day 9 (dispatch freeze) -> Day 10 (final loop-back)

## Phase execution order

### Phase emergency

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 20 | backend/domains/comms/models/cross_country_session.py | none | 1 | S (0h) |
| 2 | FILE 108 | backend/config.py | none | 5 | L (6h) |
| 3 | FILE 176 | backend/lifespan.py | none | 1 | — |
| 4 | FILE 177 | backend/main.py | none | 2 | — |

### Phase boot

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 88 | backend/scripts/fix_misplaced.py | none | 1 | — |
| 2 | FILE 99 | .github/workflows/deploy.yml | none | 2 | — |
| 3 | FILE 100 | .github/workflows/e2e.yml | none | 3 | — |
| 4 | FILE 102 | .github/workflows/schema-audit.yml | none | 2 | — |
| 5 | FILE 104 | .pre-commit-config.yaml | none | 1 | — |
| 6 | FILE 119 | backend/jobs/celery_app.py | none | 3 | L (6h) |
| 7 | FILE 123 | backend/jobs/periodic_tasks.py | none | 3 | M (3h) |
| 8 | FILE 166 | backend/jobs/fraud_monitoring.py | none | 1 | — |
| 9 | FILE 167 | backend/jobs/fx_revaluation.py | none | 1 | — |
| 10 | FILE 168 | backend/jobs/ghost_order_detector.py | none | 1 | — |
| 11 | FILE 169 | backend/jobs/mcp_server.py | none | 1 | — |
| 12 | FILE 170 | backend/jobs/ml_worker.py | none | 2 | — |
| 13 | FILE 171 | backend/jobs/payout_sweep.py | none | 1 | — |
| 14 | FILE 172 | backend/jobs/payroll_run.py | none | 1 | — |
| 15 | FILE 174 | backend/jobs/reconciliation_cron.py | none | 1 | — |

### Phase tech

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 37 | backend/domains/catalog/services/search_service.py | none | 2 | — |
| 2 | FILE 56 | backend/DOMAIN_ALLOWLIST.yaml | none | 1 | S (0.5h) |
| 3 | FILE 71 | backend/infrastructure/utils/currency_service.py | none | 1 | — |
| 4 | FILE 73 | backend/infrastructure/utils/free_image_tools.py | none | 1 | — |
| 5 | FILE 74 | backend/infrastructure/utils/image_ai_service.py | none | 1 | — |
| 6 | FILE 75 | backend/infrastructure/utils/media_service.py | none | 1 | — |
| 7 | FILE 76 | backend/infrastructure/utils/media_storage.py | none | 1 | — |
| 8 | FILE 78 | backend/middleware/country_context.py | none | 2 | — |
| 9 | FILE 81 | backend/middleware/impossible_travel_middleware.py | none | 1 | — |
| 10 | FILE 82 | backend/middleware/lifespan.py | none | 2 | — |
| 11 | FILE 98 | .github/workflows/ci.yml | none | 2 | — |
| 12 | FILE 114 | backend/infrastructure/observability/retry.py | none | 1 | S (1h) |
| 13 | FILE 117 | backend/infrastructure/valkey/client.py | none | 2 | M (2h) |
| 14 | FILE 118 | backend/jobs/ai_tasks.py | none | 1 | S (1h) |
| 15 | FILE 120 | backend/jobs/email_tasks.py | none | 1 | S (1h) |
| 16 | FILE 151 | backend/providers/payments/stripe_sdk.py | none | 1 | — |
| 17 | FILE 179 | docker-compose.prod.yml | none | 2 | — |
| 18 | FILE 180 | monitoring/alerts.yml | none | 1 | — |
| 19 | FILE 181 | monitoring/docker-compose.monitoring.yml | none | 1 | — |

### Phase db

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 11 | backend/domains/orders/services/orders_package_service.py | none | 1 | S (0.5h) |
| 2 | FILE 14 | backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py | none | 1 | S (0.5h) |
| 3 | FILE 16 | backend/domains/catalog/models/commission.py | none | 1 | S (0.5h) |
| 4 | FILE 17 | backend/domains/catalog/models/products.py | none | 1 | M (1h) |
| 5 | FILE 18 | backend/domains/comms/models/chat.py | none | 1 | S (0.5h) |
| 6 | FILE 19 | backend/domains/comms/models/communication_schema_models.py | none | 2 | M (2h) |
| 7 | FILE 22 | backend/domains/comms/services/shared/chat_threads_query.py | none | 1 | — |
| 8 | FILE 23 | backend/domains/country/models/country_control.py | none | 1 | — |
| 9 | FILE 26 | backend/domains/customers/models/cross_country_session.py | none | 1 | — |
| 10 | FILE 27 | backend/domains/finance/models/general_ledger.py | none | 2 | — |
| 11 | FILE 29 | backend/domains/finance/models/payments.py | none | 2 | — |
| 12 | FILE 34 | backend/domains/promotions/models/promotion_config.py | none | 1 | — |
| 13 | FILE 35 | backend/domains/promotions/models/promotion_ledger.py | none | 1 | — |
| 14 | FILE 40 | backend/domains/hr/services/compliance_engine.py | none | 1 | — |
| 15 | FILE 58 | backend/domains/accounts/ports.py | none | 1 | S (0.5h) |
| 16 | FILE 107 | backend/alembic/versions/2026_07_30_0004-20260730_0004_create_event_tables.py | none | 3 | M (2h) |

### Phase logic

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 2 | backend/domains/catalog/services/commission_service.py | none | 1 | S (1h) |
| 2 | FILE 5 | backend/domains/finance/services/data_import_service.py | none | 1 | M (1.5h) |
| 3 | FILE 8 | backend/domains/finance/services/trading_service.py | none | 1 | M (2.5h) |
| 4 | FILE 38 | backend/domains/finance/services/payments/payment_engine.py | none | 2 | — |
| 5 | FILE 39 | backend/domains/finance/services/payments/payment_orchestrator.py | none | 3 | — |
| 6 | FILE 42 | backend/domains/logistics/services/shipping_label.py | none | 1 | S (0.5h) |
| 7 | FILE 43 | backend/domains/orders/services/admin_orders_service.py | none | 1 | S (0.5h) |
| 8 | FILE 44 | backend/domains/orders/services/admin_orders_status_service.py | none | 1 | S (0.5h) |
| 9 | FILE 45 | backend/domains/orders/services/core/admin.py | none | 1 | S (0.5h) |
| 10 | FILE 48 | backend/domains/promotions/services/customer_coupons_create_service.py | none | 1 | S (0.5h) |
| 11 | FILE 129 | backend/modules/admin/routers/accounts.py | none | 3 | M (2h) |

### Phase arch

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 3 | backend/domains/catalog/services/products/products_service.py | none | 2 | L (8h) |
| 2 | FILE 6 | backend/domains/finance/services/finance_service.py | none | 2 | M (3h) |
| 3 | FILE 50 | backend/domains/suppliers/services/supplier_service.py | none | 1 | S (0.5h) |
| 4 | FILE 63 | backend/domains/suppliers/services/supplier_shared.py | none | 10 | M (2h) |
| 5 | FILE 64 | backend/infrastructure/database/seed/_common.py | none | 10 | M (2h) |
| 6 | FILE 68 | backend/infrastructure/storage/storage.py | none | 3 | — |
| 7 | FILE 69 | backend/infrastructure/utils/category_tree.py | none | 1 | — |
| 8 | FILE 70 | backend/infrastructure/utils/country_rls.py | none | 2 | — |
| 9 | FILE 72 | backend/infrastructure/utils/dependencies.py | none | 1 | — |
| 10 | FILE 86 | backend/rbac/dependencies.py | none | 1 | — |
| 11 | FILE 110 | backend/domains/orders/subscribers.py | none | 1 | M (2h) |
| 12 | FILE 111 | backend/infrastructure/events/subscriber.py | none | 1 | M (2h) |
| 13 | FILE 112 | backend/infrastructure/messaging/events/event_bus.py | FILE-7 | 1 | L (6h) |
| 14 | FILE 113 | backend/infrastructure/messaging/events/event_publisher.py | FILE-8 | 1 | L (4h) |
| 15 | FILE 121 | backend/jobs/event_workers.py | FILE-7, FILE-8 | 3 | L (4h) |
| 16 | FILE 178 | backend/tests/architecture/test_law271_through_law295.py | none | 1 | — |
| 17 | FILE 182 | monitoring/fraud_monitoring.py | none | 1 | — |

### Phase security

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 60 | backend/domains/accounts/services/auth/auth_service.py | none | 1 | M (1h) |
| 2 | FILE 124 | backend/middleware/authentication_middleware.py | none | 1 | S (1h) |
| 3 | FILE 133 | backend/modules/customer/routers/accounts.py | none | 1 | M (3h) |

### Phase frontend

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 90 | components/LocationPicker.tsx (frontend/mobile_app/components/LocationPicker.tsx) | none | 1 | — |

### Phase defer

| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE 101 | .github/workflows/rollback.yml | none | 1 | — |
| 2 | FILE 103 | .github/workflows/security.yml | none | 2 | — |

