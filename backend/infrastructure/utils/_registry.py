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



import domains.media.services.automation_scheduler

import domains.finance.services.financial_reports_service

import domains.governance.services.audit_trail_service

import domains.governance.services.worm_audit

import domains.finance.services.bank_transaction_service

import domains.catalog.services.advanced_filter_service

import domains.media.services.ai_search_service

import domains.orders.services

import domains.country.services.cross_border_tracker

import domains.customers.services.customer_health_engine

import domains.orders.services

import domains.customers.services.retention_service

import domains.orders.services

import domains.comms.services.chat_enrichment

import domains.comms.services.communication_audit

import domains.comms.services.content_service

import domains.comms.services.email_enrichment

import domains.comms.services.email_event_service

import domains.comms.services.email_reputation

import domains.comms.services.entity_messaging

import domains.comms.services.escalation_sla

import domains.comms.services.external_contact

import domains.comms.services.internal_communication

import domains.comms.services.notification_engine

import domains.comms.services.notification_worker

import domains.comms.services.payout_notification_service

import domains.comms.services.translation_service

import domains.comms.services.video_service

import domains.comms.services.websocket_manager

import domains.accounts.services

import domains.comms.services.chat_system

# REMOVED: registry referenced 'services.core.health_service' but no such module exists in the codebase

import domains.accounts.services

import domains.accounts.services

import domains.governance.services

import domains.media.services.country_ai_research

import domains.country.services.country_communication_service

import domains.country.services.country_data_orchestrator

import domains.country.services.country_detection

import domains.country.services.country_heuristic_engine

import domains.country.services.country_research

import domains.country.services.country_rls_service

import domains.country.services.cross_border_detection

import domains.comms.services

import domains.suppliers.services.legal_contract_service

import domains.country.services.localization_service

import domains.logistics.services.map_service

# REMOVED: registry referenced 'services.finance.base_models' but no such module exists in the codebase

import domains.finance.services.financial_reporting

# REMOVED: registry referenced 'services.finance.ghost_order_detector' but no such module exists in the codebase

# REMOVED: registry referenced 'services.finance.invoice_service' but no such module exists in the codebase

import domains.finance.services.invoice_write_service

# REMOVED: registry referenced 'services.finance.orphan_detector_service' but no such module exists in the codebase

import domains.finance.services.payment_orchestrator

# REMOVED: registry referenced 'services.treasury.payouts_write_service' but no such module exists in the codebase

import domains.finance.services.sub_ledger_service

import domains.finance.services.tax_service

import domains.comms.services

import domains.hr.services.attendance_service

import domains.hr.services.background_check

import domains.hr.services.coi_engine

import domains.governance.services.compliance_engine

import domains.hr.services.dei_auditor

import domains.hr.services.employee_activity_logger

import domains.hr.services.employee_communication_service

import domains.finance.services.expense_processing

import domains.finance.services.expense_routing

import domains.accounts.services

import domains.hr.services.hse_manager

import domains.governance.services.iam_service

import domains.hr.services.leave_accrual

import domains.hr.services.lms

import domains.hr.services.lms_permission_lock

import domains.hr.services.offboarding

import domains.hr.services.okr_engine

import domains.hr.services.payroll_engine

import domains.hr.services.payroll_service

import domains.hr.services.performance_service

import domains.hr.services.shift_handover

import domains.hr.services.shift_roster_service

import domains.hr.services.shift_scheduling

import domains.hr.services.succession_service

import domains.country.services.travel_detector

import domains.country.services.travel_service

# REMOVED: registry referenced 'services.location.main' but no such module exists in the codebase

import domains.logistics.services.geo_fence_service

import domains.logistics.services.live_tracking_service

import domains.logistics.services.logistics_engine

import domains.logistics.services.logistics_health_engine

import domains.logistics.services.logistics_sla_service

import domains.logistics.services.logistics_write_service

import domains.logistics.services.shipping_tier

import domains.comms.services

import domains.comms.services

import domains.comms.services

import domains.comms.services

import domains.comms.services

import domains.orders.services.orders_write_service

import domains.comms.services

import domains.orders.services.returns_write_service

import domains.governance.services.biometric_auth

import domains.governance.services.data_residency

import domains.governance.services.data_residency_service

# REMOVED: registry referenced 'services.security.effective_permissions' but no such module exists in the codebase

import domains.governance.services.fraud_detection

# REMOVED: registry referenced 'services.security.fraud_monitoring' but no such module exists in the codebase

import domains.governance.services.fraud_service

import domains.orders.services.ghost_watchdog

import domains.governance.services.iam_write_service

import domains.governance.services.incident_service

import domains.governance.services.kms_encryption

import domains.governance.services.mobile_auth_service

import domains.governance.services.permission_service

import domains.governance.services.permission_primitive_write_service

# REMOVED: registry referenced 'services.security.threat_feed_updater' but no such module exists in the codebase

import domains.governance.services.triple_auth

import domains.suppliers.services.supplier_badge_service

import domains.suppliers.services.supplier_health_engine

import domains.suppliers.services.suppliers_write_service

import structlog

logger = structlog.get_logger(__name__)

