

## ===========================================================================
## CURRENT ARCHITECTURE AUDIT DISCUSSION 
## ===========================================================================


Let's refine the plan first in detail. 
---

Right now, I don't know what is the architecture audit is doing or is that working correctly or not, creating file, distributing functions and etc. should be completely into the organize way.

---

First of all, we must to draw a `grid line` what `aligned structure/circuit` we need.
Secondly, which files are crossing our architecture structured line and why and how to make changes to put into our `aligned structure`
Third, Recommendation for changes.

---

Am I correct or not ?

---

Right Now, our project backend architecture is not properly defined, all files are created by AI randomly, running all the functions of the website but what is working at where we don't know.

---

First of all, we must to draw a `grid line` what `aligned structure/circuit` we need.

---

I asked to AI what is our Architecture it said first below:

```
`db → models → services → controllers → routers → frontend`

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""

"""
	Database
		↓ (db.database, db.base, db.schemas)
	Models
		↓
	Providers (ai, automation process, bg removal, serach engine, vectorization, )
		↓
	Services  (business logic, database access)
		↘
	Controllers  (business logic orchestration, uses Services + Models directly)
		↓
	Routers  (HTTP endpoints, use Controllers)
		↓
	Frontend
"""
```

then I asked (Where `middleware` is fitting into the circuit of flow of backend ?)
then I got reply below:

```
## Middleware Position in the Backend Circuit
Based on the codebase analysis, here is exactly where middleware fits:

### The Complete Backend Circuit Flow

```
HTTP/WebSocket Request
        │
        ▼
  ┌──────────────────────────────────┐
  │    FastAPI/ASGI Server (uvicorn) │
  └──────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ MIDDLEWARE LAYER  ←  `backend/middleware/`              │
│                                                          │
│  Layer 1  FOUNDATION:  GZip → CORS → IP Extraction →     │
│                         RequestID → ApiVersion           │
│  Layer 2  SECURITY:    SecurityHeaders → ImpossibleTravel │
│                         → CSRF                           │
│  Layer 3  RATE LIMIT:  RateLimit                         │
│  Layer 4  GEO/CCOUNTRY: CountryContext                  │
│  Layer 5  OBSERVABILITY: RequestLogging                │
│  Layer 6  COMPLIANCE:  PCI-DSS (prod only)             │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ ROUTERS (by surface: admin/supplier/customer/internal)│
│  `backend/routers/{surface}/{feature}.py`             │
│  → Validates request                                   │
│  → Calls controller                                    │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ CONTROLLERS (by domain)  ← `backend/controllers/`     │
│  `backend/controllers/{domain}/{name}_controller.py`  │
│  → Orchestrates business logic                         │
│  → Calls services                                      │
│  → Uses models directly                                │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ SERVICES (by domain)  ← `backend/services/`             │
│  `backend/services/{domain}/{name}_service.py`         │
│  → Executes database operations                         │
│  → Contains business rules                            │
│  → Returns model objects                              │
└────────────────────────────────────────────────────────┘
        │
        ▼
DB MODELS + SQLAlchemy   ←  `backend/models/`
        │
        ▼
   DATABASE (PostgreSQL/SQLite)
```

### Middleware's Role in the Circuit

Middleware operates as the **request preprocessing pipeline** that runs *before* any router, controller, or service code. It is the **outermost layer** of the backend logic (after the ASGI server's network handling).

### Key Integration Points

1. **Entry Point**: `main.py:65` → `setup_middleware(app)` registers all middleware on the FastAPI app
2. **Request Context**: Middleware populates `request.state` with:
   - `client_ip` (from `IPExtractionMiddleware`)
   - `country_code` / `country_scope` (from `CountryContextMiddleware`)
   - `request_id` (from `RequestIDMiddleware`)
3. **Downstream Consumption**: Routers read country context via `from middleware.rls_dependency import get_country_scope` (used in `routers/supplier/countries.py:15`)
4. **Service Integration**: `CountryContextMiddleware` calls `from services.hr.coi_service import check_approval_blocked` (line 38 of `country_context.py`) — **this is a cross-layer violation** where middleware reaches into HR service domain directly

### Architectural Problem

The circuit as documented has **no middleware layer**, but the actual code has a critical middleware layer that:
- Sets up RLS country scoping before any router runs
- Handles security headers, CSRF, rate limiting, PCI compliance
- Extracts and forwards context (IP, country, request ID) to downstream layers
- **Directly imports from `services.hr.coi_service`** and `utils.rls_interceptor` — coupling security middleware to HR domain logic and utility-level RLS interceptors

This means the **documented circuit is incomplete**. The real backend circuit includes middleware as the **first processing layer** before routers.

```
---

It is not clearly defined what is the architecture we have and what AI have to do?

---

The Audit Purpose is to Grid everything line and all code properly.
List down, First what will be the backend circuit for large project workable and be specific and according to the destroyed structure.

Secondly, we must to draw a `grid line` what `aligned structure/circuit` we need.
Third, which files are crossing our architecture structured line and why and how to make changes to put into our `aligned structure`
Forth, Recommendation for changes.

---

Am I correct ?

## ===========================================================================
## USER PROBLEM IDENTIFICATION
## ===========================================================================


What i got from your above suggestion we should to keep these below folders for each Domain and Sub-Domain to keep better aligned and cleaned structure of the backend - folders, sub-folders file name, clearly defined properly and indicative to right domain.

___________________________________________________________________________________________
| `Circuit`                 | `Domain` | `Sub_Domain_1` | `Sub_Domain_2` | `Sub_Domain_3` |
| `backend/main`            |
| `MIDDLEWARE`              |
| `ROUTERS`                 |
| `CONTROLLERS`             |
| `SERVICES`                |
| `PROVIDERS`               |
| `MODELS`                  |
| `DATABASE INFRASTRUCTURE` |
| `UTILITIES`               |
| `ASYNC WORKERS`-`JOBS`    |
| `TEST`                    |
___________________________________________________________________________________________

---

- Files Name like `media_models.py`, `orders.py`, `commission.py` and etc. is not indicative properly.
- Folder Name also have same routine of which is not properly indicative.
- Sub-Folder Name also have same routine of which is not properly indicative.
    - `Admin` have `Orders` functions, `Customers` have `Orders` functions, `Suppliers` have `Orders` functions, `Logistics` have `Orders` functions  but those are all different, 
        For example: [`Admin` have `Orders` functions: have checking the order, modiratoring, CRUD operations, real-time tracking and etc]
                    [`Suppliers` have `Orders` functions: have Check the order, Pack the Order, Update the Order Status to Delivery, Hand-over the order Delivery to logistic, modiratoring, real-time tracking and etc]
                    [`Logistics` have `Orders` functions: have Check the delivery status of order, take the delivery from supplier, hand-over to customer, modiratoring, real-time tracking and etc]
                    [`Customers` have `Orders` functions: have Checking the order, modiratoring, CRUD operations, Real-time check and etc]   
    means One `Sub_Domain` have many `Domain`.
    - On Other Hand: Some Domain have straight flow, or just 2 way flow.
        For Example: [`Admin` -> `Accounts & Finance` have one flow, it is not needed to be in `Supplier`, `Logistics`, `Customers`, but the `Sub_Domain` of `Accounts & Finance` have tree flow, 
                        for example: `Order Income` is coming from `Customer`, `Payments` & `Payout` are out-flow to `Suppliers` & `Logistic-Partner`, and etc ]
        For Example: [`Supplier` -> `Upload & Add Product` is one way process, no need for another ]   
        For Example: [`Customer` -> `Cart` is one way process, no need for another ]
- There are a range of Forward-Flow, Backward-Flow, Tree-Flow (either 2-way or 3-way or 4-way, or more) and etc.

---

so Audit Files needs to check everything in detail "in side of the files the content what is indicative and if it needs break then which domain/folder belonging" and "outside of the files also what name it should be and what domain its belonging"

When you are planning for architecture audit file, you have to keep in mind everything properly. 
---

## ===========================================================================
## AI SUGGESTION - FRIST
## ===========================================================================


# ZOZI Backend Architecture: Circuit-Aligned Naming & Structure Specification

## You Are Absolutely Correct

The core problem is: **file names, folder names, and sub-folder names are not indicative of what they actually do or who they serve.** The audit must check BOTH the outside (naming/placement) AND the inside (content/operations).

---

## 1. The Circuit Map (Who Does What to Each Domain)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ZOZI DOMAIN CIRCUIT MAP                                 │
│                                                                                 │
│  Domain: ORDERS                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ CUSTOMER │───▶│ SUPPLIER │───▶│LOGISTICS │───▶│ CUSTOMER │                   │
│  │  places  │    │  packs   │    │ delivers │    │ receives │                   │
│  │  tracks  │    │  ships   │    │  POD     │    │ returns  │                   │
│  │  cancels │    │  hands   │    │  tracks  │    │ reviews  │                   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘                   │
│       │               │               │               │                          │
│       ▼               ▼               ▼               ▼                          │
│  [order_place]  [order_fulfill] [order_deliver] [order_receive]                 │
│  [order_track]  [order_pack]    [order_pickup]  [order_return]                  │
│  [order_cancel] [order_status]  [order_pod]     [order_review]                  │
│                                                                                  │
│  ADMIN sits ABOVE all: moderates, overrides, monitors, reports                   │
│  [order_moderate] [order_override] [order_monitor] [order_report]               │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Domain: FINANCE                                                                 │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                        │
│  │ CUSTOMER │──pay──▶│  FINANCE  │──payout─▶│ SUPPLIER │                        │
│  │          │         │  ENGINE   │──payout─▶│LOGISTICS │                        │
│  └──────────┘         └──────────┘         └──────────┘                        │
│  ONE-WAY IN (customer pays) → TREE-WAY OUT (payouts to supplier + logistics)    │
│  ADMIN: configures rates, views ledger, approves payouts                        │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Domain: CATALOG (Products)                                                      │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐                        │
│  │ SUPPLIER │──add──▶│  CATALOG  │──browse─▶│ CUSTOMER │                        │
│  │  upload  │         │  STORE    │──search─▶│          │                        │
│  │  edit    │         │           │          │          │                        │
│  └──────────┘         └──────────┘         └──────────┘                        │
│  ONE-WAY: Supplier adds → Customer browses. ADMIN moderates.                    │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Domain: COMMUNICATION                                                           │
│  ┌──────────┐◀─────▶┌──────────┐◀─────▶┌──────────┐                           │
│  │ CUSTOMER │       │ SUPPLIER │       │  ADMIN   │                           │
│  │  chat    │       │  chat    │       │  monitor │                           │
│  │  tickets │       │  tickets │       │  respond │                           │
│  └──────────┘       └──────────┘       └──────────┘                           │
│  MULTI-WAY: All surfaces communicate. ADMIN monitors/moderates.                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Naming Convention (Indicative Names)

### Rule: Every file name must answer TWO questions:
1. **WHAT** does it do? (operation verb + entity)
2. **WHO** is it for? (surface context, when in routers/controllers)

### File Naming Pattern:

```
{surface_context}_{domain_entity}_{operation_group}.py
```

### Examples — BEFORE vs AFTER:

| ❌ Current (Not Indicative) | ✅ Correct (Indicative) | Why |
|---|---|---|
| `routers/admin/orders.py` | `routers/admin/order_management.py` | Admin MANAGES orders (CRUD, moderate, override) |
| `routers/supplier/orders.py` | `routers/supplier/order_fulfillment.py` | Supplier FULFILLS orders (pack, ship, handover) |
| `routers/logistics/logistics.py` | `routers/logistics/order_delivery.py` | Logistics DELIVERS orders (pickup, deliver, POD) |
| `routers/customer/orders.py` | `routers/customer/order_tracking.py` | Customer TRACKS orders (view, cancel, return) |
| `models/orders/orders.py` | `models/orders/order_entities.py` | Contains Order, OrderItem, OrderStatus entities |
| `models/media/media_models.py` | `models/media/asset_entities.py` | Contains MediaAsset, UploadJob entities |
| `models/finance/commission.py` | `models/finance/commission_entities.py` | Contains CommissionRule, CommissionEntry |
| `services/orders/orders_write_service.py` | `services/orders/order_lifecycle_service.py` | Manages order state transitions |
| `controllers/admin/orders.py` | `controllers/admin/order_management_controller.py` | Orchestrates admin order operations |
| `routers/admin/admin.py` | `routers/admin/platform_overview.py` | Admin dashboard/overview endpoints |
| `routers/admin/admin_treasury.py` | `routers/admin/treasury_management.py` | Admin manages treasury operations |
| `services/ai/bg_removal_service.py` | `services/ai/image_background_removal.py` | Specific AI operation |
| `utils/auth.py` | `utils/authentication_helpers.py` | Indicative of what it provides |
| `providers/ai/vision.py` | `providers/ai/image_analysis_provider.py` | External AI vision adapter |

### Folder Naming Pattern:

| ❌ Current | ✅ Correct | Why |
|---|---|---|
| `services/payments/` | `services/finance/` | Payments is a sub-domain of Finance |
| `services/location/` | `services/logistics/` | Location serves logistics domain |
| `routers/public/` | `routers/customer/` | "Public" = customer-facing |
| `controllers/products/` | `controllers/catalog/` | Products belong to Catalog domain |
| `models/country/` | `models/geography/` | Country is geography domain |

---

## 3. The Complete Folder Structure (Circuit-Aligned)

```
backend/
├── main.py                          # App entry, middleware registration, router mounting
├── lifespan.py                      # Startup/shutdown lifecycle
│
├── middleware/                       # LAYER 1: Request preprocessing (FLAT - no sub-folders)
│   ├── __init__.py
│   ├── gzip_compression.py
│   ├── cors_policy.py
│   ├── ip_extraction.py
│   ├── request_id.py
│   ├── api_versioning.py
│   ├── security_headers.py
│   ├── impossible_travel_detection.py
│   ├── csrf_protection.py
│   ├── rate_limiting.py
│   ├── country_context.py          # RLS country scoping
│   ├── request_logging.py
│   └── pci_compliance.py
│
├── routers/                          # LAYER 2: HTTP endpoints (grouped by SURFACE)
│   ├── __init__.py
│   ├── admin/                        # Surface: Admin (manages everything)
│   │   ├── __init__.py
│   │   ├── order_management.py      # CRUD, moderate, override, monitor
│   │   ├── product_moderation.py    # Approve/reject products
│   │   ├── supplier_management.py   # Approve/suspend suppliers
│   │   ├── customer_management.py   # View/manage customers
│   │   ├── treasury_management.py   # View ledger, approve payouts
│   │   ├── finance_reporting.py     # Financial reports, analytics
│   │   ├── logistics_monitoring.py  # Monitor all shipments
│   │   ├── communication_hub.py     # Monitor all communications
│   │   ├── platform_settings.py     # Global settings, banners
│   │   ├── user_management.py       # Staff users, roles, permissions
│   │   ├── country_administration.py # Country configs, feature flags
│   │   └── command_center.py        # Real-time dashboard
│   │
│   ├── supplier/                     # Surface: Supplier (fulfills orders, manages products)
│   │   ├── __init__.py
│   │   ├── order_fulfillment.py     # Pack, ship, handover, status update
│   │   ├── product_management.py    # Add, edit, delete own products
│   │   ├── product_upload.py        # Bulk upload, AI-assisted upload
│   │   ├── inventory_management.py  # Stock levels, alerts
│   │   ├── payout_tracking.py       # View own payouts, earnings
│   │   ├── profile_management.py    # Store profile, documents, KYC
│   │   ├── analytics_dashboard.py   # Own sales analytics
│   │   ├── return_handling.py       # Process customer returns
│   │   └── communication.py         # Chat with customers/admin
│   │
│   ├── customer/                     # Surface: Customer (browses, buys, tracks)
│   │   ├── __init__.py
│   │   ├── product_browsing.py      # Search, filter, view products
│   │   ├── cart_management.py       # Add/remove/update cart
│   │   ├── checkout_flow.py         # Place order, apply coupons
│   │   ├── order_tracking.py        # Track order status, delivery
│   │   ├── return_requests.py       # Request returns, refunds
│   │   ├── profile_management.py    # Addresses, preferences
│   │   ├── wishlist_management.py   # Save products
│   │   ├── communication.py         # Chat with supplier, tickets
│   │   └── review_submission.py     # Write product reviews
│   │
│   ├── logistics/                    # Surface: Logistics Partner (delivers)
│   │   ├── __init__.py
│   │   ├── order_delivery.py        # Pickup, deliver, POD
│   │   ├── shipment_tracking.py     # Update delivery status
│   │   ├── route_management.py      # Optimize routes
│   │   ├── payout_tracking.py       # View delivery earnings
│   │   └── profile_management.py    # Partner profile, vehicles
│   │
│   ├── internal/                     # Surface: Internal (system-to-system, health)
│   │   ├── __init__.py
│   │   ├── health_check.py
│   │   ├── webhook_receiver.py
│   │   └── system_jobs_trigger.py
│   │
│   └── external/                     # Surface: External (payment gateway callbacks)
│       ├── __init__.py
│       └── payment_webhooks.py
│
├── controllers/                      # LAYER 3: Orchestration (grouped by DOMAIN)
│   ├── __init__.py
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── order_management_controller.py    # Admin operations
│   │   ├── order_fulfillment_controller.py   # Supplier operations
│   │   ├── order_delivery_controller.py      # Logistics operations
│   │   └── order_tracking_controller.py      # Customer operations
│   ├── catalog/
│   │   ├── __init__.py
│   │   ├── product_management_controller.py
│   │   ├── product_moderation_controller.py
│   │   └── product_search_controller.py
│   ├── finance/
│   │   ├── __init__.py
│   │   ├── payment_processing_controller.py
│   │   ├── payout_management_controller.py
│   │   ├── commission_calculation_controller.py
│   │   └── financial_reporting_controller.py
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── chat_controller.py
│   │   ├── notification_controller.py
│   │   └── ticket_controller.py
│   ├── logistics/
│   │   ├── __init__.py
│   │   ├── shipment_controller.py
│   │   └── delivery_controller.py
│   ├── supplier/
│   │   ├── __init__.py
│   │   ├── onboarding_controller.py
│   │   └── profile_controller.py
│   └── security/
│       ├── __init__.py
│       ├── authentication_controller.py
│       └── authorization_controller.py
│
├── services/                         # LAYER 4: Business logic (grouped by DOMAIN)
│   ├── __init__.py
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── order_lifecycle_service.py       # State machine: placed→packed→shipped→delivered
│   │   ├── order_placement_service.py       # Customer places order
│   │   ├── order_fulfillment_service.py     # Supplier packs & ships
│   │   ├── order_delivery_service.py        # Logistics delivers
│   │   ├── order_return_service.py          # Return/refund processing
│   │   └── order_notification_service.py    # Status change notifications
│   ├── catalog/
│   │   ├── __init__.py
│   │   ├── product_crud_service.py
│   │   ├── product_search_service.py
│   │   ├── product_moderation_service.py
│   │   └── inventory_service.py
│   ├── finance/
│   │   ├── __init__.py
│   │   ├── payment_processing_service.py
│   │   ├── payout_execution_service.py
│   │   ├── commission_calculation_service.py
│   │   ├── ledger_service.py
│   │   ├── invoice_service.py
│   │   └── tax_calculation_service.py
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── email_service.py
│   │   ├── sms_service.py
│   │   ├── push_notification_service.py
│   │   └── ticket_service.py
│   ├── logistics/
│   │   ├── __init__.py
│   │   ├── shipment_service.py
│   │   ├── delivery_tracking_service.py
│   │   ├── route_optimization_service.py
│   │   └── geo_fence_service.py
│   ├── supplier/
│   │   ├── __init__.py
│   │   ├── onboarding_service.py
│   │   ├── kyc_verification_service.py
│   │   └── supplier_health_service.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── authentication_service.py
│   │   ├── authorization_service.py
│   │   ├── fraud_detection_service.py
│   │   └── audit_trail_service.py
│   ├── hr/
│   │   ├── __init__.py
│   │   ├── employee_lifecycle_service.py
│   │   ├── attendance_service.py
│   │   ├── payroll_service.py
│   │   └── leave_management_service.py
│   └── ai/
│       ├── __init__.py
│       ├── image_background_removal.py
│       ├── product_description_generation.py
│       ├── ocr_extraction_service.py
│       └── recommendation_service.py
│
├── providers/                        # LAYER 5: External adapters (grouped by ADAPTER TYPE)
│   ├── __init__.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── vision_api_provider.py          # External AI vision API
│   │   ├── llm_provider.py                 # LLM API adapter
│   │   └── ocr_api_provider.py             # OCR API adapter
│   ├── payment/
│   │   ├── __init__.py
│   │   ├── stripe_provider.py
│   │   ├── paypal_provider.py
│   │   └── thawani_provider.py
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── sendgrid_email_provider.py
│   │   ├── twilio_sms_provider.py
│   │   └── firebase_push_provider.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── s3_storage_provider.py
│   └── maps/
│       ├── __init__.py
│       └── google_maps_provider.py
│
├── models/                           # LAYER 6: Data entities (grouped by DOMAIN)
│   ├── __init__.py
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── order_entities.py              # Order, OrderItem, OrderStatus
│   │   ├── cart_entities.py               # Cart, CartItem
│   │   └── return_entities.py             # ReturnRequest, Refund
│   ├── catalog/
│   │   ├── __init__.py
│   │   ├── product_entities.py            # Product, ProductVariant, Category
│   │   └── inventory_entities.py          # StockLevel, Warehouse
│   ├── finance/
│   │   ├── __init__.py
│   │   ├── payment_entities.py            # Payment, PaymentIntent
│   │   ├── payout_entities.py             # Payout, PayoutBatch
│   │   ├── commission_entities.py         # CommissionRule, CommissionEntry
│   │   ├── ledger_entities.py             # JournalEntry, SubLedger
│   │   └── invoice_entities.py            # Invoice, InvoiceLine
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── chat_entities.py               # ChatThread, ChatMessage
│   │   ├── notification_entities.py       # Notification, PushToken
│   │   └── ticket_entities.py             # Ticket, TicketMessage
│   ├── logistics/
│   │   ├── __init__.py
│   │   ├── shipment_entities.py           # Shipment, ShipmentEvent
│   │   └── delivery_entities.py           # DeliveryRoute, ProofOfDelivery
│   ├── supplier/
│   │   ├── __init__.py
│   │   ├── supplier_entities.py           # Supplier, SupplierDocument
│   │   └── onboarding_entities.py         # OnboardingStep, KycRecord
│   ├── security/
│   │   ├── __init__.py
│   │   ├── user_entities.py               # User, Role, Permission
│   │   └── audit_entities.py              # AuditLog, SecurityEvent
│   ├── hr/
│   │   ├── __init__.py
│   │   ├── employee_entities.py           # Employee, Department
│   │   └── attendance_entities.py         # AttendanceRecord, LeaveRequest
│   └── geography/
│       ├── __init__.py
│       └── country_entities.py            # Country, City, Currency
│
├── db/                               # LAYER 7: Database infrastructure
│   ├── __init__.py
│   ├── database.py                   # Engine, session factory
│   ├── base.py                       # DeclarativeBase
│   ├── mixins.py                     # TimestampMixin, SoftDeleteMixin
│   └── schemas.py                    # Shared Pydantic schemas
│
├── utils/                            # CROSS-CUTTING: Pure helpers (FLAT)
│   ├── __init__.py
│   ├── authentication_helpers.py
│   ├── pagination_helpers.py
│   ├── datetime_helpers.py
│   ├── currency_helpers.py
│   ├── encryption_helpers.py
│   ├── validation_helpers.py
│   └── logging_config.py
│
├── jobs/                             # ASYNC WORKERS (grouped by DOMAIN)
│   ├── __init__.py
│   ├── finance/
│   │   ├── payout_batch_job.py
│   │   └── period_close_job.py
│   ├── orders/
│   │   └── order_timeout_job.py
│   └── communication/
│       └── email_digest_job.py
│
├── alembic/                          # MIGRATIONS ONLY
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
└── tests/                            # TESTS (mirror structure)
    ├── __init__.py
    ├── unit/
    │   ├── services/
    │   ├── controllers/
    │   └── utils/
    ├── integration/
    └── e2e/
```

---

## 4. What the Audit Must Check (Inside + Outside)

### OUTSIDE the file (Naming & Placement):

| Check | Rule | Example Violation |
|---|---|---|
| File name indicative? | Must contain `{entity}_{operation}` | ❌ `orders.py` → ✅ `order_fulfillment.py` |
| Folder = correct domain? | Services/models grouped by DOMAIN | ❌ `services/payments/` → ✅ `services/finance/` |
| Sub-folder = correct surface? | Routers grouped by SURFACE | ❌ `routers/public/` → ✅ `routers/customer/` |
| Layer = correct circuit position? | No service logic in routers | ❌ `session.commit()` in router |
| File in wrong domain folder? | Content doesn't match folder | ❌ `services/finance/chat_service.py` |

### INSIDE the file (Content Analysis):

| Check | Rule | Example Violation |
|---|---|---|
| Functions match file name? | `order_fulfillment.py` must contain fulfill/pack/ship functions | ❌ Contains `cancel_order()` |
| Single domain responsibility? | One file = one domain's operations | ❌ File has both finance AND communication logic |
| Surface-appropriate operations? | Admin file shouldn't have customer-only ops | ❌ Admin router has `add_to_cart()` |
| Flow direction correct? | Service doesn't import from router | ❌ `services/` imports from `routers/` |
| Needs splitting? | File has operations from 2+ domains | ❌ File has `process_payment()` AND `send_email()` |
| Operation verbs match surface? | Supplier ops = pack/ship; Customer ops = browse/track | ❌ Customer router has `approve_supplier()` |

---

## 5. The Flow-Type Classification

Each domain-surface intersection has a **flow type**:

| Domain | Surface | Flow Type | Operations |
|---|---|---|---|
| Orders | Customer | **Forward** (place→track→receive) | place, track, cancel, return, review |
| Orders | Supplier | **Forward** (receive→pack→ship) | accept, pack, ship, handover |
| Orders | Logistics | **Forward** (pickup→deliver→POD) | pickup, deliver, pod, update_status |
| Orders | Admin | **Oversight** (monitor→moderate→override) | view_all, moderate, override, report |
| Finance | Customer | **One-way IN** (pay) | pay, view_receipt |
| Finance | Supplier | **One-way OUT** (receive payout) | view_earnings, request_payout |
| Finance | Admin | **Tree** (configure→monitor→approve) | configure_rates, view_ledger, approve_payout |
| Catalog | Supplier | **One-way IN** (add/edit) | create, edit, delete, upload |
| Catalog | Customer | **One-way OUT** (browse/search) | search, filter, view |
| Catalog | Admin | **Oversight** (moderate) | approve, reject, feature |
| Communication | All | **Multi-way** (bidirectional) | send, receive, read |

---

## 6. How This Changes the Audit Script

The audit script must now perform **TWO passes** on every file:

### Pass 1: External Check (Naming & Placement)
```python
def check_external_alignment(file_path, expected_circuit_map):
    """Check if file name and location match the circuit map."""
    # 1. Is the file in the correct layer?
    # 2. Is it in the correct domain folder?
    # 3. Is it in the correct surface folder (for routers)?
    # 4. Is the file name indicative of its operations?
    # 5. Does the file name match the flow-type for this surface+domain?
```

### Pass 2: Internal Check (Content Analysis)
```python
def check_internal_alignment(file_path, parsed_ast, circuit_map):
    """Check if file content matches its declared purpose."""
    # 1. Extract all function names → determine operations
    # 2. Extract all imports → determine domain dependencies
    # 3. Extract all DB operations → determine if layer-appropriate
    # 4. Check if operations match the file name
    # 5. Check if operations match the surface (admin vs supplier vs customer)
    # 6. Check if file needs splitting (multiple domains detected)
    # 7. Check flow direction (no backward imports)
```

---

## Summary: Your Plan is Correct

| Step | What | Status |
|---|---|---|
| 1 | Define the Circuit (who does what to each domain) | ✅ Defined above |
| 2 | Define Naming Convention (indicative names) | ✅ Defined above |
| 3 | Define Folder Structure (circuit-aligned) | ✅ Defined above |
| 4 | Audit checks OUTSIDE (naming, placement, domain) | ✅ Specified |
| 5 | Audit checks INSIDE (content, operations, flow) | ✅ Specified |
| 6 | Classify flow types (one-way, two-way, tree, multi-way) | ✅ Defined above |






## ===========================================================================
## AI SUGGESTION - SECOND
## ===========================================================================


"""
## ============================================================================

# Complete Architecture Audit File — Master Plan

## The Grid Line (What We're Enforcing)

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 0: ENTRY (main.py, lifespan.py)                           │
│   Only: app creation, middleware registration, router mounting  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: MIDDLEWARE + DEPENDENCIES (flat, no sub-folders)       │
│   Only: request preprocessing, auth extraction, RLS context     │
│   FORBIDDEN: import from services/*, controllers/*, models/*    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: ROUTERS — grouped by SURFACE                           │
│   admin/ supplier/ customer/ logistics/ internal/ external/     │
│   Only: endpoint definitions, request validation, call controller│
│   FORBIDDEN: session.add/commit/delete, business logic          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: CONTROLLERS — grouped by DOMAIN                        │
│   finance/ orders/ catalog/ logistics/ communication/ hr/ ...   │
│   Only: orchestrate services, compose responses                 │
│   FORBIDDEN: session writes, raw SQL, import from routers/      │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: SERVICES — grouped by DOMAIN                           │
│   finance/ orders/ catalog/ logistics/ communication/ hr/ ...   │
│   Only: business rules, DB operations, call providers/models    │
│   FORBIDDEN: import from routers/, controllers/, middleware/    │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: PROVIDERS — grouped by DOMAIN/ADAPTER                  │
│   ai/ media/ logistics/ finance/ communication/                 │
│   Only: external API adapters (AI, maps, email, payment GW)    │
│   FORBIDDEN: import from services/, controllers/, routers/      │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 6: MODELS — grouped by DOMAIN                             │
│   finance/ orders/ catalog/ logistics/ communication/ hr/ ...   │
│   Only: SQLAlchemy ORM definitions, relationships               │
│   FORBIDDEN: import from ANY other layer                        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 7: DB INFRASTRUCTURE (db/, alembic/)                      │
│   Only: engine, session factory, base classes, migrations       │
└─────────────────────────────────────────────────────────────────┘

CROSS-CUTTING:
  utils/     — pure helpers, no state, no DB (importable by all)
  events/    — domain events (grouped by domain)
  jobs/      — background tasks (grouped by domain)
  tests/     — test files (exempt from most rules)
  scripts/   — ops/maintenance scripts (exempt)
```

---

## File Structure Plan — 5 Parts

### PART 1 of 5 (~1,400 lines)
**Header + Constants + Domain Taxonomy + Data Models + Generic Helpers + Rule Loading**

| Section | Contents |
|---|---|
| 1. Docstring + Imports | Version, purpose, usage, all imports |
| 2. Severity + Rule Dictionary | RED/YEL/GRN, RULE_MEANING (single, complete, 80+ rules), HOTLIST_RULES |
| 3. Default Constants | ALL DEFAULT_* constants (single definition each) |
| 4. Domain Taxonomy | PLACEMENT_DOMAIN_KEYWORDS (single), PLACEMENT_ALIAS_TO_DOMAIN, PLACEMENT_STOP_TOKENS, PLACEMENT_FOLDER_STABLE_TOKENS, PLACEMENT_DOMAIN_LAYERS, PLACEMENT_SKIP_PARTS |
| 5. Enhancement Constants | ENH_* constants (single set) |
| 6. Data Models | Finding, Report, ModuleGraph, FeatureRegistry, AutoDomainModel |
| 7. Generic Helpers | rel, walk_dirs, iter_text_files, read_text, parse_safe, in_parts, is_relative_to, domain_of, is_scratch_name, layer_of, layer_of_module, module_path_rel, backend_module_name, normalize_import, resolve_relative_import, resolve_target_module, domain_of_module, normalize_cycle, ensure_required_ignore_dirs |
| 8. Rule Loading | _compile, _merge_dict_of_lists, _read_cfg, _apply_policy, _apply_advanced_policy, _apply_structure, _apply_layer, load_rules |

### PART 2 of 5 (~1,800 lines)
**Feature Discovery + Graph Builder + Structure/Hygiene Checks**

| Section | Contents |
|---|---|
| 9. Feature Discovery | normalize_feature_name, discover_features |
| 10. Module Graph Builder | build_module_graph |
| 11. Structure/Hygiene Checks | check_gitignore, check_lockfiles, check_cache_dirs, check_node_modules, check_hardcoded_local_paths, check_ghost_backend, check_duplicate_basenames, check_secrets_on_disk, check_intended_violations, check_backend_root_modules, check_scratch_scripts, check_doc_and_root_allowlists, check_expected_packages, check_package_init_shape, check_subfolder_axis_and_shape, check_rls_cluster, check_raw_env_in_middleware, check_media_on_disk |

### PART 3 of 5 (~1,600 lines)
**Layer/Dependency Checks + Security/Performance/Quality + Dynamic Imports + Policy + Frontend**

| Section | Contents |
|---|---|
| 12. Layer/Dependency Checks | check_router_outside, check_layer_writes, check_dependency_graph, detect_cycles, check_dependency_cycles, check_dead_modules, check_metrics, check_duplicate_classes |
| 13. Dynamic Imports + Policy + Frontend | check_dynamic_dependency_signals, check_policy_config, check_frontend_structure, collect_frontend_metrics, _merge_features, reconcile_auto_policy |
| 14. Security/Performance/Quality | _enh_call_full_name, _enh_call_has_attr, _enh_backend_parts, _enh_is_excluded_backend_path, check_enhanced_secrets_in_code, check_enhanced_dangerous_calls, check_enhanced_runtime_security_settings, check_enhanced_async_blocking, check_enhanced_query_in_loop, check_enhanced_exception_handling, check_enhanced_todo_debt, check_enhanced_size_complexity, check_enhanced_print_debug, check_enhanced_model_schema, check_enhanced_alembic_heads, check_enhanced_gitignore_generated, check_enhanced_frontend_debug |

### PART 4 of 5 (~1,500 lines)
**Domain Placement Engine + Surface×Domain Matrix + Frontend Roles + Scaffolding Contract + Auto-Learning**

| Section | Contents |
|---|---|
| 15. Domain Placement Engine (_pl_*) | _pl_normalize_domain, _pl_tokenize, _pl_route_tokens, _pl_extract_signals, _pl_known_domains, _pl_infer_domain, _pl_infer_router_target, _pl_check_unknown_folders, check_move_suggestions (SINGLE, with folder-stability override, backend-root placement, grouped emission) |
| 16. Surface×Domain Matrix | check_surface_domain_matrix |
| 17. Frontend Role Pages | check_frontend_role_pages |
| 18. Scaffolding Contract | emit_scaffolding_contract, generate_ai_placement_contract |
| 19. Auto-Learning Engine | _auto_stop_tokens, auto_tokenize, _add_auto_signals, extract_auto_signals, learn_domain_model, infer_auto_domain, detect_surface_from_name, analyze_domain_placement, check_domain_placement |

### PART 5 of 5 (~1,700 lines)
**Summary + Trend + Rendering + Mermaid + Repo Root + main()**

| Section | Contents |
|---|---|
| 20. Summary/Metrics/Trend | compute_debt_score, collect_info, build_summary, read_json, print_trend, update_trend, collapse_noisy_findings, write_move_map |
| 21. Rendering | render_intended_tree (with AI contract inline), render_stdout, write_metrics_json, render_markdown |
| 22. Mermaid Generation | generate_current_structure_mermaid, generate_suggested_structure_mermaid, generate_current_frontend_mermaid, generate_suggested_frontend_mermaid, _mermaid_safe_id, _mermaid_label |
| 23. Registry/CODEOWNERS | _suggest_domain, _load_semantic_overrides, _edge_legal, emit_registry, eff_surface_names_safe, emit_codeowners, emit_graph_mermaid |
| 24. Repo Root Detection | _repo_root_thresholds, _looks_like_repo_root, find_repo, resolve_repo_output_path |
| 25. main() | FULLY WIRED — calls ALL checks in correct order |
| 26. Entry Point | if __name__ == "__main__": sys.exit(main()) |

---

## What's Different From the Old File

| Old File Problem | New File Fix |
|---|---|
| `check_move_suggestions` defined 3× | Defined **1×** (the _pl_* version) |
| `MOVE_DOMAIN_KEYWORDS` + `DP_DOMAIN_KEYWORDS` + `PLACEMENT_DOMAIN_KEYWORDS` | **Single** `PLACEMENT_DOMAIN_KEYWORDS` |
| `_move_*` functions (5) + `dp_*` functions (10) | **Deleted** — replaced by `_pl_*` |
| `_repo_root_thresholds` defined 2× | Defined **1×** |
| `resolve_repo_output_path` defined 2× | Defined **1×** |
| `generate_ai_placement_contract` defined 2× | Defined **1×** |
| `_suggest_domain` / `_load_semantic_overrides` / `_edge_legal` defined 2× | Defined **1×** each |
| `emit_registry` / `emit_codeowners` / `emit_graph_mermaid` defined 2× | Defined **1×** each |
| `collapse_noisy_findings` defined 2× | Defined **1×** |
| `compute_debt_score` / `collect_info` / `build_summary` / `read_json` / `print_trend` / `update_trend` defined 2× | Defined **1×** each |
| `RULE_MEANING.update()` called 5× | **Single** dict literal |
| `HOTLIST_RULES.update()` called 4× | **Single** set literal |
| `DEFAULT_ALLOW_ROOT_MD.update()` called 3× | **Single** set literal |
| `emit_scaffolding_contract` never called in main() | **Called** in main() |
| `check_surface_domain_matrix` never called in main() | **Called** in main() |
| `check_frontend_role_pages` never called in main() | **Called** in main() |
| `learn_domain_model` / `analyze_domain_placement` / `check_domain_placement` never called | **Called** in main() |
| Duplicate emission loop in check_move_suggestions | **Single** loop |
| Monkey-patch `render_intended_tree` | **Inline** contract in the function |
| Section numbering broken (two "5", two "14") | **Sequential** 1–26 |

---

## main() Call Order (The Critical Fix)

```python
def main():
    # 1. Parse args, find repo, load rules
    # 2. Build graph + discover features
    # 3. Domain placement engine (check_move_suggestions)
    # 4. Auto-learning engine (learn_domain_model → analyze → check)
    # 5. Auto-policy reconciliation
    # 6. Structure/hygiene checks (18 functions)
    # 7. Layer/dependency checks (8 functions)
    # 8. Dynamic imports + policy + frontend (6 functions)
    # 9. Security/performance/quality (13 functions)
    # 10. Surface×Domain matrix validation  ← NEW
    # 11. Frontend role-page validation     ← NEW
    # 12. Collapse noisy findings
    # 13. Summary + debt score
    # 14. Registry / CODEOWNERS / graph
    # 15. Scaffolding contract              ← NEW
    # 16. Trend
    # 17. Render stdout + markdown + JSON + metrics + move-map
```

---

# ============================================================================
"""


## ===========================================================================
## AI IDENFICATION ON IT OWN CREATED MODEL OF AUDIT
## ===========================================================================

# Verification Report: `system_architecture_audit_2.py`

## Verdict: ❌ NOT CORRECT — Still Has Critical Issues

The file is **6,323 lines** but approximately **1,050 lines (~17%) are dead/duplicate code**. The "fix-pack append" pattern was **NOT eliminated** — v3.5, v3.6, and v3.7 blocks are still appended after the main code, creating duplicates.

---

## Issue 1: Duplicate Function Definitions (20 functions defined 2×)

| Function | First Definition | Second Definition (wins) | Status |
|---|---|---|---|
| `check_move_suggestions` | v3.5 MOVE version (~line 2800) | v3.7 PLACEMENT version (~line 5800) | ❌ First is DEAD CODE |
| `generate_ai_placement_contract` | v3.6 (uses `DP_DOMAIN_KEYWORDS`) | v3.7 (uses `PLACEMENT_DOMAIN_KEYWORDS`) | ❌ First is DEAD CODE |
| `render_intended_tree` | Section 11 (original) | Monkey-patched after v3.6 | ❌ Monkey-patch still present |
| `_repo_root_thresholds` | Section 12 (~line 4100) | Section 12 (~line 4115) | ❌ Identical duplicate |
| `resolve_repo_output_path` | Section 12 (~line 4200) | v3.7 (~line 5700) | ❌ Duplicate |
| `_suggest_domain` | v3.3 (~line 4300) | v3.7 (~line 5500) | ❌ Duplicate |
| `_load_semantic_overrides` | v3.3 (~line 4320) | v3.7 (~line 5520) | ❌ Duplicate |
| `_edge_legal` | v3.3 (~line 4340) | v3.7 (~line 5540) | ❌ Duplicate |
| `emit_registry` | v3.3 (~line 4360) | v3.7 (~line 5560) | ❌ Duplicate |
| `emit_codeowners` | v3.3 (~line 4450) | v3.7 (~line 5650) | ❌ Duplicate |
| `emit_graph_mermaid` | v3.3 (~line 4520) | v3.7 (~line 5720) | ❌ Duplicate |
| `collapse_noisy_findings` | v3.7 (~line 5300) | v3.7 (~line 5900) | ❌ Duplicate |
| `compute_debt_score` | Section 10 (~line 3900) | v3.7 (~line 5100) | ❌ Duplicate |
| `collect_info` | Section 10 (~line 3940) | v3.7 (~line 5140) | ❌ Duplicate |
| `build_summary` | Section 10 (~line 3960) | v3.7 (~line 5160) | ❌ Duplicate |
| `read_json` | Section 10 (~line 4000) | v3.7 (~line 5200) | ❌ Duplicate |
| `print_trend` | Section 10 (~line 4010) | v3.7 (~line 5210) | ❌ Duplicate |
| `update_trend` | Section 10 (~line 4060) | v3.7 (~line 5260) | ❌ Duplicate |
| `eff_surface_names_safe` | v3.3 (~line 4500) | v3.7 (~line 5700) | ❌ Duplicate |
| `write_move_map` | v3.5 (~line 2780) | Only once | ✅ OK |

---

## Issue 2: Dead Code Blocks (~500 lines)

### v3.5 MOVE Engine (DEAD — ~200 lines)
```
MOVE_DOMAIN_KEYWORDS          ← NEVER USED (v3.7 uses PLACEMENT_DOMAIN_KEYWORDS)
_move_normalize_stem()        ← NEVER CALLED
_move_known_domains_from_dirs() ← NEVER CALLED
_move_infer_domain()          ← NEVER CALLED
_move_infer_surface()         ← NEVER CALLED
First check_move_suggestions() ← OVERRIDDEN by v3.7 version
```

### v3.6 DP Engine (DEAD — ~300 lines)
```
DP_DOMAIN_LAYERS              ← NEVER USED
DP_SKIP_PARTS                 ← NEVER USED
DP_DOMAIN_KEYWORDS            ← NEVER USED
DP_ALIAS_TO_DOMAIN            ← NEVER USED
DP_STOP_TOKENS                ← NEVER USED
dp_normalize_domain()         ← NEVER CALLED
dp_stop_tokens()              ← NEVER CALLED
dp_tokenize()                 ← NEVER CALLED
dp_route_tokens()             ← NEVER CALLED
dp_extract_signals()          ← NEVER CALLED
dp_build_candidate_domains()  ← NEVER CALLED
dp_known_domains()            ← NEVER CALLED
dp_infer_domain()             ← NEVER CALLED
dp_infer_router_target()      ← NEVER CALLED
dp_check_unknown_folders()    ← NEVER CALLED
First generate_ai_placement_contract() ← OVERRIDDEN by v3.7 version
```

---

## Issue 3: Duplicate Emission Loop in `check_move_suggestions` (v3.7)

The v3.7 `check_move_suggestions` has the emission loop **TWICE**:

```python
# FIRST LOOP (~line 5850):
for key in sorted(group_files.keys()):
    ...
    rep.add(YEL, code, layer, ...)  # ← Reports findings

# SECOND LOOP (~line 5880):
for key in sorted(group_files.keys()):
    ...
    mkdir_path = ...
    rep.add(YEL, code, layer, ...)  # ← Reports SAME findings AGAIN!
```

**Result: Every move suggestion finding is reported TWICE in the output.**

---

## Issue 4: Functions NOT Wired in `main()` (6 missing)

| Function | Defined? | Called in `main()`? | Status |
|---|---|---|---|
| `check_move_suggestions` | ✅ | ✅ (via `globals()` check) | ✅ OK |
| `learn_domain_model` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |
| `analyze_domain_placement` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |
| `check_domain_placement` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |
| `check_surface_domain_matrix` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |
| `check_frontend_role_pages` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |
| `emit_scaffolding_contract` | ✅ | ❌ **NOT CALLED** | ❌ MISSING |

---

## Issue 5: Monkey-Patch Still Present

```python
# Line ~5400 — THIS SHOULD NOT EXIST:
try:
    _ORIGINAL_RENDER_INTENDED_TREE = render_intended_tree
    def render_intended_tree() -> str:
        return (
            _ORIGINAL_RENDER_INTENDED_TREE()
            + "\n"
            + generate_ai_placement_contract()
        )
except Exception:
    pass
```

We agreed to **inline** the contract into `render_intended_tree`, not monkey-patch it.

---

## Issue 6: Duplicate Constant Definitions

| Constant | Defined 1st | Defined 2nd | Issue |
|---|---|---|---|
| `PLACEMENT_DOMAIN_KEYWORDS` | Section 3 (~line 430) | v3.7 (~line 5300) | ❌ 2nd overwrites 1st |
| `PLACEMENT_ALIAS_TO_DOMAIN` | Section 3 (~line 530) | v3.7 `_rebuild_placement_aliases()` | ❌ Rebuilt twice |
| `PLACEMENT_STOP_TOKENS` | Section 3 (~line 540) | v3.7 (~line 5400) | ❌ 2nd has INTERNAL DUPLICATES |
| `PLACEMENT_DOMAIN_LAYERS` | Section 3 (~line 575) | v3.7 (~line 5280) | ❌ Duplicate |
| `PLACEMENT_SKIP_PARTS` | Section 3 (~line 580) | v3.7 (~line 5290) | ❌ Duplicate |
| `AUTO_ROUTE_PREFIX_RE` | Section 4 (~line 630) | v3.5 (~line 990) | ❌ Duplicate |
| `AUTO_ROUTE_DECOR_RE` | Section 4 (~line 635) | v3.5 (~line 995) | ❌ Duplicate |
| `_ACTIVE_EFF` / `_ACTIVE_REG` | Section 5 (~line 640) | Section 5 (~line 700) | ❌ Duplicate |

### `PLACEMENT_STOP_TOKENS` Internal Duplicates (v3.7):
```python
PLACEMENT_STOP_TOKENS = {
    ...
    "temp", "tmp", "test", "debug", "old", "new", "copy", "backup", "final", "wip", "legacy", "engine",
    ...
    "temp", "tmp", "test", "debug", "old", "new", "copy", "backup", "final", "wip", "legacy", "engine",  # ← DUPLICATED!
    ...
}
```

---

## Issue 7: `RULE_MEANING.update()` Called 4× (Should Be Single Dict)

```python
# 1st: Initial dict definition (Section 1)
RULE_MEANING = { ... }

# 2nd: v3.4 enhancements
RULE_MEANING.update({ "SEC2": ..., "PERF1": ..., ... })

# 3rd: v3.5 move suggestions
RULE_MEANING.update({ "MV1": ..., "MV2": ..., "MV3": ..., "I4": ... })

# 4th: v3.6 domain placement
RULE_MEANING.update({ "DOM1": ..., "DOM2": ..., "DOM3": ..., "DOM6": ..., "DOM7": ..., "DOM8": ... })

# 5th: v3.7 final fix
RULE_MEANING.update({ "MV1": ..., "MV2": ..., "MV3": ..., "DOM1": ..., ... })  # OVERWRITES v3.5/v3.6!
```

Same for `HOTLIST_RULES.update()` (4×) and `DEFAULT_ALLOW_ROOT_MD.update()` (3×).

---

## Issue 8: Section Numbering Broken

```
Section 1: SEVERITY + RULE DICTIONARY     ✅
Section 2: DEFAULT EMBEDDED RULES         ✅
Section 3: UNIFIED DOMAIN TAXONOMY        ✅
Section 4: ENHANCEMENT CONSTANTS          ✅
Section 5: DATA MODELS                    ✅
Section 5: GENERIC HELPERS                ❌ DUPLICATE NUMBER (should be 6)
Section 7: RULE LOADING                   ❌ (should be 8)
Section 9: FEATURE AUTO-DISCOVERY         ✅
Section 10: MODULE GRAPH BUILDER          ✅
Section 11: STRUCTURE / HYGIENE CHECKS    ✅
Section 12: LAYER / DEPENDENCY CHECKS     ✅
Section 13: DYNAMIC IMPORTS/POLICY/...    ✅
Section 14: v3.4 ENHANCEMENTS             ✅
(unnumbered): v3.5 MOVE ENGINE            ❌ Should not exist
(unnumbered): v3.6 DOMAIN PLACEMENT FIX   ❌ Should not exist
(unnumbered): v3.7 FINAL FIX PACK         ❌ Should not exist
```

---

## Issue 9: `DEFAULT_FORBIDDEN_ROOT["backend"]` Mutated in v3.7

```python
# v3.7 block:
try:
    DEFAULT_FORBIDDEN_ROOT["backend"] = [
        r".*\.(log|db|db-shm|db-wal)$",
        r"^token\.tmp$",
        r"^.*\.json$",
        r"^(?!requirements\.txt$).*\.txt$",
    ]
except Exception:
    pass
```

This mutates the default at runtime — fragile and unnecessary since the value is identical to the original.

---

## Summary Scorecard

| Category | Status | Count |
|---|---|---|
| Duplicate function definitions | ❌ | 20 functions |
| Dead code (MOVE_* engine) | ❌ | ~200 lines |
| Dead code (DP_* engine) | ❌ | ~300 lines |
| Duplicate emission loop | ❌ | Findings reported 2× |
| Functions not wired in main() | ❌ | 6 functions |
| Monkey-patch present | ❌ | 1 instance |
| Duplicate constant definitions | ❌ | 8 constants |
| RULE_MEANING.update() calls | ❌ | 4× (should be 1) |
| HOTLIST_RULES.update() calls | ❌ | 4× (should be 1) |
| Section numbering | ❌ | Broken |
| **Total dead/duplicate lines** | ❌ | **~1,050 lines (~17%)** |

---

## What Must Be Fixed

| # | Fix | Lines Saved |
|---|---|---|
| 1 | Delete entire v3.5 MOVE engine (`MOVE_DOMAIN_KEYWORDS` + `_move_*` + first `check_move_suggestions`) | ~200 |
| 2 | Delete entire v3.6 DP engine (`DP_*` + `dp_*` + first `generate_ai_placement_contract`) | ~300 |
| 3 | Remove duplicate emission loop in v3.7 `check_move_suggestions` | ~30 |
| 4 | Remove monkey-patch of `render_intended_tree`, inline the contract | ~10 |
| 5 | Delete all duplicate function definitions (keep only ONE of each) | ~400 |
| 6 | Merge all `RULE_MEANING.update()` into single dict | ~40 |
| 7 | Merge all `HOTLIST_RULES.update()` into single set | ~20 |
| 8 | Merge all `DEFAULT_ALLOW_ROOT_MD.update()` into single set | ~10 |
| 9 | Remove duplicate `PLACEMENT_*` constants (keep Section 3 only) | ~80 |
| 10 | Remove duplicate `AUTO_ROUTE_*` (keep Section 4 only) | ~10 |
| 11 | Fix section numbering (sequential 1–26) | 0 |
| 12 | Wire 6 missing functions into `main()` | +15 |
| 13 | Remove `DEFAULT_FORBIDDEN_ROOT["backend"]` mutation | ~5 |
| | **Total** | **~1,050 lines removed** |

**After fixes: ~5,270 clean lines, 0 duplicates, 0 dead code, all functions wired.**

---


# ============================================================================
# AI MADE PLAN 
# ============================================================================


# Proper Plan for `system_architecture_audit.py` v4.0

You're right. I was generating code without a proper plan. Let me stop, re-read both files, and create a **correct plan first**.

---

## What I Understand From Reading Both Files

### From `ARCHITECTURE_AUDIT_DISCUSSION.md`:

The audit must enforce **ONE circuit**:

```
ENTRY → MIDDLEWARE → ROUTERS(surface) → CONTROLLERS(domain) → SERVICES(domain) → PROVIDERS → MODELS → DB
```

And check **TWO things per file**:
- **OUTSIDE**: Is the file in the correct layer/folder? Is the name indicative?
- **INSIDE**: Does the content match the file's declared purpose? Are imports legal for this layer?

### From `system_architecture_audit.py` (current 10,427 lines):

The file **works** but is **broken structurally**:
- 20 functions defined twice (Python silently uses the last one)
- ~1,900 lines of dead code that never executes
- 3 competing domain keyword maps
- 6 functions defined but never called in `main()`
- The audit **detects problems** but doesn't **enforce the circuit** properly

---

## The Real Problem (Why the Audit Fails)

The current audit checks **symptoms** (flat folders, dead modules, forbidden edges) but does NOT check:

| Missing Check | What It Should Detect |
|---|---|
| **Circuit layer violation** | A service importing from a router (upward import) |
| **Surface leak in domain layer** | `services/admin/` existing (surface in domain layer) |
| **File name vs content mismatch** | File named `order_service.py` but contains `send_email()` |
| **Cross-surface operation leak** | Customer router containing `approve_supplier()` |
| **Provider importing service** | Provider layer reaching up into services |
| **Controller doing DB writes** | Already checked (W1) but needs circuit context |
| **Middleware importing service** | `country_context.py` importing `services.hr.coi_service` |

---

## The Plan: What the New File Must Do

### Principle: The audit is a **CIRCUIT ENFORCER**, not just a linter.

```
For every .py file in backend/:
  1. Determine its LAYER (by folder position)
  2. Determine its DOMAIN or SURFACE (by sub-folder)
  3. Check: Are its IMPORTS legal for this layer? (circuit direction)
  4. Check: Are its OPERATIONS legal for this layer? (DB writes only in services)
  5. Check: Is its NAME indicative of its content?
  6. Check: Is it in the correct sub-folder for its grouping axis?
  7. Check: Does its content match its declared domain?
```

---

## Exact File Structure (No Duplicates)

```
system_architecture_audit.py (~5,500 lines)
│
├── SECTION 1: Header + Imports + Constants (~400 lines)
│   ├── Docstring
│   ├── Imports
│   ├── RED/YEL/GRN + SEV_ICON + SEV_TAG
│   ├── RULE_MEANING (SINGLE dict, all 80+ rules)
│   ├── HOTLIST_RULES (SINGLE set)
│   └── All DEFAULT_* constants (each defined ONCE)
│
├── SECTION 2: Domain Taxonomy (~200 lines)
│   ├── PLACEMENT_DOMAIN_KEYWORDS (SINGLE map)
│   ├── PLACEMENT_ALIAS_TO_DOMAIN (built once)
│   ├── PLACEMENT_STOP_TOKENS (SINGLE set)
│   ├── PLACEMENT_FOLDER_STABLE_TOKENS
│   ├── PLACEMENT_DOMAIN_LAYERS
│   └── PLACEMENT_SKIP_PARTS
│
├── SECTION 3: Circuit Definition (~100 lines)
│   ├── CIRCUIT_LAYERS (ordered list: entry→middleware→routers→controllers→services→providers→models→db)
│   ├── LAYER_IMPORT_RULES (what each layer MAY import)
│   ├── LAYER_FORBIDDEN_IMPORTS (what each layer MUST NOT import)
│   ├── LAYER_OPERATIONS (what DB operations each layer may perform)
│   └── SURFACE_NAMES + DOMAIN_NAMES
│
├── SECTION 4: Data Models (~150 lines)
│   ├── Finding
│   ├── Report
│   ├── ModuleGraph
│   ├── FeatureRegistry
│   └── AutoDomainModel
│
├── SECTION 5: Generic Helpers (~250 lines)
│   ├── rel(), walk_dirs(), iter_text_files(), read_text(), parse_safe()
│   ├── in_parts(), is_relative_to()
│   ├── domain_of(), domain_of_cfg(), _domain_of_legacy()
│   ├── is_scratch_name()
│   ├── layer_of(), layer_of_module(), module_path_rel()
│   ├── backend_module_name(), normalize_import()
│   ├── resolve_relative_import(), resolve_target_module()
│   ├── domain_of_module(), normalize_cycle()
│   └── ensure_required_ignore_dirs()
│
├── SECTION 6: Rule Loading (~300 lines)
│   ├── _compile(), _merge_dict_of_lists(), _read_cfg()
│   ├── _apply_policy(), _apply_advanced_policy()
│   ├── _apply_structure(), _apply_layer()
│   └── load_rules()
│
├── SECTION 7: Module Graph Builder (~150 lines)
│   └── build_module_graph()
│
├── SECTION 8: Feature Discovery (~200 lines)
│   ├── normalize_feature_name()
│   └── discover_features()
│
├── SECTION 9: Structure/Hygiene Checks (~500 lines)
│   ├── check_gitignore()
│   ├── check_lockfiles()
│   ├── check_cache_dirs()
│   ├── check_node_modules()
│   ├── check_hardcoded_local_paths()
│   ├── check_ghost_backend()
│   ├── check_duplicate_basenames()
│   ├── check_secrets_on_disk()
│   ├── check_intended_violations()
│   ├── check_backend_root_modules()
│   ├── check_scratch_scripts()
│   ├── check_doc_and_root_allowlists()
│   ├── check_expected_packages()
│   ├── check_package_init_shape()
│   ├── check_subfolder_axis_and_shape()
│   ├── check_rls_cluster()
│   ├── check_raw_env_in_middleware()
│   └── check_media_on_disk()
│
├── SECTION 10: Circuit Enforcement Checks (~400 lines) ← NEW
│   ├── check_circuit_import_direction()     ← NEW: upward imports
│   ├── check_layer_operations()             ← DB writes only in services
│   ├── check_surface_in_domain_layer()      ← services/admin/ detection
│   ├── check_middleware_service_import()    ← middleware→service violation
│   ├── check_provider_upward_import()       ← provider→service violation
│   ├── check_controller_db_writes()         ← controller doing session.commit()
│   ├── check_router_business_logic()        ← router containing business logic
│   └── check_cross_domain_import()          ← domain A importing domain B
│
├── SECTION 11: Layer/Dependency Checks (~300 lines)
│   ├── check_router_outside()
│   ├── check_layer_writes()
│   ├── check_dependency_graph()
│   ├── detect_cycles()
│   ├── check_dependency_cycles()
│   ├── check_dead_modules()
│   ├── check_metrics()
│   └── check_duplicate_classes()
│
├── SECTION 12: Dynamic Imports + Policy + Frontend (~400 lines)
│   ├── check_dynamic_dependency_signals()
│   ├── check_policy_config()
│   ├── check_frontend_structure()
│   ├── collect_frontend_metrics()
│   ├── _merge_features()
│   └── reconcile_auto_policy()
│
├── SECTION 13: Security/Performance/Quality (~500 lines)
│   ├── ENH_* constants (SINGLE set)
│   ├── _enh_call_full_name(), _enh_call_has_attr()
│   ├── _enh_backend_parts(), _enh_is_excluded_backend_path()
│   ├── check_enhanced_secrets_in_code()
│   ├── check_enhanced_dangerous_calls()
│   ├── check_enhanced_runtime_security_settings()
│   ├── check_enhanced_async_blocking()
│   ├── check_enhanced_query_in_loop()
│   ├── check_enhanced_exception_handling()
│   ├── check_enhanced_todo_debt()
│   ├── check_enhanced_size_complexity()
│   ├── check_enhanced_print_debug()
│   ├── check_enhanced_model_schema()
│   ├── check_enhanced_alembic_heads()
│   ├── check_enhanced_gitignore_generated()
│   └── check_enhanced_frontend_debug()
│
├── SECTION 14: Domain Placement Engine (~400 lines)
│   ├── _pl_normalize_domain()
│   ├── _pl_tokenize()
│   ├── _pl_route_tokens()
│   ├── _pl_extract_signals()
│   ├── _pl_known_domains()
│   ├── _pl_infer_domain()
│   ├── _pl_infer_router_target()
│   ├── _pl_check_unknown_folders()
│   └── check_move_suggestions() (SINGLE, with folder-stability)
│
├── SECTION 15: Scaffolding + Matrix + Frontend Roles (~200 lines)
│   ├── emit_scaffolding_contract()
│   ├── check_surface_domain_matrix()
│   └── check_frontend_role_pages()
│
├── SECTION 16: Auto-Learning Engine (~250 lines)
│   ├── _auto_stop_tokens(), auto_tokenize()
│   ├── _add_auto_signals(), extract_auto_signals()
│   ├── learn_domain_model()
│   ├── infer_auto_domain()
│   ├── detect_surface_from_name()
│   ├── analyze_domain_placement()
│   └── check_domain_placement()
│
├── SECTION 17: Summary + Trend + Collapse (~200 lines)
│   ├── compute_debt_score()
│   ├── collect_info()
│   ├── build_summary()
│   ├── read_json()
│   ├── print_trend()
│   ├── update_trend()
│   ├── collapse_noisy_findings()
│   └── write_move_map()
│
├── SECTION 18: Rendering (~400 lines)
│   ├── render_intended_tree() (with AI contract inline)
│   ├── render_stdout()
│   ├── write_metrics_json()
│   ├── render_markdown()
│   ├── generate_current_structure_mermaid()
│   ├── generate_suggested_structure_mermaid()
│   ├── generate_current_frontend_mermaid()
│   ├── generate_suggested_frontend_mermaid()
│   ├── _mermaid_safe_id(), _mermaid_label()
│   └── generate_ai_placement_contract()
│
├── SECTION 19: Registry/CODEOWNERS (~200 lines)
│   ├── _suggest_domain()
│   ├── _load_semantic_overrides()
│   ├── _edge_legal()
│   ├── emit_registry()
│   ├── eff_surface_names_safe()
│   ├── emit_codeowners()
│   └── emit_graph_mermaid()
│
├── SECTION 20: Repo Root Detection (~100 lines)
│   ├── _repo_root_thresholds()
│   ├── _looks_like_repo_root()
│   ├── find_repo()
│   └── resolve_repo_output_path()
│
└── SECTION 21: main() (~200 lines)
    └── main() — calls ALL checks in correct order
```

---

## The `main()` Call Order (Exact)

```python
def main():
    # Phase 0: Setup
    parse args → find_repo → load_rules → ensure_required_ignore_dirs

    # Phase 1: Build graph + discover
    graph = build_module_graph()
    reg = discover_features()

    # Phase 2: Circuit enforcement (NEW — the core)
    check_circuit_import_direction()      # upward imports
    check_layer_operations()              # DB writes in wrong layer
    check_surface_in_domain_layer()       # services/admin/
    check_middleware_service_import()     # middleware→service
    check_provider_upward_import()        # provider→service
    check_controller_db_writes()          # controller session.commit()
    check_router_business_logic()         # router with business logic
    check_cross_domain_import()           # domain A → domain B

    # Phase 3: Structure/hygiene
    check_gitignore() ... check_media_on_disk()  # 18 checks

    # Phase 4: Layer/dependency
    check_router_outside() ... check_duplicate_classes()  # 8 checks

    # Phase 5: Dynamic/policy/frontend
    check_dynamic_dependency_signals() ... reconcile_auto_policy()

    # Phase 6: Security/performance/quality
    check_enhanced_*()  # 13 checks

    # Phase 7: Domain placement
    check_move_suggestions()
    check_surface_domain_matrix()
    check_frontend_role_pages()

    # Phase 8: Auto-learning
    learn_domain_model() → analyze_domain_placement() → check_domain_placement()

    # Phase 9: Collapse + Summary
    collapse_noisy_findings()
    compute_debt_score() → build_summary()

    # Phase 10: Output
    emit_scaffolding_contract()
    emit_registry() / emit_codeowners() / emit_graph_mermaid()
    render_stdout() → render_markdown()
    write JSON / metrics / move-map
    print_trend() / update_trend()
```

---

## What's REMOVED vs KEPT from Old File

| REMOVED (dead/duplicate) | Lines Saved |
|---|---|
| `MOVE_DOMAIN_KEYWORDS` + `_move_*` functions (v3.5 engine) | ~250 |
| `DP_DOMAIN_KEYWORDS` + `dp_*` functions (v3.6 engine) | ~400 |
| Duplicate `check_move_suggestions` (v3.5 + v3.6 versions) | ~500 |
| Duplicate `generate_ai_placement_contract` (v3.6 version) | ~60 |
| Duplicate `_repo_root_thresholds` | ~15 |
| Duplicate `resolve_repo_output_path` | ~10 |
| Duplicate `_suggest_domain` / `_load_semantic_overrides` / `_edge_legal` | ~80 |
| Duplicate `emit_registry` / `emit_codeowners` / `emit_graph_mermaid` | ~200 |
| Duplicate `collapse_noisy_findings` | ~60 |
| Duplicate `compute_debt_score` / `collect_info` / `build_summary` / `read_json` / `print_trend` / `update_trend` | ~200 |
| Duplicate `PLACEMENT_*` constants (v3.7 re-declaration) | ~200 |
| Duplicate `ENH_*` constants (declared twice) | ~60 |
| Monkey-patch of `render_intended_tree` | ~15 |
| Duplicate emission loop in `check_move_suggestions` | ~40 |
| **Total removed** | **~1,900 lines** |

| KEPT (working logic) | Notes |
|---|---|
| All 18 structure/hygiene checks | Working correctly |
| All 8 layer/dependency checks | Working correctly |
| All 13 enhanced checks | Working correctly |
| `check_move_suggestions` (v3.7 `_pl_*` version only) | With folder-stability fix |
| `check_surface_domain_matrix` | Was defined but never called → now called |
| `check_frontend_role_pages` | Was defined but never called → now called |
| `emit_scaffolding_contract` | Was defined but never called → now called |
| Auto-learning engine | Was defined but never called → now called |
| All rendering/mermaid/registry | Working correctly |

| ADDED (new circuit enforcement) | Lines |
|---|---|
| `CIRCUIT_LAYERS` + `LAYER_IMPORT_RULES` + `LAYER_FORBIDDEN_IMPORTS` | ~100 |
| `check_circuit_import_direction()` | ~60 |
| `check_layer_operations()` | ~50 |
| `check_surface_in_domain_layer()` | ~40 |
| `check_middleware_service_import()` | ~40 |
| `check_provider_upward_import()` | ~40 |
| `check_controller_db_writes()` | ~40 |
| `check_router_business_logic()` | ~50 |
| `check_cross_domain_import()` | ~50 |
| **Total new** | **~400 lines** |

---

## Final File Size Estimate

```
Old file:     10,427 lines (with ~1,900 dead)
Effective:     8,500 lines (working code)
New file:     ~5,500 lines (clean, no duplicates, +400 new circuit checks)
```

---

## Verification Checklist (Before I Generate Code)

- [ ] Every function defined exactly ONCE
- [ ] Every function called in `main()`
- [ ] ONE domain keyword map (`PLACEMENT_DOMAIN_KEYWORDS`)
- [ ] ONE `RULE_MEANING` dict (no `.update()` calls)
- [ ] ONE `HOTLIST_RULES` set (no `.update()` calls)
- [ ] No monkey-patching
- [ ] No "fix pack" append pattern
- [ ] Circuit enforcement checks exist and are called
- [ ] `emit_scaffolding_contract()` called in `main()`
- [ ] `check_surface_domain_matrix()` called in `main()`
- [ ] `check_frontend_role_pages()` called in `main()`
- [ ] Auto-learning engine called in `main()`
- [ ] Section numbers sequential (1–21)
- [ ] No duplicate emission loops

---

## ===========================================================================
## USER SUGGESTION
## ===========================================================================

I got very basic problem which is the arguments system is unnecessary distributed and non-scene. 
this audit file needs to keep all the audit things into one .md file where everything and all problems of the system should be define properly. 
this audit file should to focus on just one .md file to product the AI and User complete details regarding project gridline and violation of grid line, not on json and etc unnecessary items.

creation of json, out, metrics-json and etc all are unnecessary means below all should be not included.


---

- `system_architecture_audit_3.py` have latest audit model.
- `ARCHITECTURE_AUDIT_DISCUSSION.md` have complete discussion of brain storming.

---

- You have do complete audit of the script in detail after reading the complete discussion.
- Find out all, hardcode, dead code to be convert into meaningful audit code, error to be fix and etc.
- Find out, the script contain all the discussion point properly.
- Find out, what improvement is needed to capture all the segments and any more advanced level.

---






## ===========================================================================
## PREVIOUS AND INITIAL DISCUSSION BULLET POINT OF AUDIT ARCHITECTURE DESIGN 
## ===========================================================================

- **Purpose of the document**
  - Defines a **target repository structure** for ZOZI after cleanup.
  - Describes an **audit/governance system** that mechanically enforces architecture instead of relying on manual discipline.
  - Captures a design discussion evolving from a monolithic audit script into a **YAML-driven architecture governance tool**.

- **Core problem being solved**
  - AI/contributors keep drifting from the intended architecture.
  - There is no mechanical enforcement of where files belong and what layers may depend on.
  - The repo accumulated scratch files, duplicate backends, misplaced models, duplicate migrations, secrets/artifacts, and documentation rot.

- **Primary design principle**
  - The audit script should not merely say “wrong.”
  - It should say:
    - what is wrong,
    - where it should move,
    - why,
    - and what the intended target structure is.

- **Target end-state structure**
  - Clean repo root with only intentional entries:
    - `.gitignore`
    - `.env.example`
    - `.aiignore`
    - `README.md`
    - `docker-compose.yml`
    - `Makefile` / `justfile`
    - `railway.toml`
  - Main top-level areas:
    - `backend/`
    - `frontend/`
    - `documents/`
    - `infra/` or root monitoring/nginx
    - `experiments/`
    - `design/`
    - `scripts/`

- **Important architectural decision: logical domains**
  - `database` and `security` are **logical domains**, not top-level folders.
  - Physical homes:
    - database domain:
      - `backend/db/`
      - `backend/alembic/`
      - `backend/models/`
    - security domain:
      - `backend/middleware/`
      - `backend/dependencies/`
      - `backend/SECURITY_CONFIG.ini`
  - The auditor tags findings by logical domain, but does **not** require top-level `database/` or `security/` directories.

- **Backend target layout**
  - `backend/main.py`
    - single router registry.
  - `backend/routers/`
    - API entrypoints only.
    - no DB writes.
  - `backend/controllers/`
    - orchestration only.
    - no DB writes.
  - `backend/services/`
    - the **only writers** to the database.
    - grouped by domain:
      - `finance/`
      - `treasury/`
      - `hr/`
      - `logistics/`
      - `supplier/`
      - `ai/`
      - `comms/`
      - `catalog/`
      - `audit/`
  - `backend/models/`
    - only ORM models.
    - each model should declare schema via `__table_args__`.
  - `backend/middleware/`
    - security-related cross-cutting logic.
    - exactly one canonical RLS enforcer.
  - `backend/db/`
    - DB infrastructure only.
    - no ORM models living here.
  - `backend/alembic/`
    - the only migrations home.
    - no diagnostics, no stub revisions, no fractured heads.
  - `backend/scripts/`
    - one home for ops/dev scripts.
  - `backend/data/`
    - config-as-data.
  - `backend/tests/`
    - unit/integration/contract tests.

- **Frontend target layout**
  - `frontend/web_app/`
  - `frontend/mobile_app/`
  - `frontend/shared/`
  - No scratch scripts:
    - `countDivs*.js`
    - `fixTailwind*.js`
    - `*.bak`
    - `*.tsbuildinfo`
  - One lockfile per workspace only.

- **Documents target layout**
  - `documents/scope/`
    - authoritative specs only.
    - includes:
      - `00_SCOPE_BINDING.md`
      - `01_DATABASE.md`
      - `02_SEARCH.md` …
      - `00_REPO_STRUCTURE.md`
      - `repo_structure.yaml`
      - `layer_rules.yaml`
  - `documents/archive/`
    - old audits, reports, generated docs, to-do lists, etc.
  - Only `scope/` is authoritative.

- **Major cleanup / “exits” list**
  - Delete frontend scratch/debug scripts:
    - `countDivs.js`
    - `countDivs2.js`
    - `linenums.js`
    - `listDivs.js`
    - `verify-tmp.js`
    - `fixTailwind*.js`
  - Fix hardcoded local paths:
    - e.g. `d:/Projects/...`
  - Move non-authoritative docs out of `documents/` root:
    - audit reports,
    - security reports,
    - cash/payment audits,
    - generated data dictionaries,
    - workflow summaries,
    - to-do lists.
  - Move/delete repo-root experiments and backups:
    - `Working_API/`
    - `provider_test/`
    - `_trash/`
    - `backup_*/`
    - `image/`
    - logo zips
    - stray YAML/text files
  - Move `backend/db/employee_models.py`
    - to `backend/models/`
  - Delete second migrations home:
    - `backend/db/migrations/`
    - fold into Alembic
  - Move Alembic diagnostics out:
    - `_graph_analysis.py`
    - `_diagnose_tree.py`
    - to `backend/scripts/`
  - Move `backend/api/country_communications.py`
    - to `backend/routers/`
  - Move controller writes into services:
    - e.g. `chat_controller.py` deleting wishlist rows directly.
  - Relocate mis-housed controller logic:
    - `audit_controller.py` → `services/audit/`
    - `cache_utils.py` → `utils/`
  - Consolidate RLS enforcement:
    - keep one canonical RLS enforcer.
    - remove/alias duplicates.
  - Remove ghost backend:
    - `scripts/backend/`
    - because it duplicates `main.py` and DB infrastructure.
  - Remove committed artifacts:
    - logs
    - SQLite WAL/SHM files
    - caches
    - `.tsbuildinfo`
    - JSON reports
    - temp secrets
  - Enforce one lockfile per frontend workspace.

- **Sub-folder discussion: module-by-folder idea**
  - User proposed:
    - `backend/services/admin/**`
    - `backend/controllers/admin/**`
  - Verdict:
    - grouping by module is correct,
    - but the grouping axis matters.
  - Correct rule:
    - `routers/` and `controllers/` may group by **surface**
      - `admin/`
      - `supplier/`
      - `customer/`
      - `public/`
      - `webhooks/`
    - `services/` and `models/` must group by **domain**
      - `finance/`
      - `orders/`
      - `catalog/`
      - `supplier/`
      - `logistics/`
      - `comms/`
      - `hr/`
      - `ai/`
      - `core/`
  - Reason:
    - `admin` is a user/surface role, not a business domain.
    - `services/admin/` would become a catch-all and recreate flat-folder chaos.

- **Review of original audit script**
  - Overall score:
    - idea: 10/10
    - architecture: 9.8/10
    - scalability: 9/10
    - maintainability: 8/10
    - long term: 7.5/10
    - overall: 9/10
  - Strong points:
    - gives corrective destination, not just errors.
    - logical domain concept is correct.
    - intended tree is valuable.
  - Weak points:
    - mixes architecture, security, repo hygiene, quality, and style in one script.
    - hardcodes intended structure inside Python.
    - too many project-specific regex rules.
    - architecture knowledge duplicated in code and docs.
    - too large / too monolithic.
    - missing dependency-graph enforcement.
    - missing ownership boundaries.
    - missing architecture versioning.
    - missing explicit layer contracts.
    - missing feature manifests.

- **Reviewer’s recommended evolution**
  - Split responsibilities into separate auditors:
    - architecture auditor
    - repository auditor
    - security auditor
    - code quality auditor
    - dependency auditor
    - performance auditor
  - Make structure definition external:
    - `repo_structure.yaml`
  - Make layer rules external:
    - `layer_rules.yaml`
  - Reduce regex accumulation:
    - use categories instead of endless deny-lists.
  - Make scope docs the single source of truth.
  - Add dependency graph validation:
    - detect illegal edges such as:
      - controller → database
      - service → router
      - model → router
      - controller → controller internals
  - Add ownership validation:
    - features/domains should not import each other’s internals directly.
  - Add layer contracts:
    - controller can:
      - validate
      - call service
      - return response
    - controller cannot:
      - touch DB
      - filesystem
      - Redis
      - MQ
      - raw SQL
    - service can:
      - use repository/models
      - providers
      - cache
    - service cannot:
      - depend on FastAPI request/response machinery

- **Reconciled decision from discussion**
  - Adopt 8 of 10 reviewer points immediately.
  - Defer 2 as premature:
    - architecture versioning
    - per-feature `feature.yaml`
  - Reason for deferral:
    - useful later, but too much ceremony for current stage.
    - would create more files to maintain before the team/feature count justifies it.

- **Agreed near-term governance architecture**
  - Source of truth:
    - `documents/scope/`
      - narrative specs
      - `repo_structure.yaml`
      - `layer_rules.yaml`
  - Auditors:
    - `governance/audit.py` as one entrypoint
    - `structure_auditor.py`
    - `dependency_auditor.py`
    - `security_auditor.py`
    - `repository_auditor.py`
    - `quality_auditor.py`
    - `reporter.py`
  - Key discipline:
    - YAML defines policy.
    - Python only executes checks.
    - docs and machine rules must not drift.
    - CI gate fails on red violations.

- **Most important upgrade: dependency-graph validator**
  - Considered the headline improvement.
  - Replaces many fragile regex checks with one structural mechanism.
  - Parses Python imports using `ast`.
  - Classifies modules by layer.
  - Rejects forbidden dependency edges.
  - Catches real existing issues:
    - controller writing to DB
    - services importing controllers
    - mis-housed shared controller logic being imported across layers
    - future model/router or service/FastAPI misuse

- **Example layer contract**
  - `routers` may import:
    - controllers
    - services
    - utils
    - dependencies
    - read-only model usage if allowed
  - `controllers` may import:
    - services
    - utils
  - `services` may import:
    - models
    - providers
    - utils
    - events
  - `models` may import:
    - db
    - utils
  - `providers` may import:
    - utils
  - Forbidden examples:
    - controller → DB write/session
    - service → router
    - model → service
    - provider → service

- **Phased implementation plan**
  - **Phase 0**
    - extract intended structure into `repo_structure.yaml`
    - split monolith into sub-auditors
    - auditor reads YAML instead of hardcoded structure
  - **Phase 1**
    - add dependency auditor
    - add `layer_rules.yaml`
    - replace scratch deny-lists with categories
  - **Phase 2**
    - perform domain-axis folder moves:
      - `routers/admin/`
      - `controllers/<surface or domain as agreed>/`
      - `services/<domain>/`
      - `models/<domain>/`
    - grep imports before moving
    - run tests after each batch
  - **Phase 3**
    - wire auditor into CI
    - fail build on red findings
    - cross-check docs vs YAML
  - **Deferred**
    - architecture versioning
    - feature manifests
    - trigger later when:
      - multiple contributors exist,
      - or major restructure happens,
      - or domain collisions become real

- **Actual script described in the file**
  - File:
    - `backend/scripts/backend_layout_audit.py`
  - Nature:
    - read-only
    - repo-wide
    - structural + dependency auditor
    - version v2.2
  - Uses:
    - standard library mostly
    - `ast`
    - optional PyYAML as soft dependency
  - Does not import app code.
  - Can output:
    - stdout scorecard
    - damage hotlist
    - domain-grouped findings
    - intended tree
    - markdown report
    - JSON for CI
  - Exit behavior:
    - returns 1 if any red violations
    - `--no-fail` forces exit 0

- **Logical sub-auditors embedded in one file**
  - structure auditor:
    - intended violations
    - backend root modules
    - doc/root allow-lists
    - scratch scripts
  - dependency auditor:
    - import graph / layer contracts
  - security auditor:
    - secrets on disk
    - raw env reads in middleware
    - RLS duplication
  - repository auditor:
    - gitignore
    - cache dirs
    - node_modules
    - lockfiles
    - ghost backend
  - quality auditor:
    - hardcoded local paths
    - media on disk
    - duplicate basenames
  - backend auditor:
    - layer writes
    - router outside routers
    - services shape

- **Important rule codes used**
  - `W1`
    - controller/router writes to DB
  - `W2`
    - misnamed writer-controller should move to services
  - `W3`
    - imports a mis-housed controller
  - `W4`
    - controller imports another controller
  - `Q1`
    - controller/router reads via `db.query`
  - `M1`
    - ORM model outside `models/`
  - `R1`
    - `APIRouter` outside `routers/`
  - `G1`
    - second migrations home
  - `X1`
    - ghost/duplicate backend skeleton
  - `D1`
    - duplicate module basename within backend
  - `D2`
    - duplicate module basename across top dirs
  - `S1`
    - services folder is flat
  - `S2`
    - overlapping service stems
  - `L1`
    - multiple RLS enforcers
  - `A1`
    - Alembic diagnostics/stubs/fractured heads
  - `P1`
    - scratch script at backend root
  - `P3`
    - module at backend root
  - `F1`
    - scratch/debug script
  - `F2`
    - hardcoded local path
  - `F3`
    - multiple lockfiles
  - `F4`
    - committed cache/build/artifact
  - `F5`
    - secret material on disk
  - `F6`
    - media written/served from local disk
  - `F7`
    - raw env secret read in middleware
  - `F8`
    - unauthorized documents root entry
  - `F9`
    - unauthorized repo-root note/dir
  - `G0`
    - missing/weak root `.gitignore`
  - `DG`
    - forbidden dependency edge
  - `NM`
    - node_modules present

- **YAML policy files introduced**
  - `documents/repo_structure.yaml`
    - forbidden root patterns
    - forbidden anywhere patterns
    - allowed root markdown files
    - allowed documents root entries
    - scratch phrase detection
    - scratch token detection
  - `documents/layer_rules.yaml`
    - forbidden dependency edges
    - mis-housed controllers
    - controller-to-controller import policy

- **Key policy choices in YAML**
  - Forbid artifacts at backend root:
    - logs
    - db files
    - temp files
    - JSON/text scratch
  - Forbid diagnostics in `backend/alembic/`
  - Forbid frontend artifacts:
    - logs
    - tsbuildinfo
    - backups
    - screenshots
  - Forbid repo-root clutter:
    - experiments
    - backups
    - images
    - zips
    - stray YAML
    - SQLite DBs
  - Forbid second migrations home
  - Forbid `employee_models.py` outside models
  - Allow only specific root docs:
    - `README.md`
    - `AGENTS.md`
    - `CONTRIBUTING.md`
    - `CHANGELOG.md`
    - `SECURITY.md`
    - `LICENSE*`
  - Allow only specific documents root entries:
    - `scope`
    - `archive`
    - index/readme files

- **Second review of improved script**
  - New rating:
    - about **9.5/10**
  - Major improvements:
    - dependency graph validation
    - YAML as authoritative policy
    - explicit layer contracts
    - allow-list philosophy
    - correct domain-vs-surface organization

- **Remaining recommended improvements**
  - **Import resolution is approximate**
    - current resolver handles many but not all Python import forms.
    - edge cases:
      - relative imports
      - `TYPE_CHECKING`
      - `importlib.import_module`
      - dynamic imports
  - **No cycle detection**
    - should detect circular dependencies:
      - orders → payments → inventory → orders
    - suggested code: `DG2`
  - **No ownership validation**
    - should define domain boundaries:
      - which domains may import which other domains
    - prevents bounded-context leakage
  - **No dead-code graph**
    - can detect unused:
      - services
      - utils
      - controllers
      - providers
      - middleware
  - **No architectural metrics**
    - fan-in
    - fan-out
    - instability
    - afferent/efferent coupling
    - god-module detection
  - **No package completeness validation**
    - expected files/exports inside a package
  - **No duplicate class detection**
    - same class name repeated across modules
  - **No trend reporting**
    - compare audit results over time
    - show improvement or regression
  - **More constants should move into YAML**
    - write verbs
    - read verbs
    - known writer controllers
    - secret patterns
    - cache dir names
    - lockfiles

- **Overall conclusion**
  - The project evolved from:
    - “audit file locations”
  - to:
    - “enforce architecture with a dependency graph and external policy.”
  - The most binding improvements are:
    - target tree,
    - YAML source of truth,
    - dependency-graph validator,
    - CI gate.
  - The system is now strong enough for governance, but should next add:
    - cycle detection,
    - domain ownership rules,
    - metrics,
    - dead-code detection,
    - fuller import resolution.



































give the code to b fixes of below to be replace into the script.

---

## 2.1 Undefined constants used by auto-learning engine

### Location

`extract_auto_signals()` uses:

- `AUTO_ROUTE_PREFIX_RE`
- `AUTO_ROUTE_DECOR_RE`

### Problem

These constants are **not defined anywhere** in the pasted script.

### Impact

Because `main()` calls:

- `learn_domain_model()`
- `analyze_domain_placement()`

and those call `extract_auto_signals()`, the script can crash with a `NameError` during normal execution.

### Severity

**Critical**

### Fix

Define them explicitly, for example:

- one regex for `APIRouter(prefix=...)`
- one regex for route decorators like `@router.get("/...")`

Even better:

- reuse the logic already present in `_pl_route_tokens()`
- remove duplicate route-extraction logic
- keep only one route-signal extractor

---

## 2.2 Duplicate `render_markdown()` definitions

### Location

There are two `render_markdown()` functions:

- one in the earlier rendering section
- one later as the “single comprehensive .md report” version

### Problem

Python silently keeps the **last definition**.

That means:

- the first `render_markdown()` is dead code,
- the script violates its own claim of “single implementation of each function”,
- future maintenance becomes dangerous because a reader may edit the wrong one.

### Severity

**High**

### Fix

Delete the older `render_markdown()` completely.

Keep only the final comprehensive one that writes the single report.

---

## 2.3 CLI docstring does not match actual argument parser

### Docstring claims usage like

- `--ci`
- `--update-trend`
- `--reset-auto-policy`

### Actual `main()` supports only

- `--root`
- `--out`
- `--show-intended`
- `--no-fail`

### Problem

The script documentation is misleading.

### Severity

**Medium**

### Fix

Either:

1. remove those claims from the docstring, or
2. implement the missing flags.

Given your latest instruction that the auditor should focus on **one `.md` report only**, the better path is:

- remove trend/JSON/reset-auto-policy from the primary workflow,
- keep only the minimal CLI,
- optionally add hidden advanced flags later.

---

## 2.4 Domain rendering bug: many findings will not appear in the “by domain” report sections

### Problem

Many checks add findings with `domain` values like:

- `services`
- `routers`
- `controllers`
- `models`
- `providers`

But both console rendering and markdown rendering only iterate over a fixed list:

- `repo`
- `backend`
- `database`
- `frontend`
- `security`
- `docs`
- `infra`

### Impact

Findings from very important checks may be counted in the scorecard, but **not shown in the domain sections**.

This is especially dangerous for:

- move suggestions,
- surface/domain matrix findings,
- domain placement findings.

### Severity

**High**

### Fix

Use a dynamic domain list:

- collect all `finding.domain` values,
- sort them,
- render all of them.

Or standardize domain tagging:

- use logical domains only (`backend`, `database`, `security`, etc.),
- add a separate `layer` field if needed.

---

# 3. Major dead code / unwired code

This is one of the biggest problems in the current script.

A lot of code exists, but is never called.

---

## 3.1 Entire “Circuit Enforcement Checks” section is mostly unwired

The script defines these functions:

- `check_circuit_import_direction()`
- `check_layer_operations()`
- `check_surface_in_domain_layer()`
- `check_middleware_service_import()`
- `check_provider_upward_import()`
- `check_controller_db_writes()`
- `check_router_business_logic()`
- `check_cross_domain_import()`

### Problem

`main()` does **not** call them.

Instead, `main()` calls older checks such as:

- `check_layer_writes()`
- `check_dependency_graph()`

### Impact

The “new circuit enforcement” model discussed in the brainstorming is **not actually active**.

That is a major gap because the discussion explicitly says the auditor must be a **circuit enforcer**, not just a linter.

### Severity

**High**

### Fix

You have two options:

#### Option A — Wire them properly

Add a dedicated phase in `main()`:

- circuit import direction
- middleware-to-service violation
- provider upward imports
- controller DB writes
- router business logic
- cross-domain imports

#### Option B — Remove them

If you do not want duplicate logic, delete them and strengthen the existing checks.

But in my opinion, **Option A is better**, because these checks represent the real architectural intent.

---

## 3.2 `emit_scaffolding_contract()` is defined but never called

### Problem

The discussion specifically wanted a scaffolding contract for AI file placement.

The function exists, but `main()` never calls it.

### Severity

**Medium**

### Fix

Since you now want **one `.md` only**, you probably should:

- **not** emit JSON,
- instead embed the scaffolding contract inside the markdown report.

In fact, the final markdown already includes an AI placement contract via `generate_ai_placement_contract()`.

So the JSON emitter can be removed or made optional.

---

## 3.3 `reconcile_auto_policy()` is defined but never called

### Problem

The script claims safe self-learning auto-policy support, but the reconciliation function is not used.

### Severity

**Medium**

### Fix

Either:

- remove it,
- or wire it if you want hidden local learning state.

Given your latest preference for a single report and no extra artifacts, I recommend:

- keep auto-learning **in-memory only**,
- remove persistent auto-policy JSON unless explicitly requested.

---

## 3.4 Registry / CODEOWNERS / graph emission functions are dead

Defined but not called:

- `emit_registry()`
- `emit_codeowners()`
- `emit_graph_mermaid()`
- helper functions around them

### Severity

**Medium**

### Fix

Remove them from the default auditor.

If needed later, move them into a separate optional governance-export script.

---

## 3.5 Trend functions are dead in the current `main()`

Defined but not used:

- `print_trend()`
- `update_trend()`
- `read_json()`

### Severity

**Low to Medium**

### Fix

Since your latest direction says no unnecessary JSON/output files, either:

- remove trend reporting from this script,
- or move it to a separate optional tool.

---

## 3.6 `write_move_map()` is dead

### Problem

It writes JSON move maps, but is not called.

### Severity

**Low**

### Fix

Remove it.

The move suggestions are already embedded in the final markdown report.

---

## 3.7 `write_metrics_json()` is dead

### Problem

Not called by `main()`.

### Severity

**Low**

### Fix

Remove it.

---

## 3.8 Unused top-level circuit constants

These are defined:

- `CIRCUIT_LAYERS`
- `LAYER_IMPORT_RULES`
- `LAYER_FORBIDDEN_IMPORTS`
- `LAYER_OPERATIONS`
- `SURFACE_NAMES`
- `DOMAIN_NAMES`

### Problem

Most of these are not used as the actual source of truth.

For example:

- `check_circuit_import_direction()` uses `CIRCUIT_LAYER_ORDER`
- actual dependency checks use `eff["forbidden_edges"]`
- surface/domain checks use `eff["surface_names"]`

So these Section 3 constants are mostly decorative.

### Severity

**Medium**

### Fix

Either:

- remove them,
- or make them the actual canonical model and wire them consistently.

Right now they create the illusion of a formal circuit model that is not really in force.

---

# 4. Duplicate / conflicting logic

This is a major source of future drift.

---

## 4.1 Two different placement engines exist at the same time

You now have:

### Engine A — deterministic placement engine

- `_pl_*`
- `check_move_suggestions()`

### Engine B — auto-learning engine

- `learn_domain_model()`
- `infer_auto_domain()`
- `analyze_domain_placement()`
- `check_domain_placement()`

### Problem

Both produce placement recommendations.

They can disagree.

They also use different signal models:

- `_pl_extract_signals()`
- `extract_auto_signals()`

### Severity

**High**

### Fix

Choose one authoritative engine.

My recommendation:

- keep the deterministic `_pl_*` engine as the primary move-suggestion engine,
- keep auto-learning only as a **discovery / candidate-domain helper**, not as a second move engine.

Otherwise the report can contain contradictory advice.

---

## 4.2 Duplicate DB-write checks

You have:

- `check_layer_operations()`
- `check_controller_db_writes()`
- `check_layer_writes()`

All overlap.

### Problem

If you wire all of them, you will create duplicate findings.

### Severity

**Medium**

### Fix

Keep one authoritative implementation.

Best choice:

- keep `check_layer_writes()` as the main AST write-check,
- remove or refactor the other two into helper functions.

---

## 4.3 Duplicate surface-in-domain checks

You have:

- `check_surface_in_domain_layer()`
- `check_surface_domain_matrix()`
- plus parts of `check_subfolder_axis_and_shape()`

### Problem

They overlap and are not consistent about which layers they cover.

For example:

- one checks `services/models/providers/events/jobs`
- another checks `services/models/controllers`

### Severity

**Medium**

### Fix

Create one single function:

- `check_grouping_axis()`

That function should enforce:

- routers: surface or allowed domain
- controllers: canonical axis (decide surface or domain)
- services/models/providers/events/jobs: domain only

Then remove the overlapping functions.

---

# 5. Major architectural contradictions inside the script

These are not just code bugs. They are design contradictions.

---

## 5.1 Controllers: surface vs domain is contradictory

This is one of the most important issues.

### The script contradicts itself

#### Docstring says

- `controllers/` grouped by **surface**

#### Later rendering / scaffolding says

- `controllers/` grouped by **domain**

#### Code behavior says

- `check_surface_domain_matrix()` treats `controllers/` as a **domain layer**
- `check_move_suggestions()` treats `controllers/` as a **domain layer**

### Why this matters

This directly affects whether folders like these are legal:

- `backend/controllers/admin/`
- `backend/controllers/supplier/`

or whether only these are legal:

- `backend/controllers/finance/`
- `backend/controllers/orders/`

### Severity

**High**

### Fix

You must make one final decision.

Based on the latest plan in the discussion, the stronger model is:

- **routers = surface**
- **controllers = domain**
- **services = domain**
- **models = domain**

If you choose that, then update:

- docstring,
- intended tree,
- scaffolding contract,
- all checks,
- all examples.

If you instead choose the older DIR_AUDIT model where controllers are surface-based, then the code must be changed substantially.

My recommendation:

### Final recommended rule

- `routers/` = surface
- `controllers/` = domain
- `services/` = domain
- `models/` = domain
- `providers/` = domain/adapter
- `events/` = domain
- `jobs/` = domain

That is cleaner for bounded contexts.

---

## 5.2 Surface names and domain names overlap dangerously

### Problem

`DEFAULT_SURFACE_NAMES` includes:

- `supplier`
- `customer`

But your domain taxonomy also includes:

- `supplier`
- `customer`

### Impact

Several checks will incorrectly flag valid domain folders as illegal surface folders.

For example:

- `backend/services/supplier/`
- `backend/services/customer/`

may be flagged as:

- “surface folder inside domain layer”

even though they are valid domains.

### Severity

**Very High**

This is one of the biggest false-positive risks in the whole script.

### Fix

You need context-aware disambiguation.

Recommended logic:

- if a folder name is a **known domain**, allow it in domain layers,
- only flag it as a surface violation if it is **surface-only** and not a domain.

In other words:

```text
if name in domains:
    allowed in services/models/providers
elif name in surfaces:
    violation in services/models/providers
```

Do not blindly flag all surface names.

---

## 5.3 `comms` vs `communication` canonical mismatch

### Problem

Your discussion sometimes uses:

- `comms/`

But the taxonomy canonicalizes:

- `comms -> communication`

The placement engine may therefore tell you to rename:

- `backend/services/comms/`

to:

- `backend/services/communication/`

### Severity

**Medium**

### Fix

Decide canonical domain names explicitly.

Either:

- make `comms` canonical,
- or make `communication` canonical and update the discussion/docs.

Then make the auditor accept only the canonical name.

---

## 5.4 `country` vs `geography`

### Problem

Earlier discussion used:

- `models/geography/`

Current script uses:

- `country` domain

### Severity

**Low to Medium**

### Fix

Pick one canonical name.

Recommended:

- use `geography` as the domain,
- keep `country` as an alias.

Or vice versa, but do not leave both alive informally.

---

## 5.5 Circuit-order logic conflicts with allowed-import logic

### Problem

`check_circuit_import_direction()` only checks upward/downward layer order.

But real architecture rules are not purely linear.

Example:

- routers may need to import middleware helpers or dependencies,
- even though middleware is “above” routers in request flow.

So a pure order check can create false positives.

### Severity

**Medium**

### Fix

Do not rely only on layer order.

Use an explicit allowed-import matrix:

- layer A may import layer B
- layer A may not import layer C

That matrix should be YAML-driven.

---

# 6. Hardcoded policy that should be externalized

The script already moved some policy into YAML, but not enough.

---

## 6.1 Circuit model is still hardcoded

Currently hardcoded:

- `CIRCUIT_LAYER_ORDER`
- `LAYER_IMPORT_RULES`
- `LAYER_FORBIDDEN_IMPORTS`
- `LAYER_OPERATIONS`

### Problem

This is core architecture policy.

It should not live in Python.

### Fix

Move to YAML:

- `layer_rules.yaml`
- or `governance.yaml`

Define:

- layer order,
- allowed imports,
- forbidden imports,
- allowed DB operations,
- forbidden symbols per layer.

---

## 6.2 Domain taxonomy is hardcoded

`PLACEMENT_DOMAIN_KEYWORDS` is a huge hardcoded dictionary.

### Problem

This is business-domain policy.

It should be configurable.

### Fix

Move to YAML:

```yaml
domains:
  finance:
    keywords: [...]
  treasury:
    keywords: [...]
  orders:
    keywords: [...]
```

Then Python only executes the policy.

---

## 6.3 Stop tokens / stable tokens are hardcoded

Examples:

- `PLACEMENT_STOP_TOKENS`
- `PLACEMENT_FOLDER_STABLE_TOKENS`
- `PLACEMENT_SKIP_PARTS`

### Fix

Move to config under:

```yaml
placement:
  stop_tokens:
  folder_stable_tokens:
  skip_parts:
```

---

## 6.4 Security / performance / quality rules are still mostly hardcoded

Examples:

- `ENH_SECRET_LITERAL_RES`
- `ENH_DANGEROUS_CALLS`
- `ENH_BLOCKING_CALLS`
- `ENH_QUERY_ATTRS`
- `ENH_TODO_RE`
- `ENH_FRONTEND_DEBUG_RE`
- file line limit
- function line limit

### Fix

Move to YAML:

```yaml
security:
  secret_patterns:
  dangerous_calls:
performance:
  blocking_calls:
  query_attrs:
quality:
  max_file_lines:
  max_function_lines:
```

---

## 6.5 Frontend role-page rules are hardcoded

`check_frontend_role_pages()` hardcodes:

- admin required pages
- supplier required pages
- logistics-partner required pages
- customer root pages

### Fix

Move to YAML:

```yaml
frontend:
  web_app:
    roles:
      admin:
        required_pages:
        optional_pages:
      supplier:
        required_pages:
```

---

## 6.6 Debt score weights are hardcoded

`compute_debt_score()` has many hardcoded weights.

### Fix

Move to YAML:

```yaml
debt_weights:
  red: 100
  yellow: 15
  DG2: 35
  DG3: 50
```

---

## 6.7 Ghost backend candidates are hardcoded

`check_ghost_backend()` only checks:

- `scripts/backend`
- `Working_API`

### Fix

Move to config:

```yaml
forbidden_ghost_backends:
  - scripts/backend
  - Working_API
```

---

## 6.8 RLS detection pattern is hardcoded

`check_rls_cluster()` looks for filenames starting with:

- `rls_`
- `country_rls`

### Fix

Move to config:

```yaml
security:
  rls_filename_patterns:
    - "^rls_.*"
    - "^country_rls$"
```

---

# 7. Missing or incomplete implementation of discussion points

Now let’s audit the script against the discussion itself.

---

## 7.1 “Draw the grid line” — partially done

### Present

- The circuit is described in comments.
- Layer concepts exist.
- Intended tree exists.

### Missing

- The circuit is not fully enforced.
- Circuit checks are unwired.
- Layer contracts are not consistently applied.

### Status

**Partial**

---

## 7.2 “Which files cross the line and why” — mostly done

### Present

- move suggestions,
- domain placement,
- forbidden edges,
- wrong-folder detection.

### Missing

- better explanation of why a file belongs to a domain,
- clearer confidence breakdown,
- less conflict between deterministic and auto-learning suggestions.

### Status

**Mostly done, needs consolidation**

---

## 7.3 “Recommendation for changes” — done, but noisy

### Present

- intended home,
- move commands,
- remediation hints.

### Problem

- two engines can produce overlapping advice,
- some recommendations can conflict,
- domain rendering bug hides some recommendations.

### Status

**Partial**

---

## 7.4 “Backend circuit for large project” — partially done

### Present

- layer model,
- dependency checks,
- write-location enforcement.

### Missing

- full enforcement of:
  - middleware → service violation,
  - provider upward imports,
  - router business logic,
  - utils purity,
  - db infrastructure isolation,
  - events/jobs rules,
  - dependencies rules.

### Status

**Partial**

---

## 7.5 “Middleware position in circuit” — weakly implemented

### Present

- middleware package expected,
- raw env read check,
- multiple RLS enforcer check.

### Missing

- middleware → service import check is not wired,
- no middleware layering/order validation,
- no validation of security pipeline stages,
- no validation of request context population.

### Status

**Weak / Partial**

---

## 7.6 “Domain and sub-domain alignment” — partially done

### Present

- domain taxonomy,
- domain inference,
- domain placement suggestions.

### Missing

- true sub-domain modeling,
- flow-type classification,
- operation-to-surface mapping,
- file-content-to-filename alignment.

### Status

**Partial**

---

## 7.7 “Indicative file names” — only partially addressed

### Present

- domain inference from names,
- move suggestions.

### Missing

The discussion explicitly wanted names that answer:

- WHAT does it do?
- WHO is it for?

The script does not truly validate naming conventions.

It does not reliably flag:

- `orders.py` as non-indicative,
- `admin.py` as too generic,
- `media_models.py` as weak,
- `commission.py` as under-specified.

### Status

**Missing / Weak**

---

## 7.8 “Inside-file content analysis” — partially done

### Present

It checks:

- DB writes,
- imports,
- secrets,
- dangerous calls,
- blocking calls,
- query-in-loop,
- print/debug,
- TODO debt,
- oversized functions/files.

### Missing

It does not really check:

- whether functions match the file name,
- whether a file mixes multiple domains,
- whether admin-only operations appear in customer files,
- whether supplier operations appear in customer surfaces,
- whether a file needs to be split.

### Status

**Partial**

---

## 7.9 “Flow-type classification” — missing

The discussion wanted:

- one-way flow,
- two-way flow,
- tree flow,
- multi-way flow.

The script does not model this at all.

### Status

**Missing**

---

## 7.10 “Surface × Domain matrix” — partially done

### Present

- `check_surface_domain_matrix()`
- frontend role-page checks

### Problem

- false positives due to surface/domain overlap,
- controller axis contradiction,
- incomplete layer coverage.

### Status

**Partial**

---

## 7.11 “Single .md report only” — mostly done, but dead code remains

### Present

- final markdown report is comprehensive,
- main writes one `.md`.

### Problem

Dead code still exists for:

- JSON metrics,
- move maps,
- registry,
- CODEOWNERS,
- trend files,
- scaffolding JSON.

### Status

**Mostly done, needs cleanup**

---

# 8. Rule-level audit: rules defined but not implemented correctly

---

## 8.1 `H1` is defined but not implemented

`RULE_MEANING` defines:

- `H1`: `sys.path.insert/append`

But there is no check emitting `H1`.

### Fix

Add a check for:

- `sys.path.insert`
- `sys.path.append`

or remove the rule.

---

## 8.2 `P2` is defined but not implemented

`P2` says:

- controller file outside controllers/

But no check emits `P2`.

### Fix

Add a check that detects controller-like files outside `controllers/`.

Examples:

- files ending in `_controller.py`
- classes ending in `Controller`
- controller route orchestration logic outside the layer

Or remove the rule.

---

## 8.3 `A1` is overloaded

Currently `A1` is used for:

- architecture hotspot,
- alembic diagnostics/stub issues.

That is confusing.

### Fix

Split into:

- `A1` = architecture hotspot,
- `DB3` = alembic diagnostics/stub/fracture issue.

---

## 8.4 `AUTO*` rules are mostly dead

These exist:

- `AUTO0`
- `AUTO3`
- `AUTO6`
- `AUTO8`
- `AUTO10`

But they are mainly tied to `reconcile_auto_policy()`, which is not called.

### Fix

Either:

- wire auto-policy reconciliation,
- or remove these rules from the active dictionary/hotlist.

---

## 8.5 `T1` trend rule is dead

Trend reporting is not wired.

### Fix

Remove or implement.

---

# 9. False-positive risks and logic weaknesses

These are very important if you want the auditor to be trusted.

---

## 9.1 Duplicate basename detection is too aggressive

`check_duplicate_basenames()` flags the same module basename in multiple directories.

### Problem

This is often valid.

Example:

- `routers/admin/orders.py`
- `routers/supplier/orders.py`
- `routers/customer/orders.py`

That is not necessarily an import shadow.

### Severity

**High**

### Fix

Refine `D1`:

- allow same basename in different surface packages,
- only flag infrastructure duplicates (`database.py`, `config.py`, `schemas.py`, etc.),
- or flag only when module path ambiguity is real.

---

## 9.2 Domain-layer surface detection can falsely flag valid domains

Already mentioned, but worth repeating:

- `services/supplier/`
- `services/customer/`

can be falsely flagged because those names are both surfaces and domains.

### Severity

**Very High**

---

## 9.3 `check_cross_domain_import()` would be too strict if wired as-is

If there is no explicit domain policy, it flags all cross-domain imports.

That may be too aggressive.

### Fix

Only emit `DG3` when:

- ownership policy exists,
- and the target domain is not in `may_import`.

Do not fail all cross-domain imports by default unless you intentionally want strict mode.

---

## 9.4 Provider rules are incomplete

Current default forbidden edges do not fully match the discussion.

### Discussion says providers may only import utils

But current defaults may allow:

- providers → models

### Fix

Forbid:

- providers → services
- providers → controllers
- providers → routers
- providers → models
- providers → middleware

---

## 9.5 Middleware rules are incomplete

The default forbidden edges do not explicitly forbid:

- middleware → services
- middleware → controllers
- middleware → routers
- middleware → models

But the discussion explicitly identified middleware-to-service as a violation.

### Fix

Add those forbidden edges.

---

## 9.6 Utils purity is not checked

The discussion says utils should be pure helpers.

But the script does not check whether utils import:

- models,
- db,
- services,
- request/context machinery.

### Fix

Add a utils-purity check.

---

## 9.7 Models purity is not fully checked

The script partially checks forbidden model imports, but not comprehensively.

Models should not import:

- routers,
- controllers,
- services,
- providers,
- middleware,
- FastAPI request/response objects.

### Fix

Add a strict model-purity check.

---

## 9.8 Dead-module exemptions are inconsistent

`DEFAULT_DEAD_AUDIT_LAYERS` includes:

- providers
- events
- jobs

But `DEFAULT_DEAD_EXEMPT_LAYERS` also includes them.

So they are effectively skipped.

### Problem

The discussion wanted detection of unused:

- providers,
- middleware,
- utils,
- controllers,
- services.

### Fix

Rethink exemptions.

Possible rule:

- exempt entrypoint-like layers,
- but still audit providers/events/jobs for dead code.

---

# 10. Missing advanced checks needed to fully capture the discussion

These are the “next level” improvements.

---

## 10.1 File-name-to-content alignment

The auditor should verify that a file’s contents match its name.

Examples:

- `order_fulfillment_service.py` should contain fulfill/pack/ship logic,
- `order_tracking_controller.py` should not contain payout logic,
- `product_moderation_service.py` should not send email.

### Needed checks

- extract function names,
- extract class names,
- extract route tags,
- extract table names,
- compare against filename/domain signals,
- detect mixed-domain files.

---

## 10.2 Split-file detection

The discussion explicitly asked:

> if a file needs breaking, then which domain/folder belonging?

The script does not really detect that a file should be split.

### Needed check

If one file contains strong signals for multiple domains:

- finance + communication,
- orders + logistics,
- catalog + ai,

then emit:

- “file should be split into domain-specific services”

---

## 10.3 Surface-appropriate operation validation

You need checks like:

- customer router should not contain `approve_supplier()`
- supplier router should not contain `configure_platform_commission()`
- logistics router should not contain `create_product()`

### Needed model

Define in YAML:

```yaml
surfaces:
  admin:
    allowed_operations:
      - moderate
      - override
      - monitor
      - configure
  supplier:
    allowed_operations:
      - pack
      - ship
      - upload
      - fulfill
  customer:
    allowed_operations:
      - browse
      - track
      - cancel
      - return
```

Then compare function names/routes against allowed operations.

---

## 10.4 Flow-type modeling

The discussion wanted flow types:

- forward-flow,
- backward-flow,
- two-way,
- tree-flow,
- multi-way.

This is not implemented.

### Needed model

Example YAML:

```yaml
flows:
  orders:
    customer: forward
    supplier: forward
    logistics: forward
    admin: oversight
  finance:
    customer: one_way_in
    supplier: one_way_out
    admin: tree
```

Then auditor can validate:

- endpoint verbs,
- service operations,
- cross-surface calls.

---

## 10.5 Naming convention enforcement

The script should not only suggest moves, but also detect weak names.

Examples:

- `orders.py`
- `admin.py`
- `utils2.py`
- `helper.py`
- `media_models.py`

### Needed checks

- generic-name detection,
- missing operation group in filename,
- missing surface context where required,
- inconsistent suffixes (`_service`, `_controller`, `_entities`).

---

## 10.6 Package contract validation

For each domain package, enforce expected shape.

Example:

```text
services/finance/
  __init__.py
  payment_processing_service.py
  payout_execution_service.py
  ledger_service.py
```

### Needed checks

- missing `__init__.py`,
- empty domain package,
- oversized package,
- missing expected service types,
- missing model package for a domain that has services.

---

## 10.7 Middleware pipeline validation

The discussion described middleware layers:

- foundation,
- security,
- rate limit,
- geo/country,
- observability,
- compliance.

The script does not validate this.

### Needed checks

- required middleware present,
- middleware order correct,
- no middleware importing services,
- context fields populated (`request.state.request_id`, etc.).

---

## 10.8 Required project files validation

The target structure discussed required files like:

- `.gitignore`
- `.env.example`
- `.aiignore`
- `README.md`
- `docker-compose.yml`
- `Makefile` / `justfile`

The script only checks some forbidden files and gitignore.

### Needed check

Add required-file validation.

---

## 10.9 Scope documentation validation

The discussion wanted `documents/scope/` to be authoritative.

The script checks some allow-lists, but does not validate:

- required scope docs exist,
- YAML and docs agree,
- every domain has a scope document,
- every major layer has a spec.

### Needed check

Add documentation governance.

---

## 10.10 API shape validation

The script does not check:

- route prefixes align with surface,
- OpenAPI tags align with domain,
- routers mount correctly,
- endpoint naming conventions.

### Needed check

Parse FastAPI route decorators and validate:

- prefix,
- tags,
- methods,
- filename,
- surface/domain alignment.

---

## 10.11 True import graph completeness

Current import resolution is approximate.

It may miss:

- `from . import x`
- conditional imports,
- `TYPE_CHECKING` imports,
- dynamic imports with non-constant targets,
- re-exports through `__init__.py`.

### Needed improvement

Build a more complete module resolver.

---

## 10.12 Call graph, not just import graph

Right now the script checks imports.

It does not check actual calls.

Example:

- controller imports service but calls DB directly anyway,
- provider imports utils but secretly reaches into service via injected object.

### Advanced improvement

Build a lightweight call graph for:

- session writes,
- provider usage,
- service-to-service calls,
- controller-to-service calls.

---

## 10.13 Domain event / bounded-context validation

The script does not check whether cross-domain communication happens through events/facades.

### Needed check

If domain A needs domain B:

- allowed only through explicit service facade,
- or through events,
- not by importing internal helpers.

---

## 10.14 Architectural metrics beyond fan-in/fan-out

Current metrics are useful but basic.

### Add

- instability index,
- abstractness,
- distance from main sequence,
- god-module detection,
- domain coupling score,
- layer coupling score,
- change hotspot if git history is available.

---

## 10.15 Security advanced checks

Current security checks are decent but not complete.

### Add

- raw SQL injection risk,
- path traversal risk,
- SSRF risk,
- unsafe redirect,
- JWT secret handling,
- password hashing checks,
- CORS policy validation,
- CSRF presence,
- permission decorator validation.

---

## 10.16 Performance advanced checks

Current checks:

- blocking async,
- query-in-loop.

### Add

- missing pagination,
- unbounded queries,
- large transaction risk,
- missing indexes from model definitions,
- repeated cache access patterns,
- N+1 relationship loading patterns.

---

## 10.17 Frontend advanced checks

Current frontend checks are good but not enough.

### Add

- feature-folder ownership,
- component-domain alignment,
- shared-package boundary rules,
- state-management boundary rules,
- API-client boundary rules,
- page/screen naming conventions,
- mobile-app role structure.

---

# 11. What the script already does well

To be fair, many parts are strong.

---

## 11.1 Strong structure/hygiene checks

It already detects:

- bad root files,
- scratch scripts,
- cache directories,
- lockfile drift,
- ghost backend,
- duplicate basenames,
- secrets on disk,
- hardcoded local paths,
- media-on-disk,
- weak gitignore.

This is valuable.

---

## 11.2 Good dependency-graph foundation

The AST-based module graph is a major improvement over regex-only auditing.

---

## 11.3 Good domain placement intent

The move-suggestion engine is conceptually correct.

---

## 11.4 Good enhanced checks

The security/performance/quality section is one of the strongest parts.

It catches:

- hardcoded secrets,
- dangerous calls,
- async blocking,
- query-in-loop,
- weak exception handling,
- oversized code,
- print/debug noise,
- frontend debug statements.

---

## 11.5 Good single-report direction

The final comprehensive markdown report is exactly aligned with your latest instruction.

---

# 12. Recommended remediation plan

Here is the best order to fix everything.

---

## Phase 0 — Stabilize runtime

Fix these first:

1. define missing `AUTO_ROUTE_PREFIX_RE` and `AUTO_ROUTE_DECOR_RE`
2. remove duplicate `render_markdown()`
3. fix domain rendering so no findings are hidden
4. fix CLI/docstring mismatch
5. remove or wire dead code that can crash or confuse

---

## Phase 1 — Resolve architectural contradictions

Decide and enforce:

1. controllers = domain or surface?
2. which names are surfaces, which are domains?
3. which domains are canonical (`comms` vs `communication`, `country` vs `geography`)
4. which layers may import which layers?

Then update:

- docstring,
- intended tree,
- YAML,
- all checks.

---

## Phase 2 — Wire the real circuit enforcer

Activate or consolidate:

- middleware → service violation,
- provider upward imports,
- controller DB writes,
- router business logic,
- cross-domain ownership violations,
- forbidden layer edges.

Do not leave Section 10 dead.

---

## Phase 3 — Remove duplicate engines

Consolidate:

- placement engine,
- auto-learning engine,
- DB-write checks,
- surface/domain checks.

You should have:

- one authoritative placement engine,
- one authoritative layer-contract checker,
- one authoritative grouping-axis checker.

---

## Phase 4 — Externalize remaining policy

Move to YAML:

- circuit model,
- domain taxonomy,
- stop tokens,
- security patterns,
- performance patterns,
- quality thresholds,
- frontend role pages,
- debt weights.

---

## Phase 5 — Add missing discussion features

Implement:

- naming convention validation,
- file-content-to-name alignment,
- split-file detection,
- surface-operation validation,
- flow-type classification,
- required-file validation,
- scope-doc validation.

---

## Phase 6 — Advanced governance

Add:

- better import resolution,
- call graph,
- richer metrics,
- suppressions/waivers,
- diff mode,
- CI annotations,
- dependency vulnerability scanning,
- frontend architecture rules,
- middleware pipeline validation.

---



















































































