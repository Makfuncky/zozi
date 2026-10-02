# DIMENSION: Performance

## Summary
- Confirmation: ❌
- Files inspected: 30
- Files compliant: 18
- Files with findings: 12
- Laws implicated: [L-45, L-46, L-47, L-48, L-53, L-73, L-317, L-319]
- Findings: 9
- P0: 2  P1: 3  P2: 3  P3: 1
- Clusters: 2
- Average confidence: 4/5
- Average evidence strength: multiple
- Status: NEW: 9 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 0 partial · 7 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| PERF-001 | db | COMPILED | CLUSTER-n-plus-1-lazy | backend/domains/catalog/models/products.py:107 | `cart_items = relationship("CartItem", back_populates="product")` — default `lazy="select"` | `lazy="selectin"` per Law 45 | Accessing `product.cart_items` triggers one query per product (N+1) | Add `lazy="selectin"` to the `cart_items` relationship | S (0.5h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/domains/catalog/models/products.py:101 (supplier uses lazy="selectin") | `pytest tests/domains/catalog/test_products.py -k n_plus_one` | tests/domains/catalog/test_products.py::test_no_n_plus_one_product_cart_items | revert lazy change | F-004 (cart), F-007 (checkout), CHAIN-001 | none | PERF-003 | yes |
| PERF-002 | frontend | RESOLVED | CLUSTER-n-plus-1-lazy | backend/domains/orders/models/order_entities.py:67 | `items = relationship('OrderItem', back_populates='order')` — default `lazy="select"` | `lazy="selectin"` per Law 45 | Accessing `order.items` outside `get_all_orders`/`get_orders` triggers N+1 for order lines | Add `lazy="selectin"` to the `items` relationship | S (0.5h) | P0 | 5 | multiple | L0 | VERIFIED | backend/domains/orders/models/order_entities.py:65 (user uses lazy='selectin') | `pytest tests/domains/orders/test_orders.py -k n_plus_one` | tests/domains/orders/test_orders.py::test_no_n_plus_one_order_items | revert lazy change | F-005 (order detail), F-006 (order history), CHAIN-001 | none | PERF-009 | yes |
| PERF-003 | db | COMPILED | CLUSTER-n-plus-1-lazy | backend/domains/catalog/models/products.py:108-112 | `variants` and `videos` relationships use default `lazy="select"` | `lazy="selectin"` per Law 45 | Loading product variants/videos without eager loading triggers N+1 in product detail and supplier catalog | Add `lazy="selectin"` to `variants` and `videos` relationships | S (0.5h) | P1 | 5 | multiple | L0 | VERIFIED | backend/domains/catalog/models/products.py:104 (reviews uses lazy="selectin") | `pytest tests/domains/catalog/test_products.py -k n_plus_one` | tests/domains/catalog/test_products.py::test_no_n_plus_one_product_variants | revert lazy change | F-003 (product detail), F-016 (supplier catalog), CHAIN-001 | PERF-001 | PERF-009 | no |
| PERF-004 | frontend | COMPILED |  | frontend/web_app/next.config.ts:19 | `formats: ['image/webp']` — AVIF absent | Add `'image/avif'` per TECHNOLOGY_STACK.md §12 (sharp 0.35.4 supports AVIF) | AVIF provides 20–30% smaller files than WebP; missing AVIF increases image payload and LCP | Add `'image/avif'` before `'image/webp'` in formats array | S (0.25h) | P1 | 4 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:186 (sharp 0.35.4 supports AVIF) | `cd frontend/web_app && pnpm build` | frontend/web_app/tests/next-config.test.ts | revert formats array | F-003 (product pages), F-001 (homepage LCP) | none | PERF-006 | no |
| PERF-005 | frontend | COMPILED |  | frontend/web_app/src/components/ProductCard.tsx:141-151 | `<MotionImage src={imageUrl} ... />` — no `placeholder="blur"` or `blurDataURL` | `placeholder="blur"` with `blurDataURL` per next/image best practice | Missing blur placeholder causes layout shift while image loads, increasing CLS | Add `placeholder="blur"` and generate/provide `blur_data_url` from backend | M (2h) | P1 | 4 | multiple | L0 | VERIFIED | frontend/web_app/src/app/products/[id]/page.tsx (also missing blur) | Lighthouse CLS audit | frontend/web_app/tests/cls.test.ts | remove blur props | F-003 (product listing CLS), F-017 (homepage CLS) | none | PERF-004 | no |
| PERF-006 | db | COMPILED | CLUSTER-offset-hot-list | backend/domains/catalog/services/products/products_service.py:305 | `ordered.offset(offset).limit(limit).all()` — OFFSET on customer product listing | Keyset (cursor) pagination per Law 317: "NEVER OFFSET on hot lists" | OFFSET scales O(n) — page 1000 requires scanning 1000 rows; customer product listing is the hottest path | Use keyset cursor (`Product.id < last_id`) for page 2+; cursor already implemented for `cursor` param at line 287-303 | M (2h) | P1 | 4 | multiple | L0 | VERIFIED | backend/domains/catalog/services/products/products_service.py:287-303 (cursor path exists but unused by router) | `pytest tests/domains/catalog/test_products.py -k pagination` | tests/domains/catalog/test_products.py::test_keyset_pagination | revert to offset | F-003 (product listing), F-004 (cart), CHAIN-001 | PERF-007 | PERF-009 | no |
| PERF-007 | db | COMPILED | CLUSTER-offset-hot-list | backend/domains/orders/services/core/order_engine.py:1009 | `orders.offset(skip)` — OFFSET in customer order history when cursor not provided | Keyset cursor per Law 317 | Customer order history uses OFFSET pagination; at 1000+ orders, latency degrades | Use keyset cursor as default; OFFSET only as backward-compat fallback | S (1h) | P2 | 4 | single | L0 | VERIFIED | backend/domains/orders/services/core/order_engine.py:1006-1007 (cursor branch exists) | `pytest tests/domains/orders/test_orders.py -k pagination` | tests/domains/orders/test_orders.py::test_order_cursor_pagination | revert to offset | F-005 (order history) | PERF-006 | PERF-009 | no |
| PERF-008 | db | INVALID |  | backend/domains/catalog/services/products/products_service.py:248 | `Product.name.ilike(f"%{q}%")` — leading wildcard prevents btree index use; pg_trgm not used | `pg_trgm` similarity search or `gin` index on `name` per TECHNOLOGY_STACK.md §2 (pg_trgm is PG 18 built-in) | Leading wildcard `%q%` forces sequential scan on products table; pg_trgm extension available but unused for catalog search | Create GIN index on `catalog.products.name` using `pg_trgm`; replace `ilike` with `name.op(' %> ')(q)` or keep `ilike` with GIN support | M (2h) | P2 | 3 | single | L0 | VERIFIED | TECHNOLOGY_STACK.md:46 (pg_trgm available) | `EXPLAIN ANALYZE SELECT ... WHERE name ILIKE '%query%'` | tests/domains/catalog/test_search.py::test_pg_trgm_index | drop GIN index | F-003 (search performance) | none | PERF-009 | no |
| PERF-009 | db | RESOLVED |  | backend/domains/orders/models/order_entities.py:176 | `order = relationship('Order')` — default `lazy="select"` on ReturnRequest.order | `lazy="selectin"` per Law 45 | Accessing `return_request.order` from a list of returns triggers N+1 | Add `lazy="selectin"` to the `order` relationship | S (0.5h) | P3 | 4 | single | L0 | VERIFIED | backend/domains/orders/models/order_entities.py:65 (Order.user uses lazy='selectin') | `pytest tests/domains/orders/test_returns.py -k n_plus_one` | tests/domains/orders/test_returns.py::test_no_n_plus_one_return_order | revert lazy change | F-006 (returns list) | PERF-002 | PERF-009 | no |

## Over all

### Problem(s)
1. Multiple SQLAlchemy relationships use default `lazy="select"` (N+1 trigger) instead of `lazy="selectin"` as required by Law 45 — affects product cart_items, variants, videos, order items, and return order access.
2. Customer-facing product listing and order history use OFFSET pagination instead of keyset cursor, violating Law 317 ("NEVER OFFSET on hot lists") and degrading at scale.
3. Frontend image pipeline is incomplete: AVIF format missing from next.config.ts, and no blur placeholders on product images — increases LCP and CLS.
4. Product name search uses `ilike '%q%'` without pg_trgm GIN index, causing sequential scans on the products table.

### Solution(s)
1. Add `lazy="selectin"` to all identified relationships (PERF-001, PERF-002, PERF-003, PERF-009).
2. Switch customer product listing and order history to keyset cursor pagination as default; keep OFFSET only as backward-compat fallback.
3. Add `'image/avif'` to Next.js image formats and implement blur placeholder pipeline (store `blur_data_url` on Product model, pass to `next/image`).
4. Create GIN index on `catalog.products.name` using pg_trgm extension.

### Suggestion(s)
1. Run `pytest tests/ -k "n_plus_one"` after fixes to verify no regressions.
2. Add a CI architecture test that fails on any `relationship(...)` without explicit `lazy=` in `backend/domains/*/models/`.
3. Instrument `db.query` count per route via SQLAlchemy events and emit Prometheus metrics (Law 73: performance regression tests).
4. Add `next build` bundle analysis to CI; fail on chunks > 200KB.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Add `lazy="selectin"` to `Product.cart_items` and `Order.items` relationships | Law 45 (no N+1) | yes | S | 5 |
| P0 | Switch customer product listing to keyset cursor pagination | Law 317 (never OFFSET on hot lists) | yes | M | 4 |
| P1 | Add `lazy="selectin"` to `Product.variants`, `Product.videos`, `ReturnRequest.order` | Law 45 | no | S | 5 |
| P1 | Add `'image/avif'` to next.config.ts image formats | TECHNOLOGY_STACK.md §12 | no | S | 4 |
| P1 | Implement blur placeholder for product images | CWV CLS < 0.1 | no | M | 4 |
| P2 | Switch customer order history to keyset cursor pagination | Law 317 | no | S | 4 |
| P2 | Create GIN index on `catalog.products.name` using pg_trgm | TECHNOLOGY_STACK.md pg_trgm | no | M | 3 |
| P3 | Add `lazy="selectin"` to remaining unloaded relationships (Review.product, WishlistItem.product) | Law 45 | no | S | 4 |
