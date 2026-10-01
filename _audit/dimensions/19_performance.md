# Performance Audit Report

| Check | Status | File(s) | Line(s) | Severity | Notes |
|-------|--------|---------|---------|----------|-------|
| 1. N+1 queries — relationship loading | NEW | `backend/domains/security/models/security_schema_models.py`, `backend/domains/security/models/fraud.py`, `backend/domains/orders/models/order_entities.py`, `backend/domains/suppliers/models/suppliers.py`, `backend/domains/finance/models/payments.py`, `backend/domains/logistics/models/logistics_entities.py`, `backend/domains/governance/models/admin.py` | Multiple | HIGH | Many `relationship()` declarations omit `lazy="selectin"`; default lazy loading will trigger N+1 queries when collections or scalars are accessed in service loops. |
| 2. SELECT * in queries | NEW | `backend/domains/comms/services/email/email_management.py:460`, `backend/domains/comms/services/shared/chat_threads_query.py:29` | 2 | LOW | Two raw-SQL `SELECT * FROM (...)` occurrences found; application-layer queries generally use explicit columns. |
| 3. Missing indexes on FK columns | NEW | `backend/domains/payments/models/payment_models.py` (payment_methods.user_id, payment_intents.order_id have `index=True`; refunds.payment_id indexed) | — | LOW | Scanned models show most FK columns carry explicit `index=True`. No large missing-index gaps detected in sampled models. |
| 4. OFFSET on hot lists | PARTIAL | `backend/domains/catalog/services/search/search_service.py:1102`, `backend/domains/catalog/services/products/products_service.py:806`, `backend/domains/orders/services/admin_orders_service.py:49`, `backend/domains/comms/services/email/email_gateway.py:349`, `backend/domains/logistics/services/partners/service.py:2087`, `backend/domains/finance/services/payouts/payout_batch_service.py:2587,2887,4035,4090,4114,4162,4190,4204`, `backend/domains/audit/services/logs/audit_query_service.py:101`, `backend/domains/accounts/services/users/user_management_service.py:1138,1170` | 25+ | HIGH | OFFSET pagination is still used on hot list endpoints (products, orders, payouts, audit logs, messages, admin bank accounts) despite keyset-pagination helpers existing in `accounts/ports.py`, `hr/ports.py`, `logistics/ports.py`, `security/ports.py`. `backend/modules/admin/routers/accounts.py:77` passes `offset=(page - 1) * page_size` to service; actual SQL `.offset()` is in service layer (FILE-129 — AUDIT_CLAIM_WRONG: finding misidentifies location; fix requires service-layer changes outside contract scope). `backend/modules/customer/routers/catalog.py:59` passes `offset=offset` to `get_products()`; actual SQL `.offset()` is in `products_service.py:277` (FILE-134 — AUDIT_CLAIM_WRONG: same misattribution pattern; router is thin, service-layer offset is documented and cached). Admin bank accounts offset is out of scope for current contract. |
| 5. Cache strategy — Valkey hit ratio / TTL / invalidation | NEW | `backend/infrastructure/utils/cache.py` (no-op), `backend/infrastructure/utils/performance_cache.py` (real), services importing from no-op | — | CRITICAL | **Production cache is non-functional.** `infrastructure/utils/cache.py` is a no-op shim, yet services import `cache_get_json`, `cache_set_json`, `cache_or_compute` from it: `catalog/services/search/search_service.py`, `customers/services/search_service.py`, `customers/services/recommendations/recommendation_service.py`, `catalog/services/coc_service.py`, `domains/_parked/orders_package_service.py`, `accounts/services/auth/auth_service.py`, `suppliers/services/supplier_shared.py`, `promotions/services/banners/banner_service.py`, `analytics/services/dashboards/analytics_service.py`. Real Valkey-backed helpers exist in `performance_cache.py` but are not used by these services. |
| 6. CDN caching headers | NEW | `backend/domains/catalog/services/products/products_service.py:62,833`, `backend/domains/catalog/services/search/search_service.py:492,530`, `backend/domains/customers/services/search_service.py:604`, `backend/middleware/security_headers.py:26,126` | 4 | MEDIUM | `Cache-Control: public, max-age=30, stale-while-revalidate=60` is set on public catalog/search endpoints; security middleware sets `no-store` for sensitive paths. CDN caching is present but short-TTL (30s). |
| 7. Bundle size — chunks > 200KB | NEW | `frontend/web_app/.next/` | — | HIGH | **Cannot verify.** No `.next` build output directory was found in the workspace. Bundle analysis is blocked until a production build is generated. |
| 8. Image optimization — next/image, WebP/AVIF, lazy, blur | NEW | `frontend/web_app/src/components/ProductCard.tsx:65`, `frontend/web_app/src/app/products/[id]/page.tsx:252-253`, `frontend/web_app/src/app/checkout/page.tsx:743`, `frontend/web_app/src/app/cart/page.tsx:143`, `frontend/web_app/next.config.ts:6-17` | Multiple | MEDIUM | `next/image` is used extensively and `next.config.ts` enables WebP. However, blur placeholders / `placeholder="blur"` are not observed in the sampled components, and many product images are rendered via resolved URLs without explicit `loading="lazy"` props on non-Next `<img>` tags. |
| 9. Async processing — Celery / async_workers | NEW | `backend/jobs/celery_app.py`, `backend/jobs/async_workers.py`, `backend/jobs/video_tasks.py`, `backend/jobs/periodic_tasks.py`, `backend/jobs/email_tasks.py`, `backend/jobs/reconciliation_cron.py`, `backend/jobs/data_retention.py`, `backend/jobs/payroll_run.py`, `backend/jobs/fx_revaluation.py` | — | PASS | CPU-bound provider work is correctly routed through `jobs.async_workers` via `asyncio.to_thread` + bounded `ThreadPoolExecutor`. Celery queues are separated by domain (ml, periodic, payouts, emails). |
| 10. No blocking I/O in async handlers | RESOLVED | `backend/jobs/async_workers.py:62-71` | 1 | PASS | Blocking provider calls are wrapped in `loop.run_in_executor(_executor, ...)` with `asyncio.wait_for(..., timeout=TASK_TIMEOUT)`. No raw blocking I/O observed in async hot paths. |
| 11. Connection pool sized correctly | NEW | `backend/config.py:96-99,500`, `backend/infrastructure/database/database.py:69-85,209-216,319-334` | — | PASS | `db_pool_size=50`, `db_max_overflow=100`, `pool_recycle=1800s`, `pool_timeout=30s`. Pool sizing is documented for 100K+ concurrent users; `pool_pre_ping=True` is enabled. |
| 12. Statement timeout configured | NEW | `backend/config.py:25-43,114`, `backend/lifespan.py:298-306` | 3 | PASS | `db_statement_timeout=60000` ms. `apply_db_statement_timeout` is registered as a connect listener at boot in `lifespan.py`. |

## Summary

| Dimension | Finding |
|-----------|---------|
| N+1 queries | HIGH — widespread missing `lazy="selectin"` on cross-domain relationships |
| SELECT * | LOW — only 2 raw-SQL occurrences |
| Missing indexes | LOW — sampled models show explicit FK indexes |
| OFFSET on hot lists | HIGH — 25+ hot-list endpoints still use OFFSET despite keyset helpers; FILE-129 admin bank accounts offset is out of scope for current contract (requires service-layer edit) |
| Cache strategy | **CRITICAL — production cache is a no-op; services import the wrong module** |
| CDN headers | MEDIUM — present, short-TTL |
| Bundle size | **HIGH — cannot verify; no build output found** |
| Image optimization | MEDIUM — `next/image` + WebP enabled; blur/lazy props missing in places |
| Async processing | PASS — Celery + bounded thread-pool workers |
| Blocking I/O | PASS — executor-offloaded |
| Connection pool | PASS — sized for 100K+ users |
| Statement timeout | PASS — 60s, applied at boot |

### Project Completion Blocker

**Yes.** Two issues prevent acceptable launch UX:
1. **Cache strategy is broken** (`backend/infrastructure/utils/cache.py` is a no-op, yet hot-path services import from it). This will cause unnecessary DB load and degraded response times under production traffic.
2. **Bundle size cannot be verified** (`frontend/web_app/.next/` is absent). Without a build artifact, chunk sizes, initial JS payload, and image-optimization effectiveness are unknown.

### Recommended Remediations

1. **Fix cache imports**: Redirect services from `infrastructure.utils.cache` to `infrastructure.utils.performance_cache` (or restore the real Valkey-backed implementation in `infrastructure.utils.cache`).
2. **Add `lazy="selectin"`** to all cross-domain `relationship()` declarations missing it, especially in `security`, `fraud`, `orders`, `suppliers`, `finance/payments`, `logistics`, and `governance` models.
3. **Replace OFFSET with keyset pagination** on hot-list endpoints (products, orders, payouts, audit logs, messages) using the existing helpers in `*_ports.py`.
4. **Run a Next.js production build** and analyze `.next/analyze/` for chunks > 200KB; introduce `dynamic()` / code-splitting where needed.
5. **Add blur placeholders and lazy-load props** to `next/image` instances on product cards, lists, and below-the-fold images.
