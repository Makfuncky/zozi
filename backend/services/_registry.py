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
import services.commerce.wishlist_read_service
import services.cross_border_tracker
import services.customer_health_engine
import services.promotion_bogo_service
import services.retention_service
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
import services.approval_matrix_service
import services.chat_system
# REMOVED: registry referenced 'services.core.health_service' but no such module exists in the codebase
import services.rbac_service
import services.workflow_engine
import services.confidence_scoring
import services.country_ai_research
import services.geography.country_communication_service
import services.country_data_orchestrator
import services.country_detection
import services.country_heuristic_engine
import services.country_research
import services.country_rls_service
import services.cross_border_detection
import services.downstream_hooks
import services.legal_contract_service
import services.localization_service
import services.map_service
# REMOVED: registry referenced 'services.finance.base_models' but no such module exists in the codebase
import services.financial_reporting
# REMOVED: registry referenced 'services.finance.ghost_order_detector' but no such module exists in the codebase
# REMOVED: registry referenced 'services.finance.invoice_service' but no such module exists in the codebase
import services.invoice_write_service
# REMOVED: registry referenced 'services.finance.orphan_detector_service' but no such module exists in the codebase
import services.payment_orchestrator
# REMOVED: registry referenced 'services.treasury.payouts_write_service' but no such module exists in the codebase
import services.sub_ledger_service
import services.tax_service
import services.asset_tracking
import services.attendance_service
import services.background_check
import services.coi_engine
import services.compliance_engine
import services.dei_auditor
import services.employee_activity_logger
import services.employee_communication_service
import services.expense_processing
import services.expense_routing
import services.hierarchy_service
import services.hse_manager
import services.iam_service
import services.leave_accrual
import services.lms
import services.lms_permission_lock
import services.offboarding
import services.okr_engine
import services.payroll_engine
import services.hr.payroll_service
import services.performance_service
import services.shift_handover
import services.shift_roster_service
import services.shift_scheduling
import services.succession_service
import services.travel_detector
import services.travel_service
# REMOVED: registry referenced 'services.location.main' but no such module exists in the codebase
import services.geo_fence_service
import services.live_tracking_service
import services.logistics_engine
import services.logistics_health_engine
import services.logistics_sla_service
import services.logistics_write_service
import services.shipping_tier
import services.free_image_tools
import services.image_ai_service
import services.media_service
import services.media_storage
import services.upload_job_service
import services.orders.orders_write_service
import services.orders.qr_service
import services.orders.returns_write_service
import services.biometric_auth
import services.data_residency
import services.data_residency_service
# REMOVED: registry referenced 'services.security.effective_permissions' but no such module exists in the codebase
import services.fraud_detection
# REMOVED: registry referenced 'services.security.fraud_monitoring' but no such module exists in the codebase
import services.fraud_service
import services.ghost_watchdog
import services.iam_write_service
import services.incident_service
import services.kms_encryption
import services.mobile_auth_service
import services.permission_service
import services.permission_primitive_write_service
# REMOVED: registry referenced 'services.security.threat_feed_updater' but no such module exists in the codebase
import services.triple_auth
import services.supplier_badge_service
import services.supplier_health_engine
import services.suppliers_write_service
import structlog
logger = structlog.get_logger(__name__)
