# DIMENSION: Tables & Fields

## Summary
- Confirmation: FAIL
- Tables inspected: 343
- Tables compliant: 142
- Tables with findings: 201
- Laws implicated: [L-5, L-6, L-19, L-20, L-21, L-22, L-23, L-49, L-53, L-54, L-55, L-56]
- Findings: 272
- P0: 1  P1: 77  P2: 194  P3: 0
- Clusters: 0
- Average confidence: 5/5
- Average evidence strength: triangulated
- Status: NEW: 272 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 78 yes · 0 partial · 194 no

## Tables Inspected

| # | Schema.Table | Model | DB | Findings |
|---|-------------|-------|-----|----------|
| 1 | accounts.addresses | YES | YES | COMPLIANT |
| 2 | accounts.cart_items | YES | YES | COMPLIANT |
| 3 | accounts.carts | YES | YES | COMPLIANT |
| 4 | accounts.email_verification_tokens | YES | YES | COMPLIANT |
| 5 | accounts.logistics_partner_bank_accounts | YES | YES | COMPLIANT |
| 6 | accounts.mfa_factors | YES | YES | COMPLIANT |
| 7 | accounts.ocr_results | YES | YES | COMPLIANT |
| 8 | accounts.onboarding_pipelines | YES | YES | 2 finding(s) |
| 9 | accounts.onboarding_steps | YES | YES | 2 finding(s) |
| 10 | accounts.otp_codes | YES | YES | COMPLIANT |
| 11 | accounts.password_histories | YES | YES | COMPLIANT |
| 12 | accounts.password_reset_tokens | YES | YES | COMPLIANT |
| 13 | accounts.refresh_token_families | YES | YES | COMPLIANT |
| 14 | accounts.revoked_tokens | YES | YES | COMPLIANT |
| 15 | accounts.social_identities | YES | YES | COMPLIANT |
| 16 | accounts.supplier_bank_accounts | YES | YES | COMPLIANT |
| 17 | accounts.user_consents | YES | YES | COMPLIANT |
| 18 | accounts.user_devices | YES | YES | COMPLIANT |
| 19 | accounts.user_login_histories | YES | YES | COMPLIANT |
| 20 | accounts.user_preferences | YES | YES | COMPLIANT |
| 21 | accounts.user_sessions | YES | YES | COMPLIANT |
| 22 | accounts.users | YES | YES | 3 finding(s) |
| 23 | analytics.executive_news | YES | YES | COMPLIANT |
| 24 | analytics.predictive_simulations | YES | YES | COMPLIANT |
| 25 | audit.audit_logs | YES | YES | COMPLIANT |
| 26 | audit.command_center_views | YES | YES | COMPLIANT |
| 27 | catalog.ai_generation_logs | YES | YES | COMPLIANT |
| 28 | catalog.ai_staging_products | YES | YES | COMPLIANT |
| 29 | catalog.ai_staging_variants | YES | YES | COMPLIANT |
| 30 | catalog.ai_upload_jobs | YES | YES | COMPLIANT |
| 31 | catalog.categories | YES | YES | COMPLIANT |
| 32 | catalog.category_attribute_values | YES | YES | COMPLIANT |
| 33 | catalog.category_attributes | YES | YES | COMPLIANT |
| 34 | catalog.chart_of_categories | YES | YES | COMPLIANT |
| 35 | catalog.commission_groups | YES | YES | COMPLIANT |
| 36 | catalog.commission_profiles | YES | YES | COMPLIANT |
| 37 | catalog.commission_rules | YES | YES | COMPLIANT |
| 38 | catalog.commission_transactions | YES | YES | COMPLIANT |
| 39 | catalog.product_filter_metadatas | YES | YES | COMPLIANT |
| 40 | catalog.product_filter_options | YES | YES | COMPLIANT |
| 41 | catalog.product_types | YES | YES | COMPLIANT |
| 42 | catalog.product_variants | YES | YES | COMPLIANT |
| 43 | catalog.product_videos | YES | YES | COMPLIANT |
| 44 | catalog.products | YES | YES | COMPLIANT |
| 45 | catalog.reviews | YES | YES | COMPLIANT |
| 46 | catalog.upload_jobs | YES | YES | 1 finding(s) |
| 47 | catalog.video_analytics | YES | YES | COMPLIANT |
| 48 | catalog.wishlist_items | YES | YES | 3 finding(s) |
| 49 | catalog.wishlists | YES | YES | COMPLIANT |
| 50 | comms.announcements | YES | YES | 2 finding(s) |
| 51 | comms.campaign_recipients | YES | YES | 2 finding(s) |
| 52 | comms.chat_attachments | YES | YES | 1 finding(s) |
| 53 | comms.chat_read_receipts | YES | YES | 1 finding(s) |
| 54 | comms.communication_audit_trails | YES | YES | 2 finding(s) |
| 55 | comms.direct_chat_messages | YES | YES | 2 finding(s) |
| 56 | comms.direct_chat_rooms | YES | YES | 1 finding(s) |
| 57 | comms.email_campaign_logs | YES | YES | 2 finding(s) |
| 58 | comms.email_campaigns | YES | YES | 2 finding(s) |
| 59 | comms.email_delivery_events | YES | YES | 2 finding(s) |
| 60 | comms.email_folders | YES | YES | 2 finding(s) |
| 61 | comms.email_runtime_configs | YES | YES | 1 finding(s) |
| 62 | comms.email_suppressions | YES | YES | 2 finding(s) |
| 63 | comms.email_templates | YES | YES | 2 finding(s) |
| 64 | comms.employee_communication_threads | YES | YES | 1 finding(s) |
| 65 | comms.entity_chat_messages | YES | YES | 3 finding(s) |
| 66 | comms.entity_chat_threads | YES | YES | 2 finding(s) |
| 67 | comms.escalation_sla_logs | YES | YES | 3 finding(s) |
| 68 | comms.escalation_sla_rules | YES | YES | 3 finding(s) |
| 69 | comms.external_contact_maskings | YES | YES | 1 finding(s) |
| 70 | comms.faqs | YES | YES | 2 finding(s) |
| 71 | comms.flash_sale_items | YES | YES | COMPLIANT |
| 72 | comms.group_chat_members | YES | YES | 3 finding(s) |
| 73 | comms.group_chat_messages | YES | YES | 3 finding(s) |
| 74 | comms.group_chat_rooms | YES | YES | 1 finding(s) |
| 75 | comms.help_categories | YES | YES | 2 finding(s) |
| 76 | comms.incident_action_items | YES | YES | 1 finding(s) |
| 77 | comms.incident_threads | YES | YES | 1 finding(s) |
| 78 | comms.incident_war_rooms | YES | YES | 2 finding(s) |
| 79 | comms.internal_channel_members | YES | YES | 1 finding(s) |
| 80 | comms.internal_channels | YES | YES | COMPLIANT |
| 81 | comms.internal_emails | YES | YES | 2 finding(s) |
| 82 | comms.internal_messages | YES | YES | 2 finding(s) |
| 83 | comms.internal_notices | YES | YES | 3 finding(s) |
| 84 | comms.masked_messages | YES | YES | 2 finding(s) |
| 85 | comms.meeting_recordings | YES | YES | 1 finding(s) |
| 86 | comms.messages | YES | YES | 1 finding(s) |
| 87 | comms.news_articles | YES | YES | 1 finding(s) |
| 88 | comms.news_sources | YES | YES | 3 finding(s) |
| 89 | comms.newsletter_subscribers | YES | YES | 2 finding(s) |
| 90 | comms.notification_channels | NO | YES | 1 finding(s) |
| 91 | comms.notification_rules | NO | YES | 1 finding(s) |
| 92 | comms.notification_template_translations | NO | YES | 1 finding(s) |
| 93 | comms.notification_templates | NO | YES | 1 finding(s) |
| 94 | comms.notifications | YES | YES | 2 finding(s) |
| 95 | comms.proxy_call_logs | YES | YES | 1 finding(s) |
| 96 | comms.proxy_channels | YES | YES | 1 finding(s) |
| 97 | comms.proxy_messages | YES | YES | 2 finding(s) |
| 98 | comms.proxy_sessions | YES | YES | 1 finding(s) |
| 99 | comms.push_notification_tokens | NO | YES | 1 finding(s) |
| 100 | comms.support_ticket_replies | YES | YES | 3 finding(s) |
| 101 | comms.support_tickets | YES | YES | 1 finding(s) |
| 102 | comms.ticket_attachments | YES | YES | 3 finding(s) |
| 103 | comms.ticket_messages | YES | YES | 2 finding(s) |
| 104 | comms.video_room_participants | YES | YES | 3 finding(s) |
| 105 | comms.video_room_recordings | YES | YES | 3 finding(s) |
| 106 | comms.video_rooms | YES | YES | 1 finding(s) |
| 107 | comms.war_room_templates | YES | YES | 2 finding(s) |
| 108 | country.country_basics | YES | YES | 1 finding(s) |
| 109 | country.country_category_tax_rates | YES | YES | 1 finding(s) |
| 110 | country.country_cities | YES | YES | 1 finding(s) |
| 111 | country.country_commission_rate_histories | YES | YES | 1 finding(s) |
| 112 | country.country_commission_rates | YES | YES | COMPLIANT |
| 113 | country.country_communication_threads | YES | YES | 1 finding(s) |
| 114 | country.country_communications | YES | YES | 1 finding(s) |
| 115 | country.country_config_versions | YES | YES | COMPLIANT |
| 116 | country.country_configs | YES | YES | 1 finding(s) |
| 117 | country.country_economics | YES | YES | 1 finding(s) |
| 118 | country.country_feature_flags | YES | YES | 1 finding(s) |
| 119 | country.country_gateway_configs | YES | YES | 1 finding(s) |
| 120 | country.country_gateway_credentials | YES | YES | COMPLIANT |
| 121 | country.country_holiday_calendars | YES | YES | 1 finding(s) |
| 122 | country.country_legal_contracts | YES | YES | 1 finding(s) |
| 123 | country.country_legals | YES | YES | 1 finding(s) |
| 124 | country.country_localizations | YES | YES | 1 finding(s) |
| 125 | country.country_logistics_zones | YES | YES | 1 finding(s) |
| 126 | country.country_map_configs | YES | YES | 1 finding(s) |
| 127 | country.country_payment_aliases | YES | YES | 1 finding(s) |
| 128 | country.country_payout_rules | YES | YES | 1 finding(s) |
| 129 | country.country_staff_assignments | YES | YES | 1 finding(s) |
| 130 | country.country_taxes | YES | YES | 1 finding(s) |
| 131 | country.data_residency_records | YES | YES | 1 finding(s) |
| 132 | country.logistics_partner_kyc_requirements | YES | YES | 1 finding(s) |
| 133 | country.logistics_partner_locations | YES | YES | 1 finding(s) |
| 134 | country.oman_delivery_zones | YES | YES | 1 finding(s) |
| 135 | country.parcel_location_trackers | YES | YES | 1 finding(s) |
| 136 | country.payment_orchestrator_syncs | YES | YES | 1 finding(s) |
| 137 | country.shift_handover_logs | YES | YES | 1 finding(s) |
| 138 | country.shop_warehouse_locations | YES | YES | 1 finding(s) |
| 139 | country.supplier_kyc_requirements | YES | YES | 1 finding(s) |
| 140 | country.supplier_onboarding_syncs | YES | YES | 1 finding(s) |
| 141 | customers.cross_country_customer_sessions | YES | YES | 2 finding(s) |
| 142 | customers.referral_point_events | YES | YES | 1 finding(s) |
| 143 | customers.referrals | YES | YES | 1 finding(s) |
| 144 | finance.account_balances | YES | YES | COMPLIANT |
| 145 | finance.account_groups | YES | YES | 1 finding(s) |
| 146 | finance.accounts | YES | YES | 2 finding(s) |
| 147 | finance.accruals | YES | YES | 1 finding(s) |
| 148 | finance.ap_bills | YES | YES | 1 finding(s) |
| 149 | finance.ap_ledger_entries | YES | YES | 1 finding(s) |
| 150 | finance.ar_invoices | YES | YES | 1 finding(s) |
| 151 | finance.ar_ledger_entries | YES | YES | 1 finding(s) |
| 152 | finance.automation_logs | YES | YES | 1 finding(s) |
| 153 | finance.automation_rules | YES | YES | 1 finding(s) |
| 154 | finance.bank_accounts | YES | YES | 1 finding(s) |
| 155 | finance.bank_mapping_rules | YES | YES | 1 finding(s) |
| 156 | finance.bank_reconciliations | YES | YES | COMPLIANT |
| 157 | finance.bank_statement_imports | YES | YES | 1 finding(s) |
| 158 | finance.bank_statement_lines | YES | YES | 1 finding(s) |
| 159 | finance.bank_transactions | YES | YES | 1 finding(s) |
| 160 | finance.budgets | YES | YES | 1 finding(s) |
| 161 | finance.cash_accounts | YES | YES | 1 finding(s) |
| 162 | finance.cash_flow_forecasts | YES | YES | 1 finding(s) |
| 163 | finance.cash_position_snapshots | YES | YES | 1 finding(s) |
| 164 | finance.cash_transactions | YES | YES | 1 finding(s) |
| 165 | finance.commission_agreements | YES | YES | 1 finding(s) |
| 166 | finance.commission_category_rates | YES | YES | 1 finding(s) |
| 167 | finance.commission_ledger_entries | YES | YES | 1 finding(s) |
| 168 | finance.cost_centers | YES | YES | 1 finding(s) |
| 169 | finance.customers | YES | YES | 1 finding(s) |
| 170 | finance.finance_audit_logs | YES | YES | 1 finding(s) |
| 171 | finance.finance_automation_logs | YES | YES | 1 finding(s) |
| 172 | finance.financial_reports | YES | YES | COMPLIANT |
| 173 | finance.fiscal_periods | YES | YES | 1 finding(s) |
| 174 | finance.fixed_assets | YES | YES | 1 finding(s) |
| 175 | finance.gateway_settlement_schedules | YES | YES | 1 finding(s) |
| 176 | finance.invoice_items | YES | YES | 1 finding(s) |
| 177 | finance.invoices | YES | YES | 1 finding(s) |
| 178 | finance.journal_entries | YES | YES | 1 finding(s) |
| 179 | finance.journal_entry_lines | YES | YES | 1 finding(s) |
| 180 | finance.logistics_partner_payouts | YES | YES | COMPLIANT |
| 181 | finance.payment_gateway_connections | YES | YES | COMPLIANT |
| 182 | finance.payment_reconciliation_runs | YES | YES | COMPLIANT |
| 183 | finance.payments | YES | YES | COMPLIANT |
| 184 | finance.payout_batch_items | YES | YES | COMPLIANT |
| 185 | finance.payout_batches | YES | YES | 1 finding(s) |
| 186 | finance.payout_rule_categories | YES | YES | 1 finding(s) |
| 187 | finance.payout_rule_products | YES | YES | 1 finding(s) |
| 188 | finance.payout_rules | YES | YES | 1 finding(s) |
| 189 | finance.payouts | YES | YES | COMPLIANT |
| 190 | finance.pending_journal_entries | YES | YES | 1 finding(s) |
| 191 | finance.product_commission_overrides | YES | YES | 1 finding(s) |
| 192 | finance.recurring_templates | YES | YES | 1 finding(s) |
| 193 | finance.refund_ledgers | YES | YES | 1 finding(s) |
| 194 | finance.scanned_expenses | YES | YES | 1 finding(s) |
| 195 | finance.supplier_settlements | YES | YES | 1 finding(s) |
| 196 | finance.tax_rules | YES | YES | 1 finding(s) |
| 197 | finance.transaction_ledgers | YES | YES | 1 finding(s) |
| 198 | finance.treasury_accounts | YES | YES | 1 finding(s) |
| 199 | finance.treasury_transactions | YES | YES | COMPLIANT |
| 200 | finance.vat_remittances | YES | YES | 1 finding(s) |
| 201 | finance.vendors | YES | YES | 1 finding(s) |
| 202 | governance.admin_activity_logs | YES | YES | COMPLIANT |
| 203 | governance.admin_analytics_snapshots | YES | YES | 2 finding(s) |
| 204 | governance.admin_change_audit_logs | YES | YES | COMPLIANT |
| 205 | governance.api_keys | YES | YES | COMPLIANT |
| 206 | governance.badge_billing_records | YES | YES | COMPLIANT |
| 207 | governance.badge_tiers | YES | YES | COMPLIANT |
| 208 | governance.badge_transactions | YES | YES | COMPLIANT |
| 209 | governance.chatbot_query_events | YES | YES | COMPLIANT |
| 210 | governance.commission_badge_tiers | YES | YES | COMPLIANT |
| 211 | governance.commission_global_configs | YES | YES | COMPLIANT |
| 212 | governance.email_provider_configs | YES | YES | COMPLIANT |
| 213 | governance.employee_expenses | YES | YES | COMPLIANT |
| 214 | governance.finance_bank_accounts | YES | YES | COMPLIANT |
| 215 | governance.legal_contract_templates | YES | YES | COMPLIANT |
| 216 | governance.logistics_cod_remittance_receipts | YES | YES | COMPLIANT |
| 217 | governance.logistics_partner_documents | YES | YES | COMPLIANT |
| 218 | governance.logistics_settlements | YES | YES | COMPLIANT |
| 219 | governance.normalized_webhook_events | YES | YES | COMPLIANT |
| 220 | governance.payment_provider_configs | YES | YES | COMPLIANT |
| 221 | governance.processed_webhook_events | YES | YES | COMPLIANT |
| 222 | governance.product_verifications | YES | YES | COMPLIANT |
| 223 | governance.promotion_order_tiers | YES | YES | COMPLIANT |
| 224 | governance.push_notification_tokens | YES | YES | COMPLIANT |
| 225 | governance.retention_job_runs | YES | YES | COMPLIANT |
| 226 | governance.role_permission_settings | YES | YES | COMPLIANT |
| 227 | governance.shipment_confirmations | YES | YES | COMPLIANT |
| 228 | governance.shipping_carriers | YES | YES | COMPLIANT |
| 229 | governance.shipping_zones | YES | YES | COMPLIANT |
| 230 | governance.supplier_country_commissions | YES | YES | COMPLIANT |
| 231 | governance.system_alerts | YES | YES | COMPLIANT |
| 232 | governance.system_health_events | YES | YES | COMPLIANT |
| 233 | governance.system_settings | YES | YES | COMPLIANT |
| 234 | governance.ticket_replies | YES | YES | COMPLIANT |
| 235 | governance.user_browsing_histories | YES | YES | COMPLIANT |
| 236 | hr.alumni_networks | YES | YES | COMPLIANT |
| 237 | hr.coi_reports | YES | YES | COMPLIANT |
| 238 | hr.disciplinary_cases | YES | YES | COMPLIANT |
| 239 | hr.dynamic_qr_sessions | YES | YES | COMPLIANT |
| 240 | hr.employee_activity_logs | YES | YES | COMPLIANT |
| 241 | hr.employee_addresses | YES | YES | COMPLIANT |
| 242 | hr.employee_assets | YES | YES | COMPLIANT |
| 243 | hr.employee_attendances | YES | YES | COMPLIANT |
| 244 | hr.employee_biometrics | YES | YES | 2 finding(s) |
| 245 | hr.employee_certifications | YES | YES | COMPLIANT |
| 246 | hr.employee_dependents | YES | YES | COMPLIANT |
| 247 | hr.employee_documents | YES | YES | COMPLIANT |
| 248 | hr.employee_leave_ledgers | YES | YES | COMPLIANT |
| 249 | hr.employee_leave_requests | YES | YES | COMPLIANT |
| 250 | hr.employee_relations | YES | YES | COMPLIANT |
| 251 | hr.employee_risk_scores | YES | YES | COMPLIANT |
| 252 | hr.employee_roles | YES | YES | COMPLIANT |
| 253 | hr.employee_shift_rosters | YES | YES | COMPLIANT |
| 254 | hr.employee_travel_requests | YES | YES | COMPLIANT |
| 255 | hr.employee_work_logs | YES | YES | COMPLIANT |
| 256 | hr.employees | YES | YES | COMPLIANT |
| 257 | hr.geo_fence_logs | YES | YES | 2 finding(s) |
| 258 | hr.offboarding_cases | YES | YES | COMPLIANT |
| 259 | hr.offices | YES | YES | COMPLIANT |
| 260 | hr.onboarding_pipelines | NO | YES | 1 finding(s) |
| 261 | hr.onboarding_steps | NO | YES | 1 finding(s) |
| 262 | hr.org_units | YES | YES | 2 finding(s) |
| 263 | hr.physical_id_cards | YES | YES | COMPLIANT |
| 264 | hr.shift_handover_sessions | YES | YES | COMPLIANT |
| 265 | hr.shift_handover_tasks | YES | YES | COMPLIANT |
| 266 | hr.training_modules | YES | YES | COMPLIANT |
| 267 | logistics.city_distance_matrices | YES | YES | 1 finding(s) |
| 268 | logistics.customs_entries | YES | YES | COMPLIANT |
| 269 | logistics.goods_receipt_lines | YES | YES | COMPLIANT |
| 270 | logistics.goods_receipt_notes | YES | YES | COMPLIANT |
| 271 | logistics.import_cost_templates | YES | YES | COMPLIANT |
| 272 | logistics.import_shipment_lines | YES | YES | COMPLIANT |
| 273 | logistics.import_shipments | YES | YES | COMPLIANT |
| 274 | logistics.landed_cost_allocations | YES | YES | COMPLIANT |
| 275 | logistics.logistics_category_pricing_rules | YES | YES | 1 finding(s) |
| 276 | logistics.logistics_partner_profiles | YES | YES | 1 finding(s) |
| 277 | logistics.logistics_partner_service_areas | YES | YES | 1 finding(s) |
| 278 | logistics.logistics_partners | YES | YES | 1 finding(s) |
| 279 | logistics.logistics_pricing_profiles | YES | YES | 1 finding(s) |
| 280 | logistics.logistics_vehicle_rules | YES | YES | 1 finding(s) |
| 281 | logistics.partner_performance_projections | NO | YES | 1 finding(s) |
| 282 | logistics.purchase_order_lines | YES | YES | COMPLIANT |
| 283 | logistics.purchase_orders | YES | YES | COMPLIANT |
| 284 | logistics.sales_order_lines | YES | YES | COMPLIANT |
| 285 | logistics.sales_orders | YES | YES | COMPLIANT |
| 286 | logistics.shipment_events | YES | YES | 1 finding(s) |
| 287 | logistics.shipment_tracking_projections | NO | YES | 1 finding(s) |
| 288 | logistics.shipments | YES | YES | 1 finding(s) |
| 289 | logistics.shipping_rules | YES | YES | 1 finding(s) |
| 290 | logistics.stock_movements | YES | YES | COMPLIANT |
| 291 | logistics.warehouses | YES | YES | COMPLIANT |
| 292 | orders.order_items | YES | YES | COMPLIANT |
| 293 | orders.order_logistics_allocations | YES | YES | COMPLIANT |
| 294 | orders.order_notifications | YES | YES | 1 finding(s) |
| 295 | orders.orders | YES | YES | COMPLIANT |
| 296 | orders.return_requests | YES | YES | 2 finding(s) |
| 297 | payments.payment_attempts | YES | YES | COMPLIANT |
| 298 | payments.payment_intents | YES | YES | 2 finding(s) |
| 299 | payments.payment_methods | YES | YES | 2 finding(s) |
| 300 | payments.refunds | YES | YES | COMPLIANT |
| 301 | promotions.banners | YES | YES | COMPLIANT |
| 302 | promotions.bogo_promotions | YES | YES | COMPLIANT |
| 303 | promotions.coupon_usages | YES | YES | 1 finding(s) |
| 304 | promotions.coupons | YES | YES | COMPLIANT |
| 305 | promotions.flash_sales | YES | YES | COMPLIANT |
| 306 | promotions.points_transactions | YES | YES | COMPLIANT |
| 307 | promotions.promotion_engine_configs | YES | YES | 1 finding(s) |
| 308 | promotions.promotion_ledger_entries | YES | YES | COMPLIANT |
| 309 | promotions.user_points | YES | YES | COMPLIANT |
| 310 | security.alert_escalation_rules | YES | YES | COMPLIANT |
| 311 | security.credit_card_bins | YES | YES | 1 finding(s) |
| 312 | security.device_fingerprints | YES | YES | 2 finding(s) |
| 313 | security.dlp_violations | YES | YES | 1 finding(s) |
| 314 | security.document_verifications | YES | YES | COMPLIANT |
| 315 | security.fraud_alerts | YES | YES | 2 finding(s) |
| 316 | security.fraud_blacklists | YES | YES | 2 finding(s) |
| 317 | security.fraud_case_assignments | YES | YES | 1 finding(s) |
| 318 | security.fraud_cases | YES | YES | 1 finding(s) |
| 319 | security.fraud_events | YES | YES | 2 finding(s) |
| 320 | security.fraud_rules | YES | YES | 1 finding(s) |
| 321 | security.fraud_scoring_logs | YES | YES | 2 finding(s) |
| 322 | security.fraud_velocity_counters | YES | YES | 1 finding(s) |
| 323 | security.ip_account_linkages | YES | YES | 2 finding(s) |
| 324 | security.ip_reputations | YES | YES | 1 finding(s) |
| 325 | security.kyc_verifications | YES | YES | COMPLIANT |
| 326 | security.logistics_fraud_indicators | YES | YES | 2 finding(s) |
| 327 | security.manual_review_queues | YES | YES | 1 finding(s) |
| 328 | security.meeting_action_items | YES | YES | 2 finding(s) |
| 329 | security.meeting_transcripts | YES | YES | 1 finding(s) |
| 330 | security.permission_audit_log | NO | YES | 1 finding(s) |
| 331 | security.permission_categories | NO | YES | 1 finding(s) |
| 332 | security.permissions | NO | YES | 1 finding(s) |
| 333 | security.return_abuse_patterns | YES | YES | 2 finding(s) |
| 334 | security.role_permission_assignments | NO | YES | 1 finding(s) |
| 335 | security.user_permission_overrides | NO | YES | 1 finding(s) |
| 336 | suppliers.supplier_badge_billing_histories | YES | YES | 1 finding(s) |
| 337 | suppliers.supplier_badge_catalogs | YES | YES | 1 finding(s) |
| 338 | suppliers.supplier_badges | YES | YES | 1 finding(s) |
| 339 | suppliers.supplier_disputes | YES | YES | 2 finding(s) |
| 340 | suppliers.supplier_documents | YES | YES | 2 finding(s) |
| 341 | suppliers.supplier_fraud_indicators | YES | YES | COMPLIANT |
| 342 | suppliers.supplier_notification_preferences | YES | YES | 2 finding(s) |
| 343 | suppliers.supplier_profiles | YES | YES | 1 finding(s) |

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| TF-001 | db | COMPILED |  | backend/alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py | alembic current shows 5 heads: 20260930_0002, 20260930_0003, | Linear migration history with single head | Multiple alembic heads (5 heads) + load failure | Merge 5 heads into 1 | M | P0 | 5 | triangulated | L1 | VERIFIED |  | `alembic heads` returns single head | test_migration_linear | Revert failed migration | CI/CD, deployment | none |  | yes |
| TF-002 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-003 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-004 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-005 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-006 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-007 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-008 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-009 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-010 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-011 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-012 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-013 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-014 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-015 | db | COMPILED |  | : | Table exists in DB but has no matching model in domains/*/mo | Model exists in domains/*/models/ mapping to this table | Table in DB has no ORM model | Create model class in appropriate domain | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-016 | db | COMPILED |  | : | Model in backend\domains\hr\models\employee_models.py:531 ha | __table_args__ = {"schema": "<domain>"} | Model missing schema declaration | Add schema to __table_args__ | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-017 | db | COMPILED |  | : | Model in backend\domains\hr\models\employee_models.py:560 ha | __table_args__ = {"schema": "<domain>"} | Model missing schema declaration | Add schema to __table_args__ | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-018 | db | INVALID |  | backend\domains\media\models\media_asset.py:9 | Model exists but table not found in live database | Table exists in live database | Model declared but migration not applied | Apply pending Alembic migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-019 | db | COMPILED |  | backend\domains\media\models\media_asset.py:24 | Model exists but table not found in live database | Table exists in live database | Model declared but migration not applied | Apply pending Alembic migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-020 | db | INVALID |  | backend\domains\accounts\models\onboarding.py:15 | Column 'status' exists in DB but not in model (type: charact | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-021 | db | INVALID |  | backend\domains\accounts\models\onboarding.py:15 | Column 'pipeline_status' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-022 | db | INVALID |  | backend\domains\accounts\models\onboarding.py:38 | Column 'status' exists in DB but not in model (type: charact | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-023 | db | INVALID |  | backend\domains\accounts\models\onboarding.py:38 | Column 'step_status' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-024 | db | COMPILED |  | backend\domains\accounts\models\user.py:25 | Column 'referral_code' exists in DB but not in model (type: | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-025 | db | COMPILED |  | backend\domains\accounts\models\user.py:25 | Column 'referral_points' exists in DB but not in model (type | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-026 | db | COMPILED |  | backend\domains\accounts\models\user.py:25 | Column 'phone' exists in DB but not in model (type: characte | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-027 | db | COMPILED |  | backend\domains\catalog\models\upload_job.py:62 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-028 | db | INVALID |  | backend\domains\catalog\models\products.py:135 | Column 'created_by_id' exists in DB but not in model (type: | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-029 | db | INVALID |  | backend\domains\catalog\models\products.py:135 | Column 'updated_by_id' exists in DB but not in model (type: | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-030 | db | INVALID |  | backend\domains\catalog\models\products.py:135 | Column 'deleted_by_id' exists in DB but not in model (type: | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-031 | db | COMPILED |  | backend\domains\comms\models\communication.py:60 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-032 | db | COMPILED |  | backend\domains\comms\models\communication.py:60 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-033 | db | COMPILED |  | backend\domains\comms\models\marketing.py:119 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-034 | db | COMPILED |  | backend\domains\comms\models\marketing.py:119 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-035 | db | COMPILED |  | backend\domains\comms\models\communication.py:359 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-036 | db | COMPILED |  | backend\domains\comms\models\communication.py:341 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-037 | db | COMPILED |  | backend\domains\comms\models\communication.py:247 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-038 | db | COMPILED |  | backend\domains\comms\models\communication.py:247 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-039 | db | COMPILED |  | backend\domains\comms\models\chat.py:155 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-040 | db | COMPILED |  | backend\domains\comms\models\chat.py:155 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-041 | db | COMPILED |  | backend\domains\comms\models\chat.py:75 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-042 | db | COMPILED |  | backend\domains\comms\models\marketing.py:99 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-043 | db | COMPILED |  | backend\domains\comms\models\marketing.py:99 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-044 | db | COMPILED |  | backend\domains\comms\models\marketing.py:39 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-045 | db | INVALID |  | backend\domains\comms\models\marketing.py:39 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-046 | db | COMPILED |  | backend\domains\comms\models\marketing.py:144 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-047 | db | COMPILED |  | backend\domains\comms\models\marketing.py:144 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-048 | db | COMPILED |  | backend\domains\comms\models\communication.py:410 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-049 | db | COMPILED |  | backend\domains\comms\models\communication.py:410 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-050 | db | COMPILED |  | backend\domains\comms\models\marketing.py:185 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-051 | db | COMPILED |  | backend\domains\comms\models\marketing.py:163 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-052 | db | COMPILED |  | backend\domains\comms\models\marketing.py:163 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-053 | db | COMPILED |  | backend\domains\comms\models\marketing.py:65 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-054 | db | COMPILED |  | backend\domains\comms\models\marketing.py:65 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-055 | db | COMPILED |  | backend\domains\comms\models\communication.py:208 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-056 | db | COMPILED |  | backend\domains\comms\models\chat.py:124 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-057 | db | COMPILED |  | backend\domains\comms\models\chat.py:124 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-058 | db | COMPILED |  | backend\domains\comms\models\chat.py:124 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-059 | db | COMPILED |  | backend\domains\comms\models\chat.py:19 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-060 | db | COMPILED |  | backend\domains\comms\models\chat.py:19 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-061 | db | COMPILED |  | backend\domains\comms\models\chat.py:104 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-062 | db | COMPILED |  | backend\domains\comms\models\chat.py:104 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-063 | db | COMPILED |  | backend\domains\comms\models\chat.py:104 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-064 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:115 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-065 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:115 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-066 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:115 | Column 'is_deleted' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-067 | db | COMPILED |  | backend\domains\comms\models\communication.py:227 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-068 | db | COMPILED |  | backend\domains\comms\models\communication.py:79 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-069 | db | INVALID |  | backend\domains\comms\models\communication.py:79 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-070 | db | COMPILED |  | backend\domains\comms\models\chat.py:91 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-071 | db | COMPILED |  | backend\domains\comms\models\chat.py:91 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-072 | db | COMPILED |  | backend\domains\comms\models\chat.py:91 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-073 | db | COMPILED |  | backend\domains\comms\models\chat.py:188 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-074 | db | COMPILED |  | backend\domains\comms\models\chat.py:188 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-075 | db | COMPILED |  | backend\domains\comms\models\chat.py:188 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-076 | db | COMPILED |  | backend\domains\comms\models\chat.py:171 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-077 | db | COMPILED |  | backend\domains\comms\models\communication.py:96 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-078 | db | COMPILED |  | backend\domains\comms\models\communication.py:96 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-079 | db | COMPILED |  | backend\domains\comms\models\incident.py:45 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-080 | db | COMPILED |  | backend\domains\comms\models\incident.py:31 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-081 | db | COMPILED |  | backend\domains\comms\models\incident.py:11 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-082 | db | COMPILED |  | backend\domains\comms\models\incident.py:11 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-083 | db | COMPILED |  | backend\domains\comms\models\communication.py:299 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-084 | db | COMPILED |  | backend\domains\comms\models\communication.py:384 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-085 | db | INVALID |  | backend\domains\comms\models\communication.py:384 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-086 | db | COMPILED |  | backend\domains\comms\models\communication.py:319 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-087 | db | COMPILED |  | backend\domains\comms\models\communication.py:319 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-088 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:99 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-089 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:99 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-090 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:99 | Column 'is_deleted' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-091 | db | COMPILED |  | backend\domains\comms\models\communication.py:429 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-092 | db | INVALID |  | backend\domains\comms\models\communication.py:429 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-093 | db | COMPILED |  | backend\domains\comms\models\fraud.py:12 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-094 | db | COMPILED |  | backend\domains\comms\models\message.py:23 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-095 | db | COMPILED |  | backend\domains\comms\models\news.py:18 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-096 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:83 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-097 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:83 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-098 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:83 | Column 'is_deleted' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-099 | db | COMPILED |  | backend\domains\comms\models\marketing.py:84 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-100 | db | COMPILED |  | backend\domains\comms\models\marketing.py:84 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-101 | db | COMPILED |  | backend\domains\comms\models\communication.py:13 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-102 | db | INVALID |  | backend\domains\comms\models\communication.py:13 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-103 | db | COMPILED |  | backend\domains\comms\models\communication.py:182 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-104 | db | COMPILED |  | backend\domains\comms\models\communication.py:112 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-105 | db | COMPILED |  | backend\domains\comms\models\communication.py:158 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-106 | db | COMPILED |  | backend\domains\comms\models\communication.py:158 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-107 | db | COMPILED |  | backend\domains\comms\models\communication.py:133 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-108 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:53 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-109 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:53 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-110 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:53 | Column 'is_deleted' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-111 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:36 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-112 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:68 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-113 | db | RESOLVED |  | backend\domains\comms\models\communication_schema_models.py:68 | Column 'updated_at' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-114 | db | COMPILED |  | backend\domains\comms\models\communication_schema_models.py:68 | Column 'is_deleted' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-115 | db | COMPILED |  | backend\domains\comms\models\communication.py:40 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-116 | db | INVALID |  | backend\domains\comms\models\communication.py:40 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-117 | db | COMPILED |  | backend\domains\comms\models\chat.py:60 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-118 | db | COMPILED |  | backend\domains\comms\models\chat.py:60 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-119 | db | COMPILED |  | backend\domains\comms\models\chat.py:60 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-120 | db | COMPILED |  | backend\domains\comms\models\chat.py:139 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-121 | db | COMPILED |  | backend\domains\comms\models\chat.py:139 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-122 | db | COMPILED |  | backend\domains\comms\models\chat.py:139 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-123 | db | COMPILED |  | backend\domains\comms\models\chat.py:33 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-124 | db | COMPILED |  | backend\domains\comms\models\incident.py:64 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-125 | db | COMPILED |  | backend\domains\comms\models\incident.py:64 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-126 | db | COMPILED |  | backend\domains\country\models\country_basics.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-127 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:234 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-128 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:261 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-129 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:356 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-130 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:335 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-131 | db | COMPILED |  | backend\domains\country\models\countries.py:129 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-132 | db | COMPILED |  | backend\domains\country\models\countries.py:15 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-133 | db | COMPILED |  | backend\domains\country\models\country_economics.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-134 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:14 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-135 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:310 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-136 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:290 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-137 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:215 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-138 | db | COMPILED |  | backend\domains\country\models\country_legal.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-139 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:176 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-140 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:380 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-141 | db | COMPILED |  | backend\domains\country\models\country_control.py:103 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-142 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:196 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-143 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:402 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-144 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:36 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-145 | db | COMPILED |  | backend\domains\country\models\country_tax.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-146 | db | COMPILED |  | backend\domains\country\models\country_control.py:82 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-147 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:128 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-148 | db | COMPILED |  | backend\domains\country\models\country_control.py:142 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-149 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:59 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-150 | db | COMPILED |  | backend\domains\country\models\country_control.py:163 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-151 | db | COMPILED |  | backend\domains\country\models\country_control.py:35 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-152 | db | COMPILED |  | backend\domains\country\models\country_control.py:13 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-153 | db | COMPILED |  | backend\domains\country\models\country_control.py:122 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-154 | db | COMPILED |  | backend\domains\country\models\country_enhancements.py:108 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-155 | db | COMPILED |  | backend\domains\country\models\country_control.py:59 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-156 | db | COMPILED |  | backend\domains\customers\models\cross_country_session.py:22 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-157 | db | COMPILED |  | backend\domains\customers\models\cross_country_session.py:22 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-158 | db | COMPILED |  | backend\domains\customers\models\customer_schema_models.py:44 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-159 | db | COMPILED |  | backend\domains\customers\models\customer_schema_models.py:22 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-160 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:186 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-161 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:162 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-162 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:162 | Column 'account_type' exists in DB but not in model (type: c | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-163 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:806 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-164 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:983 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-165 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:262 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-166 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1011 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-167 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:232 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-168 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:893 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-169 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:865 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-170 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1039 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-171 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:700 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-172 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:724 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-173 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:750 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-174 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:407 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-175 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1063 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-176 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:469 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-177 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:561 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-178 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:582 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-179 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:490 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-180 | db | COMPILED |  | backend\domains\finance\models\commission.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-181 | db | COMPILED |  | backend\domains\finance\models\commission.py:94 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-182 | db | COMPILED |  | backend\domains\finance\models\commission.py:54 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-183 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:964 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-184 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:941 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-185 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1132 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-186 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1154 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-187 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:11 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-188 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:777 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-189 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:601 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-190 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:350 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-191 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:314 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-192 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:109 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-193 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:137 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-194 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:650 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-195 | db | COMPILED |  | backend\domains\finance\models\tax_rules.py:65 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-196 | db | COMPILED |  | backend\domains\finance\models\tax_rules.py:86 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-197 | db | COMPILED |  | backend\domains\finance\models\tax_rules.py:23 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-198 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:621 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-199 | db | COMPILED |  | backend\domains\finance\models\commission.py:34 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-200 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:1109 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-201 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:374 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-202 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:832 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-203 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:78 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-204 | db | COMPILED |  | backend\domains\finance\models\tax_rules.py:45 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-205 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:36 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-206 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:513 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-207 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:441 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-208 | db | COMPILED |  | backend\domains\finance\models\general_ledger.py:919 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-209 | db | COMPILED |  | backend\domains\governance\models\admin.py:37 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-210 | db | COMPILED |  | backend\domains\governance\models\admin.py:37 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-211 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:80 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-212 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:80 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-213 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:96 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-214 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:96 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-215 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:128 | Column 'path' exists in DB but not in model (type: character | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-216 | db | COMPILED |  | backend\domains\hr\models\employee_models.py:128 | Column 'depth' exists in DB but not in model (type: integer) | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-217 | db | COMPILED |  | backend\domains\logistics\models\logistics_schema_models.py:26 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-218 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:194 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-219 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:66 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-220 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:91 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-221 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:13 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-222 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:129 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-223 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:164 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-224 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:268 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-225 | db | COMPILED |  | backend\domains\logistics\models\logistics_entities.py:222 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-226 | db | COMPILED |  | backend\domains\logistics\models\shipping_rules.py:24 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-227 | db | COMPILED |  | backend\domains\orders\models\order_entities.py:178 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-228 | db | COMPILED |  | backend\domains\orders\models\order_entities.py:142 | Column 'requested_by_id' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-229 | db | COMPILED |  | backend\domains\orders\models\order_entities.py:142 | Column 'approved_by_id' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-230 | db | INVALID |  | backend\domains\payments\models\payment_models.py:134 | Column 'metadata' exists in DB but not in model (type: json) | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-231 | db | INVALID |  | backend\domains\payments\models\payment_models.py:134 | Column 'metadata_json' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-232 | db | INVALID |  | backend\domains\payments\models\payment_models.py:41 | Column 'metadata' exists in DB but not in model (type: json) | All DB columns represented in model | DB column not in model | Add column to model or remove from DB | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-233 | db | INVALID |  | backend\domains\payments\models\payment_models.py:41 | Column 'metadata_json' in model but not in live DB | All model columns exist in live DB | Schema drift: model column not in DB | Apply migration to add missing column | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-234 | db | COMPILED |  | backend\domains\promotions\models\coupon_usage.py:12 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-235 | db | COMPILED |  | backend\domains\promotions\models\promotion_config.py:13 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-236 | db | COMPILED |  | backend\domains\security\models\fraud.py:149 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-237 | db | COMPILED |  | backend\domains\security\models\fraud.py:128 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-238 | db | COMPILED |  | backend\domains\security\models\fraud.py:128 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-239 | db | COMPILED |  | backend\domains\security\models\fraud.py:314 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-240 | db | COMPILED |  | backend\domains\security\models\fraud.py:191 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-241 | db | COMPILED |  | backend\domains\security\models\fraud.py:191 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-242 | db | COMPILED |  | backend\domains\security\models\fraud.py:47 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-243 | db | COMPILED |  | backend\domains\security\models\fraud.py:47 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-244 | db | COMPILED |  | backend\domains\security\models\fraud.py:295 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-245 | db | COMPILED |  | backend\domains\security\models\fraud.py:265 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-246 | db | COMPILED |  | backend\domains\security\models\fraud.py:16 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-247 | db | COMPILED |  | backend\domains\security\models\fraud.py:16 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-248 | db | COMPILED |  | backend\domains\security\models\fraud.py:66 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-249 | db | COMPILED |  | backend\domains\security\models\fraud.py:241 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-250 | db | COMPILED |  | backend\domains\security\models\fraud.py:241 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-251 | db | COMPILED |  | backend\domains\security\models\fraud.py:225 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-252 | db | COMPILED |  | backend\domains\security\models\fraud.py:209 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-253 | db | COMPILED |  | backend\domains\security\models\fraud.py:209 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-254 | db | COMPILED |  | backend\domains\security\models\fraud.py:108 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-255 | db | COMPILED |  | backend\domains\security\models\fraud.py:178 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-256 | db | COMPILED |  | backend\domains\security\models\fraud.py:178 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-257 | db | COMPILED |  | backend\domains\security\models\fraud.py:85 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-258 | db | COMPILED |  | backend\domains\security\models\fraud.py:357 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-259 | db | COMPILED |  | backend\domains\security\models\fraud.py:357 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-260 | db | COMPILED |  | backend\domains\security\models\fraud.py:340 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-261 | db | COMPILED |  | backend\domains\security\models\fraud.py:163 | Model missing created_at column | created_at with server_default=func.now() | Audit column missing | Add created_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-262 | db | COMPILED |  | backend\domains\security\models\fraud.py:163 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-263 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:183 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-264 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:111 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-265 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:142 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-266 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:263 | Model missing updated_at column | updated_at with server_default=func.now() | Audit column missing | Add updated_at column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-267 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:263 | User-facing table missing is_deleted column (Law 54) | is_deleted boolean default false | Soft delete column missing | Add is_deleted column | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-268 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:57 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-269 | db | INVALID |  | backend\domains\suppliers\models\suppliers.py:57 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-270 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:86 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |
| TF-271 | db | INVALID |  | backend\domains\suppliers\models\suppliers.py:86 | User-facing table missing country_code column (Law 5, 20) | country_code String(2) column on every user-facing table | Table missing country_code for RLS scoping | Add country_code column via migration | M | P1 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | yes |
| TF-272 | db | COMPILED |  | backend\domains\suppliers\models\suppliers.py:29 | created_at missing server_default=func.now() (Law 21) | server_default=func.now() for timestamps | Using Python-side default instead of DB-side | Change to server_default=func.now() | M | P2 | 5 | triangulated | L1 | VERIFIED |  | Verify column exists | Apply migration | Revert migration | Domain data | none |  | no |

## Over all

### Problem(s)
1. Multiple Alembic heads (5 heads) violate Law 49 (linear migration history). `alembic current` shows: 20260930_0002, 20260930_0003, 20260930_0006, 20260930_0007, 20260930_0008. `alembic heads` fails with ModuleNotFoundError in 2026_08_06_0001_add_analytics_audit_columns.py.
2. 14 tables in DB lack ORM models, creating schema drift and untraceable data: comms.notification_channels, comms.notification_rules, comms.notification_template_translations, comms.notification_templates, comms.push_notification_tokens, hr.onboarding_pipelines, hr.onboarding_steps, logistics.partner_performance_projections, logistics.shipment_tracking_projections, security.permission_audit_log, security.permission_categories, security.permissions, security.role_permission_assignments, security.user_permission_overrides.
3. 2 models (media.media_assets, media.upload_sessions) have no corresponding DB tables - migration not applied.
4. 42 user-facing tables missing country_code break RLS scoping (Law 5, 20). Primarily in comms domain (37 tables), plus customers.cross_country_customer_sessions, orders.order_notifications, suppliers.supplier_documents, suppliers.supplier_notification_preferences.
5. 150 tables use Python-side default=_utcnow instead of server_default=func.now() (Law 21).
6. 2 models (payroll_records, employee_trainings) lack __table_args__ schema declaration - tables would land in public schema if created.
7. 13 orphan columns in DB not represented in models (e.g., accounts.users.referral_code, accounts.users.phone).
8. 17 model columns missing from live DB (e.g., accounts.onboarding_pipelines.pipeline_status, payments.payment_intents.metadata_json).
9. Float type used for non-monetary columns (latitude, longitude, scores) - acceptable per Law 19.

### Solution(s)
1. Merge 5 Alembic heads into single linear head. Fix 2026_08_06_0001_add_analytics_audit_columns.py import of migration_helpers.
2. Create ORM models for 14 unmapped tables in appropriate domains.
3. Apply media schema migration to create media.media_assets and media.upload_sessions tables.
4. Add country_code to 42 user-facing tables via migration.
5. Convert Python-side defaults to server_default=func.now() where applicable per Law 21.
6. Add schema declarations to payroll_records and employee_trainings models.
7. Sync orphan columns with models or remove from DB.
8. Apply pending migrations for 17 missing columns.

### Suggestion(s)
1. Add schema-drift CI check to prevent future model/DB divergence.
2. Add country_code presence test to architecture test suite.
3. Add timestamp server_default lint rule.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Merge 5 Alembic heads into single linear head | Linear migration history per Law 49 | yes | L | 5 |
| P1 | Add country_code to 42 user-facing tables | RLS scoping per Law 5 | yes | M | 5 |
| P1 | Create models for 14 unmapped tables | Schema traceability | yes | M | 5 |
| P1 | Apply media schema migration | media.media_assets, media.upload_sessions | yes | S | 5 |
| P2 | Convert Python defaults to server_default=func.now() | Timestamp consistency per Law 21 | no | M | 5 |
| P2 | Add schema to 2 models (payroll_records, employee_trainings) | Schema discipline per Law 6 | no | S | 5 |
| P2 | Sync 13 orphan columns with models | Model/DB alignment | no | S | 5 |
| P2 | Apply 17 pending column migrations | Schema completeness | no | S | 5 |