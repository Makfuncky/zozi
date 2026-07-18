# ZOZI E-Commerce — Full Feature List

> **Last Updated:** April 11, 2026 | Cross-referenced against `CODEBASE_STATUS_MATRIX_DETAILED.md`
> Features marked **✅ LIVE** are fully implemented and tested. **⚠️ PARTIAL** are in progress. **❌ PLANNED** are not yet built.
> **Feature Cycles:** 15 cross-role E2E workflows audited and tested — see [Feature Cycles](#-feature-cycles--cross-role-e2e-workflows) section at the end.

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
- **✅ Refund Processing** — Automatic routing to the original payment provider when a return is completed
- **✅ Configurable Return Windows** — Per-product supplier-configured windows with a 10-day minimum and supplier max cap
- **📄 Complete Flow Document** — [RETURN_POLICY_FLOW.md](RETURN_POLICY_FLOW.md) covers the implemented customer, supplier, and admin workflow
- **❌ Return Policy Analytics** — Planned

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

### 🎁 Referral System
> **Codebase location:** `controllers/auth_controller.py` · `db/models.py` (`ReferralPointEvent`) · `frontend/web_app/src/app/profile/referrals/page.tsx` · `frontend/mobile_app/app/referrals.tsx` · `frontend/web_app/src/app/r/[code]/page.tsx`

- **✅ Referral Code Generation** — Every user receives a unique referral code via `GET /auth/referrals/me`; shareable link via `GET /auth/referrals/share`
- **✅ Referral Landing Page** — `/r/[code]` redirects new visitors to register with referral code pre-applied
- **✅ Referral History** — `GET /auth/referrals/history`; paginated list of referred users and point events
- **✅ Referral Points** — `ReferralPointEvent` model tracks referrer/referee point grants; configurable via `PromotionEngineConfig` (`referral_referrer_points`, `referral_referee_points`, `referral_monthly_cap`, `referral_verification_delay_days`)
- **✅ Profile Referrals Tab** — Web: `/profile/referrals`; Mobile: `app/referrals.tsx`; copy referral link via expo-clipboard
- **✅ Tests** — `backend/tests/test_referrals.py`; mobile `customerAccountScreens.test.tsx`
- **❌ Referral Points Redemption at Checkout** — Planned (balance apply step)
- **❌ Referral Leaderboard** — Planned

### 🏆 Loyalty & Promotions Engine
> **Codebase location:** `controllers/promotion_controller.py` · `routers/cash_management.py` (admin/promotions) · `db/models.py` (`PromotionEngineConfig`, `PromotionOrderTier`, `PromotionLedgerEntry`)

- **✅ Points Configuration** — `PromotionEngineConfig` fields: `points_per_omr`, `points_expiry_months`, `min_points_redeem`, `allow_partial_points_redemption`
- **✅ Order Tier Discounts** — `PromotionOrderTier` rows define discount tiers by order value; `discount_type` in `percent|fixed`; engine applies best-matching tier automatically or stacks per `stacking_mode`
- **✅ Promotion Ledger** — `PromotionLedgerEntry` writes immutable audit record per promoted order; `GET /admin/promotions/ledger` for history
- **✅ Engine Preview** — `POST /admin/promotions/preview` previews which tier and discount apply to a given subtotal
- **⚠️ Customer Balance View** — Engine and DB models present; customer-facing points balance display not yet surfaced on profile/checkout
- **⚠️ Redemption at Checkout** — Engine config ready; checkout redemption step not yet wired in web/mobile UX
- **❌ VIP Tiers** — Planned (customer-facing tier names based on cumulative points)
- **❌ Points Expiry Enforcement** — Planned

### ❌ Not Yet Implemented (Customer)
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

### � Configurable Return Window
- **✅ Per-Product Return Window** — `PATCH /supplier/products/{id}/return-window`; `{"days": int}`; minimum 10 days enforced server-side
- **✅ Supplier Max Cap** — `SupplierProfile.max_return_days` (default 30) caps product setting
- **✅ Return Window Enforced at RMA** — Return requests rejected when the window has expired at submission time
- **✅ Payout Hold Integration** — `create_settlements_on_delivery()` delays supplier/LP payouts to `max(gateway_delay, return_window)` days
- **❌ Return Window Visibility to Customer** — Planned (show remaining return days on order detail)

### 📑 Commission & ZOZI Terms
- **✅ Terms Page** — `GET /supplier/terms`; per-supplier commission rate displayed from live `CommissionAgreement`
- **✅ Dynamic Commission Rate Config** — Admin sets per-supplier override via `CommissionAgreement`; falls back to category rate → platform default (10%)
- **✅ Category Commission Rates** — Admin configures per-category rates via commission management page
- **✅ Commission Policy Summary** — `CommissionPolicySummary` component shown on supplier terms page and dashboard
- **✅ Commission Ledger** — `CommissionLedgerEntry` records immutable per-settled-order commission entry
- **❌ Automated Commission Deduction from Payout** — Planned (currently requires manual reconciliation)

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

### 📊 Dashboard & Analytics
- **✅ Dashboard** — `GET /logistics-partners/dashboard`; top-level KPIs: active shipments, delivery rate, channels
- **✅ LP Analytics Page** — `/logistics-partner/analytics`; `GET /logistics-partners/analytics`; full KPI suite: `delivery_rate`, `average_transit_hours`, `sla_on_time_rate`, `scan_compliance_rate`, `total_shipments`, `delivered`, `failed`, `in_transit`
- **✅ Payout Summary on Analytics** — Payout status, paid period, unpaid summary aggregated on analytics page
- **✅ CSV Export** — Analytics data exportable as CSV from LP analytics dashboard
- **✅ Tests** — `test_logistics_partner.py`; web `logisticsPartnerPages.test.tsx`; mobile `partnerDashboardScreens.test.tsx`, `logisticsPartnerApi.test.ts`

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
- **❌ KYC at Registration** — Document upload during LP registration flow
- **❌ GPS Map Widget UI** — Connect lat/lng from GPS patch endpoint to interactive map on delivery screens
- **❌ WebSocket Real-Time Tracking Broadcast** — Live push updates for shipment events to customer tracking + LP dashboard
- **❌ Route Optimization** — Suggested delivery routes based on GPS + zones + vehicle capacity
- **❌ SLA Breach Tracking & Alerts** — Detect delivery SLA breaches; notify partner + escalate to admin
- **❌ Batch Warehouse Scanning** — Scan multiple parcels in a single session
- **❌ Offline Scan Queue** — Queue scan events when offline; sync on reconnect

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
- **✅ Email Webhook Receipt** — `POST /email/webhook`; accepts Resend webhook events; records bounces, opens, complaints in `EmailDeliveryEvent`; auto-adds to `EmailSuppression` on bounce/complaint
- **✅ Runtime Email Config** — `GET/PUT /admin/email/config`; admin updates email provider credentials at runtime without restart
- **✅ Suppression Management** — `GET/DELETE /admin/email/suppression`; admin views and removes suppression records
- **✅ Tests** — `test_email_ab.py`, `test_email_campaigns.py`, `test_email_runtime_config.py`, `test_email_webhooks_and_transactional_flows.py`

### 💳 Payment Gateway Management
> **Codebase location:** `controllers/payments_controller.py` · `routers/payments.py` · `db/models.py` (`PaymentGatewayConnection`, `PaymentProviderConfig`) · `frontend/web_app/src/app/admin/payments/page.tsx`

- **✅ Gateway Registry** — `GET /payments/config/gateways`; lists all configured gateways: Stripe, Tap, PayTabs, PayPal, HyperPay
- **✅ Runtime Key Management** — `PUT /payments/config/gateways/{provider_code}`; admin updates gateway secret keys, webhook URLs, fee structures at runtime
- **✅ Fee Pass-Through** — `fee_percent` + `fixed_fee_amount` + `pass_fee_to_customer` per gateway; order totals reflect gateway surcharge at creation time
- **✅ Test/Live Mode Toggle** — `mode: test|live` per gateway; guards prevent live keys in test environments
- **✅ PayTabs Hosted Payments** — `POST /payments/paytabs/create` + `POST /payments/paytabs/confirm`; server-key + profile-ID resolved from DB config
- **✅ DB-Keyed Stripe** — `POST /payments/create-payment-intent` reads `stripe_secret_key` from `PaymentGatewayConnection` when present, overriding env var
- **✅ Tests** — `test_payment_gateway_management.py` (8 tests)

### 🎯 Promotions Engine
> **Codebase location:** `controllers/promotion_controller.py` · `routers/cash_management.py` · `db/models.py` (`PromotionEngineConfig`, `PromotionOrderTier`, `PromotionLedgerEntry`) · `frontend/web_app/src/app/admin/promotions/page.tsx`

- **✅ Engine Config** — `GET/PUT /admin/promotions/config`; `engine_enabled`, `allow_order_tier_discounts`, `stacking_mode` (`best_only|stack_all|custom`), `max_combined_discount_percent`, `max_combined_discount_amount`
- **✅ Order Tier CRUD** — `GET/POST/PUT/DELETE /admin/promotions/tiers`; tiers with `min_order`, `max_order`, `discount_type`, `discount_value`, `stacking_allowed`, `is_active`, `sort_order`
- **✅ Discount Preview** — `POST /admin/promotions/preview`; shows matched tier and discount amount for a given subtotal
- **✅ Auto-Apply at Order Creation** — When engine enabled, best-matching tier applied to new orders and recorded in `PromotionLedgerEntry`
- **✅ Promotions Page** — `/admin/promotions`; engine toggle, tier table with create/edit/delete modals, referral config
- **✅ Tests** — `test_admin_promotion_builder.py` (5 tests including ledger integrity check)
- **❌ Customer-Facing Tier Display** — Planned (show promotion tiers on offers/checkout)
- **❌ Push Notification on Promotion Activation** — Planned

### 💼 Commission Management
> **Codebase location:** `controllers/commission_controller.py` · `routers/commission.py` · `db/models.py` (`CommissionGlobalConfig`, `CommissionCategoryRate`, `CommissionBadgeTier`, `CommissionAgreement`, `CommissionLedgerEntry`, `ProductCommissionOverride`) · `frontend/web_app/src/app/admin/commission/page.tsx`

- **✅ Global Config** — `GET/PUT /admin/commission/config`; `default_rate`, `min_rate`, `max_rate`, `margin_protection_rate`
- **✅ Category Rates** — `GET/POST/PUT/DELETE /admin/commission/category-rates`; per-category override rates
- **✅ Supplier Agreements** — `GET/POST/PUT /admin/commission/agreements`; per-supplier negotiated rates with effective dates
- **✅ Product Overrides** — `GET/POST/PATCH /admin/commission/product-overrides`; per-product commission exceptions
- **✅ Badge Tiers** — `GET/POST/PUT/DELETE /admin/commission/badge-tiers`; Bronze/Silver/Gold badge definitions with setup/recurring fees
- **✅ Commission Ledger** — `GET /admin/commission/ledger`; immutable per-settlement commission records
- **✅ Effective Rate Lookup** — `GET /admin/commission/effective-rate`; returns effective rate: product-override → supplier-agreement → category → global default
- **✅ Commission Page** — `/admin/commission`; Supplier Agreements tab + Product Overrides tab
- **✅ Tests** — `test_commission_engine.py` (10 tests)

### 💰 Cash Management & Finance
> **Codebase location:** `controllers/cash_management_controller.py` · `routers/cash_management.py` · `db/models.py` (`TransactionLedger`, `VATRemittance`, `PaymentReconciliationRun`)

- **✅ Finance Dashboard** — `GET /admin/finance/summary`; revenue, payouts, outstanding amounts by period
- **✅ Reconciliation Runs** — `POST /admin/finance/reconcile`; creates `PaymentReconciliationRun` audit records
- **✅ VAT Remittance** — `VATRemittance` model tracks 5% UAE VAT on orders; `GET /admin/finance/vat`
- **✅ Bank Account Management** — `GET/POST/PUT/DELETE /admin/bank-accounts`; admin, supplier, LP bank accounts
- **✅ COD Remittance Receipts** — `LogisticsCODRemittanceReceipt`; LP submits COD collection proofs; admin verification flow
- **✅ Tests** — `test_cash_management.py`, `test_admin_hierarchy_payouts.py`

### 🎫 Tickets with Categories & Attachments
- **✅ Ticket Categories** — `ticket_category` field on `SupportTicket`; role-aware category list per creator role
- **✅ Ticket Attachments** — `POST /tickets/{id}/attachments`; file uploads linked to `TicketAttachment` model
- **✅ Role-Aware Entry Points** — Supplier and LP panels link into shared `/tickets` flow with pre-populated entity context (`related_entity_type`, `related_entity_id`)
- **✅ Admin Ticket Thread** — `/admin/tickets/{id}`; full thread view with all replies and attachments
- **✅ JSON Body Status Updates** — Admin can update ticket status via JSON body (not just query param); supports `pending`, `resolved`, `open`, `in_progress`, `closed`
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

### � Staff Management System
> **Codebase location:** `controllers/admin_controller.py` · `routers/admin.py` (`/admin/staff/*`, `/admin/hierarchy/permissions`) · `frontend/web_app/src/app/admin/staff/page.tsx` · `frontend/shared/src/adminPermissions.ts`

- **✅ Staff Roles** — 4 non-customer staff roles: `admin`, `sub_admin`, `moderator`, `support`; enforced via `STAFF_ROLES` frozenset
- **✅ Create Staff Account** — `POST /admin/staff`; requires `staff.create` permission; captures: role, `staff_role_label`, `staff_title`, `staff_department`, `staff_area_of_operation`, `staff_hire_date`, `staff_experience_level`, `staff_performance_summary`, `staff_assigned_tasks`, `staff_assigned_projects`
- **✅ List Staff Accounts** — `GET /admin/staff`; all staff with effective permissions; requires `staff.view`
- **✅ Update Staff Account** — `PUT /admin/staff/{id}`; update role, permissions, assignments, profile metadata; requires `staff.manage`
- **✅ Bulk Update Staff** — `PUT /admin/staff/bulk`; batch update multiple staff accounts with same changes; max 200; requires `staff.manage`
- **✅ Delete Staff Account** — `DELETE /admin/staff/{id}`; hard-delete when no retention blockers; requires `staff.delete`
- **✅ Permission Catalog** — `GET /admin/staff/permission-catalog`; returns assignable permissions grouped for UI; requires `staff.manage`
- **✅ Staff Management Page** — `/admin/staff`; `EnterpriseDataTable` with create/edit/bulk-action modals; `HierarchyTab` component shows role matrix
- **✅ Tests** — `test_admin_management.py` (9 tests covering staff creation, updates, bulk ops, role boundaries, hierarchy permission updates)
- **❌ Staff Activity Log** — Planned (per-staff action trail beyond global audit log)
- **❌ Staff Performance Metrics** — Planned (tickets resolved, average response time)

### 🔐 Permission Hierarchy (RBAC)
> **Codebase location:** `frontend/shared/src/adminPermissions.ts` · `backend/controllers/admin_controller.py` (`get_hierarchy_permissions`, `update_role_permissions`) · `backend/routers/admin.py` (`/admin/hierarchy/permissions`)

- **✅ Permission Groups** — 11 permission groups: `analytics`, `users`, `staff`, `hierarchy`, `orders`, `payouts`, `coupons`, `moderation`, `audit`, `tickets`, `integrations`
- **✅ Default Permissions Per Role** — `sub_admin`: users + audit + hierarchy; `moderator`: analytics + audit + moderation; `support`: audit + tickets + orders
- **✅ Runtime Permission Override** — `PUT /admin/hierarchy/permissions/{role}`; admin updates role permissions; reloads into in-memory map without restart
- **✅ Permission Gate in UI** — `hasAdminPermission(role, permission)` + `isAdminStaffRole()` helpers guard all admin page renders and action buttons
- **✅ RBAC Tests** — `test_rbac.py` (29 boundary tests); 5 role × endpoint access matrix verified
- **❌ Fine-Grained Permission Editor UI** — Partially implemented (HierarchyTab shows grid; per-user override editor planned)

### �📋 Audit Logs & Activity Feed
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

### �️ Bulk Admin Operations
> **Codebase location:** `routers/admin.py` · `controllers/admin_controller.py` · `frontend/web_app/src/components/BulkActionBar.tsx` · `frontend/web_app/src/app/admin/staff/page.tsx`

- **✅ Bulk User Delete** — `DELETE /admin/users/bulk`; up to 200 users; skips accounts with orders; requires `users.delete`
- **✅ Bulk User Toggle Active** — `POST /admin/users/bulk-toggle-active`; batch enable/disable accounts; requires `users.toggle_active`
- **✅ Bulk User Role Update** — `POST /admin/users/bulk-role`; apply same role to multiple users; requires `users.role.update`
- **✅ Bulk Order Status Update** — `POST /admin/orders/bulk-status`; update up to 200 orders to same status; requires `orders.manage`
- **✅ Bulk Order Delete** — `DELETE /admin/orders/bulk`; up to 200 orders; requires `orders.manage`
- **✅ Bulk Staff Update** — `PUT /admin/staff/bulk`; batch update multiple staff accounts; requires `staff.manage`
- **✅ Bulk Action Bar** — `BulkActionBar` component shows floating action bar with item count when rows selected; web `EnterpriseDataTable` supports row-checkbox selection
- **✅ MAX_BULK_ITEMS guard** — All bulk endpoints validate max 200 items via `@field_validator`
- **✅ Admin Password Reset** — `POST /admin/users/{id}/reset-password`; force-set any user's password without old password; requires `users.reset_password`; used in staff management

### �🗑️ Archive & Soft-Delete Restore
- **✅ View Archived Products** — `GET /admin/products?is_deleted=true`; admin sees all archived products across all suppliers
- **✅ Restore Product** — `POST /admin/products/{id}/restore`; sets `is_deleted=False`; audit-logged (`PRODUCT_UPDATE` + action "restore")
- **✅ Archive Browser Page** — `/archive/` web page; shared admin+supplier view (supplier read-only, admin can restore)
- **❌ Scheduled Auto-Purge** — Planned (permanently delete after N days)
- **❌ Bulk Restore** — Planned

### ❌ Not Yet Implemented (Admin)
- **❌ Real-Time Alerts** — Low-stock, suspicious order, SLA breach pushed live to admin dashboard (needs WebSocket)
- **❌ Platform Fee Management** — Fee rules, reconciliation ledger, auto-deduction from supplier payouts (commission system exists; auto-deduction planned)
- **❌ Admin A/B Testing Framework** — Beyond email: product page variants, checkout flow experiments
- **❌ Dispute Resolution Center** — Supplier/customer dispute evidence review, arbitration, auto-refund on resolution
- **❌ Merchant Portal** — 5th party onboarding (Merchant role), brand page, catalog management, dedicated payout system
- **❌ Sub-Admin Permission Scoping UI** — Per-user fine-grained permission editor (role-level hierarchy editor now live; individual overrides planned)

---

# 🏪 Supplier Storefront (Public Brand Pages)
> **Codebase location:** `frontend/web_app/src/app/suppliers/[id]/page.tsx` · `frontend/web_app/src/app/supplier-storefront/[slug]/page.tsx` · `backend/routers/public_suppliers.py`

- **✅ Public Supplier Profile** — `GET /suppliers/{id}`; public supplier page with bio, product listing, credibility badge score
- **✅ Supplier Storefront Route** — `/supplier-storefront/[slug]` re-exports from `/suppliers/[id]/page.tsx`; slug-based URL for SEO-friendly brand links
- **✅ Tests** — `supplierStorefront.test.tsx` (web); `test_public_suppliers.py` (backend)
- **❌ Full Supplier Brand Page** — Planned: customizable banner, rich bio, category filter, verified badge prominence
- **❌ Follow / Subscribe** — Planned: customer follows supplier for new product notifications
- **❌ Supplier Reviews** — Planned: overall supplier-level rating distinct from per-product reviews

---

# 🌐 Platform-Wide & Infrastructure Features

### 🌍 Internationalisation & Localisation
- **✅ 9-Locale Support** — `en`, `ar`, `fr`, `de`, `es`, `hi`, `ur`, `tr`, `fa`; normalised via `shared/src/localization.ts`
- **✅ RTL Support** — Arabic, Farsi, Urdu trigger RTL layout (`isRtlLocale()`); web/mobile banner and product-card surfaces adjust positioning
- **✅ Runtime Translation** — `POST /translate`; auto-translate product descriptions, offer text on demand
- **✅ Web Multi-Language Picker** — Header locale switcher; SSR-safe hydration via `LocaleInit` component
- **✅ Mobile Language Settings** — Settings screen locale selector; all offer/product/wishlist surfaces use runtime translation
- **✅ Shared Locale Helpers** — `normalizeLocale`, `getLocaleTag`, `isRtlLocale`, locale-aware date formatting (source of truth in `frontend/shared/src/localization.ts`)
- **✅ Currency Locale Precision** — `Intl`-resolved fraction digits; KWD/BHD-like 3-decimal currencies handled natively
- **❌ Live Language Switch Without Page Reload** — Planned (i18n store hydration without refresh)
- **❌ Admin Panel Localisation** — Planned (admin UI currently English-only)

### ⚡ Performance & Reliability
- **✅ Loading Skeletons** — 13 `loading.tsx` files across routes covering products, cart, orders, checkout, notifications, profile, dashboard, and portal screens
- **✅ Error Boundaries** — 16 `error.tsx` files; root and per-route boundaries with contextual recovery UI
- **✅ WebSocket Auto-Reconnect** — Exponential backoff (1s→30s, jitter, 10 max attempts) in `shared/src/realtime.ts`; wired to all realtime consumers (notifications, admin, LP, user bridge)
- **✅ Mobile FlatList Performance** — `initialNumToRender`, `maxToRenderPerBatch`, `windowSize`, `removeClippedSubviews` tuned on product and order lists
- **✅ Redis Caching** — Recommendation engine (`rec:*` keys at 300 s TTL); product reads via `cache_utils.py`
- **✅ Query Pagination at Scale** — All list endpoints bounded with `skip/limit`; max-page-size constants per domain; streaming CSV exports use `yield_per(500)`
- **❌ Lighthouse Performance Scores** — Automated Lighthouse CI run not yet scripted
- **❌ CDN Asset Delivery** — Static images served via upload directory; CDN integration planned
- **❌ Rate Limiting (Prod)** — slowapi in place but limits tuned for dev; production tuning pending

### 🔐 Security & Compliance
- **✅ OWASP Top-10 Hardening** — XSS prevention (`html.escape` on CSV), SSRF prevention (`image_url=None` on import), SQL injection prevention (SQLAlchemy ORM), path traversal guard (backup download), IDOR guards (ownership checks per controller)
- **✅ HMAC Webhook Validation** — Stripe and Tap webhooks HMAC-validated; email webhooks validated via Resend signature header
- **✅ Idempotent Webhook Processing** — `ProcessedWebhookEvent` deduplication prevents double-charge/double-refund
- **✅ JWT Security** — Short-lived access tokens, refresh token rotation, `RevokedToken` blacklist
- **✅ PII Field Encryption** — Fernet symmetric encryption on 38+ fields across phone, address, tax, contact data
- **✅ Account Lockout** — 5-fail/15-min; Redis-backed; `ACCOUNT_LOCKED` audit trail
- **✅ Security Headers** — CSRF, CSP, HSTS, X-Frame-Options, Referrer-Policy, Permissions-Policy
- **✅ Key Rotation** — `POST /admin/security/rotate-key`; batch re-encrypts all EncryptedString fields

### 🔄 Real-Time & WebSocket
- **✅ User Notification Hub** — `/ws/user`; customer receives in-app notifications in real-time; auth token required
- **✅ Logistics Real-Time Hub** — `/ws/logistics/{partner_id}`; LP receives shipment events live
- **✅ Order Tracking WebSocket** — `/ws/logistics/order/{order_id}`; order tracking updates pushed live
- **✅ Web UserRealtimeBridge** — `UserRealtimeBridge` component subscribes to WebSocket in `frontend/web_app` and syncs notification state
- **✅ Mobile UserRealtimeBridge** — Mobile equivalent triggers toast alerts and updates notification badge
- **❌ WebSocket Real-Time Order Alerts for Admin** — Planned
- **❌ WebSocket Streaming Chatbot Replies** — Planned

---

# 🔄 Feature Cycles — Cross-Role E2E Workflows

> **Audited:** April 11, 2026 | **359+ backend cycle tests passed** | **269 web tests passed** | **246 mobile tests passed**
>
> A **Feature Cycle** is a complete end-to-end workflow spanning multiple user roles and system components. Unlike individual features (listed above by role), cycles document how features chain together across the platform.

---

## Cycle Test Results Summary

| # | Cycle | Backend Test File(s) | Backend Tests | Web Tests | Mobile Tests | E2E Status |
|---|---|---|---|---|---|---|
| 1 | Order → Ship → Deliver | `test_supply_chain_flow.py` | 8 | `checkout.test.tsx`, `trackingPage.test.tsx` | `checkoutFlow.test.ts`, `ordersScreen.test.ts`, `trackingScreen.test.tsx` | ✅ FULL |
| 2 | Return / RMA | `test_returns.py` | 6 | `adminStandalonePages.test.tsx` | `returnsScreen.test.tsx` | ✅ FULL |
| 3 | Product Lifecycle | `test_products.py` + `test_reviews.py` | 16 | `products.test.tsx`, `productDetail.test.tsx`, `ProductCard.test.tsx` | `productDetailScreen.test.ts` | ✅ FULL |
| 4 | Payment Processing | `test_payments_orders.py` + `test_payment_gateway_management.py` | 52 | `checkout.test.tsx`, `adminPaymentsPage.test.tsx` | `checkoutFlow.test.ts` | ✅ FULL |
| 5 | Registration → Verification → Onboarding | `test_auth.py` + `test_auth_hardening.py` | 18+ | `login.test.tsx`, `forgotPassword.test.tsx`, `supplierRegister.test.tsx`, `logisticsPartnerAuth.test.tsx` | `loginScreen.test.ts`, `registerScreen.test.ts`, `authStore.test.ts` | ✅ FULL |
| 6 | Finance / Reconciliation | `test_cash_management.py` + `test_admin_hierarchy_payouts.py` | 36+ | `adminFinanceCodVerification.test.tsx` | — | ✅ FULL |
| 7 | Support Ticket | `test_tickets.py` | 9 | `help.test.tsx` | `ticketsScreen.test.ts` | ✅ FULL |
| 8 | Promotion / Coupon | `test_coupons.py` + `test_admin_promotion_builder.py` | 8 | `promotionBuilderPanel.test.tsx`, `checkout.test.tsx` | `couponsScreen.test.ts` | ✅ FULL |
| 9 | Flash Sale | `test_flash_sales.py` | 14 | `adminStandalonePages.test.tsx` | `flashSalesScreen.test.ts` | ✅ FULL |
| 10 | LP Onboarding → Payout | `test_logistics_partner.py` | 44 | `logisticsPartnerPages.test.tsx`, `logisticsPartnerPayoutsReceipt.test.tsx` | `partnerDashboardScreens.test.tsx`, `logisticsPartnerApi.test.ts` | ✅ FULL |
| 11 | Email Campaign | `test_email_campaigns.py` + `test_email_webhooks_and_transactional_flows.py` | 36 | `emailComponents.test.tsx` | `newsletterPreferencesScreen.test.tsx` | ✅ FULL |
| 12 | Product Verification | `test_product_verification.py` | 20 | `adminStandalonePages.test.tsx` | `logisticsPartnerScanScreen.test.tsx` | ✅ FULL |
| 13 | Bulk Import / Export | `test_bulk_crud.py` + `test_admin_export.py` | 76 | `bulkOperations.test.tsx`, `supplierBulkAi.test.tsx` | `supplierProductAi.test.ts`, `adminManagementUtils.test.ts` | ✅ FULL |
| 14 | Referral | `test_referrals.py` | 2 | `profile.test.tsx` | `customerAccountScreens.test.tsx` | ✅ FULL |
| 15 | Commission | `test_commission_engine.py` | 5 | `commissionPolicySync.test.tsx` | — | ✅ FULL |
| 16 | Staff / RBAC Management | `test_admin_management.py` + `test_rbac.py` | 38+ | `adminManagementPages.test.tsx`, `adminPermissions.test.ts` | `adminGuardedScreens.test.tsx`, `adminManagementUtils.test.ts` | ✅ FULL |
| | **TOTALS** | **20 test files** | **359+** | **48 suites / 269 tests** | **38 suites / 246 tests** | **16/16 ✅** |

---

### Cycle 1: 🛒 Order → Ship → Deliver (Order-to-Delivery)

**Roles:** Customer → Supplier → Logistics Partner → Customer
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Customer browses** → `GET /products` → product catalog with filters, search, badges
2. **Customer adds to cart** → `POST /cart` → server-side cart for cross-device sync
3. **Customer places order** → `POST /orders` → multi-supplier order split; inventory reserved atomically; gateway fee snapshot captured
4. **Supplier sees order** → `GET /supplier/orders` → supplier-scoped view of own-product orders
5. **Supplier creates shipment** → `POST /logistics/shipments` → assigns logistics partner; package metadata captured
6. **Invoice auto-generated** → `InvoiceCreated` event → HTML email sent to customer; `INVOICE_CREATED` audit
7. **LP scans package** → `POST /logistics/scan-event` → 7 event types; location encrypted; audit-trailed
8. **LP updates status** → `PATCH /logistics/shipments/{id}` → `picked_up → in_transit → out_for_delivery → delivered`
9. **Customer verifies** → `POST /product-verifications` (type: `customer_receipt`) → QR / barcode scan confirmation
10. **Order marked delivered** → Multi-shipment reconciliation: order not complete until ALL shipments delivered
11. **Tracking visible** → `GET /orders/{id}/tracking` → full event history with return/replacement intent

**Backend Tests:** `test_supply_chain_flow.py` (8 tests) — Covers register → product create → order → shipment → barcode → delivery confirmation
**Web Tests:** `checkout.test.tsx`, `trackingPage.test.tsx`
**Mobile Tests:** `checkoutFlow.test.ts`, `ordersScreen.test.ts`, `trackingScreen.test.tsx`

---

### Cycle 2: ↩️ Return / RMA (Return Request → Approval → Resolution)

**Roles:** Customer → Admin/Supplier → Logistics Partner → Payment Gateway
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Customer initiates return** → `POST /returns` → intent: `return` or `replacement`; validated against per-product return window
2. **Return window enforced** → Server checks `days_since_delivery ≤ min(product.return_days, supplier.max_return_days)`
3. **Admin reviews queue** → `GET /returns` → filterable by status; stats bar shows pending/processing/completed
4. **Admin approves/rejects** → `PATCH /returns/{id}/status` → resolution notes captured; audit-logged
5. **Refund routing** → If return (not replacement): `chg_*` → Tap refund; `pi_*/py_*` → Stripe refund; COD → manual
6. **Replacement flow** → `intent: replacement` tracks without refund side effects
7. **Supplier restock** → Supplier queue shows per-supplier returns for restock processing
8. **Tracking updated** → `GET /orders/{id}/tracking` → payload includes active return/replacement intent summary

**Backend Tests:** `test_returns.py` (6 tests) — Covers create → admin status update → replacement intent → supplier queue
**Web Tests:** `adminStandalonePages.test.tsx` (returns admin page)
**Mobile Tests:** `returnsScreen.test.tsx`

---

### Cycle 3: 📦 Product Lifecycle (Create → Approve → Display → Review)

**Roles:** Supplier → Admin → Customer → Public
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Supplier creates product** → `POST /supplier/products` → includes name, price, images, description, stock, discount fields
2. **AI-assisted description** → `POST /ai/suggest` → optional AI description generation (⚡ button)
3. **Admin approval queue** → `GET /admin/products?is_approved=false` → admin sees pending products
4. **Admin approves** → `PATCH /admin/products/{id}/approve` → product visible to customers; audit-logged
5. **Admin sets badges** → `PATCH /admin/products/{id}/badge?field=is_hot&value=true` → hot/featured/new badges
6. **Customer discovers** → `GET /products` → grid layout with filters, badges, categories
7. **Customer searches** → `GET /search?q=` → FTS-indexed search with max 200 chars
8. **Customer views detail** → `GET /products/{id}` → full product page with supplier badge, offer badges, images
9. **Customer reviews** → `POST /reviews/products/{id}` → verified-purchase guard; star rating
10. **Public sees reviews** → `GET /reviews/products/{id}` → rating display on cards and detail page
11. **Soft delete** → `DELETE /supplier/products/{id}` → `is_deleted=True`; hidden from catalog
12. **Admin restore** → `POST /admin/products/{id}/restore` → re-activates archived product

**Backend Tests:** `test_products.py` (9 tests) + `test_reviews.py` (7 tests) + `test_admin_management.py`
**Web Tests:** `products.test.tsx`, `productDetail.test.tsx`, `ProductCard.test.tsx`
**Mobile Tests:** `productDetailScreen.test.ts`

---

### Cycle 4: 💳 Payment Processing (Intent → Webhook → Settlement → Payout)

**Roles:** Customer → Payment Gateway → System → Admin → Supplier
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Customer places order** → `POST /orders` → order created with `payment_method: cod|card`
2. **COD path** → Order confirmed immediately; inventory reserved; COD collection tracked via logistics
3. **Card path — Stripe** → `POST /payments/create-payment-intent` → reads `stripe_secret_key` from DB `PaymentGatewayConnection`
4. **Card path — Tap** → `POST /payments/tap/create` → creates Tap charge via DB-keyed credentials
5. **Card path — PayTabs** → `POST /payments/paytabs/create` → hosted payment page; `POST /payments/paytabs/confirm` on return
6. **Webhook confirmation** → `POST /payments/webhook` (Stripe) or `POST /payments/tap/webhook` → HMAC-validated; idempotent via `ProcessedWebhookEvent`
7. **Gateway fee captured** → `fee_percent` + `fixed_fee_amount` from `PaymentGatewayConnection`; stored on order
8. **Settlement created** → On delivery complete: `create_settlements_on_delivery()` → settlement delayed by `max(gateway_delay, return_window)` days
9. **Admin reconciliation** → `POST /admin/finance/reconcile` → creates `PaymentReconciliationRun` audit record
10. **Supplier payout** → `POST /finance/admin/payouts/supplier/process` → commission deducted; ledger entries created
11. **Refund flow** → `POST /payments/refund` → routes to original gateway; `chg_*` → Tap; `pi_*` → Stripe

**Backend Tests:** `test_payments_orders.py` (52 tests) + `test_payment_gateway_management.py` (8 tests)
**Web Tests:** `checkout.test.tsx`, `adminPaymentsPage.test.tsx`
**Mobile Tests:** `checkoutFlow.test.ts`

---

### Cycle 5: 🔐 Registration → Verification → Onboarding

**Roles:** User (any role) → Email Provider → Admin (for LP/Supplier approval)
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **User registers** → `POST /auth/register` → role assigned; referral code applied if present; verification email sent
2. **Email verification** → `GET /auth/verify-email?token=X` → customer email-verified (gate mode configurable)
3. **User logs in** → `POST /auth/login` → JWT access (15 min) + refresh (7 days) tokens issued; CSRF cookie set
4. **Profile setup** → `PUT /auth/me` → complete profile (business details for supplier)
5. **Supplier KYC** → `POST /supplier/documents` → upload business documents; status: pending → approved/rejected
6. **Admin verifies** → `PATCH /admin/suppliers/{id}/verify` → auto-promotes on doc approval; notification + email
7. **LP self-registration** → `POST /logistics-partners/register` → admin approval required before LP access
8. **Admin approves LP** → `PATCH /admin/logistics-partners/{id}/approve` → partner gains platform access
9. **Password flows** → `POST /auth/forgot-password` → token email → `POST /auth/reset-password` → generic responses prevent enumeration
10. **OAuth flow** → `POST /auth/google/id-token` → Google ID token validated; auto-register or link

**Backend Tests:** `test_auth.py` (18 tests) + `test_auth_hardening.py`
**Web Tests:** `login.test.tsx`, `forgotPassword.test.tsx`, `supplierRegister.test.tsx`, `logisticsPartnerAuth.test.tsx`
**Mobile Tests:** `loginScreen.test.ts`, `registerScreen.test.ts`, `authStore.test.ts`

---

### Cycle 6: 💰 Finance / Reconciliation (Order → Commission → Settlement → Payout → Reconciliation)

**Roles:** Customer → Supplier → LP → Admin → Finance System
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Order delivered** → Settlement creation triggered with return-window hold
2. **Commission calculated** → `get_effective_rate()`: product-override → supplier-agreement → category-rate → global default (10%)
3. **Ledger entries created** → `CommissionLedgerEntry` (immutable) + `TransactionLedger` (settlement record)
4. **VAT captured** → `VATRemittance` records 5% UAE VAT per order
5. **Admin reviews finance** → `GET /admin/finance/summary` → revenue, payouts, outstanding by period
6. **Supplier payout** → `POST /finance/admin/payouts/supplier/process` → batch processes eligible settlements; commission deducted
7. **LP payout** → `POST /finance/admin/payouts/logistics/process` → LP payout based on pricing profiles
8. **COD remittance** → LP submits `LogisticsCODRemittanceReceipt` → admin verifies collection proof
9. **Reconciliation** → `POST /admin/finance/reconcile` → marks bank transactions as reconciled
10. **Ledger complete** → `TransactionLedger` entry marked `fully_settled`
11. **Badge recalculation** → Supplier credibility badges recalculated based on delivery/review performance
12. **Auto-scheduler** → `_finance_scheduler_loop()` runs every 300s; processes payouts + reconciliation + badge recalc

**Backend Tests:** `test_cash_management.py` (36 tests) + `test_admin_hierarchy_payouts.py` + `test_commission_engine.py` (5 tests)
**Web Tests:** `adminFinanceCodVerification.test.tsx`

---

### Cycle 7: 🎫 Support Ticket Lifecycle

**Roles:** Customer/Supplier/LP → Admin/Support
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **User creates ticket** → `POST /tickets` → subject, description, priority; category auto-populated per role
2. **Entity context** → Supplier/LP tickets include `related_entity_type` and `related_entity_id` (order, shipment, etc.)
3. **Attachment upload** → `POST /tickets/{id}/attachments` → files linked to `TicketAttachment` model
4. **User views thread** → `GET /tickets/{id}` → full reply thread with role-differentiated styling
5. **User replies** → `POST /tickets/{id}/reply` → closed/resolved guard prevents replying to completed tickets
6. **Admin reviews queue** → `GET /tickets` → admin sees all tickets; filterable by status/category
7. **Admin replies** → `POST /tickets/{id}/reply` → admin reply visually distinct in thread
8. **Admin resolves** → `PATCH /tickets/{id}/status` → status: `open → in_progress → resolved → closed`
9. **Email notification** → Status changes trigger email to ticket creator

**Backend Tests:** `test_tickets.py` (9 tests)
**Web Tests:** `help.test.tsx`
**Mobile Tests:** `ticketsScreen.test.ts`

---

### Cycle 8: 🎟️ Promotion / Coupon → Checkout Discount

**Roles:** Admin → Customer → System
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Admin creates coupon** → `POST /coupons` → code normalized uppercase; expiry, max-uses, min-order set
2. **Admin configures promotion engine** → `PUT /admin/promotions/config` → enable/disable, stacking mode, max discount caps
3. **Admin creates order tiers** → `POST /admin/promotions/tiers` → min/max order values, discount type (percent/fixed)
4. **Customer validates coupon** → `POST /coupons/validate` → checks expiry, usage count, min-order threshold
5. **Customer places order with coupon** → `POST /orders` → coupon discount applied; promotion tier also evaluated
6. **Engine auto-applies best tier** → When engine enabled, best-matching `PromotionOrderTier` applied automatically
7. **Promotion ledger** → `PromotionLedgerEntry` created for audit trail; records matched tier + discount amount
8. **Admin previews** → `POST /admin/promotions/preview` → shows which tier matches for any given subtotal

**Backend Tests:** `test_coupons.py` (5 tests) + `test_admin_promotion_builder.py` (3 tests)
**Web Tests:** `promotionBuilderPanel.test.tsx`, `checkout.test.tsx`
**Mobile Tests:** `couponsScreen.test.ts`

---

### Cycle 9: ⚡ Flash Sale Campaign

**Roles:** Admin → System → Customer
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Admin creates flash sale** → `POST /admin/flash-sales` → select products, discount %, date window
2. **Product fields updated** → `discount_starts_at` + `discount_ends_at` set on products; `compare_price` calculated
3. **Supplier discount integration** → Suppliers can also set `compare_price` directly via `PUT /supplier/products/{id}`
4. **Public API exposed** → `GET /flash-sales` → returns only currently-active sales
5. **Customer sees badges** → Product cards show Flash Sale (red), Supplier Discount (lime-green 🏷), Promotional (orange) badges
6. **Countdown display** → Flash sale countdown timer on offers page
7. **Customer purchases** → `POST /orders` → discount price applied during sale window
8. **Sale ends** → Products revert to regular price when `discount_ends_at` passes
9. **Admin manages** → `PUT /admin/flash-sales/{id}` → update dates/products/discount; `DELETE` to remove

**Backend Tests:** `test_flash_sales.py` (14 tests)
**Web Tests:** `adminStandalonePages.test.tsx`
**Mobile Tests:** `flashSalesScreen.test.ts`

---

### Cycle 10: 🚚 Logistics Partner Onboarding → Shipment → Payout

**Roles:** LP → Admin → Supplier → Customer → Finance
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **LP self-registers** → `POST /logistics-partners/register` → profile created; pending admin approval
2. **Admin approves** → `PATCH /admin/logistics-partners/{id}/approve` → LP gains platform access
3. **LP defines service areas** → `POST /logistics-partners/service-areas` → geographic coverage zones
4. **LP sets pricing** → `POST /logistics-partners/pricing-profiles` → per-zone/weight pricing rules
5. **Supplier creates shipment** → `POST /logistics/shipments` → system assigns LP based on zone/availability
6. **LP accepts shipment** → `PATCH /logistics/shipments/{id}` → status: `assigned → picked_up`
7. **LP scans events** → `POST /logistics/scan-event` → 7 event types; barcode/QR; GPS lat/lng captured
8. **LP updates status** → `PATCH /logistics/shipments/{id}` → `in_transit → out_for_delivery → delivered`
9. **Customer tracks** → `GET /orders/{id}/tracking` → full shipment event timeline
10. **LP views dashboard** → `GET /logistics-partners/dashboard` → active shipments, delivery rate, SLA metrics
11. **LP analytics** → `GET /logistics-partners/analytics` → transit hours, scan compliance, payout summary
12. **LP payout** → `POST /finance/admin/payouts/logistics/process` → admin triggers LP payout based on pricing profiles
13. **COD remittance** → LP submits COD receipt → admin verifies → funds reconciled

**Backend Tests:** `test_logistics_partner.py` (44 tests)
**Web Tests:** `logisticsPartnerPages.test.tsx`, `logisticsPartnerPayoutsReceipt.test.tsx`
**Mobile Tests:** `partnerDashboardScreens.test.tsx`, `logisticsPartnerApi.test.ts`

---

### Cycle 11: 📧 Email Campaign Lifecycle

**Roles:** Admin/Marketing → Email Provider → Customers
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Admin creates template** → `POST /email/templates` → reusable HTML template with variables
2. **Admin creates campaign** → `POST /email/campaigns` → links template; sets subject, audience, schedule
3. **A/B testing** → `ab_test_enabled: true` → 50/50 subject split; two subject variants
4. **Admin schedules** → `PUT /email/campaigns/{id}` → `status: scheduled`; `send_at` datetime
5. **Scheduler dispatches** → `_email_campaign_scheduler_loop()` picks up due campaigns → sends via provider
6. **Safe status transition** → `scheduled → sending → draft → sent` (April 11 hardening: reverts to `scheduled` on failure)
7. **Provider sends** → Emails delivered via Resend API; suppression list respected
8. **Webhooks received** → `POST /email/webhooks` → Resend webhook: delivered, bounced, opened, complained
9. **Suppression auto-added** → Bounces/complaints auto-create `EmailSuppression` records
10. **A/B resolution** → `POST /email/campaigns/{id}/ab-resolve` → picks winner variant
11. **Admin reviews analytics** → `GET /email/campaigns/{id}/ab-analytics` → open rates per variant
12. **Runtime config** → `PUT /admin/email/config` → update email provider credentials without restart
13. **Newsletter flow** → `POST /email/newsletter/subscribe` → `POST /email/newsletter/unsubscribe` → preference management

**Backend Tests:** `test_email_campaigns.py` (36 tests) + `test_email_webhooks_and_transactional_flows.py`
**Web Tests:** `emailComponents.test.tsx`
**Mobile Tests:** `newsletterPreferencesScreen.test.tsx`

---

### Cycle 12: 🔍 Product Verification (3-Checkpoint Chain)

**Roles:** Supplier → Logistics Partner → Customer → Admin
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Supplier dispatch check** → `POST /product-verifications` (type: `supplier_dispatch`) → supplier verifies product before shipping
2. **Verification result** → `passed` / `failed` / `partial` → includes specs comparison, discrepancy payload, evidence URL
3. **LP receipt check** → `POST /product-verifications` (type: `logistics_receipt`) → LP verifies on pickup
4. **Customer receipt check** → `POST /product-verifications` (type: `customer_receipt`) → customer verifies on delivery
5. **Role restriction** → Each role can only create their checkpoint type; enforced server-side
6. **Admin full view** → Admin sees all 3 checkpoint types across all products
7. **Discrepancy handling** → Failed verifications create audit trail; admin reviews evidence

**Backend Tests:** `test_product_verification.py` (20 tests) — Covers all 3 checkpoint types + access control
**Web Tests:** `adminStandalonePages.test.tsx`
**Mobile Tests:** `logisticsPartnerScanScreen.test.tsx`

---

### Cycle 13: 📥 Bulk Import / Export

**Roles:** Supplier → Admin → System
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Supplier CSV import** → `POST /supplier/products/import` → validates rows; creates products in bulk; SSRF prevention (`image_url=None`)
2. **Supplier CSV export** → `GET /supplier/products/export` → all supplier products as CSV; XSS-safe (`html.escape()`)
3. **Admin bulk operations** → `POST /admin/bulk/products/delete` → `POST /admin/bulk/users/toggle-active` → `POST /admin/bulk/orders/update-status`
4. **Supplier bulk status** → `POST /supplier/products/bulk` → activate/deactivate products in bulk
5. **Supplier bulk inventory** → `POST /supplier/products/bulk-inventory` → set/adjust stock in bulk; ownership enforced
6. **LP bulk shipment status** → `PUT /logistics-partners/shipments/bulk-status` → bulk update shipment statuses; ownership enforced
7. **Admin CSV exports** → 5 endpoints: Users / Orders / Products / Coupons / Audit Logs
8. **PII redaction** → Encrypted fields appear as `[ENCRYPTED]` in all exports
9. **Audit on export** → `DATA_EXPORTED` AuditAction on every download
10. **AI bulk** → `POST /ai/bulk-suggest` → AI-generated descriptions for multiple products

**Backend Tests:** `test_bulk_crud.py` (58 tests) + `test_admin_export.py` (18 tests) + `test_ai_bulk.py`
**Web Tests:** `bulkOperations.test.tsx`, `supplierBulkAi.test.tsx`
**Mobile Tests:** `supplierProductAi.test.ts`, `adminManagementUtils.test.ts`

---

### Cycle 14: 🎁 Referral (Share → Register → Points)

**Roles:** Referrer (Customer) → Referee (New Customer) → System
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Referrer gets code** → `GET /auth/referrals/me` → unique referral code auto-generated on registration
2. **Referrer shares link** → `POST /auth/referrals/share` → shareable URL; daily share action awards points
3. **Landing page** → `/r/[code]` → redirects to registration with referral code pre-applied
4. **Referee registers** → `POST /auth/register` with `referral_code` param → referee linked to referrer
5. **Points awarded** → `ReferralPointEvent` created for both referrer and referee; configurable amounts
6. **Configurable via engine** → `PromotionEngineConfig`: `referral_referrer_points`, `referral_referee_points`, `referral_monthly_cap`, `referral_verification_delay_days`
7. **History view** → `GET /auth/referrals/history` → paginated list of referred users and point events
8. **Profile tab** → Web: `/profile/referrals`; Mobile: `app/referrals.tsx` → copy link via expo-clipboard

**Backend Tests:** `test_referrals.py` (2 tests) — register with code + daily share limit
**Web Tests:** `profile.test.tsx`
**Mobile Tests:** `customerAccountScreens.test.tsx`

---

### Cycle 15: 💼 Commission (Delivery → Rate Lookup → Ledger → Payout Deduction)

**Roles:** System → Admin → Supplier
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Order delivered** → Settlement creation triggered
2. **Effective rate lookup** → `get_effective_rate()` cascades: Product Override → Supplier Agreement → Category Rate → Global Default (10%)
3. **Admin configures rates** → `PUT /admin/commission/config` (global) → `POST /admin/commission/category-rates` → `POST /admin/commission/agreements` (per-supplier) → `POST /admin/commission/product-overrides`
4. **Commission calculated** → `zozi_commission = settlement_amount × effective_rate`; `net_supplier_amount = settlement_amount - zozi_commission`
5. **Ledger entry created** → `CommissionLedgerEntry` (immutable); records effective rate, zozi amount, net supplier amount
6. **Badge tier fees** → `CommissionBadgeTier`: Bronze/Silver/Gold; setup + recurring fees applied to supplier payouts
7. **Admin previews** → `GET /admin/commission/effective-rate?supplier_id=&product_id=` → shows rate cascade
8. **Payout deduction** → Supplier payout amount = settlement amount - commission - badge fees
9. **Admin reviews ledger** → `GET /admin/commission/ledger` → immutable audit trail of all commission entries
10. **Terms page** → `GET /supplier/terms` → supplier sees their effective commission rate and terms

**Backend Tests:** `test_commission_engine.py` (5 tests) — Rate cascade + badge + category combination
**Web Tests:** `commissionPolicySync.test.tsx`

---

## Feature Cycle Coverage Gaps & Planned Enhancements

| Cycle | Gap | Planned Enhancement |
|---|---|---|
| Order → Deliver | No real-time push to customer during delivery | WebSocket GPS broadcast to tracking page |
| Return / RMA | No automated refund approval rules | Rule-based auto-approve for low-value returns |
| Product Lifecycle | Admin approval is manual-only | AI-assisted moderation scoring |
| Payment | Saved cards not yet implemented | PCI-DSS Stripe/Tap vault for saved methods |
| Registration | No KYC at LP registration | Document upload during LP self-registration |
| Finance | No auto-payout threshold | Trigger payout when balance exceeds configurable threshold |
| Support Ticket | No SLA breach tracking | Detect overdue tickets; escalate to admin |
| Promotion | Customer can't see tier discounts | Show active promotion tiers on offers/checkout page |
| Flash Sale | No push notification on launch | Send push when flash sale goes live |
| LP → Payout | No automated SLA scoring | Score LP performance; auto-rank for assignment priority |
| Email Campaign | No open/click pixel tracking | Embed tracking pixels in campaign emails |
| Product Verification | No photo/video evidence UI | Evidence capture + admin review interface |
| Bulk Import | No error report on failed rows | Return CSV with per-row error details |
| Referral | No points redemption at checkout | Apply referral points as balance credit during checkout |
| Commission | No auto-deduction from payout | Fully automated commission deduction (currently semi-manual) |
| Staff / RBAC | No per-user permission override UI | Individual staff permission editor beyond role defaults |

---

### Cycle 16: 👤 Staff / RBAC Management

**Roles:** Super Admin → Staff Accounts (sub_admin, moderator, support) → Platform Access
**Status:** ✅ FULLY E2E TESTED

**Step-by-Step Flow:**
1. **Admin creates staff** → `POST /admin/staff` → role: `sub_admin|moderator|support`; captures HR metadata (title, department, hire date, tasks)
2. **Permissions assigned** → `permissions[]` per account; or inherited from role defaults (`sub_admin` → users+audit, `moderator` → analytics+moderation, `support` → tickets+orders)
3. **Permission catalog fetched** → `GET /admin/staff/permission-catalog` → returns 11 permission groups grouped for UI rendering
4. **Staff logs in** → `POST /auth/login` with staff role → JWT includes `role` and `permissions` claims
5. **Permission gate** → `require_permission("perm.name", current_admin)` in every admin route; `hasAdminPermission()` in UI components
6. **Runtime permission update** → `PUT /admin/hierarchy/permissions/{role}` → replaces full role permission set; reloads in-memory map without restart
7. **RBAC boundary tests** → `test_rbac.py`: customer/supplier/admin/sub_admin access verified per endpoint
8. **Staff list** → `GET /admin/staff` → `EnterpriseDataTable` with HR profile columns
9. **Bulk staff update** → `PUT /admin/staff/bulk` → update multiple staff accounts simultaneously
10. **Staff deleted** → `DELETE /admin/staff/{id}` → hard-delete when no retention blockers; audit-logged

**Backend Tests:** `test_admin_management.py` (9 tests) + `test_rbac.py` (29+ boundary tests)
**Web Tests:** `adminManagementPages.test.tsx`, `adminPermissions.test.ts`
**Mobile Tests:** `adminGuardedScreens.test.tsx`, `adminManagementUtils.test.ts`
