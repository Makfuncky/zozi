#!/usr/bin/env python3
"""Script to write the full FEATURES_LIST.md content."""
import os

CONTENT = r"""# ZOZI E-Commerce — Full Feature List

> **Last Updated:** March 28, 2026 | Cross-referenced against `CODEBASE_STATUS_MATRIX_DETAILED.md`
> Features marked **✅ LIVE** are fully implemented and tested. **⚠️ PARTIAL** are in progress. **❌ PLANNED** are not yet built.

---

# 🛍️ Customer Features

### 🔐 Authentication & Account
- **✅ Email/Password Login & Registration** — JWT-based auth, CSRF protection, lockout after 5 failed attempts (15 min Redis-backed)
- **✅ Google OAuth Login** — Google ID-token flow; popup and redirect modes; One Tap pending
- **✅ Email Verification** — Verification link on register; re-send available; gate mode configurable via `CUSTOMER_EMAIL_VERIFICATION_MODE`
- **✅ Forgot Password / Reset** — Token-based password reset with expiry; generic messages to prevent enumeration
- **✅ Token Refresh** — Automatic JWT refresh on 401; PushTokenSync on login/logout

### 👤 Profile & Settings
- **✅ View & Edit Profile** — `GET/PATCH /users/me`; phone field-encrypted at rest
- **✅ Change Password** — `POST /users/me/change-password`; re-auth required
- **✅ Settings Screen** — Locale, currency, theme preferences
- **❌ Avatar Upload** — Planned; endpoint scaffolded
- **❌ Social OAuth Link/Unlink** — Planned for Facebook parity

### 📍 Address Book
- **✅ CRUD Addresses** — `GET/POST/PUT/DELETE /users/me/addresses/*`; all address fields field-encrypted
- **✅ Set Default Address** — `PATCH /users/me/addresses/{id}/default`
- **✅ Audit Logged** — All create/update/delete/set-default actions audit-trailed
- **❌ Google Maps Autocomplete** — Planned; address validation API integration

### 🛍️ Product Catalog & Browsing
- **✅ Product Listing** — Grid layout; category filter; badge filters (hot/featured/new/deals)
- **✅ Category Navigation** — Hierarchical category tree; `GET /categories`
- **✅ Quick Filters** — Price range, badges, supplier filter; all NULL-safe backend filters
- **✅ Seasonal Banners** — DB-backed banner stack; theme-aware shadows and gradients
- **❌ Infinite Scroll** — Planned; skeleton loading in place
- **❌ Video Product Cards** — Planned

### 🔍 Product Search
- **✅ Full-Text Search** — `GET /search?q=&limit=`; FTS indexed; q max 200 chars, limit max 60
- **✅ Live Search Bar** — Web: inline component; Mobile: hero search with AI/chatbot integration
- **✅ Search Results Page** — 14 mobile tests; web search filter panel
- **❌ Voice Search** — Planned
- **❌ Saved Searches** — Planned
- **❌ Search Analytics** — Planned

### 💡 Product Recommendations Engine
- **✅ 5-Signal Blend** — Browse history + purchase history + wishlist (0.3 pts/item) + price-band (avg ±0.4–2.5) + item-item collaborative filtering
- **✅ Redis Cache** — `rec:{user_id}:{limit}:{hash}` key; 300s TTL
- **❌ User-User ML Model** — Planned; user-user collaborative filtering to complement item-item signals

### 📦 Product Detail Page
- **✅ Full Product View** — Name, price, description, supplier badge, images, reviews
- **✅ Offer Badges** — Flash sale (red), Supplier Discount (lime-green 🏷), Promotional (orange)
- **✅ Supplier Credibility Badge** — Score-based badge level shown inline
- **❌ Video Gallery / 360° View / AR Preview** — Planned

### ⭐ Reviews & Ratings
- **✅ View Reviews** — Star rating display on product cards and detail page
- **✅ Write Review** — `POST /reviews`; verified-purchase guard enforced server-side; auth-required
- **❌ Review Images/Video** — Planned
- **❌ Helpful Vote** — Planned
- **❌ Moderation Queue** — Planned

### ❤️ Wishlist
- **✅ Add / Remove Products** — `GET/POST/DELETE /wishlist/*`; auth-required
- **✅ Wishlist Grid** — 2-col responsive grid; add-to-cart from wishlist; pull-to-refresh (mobile)
- **✅ Recommendation Feed** — Wishlist items feed the recommendation engine (+0.3 pts/item)
- **❌ Share Wishlist Link** — Planned
- **❌ Notify-on-Restock Toggle** — Planned
- **❌ Collaborative Lists** — Planned

### 🛒 Shopping Cart
- **✅ Cart CRUD** — `GET/POST/DELETE /cart/*`; auth-required; server-side for cross-device sync
- **✅ Quantity Management** — Add, remove, update quantity
- **✅ Cart Summary** — Line items; unit prices; totals; coupon field
- **❌ Save-for-Later** — Planned
- **❌ Cart Abandonment Recovery** — Planned

### 🏁 Checkout — 4-Step Flow
- **✅ Step 1: Address** — Pick from saved addresses or enter new
- **✅ Step 2: Delivery** — Shipping method selection (shipping zones)
- **✅ Step 3: Payment** — COD (active); Stripe/Tap (capability-gated)
- **✅ Step 4: Confirm** — Order summary; authoritative totals enforced server-side
- **❌ Apple Pay / Google Pay** — Planned (Stripe Payment Request Button + Tap Apple Pay)
- **❌ Address Autocomplete** — Planned (Google Maps)

### 💳 Payment Processing
- **✅ Cash on Delivery (COD)** — Active production checkout path; reserves inventory immediately
- **⚠️ Stripe** — Integration built; capability-gated until bank onboarding complete
- **⚠️ Tap Payments** — Integration built; capability-gated until bank onboarding complete
- **✅ Webhook Validation** — HMAC validation on Stripe + Tap webhooks; idempotent event processing
- **✅ Refund Routing** — `chg_*` → Tap refund; `pi_*/py_*` → Stripe refund
- **❌ Saved Payment Methods / Vault** — Planned (PCI-DSS Stripe/Tap vault)

### ⚡ Flash Sales & Promotional Offers — Customer View
- **✅ Flash Sales Page** — `GET /flash-sales` (public); countdown timer display
- **✅ Offers Page** — Three offer slots: Flash Sales, Promotional Offers, Supplier Discounts
- **✅ Inline Product Badges** — Flash sale (red), Supplier Discount (lime-green), Promotional (orange)
- **✅ Seasonal Banner Stack** — DB-backed; shown on products page home
- **❌ Flash Sale Countdown Push Notification** — Planned

### 🎟️ Coupons & Discount Codes
- **✅ Apply Coupon at Checkout** — `POST /coupons/validate`; normalized uppercase; min-order enforced
- **✅ Coupon Validation** — Expiry, max-uses, and min-order-value enforced server-side
- **✅ Coupons List** — View available/active coupons
- **❌ Category/Product-Specific Coupons** — Planned
- **❌ First-Use Coupons** — Planned

### 📦 Order Placement & History
- **✅ Place Order** — `POST /orders`; multi-supplier split; inventory reserved
- **✅ Order History** — `GET /orders/*`; paginated list; status filters
- **✅ Order Detail** — Items, status, tracking, invoice link
- **✅ Cancel Order** — Inventory restored on cancel; refund routed appropriately
- **❌ Order Amendment Window** — Planned (short window to modify post-placement)

### 📍 Order Tracking
- **✅ Tracking Timeline** — `GET /orders/{id}/tracking`; full shipment event history
- **✅ Multi-Supplier Reconciliation** — Order not marked delivered until ALL shipments delivered
- **✅ Return Intent Summary** — Tracking payload includes return/replacement intent
- **❌ Real-Time WebSocket Push** — Planned
- **❌ GPS Map Widget** — Planned (connect lat/lng data)

### ↩️ Returns & RMA
- **✅ Submit Return Request** — `POST /returns`; return or replacement intent
- **✅ Return Status Tracking** — `GET /returns/{id}`; customer view of approval/completion
- **✅ Refund Processing** — Automatic routing to original payment provider on approval
- **❌ Return Policy Analytics** — Planned
- **❌ Configurable Return Windows** — Planned

### 🧾 Invoice Viewing
- **✅ View HTML Invoice** — `GET /invoices/{id}/html`; customer sees own invoices only
- **✅ Download PDF Invoice** — `GET /invoices/{id}/pdf` (binary PDF via ReportLab)

### 🔔 In-App Notifications
- **✅ Notification List** — `GET /notifications`; read/unread state
- **✅ Mark Read** — `PATCH /notifications/{id}/read`; triggered by doc approval, returns, low-stock, chatbot
- **❌ Mark-All-Read** — Planned
- **❌ Notification Preference Categories** — Planned

### 📱 Push Notifications
- **✅ Token Registration** — `POST /push/register` (Expo/FCM/APNs supported)
- **✅ Token Deregistration** — `DELETE /push/deregister` on logout; PushTokenSync hook
- **❌ Rich Push (images, action buttons)** — Planned
- **❌ Topic-Based Subscriptions** — Planned

### 📰 Newsletter
- **✅ Subscribe** — `POST /email/newsletter/subscribe`; auth-aware (uses real user email)
- **✅ Unsubscribe** — `POST /email/newsletter/unsubscribe`; unsubscribe page + preferences
- **✅ Preference Management** — Newsletter preference categories (pending backend toggles)
- **❌ Re-Engagement Campaigns** — Planned

### 🎫 Customer Support & Help
- **✅ Create Support Ticket** — `POST /tickets`; subject, description, priority; auth-required
- **✅ View Ticket Thread** — `GET /tickets/{id}`; full reply thread; admin vs customer reply styling
- **✅ Reply to Ticket** — `POST /tickets/{id}/reply`; closed/resolved guard prevents replying
- **✅ Help / Support Portal** — `/help/` page: ticket list with status icons for quick access
- **❌ WebSocket Real-Time Replies** — Planned
- **❌ SLA Breach Tracking** — Planned
- **❌ Priority Escalation Automation** — Planned

### 🤖 Chatbot / AI Assistant
- **✅ Conversational AI** — `POST /chatbot/message`; intent detection; context-aware follow-ups
- **✅ Product Suggestions** — Returns matching products in chatbot reply payload
- **✅ Session Memory** — Per-user 24h TTL + 10-message history cap (Redis)
- **✅ Floating Widget (Web)** — Yellow shadowed FAB; expands to popup panel
- **✅ Modal (Mobile)** — Opens as modal route from bottom FAB
- **❌ WebSocket Streaming Replies** — Planned
- **❌ Sentiment Analysis** — Planned

### 📷 Barcode Scan — Receipt Verify
- **✅ Scan Product Barcode** — `POST /product-verifications` (type: customer_receipt)
- **✅ Role Restriction** — Customer-only access to receipt checkpoint
- **❌ Photo Evidence Capture** — Planned
- **❌ Dispute Trigger on Failed Scan** — Planned

### ❌ Not Yet Implemented (Customer)
- **❌ Loyalty / Points System** — VIP tiers, points-on-purchase, balance view, redemption at checkout
- **❌ Referral System** — Referral codes, reward credits, referral tracking
- **❌ Product Comparison Tool** — Side-by-side spec comparison for 2–4 products
- **❌ Social Sharing** — Share products, wishlist, order confirmations via OS share sheet

---

# 🏭 Supplier Features

### 🔐 Supplier Auth & Registration
- **✅ Login** — Shared `/auth/login` with role=supplier enforcement
- **✅ Registration** — `POST /auth/register`; automatic supplier role assignment
- **✅ Supplier Onboarding** — Guide page at `supplier/guide/` with setup checklist
- **❌ Invite-Based Onboarding** — Planned

### 🏢 Supplier Profile Management
- **✅ View / Update Profile** — `PUT /supplier/profile`; business name, address, phone, tax — all field-encrypted
- **✅ Operating Regions** — `operating_regions` JSON field; governs product coverage
- **❌ Multi-Region Profile** — Planned
- **❌ Public Supplier Brand Page** — Planned (`/suppliers/{id}` public storefront)

### 📄 KYC Document Management
- **✅ Upload Documents** — `POST /supplier/documents`; supports multiple document types with expiry dates
- **✅ Document Status Tracking** — `GET /supplier/documents`; pending → approved → rejected
- **✅ Auto-Promote on Approval** — Doc approval sets `verification_status="verified"` + in-app notification + email
- **❌ Auto-Expiry Reminder** — Planned
- **❌ Document Version History** — Planned

### 📦 Product Management — CRUD
- **✅ Create Product** — `POST /supplier/products`; requires admin approval before customer visibility
- **✅ Edit Product** — `PUT /supplier/products/{id}`; includes discount pricing fields
- **✅ Delete Product (Soft-Delete)** — Product archived; not permanently removed; `is_deleted=True`
- **✅ Stock Management** — `PATCH /products/{id}/stock?delta=N`; delta patch (positive/negative)
- **✅ Low-Stock Email Alert** — Triggered at ≤5 units remaining
- **✅ AI Description Suggestion** — `POST /ai/suggest`; supplier can generate product description via AI (⚡ button)
- **✅ Image AI** — `POST /ai/image`; AI-generated product imagery
- **❌ Video Support** — Planned
- **❌ SKU Analytics** — Planned

### 📥 Bulk Import / Export
- **✅ CSV Export** — `GET /supplier/products/export`; downloads all supplier products as CSV (XSS-safe via `html.escape()`)
- **✅ CSV Import** — `POST /supplier/products/import`; validates and creates products in bulk; SSRF prevention (`image_url=None`)
- **❌ Error Report on Failed Rows** — Planned
- **❌ Async Bulk Jobs** — Planned

### 📊 Inventory Management
- **✅ Inventory View** — `GET /supplier/inventory`; paginated stock levels per product
- **✅ Stock Adjustment** — `PATCH /products/{id}/stock?delta=N`; audit-logged
- **❌ Reorder Automation** — Planned
- **❌ Multi-Location Stock** — Planned

### 📋 Order Management
- **✅ View Orders** — `GET /supplier/orders`; supplier sees only own-product orders
- **✅ Order Detail** — `GET /supplier/orders/{id}`; items, status, shipment info
- **✅ Update Order Status** — `PUT /supplier/orders/{id}/status`; audit-logged on every change
- **❌ Row-Level Visibility Upgrade** — Pending (supplier orders/logistics tables need same mirroring as admin)

### 🏷️ Shipping Label & Parcel Sheet
- **✅ Generate Shipping Label** — `GET /supplier/orders/{id}/label`; dedicated backend label payload (not client-stitched)
- **✅ Web Print** — Browser print from label page
- **⚠️ Mobile Print/Share** — Native `expo-sharing`+`expo-print` flow not yet built; label page exists on web only

### 🚚 Logistics & Shipping Zones
- **✅ Zone Management** — `/logistics/zones/*`; supplier-scoped zone definitions
- **✅ Carrier Templates** — `/logistics/carriers/*`; carrier templates for delivery options
- **❌ Live Carrier API Integration** — Planned (DHL, Aramex, FedEx)
- **❌ Multi-Carrier Rate Shopping** — Planned

### 📈 Analytics & Revenue Reports
- **✅ Dashboard Analytics** — `GET /supplier/analytics`; revenue, orders, top products
- **✅ Time-Series Reports** — `GET /supplier/analytics/timeseries`; revenue/order trends over time
- **✅ Product Performance** — `GET /supplier/products/performance`; per-SKU metrics
- **❌ Cohort Analysis** — Planned
- **❌ Export to PDF** — Planned

### 💰 Payout System
- **✅ View Payouts** — `GET /supplier/payouts`; payout history (pending → processing → completed)
- **✅ Request Payout** — `POST /supplier/payouts`; admin reviews and approves
- **❌ Auto-Payout on Threshold** — Planned
- **❌ Bank Transfer Integration** — Planned

### 📑 Commission & ZOZI Terms
- **⚠️ Terms Page** — `GET /supplier/terms`; static terms display; commission % model at page level only
- **❌ Dynamic Commission Rate Config** — Planned (admin-controlled per-supplier/category rates)
- **❌ Automated Commission Deduction** — Planned (auto-deduct on payout)

### 🏅 Credibility Badge System
- **✅ View Badge** — `GET /supplier/badge`; score + badge level (role-gated)
- **✅ Score Factors** — Orders completed + reviews received + documents approved + delivery timeliness
- **✅ Badge Display** — `SupplierBadge` component shown on all product cards
- **❌ Automated Badge Upgrade Notifications** — Planned
- **❌ Tiered Public Badge on Storefront** — Planned (requires public supplier page)

### 🏷️ Supplier Discounts & Promotional Pricing
> **Codebase location:** `products_controller.py` (detection) · `routers/supplier.py` (write) · `db/models.py` (fields) · `alembic/versions/j1k2l3m4n5o6` (migration)

- **✅ Set Discount Price** — Set `compare_price` (original/higher price) above current `price` on any product to activate a discount
- **✅ Time-Window Scheduling** — `discount_starts_at` and `discount_ends_at` (DateTime fields) control the active window
- **✅ Automatic Activation** — `is_supplier_discount_active()` in `products_controller.py` detects: `compare_price IS NOT NULL AND compare_price > price AND current datetime within window`
- **✅ Computed Offer Fields** — At API response time, sets: `offer_type="supplier_discount"` · `offer_title="Supplier Discount"` · `offer_discount_pct` (% saving) · `offer_starts_at` · `offer_ends_at`
- **✅ Lime-Green Badge** — 🏷 badge rendered on `ProductCard` (web + mobile) during active discount window
- **✅ Supplier Write Path** — `PUT /supplier/products/{id}` accepts `compare_price`, `discount_starts_at`, `discount_ends_at` in request body
- **✅ Customer Visibility** — Discount products surfaced in `/products?deals=true` and shown in `offers/` page alongside flash sales
- **✅ DB Migration** — `j1k2l3m4n5o6_add_supplier_discount_duration_fields.py` adds `discount_starts_at` + `discount_ends_at` columns to `products` table
- **✅ Tests** — Covered via `test_flash_sales.py` (14/14 passing; includes `compare_price` assertion tests)
- **✅ Matrix Row** — Section III: `🏷️ Supplier Discounts & Promotions` | **Status: 99%**
- **❌ Bulk Discount Scheduling** — Planned (schedule discounts on multiple products at once)
- **❌ Category-Level Promotions** — Planned
- **❌ Flash Deal Campaign Integration** — Planned (link supplier discounts to flash sale campaigns)

### 🧾 Supplier Invoices
- **✅ View Invoices** — `GET /invoices?supplier_id=`; paginated; supplier sees only own invoices
- **✅ Update Invoice Status** — `PATCH /invoices/{id}/status`; audit-logged
- **✅ HTML/PDF Invoices** — `GET /invoices/{id}/html` and `/pdf`
- **✅ Auto-Invoice on Shipment** — Invoice auto-created when shipment is created
- **❌ Invoice Dispute Flow** — Planned

### 🔍 Product Verification — Dispatch Checkpoint
- **✅ Log Verification** — `POST /product-verifications` (type: supplier_dispatch)
- **✅ Results** — passed / failed / partial; includes discrepancy payload + evidence URL
- **✅ Role Restricted** — Supplier restricted to `supplier_dispatch` checkpoint only
- **❌ Photo/Video Evidence UI** — Planned
- **❌ Automated Re-Dispatch on Failed Check** — Planned

### 📷 Barcode Scan — Dispatch
- **✅ Scan at Dispatch** — `POST /logistics/scan-event` (shipment-create, shipment-event types)
- **✅ Audit Trail** — All scan events audit-logged
- **❌ Batch Dispatch Scanning** — Planned

### 🌏 Regions & Coverage
- **✅ Operating Regions** — `PUT /supplier/profile` (operating_regions field); JSON array of region names
- **❌ Interactive Coverage Map** — Planned
- **❌ Zone-to-Supplier Auto-Routing** — Planned

### 🗑️ Archived Products (Soft-Delete & Restore)
- **✅ Archive (Soft-Delete) Product** — Product marked `is_deleted=True`; hidden from customer catalog automatically
- **✅ View Archived Products** — `/archive/` page shows supplier's own archived products (`GET /supplier/products?is_deleted=true`)
- **⚠️ Restore Product** — Admin-initiated via `POST /admin/products/{id}/restore`; suppliers can view archived but only admin can restore
- **❌ Scheduled Auto-Purge** — Planned (permanent delete after N days)
- **❌ Bulk Restore** — Planned

### ❌ Not Yet Implemented (Supplier)
- **❌ About Page / Public Storefront** — Public-facing supplier brand page with bio, product catalog, rating, credibility badge
- **❌ Returns Management** — Supplier-facing return queue: approve/reject/restock returned items
- **❌ Dispute Resolution** — Submit dispute evidence against return or verification failure; admin arbitration
- **❌ Multi-User / Sub-Accounts** — Team roles within a supplier account (warehouse staff, accounting, manager)
- **❌ Notification Preferences** — Granular opt-in per event type: new order, low stock, payout processed, doc expiry

---

# 🚚 Logistor (Logistics Partner) Features

### 🔐 Auth & Registration
- **✅ Login** — Shared auth with role=logistics_partner enforcement
- **✅ Self-Registration** — `POST /logistics-partners/register`; admin approval required before access
- **❌ KYC at Registration** — Planned (doc upload flow during registration)

### 📊 Dashboard & Stats
- **⚠️ Dashboard** — `GET /logistics-partners/dashboard`; top-level KPIs: active shipments, delivery rate, channels
- **❌ Full Analytics** — Planned: delivery rate, avg transit time, scan compliance, SLA adherence charts

### 📦 Shipment Management
- **✅ View Shipments** — `GET /logistics/shipments`; partner sees assigned shipments
- **✅ Accept & Update Shipments** — `PATCH /logistics/shipments/{id}`; status lifecycle management
- **✅ Package Metadata** — `package_count`, `weight_kg`, `dimensions`, `packaged_at`, `packaged_by_user_id`, `packaging_notes` — preserved across lifecycle
- **⚠️ Row-Level Visibility** — Scoping fix pending (same as admin orders mirroring)

### 📍 Delivery Scan Audit Trail
- **✅ Log Scan Events** — `POST /logistics/scan-event` (7 event types)
- **✅ View Scan History** — `GET /logistics/shipments/{id}/events`; immutable audit trail
- **✅ Location Encryption** — Location field-encrypted at rest
- **❌ Timeline UI Enrichment** — Planned
- **❌ Anomaly Detection** — Planned

### 🌐 GPS Location Ingestion
- **✅ GPS Patch** — `PATCH /logistics/events/{id}/gps`; `latitude` + `longitude` Float fields
- **✅ GPS Data Exposed** — Via `_serialize_event()` in tracking payload
- **❌ GPS Map Widget UI** — Planned (connect to interactive map component)
- **❌ Real-Time WebSocket GPS Broadcast** — Planned

### 🗺️ Order Tracking Payload to Customer
- **✅ Tracking API** — `GET /orders/{id}/tracking`; reconciles all shipments; includes return/replacement intent summary
- **✅ Multi-Shipment Reconciliation** — Requires ALL shipments delivered before marking order delivered

### 📷 Barcode / QR Scanning
- **✅ Mobile Scanning** — `expo-camera` (lazy-loaded); 7 scan event types
- **✅ Web Scanning** — Native `BarcodeDetector` API + `@zxing/library ^0.21.3` ZXing cross-browser fallback
- **❌ Batch Warehouse Scanning** — Planned
- **❌ Offline Scan Queue** — Planned

### 🔍 Product Verification — Receipt Checkpoint
- **✅ Log Verification** — `POST /product-verifications` (type: logistics_receipt)
- **✅ Results** — passed / failed / partial; discrepancy payload; evidence URL
- **✅ Role Restricted** — Logistics role restricted to `logistics_receipt` checkpoint only
- **❌ Automated Re-Routing on Failed Receipt** — Planned

### 🚛 Shipping Carrier Access
- **✅ View Carriers** — `GET /logistics/carriers`; carrier list with tracking URL templates
- **❌ Live Carrier API Integration** — Planned (DHL, Aramex, FedEx rate-shopping)

### 🧾 Auto-Invoice Receipt
- **✅ Auto-Invoice on Shipment** — Invoice auto-created on shipment trigger; HTML email to customer on creation
- **✅ Invoice Audit** — `INVOICE_CREATED` + `INVOICE_STATUS_UPDATED` AuditActions

### ❌ Not Yet Implemented (Logistor)
- **❌ GPS Map Widget UI** — Connect lat/lng from GPS patch endpoint to interactive map on delivery screens
- **❌ WebSocket Real-Time Tracking Broadcast** — Live push updates for shipment events to customer tracking + logistics dashboard
- **❌ Route Optimization** — Suggested delivery routes based on GPS + zones + vehicle capacity
- **❌ SLA Breach Tracking & Alerts** — Detect delivery SLA breaches; notify partner + escalate to admin
- **❌ Logistics Partner Revenue & Payout** — Partner earnings per delivery, payout requests (parallel to supplier payouts)

---

# 👨‍💼 Admin Features

### 🔐 Admin Auth & Role Login
- **✅ Admin Login** — `POST /auth/login` with role=admin|sub_admin
- **✅ Permission Hierarchy (RBAC)** — `STAFF_ROLES` frozenset; 29 boundary tests; unauthenticated/customer/supplier/admin access tested
- **✅ All Writes Audit-Logged** — Every admin action leaves an `AuditLog` entry
- **❌ Sub-Admin Permission Scoping UI** — Planned (fine-grained permission editor)

### 📊 Dashboard & KPI Summary
- **✅ Admin Dashboard** — `GET /admin/dashboard`; cross-table aggregations (orders, revenue, users, products)
- **✅ Mobile Admin Dashboard** — 4 mobile tests passing
- **❌ Real-Time Dashboard (WebSocket)** — Planned
- **❌ Drill-Down Links** — Planned

### 📈 Analytics & Time-Series
- **✅ Analytics Page** — `GET /admin/analytics`; revenue / order / conversion metrics
- **✅ Time-Series Charts** — `GET /admin/analytics/timeseries`; daily/weekly/monthly breakdowns
- **❌ Cohort Analysis** — Planned
- **❌ Funnel Visualization** — Planned
- **❌ Export to PDF** — Planned

### 👥 User Management
- **✅ User List** — `GET /admin/users`; paginated with filters
- **✅ Activate / Deactivate** — `PATCH /admin/users/{id}/activate`; audit-logged
- **✅ Role Change** — `PATCH /admin/users/{id}/role`; validates permission hierarchy
- **❌ Bulk User Management** — Planned
- **❌ User Impersonation (Support Tool)** — Planned

### 🏭 Supplier Verification & Management
- **✅ Supplier List** — `GET /admin/suppliers`
- **✅ Verify Supplier** — `PATCH /admin/suppliers/{id}/verify`; doc approval auto-promotes + notification + email
- **✅ Badge Management** — `PATCH /admin/suppliers/{id}/badge`; credibility level assignment
- **❌ Bulk Supplier Actions** — Planned
- **❌ Supplier Fraud Scoring** — Planned

### ✅ Product Approval & Moderation
- **✅ Approval Queue** — `GET /admin/products?is_approved=false`; all pending products
- **✅ Approve Product** — `PATCH /admin/products/{id}/approve`; audit-logged; product becomes customer-visible
- **❌ AI-Assisted Moderation** — Planned
- **❌ Bulk Approve/Reject** — Planned

### 🔥 Product Badge Management
- **✅ Badge Toggle** — `PATCH /admin/products/{id}/badge?field=is_hot&value=true`; supports is_hot/is_featured/is_new
- **✅ Race Condition Guard** — `badgeLoading` state prevents double-click race
- **✅ Audit-Logged** — `PRODUCT_UPDATE` AuditAction on every badge change
- **❌ SKU-Level Badge Scheduling** — Planned
- **❌ Bulk Badge Assignment** — Planned

### 🛒 Order Management
- **✅ All Orders** — `GET /admin/orders`; full platform order visibility; safely normalizes array-like API responses
- **✅ Status Update** — `PUT /orders/{id}/status?status=`; audit-logged
- **❌ Real-Time Order Alerts** — Planned
- **❌ Anomaly Detection** — Planned

### ↩️ Returns Management & RMA Queue
- **✅ Full Return Queue** — `GET /returns`; admin sees all; filterable by status
- **✅ Approve / Reject / Complete** — `PATCH /returns/{id}/status`; resolution notes; refund routing Stripe/Tap
- **✅ Stats Bar** — Pending/processing/completed count at top of returns page
- **❌ SLA Breach on Overdue Returns** — Planned
- **❌ Automated Refund Approval Rules** — Planned

### 🎟️ Coupon & Discount Management
- **✅ Create Coupons** — `POST /coupons`; code normalized uppercase; expiry, max-uses, min-order enforced
- **✅ Delete Coupons** — `DELETE /coupons/{code}`; audit-logged
- **✅ Coupon List** — `GET /coupons`; all active coupons
- **❌ Bulk Coupon Generation** — Planned
- **❌ Usage Analytics** — Planned

### ⚡ Flash Sales Management
- **✅ CRUD Flash Sales** — `GET/POST/PUT/DELETE /admin/flash-sales`
- **✅ Global Discount** — `product_ids=[]` applies discount platform-wide
- **✅ Scheduled Dates** — `discount_starts_at` + `discount_ends_at` on products (migration `j1k2l3m4n5o6`)
- **❌ Personalised Flash Targeting** — Planned
- **❌ Flash Sale Push Notification on Launch** — Planned

### 🖼️ Promotional Banner Management
- **✅ Banner CRUD** — `GET/POST/PUT/DELETE /banners`; DB-backed effect, color, is_active, schedule
- **✅ Consistent Theming** — Banner editor uses DB-backed fields; stays in sync across web/mobile
- **❌ Scheduled Banner Campaigns** — Planned
- **❌ A/B Banner Testing** — Planned

### 📧 Email Campaign Management
- **✅ Email Campaigns** — `/email/campaigns/*`; create, schedule, send
- **✅ A/B Subject Testing** — `ab_test_enabled` flag; 50/50 subject split; winner resolution via `POST /email/campaigns/{id}/ab-resolve`
- **✅ A/B Analytics** — `GET /email/campaigns/{id}/ab-analytics`
- **✅ Email Templates** — `/email/templates/*`; manage reusable templates
- **✅ 3-Attempt Backoff Scheduler** — Exponential backoff on email delivery failures
- **❌ Open/Click Pixel Tracking** — Planned
- **❌ Dynamic Content Blocks** — Planned

### 🚛 Logistics Partner Management
- **✅ Partner List** — `GET /admin/logistics-partners`; all registered partners
- **✅ Approve Partner** — `PATCH /admin/logistics-partners/{id}/approve`; required before partner access
- **❌ Automated SLA Scoring Per Partner** — Planned
- **❌ Performance Ranking** — Planned

### 🧾 Invoice & Supply Chain Tracker
- **✅ Invoice List** — `GET /invoices`; admin sees all; normalizes array-like responses
- **✅ Status Management** — `PATCH /invoices/{id}/status`; `picked_at`/`dispatched_at`/`delivered_at` auto-set
- **✅ HTML/PDF Render** — `GET /invoices/{id}/html` + `/pdf`
- **✅ Audit Trail** — `INVOICE_CREATED` + `INVOICE_STATUS_UPDATED` AuditActions
- **❌ SLA Tracking** — Planned
- **❌ Invoice Analytics Dashboard** — Planned

### 🔍 Product Verification System
- **✅ Full Admin View** — All 3 checkpoint types: `supplier_dispatch`, `logistics_receipt`, `customer_receipt`
- **✅ Verification Form** — Type, result (passed/failed/partial), specs, evidence URL; 20-test suite
- **✅ Role-Based Per Checkpoint** — Each role sees only their permitted checkpoint types
- **❌ Photo/Video Evidence Capture UI** — Planned (admin review of supplier/logistics evidence)

### 📷 Admin Barcode / QR Scanning
- **✅ Web Scanning** — Native `BarcodeDetector` API + `@zxing/library v0.21.3` fallback
- **✅ Mobile Scanning** — `expo-camera` lazy-loaded; 7 scan event types
- **✅ Audit Trail** — All scan events audit-logged; admin/supplier/logistics-only write
- **❌ Batch Warehouse Scanning Mode** — Planned

### 📤 Data Export — CSV
- **✅ 5 CSV Endpoints** — Users / Orders / Products / Coupons / Audit Logs
- **✅ PII Redaction** — All encrypted fields appear as `[ENCRYPTED]` in export
- **✅ Audit on Export** — `DATA_EXPORTED` AuditAction on every download
- **❌ Scheduled Export to S3** — Planned

### 💾 Backup & Recovery
- **✅ Trigger Backup** — `POST /admin/backup/trigger`; SQLite backup + rotation
- **✅ List Backups** — `GET /admin/backup/list`
- **✅ Download Backup** — `GET /admin/backup/download/{filename}`; path-traversal guard on filename
- **✅ Auto-Scheduler** — 30-min automated backup scheduler
- **❌ Cloud Storage (S3/GCS)** — Planned
- **❌ Long-Term Retention Policy** — Planned

### 📋 Audit Logs & Activity Feed
- **✅ Paginated Audit Log** — `GET /admin/audit-logs?page=&search=`; admin-only
- **✅ Full-Text Search** — Search across entity types, actions, user IDs
- **✅ Coverage** — All write operations across all controllers
- **❌ CSV/JSON Export** — Planned
- **❌ Real-Time Audit Stream** — Planned

### 🔑 Security & Key Rotation
- **✅ Key Rotation** — `POST /admin/security/rotate-key`; batch re-encrypts all EncryptedString fields
- **✅ PII Encryption** — Field-level on phone/address/tax/contact across 38 models
- **✅ Security Headers** — CSRF, JWT rotation, CSP, HSTS, X-Frame-Options, Referrer-Policy, Permissions-Policy
- **✅ Account Lockout** — 5-fail/15-min; Redis-backed; `ACCOUNT_LOCKED` AuditAction
- **❌ External Secret-Store (Vault/SSM)** — Planned

### 💸 Payout Hierarchy & Approval
- **✅ Payout Queue** — `GET /admin/payouts`; all pending supplier payout requests
- **✅ Approve Payout** — `PATCH /admin/payouts/{id}/approve`; lifecycle: pending → processing → completed; audit-logged
- **❌ Auto-Payout Threshold Rules** — Planned
- **❌ Bank Reconciliation Dashboard** — Planned

### 🎫 Support Ticket Management
- **✅ All Tickets** — `GET /tickets`; admin sees all customer tickets
- **✅ Admin Reply** — `POST /tickets/{id}/reply`; admin reply differentiated from customer in thread
- **✅ Status Management** — `PATCH /tickets/{id}/status`; closed/resolved guard enforced
- **❌ AI-Assisted Reply Suggestions** — Planned
- **❌ Routing by Category** — Planned

### 📁 Categories Management
- **✅ CRUD Categories** — `GET/POST/PUT/DELETE /categories`; hierarchical parent/child structure
- **✅ Admin-Only Write** — Customer category reads are public; write is admin-restricted
- **❌ Drag-and-Drop Reorder** — Planned
- **❌ Category-Level Commission** — Planned

### 🗑️ Archive & Soft-Delete Restore
- **✅ View Archived Products** — `GET /admin/products?is_deleted=true`; admin sees all archived products across all suppliers
- **✅ Restore Product** — `POST /admin/products/{id}/restore`; sets `is_deleted=False`; audit-logged (`PRODUCT_UPDATE` + action "restore")
- **✅ Archive Browser Page** — `/archive/` web page; shared admin+supplier view (supplier read-only, admin can restore)
- **❌ Scheduled Auto-Purge** — Planned (permanently delete after N days)
- **❌ Bulk Restore** — Planned

### ❌ Not Yet Implemented (Admin)
- **❌ Real-Time Alerts** — Low-stock, suspicious order, SLA breach pushed live to admin dashboard (needs WebSocket)
- **❌ Bulk Actions** — Bulk approve/reject/delete products, orders, users; bulk coupon generation
- **❌ Commission Rate Configuration** — Per-supplier or global ZOZI commission % editor; category-level tiers
- **❌ Platform Fee Management** — Fee rules, reconciliation ledger, auto-deduction from supplier payouts
- **❌ Admin A/B Testing Framework** — Beyond email: product page variants, checkout flow experiments
- **❌ Dispute Resolution Center** — Supplier/customer dispute evidence review, arbitration, auto-refund on resolution
- **❌ Merchant Portal** — 5th party onboarding (Merchant role), brand page, catalog management, dedicated payout system
"""

output_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "documents",
    "FEATURES_LIST.md"
)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(CONTENT)

print(f"Written {len(CONTENT)} chars to {output_path}")
