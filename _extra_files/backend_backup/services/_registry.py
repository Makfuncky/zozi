"""Service module registry (import side-effects only).

Some service modules are only reachable through runtime dispatch (schedulers,
webhook handlers, event consumers). They still must be imported once so their
decorators/handlers register and so they are not reported as orphan modules.

This registry lives *inside* the services layer on purpose: `main` may not
import `services` directly (circuit contract), but a services module importing
sibling services modules is a legal, same-layer edge.

Do not add business logic here. Import-only.
"""
from __future__ import annotations

import services.ai.automation_scheduler
import services.analytics.financial_reports_service
import services.audit.audit_trail_service
import services.audit.worm_audit
import services.bank_transaction_service
import services.catalog.advanced_filter_service
import services.catalog.ai_search_service
import services.catalog.wishlist_read_service
import services.commerce.cross_border_tracker
import services.commerce.customer_health_engine
import services.commerce.promotion_bogo_service
import services.commerce.retention_service
import services.commerce.reviews_service
import services.comms.chat_enrichment
import services.comms.communication_audit
import services.comms.content_service
import services.comms.email_enrichment
import services.comms.email_event_service
import services.comms.email_reputation
import services.comms.entity_messaging
import services.comms.escalation_sla
import services.comms.external_contact
import services.comms.internal_communication
import services.comms.notification_engine
import services.comms.notification_worker
import services.comms.payout_notification_service
import services.comms.translation_service
import services.comms.video_service
import services.comms.websocket_manager
import services.core.approval_matrix_service
import services.core.chat_system
import services.core.health_service
import services.core.rbac_service
import services.core.workflow_engine
import services.geography.confidence_scoring
import services.geography.country_ai_research
import services.geography.country_communication_service
import services.geography.country_data_orchestrator
import services.geography.country_detection
import services.geography.country_heuristic_engine
import services.geography.country_research
import services.geography.country_rls_service
import services.geography.cross_border_detection
import services.geography.downstream_hooks
import services.geography.legal_contract_service
import services.geography.localization_service
import services.geography.map_service
import services.finance.base_models
import services.finance.financial_reporting
import services.finance.ghost_order_detector
import services.finance.invoice_service
import services.finance.invoice_write_service
import services.finance.orphan_detector_service
import services.finance.payment_orchestrator
import services.treasury.payouts_write_service
import services.finance.sub_ledger_service
import services.finance.tax_service
import services.hr.asset_tracking
import services.hr.attendance_service
import services.hr.background_check
import services.hr.coi_engine
import services.hr.compliance_engine
import services.hr.dei_auditor
import services.hr.employee_activity_logger
import services.hr.employee_communication_service
import services.hr.expense_processing
import services.hr.expense_routing
import services.hr.hierarchy_service
import services.hr.hse_manager
import services.hr.iam_service
import services.hr.leave_accrual
import services.hr.lms
import services.hr.lms_permission_lock
import services.hr.offboarding
import services.hr.okr_engine
import services.hr.payroll_engine
import services.hr.payroll_service
import services.hr.performance_service
import services.hr.shift_handover
import services.hr.shift_roster_service
import services.hr.shift_scheduling
import services.hr.succession_service
import services.hr.travel_detector
import services.hr.travel_service
import services.location.main
import services.logistics.geo_fence_service
import services.logistics.live_tracking_service
import services.logistics.logistics_engine
import services.logistics.logistics_health_engine
import services.logistics.logistics_sla_service
import services.logistics.logistics_write_service
import services.logistics.shipping_tier
import services.media.free_image_tools
import services.media.image_ai_service
import services.media.media_service
import services.media.media_storage
import services.media.upload_job_service
import services.orders.orders_write_service
import services.orders.qr_service
import services.orders.returns_write_service
import services.finance.payment_engine
import services.finance.webhook_processor
import services.security.biometric_auth
import services.security.data_residency
import services.security.data_residency_service
import services.security.effective_permissions
import services.security.fraud_detection
import services.security.fraud_monitoring
import services.security.fraud_service
import services.security.ghost_watchdog
import services.security.iam_write_service
import services.security.incident_service
import services.security.kms_encryption
import services.security.mobile_auth_service
import services.security.permission_service
import services.security.threat_feed_updater
import services.security.triple_auth
import services.supplier.supplier_badge_service
import services.supplier.supplier_health_engine
import services.supplier.suppliers_write_service
