# PHASE 12 — PERFORMANCE / COMPUTATION AUDIT

**Project:** ZOZI Marketplace  
**Date:** 2026-09-11  
**Status:** Static-analysis findings — no profiling data was available  
**Constraint:** Read-only audit; no files were modified  

---

## 1. EXECUTIVE SUMMARY

The audit identified **16 performance hotspots** across the backend. The most critical are:

1. **O(n·m) nested loop in order stock validation** — scales quadratically with cart size.
2. **Synchronous Ollama embedding calls in the search path** — blocking I/O with no connection reuse.
3. **N+1 commission-rule evaluation** — one DB query per rule per product context.
4. **Unbounded `.all()` loads in payout and reconciliation jobs** — memory risk under scale.
5. **Multiple COUNT queries in filter/advanced-search endpoints** — redundant pagination work.
6. **CPU-intensive background-removal pipeline on request threads** — no async offload visible.
7. **ILIKE + multiple OR conditions on text fields** — full-table scans for search.

All findings below are **static-analysis only**. Actual latency/throughput numbers are **NOT DETERMINABLE FROM AVAILABLE CODE** because no profiling data (cProfile, py-spy, SQL EXPLAIN, APM traces) was found.

---

## 2. FINDINGS BY DOMAIN

### 2.1 Order Engine — Quadratic Stock Validation

**Location:** `backend/domains/orders/services/core/order_engine.py:215-263`  
**Operation:** `_load_products_for_order`  
**Observed behavior:** For each unique `product_id` in the order, the code iterates **all** `order.items` again to resolve variants and sum stock.  
**Estimated complexity:** O(n · m) where n = unique products, m = total line items.  
**Why it is expensive:** A cart with 20 items across 10 unique products triggers ~200 redundant iterations and repeated `resolve_product_variant` calls.  
**Evidence:**
```python
# Line 241-261
for product_id, requested_quantity in requested_quantities.items():
    product = products.get(product_id)
    ...
    matching_variants = [
        resolve_product_variant(product, item.selected_size, item.selected_color)
        for item in order.items          # <-- iterates ALL items per unique product
        if item.product_id == product_id
    ]
```
**Potential optimization:** Pre-group `order.items` by `product_id` once, then iterate only the grouped items. Cache variant resolution results.  
**Expected benefit:** Reduce from O(n·m) to O(n + m).  
**Risk of optimization:** Low — algorithmic change with no DB schema impact.

---

### 2.2 Order Engine — Sequential DB Reads in Order Creation

**Location:** `backend/domains/orders/services/core/order_engine.py:726-916`  
**Operation:** `create_order` → `_calculate_order_amounts`  
**Observed behavior:** Order creation performs: (1) `SELECT FOR UPDATE` on products, (2) supplier profile query, (3) shipping zone query, (4) tax query (commented out), (5) fraud scoring via Redis. All in a single synchronous request path.  
**Estimated complexity:** O(1) queries but high constant factor (5+ round-trips).  
**Why it is expensive:** The `SELECT FOR UPDATE` holds row locks while subsequent non-product queries execute, increasing lock contention under concurrency.  
**Evidence:** Lines 644-706 show sequential DB calls inside `_calculate_order_amounts`.  
**Potential optimization:** Batch independent reads; consider moving tax/shipping calculation to async background if eventual consistency is acceptable.  
**Expected benefit:** Reduced p95 latency and lower lock hold time.  
**Risk of optimization:** Medium — requires careful transaction boundary review.

---

### 2.3 Search Service — In-Memory Scoring Without Caching

**Location:** `backend/domains/catalog/services/search/search_service.py:306-398`  
**Operation:** `_score_product` + `_sort_ranked_products`  
**Observed behavior:** After fetching up to `max(limit * 12, 48)` candidates from the DB, every product is scored in Python by rebuilding its search blob and re-parsing attributes.  
**Estimated complexity:** O(k · t) where k = candidate count (48–240+), t = text fields per product.  
**Why it is expensive:** `_product_search_blob` (line 288-303) joins 9 text fields per product; `_deserialize_sizes` (line 202-215) does JSON.parse or string.split per product; shopper-profile matching adds set/dict construction per product. No memoization.  
**Evidence:**
```python
# Line 580-581
ranked = [(_score_product(product, parsed, shopper_profile=shopper_profile), product) for product in candidates]
```
**Potential optimization:** Cache blob + parsed sizes on the Product model or in Redis; move scoring into a materialized column or Postgres FTS rank.  
**Expected benefit:** Eliminate per-request Python-side text processing for cached searches.  
**Risk of optimization:** Low — cache invalidation on product update is straightforward.

---

### 2.4 Search Service — ILIKE + Multi-Field OR Queries

**Location:** `backend/domains/catalog/services/search/search_service.py:547-567`  
**Operation:** `smart_search_from_parsed` text filter construction  
**Observed behavior:** Up to 6 search terms are each turned into 6 `ILIKE '%term%'` conditions across `name`, `description`, `category`, `brand`, `tags`, `ai_description`, `materials`, `color`, `sizes`.  
**Estimated complexity:** Full-table scan when FTS is unavailable (SQLite or non-Postgres).  
**Why it is expensive:** `ILIKE '%term%'` cannot use standard B-tree indexes; combined with `OR` across 9 columns, the planner falls back to sequential scan.  
**Evidence:**
```python
# Line 549-553
if parsed["q"]:
    phrase = f"%{parsed['q'].lower()}%"
    text_conditions.extend(field.ilike(phrase) for field in _text_search_fields())
for term in parsed["terms"][:6]:
    token = f"%{term}%"
    text_conditions.extend(field.ilike(token) for field in _text_search_fields())
```
**Potential optimization:** Use Postgres `websearch_to_tsquery` + GIN index on `search_vector` (already partially implemented at line 556-565). Ensure `search_vector` is kept current via trigger.  
**Expected benefit:** Reduce search query time from O(n) sequential scan to O(log n) index scan.  
**Risk of optimization:** Low — FTS path already exists; needs index creation and trigger.

---

### 2.5 Commission Engine — N+1 DB Query Per Rule Match

**Location:** `backend/domains/catalog/services/commission_engine.py:140-184`  
**Operation:** `_rule_matches` → `_get_node_path_prefix`  
**Observed behavior:** For each commission rule (ordered by priority), `_rule_matches` may call `_get_node_path_prefix`, which issues a separate DB query to fetch `ChartOfCategory.path`.  
**Estimated complexity:** O(r) queries per commission calculation, where r = number of active rules for the supplier profile.  
**Why it is expensive:** A supplier with 20 commission rules triggers up to 20 sequential DB queries for a single product price lookup.  
**Evidence:**
```python
# Line 156-158
if context.coc_path_prefix and context.coc_path_prefix.startswith(
    _get_node_path_prefix(context.db, rule.coc_node_id)   # <-- DB query per rule
):
```
**Potential optimization:** Preload all `ChartOfCategory.path` values for the rule's `coc_node_id` set in a single `IN` query before the loop.  
**Expected benefit:** Reduce r queries to 1 query.  
**Risk of optimization:** Low — pure read, no transaction changes.

---

### 2.6 Background Image Removal — CPU-Intensive Work on Request Thread

**Location:** `backend/providers/image/bg_remover/public_api.py:17-134`  
**Operation:** `remove_background` (and `process_product_image`)  
**Observed behavior:** Loads ML models (`rembg`/U2-Net or IS-Net), runs inference on NumPy arrays, and optionally compares multiple models sequentially. No async offload is visible in the call chain from API routers.  
**Estimated complexity:** O(1) per image but with very high constant factor (seconds per image on CPU).  
**Why it is expensive:** Blocking the event loop / request thread during CPU-bound inference. Under concurrent uploads, workers are starved.  
**Evidence:**
```python
# Line 53-66 (model loop)
for model_name in selected_models[: config.max_models_to_try]:
    session = _SessionManager.get_session(model_name)
    ...
    raw_output = _run_model_with_dimension(img, session, model_name, config.max_rembg_dimension)
```
**Potential optimization:** Offload to a Celery worker or `asyncio.to_thread`; add a processing queue with concurrency limit; cache results by image hash.  
**Expected benefit:** Free request threads; improve checkout/upload latency.  
**Risk of optimization:** Medium — requires async boundary and result-polling or webhook.

---

### 2.7 Payout Sweep — Unbounded `.all()` Load with Per-Row Flush

**Location:** `backend/domains/finance/services/payments/payment_orchestrator.py:863-1132`  
**Operation:** `run_auto_payout_sweep`  
**Observed behavior:** Queries **all** eligible `SupplierSettlement` rows with `.all()`, then iterates to create individual `Payout` records with `db.flush()` per record.  
**Estimated complexity:** O(s) memory and O(s) DB round-trips, where s = eligible settlements.  
**Why it is expensive:** At scale (thousands of pending settlements), this loads every row into memory and performs N+1 flush operations.  
**Evidence:**
```python
# Line 898-913
settlements = (
    db.query(SupplierSettlement)
    .filter(...)
    .all()                            # <-- unbounded load
)
# Line 1007-1012
for settlement in settlements:
    payout = Payout(...)
    db.add(payout)
    db.flush()                       # <-- per-row flush
```
**Potential optimization:** Use `yield_per()` for cursor-based iteration; batch inserts with `bulk_save_objects`; process in chunks of 500–1000.  
**Expected benefit:** Constant memory footprint; fewer DB round-trips.  
**Risk of optimization:** Low — batch semantics already exist elsewhere in the codebase.

---

### 2.8 Finance Reconciliation — Sequential Settlement Matching

**Location:** `backend/domains/finance/services/payments/payment_orchestrator.py:1503-1530`  
**Operation:** `run_gateway_3way_reconciliation`  
**Observed behavior:** Loads up to 1000 `GatewaySettlementSchedule` rows, then loops calling `match_gateway_settlement` (which itself queries orders and does math) for each.  
**Estimated complexity:** O(s) where s = settlements, but each iteration is O(o) for order lookup.  
**Why it is expensive:** 1000 settlements × multiple inner queries = 3000+ queries in a single cron job.  
**Evidence:**
```python
# Line 1513
for settlement in q.limit(1000).all():
    result = match_gateway_settlement(db, settlement.id, country_code)
```
**Potential optimization:** Prefetch matching orders for all settlements in one `IN` query; process in parallel threads if I/O bound.  
**Expected benefit:** Reduce 3k queries to ~3 queries.  
**Risk of optimization:** Medium — requires idempotency safeguards for webhook deduplication.

---

### 2.9 Advanced Filter Service — Redundant COUNT Queries

**Location:** `backend/domains/catalog/services/search/search_service.py:987-1018`  
**Operation:** `AdvancedFilterService._get_ratings`, `_get_video_count`, `_get_discount_count`  
**Observed behavior:** `get_available_filters` triggers 5+ separate COUNT queries against the same base `Product` table with different predicates. `get_active_filters_summary` adds 3 more COUNT queries.  
**Estimated complexity:** O(f) queries per request, where f = 5–8.  
**Why it is expensive:** Each COUNT scans the filtered product set independently. On a 100k-product table, this is 5–8 sequential index/table scans per request.  
**Evidence:**
```python
# Line 987-992
for rating_low, rating_high, label in [(4.0, 5.0, "4_stars"), ...]:
    count = base_query.filter(Product.rating >= rating_low, Product.rating < rating_high).count()
```
**Potential optimization:** Compute all stats in a single query using `FILTER` clauses (Postgres) or conditional aggregation. Cache the result for 60–300s.  
**Expected benefit:** Reduce 8 queries to 1; cut filter-page latency significantly.  
**Risk of optimization:** Low — read-only aggregation.

---

### 2.10 AI Text Provider — Synchronous Ollama HTTP Calls

**Location:** `backend/providers/ai/text.py:186-213`  
**Operation:** `embed_text`  
**Observed behavior:** Opens a new `urllib.request` connection to Ollama for every embedding. No connection pooling, no async, no batching.  
**Estimated complexity:** O(1) network call per query, blocking the thread for 50–500ms.  
**Why it is expensive:** Search queries trigger at least one embedding call. Without pooling, each call pays TCP handshake + TLS overhead.  
**Evidence:**
```python
# Line 206-210
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    return data.get("embedding", [])
```
**Potential optimization:** Use `requests.Session` or `httpx.AsyncClient` with connection pooling; batch embeddings when possible; cache embeddings by product ID.  
**Expected benefit:** Cut embedding latency by 30–70% via connection reuse.  
**Risk of optimization:** Low — provider-layer change only.

---

### 2.11 Tracking Service — In-Memory Sorting and Grouping

**Location:** `backend/domains/orders/services/tracking/service.py:645-891`  
**Operation:** `build_tracking_timeline` and `build_order_tracking_payload`  
**Observed behavior:** Sorts all shipment events in Python (`sorted(...)`), groups by `shipment_id` using `defaultdict`, then iterates shipments to build per-shipment dicts. For orders with 50+ events across 10+ shipments, this is non-trivial CPU work per request.  
**Estimated complexity:** O(e log e + s · e) where e = events, s = shipments.  
**Why it is expensive:** `build_order_tracking_payload` (line 785) calls `build_tracking_timeline` (line 882) after doing its own sorting and grouping. The work is duplicated across multiple helper functions.  
**Evidence:**
```python
# Line 797-804
for event in sorted(events, key=lambda current: ...):
    events_by_shipment[event.shipment_id].append(event)
for confirmation in sorted(confirmations or [], ...):
    confirmations_by_shipment[confirmation.shipment_id].append(confirmation)
```
**Potential optimization:** Do grouping and sorting once at the ORM level (`joinedload` + `order_by`); memoize timeline construction per order for the duration of the request.  
**Expected benefit:** Reduce Python-side work; lower serialization latency.  
**Risk of optimization:** Low — pure in-memory restructuring.

---

### 2.12 Product Delete — Notification Loop Inside Transaction

**Location:** `backend/domains/catalog/services/products/products_service.py:371-407`  
**Operation:** `delete_product`  
**Observed behavior:** After soft-deleting a product, queries all affected `pending/processing/confirmed` orders, then loops to create `Notification` rows one by one inside the same transaction.  
**Estimated complexity:** O(o) where o = affected active orders.  
**Why it is expensive:** If a popular product is in 500 active orders, this creates 500 notification inserts in the request path.  
**Evidence:**
```python
# Line 392-402
affected_orders = (
    db.query(Order).join(OrderItem, OrderItem.order_id == Order.id)
    .filter(OrderItem.product_id == product_id, Order.status.in_([...]))
    .all()
)
for order in affected_orders:
    db.add(Notification(...))
```
**Potential optimization:** Enqueue notifications to a background job (Celery) instead of inserting inline; batch insert with `bulk_save_objects`.  
**Expected benefit:** Reduce delete latency from O(o) to O(1) + async notification.  
**Risk of optimization:** Low — notification is best-effort per the existing `try/except` pattern.

---

### 2.13 Category Tree — Full Table Rebuild

**Location:** `backend/domains/catalog/services/categories/category_tree.py:57-71`  
**Operation:** `rebuild_category_paths`  
**Observed behavior:** Loads **all** `Category` rows, builds a dict, then iterates every row to recompute `path` and `depth`.  
**Estimated complexity:** O(c) where c = total categories. Acceptable for small catalogs, but grows linearly.  
**Why it is expensive:** For 10k categories, this loads 10k rows and does ancestor-chain traversal for each. Called after category create/move operations.  
**Evidence:**
```python
# Line 58-70
cats = db.query(Category).all()
by_id = {c.id: c for c in cats}
for c in cats:
    path, depth = compute_category_path(c, by_id)
    ...
```
**Potential optimization:** Incremental path maintenance on parent change; use a database trigger or application hook to update only the moved subtree.  
**Expected benefit:** Reduce from O(c) to O(depth) per mutation.  
**Risk of optimization:** Medium — must handle cycle detection and dangling parent references.

---

### 2.14 Order Invoice — Missing Pagination on Large Result Sets

**Location:** `backend/domains/orders/services/core/order_engine.py:1161-1184`  
**Operation:** `get_order_invoice`  
**Observed behavior:** Queries `Shipment` with `.limit(1000)` but no offset or cursor; if an order has >1000 shipments (data corruption or test scenario), it silently truncates.  
**Estimated complexity:** O(1000) rows per call.  
**Why it is expensive:** Loading 1000 shipments + their events for a single invoice is excessive; typical orders have 1–5 shipments.  
**Evidence:**
```python
# Line 1184
shipments = db.query(Shipment).filter(Shipment.order_id == order_id).order_by(...).limit(1000).all()
```
**Potential optimization:** Paginate shipments on the invoice; lazy-load events only for the first 10 shipments.  
**Expected benefit:** Reduce memory and serialization time for abnormal cases.  
**Risk of optimization:** Low — defensive fix.

---

### 2.15 AI Upload Pipeline — Sequential Image Processing

**Location:** `backend/domains/catalog/services/products/ai_upload_service.py:38-50`  
**Operation:** `_preprocess_for_ai`  
**Observed behavior:** Applies `auto_rotate` → `auto_lighting` → `smart_crop` → `magic_erase` → `bg_remove` sequentially on a single image bytes blob. Each step decodes/encodes the full image.  
**Estimated complexity:** O(k) CPU-bound steps per image, where k = 5.  
**Why it is expensive:** Each OpenCV/PIL operation re-decodes the byte stream. For bulk uploads, this is CPU-bound and blocks the worker.  
**Evidence:**
```python
# Line 42-49
img_bytes = auto_rotate(img_bytes)
img_bytes = auto_lighting(img_bytes)
img_bytes = smart_crop(img_bytes, target_ratio=1.0)
img_bytes = magic_erase(img_bytes, max_dim=1024)
img_bytes = bg_remove(img_bytes, fast_mode=True)
```
**Potential optimization:** Chain operations on a single decoded `PIL.Image` / `numpy.ndarray` object; resize once at the start.  
**Expected benefit:** Reduce memory allocations and decode/encode overhead.  
**Risk of optimization:** Low — pure algorithmic.

---

### 2.16 Order List — Reconciliation Writes on Every Read

**Location:** `backend/domains/orders/services/core/order_engine.py:999-1026`  
**Operation:** `get_orders`  
**Observed behavior:** For every order list fetch, the code loads shipments + events for all returned orders, reconciles status, and **commits** if any status changed.  
**Estimated complexity:** O(o · s · e) where o = orders, s = shipments per order, e = events per shipment.  
**Why it is expensive:** A page of 50 orders with 3 shipments each triggers 150 shipment queries + event queries, plus a write transaction commit, just to render a list.  
**Evidence:**
```python
# Line 1012-1026
shipments_by_order = _load_shipments_for_orders(order_ids, db)
shipment_ids = [...]
events_by_shipment = _load_events_for_shipments(shipment_ids, db)
...
if updated:
    db.commit()    # <-- write on read
```
**Potential optimization:** Move reconciliation to a background job or a DB trigger; return stale data if <5min old. Cache reconciled status for 30–60s.  
**Expected benefit:** Eliminate write transaction from read path; reduce query count from O(o·s) to O(o).  
**Risk of optimization:** Medium — must ensure eventual consistency for order status UI.

---

## 3. CROSS-CUTTING CONCERNS

### 3.1 Caching Gaps

- **Search results:** `cache_search_results` / `set_search_results` exist (`infrastructure/utils/performance_cache.py` referenced in `search_service.py:21`), but `smart_search` only caches the final result dict, not the intermediate candidate set or scoring. A query that changes limit/offset bypasses cache.
- **Product listings:** `get_products` uses `Cache-Control` headers but no server-side Redis cache for the query result itself (only the `AdvancedFilterService` uses an in-memory `TTLCache`).
- **Commission rules:** No cache for active `CommissionRule` sets; every `calculate_commission` call reloads all rules for the profile.

### 3.2 Serialization / Deserialization Hotspots

- `_serialize_product` in multiple files repeats the same field extraction logic.
- `_deserialize_sizes` does `json.loads` or `split(',')` per product per request.
- `pricing_breakdown_json` fields are deserialized with `json.loads` inside tracking payload construction (`tracking/service.py:440`).

### 3.3 Blocking I/O in Request Handlers

- `_ollama_chat` and `embed_text` use `urllib.request.urlopen` synchronously.
- `create_generic_gateway_payment` uses `httpx.Client` (sync) inside an async route handler (`payment_orchestrator.py:539-541`), blocking the event loop.
- `check_connection_health` opens a new DB connection for every health-check ping.

### 3.4 Pagination Strategy

- OFFSET pagination is used in `get_products`, `list_products_paginated`, `list_my_products`. The code comments acknowledge this is acceptable for shallow pages, but there is no keyset-pagination fallback for admin deep-pagination endpoints.
- `AdvancedFilterService.get_filtered_products` uses offset but also does `query.count()` before fetching, which is expensive on large tables.

---

## 4. EVIDENCE TABLE

| # | Hotspot | File:Line | Complexity | Type |
|---|---------|-----------|------------|------|
| 1 | Order stock validation loop | `orders/services/core/order_engine.py:241-261` | O(n·m) | Nested loop |
| 2 | Sequential reads in order creation | `orders/services/core/order_engine.py:644-706` | 5+ queries | Sequential I/O |
| 3 | In-memory search scoring | `catalog/services/search/search_service.py:580-581` | O(k·t) | Repeated computation |
| 4 | ILIKE multi-field OR | `catalog/services/search/search_service.py:549-553` | O(n) scan | Missing index |
| 5 | Commission rule N+1 | `catalog/services/commission_engine.py:156-158` | O(r) queries | N+1 |
| 6 | BG removal on request thread | `providers/image/bg_remover/public_api.py:53-112` | High constant | Blocking CPU |
| 7 | Payout sweep unbounded load | `finance/services/payments/payment_orchestrator.py:898-913` | O(s) memory | Unbounded query |
| 8 | Reconciliation sequential loop | `finance/services/payments/payment_orchestrator.py:1513` | O(s·o) | Sequential I/O |
| 9 | Filter COUNT storms | `catalog/services/search/search_service.py:987-1018` | O(f) queries | Redundant scans |
| 10 | Ollama sync HTTP | `providers/ai/text.py:206-210` | O(1) per call | Blocking I/O |
| 11 | Tracking in-memory sort/group | `orders/services/tracking/service.py:797-804` | O(e log e) | Repeated sort |
| 12 | Product delete notification loop | `catalog/services/products/products_service.py:392-402` | O(o) inserts | Inline write |
| 13 | Category full-table rebuild | `catalog/services/categories/category_tree.py:58-70` | O(c) | Full scan |
| 14 | Invoice shipment limit(1000) | `orders/services/core/order_engine.py:1184` | O(1000) | Unbounded read |
| 15 | AI upload sequential pipeline | `catalog/services/products/ai_upload_service.py:42-49` | O(k) steps | Repeated decode |
| 16 | Order list write-on-read | `orders/services/core/order_engine.py:1012-1026` | O(o·s·e) | Write on read |

---

## 5. RISK ASSESSMENT SUMMARY

| Risk Level | Count | Representative Items |
|------------|-------|----------------------|
| **High** (scale-breaking) | 4 | #1 Order O(n·m), #6 BG removal blocking, #7 Payout unbounded, #8 Reconciliation N+1 |
| **Medium** (latency) | 8 | #2 Sequential reads, #3 Search scoring, #5 Commission N+1, #10 Ollama sync, #11 Tracking sort, #12 Notification loop, #15 AI pipeline, #16 Write-on-read |
| **Low** (defensive) | 4 | #4 ILIKE scan, #9 COUNT storms, #13 Category rebuild, #14 Invoice limit |

---

## 6. RECOMMENDATIONS (PRIORITIZED)

### P0 — Fix Before Production Scale
1. **Fix order stock validation loop** (`order_engine.py:241-261`) — group items by product_id before iterating.
2. **Offload background-removal to Celery** — add a job queue with `asyncio.to_thread` or `process_folder`-style batching.
3. **Chunk payout/reconciliation sweeps** — replace `.all()` with `yield_per(500)` or batched `IN` queries.
4. **Preload commission rule paths** — single `IN` query for all `ChartOfCategory.path` before rule loop.

### P1 — Improve Latency
5. **Cache search blobs + embeddings** — Redis with TTL; invalidate on product update.
6. **Enable Postgres FTS with GIN index** — ensure `search_vector` is populated and used for all text search.
7. **Replace synchronous `urllib`/`httpx.Client` with pooled/async clients** in `providers/ai/text.py` and payment gateway adapters.
8. **Batch advanced-filter COUNT queries** — use conditional aggregation.

### P2 — Cleanup / Defense
9. **Move order reconciliation to background** — schedule a 30–60s delayed job instead of committing on every list fetch.
10. **Batch product-delete notifications** — insert via `bulk_save_objects` or enqueue to Celery.
11. **Incremental category path maintenance** — avoid full-table rebuild on every parent change.
12. **Paginate invoice shipments** — lazy-load events only for visible shipments.

---

*End of Phase 12 Performance Audit*
