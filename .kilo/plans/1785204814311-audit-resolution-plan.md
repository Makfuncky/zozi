# Audit Resolution Plan — ZOZI Platform

**Status:** Planning  
**Goal:** Resolve all remaining audit issues with a concrete file-to-file execution map.  
**Out of scope:** New features, schema changes beyond audit findings, production data migration.

## 1. Ground Rules
- Keep every public import path backward-compatible until the full split is landed.
- Each phase must be independently testable.
- No source edits in this plan; this file is the implementation contract.

## 2. Phased Execution Order
1. Backend structural refactor (`H1`, `H2`, backend medium/large-file splits)
2. Frontend large-file splits (`H15`, web medium issues)
3. Mobile large-file split (`H20`, mobile medium issues)
4. Cross-cutting RSC/code-splitting (`H12`, `H18`)
5. Verification and regression gate

## 3. Backend Phase

### 3.1 H1 — `backend/dependencies.py` (718 lines) is dead code. Decision required.

**Finding:** `backend/dependencies.py` defines `router = APIRouter(tags=["accounts"])` and ~30 route handlers, plus Pydantic models. However:
- `_load_routers()` in `main.py` (lines 202–395) only scans `routers.{name}` and `controllers.{name}` — it never imports `dependencies`.
- There is no `app.include_router(dependencies.router)` anywhere in the codebase.
- `dependencies.py` line 20 imports `from controllers.accounts import coa, journal, subledgers, periods, multi_book, fx, controls` — the `controllers/accounts` module does not exist.
- No other file imports `dependencies.router` or references routes from this file.

**Decision point (must resolve before implementation):**
- **Option A (recommended):** Delete `backend/dependencies.py` entirely as dead code. The legacy `/accounting` and `/finance` surfaces are already covered by `routers/accounting.py` and other registered routers.
- **Option B:** Complete the versioned API migration by moving the route handlers into a proper `routers/accounts_v1.py` file, registering it in `_load_routers()` with prefix `/api/v1/accounts`, and fixing the broken `controllers.accounts` imports (which would require creating or locating the actual target modules).

**If Option B is chosen:**
- New file: `backend/routers/accounts_v1.py` — contains all route handlers from `dependencies.py`.
- Update `_load_routers()` static list at `main.py` line 206 to include `("accounts_v1", "/api/v1/accounts")`.
- Fix or remove the broken `from controllers.accounts import ...` line; if the target services exist elsewhere, re-import from the correct module.

**If Option A is chosen:**
- Delete `backend/dependencies.py`.
- Audit any files that import from `dependencies` (e.g., `from dependencies import require_accounts_admin`) and clean up orphan imports. Note: `backend/dependencies/country_rls.py` is a separate module and is currently unused; leave it unless explicitly targeted.

**Validation:**
- `grep -r "dependencies\.py" backend/` — should return zero references after deletion.
- `python -m py_compile backend/main.py` — ensure no import errors.
- Smoke test: `uvicorn backend.main:app --reload` and verify `/docs` loads without missing-router warnings.

### 3.2 H2 — Extract service layer from 4 mega-controllers
Target:
- `backend/controllers/payments_controller.py` → 4,483 lines, 100+ functions
- `backend/controllers/admin_controller.py` → 4,340 lines, 100+ functions
- `backend/controllers/logistics_partner_controller.py` → 3,841 lines, 100+ functions
- `backend/controllers/auth_controller.py` → 1,959 lines, 76 functions

Rule: controllers become thin HTTP adapters only. Service functions take explicit `db: Session` parameters. Controllers keep HTTP concerns: parameter parsing, auth dependency injection, response shaping, HTTPException mapping.

#### 3.2.1 Payments controller split
Group boundaries in `backend/controllers/payments_controller.py`:

**`backend/services/payments/config.py`** — gateway config resolution helpers:
- `_resolve_stripe_secret_key` (line 529), `_resolve_stripe_webhook_secret` (line 542), `_apply_stripe_runtime_key` (line 550), `_stripe_configured` (line 559)
- `_resolve_tap_secret_key` (line 564), `_resolve_tap_webhook_secret` (line 572), `_resolve_tap_api_base_url` (line 580), `_resolve_tap_webhook_url` (line 589), `_tap_configured` (line 598)
- `_resolve_paytabs_server_key` (line 603), `_resolve_paytabs_webhook_secret` (line 611), `_verify_paytabs_signature` (line 619), `_resolve_paytabs_profile_id` (line 630), `_resolve_paytabs_api_base_url` (line 638), `_resolve_paytabs_callback_url` (line 648), `_paytabs_configured` (line 657)
- `_resolve_thawani_secret_key` (line 858), `_resolve_thawani_publishable_key` (line 878), `_resolve_thawani_api_base_url` (line 887), `_resolve_thawani_webhook_secret` (line 897), `_thawani_configured` (line 905)

**`backend/services/payments/quote.py`** — payment quotes and snapshots:
- `build_order_payment_snapshot` (line 761), `_payment_provider_runtime_status` (line 679), `_payment_provider_mode_allows` (line 726), `_gateway_charge_quote` (line 733)
- `get_payment_methods_status` (line 919), `get_customer_checkout_gateways` (line 1008), `get_payment_provider_runtime_config` (line 1065), `update_payment_provider_runtime_config` (line 1069)
- `_built_in_gateway_defaults` (line 1096), `_serialize_gateway_connection` (line 1312), `list_payment_gateway_connections` (line 1422), `upsert_payment_gateway_connection` (line 1442), `test_payment_gateway_connection` (line 1505)
- `build_payment_finance_quote` (line 1598)

**`backend/services/payments/stripe.py`** — Stripe flows:
- `create_payment_intent` (line 2213), `create_stripe_checkout_session` (line 2316), `confirm_card_payment` (line 2383), `handle_stripe_webhook` (line 2508)

**`backend/services/payments/tap.py`** — Tap flows:
- `create_tap_charge` (line 2706), `_finalize_tap_charge_status` (line 2807), `confirm_tap_payment` (line 2919), `_verify_tap_signature` (line 3139), `handle_tap_webhook` (line 3162)

**`backend/services/payments/paytabs.py`** — PayTabs flows:
- `_query_paytabs_transaction` (line 2963), `_finalize_paytabs_transaction` (line 2987), `create_paytabs_charge` (line 3053), `confirm_paytabs_payment` (line 3120), `handle_paytabs_callback` (line 3217)

**`backend/services/payments/cod.py`** — COD and order lifecycle:
- `_order_holds_inventory` (line 911), `_mark_coupon_as_used` (line 1926), `_increment_sales_counts` (line 1937), `_finalize_inventory_for_paid_order` (line 1960), `_restore_inventory_for_order` (line 2052)
- `apply_order_status_change` (line 2081), `_confirm_order` (line 2104), `_apply_successful_payment` (line 2162), `confirm_cash_on_delivery_order` (line 2201)

**`backend/services/payments/refund.py`** — refund logic

**`backend/services/payments/reconciliation.py`** — reconciliation logic

**`backend/services/payments/webhook.py`** — webhook idempotency helpers

**`backend/services/payments/schemas.py`** — shared Pydantic request/response models:
- `PaymentIntentRequest` (line 100), `StripeCheckoutSessionRequest` (line 107), and other request models

**`backend/services/payments/utils.py`** — generic helpers:
- `_optional_text` (line 382), `_normalize_gateway_code` (line 387), `_normalize_currency_codes` (line 395), `_decimal_from_value` (line 405), `_float_money` (line 412), `_json_load_dict` (line 416), `_json_load_currency_list` (line 429), `_is_non_placeholder_secret` (line 442), `_gateway_adapter_supported` (line 453), `normalize_checkout_payment_method` (line 458), `gateway_code_for_payment_method` (line 465), `is_checkout_payment_method_allowed` (line 469)
- `_get_gateway_connection_record` (line 496)
- `_get_user_order` (line 1658), `_resolved_payment_currency` (line 1671), `_extract_order_customer_name` (line 1676), `_split_customer_name` (line 1693), `_tap_country_dial_code` (line 1705), `_tap_phone_payload` (line 1710), `_build_tap_customer` (line 1735)
- `_order_charge_total_amount` (line 1770), `_order_gateway_metadata` (line 1777)
- `_paytabs_customer_details` (line 1785), `_paytabs_shipping_details` (line 1785), `_paytabs_transaction_reference` (line 1809), `_paytabs_response_status` (line 1818), `_paytabs_response_message` (line 1827)
- `_stripe_object_get` (line 1836), `_stripe_metadata_map` (line 1855), `_payment_intent_status` (line 1877), `_payment_intent_id` (line 1881), `_payment_intent_matches_order` (line 1885)
- `_tap_error_detail` (line 2795)

Per-controller migration rule:
1. Create service module and move business-logic functions there with explicit `db: Session` parameters where needed.
2. Replace controller logic with thin call to service function.
3. Keep controller responsible for HTTP concerns only: parameter parsing, response shaping, auth dependency, HTTPException mapping.
4. Update `backend/main.py` router registrations if file paths change.

Validation:
- `pytest backend/tests` after each controller split.
- Diff route responses with recorded snapshots or manual curl checks before/after.

#### 3.2.2 Admin controller split
Group boundaries in `backend/controllers/admin_controller.py`:

**`backend/services/admin/users.py`**:
- `get_all_users` (line 630), `update_user_role` (line 681), `toggle_user_active` (line 710)
- `_build_user_delete_blocker` (line 819), `_delete_user_ticket_records` (line 853), `_cleanup_user_references` (line 886), `_hard_delete_user_record` (line 901), `_delete_order_records` (line 908), `delete_user_admin` (line 991), `bulk_delete_users_admin` (line 1053), `force_reset_password_admin` (line 1119)

**`backend/services/admin/staff.py`**:
- `_effective_staff_permissions` (line 196), `_serialize_staff_user` (line 203), `get_staff_permission_catalog` (line 227), `list_staff_accounts` (line 244)
- `create_staff_account` (line 1754), `update_staff_account` (line 1815), `delete_staff_account` (line 1897), `bulk_update_staff_accounts` (line 1919)

**`backend/services/admin/orders.py`**:
- `bulk_update_order_status_admin` (line 1154), `bulk_delete_orders_admin` (line 1212), `delete_order_admin` (line 1721)
- `_order_to_dict` (line 2146), `_can_staff_override_order_status` (line 2170), `update_order_status` (line 2178), `refund_order` (line 2259), `update_order_tracking` (line 2333)

**`backend/services/admin/products.py`**:
- `get_all_products` (line 2396), `delete_product_admin` (line 2436), `restore_product_admin` (line 2501)
- `_product_to_dict` (line 2371), `_variant_to_dict` (line 2385)
- `bulk_delete_products_admin` (line 1267), `bulk_product_moderation` (line 1312), `approve_product` (line 3160), `reject_product` (line 3203)
- `archive_entity` (line 2526), `restore_entity` (line 2564), `bulk_archive_entities` (line 2586), `bulk_restore_entities` (line 2609), `hard_delete_entity` (line 2631), `bulk_category_change` (line 2654)

**`backend/services/admin/analytics.py`**:
- `_load_admin_analytics_snapshot` (line 88), `_store_admin_analytics_snapshot` (line 102), `_get_admin_analytics_payload` (line 134), `refresh_admin_analytics_snapshots` (line 163)
- `get_database_overview` (line 486), `_database_health_snapshot` (line 366), `_safe_database_location` (line 374), `_table_row_count` (line 382), `_table_column_details` (line 394), `_sqlite_service_snapshot` (line 413), `_postgres_service_snapshot` (line 434), `_redis_service_snapshot` (line 456), `_database_architecture_snapshot` (line 476)
- `_compute_analytics_overview` (line 2687), `get_analytics` (line 2731), `get_supplier_comparison` (line 2735)
- `get_customer_insights` (line 2860)
- `_compute_analytics_timeseries_payload` (line 3701), `get_analytics_timeseries` (line 3733)
- `_compute_top_products_payload` (line 3744)

**`backend/services/admin/content.py`**:
- `list_coupons` (line 3235), `create_coupon` (line 3267), `update_coupon` (line 3309), `delete_coupon` (line 3326)
- `_serialize_ticket_attachment` (line 3352), `_serialize_ticket_message` (line 3363), `_serialize_support_ticket` (line 3376), `list_tickets` (line 3401), `get_ticket_detail` (line 3421), `reply_to_ticket` (line 3428), `update_ticket_status` (line 3457)
- `bulk_supplier_verification` (line 1387), `bulk_manage_suppliers` (line 1471), `get_pending_suppliers` (line 2955), `verify_supplier` (line 2981), `reject_supplier` (line 3061)
- `get_pending_products` (line 3104), `toggle_product_badge` (line 3130)
- `load_role_permission_settings` (line 584), `get_hierarchy_permissions` (line 3644), `update_role_permissions` (line 3653)
- `list_pending_payouts` (line 3470), `_refresh_order_finance_settlement_status` (line 3494), `_sync_supplier_settlements_for_payout` (line 3537), `verify_payout` (line 3569)
- `get_audit_log_page` (line 2921), `get_available_audit_actions` (line 2949)
- `bulk_update_users_role` (line 1590), `bulk_toggle_users_active` (line 1668)

**`backend/services/admin/helpers.py`** — shared helpers kept in controller:
- `_build_list_page_payload` (line 76), `_database_health_snapshot` (line 366), `_safe_database_location` (line 374), `_table_row_count` (line 382), `_table_column_details` (line 394), `_serialize_staff_user` (line 203), `_effective_staff_permissions` (line 196)

#### 3.2.3 Logistics partner controller split
Group boundaries in `backend/controllers/logistics_partner_controller.py`:

**`backend/services/logistics/partners.py`**:
- `_next_partner_code` (line 58), `_serialize_partner` (line 68), `_sanitize_optional_string` (line 132), `_build_partner_delete_blocker` (line 139), `_parse_partner_social_links` (line 147), `_parse_partner_service_area_payload` (line 160), `_parse_pricing_profile_payload` (line 262), `_parse_optional_service_area_id` (line 344), `_parse_category_pricing_rule_payload` (line 354), `_parse_vehicle_rule_payload` (line 389), `_validate_partner_service_area` (line 443)
- `_pickup_visible_to_partner` (line 458), `_require_admin` (line 469), `_get_partner_for_user` (line 474), `_partner_is_active` (line 496), `_resolve_partner_user_link` (line 500)
- `get_my_partner_profile` (line 548), `update_my_partner_profile` (line 554), `accept_partner_terms` (line 662), `submit_partner_profile_for_review` (line 674)
- `list_my_partner_service_areas` (line 700), `list_my_partner_pricing_profiles` (line 728), `list_my_partner_category_rules` (line 757), `list_my_partner_vehicle_rules` (line 786)
- `upsert_my_partner_service_area` (line 815), `upsert_my_partner_pricing_profile` (line 868), `upsert_my_partner_category_rule` (line 929), `upsert_my_partner_vehicle_rule` (line 990)
- `delete_my_partner_pricing_profile` (line 1051), `delete_my_partner_category_rule` (line 1067), `delete_my_partner_vehicle_rule` (line 1083), `delete_my_partner_service_area` (line 1099)
- `review_partner_profile` (line 1115), `review_partner_service_area` (line 1135), `review_partner_pricing_profile` (line 1154), `review_partner_category_rule` (line 1173), `review_partner_vehicle_rule` (line 1192)
- `list_partners` (line 1967), `create_partner` (line 1987), `update_partner` (line 2067), `delete_partner` (line 2118), `bulk_manage_partners` (line 2139)
- `get_partner_dashboard` (line 2236), `get_partner_analytics` (line 2311), `get_partner_payouts` (line 2318), `request_partner_payout` (line 2335), `list_pending_partner_payouts` (line 2393), `verify_partner_payout` (line 2404)
- `get_partner_bank_account` (line 3415), `upsert_partner_bank_account` (line 3450)
- `list_partner_documents` (line 3522), `upload_partner_document` (line 3611), `delete_partner_document` (line 3669), `admin_review_lp_document` (line 3687)
- `list_partner_cod_remittance_receipts` (line 3536), `upload_partner_cod_remittance_receipt` (line 3556)
- `list_city_distances` (line 3732), `create_city_distance` (line 3764), `update_city_distance` (line 3810)

**`backend/services/logistics/shipments.py`**:
- `shipping_quote_for_customer` (line 1211), `list_public_partners` (line 1259), `get_public_partner` (line 1312)
- `_scoped_shipments_query` (line 1335), `_partner_visible_shipments_query` (line 1345), `_is_shipment_visible_to_partner` (line 1369), `_is_pickup_ready` (line 1376), `_partner_api_status` (line 1383), `_status_display` (line 1389)
- `get_partner_shipments` (line 2628), `create_shipment_confirmation_request_partner` (line 2755), `update_shipment_status_partner` (line 3052), `bulk_update_shipment_status_partner` (line 3241)
- `scan_lookup_shipment_partner` (line 2466)

**`backend/services/logistics/tracking.py`**:
- `_apply_delivery_signature` (line 1394), `_extract_delivery_signature` (line 1407), `_active_confirmation_map` (line 1418), `_notify_partner_transition` (line 1438)
- `_calculate_partner_analytics` (line 1474), `_partner_dashboard_shipments_query` (line 1535), `_filter_partner_analytics_period` (line 1551), `_serialize_partner_analytics_payload` (line 1567), `_serialize_partner_payout` (line 1589), `_order_shipment_counts` (line 1608), `_format_compound_location` (line 1620), `_shipment_pickup_details` (line 1629), `_shipment_logistics_allocation` (line 1651), `_shipment_effective_pricing_breakdown` (line 1667), `_shipment_partner_revenue` (line 1677), `_calculate_partner_payout_summary` (line 1696), `_latest_geo_events_for_shipments` (line 1763), `_build_live_locations` (line 1785), `_haversine_km` (line 1809), `_build_route_plan` (line 1817), `_collect_sla_alerts` (line 1871), `_ensure_sla_notifications` (line 1903), `_publish_shipment_update` (line 1935)
- `get_partner_pricing_insights` (line 2885)

**`backend/services/logistics/pricing.py`** — pricing helpers

**`backend/services/logistics/cod.py`** — COD remittance helpers

#### 3.2.4 Auth controller split
Group boundaries in `backend/controllers/auth_controller.py`:

**`backend/services/auth/social.py`**:
- `get_social_providers_status` (line 153)
- `_normalize_customer_verification_when_gate_disabled` (line 177), `_resolve_user_from_subject` (line 187)
- `_user_id` (line 194), `_user_username` (line 198), `_user_email` (line 202), `_user_role` (line 206), `_user_phone` (line 210), `_user_email_verified` (line 214), `_user_profile_image` (line 218), `_user_effective_permissions` (line 223), `_user_staff_payload` (line 235), `_user_public_payload` (line 330)
- `_total_referral_points` (line 253), `_build_referral_link` (line 259), `_referral_event_description` (line 263), `_serialize_referral_event` (line 272), `_generate_unique_referral_code` (line 290)
- `_ensure_verification_delivery_available` (line 300), `_record_referral_event` (line 310)
- `_create_social_user` (line 630), `_resolve_or_create_social_user` (line 656)
- `_oauth_state_cookie_name` (line 679), `_build_social_redirect_response` (line 683), `_validate_social_state` (line 696), `_frontend_social_callback` (line 702), `_resolve_google_identity_token` (line 714)
- `get_google_oauth_start` (line 736), `handle_google_id_token_login` (line 755), `handle_google_oauth_callback` (line 781)
- `get_facebook_oauth_start` (line 834), `handle_facebook_oauth_callback` (line 852)

**`backend/services/auth/login.py`**:
- `_find_user_for_login` (line 441), `_record_device_fingerprint` (line 456)
- `_issue_auth_tokens` (line 498), `_log_login_success` (line 536), `_persist_last_login` (line 552), `_create_tokens_response` (line 568)
- `_slugify_username` (line 594), `_unique_username` (line 599), `_extract_avatar_url` (line 612)
- `login_user` (line 1182), `json_login_user` (line 1260)

**`backend/services/auth/registration.py`**:
- `register_user` (line 909), `json_register_user` (line 1391)
- `verify_email_token` (line 1070), `resend_verification` (line 1096), `resend_verification_public` (line 1134)
- `_ensure_referral_code` (line 1417)

**`backend/services/auth/profile.py`**:
- `get_current_user` (line 356), `get_optional_user` (line 397)
- `get_referral_dashboard` (line 1428), `get_referral_history` (line 1458), `claim_share_points` (line 1481)
- `update_profile` (line 1585), `upload_avatar` (line 1633), `change_password` (line 1659)
- `forgot_password` (line 1674), `reset_password` (line 1702)
- `get_user_preferences` (line 1739), `update_user_preferences` (line 1758)

**`backend/services/auth/tokens.py`**:
- `refresh_access_token` (line 1324), `logout_user` (line 1539)

**`backend/services/auth/otp.py`**:
- `_issue_totp_challenge` (line 1240), `_generate_totp_provisioning_uri` (line 1790), `_validate_totp_code` (line 1801), `setup_totp` (line 1809), `enable_totp` (line 1827), `disable_totp` (line 1855), `_verify_totp_code_with_fallback` (line 1873), `complete_totp_login` (line 1891), `admin_verify_totp` (line 1921)
- `get_totp_status` (line 1782)

**`backend/services/auth/helpers.py`** — shared auth helpers:
- `resolve_rate_limit` (line 100)

Validation:
- `pytest backend/tests` after each controller split.
- Diff route responses with recorded snapshots or manual curl checks before/after.

### 3.3 Backend medium/large-file splits
- `backend/utils/order_tracking.py` (820 lines) → `order_tracking/status.py`, `order_tracking/financials.py`, `order_tracking/shipments.py`, `order_tracking/__init__.py`
- `backend/utils/schema_audit.py` (956 lines) → `schema_audit/validation.py`, `schema_audit/reporting.py`, `schema_audit/comparison.py`, `schema_audit/__init__.py`
- `backend/utils/realtime.py` (654 lines) → `realtime/hub.py`, `realtime/connections.py`, `realtime/broadcast.py`, `realtime/__init__.py`
- `backend/utils/rls_interceptor.py` (431 lines) → `rls_interceptor/policies.py`, `rls_interceptor/execution.py`, `rls_interceptor/__init__.py`
- `backend/utils/email_service.py` (653 lines) → `email_service/smtp.py`, `email_service/templates.py`, `email_service/sender.py`, `email_service/__init__.py`

Implementation agent must read each file and identify exact function/class boundaries before splitting. Keep `__init__.py` as a re-export shim for backward compatibility.

Validation:
- `python -m py_compile backend/utils/<new_package>/*.py`
- Run existing backend tests.

### 3.4 Backend medium fixes

- `backend/middleware/pci_dss_compliance.py`:
  - `pci_dss_required` decorator (around line 137) creates a new `PCIDSSCompliance()` per call, while `PCIDSSMiddleware` uses a class-level singleton. Change decorator to reuse the singleton or inject from `app.state`.
  - Replace `os.environ.get("APP_ENV", "")` with `str(settings.app_env).lower()` for consistency.
  - Document that reverse proxies must set `X-Forwarded-Proto` (scheme resolution already present).

- `backend/middleware/security_headers.py`:
  - Production `CSP_POLICY` does not include `ws:`/`wss:`. Add app-specific WebSocket origin (e.g., `ws: wss:`) or document that WebSockets are blocked in production CSP.
  - `CSP_POLICY_DEV` includes localhost origins — these are already gated by the `settings.app_env.lower() != "production"` branch at line 92. No further change needed.

- `backend/middleware/rate_limit_middleware.py`:
  - `loadtest_profile_enabled` (around line 119) currently short-circuits the entire middleware, returning `call_next` without any limit checks. Remove the early return; instead, keep the warning log and raise the configured limits (e.g., multiply max_requests by 10 or disable per-route limits only).
  - Redis failure (around line 136) silently falls back to in-memory limit. Replace with a logged warning (`logger.warning`) and per-IP grace mode (e.g., allow 2x the normal limit for 60 seconds) rather than full in-memory rate limiting.

- `backend/middleware/country_context.py`:
  - JWT decode is wrapped in try/except. Verify `decode_token` in `utils/auth.py` raises `JWTError` on expired/malformed tokens; if it raises other exceptions, broaden the except clause.
  - `CountryDetectionService` instance caching is already implemented. No change needed.

- `backend/utils/config.py` — migrate from hand-rolled `Settings` class to Pydantic `BaseSettings`:
  - Create `backend/utils/config_new.py` with `class Settings(BaseSettings)` preserving all existing env var names, defaults, and type casting (`_BOOL_KEYS`, `_INT_KEYS`, `_FLOAT_KEYS`).
  - Keep the module-level `settings = Settings()` singleton so all existing `from utils.config import settings` imports continue to work.
  - Remove dotenv loading from the new file; load `.env` at application entry point (e.g., `main.py` or a dedicated `load_env.py`).
  - Validation: all existing imports of `settings.X` must return identical values.

- `backend/requirements.txt`: `python-decouple` is not present. No action needed.

### 3.5 Backend auth — token blacklist multi-worker safety
- `backend/utils/auth.py` uses an in-memory dict `_memory_blacklist` (line 27) as fallback when Redis is unavailable. This does not work across multiple workers/processes.
- Migrate to Redis-backed blacklist as the primary store:
  - Keep the in-memory dict as a local L1 cache with TTL, but write-through to Redis.
  - Add a `token_blacklist` database table as the authoritative store for production deployments without Redis.
- Document the limitation in a code comment at `_memory_blacklist` declaration.

### 3.6 Backend database — `backend/db/database.py` cleanup
Current state: 1 engine (`engine`), 1 session factory (`SessionLocal`), 4 session helper functions.

- `get_db_session()` (line 126): returns a session without commit/rollback/close. Callers in `main.py` health endpoints use it with explicit `db.close()`. **Fix:** add explicit commit on success, rollback on exception, and close in `finally`, or convert to a context manager. Do NOT leave bare session creation in a public helper.
- `get_db_sync()` (line 173): creates a session and closes it in `finally`, but never commits or rolls back. **Fix:** add commit on success, rollback on exception.
- `get_db_context()` (line 155) and `get_service_session()` (line 131) are identical context managers. **Fix:** consolidate into a single `get_db_context()` and have `get_service_session()` delegate to it (or vice versa), preserving the `timeout_seconds` warning in the service variant.
- `db.base` is the canonical `Base` export. `db.database` remains the canonical module for engine/session utilities. Do NOT try to consolidate `get_db`/`engine` imports to `db.base`.

Validation:
- `python -m py_compile backend/db/database.py`
- Run backend tests; verify health endpoints still pass.

## 4. Frontend Web Phase

### 4.1 H15 — Split frontend files >1000 lines
Target files and split plan. Implementation agent must read each file and identify exact component/function boundaries before splitting.

- `frontend/web_app/src/app/admin/countries/page.tsx` (3,562 lines) → extract into:
  - `frontend/web_app/src/app/admin/countries/CountryList.tsx` — table/list view
  - `frontend/web_app/src/app/admin/countries/CountryForm.tsx` — create/edit form
  - `frontend/web_app/src/app/admin/countries/CountryDetail.tsx` — detail view
  - `frontend/web_app/src/app/admin/countries/CountryLedgerTable.tsx` — already exists (219 lines), integrate it
  - keep `page.tsx` as composition root with `{list, form, detail}` state orchestration

- `frontend/web_app/src/app/admin/treasury/treasury-content.tsx` (2,300 lines) → extract into:
  - `frontend/web_app/src/app/admin/treasury/TreasuryDashboard.tsx` — top-level dashboard shell
  - `frontend/web_app/src/app/admin/treasury/TreasuryCharts.tsx` — chart components
  - `frontend/web_app/src/app/admin/treasury/TreasuryTables.tsx` — data tables
  - keep `page.tsx` as composition root

- `frontend/web_app/src/app/logistics-partner/profile/page.tsx` (2,273 lines) → extract into:
  - `frontend/web_app/src/app/logistics-partner/profile/ProfileView.tsx` — read-only profile display
  - `frontend/web_app/src/app/logistics-partner/profile/ProfileEdit.tsx` — edit form
  - `frontend/web_app/src/app/logistics-partner/profile/ProfileSecurity.tsx` — security settings
  - keep `page.tsx` as composition root

- `frontend/web_app/src/app/supplier/products/add/page.tsx` (2,140 lines) → extract into:
  - `frontend/web_app/src/app/supplier/products/add/ProductForm.tsx` — core product fields
  - `frontend/web_app/src/app/supplier/products/add/ProductMedia.tsx` — media upload/preview
  - `frontend/web_app/src/app/supplier/products/add/ProductReview.tsx` — review/submit step
  - keep `page.tsx` as composition root

- `frontend/web_app/src/app/supplier/products/[id]/page.tsx` (2,140 lines) → extract into:
  - `frontend/web_app/src/app/supplier/products/[id]/ProductEditor.tsx` — core edit form
  - `frontend/web_app/src/app/supplier/products/[id]/ProductInventory.tsx` — inventory/stock section
  - `frontend/web_app/src/app/supplier/products/[id]/ProductPricing.tsx` — pricing section
  - keep `page.tsx` as composition root

- `frontend/web_app/src/app/supplier/batch-upload/page.tsx` (2,077 lines) → extract into:
  - `frontend/web_app/src/app/supplier/batch-upload/BatchUploadWizard.tsx` — multi-step wizard
  - `frontend/web_app/src/app/supplier/batch-upload/BatchPreview.tsx` — preview table
  - `frontend/web_app/src/app/supplier/batch-upload/BatchHistory.tsx` — past uploads
  - keep `page.tsx` as composition root

- `frontend/web_app/src/app/supplier/profile/page.tsx` (1,797 lines) → extract into:
  - `frontend/web_app/src/app/supplier/profile/ProfileHeader.tsx` — header/avatar
  - `frontend/web_app/src/app/supplier/profile/ProfileSettings.tsx` — settings form
  - `frontend/web_app/src/app/supplier/profile/ProfileDocuments.tsx` — document management
  - keep `page.tsx` as composition root

- `frontend/web_app/src/components/BannerCanvasEditor.tsx` (1,792 lines) → extract into:
  - `frontend/web_app/src/components/BannerCanvasEditor/Toolbar.tsx` — toolbar controls
  - `frontend/web_app/src/components/BannerCanvasEditor/Canvas.tsx` — canvas rendering
  - `frontend/web_app/src/components/BannerCanvasEditor/Layers.tsx` — layer management
  - keep `BannerCanvasEditor.tsx` as composition root

Rule: extracted components use named exports, original files become composition roots, imports update in place. Do NOT create barrel `index.ts` files unless the directory already has one.

Validation:
- `npm run typecheck` in `frontend/web_app`
- `npm run lint`
- Manual smoke test of affected routes.

### 4.2 Frontend medium issues
- Standardize layouts: create `frontend/web_app/src/components/layouts/AdminLayout.tsx`, `SupplierLayout.tsx`, `LogisticsLayout.tsx`. Replace duplicated layout wrappers in `app/admin/**/page.tsx`, `app/supplier/**/page.tsx`, and `app/logistics-partner/**/page.tsx`.
- Add error boundaries: wrap `page.tsx` roots in `frontend/web_app/src/app/admin/**/`, `frontend/web_app/src/app/supplier/**/`, and `frontend/web_app/src/app/logistics-partner/**/` with a shared `PageErrorBoundary` component.
- Replace `any` with typed interfaces in `frontend/web_app/src/lib/*` and `frontend/web_app/src/components/*` files flagged by the audit. Target files: `variantConfig.ts`, `api/country.ts`, `api/orders.ts`, and any component using `React.FC<{ children: any }>`.
- Update `frontend/web_app/src/lib/api/*` modules to use typed request/response wrappers. Create `ApiResponse<T>` and `ApiError` types in `frontend/web_app/src/lib/api/types.ts` and adopt them across `country.ts`, `orders.ts`, `payments.ts`, `products.ts`.

### 4.3 H12 — React Server Components
Target data-heavy routes first:
- `frontend/web_app/src/app/admin/countries/page.tsx`
- `frontend/web_app/src/app/products/page.tsx`
- `frontend/web_app/src/app/products/[id]/page.tsx`
- `frontend/web_app/src/app/admin/orders/page.tsx`

Rule:
- Remove `"use client"` from pages that only fetch and render.
- Keep `"use client"` only on components with interactivity.
- Use `async` page components and `await` data fetching.

Validation:
- `npm run build` in `frontend/web_app`
- Verify pages render without client hydration errors.

### 4.4 H18 — Code-splitting
Target admin bundle:
- Convert `frontend/web_app/src/app/admin/**/page.tsx` routes to dynamic imports with `next/dynamic` where components are large and route-specific.
- Add `loading.tsx` skeletons for each dynamic segment.

Validation:
- `npm run build` and review route chunks.
- Lighthouse bundle audit to confirm reduction.

## 5. Mobile Phase

### 5.1 H20 — Split `frontend/mobile_app/lib/api.ts` (2,333 lines)
New file map:
- `frontend/mobile_app/lib/api/client.ts` — base URL, headers, request wrapper
- `frontend/mobile_app/lib/api/token.ts` — token storage, refresh, expiry
- `frontend/mobile_app/lib/api/endpoints.ts` — endpoint URL definitions
- `frontend/mobile_app/lib/api/types.ts` — request/response types
- `frontend/mobile_app/lib/api/cache.ts` — cache utilities
- `frontend/mobile_app/lib/api/index.ts` — re-exports for backward compatibility

Implementation agent must read `frontend/mobile_app/lib/api.ts` and identify exact function/class boundaries before splitting.

Validation:
- `npx tsc --noEmit` in `frontend/mobile_app`
- Run mobile test suite.

### 5.2 Mobile medium fixes
- `.gitignore`: add mobile build artifacts (`.expo/`, `dist/`, `web-build/`, `android/app/build/`, `ios/build/`).
- Remove unused polyfills: delete `frontend/mobile_app/polyfills/react.js` (dead code).
- Fix EAS config: review `frontend/mobile_app/eas.json` and `app.json` for deprecated fields; ensure `expo.build.ios.builder` and `expo.build.android.builder` are set correctly.
- Fix TypeScript strict mode violations: run `npx tsc --noEmit --strict` and fix `null`/`undefined` mismatches in `frontend/mobile_app/lib/*.ts` and `frontend/mobile_app/screens/*.tsx`.

## 6. Database Phase
- Add missing indexes for common query paths flagged in N+1 review. Target tables: `orders` (composite index on `customer_id + created_at`), `products` (composite index on `supplier_id + status`), `shipments` (composite index on `order_id + status`).
- Standardize Alembic migration naming: ensure each migration file uses the pattern `YYYYMMDDHHMMSS_description.py` and that `alembic/versions/` has no orphan files.
- `backend/db/database.py` cleanup (see Section 3.6 for concrete targets).
- Review `backend/db/database.py` for duplicate engine/session factory consolidation — confirmed: 1 engine, 1 session factory. No duplicate engines exist.

## 7. Low-Priority Cleanup
- Add lazy imports where startup cost is measurable: target `backend/main.py` and `backend/lifespan.py` for heavy imports inside functions rather than at module top-level.
- Document bcrypt 72-char truncation caveat in `backend/utils/auth.py` near `get_password_hash`.
- Clean up remaining dead imports and unused variables flagged by lint. Run `ruff check backend/` and fix reported issues.
- Remove orphan backup files (e.g., `package.json.wyJ3QXz5UTYVCJ5vF4RXrbU7AaAMy7-F5hmL-pJuRaM` at repo root, `check.js` in mobile root, `polyfills/react.js` in mobile app).

## 8. Risks and Open Questions
1. **H1 dead-code decision:** `backend/dependencies.py` is currently dead code — its routes are never registered and its imports reference a non-existent module. The user must choose between deletion (Option A) and completing the versioned API migration (Option B). This decision gates all backend structural work.
2. **Backward compatibility during H2:** Service extraction must keep controller functions as thin HTTP adapters. All existing route response shapes must remain identical. The implementation agent must run route-level smoke tests after each controller split.
3. **Service extraction scope:** The controller functions listed are the public API surface. Private helper functions (prefixed `_`) should move with the public functions they support, not be split into separate modules.
4. **Frontend component boundaries:** The suggested split targets are based on file names and sizes. The implementation agent must read each file and verify the component boundaries before creating new files.
5. **RSC adoption risk:** Removing `"use client"` from pages that use hooks, context, or browser APIs will break the page. The implementation agent must verify each page only uses server-safe patterns before converting.
6. **Mobile api.ts dependencies:** The file is 2,333 lines with many cross-references. The implementation agent must identify the dependency graph before splitting to avoid circular imports.
7. **Config migration:** Migrating `utils/config.py` from hand-rolled `Settings` to Pydantic `BaseSettings` must preserve all existing env var names and defaults. Any mismatch will break startup. Validate by comparing `settings` attribute values before and after migration.
8. **Auth blacklist multi-worker:** The in-memory token blacklist does not work across workers. For production with multiple workers, Redis or a database table is required. The migration must not break single-worker dev setups.

## 9. Validation Gate
Run after each phase:
- Backend: `pytest backend/tests`
- Web: `npm run typecheck && npm run lint`
- Mobile: `npx tsc --noEmit`
- Build: Docker build for `backend` and `frontend/web_app`
- E2E: targeted smoke tests for changed routes

## 10. Execution Order Within Phases
Execute in this exact order:
1. `H1` — Resolve `backend/dependencies.py` dead-code decision (delete or register)
2. `H2` — service extraction for `payments_controller.py`
3. `H2` — service extraction for `admin_controller.py`
4. `H2` — service extraction for `logistics_partner_controller.py`
5. `H2` — service extraction for `auth_controller.py`
6. Backend medium + utility splits
7. Backend config.py migration to Pydantic BaseSettings
8. Backend auth blacklist multi-worker migration
9. Backend database.py cleanup (`get_db_session`, `get_db_sync`, consolidate context managers)
10. `H15` — web large-file splits
11. Frontend medium fixes
12. `H12` — RSC adoption
13. `H18` — code-splitting
14. `H20` — mobile `api.ts` split
15. Mobile medium fixes
16. Database fixes (indexes, Alembic naming)
17. Low-priority cleanup
18. Full validation gate
