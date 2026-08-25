# Medium Severity Performance Fixes

**Date:** 2026-08-26
**Agent:** Performance Fix Agent
**Scope:** N+1 queries, missing pagination, missing error handling

---

## Issue 1: N+1 Query Problems (7 instances fixed)

### 1.1 Customer Health Service
**File:** `backend/domains/customers/services/customer_health_service.py`
**Problem:** `list_customer_health()` iterated over users and called `engine.calculate_health_score(u.id)` inside the loop, issuing multiple DB queries per user (orders, returns, user lookup).
**Fix:** Batch-loaded all orders for all users in a single query using `Order.user_id.in_(user_ids)`, batch-loaded all returns using `ReturnRequest.order_id.in_(order_ids)`, then computed scores from pre-loaded data via new `calculate_health_score_from_data()` method.
**Impact:** Reduced from O(N) queries to O(1) for the batch.

### 1.2 Customer Health Engine (duplicate)
**File:** `backend/domains/customers/services/customer_health_engine.py`
**Problem:** `list_customer_health()` function at module level had the same N+1 pattern.
**Fix:** Refactored to use the same batched approach with `calculate_health_score_from_data()`.
**Impact:** Consistent performance improvement across both call paths.

### 1.3 Order Tracking Service
**File:** `backend/domains/orders/services/tracking/service.py`
**Problem:** `get_available_orders_for_logistics()` queried `Shipment` individually for each order inside a loop (`db.query(Shipment).filter(Shipment.order_id == order.id).first()`).
**Fix:** Batch-loaded all shipments for all order IDs in a single query, then looked up by order ID in a dictionary.
**Impact:** Reduced from O(N) queries to O(1).

### 1.4 Products Service — finalize_inventory_atomic
**File:** `backend\domains\catalog\services\products\products_service.py`
**Problem:** When atomic stock decrement failed, the function queried each product individually inside the loop to determine if it was missing or just insufficient stock.
**Fix:** Collected insufficient product IDs, then batch-loaded all of them in a single query using `Product.id.in_(insufficient_product_ids)`.
**Impact:** Reduced from O(K) queries to O(1) on the error path (K = number of insufficient items).

### 1.5 Chat Service — mark_read
**File:** `backend/domains/comms/services/messaging/chat_service.py`
**Problem:** `mark_read()` loaded all unread messages then iterated to set `read_at` on each one individually (N+1 update pattern for direct, group, and entity chats).
**Fix:** Replaced the loop with a single bulk `UPDATE` via `query.update({"read_at": now}, synchronize_session=False)`.
**Impact:** Reduced from O(N) UPDATE statements to O(1) for all chat types.

---

## Issue 2: Missing Pagination (5 instances fixed)

### 2.1 Disputes Service — list_supplier_disputes
**File:** `backend/domains/orders/services/disputes/service.py`
**Problem:** Used `OFFSET/LIMIT` pagination which degrades on large datasets.
**Fix:** Integrated `keyset_paginate()` from `infrastructure/utils/pagination.py`. Falls back to `keyset_offset_window()` when an explicit offset is provided for backward compatibility.
**Response now includes:** `next_cursor`, `has_next` for cursor-based navigation.

### 2.2 Disputes Service — list_admin_disputes
**File:** `backend/domains/orders/services/disputes/service.py`
**Problem:** Same OFFSET-based pagination issue.
**Fix:** Same keyset pagination integration as above.

### 2.3 Payment Orchestrator — list_badge_billing_records
**File:** `backend/domains/finance/services/payments/payment_orchestrator.py`
**Problem:** Used `OFFSET/LIMIT` without cursor support.
**Fix:** Added optional `cursor` parameter. When provided, uses `keyset_paginate()` from `infrastructure/utils/pagination.py`. Returns `(items, total, next_cursor, has_next)` tuple.
**Impact:** Enables efficient deep pagination for admin billing views.

---

## Issue 3: Missing Error Handling (3 files fixed)

### 3.1 Checkout Service — Address CRUD
**File:** `backend/domains/orders/services/checkout/service.py`
**Problem:** `create_address()`, `update_address()`, `delete_address()`, `set_default_address()` had no try/except blocks — DB errors propagated as unhandled 500s without logging.
**Fix:** Added try/except with specific handling for `IntegrityError` (409) and generic `Exception` (500), including `db.rollback()` and structured logging via `structlog`.
**Impact:** Proper HTTP status codes, rollback on failure, structured error logging.

### 3.2 Checkout Service — validate_coupon
**File:** `backend/domains/orders/services/checkout/service.py`
**Problem:** No top-level error handling — unexpected exceptions (e.g., malformed input) would propagate unhandled.
**Fix:** Wrapped entire function body in try/except that re-raises `HTTPException` and catches generic `Exception` with 500 response and structured logging.
**Impact:** Graceful degradation on unexpected errors.

### 3.3 Email Service — send_email
**File:** `backend/infrastructure/messaging/email_service.py`
**Problem:** Only caught `RuntimeError` — other exceptions from the provider SDK propagated unhandled. No availability check before attempting delivery.
**Fix:** Added explicit `transport.get("available")` check with early `EmailDeliveryDisabledError`. Expanded exception handling to catch all `Exception` types with structured logging via `exc_info=True`.
**Impact:** Clear error messages when email provider is unavailable; all delivery failures are logged with full stack traces.

---

## Files Modified

| File | Change Type |
|------|-------------|
| `backend/domains/customers/services/customer_health_service.py` | N+1 fix |
| `backend/domains/customers/services/customer_health_engine.py` | N+1 fix |
| `backend/domains/orders/services/tracking/service.py` | N+1 fix |
| `backend/domains/catalog/services/products/products_service.py` | N+1 fix |
| `backend/domains/comms/services/messaging/chat_service.py` | N+1 fix |
| `backend/domains/orders/services/disputes/service.py` | Pagination |
| `backend/domains/finance/services/payments/payment_orchestrator.py` | Pagination |
| `backend/domains/orders/services/checkout/service.py` | Error handling |
| `backend/infrastructure/messaging/email_service.py` | Error handling |

---

## Notes

- All N+1 fixes use bulk `IN` queries or eager loading to reduce query count from O(N) to O(1).
- Pagination fixes use the existing `infrastructure/utils/pagination.py` module (keyset_paginate, keyset_offset_window).
- Error handling fixes follow the existing pattern: `IntegrityError` → 409, generic `Exception` → 500, always rollback, always log.
- The `admin_service.py` file imports from a non-existent `flat_admin_logistics_operations_service.py` module — no actual list functions exist on disk to fix there.
- The `payments.py` file is a re-export shim; the actual list function (`list_badge_billing_records`) lives in `payment_orchestrator.py`.
