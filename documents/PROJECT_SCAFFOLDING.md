# 📂 ZOZI Project Scaffolding Structure

**Root Directory:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`

```text
zozi/
├── Working_API/
│   ├── zozi_ai_image_service/
│   │   ├── bg_all_results/
│   │   ├── image/
│   │   │   ├── image_01.webp
│   │   │   ├── image_02.webp
│   │   │   ├── image_03.webp
│   │   │   ├── image_04.jpg
│   │   │   ├── image_05.jpg
│   │   │   ├── image_06.jpg
│   │   │   ├── image_07.jpg
│   │   │   ├── image_08.webp
│   │   │   ├── image_09.jpg
│   │   │   ├── image_10.jpg
│   │   │   ├── image_11.jpg
│   │   │   ├── image_12.jpg
│   │   │   ├── image_13.jpg
│   │   │   ├── image_14.jpeg
│   │   │   ├── image_15.jpeg
│   │   │   ├── image_16.jpeg
│   │   │   ├── image_17.jpeg
│   │   │   ├── image_18.jpeg
│   │   │   ├── image_19.webp
│   │   │   ├── image_20.jpg
│   │   │   ├── image_21.jpg
│   │   │   ├── image_22.webp
│   │   │   ├── image_23.jpg
│   │   │   ├── image_24.jpeg
│   │   │   ├── image_25.jpg
│   │   │   ├── image_26.jpg
│   │   │   ├── image_27.jpg
│   │   │   ├── image_28.webp
│   │   │   ├── image_29.webp
│   │   │   └── image_30.jpg
│   │   ├── output_bg_all/
│   │   ├── output_br_05/
│   │   ├── output_br_06/
│   │   ├── output_br_08/
│   │   ├── output_br_11/
│   │   ├── output_br_12/
│   │   ├── output_br_13/
│   │   ├── br.md
│   │   ├── br_05.py
│   │   ├── br_06.py
│   │   ├── br_08.py
│   │   ├── br_11.py
│   │   ├── br_12.py
│   │   ├── br_13.py
│   │   ├── check_BiRefNet.py
│   │   ├── combine_to_md.py
│   │   ├── combined_code.md
│   │   ├── requirements.txt
│   │   ├── run_bg_all.py
│   │   ├── run_br_benchmark.py
│   │   ├── test_birefnet.py
│   │   └── test_strategies.py
│   └── zozi_ai_upload_session/
│       ├── products_output/
│       │   └── zozi_products.csv
│       ├── unified_output/
│       │   └── bg_output/
│       │       ├── br_11/
│       │       ├── br_12/
│       │       ├── br_13/
│       │       └── processed/
│       ├── combine_to_md.py
│       ├── combined_code.md
│       ├── probe.py
│       ├── probe_vision.py
│       ├── run_log.txt
│       ├── upload_auto_01.py
│       ├── upload_auto_02.py
│       ├── upload_auto_03.py
│       ├── upload_auto_04.py
│       ├── upload_auto_05.py
│       ├── vision_cache.json
│       └── zozi_variant_config.json
├── _trash/
│   ├── codebase_v1.md
│   ├── codebase_v2.md
│   ├── codebase_v3.md
│   └── codebase_v4.md
├── alembic/
│   └── versions/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py
│   │   │   ├── 2026_07_26_20_27-837e1e29bd49_add_banner_layout_json.py
│   │   │   ├── 2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py
│   │   │   ├── 2026_07_26_22_00-e70b2cb9a90f_fix_internal_channels_fk.py
│   │   │   ├── 2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py
│   │   │   ├── 2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py
│   │   │   ├── 2026_07_28_0000_employee_hr_tables.py
│   │   │   ├── 2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py
│   │   │   ├── 2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py
│   │   │   ├── 2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py
│   │   │   ├── 2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py
│   │   │   ├── 2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py
│   │   │   ├── 2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py
│   │   │   ├── 2026_07_30_0001-20260730_0001_create_user_points_table.py
│   │   │   ├── 2026_07_30_0002-20260730_0002_create_points_transactions_table.py
│   │   │   ├── 2026_07_30_0003-20260730_0003_create_upload_jobs_table.py
│   │   │   ├── 2026_07_30_0004-20260730_0004_create_event_tables.py
│   │   │   └── 2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py
│   │   ├── _analyze_graph.py
│   │   ├── _diagnose_tree.py
│   │   ├── _graph_analysis.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── api/
│   │   └── country_communications.py
│   ├── controllers/
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   ├── bulk_ops.py
│   │   │   ├── coupons.py
│   │   │   ├── database.py
│   │   │   ├── misc.py
│   │   │   ├── orders.py
│   │   │   ├── payouts.py
│   │   │   ├── permissions.py
│   │   │   ├── products.py
│   │   │   ├── suppliers.py
│   │   │   ├── tickets.py
│   │   │   └── users.py
│   │   ├── commerce/
│   │   │   ├── __init__.py
│   │   │   └── package.py
│   │   ├── communication/
│   │   │   ├── __init__.py
│   │   │   └── package.py
│   │   ├── finance/
│   │   │   ├── __init__.py
│   │   │   └── package.py
│   │   ├── governance/
│   │   │   ├── __init__.py
│   │   │   └── package.py
│   │   ├── hr/
│   │   │   ├── __init__.py
│   │   │   └── package.py
│   │   ├── products/
│   │   │   └── __init__.py
│   │   ├── supplier/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── badge.py
│   │   │   ├── inventory.py
│   │   │   ├── orders.py
│   │   │   ├── payouts.py
│   │   │   ├── products.py
│   │   │   └── profile.py
│   │   ├── __init__.py
│   │   ├── accounting_controller.py
│   │   ├── address_controller.py
│   │   ├── admin_controller.py
│   │   ├── ai_controller.py
│   │   ├── audit_controller.py
│   │   ├── auth_controller.py
│   │   ├── banner_controller.py
│   │   ├── cart_controller.py
│   │   ├── cash_management_controller.py
│   │   ├── categories_controller.py
│   │   ├── chat_controller.py
│   │   ├── chatbot_controller.py
│   │   ├── comm_controller.py
│   │   ├── command_center.py
│   │   ├── command_center_controller.py
│   │   ├── commission_controller.py
│   │   ├── compliance_controller.py
│   │   ├── country_controller.py
│   │   ├── country_versioning_controller.py
│   │   ├── coupons_controller.py
│   │   ├── disputes_controller.py
│   │   ├── email_controller.py
│   │   ├── employee_controller.py
│   │   ├── employees_controller.py
│   │   ├── expense_controller.py
│   │   ├── export_controller.py
│   │   ├── financial_controller.py
│   │   ├── flash_sale_controller.py
│   │   ├── hr_controller.py
│   │   ├── iam_controller.py
│   │   ├── invoice_controller.py
│   │   ├── lms_controller.py
│   │   ├── logistics_controller.py
│   │   ├── logistics_partner_controller.py
│   │   ├── mobile_controller.py
│   │   ├── notifications_controller.py
│   │   ├── operational_controller.py
│   │   ├── orders_controller.py
│   │   ├── payments_controller.py
│   │   ├── product_verification_controller.py
│   │   ├── products_controller.py
│   │   ├── promotion_controller.py
│   │   ├── returns_controller.py
│   │   ├── reviews_controller.py
│   │   ├── risk_controller.py
│   │   ├── search_controller.py
│   │   ├── sub_ledger_controller.py
│   │   ├── supplier_controller.py
│   │   ├── supplier_document_controller.py
│   │   ├── video_controller.py
│   │   └── wishlist_controller.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── category_tax_profiles.py
│   │   ├── country_curated.py
│   │   ├── curated_cities.py
│   │   └── vat_rates.py
│   ├── db/
│   │   ├── migrations/
│   │   │   └── new_tables.py
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── create_tables.py
│   │   ├── database.py
│   │   ├── employee_models.py
│   │   ├── init_db.py
│   │   ├── media_models.py
│   │   ├── mixins.py
│   │   ├── models_country_enhancements.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   ├── transaction.py
│   │   └── treasury_seeder.py
│   ├── dependencies/
│   │   └── country_rls.py
│   ├── docs/
│   │   ├── connection-pooling.md
│   │   └── schema_mapping.json
│   ├── events/
│   │   ├── __init__.py
│   │   ├── event_publisher.py
│   │   └── payment_events.py
│   ├── jobs/
│   │   ├── ghost_order_detector.py
│   │   └── threat_feed_updater.py
│   ├── location_service/
│   │   ├── __init__.py
│   │   ├── geo_resolver.py
│   │   └── main.py
│   ├── log/
│   │   ├── boot_final.log
│   │   ├── research_stderr.log
│   │   ├── research_stdout.log
│   │   ├── rs_err.log
│   │   ├── rs_out.log
│   │   ├── server_stderr.log
│   │   ├── server_stderr_20260722_204238.log
│   │   ├── server_stderr_8001.log
│   │   ├── server_stdout.log
│   │   ├── uvicorn_stderr.log
│   │   └── uvicorn_stdout.log
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── api_version_middleware.py
│   │   ├── behavioral_analytics.py
│   │   ├── coi_middleware.py
│   │   ├── country_context.py
│   │   ├── csrf_middleware.py
│   │   ├── database_security.py
│   │   ├── device_binding_middleware.py
│   │   ├── impossible_travel_middleware.py
│   │   ├── ip_extraction_middleware.py
│   │   ├── logging_middleware.py
│   │   ├── orchestrator.py
│   │   ├── pci_dss_compliance.py
│   │   ├── rate_limit_middleware.py
│   │   ├── request_id_middleware.py
│   │   ├── rls_dependency.py
│   │   ├── security_headers.py
│   │   ├── siem_engine.py
│   │   ├── webhook_ip_whitelist.py
│   │   └── webhook_verification.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── ai_upload.py
│   │   ├── commission.py
│   │   ├── communication.py
│   │   ├── core.py
│   │   ├── countries.py
│   │   ├── country_control.py
│   │   ├── country_enhancements.py
│   │   ├── employee_models.py
│   │   ├── finance.py
│   │   ├── fraud.py
│   │   ├── incident.py
│   │   ├── logistics.py
│   │   ├── marketing.py
│   │   ├── media_models.py
│   │   ├── mixins.py
│   │   ├── onboarding.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   ├── permissions.py
│   │   ├── products.py
│   │   ├── suppliers.py
│   │   └── user.py
│   ├── monitoring/
│   │   ├── docker-compose.monitoring.yml
│   │   └── prometheus.yml
│   ├── provider_test/
│   │   └── visual_regression/
│   │       ├── metrics.json
│   │       └── report_index.html
│   ├── providers/
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── text.py
│   │   │   └── vision.py
│   │   ├── legacy/
│   │   │   ├── __init__.py
│   │   │   ├── br_05.py
│   │   │   ├── br_06.py
│   │   │   ├── br_08.py
│   │   │   ├── br_11.py
│   │   │   ├── br_12.py
│   │   │   ├── br_13.py
│   │   │   └── check_BiRefNet.py
│   │   ├── __init__.py
│   │   ├── _base.py
│   │   ├── analytics.py
│   │   ├── async_workers.py
│   │   ├── bg_remover.py
│   │   ├── chatbot.py
│   │   ├── config.py
│   │   ├── country.py
│   │   ├── finance_ai.py
│   │   ├── geo.py
│   │   ├── image.py
│   │   ├── map.py
│   │   ├── ocr.py
│   │   ├── parcel_verification.py
│   │   ├── search.py
│   │   ├── text.py
│   │   ├── vision.py
│   │   └── voice_to_text.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── accounting.py
│   │   ├── addresses.py
│   │   ├── admin.py
│   │   ├── admin_banners.py
│   │   ├── admin_cash.py
│   │   ├── admin_categories.py
│   │   ├── admin_chat.py
│   │   ├── admin_commission.py
│   │   ├── admin_email.py
│   │   ├── admin_fallback.py
│   │   ├── admin_logistics.py
│   │   ├── admin_orders.py
│   │   ├── admin_payouts.py
│   │   ├── admin_products.py
│   │   ├── admin_promotions.py
│   │   ├── admin_settings.py
│   │   ├── admin_suppliers.py
│   │   ├── admin_treasury.py
│   │   ├── admin_users.py
│   │   ├── admin_video.py
│   │   ├── ai.py
│   │   ├── ai_image.py
│   │   ├── ai_research.py
│   │   ├── ai_upload.py
│   │   ├── audit.py
│   │   ├── auth.py
│   │   ├── automation.py
│   │   ├── banners.py
│   │   ├── batch_upload.py
│   │   ├── cart.py
│   │   ├── cash_management.py
│   │   ├── categories.py
│   │   ├── chat.py
│   │   ├── chat_enrichment.py
│   │   ├── chatbot.py
│   │   ├── comm.py
│   │   ├── command_center.py
│   │   ├── commission.py
│   │   ├── comms_unified.py
│   │   ├── compliance.py
│   │   ├── contact.py
│   │   ├── countries.py
│   │   ├── country_admin.py
│   │   ├── country_auto_populate.py
│   │   ├── country_dropdown.py
│   │   ├── country_maps.py
│   │   ├── country_payouts.py
│   │   ├── country_research.py
│   │   ├── country_staff.py
│   │   ├── coupons.py
│   │   ├── cross_border.py
│   │   ├── csp_reporting.py
│   │   ├── currency.py
│   │   ├── customer_health.py
│   │   ├── ediscovery.py
│   │   ├── email.py
│   │   ├── email_enrichment.py
│   │   ├── employees.py
│   │   ├── entity_chat.py
│   │   ├── entity_communication.py
│   │   ├── escalation.py
│   │   ├── ess.py
│   │   ├── expenses.py
│   │   ├── export.py
│   │   ├── finance.py
│   │   ├── finance_automation.py
│   │   ├── finance_erp.py
│   │   ├── flash_sales.py
│   │   ├── fraud_detection.py
│   │   ├── frontend_errors.py
│   │   ├── geo.py
│   │   ├── hierarchy.py
│   │   ├── hr.py
│   │   ├── hr_dashboard.py
│   │   ├── iam.py
│   │   ├── imports.py
│   │   ├── incident.py
│   │   ├── internal_channels.py
│   │   ├── invoices.py
│   │   ├── jobs.py
│   │   ├── lms.py
│   │   ├── location_api.py
│   │   ├── logistics.py
│   │   ├── logistics_health.py
│   │   ├── logistics_locations.py
│   │   ├── logistics_orders.py
│   │   ├── logistics_orders_v2.py
│   │   ├── logistics_partner.py
│   │   ├── messaging.py
│   │   ├── notifications.py
│   │   ├── okr.py
│   │   ├── onboarding.py
│   │   ├── orders.py
│   │   ├── parcel_tracking.py
│   │   ├── payments.py
│   │   ├── payout_approval.py
│   │   ├── payroll.py
│   │   ├── performance.py
│   │   ├── permissions.py
│   │   ├── product_moderation.py
│   │   ├── product_verification.py
│   │   ├── product_videos.py
│   │   ├── products.py
│   │   ├── proxy_communication.py
│   │   ├── public_suppliers.py
│   │   ├── push_notifications.py
│   │   ├── referrals.py
│   │   ├── returns.py
│   │   ├── reviews.py
│   │   ├── risk.py
│   │   ├── search.py
│   │   ├── shift_handover.py
│   │   ├── shipments.py
│   │   ├── shop_locations.py
│   │   ├── succession.py
│   │   ├── supplier.py
│   │   ├── supplier_analytics.py
│   │   ├── supplier_bg_ab_test.py
│   │   ├── supplier_documents.py
│   │   ├── supplier_finance.py
│   │   ├── supplier_health.py
│   │   ├── supplier_orders.py
│   │   ├── supplier_payouts.py
│   │   ├── supplier_products.py
│   │   ├── supplier_profile.py
│   │   ├── tickets.py
│   │   ├── trading.py
│   │   ├── translate.py
│   │   ├── travel.py
│   │   ├── treasury.py
│   │   ├── upload.py
│   │   ├── upload_jobs.py
│   │   ├── users.py
│   │   ├── video.py
│   │   ├── video_controller.py
│   │   ├── wishlist.py
│   │   ├── workflows.py
│   │   └── ws_chat.py
│   ├── scripts/
│   │   ├── add_schema_declarations.py
│   │   ├── add_schema_declarations_ast.py
│   │   ├── add_schema_declarations_debug.py
│   │   ├── add_schema_declarations_v2.py
│   │   ├── add_schema_declarations_v3.py
│   │   ├── add_schema_to_bare_classes.py
│   │   ├── add_schema_to_models.py
│   │   ├── check_db_models.py
│   │   ├── check_multiline_table_args.py
│   │   ├── check_remaining.py
│   │   ├── check_schema_coverage.py
│   │   ├── comprehensive_schema_check.py
│   │   ├── debug_bare.py
│   │   ├── debug_classes.py
│   │   ├── debug_events.py
│   │   ├── debug_events2.py
│   │   ├── debug_events3.py
│   │   ├── debug_events4.py
│   │   ├── debug_events5.py
│   │   ├── debug_first_class.py
│   │   ├── debug_regex.py
│   │   ├── debug_systemalert.py
│   │   ├── fix_db_models.py
│   │   ├── fix_inline_schema.py
│   │   ├── fix_single_line_table_args.py
│   │   ├── fix_table_args_ast.py
│   │   ├── fix_table_args_comprehensive.py
│   │   ├── fix_table_args_final.py
│   │   ├── fix_table_args_v2.py
│   │   ├── fix_table_args_v3.py
│   │   ├── fix_table_args_v4.py
│   │   ├── list_no_table_args.py
│   │   ├── migrate_media_to_s3.py
│   │   ├── partition_maintenance.sql
│   │   ├── safe_structure_migration.py
│   │   ├── schema_audit_ci.py
│   │   ├── test_create_all.py
│   │   ├── validate_migrations.py
│   │   └── verify_syntax.py
│   ├── services/
│   │   ├── payments/
│   │   ├── __init__.py
│   │   ├── advanced_filter_service.py
│   │   ├── advanced_search_engine.py
│   │   ├── ai_automation_service.py
│   │   ├── ai_copy_jobs.py
│   │   ├── ai_research_jobs.py
│   │   ├── ai_search_service.py
│   │   ├── ai_service.py
│   │   ├── ai_variant_config.py
│   │   ├── approval_matrix_service.py
│   │   ├── asset_tracking.py
│   │   ├── attendance_service.py
│   │   ├── audit_service.py
│   │   ├── audit_trail_service.py
│   │   ├── auth_service.py
│   │   ├── auto_payout_scheduler.py
│   │   ├── automation_scheduler.py
│   │   ├── background_check.py
│   │   ├── bg_removal_presets.py
│   │   ├── bg_removal_service.py
│   │   ├── biometric_auth.py
│   │   ├── cash_flow_forecast_service.py
│   │   ├── cash_management_service.py
│   │   ├── chat_enrichment.py
│   │   ├── chat_system.py
│   │   ├── coi_engine.py
│   │   ├── coi_service.py
│   │   ├── command_center_background.py
│   │   ├── command_center_service.py
│   │   ├── commission_engine.py
│   │   ├── communication_audit.py
│   │   ├── compliance_engine.py
│   │   ├── confidence_scoring.py
│   │   ├── content_service.py
│   │   ├── country_ai_research.py
│   │   ├── country_auto_populate.py
│   │   ├── country_data_orchestrator.py
│   │   ├── country_detection.py
│   │   ├── country_heuristic_engine.py
│   │   ├── country_research.py
│   │   ├── country_rls_service.py
│   │   ├── credit_control_service.py
│   │   ├── cross_border_detection.py
│   │   ├── cross_border_service.py
│   │   ├── cross_border_tracker.py
│   │   ├── customer_health_engine.py
│   │   ├── data_residency.py
│   │   ├── data_residency_service.py
│   │   ├── dei_auditor.py
│   │   ├── downstream_hooks.py
│   │   ├── downstream_wiring.py
│   │   ├── ediscovery.py
│   │   ├── effective_permissions.py
│   │   ├── email_enrichment.py
│   │   ├── email_event_service.py
│   │   ├── email_gateway.py
│   │   ├── email_reputation.py
│   │   ├── employee_activity_logger.py
│   │   ├── employee_communication_service.py
│   │   ├── employee_lifecycle_service.py
│   │   ├── entity_chat_service.py
│   │   ├── erp_finance_service.py
│   │   ├── escalation_sla.py
│   │   ├── expense_processing.py
│   │   ├── expense_routing.py
│   │   ├── external_contact.py
│   │   ├── finance_automation.py
│   │   ├── finance_transfer_service.py
│   │   ├── financial_reporting.py
│   │   ├── financial_reports_service.py
│   │   ├── fix_chat.py
│   │   ├── fraud_detection.py
│   │   ├── fraud_detection_service.py
│   │   ├── fraud_service.py
│   │   ├── free_image_tools.py
│   │   ├── fulfillment_service.py
│   │   ├── gateway_auto_enable.py
│   │   ├── gateway_reconciliation_service.py
│   │   ├── general_ledger_service.py
│   │   ├── geo_fence_service.py
│   │   ├── ghost_watchdog.py
│   │   ├── hierarchy_service.py
│   │   ├── hse_manager.py
│   │   ├── iam_service.py
│   │   ├── image_ai_service.py
│   │   ├── import_service.py
│   │   ├── incident_service.py
│   │   ├── internal_communication.py
│   │   ├── je_reversal_service.py
│   │   ├── kms_encryption.py
│   │   ├── leave_accrual.py
│   │   ├── legal_contract_service.py
│   │   ├── live_tracking_service.py
│   │   ├── lms.py
│   │   ├── lms_permission_lock.py
│   │   ├── localization_service.py
│   │   ├── logistics_engine.py
│   │   ├── logistics_health_engine.py
│   │   ├── logistics_partner_pricing.py
│   │   ├── logistics_sla_service.py
│   │   ├── maker.py
│   │   ├── map_service.py
│   │   ├── media_service.py
│   │   ├── media_storage.py
│   │   ├── mobile_auth_service.py
│   │   ├── notification_engine.py
│   │   ├── notification_service.py
│   │   ├── ocr_parser.py
│   │   ├── offboarding.py
│   │   ├── okr_engine.py
│   │   ├── onboarding_pipeline.py
│   │   ├── order_tracking_service.py
│   │   ├── payment_engine.py
│   │   ├── payment_orchestrator.py
│   │   ├── payout_batch_service.py
│   │   ├── payout_engine.py
│   │   ├── payout_notification_service.py
│   │   ├── payroll_engine.py
│   │   ├── payroll_service.py
│   │   ├── performance_service.py
│   │   ├── period_close_service.py
│   │   ├── permission_service.py
│   │   ├── promotion_bogo_service.py
│   │   ├── promotion_points_service.py
│   │   ├── proxy_communication.py
│   │   ├── qr_service.py
│   │   ├── rbac_service.py
│   │   ├── refund_posting_service.py
│   │   ├── retention_service.py
│   │   ├── run_py.py
│   │   ├── script1.py
│   │   ├── shift_handover.py
│   │   ├── shift_roster_service.py
│   │   ├── shift_scheduling.py
│   │   ├── shipping_tier.py
│   │   ├── storage.py
│   │   ├── sub_ledger_service.py
│   │   ├── succession_service.py
│   │   ├── supplier_health_engine.py
│   │   ├── supplier_onboarding_service.py
│   │   ├── tax_service.py
│   │   ├── template.py
│   │   ├── trading_service.py
│   │   ├── transactional_email_service.py
│   │   ├── translation_service.py
│   │   ├── travel_detector.py
│   │   ├── travel_service.py
│   │   ├── treasurer.py
│   │   ├── treasury_adapter.py
│   │   ├── treasury_engine.py
│   │   ├── treasury_service.py
│   │   ├── triple_auth.py
│   │   ├── upload_job_service.py
│   │   ├── variant_config_service.py
│   │   ├── video_conferencing.py
│   │   ├── video_service.py
│   │   ├── webhook_processor.py
│   │   ├── websocket_chat.py
│   │   ├── workflow_engine.py
│   │   ├── worm_audit.py
│   │   ├── write_chat.py
│   │   └── write_files_script.py
│   ├── settings/
│   │   ├── __init__.py
│   │   └── notification_worker.py
│   ├── static/
│   ├── tasks/
│   │   ├── background_tasks.py
│   │   └── fraud_monitoring.py
│   ├── tests/
│   │   ├── playwright/
│   │   │   ├── e2e/
│   │   │   │   ├── finance/
│   │   │   │   ├── auth.spec.ts
│   │   │   │   ├── cart.spec.ts
│   │   │   │   ├── checkout.spec.ts
│   │   │   │   ├── finance-automation.spec.ts
│   │   │   │   ├── products.spec.ts
│   │   │   │   └── user-profile.spec.ts
│   │   │   ├── helpers/
│   │   │   │   └── auth.ts
│   │   │   ├── package.json
│   │   │   └── playwright.config.ts
│   │   ├── conftest.py
│   │   ├── test_admin.py
│   │   ├── test_ai_research_jobs.py
│   │   ├── test_ai_research_router.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_api_pagination.py
│   │   ├── test_auth.py
│   │   ├── test_auto_payout_sweep.py
│   │   ├── test_background_jobs.py
│   │   ├── test_banners.py
│   │   ├── test_cart.py
│   │   ├── test_categories.py
│   │   ├── test_chat.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_communication_services.py
│   │   ├── test_comprehensive_system.py
│   │   ├── test_controller_subpackages.py
│   │   ├── test_countries.py
│   │   ├── test_country_ai_research.py
│   │   ├── test_country_auto_populate.py
│   │   ├── test_country_research.py
│   │   ├── test_coupons.py
│   │   ├── test_ems_edge_cases.py
│   │   ├── test_ems_lifecycle.py
│   │   ├── test_error_handling.py
│   │   ├── test_free_country_research.py
│   │   ├── test_health.py
│   │   ├── test_internal_communication.py
│   │   ├── test_logistics.py
│   │   ├── test_middleware_helpers.py
│   │   ├── test_models.py
│   │   ├── test_notifications.py
│   │   ├── test_orders.py
│   │   ├── test_pagination_integration.py
│   │   ├── test_payments.py
│   │   ├── test_products.py
│   │   ├── test_response_wrapper.py
│   │   ├── test_reviews.py
│   │   ├── test_search.py
│   │   ├── test_search_endpoints.py
│   │   ├── test_security.py
│   │   ├── test_shipping_quote.py
│   │   ├── test_suppliers.py
│   │   ├── test_transaction.py
│   │   ├── test_treasury.py
│   │   ├── test_users.py
│   │   ├── test_versioning.py
│   │   └── test_wishlist.py
│   ├── tools/
│   │   └── mcp/
│   │       ├── mcp_client_example.py
│   │       └── mcp_server.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── analytics_service.py
│   │   ├── api_docs.py
│   │   ├── audit.py
│   │   ├── auth.py
│   │   ├── background_jobs.py
│   │   ├── backup.py
│   │   ├── cache.py
│   │   ├── category_tree.py
│   │   ├── circuit_breaker.py
│   │   ├── config.py
│   │   ├── constant_time.py
│   │   ├── constants.py
│   │   ├── country_detection_middleware.py
│   │   ├── country_rls.py
│   │   ├── currency.py
│   │   ├── datetime_utils.py
│   │   ├── db_backup.py
│   │   ├── dependencies.py
│   │   ├── email_service.py
│   │   ├── encryption.py
│   │   ├── entity_messaging.py
│   │   ├── error_handler.py
│   │   ├── file_validation.py
│   │   ├── ghost_record.py
│   │   ├── health.py
│   │   ├── invoice_html.py
│   │   ├── ip_utils.py
│   │   ├── key_rotation.py
│   │   ├── kms_encryption.py
│   │   ├── kms_integration.py
│   │   ├── logging_config.py
│   │   ├── metrics.py
│   │   ├── middleware_helpers.py
│   │   ├── migrations.py
│   │   ├── ml_worker.py
│   │   ├── money.py
│   │   ├── multi_secret_webhook.py
│   │   ├── order_tracking.py
│   │   ├── pagination.py
│   │   ├── prometheus_setup.py
│   │   ├── qr_auth.py
│   │   ├── rate_limiter.py
│   │   ├── realtime.py
│   │   ├── redis_client.py
│   │   ├── response_wrapper.py
│   │   ├── rls_context.py
│   │   ├── rls_interceptor.py
│   │   ├── rls_middleware.py
│   │   ├── schema_audit.py
│   │   ├── secrets_manager.py
│   │   ├── security_audit.py
│   │   ├── security_metrics.py
│   │   ├── slug.py
│   │   ├── soft_delete.py
│   │   ├── staff_permissions.py
│   │   ├── tracing.py
│   │   ├── variant_key.py
│   │   ├── vault.py
│   │   ├── versioning.py
│   │   └── websocket_manager.py
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── __init__.py
│   ├── _import_test_out.txt
│   ├── alembic.ini
│   ├── alembic_test.json
│   ├── backend.log
│   ├── database.py
│   ├── database_logging.py
│   ├── dev.db
│   ├── lifespan.py
│   ├── main.py
│   ├── pyproject.toml
│   ├── requirements.lock
│   ├── requirements.txt
│   ├── run_server.py
│   ├── run_tests.ps1
│   ├── run_tests.sh
│   ├── schema-audit-report.json
│   ├── schema_mapping.json
│   ├── schemas.py
│   ├── seed_all.py
│   ├── server_stderr.log
│   ├── server_stdout.log
│   └── start_backend.ps1
├── backup_20260729/
│   ├── archive/
│   │   └── alembic-versions-archive-2026-07-27/
│   │       ├── 05a62fd3c5d3_add_origin_city_to_service_areas_and_lp_.py
│   │       ├── 0b41557984a8_phase3_auth_hardening.py
│   │       ├── 0bccd868b96e_add_financial_ledger_and_treasury.py
│   │       ├── 18afc076b757_add_compare_price_to_products.py
│   │       ├── 1abf0fe5acce_phase9_supplier_verification.py
│   │       ├── 2024_10_01_add_country_code_fields.py
│   │       ├── 2026_07_11_17_36-4481d6124799_baseline_canonical_orm_schema_recovered.py
│   │       ├── 20915daf9b29_add_missing_country_config_columns.py
│   │       ├── 20926f31a19a_normalize_country_city_schema.py
│   │       ├── 20926f31a19b_add_country_category_tax_rates_table.py
│   │       ├── 20926f31a19c_add_country_staff_assignments_table.py
│   │       ├── 20926f31a19d_add_country_communications_table.py
│   │       ├── 20926f31a19e_add_cross_country_customer_records_table.py
│   │       ├── 20926f31a19f_add_country_config_versions_table.py
│   │       ├── 20926f31a1a0_add_country_feature_flags_table.py
│   │       ├── 2f07459e835f_phase9_product_moderation_and_tickets.py
│   │       ├── 48c2a8404b0e_add_cart_items.py
│   │       ├── 598ce7e939d1_add_commission_engine_tables.py
│   │       ├── 5ca199ab0c03_initial_schema.py
│   │       ├── 5d9f3a1c2b44_add_order_logistics_allocations.py
│   │       ├── 784a891dd168_add_partner_tracking_and_charge_split.py
│   │       ├── 78b323427448_add_email_marketing_models.py
│   │       ├── 79b533c27897_add_cash_management_tables.py
│   │       ├── 7b91a42af432_cart_variants_and_delivery_profile.py
│   │       ├── 8a1e29bb7c55_add_vat_remittances.py
│   │       ├── 97126a91bc8e_add_operating_regions_to_supplier_.py
│   │       ├── a0b1c2d3e4f5_add_staff_country_codes.py
│   │       ├── a1b2c3d4e5f6_6ec4f9ba_phase1_backend_hardening.py
│   │       ├── a1b2c3d4e5f6_add_normalized_webhook_events.py
│   │       ├── a1b2c3d4e5f6_add_rls_policies_and_country_fields.py
│   │       ├── a1b2c3d4e5f6_add_rls_policies_and_security_enhancements.py
│   │       ├── a1b2c3d4e5f6_check_constraints.py
│   │       ├── a1b2c3d4e5f6_phase1_backend_hardening.py
│   │       ├── a1b2c3d4e5f6a_add_normalized_webhook_events.py
│   │       ├── a1b2c3d4e5f6b_add_rls_policies_and_country_fields.py
│   │       ├── a1b2c3d4e5f7_add_audit_log_table.py
│   │       ├── a1b2c3d4e5f7_add_country_management_tables.py
│   │       ├── a1b2c3d4e5f7a_add_audit_log_table.py
│   │       ├── a1b2c3d4e5f7b_add_country_management_tables.py
│   │       ├── a268796caed2_merge_three_heads.py
│   │       ├── a2b3c4d5e6f7_add_confidence_score.py
│   │       ├── a3b4c5d6e7f8_phase10_push_tokens_revoked_banner.py
│   │       ├── a4b5c6d7e8f9_add_country_cities_and_category_tax_and_macro.py
│   │       ├── a9b0c1d2e3f4_add_payout_provider_metadata.py
│   │       ├── ab8d4b3ead2b_add_maximum_charge_to_logistics_pricing_.py
│   │       ├── add_communication_channels.py
│   │       ├── b0c1d2e3f4a5_convert_payout_amount_to_numeric.py
│   │       ├── b1c2d3e4f5a6_add_product_badge_fields.py
│   │       ├── b1c2d3e4f5g6_add_country_consistency_triggers.py
│   │       ├── b1c8f348e2c7_merge_financial_ledger_and_soft_delete_.py
│   │       ├── b2c3d4e5f6g7_add_command_center_models.py
│   │       ├── b2c3d4e5f6g7_add_employee_hcm_models.py
│   │       ├── b2c3d4e5f6g7a_add_command_center_models.py
│   │       ├── b2c3d4e5f6g7b_add_employee_hcm_models.py
│   │       ├── b7c8d9e0f1a2_add_check_constraints_core_tables.py
│   │       ├── bc641c523e77_phase4_payment_intent_fields.py
│   │       ├── c1d2e3f4a5b6_commission_return_tickets.py
│   │       ├── c1d2e3f4a5b6_create_employee_system.py
│   │       ├── c1d2e3f4a5b6a_commission_return_tickets.py
│   │       ├── c1d2e3f4a5b6b_create_employee_system.py
│   │       ├── c2d3e4f5a6b7_add_notification_fields_and_country_cities.py
│   │       ├── c2d3e4f5a6b7_add_provider_mapping_to_recipient_bank_accounts.py
│   │       ├── c3d4e5f6g7h8_add_materialized_views_for_tier4_analytics.py
│   │       ├── c4d5e6f7a8b9_use_numeric_for_money_fields.py
│   │       ├── c7d8e9f0a1b2_add_logistics_acceptance_vehicle_overrides.py
│   │       ├── c9d2e3f4a5b6_add_supplier_profiles.py
│   │       ├── cabbef94c669_add_supplier_documents_invoices_product_.py
│   │       ├── d0e1f2a3b4c5_add_product_minimum_stock_maximum_stock_.py
│   │       ├── d1e2f3a4b5c6_add_logistics_tables.py
│   │       ├── d3ec18c6ac15_add_index_product_supplier_id.py
│   │       ├── d4a7c6f2b9e1_phase4_authoritative_order_totals.py
│   │       ├── d5477adebb01_merge_heads.py
│   │       ├── d6e7f8a9b0c1_add_payment_provider_runtime_config.py
│   │       ├── d6e7f8a9b0c1_fix_missing_stub.py
│   │       ├── d6e7f8a9b0c1b_fix_missing_stub_unique.py
│   │       ├── d6e7f8a9b0c2_add_email_provider_config.py
│   │       ├── e1f2a3b4c5d6_add_banner_appearance_columns.py
│   │       ├── e3f4a5b6c7d8_add_vat_shipping_to_orders.py
│   │       ├── e7f8a9b0c1d2_add_payment_gateway_connections.py
│   │       ├── ems_2026_07_25_add_ems_gap_tables.py
│   │       ├── ems_2026_07_26_add_chat_reactions_legal_holds.py
│   │       ├── ems_2026_07_26_add_hierarchy_columns.py
│   │       ├── f1a2b3c4d5e6_search_snapshots_and_schema_hardening.py
│   │       ├── f2c3d4e5f6a7_phase0_product_active_sales_count.py
│   │       ├── f7e8d9c0b1a2_supply_chain_shipment_events.py
│   │       ├── f8a9b0c1d2e3_add_order_gateway_fee_fields.py
│   │       ├── g1h2i3j4k5l6_add_email_ab_and_gps_fields.py
│   │       ├── g1h2i3j4k5l6_add_gateway_settlement_cycle.py
│   │       ├── g1h2i3j4k5l6a_add_email_ab_and_gps_fields.py
│   │       ├── g1h2i3j4k5l6b_add_gateway_settlement_cycle.py
│   │       ├── h1j2k3l4m5n6_widen_bounded_encrypted_columns.py
│   │       ├── h7i8j9k0l1m2_merge_feature_heads.py
│   │       ├── j1k2l3m4n5o6_add_supplier_discount_duration_fields.py
│   │       ├── k2l3m4n5o6p7_add_shipment_package_fields_and_return_intent.py
│   │       ├── m0n1o2p3q4r5_add_country_staff_assignment_communication_cross_country.py
│   │       ├── m1n2o3p4q5r6_add_gin_indexes_country_configs.py
│   │       ├── m2n3o4p5q6r7_add_media_asset_and_fraud_models.py
│   │       ├── m3n4o5p6q7r8_add_order_payment_method.py
│   │       ├── m5n6o7p8q9r0_add_country_config_gin_indexes.py
│   │       ├── m9n0o1p2q3r4_add_country_admin_control_plane.py
│   │       ├── n1o2p3q4r5s6_add_supplier_public_profile_fields.py
│   │       ├── n5o6p7q8r9s0_uuid_enumeration_prevention.py
│   │       ├── n9o8p7q6r5s4_add_badge_billing_records.py
│   │       ├── p1h2i3j4k5l6_phase1_employee_hierarchy.py
│   │       ├── p1q2r3s4t5u6_add_payout_rule_tables.py
│   │       ├── p4q5r6s7t8u9_add_partner_assignment_and_supplier_return_state.py
│   │       ├── p5q6r7s8t9u0_add_country_config_heuristic_and_expansion.py
│   │       ├── p9q0r1s2t3u4_add_comprehensive_gin_indexes.py
│   │       ├── p9q8r7s6t5u4_add_product_variants_and_video.py
│   │       ├── q1r2s3t4u5v6_add_composite_indexes.py
│   │       ├── q5r6s7t8u9v0_add_gcc_country_config_fields_and_credentials.py
│   │       ├── q6r7s8t9u0v1_backfill_supplier_profile_badge_fields.py
│   │       ├── r0a1b2c3d4e5_add_role_permission_settings.py
│   │       ├── r7s8t9u0v1w2_add_logistics_partner_payouts.py
│   │       ├── s1t2u3v4w5x6_add_staff_management_user_fields.py
│   │       ├── s1t2u3v4w5x6_merge_variant_runtime_heads.py
│   │       ├── s1t2u3v4w5x6a_add_staff_management_user_fields.py
│   │       ├── s1t2u3v4w5x6b_merge_variant_runtime_heads.py
│   │       ├── s9t0u1v2w3x4_add_shipment_delivery_signature_fields.py
│   │       ├── s_20926f31a1a0_stub_for_20926f31a1a0.py
│   │       ├── s_a1b2c3d4e5f6_stub_for_a1b2c3d4e5f6_check_constraints.py
│   │       ├── s_a1b2c3d4e5f6_stub_for_a1b2c3d4e5f6a_add_normalized_webhook_events.py
│   │       ├── s_a2b3c4d5e6f7_stub_for_a2b3c4d5e6f7_add_confidence_score.py
│   │       ├── s_add_communic_stub_for_add_communication_channels.py
│   │       ├── s_b1c2d3e4f5g6_stub_for_b1c2d3e4f5g6_add_country_consistency_triggers.py
│   │       ├── s_b2c3d4e5f6g7_stub_for_b2c3d4e5f6g7b_add_employee_hcm_models.py
│   │       ├── s_c3d4e5f6g7h8_stub_for_c3d4e5f6g7h8.py
│   │       ├── s_d6e7f8a9b0c2_stub_for_d6e7f8a9b0c2.py
│   │       ├── s_g1h2i3j4k5l6_stub_for_g1h2i3j4k5l6b.py
│   │       ├── s_m1n2o3p4q5r6_stub_for_m1n2o3p4q5r6.py
│   │       ├── s_m2n3o4p5q6r7_stub_for_m2n3o4p5q6r7.py
│   │       ├── s_p1h2i3j4k5l6_stub_for_p1h2i3j4k5l6.py
│   │       ├── s_p9q0r1s2t3u4_stub_for_p9q0r1s2t3u4.py
│   │       ├── s_s1t2u3v4w5x6_stub_for_s1t2u3v4w5x6.py
│   │       ├── s_y5z6a7b8c9d0_stub_for_y5z6a7b8c9d0.py
│   │       ├── t1u2v3w4x5y6_add_chatbot_query_events.py
│   │       ├── t1u2v3w4x5y6_add_shipment_confirmation_requests.py
│   │       ├── t1u2v3w4x5y6a_add_chatbot_query_events.py
│   │       ├── t1u2v3w4x5y6b_add_shipment_confirmation_requests.py
│   │       ├── t2u3v4w5x6y7_merge_variant_runtime_heads.py
│   │       ├── u4v5w6x7y8z9_add_finance_bank_accounts.py
│   │       ├── u8v9w0x1y2z3_add_service_area_pricing_fields.py
│   │       ├── v1w2x3y4z5a6_add_per_km_rate_city_distance_matrix_and_breakdown_snapshot.py
│   │       ├── v2w3x4y5z6a7_add_feed_and_campaign_indexes.py
│   │       ├── v3w4x5y6z7a8_add_recipient_bank_accounts.py
│   │       ├── w1x2y3z4a5b6_add_logistics_pricing_profiles.py
│   │       ├── w3x4y5z6a7b8_add_referral_points_system.py
│   │       ├── w9x8y7z6a5b4_add_logistics_cod_remittance_receipts.py
│   │       ├── x1y2z3a4b5c6_add_user_last_login.py
│   │       ├── x2y3z4a5b6c7_merge_logistics_pricing_profile_and_cod_receipt_heads.py
│   │       ├── y3z4a5b6c7d8_add_logistics_category_and_vehicle_rules.py
│   │       ├── y4z5a6b7c8d9_add_email_provider_runtime_config.py
│   │       ├── y5z6a7b8c9d0_add_country_code_to_all_tables.py
│   │       ├── z0y1x2w3v4u5_merge_runtime_bootstrap_heads.py
│   │       ├── z1a2b3c4d5e6_add_employee_system_tables.py
│   │       ├── z2a3b4c5d6e7_seed_employee_test_data.py
│   │       ├── z7b8c9d0e1f2_add_email_delivery_events_and_suppressions.py
│   │       ├── z9a0b1c2d3e4_add_logistics_partner_profile_review_schema.py
│   │       ├── za1b2c3d4e5_remove_legacy_logistics_category_fields.py
│   │       ├── zb1c2d3e4f5_add_product_subcategory_and_visibility_regions.py
│   │       ├── zc1d2e3f4a5_add_soft_delete_columns_to_all_entities.py
│   │       └── zd1e2f3a4b5c_add_advanced_search_filter_and_video_models.py
│   ├── admin.py
│   ├── analytics.py
│   ├── cache_utils.py
│   ├── check_email_events.py
│   ├── check_indexes2.py
│   ├── clean_alembic_migrations.py
│   ├── config.py
│   ├── database.py
│   ├── email_service.py
│   ├── employee_active_tasks.py
│   ├── employee_audit_timeline.py
│   ├── employee_models.py
│   ├── employee_risk_scores.py
│   ├── lifespan.py
│   ├── seed.py
│   ├── seed_commission.py
│   ├── seed_comms.py
│   ├── seed_orders.py
│   ├── seed_products.py
│   ├── seed_users.py
│   ├── soft_delete.py
│   ├── treasury_controller.py
│   ├── user.py
│   └── verify_all_automation.py
├── browser-tests/
│   └── scaling_audit.spec.ts
├── docs/
│   ├── SCALING_PLAN.md
│   └── pgbouncer.md
├── document/
│   ├── BANNER_PROMOTION_DISCOUNT_CODE.md
│   ├── DISCOUNT_SYSTEM.md
│   ├── DISCOUNT_SYSTEM_ADDENDUM.md
│   ├── PROMOTION.md
│   └── PROMOTION_ADDENDUM.md
├── documents/
│   ├── scope/
│   │   ├── governance.yaml
│   │   ├── layer_rules.yaml
│   │   └── repo_structure.yaml
│   ├── snap/
│   │   └── Logo/
│   │       ├── stitch_zozi/
│   │       │   ├── code copy 2.html
│   │       │   ├── code copy.html
│   │       │   ├── code.html
│   │       │   ├── screen.png
│   │       │   ├── screen_1.png
│   │       │   └── screen_2.png
│   │       ├── zozi-logo-app/
│   │       │   ├── recordings/
│   │       │   │   ├── WhatsApp Video 2026-04-03 at 15.43.18.mp4
│   │       │   │   ├── page@0bde5035c7c3ed04ad399d0876f59789.webm
│   │       │   │   └── page@ef9d054f22c85c1c7c6cd7d152691197.webm
│   │       │   ├── scripts/
│   │       │   │   └── record-wordmark.mjs
│   │       │   ├── src/
│   │       │   │   ├── zozi-logo/
│   │       │   │   │   ├── README.md
│   │       │   │   │   ├── ZoziLockup.tsx
│   │       │   │   │   ├── ZoziLogo.tsx
│   │       │   │   │   └── index.ts
│   │       │   │   ├── AnimatedLogo.tsx
│   │       │   │   ├── App.tsx
│   │       │   │   ├── Logo.tsx
│   │       │   │   ├── main.tsx
│   │       │   │   └── styles.css
│   │       │   ├── zozi-logo/
│   │       │   │   ├── README.md
│   │       │   │   ├── ZoziLogo.tsx
│   │       │   │   ├── ZoziWordmark.tsx
│   │       │   │   ├── index.ts
│   │       │   │   └── shared.ts
│   │       │   ├── README.md
│   │       │   ├── index.html
│   │       │   ├── package.json
│   │       │   ├── tsconfig.json
│   │       │   └── vite.config.ts
│   │       ├── stitch_zozi.zip
│   │       └── zozi-logo-app.zip
│   ├── 00_SCOPE_BINDING.md
│   ├── 01_DATABASE.md
│   ├── ADMIN_PANEL_AUDIT_AND_OPTIMIZATION.md
│   ├── CASH_MANAGEMENT_SYSTEM.md
│   ├── CASH_PAYMENT_CYCLE_AUDIT.md
│   ├── CODEBASE_AUDIT.md
│   ├── CODEBASE_FILE_INDEX.md
│   ├── CODEBASE_STATUS_MATRIX.md
│   ├── COMMISSION_STRUCTURE.md
│   ├── DATABASE_IMPLEMENTATION_PLAN.md
│   ├── DATABASE_REFERENCE.md
│   ├── DESIGN_SYSTEM.md
│   ├── DIR_AUDIT.md
│   ├── DIR_AUDIT_FILE_WORKING.md
│   ├── DISCOUNT_SYSTEM.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── EMAIL_SYSTEM_AUDIT.md
│   ├── FEATURES_LIST.md
│   ├── FILE_ORGANIZATION_RULES.md
│   ├── GENERATED_DATA_DICTIONARY.md
│   ├── ICON_INVENTORY.md
│   ├── LOGISTICS_AUDIT_GAPS.md
│   ├── LOGISTIC_MANAGEMENT.md
│   ├── MULTI_COUNTRY_ADMIN_LAUNCH_PLAN.md
│   ├── MULTI_COUNTRY_SYSTEM.md
│   ├── ORDER_MANAGEMENT.md
│   ├── PAKISTAN_MARKET_PROBLEM.md
│   ├── PAYMENT_GATEWAY_MANAGEMENT.md
│   ├── PLAN_financial_ledger_treasury.md
│   ├── PRODUCTION_DEPLOYMENT.md
│   ├── PROJECT-ROADMAP.md
│   ├── PROJECT_SCAFFOLDING.md
│   ├── PROMOTION.md
│   ├── PROMPT.md
│   ├── Prompt_1.md
│   ├── RETURN_POLICY_FLOW.md
│   ├── RUNTIME_FILE_MAP.md
│   ├── SECURITY_AUDIT_REPORT.md
│   ├── SECURITY_ENHANCEMENT_PLAN.md
│   ├── SECURITY_FINAL_REPORT.md
│   ├── SECURITY_IMPLEMENTATION.md
│   ├── SECURITY_IMPLEMENTATION_REPORT.md
│   ├── STAFF_MANAGEMENT.md
│   ├── SUPPLIER_PRODUCT_UPLOAD.md
│   ├── TEST_STATUS_SUMMARY.md
│   ├── To_Do_List.md
│   ├── WEB_APP_UIUX.md
│   ├── WORKFLOW_STATUS_SUMMARY.md
│   └── admin-country-e2e-checklist.md
├── frontend/
│   ├── mobile_app/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── forgot-password.tsx
│   │   │   │   ├── login.tsx
│   │   │   │   ├── register.tsx
│   │   │   │   ├── reset-password.tsx
│   │   │   │   └── verify-email.tsx
│   │   │   ├── (tabs)/
│   │   │   │   ├── orders/
│   │   │   │   │   ├── [id].tsx
│   │   │   │   │   └── index.tsx
│   │   │   │   ├── products/
│   │   │   │   │   ├── [id].tsx
│   │   │   │   │   └── index.tsx
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── cart.tsx
│   │   │   │   └── profile.tsx
│   │   │   ├── admin/
│   │   │   │   ├── analytics.tsx
│   │   │   │   ├── audit-logs.tsx
│   │   │   │   ├── bank-accounts.tsx
│   │   │   │   ├── banners.tsx
│   │   │   │   ├── barcode.tsx
│   │   │   │   ├── coupons.tsx
│   │   │   │   ├── dashboard.tsx
│   │   │   │   ├── email.tsx
│   │   │   │   ├── exports.tsx
│   │   │   │   ├── flash-sales.tsx
│   │   │   │   ├── invoices.tsx
│   │   │   │   ├── login.tsx
│   │   │   │   ├── logistics-partners.tsx
│   │   │   │   ├── orders.tsx
│   │   │   │   ├── product-verification.tsx
│   │   │   │   ├── products.tsx
│   │   │   │   ├── promotions.tsx
│   │   │   │   ├── returns.tsx
│   │   │   │   ├── suppliers.tsx
│   │   │   │   └── users.tsx
│   │   │   ├── logistics-partner/
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── analytics.tsx
│   │   │   │   ├── dashboard.tsx
│   │   │   │   ├── login.tsx
│   │   │   │   ├── payouts.tsx
│   │   │   │   ├── profile.tsx
│   │   │   │   ├── register.tsx
│   │   │   │   ├── scan.tsx
│   │   │   │   └── shipments.tsx
│   │   │   ├── logistics-partners/
│   │   │   │   ├── [id].tsx
│   │   │   │   └── index.tsx
│   │   │   ├── newsletter/
│   │   │   │   ├── preferences.tsx
│   │   │   │   └── unsubscribe.tsx
│   │   │   ├── orders/
│   │   │   │   └── [id].tsx
│   │   │   ├── products/
│   │   │   │   ├── [id].tsx
│   │   │   │   └── index.tsx
│   │   │   ├── r/
│   │   │   │   └── [code].tsx
│   │   │   ├── returns/
│   │   │   │   └── [id].tsx
│   │   │   ├── supplier/
│   │   │   │   ├── labels/
│   │   │   │   │   └── [id].tsx
│   │   │   │   ├── products/
│   │   │   │   │   ├── [id].tsx
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   └── new.tsx
│   │   │   │   ├── _layout.tsx
│   │   │   │   ├── analytics.tsx
│   │   │   │   ├── bulk.tsx
│   │   │   │   ├── credibility.tsx
│   │   │   │   ├── dashboard.tsx
│   │   │   │   ├── disputes.tsx
│   │   │   │   ├── documents.tsx
│   │   │   │   ├── guide.tsx
│   │   │   │   ├── inventory.tsx
│   │   │   │   ├── invoices.tsx
│   │   │   │   ├── label.tsx
│   │   │   │   ├── login.tsx
│   │   │   │   ├── logistics.tsx
│   │   │   │   ├── notification-preferences.tsx
│   │   │   │   ├── orders.tsx
│   │   │   │   ├── payouts.tsx
│   │   │   │   ├── profile.tsx
│   │   │   │   ├── regions.tsx
│   │   │   │   ├── register.tsx
│   │   │   │   ├── reports.tsx
│   │   │   │   ├── returns.tsx
│   │   │   │   ├── support.tsx
│   │   │   │   ├── terms.tsx
│   │   │   │   └── upload.tsx
│   │   │   ├── supplier-storefront/
│   │   │   │   └── [slug].tsx
│   │   │   ├── suppliers/
│   │   │   │   └── [id].tsx
│   │   │   ├── tracking/
│   │   │   │   └── [id].tsx
│   │   │   ├── _layout.tsx
│   │   │   ├── archive.tsx
│   │   │   ├── barcode-scan.tsx
│   │   │   ├── change-password.tsx
│   │   │   ├── chatbot-history.tsx
│   │   │   ├── chatbot.tsx
│   │   │   ├── checkout.tsx
│   │   │   ├── coupons.tsx
│   │   │   ├── edit-profile.tsx
│   │   │   ├── flash-sales.tsx
│   │   │   ├── help.tsx
│   │   │   ├── index.tsx
│   │   │   ├── invoice.tsx
│   │   │   ├── newsletter.tsx
│   │   │   ├── notification-preferences.tsx
│   │   │   ├── notifications.tsx
│   │   │   ├── offers.tsx
│   │   │   ├── orders.tsx
│   │   │   ├── push_notifications.tsx
│   │   │   ├── referrals.tsx
│   │   │   ├── returns.tsx
│   │   │   ├── settings.tsx
│   │   │   ├── ticket-detail.tsx
│   │   │   ├── tickets.tsx
│   │   │   ├── wishlist.tsx
│   │   │   └── write-review.tsx
│   │   ├── assets/
│   │   │   ├── adaptive-icon.png
│   │   │   ├── favicon.png
│   │   │   ├── icon.png
│   │   │   └── splash-icon.png
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── AppDrawer.tsx
│   │   │   │   ├── AppHeader.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── CurrencyInit.tsx
│   │   │   │   ├── EmptyState.tsx
│   │   │   │   ├── ErrorAlert.tsx
│   │   │   │   ├── ErrorBanner.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   ├── ErrorHandlerInit.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── GlassCard.tsx
│   │   │   │   ├── GradientButton.tsx
│   │   │   │   ├── GradientHero.tsx
│   │   │   │   ├── HeaderBar.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── LanguageSheet.tsx
│   │   │   │   ├── ListSkeleton.tsx
│   │   │   │   ├── LoadingSkeleton.tsx
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   ├── Logo.tsx
│   │   │   │   ├── ProductGrid.tsx
│   │   │   │   ├── ProductSearchFilterBar.tsx
│   │   │   │   ├── QuickFilters.tsx
│   │   │   │   ├── Screen.tsx
│   │   │   │   ├── ScreenHeader.tsx
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── SearchableSelect.tsx
│   │   │   │   ├── SectionHeader.tsx
│   │   │   │   ├── StatCard.tsx
│   │   │   │   ├── StatusBadge.tsx
│   │   │   │   ├── SupplierBadge.tsx
│   │   │   │   ├── ThemeToggle.tsx
│   │   │   │   ├── TranslatedText.tsx
│   │   │   │   └── index.ts
│   │   │   ├── AddressesScreen.tsx
│   │   │   ├── AuthRequiredModal.tsx
│   │   │   ├── BackgroundJobCenter.tsx
│   │   │   ├── CartItem.tsx
│   │   │   ├── HeroBanner.tsx
│   │   │   ├── HomeProductShowcase.tsx
│   │   │   ├── LimitedTimeOfferBanner.tsx
│   │   │   ├── LocationPicker.tsx
│   │   │   ├── Logo.tsx
│   │   │   ├── MobileBackgroundEffect.tsx
│   │   │   ├── MobileSeasonalBanner.tsx
│   │   │   ├── NewsletterSignup.tsx
│   │   │   ├── OrderCard.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   ├── QuickViewModal.tsx
│   │   │   ├── RecentlyViewed.tsx
│   │   │   ├── Recommendations.tsx
│   │   │   ├── SignaturePad.tsx
│   │   │   ├── ToastContainer.tsx
│   │   │   └── UserRealtimeBridge.tsx
│   │   ├── e2e/
│   │   │   ├── auth-login-smoke.e2e.js
│   │   │   ├── auth.spec.ts
│   │   │   ├── customer-browse-checkout-smoke.e2e.js
│   │   │   ├── init.js
│   │   │   ├── jest.config.js
│   │   │   ├── mobile-smoke.spec.ts
│   │   │   ├── navigation.spec.ts
│   │   │   └── role-dashboard-smoke.e2e.js
│   │   ├── lib/
│   │   │   ├── __mocks__/
│   │   │   │   ├── LoadingSkeleton.js
│   │   │   │   ├── expo-clipboard.ts
│   │   │   │   ├── expo-linear-gradient.ts
│   │   │   │   └── react-native.ts
│   │   │   ├── __tests__/
│   │   │   │   ├── addressesScreen.test.ts
│   │   │   │   ├── adminAnalyticsScreen.test.tsx
│   │   │   │   ├── adminBankAccountsScreen.test.tsx
│   │   │   │   ├── adminDashboardScreen.test.ts
│   │   │   │   ├── adminGuardedScreens.test.tsx
│   │   │   │   ├── adminListUtils.test.ts
│   │   │   │   ├── adminManagementUtils.test.ts
│   │   │   │   ├── adminMobileAudit.test.tsx
│   │   │   │   ├── adminPromotionsHub.test.tsx
│   │   │   │   ├── api.test.ts
│   │   │   │   ├── authRecoveryScreens.test.tsx
│   │   │   │   ├── authStore.test.ts
│   │   │   │   ├── backgroundJobStore.test.ts
│   │   │   │   ├── backgroundJobs.test.ts
│   │   │   │   ├── cartScreen.test.tsx
│   │   │   │   ├── cartStore.test.ts
│   │   │   │   ├── chatbotScreen.test.tsx
│   │   │   │   ├── checkoutFlow.test.ts
│   │   │   │   ├── checkoutScreen.test.tsx
│   │   │   │   ├── countryContext.test.tsx
│   │   │   │   ├── couponsScreen.test.ts
│   │   │   │   ├── currencyStore.test.ts
│   │   │   │   ├── customerAccountScreens.test.tsx
│   │   │   │   ├── flashSalesScreen.test.ts
│   │   │   │   ├── homeInsights.test.ts
│   │   │   │   ├── jest.setup.ts
│   │   │   │   ├── localeStore.test.ts
│   │   │   │   ├── loginScreen.test.ts
│   │   │   │   ├── loginScreenRouting.test.tsx
│   │   │   │   ├── logisticsPartnerApi.test.ts
│   │   │   │   ├── logisticsPartnerProfileScreen.test.tsx
│   │   │   │   ├── logisticsPartnerScanScreen.test.tsx
│   │   │   │   ├── logisticsPayoutInsights.test.ts
│   │   │   │   ├── logisticsScreen.test.ts
│   │   │   │   ├── logisticsShipmentsScreen.test.tsx
│   │   │   │   ├── mobileApiRouteHelpers.test.ts
│   │   │   │   ├── newsletterPreferencesScreen.test.tsx
│   │   │   │   ├── notificationsScreen.test.ts
│   │   │   │   ├── ordersScreen.test.ts
│   │   │   │   ├── partnerDashboardScreens.test.tsx
│   │   │   │   ├── productDetailScreen.test.ts
│   │   │   │   ├── productDetailScreenRender.test.tsx
│   │   │   │   ├── productRouteFilters.test.ts
│   │   │   │   ├── registerScreen.test.ts
│   │   │   │   ├── returnsScreen.test.tsx
│   │   │   │   ├── rootLayout.test.tsx
│   │   │   │   ├── searchScreen.test.ts
│   │   │   │   ├── supplierBulkScreen.test.tsx
│   │   │   │   ├── supplierDocumentsApi.test.ts
│   │   │   │   ├── supplierDocumentsScreen.test.tsx
│   │   │   │   ├── supplierNotificationPreferencesScreen.test.tsx
│   │   │   │   ├── supplierOrdersScreen.test.ts
│   │   │   │   ├── supplierPayoutsScreen.test.tsx
│   │   │   │   ├── supplierProductAi.test.ts
│   │   │   │   ├── supplierProductCreateScreen.test.tsx
│   │   │   │   ├── supplierProductForm.test.ts
│   │   │   │   ├── supplierShipmentWorkspace.test.ts
│   │   │   │   ├── supplierSupportScreen.test.tsx
│   │   │   │   ├── themeStore.test.ts
│   │   │   │   ├── ticketsScreen.test.ts
│   │   │   │   ├── toastStore.test.ts
│   │   │   │   ├── trackingScreen.test.tsx
│   │   │   │   ├── trackingScreenRender.test.tsx
│   │   │   │   ├── userRealtime.test.ts
│   │   │   │   └── wishlistStore.test.ts
│   │   │   ├── adminManagementUtils.ts
│   │   │   ├── api.ts
│   │   │   ├── authPrompt.tsx
│   │   │   ├── authStore.ts
│   │   │   ├── backgroundJobStore.ts
│   │   │   ├── backgroundJobs.ts
│   │   │   ├── cartStore.ts
│   │   │   ├── chatbotStore.ts
│   │   │   ├── clipboard.js
│   │   │   ├── clipboard.ts
│   │   │   ├── countryContext.tsx
│   │   │   ├── countrySelection.ts
│   │   │   ├── currencyStore.ts
│   │   │   ├── documentPicker.js
│   │   │   ├── documentPicker.ts
│   │   │   ├── effectStore.ts
│   │   │   ├── errorReporter.ts
│   │   │   ├── expoSecureStorage.ts
│   │   │   ├── fileSystem.js
│   │   │   ├── fileSystem.ts
│   │   │   ├── geo.ts
│   │   │   ├── globalErrorHandler.ts
│   │   │   ├── homeInsights.ts
│   │   │   ├── icons.ts
│   │   │   ├── imagePicker.js
│   │   │   ├── imagePicker.ts
│   │   │   ├── invoiceService.ts
│   │   │   ├── localeStore.ts
│   │   │   ├── logger.ts
│   │   │   ├── logisticsPayoutInsights.ts
│   │   │   ├── notificationStore.ts
│   │   │   ├── paymentService.ts
│   │   │   ├── productDraft.ts
│   │   │   ├── productRouteFilters.ts
│   │   │   ├── recentlyViewedStore.ts
│   │   │   ├── searchHistoryStore.ts
│   │   │   ├── sharing.js
│   │   │   ├── sharing.ts
│   │   │   ├── socialAuth.ts
│   │   │   ├── supplierProductAi.ts
│   │   │   ├── supplierProductForm.ts
│   │   │   ├── supplierShipmentWorkspace.ts
│   │   │   ├── themeStore.ts
│   │   │   ├── toastStore.ts
│   │   │   ├── uiBus.ts
│   │   │   ├── useTranslate.ts
│   │   │   ├── userRealtime.ts
│   │   │   └── wishlistStore.ts
│   │   ├── mocks/
│   │   │   └── LogBox.ts
│   │   ├── playwright-report/
│   │   │   ├── data/
│   │   │   │   ├── 6c6f6f69f352261e263926abb8f3cd9ac99a09c3.webm
│   │   │   │   └── c2f840b8d4629568cb702d3ac18ff61da574d6e3.md
│   │   │   └── index.html
│   │   ├── scripts/
│   │   │   ├── pw-smoke-prod.js
│   │   │   ├── pw-smoke.js
│   │   │   ├── server.err
│   │   │   ├── server.log
│   │   │   ├── simple-server.js
│   │   │   ├── spa.log
│   │   │   └── static-server.js
│   │   ├── test-output/
│   │   │   └── mobile-smoke-Mobile-App-Sm-d7899--with-header-and-navigation-mobile-web/
│   │   │       ├── error-context.md
│   │   │       └── video.webm
│   │   ├── theme/
│   │   │   ├── animations.ts
│   │   │   └── index.ts
│   │   ├── app.config.js
│   │   ├── app.json
│   │   ├── babel.config.js
│   │   ├── eslint.config.js
│   │   ├── expo-env.d.ts
│   │   ├── expo-err.log
│   │   ├── expo-start.log
│   │   ├── jest.config.js
│   │   ├── metro.config.js
│   │   ├── package.json
│   │   ├── patch-logbox.js
│   │   ├── playwright.config.ts
│   │   ├── pnpm-workspace.yaml
│   │   ├── sentry.config.ts
│   │   └── tsconfig.json
│   ├── shared/
│   │   ├── src/
│   │   │   ├── __tests__/
│   │   │   │   ├── cartHelpers.test.ts
│   │   │   │   ├── chatbot.test.ts
│   │   │   │   ├── checkoutHelpers.test.ts
│   │   │   │   ├── localization.test.ts
│   │   │   │   ├── money.test.ts
│   │   │   │   └── orderHelpers.test.ts
│   │   │   ├── components/
│   │   │   │   ├── logo/
│   │   │   │   │   ├── Logo.native.tsx
│   │   │   │   │   ├── Logo.web.tsx
│   │   │   │   │   ├── LogoAnimation.tsx
│   │   │   │   │   ├── ZoziLogo.tsx
│   │   │   │   │   ├── index.ts
│   │   │   │   │   ├── logoArt.ts
│   │   │   │   │   ├── native.ts
│   │   │   │   │   ├── types.ts
│   │   │   │   │   └── web.ts
│   │   │   │   ├── ui/
│   │   │   │   │   ├── Button.native.tsx
│   │   │   │   │   ├── Button.tsx
│   │   │   │   │   ├── Button.web.tsx
│   │   │   │   │   ├── CurrencyInit.native.tsx
│   │   │   │   │   ├── CurrencyInit.tsx
│   │   │   │   │   ├── CurrencyInit.web.tsx
│   │   │   │   │   ├── ErrorAlert.native.tsx
│   │   │   │   │   ├── ErrorAlert.web.tsx
│   │   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   │   ├── ErrorHandlerInit.native.tsx
│   │   │   │   │   ├── ErrorHandlerInit.tsx
│   │   │   │   │   ├── ErrorHandlerInit.web.tsx
│   │   │   │   │   ├── GlassCard.native.tsx
│   │   │   │   │   ├── GlassCard.web.tsx
│   │   │   │   │   ├── Input.native.tsx
│   │   │   │   │   ├── Input.tsx
│   │   │   │   │   ├── Input.web.tsx
│   │   │   │   │   ├── LoadingSkeleton.native.tsx
│   │   │   │   │   ├── LoadingSkeleton.web.tsx
│   │   │   │   │   ├── Logo.native.tsx
│   │   │   │   │   ├── Logo.web.tsx
│   │   │   │   │   ├── LogoAnimation.tsx
│   │   │   │   │   ├── ProductGrid.native.tsx
│   │   │   │   │   ├── QuickFilters.native.tsx
│   │   │   │   │   ├── QuickFilters.tsx
│   │   │   │   │   ├── SearchBar.native.tsx
│   │   │   │   │   ├── SearchBar.tsx
│   │   │   │   │   ├── SearchBar.web.tsx
│   │   │   │   │   ├── SupplierBadge.native.tsx
│   │   │   │   │   ├── SupplierBadge.web.tsx
│   │   │   │   │   ├── ThemeToggle.native.tsx
│   │   │   │   │   ├── ThemeToggle.web.tsx
│   │   │   │   │   ├── TranslatedText.native.tsx
│   │   │   │   │   ├── TranslatedText.web.tsx
│   │   │   │   │   └── index.ts
│   │   │   │   ├── EnterpriseDataTable.tsx
│   │   │   │   ├── ProductCard.test.ts
│   │   │   │   └── ProductCard.ts
│   │   │   ├── logo/
│   │   │   │   ├── Logo.native.tsx
│   │   │   │   ├── Logo.web.tsx
│   │   │   │   ├── LogoAnimation.tsx
│   │   │   │   ├── ZoziLogo.tsx
│   │   │   │   ├── index.ts
│   │   │   │   ├── motion.tsx
│   │   │   │   ├── native.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── web.ts
│   │   │   ├── addressHelpers.ts
│   │   │   ├── adminListUtils.ts
│   │   │   ├── adminPermissions.ts
│   │   │   ├── api-core.ts
│   │   │   ├── cartHelpers.test.ts
│   │   │   ├── cartHelpers.ts
│   │   │   ├── chatbot.test.ts
│   │   │   ├── chatbot.ts
│   │   │   ├── checkoutHelpers.test.ts
│   │   │   ├── checkoutHelpers.ts
│   │   │   ├── errorLogging.ts
│   │   │   ├── i18n.ts
│   │   │   ├── index.ts
│   │   │   ├── localization.test.ts
│   │   │   ├── localization.ts
│   │   │   ├── money.test.ts
│   │   │   ├── money.ts
│   │   │   ├── notificationHelpers.ts
│   │   │   ├── notificationStore.ts
│   │   │   ├── orderHelpers.test.ts
│   │   │   ├── orderHelpers.ts
│   │   │   ├── productCardModel.ts
│   │   │   ├── productHelpers.ts
│   │   │   ├── productQuery.ts
│   │   │   ├── realtime.ts
│   │   │   ├── requestCache.ts
│   │   │   ├── returnsApi.ts
│   │   │   ├── statusColors.ts
│   │   │   ├── supplierProductOptions.ts
│   │   │   ├── theme.native.ts
│   │   │   ├── theme.ts
│   │   │   ├── ticketHelpers.ts
│   │   │   ├── trackingMap.ts
│   │   │   ├── types.ts
│   │   │   ├── userRealtimeAlerts.ts
│   │   │   ├── utils.ts
│   │   │   └── wishlistHelpers.ts
│   │   ├── jest.config.js
│   │   ├── jest.setup.ts
│   │   ├── package.json
│   │   ├── tsconfig.build.json
│   │   └── tsconfig.json
│   ├── web_app/
│   │   ├── __tests__/
│   │   │   ├── ErrorBoundary.test.tsx.bak
│   │   │   └── browser.spec.ts
│   │   ├── coverage/
│   │   │   ├── lcov-report/
│   │   │   │   ├── base.css
│   │   │   │   ├── block-navigation.js
│   │   │   │   ├── favicon.png
│   │   │   │   ├── index.html
│   │   │   │   ├── prettify.css
│   │   │   │   ├── prettify.js
│   │   │   │   ├── sort-arrow-sprite.png
│   │   │   │   ├── sorter.js
│   │   │   │   ├── useAuth.ts.html
│   │   │   │   └── useAuth.tsx.html
│   │   │   ├── clover.xml
│   │   │   ├── coverage-final.json
│   │   │   └── lcov.info
│   │   ├── e2e/
│   │   │   ├── bg-comparison-visual.spec.ts-snapshots/
│   │   │   ├── helpers/
│   │   │   │   ├── api.ts
│   │   │   │   └── auth.ts
│   │   │   ├── admin-audit-fixes.spec.ts
│   │   │   ├── admin-commission.spec.ts
│   │   │   ├── admin-communication-hub.spec.ts
│   │   │   ├── admin-country-control-plane.spec.ts
│   │   │   ├── admin-country-enhanced.spec.ts
│   │   │   ├── admin-data-ops.spec.ts
│   │   │   ├── admin-hr-permissions.spec.ts
│   │   │   ├── admin-logistics-pricing-insights-live.spec.ts
│   │   │   ├── admin-logistics-workspace.spec.ts
│   │   │   ├── admin-modules-reconciliation.spec.ts
│   │   │   ├── admin-payment-gateways.spec.ts
│   │   │   ├── admin-supplier-logistics-sanity.spec.ts
│   │   │   ├── admin-treasury-payout.spec.ts
│   │   │   ├── amendment-verify.spec.ts
│   │   │   ├── auth-registration-login.spec.ts
│   │   │   ├── auth-role-login.spec.ts
│   │   │   ├── bg-comparison-visual.spec.ts
│   │   │   ├── chatbot-shopping-assistant.spec.ts
│   │   │   ├── collapse-poll.spec.ts
│   │   │   ├── command-center.spec.ts
│   │   │   ├── comprehensive-test.spec.ts
│   │   │   ├── consistency-audit.spec.ts
│   │   │   ├── countries-search.spec.ts
│   │   │   ├── country-auto-populate.spec.ts
│   │   │   ├── country-integration-rls.spec.ts
│   │   │   ├── country-research-all-modules.spec.ts
│   │   │   ├── cross-border-checkout.spec.ts
│   │   │   ├── customer-core-flow.spec.ts
│   │   │   ├── debug-price.spec.ts
│   │   │   ├── debug2.spec.ts
│   │   │   ├── debug3.spec.ts
│   │   │   ├── debug4.spec.ts
│   │   │   ├── debug5.spec.ts
│   │   │   ├── debug6.spec.ts
│   │   │   ├── debug_test6.js
│   │   │   ├── diag-console.spec.ts
│   │   │   ├── diag-logistics.spec.ts
│   │   │   ├── diag-perf.spec.ts
│   │   │   ├── finance-cod-proof-live.spec.ts
│   │   │   ├── finance-e2e.spec.ts
│   │   │   ├── fulfillment-role-flow.spec.ts
│   │   │   ├── hr-dashboard-visual.spec.ts
│   │   │   ├── hr-dashboard.spec.ts
│   │   │   ├── hr-router-prefix.spec.ts
│   │   │   ├── logistics-country-switching.spec.ts
│   │   │   ├── mobile-panel-audit.spec.ts
│   │   │   ├── panel-slider-audit.spec.ts
│   │   │   ├── parcel-verification.spec.ts
│   │   │   ├── products-visual-shell.spec.ts
│   │   │   ├── scaling_audit.spec.ts
│   │   │   ├── search-bar-header.spec.ts
│   │   │   ├── shipping-quote-checkout.spec.ts
│   │   │   ├── supplier-bulk-upload.spec.ts
│   │   │   ├── supplier-kyc-form.spec.ts
│   │   │   ├── supplier-product-upload-complete.spec.ts
│   │   │   ├── supplier-search.spec.ts
│   │   │   ├── supplier-smoke.spec.ts
│   │   │   ├── test_vat_remittance_fix.py
│   │   │   ├── verify-8-fixes.spec.ts
│   │   │   ├── verify-all-panels.spec.ts
│   │   │   └── voice-to-catalog.spec.ts
│   │   ├── e2e-screenshots/
│   │   │   ├── admin-dashboard.png
│   │   │   ├── checkout-page.png
│   │   │   ├── products-page.png
│   │   │   ├── supplier-orders.png
│   │   │   └── supplier-parcel.png
│   │   ├── public/
│   │   │   ├── file.svg
│   │   │   ├── globe.svg
│   │   │   ├── next.svg
│   │   │   ├── placeholder.svg
│   │   │   ├── vercel.svg
│   │   │   └── window.svg
│   │   ├── scripts/
│   │   │   ├── check_pages.py
│   │   │   ├── diag_checkout.cjs
│   │   │   ├── diag_login.cjs
│   │   │   ├── e2e_payment_gateway.cjs
│   │   │   ├── e2e_storefront_checkout.cjs
│   │   │   ├── extract_tabs.py
│   │   │   ├── extract_tabs_v2.py
│   │   │   ├── final_fixes.py
│   │   │   ├── fix_components.py
│   │   │   ├── gen_variant_config.js
│   │   │   ├── insert_dark_css.py
│   │   │   ├── start-dev.js
│   │   │   └── update_page_imports.py
│   │   ├── src/
│   │   │   ├── __mocks__/
│   │   │   │   ├── nanoid.ts
│   │   │   │   └── styleMock.js
│   │   │   ├── __tests__/
│   │   │   │   ├── components/
│   │   │   │   │   ├── ApprovalActionModal.test.tsx
│   │   │   │   │   ├── CountryDetailWorkspace.test.tsx
│   │   │   │   │   ├── CountryResearchPanel.test.tsx
│   │   │   │   │   ├── Footer.test.tsx
│   │   │   │   │   ├── GhostRowForm.test.tsx
│   │   │   │   │   ├── Header.test.tsx
│   │   │   │   │   ├── ProductCard.test.tsx
│   │   │   │   │   ├── QuickViewModal.test.tsx
│   │   │   │   │   ├── Recommendations.test.tsx
│   │   │   │   │   └── emailComponents.test.tsx
│   │   │   │   ├── lib/
│   │   │   │   │   ├── adminPermissions.test.ts
│   │   │   │   │   ├── api.test.ts
│   │   │   │   │   ├── authCookieProxy.test.ts
│   │   │   │   │   ├── cartStore.test.ts
│   │   │   │   │   ├── cartUtils.test.ts
│   │   │   │   │   ├── currencyStore.test.ts
│   │   │   │   │   ├── localeStore.test.ts
│   │   │   │   │   ├── requestCache.test.ts
│   │   │   │   │   ├── useApprovalCheck.test.tsx
│   │   │   │   │   ├── useAuth.preferences.test.tsx
│   │   │   │   │   ├── userRealtime.test.ts
│   │   │   │   │   ├── utils.test.ts
│   │   │   │   │   └── wishlistStore.test.ts
│   │   │   │   ├── pages/
│   │   │   │   │   ├── adminCommunicationHub.test.tsx
│   │   │   │   │   ├── adminDashboardNavigation.test.tsx
│   │   │   │   │   ├── adminExportsPanel.test.tsx
│   │   │   │   │   ├── adminFinanceCodVerification.test.tsx
│   │   │   │   │   ├── adminLogisticsPages.test.tsx
│   │   │   │   │   ├── adminManagementPages.test.tsx
│   │   │   │   │   ├── adminPaymentsPage.test.tsx
│   │   │   │   │   ├── adminStaffPage.test.tsx
│   │   │   │   │   ├── adminStandalonePages.test.tsx
│   │   │   │   │   ├── bulkOperations.test.tsx
│   │   │   │   │   ├── cart.test.tsx
│   │   │   │   │   ├── checkout.test.tsx
│   │   │   │   │   ├── commissionPolicySync.test.tsx
│   │   │   │   │   ├── countryAdmin.spec.ts
│   │   │   │   │   ├── forgotPassword.test.tsx
│   │   │   │   │   ├── help.test.tsx
│   │   │   │   │   ├── login.test.tsx
│   │   │   │   │   ├── logisticsPartnerAuth.test.tsx
│   │   │   │   │   ├── logisticsPartnerPages.test.tsx
│   │   │   │   │   ├── logisticsPartnerPayoutsReceipt.test.tsx
│   │   │   │   │   ├── productDetail.test.tsx
│   │   │   │   │   ├── products.test.tsx
│   │   │   │   │   ├── profile.test.tsx
│   │   │   │   │   ├── promotionBuilderPanel.test.tsx
│   │   │   │   │   ├── realtimeRefreshPages.test.tsx
│   │   │   │   │   ├── supplierBulkAi.test.tsx
│   │   │   │   │   ├── supplierInvoices.test.tsx
│   │   │   │   │   ├── supplierOrdersPage.test.tsx
│   │   │   │   │   ├── supplierPayoutsPage.test.tsx
│   │   │   │   │   ├── supplierProductsPage.test.tsx
│   │   │   │   │   ├── supplierProfilePage.test.tsx
│   │   │   │   │   ├── supplierRegister.test.tsx
│   │   │   │   │   ├── supplierStorefront.test.tsx
│   │   │   │   │   ├── supplierSupportPage.test.tsx
│   │   │   │   │   ├── trackingPage.test.tsx
│   │   │   │   │   └── wishlist.test.tsx
│   │   │   │   ├── Chatbot.test.tsx
│   │   │   │   └── ErrorBoundary.test.tsx
│   │   │   ├── app/
│   │   │   │   ├── admin/
│   │   │   │   │   ├── accounting/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── audit-logs/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── bank-accounts/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── banners/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── barcode/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── categories/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── chat/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── command-center/
│   │   │   │   │   │   ├── alerts/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── fraud/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── headlines/
│   │   │   │   │   │   │   ├── create/
│   │   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── commission/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── communication/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── countries/
│   │   │   │   │   │   ├── [code]/
│   │   │   │   │   │   │   └── staff/
│   │   │   │   │   │   │       └── page.tsx
│   │   │   │   │   │   ├── components/
│   │   │   │   │   │   │   ├── AnalyticsTab.tsx
│   │   │   │   │   │   │   ├── CategoryCommissionsTab.tsx
│   │   │   │   │   │   │   ├── CommissionTiersTab.tsx
│   │   │   │   │   │   │   ├── CommunicationsTab.tsx
│   │   │   │   │   │   │   ├── CountriesTabProps.ts
│   │   │   │   │   │   │   ├── FeatureFlagsTab.tsx
│   │   │   │   │   │   │   ├── KycTab.tsx
│   │   │   │   │   │   │   ├── LegalRulesTab.tsx
│   │   │   │   │   │   │   ├── LocalizationTab.tsx
│   │   │   │   │   │   │   ├── LogisticsModelTab.tsx
│   │   │   │   │   │   │   ├── LogisticsProvidersTab.tsx
│   │   │   │   │   │   │   ├── MapTab.tsx
│   │   │   │   │   │   │   ├── OverviewTab.tsx
│   │   │   │   │   │   │   ├── PaymentGatewaysTab.tsx
│   │   │   │   │   │   │   ├── PayoutSettingsTab.tsx
│   │   │   │   │   │   │   ├── PromotionsTab.tsx
│   │   │   │   │   │   │   ├── RegionsTab.tsx
│   │   │   │   │   │   │   ├── StaffTab.tsx
│   │   │   │   │   │   │   ├── TaxTab.tsx
│   │   │   │   │   │   │   └── VersionsTab.tsx
│   │   │   │   │   │   ├── CountryLedgerTable.tsx
│   │   │   │   │   │   ├── constants.ts
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   └── types.ts
│   │   │   │   │   ├── coupons/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── ExportsPanel.tsx
│   │   │   │   │   │   ├── _tabs/
│   │   │   │   │   │   │   ├── AnalyticsTab.tsx
│   │   │   │   │   │   │   ├── ApprovalMatrixTab.tsx
│   │   │   │   │   │   │   ├── BannerTab.tsx
│   │   │   │   │   │   │   ├── CouponsTab.tsx
│   │   │   │   │   │   │   ├── FinanceTab.tsx
│   │   │   │   │   │   │   ├── HierarchyTab.tsx
│   │   │   │   │   │   │   ├── InsightsTab.tsx
│   │   │   │   │   │   │   ├── ModerationTab.tsx
│   │   │   │   │   │   │   ├── OrdersTab.tsx
│   │   │   │   │   │   │   ├── PayoutsTab.tsx
│   │   │   │   │   │   │   ├── ProductsTab.tsx
│   │   │   │   │   │   │   ├── SupplierDocumentsTab.tsx
│   │   │   │   │   │   │   └── TicketsTab.tsx
│   │   │   │   │   │   ├── loading.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── disputes/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── DisputesPanel.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── email/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── employees/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   ├── employee-types.ts
│   │   │   │   │   │   │   └── employees-content.tsx
│   │   │   │   │   │   ├── _tabs/
│   │   │   │   │   │   │   ├── AddressMatrixTab.tsx
│   │   │   │   │   │   │   ├── AlumniContractorTab.tsx
│   │   │   │   │   │   │   ├── CommunicationsTab.tsx
│   │   │   │   │   │   │   ├── DEITab.tsx
│   │   │   │   │   │   │   ├── DisciplinaryOffboardingTab.tsx
│   │   │   │   │   │   │   ├── HseTab.tsx
│   │   │   │   │   │   │   ├── InsuranceBenefitsTab.tsx
│   │   │   │   │   │   │   └── PerformanceTab.tsx
│   │   │   │   │   │   ├── employee-types.ts
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── ess/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── exports/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── finance/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   ├── AccountingPanels.tsx
│   │   │   │   │   │   │   ├── BankAccountsPanel.tsx
│   │   │   │   │   │   │   ├── CashFlowCycleTab.tsx
│   │   │   │   │   │   │   └── ErpPanels.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── flash-sales/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── hr/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── inventory-alerts/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── invoices/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── login/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── logistics/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── LogisticsPartnersPanel.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── logistics-partners/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── moderation/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── orders/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   ├── BarcodePanel.tsx
│   │   │   │   │   │   │   └── ReturnsPanel.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── organization/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── payments/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── payouts/
│   │   │   │   │   │   ├── background-jobs/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── payroll/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── permissions/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── permissions-content.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── product-verification/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── products/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── promotions/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   ├── BannersPanel.tsx
│   │   │   │   │   │   │   ├── CouponsPanel.tsx
│   │   │   │   │   │   │   ├── FlashSalesPanel.tsx
│   │   │   │   │   │   │   └── PromotionBuilderPanel.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── resolution/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── returns/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── staff/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── staff-content.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── supplier-documents/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── suppliers/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── tickets/
│   │   │   │   │   │   ├── [id]/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── treasury/
│   │   │   │   │   │   ├── _components/
│   │   │   │   │   │   │   └── treasury-content.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── users/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── video/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── layout.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── api/
│   │   │   │   │   ├── auth/
│   │   │   │   │   │   ├── _shared/
│   │   │   │   │   │   │   └── cookies.ts
│   │   │   │   │   │   ├── login/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   ├── logout/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   ├── me/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   ├── oauth/
│   │   │   │   │   │   │   ├── google/
│   │   │   │   │   │   │   │   └── id-token/
│   │   │   │   │   │   │   │       └── route.ts
│   │   │   │   │   │   │   └── providers/
│   │   │   │   │   │   │       └── route.ts
│   │   │   │   │   │   ├── refresh/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   ├── register/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   └── resend-verification/
│   │   │   │   │   │       └── route.ts
│   │   │   │   │   ├── currency/
│   │   │   │   │   │   └── context/
│   │   │   │   │   │       └── route.ts
│   │   │   │   │   ├── frontend-errors/
│   │   │   │   │   │   └── route.ts
│   │   │   │   │   ├── geo/
│   │   │   │   │   │   └── route.ts
│   │   │   │   │   └── z-rmbg/
│   │   │   │   │       └── route.ts
│   │   │   │   ├── archive/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── auth/
│   │   │   │   │   └── callback/
│   │   │   │   │       ├── SocialAuthCallbackClient.tsx
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── barcode-scan/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── brand/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── cart/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── chatbot/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── checkout/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── contact/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── help/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   └── loading.tsx
│   │   │   │   ├── invoice/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── login/
│   │   │   │   │   ├── LoginClient.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── logistics-partner/
│   │   │   │   │   ├── (auth)/
│   │   │   │   │   │   ├── login/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── register/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── layout.tsx
│   │   │   │   │   ├── analytics/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   ├── loading.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── login/
│   │   │   │   │   ├── payouts/
│   │   │   │   │   │   ├── FinanceSection.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── profile/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── register/
│   │   │   │   │   ├── routes/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── scan/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── shipments/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   └── layout.tsx
│   │   │   │   ├── logistics-partners/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── logo-animation/
│   │   │   │   │   ├── LogoAnimationClient.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── meet/
│   │   │   │   │   └── [room]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── newsletter/
│   │   │   │   │   ├── preferences/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── unsubscribe/
│   │   │   │   │       ├── UnsubscribeClient.tsx
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── notifications/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── orders/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── products/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── profile/
│   │   │   │   │   ├── referrals/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── r/
│   │   │   │   │   └── [code]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── register/
│   │   │   │   │   ├── RegisterClient.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── reset-password/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── returns/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── supplier/
│   │   │   │   │   ├── (auth)/
│   │   │   │   │   │   ├── login/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── register/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── layout.tsx
│   │   │   │   │   ├── analytics/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── batch-upload/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   └── types.ts
│   │   │   │   │   ├── bulk/
│   │   │   │   │   │   ├── components/
│   │   │   │   │   │   │   ├── ColorPickerField.tsx
│   │   │   │   │   │   │   ├── DraftStepSection.tsx
│   │   │   │   │   │   │   ├── MediaSection.tsx
│   │   │   │   │   │   │   ├── ProductDraftCard.tsx
│   │   │   │   │   │   │   ├── SearchableComboBox.tsx
│   │   │   │   │   │   │   └── VariantSection.tsx
│   │   │   │   │   │   ├── draftUtils.ts
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── types.ts
│   │   │   │   │   │   └── validation.ts
│   │   │   │   │   ├── credibility/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   ├── loading.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── disputes/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── documents/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── guide/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── inventory/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── invoices/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── labels/
│   │   │   │   │   │   ├── [id]/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── login/
│   │   │   │   │   ├── logistics/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── notification-preferences/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── orders/
│   │   │   │   │   │   ├── [id]/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── SupplierOrdersList.tsx
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   └── shared.tsx
│   │   │   │   │   ├── payouts/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── products/
│   │   │   │   │   │   ├── [id]/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── add/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── profile/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── regions/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── register/
│   │   │   │   │   ├── reports/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── returns/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── support/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── terms/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── upload/
│   │   │   │   │   │   ├── bg-compare/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── videos/
│   │   │   │   │   │   └── upload/
│   │   │   │   │   │       └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── layout.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── supplier-storefront/
│   │   │   │   │   └── [slug]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── suppliers/
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── tickets/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   └── loading.tsx
│   │   │   │   ├── tracking/
│   │   │   │   │   └── [id]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── verify-email/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── wishlist/
│   │   │   │   │   ├── error.tsx
│   │   │   │   │   ├── loading.tsx
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── HomeClient.tsx
│   │   │   │   ├── document.tsx
│   │   │   │   ├── error.tsx
│   │   │   │   ├── global-error.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── loading.tsx
│   │   │   │   ├── not-found.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── components/
│   │   │   │   ├── admin/
│   │   │   │   │   ├── commandCenter/
│   │   │   │   │   │   └── hud.tsx
│   │   │   │   │   ├── AdminChatPanel.tsx
│   │   │   │   │   ├── AdminEmailPanel.tsx
│   │   │   │   │   ├── AdminVideoPanel.tsx
│   │   │   │   │   ├── CreateCampaignForm.tsx
│   │   │   │   │   ├── EmailCampaignManager.tsx
│   │   │   │   │   ├── EmailProviderConfigManager.tsx
│   │   │   │   │   ├── EmailSuppressionManager.tsx
│   │   │   │   │   └── EmailTemplateManager.tsx
│   │   │   │   ├── auth/
│   │   │   │   │   └── GoogleSignInButton.tsx
│   │   │   │   ├── chat/
│   │   │   │   │   ├── PresenceIndicator.tsx
│   │   │   │   │   └── TypingIndicator.tsx
│   │   │   │   ├── comms/
│   │   │   │   │   ├── Context/
│   │   │   │   │   │   └── Context.tsx
│   │   │   │   │   ├── Rail/
│   │   │   │   │   │   ├── EmailFolderTree.tsx
│   │   │   │   │   │   ├── Rail.tsx
│   │   │   │   │   │   └── ThreadContextMenu.tsx
│   │   │   │   │   ├── Stage/
│   │   │   │   │   │   ├── renderers/
│   │   │   │   │   │   │   ├── B2BMasked.tsx
│   │   │   │   │   │   │   ├── ChatStream.tsx
│   │   │   │   │   │   │   ├── ContactTimeline.tsx
│   │   │   │   │   │   │   ├── EmailView.tsx
│   │   │   │   │   │   │   ├── IncidentRoom.tsx
│   │   │   │   │   │   │   └── VideoRoom.tsx
│   │   │   │   │   │   └── Stage.tsx
│   │   │   │   │   ├── CommShell.tsx
│   │   │   │   │   ├── CommandPalette.tsx
│   │   │   │   │   ├── Composer.tsx
│   │   │   │   │   ├── DragProvider.tsx
│   │   │   │   │   ├── LensChips.tsx
│   │   │   │   │   ├── StatusDock.tsx
│   │   │   │   │   └── UnifiedInboxBridge.tsx
│   │   │   │   ├── country/
│   │   │   │   │   ├── tabs/
│   │   │   │   │   │   └── OverviewTab.tsx
│   │   │   │   │   ├── AuditTrailTimeline.tsx
│   │   │   │   │   ├── CountryDetailWorkspace.tsx
│   │   │   │   │   ├── CountryLedgerTable.tsx
│   │   │   │   │   ├── CountryMapView.tsx
│   │   │   │   │   ├── CountryResearchPanel.tsx
│   │   │   │   │   ├── CountryStaffAssignmentModal.tsx
│   │   │   │   │   ├── DynamicAddressForm.tsx
│   │   │   │   │   ├── GhostRowForm.tsx
│   │   │   │   │   ├── InternalCommunicationsSystem.tsx
│   │   │   │   │   ├── LegalContractGenerator.tsx
│   │   │   │   │   ├── LocationTrackerMap.tsx
│   │   │   │   │   ├── ParcelTracker.tsx
│   │   │   │   │   └── ShiftHandoverModal.tsx
│   │   │   │   ├── ems/
│   │   │   │   │   ├── ActivityTimeline.tsx
│   │   │   │   │   ├── ChatEnrichment.tsx
│   │   │   │   │   ├── OrgChartTree.tsx
│   │   │   │   │   └── PayrollWorkflow.tsx
│   │   │   │   ├── map/
│   │   │   │   │   ├── LocationPicker.tsx
│   │   │   │   │   ├── MapView.tsx
│   │   │   │   │   ├── mapMarker.ts
│   │   │   │   │   └── parseLocation.ts
│   │   │   │   ├── supplier/
│   │   │   │   │   ├── upload/
│   │   │   │   │   │   └── UploadModal.tsx
│   │   │   │   │   ├── AIResultsModal.tsx
│   │   │   │   │   ├── BgStrategyOnboardingTooltip.tsx
│   │   │   │   │   ├── CommissionPolicySummary.tsx
│   │   │   │   │   ├── ParcelAuditWidget.tsx
│   │   │   │   │   ├── PhotoEditorModal.tsx
│   │   │   │   │   ├── ProcessingModal.tsx
│   │   │   │   │   ├── ProductImageCanvas.tsx
│   │   │   │   │   ├── ProductPublishSuccess.tsx
│   │   │   │   │   ├── ProductSpecsSelector.tsx
│   │   │   │   │   ├── QuantityModal.tsx
│   │   │   │   │   ├── SmartMediaUpload.tsx
│   │   │   │   │   ├── SmartPricingPanel.tsx
│   │   │   │   │   ├── SmartVariantMatrix.tsx
│   │   │   │   │   ├── UploadProgressDashboard.tsx
│   │   │   │   │   ├── VerificationPopup.tsx
│   │   │   │   │   ├── VerifyPublishModal.tsx
│   │   │   │   │   ├── VoiceProductInput.tsx
│   │   │   │   │   └── VoiceToCatalogPipeline.tsx
│   │   │   │   ├── ui/
│   │   │   │   │   ├── shared/
│   │   │   │   │   │   ├── Badge.tsx
│   │   │   │   │   │   ├── EmptyState.tsx
│   │   │   │   │   │   ├── LoadingSkeleton.tsx
│   │   │   │   │   │   ├── Modal.tsx
│   │   │   │   │   │   ├── Table.tsx
│   │   │   │   │   │   └── index.ts
│   │   │   │   │   ├── Button.tsx
│   │   │   │   │   ├── Card.tsx
│   │   │   │   │   ├── Dropdown.tsx
│   │   │   │   │   ├── FormLayout.tsx
│   │   │   │   │   ├── GlassCard.tsx
│   │   │   │   │   └── StatCard.tsx
│   │   │   │   ├── AdminLayout.tsx
│   │   │   │   ├── AdminRouteRedirect.tsx
│   │   │   │   ├── AdvancedFilter.tsx
│   │   │   │   ├── AdvancedFilterPanel.tsx
│   │   │   │   ├── AppFooter.tsx
│   │   │   │   ├── ApprovalActionModal.tsx
│   │   │   │   ├── AuthRequiredModal.tsx
│   │   │   │   ├── BackgroundEffect.tsx
│   │   │   │   ├── BackgroundJobCenter.tsx
│   │   │   │   ├── BannerCanvasEditor.tsx
│   │   │   │   ├── BannerCarousel.tsx
│   │   │   │   ├── BrandLoading.tsx
│   │   │   │   ├── Breadcrumbs.tsx
│   │   │   │   ├── BulkActionBar.tsx
│   │   │   │   ├── Carousel.tsx
│   │   │   │   ├── CategoryGrid.tsx
│   │   │   │   ├── CategorySidebar.tsx
│   │   │   │   ├── ChartComponents.tsx
│   │   │   │   ├── Chatbot.tsx
│   │   │   │   ├── ClientDeferred.tsx
│   │   │   │   ├── ColumnVisibilityPanel.tsx
│   │   │   │   ├── CurrencyInit.tsx
│   │   │   │   ├── DataDensityToggle.tsx
│   │   │   │   ├── DirectorySection.tsx
│   │   │   │   ├── EcosystemWidget.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   ├── ErrorHandlerInit.tsx
│   │   │   │   ├── FilterSearchBar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   ├── FraudDetectionDashboard.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── HeaderSearchBar.tsx
│   │   │   │   ├── Hero.tsx
│   │   │   │   ├── HomeProductShowcase.tsx
│   │   │   │   ├── InlineActionButtons.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── KeyboardShortcutsHelp.tsx
│   │   │   │   ├── LimitedTimeOffer.tsx
│   │   │   │   ├── LoadingSkeleton.tsx
│   │   │   │   ├── LocaleInit.tsx
│   │   │   │   ├── LogisticsPartnerLayout.tsx
│   │   │   │   ├── Logo.tsx
│   │   │   │   ├── MobileNav.tsx
│   │   │   │   ├── MobileSearchOverlay.tsx
│   │   │   │   ├── NewsletterSignup.tsx
│   │   │   │   ├── PanelPage.tsx
│   │   │   │   ├── PanelShell.tsx
│   │   │   │   ├── PillTag.tsx
│   │   │   │   ├── ProductCard.test.tsx
│   │   │   │   ├── ProductCard.tsx
│   │   │   │   ├── ProductGrid.tsx
│   │   │   │   ├── QuickDetailModal.tsx
│   │   │   │   ├── QuickViewModal.tsx
│   │   │   │   ├── RecentlyViewed.tsx
│   │   │   │   ├── Recommendations.tsx
│   │   │   │   ├── SearchParamsReader.tsx
│   │   │   │   ├── SeasonalBanner.tsx
│   │   │   │   ├── SignaturePad.tsx
│   │   │   │   ├── StatsGrid.tsx
│   │   │   │   ├── SupplierLayout.tsx
│   │   │   │   ├── SupplierRouteRedirect.tsx
│   │   │   │   ├── TestimonialsWidget.tsx
│   │   │   │   ├── ThemeProvider.tsx
│   │   │   │   ├── ThemeToggle.tsx
│   │   │   │   ├── TickerBar.tsx
│   │   │   │   ├── ToastContainer.tsx
│   │   │   │   ├── TopCategoriesWidget.tsx
│   │   │   │   ├── TranslatedText.tsx
│   │   │   │   ├── UnifiedSearchBar.tsx
│   │   │   │   ├── UserRealtimeBridge.tsx
│   │   │   │   ├── VideoScrollingRow.tsx
│   │   │   │   └── approvalTypes.ts
│   │   │   ├── hooks/
│   │   │   │   ├── useApprovalCheck.ts
│   │   │   │   ├── useChatHistory.ts
│   │   │   │   ├── useChatWebSocket.ts
│   │   │   │   ├── useCommState.ts
│   │   │   │   ├── useCountryAccess.ts
│   │   │   │   ├── useCountryAutoPopulate.ts
│   │   │   │   ├── useCrossBorder.ts
│   │   │   │   ├── usePanelLayout.ts
│   │   │   │   ├── useSearchHistory.ts
│   │   │   │   ├── useSendMessage.ts
│   │   │   │   ├── useThreadMessages.ts
│   │   │   │   ├── useUnifiedInbox.ts
│   │   │   │   └── useWebSocket.ts
│   │   │   ├── lib/
│   │   │   │   ├── api/
│   │   │   │   │   ├── auth.ts
│   │   │   │   │   ├── client.ts
│   │   │   │   │   ├── country.ts
│   │   │   │   │   ├── errors.ts
│   │   │   │   │   └── index.ts
│   │   │   │   ├── addressBook.ts
│   │   │   │   ├── adminPanelConfig.ts
│   │   │   │   ├── approvalMatrixApi.ts
│   │   │   │   ├── authCapabilities.ts
│   │   │   │   ├── authModalStore.ts
│   │   │   │   ├── authRedirects.ts
│   │   │   │   ├── authVerification.ts
│   │   │   │   ├── backgroundJobRealtime.ts
│   │   │   │   ├── backgroundJobStore.ts
│   │   │   │   ├── backgroundJobs.ts
│   │   │   │   ├── cartStore.ts
│   │   │   │   ├── cartUtils.ts
│   │   │   │   ├── categoryVariantBridge.ts
│   │   │   │   ├── checkoutConfig.ts
│   │   │   │   ├── crossBorderService.ts
│   │   │   │   ├── currencyStore.ts
│   │   │   │   ├── deliveryStore.ts
│   │   │   │   ├── densityContext.tsx
│   │   │   │   ├── effectStore.ts
│   │   │   │   ├── errorLogging.ts
│   │   │   │   ├── errorReporter.ts
│   │   │   │   ├── globalErrorHandler.ts
│   │   │   │   ├── hierarchyApi.ts
│   │   │   │   ├── i18n.ts
│   │   │   │   ├── icons.ts
│   │   │   │   ├── listResponse.ts
│   │   │   │   ├── localeStore.ts
│   │   │   │   ├── logger.ts
│   │   │   │   ├── notificationStore.ts
│   │   │   │   ├── panelNavigation.ts
│   │   │   │   ├── payoutsApi.ts
│   │   │   │   ├── productCardModel.ts
│   │   │   │   ├── productQrBundle.ts
│   │   │   │   ├── recentlyViewedStore.ts
│   │   │   │   ├── serverAuth.ts
│   │   │   │   ├── themeStore.ts
│   │   │   │   ├── toastStore.ts
│   │   │   │   ├── trackingRealtime.ts
│   │   │   │   ├── types.ts
│   │   │   │   ├── uploadOrchestrator.ts
│   │   │   │   ├── useAdminApi.ts
│   │   │   │   ├── useAdminCountry.tsx
│   │   │   │   ├── useApi.ts
│   │   │   │   ├── useAuth.tsx
│   │   │   │   ├── useBgABTest.ts
│   │   │   │   ├── useBgRecommendations.ts
│   │   │   │   ├── useRequireAuthAction.ts
│   │   │   │   ├── useTranslate.ts
│   │   │   │   ├── userRealtime.ts
│   │   │   │   ├── utils.ts
│   │   │   │   ├── variantConfig.ts
│   │   │   │   └── wishlistStore.ts
│   │   │   ├── logo/
│   │   │   │   ├── Logo.web.tsx
│   │   │   │   ├── ZoziLogo.tsx
│   │   │   │   ├── index.ts
│   │   │   │   ├── motion.tsx
│   │   │   │   ├── types.ts
│   │   │   │   └── web.ts
│   │   │   ├── services/
│   │   │   │   ├── addressFormatService.ts
│   │   │   │   ├── crossBorderService.ts
│   │   │   │   └── localizationService.ts
│   │   │   ├── styles/
│   │   │   │   ├── comm.css
│   │   │   │   ├── globals.css
│   │   │   │   ├── panel-modern.css
│   │   │   │   └── tokens.css
│   │   │   ├── theme/
│   │   │   │   └── animations.ts
│   │   │   ├── types/
│   │   │   │   └── framer-motion.d.ts
│   │   │   └── utils/
│   │   │       └── test.ts
│   │   ├── test-assets/
│   │   │   └── product-test.jpg
│   │   ├── tmp/
│   │   ├── -w
│   │   ├── Dockerfile
│   │   ├── ERROR_HANDLING.md
│   │   ├── README.md
│   │   ├── _audit_ar.cjs
│   │   ├── _audit_auth.cjs
│   │   ├── _audit_content.cjs
│   │   ├── _audit_html.cjs
│   │   ├── _audit_low.cjs
│   │   ├── _audit_markers.cjs
│   │   ├── _audit_net.cjs
│   │   ├── _audit_panels.cjs
│   │   ├── _audit_single.cjs
│   │   ├── _audit_tabs.cjs
│   │   ├── _audit_treasury.cjs
│   │   ├── _audit_valid.cjs
│   │   ├── _collect_icons.cjs
│   │   ├── _gen_lucide.cjs
│   │   ├── audit-logs-fixed.png
│   │   ├── build_final.log
│   │   ├── build_final2.log
│   │   ├── build_final3.log
│   │   ├── build_final4.log
│   │   ├── build_final5.log
│   │   ├── build_final6.log
│   │   ├── build_log.txt
│   │   ├── build_out.log
│   │   ├── build_out10.log
│   │   ├── build_out11.log
│   │   ├── build_out12.log
│   │   ├── build_out2.log
│   │   ├── build_out3.log
│   │   ├── build_out4.log
│   │   ├── build_out5.log
│   │   ├── build_out6.log
│   │   ├── build_out7.log
│   │   ├── build_out8.log
│   │   ├── build_out9.log
│   │   ├── build_output.txt
│   │   ├── bulk-suppliers-jest.json
│   │   ├── bulk_test_output.txt
│   │   ├── bulk_test_verbose.txt
│   │   ├── command-center-fixed.png
│   │   ├── eslint.config.js
│   │   ├── inspect-playwright.cjs
│   │   ├── jest.config.js
│   │   ├── jest.setup.ts
│   │   ├── logistics_test.txt
│   │   ├── middleware.ts
│   │   ├── next-env.d.ts
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   ├── playwright-results.txt
│   │   ├── playwright.__tests__.config.ts
│   │   ├── playwright.config.ts
│   │   ├── playwright.config.ts.bak
│   │   ├── postcss.config.js
│   │   ├── staff_test.txt
│   │   ├── staff_test2.txt
│   │   ├── standalone_test.txt
│   │   ├── standalone_test2.txt
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── tsconfig.tsbuildinfo
│   │   ├── verify_cart.cjs
│   │   ├── verify_chatbot.cjs
│   │   ├── verify_hash.cjs
│   │   ├── verify_hash_dbg.cjs
│   │   ├── verify_imgs.cjs
│   │   ├── verify_pages.cjs
│   │   ├── verify_style.cjs
│   │   └── verify_zero.cjs
│   ├── README.md
│   └── package.json
├── image/
│   ├── image_01.webp
│   ├── image_02.webp
│   ├── image_03.webp
│   ├── image_04.jpg
│   ├── image_05.jpg
│   ├── image_06.jpg
│   ├── image_07.jpg
│   ├── image_08.webp
│   ├── image_09.jpg
│   ├── image_10.jpg
│   ├── image_11.jpg
│   ├── image_12.jpg
│   ├── image_13.jpg
│   ├── image_14.jpeg
│   ├── image_15.jpeg
│   ├── image_16.jpeg
│   ├── image_17.jpeg
│   ├── image_18.jpeg
│   ├── image_19.webp
│   ├── image_20.jpg
│   ├── image_21.jpg
│   ├── image_22.webp
│   ├── image_23.jpg
│   ├── image_24.jpeg
│   ├── image_25.jpg
│   ├── image_26.jpg
│   ├── image_27.jpg
│   ├── image_28.webp
│   ├── image_29.webp
│   └── image_30.jpg
├── monitoring/
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   └── zozi-system-health.json
│   │       └── datasources/
│   │           └── datasources.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── promtail/
│   │   └── promtail-config.yml
│   ├── tempo/
│   │   └── tempo.yaml
│   ├── alertmanager.yml
│   ├── alerts.yml
│   ├── docker-compose.monitoring.yml
│   ├── fraud_monitoring.py
│   ├── ghost_order_detector.py
│   ├── prometheus.yml
│   └── threat_feed_updater.py
├── nginx/
│   └── nginx.conf
├── provider_test/
│   ├── bg_comparison/
│   │   ├── individual/
│   │   ├── index.html
│   │   └── metrics.json
│   ├── output_bg_all/
│   └── run_bg_comparison.py
├── scripts/
│   ├── backend/
│   │   ├── controllers/
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── config.py
│   │   │   ├── constants.py
│   │   │   └── migrations.py
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── balance.js
│   │   ├── countDivs.js
│   │   ├── countDivs2.js
│   │   ├── linenums.js
│   │   ├── listDivs.js
│   │   ├── parse.js
│   │   ├── patch-vars.js
│   │   ├── patch-vars2.js
│   │   ├── printLines.js
│   │   ├── stackDivs.js
│   │   └── tailwind.config.js
│   ├── maintenance/
│   │   ├── cleanup-bak.sh
│   │   ├── convert-fontsize-to-theme.js
│   │   ├── debug_coupon.py
│   │   ├── fix-theme-module-styles.js
│   │   ├── fix_bad_import_createStyles.py
│   │   ├── fix_createStyles.py
│   │   ├── fix_tailwind_tokens.py
│   │   ├── gen_matrix.py
│   │   ├── gen_routers.py
│   │   ├── overwrite_routers.py
│   │   ├── replace-hardcoded-mobile-sizes.js
│   │   ├── replace_focus_border.py
│   │   ├── seed_finance_browser_walkthrough.py
│   │   └── write_features_list.py
│   ├── recovery/
│   │   ├── recover_remaining_nulls.py
│   │   ├── recovery_strip_null_bytes.py
│   │   ├── restore_phase1.py
│   │   ├── restore_phase2a.py
│   │   ├── restore_phase2b.py
│   │   └── restore_phase3.py
│   ├── setup/
│   │   ├── backend_startup_smoke.py
│   │   └── test_server.py
│   ├── testing/
│   │   ├── loadtests/
│   │   │   ├── README.md
│   │   │   └── k6-core-flows.js
│   │   ├── _batch_ai_test.py
│   │   ├── _smoke_admin_users.py
│   │   ├── ai_image_group_smoke.py
│   │   ├── finance_cycle_smoke.py
│   │   ├── full_stack_health_check.py
│   │   ├── live_order_tracking_smoke.py
│   │   ├── sqlite_schema_contract_smoke.py
│   │   └── test_netstat.bat
│   ├── validation/
│   │   ├── check_backups.py
│   │   ├── check_db.py
│   │   ├── check_git.py
│   │   ├── check_node_modules.py
│   │   ├── check_venv_packages.py
│   │   ├── probe_backend_import.py
│   │   └── validate_stripe_testmode_checkout.py
│   ├── README.md
│   ├── admin_verification.py
│   ├── audit_recovery.py
│   ├── backend_layout_audit_3_0.py
│   ├── backup_restore_drill.py
│   ├── ci_schema_check.py
│   ├── deploy.sh
│   ├── free_country_ecommerce_research.py
│   ├── generate_codebase.py
│   ├── generate_scaffolding.py
│   ├── health-check.sh
│   ├── migrate_to_target_structure.py
│   └── system_architecture_audit.py
├── AGENTS.md
├── API_DOCUMENTATION.md
├── Background_remove_AI_of photo.txt
├── Banner_Promotion_Discount..txt
├── COUNTRY_DETAILS.md
├── Database_Management_System.txt
├── Employee_Chat_Video_Email_System.md
├── Error_Handling_System.txt
├── FEATURE_MATRIX.md
├── Features_List.md
├── Finance_Treasury_System.txt
├── Fraud_Detection_System.txt
├── Makefile
├── Mobile_App_Features_List.txt
├── Multi_Country_System.md
├── PROJECT_SCAFFOLDING.md
├── Payment_Gateway_System.md
├── README.md
├── REPO_LAYOUT_AUDIT_REPORT.md
├── SECURITY.md
├── Search_Filter_Supplier_Video_scrolling.txt
├── Security_System.txt
├── Single_Window_Dashboard_System.txt
├── _orchestrator_read.py
├── backend_server.log
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── fix_issues.py
├── fix_migration_downgrade.py
├── ignored_report.txt
├── login_form.yml
├── login_rsp.json
├── mobile_app.html
├── package.json
├── problems.txt
├── railway.toml
├── run_e2e.ps1
├── run_zozi.bat
├── run_zozi.sh
└── vercel.json
```
