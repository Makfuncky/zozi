# ZOZI FORENSIC AUDIT

> **Generated:** 2026-10-02T20:38:10.140547+00:00  
> **Run ID:** `20261002T203716Z-9d68f1`  
> **Commit:** `6666d435a947e61ce63cf238439514a248891063`  
> **Mode:** fast (static only) · **Workers:** 10 · **Repo root:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
> **Benchmarks:** `_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`, `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md`, `_most_imp_docx/FEATURE_STACK.md`  
> **Surface:** 1953 Python · 1288 TS/TSX · 3895 total files walked (excludes `.git`, `.kilo`, `node_modules`, caches, build output).

## 0 · Pre-conditions (Phase 0 / 0.5)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | Boot smoke test | SKIPPED | --no-tools |
| 2 | Required env vars | PASS | .env.example declared=193; typed settings fields=188 |
| 3 | Database connectivity | PASS | postgresql://ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech:5432/neondb — ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech:5432 reachable (source: .env:DATABASE_URL) |
| 4 | Valkey connectivity | FAIL | valkey://localhost:6379/? — ConnectionRefusedError (source: .env:VALKEY_URL) |
| 5 | Test collection | SKIPPED | fast mode |
| 6 | Frontend type check | SKIPPED | fast mode |
| 7 | Backend lint | SKIPPED | fast mode |
| 8 | Alembic heads | SKIPPED | fast mode |
| 9 | Lockfile sync | PASS | requirements=55 uv-lock-entries=107 web-deps=29 pnpm-lock=yes |
| 10 | Architecture tests | SKIPPED | fast mode |

---
**VERDICT: NOT PRODUCTION READY** — 46 hard completion blocker(s).

## 1 · Headline numbers

| Metric | Value |
|---|---|
| Findings total | 574 |
| P0 / P1 / P2 / P3 | 45 / 354 / 114 / 61 |
| Older-status (COMPILED/RESOLVED/etc.) | 0 — this run emits NEW only |
| Completion blockers (yes / partial / no) | 46 / 157 / 371 |
| Clusters | 19 |
| Files with findings | 346 |
| Contradictions | 0 |
| Anti-pattern categories | 1 |
| Chains audited | 0 |
| Browser steps recorded | 0 |
| LLM-reviewed hotspots | 0 |
| HTTP responses probed | 0 |
| Recommendations (not blockers) | 0 |
| Estimated P0+P1 effort | ~987h (S=1h, M=2.5h, L=6h) |
| Coverage (dimensions with findings) | 4/28 |

---
## 2 · Completion blockers (fix before anything else)

**46** yes-blocker(s) · **157** partial-blocker(s) blocking some journeys/environments.

| ID | Phase | Dimension | File:Line | Fix | Effort | Priority | Conf | Verify | Depends on |
|---|---|---|---|---|---|---|---|---|---|
| BLOCK-valkey-unreachable | infra | 27 · Project Completion Blockers | backend/ | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | S | P0 | 5 | cd backend && python -c "import valkey; print(valkey.Valkey.from_url('valkey://host:6379').ping())" | — |
| LOGIC-120 | logic | 03 · Logical | backend/domains/country/services/tax/country_tax_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/tax/country_tax_service.py \| head -20 | — |
| LOGIC-127 | logic | 03 · Logical | backend/domains/finance/schemas/finance_schemas.py:11 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/schemas/finance_schemas.py \| head -20 | — |
| LOGIC-128 | logic | 03 · Logical | backend/domains/finance/services/commission_read_service.py:70 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/commission_read_service.py \| head -20 | — |
| LOGIC-129 | logic | 03 · Logical | backend/domains/finance/services/country/supplier_finance_service.py:160 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/country/supplier_finance_service.py \| head -20 | — |
| LOGIC-130 | logic | 03 · Logical | backend/domains/finance/services/data_import_service.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/data_import_service.py \| head -20 | — |
| LOGIC-131 | logic | 03 · Logical | backend/domains/finance/services/finance_service.py:66 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/finance_service.py \| head -20 | — |
| LOGIC-132 | logic | 03 · Logical | backend/domains/finance/services/ledger/accounting_controller.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/accounting_controller.py \| head -20 | — |
| LOGIC-133 | logic | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:5836 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/general_ledger.py \| head -20 | — |
| LOGIC-134 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_paypal.py:189 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_paypal.py \| head -20 | — |
| LOGIC-135 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_stripe.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_stripe.py \| head -20 | — |
| LOGIC-136 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:131 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_tap.py \| head -20 | — |
| LOGIC-137 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:4704 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_engine.py \| head -20 | — |
| LOGIC-138 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_orchestrator.py \| head -20 | — |
| LOGIC-139 | logic | 03 · Logical | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payouts/payout_batch_service.py \| head -20 | — |
| LOGIC-140 | logic | 03 · Logical | backend/domains/finance/services/trading_service.py:134 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/trading_service.py \| head -20 | — |
| LOGIC-141 | logic | 03 · Logical | backend/domains/finance/services/treasury/cash_management_service.py:269 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/treasury/cash_management_service.py \| head -20 | — |
| LOGIC-177 | logic | 03 · Logical | backend/domains/orders/services/cart/cart_service__orders.py:166 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/cart_service__orders.py \| head -20 | — |
| LOGIC-178 | logic | 03 · Logical | backend/domains/orders/services/cart/service.py:50 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/service.py \| head -20 | — |
| LOGIC-179 | logic | 03 · Logical | backend/domains/orders/services/core/logistics.py:1892 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/logistics.py \| head -20 | — |
| LOGIC-180 | logic | 03 · Logical | backend/domains/orders/services/core/misc.py:201 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/misc.py \| head -20 | — |
| LOGIC-181 | logic | 03 · Logical | backend/domains/orders/services/core/order_engine.py:906 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/order_engine.py \| head -20 | — |
| LOGIC-182 | logic | 03 · Logical | backend/domains/orders/services/orders_service.py:213 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/orders_service.py \| head -20 | — |
| LOGIC-183 | logic | 03 · Logical | backend/domains/orders/services/tracking/service.py:348 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/tracking/service.py \| head -20 | — |
| LOGIC-203 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders.py:337 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders.py \| head -20 | — |
| LOGIC-204 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_service.py:80 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders_service.py \| head -20 | — |
| LOGIC-209 | logic | 03 · Logical | backend/domains/suppliers/services/profile/supplier_payouts_service.py:73 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/profile/supplier_payouts_service.py \| head -20 | — |
| LOGIC-225 | logic | 03 · Logical | backend/modules/customer/routers/orders.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/orders.py \| head -20 | — |
| LOGIC-230 | logic | 03 · Logical | backend/modules/employee/routers/finance.py:466 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/finance.py \| head -20 | — |
| LOGIC-233 | logic | 03 · Logical | backend/modules/employee/routers/orders.py:53 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/orders.py \| head -20 | — |
| LOGIC-238 | logic | 03 · Logical | backend/modules/supplier/routers/finance.py:45 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/finance.py \| head -20 | — |
| LOGIC-242 | logic | 03 · Logical | backend/providers/ai/finance_ai.py:87 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/finance_ai.py \| head -20 | — |
| LOGIC-252 | logic | 03 · Logical | backend/providers/payments/base.py:99 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base.py \| head -20 | — |
| LOGIC-253 | logic | 03 · Logical | backend/providers/payments/base_models.py:31 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base_models.py \| head -20 | — |
| LOGIC-254 | logic | 03 · Logical | backend/providers/payments/webhook_models.py:42 | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/payments/webhook_models.py \| head -20 | — |
| LOGIC-320 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:169 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '169p' backend/domains/customers/services/coins/zozi_coins_service.py | — |
| LOGIC-321 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:182 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '182p' backend/domains/customers/services/coins/zozi_coins_service.py | — |
| LOGIC-322 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:371 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '371p' backend/domains/finance/services/payments/payment_engine.py | — |
| LOGIC-323 | logic | 03 · Logical | backend/domains/promotions/services/coupons/coupon_service.py:538 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '538p' backend/domains/promotions/services/coupons/coupon_service.py | — |
| LOGIC-324 | logic | 03 · Logical | backend/domains/promotions/services/coupons/coupon_service.py:554 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '554p' backend/domains/promotions/services/coupons/coupon_service.py | — |
| LOGIC-325 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:25 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '25p' backend/domains/security/services/detection/public_security_detection_service.py | — |
| LOGIC-326 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:83 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '83p' backend/domains/security/services/detection/public_security_detection_service.py | — |
| LOGIC-327 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:104 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '104p' backend/domains/security/services/detection/public_security_detection_service.py | — |
| LOGIC-328 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:127 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '127p' backend/domains/security/services/detection/public_security_detection_service.py | — |
| LOGIC-329 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:144 | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | sed -n '144p' backend/domains/security/services/detection/public_security_detection_service.py | — |
| ARCH-001 | arch | 01 · Architectural | backend/modules/finance:1 | Move finance routers under a canonical module or delete the package | M | P1 | 4 | ls backend/modules | — |

### Partial blockers

| ID | Phase | Dimension | File:Line | Fix | Effort | Priority | Conf | Verify | Depends on |
|---|---|---|---|---|---|---|---|---|---|
| ARCH-002 | arch | 01 · Architectural | backend/domains/media:1 | Demote media to canonical domain or document an ARCH change | M | P1 | 4 | ls backend/domains | — |
| ARCH-003 | arch | 01 · Architectural | backend/domains/payments:1 | Demote payments to canonical domain or document an ARCH change | M | P1 | 4 | ls backend/domains | — |
| MIG-001 | db | 10 · Migrations | backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:159 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '159p' backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py | — |
| MIG-006 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py:123 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '123p' backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py | — |
| MIG-007 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0003_add_version_columns.py:65 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '65p' backend/alembic/versions/2026_08_31_0003_add_version_columns.py | — |
| MIG-008 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0005_add_materialized_views.py:135 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '135p' backend/alembic/versions/2026_08_31_0005_add_materialized_views.py | — |
| MIG-009 | db | 10 · Migrations | backend/alembic/versions/2026_09_01_workspace.py:161 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '161p' backend/alembic/versions/2026_09_01_workspace.py | — |
| MIG-011 | db | 10 · Migrations | backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py:62 | Split into expand + contract steps with a rollback window | S | P1 | 3 | sed -n '62p' backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py | — |
| LOGIC-001 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health.py:1430 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/health/supplier_health.py | — |
| LOGIC-005 | logic | 03 · Logical | backend/domains/security/services/fraud/fraud_detection_service.py:102 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/security/services/fraud/fraud_detection_service.py | — |
| LOGIC-006 | logic | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:3774 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/ledger/general_ledger.py | — |
| LOGIC-009 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products.py:280 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/products/supplier_products.py | — |
| LOGIC-010 | logic | 03 · Logical | backend/domains/suppliers/services/supplier_shared.py:437 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/supplier_shared.py | — |
| LOGIC-018 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_service.py:518 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_service.py | — |
| LOGIC-020 | logic | 03 · Logical | backend/infrastructure/security/dependencies.py:49 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/infrastructure/security/dependencies.py | — |
| LOGIC-025 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:1111 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/payments/gateway_tap.py | — |
| LOGIC-026 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:693 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/payments/payment_orchestrator.py | — |
| LOGIC-032 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_verify_service.py:139 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_verify_service.py | — |
| LOGIC-046 | logic | 03 · Logical | backend/providers/payments/generic.py:25 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/providers/payments/generic.py | — |
| LOGIC-047 | logic | 03 · Logical | backend/providers/payments/paypal.py:135 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/providers/payments/paypal.py | — |
| LOGIC-052 | logic | 03 · Logical | backend/domains/accounts/services/auth/public_security_registration_service.py:69 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/accounts/services/auth/public_security_registration_service.py | — |
| LOGIC-062 | logic | 03 · Logical | backend/domains/finance/services/data_import_service.py:75 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/data_import_service.py | — |
| LOGIC-063 | logic | 03 · Logical | backend/domains/finance/services/finance_ai_service.py:87 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/finance_ai_service.py | — |
| LOGIC-064 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:3411 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/finance/services/payments/payment_engine.py | — |
| LOGIC-074 | logic | 03 · Logical | backend/domains/security/services/security_provider_helpers.py:30 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/security/services/security_provider_helpers.py | — |
| LOGIC-075 | logic | 03 · Logical | backend/domains/security/services/core/kms_encryption.py:78 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/security/services/core/kms_encryption.py | — |
| LOGIC-076 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:44 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/security/services/detection/public_security_detection_service.py | — |
| LOGIC-077 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_product_service.py:237 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/products/supplier_product_service.py | — |
| LOGIC-078 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products_service.py:203 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/domains/suppliers/services/products/supplier_products_service.py | — |
| LOGIC-084 | logic | 03 · Logical | backend/infrastructure/security/kms_integration.py:26 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/infrastructure/security/kms_integration.py | — |
| LOGIC-086 | logic | 03 · Logical | backend/providers/ai/finance_ai.py:88 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/providers/ai/finance_ai.py | — |
| LOGIC-088 | logic | 03 · Logical | backend/providers/finance/bank_api.py:115 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/providers/finance/bank_api.py | — |
| LOGIC-098 | logic | 03 · Logical | backend/providers/security/watchlist.py:73 | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | grep -n 'except' backend/providers/security/watchlist.py | — |
| LOGIC-100 | logic | 03 · Logical | backend/domains/accounts/services/permissions/permission_service.py:693 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/accounts/services/permissions/permission_service.py \| head -20 | — |
| LOGIC-101 | logic | 03 · Logical | backend/domains/analytics/services/dashboards/admin_analytics_service.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/analytics/services/dashboards/admin_analytics_service.py \| head -20 | — |
| LOGIC-102 | logic | 03 · Logical | backend/domains/analytics/services/dashboards/analytics_service.py:282 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/analytics/services/dashboards/analytics_service.py \| head -20 | — |
| LOGIC-103 | logic | 03 · Logical | backend/domains/catalog/services/categories/bulk_category_service.py:238 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/bulk_category_service.py \| head -20 | — |
| LOGIC-104 | logic | 03 · Logical | backend/domains/catalog/services/categories/categories_service.py:86 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/categories_service.py \| head -20 | — |
| LOGIC-105 | logic | 03 · Logical | backend/domains/catalog/services/categories/category_service.py:186 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/category_service.py \| head -20 | — |
| LOGIC-106 | logic | 03 · Logical | backend/domains/catalog/services/commission_service.py:285 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/commission_service.py \| head -20 | — |
| LOGIC-107 | logic | 03 · Logical | backend/domains/catalog/services/products/product_discount_service.py:65 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/products/product_discount_service.py \| head -20 | — |
| LOGIC-108 | logic | 03 · Logical | backend/domains/catalog/services/products/products_service.py:216 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/products/products_service.py \| head -20 | — |
| LOGIC-109 | logic | 03 · Logical | backend/domains/catalog/services/search/ai_search_service.py:78 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/search/ai_search_service.py \| head -20 | — |
| LOGIC-110 | logic | 03 · Logical | backend/domains/catalog/services/search/search_service.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/search/search_service.py \| head -20 | — |
| LOGIC-111 | logic | 03 · Logical | backend/domains/comms/services/email/email_management.py:341 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/email/email_management.py \| head -20 | — |
| LOGIC-112 | logic | 03 · Logical | backend/domains/comms/services/email/transactional.py:441 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/email/transactional.py \| head -20 | — |
| LOGIC-113 | logic | 03 · Logical | backend/domains/comms/services/messaging/chat_service.py:717 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/messaging/chat_service.py \| head -20 | — |
| LOGIC-114 | logic | 03 · Logical | backend/domains/comms/services/shared/utility/shared_utils.py:399 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/shared/utility/shared_utils.py \| head -20 | — |
| LOGIC-115 | logic | 03 · Logical | backend/domains/country/ports.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/ports.py \| head -20 | — |
| LOGIC-116 | logic | 03 · Logical | backend/domains/country/services/core/country_config_admin_service.py:286 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/core/country_config_admin_service.py \| head -20 | — |
| LOGIC-117 | logic | 03 · Logical | backend/domains/country/services/localization/localization_service.py:155 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/localization/localization_service.py \| head -20 | — |
| LOGIC-118 | logic | 03 · Logical | backend/domains/country/services/research/country_auto_populate.py:617 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/research/country_auto_populate.py \| head -20 | — |
| LOGIC-119 | logic | 03 · Logical | backend/domains/country/services/research/country_heuristic_engine.py:290 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/research/country_heuristic_engine.py \| head -20 | — |
| LOGIC-121 | logic | 03 · Logical | backend/domains/customers/services/cart_service.py:149 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/cart_service.py \| head -20 | — |
| LOGIC-122 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:274 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/coins/zozi_coins_service.py \| head -20 | — |
| LOGIC-123 | logic | 03 · Logical | backend/domains/customers/services/customer_health_engine.py:67 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/customer_health_engine.py \| head -20 | — |
| LOGIC-124 | logic | 03 · Logical | backend/domains/customers/services/profile_service.py:105 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/profile_service.py \| head -20 | — |
| LOGIC-125 | logic | 03 · Logical | backend/domains/customers/services/recommendations/recommendation_service.py:250 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/recommendations/recommendation_service.py \| head -20 | — |
| LOGIC-126 | logic | 03 · Logical | backend/domains/customers/services/search_service.py:51 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/search_service.py \| head -20 | — |
| LOGIC-142 | logic | 03 · Logical | backend/domains/governance/read_models/governance_read_models.py:96 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/read_models/governance_read_models.py \| head -20 | — |
| LOGIC-143 | logic | 03 · Logical | backend/domains/governance/schemas/governance_schemas.py:177 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/schemas/governance_schemas.py \| head -20 | — |
| LOGIC-144 | logic | 03 · Logical | backend/domains/governance/services/admin/admin_service.py:118 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/admin/admin_service.py \| head -20 | — |
| LOGIC-145 | logic | 03 · Logical | backend/domains/governance/services/approval/approval_matrix_service.py:30 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/approval/approval_matrix_service.py \| head -20 | — |
| LOGIC-146 | logic | 03 · Logical | backend/domains/governance/services/command_center/command_center_service.py:144 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/command_center/command_center_service.py \| head -20 | — |
| LOGIC-147 | logic | 03 · Logical | backend/domains/governance/services/command_center/service.py:344 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/command_center/service.py \| head -20 | — |
| LOGIC-148 | logic | 03 · Logical | backend/domains/governance/services/products_service.py:38 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/products_service.py \| head -20 | — |
| LOGIC-149 | logic | 03 · Logical | backend/domains/governance/services/settings/admin_service.py:41 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/settings/admin_service.py \| head -20 | — |
| LOGIC-150 | logic | 03 · Logical | backend/domains/governance/services/settings/governance_package_service.py:38 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/settings/governance_package_service.py \| head -20 | — |
| LOGIC-151 | logic | 03 · Logical | backend/domains/hr/services/employees/employee_service.py:152 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/employees/employee_service.py \| head -20 | — |
| LOGIC-152 | logic | 03 · Logical | backend/domains/hr/services/hr_employee_service.py:539 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/hr_employee_service.py \| head -20 | — |
| LOGIC-153 | logic | 03 · Logical | backend/domains/hr/services/learning/lms_service.py:148 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/learning/lms_service.py \| head -20 | — |
| LOGIC-154 | logic | 03 · Logical | backend/domains/hr/services/payroll/payroll_engine.py:377 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/payroll/payroll_engine.py \| head -20 | — |
| LOGIC-155 | logic | 03 · Logical | backend/domains/hr/services/payroll/payroll_service.py:265 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/payroll/payroll_service.py \| head -20 | — |
| LOGIC-156 | logic | 03 · Logical | backend/domains/hr/services/performance/dei_auditor.py:69 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/performance/dei_auditor.py \| head -20 | — |
| LOGIC-157 | logic | 03 · Logical | backend/domains/hr/services/performance/okr.py:190 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/performance/okr.py \| head -20 | — |
| LOGIC-158 | logic | 03 · Logical | backend/domains/hr/services/shift/shift_roster_service.py:164 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/shift/shift_roster_service.py \| head -20 | — |
| LOGIC-159 | logic | 03 · Logical | backend/domains/hr/services/travel/travel_service.py:152 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/travel/travel_service.py \| head -20 | — |
| LOGIC-160 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:40 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_fallback_service.py \| head -20 | — |
| LOGIC-161 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_imports_service.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_imports_service.py \| head -20 | — |
| LOGIC-162 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_operations_service.py:18 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_operations_service.py \| head -20 | — |
| LOGIC-163 | logic | 03 · Logical | backend/domains/logistics/services/core/logistics_engine.py:93 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/logistics_engine.py \| head -20 | — |
| LOGIC-164 | logic | 03 · Logical | backend/domains/logistics/services/core/service.py:1057 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/service.py \| head -20 | — |
| LOGIC-165 | logic | 03 · Logical | backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py:33 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py \| head -20 | — |
| LOGIC-166 | logic | 03 · Logical | backend/domains/logistics/services/geo/map_service.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/map_service.py \| head -20 | — |
| LOGIC-167 | logic | 03 · Logical | backend/domains/logistics/services/geo/routing_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/routing_service.py \| head -20 | — |
| LOGIC-168 | logic | 03 · Logical | backend/domains/logistics/services/geo/service.py:452 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/service.py \| head -20 | — |
| LOGIC-169 | logic | 03 · Logical | backend/domains/logistics/services/health/service.py:63 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/health/service.py \| head -20 | — |
| LOGIC-170 | logic | 03 · Logical | backend/domains/logistics/services/partners/admin_logistics_operations_service.py:221 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/admin_logistics_operations_service.py \| head -20 | — |
| LOGIC-171 | logic | 03 · Logical | backend/domains/logistics/services/partners/logistics_partner_service.py:232 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/logistics_partner_service.py \| head -20 | — |
| LOGIC-172 | logic | 03 · Logical | backend/domains/logistics/services/partners/logistics_pricing_service.py:62 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/logistics_pricing_service.py \| head -20 | — |
| LOGIC-173 | logic | 03 · Logical | backend/domains/logistics/services/partners/pricing_service.py:209 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/pricing_service.py \| head -20 | — |
| LOGIC-174 | logic | 03 · Logical | backend/domains/logistics/services/partners/service.py:229 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/service.py \| head -20 | — |
| LOGIC-175 | logic | 03 · Logical | backend/domains/logistics/services/partners/settlement_service.py:136 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/settlement_service.py \| head -20 | — |
| LOGIC-176 | logic | 03 · Logical | backend/domains/logistics/services/shipping/service.py:337 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/shipping/service.py \| head -20 | — |
| LOGIC-184 | logic | 03 · Logical | backend/domains/promotions/events.py:16 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/events.py \| head -20 | — |
| LOGIC-185 | logic | 03 · Logical | backend/domains/promotions/services/admin_promotion_ops_service.py:62 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/admin_promotion_ops_service.py \| head -20 | — |
| LOGIC-186 | logic | 03 · Logical | backend/domains/promotions/services/admin_promotion_service.py:95 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/admin_promotion_service.py \| head -20 | — |
| LOGIC-187 | logic | 03 · Logical | backend/domains/promotions/services/coins/coin_service.py:129 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coins/coin_service.py \| head -20 | — |
| LOGIC-188 | logic | 03 · Logical | backend/domains/promotions/services/coins/promotion_points_service.py:128 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coins/promotion_points_service.py \| head -20 | — |
| LOGIC-189 | logic | 03 · Logical | backend/domains/promotions/services/coupons/customer_coupons_create_service.py:29 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coupons/customer_coupons_create_service.py \| head -20 | — |
| LOGIC-190 | logic | 03 · Logical | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:47 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/admin_commerce_configuration_service.py \| head -20 | — |
| LOGIC-191 | logic | 03 · Logical | backend/domains/promotions/services/engine/admin_promotions_write_service.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/admin_promotions_write_service.py \| head -20 | — |
| LOGIC-192 | logic | 03 · Logical | backend/domains/promotions/services/engine/promotion_service.py:49 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/promotion_service.py \| head -20 | — |
| LOGIC-193 | logic | 03 · Logical | backend/domains/promotions/services/promotion_admin_write_service.py:77 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/promotion_admin_write_service.py \| head -20 | — |
| LOGIC-194 | logic | 03 · Logical | backend/domains/security/services/detection/confidence_scoring.py:106 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/security/services/detection/confidence_scoring.py \| head -20 | — |
| LOGIC-195 | logic | 03 · Logical | backend/domains/security/services/fraud/fraud_detection_service.py:485 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/security/services/fraud/fraud_detection_service.py \| head -20 | — |
| LOGIC-196 | logic | 03 · Logical | backend/domains/suppliers/events.py:113 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/events.py \| head -20 | — |
| LOGIC-197 | logic | 03 · Logical | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:56 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/analytics/supplier_analytics_service.py \| head -20 | — |
| LOGIC-198 | logic | 03 · Logical | backend/domains/suppliers/services/badges/badge_service.py:386 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/badges/badge_service.py \| head -20 | — |
| LOGIC-199 | logic | 03 · Logical | backend/domains/suppliers/services/contract/contract_service.py:52 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/contract/contract_service.py \| head -20 | — |
| LOGIC-200 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health.py:363 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/health/supplier_health.py \| head -20 | — |
| LOGIC-201 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health_engine.py:151 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/health/supplier_health_engine.py \| head -20 | — |
| LOGIC-202 | logic | 03 · Logical | backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py \| head -20 | — |
| LOGIC-205 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_product_service.py:47 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_product_service.py \| head -20 | — |
| LOGIC-206 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products.py:206 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_products.py \| head -20 | — |
| LOGIC-207 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products_service.py:120 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_products_service.py \| head -20 | — |
| LOGIC-208 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:119 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_supplier_upload_service.py \| head -20 | — |
| LOGIC-210 | logic | 03 · Logical | backend/domains/suppliers/services/profile/supplier_profile.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/profile/supplier_profile.py \| head -20 | — |
| LOGIC-211 | logic | 03 · Logical | backend/domains/suppliers/services/quality/quality_control_service.py:98 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/quality/quality_control_service.py \| head -20 | — |
| LOGIC-212 | logic | 03 · Logical | backend/domains/suppliers/services/settlement/multi_currency_settlement.py:90 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/settlement/multi_currency_settlement.py \| head -20 | — |
| LOGIC-213 | logic | 03 · Logical | backend/domains/suppliers/services/supplier_shared.py:200 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/supplier_shared.py \| head -20 | — |
| LOGIC-214 | logic | 03 · Logical | backend/domains/suppliers/services/tier/tier_service.py:102 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/tier/tier_service.py \| head -20 | — |
| LOGIC-215 | logic | 03 · Logical | backend/infrastructure/database/schemas.py:394 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/infrastructure/database/schemas.py \| head -20 | — |
| LOGIC-216 | logic | 03 · Logical | backend/infrastructure/database/seed/logistics.py:18 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/infrastructure/database/seed/logistics.py \| head -20 | — |
| LOGIC-217 | logic | 03 · Logical | backend/infrastructure/messaging/downstream_wiring.py:128 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/infrastructure/messaging/downstream_wiring.py \| head -20 | — |
| LOGIC-218 | logic | 03 · Logical | backend/infrastructure/utils/analytics.py:69 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/infrastructure/utils/analytics.py \| head -20 | — |
| LOGIC-219 | logic | 03 · Logical | backend/infrastructure/utils/currency_service.py:271 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/infrastructure/utils/currency_service.py \| head -20 | — |
| LOGIC-220 | logic | 03 · Logical | backend/modules/admin/routers/hr.py:32 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/hr.py \| head -20 | — |
| LOGIC-221 | logic | 03 · Logical | backend/modules/admin/routers/promotions.py:165 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/promotions.py \| head -20 | — |
| LOGIC-222 | logic | 03 · Logical | backend/modules/admin/routers/security.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/security.py \| head -20 | — |
| LOGIC-223 | logic | 03 · Logical | backend/modules/customer/routers/catalog.py:35 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/catalog.py \| head -20 | — |
| LOGIC-224 | logic | 03 · Logical | backend/modules/customer/routers/comms.py:25 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/comms.py \| head -20 | — |
| LOGIC-226 | logic | 03 · Logical | backend/modules/customer/routers/promotions.py:148 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/promotions.py \| head -20 | — |
| LOGIC-227 | logic | 03 · Logical | backend/modules/customer/serializers/customer_serializers.py:19 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/customer/serializers/customer_serializers.py \| head -20 | — |
| LOGIC-228 | logic | 03 · Logical | backend/modules/employee/routers/catalog.py:31 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/catalog.py \| head -20 | — |
| LOGIC-229 | logic | 03 · Logical | backend/modules/employee/routers/country.py:49 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/country.py \| head -20 | — |
| LOGIC-231 | logic | 03 · Logical | backend/modules/employee/routers/hr.py:122 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/hr.py \| head -20 | — |
| LOGIC-232 | logic | 03 · Logical | backend/modules/employee/routers/hr/schemas.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/hr/schemas.py \| head -20 | — |
| LOGIC-234 | logic | 03 · Logical | backend/modules/employee/routers/suppliers.py:53 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/suppliers.py \| head -20 | — |
| LOGIC-235 | logic | 03 · Logical | backend/modules/employee/serializers/employee_serializers.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/employee/serializers/employee_serializers.py \| head -20 | — |
| LOGIC-236 | logic | 03 · Logical | backend/modules/logistics/routers/logistics.py:1014 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/logistics/routers/logistics.py \| head -20 | — |
| LOGIC-237 | logic | 03 · Logical | backend/modules/supplier/routers/analytics.py:34 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/analytics.py \| head -20 | — |
| LOGIC-239 | logic | 03 · Logical | backend/modules/supplier/routers/logistics.py:32 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/logistics.py \| head -20 | — |
| LOGIC-240 | logic | 03 · Logical | backend/modules/supplier/serializers/supplier_serializers.py:19 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/serializers/supplier_serializers.py \| head -20 | — |
| LOGIC-241 | logic | 03 · Logical | backend/providers/ai/ai_variant_config.py:111 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/ai_variant_config.py \| head -20 | — |
| LOGIC-243 | logic | 03 · Logical | backend/providers/ai/price_intelligence.py:80 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/price_intelligence.py \| head -20 | — |
| LOGIC-244 | logic | 03 · Logical | backend/providers/ai/recommendation.py:273 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/recommendation.py \| head -20 | — |
| LOGIC-245 | logic | 03 · Logical | backend/providers/ai/search.py:120 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/search.py \| head -20 | — |
| LOGIC-246 | logic | 03 · Logical | backend/providers/ai/sentiment.py:215 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ai/sentiment.py \| head -20 | — |
| LOGIC-247 | logic | 03 · Logical | backend/providers/bg_removal/bg_removal_service.py:678 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/bg_removal/bg_removal_service.py \| head -20 | — |
| LOGIC-248 | logic | 03 · Logical | backend/providers/geography/rates.py:177 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/geography/rates.py \| head -20 | — |
| LOGIC-249 | logic | 03 · Logical | backend/providers/image/free_image_tools.py:811 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/image/free_image_tools.py \| head -20 | — |
| LOGIC-250 | logic | 03 · Logical | backend/providers/image/ocr.py:236 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/image/ocr.py \| head -20 | — |
| LOGIC-251 | logic | 03 · Logical | backend/providers/ocr/ocr_parser.py:178 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/ocr/ocr_parser.py \| head -20 | — |
| LOGIC-255 | logic | 03 · Logical | backend/providers/qr/qr_generator.py:103 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/qr/qr_generator.py \| head -20 | — |
| LOGIC-256 | logic | 03 · Logical | backend/providers/shipping/shipping_calculator.py:416 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/shipping/shipping_calculator.py \| head -20 | — |
| LOGIC-257 | logic | 03 · Logical | backend/providers/voice/voice_to_text.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | grep -nE 'float\(\|Float\|: float' backend/providers/voice/voice_to_text.py \| head -20 | — |

---
## 3 · Top findings (priority ranked)

| ID | Priority | Dimension | File:Line | Fix | Effort | Conf | Blocker |
|---|---|---|---|---|---|---|---|
| BLOCK-valkey-unreachable | P0 | 27 · Project Completion Blockers | backend/ | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | S | 5 | yes |
| LOGIC-120 | P0 | 03 · Logical | backend/domains/country/services/tax/country_tax_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-127 | P0 | 03 · Logical | backend/domains/finance/schemas/finance_schemas.py:11 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-128 | P0 | 03 · Logical | backend/domains/finance/services/commission_read_service.py:70 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-129 | P0 | 03 · Logical | backend/domains/finance/services/country/supplier_finance_service.py:160 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-130 | P0 | 03 · Logical | backend/domains/finance/services/data_import_service.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-131 | P0 | 03 · Logical | backend/domains/finance/services/finance_service.py:66 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-132 | P0 | 03 · Logical | backend/domains/finance/services/ledger/accounting_controller.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-133 | P0 | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:5836 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-134 | P0 | 03 · Logical | backend/domains/finance/services/payments/gateway_paypal.py:189 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-135 | P0 | 03 · Logical | backend/domains/finance/services/payments/gateway_stripe.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-136 | P0 | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:131 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-137 | P0 | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:4704 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-138 | P0 | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-139 | P0 | 03 · Logical | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-140 | P0 | 03 · Logical | backend/domains/finance/services/trading_service.py:134 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-141 | P0 | 03 · Logical | backend/domains/finance/services/treasury/cash_management_service.py:269 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-177 | P0 | 03 · Logical | backend/domains/orders/services/cart/cart_service__orders.py:166 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-178 | P0 | 03 · Logical | backend/domains/orders/services/cart/service.py:50 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-179 | P0 | 03 · Logical | backend/domains/orders/services/core/logistics.py:1892 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |

---
## 4 · Clusters (shared root causes)

| Cluster | Size | Members | Recommended single fix | Yes-blockers |
|---|---|---|---|---|
| CLUSTER-float-money | 158 | LOGIC-100, LOGIC-101, LOGIC-102, LOGIC-103, LOGIC-104, LOGIC-105, LOGIC-106, LOGIC-107, LOGIC-108, LOGIC-109, LOGIC-110, LOGIC-111... | Convert to Decimal and use kernel.money rounding helpers | 34 |
| CLUSTER-silent-except | 99 | LOGIC-001, LOGIC-002, LOGIC-003, LOGIC-004, LOGIC-005, LOGIC-006, LOGIC-007, LOGIC-008, LOGIC-009, LOGIC-010, LOGIC-011, LOGIC-012... | Add logger.warning(..., exc_info=True) or re-raise | 0 |
| CLUSTER-cross-domain-direct | 92 | ARCH-110, ARCH-111, ARCH-112, ARCH-113, ARCH-114, ARCH-115, ARCH-116, ARCH-117, ARCH-118, ARCH-119, ARCH-120, ARCH-121... | Move the call behind the owning domain's ports/ or emit an event | 0 |
| CLUSTER-module-imports-infrastructure | 69 | ARCH-041, ARCH-042, ARCH-043, ARCH-044, ARCH-045, ARCH-046, ARCH-047, ARCH-048, ARCH-049, ARCH-050, ARCH-051, ARCH-052... | Route through the sanctioned layer (events/ports/service call) | 0 |
| CLUSTER-long-function | 60 | LOGIC-258, LOGIC-259, LOGIC-260, LOGIC-261, LOGIC-262, LOGIC-263, LOGIC-264, LOGIC-265, LOGIC-266, LOGIC-267, LOGIC-268, LOGIC-269... | Split the longest functions by responsibility | 0 |
| CLUSTER-allowlist | 20 | ARCH-004, ARCH-005, ARCH-006, ARCH-007, ARCH-008, ARCH-009, ARCH-010, ARCH-011, ARCH-012, ARCH-013, ARCH-014, ARCH-015... | Add the removal date or remove the entry | 0 |
| CLUSTER-circular-import | 16 | ARCH-202, ARCH-203, ARCH-204, ARCH-205, ARCH-206, ARCH-207, ARCH-208, ARCH-209, ARCH-210, ARCH-211, ARCH-212, ARCH-213... | Break the cycle with a port/event boundary | 0 |
| CLUSTER-infra-imports-above | 15 | ARCH-024, ARCH-025, ARCH-026, ARCH-027, ARCH-028, ARCH-029, ARCH-030, ARCH-031, ARCH-032, ARCH-033, ARCH-034, ARCH-035... | Route through the sanctioned layer (events/ports/service call) | 0 |
| CLUSTER-router-business-logic | 10 | ARCH-218, ARCH-220, ARCH-221, ARCH-222, ARCH-224, ARCH-225, ARCH-226, ARCH-227, ARCH-231, ARCH-232 | Extract branching logic into the domain service | 0 |
| CLUSTER-idempotency | 10 | LOGIC-320, LOGIC-321, LOGIC-322, LOGIC-323, LOGIC-324, LOGIC-325, LOGIC-326, LOGIC-327, LOGIC-328, LOGIC-329 | Make the idempotency key required and enforce uniqueness | 10 |
| CLUSTER-migration-destructive | 6 | MIG-001, MIG-006, MIG-007, MIG-008, MIG-009, MIG-011 | Split into expand + contract steps with a rollback window | 0 |
| CLUSTER-migration-downgrade | 6 | MIG-002, MIG-003, MIG-004, MIG-005, MIG-010, MIG-012 | Implement downgrade() or document irreversibility | 0 |
| CLUSTER-extra-domain | 2 | ARCH-002, ARCH-003 | Demote media to canonical domain or document an ARCH change | 0 |
| CLUSTER-middleware-imports-above | 2 | ARCH-039, ARCH-040 | Route through the sanctioned layer (events/ports/service call) | 0 |
| CLUSTER-router-db-access | 2 | ARCH-219, ARCH-223 | Move DB access into the domain service | 0 |
| CLUSTER-boot-preflight | 1 | BLOCK-valkey-unreachable | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | 1 |
| CLUSTER-extra-module | 1 | ARCH-001 | Move finance routers under a canonical module or delete the package | 1 |
| CLUSTER-deep-nesting | 1 | LOGIC-318 | Refactor with guard clauses / extracted helpers | 0 |
| CLUSTER-todo-hygiene | 1 | LOGIC-319 | Link each TODO to a ticket or delete it | 0 |

---
## 5 · Dimensions

## Dimension 01 · Architectural

### Summary
- Confirmation: ❌ FAIL
- Files with findings: 146
- Findings: 232
- P0: 0  P1: 199  P2: 33  P3: 0
- Clusters: 10
- Laws implicated: L-1, L-2, L-3, L-7, L-8, L-12, L-13, L-17, L-90, L-97, L-98, L-99, L-100, L-101, L-102, L-103, L-104, L-134
- Completion blockers: 1 yes · 2 partial · 229 no
- Observations: 101 (L0: 101)
- Status: NEW: 232 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Conf | Evidence | Truth | Claim | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker | Laws |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARCH-110 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/accounts/models/user.py:21 | cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/accounts | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-111 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/accounts/models/user.py:22 | cross-domain import `domains.customers.models.customer_schema_models` (domains.accounts -> domains.customers); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.customers.models.customer_schema_models` (domains.accounts -> domains.customers); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.customers' backend/domains/accounts | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-112 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/accounts/services/permissions/permission_service.py:699 | cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/accounts | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-113 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/accounts/services/users/user_management_service.py:87 | cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/accounts | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-114 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/analytics/models/analytics_schema_models.py:85 | cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/analytics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-118 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/audit/services/compliance_engine.py:13 | cross-domain import `domains.hr.models.employee_models` (domains.audit -> domains.hr); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.audit -> domains.hr); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/audit | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-115 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/audit/services/compliance_engine.py:16 | cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/audit | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-116 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/audit/services/data_residency_service.py:11 | cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/audit | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-117 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/audit/services/ediscovery.py:171 | cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/audit | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-121 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/catalog/ports.py:27 | cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/catalog | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-120 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/catalog/services/products/admin_products_service.py:393 | cross-domain import `domains.governance.models.core` (domains.catalog -> domains.governance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.core` (domains.catalog -> domains.governance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/catalog | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-119 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/catalog/services/products/admin_products_service.py:395 | cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/catalog | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-124 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/models/communication.py:8 | cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-128 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/models/suppliers.py:12 | cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.suppliers' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-127 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/ports.py:50 | cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-122 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/services/messaging/chat_service.py:459 | cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-126 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/services/messaging/chat_service.py:562 | cross-domain import `domains.governance.models.core` (domains.comms -> domains.governance); 19 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.core` (domains.comms -> domains.governance); 19 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-123 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/services/shared/utility/shared_utils.py:251 | cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-125 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/comms/services/tickets/tickets_service.py:2 | cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/comms | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-129 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/country/models/country_enhancements.py:10 | cross-domain import `domains.accounts.models` (domains.country -> domains.accounts); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models` (domains.country -> domains.accounts); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/country | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-131 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/country/ports.py:23 | cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/country | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-132 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/country/services/core/country_service.py:1789 | cross-domain import `domains.governance.models.legal_contract_template` (domains.country -> domains.governance); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.legal_contract_template` (domains.country -> domains.governance); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/country | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-130 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/country/services/core/country_service.py:1792 | cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.customers' backend/domains/country | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-133 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/country/services/geo/country_detection.py:149 | cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/country | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-134 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/customers/services/cart_service.py:23 | cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/customers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-135 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/customers/services/cart_service.py:24 | cross-domain import `domains.catalog.models.products` (domains.customers -> domains.catalog); 5 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.customers -> domains.catalog); 5 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/customers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-137 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/customers/services/coupons_read_service.py:17 | cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/customers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-136 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/customers/services/customer_health_engine.py:11 | cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/customers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-142 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/country/admin_commission_service.py:11 | cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-144 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/country/supplier_finance_service.py:23 | cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-139 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/data_import_service.py:13 | cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-143 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/data_import_service.py:17 | cross-domain import `domains.logistics.models.erp` (domains.finance -> domains.logistics); 26 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.logistics.models.erp` (domains.finance -> domains.logistics); 26 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.logistics' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-138 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/finance_service.py:495 | cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-141 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/ledger/general_ledger.py:1439 | cross-domain import `domains.country.models.countries` (domains.finance -> domains.country); 5 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.finance -> domains.country); 5 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-140 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/ledger/general_ledger.py:3005 | cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-145 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/finance/services/payments/payment_engine.py:73 | cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/finance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-150 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/models/admin.py:9 | cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-146 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:24 | cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 21 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 21 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-158 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:25 | cross-domain import `domains.suppliers.models.suppliers` (domains.governance -> domains.suppliers); 10 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.suppliers.models.suppliers` (domains.governance -> domains.suppliers); 10 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.suppliers' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-156 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:26 | cross-domain import `domains.promotions.models.coupon_usage` (domains.governance -> domains.promotions); 15 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.models.coupon_usage` (domains.governance -> domains.promotions); 15 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-151 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:35 | cross-domain import `domains.customers.models.customer_schema_models` (domains.governance -> domains.customers); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.customers.models.customer_schema_models` (domains.governance -> domains.customers); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.customers' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-157 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:36 | cross-domain import `domains.security.models.fraud` (domains.governance -> domains.security); 39 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.security.models.fraud` (domains.governance -> domains.security); 39 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.security' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-149 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/ports.py:38 | cross-domain import `domains.comms.models.fraud` (domains.governance -> domains.comms); 26 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.fraud` (domains.governance -> domains.comms); 26 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-152 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/admin/bulk_ops_service.py:18 | cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-153 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/approval/approval_matrix_service.py:17 | cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-147 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/audit/__init__.py:2 | cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.audit' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-148 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/export_read_service.py:15 | cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-155 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/export_read_service.py:16 | cross-domain import `domains.orders.models.orders` (domains.governance -> domains.orders); 12 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.models.orders` (domains.governance -> domains.orders); 12 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-154 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/governance/services/users_service.py:10 | cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.logistics' backend/domains/governance | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-160 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/hr/models/employee_models.py:7 | cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/hr | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-162 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/hr/services/employees/coi_service.py:19 | cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/hr | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-161 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/hr/services/employees/hr_service.py:678 | cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/hr | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-159 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/hr/services/hr_employee_service.py:20 | cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/hr | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-168 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/models/logistics_entities.py:9 | cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 47 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 47 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-163 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/models/logistics_schema_models.py:50 | cross-domain import `domains.accounts.models.banking` (domains.logistics -> domains.accounts); 27 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.banking` (domains.logistics -> domains.accounts); 27 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-166 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/ports.py:193 | cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-164 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:22 | cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-169 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:23 | cross-domain import `domains.governance.models.admin` (domains.logistics -> domains.governance); 67 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.admin` (domains.logistics -> domains.governance); 67 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-170 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:26 | cross-domain import `domains.hr.models.employee_models` (domains.logistics -> domains.hr); 6 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.logistics -> domains.hr); 6 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-171 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:36 | cross-domain import `domains.orders.models.orders` (domains.logistics -> domains.orders); 25 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.models.orders` (domains.logistics -> domains.orders); 25 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-165 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/admin_logistics_operations_service.py:8 | cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-167 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/country_communication_service.py:13 | cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.customers' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-173 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/core/shipment_service.py:16 | cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.suppliers' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-172 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/logistics/services/health/service.py:114 | cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.security' backend/domains/logistics | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-002 | arch | NEW | CLUSTER-extra-domain | backend/domains/media:1 | domain package `media` exists | fixed 15 domains (Law 12); media/treasury/ai/configuration are schemas only | domain package `media` exists | Demote media to canonical domain or document an ARCH change | M | P1 | 4 | multiple | L0 | VERIFIED | — | ls backend/domains | — | git revert <commit> | — | — | — | partial | L-12 |
| ARCH-178 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/models/order_entities.py:8 | cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-176 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/ports.py:1491 | cross-domain import `domains.catalog.models.products` (domains.orders -> domains.catalog); 10 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.orders -> domains.catalog); 10 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-174 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/ports.py:1538 | cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-184 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/ports.py:1600 | cross-domain import `domains.promotions.services.admin_promotion_service` (domains.orders -> domains.promotions); 8 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.promotions.services.admin_promotion_service` (domains.orders -> domains.promotions); 8 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.promotions' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-181 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/cart/service.py:30 | cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-177 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/core/admin_extra.py:146 | cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-182 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/core/misc.py:370 | cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-179 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/core/order_engine.py:27 | cross-domain import `domains.customers.services.coupons_service` (domains.orders -> domains.customers); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.customers.services.coupons_service` (domains.orders -> domains.customers); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.customers' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-175 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/core/order_engine.py:49 | cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.audit' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-185 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/disputes/service.py:16 | cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.suppliers' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-183 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/logistics_service.py:16 | cross-domain import `domains.logistics.services.core.shipment_service` (domains.orders -> domains.logistics); 33 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.logistics.services.core.shipment_service` (domains.orders -> domains.logistics); 33 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.logistics' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-180 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/orders/services/orders_service.py:25 | cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/orders | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-003 | arch | NEW | CLUSTER-extra-domain | backend/domains/payments:1 | domain package `payments` exists | fixed 15 domains (Law 12); media/treasury/ai/configuration are schemas only | domain package `payments` exists | Demote payments to canonical domain or document an ARCH change | M | P1 | 4 | multiple | L0 | VERIFIED | — | ls backend/domains | — | git revert <commit> | — | — | — | partial | L-12 |
| ARCH-188 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/promotions/models/coupon_usage.py:9 | cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/promotions | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-187 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/promotions/services/coupons/coupon_service.py:47 | cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/promotions | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-190 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/promotions/services/coupons/customer_coupons_create_service.py:21 | cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/promotions | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-186 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:6 | cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/promotions | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-189 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:9 | cross-domain import `domains.governance.models.admin` (domains.promotions -> domains.governance); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance.models.admin` (domains.promotions -> domains.governance); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/promotions | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-191 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/security/services/detection/public_security_detection_service.py:8 | cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/security | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-193 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/security/services/fraud/fraud_detection_service.py:30 | cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.suppliers' backend/domains/security | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-192 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/security/services/health/flat_risk_service.py:10 | cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.hr' backend/domains/security | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-199 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/models/suppliers.py:233 | cross-domain import `domains.governance` (domains.suppliers -> domains.governance); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.governance` (domains.suppliers -> domains.governance); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.governance' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-194 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/models/suppliers.py:249 | cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.accounts' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-195 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:12 | cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.catalog' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-201 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:14 | cross-domain import `domains.orders.models.orders` (domains.suppliers -> domains.orders); 14 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.orders.models.orders` (domains.suppliers -> domains.orders); 14 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.orders' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-198 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/badges/badge_write_service.py:31 | cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.finance' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-197 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/contract/contract_service.py:15 | cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.country' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-196 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/disputes_service.py:14 | cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.comms' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-200 | arch | NEW | CLUSTER-cross-domain-direct | backend/domains/suppliers/services/health/supplier_health.py:15 | cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrence(s) in this file | cross-domain reads via ports.py, writes via events.py (Law 3) | cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrence(s) in this file | Move the call behind the owning domain's ports/ or emit an event | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -rn 'from domains.logistics' backend/domains/suppliers | — | git revert <commit> | — | — | — | no | L-3,L-17 |
| ARCH-024 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/database/init_db.py:49 | `infra imports above`: imports `domains` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains' backend/infrastructure/database/init_db.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-025 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/database/seed/_common.py:1078 | `infra imports above`: imports `domains.finance.services.seeders.treasury_seeder` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.finance.services.seeders.treasury_seeder` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.finance.services.seeders.treasury_seeder' backend/infrastructure/database/seed/_common.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-026 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/geography/__init__.py:8 | `infra imports above`: imports `providers.geography.geoip` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.geography.geoip` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.geography.geoip' backend/infrastructure/geography/__init__.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-027 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/geography/__init__.py:9 | `infra imports above`: imports `providers.geography.ip` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.geography.ip` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.geography.ip' backend/infrastructure/geography/__init__.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-028 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/messaging/email_service.py:28 | `infra imports above`: imports `providers.comms.email` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.comms.email` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.comms.email' backend/infrastructure/messaging/email_service.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-029 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/messaging/realtime.py:495 | `infra imports above`: imports `domains.accounts.models.user` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.accounts.models.user` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.accounts.models.user' backend/infrastructure/messaging/realtime.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-030 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/ml/worker.py:52 | `infra imports above`: imports `providers.image.bg_remover` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.image.bg_remover` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.image.bg_remover' backend/infrastructure/ml/worker.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-031 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/storage/backup.py:300 | `infra imports above`: imports `providers.storage` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.storage` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.storage' backend/infrastructure/storage/backup.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-032 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/storage/storage.py:27 | `infra imports above`: imports `providers.storage` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `providers.storage` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.storage' backend/infrastructure/storage/storage.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-033 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/category_tree.py:56 | `infra imports above`: imports `domains.catalog.models.products` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.catalog.models.products` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.catalog.models.products' backend/infrastructure/utils/category_tree.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-034 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/category_tree.py:76 | `infra imports above`: imports `domains.catalog.models.products` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.catalog.models.products` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.catalog.models.products' backend/infrastructure/utils/category_tree.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-035 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/country_detection_middleware.py:2 | `infra imports above`: imports `middleware.country_context` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `middleware.country_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'middleware.country_context' backend/infrastructure/utils/country_detection_middleware.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-036 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/country_rls.py:26 | `infra imports above`: imports `domains.country.models.country_enhancements` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.country.models.country_enhancements` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.country.models.country_enhancements' backend/infrastructure/utils/country_rls.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-037 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/country_rls.py:102 | `infra imports above`: imports `domains.country.models.countries` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.country.models.countries` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.country.models.countries' backend/infrastructure/utils/country_rls.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-038 | arch | NEW | CLUSTER-infra-imports-above | backend/infrastructure/utils/import_service.py:14 | `infra imports above`: imports `domains.logistics.models.erp` | Arrows point down only (Law 1/97-106) | `infra imports above`: imports `domains.logistics.models.erp` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.logistics.models.erp' backend/infrastructure/utils/import_service.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-039 | arch | NEW | CLUSTER-middleware-imports-above | backend/middleware/dependencies/auth.py:19 | `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies` | Arrows point down only (Law 1/97-106) | `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'domains.accounts.services.auth.security_dependencies' backend/middleware/dependencies/auth.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-040 | arch | NEW | CLUSTER-middleware-imports-above | backend/middleware/dependencies/country_detection.py:34 | `middleware imports above`: imports `providers.geography.ip` | Arrows point down only (Law 1/97-106) | `middleware imports above`: imports `providers.geography.ip` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'providers.geography.ip' backend/middleware/dependencies/country_detection.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-041 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/accounts.py:50 | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.schemas.CreateStaffAccount' backend/modules/admin/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-042 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/accounts.py:50 | `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.schemas.UpdateStaffAccount' backend/modules/admin/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-043 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/catalog.py:36 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_super_admin' backend/modules/admin/routers/catalog.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-044 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/comms.py:10 | `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.messaging.ws_manager.manager' backend/modules/admin/routers/comms.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-045 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/governance.py:12 | `module imports infrastructure`: imports `infrastructure.utils.config.settings` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.config.settings` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.config.settings' backend/modules/admin/routers/governance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-046 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/logistics.py:10 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_super_admin' backend/modules/admin/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-047 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/logistics.py:12 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/admin/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-048 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/logistics.py:13 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/admin/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-049 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/logistics.py:13 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/admin/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-050 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/promotions.py:32 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/admin/routers/promotions.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-051 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/promotions.py:33 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/admin/routers/promotions.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-052 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/promotions.py:33 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/admin/routers/promotions.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-219 | arch | NEW | CLUSTER-router-db-access | backend/modules/admin/routers/staff.py:1 | router touches DB/ORM directly (1 hit(s)) | router = auth + require_feature + ONE service call (Law 2) | router touches DB/ORM directly (1 hit(s)) | Move DB access into the domain service | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'get_db\|Session\|session\.' backend/modules/admin/routers/staff.py | — | git revert <commit> | — | — | — | no | L-2,L-90 |
| ARCH-053 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/staff.py:32 | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.schemas.CreateStaffAccount' backend/modules/admin/routers/staff.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-054 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/staff.py:32 | `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.schemas.UpdateStaffAccount' backend/modules/admin/routers/staff.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-055 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/admin/routers/staff.py:38 | `module imports infrastructure`: imports `infrastructure.security.country_access.get_country_access_scope` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.country_access.get_country_access_scope` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.country_access.get_country_access_scope' backend/modules/admin/routers/staff.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-056 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/accounts.py:10 | `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.verify_captcha' backend/modules/customer/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-057 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/accounts.py:247 | `module imports infrastructure`: imports `infrastructure.utils.auth.decode_token` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.auth.decode_token` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.auth.decode_token' backend/modules/customer/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-058 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/catalog.py:20 | `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.get_current_user_optional' backend/modules/customer/routers/catalog.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-059 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/country.py:13 | `module imports infrastructure`: imports `infrastructure.utils.currency_service.get_currency_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.currency_service.get_currency_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.currency_service.get_currency_context' backend/modules/customer/routers/country.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-060 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/orders.py:13 | `module imports infrastructure`: imports `infrastructure.utils.config.settings` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.config.settings` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.config.settings' backend/modules/customer/routers/orders.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-223 | arch | NEW | CLUSTER-router-db-access | backend/modules/customer/routers/reviews.py:1 | router touches DB/ORM directly (1 hit(s)) | router = auth + require_feature + ONE service call (Law 2) | router touches DB/ORM directly (1 hit(s)) | Move DB access into the domain service | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'get_db\|Session\|session\.' backend/modules/customer/routers/reviews.py | — | git revert <commit> | — | — | — | no | L-2,L-90 |
| ARCH-061 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/customer/routers/reviews.py:30 | `module imports infrastructure`: imports `infrastructure.storage.storage._store` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.storage.storage._store` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.storage.storage._store' backend/modules/customer/routers/reviews.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-062 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/attendance.py:8 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/attendance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-063 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/finance.py:1207 | `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_html` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_html` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.invoice_html.generate_invoice_html' backend/modules/employee/routers/finance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-064 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/finance.py:1207 | `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_pdf_bytes` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_pdf_bytes` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.invoice_html.generate_invoice_pdf_bytes' backend/modules/employee/routers/finance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-065 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/hr.py:13 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-068 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/hr/attendance.py:9 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/attendance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-069 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/hr/employees.py:9 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/employees.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-070 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/hr/leaves.py:7 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/leaves.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-071 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/hr/offices.py:7 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/offices.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-066 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/offices.py:8 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/offices.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-067 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/employee/routers/orders.py:11 | `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.background_jobs.get_job' backend/modules/employee/routers/orders.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-001 | arch | NEW | CLUSTER-extra-module | backend/modules/finance:1 | top-level module `finance` exists | fixed 5 modules: admin, customer, employee, logistics, supplier (Law 13) | top-level module `finance` exists | Move finance routers under a canonical module or delete the package | M | P1 | 4 | multiple | L0 | VERIFIED | — | ls backend/modules | — | git revert <commit> | — | — | — | yes | L-13 |
| ARCH-072 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:307 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-073 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:308 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-074 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:308 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-075 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:318 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-076 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:319 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-077 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:319 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-078 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:329 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-079 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:335 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-080 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:336 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-081 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:336 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-082 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:346 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-083 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:347 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-084 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:347 | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-085 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/finance/routers/cash_management.py:357 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-086 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/accounts.py:15 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-087 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/analytics.py:15 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/analytics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-088 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/catalog.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/catalog.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-089 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/comms.py:18 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/comms.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-090 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/country.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/country.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-091 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/hr.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/hr.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-092 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/logistics.py:12 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-093 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/logistics.py:14 | `module imports infrastructure`: imports `infrastructure.utils.pagination.paginated_response` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.utils.pagination.paginated_response` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.utils.pagination.paginated_response' backend/modules/logistics/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-094 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/orders.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/orders.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-095 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/promotions.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/promotions.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-096 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/security.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/security.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-097 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/logistics/routers/suppliers.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/suppliers.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-098 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/accounts.py:14 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/accounts.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-099 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/analytics.py:18 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/analytics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-100 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/catalog.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/catalog.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-101 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/comms.py:18 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/comms.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-102 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/country.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/country.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-103 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/finance.py:10 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/finance.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-104 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/hr.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/hr.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-105 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/logistics.py:14 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/logistics.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-106 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/orders.py:10 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/orders.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-107 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/promotions.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/promotions.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-108 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/security.py:7 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/security.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-109 | arch | NEW | CLUSTER-module-imports-infrastructure | backend/modules/supplier/routers/suppliers.py:8 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Arrows point down only (Law 1/97-106) | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` | Route through the sanctioned layer (events/ports/service call) | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/suppliers.py | — | git revert <commit> | — | — | — | no | L-1,L-97,L-98,L-99,L-100,L-101,L-102,L-103,L-104 |
| ARCH-203 | arch | NEW | CLUSTER-circular-import | domains.accounts ↔ domains.audit | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics | no circular imports between packages (Law 98) | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers -> domains.finance -> domains.governance | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-212 | arch | NEW | CLUSTER-circular-import | domains.accounts ↔ domains.audit | circular package dependency: domains.accounts -> domains.audit | no circular imports between packages (Law 98) | circular package dependency: domains.accounts -> domains.audit | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-213 | arch | NEW | CLUSTER-circular-import | domains.accounts ↔ domains.audit | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> infrastructure | no circular imports between packages (Law 98) | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> infrastructure | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-215 | arch | NEW | CLUSTER-circular-import | domains.accounts ↔ domains.audit | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers | no circular imports between packages (Law 98) | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-202 | arch | NEW | CLUSTER-circular-import | domains.audit ↔ domains.catalog | circular package dependency: domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics | no circular imports between packages (Law 98) | circular package dependency: domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-210 | arch | NEW | CLUSTER-circular-import | domains.catalog ↔ domains.comms | circular package dependency: domains.catalog -> domains.comms | no circular imports between packages (Law 98) | circular package dependency: domains.catalog -> domains.comms | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-214 | arch | NEW | CLUSTER-circular-import | domains.catalog ↔ domains.country | circular package dependency: domains.catalog -> domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics | no circular imports between packages (Law 98) | circular package dependency: domains.catalog -> domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-204 | arch | NEW | CLUSTER-circular-import | domains.country ↔ domains.customers | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics -> domains.orders | no circular imports between packages (Law 98) | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics -> domains.orders | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-209 | arch | NEW | CLUSTER-circular-import | domains.country ↔ domains.customers | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.hr | no circular imports between packages (Law 98) | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.hr | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-217 | arch | NEW | CLUSTER-circular-import | domains.country ↔ domains.customers | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics -> domains.orders -> domains.promotions | no circular imports between packages (Law 98) | circular package dependency: domains.country -> domains.customers -> domains.finance -> domains.governance -> domains.logistics -> domains.orders -> domains.promotions | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-206 | arch | NEW | CLUSTER-circular-import | domains.finance ↔ domains.governance | circular package dependency: domains.finance -> domains.governance -> domains.logistics -> domains.orders -> domains.security -> domains.suppliers | no circular imports between packages (Law 98) | circular package dependency: domains.finance -> domains.governance -> domains.logistics -> domains.orders -> domains.security -> domains.suppliers | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-207 | arch | NEW | CLUSTER-circular-import | domains.finance ↔ domains.governance | circular package dependency: domains.finance -> domains.governance -> domains.hr | no circular imports between packages (Law 98) | circular package dependency: domains.finance -> domains.governance -> domains.hr | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-208 | arch | NEW | CLUSTER-circular-import | domains.finance ↔ domains.logistics | circular package dependency: domains.finance -> domains.logistics | no circular imports between packages (Law 98) | circular package dependency: domains.finance -> domains.logistics | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-211 | arch | NEW | CLUSTER-circular-import | domains.finance ↔ domains.logistics | circular package dependency: domains.finance -> domains.logistics -> domains.orders | no circular imports between packages (Law 98) | circular package dependency: domains.finance -> domains.logistics -> domains.orders | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-216 | arch | NEW | CLUSTER-circular-import | domains.logistics ↔ domains.orders | circular package dependency: domains.logistics -> domains.orders -> domains.suppliers | no circular imports between packages (Law 98) | circular package dependency: domains.logistics -> domains.orders -> domains.suppliers | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-205 | arch | NEW | CLUSTER-circular-import | domains.orders ↔ domains.promotions | circular package dependency: domains.orders -> domains.promotions | no circular imports between packages (Law 98) | circular package dependency: domains.orders -> domains.promotions | Break the cycle with a port/event boundary | M | P1 | 4 | multiple | L1 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-98 |
| ARCH-004 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.models.suppliers: SupplierProfile` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.models.suppliers: SupplierProfile` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-005 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.governance.models.admin: CommissionBadgeTier, Commissio` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.governance.models.admin: CommissionBadgeTier, Commissio` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-006 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.comms.models.suppliers: SupplierProfile` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.comms.models.suppliers: SupplierProfile` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-007 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governance.models.admin: CommissionBadgeTier, Commissi` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governance.models.admin: CommissionBadgeTier, Commissi` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-008 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.catalog.ports: Product` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.catalog.ports: Product` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-009 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governance.ports: User` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governance.ports: User` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-010 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> fastapi: HTTPException, Depends, Query` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> fastapi: HTTPException, Depends, Query` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-011 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> modules.admin.routers.auth: require_admin, require_permission` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> modules.admin.routers.auth: require_admin, require_permission` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-012 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> fastapi: HTTPException` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> fastapi: HTTPException` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-013 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> modules.admin.routers.auth: require_admin` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> modules.admin.routers.auth: require_admin` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-014 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_controller -> domains.finance.services.commission.commission_service: _re` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_controller -> domains.finance.services.commission.commission_service: _re` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-015 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.country.admin_payouts_service -> infrastructure.utils.dependencies: require_admin` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.country.admin_payouts_service -> infrastructure.utils.dependencies: require_admin` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-016 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.payments.public_treasury_payments_service -> infrastructure.utils.dependencies: require_admin` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.payments.public_treasury_payments_service -> infrastructure.utils.dependencies: require_admin` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-017 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.treasury.cash_management_service -> fastapi: HTTPException, Depends, Query` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.treasury.cash_management_service -> fastapi: HTTPException, Depends, Query` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-018 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.treasury.cash_management_service -> modules.admin.routers.auth: require_admin, require_permissi` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.treasury.cash_management_service -> modules.admin.routers.auth: require_admin, require_permissi` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-019 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.*.all() -> multiple files: add pagination` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.*.all() -> multiple files: add pagination` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-020 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_geography_service -> OFFSET pagination:` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_geography_service -> OFFSET pagination:` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-021 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.finance.services.payments.payout_approval_read_service -> OFFSET pagination:` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.finance.services.payments.payout_approval_read_service -> OFFSET pagination:` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-022 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.governance.models.fraud -> domains.security.models.fraud: CreditCardBin, DLPViolation, DeviceFingerprint, FraudA` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.governance.models.fraud -> domains.security.models.fraud: CreditCardBin, DLPViolation, DeviceFingerprint, FraudA` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-023 | arch | NEW | CLUSTER-allowlist | backend/DOMAIN_ALLOWLIST.yaml:1 | allowlist entry without dated removal plan: `domains.governance.models.fraud -> domains.comms.models.fraud: MeetingRecording` | every allowlist entry carries a dated removal plan <=30 days (Law 7) | allowlist entry without dated removal plan: `domains.governance.models.fraud -> domains.comms.models.fraud: MeetingRecording` | Add the removal date or remove the entry | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-7 |
| ARCH-218 | arch | NEW | CLUSTER-router-business-logic | backend/modules/admin/routers/permissions.py:1 | router contains 12 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 12 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-220 | arch | NEW | CLUSTER-router-business-logic | backend/modules/admin/routers/staff.py:1 | router contains 16 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 16 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-221 | arch | NEW | CLUSTER-router-business-logic | backend/modules/customer/routers/accounts.py:1 | router contains 11 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 11 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-222 | arch | NEW | CLUSTER-router-business-logic | backend/modules/customer/routers/promotions.py:1 | router contains 17 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 17 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-224 | arch | NEW | CLUSTER-router-business-logic | backend/modules/employee/routers/comms.py:1 | router contains 22 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 22 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-225 | arch | NEW | CLUSTER-router-business-logic | backend/modules/employee/routers/finance.py:1 | router contains 31 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 31 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-226 | arch | NEW | CLUSTER-router-business-logic | backend/modules/employee/routers/hr.py:1 | router contains 7 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 7 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-228 | arch | NEW | — | backend/modules/employee/routers/hr/schemas.py:1 | file lives in routers/ but declares zero endpoint decorators | routers declare HTTP endpoints (anti-inference: verify content) | file lives in routers/ but declares zero endpoint decorators | Delete or convert to a service module | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-8,L-134 |
| ARCH-229 | arch | NEW | — | backend/modules/employee/routers/hr/schemas_admin.py:1 | file lives in routers/ but declares zero endpoint decorators | routers declare HTTP endpoints (anti-inference: verify content) | file lives in routers/ but declares zero endpoint decorators | Delete or convert to a service module | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-8,L-134 |
| ARCH-227 | arch | NEW | CLUSTER-router-business-logic | backend/modules/employee/routers/orders.py:1 | router contains 15 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 15 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-230 | arch | NEW | — | backend/modules/finance/routers/cash_management.py:1 | file lives in routers/ but declares zero endpoint decorators | routers declare HTTP endpoints (anti-inference: verify content) | file lives in routers/ but declares zero endpoint decorators | Delete or convert to a service module | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-8,L-134 |
| ARCH-231 | arch | NEW | CLUSTER-router-business-logic | backend/modules/logistics/routers/accounts.py:1 | router contains 10 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 10 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |
| ARCH-232 | arch | NEW | CLUSTER-router-business-logic | backend/modules/logistics/routers/logistics.py:1 | router contains 7 branch statements (business logic signal) | routers contain only auth/gate/parse/one service call (Law 90) | router contains 7 branch statements (business logic signal) | Extract branching logic into the domain service | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-90 |


### Over all

**Problem(s)**
1. `infra imports above`: imports `domains.accounts.models.user`
2. `infra imports above`: imports `domains.catalog.models.products`
3. `infra imports above`: imports `domains.country.models.countries`
4. `infra imports above`: imports `domains.country.models.country_enhancements`
5. `infra imports above`: imports `domains.finance.services.seeders.treasury_seeder`
6. `infra imports above`: imports `domains.logistics.models.erp`
7. `infra imports above`: imports `domains`
8. `infra imports above`: imports `middleware.country_context`
9. `infra imports above`: imports `providers.comms.email`
10. `infra imports above`: imports `providers.geography.geoip`
11. `infra imports above`: imports `providers.geography.ip`
12. `infra imports above`: imports `providers.image.bg_remover`
13. `infra imports above`: imports `providers.storage`
14. `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies`
15. `middleware imports above`: imports `providers.geography.ip`
16. `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context`
17. `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context`
18. `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount`
19. `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount`
20. `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager`
21. `module imports infrastructure`: imports `infrastructure.security.country_access.get_country_access_scope`
22. `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional`
23. `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
24. `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin`
25. `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
26. `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha`
27. `module imports infrastructure`: imports `infrastructure.storage.storage._store`
28. `module imports infrastructure`: imports `infrastructure.utils.auth.decode_token`
29. `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job`
30. `module imports infrastructure`: imports `infrastructure.utils.config.settings`

**Solution(s)**
1. Add the removal date or remove the entry
2. Break the cycle with a port/event boundary
3. Delete or convert to a service module
4. Demote media to canonical domain or document an ARCH change
5. Demote payments to canonical domain or document an ARCH change
6. Extract branching logic into the domain service
7. Move DB access into the domain service
8. Move finance routers under a canonical module or delete the package
9. Move the call behind the owning domain's ports/ or emit an event
10. Route through the sanctioned layer (events/ports/service call)

**Corrections required (prioritized)**

| Priority | Correction | Target | Blocking | Effort |
|---|---|---|---|---|
| P1 | Move finance routers under a canonical module or delete the package | backend/modules/finance:1 | yes | M |
| P1 | Demote media to canonical domain or document an ARCH change | backend/domains/media:1 | partial | M |
| P1 | Demote payments to canonical domain or document an ARCH change | backend/domains/payments:1 | partial | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/database/init_db.py:49 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/database/seed/_common.py:1078 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/geography/__init__.py:8 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/geography/__init__.py:9 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/messaging/email_service.py:28 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/messaging/realtime.py:495 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/ml/worker.py:52 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/storage/backup.py:300 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/storage/storage.py:27 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/category_tree.py:56 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/category_tree.py:76 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/country_detection_middleware.py:2 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/country_rls.py:26 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/country_rls.py:102 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/infrastructure/utils/import_service.py:14 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/middleware/dependencies/auth.py:19 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/middleware/dependencies/country_detection.py:34 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/accounts.py:50 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/accounts.py:50 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/catalog.py:36 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/comms.py:10 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/governance.py:12 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/logistics.py:10 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/logistics.py:12 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/logistics.py:13 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/logistics.py:13 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/promotions.py:32 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/promotions.py:33 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/promotions.py:33 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/staff.py:32 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/staff.py:32 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/admin/routers/staff.py:38 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/accounts.py:10 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/accounts.py:247 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/catalog.py:20 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/country.py:13 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/orders.py:13 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/customer/routers/reviews.py:30 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/attendance.py:8 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/finance.py:1207 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/finance.py:1207 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/hr.py:13 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/offices.py:8 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/orders.py:11 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/hr/attendance.py:9 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/hr/employees.py:9 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/hr/leaves.py:7 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/employee/routers/hr/offices.py:7 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:307 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:308 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:308 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:318 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:319 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:319 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:329 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:335 | no | M |
| P1 | Route through the sanctioned layer (events/ports/service call) | backend/modules/finance/routers/cash_management.py:336 | no | M |

---
## Dimension 02 · Technological

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 03 · Logical

### Summary
- Confirmation: ❌ FAIL
- Files with findings: 236
- Findings: 329
- P0: 44  P1: 149  P2: 75  P3: 61
- Clusters: 6
- Laws implicated: L-19, L-59, L-62, L-64, L-65, L-239
- Completion blockers: 44 yes · 149 partial · 136 no
- Observations: 0 (L0: 0)
- Status: NEW: 329 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Conf | Evidence | Truth | Claim | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker | Laws |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOGIC-120 | logic | NEW | CLUSTER-float-money | backend/domains/country/services/tax/country_tax_service.py:68 | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float \| None]]` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float \| None]]` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/tax/country_tax_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-320 | logic | NEW | CLUSTER-idempotency | backend/domains/customers/services/coins/zozi_coins_service.py:169 | idempotency_key: Optional[str] = None, | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | idempotency_key: Optional[str] = None, | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '169p' backend/domains/customers/services/coins/zozi_coins_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-321 | logic | NEW | CLUSTER-idempotency | backend/domains/customers/services/coins/zozi_coins_service.py:182 | idempotency_key: Optional unique key for deduplication. | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | idempotency_key: Optional unique key for deduplication. | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '182p' backend/domains/customers/services/coins/zozi_coins_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-127 | logic | NEW | CLUSTER-float-money | backend/domains/finance/schemas/finance_schemas.py:11 | 4 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/schemas/finance_schemas.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-128 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/commission_read_service.py:70 | 1 float-for-money signal(s); first: `"rate": float(rule.rate),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"rate": float(rule.rate),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/commission_read_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-129 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/country/supplier_finance_service.py:160 | 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),` | monetary values use Decimal/Numeric only (Law 19) | 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/country/supplier_finance_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-130 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/data_import_service.py:124 | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/data_import_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-131 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/finance_service.py:66 | 2 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/finance_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-132 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/ledger/accounting_controller.py:24 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/accounting_controller.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-133 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/ledger/general_ledger.py:5836 | 90 float-for-money signal(s); first: `VAT_RATES: dict[str, float]` | monetary values use Decimal/Numeric only (Law 19) | 90 float-for-money signal(s); first: `VAT_RATES: dict[str, float]` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/general_ledger.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-134 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/gateway_paypal.py:189 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_paypal.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-135 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/gateway_stripe.py:167 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_stripe.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-136 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/gateway_tap.py:131 | 7 float-for-money signal(s); first: `"amount": float(converted_total),` | monetary values use Decimal/Numeric only (Law 19) | 7 float-for-money signal(s); first: `"amount": float(converted_total),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_tap.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-322 | logic | NEW | CLUSTER-idempotency | backend/domains/finance/services/payments/payment_engine.py:371 | idempotency_key: Optional[str] = None | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | idempotency_key: Optional[str] = None | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '371p' backend/domains/finance/services/payments/payment_engine.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-137 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_engine.py:4704 | 3 float-for-money signal(s); first: `"amount": float(p.amount),` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `"amount": float(p.amount),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-138 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_orchestrator.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-139 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | 36 float-for-money signal(s); first: `amount: Decimal \| float` | monetary values use Decimal/Numeric only (Law 19) | 36 float-for-money signal(s); first: `amount: Decimal \| float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payouts/payout_batch_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-140 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/trading_service.py:134 | 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/trading_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-141 | logic | NEW | CLUSTER-float-money | backend/domains/finance/services/treasury/cash_management_service.py:269 | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/treasury/cash_management_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-177 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/cart/cart_service__orders.py:166 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/cart_service__orders.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-178 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/cart/service.py:50 | 10 float-for-money signal(s); first: `subtotal: float` | monetary values use Decimal/Numeric only (Law 19) | 10 float-for-money signal(s); first: `subtotal: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-179 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/core/logistics.py:1892 | 39 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)` | monetary values use Decimal/Numeric only (Law 19) | 39 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/logistics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-180 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/core/misc.py:201 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/misc.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-181 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/core/order_engine.py:906 | 4 float-for-money signal(s); first: `total=float(total_amount),` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `total=float(total_amount),` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/order_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-182 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/orders_service.py:213 | 4 float-for-money signal(s); first: `min_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `min_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/orders_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-183 | logic | NEW | CLUSTER-float-money | backend/domains/orders/services/tracking/service.py:348 | 1 float-for-money signal(s); first: `total = round(after_discount + shipping + vat, 2)` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `total = round(after_discount + shipping + vat, 2)` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/tracking/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-323 | logic | NEW | CLUSTER-idempotency | backend/domains/promotions/services/coupons/coupon_service.py:538 | idempotency_key: Optional[str] = None, | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | idempotency_key: Optional[str] = None, | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '538p' backend/domains/promotions/services/coupons/coupon_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-324 | logic | NEW | CLUSTER-idempotency | backend/domains/promotions/services/coupons/coupon_service.py:554 | idempotency_key: Optional unique key for deduplication (24h TTL). | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | idempotency_key: Optional unique key for deduplication (24h TTL). | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '554p' backend/domains/promotions/services/coupons/coupon_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-325 | logic | NEW | CLUSTER-idempotency | backend/domains/security/services/detection/public_security_detection_service.py:25 | def _idempotency_key(idempotency_key: Optional[str] = Header(None, alias=_IDEMPOTENCY_KEY_HEADER)) -> Optional[str]: | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | def _idempotency_key(idempotency_key: Optional[str] = Header(None, alias=_IDEMPOTENCY_KEY_HEADER)) -> Optional[str]: | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '25p' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-326 | logic | NEW | CLUSTER-idempotency | backend/domains/security/services/detection/public_security_detection_service.py:83 | def remove_from_blacklist(entry_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | def remove_from_blacklist(entry_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '83p' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-327 | logic | NEW | CLUSTER-idempotency | backend/domains/security/services/detection/public_security_detection_service.py:104 | def create_rule(payload: FraudRuleCreate, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | def create_rule(payload: FraudRuleCreate, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '104p' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-328 | logic | NEW | CLUSTER-idempotency | backend/domains/security/services/detection/public_security_detection_service.py:127 | def assign_review(review_id: int, assignee_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | def assign_review(review_id: int, assignee_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '127p' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-329 | logic | NEW | CLUSTER-idempotency | backend/domains/security/services/detection/public_security_detection_service.py:144 | def resolve_review(review_id: int, payload: ManualReviewResolve, current_user: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_idempotency_key)): | idempotency keys are REQUIRED on payment/order/refund/webhook paths (Law 239) | def resolve_review(review_id: int, payload: ManualReviewResolve, current_user: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key: Optional[str] = Depends(_i | Make the idempotency key required and enforce uniqueness | M | P0 | 4 | multiple | L0 | VERIFIED | — | sed -n '144p' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | yes | L-239 |
| LOGIC-203 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/orders/supplier_orders.py:337 | 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-204 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/orders/supplier_orders_service.py:80 | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))` | monetary values use Decimal/Numeric only (Law 19) | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-209 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/profile/supplier_payouts_service.py:73 | 5 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/profile/supplier_payouts_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-225 | logic | NEW | CLUSTER-float-money | backend/modules/customer/routers/orders.py:124 | 2 float-for-money signal(s); first: `price: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/orders.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-230 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/finance.py:466 | 6 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 6 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/finance.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-233 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/orders.py:53 | 5 float-for-money signal(s); first: `unit_price: float` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `unit_price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/orders.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-238 | logic | NEW | CLUSTER-float-money | backend/modules/supplier/routers/finance.py:45 | 3 float-for-money signal(s); first: `min_payout_amount: float` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `min_payout_amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/finance.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-242 | logic | NEW | CLUSTER-float-money | backend/providers/ai/finance_ai.py:87 | 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/finance_ai.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-252 | logic | NEW | CLUSTER-float-money | backend/providers/payments/base.py:99 | 2 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-253 | logic | NEW | CLUSTER-float-money | backend/providers/payments/base_models.py:31 | 2 float-for-money signal(s); first: `amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base_models.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-254 | logic | NEW | CLUSTER-float-money | backend/providers/payments/webhook_models.py:42 | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P0 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/payments/webhook_models.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | yes | L-19 |
| LOGIC-052 | logic | NEW | CLUSTER-silent-except | backend/domains/accounts/services/auth/public_security_registration_service.py:69 | 1 silent except block(s); first at line 69: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 69: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/accounts/services/auth/public_security_registration_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-100 | logic | NEW | CLUSTER-float-money | backend/domains/accounts/services/permissions/permission_service.py:693 | 1 float-for-money signal(s); first: `amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/accounts/services/permissions/permission_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-101 | logic | NEW | CLUSTER-float-money | backend/domains/analytics/services/dashboards/admin_analytics_service.py:37 | 1 float-for-money signal(s); first: `"total_revenue": round(total_revenue, 2),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"total_revenue": round(total_revenue, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/analytics/services/dashboards/admin_analytics_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-102 | logic | NEW | CLUSTER-float-money | backend/domains/analytics/services/dashboards/analytics_service.py:282 | 1 float-for-money signal(s); first: `"click_through_rate": round((clicked_session_count / query_count) * 100, 1) if query_count else 0.0,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"click_through_rate": round((clicked_session_count / query_count) * 100, 1) if query_count else 0.0,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/analytics/services/dashboards/analytics_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-103 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/categories/bulk_category_service.py:238 | 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/bulk_category_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-104 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/categories/categories_service.py:86 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/categories_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-105 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/categories/category_service.py:186 | 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/categories/category_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-106 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/commission_service.py:285 | 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/commission_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-107 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/products/product_discount_service.py:65 | 1 float-for-money signal(s); first: `discount_value: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `discount_value: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/products/product_discount_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-108 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/products/products_service.py:216 | 13 float-for-money signal(s); first: `min_price: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 13 float-for-money signal(s); first: `min_price: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/products/products_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-109 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/search/ai_search_service.py:78 | 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/search/ai_search_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-110 | logic | NEW | CLUSTER-float-money | backend/domains/catalog/services/search/search_service.py:24 | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float \| None, float \| None]]` | monetary values use Decimal/Numeric only (Law 19) | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float \| None, float \| None]]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/catalog/services/search/search_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-111 | logic | NEW | CLUSTER-float-money | backend/domains/comms/services/email/email_management.py:341 | 2 float-for-money signal(s); first: `open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/email/email_management.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-112 | logic | NEW | CLUSTER-float-money | backend/domains/comms/services/email/transactional.py:441 | 2 float-for-money signal(s); first: `total_amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `total_amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/email/transactional.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-113 | logic | NEW | CLUSTER-float-money | backend/domains/comms/services/messaging/chat_service.py:717 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/messaging/chat_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-114 | logic | NEW | CLUSTER-float-money | backend/domains/comms/services/shared/utility/shared_utils.py:399 | 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/comms/services/shared/utility/shared_utils.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-115 | logic | NEW | CLUSTER-float-money | backend/domains/country/ports.py:124 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/ports.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-116 | logic | NEW | CLUSTER-float-money | backend/domains/country/services/core/country_config_admin_service.py:286 | 11 float-for-money signal(s); first: `tax_reduced_rates: Optional[dict[str, float]]` | monetary values use Decimal/Numeric only (Law 19) | 11 float-for-money signal(s); first: `tax_reduced_rates: Optional[dict[str, float]]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/core/country_config_admin_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-117 | logic | NEW | CLUSTER-float-money | backend/domains/country/services/localization/localization_service.py:155 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/localization/localization_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-118 | logic | NEW | CLUSTER-float-money | backend/domains/country/services/research/country_auto_populate.py:617 | 3 float-for-money signal(s); first: `return float(data.get("standard_rate", 0))` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `return float(data.get("standard_rate", 0))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/research/country_auto_populate.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-119 | logic | NEW | CLUSTER-float-money | backend/domains/country/services/research/country_heuristic_engine.py:290 | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/research/country_heuristic_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-121 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/cart_service.py:149 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/cart_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-122 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/coins/zozi_coins_service.py:274 | 1 float-for-money signal(s); first: `"balance": float(balance),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"balance": float(balance),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/coins/zozi_coins_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-123 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/customer_health_engine.py:67 | 2 float-for-money signal(s); first: `"cod_failure_rate": round(cod_failure_rate * 100, 2),` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"cod_failure_rate": round(cod_failure_rate * 100, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/customer_health_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-124 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/profile_service.py:105 | 1 float-for-money signal(s); first: `percent = int(round((filled / total) * 100))` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `percent = int(round((filled / total) * 100))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/profile_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-125 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/recommendations/recommendation_service.py:250 | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/recommendations/recommendation_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-126 | logic | NEW | CLUSTER-float-money | backend/domains/customers/services/search_service.py:51 | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float \| None, float \| None]]` | monetary values use Decimal/Numeric only (Law 19) | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float \| None, float \| None]]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/customers/services/search_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-062 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/data_import_service.py:75 | 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/data_import_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-063 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/finance_ai_service.py:87 | 1 silent except block(s); first at line 87: pass-only: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 87: pass-only: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/finance_ai_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-006 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/ledger/general_ledger.py:3774 | 5 silent except block(s); first at line 3774: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 5 silent except block(s); first at line 3774: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/ledger/general_ledger.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-025 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/payments/gateway_tap.py:1111 | 2 silent except block(s); first at line 1111: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 1111: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/payments/gateway_tap.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-064 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/payments/payment_engine.py:3411 | 1 silent except block(s); first at line 3411: truly-silent: except HTTPException as exc: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 3411: truly-silent: except HTTPException as exc: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/payments/payment_engine.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-026 | logic | NEW | CLUSTER-silent-except | backend/domains/finance/services/payments/payment_orchestrator.py:693 | 2 silent except block(s); first at line 693: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 693: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/finance/services/payments/payment_orchestrator.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-142 | logic | NEW | CLUSTER-float-money | backend/domains/governance/read_models/governance_read_models.py:96 | 2 float-for-money signal(s); first: `amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/read_models/governance_read_models.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-143 | logic | NEW | CLUSTER-float-money | backend/domains/governance/schemas/governance_schemas.py:177 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/schemas/governance_schemas.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-144 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/admin/admin_service.py:118 | 2 float-for-money signal(s); first: `open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/admin/admin_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-145 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/approval/approval_matrix_service.py:30 | 3 float-for-money signal(s); first: `amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/approval/approval_matrix_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-146 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/command_center/command_center_service.py:144 | 10 float-for-money signal(s); first: `commission_reserve: float` | monetary values use Decimal/Numeric only (Law 19) | 10 float-for-money signal(s); first: `commission_reserve: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/command_center/command_center_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-147 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/command_center/service.py:344 | 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/command_center/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-148 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/products_service.py:38 | 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/products_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-149 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/settings/admin_service.py:41 | 2 float-for-money signal(s); first: `open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `open_rate = round(total_opened / total_sent * 100, 1) if total_sent else 0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/settings/admin_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-150 | logic | NEW | CLUSTER-float-money | backend/domains/governance/services/settings/governance_package_service.py:38 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/governance/services/settings/governance_package_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-151 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/employees/employee_service.py:152 | 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/employees/employee_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-152 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/hr_employee_service.py:539 | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/hr_employee_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-153 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/learning/lms_service.py:148 | 1 float-for-money signal(s); first: `"completion_rate": round((progress[1] or 0) / (progress[0] or 1) * 100, 2),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"completion_rate": round((progress[1] or 0) / (progress[0] or 1) * 100, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/learning/lms_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-154 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/payroll/payroll_engine.py:377 | 9 float-for-money signal(s); first: `"base_salary": float(base_salary),` | monetary values use Decimal/Numeric only (Law 19) | 9 float-for-money signal(s); first: `"base_salary": float(base_salary),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/payroll/payroll_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-155 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/payroll/payroll_service.py:265 | 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/payroll/payroll_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-156 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/performance/dei_auditor.py:69 | 1 float-for-money signal(s); first: `"salary": float(emp.salary),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"salary": float(emp.salary),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/performance/dei_auditor.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-157 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/performance/okr.py:190 | 1 float-for-money signal(s); first: `progress_pct = round((weighted_progress / total_weight) * 100, 1)` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `progress_pct = round((weighted_progress / total_weight) * 100, 1)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/performance/okr.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-158 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/shift/shift_roster_service.py:164 | 1 float-for-money signal(s); first: `"total_days": float(l.total_days),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"total_days": float(l.total_days),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/shift/shift_roster_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-159 | logic | NEW | CLUSTER-float-money | backend/domains/hr/services/travel/travel_service.py:152 | 2 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/hr/services/travel/travel_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-160 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:40 | 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders, 'active_sessions': 0, 'pending_payouts': db.query(PayoutModel).filter(PayoutModel.status == 'pe` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders, 'active_sessions': 0, 'pending_payouts | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_fallback_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-161 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/core/admin_logistics_imports_service.py:55 | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_imports_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-162 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/core/admin_logistics_operations_service.py:18 | 3 float-for-money signal(s); first: `return float(payout.amount)` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `return float(payout.amount)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/admin_logistics_operations_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-163 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/core/logistics_engine.py:93 | 5 float-for-money signal(s); first: `"base_rate": float(base_rate),` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `"base_rate": float(base_rate),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/logistics_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-164 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/core/service.py:1057 | 45 float-for-money signal(s); first: `duty_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 45 float-for-money signal(s); first: `duty_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/core/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-165 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py:33 | 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-166 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/geo/map_service.py:97 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/map_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-167 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/geo/routing_service.py:68 | 2 float-for-money signal(s); first: `"estimated_distance_km": round(total_distance, 1),` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"estimated_distance_km": round(total_distance, 1),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/routing_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-168 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/geo/service.py:452 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/geo/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-169 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/health/service.py:63 | 8 float-for-money signal(s); first: `"acceptance_rate": round(acceptance_rate * 100, 2),` | monetary values use Decimal/Numeric only (Law 19) | 8 float-for-money signal(s); first: `"acceptance_rate": round(acceptance_rate * 100, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/health/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-170 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/admin_logistics_operations_service.py:221 | 9 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 9 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/admin_logistics_operations_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-171 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/logistics_partner_service.py:232 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/logistics_partner_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-172 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/logistics_pricing_service.py:62 | 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/logistics_pricing_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-173 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/pricing_service.py:209 | 10 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),` | monetary values use Decimal/Numeric only (Law 19) | 10 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/pricing_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-174 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/service.py:229 | 74 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 74 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-175 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/partners/settlement_service.py:136 | 3 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/partners/settlement_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-176 | logic | NEW | CLUSTER-float-money | backend/domains/logistics/services/shipping/service.py:337 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/logistics/services/shipping/service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-184 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/events.py:16 | 1 float-for-money signal(s); first: `discount_amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `discount_amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/events.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-185 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/admin_promotion_ops_service.py:62 | 8 float-for-money signal(s); first: `discount_value: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 8 float-for-money signal(s); first: `discount_value: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/admin_promotion_ops_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-186 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/admin_promotion_service.py:95 | 4 float-for-money signal(s); first: `discount_value: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `discount_value: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/admin_promotion_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-187 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/coins/coin_service.py:129 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coins/coin_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-188 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/coins/promotion_points_service.py:128 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coins/promotion_points_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-189 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/coupons/customer_coupons_create_service.py:29 | 6 float-for-money signal(s); first: `order_total: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 6 float-for-money signal(s); first: `order_total: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/coupons/customer_coupons_create_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-190 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:47 | 4 float-for-money signal(s); first: `discount_value: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `discount_value: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/admin_commerce_configuration_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-191 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/engine/admin_promotions_write_service.py:55 | 4 float-for-money signal(s); first: `discount_value: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `discount_value: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/admin_promotions_write_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-192 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/engine/promotion_service.py:49 | 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount", 0) or 0),` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount", 0) or 0),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/engine/promotion_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-193 | logic | NEW | CLUSTER-float-money | backend/domains/promotions/services/promotion_admin_write_service.py:77 | 4 float-for-money signal(s); first: `discount_value: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `discount_value: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/promotions/services/promotion_admin_write_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-075 | logic | NEW | CLUSTER-silent-except | backend/domains/security/services/core/kms_encryption.py:78 | 1 silent except block(s); first at line 78: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 78: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/security/services/core/kms_encryption.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-194 | logic | NEW | CLUSTER-float-money | backend/domains/security/services/detection/confidence_scoring.py:106 | 2 float-for-money signal(s); first: `percentage = round((score / total_checks) * 100, 1)` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `percentage = round((score / total_checks) * 100, 1)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/security/services/detection/confidence_scoring.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-076 | logic | NEW | CLUSTER-silent-except | backend/domains/security/services/detection/public_security_detection_service.py:44 | 1 silent except block(s); first at line 44: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 44: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/security/services/detection/public_security_detection_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-005 | logic | NEW | CLUSTER-silent-except | backend/domains/security/services/fraud/fraud_detection_service.py:102 | 6 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 6 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/security/services/fraud/fraud_detection_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-195 | logic | NEW | CLUSTER-float-money | backend/domains/security/services/fraud/fraud_detection_service.py:485 | 4 float-for-money signal(s); first: `amount: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `amount: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/security/services/fraud/fraud_detection_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-074 | logic | NEW | CLUSTER-silent-except | backend/domains/security/services/security_provider_helpers.py:30 | 1 silent except block(s); first at line 30: pass-only: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 30: pass-only: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/security/services/security_provider_helpers.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-196 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/events.py:113 | 2 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/events.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-197 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:56 | 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/analytics/supplier_analytics_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-198 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/badges/badge_service.py:386 | 1 float-for-money signal(s); first: `total = float(weight.scalar() or 0.0)` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `total = float(weight.scalar() or 0.0)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/badges/badge_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-199 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/contract/contract_service.py:52 | 2 float-for-money signal(s); first: `"commission_rate": float(default_commission),` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"commission_rate": float(default_commission),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/contract/contract_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-200 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/health/supplier_health.py:363 | 19 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | monetary values use Decimal/Numeric only (Law 19) | 19 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/health/supplier_health.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-001 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/health/supplier_health.py:1430 | 9 silent except block(s); first at line 1430: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 9 silent except block(s); first at line 1430: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/health/supplier_health.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-201 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/health/supplier_health_engine.py:151 | 6 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)` | monetary values use Decimal/Numeric only (Law 19) | 6 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/health/supplier_health_engine.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-202 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py:97 | 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-018 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/orders/supplier_orders_service.py:518 | 3 silent except block(s); first at line 518: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 518: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-032 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/orders/supplier_orders_verify_service.py:139 | 2 silent except block(s); first at line 139: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 139: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_verify_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-205 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/products/supplier_product_service.py:47 | 9 float-for-money signal(s); first: `price: float` | monetary values use Decimal/Numeric only (Law 19) | 9 float-for-money signal(s); first: `price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_product_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-077 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/products/supplier_product_service.py:237 | 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/products/supplier_product_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-206 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/products/supplier_products.py:206 | 5 float-for-money signal(s); first: `price: float` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_products.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-009 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/products/supplier_products.py:280 | 5 silent except block(s); first at line 280: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 5 silent except block(s); first at line 280: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/products/supplier_products.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-207 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/products/supplier_products_service.py:120 | 7 float-for-money signal(s); first: `"price": float(product.price),` | monetary values use Decimal/Numeric only (Law 19) | 7 float-for-money signal(s); first: `"price": float(product.price),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_products_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-078 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/products/supplier_products_service.py:203 | 1 silent except block(s); first at line 203: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 203: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/products/supplier_products_service.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-208 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:119 | 3 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/products/supplier_supplier_upload_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-210 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/profile/supplier_profile.py:55 | 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/profile/supplier_profile.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-211 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/quality/quality_control_service.py:98 | 1 float-for-money signal(s); first: `"return_rate": round(return_rate, 2),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"return_rate": round(return_rate, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/quality/quality_control_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-212 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/settlement/multi_currency_settlement.py:90 | 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/settlement/multi_currency_settlement.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-213 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/supplier_shared.py:200 | 4 float-for-money signal(s); first: `price: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/supplier_shared.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-010 | logic | NEW | CLUSTER-silent-except | backend/domains/suppliers/services/supplier_shared.py:437 | 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError): | all except blocks log at minimum DEBUG (Law 59) | 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/suppliers/services/supplier_shared.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-214 | logic | NEW | CLUSTER-float-money | backend/domains/suppliers/services/tier/tier_service.py:102 | 1 float-for-money signal(s); first: `"fulfillment_rate": round(fulfillment_rate, 2),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"fulfillment_rate": round(fulfillment_rate, 2),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/tier/tier_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-215 | logic | NEW | CLUSTER-float-money | backend/infrastructure/database/schemas.py:394 | 63 float-for-money signal(s); first: `price: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 63 float-for-money signal(s); first: `price: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/infrastructure/database/schemas.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-216 | logic | NEW | CLUSTER-float-money | backend/infrastructure/database/seed/logistics.py:18 | 1 float-for-money signal(s); first: `total_weight_kg: Decimal \| float \| int \| None` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `total_weight_kg: Decimal \| float \| int \| None` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/infrastructure/database/seed/logistics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-217 | logic | NEW | CLUSTER-float-money | backend/infrastructure/messaging/downstream_wiring.py:128 | 4 float-for-money signal(s); first: `net_amount = float(subtotal_decimal)` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `net_amount = float(subtotal_decimal)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/infrastructure/messaging/downstream_wiring.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-020 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/security/dependencies.py:49 | 3 silent except block(s); first at line 49: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 49: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/security/dependencies.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-084 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/security/kms_integration.py:26 | 1 silent except block(s); first at line 26: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 26: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/security/kms_integration.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-218 | logic | NEW | CLUSTER-float-money | backend/infrastructure/utils/analytics.py:69 | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/infrastructure/utils/analytics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-219 | logic | NEW | CLUSTER-float-money | backend/infrastructure/utils/currency_service.py:271 | 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/infrastructure/utils/currency_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-220 | logic | NEW | CLUSTER-float-money | backend/modules/admin/routers/hr.py:32 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/hr.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-221 | logic | NEW | CLUSTER-float-money | backend/modules/admin/routers/promotions.py:165 | 4 float-for-money signal(s); first: `discount_pct=float(payload.get("discount_pct", 0)),` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `discount_pct=float(payload.get("discount_pct", 0)),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/promotions.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-222 | logic | NEW | CLUSTER-float-money | backend/modules/admin/routers/security.py:97 | 1 float-for-money signal(s); first: `amount: float \| None` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float \| None` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/admin/routers/security.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-223 | logic | NEW | CLUSTER-float-money | backend/modules/customer/routers/catalog.py:35 | 4 float-for-money signal(s); first: `min_price: float \| None` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `min_price: float \| None` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/catalog.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-224 | logic | NEW | CLUSTER-float-money | backend/modules/customer/routers/comms.py:25 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/comms.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-226 | logic | NEW | CLUSTER-float-money | backend/modules/customer/routers/promotions.py:148 | 6 float-for-money signal(s); first: `order_total: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 6 float-for-money signal(s); first: `order_total: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/promotions.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-227 | logic | NEW | CLUSTER-float-money | backend/modules/customer/serializers/customer_serializers.py:19 | 3 float-for-money signal(s); first: `total: float` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `total: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/customer/serializers/customer_serializers.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-228 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/catalog.py:31 | 2 float-for-money signal(s); first: `min_price: float \| None` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `min_price: float \| None` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/catalog.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-229 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/country.py:49 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/country.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-231 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/hr.py:122 | 2 float-for-money signal(s); first: `salary: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `salary: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/hr.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-232 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/hr/schemas.py:37 | 2 float-for-money signal(s); first: `salary: Optional[float]` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `salary: Optional[float]` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/hr/schemas.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-234 | logic | NEW | CLUSTER-float-money | backend/modules/employee/routers/suppliers.py:53 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/suppliers.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-235 | logic | NEW | CLUSTER-float-money | backend/modules/employee/serializers/employee_serializers.py:37 | 2 float-for-money signal(s); first: `gross_amount: float` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `gross_amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/employee/serializers/employee_serializers.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-236 | logic | NEW | CLUSTER-float-money | backend/modules/logistics/routers/logistics.py:1014 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/logistics/routers/logistics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-237 | logic | NEW | CLUSTER-float-money | backend/modules/supplier/routers/analytics.py:34 | 1 float-for-money signal(s); first: `total_revenue: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `total_revenue: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/analytics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-239 | logic | NEW | CLUSTER-float-money | backend/modules/supplier/routers/logistics.py:32 | 4 float-for-money signal(s); first: `base_price: float` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `base_price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/logistics.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-240 | logic | NEW | CLUSTER-float-money | backend/modules/supplier/serializers/supplier_serializers.py:19 | 3 float-for-money signal(s); first: `total: float` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `total: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/serializers/supplier_serializers.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-241 | logic | NEW | CLUSTER-float-money | backend/providers/ai/ai_variant_config.py:111 | 2 float-for-money signal(s); first: `"price_min": round(base * 0.75, 3),` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"price_min": round(base * 0.75, 3),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/ai_variant_config.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-086 | logic | NEW | CLUSTER-silent-except | backend/providers/ai/finance_ai.py:88 | 1 silent except block(s); first at line 88: pass-only: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 88: pass-only: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/ai/finance_ai.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-243 | logic | NEW | CLUSTER-float-money | backend/providers/ai/price_intelligence.py:80 | 8 float-for-money signal(s); first: `current_price: float` | monetary values use Decimal/Numeric only (Law 19) | 8 float-for-money signal(s); first: `current_price: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/price_intelligence.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-244 | logic | NEW | CLUSTER-float-money | backend/providers/ai/recommendation.py:273 | 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/recommendation.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-245 | logic | NEW | CLUSTER-float-money | backend/providers/ai/search.py:120 | 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/search.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-246 | logic | NEW | CLUSTER-float-money | backend/providers/ai/sentiment.py:215 | 4 float-for-money signal(s); first: `confidence = round(min(abs(score), 1.0), 4) if total > 0 else 0.0` | monetary values use Decimal/Numeric only (Law 19) | 4 float-for-money signal(s); first: `confidence = round(min(abs(score), 1.0), 4) if total > 0 else 0.0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ai/sentiment.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-247 | logic | NEW | CLUSTER-float-money | backend/providers/bg_removal/bg_removal_service.py:678 | 5 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0` | monetary values use Decimal/Numeric only (Law 19) | 5 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/bg_removal/bg_removal_service.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-088 | logic | NEW | CLUSTER-silent-except | backend/providers/finance/bank_api.py:115 | 1 silent except block(s); first at line 115: truly-silent: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 115: truly-silent: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/finance/bank_api.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-248 | logic | NEW | CLUSTER-float-money | backend/providers/geography/rates.py:177 | 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expires_at"])` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expires_at"])` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/geography/rates.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-249 | logic | NEW | CLUSTER-float-money | backend/providers/image/free_image_tools.py:811 | 1 float-for-money signal(s); first: `white_balance_strength: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `white_balance_strength: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/image/free_image_tools.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-250 | logic | NEW | CLUSTER-float-money | backend/providers/image/ocr.py:236 | 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))` | monetary values use Decimal/Numeric only (Law 19) | 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/image/ocr.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-251 | logic | NEW | CLUSTER-float-money | backend/providers/ocr/ocr_parser.py:178 | 2 float-for-money signal(s); first: `"amount": float(amt),` | monetary values use Decimal/Numeric only (Law 19) | 2 float-for-money signal(s); first: `"amount": float(amt),` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/ocr/ocr_parser.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-046 | logic | NEW | CLUSTER-silent-except | backend/providers/payments/generic.py:25 | 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/payments/generic.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-047 | logic | NEW | CLUSTER-silent-except | backend/providers/payments/paypal.py:135 | 2 silent except block(s); first at line 135: truly-silent: except (TypeError, ValueError): | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 135: truly-silent: except (TypeError, ValueError): | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/payments/paypal.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-255 | logic | NEW | CLUSTER-float-money | backend/providers/qr/qr_generator.py:103 | 1 float-for-money signal(s); first: `amount: float` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `amount: float` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/qr/qr_generator.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-098 | logic | NEW | CLUSTER-silent-except | backend/providers/security/watchlist.py:73 | 1 silent except block(s); first at line 73: truly-silent: except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 73: truly-silent: except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc: | Add logger.warning(..., exc_info=True) or re-raise | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/security/watchlist.py | — | git revert <commit> | — | — | — | partial | L-59 |
| LOGIC-256 | logic | NEW | CLUSTER-float-money | backend/providers/shipping/shipping_calculator.py:416 | 9 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))` | monetary values use Decimal/Numeric only (Law 19) | 9 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/shipping/shipping_calculator.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-257 | logic | NEW | CLUSTER-float-money | backend/providers/voice/voice_to_text.py:167 | 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)` | monetary values use Decimal/Numeric only (Law 19) | 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)` | Convert to Decimal and use kernel.money rounding helpers | M | P1 | 4 | multiple | L0 | VERIFIED | — | grep -nE 'float\(\|Float\|: float' backend/providers/voice/voice_to_text.py \| head -20 | — | git revert <commit> | money calculations, payouts, tax, commissions | — | — | partial | L-19 |
| LOGIC-049 | logic | NEW | CLUSTER-silent-except | backend/config.py:895 | 1 silent except block(s); first at line 895: truly-silent: except AttributeError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 895: truly-silent: except AttributeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/config.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-319 | logic | NEW | CLUSTER-todo-hygiene | backend/domains/accounts/models/core.py:58 | 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts/models/core.py:58; backend/domains/accounts/models/core.py:84; backend/domains/accounts/models/core.py:103; backend/domains/accounts/models/core.py:106; backend/domains/accounts/models/onboarding.py:19) | TODO/FIXME carry a ticket reference and expiration date (Law 62) | 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts/models/core.py:58; backend/domains/accounts/models/core.py:84; backend/domains/accounts/mo | Link each TODO to a ticket or delete it | M | P2 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-62 |
| LOGIC-003 | logic | NEW | CLUSTER-silent-except | backend/domains/accounts/services/auth/auth_service.py:3044 | 6 silent except block(s); first at line 3044: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 6 silent except block(s); first at line 3044: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/accounts/services/auth/auth_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-013 | logic | NEW | CLUSTER-silent-except | backend/domains/catalog/services/commission_service.py:54 | 3 silent except block(s); first at line 54: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 54: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/catalog/services/commission_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-014 | logic | NEW | CLUSTER-silent-except | backend/domains/catalog/services/products/products_service.py:126 | 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/catalog/services/products/products_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-053 | logic | NEW | CLUSTER-silent-except | backend/domains/catalog/services/search/search_service.py:212 | 1 silent except block(s); first at line 212: pass-only: except (TypeError, ValueError, json.JSONDecodeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 212: pass-only: except (TypeError, ValueError, json.JSONDecodeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/catalog/services/search/search_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-055 | logic | NEW | CLUSTER-silent-except | backend/domains/comms/services/email/email_management.py:454 | 1 silent except block(s); first at line 454: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 454: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/comms/services/email/email_management.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-056 | logic | NEW | CLUSTER-silent-except | backend/domains/comms/services/messaging/websocket_handlers.py:281 | 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/comms/services/messaging/websocket_handlers.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-054 | logic | NEW | CLUSTER-silent-except | backend/domains/comms/services/notification_gateway.py:166 | 1 silent except block(s); first at line 166: truly-silent: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 166: truly-silent: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/comms/services/notification_gateway.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-015 | logic | NEW | CLUSTER-silent-except | backend/domains/comms/services/public_comms_status_service.py:283 | 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/comms/services/public_comms_status_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-023 | logic | NEW | CLUSTER-silent-except | backend/domains/comms/services/system_comms_status_service.py:84 | 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/comms/services/system_comms_status_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-057 | logic | NEW | CLUSTER-silent-except | backend/domains/country/services/core/country_config_version_service.py:218 | 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/country/services/core/country_config_version_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-058 | logic | NEW | CLUSTER-silent-except | backend/domains/country/services/core/country_service.py:191 | 1 silent except block(s); first at line 191: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 191: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/country/services/core/country_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-059 | logic | NEW | CLUSTER-silent-except | backend/domains/country/services/cross_border/cross_border_service.py:70 | 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/country/services/cross_border/cross_border_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-060 | logic | NEW | CLUSTER-silent-except | backend/domains/country/services/research/country_ai_research.py:480 | 1 silent except block(s); first at line 480: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 480: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/country/services/research/country_ai_research.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-024 | logic | NEW | CLUSTER-silent-except | backend/domains/customers/services/coins/zozi_coins_service.py:130 | 2 silent except block(s); first at line 130: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 130: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/customers/services/coins/zozi_coins_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-016 | logic | NEW | CLUSTER-silent-except | backend/domains/customers/services/public_comms_status_service.py:276 | 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/customers/services/public_comms_status_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-061 | logic | NEW | CLUSTER-silent-except | backend/domains/customers/services/search_service.py:232 | 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/customers/services/search_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-027 | logic | NEW | CLUSTER-silent-except | backend/domains/governance/services/command_center/command_center_service.py:307 | 2 silent except block(s); first at line 307: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 307: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/governance/services/command_center/command_center_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-065 | logic | NEW | CLUSTER-silent-except | backend/domains/governance/services/command_center/service.py:43 | 1 silent except block(s); first at line 43: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 43: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/governance/services/command_center/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-028 | logic | NEW | CLUSTER-silent-except | backend/domains/hr/services/payroll/payroll_service.py:97 | 2 silent except block(s); first at line 97: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 97: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/hr/services/payroll/payroll_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-066 | logic | NEW | CLUSTER-silent-except | backend/domains/hr/services/performance/okr.py:120 | 1 silent except block(s); first at line 120: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 120: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/hr/services/performance/okr.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-067 | logic | NEW | CLUSTER-silent-except | backend/domains/hr/services/performance/reviews.py:85 | 1 silent except block(s); first at line 85: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 85: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/hr/services/performance/reviews.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-068 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/core/logistics_engine.py:126 | 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/core/logistics_engine.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-004 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/core/service.py:1439 | 6 silent except block(s); first at line 1439: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 6 silent except block(s); first at line 1439: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/core/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-069 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/core/zone_service.py:28 | 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/core/zone_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-029 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/partners/admin_logistics_operations_service.py:355 | 2 silent except block(s); first at line 355: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 355: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/partners/admin_logistics_operations_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-070 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/partners/contract_service.py:168 | 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/partners/contract_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-017 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/partners/partner_service.py:73 | 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/partners/partner_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-030 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/partners/service.py:508 | 2 silent except block(s); first at line 508: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 508: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/partners/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-031 | logic | NEW | CLUSTER-silent-except | backend/domains/logistics/services/sla/service.py:55 | 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/logistics/services/sla/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-007 | logic | NEW | CLUSTER-silent-except | backend/domains/orders/services/core/logistics.py:284 | 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/orders/services/core/logistics.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-008 | logic | NEW | CLUSTER-silent-except | backend/domains/orders/services/core/order_engine.py:211 | 5 silent except block(s); first at line 211: pass-only: except AttributeError: | all except blocks log at minimum DEBUG (Law 59) | 5 silent except block(s); first at line 211: pass-only: except AttributeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/orders/services/core/order_engine.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-071 | logic | NEW | CLUSTER-silent-except | backend/domains/orders/services/returns/service.py:67 | 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/orders/services/returns/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-072 | logic | NEW | CLUSTER-silent-except | backend/domains/orders/services/tracking/service.py:362 | 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/orders/services/tracking/service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-073 | logic | NEW | CLUSTER-silent-except | backend/domains/promotions/services/coupons/coupon_service.py:527 | 1 silent except block(s); first at line 527: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 527: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/domains/promotions/services/coupons/coupon_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-079 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/database/database_service.py:188 | 1 silent except block(s); first at line 188: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 188: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/database/database_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-033 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/database/rls_interceptor.py:174 | 2 silent except block(s); first at line 174: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 174: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/database/rls_interceptor.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-019 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/database/schemas.py:1104 | 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError): | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/database/schemas.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-035 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/messaging/events/event_bus.py:113 | 2 silent except block(s); first at line 113: pass-only: except Exception:  # noqa: BLE001 | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 113: pass-only: except Exception:  # noqa: BLE001 | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/messaging/events/event_bus.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-080 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/messaging/realtime.py:599 | 1 silent except block(s); first at line 599: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 599: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/messaging/realtime.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-034 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/messaging/ws_manager.py:91 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/messaging/ws_manager.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-081 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/ml/worker.py:92 | 1 silent except block(s); first at line 92: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 92: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/ml/worker.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-082 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/observability/audit.py:323 | 1 silent except block(s); first at line 323: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 323: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/observability/audit.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-036 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/observability/provider_observability.py:22 | 2 silent except block(s); first at line 22: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 22: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/observability/provider_observability.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-083 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/observability/service_observability.py:132 | 1 silent except block(s); first at line 132: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 132: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/observability/service_observability.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-037 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/utils/analytics.py:57 | 2 silent except block(s); first at line 57: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 57: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/utils/analytics.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-038 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/utils/pagination.py:31 | 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/utils/pagination.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-039 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/utils/performance_cache.py:110 | 2 silent except block(s); first at line 110: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 110: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/utils/performance_cache.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-002 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/utils/schema_audit.py:67 | 7 silent except block(s); first at line 67: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 7 silent except block(s); first at line 67: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/utils/schema_audit.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-040 | logic | NEW | CLUSTER-silent-except | backend/infrastructure/utils/websocket_manager.py:91 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/infrastructure/utils/websocket_manager.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-050 | logic | NEW | CLUSTER-silent-except | backend/lifespan.py:293 | 1 silent except block(s); first at line 293: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 293: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/lifespan.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-051 | logic | NEW | CLUSTER-silent-except | backend/main.py:199 | 1 silent except block(s); first at line 199: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 199: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/main.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-021 | logic | NEW | CLUSTER-silent-except | backend/middleware/country_context.py:245 | 3 silent except block(s); first at line 245: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 245: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/middleware/country_context.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-085 | logic | NEW | CLUSTER-silent-except | backend/middleware/webhook_ip_whitelist.py:424 | 1 silent except block(s); first at line 424: truly-silent: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 424: truly-silent: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/middleware/webhook_ip_whitelist.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-011 | logic | NEW | CLUSTER-silent-except | backend/middleware/webhook_verification.py:242 | 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError: | all except blocks log at minimum DEBUG (Law 59) | 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/middleware/webhook_verification.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-041 | logic | NEW | CLUSTER-silent-except | backend/modules/admin/routers/comms.py:150 | 2 silent except block(s); first at line 150: pass-only: except WebSocketDisconnect: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 150: pass-only: except WebSocketDisconnect: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/modules/admin/routers/comms.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-022 | logic | NEW | CLUSTER-silent-except | backend/modules/customer/routers/orders.py:160 | 3 silent except block(s); first at line 160: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 3 silent except block(s); first at line 160: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/modules/customer/routers/orders.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-043 | logic | NEW | CLUSTER-silent-except | backend/providers/ai/huggingface.py:78 | 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/ai/huggingface.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-044 | logic | NEW | CLUSTER-silent-except | backend/providers/ai/image_ai_service.py:231 | 2 silent except block(s); first at line 231: pass-only: except OSError: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 231: pass-only: except OSError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/ai/image_ai_service.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-045 | logic | NEW | CLUSTER-silent-except | backend/providers/ai/text.py:281 | 2 silent except block(s); first at line 281: truly-silent: except json.JSONDecodeError: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 281: truly-silent: except json.JSONDecodeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/ai/text.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-087 | logic | NEW | CLUSTER-silent-except | backend/providers/comms/whatsapp_selfhosted.py:148 | 1 silent except block(s); first at line 148: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 148: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/comms/whatsapp_selfhosted.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-089 | logic | NEW | CLUSTER-silent-except | backend/providers/geography/geo.py:108 | 1 silent except block(s); first at line 108: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 108: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/geography/geo.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-092 | logic | NEW | CLUSTER-silent-except | backend/providers/image/bg_remover/br_05__clean_edge_refiner.py:35 | 1 silent except block(s); first at line 35: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 35: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/bg_remover/br_05__clean_edge_refiner.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-093 | logic | NEW | CLUSTER-silent-except | backend/providers/image/bg_remover/br_06__precision_geometry_classes.py:237 | 1 silent except block(s); first at line 237: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 237: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/bg_remover/br_06__precision_geometry_classes.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-094 | logic | NEW | CLUSTER-silent-except | backend/providers/image/bg_remover/core_i_o.py:155 | 1 silent except block(s); first at line 155: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 155: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/bg_remover/core_i_o.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-095 | logic | NEW | CLUSTER-silent-except | backend/providers/image/bg_remover/public_api.py:302 | 1 silent except block(s); first at line 302: truly-silent: except Exception as exc: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 302: truly-silent: except Exception as exc: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/bg_remover/public_api.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-096 | logic | NEW | CLUSTER-silent-except | backend/providers/image/bg_remover/session_management.py:113 | 1 silent except block(s); first at line 113: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 113: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/bg_remover/session_management.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-090 | logic | NEW | CLUSTER-silent-except | backend/providers/image/free_image_tools.py:288 | 1 silent except block(s); first at line 288: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 288: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/free_image_tools.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-012 | logic | NEW | CLUSTER-silent-except | backend/providers/image/ocr.py:95 | 4 silent except block(s); first at line 95: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 4 silent except block(s); first at line 95: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/ocr.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-091 | logic | NEW | CLUSTER-silent-except | backend/providers/image/parcel_verification.py:510 | 1 silent except block(s); first at line 510: truly-silent: except (ValueError, TypeError): | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 510: truly-silent: except (ValueError, TypeError): | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/image/parcel_verification.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-042 | logic | NEW | CLUSTER-silent-except | backend/providers/observability.py:24 | 2 silent except block(s); first at line 24: pass-only: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 24: pass-only: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/observability.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-097 | logic | NEW | CLUSTER-silent-except | backend/providers/ocr/ocr_parser.py:44 | 1 silent except block(s); first at line 44: truly-silent: except ValueError: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 44: truly-silent: except ValueError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/ocr/ocr_parser.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-048 | logic | NEW | CLUSTER-silent-except | backend/providers/scanner/scanner.py:95 | 2 silent except block(s); first at line 95: truly-silent: except UnicodeDecodeError: | all except blocks log at minimum DEBUG (Law 59) | 2 silent except block(s); first at line 95: truly-silent: except UnicodeDecodeError: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/providers/scanner/scanner.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-099 | logic | NEW | CLUSTER-silent-except | backend/rbac/catalog.py:33 | 1 silent except block(s); first at line 33: truly-silent: except Exception: | all except blocks log at minimum DEBUG (Law 59) | 1 silent except block(s); first at line 33: truly-silent: except Exception: | Add logger.warning(..., exc_info=True) or re-raise | M | P2 | 4 | multiple | L0 | VERIFIED | — | grep -n 'except' backend/rbac/catalog.py | — | git revert <commit> | — | — | — | no | L-59 |
| LOGIC-286 | logic | NEW | CLUSTER-long-function | backend/config.py:359 | 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-262 | logic | NEW | CLUSTER-long-function | backend/domains/accounts/services/auth/auth_service.py:396 | 10 function(s) >50 lines; longest sample `authenticate_password` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 10 function(s) >50 lines; longest sample `authenticate_password` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-301 | logic | NEW | CLUSTER-long-function | backend/domains/accounts/services/gdpr_service.py:74 | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-263 | logic | NEW | CLUSTER-long-function | backend/domains/accounts/services/users/user_management_service.py:317 | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-302 | logic | NEW | CLUSTER-long-function | backend/domains/analytics/services/dashboards/analytics_service.py:91 | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-287 | logic | NEW | CLUSTER-long-function | backend/domains/catalog/services/ai_upload_service.py:76 | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-303 | logic | NEW | CLUSTER-long-function | backend/domains/catalog/services/products/products_service.py:204 | 2 function(s) >50 lines; longest sample `list_products` = 119 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `list_products` = 119 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-268 | logic | NEW | CLUSTER-long-function | backend/domains/catalog/services/search/search_service.py:306 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-304 | logic | NEW | CLUSTER-long-function | backend/domains/comms/services/email/email_gateway.py:371 | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-288 | logic | NEW | CLUSTER-long-function | backend/domains/comms/services/messaging/chat_service.py:153 | 3 function(s) >50 lines; longest sample `send_message` = 58 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `send_message` = 58 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-305 | logic | NEW | CLUSTER-long-function | backend/domains/comms/services/shared/chat_threads_query.py:19 | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-269 | logic | NEW | CLUSTER-long-function | backend/domains/country/services/core/country_service.py:183 | 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-306 | logic | NEW | CLUSTER-long-function | backend/domains/country/services/research/country_heuristic_engine.py:173 | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-270 | logic | NEW | CLUSTER-long-function | backend/domains/customers/services/search_service.py:326 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-308 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/country/supplier_finance_service.py:97 | 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-271 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/data_import_service.py:90 | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-258 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/ledger/general_ledger.py:62 | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines | functions SHOULD stay <=50 lines (Law 64) | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-289 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payments/gateway_paypal.py:39 | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-276 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payments/gateway_stripe.py:64 | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-265 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payments/gateway_tap.py:81 | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines | functions SHOULD stay <=50 lines (Law 64) | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-264 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payments/payment_engine.py:2054 | 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines | functions SHOULD stay <=50 lines (Law 64) | 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-290 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payments/payment_orchestrator.py:451 | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-261 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/payouts/payout_batch_service.py:50 | 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines | functions SHOULD stay <=50 lines (Law 64) | 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-307 | logic | NEW | CLUSTER-long-function | backend/domains/finance/services/trading_service.py:99 | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-309 | logic | NEW | CLUSTER-long-function | backend/domains/governance/services/command_center/background.py:297 | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-310 | logic | NEW | CLUSTER-long-function | backend/domains/governance/services/command_center/command_center_service.py:478 | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-291 | logic | NEW | CLUSTER-long-function | backend/domains/hr/services/employees/hr_service.py:401 | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-311 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/core/admin_service.py:78 | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-292 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/core/service.py:1479 | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-272 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/core/shipment_service.py:305 | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-273 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/partners/logistics_pricing_service.py:51 | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-293 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/partners/partner_service.py:62 | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-266 | logic | NEW | CLUSTER-long-function | backend/domains/logistics/services/partners/service.py:394 | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines | functions SHOULD stay <=50 lines (Law 64) | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-259 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/core/logistics.py:273 | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines | functions SHOULD stay <=50 lines (Law 64) | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-278 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/core/order_admin.py:5 | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-267 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/core/order_engine.py:304 | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines | functions SHOULD stay <=50 lines (Law 64) | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-277 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/orders_service.py:58 | 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-294 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/returns/service.py:265 | 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-279 | logic | NEW | CLUSTER-long-function | backend/domains/orders/services/tracking/service.py:401 | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-312 | logic | NEW | CLUSTER-long-function | backend/domains/promotions/services/coins/promotion_points_service.py:106 | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-313 | logic | NEW | CLUSTER-long-function | backend/domains/promotions/services/engine/admin_promotions_write_service.py:151 | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-314 | logic | NEW | CLUSTER-long-function | backend/domains/promotions/services/engine/promotion_service.py:119 | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-315 | logic | NEW | CLUSTER-long-function | backend/domains/security/services/fraud/fraud_detection_service.py:96 | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-260 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/health/supplier_health.py:73 | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines | functions SHOULD stay <=50 lines (Law 64) | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-281 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/orders/supplier_orders.py:35 | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-295 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/orders/supplier_orders_service.py:51 | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-296 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/products/supplier_product_service.py:43 | 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-282 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/products/supplier_products.py:142 | 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-316 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:32 | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-280 | logic | NEW | CLUSTER-long-function | backend/domains/suppliers/services/supplier_shared.py:196 | 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-274 | logic | NEW | CLUSTER-long-function | backend/infrastructure/database/seed/_common.py:328 | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-283 | logic | NEW | CLUSTER-long-function | backend/infrastructure/messaging/email_service.py:96 | 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-297 | logic | NEW | CLUSTER-long-function | backend/infrastructure/messaging/realtime.py:365 | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-317 | logic | NEW | CLUSTER-long-function | backend/infrastructure/observability/retry.py:27 | 2 function(s) >50 lines; longest sample `with_retry` = 87 lines | functions SHOULD stay <=50 lines (Law 64) | 2 function(s) >50 lines; longest sample `with_retry` = 87 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-284 | logic | NEW | CLUSTER-long-function | backend/infrastructure/utils/schema_audit.py:327 | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-318 | logic | NEW | CLUSTER-deep-nesting | backend/lifespan.py:232 | 87 function(s) exceed 4 nesting levels (max seen 17) | maximum 4 indentation levels per function (Law 65) | 87 function(s) exceed 4 nesting levels (max seen 17) | Refactor with guard clauses / extracted helpers | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-65 |
| LOGIC-285 | logic | NEW | CLUSTER-long-function | backend/providers/ai/ai_variant_config.py:497 | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines | functions SHOULD stay <=50 lines (Law 64) | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-298 | logic | NEW | CLUSTER-long-function | backend/providers/image/free_image_tools.py:160 | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-275 | logic | NEW | CLUSTER-long-function | backend/providers/image/parcel_verification.py:64 | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines | functions SHOULD stay <=50 lines (Law 64) | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-299 | logic | NEW | CLUSTER-long-function | backend/providers/payments/paypal.py:176 | 3 function(s) >50 lines; longest sample `create_order` = 79 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `create_order` = 79 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |
| LOGIC-300 | logic | NEW | CLUSTER-long-function | backend/providers/payments/paytabs.py:77 | 3 function(s) >50 lines; longest sample `create_payment_page` = 90 lines | functions SHOULD stay <=50 lines (Law 64) | 3 function(s) >50 lines; longest sample `create_payment_page` = 90 lines | Split the longest functions by responsibility | M | P3 | 4 | multiple | L0 | VERIFIED | — | — | — | git revert <commit> | — | — | — | no | L-64 |


### Over all

**Problem(s)**
1. 1 float-for-money signal(s); first: `"balance": float(balance),`
2. 1 float-for-money signal(s); first: `"click_through_rate": round((clicked_session_count / query_count) * 100, 1) if query_count else 0.0,`
3. 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,`
4. 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,`
5. 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None,`
6. 1 float-for-money signal(s); first: `"completion_rate": round((progress[1] or 0) / (progress[0] or 1) * 100, 2),`
7. 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`
8. 1 float-for-money signal(s); first: `"fulfillment_rate": round(fulfillment_rate, 2),`
9. 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,`
10. 1 float-for-money signal(s); first: `"rate": float(rule.rate),`
11. 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),`
12. 1 float-for-money signal(s); first: `"return_rate": round(return_rate, 2),`
13. 1 float-for-money signal(s); first: `"salary": float(emp.salary),`
14. 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,`
15. 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,`
16. 1 float-for-money signal(s); first: `"total_days": float(l.total_days),`
17. 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
18. 1 float-for-money signal(s); first: `"total_revenue": round(total_revenue, 2),`
19. 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),`
20. 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]`
21. 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]`
22. 1 float-for-money signal(s); first: `amount: Optional[float]`
23. 1 float-for-money signal(s); first: `amount: float | None`
24. 1 float-for-money signal(s); first: `amount: float`
25. 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`
26. 1 float-for-money signal(s); first: `discount_amount: float`
27. 1 float-for-money signal(s); first: `discount_value: Optional[float]`
28. 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))`
29. 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]`
30. 1 float-for-money signal(s); first: `percent = int(round((filled / total) * 100))`

**Solution(s)**
1. Add logger.warning(..., exc_info=True) or re-raise
2. Convert to Decimal and use kernel.money rounding helpers
3. Link each TODO to a ticket or delete it
4. Make the idempotency key required and enforce uniqueness
5. Refactor with guard clauses / extracted helpers
6. Split the longest functions by responsibility

**Corrections required (prioritized)**

| Priority | Correction | Target | Blocking | Effort |
|---|---|---|---|---|
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/country/services/tax/country_tax_service.py:68 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/schemas/finance_schemas.py:11 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/commission_read_service.py:70 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/country/supplier_finance_service.py:160 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/data_import_service.py:124 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/finance_service.py:66 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/ledger/accounting_controller.py:24 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/ledger/general_ledger.py:5836 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payments/gateway_paypal.py:189 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payments/gateway_stripe.py:167 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payments/gateway_tap.py:131 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payments/payment_engine.py:4704 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/trading_service.py:134 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/finance/services/treasury/cash_management_service.py:269 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/cart/cart_service__orders.py:166 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/cart/service.py:50 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/core/logistics.py:1892 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/core/misc.py:201 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/core/order_engine.py:906 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/orders_service.py:213 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/orders/services/tracking/service.py:348 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/suppliers/services/orders/supplier_orders.py:337 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/suppliers/services/orders/supplier_orders_service.py:80 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/domains/suppliers/services/profile/supplier_payouts_service.py:73 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/modules/customer/routers/orders.py:124 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/modules/employee/routers/finance.py:466 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/modules/employee/routers/orders.py:53 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/modules/supplier/routers/finance.py:45 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/providers/ai/finance_ai.py:87 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/providers/payments/base.py:99 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/providers/payments/base_models.py:31 | yes | M |
| P0 | Convert to Decimal and use kernel.money rounding helpers | backend/providers/payments/webhook_models.py:42 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/customers/services/coins/zozi_coins_service.py:169 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/customers/services/coins/zozi_coins_service.py:182 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/finance/services/payments/payment_engine.py:371 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/promotions/services/coupons/coupon_service.py:538 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/promotions/services/coupons/coupon_service.py:554 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/security/services/detection/public_security_detection_service.py:25 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/security/services/detection/public_security_detection_service.py:83 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/security/services/detection/public_security_detection_service.py:104 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/security/services/detection/public_security_detection_service.py:127 | yes | M |
| P0 | Make the idempotency key required and enforce uniqueness | backend/domains/security/services/detection/public_security_detection_service.py:144 | yes | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/suppliers/services/health/supplier_health.py:1430 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/security/services/fraud/fraud_detection_service.py:102 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/ledger/general_ledger.py:3774 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/suppliers/services/products/supplier_products.py:280 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/suppliers/services/supplier_shared.py:437 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/suppliers/services/orders/supplier_orders_service.py:518 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/infrastructure/security/dependencies.py:49 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/payments/gateway_tap.py:1111 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/payments/payment_orchestrator.py:693 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/suppliers/services/orders/supplier_orders_verify_service.py:139 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/providers/payments/generic.py:25 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/providers/payments/paypal.py:135 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/accounts/services/auth/public_security_registration_service.py:69 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/data_import_service.py:75 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/finance_ai_service.py:87 | partial | M |
| P1 | Add logger.warning(..., exc_info=True) or re-raise | backend/domains/finance/services/payments/payment_engine.py:3411 | partial | M |

---
## Dimension 04 · Operational

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 05 · Wiring

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 06 · Database

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 07 · Tables Fields

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 08 · Providers

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 09 · Laws

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

_Law matrix not produced._

---
## Dimension 10 · Migrations

### Summary
- Confirmation: ❌ FAIL
- Files with findings: 12
- Findings: 12
- P0: 0  P1: 6  P2: 6  P3: 0
- Clusters: 2
- Laws implicated: L-57
- Completion blockers: 0 yes · 6 partial · 6 no
- Observations: 0 (L0: 0)
- Status: NEW: 12 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Conf | Evidence | Truth | Claim | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker | Laws |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MIG-001 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:159 | upgrade() performs an unguarded destructive op at line 159 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 159 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '159p' backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-006 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py:123 | upgrade() performs an unguarded destructive op at line 123 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 123 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '123p' backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-007 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_08_31_0003_add_version_columns.py:65 | upgrade() performs an unguarded destructive op at line 65 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 65 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '65p' backend/alembic/versions/2026_08_31_0003_add_version_columns.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-008 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_08_31_0005_add_materialized_views.py:135 | upgrade() performs an unguarded destructive op at line 135 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 135 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '135p' backend/alembic/versions/2026_08_31_0005_add_materialized_views.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-009 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_09_01_workspace.py:161 | upgrade() performs an unguarded destructive op at line 161 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 161 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '161p' backend/alembic/versions/2026_09_01_workspace.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-011 | db | NEW | CLUSTER-migration-destructive | backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py:62 | upgrade() performs an unguarded destructive op at line 62 with no expand-contract staging | destructive migrations use expand-contract (Law 57) | upgrade() performs an unguarded destructive op at line 62 with no expand-contract staging | Split into expand + contract steps with a rollback window | S | P1 | 3 | multiple | L1 | INFERRED | — | sed -n '62p' backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py | — | git revert <commit> | — | — | — | partial | L-57 |
| MIG-002 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_08_08_21_02-02ebc285f66f_merge_divergent_heads_20260806_0009_and_.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |
| MIG-003 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_08_21_0005-20260821_crosscutting_domains.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |
| MIG-004 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_08_21_0006-20260821_customer_comm_logistics_media.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |
| MIG-005 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_08_21_0007-20260821_user_referral_to_customer.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |
| MIG-010 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |
| MIG-012 | db | NEW | CLUSTER-migration-downgrade | backend/alembic/versions/2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py:1 | empty/missing downgrade() | migrations are reversible or explicitly irreversible (Laws 57/219) | empty/missing downgrade() | Implement downgrade() or document irreversibility | S | P2 | 3 | multiple | L1 | INFERRED | — | — | — | git revert <commit> | — | — | — | no | — |


### Over all

**Problem(s)**
1. empty/missing downgrade()
2. upgrade() performs an unguarded destructive op at line 123 with no expand-contract staging
3. upgrade() performs an unguarded destructive op at line 135 with no expand-contract staging
4. upgrade() performs an unguarded destructive op at line 159 with no expand-contract staging
5. upgrade() performs an unguarded destructive op at line 161 with no expand-contract staging
6. upgrade() performs an unguarded destructive op at line 62 with no expand-contract staging
7. upgrade() performs an unguarded destructive op at line 65 with no expand-contract staging

**Solution(s)**
1. Implement downgrade() or document irreversibility
2. Split into expand + contract steps with a rollback window

**Corrections required (prioritized)**

| Priority | Correction | Target | Blocking | Effort |
|---|---|---|---|---|
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:159 | partial | S |
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py:123 | partial | S |
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_08_31_0003_add_version_columns.py:65 | partial | S |
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_08_31_0005_add_materialized_views.py:135 | partial | S |
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_09_01_workspace.py:161 | partial | S |
| P1 | Split into expand + contract steps with a rollback window | backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py:62 | partial | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_08_08_21_02-02ebc285f66f_merge_divergent_heads_20260806_0009_and_.py:1 | no | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_08_21_0005-20260821_crosscutting_domains.py:1 | no | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_08_21_0006-20260821_customer_comm_logistics_media.py:1 | no | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_08_21_0007-20260821_user_referral_to_customer.py:1 | no | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py:1 | no | S |
| P2 | Implement downgrade() or document irreversibility | backend/alembic/versions/2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py:1 | no | S |

---
## Dimension 11 · Environmental

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 12 · Tests

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 13 · Dev To Prod

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 14 · Frontend Web

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 15 · Frontend Mobile

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 16 · Features

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 17 · Code File Management

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 18 · Security

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 19 · Performance

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 20 · Observability Resilience

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 21 · Contradictions

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 22 · Anti Patterns

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 23 · Code Intent

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 24 · Browser Behavior

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 25 · Ai Drift

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 26 · Code Alignment

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## Dimension 27 · Project Completion Blockers

### Summary
- Confirmation: ❌ FAIL
- Files with findings: 1
- Findings: 1
- P0: 1  P1: 0  P2: 0  P3: 0
- Clusters: 1
- Laws implicated: L-81
- Completion blockers: 1 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 1 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Conf | Evidence | Truth | Claim | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker | Laws |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BLOCK-valkey-unreachable | infra | NEW | CLUSTER-boot-preflight | backend/ | Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limiting and the event bus degrade | Valkey 9.0.6+ reachable in every environment that runs the API | Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limiting and the event bus degrade | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | S | P0 | 5 | triangulated | L1 | VERIFIED | — | cd backend && python -c "import valkey; print(valkey.Valkey.from_url('valkey://host:6379').ping())" | — | git revert <commit> | boot, CI, deployment | — | — | yes | L-81 |


### Over all

**Problem(s)**
1. Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limiting and the event bus degrade

**Solution(s)**
1. Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed

**Corrections required (prioritized)**

| Priority | Correction | Target | Blocking | Effort |
|---|---|---|---|---|
| P0 | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | backend/ | yes | S |

---
## Dimension 28 · Supply Chain Security

### Summary
- Confirmation: ⚠️  NO EVIDENCE (check produced neither findings nor observations — treat as unverified)
- Files with findings: 0
- Findings: 0
- P0: 0  P1: 0  P2: 0  P3: 0
- Clusters: 0
- Laws implicated: —
- Completion blockers: 0 yes · 0 partial · 0 no
- Observations: 0 (L0: 0)
- Status: NEW: 0 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0

### Findings

_None._


### Over all

**Problem(s)**
1. None identified.

**Solution(s)**
1. None required.

**Corrections required (prioritized)**

_None._

---
## 6 · Cross-cutting passes

## 6.1 · Chains (critical business journeys)

_No chain data produced (scanner failure or --fast mode)._
---
## 6.2 · Contradictions (never silently resolved)

_None detected by the checks that ran._
---
## 6.3 · Anti-patterns

| ID | Category | Occurrences | Sample location | Blocker | Remediation |
|---|---|---|---|---|---|
| AP-silent-except | Silent except | 199 | backend/config.py | partial | Log or re-raise in every handler |

---
## 6.4 · Feature health

_No feature catalog data._
---
## 6.5 · Code intent

_None recorded._
---
## 6.6 · AI drift

_None recorded._
---
## 6.7 · Code alignment (frontend ↔ backend ↔ mobile)

_None recorded._
---
## 6.8 · Browser behavior

_None recorded._
---
## 6.9 · Supply chain security

_None recorded._
---
## 6.10 · LLM semantic review (Ollama, L2 only)

_None recorded (run with --llm)._
---
## 6.11 · Live database drift

_None recorded._
---
## 6.12 · Load / latency probe

_None recorded (run with --load against a live API)._
---
## 7 · Production readiness — 18-condition gate

**2 pass · 2 fail · 0 partial · 14 unverifiable · 0 deferred**

| # | Condition | Status | Evidence |
|---|---|---|---|
| 1 | All yes completion-blocker findings RESOLVED or waived | fail | 46 open yes-blocker(s) |
| 2 | All P1 findings RESOLVED or scheduled with a date | fail | 354 open P1 |
| 3 | pytest tests/architecture green | unverifiable | run `pytest tests/architecture/` |
| 4 | pytest commerce-domain suite green | unverifiable | collection status from pre-flight |
| 5 | pytest security suite green | unverifiable | collection status from pre-flight |
| 6 | App boots with zero skipped routers/stubs | unverifiable | boot smoke output |
| 7 | Frontend build passes with zero errors | unverifiable | tsc --noEmit / next build |
| 8 | Mobile build succeeds or explicitly deferred | unverifiable | eas build / deferral |
| 9 | Browser: money-path features pass | unverifiable | browser probe results |
| 10 | Browser: security-path features pass | unverifiable | browser probe results |
| 11 | Load test p95 < 500 ms at 2x peak | unverifiable | load probe results |
| 12 | Zero KEEP/HARDEN violations | pass | no KEEP/HARDEN constraints defined |
| 13 | Zero open contradictions blocking P0/P1 | pass | 0 contradiction(s) |
| 14 | Verifier: 3 consecutive GREEN cycles | unverifiable | CI history |
| 15 | All required env vars set in production config | unverifiable | env inventory |
| 16 | Database migrations linear and tested | unverifiable | alembic heads |
| 17 | Payment credentials stored encrypted | unverifiable | field-encryption check |
| 18 | PCI-DSS compliance verified (if card payments active) | unverifiable | not automatically verifiable |


### Unverifiable conditions

| # | Condition | Reason | What would verify it |
|---|---|---|---|
| 3 | pytest tests/architecture green | run `pytest tests/architecture/` | live environment / CI |
| 4 | pytest commerce-domain suite green | collection status from pre-flight | live environment / CI |
| 5 | pytest security suite green | collection status from pre-flight | live environment / CI |
| 6 | App boots with zero skipped routers/stubs | boot smoke output | live environment / CI |
| 7 | Frontend build passes with zero errors | tsc --noEmit / next build | live environment / CI |
| 8 | Mobile build succeeds or explicitly deferred | eas build / deferral | live environment / CI |
| 9 | Browser: money-path features pass | browser probe results | live environment / CI |
| 10 | Browser: security-path features pass | browser probe results | live environment / CI |
| 11 | Load test p95 < 500 ms at 2x peak | load probe results | live environment / CI |
| 14 | Verifier: 3 consecutive GREEN cycles | CI history | live environment / CI |
| 15 | All required env vars set in production config | env inventory | live environment / CI |
| 16 | Database migrations linear and tested | alembic heads | live environment / CI |
| 17 | Payment credentials stored encrypted | field-encryption check | live environment / CI |
| 18 | PCI-DSS compliance verified (if card payments active) | not automatically verifiable | live environment / CI |


### Waivers

_None on record._
---
## 8 · Design, interaction, taxonomy, workflow & data measurements

Every number below is measured from source during this run.

_No extension measurements were produced in this run._

---
## 7 · Recommendations & automation opportunities

_No recommendations were produced in this run._

---
## 8 · Remediation plan

### Completion blockers first

| ID | Phase | File:Line | Fix | Effort | Verify |
|---|---|---|---|---|---|
| BLOCK-valkey-unreachable | infra | backend/ | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | S | cd backend && python -c "import valkey; print(valkey.Valkey.from_url('valkey://host:6379').ping())" |
| ARCH-001 | arch | backend/modules/finance:1 | Move finance routers under a canonical module or delete the package | M | ls backend/modules |
| LOGIC-120 | logic | backend/domains/country/services/tax/country_tax_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/country/services/tax/country_tax_service.py \| head -20 |
| LOGIC-127 | logic | backend/domains/finance/schemas/finance_schemas.py:11 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/schemas/finance_schemas.py \| head -20 |
| LOGIC-128 | logic | backend/domains/finance/services/commission_read_service.py:70 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/commission_read_service.py \| head -20 |
| LOGIC-129 | logic | backend/domains/finance/services/country/supplier_finance_service.py:160 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/country/supplier_finance_service.py \| head -20 |
| LOGIC-130 | logic | backend/domains/finance/services/data_import_service.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/data_import_service.py \| head -20 |
| LOGIC-131 | logic | backend/domains/finance/services/finance_service.py:66 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/finance_service.py \| head -20 |
| LOGIC-132 | logic | backend/domains/finance/services/ledger/accounting_controller.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/accounting_controller.py \| head -20 |
| LOGIC-133 | logic | backend/domains/finance/services/ledger/general_ledger.py:5836 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/ledger/general_ledger.py \| head -20 |
| LOGIC-134 | logic | backend/domains/finance/services/payments/gateway_paypal.py:189 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_paypal.py \| head -20 |
| LOGIC-135 | logic | backend/domains/finance/services/payments/gateway_stripe.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_stripe.py \| head -20 |
| LOGIC-136 | logic | backend/domains/finance/services/payments/gateway_tap.py:131 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/gateway_tap.py \| head -20 |
| LOGIC-137 | logic | backend/domains/finance/services/payments/payment_engine.py:4704 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_engine.py \| head -20 |
| LOGIC-138 | logic | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payments/payment_orchestrator.py \| head -20 |
| LOGIC-139 | logic | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/payouts/payout_batch_service.py \| head -20 |
| LOGIC-140 | logic | backend/domains/finance/services/trading_service.py:134 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/trading_service.py \| head -20 |
| LOGIC-141 | logic | backend/domains/finance/services/treasury/cash_management_service.py:269 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/finance/services/treasury/cash_management_service.py \| head -20 |
| LOGIC-177 | logic | backend/domains/orders/services/cart/cart_service__orders.py:166 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/cart_service__orders.py \| head -20 |
| LOGIC-178 | logic | backend/domains/orders/services/cart/service.py:50 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/cart/service.py \| head -20 |
| LOGIC-179 | logic | backend/domains/orders/services/core/logistics.py:1892 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/logistics.py \| head -20 |
| LOGIC-180 | logic | backend/domains/orders/services/core/misc.py:201 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/misc.py \| head -20 |
| LOGIC-181 | logic | backend/domains/orders/services/core/order_engine.py:906 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/core/order_engine.py \| head -20 |
| LOGIC-182 | logic | backend/domains/orders/services/orders_service.py:213 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/orders_service.py \| head -20 |
| LOGIC-183 | logic | backend/domains/orders/services/tracking/service.py:348 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/orders/services/tracking/service.py \| head -20 |
| LOGIC-203 | logic | backend/domains/suppliers/services/orders/supplier_orders.py:337 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders.py \| head -20 |
| LOGIC-204 | logic | backend/domains/suppliers/services/orders/supplier_orders_service.py:80 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/orders/supplier_orders_service.py \| head -20 |
| LOGIC-209 | logic | backend/domains/suppliers/services/profile/supplier_payouts_service.py:73 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/domains/suppliers/services/profile/supplier_payouts_service.py \| head -20 |
| LOGIC-225 | logic | backend/modules/customer/routers/orders.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/modules/customer/routers/orders.py \| head -20 |
| LOGIC-230 | logic | backend/modules/employee/routers/finance.py:466 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/finance.py \| head -20 |
| LOGIC-233 | logic | backend/modules/employee/routers/orders.py:53 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/modules/employee/routers/orders.py \| head -20 |
| LOGIC-238 | logic | backend/modules/supplier/routers/finance.py:45 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/modules/supplier/routers/finance.py \| head -20 |
| LOGIC-242 | logic | backend/providers/ai/finance_ai.py:87 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/providers/ai/finance_ai.py \| head -20 |
| LOGIC-252 | logic | backend/providers/payments/base.py:99 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base.py \| head -20 |
| LOGIC-253 | logic | backend/providers/payments/base_models.py:31 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/providers/payments/base_models.py \| head -20 |
| LOGIC-254 | logic | backend/providers/payments/webhook_models.py:42 | Convert to Decimal and use kernel.money rounding helpers | M | grep -nE 'float\(\|Float\|: float' backend/providers/payments/webhook_models.py \| head -20 |
| LOGIC-320 | logic | backend/domains/customers/services/coins/zozi_coins_service.py:169 | Make the idempotency key required and enforce uniqueness | M | sed -n '169p' backend/domains/customers/services/coins/zozi_coins_service.py |
| LOGIC-321 | logic | backend/domains/customers/services/coins/zozi_coins_service.py:182 | Make the idempotency key required and enforce uniqueness | M | sed -n '182p' backend/domains/customers/services/coins/zozi_coins_service.py |
| LOGIC-322 | logic | backend/domains/finance/services/payments/payment_engine.py:371 | Make the idempotency key required and enforce uniqueness | M | sed -n '371p' backend/domains/finance/services/payments/payment_engine.py |
| LOGIC-323 | logic | backend/domains/promotions/services/coupons/coupon_service.py:538 | Make the idempotency key required and enforce uniqueness | M | sed -n '538p' backend/domains/promotions/services/coupons/coupon_service.py |
| LOGIC-324 | logic | backend/domains/promotions/services/coupons/coupon_service.py:554 | Make the idempotency key required and enforce uniqueness | M | sed -n '554p' backend/domains/promotions/services/coupons/coupon_service.py |
| LOGIC-325 | logic | backend/domains/security/services/detection/public_security_detection_service.py:25 | Make the idempotency key required and enforce uniqueness | M | sed -n '25p' backend/domains/security/services/detection/public_security_detection_service.py |
| LOGIC-326 | logic | backend/domains/security/services/detection/public_security_detection_service.py:83 | Make the idempotency key required and enforce uniqueness | M | sed -n '83p' backend/domains/security/services/detection/public_security_detection_service.py |
| LOGIC-327 | logic | backend/domains/security/services/detection/public_security_detection_service.py:104 | Make the idempotency key required and enforce uniqueness | M | sed -n '104p' backend/domains/security/services/detection/public_security_detection_service.py |
| LOGIC-328 | logic | backend/domains/security/services/detection/public_security_detection_service.py:127 | Make the idempotency key required and enforce uniqueness | M | sed -n '127p' backend/domains/security/services/detection/public_security_detection_service.py |
| LOGIC-329 | logic | backend/domains/security/services/detection/public_security_detection_service.py:144 | Make the idempotency key required and enforce uniqueness | M | sed -n '144p' backend/domains/security/services/detection/public_security_detection_service.py |


### Phase execution order

| Phase | Findings | Blockers (yes) | Example work |
|---|---|---|---|
| db | 12 | 0 | Split into expand + contract steps with a rollback window |
| logic | 329 | 44 | Add logger.warning(..., exc_info=True) or re-raise |
| arch | 232 | 1 | Move finance routers under a canonical module or delete the package |
| infra | 1 | 1 | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed |


### P0 — 45 finding(s)

| ID | Phase | Dimension | File:Line | Fix | Effort | Conf | Blocker |
|---|---|---|---|---|---|---|---|
| BLOCK-valkey-unreachable | infra | 27 · Project Completion Blockers | backend/ | Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed | S | 5 | yes |
| LOGIC-120 | logic | 03 · Logical | backend/domains/country/services/tax/country_tax_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-127 | logic | 03 · Logical | backend/domains/finance/schemas/finance_schemas.py:11 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-128 | logic | 03 · Logical | backend/domains/finance/services/commission_read_service.py:70 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-129 | logic | 03 · Logical | backend/domains/finance/services/country/supplier_finance_service.py:160 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-130 | logic | 03 · Logical | backend/domains/finance/services/data_import_service.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-131 | logic | 03 · Logical | backend/domains/finance/services/finance_service.py:66 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-132 | logic | 03 · Logical | backend/domains/finance/services/ledger/accounting_controller.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-133 | logic | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:5836 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-134 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_paypal.py:189 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-135 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_stripe.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-136 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:131 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-137 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:4704 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-138 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:1392 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-139 | logic | 03 · Logical | backend/domains/finance/services/payouts/payout_batch_service.py:1779 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-140 | logic | 03 · Logical | backend/domains/finance/services/trading_service.py:134 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-141 | logic | 03 · Logical | backend/domains/finance/services/treasury/cash_management_service.py:269 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-177 | logic | 03 · Logical | backend/domains/orders/services/cart/cart_service__orders.py:166 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-178 | logic | 03 · Logical | backend/domains/orders/services/cart/service.py:50 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-179 | logic | 03 · Logical | backend/domains/orders/services/core/logistics.py:1892 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-180 | logic | 03 · Logical | backend/domains/orders/services/core/misc.py:201 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-181 | logic | 03 · Logical | backend/domains/orders/services/core/order_engine.py:906 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-182 | logic | 03 · Logical | backend/domains/orders/services/orders_service.py:213 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-183 | logic | 03 · Logical | backend/domains/orders/services/tracking/service.py:348 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-203 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders.py:337 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-204 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_service.py:80 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-209 | logic | 03 · Logical | backend/domains/suppliers/services/profile/supplier_payouts_service.py:73 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-225 | logic | 03 · Logical | backend/modules/customer/routers/orders.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-230 | logic | 03 · Logical | backend/modules/employee/routers/finance.py:466 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-233 | logic | 03 · Logical | backend/modules/employee/routers/orders.py:53 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-238 | logic | 03 · Logical | backend/modules/supplier/routers/finance.py:45 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-242 | logic | 03 · Logical | backend/providers/ai/finance_ai.py:87 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-252 | logic | 03 · Logical | backend/providers/payments/base.py:99 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-253 | logic | 03 · Logical | backend/providers/payments/base_models.py:31 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-254 | logic | 03 · Logical | backend/providers/payments/webhook_models.py:42 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | yes |
| LOGIC-320 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:169 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-321 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:182 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-322 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:371 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-323 | logic | 03 · Logical | backend/domains/promotions/services/coupons/coupon_service.py:538 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-324 | logic | 03 · Logical | backend/domains/promotions/services/coupons/coupon_service.py:554 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-325 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:25 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-326 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:83 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-327 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:104 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-328 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:127 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |
| LOGIC-329 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:144 | Make the idempotency key required and enforce uniqueness | M | 4 | yes |


### P1 — 354 finding(s)

| ID | Phase | Dimension | File:Line | Fix | Effort | Conf | Blocker |
|---|---|---|---|---|---|---|---|
| ARCH-001 | arch | 01 · Architectural | backend/modules/finance:1 | Move finance routers under a canonical module or delete the package | M | 4 | yes |
| ARCH-002 | arch | 01 · Architectural | backend/domains/media:1 | Demote media to canonical domain or document an ARCH change | M | 4 | partial |
| ARCH-003 | arch | 01 · Architectural | backend/domains/payments:1 | Demote payments to canonical domain or document an ARCH change | M | 4 | partial |
| MIG-001 | db | 10 · Migrations | backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py:159 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| MIG-006 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0002_add_uuid_columns.py:123 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| MIG-007 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0003_add_version_columns.py:65 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| MIG-008 | db | 10 · Migrations | backend/alembic/versions/2026_08_31_0005_add_materialized_views.py:135 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| MIG-009 | db | 10 · Migrations | backend/alembic/versions/2026_09_01_workspace.py:161 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| MIG-011 | db | 10 · Migrations | backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py:62 | Split into expand + contract steps with a rollback window | S | 3 | partial |
| ARCH-024 | arch | 01 · Architectural | backend/infrastructure/database/init_db.py:49 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-025 | arch | 01 · Architectural | backend/infrastructure/database/seed/_common.py:1078 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-026 | arch | 01 · Architectural | backend/infrastructure/geography/__init__.py:8 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-027 | arch | 01 · Architectural | backend/infrastructure/geography/__init__.py:9 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-028 | arch | 01 · Architectural | backend/infrastructure/messaging/email_service.py:28 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-029 | arch | 01 · Architectural | backend/infrastructure/messaging/realtime.py:495 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-030 | arch | 01 · Architectural | backend/infrastructure/ml/worker.py:52 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-031 | arch | 01 · Architectural | backend/infrastructure/storage/backup.py:300 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-032 | arch | 01 · Architectural | backend/infrastructure/storage/storage.py:27 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-033 | arch | 01 · Architectural | backend/infrastructure/utils/category_tree.py:56 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-034 | arch | 01 · Architectural | backend/infrastructure/utils/category_tree.py:76 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-035 | arch | 01 · Architectural | backend/infrastructure/utils/country_detection_middleware.py:2 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-036 | arch | 01 · Architectural | backend/infrastructure/utils/country_rls.py:26 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-037 | arch | 01 · Architectural | backend/infrastructure/utils/country_rls.py:102 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-038 | arch | 01 · Architectural | backend/infrastructure/utils/import_service.py:14 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-039 | arch | 01 · Architectural | backend/middleware/dependencies/auth.py:19 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-040 | arch | 01 · Architectural | backend/middleware/dependencies/country_detection.py:34 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-041 | arch | 01 · Architectural | backend/modules/admin/routers/accounts.py:50 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-042 | arch | 01 · Architectural | backend/modules/admin/routers/accounts.py:50 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-043 | arch | 01 · Architectural | backend/modules/admin/routers/catalog.py:36 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-044 | arch | 01 · Architectural | backend/modules/admin/routers/comms.py:10 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-045 | arch | 01 · Architectural | backend/modules/admin/routers/governance.py:12 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-046 | arch | 01 · Architectural | backend/modules/admin/routers/logistics.py:10 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-047 | arch | 01 · Architectural | backend/modules/admin/routers/logistics.py:12 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-048 | arch | 01 · Architectural | backend/modules/admin/routers/logistics.py:13 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-049 | arch | 01 · Architectural | backend/modules/admin/routers/logistics.py:13 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-050 | arch | 01 · Architectural | backend/modules/admin/routers/promotions.py:32 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-051 | arch | 01 · Architectural | backend/modules/admin/routers/promotions.py:33 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-052 | arch | 01 · Architectural | backend/modules/admin/routers/promotions.py:33 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-053 | arch | 01 · Architectural | backend/modules/admin/routers/staff.py:32 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-054 | arch | 01 · Architectural | backend/modules/admin/routers/staff.py:32 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-055 | arch | 01 · Architectural | backend/modules/admin/routers/staff.py:38 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-056 | arch | 01 · Architectural | backend/modules/customer/routers/accounts.py:10 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-057 | arch | 01 · Architectural | backend/modules/customer/routers/accounts.py:247 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-058 | arch | 01 · Architectural | backend/modules/customer/routers/catalog.py:20 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-059 | arch | 01 · Architectural | backend/modules/customer/routers/country.py:13 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-060 | arch | 01 · Architectural | backend/modules/customer/routers/orders.py:13 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-061 | arch | 01 · Architectural | backend/modules/customer/routers/reviews.py:30 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-062 | arch | 01 · Architectural | backend/modules/employee/routers/attendance.py:8 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-063 | arch | 01 · Architectural | backend/modules/employee/routers/finance.py:1207 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-064 | arch | 01 · Architectural | backend/modules/employee/routers/finance.py:1207 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-065 | arch | 01 · Architectural | backend/modules/employee/routers/hr.py:13 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-066 | arch | 01 · Architectural | backend/modules/employee/routers/offices.py:8 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-067 | arch | 01 · Architectural | backend/modules/employee/routers/orders.py:11 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-068 | arch | 01 · Architectural | backend/modules/employee/routers/hr/attendance.py:9 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-069 | arch | 01 · Architectural | backend/modules/employee/routers/hr/employees.py:9 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-070 | arch | 01 · Architectural | backend/modules/employee/routers/hr/leaves.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-071 | arch | 01 · Architectural | backend/modules/employee/routers/hr/offices.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-072 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:307 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-073 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:308 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-074 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:308 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-075 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:318 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-076 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:319 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-077 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:319 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-078 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:329 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-079 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:335 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-080 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:336 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-081 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:336 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-082 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:346 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-083 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:347 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-084 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:347 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-085 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:357 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-086 | arch | 01 · Architectural | backend/modules/logistics/routers/accounts.py:15 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-087 | arch | 01 · Architectural | backend/modules/logistics/routers/analytics.py:15 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-088 | arch | 01 · Architectural | backend/modules/logistics/routers/catalog.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-089 | arch | 01 · Architectural | backend/modules/logistics/routers/comms.py:18 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-090 | arch | 01 · Architectural | backend/modules/logistics/routers/country.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-091 | arch | 01 · Architectural | backend/modules/logistics/routers/hr.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-092 | arch | 01 · Architectural | backend/modules/logistics/routers/logistics.py:12 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-093 | arch | 01 · Architectural | backend/modules/logistics/routers/logistics.py:14 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-094 | arch | 01 · Architectural | backend/modules/logistics/routers/orders.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-095 | arch | 01 · Architectural | backend/modules/logistics/routers/promotions.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-096 | arch | 01 · Architectural | backend/modules/logistics/routers/security.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-097 | arch | 01 · Architectural | backend/modules/logistics/routers/suppliers.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-098 | arch | 01 · Architectural | backend/modules/supplier/routers/accounts.py:14 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-099 | arch | 01 · Architectural | backend/modules/supplier/routers/analytics.py:18 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-100 | arch | 01 · Architectural | backend/modules/supplier/routers/catalog.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-101 | arch | 01 · Architectural | backend/modules/supplier/routers/comms.py:18 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-102 | arch | 01 · Architectural | backend/modules/supplier/routers/country.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-103 | arch | 01 · Architectural | backend/modules/supplier/routers/finance.py:10 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-104 | arch | 01 · Architectural | backend/modules/supplier/routers/hr.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-105 | arch | 01 · Architectural | backend/modules/supplier/routers/logistics.py:14 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-106 | arch | 01 · Architectural | backend/modules/supplier/routers/orders.py:10 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-107 | arch | 01 · Architectural | backend/modules/supplier/routers/promotions.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-108 | arch | 01 · Architectural | backend/modules/supplier/routers/security.py:7 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-109 | arch | 01 · Architectural | backend/modules/supplier/routers/suppliers.py:8 | Route through the sanctioned layer (events/ports/service call) | M | 4 | no |
| ARCH-110 | arch | 01 · Architectural | backend/domains/accounts/models/user.py:21 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-111 | arch | 01 · Architectural | backend/domains/accounts/models/user.py:22 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-112 | arch | 01 · Architectural | backend/domains/accounts/services/permissions/permission_service.py:699 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-113 | arch | 01 · Architectural | backend/domains/accounts/services/users/user_management_service.py:87 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-114 | arch | 01 · Architectural | backend/domains/analytics/models/analytics_schema_models.py:85 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-115 | arch | 01 · Architectural | backend/domains/audit/services/compliance_engine.py:16 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-116 | arch | 01 · Architectural | backend/domains/audit/services/data_residency_service.py:11 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-117 | arch | 01 · Architectural | backend/domains/audit/services/ediscovery.py:171 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-118 | arch | 01 · Architectural | backend/domains/audit/services/compliance_engine.py:13 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-119 | arch | 01 · Architectural | backend/domains/catalog/services/products/admin_products_service.py:395 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-120 | arch | 01 · Architectural | backend/domains/catalog/services/products/admin_products_service.py:393 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-121 | arch | 01 · Architectural | backend/domains/catalog/ports.py:27 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-122 | arch | 01 · Architectural | backend/domains/comms/services/messaging/chat_service.py:459 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-123 | arch | 01 · Architectural | backend/domains/comms/services/shared/utility/shared_utils.py:251 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-124 | arch | 01 · Architectural | backend/domains/comms/models/communication.py:8 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-125 | arch | 01 · Architectural | backend/domains/comms/services/tickets/tickets_service.py:2 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-126 | arch | 01 · Architectural | backend/domains/comms/services/messaging/chat_service.py:562 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-127 | arch | 01 · Architectural | backend/domains/comms/ports.py:50 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-128 | arch | 01 · Architectural | backend/domains/comms/models/suppliers.py:12 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-129 | arch | 01 · Architectural | backend/domains/country/models/country_enhancements.py:10 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-130 | arch | 01 · Architectural | backend/domains/country/services/core/country_service.py:1792 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-131 | arch | 01 · Architectural | backend/domains/country/ports.py:23 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-132 | arch | 01 · Architectural | backend/domains/country/services/core/country_service.py:1789 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-133 | arch | 01 · Architectural | backend/domains/country/services/geo/country_detection.py:149 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-134 | arch | 01 · Architectural | backend/domains/customers/services/cart_service.py:23 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-135 | arch | 01 · Architectural | backend/domains/customers/services/cart_service.py:24 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-136 | arch | 01 · Architectural | backend/domains/customers/services/customer_health_engine.py:11 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-137 | arch | 01 · Architectural | backend/domains/customers/services/coupons_read_service.py:17 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-138 | arch | 01 · Architectural | backend/domains/finance/services/finance_service.py:495 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-139 | arch | 01 · Architectural | backend/domains/finance/services/data_import_service.py:13 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-140 | arch | 01 · Architectural | backend/domains/finance/services/ledger/general_ledger.py:3005 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-141 | arch | 01 · Architectural | backend/domains/finance/services/ledger/general_ledger.py:1439 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-142 | arch | 01 · Architectural | backend/domains/finance/services/country/admin_commission_service.py:11 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-143 | arch | 01 · Architectural | backend/domains/finance/services/data_import_service.py:17 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-144 | arch | 01 · Architectural | backend/domains/finance/services/country/supplier_finance_service.py:23 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-145 | arch | 01 · Architectural | backend/domains/finance/services/payments/payment_engine.py:73 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-146 | arch | 01 · Architectural | backend/domains/governance/ports.py:24 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-147 | arch | 01 · Architectural | backend/domains/governance/services/audit/__init__.py:2 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-148 | arch | 01 · Architectural | backend/domains/governance/services/export_read_service.py:15 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-149 | arch | 01 · Architectural | backend/domains/governance/ports.py:38 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-150 | arch | 01 · Architectural | backend/domains/governance/models/admin.py:9 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-151 | arch | 01 · Architectural | backend/domains/governance/ports.py:35 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-152 | arch | 01 · Architectural | backend/domains/governance/services/admin/bulk_ops_service.py:18 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-153 | arch | 01 · Architectural | backend/domains/governance/services/approval/approval_matrix_service.py:17 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-154 | arch | 01 · Architectural | backend/domains/governance/services/users_service.py:10 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-155 | arch | 01 · Architectural | backend/domains/governance/services/export_read_service.py:16 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-156 | arch | 01 · Architectural | backend/domains/governance/ports.py:26 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-157 | arch | 01 · Architectural | backend/domains/governance/ports.py:36 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-158 | arch | 01 · Architectural | backend/domains/governance/ports.py:25 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-159 | arch | 01 · Architectural | backend/domains/hr/services/hr_employee_service.py:20 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-160 | arch | 01 · Architectural | backend/domains/hr/models/employee_models.py:7 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-161 | arch | 01 · Architectural | backend/domains/hr/services/employees/hr_service.py:678 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-162 | arch | 01 · Architectural | backend/domains/hr/services/employees/coi_service.py:19 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-163 | arch | 01 · Architectural | backend/domains/logistics/models/logistics_schema_models.py:50 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-164 | arch | 01 · Architectural | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:22 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-165 | arch | 01 · Architectural | backend/domains/logistics/services/core/admin_logistics_operations_service.py:8 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-166 | arch | 01 · Architectural | backend/domains/logistics/ports.py:193 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-167 | arch | 01 · Architectural | backend/domains/logistics/services/core/country_communication_service.py:13 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-168 | arch | 01 · Architectural | backend/domains/logistics/models/logistics_entities.py:9 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-169 | arch | 01 · Architectural | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:23 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-170 | arch | 01 · Architectural | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:26 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-171 | arch | 01 · Architectural | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:36 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-172 | arch | 01 · Architectural | backend/domains/logistics/services/health/service.py:114 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-173 | arch | 01 · Architectural | backend/domains/logistics/services/core/shipment_service.py:16 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-174 | arch | 01 · Architectural | backend/domains/orders/ports.py:1538 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-175 | arch | 01 · Architectural | backend/domains/orders/services/core/order_engine.py:49 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-176 | arch | 01 · Architectural | backend/domains/orders/ports.py:1491 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-177 | arch | 01 · Architectural | backend/domains/orders/services/core/admin_extra.py:146 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-178 | arch | 01 · Architectural | backend/domains/orders/models/order_entities.py:8 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-179 | arch | 01 · Architectural | backend/domains/orders/services/core/order_engine.py:27 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-180 | arch | 01 · Architectural | backend/domains/orders/services/orders_service.py:25 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-181 | arch | 01 · Architectural | backend/domains/orders/services/cart/service.py:30 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-182 | arch | 01 · Architectural | backend/domains/orders/services/core/misc.py:370 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-183 | arch | 01 · Architectural | backend/domains/orders/services/logistics_service.py:16 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-184 | arch | 01 · Architectural | backend/domains/orders/ports.py:1600 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-185 | arch | 01 · Architectural | backend/domains/orders/services/disputes/service.py:16 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-186 | arch | 01 · Architectural | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:6 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-187 | arch | 01 · Architectural | backend/domains/promotions/services/coupons/coupon_service.py:47 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-188 | arch | 01 · Architectural | backend/domains/promotions/models/coupon_usage.py:9 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-189 | arch | 01 · Architectural | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:9 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-190 | arch | 01 · Architectural | backend/domains/promotions/services/coupons/customer_coupons_create_service.py:21 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-191 | arch | 01 · Architectural | backend/domains/security/services/detection/public_security_detection_service.py:8 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-192 | arch | 01 · Architectural | backend/domains/security/services/health/flat_risk_service.py:10 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-193 | arch | 01 · Architectural | backend/domains/security/services/fraud/fraud_detection_service.py:30 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-194 | arch | 01 · Architectural | backend/domains/suppliers/models/suppliers.py:249 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-195 | arch | 01 · Architectural | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:12 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-196 | arch | 01 · Architectural | backend/domains/suppliers/services/disputes_service.py:14 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-197 | arch | 01 · Architectural | backend/domains/suppliers/services/contract/contract_service.py:15 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-198 | arch | 01 · Architectural | backend/domains/suppliers/services/badges/badge_write_service.py:31 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-199 | arch | 01 · Architectural | backend/domains/suppliers/models/suppliers.py:233 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-200 | arch | 01 · Architectural | backend/domains/suppliers/services/health/supplier_health.py:15 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-201 | arch | 01 · Architectural | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:14 | Move the call behind the owning domain's ports/ or emit an event | M | 4 | no |
| ARCH-202 | arch | 01 · Architectural | domains.audit ↔ domains.catalog | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-203 | arch | 01 · Architectural | domains.accounts ↔ domains.audit | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-204 | arch | 01 · Architectural | domains.country ↔ domains.customers | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-205 | arch | 01 · Architectural | domains.orders ↔ domains.promotions | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-206 | arch | 01 · Architectural | domains.finance ↔ domains.governance | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-207 | arch | 01 · Architectural | domains.finance ↔ domains.governance | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-208 | arch | 01 · Architectural | domains.finance ↔ domains.logistics | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-209 | arch | 01 · Architectural | domains.country ↔ domains.customers | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-210 | arch | 01 · Architectural | domains.catalog ↔ domains.comms | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-211 | arch | 01 · Architectural | domains.finance ↔ domains.logistics | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-212 | arch | 01 · Architectural | domains.accounts ↔ domains.audit | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-213 | arch | 01 · Architectural | domains.accounts ↔ domains.audit | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-214 | arch | 01 · Architectural | domains.catalog ↔ domains.country | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-215 | arch | 01 · Architectural | domains.accounts ↔ domains.audit | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-216 | arch | 01 · Architectural | domains.logistics ↔ domains.orders | Break the cycle with a port/event boundary | M | 4 | no |
| ARCH-217 | arch | 01 · Architectural | domains.country ↔ domains.customers | Break the cycle with a port/event boundary | M | 4 | no |
| LOGIC-001 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health.py:1430 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-005 | logic | 03 · Logical | backend/domains/security/services/fraud/fraud_detection_service.py:102 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-006 | logic | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:3774 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-009 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products.py:280 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-010 | logic | 03 · Logical | backend/domains/suppliers/services/supplier_shared.py:437 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-018 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_service.py:518 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-020 | logic | 03 · Logical | backend/infrastructure/security/dependencies.py:49 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-025 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:1111 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-026 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:693 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-032 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_verify_service.py:139 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-046 | logic | 03 · Logical | backend/providers/payments/generic.py:25 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-047 | logic | 03 · Logical | backend/providers/payments/paypal.py:135 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-052 | logic | 03 · Logical | backend/domains/accounts/services/auth/public_security_registration_service.py:69 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-062 | logic | 03 · Logical | backend/domains/finance/services/data_import_service.py:75 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-063 | logic | 03 · Logical | backend/domains/finance/services/finance_ai_service.py:87 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-064 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:3411 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-074 | logic | 03 · Logical | backend/domains/security/services/security_provider_helpers.py:30 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-075 | logic | 03 · Logical | backend/domains/security/services/core/kms_encryption.py:78 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-076 | logic | 03 · Logical | backend/domains/security/services/detection/public_security_detection_service.py:44 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-077 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_product_service.py:237 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-078 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products_service.py:203 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-084 | logic | 03 · Logical | backend/infrastructure/security/kms_integration.py:26 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-086 | logic | 03 · Logical | backend/providers/ai/finance_ai.py:88 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-088 | logic | 03 · Logical | backend/providers/finance/bank_api.py:115 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| LOGIC-098 | logic | 03 · Logical | backend/providers/security/watchlist.py:73 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | partial |
| ARCH-219 | arch | 01 · Architectural | backend/modules/admin/routers/staff.py:1 | Move DB access into the domain service | M | 4 | no |
| ARCH-223 | arch | 01 · Architectural | backend/modules/customer/routers/reviews.py:1 | Move DB access into the domain service | M | 4 | no |
| LOGIC-100 | logic | 03 · Logical | backend/domains/accounts/services/permissions/permission_service.py:693 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-101 | logic | 03 · Logical | backend/domains/analytics/services/dashboards/admin_analytics_service.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-102 | logic | 03 · Logical | backend/domains/analytics/services/dashboards/analytics_service.py:282 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-103 | logic | 03 · Logical | backend/domains/catalog/services/categories/bulk_category_service.py:238 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-104 | logic | 03 · Logical | backend/domains/catalog/services/categories/categories_service.py:86 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-105 | logic | 03 · Logical | backend/domains/catalog/services/categories/category_service.py:186 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-106 | logic | 03 · Logical | backend/domains/catalog/services/commission_service.py:285 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-107 | logic | 03 · Logical | backend/domains/catalog/services/products/product_discount_service.py:65 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-108 | logic | 03 · Logical | backend/domains/catalog/services/products/products_service.py:216 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-109 | logic | 03 · Logical | backend/domains/catalog/services/search/ai_search_service.py:78 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-110 | logic | 03 · Logical | backend/domains/catalog/services/search/search_service.py:24 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-111 | logic | 03 · Logical | backend/domains/comms/services/email/email_management.py:341 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-112 | logic | 03 · Logical | backend/domains/comms/services/email/transactional.py:441 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-113 | logic | 03 · Logical | backend/domains/comms/services/messaging/chat_service.py:717 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-114 | logic | 03 · Logical | backend/domains/comms/services/shared/utility/shared_utils.py:399 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-115 | logic | 03 · Logical | backend/domains/country/ports.py:124 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-116 | logic | 03 · Logical | backend/domains/country/services/core/country_config_admin_service.py:286 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-117 | logic | 03 · Logical | backend/domains/country/services/localization/localization_service.py:155 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-118 | logic | 03 · Logical | backend/domains/country/services/research/country_auto_populate.py:617 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-119 | logic | 03 · Logical | backend/domains/country/services/research/country_heuristic_engine.py:290 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-121 | logic | 03 · Logical | backend/domains/customers/services/cart_service.py:149 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-122 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:274 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-123 | logic | 03 · Logical | backend/domains/customers/services/customer_health_engine.py:67 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-124 | logic | 03 · Logical | backend/domains/customers/services/profile_service.py:105 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-125 | logic | 03 · Logical | backend/domains/customers/services/recommendations/recommendation_service.py:250 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-126 | logic | 03 · Logical | backend/domains/customers/services/search_service.py:51 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-142 | logic | 03 · Logical | backend/domains/governance/read_models/governance_read_models.py:96 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-143 | logic | 03 · Logical | backend/domains/governance/schemas/governance_schemas.py:177 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-144 | logic | 03 · Logical | backend/domains/governance/services/admin/admin_service.py:118 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-145 | logic | 03 · Logical | backend/domains/governance/services/approval/approval_matrix_service.py:30 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-146 | logic | 03 · Logical | backend/domains/governance/services/command_center/command_center_service.py:144 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-147 | logic | 03 · Logical | backend/domains/governance/services/command_center/service.py:344 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-148 | logic | 03 · Logical | backend/domains/governance/services/products_service.py:38 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-149 | logic | 03 · Logical | backend/domains/governance/services/settings/admin_service.py:41 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-150 | logic | 03 · Logical | backend/domains/governance/services/settings/governance_package_service.py:38 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-151 | logic | 03 · Logical | backend/domains/hr/services/employees/employee_service.py:152 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-152 | logic | 03 · Logical | backend/domains/hr/services/hr_employee_service.py:539 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-153 | logic | 03 · Logical | backend/domains/hr/services/learning/lms_service.py:148 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-154 | logic | 03 · Logical | backend/domains/hr/services/payroll/payroll_engine.py:377 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-155 | logic | 03 · Logical | backend/domains/hr/services/payroll/payroll_service.py:265 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-156 | logic | 03 · Logical | backend/domains/hr/services/performance/dei_auditor.py:69 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-157 | logic | 03 · Logical | backend/domains/hr/services/performance/okr.py:190 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-158 | logic | 03 · Logical | backend/domains/hr/services/shift/shift_roster_service.py:164 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-159 | logic | 03 · Logical | backend/domains/hr/services/travel/travel_service.py:152 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-160 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_fallback_service.py:40 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-161 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_imports_service.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-162 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_logistics_operations_service.py:18 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-163 | logic | 03 · Logical | backend/domains/logistics/services/core/logistics_engine.py:93 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-164 | logic | 03 · Logical | backend/domains/logistics/services/core/service.py:1057 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-165 | logic | 03 · Logical | backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py:33 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-166 | logic | 03 · Logical | backend/domains/logistics/services/geo/map_service.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-167 | logic | 03 · Logical | backend/domains/logistics/services/geo/routing_service.py:68 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-168 | logic | 03 · Logical | backend/domains/logistics/services/geo/service.py:452 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-169 | logic | 03 · Logical | backend/domains/logistics/services/health/service.py:63 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-170 | logic | 03 · Logical | backend/domains/logistics/services/partners/admin_logistics_operations_service.py:221 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-171 | logic | 03 · Logical | backend/domains/logistics/services/partners/logistics_partner_service.py:232 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-172 | logic | 03 · Logical | backend/domains/logistics/services/partners/logistics_pricing_service.py:62 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-173 | logic | 03 · Logical | backend/domains/logistics/services/partners/pricing_service.py:209 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-174 | logic | 03 · Logical | backend/domains/logistics/services/partners/service.py:229 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-175 | logic | 03 · Logical | backend/domains/logistics/services/partners/settlement_service.py:136 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-176 | logic | 03 · Logical | backend/domains/logistics/services/shipping/service.py:337 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-184 | logic | 03 · Logical | backend/domains/promotions/events.py:16 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-185 | logic | 03 · Logical | backend/domains/promotions/services/admin_promotion_ops_service.py:62 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-186 | logic | 03 · Logical | backend/domains/promotions/services/admin_promotion_service.py:95 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-187 | logic | 03 · Logical | backend/domains/promotions/services/coins/coin_service.py:129 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-188 | logic | 03 · Logical | backend/domains/promotions/services/coins/promotion_points_service.py:128 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-189 | logic | 03 · Logical | backend/domains/promotions/services/coupons/customer_coupons_create_service.py:29 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-190 | logic | 03 · Logical | backend/domains/promotions/services/engine/admin_commerce_configuration_service.py:47 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-191 | logic | 03 · Logical | backend/domains/promotions/services/engine/admin_promotions_write_service.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-192 | logic | 03 · Logical | backend/domains/promotions/services/engine/promotion_service.py:49 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-193 | logic | 03 · Logical | backend/domains/promotions/services/promotion_admin_write_service.py:77 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-194 | logic | 03 · Logical | backend/domains/security/services/detection/confidence_scoring.py:106 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-195 | logic | 03 · Logical | backend/domains/security/services/fraud/fraud_detection_service.py:485 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-196 | logic | 03 · Logical | backend/domains/suppliers/events.py:113 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-197 | logic | 03 · Logical | backend/domains/suppliers/services/analytics/supplier_analytics_service.py:56 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-198 | logic | 03 · Logical | backend/domains/suppliers/services/badges/badge_service.py:386 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-199 | logic | 03 · Logical | backend/domains/suppliers/services/contract/contract_service.py:52 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-200 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health.py:363 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-201 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health_engine.py:151 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-202 | logic | 03 · Logical | backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-205 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_product_service.py:47 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-206 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products.py:206 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-207 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products_service.py:120 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-208 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:119 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-210 | logic | 03 · Logical | backend/domains/suppliers/services/profile/supplier_profile.py:55 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-211 | logic | 03 · Logical | backend/domains/suppliers/services/quality/quality_control_service.py:98 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-212 | logic | 03 · Logical | backend/domains/suppliers/services/settlement/multi_currency_settlement.py:90 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-213 | logic | 03 · Logical | backend/domains/suppliers/services/supplier_shared.py:200 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-214 | logic | 03 · Logical | backend/domains/suppliers/services/tier/tier_service.py:102 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-215 | logic | 03 · Logical | backend/infrastructure/database/schemas.py:394 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-216 | logic | 03 · Logical | backend/infrastructure/database/seed/logistics.py:18 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-217 | logic | 03 · Logical | backend/infrastructure/messaging/downstream_wiring.py:128 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-218 | logic | 03 · Logical | backend/infrastructure/utils/analytics.py:69 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-219 | logic | 03 · Logical | backend/infrastructure/utils/currency_service.py:271 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-220 | logic | 03 · Logical | backend/modules/admin/routers/hr.py:32 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-221 | logic | 03 · Logical | backend/modules/admin/routers/promotions.py:165 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-222 | logic | 03 · Logical | backend/modules/admin/routers/security.py:97 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-223 | logic | 03 · Logical | backend/modules/customer/routers/catalog.py:35 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-224 | logic | 03 · Logical | backend/modules/customer/routers/comms.py:25 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-226 | logic | 03 · Logical | backend/modules/customer/routers/promotions.py:148 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-227 | logic | 03 · Logical | backend/modules/customer/serializers/customer_serializers.py:19 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-228 | logic | 03 · Logical | backend/modules/employee/routers/catalog.py:31 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-229 | logic | 03 · Logical | backend/modules/employee/routers/country.py:49 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-231 | logic | 03 · Logical | backend/modules/employee/routers/hr.py:122 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-232 | logic | 03 · Logical | backend/modules/employee/routers/hr/schemas.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-234 | logic | 03 · Logical | backend/modules/employee/routers/suppliers.py:53 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-235 | logic | 03 · Logical | backend/modules/employee/serializers/employee_serializers.py:37 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-236 | logic | 03 · Logical | backend/modules/logistics/routers/logistics.py:1014 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-237 | logic | 03 · Logical | backend/modules/supplier/routers/analytics.py:34 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-239 | logic | 03 · Logical | backend/modules/supplier/routers/logistics.py:32 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-240 | logic | 03 · Logical | backend/modules/supplier/serializers/supplier_serializers.py:19 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-241 | logic | 03 · Logical | backend/providers/ai/ai_variant_config.py:111 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-243 | logic | 03 · Logical | backend/providers/ai/price_intelligence.py:80 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-244 | logic | 03 · Logical | backend/providers/ai/recommendation.py:273 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-245 | logic | 03 · Logical | backend/providers/ai/search.py:120 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-246 | logic | 03 · Logical | backend/providers/ai/sentiment.py:215 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-247 | logic | 03 · Logical | backend/providers/bg_removal/bg_removal_service.py:678 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-248 | logic | 03 · Logical | backend/providers/geography/rates.py:177 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-249 | logic | 03 · Logical | backend/providers/image/free_image_tools.py:811 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-250 | logic | 03 · Logical | backend/providers/image/ocr.py:236 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-251 | logic | 03 · Logical | backend/providers/ocr/ocr_parser.py:178 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-255 | logic | 03 · Logical | backend/providers/qr/qr_generator.py:103 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-256 | logic | 03 · Logical | backend/providers/shipping/shipping_calculator.py:416 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |
| LOGIC-257 | logic | 03 · Logical | backend/providers/voice/voice_to_text.py:167 | Convert to Decimal and use kernel.money rounding helpers | M | 4 | partial |


### P2 — 114 finding(s)

| ID | Phase | Dimension | File:Line | Fix | Effort | Conf | Blocker |
|---|---|---|---|---|---|---|---|
| ARCH-004 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-005 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-006 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-007 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-008 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-009 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-010 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-011 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-012 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-013 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-014 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-015 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-016 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-017 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-018 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-019 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-020 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-021 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-022 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| ARCH-023 | arch | 01 · Architectural | backend/DOMAIN_ALLOWLIST.yaml:1 | Add the removal date or remove the entry | M | 4 | no |
| MIG-002 | db | 10 · Migrations | backend/alembic/versions/2026_08_08_21_02-02ebc285f66f_merge_divergent_heads_20260806_0009_and_.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| MIG-003 | db | 10 · Migrations | backend/alembic/versions/2026_08_21_0005-20260821_crosscutting_domains.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| MIG-004 | db | 10 · Migrations | backend/alembic/versions/2026_08_21_0006-20260821_customer_comm_logistics_media.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| MIG-005 | db | 10 · Migrations | backend/alembic/versions/2026_08_21_0007-20260821_user_referral_to_customer.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| MIG-010 | db | 10 · Migrations | backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| MIG-012 | db | 10 · Migrations | backend/alembic/versions/2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py:1 | Implement downgrade() or document irreversibility | S | 3 | no |
| LOGIC-002 | logic | 03 · Logical | backend/infrastructure/utils/schema_audit.py:67 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-003 | logic | 03 · Logical | backend/domains/accounts/services/auth/auth_service.py:3044 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-004 | logic | 03 · Logical | backend/domains/logistics/services/core/service.py:1439 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-007 | logic | 03 · Logical | backend/domains/orders/services/core/logistics.py:284 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-008 | logic | 03 · Logical | backend/domains/orders/services/core/order_engine.py:211 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-011 | logic | 03 · Logical | backend/middleware/webhook_verification.py:242 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-012 | logic | 03 · Logical | backend/providers/image/ocr.py:95 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-013 | logic | 03 · Logical | backend/domains/catalog/services/commission_service.py:54 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-014 | logic | 03 · Logical | backend/domains/catalog/services/products/products_service.py:126 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-015 | logic | 03 · Logical | backend/domains/comms/services/public_comms_status_service.py:283 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-016 | logic | 03 · Logical | backend/domains/customers/services/public_comms_status_service.py:276 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-017 | logic | 03 · Logical | backend/domains/logistics/services/partners/partner_service.py:73 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-019 | logic | 03 · Logical | backend/infrastructure/database/schemas.py:1104 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-021 | logic | 03 · Logical | backend/middleware/country_context.py:245 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-022 | logic | 03 · Logical | backend/modules/customer/routers/orders.py:160 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-023 | logic | 03 · Logical | backend/domains/comms/services/system_comms_status_service.py:84 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-024 | logic | 03 · Logical | backend/domains/customers/services/coins/zozi_coins_service.py:130 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-027 | logic | 03 · Logical | backend/domains/governance/services/command_center/command_center_service.py:307 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-028 | logic | 03 · Logical | backend/domains/hr/services/payroll/payroll_service.py:97 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-029 | logic | 03 · Logical | backend/domains/logistics/services/partners/admin_logistics_operations_service.py:355 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-030 | logic | 03 · Logical | backend/domains/logistics/services/partners/service.py:508 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-031 | logic | 03 · Logical | backend/domains/logistics/services/sla/service.py:55 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-033 | logic | 03 · Logical | backend/infrastructure/database/rls_interceptor.py:174 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-034 | logic | 03 · Logical | backend/infrastructure/messaging/ws_manager.py:91 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-035 | logic | 03 · Logical | backend/infrastructure/messaging/events/event_bus.py:113 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-036 | logic | 03 · Logical | backend/infrastructure/observability/provider_observability.py:22 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-037 | logic | 03 · Logical | backend/infrastructure/utils/analytics.py:57 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-038 | logic | 03 · Logical | backend/infrastructure/utils/pagination.py:31 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-039 | logic | 03 · Logical | backend/infrastructure/utils/performance_cache.py:110 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-040 | logic | 03 · Logical | backend/infrastructure/utils/websocket_manager.py:91 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-041 | logic | 03 · Logical | backend/modules/admin/routers/comms.py:150 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-042 | logic | 03 · Logical | backend/providers/observability.py:24 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-043 | logic | 03 · Logical | backend/providers/ai/huggingface.py:78 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-044 | logic | 03 · Logical | backend/providers/ai/image_ai_service.py:231 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-045 | logic | 03 · Logical | backend/providers/ai/text.py:281 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-048 | logic | 03 · Logical | backend/providers/scanner/scanner.py:95 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-049 | logic | 03 · Logical | backend/config.py:895 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-050 | logic | 03 · Logical | backend/lifespan.py:293 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-051 | logic | 03 · Logical | backend/main.py:199 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-053 | logic | 03 · Logical | backend/domains/catalog/services/search/search_service.py:212 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-054 | logic | 03 · Logical | backend/domains/comms/services/notification_gateway.py:166 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-055 | logic | 03 · Logical | backend/domains/comms/services/email/email_management.py:454 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-056 | logic | 03 · Logical | backend/domains/comms/services/messaging/websocket_handlers.py:281 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-057 | logic | 03 · Logical | backend/domains/country/services/core/country_config_version_service.py:218 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-058 | logic | 03 · Logical | backend/domains/country/services/core/country_service.py:191 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-059 | logic | 03 · Logical | backend/domains/country/services/cross_border/cross_border_service.py:70 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-060 | logic | 03 · Logical | backend/domains/country/services/research/country_ai_research.py:480 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-061 | logic | 03 · Logical | backend/domains/customers/services/search_service.py:232 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-065 | logic | 03 · Logical | backend/domains/governance/services/command_center/service.py:43 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-066 | logic | 03 · Logical | backend/domains/hr/services/performance/okr.py:120 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-067 | logic | 03 · Logical | backend/domains/hr/services/performance/reviews.py:85 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-068 | logic | 03 · Logical | backend/domains/logistics/services/core/logistics_engine.py:126 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-069 | logic | 03 · Logical | backend/domains/logistics/services/core/zone_service.py:28 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-070 | logic | 03 · Logical | backend/domains/logistics/services/partners/contract_service.py:168 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-071 | logic | 03 · Logical | backend/domains/orders/services/returns/service.py:67 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-072 | logic | 03 · Logical | backend/domains/orders/services/tracking/service.py:362 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-073 | logic | 03 · Logical | backend/domains/promotions/services/coupons/coupon_service.py:527 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-079 | logic | 03 · Logical | backend/infrastructure/database/database_service.py:188 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-080 | logic | 03 · Logical | backend/infrastructure/messaging/realtime.py:599 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-081 | logic | 03 · Logical | backend/infrastructure/ml/worker.py:92 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-082 | logic | 03 · Logical | backend/infrastructure/observability/audit.py:323 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-083 | logic | 03 · Logical | backend/infrastructure/observability/service_observability.py:132 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-085 | logic | 03 · Logical | backend/middleware/webhook_ip_whitelist.py:424 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-087 | logic | 03 · Logical | backend/providers/comms/whatsapp_selfhosted.py:148 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-089 | logic | 03 · Logical | backend/providers/geography/geo.py:108 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-090 | logic | 03 · Logical | backend/providers/image/free_image_tools.py:288 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-091 | logic | 03 · Logical | backend/providers/image/parcel_verification.py:510 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-092 | logic | 03 · Logical | backend/providers/image/bg_remover/br_05__clean_edge_refiner.py:35 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-093 | logic | 03 · Logical | backend/providers/image/bg_remover/br_06__precision_geometry_classes.py:237 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-094 | logic | 03 · Logical | backend/providers/image/bg_remover/core_i_o.py:155 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-095 | logic | 03 · Logical | backend/providers/image/bg_remover/public_api.py:302 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-096 | logic | 03 · Logical | backend/providers/image/bg_remover/session_management.py:113 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-097 | logic | 03 · Logical | backend/providers/ocr/ocr_parser.py:44 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| LOGIC-099 | logic | 03 · Logical | backend/rbac/catalog.py:33 | Add logger.warning(..., exc_info=True) or re-raise | M | 4 | no |
| ARCH-218 | arch | 01 · Architectural | backend/modules/admin/routers/permissions.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-220 | arch | 01 · Architectural | backend/modules/admin/routers/staff.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-221 | arch | 01 · Architectural | backend/modules/customer/routers/accounts.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-222 | arch | 01 · Architectural | backend/modules/customer/routers/promotions.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-224 | arch | 01 · Architectural | backend/modules/employee/routers/comms.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-225 | arch | 01 · Architectural | backend/modules/employee/routers/finance.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-226 | arch | 01 · Architectural | backend/modules/employee/routers/hr.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-227 | arch | 01 · Architectural | backend/modules/employee/routers/orders.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-228 | arch | 01 · Architectural | backend/modules/employee/routers/hr/schemas.py:1 | Delete or convert to a service module | M | 4 | no |
| ARCH-229 | arch | 01 · Architectural | backend/modules/employee/routers/hr/schemas_admin.py:1 | Delete or convert to a service module | M | 4 | no |
| ARCH-230 | arch | 01 · Architectural | backend/modules/finance/routers/cash_management.py:1 | Delete or convert to a service module | M | 4 | no |
| ARCH-231 | arch | 01 · Architectural | backend/modules/logistics/routers/accounts.py:1 | Extract branching logic into the domain service | M | 4 | no |
| ARCH-232 | arch | 01 · Architectural | backend/modules/logistics/routers/logistics.py:1 | Extract branching logic into the domain service | M | 4 | no |
| LOGIC-319 | logic | 03 · Logical | backend/domains/accounts/models/core.py:58 | Link each TODO to a ticket or delete it | M | 4 | no |


### P3 — 61 finding(s)

| ID | Phase | Dimension | File:Line | Fix | Effort | Conf | Blocker |
|---|---|---|---|---|---|---|---|
| LOGIC-258 | logic | 03 · Logical | backend/domains/finance/services/ledger/general_ledger.py:62 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-259 | logic | 03 · Logical | backend/domains/orders/services/core/logistics.py:273 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-260 | logic | 03 · Logical | backend/domains/suppliers/services/health/supplier_health.py:73 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-261 | logic | 03 · Logical | backend/domains/finance/services/payouts/payout_batch_service.py:50 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-262 | logic | 03 · Logical | backend/domains/accounts/services/auth/auth_service.py:396 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-263 | logic | 03 · Logical | backend/domains/accounts/services/users/user_management_service.py:317 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-264 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_engine.py:2054 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-265 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_tap.py:81 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-266 | logic | 03 · Logical | backend/domains/logistics/services/partners/service.py:394 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-267 | logic | 03 · Logical | backend/domains/orders/services/core/order_engine.py:304 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-268 | logic | 03 · Logical | backend/domains/catalog/services/search/search_service.py:306 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-269 | logic | 03 · Logical | backend/domains/country/services/core/country_service.py:183 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-270 | logic | 03 · Logical | backend/domains/customers/services/search_service.py:326 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-271 | logic | 03 · Logical | backend/domains/finance/services/data_import_service.py:90 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-272 | logic | 03 · Logical | backend/domains/logistics/services/core/shipment_service.py:305 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-273 | logic | 03 · Logical | backend/domains/logistics/services/partners/logistics_pricing_service.py:51 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-274 | logic | 03 · Logical | backend/infrastructure/database/seed/_common.py:328 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-275 | logic | 03 · Logical | backend/providers/image/parcel_verification.py:64 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-276 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_stripe.py:64 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-277 | logic | 03 · Logical | backend/domains/orders/services/orders_service.py:58 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-278 | logic | 03 · Logical | backend/domains/orders/services/core/order_admin.py:5 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-279 | logic | 03 · Logical | backend/domains/orders/services/tracking/service.py:401 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-280 | logic | 03 · Logical | backend/domains/suppliers/services/supplier_shared.py:196 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-281 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders.py:35 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-282 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_products.py:142 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-283 | logic | 03 · Logical | backend/infrastructure/messaging/email_service.py:96 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-284 | logic | 03 · Logical | backend/infrastructure/utils/schema_audit.py:327 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-285 | logic | 03 · Logical | backend/providers/ai/ai_variant_config.py:497 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-286 | logic | 03 · Logical | backend/config.py:359 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-287 | logic | 03 · Logical | backend/domains/catalog/services/ai_upload_service.py:76 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-288 | logic | 03 · Logical | backend/domains/comms/services/messaging/chat_service.py:153 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-289 | logic | 03 · Logical | backend/domains/finance/services/payments/gateway_paypal.py:39 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-290 | logic | 03 · Logical | backend/domains/finance/services/payments/payment_orchestrator.py:451 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-291 | logic | 03 · Logical | backend/domains/hr/services/employees/hr_service.py:401 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-292 | logic | 03 · Logical | backend/domains/logistics/services/core/service.py:1479 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-293 | logic | 03 · Logical | backend/domains/logistics/services/partners/partner_service.py:62 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-294 | logic | 03 · Logical | backend/domains/orders/services/returns/service.py:265 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-295 | logic | 03 · Logical | backend/domains/suppliers/services/orders/supplier_orders_service.py:51 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-296 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_product_service.py:43 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-297 | logic | 03 · Logical | backend/infrastructure/messaging/realtime.py:365 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-298 | logic | 03 · Logical | backend/providers/image/free_image_tools.py:160 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-299 | logic | 03 · Logical | backend/providers/payments/paypal.py:176 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-300 | logic | 03 · Logical | backend/providers/payments/paytabs.py:77 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-301 | logic | 03 · Logical | backend/domains/accounts/services/gdpr_service.py:74 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-302 | logic | 03 · Logical | backend/domains/analytics/services/dashboards/analytics_service.py:91 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-303 | logic | 03 · Logical | backend/domains/catalog/services/products/products_service.py:204 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-304 | logic | 03 · Logical | backend/domains/comms/services/email/email_gateway.py:371 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-305 | logic | 03 · Logical | backend/domains/comms/services/shared/chat_threads_query.py:19 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-306 | logic | 03 · Logical | backend/domains/country/services/research/country_heuristic_engine.py:173 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-307 | logic | 03 · Logical | backend/domains/finance/services/trading_service.py:99 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-308 | logic | 03 · Logical | backend/domains/finance/services/country/supplier_finance_service.py:97 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-309 | logic | 03 · Logical | backend/domains/governance/services/command_center/background.py:297 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-310 | logic | 03 · Logical | backend/domains/governance/services/command_center/command_center_service.py:478 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-311 | logic | 03 · Logical | backend/domains/logistics/services/core/admin_service.py:78 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-312 | logic | 03 · Logical | backend/domains/promotions/services/coins/promotion_points_service.py:106 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-313 | logic | 03 · Logical | backend/domains/promotions/services/engine/admin_promotions_write_service.py:151 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-314 | logic | 03 · Logical | backend/domains/promotions/services/engine/promotion_service.py:119 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-315 | logic | 03 · Logical | backend/domains/security/services/fraud/fraud_detection_service.py:96 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-316 | logic | 03 · Logical | backend/domains/suppliers/services/products/supplier_supplier_upload_service.py:32 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-317 | logic | 03 · Logical | backend/infrastructure/observability/retry.py:27 | Split the longest functions by responsibility | M | 4 | no |
| LOGIC-318 | logic | 03 · Logical | backend/lifespan.py:232 | Refactor with guard clauses / extracted helpers | M | 4 | no |


### KEEP / HARDEN (all six criteria required)

### KEEP / HARDEN

_None qualified._
---
## Appendix A · Tool-run ledger

| Tool | Command | Status | Exit | Duration | Notes |
|---|---|---|---|---|---|
| git:rev | git rev-parse HEAD | PASS | 0 | 0.08s | — |
| git:status | git status --porcelain | PASS | 0 | 0.22s | — |

---
## Appendix B · Coverage & method

**Method.** The audit walks the repository (excluding `.git`, `.kilo`, `node_modules`, caches and build output), parses Python with `ast` and TypeScript/JSON/YAML/SQL/TOML with textual analysers, parses the benchmark documents at runtime, and runs each finding-producing check as an independent task in a bounded pool (max 10 concurrent).

**Static-only findings** are marked `truth_level=L0` (source) or `L1` (evidence). Runtime claims are only made when a tool run succeeded; otherwise the item is `unverifiable` with the command that would verify it.

| Dimension | Findings | Files cited | Yes-blockers |
|---|---|---|---|
| 01_architectural | 232 | 146 | 1 |
| 02_technological | 0 | 0 | 0 |
| 03_logical | 329 | 236 | 44 |
| 04_operational | 0 | 0 | 0 |
| 05_wiring | 0 | 0 | 0 |
| 06_database | 0 | 0 | 0 |
| 07_tables_fields | 0 | 0 | 0 |
| 08_providers | 0 | 0 | 0 |
| 09_laws | 0 | 0 | 0 |
| 10_migrations | 12 | 12 | 0 |
| 11_environmental | 0 | 0 | 0 |
| 12_tests | 0 | 0 | 0 |
| 13_dev_to_prod | 0 | 0 | 0 |
| 14_frontend_web | 0 | 0 | 0 |
| 15_frontend_mobile | 0 | 0 | 0 |
| 16_features | 0 | 0 | 0 |
| 17_code_file_management | 0 | 0 | 0 |
| 18_security | 0 | 0 | 0 |
| 19_performance | 0 | 0 | 0 |
| 20_observability_resilience | 0 | 0 | 0 |
| 21_contradictions | 0 | 0 | 0 |
| 22_anti_patterns | 0 | 0 | 0 |
| 23_code_intent | 0 | 0 | 0 |
| 24_browser_behavior | 0 | 0 | 0 |
| 25_ai_drift | 0 | 0 | 0 |
| 26_code_alignment | 0 | 0 | 0 |
| 27_project_completion_blockers | 1 | 1 | 1 |
| 28_supply_chain_security | 0 | 0 | 0 |


Observations recorded: **101** (full stream: `logs/observations.jsonl`).

All registered checks completed without crashing.

**Explicit exclusions:** `.git/`, `.kilo/` (nested worktrees), `node_modules/`, `__pycache__/`, `.next/`, `dist/`, `build/`, `_extra_files/`, `_legacy.bak/`, binary/media/sqlite artifacts.

**What this audit does NOT do:** it does not compile findings, does not resolve them, does not modify source files, and does not treat the prior `_audit/**` corpus as ground truth — prior findings are re-verified or reported as not-found.
---
## Appendix C · Auditor self-check

| Check | Dimension | Findings | Observations | Duration | Status |
|---|---|---|---|---|---|
| arch_allowlist | 01_architectural | 20 | 1 | 0.22s | ok |
| arch_domain_structure | 01_architectural | 0 | 0 | 0.17s | ok |
| arch_extra_units | 01_architectural | 3 | 0 | 0.17s | ok |
| arch_import_direction | 01_architectural | 214 | 0 | 28.54s | ok |
| arch_router_thinness | 01_architectural | 15 | 100 | 32.94s | ok |
| db_migration_graph | 10_migrations | 12 | 0 | 3.18s | ok |
| logic_blocking_io | 03_logical | 0 | 0 | 25.79s | ok |
| logic_idempotency | 03_logical | 10 | 0 | 48.23s | ok |
| logic_money_type | 03_logical | 158 | 0 | 44.3s | ok |
| logic_quality | 03_logical | 62 | 0 | 45.83s | ok |
| logic_silent_excepts | 03_logical | 99 | 0 | 32.0s | ok |
| preflight_architecture_tests | 12_tests | 0 | 0 | s | ok |
| preflight_boot | 27_project_completion_blockers | 0 | 0 | s | ok |
| preflight_db | 06_database | 0 | 0 | s | ok |
| preflight_env | 11_environmental | 0 | 0 | s | ok |
| preflight_lint | 02_technological | 0 | 0 | s | ok |
| preflight_lockfiles | 02_technological | 0 | 0 | s | ok |
| preflight_migrations | 10_migrations | 0 | 0 | s | ok |
| preflight_tests | 12_tests | 0 | 0 | s | ok |
| preflight_tsc | 14_frontend_web | 0 | 0 | s | ok |
| preflight_valkey | 04_operational | 1 | 0 | s | ok |


---

_Report generated by `_zozi_audit/zozi_audit.py` — run `20261002T203716Z-9d68f1` — 2026-10-02T20:38:10.170916+00:00._

_For the ordered, executable remediation plan derived from this report, run `python _zozi_audit/zozi_compile.py` → `_zozi_audit/zozi_remediation_plan.md`._
