# Backend Module Alignment Plan

## 1. Current State Summary (Verified)

### Controllers
- **Top-level:** 33 files (all hub/utility controllers — no domain-specific controllers at top level)
- **Subdirs:** 10 populated subdirs with domain-specific controllers
- **Duplicates:** Only `country_versioning_controller.py` has a subdir copy, but files are **DIFFERENT** (6124 vs 6134 bytes)
- **Cross-imports:** Top-level controllers already import from subdir controllers using modular paths (e.g., `controllers.payments.payments_controller`)

### Routers
- **Top-level:** 66 files
- **Subdirs:** 17 populated subdirs with 56 files
- **True identical duplicate:** `routers/currency.py` == `routers/currency/currency.py` (IDENTICAL)
- **Different files with same basename:** `routers/location_api.py` (2906 bytes) vs `routers/country/location_api.py` (2923 bytes)
- **Broken state:** main.py uses dotted paths for 64 routers that don't have subdir files → routes silently missing
- **Orphaned:** `routers/supplier_payouts.py` not referenced in main.py

### Services
- **Top-level:** 126 files
- **Subdirs:** 14 populated subdirs with 111 files
- **Identical duplicates:** 28 top-level services have IDENTICAL subdir copies
- **Different duplicates:** 16 top-level services have DIFFERENT subdir copies
- **Broken imports in subdir files:** 7 files import from `controllers.risk.audit_controller` (no `controllers/risk/` subdir exists)

### Critical Finding: 64 Missing Routes
`main.py` references dotted paths like `addresses.addresses`, `admin.admin`, `ai.ai`, etc., but the subdir files don't exist. The `_load_routers` fallback to `controllers.{name}` also fails. The app starts but **64 routes are silently missing**.

## 2. Canonical Structure Decision

**Subdir files are canonical** for domain-specific code. They were created with updated modular imports.

**Top-level hub files stay at top level.** These are imported by many other modules:
- `controllers/auth_controller.py`
- `controllers/admin_controller.py`
- `controllers/audit_controller.py`
- `controllers/products_controller.py`
- `controllers/country_controller.py`
- `controllers/orders_controller.py`
- `controllers/supplier_controller.py`
- `controllers/iam_controller.py`
- `controllers/mobile_controller.py`
- `controllers/notifications_controller.py`
- `controllers/operational_controller.py`
- `controllers/risk_controller.py`
- `controllers/video_controller.py`
- `controllers/wishlist_controller.py`
- `controllers/cart_controller.py`
- `controllers/comm_controller.py`
- `controllers/chat_controller.py`
- `controllers/chatbot_controller.py`
- `controllers/ai_controller.py`
- `controllers/compliance_controller.py`
- `controllers/commission_controller.py`
- `controllers/disputes_controller.py`
- `controllers/returns_controller.py`
- `controllers/reviews_controller.py`
- `controllers/employee_controller.py`
- `controllers/employees_controller.py`
- `controllers/hr_controller.py`
- `controllers/lms_controller.py`
- `controllers/banner_controller.py`
- `controllers/promotion_controller.py`
- `controllers/search_controller.py`
- `controllers/logistics_controller.py`
- `controllers/export_controller.py`

**Utility files stay at top level:**
- `controllers/cache_utils.py`
- `controllers/soft_delete.py`

**Hub routers stay at top level:**
- `routers/auth.py`
- `routers/users.py`

## 3. Execution Steps (Phased for Safety)

### Phase 3.1: Fix Broken Imports (Safe — 7 files)

Change `controllers.risk.audit_controller` → `controllers.audit_controller` in:

**Subdir controllers:**
- `controllers/logistics/logistics_partner_controller.py`
- `controllers/marketing/coupons_controller.py`
- `controllers/marketing/flash_sale_controller.py`
- `controllers/suppliers/supplier_document_controller.py`
- `controllers/suppliers/supplier_document_controls.py`

**Subdir services:**
- `services/accounts/coa.py`
- `services/finance/orphan_detector.py`

### Phase 3.2: Remove Identical Duplicates (Safe — 29 files)

**Routers:**
- Remove `routers/currency.py` (identical to `routers/currency/currency.py`)

**Services (28 identical pairs):**
- `advanced_filter_service.py`
- `ai_search_service.py`
- `ai_service.py`
- `bg_removal_presets.py`
- `confidence_scoring.py`
- `content_service.py`
- `country_data_orchestrator.py`
- `country_rls_service.py`
- `cross_border_detection.py`
- `cross_border_service.py`
- `data_residency.py`
- `data_residency_service.py`
- `downstream_hooks.py`
- `geo_fence_service.py`
- `live_tracking_service.py`
- `localization_service.py`
- `logistics_health_engine.py`
- `logistics_partner_pricing.py`
- `map_service.py`
- `media_service.py`
- `media_storage.py`
- `shipping_tier.py`
- `supplier_health_engine.py`
- `supplier_onboarding_service.py`
- `travel_detector.py`
- `travel_service.py`
- `workflow_engine.py`
- `worm_audit.py`

### Phase 3.3: Restore Missing Routes in main.py (Safe — restores 64 routes)

Change 64 dotted-path entries in `router_names` that reference non-existent subdir files back to simple names:

**Change from dotted to simple:**
- `("addresses.addresses", "/addresses")` → `("addresses", "/addresses")`
- `("admin.admin", "/admin")` → `("admin", "/admin")`
- `("admin_analytics.admin_analytics", "/admin")` → `("admin_analytics", "/admin")`
- `("admin_banners.admin_banners", "/admin")` → `("admin_banners", "/admin")`
- `("admin_cash.admin_cash", "/admin")` → `("admin_cash", "/admin")`
- `("admin_categories.admin_categories", "/admin")` → `("admin_categories", "/admin")`
- `("admin_chat.admin_chat", "/admin")` → `("admin_chat", "/admin")`
- `("admin_commission.admin_commission", "/admin")` → `("admin_commission", "/admin")`
- `("admin_email.admin_email", "/admin")` → `("admin_email", "/admin")`
- `("admin_logistics.admin_logistics", "/admin")` → `("admin_logistics", "/admin")`
- `("admin_orders.admin_orders", "/admin")` → `("admin_orders", "/admin")`
- `("admin_payouts.admin_payouts", "/admin")` → `("admin_payouts", "/admin")`
- `("admin_promotions.admin_promotions", "/admin/promotions")` → `("admin_promotions", "/admin/promotions")`
- `("admin_settings.admin_settings", "/admin/settings")` → `("admin_settings", "/admin/settings")`
- `("admin_suppliers.admin_suppliers", "/admin")` → `("admin_suppliers", "/admin")`
- `("admin_treasury.admin_treasury", "/admin/treasury")` → `("admin_treasury", "/admin/treasury")`
- `("admin_users.admin_users", "/admin")` → `("admin_users", "/admin")`
- `("admin_video.admin_video", "/admin")` → `("admin_video", "/admin")`
- `("ai.ai", "/ai")` → `("ai", "/ai")`
- `("ai.ai_image", "/ai-image")` → `("ai_image", "/ai-image")`
- `("ai.ai_upload", "/ai-upload")` → `("ai_upload", "/ai-upload")`
- `("audit.audit", "/audit")` → `("audit", "/audit")`
- `("cart.cart", "/cart")` → `("cart", "/cart")`
- `("chat.chat", "/chat")` → `("chat", "/chat")`
- `("chatbot.chatbot", "/chatbot")` → `("chatbot", "/chatbot")`
- `("comm.comm", "/comm")` → `("comm", "/comm")`
- `("command_center.command_center", "")` → `("command_center", "")`
- `("commission.commission", "/commission")` → `("commission", "/commission")`
- `("compliance.commission", "/compliance")` → `("compliance", "/compliance")`
- `("csp_reporting.csp_reporting", "/csp-reporting")` → `("csp_reporting", "/csp-reporting")`
- `("customer_health.customer_health", "/customer-health")` → `("customer_health", "/customer-health")`
- `("ediscovery.ediscovery", "/ediscovery")` → `("ediscovery", "/ediscovery")`
- `("email.email", "/email")` → `("email", "/email")`
- `("employees.employees", "")` → `("employees", "")`
- `("entity_chat.entity_chat", "/entity-chat")` → `("entity_chat", "/entity-chat")`
- `("entity_communication.entity_communication", "/entity-communication")` → `("entity_communication", "/entity-communication")`
- `("escalation.escalation", "/escalation")` → `("escalation", "/escalation")`
- `("finance.cash_management", "/cash-management")` → `("cash_management", "/cash-management")`
- `("financial_controller.financial_controller", "/api")` → `("financial_controller", "/api")`
- `("fraud_detection.fraud_detection", "/fraud-detection")` → `("fraud_detection", "/fraud-detection")`
- `("hr.hr", "/hr")` → `("hr", "/hr")`
- `("iam.iam", "/iam")` → `("iam", "/iam")`
- `("incident.incident", "/incident")` → `("incident", "/incident")`
- `("internal_channels.internal_channels", "/internal-channels")` → `("internal_channels", "/internal-channels")`
- `("jobs.jobs", "/jobs")` → `("jobs", "/jobs")`
- `("lms.lms", "/lms")` → `("lms", "/lms")`
- `("location_api.location_api", "/location")` → `("location_api", "/location")`
- `("messaging.messaging", "/messaging")` → `("messaging", "/messaging")`
- `("notifications.notifications", "/notifications")` → `("notifications", "/notifications")`
- `("okr.okr", "/okr")` → `("okr", "/okr")`
- `("onboarding.onboarding", "/onboarding")` → `("onboarding", "/onboarding")`
- `("orders.orders", "/orders")` → `("orders", "/orders")`
- `("permissions.permissions", "/permissions")` → `("permissions", "/permissions")`
- `("proxy_communication.proxy_communication", "/proxy-communication")` → `("proxy_communication", "/proxy-communication")`
- `("push_notifications.push_notifications", "/push-notifications")` → `("push_notifications", "/push-notifications")`
- `("returns.returns", "/returns")` → `("returns", "/returns")`
- `("reviews.reviews", "/reviews")` → `("reviews", "/reviews")`
- `("risk.risk", "/risk")` → `("risk", "/risk")`
- `("tickets.tickets", "/tickets")` → `("tickets", "/tickets")`
- `("translate.translate", "/translate")` → `("translate", "/translate")`
- `("video.video", "/video")` → `("video", "/video")`
- `("video_controller.video_controller", "/video-controller")` → `("video_controller", "/video-controller")`
- `("wishlist.wishlist", "/wishlist")` → `("wishlist", "/wishlist")`
- `("ws_chat.ws_chat", "/ws-chat")` → `("ws_chat", "/ws-chat")`

**Keep as dotted (subdir file exists and works):**
- `products.products`, `orders.orders` → wait, `orders.orders` is being changed to simple because subdir doesn't exist
- Actually, keep these as dotted: `products.products`, `cart.cart`, `payments.payments`, `products.categories`, `country.countries`, `logistics.logistics`, `logistics.logistics_health`, `logistics.logistics_partner`, `logistics.logistics_orders`, `logistics.logistics_locations`, `finance.finance`, `jobs.jobs`, `finance.treasury`, `notifications.notifications`, `search.search`, `reviews.reviews`, `wishlist.wishlist`, `marketing.coupons`, `marketing.banners`, `chat.chat`, `chatbot.chatbot`, `employees.employees`, `hr.hr`, `finance.expenses`, `export.export`, `finance.cash_management`, `finance.invoices`, `commission.commission`, `compliance.compliance`, `risk.risk`, `audit.audit`, `suppliers.supplier_documents`, `suppliers.supplier`, `suppliers.supplier_health`, `logistics.parcel_tracking`, `logistics.shop_locations`, `logistics.cross_border`, `country.country_maps`, `country.country_admin`, `country.country_dropdown`, `country.country_staff`, `country.country_payouts`, `country.country_auto_populate`, `command_center.command_center`, `ai.ai`, `ai.ai_image`, `ai.ai_upload`, `entity_chat.entity_chat`, `entity_communication.entity_communication`, `internal_channels.internal_channels`, `onboarding.onboarding`, `proxy_communication.proxy_communication`, `translate.translate`, `video_controller.video_controller`, `logistics.travel`, `shift_handover.shift_handover`, `succession.succession`, `okr.okr`, `ediscovery.ediscovery`, `workflows.workflows`, `tickets.tickets`, `video.video`, `upload.upload`, `marketing.flash_sales`, `admin_users.admin_users`, `products.admin_products`, `admin_orders.admin_orders`, `admin_settings.admin_settings`, `admin_promotions.admin_promotions`, `admin_categories.admin_categories`, `admin_banners.admin_banners`, `admin_payouts.admin_payouts`, `admin_cash.admin_cash`, `admin_commission.admin_commission`, `admin_logistics.admin_logistics`, `admin_email.admin_email`, `admin_suppliers.admin_suppliers`, `admin_analytics.admin_analytics`, `admin_chat.admin_chat`, `admin_video.admin_video`, `finance.accounting`, `finance.finance_automation`, `finance.finance_erp`, `addresses.addresses`, `returns.returns`, `logistics.geo`, `iam.iam`, `currency.currency`, `csp_reporting.csp_reporting`, `products.product_videos`, `marketing.referrals`, `fraud_detection.fraud_detection`, `products.product_verification`, `suppliers.public_suppliers`, `push_notifications.push_notifications`, `messaging.messaging`, `ws_chat.ws_chat`, `contact.contact`, `email.email`, `customer_health.customer_health`, `permissions.permissions`, `financial_controller.financial_controller`, `comm.comm`, `escalation.escalation`, `incident.incident`, `lms.lms`, `products.product_moderation`, `logistics.shipments`, `location_api.location_api`

Wait, I need to be more careful. Let me re-check which dotted paths actually have working subdir files.

From my earlier analysis:
- 48 dotted-path routers HAVE working subdir files
- 64 dotted-path routers DO NOT have subdir files

So I should keep the 48 that work and change the 64 that don't.

Let me list the 48 that KEEP dotted paths:
contact.contact, country.countries, country.country_admin, country.country_auto_populate, country.country_dropdown, country.country_maps, country.country_payouts, country.country_staff, currency.currency, export.export, finance.accounting, finance.expenses, finance.finance, finance.finance_automation, finance.finance_erp, finance.invoices, finance.treasury, logistics.cross_border, logistics.geo, logistics.logistics, logistics.logistics_health, logistics.logistics_locations, logistics.logistics_orders, logistics.logistics_partner, logistics.parcel_tracking, logistics.shipments, logistics.shop_locations, logistics.travel, marketing.banners, marketing.coupons, marketing.flash_sales, marketing.referrals, payments.payments, products.admin_products, products.categories, products.product_moderation, products.product_verification, products.product_videos, products.products, search.search, shift_handover.shift_handover, succession.succession, suppliers.public_suppliers, suppliers.supplier, suppliers.supplier_documents, suppliers.supplier_health, upload.upload, workflows.workflows

And the 64 that CHANGE to simple names:
addresses.addresses, admin.admin, admin_analytics.admin_analytics, admin_banners.admin_banners, admin_cash.admin_cash, admin_categories.admin_categories, admin_chat.admin_chat, admin_commission.admin_commission, admin_email.admin_email, admin_logistics.admin_logistics, admin_orders.admin_orders, admin_payouts.admin_payouts, admin_promotions.admin_promotions, admin_settings.admin_settings, admin_suppliers.admin_suppliers, admin_treasury.admin_treasury, admin_users.admin_users, admin_video.admin_video, ai.ai, ai.ai_image, ai.ai_upload, audit.audit, cart.cart, chat.chat, chatbot.chatbot, comm.comm, command_center.command_center, commission.commission, compliance.commission, csp_reporting.csp_reporting, customer_health.customer_health, ediscovery.ediscovery, email.email, employees.employees, entity_chat.entity_chat, entity_communication.entity_communication, escalation.escalation, finance.cash_management, financial_controller.financial_controller, fraud_detection.fraud_detection, hr.hr, iam.iam, incident.incident, internal_channels.internal_channels, jobs.jobs, lms.lms, location_api.location_api, messaging.messaging, notifications.notifications, okr.okr, onboarding.onboarding, orders.orders, permissions.permissions, proxy_communication.proxy_communication, push_notifications.push_notifications, returns.returns, reviews.reviews, risk.risk, tickets.tickets, translate.translate, video.video, video_controller.video_controller, wishlist.wishlist, ws_chat.ws_chat

### Phase 3.4: Remove Orphaned File (Safe)

- `routers/supplier_payouts.py` — not referenced in main.py, no subdir copy

### Phase 3.5: Decide on Non-Identical Duplicates (Needs User Input)

**Routers:**
- `routers/location_api.py` (2906 bytes) vs `routers/country/location_api.py` (2923 bytes) — DIFFERENT
  - Recommendation: Keep subdir version as canonical, remove top-level

**Controllers:**
- `controllers/country_versioning_controller.py` (6124 bytes) vs `controllers/country/country_versioning_controller.py` (6134 bytes) — DIFFERENT
  - Recommendation: Keep subdir version as canonical, remove top-level

**Services (16 different pairs):**
- `advanced_search_engine.py` (top=16262, sub=18428)
- `ai_copy_jobs.py` (top=2999, sub=3002)
- `ai_variant_config.py` (top=63254, sub=760)
- `bg_removal_service.py` (top=45464, sub=1204)
- `country_auto_populate.py` (top=28475, sub=31803)
- `country_detection.py` (top=4947, sub=4957)
- `country_heuristic_engine.py` (top=26222, sub=26224)
- `cross_border_tracker.py` (top=3061, sub=3071)
- `downstream_wiring.py` (top=7829, sub=7837)
- `free_image_tools.py` (top=39791, sub=39794)
- `image_ai_service.py` (top=20101, sub=396)
- `legal_contract_service.py` (top=6624, sub=6632)
- `logistics_engine.py` (top=7705, sub=7715)
- `logistics_sla_service.py` (top=5075, sub=5073)
- `ocr_parser.py` (top=6978, sub=390)
- `storage.py` (top=7232, sub=7058)

Recommendation: Keep subdir versions as canonical, remove top-level duplicates.

### Phase 3.6: Optional — Complete Migration (Deferred)

Only after Phases 3.1-3.5 are complete and app is stable:
- Create missing router subdirs (admin/, ai/, audit/, cart/, chat/, chatbot/, comm/, command_center/, commission/, compliance/, csp_reporting/, customer_health/, ediscovery/, email/, employees/, entity_chat/, entity_communication/, escalation/, financial_controller/, fraud_detection/, hr/, iam/, incident/, internal_channels/, jobs/, lms/, location_api/, messaging/, notifications/, okr/, onboarding/, permissions/, proxy_communication/, push_notifications/, returns/, reviews/, tickets/, translate/, video/, video_controller/, wishlist/, ws_chat/)
- Move top-level files to subdirs
- Update imports
- Update main.py router_names to dotted paths

## 4. Validation

1. **Import smoke test:** Run `py -c "from backend.main import app"` from the backend directory.
2. **Router registration test:** Verify `app.routes` contains all expected routes (should increase from ~48 to ~112).
3. **No broken imports:** Confirm zero `ImportError` warnings in startup logs.
4. **No identical duplicates:** Confirm no top-level `.py` files remain that have identical subdir copies.

## 5. Out-of-Scope / Deferred

- `reference_data/` directory cleanup
- `backend/archive/`, `backend/artifacts/`, `backend/api/`, `backend/dependencies/`, `backend/jobs/`, `backend/location_service/`, `backend/scripts/`, `backend/seeds/`, `backend/tasks/`, `backend/providers/`
- Root-level files `auth.py`, `config.py`, `database.py`, `dependencies.py`, `email_service.py`, `exceptions.py`, `main.py`, `models.py`, `schemas.py`, `requirements.txt`
- Fixing pre-existing circular imports
- Debug/scratch files in `services/` like `fix_chat.py`, `write_chat.py`, `run_py.py`, `script1.py`, `write_files_script.py`, `maker.py`, `template.py`
