# Order Tracking System — Gap Analysis

## What Already Exists (Working)

### Backend Models
- `Order` — Full model with status, payment, shipping, fraud fields
  - Status CheckConstraint: 'pending','processing','confirmed','shipped','delivered','cancelled','refunded'
  - Timestamps, addresses, logistics references
- `OrderItem` — Items with variant, supplier, pricing
- `Shipment` — Full model with tracking, package metadata, delivery signatures
  - Status CheckConstraint: 'pending','processing','shipped','delivered','returned','cancelled'
- `ShipmentEvent` — Event tracking with actor, location, scan codes
- `ShipmentConfirmation` — Pickup/delivery confirmation requests
- `ReturnRequest` — Return/exchange/refund with full lifecycle
- `ParcelLocationTracker` — GPS location tracking for parcels

### Backend Routers
- `orders.py` — CRUD + tracking + invoice + receipt confirmation + cancellation
- `supplier_orders.py` — List + label + parcel proof upload + verify
- `logistics_orders.py` — List assigned shipments
- `admin_orders.py` — List all orders + status updates + bulk operations + archive/restore
- `shipments.py` — Shipment CRUD + events
- `parcel_tracking.py` — Location tracking endpoints

### Backend Utilities
- `order_tracking.py` — Comprehensive tracking payload builder
  - Timeline construction (5 stages)
  - Status reconciliation
  - Event normalization
  - Financial derivation
  - Return eligibility calculation
  - Shipment serialization

### Services
- `qr_service.py` — QR token generation and validation (currently for employee check-in, needs order QR)

## Key Gaps vs Spec

### 1. Order Status Constraint
Current: `'pending','processing','confirmed','shipped','delivered','cancelled','refunded'`
Needs: Add `'prepared','picking_up','in_transit'` and support logistics states

### 2. Logistics Partner Endpoints
Current: Only `GET /logistics-orders` (list assigned)
Needs:
- `POST /logistics-orders/{id}/pickup-confirm` — Confirm pickup
- `POST /logistics-orders/{id}/scan-receive` — Scan QR + mark picked from supplier
- `POST /logistics-orders/{id}/status` — Update status (logistics_received, distribution_checkpoint, out_for_delivery, etc.)
- `POST /logistics-orders/{id}/deliver` — Deliver + capture e-signature
- `POST /logistics-orders/{id}/cancel-pickup` — Cancel pickup before shipped

### 3. Supplier Order Status Updates
Current: Upload parcel photo → status change to prepared
Needs:
- `POST /supplier/orders/{id}/process` — Mark as processing
- `POST /supplier/orders/{id}/ready-for-pickup` — Mark as prepared (+ QR generation)
- QR code generation for the packing sheet
- Print-friendly packing sheet view

### 4. Admin Override Endpoints
Current: Update status + bulk operations
Needs: Admin can modify any status at any stage, including cancellation

### 5. Customer Tracking Page
Current: Backend has `get_order_tracking` with full payload
Needs: Frontend page that renders the timeline

### 6. E-Signature
Current: Backend model has delivery_signature fields
Needs: Frontend signature capture component

### 7. QR Code for Orders
Current: QR service exists for employees, scan_code field on Shipment
Needs: Order-level QR with standardized format

## Implementation Priority

1. **HIGH**: Order status constraint update (migration)
2. **HIGH**: Logistics partner full CRUD endpoints
3. **HIGH**: Supplier order status transition endpoints
4. **HIGH**: Order-level QR code generation
5. **MEDIUM**: Print-friendly packing sheet
6. **MEDIUM**: Frontend timeline components
7. **MEDIUM**: E-signature capture
8. **LOW**: Mobile app screens
