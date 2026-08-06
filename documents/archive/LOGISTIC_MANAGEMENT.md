# Logistics Management (Codebase Aligned)

## Purpose

This is the canonical operations and governance guide for Zozi logistics management.

It describes implemented behavior across:

- Partner/service-area governance
- Shipping quote generation
- Allocation snapshot persistence
- Partner pickup acceptance overrides
- Settlement-facing snapshot reads

## Canonical Source Files

### Core pricing and matching

- `backend/services/logistics_partner_pricing.py`
- `backend/controllers/orders_controller.py`
- `backend/services/cash_management_service.py`

### API routes

- `backend/routers/logistics_partner.py` (prefix `/logistics-partners`)
- `backend/routers/logistics.py` (prefix `/logistics`)

### Data model

- `backend/db/models.py`
- `backend/alembic/versions/d1e2f3a4b5c6_add_logistics_tables.py`
- `backend/alembic/versions/u8v9w0x1y2z3_add_service_area_pricing_fields.py`
- `backend/alembic/versions/w1x2y3z4a5b6_add_logistics_pricing_profiles.py`
- `backend/alembic/versions/y3z4a5b6c7d8_add_logistics_category_and_vehicle_rules.py`
- `backend/alembic/versions/5d9f3a1c2b44_add_order_logistics_allocations.py`
- `backend/alembic/versions/c7d8e9f0a1b2_add_logistics_acceptance_vehicle_overrides.py`

### Admin and partner UI

- `frontend/web_app/src/app/admin/logistics/page.tsx`
- `frontend/web_app/src/app/admin/logistics/LogisticsPartnersPanel.tsx`
- `frontend/web_app/src/app/logistics-partner/dashboard/page.tsx`

## Governance Model

### 1) Partner governance

A partner can quote only when partner state is valid:

- partner status is active
- partner verification status is approved

### 2) Service-area governance

A service area can quote only when area state is valid:

- area is active
- area approval status is approved

Matching behavior is destination-first, with optional origin-city constraints.

### 3) Rate governance

Rates are resolved by precedence:

1. Approved pricing profile for area
2. Approved partner-level fallback profile
3. Service-area fallback charge fields

### 4) Rule governance

- Handling/category rules must be approved and active.
- Vehicle/load-fit rules must be approved and active.
- Distance pricing depends on city-distance matrix data and per-km activation.

## Quote Resolution Paths

Zozi has multiple quote sources during order grouping.

### Source A: Approved logistics partner quote

Primary path from `quote_shipping_for_destination`:

- Match approved service areas
- Build normalized pricing breakdown
- Pick lowest `shipping_amount` among eligible matches

### Source B: Supplier shipping zone fallback

If no approved partner match exists for a supplier group, order flow can use supplier shipping zones.

### Source C: Flat-rate fallback

If neither approved partner nor supplier zone is available, order flow uses global fallback shipping settings.

## Route Classification

`_resolve_route_context` determines:

- `in_city`: same normalized origin and destination city
- `inter_city`: different city or unresolved same-city condition

Distance lookup is used only for inter-city quotes with effective per-km rates.

## Shipment Grouping Behavior

Order quote generation groups by supplier and computes per-group context:

- total weight
- total volume
- categories
- supplier pickup city

Each supplier group resolves its own quote source and breakdown.

## Snapshot Model

### Allocation snapshot (order time)

`OrderLogisticsAllocation` persists immutable baseline values:

- shipping amount
- pickup/dropoff charges
- partner/service-area snapshots
- destination snapshots
- pricing breakdown JSON
- allocation source (`approved_partner_quote`, `supplier_shipping_zone`, `fallback`)

### Acceptance snapshot (pickup confirmation)

Partner pickup acceptance can store accepted override values:

- accepted vehicle rule/type/multiplier
- accepted shipping/pickup/dropoff
- accepted pricing breakdown JSON
- acceptance timestamp

This does not rewrite baseline allocation values; it adds explicit accepted values for operations and settlement usage.

## Operational API Areas

### Partner profile and pricing setup

- profile update and review submission
- service-area CRUD
- pricing-profile CRUD
- category-rule CRUD
- vehicle-rule CRUD
- city-distance matrix CRUD

### Admin review and governance

- review endpoints for profile, area, pricing profile, category rule, vehicle rule, and partner documents
- admin partner list and bulk operations

### Runtime operations

- shipping quote endpoint
- shipment listing and status updates
- confirmation requests
- payout and remittance operations
- dashboard and analytics views

## Admin Workspace Guidance

Admin logistics workspace should operate in this order:

1. Approve partner profile
2. Approve service coverage
3. Approve pricing profile
4. Approve category handling and vehicle/load-fit rules
5. Maintain city-distance rows for inter-city charging
6. Monitor payout/remittance and shipment state transitions

## Language and Field Normalization

Outward pricing payloads are normalized through `normalize_pricing_breakdown_payload`.

Key normalized vocabulary:

- handling keys (`handling_fee`, `applied_handling_label`)
- load-fit keys (`load_fit_*`)
- surcharge keys (`surcharge_*`)
- floor/ceiling and weight-discount keys

Legacy keys can still exist in stored historical payloads, but normalized responses keep downstream contracts stable.

## Maintenance Rules

When changing logistics behavior:

1. Update pricing engine or matching logic in service layer.
2. Update order/cash-management integration if snapshot contract changes.
3. Update route/controller serialization if payload changes.
4. Update backend tests first, then web/mobile consumers.
5. Update logistics charge and inventory docs in `documents/`.
