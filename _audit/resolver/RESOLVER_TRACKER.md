# RESOLVER TRACKER

Generated: 2026-10-02T00:00:00Z
Source commit: HEAD
Worklist: _audit/TO_BE_RESOLVE.md (458 findings: 380 VALID, 59 INVALID, 16 RESOLVED, 2 BENCHMARK_MISMATCH, 1 PARTIALLY_VALID)
Time-box: Day 1 (start) → Day 9 (dispatch freeze) → Day 10 (final loop-back)

Total file blocks: ~90
Resolved: 0
In flight: 0
Blocked: 0
Pending: ~90

## File blocks

| FILE | Phase | Path | Depends on | Findings | Effort | Status | Contract | Agent | Browser Test | Evidence |
|------|-------|------|------------|----------|--------|--------|----------|-------|--------------|----------|
| FILE-1 | emergency | backend/.env | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-2 | emergency | backend/__init__.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-3 | emergency | backend/health_test_*.py (75 files) | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-4 | emergency | backend/run_tests.ps1, run_tests.sh | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-5 | emergency | backend/uv.lock | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-6 | emergency | backend/Dockerfile | — | 5 | 2h | PENDING | — | — | — | — |
| FILE-7 | boot | backend/main.py | FILE-2 | 2 | 2h | PENDING | — | — | — | — |
| FILE-8 | boot | backend/config.py | FILE-2 | 19 | 4h | PENDING | — | — | — | — |
| FILE-9 | boot | backend/alembic/versions/* | — | 2 | 4h | PENDING | — | — | — | — |
| FILE-10 | boot | backend/tests (collection errors) | FILE-2 | 3 | 2h | PENDING | — | — | — | — |
| FILE-11 | tech | backend/requirements.txt | — | 14 | 4h | PENDING | — | — | — | — |
| FILE-12 | tech | .github/workflows/ci.yml | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-13 | tech | backend/providers/payments/paypal.py | — | 2 | 2h | PENDING | — | — | — | — |
| FILE-14 | tech | backend/infrastructure/observability/metrics.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-15 | tech | backend/infrastructure/valkey/client.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-16 | tech | frontend/web_app/package.json | — | 9 | 2h | PENDING | — | — | — | — |
| FILE-17 | tech | frontend/mobile_app/package.json | — | 5 | 2h | PENDING | — | — | — | — |
| FILE-18 | tech | frontend/web_app/Dockerfile | — | 2 | 1h | PENDING | — | — | — | — |
| FILE-19 | db | backend/domains/comms/models/communication.py | — | 25 | 4h | PENDING | — | — | — | — |
| FILE-20 | db | backend/domains/comms/models/chat.py | — | 9 | 2h | PENDING | — | — | — | — |
| FILE-21 | db | backend/domains/finance/models/general_ledger.py | — | 41 | 4h | PENDING | — | — | — | — |
| FILE-22 | db | backend/domains/security/models/fraud.py | — | 27 | 4h | PENDING | — | — | — | — |
| FILE-23 | db | backend/domains/comms/models/communication_schema_models.py | — | 16 | 2h | PENDING | — | — | — | — |
| FILE-24 | db | backend/domains/comms/models/marketing.py | — | 14 | 2h | PENDING | — | — | — | — |
| FILE-25 | db | backend/domains/comms/models/incident.py | — | 6 | 1h | PENDING | — | — | — | — |
| FILE-26 | db | backend/domains/comms/models/fraud.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-27 | db | backend/domains/comms/models/message.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-28 | db | backend/domains/comms/models/news.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-29 | db | backend/domains/country/models/countries.py | — | 3 | 1h | PENDING | — | — | — | — |
| FILE-30 | db | backend/domains/country/models/country_basics.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-31 | db | backend/domains/country/models/country_control.py | — | 8 | 2h | PENDING | — | — | — | — |
| FILE-32 | db | backend/domains/country/models/country_economics.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-33 | db | backend/domains/country/models/country_enhancements.py | — | 16 | 2h | PENDING | — | — | — | — |
| FILE-34 | db | backend/domains/country/models/country_legal.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-35 | db | backend/domains/country/models/country_tax.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-36 | db | backend/domains/customers/models/cross_country_session.py | — | 2 | 1h | PENDING | — | — | — | — |
| FILE-37 | db | backend/domains/customers/models/customer_schema_models.py | — | 2 | 1h | PENDING | — | — | — | — |
| FILE-38 | db | backend/domains/finance/models/commission.py | — | 4 | 1h | PENDING | — | — | — | — |
| FILE-39 | db | backend/domains/finance/models/payments.py | — | 2 | 2h | PENDING | — | — | — | — |
| FILE-40 | db | backend/domains/finance/models/tax_rules.py | — | 4 | 1h | PENDING | — | — | — | — |
| FILE-41 | db | backend/domains/governance/models/admin.py | — | 2 | 1h | PENDING | — | — | — | — |
| FILE-42 | db | backend/domains/hr/models/employee_models.py | — | 6 | 1h | PENDING | — | — | — | — |
| FILE-43 | db | backend/domains/logistics/models/logistics_entities.py | — | 8 | 2h | PENDING | — | — | — | — |
| FILE-44 | db | backend/domains/logistics/models/logistics_schema_models.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-45 | db | backend/domains/logistics/models/shipping_rules.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-46 | db | backend/domains/media/models/media_asset.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-47 | db | backend/domains/orders/models/order_entities.py | — | 7 | 2h | PENDING | — | — | — | — |
| FILE-48 | db | backend/domains/promotions/models/coupon_usage.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-49 | db | backend/domains/promotions/models/promotion_config.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-50 | db | backend/domains/suppliers/models/suppliers.py | — | 10 | 2h | PENDING | — | — | — | — |
| FILE-51 | db | backend/domains/accounts/models/user.py | — | 3 | 1h | PENDING | — | — | — | — |
| FILE-52 | db | backend/domains/catalog/models/products.py | — | 5 | 2h | PENDING | — | — | — | — |
| FILE-53 | db | backend/domains/catalog/models/upload_job.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-54 | logic | backend/domains/finance/services/finance_service.py | FILE-8 | 2 | 2h | PENDING | — | — | — | — |
| FILE-55 | logic | backend/domains/orders/services/orders_service.py | FILE-8 | 1 | 1h | PENDING | — | — | — | — |
| FILE-56 | logic | backend/modules/customer/routers/orders.py | FILE-8 | 4 | 2h | PENDING | — | — | — | — |
| FILE-57 | logic | backend/domains/finance/subscribers.py | FILE-54 | 1 | 4h | PENDING | — | — | — | — |
| FILE-58 | logic | backend/domains/orders/services/returns/service.py | FILE-55 | 1 | 2h | PENDING | — | — | — | — |
| FILE-59 | logic | backend/domains/finance/services/payments/payment_engine.py | FILE-8 | 3 | 2h | PENDING | — | — | — | — |
| FILE-60 | logic | backend/domains/catalog/services/products/products_service.py | — | 3 | 2h | PENDING | — | — | — | — |
| FILE-61 | logic | backend/domains/orders/services/core/order_engine.py | FILE-55 | 1 | 1h | PENDING | — | — | — | — |
| FILE-62 | logic | backend/domains/logistics/services/core/service.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-63 | logic | backend/domains/security/services/fraud/fraud_detection_service.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-64 | arch | backend/domains/finance/ports.py | — | 2 | 4h | PENDING | — | — | — | — |
| FILE-65 | arch | backend/middleware/dependencies/auth.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-66 | arch | backend/middleware/dependencies/country_detection.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-67 | arch | backend/modules/admin/routers/finance.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-68 | arch | backend/modules/customer/routers/catalog.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-69 | arch | backend/modules/supplier/routers/accounts.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-70 | arch | backend/modules/logistics/routers/finance.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-71 | arch | backend/modules/finance/__init__.py | — | 2 | 2h | PENDING | — | — | — | — |
| FILE-72 | arch | backend/domains/payments/__init__.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-73 | arch | backend/domains/media/ | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-74 | arch | backend/modules/admin/routers/orders.py | — | 3 | 2h | PENDING | — | — | — | — |
| FILE-75 | arch | backend/modules/admin/routers/permissions.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-76 | arch | backend/modules/customer/routers/accounts.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-77 | arch | backend/modules/customer/routers/promotions.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-78 | arch | backend/modules/supplier/routers/audit.py | — | 2 | 1h | PENDING | — | — | — | — |
| FILE-79 | arch | backend/providers/comms/sms.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-80 | arch | backend/providers/geography/geo.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-81 | arch | backend/providers/payments/config.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-82 | arch | backend/providers/news/, automation/, scanner/, voice/, analytics/ | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-83 | security | backend/domains/finance/models/payments.py | — | 2 | 4h | PENDING | — | — | — | — |
| FILE-84 | security | backend/rbac/models/permission_entities.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-85 | security | backend/infrastructure/observability/error_handler.py | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-86 | security | backend/infrastructure/observability/logging_config.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-87 | security | backend/infrastructure/storage/backup.py | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-88 | frontend | frontend/web_app/src/app/admin/orders/page.tsx | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-89 | frontend | frontend/web_app/src/components/ProductCard.tsx | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-90 | frontend | frontend/web_app/src/lib/cartStore.ts | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-91 | frontend | frontend/web_app/src/lib/useAdminApi.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-92 | frontend | frontend/shared/src/permissions.ts | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-93 | frontend | frontend/shared/src/types.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-94 | frontend | frontend/mobile_app/lib/paymentService.ts | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-95 | frontend | frontend/mobile_app/lib/authStore.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-96 | frontend | frontend/mobile_app/lib/socialAuth.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-97 | frontend | frontend/mobile_app/android/app/src/main/AndroidManifest.xml | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-98 | frontend | frontend/mobile_app/app/_layout.tsx | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-99 | frontend | frontend/mobile_app/lib/api.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-100 | frontend | frontend/mobile_app/e2e/ | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-101 | frontend | frontend/web_app/src/ (TS errors) | — | 1 | 4h | PENDING | — | — | — | — |
| FILE-102 | frontend | frontend/web_app/next.config.ts | — | 1 | 1h | PENDING | — | — | — | — |
| FILE-103 | frontend | frontend/web_app/e2e/ | — | 1 | 2h | PENDING | — | — | — | — |
| FILE-104 | frontend | frontend/mobile_app/package.json + pnpm-lock.yaml | — | 7 | 2h | PENDING | — | — | — | — |
| FILE-105 | frontend | frontend/shared/src/permissions.ts + types.ts | — | 2 | 2h | PENDING | — | — | — | — |

## Status legend

- `PENDING` — file block identified, not yet dispatched
- `INVESTIGATING` — resolver investigating (3rd pass)
- `DISPATCHED` — sub-agent working
- `VERIFYING` — sub-agent done, resolver verifying
- `✅ RESOLVED` — all findings in the file block resolved and verified
- `🔄 REJECTED` — sub-agent drifted or failed verification, re-dispatching
- `⛔ BLOCKED` — could not resolve (reason in Evidence)
- `BLOCKED_BY_CONTRADICTION` — waiting for user decision
- `DEFERRED_TIMEBOX` — not closed by time-box; enters launch known issues
- `SHIPPED_WITH_KNOWN_ISSUE` — terminal at Day 10
- `PENDING_USER_REVIEW` — target-canonical or KEEP_HARDEN_CANDIDATE

## By phase

| Phase | File blocks | Findings | Total effort |
|-------|-------------|----------|--------------|
| emergency | 6 | 11 | 8h |
| boot | 4 | 26 | 12h |
| tech | 8 | 35 | 14h |
| db | 35 | 200 | 60h |
| logic | 10 | 18 | 18h |
| arch | 20 | 24 | 30h |
| security | 5 | 7 | 10h |
| frontend | 18 | 24 | 26h |
| defer | 0 | 0 | — |
