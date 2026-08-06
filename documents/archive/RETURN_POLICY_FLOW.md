# Return Policy Flow

This document describes the implemented return policy flow in Zozi from supplier setup to customer request, review, resolution, and refund or replacement handling.

## 1. Policy Source of Truth

- Return policy is product-specific, not a single site-wide period.
- Each product can define a return window in days.
- Supplier profiles can define a maximum return window; the current default is 30 days.
- The platform minimum is 10 days.
- If a product has no explicit return window, the order-level flow falls back to 10 days.
- Return requests are accepted only after the order has been delivered.
- One return request can exist per order.
- Request intent must be either return or replacement.
- Only completed return requests trigger an automatic refund.
- Replacement requests are tracked, but they do not auto-refund.

## 2. Roles and Surfaces

| Role | Main Surfaces | What They Do |
| --- | --- | --- |
| Customer | Web order detail and tracking pages, mobile returns and tracking screens, help and chatbot copy | Submit and track a return or replacement request |
| Supplier | Supplier products page, return window editor, supplier returns queue | Set product-level windows and review supplier-owned items |
| Admin / Support | Admin returns queue | Approve, reject, complete, and add resolution notes |
| Backend | Returns and supplier product routes | Enforce policy rules and persist workflow state |

## 3. End-to-End Flow

### Step 1: Supplier sets the product policy

- During product create or update, the supplier can set the product return window.
- The supplier products page exposes a dedicated Return Window editor.
- The editor prevents values below 10 days.
- The backend route validates the submitted value again.
- The product return window cannot exceed the supplier profile maximum.

### Step 2: Product is published

- Product detail pages now show the actual per-product return window instead of a generic returns badge.
- Customer-facing help and chatbot copy now avoids fixed site-wide day promises.
- Customers are directed to the product detail and order pages for eligibility.
- The backend policy remains product-specific and is the source of truth.

### Step 3: Customer places an order

- The customer checks out normally.
- Return eligibility does not begin until the order is delivered.

### Step 4: Delivery is confirmed

- The system marks the order as delivered when fulfillment is complete.
- Return requests are blocked before delivery.
- For multi-shipment orders, delivery is resolved from shipment state, not a single row only.

### Step 5: Customer opens the return flow

- The customer opens order detail or order tracking.
- The customer chooses return or replacement and submits a reason.
- Web order detail only allows the return action when the order is delivered.
- The request is tied to the customer who owns the order.

### Step 6: Backend validates the request

- The order must exist and belong to the current customer.
- The order must be delivered.
- A return request must not already exist for the order.
- The request must be within the product return window measured from delivery.
- The request intent must be valid.

### Step 7: Request record is created

- A ReturnRequest row is created with status pending.
- Supplier review state is initialized for each supplier in the order.
- Timestamps are stored on creation and later updates.
- Audit logging records the creation event.
- A return-created email is queued.

### Step 8: Supplier review

- Supplier review is per supplier, not per order item in isolation.
- The supplier queue shows only the items the supplier owns.
- The supplier can set a decision of pending, approved, rejected, or restocked.
- Restocked updates can restore inventory for supplier-owned items.
- The review state is stored as JSON on the order-level return request.

### Step 9: Admin or support resolution

- Admin and support can list, inspect, and update return requests.
- Allowed status values are pending, approved, rejected, and completed.
- Resolution notes can be attached.
- The workflow stores a resolved timestamp for final outcomes.
- Bulk update support exists for queue operations.

### Step 10: Completion outcome

- If the intent is return and the request is completed, the system attempts an automatic refund.
- Stripe payments use the payment intent refund path.
- Tap payments use the Tap refund endpoint.
- The order status is updated to refunded after a successful refund.
- Refund ledger entries and customer notifications are written.
- If the intent is replacement and the request is completed, the workflow is marked complete without a refund.
- Replacement completion triggers a customer notification only.

### Step 11: Customer visibility

- The customer can review the return request from tracking and return history.
- Status updates remain visible in both web and mobile surfaces.
- Refund status is shown where the payment provider and finance records are available.

## 4. Data Stored

- ReturnRequest: order_id, user_id, intent, reason, status, resolution_notes, supplier_review_state, created_at, updated_at, resolved_at
- Order and shipment data: used to determine delivery and eligibility
- Notification rows: used for return created, return updated, refund issued, and replacement completed messages
- Refund ledger rows: used for payment reconciliation and finance reporting
- Audit log rows: used for traceability and moderation history

## 5. Key Validation Rules

- Return requests are customer-owned.
- Return requests are delivered-only.
- Return deadlines are calculated from the delivery date plus the product window.
- The platform minimum is 10 days.
- Supplier return window settings are capped by the supplier profile maximum.
- Duplicate return requests for the same order are blocked.
- Replacement intent is supported, but it does not trigger the same refund behavior as a return.

## 6. Current Implementation Notes

- The backend is the authoritative policy source.
- Supplier max return windows are now enforced consistently across create, update, and bulk-upload flows.
- Major customer-facing help and chatbot copy now aligns with the product-specific policy model.
- Replacement is modeled and tracked, but there is no separate replacement shipment workflow yet.
- Return policy analytics and deeper dispute automation are still planned items rather than fully implemented behavior.

## 7. Key Files

- [backend/controllers/returns_controller.py](../backend/controllers/returns_controller.py)
- [backend/controllers/products_controller.py](../backend/controllers/products_controller.py)
- [backend/routers/supplier.py](../backend/routers/supplier.py)
- [backend/db/models.py](../backend/db/models.py)
- [backend/db/schemas.py](../backend/db/schemas.py)
- [frontend/web_app/src/app/orders/[id]/page.tsx](../frontend/web_app/src/app/orders/[id]/page.tsx)
- [frontend/web_app/src/app/supplier/products/page.tsx](../frontend/web_app/src/app/supplier/products/page.tsx)
- [frontend/mobile_app/app/returns.tsx](../frontend/mobile_app/app/returns.tsx)
- [frontend/mobile_app/app/help.tsx](../frontend/mobile_app/app/help.tsx)
- [frontend/shared/src/i18n.ts](../frontend/shared/src/i18n.ts)
- [frontend/shared/src/returnsApi.ts](../frontend/shared/src/returnsApi.ts)
