# RESOLVER PLAN

Generated: 2026-10-02T00:00:00Z
Time-box: Day 1 → Day 9 (dispatch freeze) → Day 10 (final loop-back)

## Phase execution order

Files are processed in phase order. A file cannot be resolved until its
dependencies are resolved.

### Phase emergency (Day 1)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-2 | backend/__init__.py | — | 1 | 1h |
| 2 | FILE-1 | backend/.env | — | 1 | 1h |
| 3 | FILE-3 | backend/health_test_*.py | — | 1 | 2h |
| 4 | FILE-4 | backend/run_tests.ps1, run_tests.sh | — | 1 | 1h |
| 5 | FILE-5 | backend/uv.lock | — | 1 | 1h |
| 6 | FILE-6 | backend/Dockerfile | — | 5 | 2h |

### Phase boot (Day 2–3)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-8 | backend/config.py | FILE-2 | 19 | 4h |
| 2 | FILE-7 | backend/main.py | FILE-2 | 2 | 2h |
| 3 | FILE-9 | backend/alembic/versions/* | — | 2 | 4h |
| 4 | FILE-10 | backend/tests (collection errors) | FILE-2 | 3 | 2h |

### Phase tech (Day 3)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-11 | backend/requirements.txt | — | 14 | 4h |
| 2 | FILE-12 | .github/workflows/ci.yml | — | 1 | 1h |
| 3 | FILE-13 | backend/providers/payments/paypal.py | — | 2 | 2h |
| 4 | FILE-14 | backend/infrastructure/observability/metrics.py | — | 1 | 1h |
| 5 | FILE-15 | backend/infrastructure/valkey/client.py | — | 1 | 1h |
| 6 | FILE-16 | frontend/web_app/package.json | — | 9 | 2h |
| 7 | FILE-17 | frontend/mobile_app/package.json | — | 5 | 2h |
| 8 | FILE-18 | frontend/web_app/Dockerfile | — | 2 | 1h |

### Phase db (Day 3–4)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-19 | backend/domains/comms/models/communication.py | — | 25 | 4h |
| 2 | FILE-20 | backend/domains/comms/models/chat.py | — | 9 | 2h |
| 3 | FILE-21 | backend/domains/finance/models/general_ledger.py | — | 41 | 4h |
| 4 | FILE-22 | backend/domains/security/models/fraud.py | — | 27 | 4h |
| 5 | FILE-23 | backend/domains/comms/models/communication_schema_models.py | — | 16 | 2h |
| 6 | FILE-24 | backend/domains/comms/models/marketing.py | — | 14 | 2h |
| 7 | FILE-25 | backend/domains/comms/models/incident.py | — | 6 | 1h |
| 8 | FILE-26 | backend/domains/comms/models/fraud.py | — | 1 | 1h |
| 9 | FILE-27 | backend/domains/comms/models/message.py | — | 1 | 1h |
| 10 | FILE-28 | backend/domains/comms/models/news.py | — | 1 | 1h |
| 11 | FILE-29 | backend/domains/country/models/countries.py | — | 3 | 1h |
| 12 | FILE-30 | backend/domains/country/models/country_basics.py | — | 1 | 1h |
| 13 | FILE-31 | backend/domains/country/models/country_control.py | — | 8 | 2h |
| 14 | FILE-32 | backend/domains/country/models/country_economics.py | — | 1 | 1h |
| 15 | FILE-33 | backend/domains/country/models/country_enhancements.py | — | 16 | 2h |
| 16 | FILE-34 | backend/domains/country/models/country_legal.py | — | 1 | 1h |
| 17 | FILE-35 | backend/domains/country/models/country_tax.py | — | 1 | 1h |
| 18 | FILE-36 | backend/domains/customers/models/cross_country_session.py | — | 2 | 1h |
| 19 | FILE-37 | backend/domains/customers/models/customer_schema_models.py | — | 2 | 1h |
| 20 | FILE-38 | backend/domains/finance/models/commission.py | — | 4 | 1h |
| 21 | FILE-39 | backend/domains/finance/models/payments.py | — | 2 | 2h |
| 22 | FILE-40 | backend/domains/finance/models/tax_rules.py | — | 4 | 1h |
| 23 | FILE-41 | backend/domains/governance/models/admin.py | — | 2 | 1h |
| 24 | FILE-42 | backend/domains/hr/models/employee_models.py | — | 6 | 1h |
| 25 | FILE-43 | backend/domains/logistics/models/logistics_entities.py | — | 8 | 2h |
| 26 | FILE-44 | backend/domains/logistics/models/logistics_schema_models.py | — | 1 | 1h |
| 27 | FILE-45 | backend/domains/logistics/models/shipping_rules.py | — | 1 | 1h |
| 28 | FILE-46 | backend/domains/media/models/media_asset.py | — | 1 | 1h |
| 29 | FILE-47 | backend/domains/orders/models/order_entities.py | — | 7 | 2h |
| 30 | FILE-48 | backend/domains/promotions/models/coupon_usage.py | — | 1 | 1h |
| 31 | FILE-49 | backend/domains/promotions/models/promotion_config.py | — | 1 | 1h |
| 32 | FILE-50 | backend/domains/suppliers/models/suppliers.py | — | 10 | 2h |
| 33 | FILE-51 | backend/domains/accounts/models/user.py | — | 3 | 1h |
| 34 | FILE-52 | backend/domains/catalog/models/products.py | — | 5 | 2h |
| 35 | FILE-53 | backend/domains/catalog/models/upload_job.py | — | 1 | 1h |

### Phase logic (Day 4–6)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-54 | backend/domains/finance/services/finance_service.py | FILE-8 | 2 | 2h |
| 2 | FILE-55 | backend/domains/orders/services/orders_service.py | FILE-8 | 1 | 1h |
| 3 | FILE-56 | backend/modules/customer/routers/orders.py | FILE-8 | 4 | 2h |
| 4 | FILE-57 | backend/domains/finance/subscribers.py | FILE-54 | 1 | 4h |
| 5 | FILE-58 | backend/domains/orders/services/returns/service.py | FILE-55 | 1 | 2h |
| 6 | FILE-59 | backend/domains/finance/services/payments/payment_engine.py | FILE-8 | 3 | 2h |
| 7 | FILE-60 | backend/domains/catalog/services/products/products_service.py | — | 3 | 2h |
| 8 | FILE-61 | backend/domains/orders/services/core/order_engine.py | FILE-55 | 1 | 1h |
| 9 | FILE-62 | backend/domains/logistics/services/core/service.py | — | 1 | 1h |
| 10 | FILE-63 | backend/domains/security/services/fraud/fraud_detection_service.py | — | 1 | 2h |

### Phase arch (Day 6–8)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-64 | backend/domains/finance/ports.py | — | 2 | 4h |
| 2 | FILE-65 | backend/middleware/dependencies/auth.py | — | 1 | 2h |
| 3 | FILE-66 | backend/middleware/dependencies/country_detection.py | — | 1 | 1h |
| 4 | FILE-67 | backend/modules/admin/routers/finance.py | — | 1 | 1h |
| 5 | FILE-68 | backend/modules/customer/routers/catalog.py | — | 1 | 2h |
| 6 | FILE-69 | backend/modules/supplier/routers/accounts.py | — | 1 | 2h |
| 7 | FILE-70 | backend/modules/logistics/routers/finance.py | — | 1 | 1h |
| 8 | FILE-71 | backend/modules/finance/__init__.py | — | 2 | 2h |
| 9 | FILE-72 | backend/domains/payments/__init__.py | — | 1 | 2h |
| 10 | FILE-73 | backend/domains/media/ | — | 1 | 2h |
| 11 | FILE-74 | backend/modules/admin/routers/orders.py | — | 3 | 2h |
| 12 | FILE-75 | backend/modules/admin/routers/permissions.py | — | 1 | 1h |
| 13 | FILE-76 | backend/modules/customer/routers/accounts.py | — | 1 | 1h |
| 14 | FILE-77 | backend/modules/customer/routers/promotions.py | — | 1 | 1h |
| 15 | FILE-78 | backend/modules/supplier/routers/audit.py | — | 2 | 1h |
| 16 | FILE-79 | backend/providers/comms/sms.py | — | 1 | 1h |
| 17 | FILE-80 | backend/providers/geography/geo.py | — | 1 | 1h |
| 18 | FILE-81 | backend/providers/payments/config.py | — | 1 | 1h |
| 19 | FILE-82 | backend/providers/news/, automation/, scanner/, voice/, analytics/ | — | 1 | 2h |

### Phase security (Day 8)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-83 | backend/domains/finance/models/payments.py | — | 2 | 4h |
| 2 | FILE-84 | backend/rbac/models/permission_entities.py | — | 1 | 2h |
| 3 | FILE-85 | backend/infrastructure/observability/error_handler.py | — | 1 | 2h |
| 4 | FILE-86 | backend/infrastructure/observability/logging_config.py | — | 1 | 1h |
| 5 | FILE-87 | backend/infrastructure/storage/backup.py | — | 1 | 1h |

### Phase frontend (Day 1–8, parallel)
| Order | FILE | Path | Depends on | Findings | Effort |
|-------|------|------|------------|----------|--------|
| 1 | FILE-88 | frontend/web_app/src/app/admin/orders/page.tsx | — | 1 | 2h |
| 2 | FILE-89 | frontend/web_app/src/components/ProductCard.tsx | — | 1 | 1h |
| 3 | FILE-90 | frontend/web_app/src/lib/cartStore.ts | — | 1 | 2h |
| 4 | FILE-91 | frontend/web_app/src/lib/useAdminApi.ts | — | 1 | 1h |
| 5 | FILE-92 | frontend/shared/src/permissions.ts | — | 1 | 2h |
| 6 | FILE-93 | frontend/shared/src/types.ts | — | 1 | 1h |
| 7 | FILE-94 | frontend/mobile_app/lib/paymentService.ts | — | 1 | 2h |
| 8 | FILE-95 | frontend/mobile_app/lib/authStore.ts | — | 1 | 1h |
| 9 | FILE-96 | frontend/mobile_app/lib/socialAuth.ts | — | 1 | 1h |
| 10 | FILE-97 | frontend/mobile_app/android/app/src/main/AndroidManifest.xml | — | 1 | 1h |
| 11 | FILE-98 | frontend/mobile_app/app/_layout.tsx | — | 1 | 1h |
| 12 | FILE-99 | frontend/mobile_app/lib/api.ts | — | 1 | 1h |
| 13 | FILE-100 | frontend/mobile_app/e2e/ | — | 1 | 2h |
| 14 | FILE-101 | frontend/web_app/src/ (TS errors) | — | 1 | 4h |
| 15 | FILE-102 | frontend/web_app/next.config.ts | — | 1 | 1h |
| 16 | FILE-103 | frontend/web_app/e2e/ | — | 1 | 2h |
| 17 | FILE-104 | frontend/mobile_app/package.json + pnpm-lock.yaml | — | 7 | 2h |
| 18 | FILE-105 | frontend/shared/src/permissions.ts + types.ts | — | 2 | 2h |

### Phase defer (Day 10)
| FILE | Path | Reason |
|------|------|--------|
