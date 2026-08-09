# ZOZI SCOPE · 05 — ORDERS DOMAIN (LIFECYCLE & FULFILLMENT)
**Document type:** Scope-binding specification — **single source of truth** for the Orders domain.
**Version:** 1.0 · **Status:** DRAFT → needs founder sign-off · **Owner:** Commerce / Orders
**Last reviewed:** 2026-08-05
**Supersedes:** none. **Must cite & never contradict:** `01_DATABASE.md`, `layer_rules.yaml`, `repo_structure.yaml`.

> **Honesty notes (baked in, never papered over):**
> - This document was authored to satisfy audit finding **PF2** (`documents/scope/05_ORDERS.md` missing). It describes the *as-built* Orders domain, not an aspirational redesign.
> - Cross-ecosystem foreign keys from `commerce.orders` to `core.users`, `finance.ar_invoices`, and `country.country_configs` are **intentional and by-design** (see §4 / ADR-019). The DATABASE audit flags these as DB06; they are retained because the platform uses shared reference schemas, not duplicated data.
> - Items marked **[CONFIRM]** require real product values; left blank rather than fabricated.

---

## 1. Overview

### 1.1 Feature title
ZOZI Orders — the commerce order lifecycle: cart → checkout → payment → fulfillment → returns/refunds.

### 1.2 Objective / purpose
Define the canonical order model, its state machine, and the fulfillment/returns flows so every surface (customer, supplier, admin, logistics) operates on one bounded context (`commerce`) with one set of rules.

### 1.3 Scope
**In scope:** order aggregate, order items, logistics allocation, return requests, order notifications, the order state machine, fulfillment hand-off to logistics, and returns/refunds.
**Out of scope (own scope docs):** payments posting workflow → `03_FINANCE.md`; search/merchandising → `02_SEARCH.md`; supplier onboarding → supplier scope doc; logistics partner routing → logistics scope doc.

### 1.4 Scope boundary (crisp ✔ / ✘)
```
IN THIS DOCUMENT (orders)                  NOT HERE
✔ Order aggregate & state machine          ✘ Payment gateway posting   → 03_FINANCE
✔ Return / refund request model            ✘ Supplier KYC               → supplier scope
✔ Fulfillment allocation record            ✘ Shipment tracking internals → logistics scope
✔ Order notifications                       ✘ Catalogue pricing rules    → 02_SEARCH
```

### 1.5 Business value / KPIs
- One order state machine with no undocumented transitions.
- Returns never exceed their window (`return_deadline_at` enforced in `returns_controller`).
- Fulfillment allocations are auditable per supplier/partner.

---

## 2. Architecture & Design

### 2.1 Bounded context
Orders live in the **commerce** ecosystem (`schema="commerce"`). Tables:
| Table | Model | Role |
|-------|-------|------|
| `orders` | `Order` | Order aggregate root |
| `order_items` | `OrderItem` | Line items (composition → CASCADE) |
| `order_logistics_allocations` | `OrderLogisticsAllocation` | Per-supplier fulfillment assignment |
| `return_requests` | `ReturnRequest` | Customer return/refund request |
| `order_notifications` | `OrderNotification` | In-app notification rows |

### 2.2 Layer rules (enforced)
Orders follow the standard layered architecture (`layer_rules.yaml`):
- **Models** `models/orders/` → **Services** `services/orders/` → **Controllers** `controllers/orders/` → **Routers** `routers/*orders*`.
- Routers MUST call controllers (or, where already wired, the orders service façade `orders_router_service`), never bypass to raw model access.

---

## 3. Order Lifecycle (State Machine)

```
        cart
         │  checkout()
         ▼
    [pending] ──payment confirmed──▶ [paid]
         │                              │
         │ (payment failed)             │ allocate()
         ▼                              ▼
    [cancelled]                   [fulfillment]
                                      │ ship()
                                      ▼
                                  [shipped] ──confirm──▶ [delivered]
                                                            │
                                                            │ return_window open
                                                            ▼
                                                      [returnable] ──return_request──▶ return_requests(returned|rejected)
```
- `Order.status` is the authoritative state; `payment_status` is a parallel axis.
- `status_label` is a display hint only.
- Transition logic lives in `controllers/orders/orders_controller.py` and `data/services_orders.py` (`apply_order_status_change`).

---

## 4. Cross-Ecosystem References (ADR-019)

The `orders` aggregate references shared reference schemas via foreign keys. These are **retained by design**:
- `orders.customer_id` / `orders.user_id` → `core.users.id` (RESTRICT — deleting a user must not delete their orders).
- `orders.invoice_id` → `finance.ar_invoices.id` (RESTRICT).
- `*_code` FKs to `country.country_configs.code` (RESTRICT — country config deletion must not orphan orders).
- Sub-tables (`order_items`, `order_logistics_allocations`, `return_requests`, `order_notifications`) use `ondelete="CASCADE"` on `order_id` (true composition).

Every FK carries an **explicit `ondelete` rule** (DB07 remediation) and every non-composite FK column carries an **explicit index** (DB08 remediation). `orders.country_code` is covered by the composite index `ix_orders_country_code_created_at` (DB31 remediation).

---

## 5. Fulfillment

- `OrderLogisticsAllocation` records the chosen partner/service-area and price snapshots per supplier.
- Allocations are created during `allocate()` and snapshotted (`partner_name_snapshot`, `accepted_shipping_amount`, …) so historical cost is preserved even if the partner config changes.
- Indexes (`ix_order_logistics_allocations_*`) support partner/shipment supplier lookups.

---

## 6. Returns & Refunds

- `ReturnRequest` is keyed by `order_id` (CASCADE) and optionally `order_item_id`.
- `return_window_days` (default 10) and `delivered_at` compute `return_deadline_at`; the controller rejects requests past the deadline (see `returns_controller.update_return_request`).
- `supplier_review_state` tracks supplier adjudication; `resolution_notes` records the outcome.
- Refund posting is delegated to the finance domain (out of scope here).

---

## 7. Notifications

- `OrderNotification` rows are created by the orders/communication layers for status changes.
- Indexed on `user_id` (`ix_order_notifications_user_id`) for fast per-user inbox queries.

---

## 8. Appendices

### Appendix A — Model → Table map
See §2.1. All models in `backend/models/orders/orders.py`.

### Appendix B — Open findings (tracked, not yet fixed)
- **DB03** (systemic): Orders models do not use `AuditMixin`/`SoftDeleteMixin`/`TenantMixin` uuid/version columns. Tracked as a platform-wide advisory (347 models), not Orders-specific.
- **DB32** (systemic): Several orders controllers/services use OFFSET pagination; to be migrated to cursor pagination per `01_DATABASE.md` §performance rules.
- **CIR2 / CA2 / QUAL3 / FE3** (systemic): cross-cutting architecture findings spanning many domains; addressed at platform level, not here.
