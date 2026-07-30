# Plan: Domain Sub-Packaging of `routers/`, `services/`, `controllers/` (Option A)

**Goal:** Restructure the three flat mega-directories into domain sub-packages so every
AI session / developer has ONE obvious home per domain (employees, finance, products,
suppliers, logistics, etc.). This stops the recurring "AI created a new file instead of
extending the real one" problem.

**Hard constraint:** Zero code loss. Move-only. Verify after every domain batch:
- Boot routes == **1439**
- `alembic heads` == **0006**
- `import routers, services, controllers, models, db, utils, middleware, accounts, providers` OK

---

## Why this is safe (keystone finding)
`main.py` registers routers via an EXPLICIT list `router_names` (main.py:445-498) using
`importlib.import_module(f"routers.{name}")` (main.py:502). `controllers.{name}` is the
fallback (main.py:505). It then does `app.include_router(module.router, prefix=...)`.

=> If `routers/employees.py` becomes `routers/employees/__init__.py`, the import
`routers.employees` STILL resolves to the package `__init__`, and as long as that
`__init__` exposes `router`, **main.py needs ZERO changes**. Same for `controllers/`
and `services/` (imported via `from services.X import Y` — a package `__init__` re-export
keeps that working).

This is the safest possible structure for a 1439-route app: each domain becomes a
package whose `__init__.py` re-exports the same public names the flat module used to.

---

## Target structure
```
backend/
  routers/
    employees/__init__.py        # re-exports router from employees.py + hr.py + employee_*.py
    finance/__init__.py          # accounting, finance, treasury, commissions, expenses, etc.
    products/__init__.py
    suppliers/__init__.py
    logistics/__init__.py
    admin/__init__.py            # the admin_* family
    auth/__init__.py
    chat/__init__.py
    country/__init__.py
    payments/__init__.py
    marketing/__init__.py        # banners, coupons, flash_sales, referrals, promotions
    media/__init__.py
    orders/__init__.py
    ai/__init__.py
    search/__init__.py
    risk/__init__.py             # fraud, compliance, risk, audit, ediscovery
    {other domains}/
  services/
    employees/  finance/  products/  suppliers/  logistics/  auth/  chat/  country/
    payments/   marketing/ media/    orders/    ai/        search/  risk/   {other}/
  controllers/
    employees/  finance/  products/  suppliers/  logistics/  admin/  auth/  chat/
    country/    payments/ marketing/ orders/    ai/        search/  risk/   {other}/
```

For each moved module `X.py` -> `domain/X.py` inside the sub-package, and the sub-package
`__init__.py` does `from .X import *` (and `router = X.router` where applicable).

---

## DOMAIN MAP (grounded in actual file lists)

### EMPLOYEES (routers: employees, hr, employee_controller-ish; controllers: employee_controller, employees_controller, hr_controller; services: attendance_service, leave_accrual, offboarding, payroll_engine, payroll_service, shift_handover, shift_roster_service, shift_scheduling, hierarchy_service, succession_service, dei_auditor, hse_manager, biometric_auth, employee_* )
- routers: `employees.py`, `hr.py`
- controllers: `employee_controller.py`, `employees_controller.py`, `hr_controller.py`
- services: `attendance_service.py`, `leave_accrual.py`, `offboarding.py`, `payroll_engine.py`, `payroll_service.py`, `shift_handover.py`, `shift_roster_service.py`, `shift_scheduling.py`, `hierarchy_service.py`, `succession_service.py`, `dei_auditor.py`, `hse_manager.py`, `biometric_auth.py`

### FINANCE (routers: accounting, accounting_extra, finance, finance_automation, finance_erp, admin_treasury, treasury, admin_cash, cash_management, commission, admin_commission, expenses, admin_payouts, supplier_payouts, api_v1_finance, cross_border; controllers: accounting_controller, financial_controller, treasury_controller, commission_controller, expense_controller, sub_ledger_controller, cash_management_controller; services: commission_engine, general_ledger_service, treasury_engine, treasury_service, treasury_adapter, treasurer, finance_transfer_service, finance_automation, finance_automation_orchestrator, erp_finance_service, financial_reporting, financial_reports_service, cash_flow_forecast_service, cash_flow_writer, period_close_service, je_reversal_service, consolidation_service, sub_ledger_service, payment_orchestrator(?), payout_engine, tax_service)
- Note: `cross_border*` and `supplier_payouts` may also belong to suppliers/country — decide per batch.

### PRODUCTS (routers: products, categories, product_moderation, product_verification, product_videos, media, upload, ai_image, ai_upload; controllers: products_controller, categories_controller, product_verification_controller; services: image_ai_service, bg_removal_service, bg_removal_presets, free_image_tools, media_service, media_storage, content_service)
- AI image sub-files can nest under `products/ai/` or `ai/`.

### SUPPLIERS (routers: supplier, supplier_profile, supplier_products, supplier_orders, supplier_documents, supplier_analytics, supplier_health, public_suppliers, supplier_payouts; controllers: supplier_controller, supplier_document_controller; services: supplier_onboarding_service, supplier_health_engine, payment_orchestrator(?), payout_engine)

### LOGISTICS (routers: logistics, logistics_orders, logistics_locations, logistics_health, logistics_partner, shipments, parcel_tracking, shop_locations, geo, cross_border; controllers: logistics_controller, logistics_partner_controller; services: logistics_engine, logistics_health_engine, logistics_partner_pricing, logistics_sla_service, shipping_tier, geo_fence_service, live_tracking_service, map_service, travel_service, travel_detector)

### ADMIN (routers: admin, admin_users, admin_products, admin_orders, admin_settings, admin_categories, admin_banners, admin_promotions, admin_logistics, admin_email, admin_suppliers, admin_analytics, admin_chat, admin_video, admin_cash, admin_commission, admin_payouts, admin_treasury; controllers: admin_controller; services: command_center_service, command_center_background, approval_matrix_service, rbac_service, permission_service, staff_permissions(utils))

### AUTH & USERS (routers: auth, users, permissions, iam; controllers: auth_controller, permissions_controller, iam_controller; services: iam_service, mobile_auth_service, triple_auth, qr_service, kms_encryption, kms_integration(utils), rbac_service)

### CHAT & COMMS (routers: chat, chatbot, ws_chat, comm, messaging, entity_chat, entity_communication, proxy_communication, internal_channels, notifications, push_notifications, email, admin_email, translate, video, video_controller; controllers: chat_controller, chatbot_controller, comm_controller, notifications_controller, email_controller, video_controller, mobile_controller, operational_controller; services: chat_system, websocket_chat, write_chat, fix_chat, write_files_script, entity_chat_service, internal_communication, proxy_communication, external_contact, email_gateway, email_event_service, email_reputation, transactional_email_service, imap_mailer, notification_engine, notification_service, translation_service, video_service, video_conferencing, communication_audit)

### COUNTRY (routers: countries, country_admin, country_auto_populate, country_dropdown, country_maps, country_payouts, country_research, country_staff, cross_border, admin_settings(country bits); controllers: country_controller, country_versioning_controller; services: country_auto_populate, country_data_orchestrator, country_detection, country_heuristic_engine, country_research, country_rls_service, cross_border_detection, cross_border_service, cross_border_tracker, data_residency, data_residency_service, localization_service, legal_contract_service)

### PAYMENTS (routers: payments, admin_cash; controllers: payments_controller; services: payment_engine, payment_orchestrator, payout_engine(?suppliers/finance), webhook_processor, gateway_auto_enable)

### MARKETING (routers: banners, coupons, flash_sales, referrals, promotions->marketing; controllers: banner_controller, coupons_controller, flash_sale_controller, promotion_controller; services: marketing-adjacent)

### ORDERS & CART (routers: orders, cart, returns, addresses, wishlist, reviews, invoices; controllers: orders_controller, cart_controller, returns_controller, address_controller, wishlist_controller, reviews_controller, invoice_controller; services: invoice/order related)

### AI (routers: ai, ai_image, ai_upload; controllers: ai_controller; services: ai_service, ai_search_service, advanced_search_engine, ai_copy_jobs, ai_variant_config, llm_finance, confidence_scoring, ocr_parser, worm_audit)

### SEARCH (routers: search; controllers: search_controller; services: advanced_search_engine, ai_search_service)

### RISK/SECURITY (routers: fraud_detection, risk, compliance, audit, ediscovery, csp_reporting, security_*; controllers: risk_controller, compliance_controller, audit_controller, disputes_controller; services: fraud_detection, fraud_detection_service, fraud_service, compliance_engine, audit_service, audit_trail_service, ediscovery, coi_engine, coi_service, incident_service, retention_service, ghost_watchdog)

### OTHER / SHARED (routers: command_center, jobs, tickets, onboarding, incident, escalation, okr, workflows, travel, succession, customer_health, export, contact, location_api; controllers: command_center, command_center_controller, incident_controller, escalation, okr, workflows, onboarding, customer_health, export, travel, succession; services: onboarding_pipeline, incident_service, escalation_sla, okr_engine, workflow_engine, customer_health_engine, ticket/helpdesk, jobs/scheduler-adjacent)
- These low-traffic / cross-cutting domains can be grouped into `operations/` or kept
  flat until a later batch.

---

## EXECUTION PROCEDURE (per domain batch)
1. Create `routers/<domain>/` (and `services/<domain>/`, `controllers/<domain>/` as needed).
2. `git mv` (or Move-Item) each file `routers/X.py` -> `routers/<domain>/X.py`.
3. Write `routers/<domain>/__init__.py`:
   ```python
   from .X import router, public_router  # re-export what main.py expects
   from .Y import router as Y_router
   ```
   If multiple routers in one package, expose each distinctly and keep a combined
   `router` only where main.py expects one. For domains with several routers, register
   them individually in main.py's `router_names` list (add `("<domain>.X", "/prefix")`).
4. Update internal imports: files moved together that imported each other via
   `from routers.X import ...` -> `from routers.<domain>.X import ...` OR keep working via
   the `__init__` re-export (preferred — fewer edits).
5. **Verify:** boot 1439, alembic 0006, package imports OK.
6. Commit the batch separately.

## CRITICAL RECURRENCE PREVENTION
After all batches, add `backend/AGENTS.md` (or append to existing AGENTS.md) with:
- "DOMAIN OWNERSHIP: employees->routers/employees/, finance->routers/finance/, etc."
- "NEVER create a new root-level file in routers/, services/, controllers/. Extend the
  domain sub-package. If a domain doesn't exist yet, create the sub-package."
- A table mapping every domain -> its folder.
This doc is the actual fix; the folder move just enables it.

## ORDER OF BATCHES (lowest-risk first, pilot then scale)
1. **PILOT: employees** (small, isolated, high duplication pain) — prove the pattern.
2. finance
3. products
4. suppliers
5. logistics
6. admin
7. auth
8. chat_comms
9. country
10. payments
11. marketing
12. orders_cart
13. ai
14. search
15. risk_security
16. other/shared

## ROLLSBACK
Every batch is a `git` commit; `archive/` tomb not needed since files are moved, not
deleted. If a batch breaks boot, `git revert` that one commit.

## VERIFICATION GATE (must pass each batch)
- `python -c "import main; print(len(main.app.routes))"` == 1439
- `alembic heads` == 0006_media_assets_cdn_url
- `python -c "import routers, services, controllers, models, db, utils, middleware, accounts, providers"` OK
