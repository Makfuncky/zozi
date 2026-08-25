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



import providers.media.services.automation_scheduler

import domains.finance.services.reporting.financial_reports_service

import domains.governance.services.audit_trail_service

import domains.governance.services.worm_audit

import domains.finance.services.ledger.bank_transaction_service

import domains.catalog.services.search.search_service

import providers.media.services.ai_search_service

import domains.orders.services

import domains.country.services.cross_border.cross_border_tracker

import domains.customers.services.customer_health_engine

import domains.orders.services

import domains.governance.services.retention_service

import domains.orders.services

import domains.comms.services.messaging.chat.chat_enrichment

import domains.comms.services.shared.admin.communication_audit

import domains.comms.services.shared.admin.content_service

import domains.comms.services.marketing.email_enrichment
import domains.comms.services.marketing.email_event_service
import domains.comms.services.marketing.email_reputation

import domains.comms.services.messaging.chat.entity_messaging

import domains.comms.services.shared.ticket.escalation_sla

import domains.comms.services.shared.security.external_contact

import domains.comms.services.messaging.channel.internal_communication

import domains.comms.services.shared.notification.notification_engine

import domains.comms.services.shared.notification.notification_worker

import domains.comms.services.shared.notification.payout_notification_service

import domains.comms.services.shared.utility.translation_service

import domains.comms.services.messaging.video.video_service

import domains.comms.services.messaging.realtime.websocket_manager

import domains.governance.services

import domains.comms.services.messaging.chat.chat_system

# REMOVED: registry referenced 'services.core.health_service' but no such module exists in the codebase

import domains.governance.services

import domains.governance.services

import domains.governance.services

import providers.media.services.country_ai_research

import domains.logistics.services.country_communication_service

import domains.country.services.research.country_data_orchestrator

import domains.country.services.geo.country_detection

import domains.country.services.research.country_heuristic_engine

import domains.country.services.research.country_research


import domains.country.services.cross_border.cross_border_detection

import domains.comms.services

import domains.suppliers.services.contracts.legal_contract_service

import domains.country.services.localization.localization_service

import domains.logistics.services.map_service

# REMOVED: registry referenced 'services.finance.base_models' but no such module exists in the codebase

import domains.finance.services.reporting.financial_reporting

# REMOVED: registry referenced 'services.finance.ghost_order_detector' but no such module exists in the codebase

# REMOVED: registry referenced 'services.finance.invoice_service' but no such module exists in the codebase

import domains.finance.services.ledger.invoice_write_service

# REMOVED: registry referenced 'services.finance.orphan_detector_service' but no such module exists in the codebase

import domains.finance.services.payouts.payment_orchestrator

# REMOVED: registry referenced 'services.treasury.payouts_write_service' but no such module exists in the codebase

import domains.finance.services.ledger.sub_ledger_service

import domains.finance.services.tax.tax_service

import domains.comms.services

import domains.hr.services.attendance_service

import domains.hr.services.background_check

import domains.hr.services.coi_engine

import domains.governance.services.compliance_engine

import domains.hr.services.dei_auditor

import domains.hr.services.employee_activity_logger

import domains.hr.services.employee_communication_service

import domains.finance.services.ledger.expense_processing

import domains.finance.services.ledger.expense_routing

import domains.governance.services

import domains.hr.services.hse_manager

import domains.governance.services.iam_service

import domains.hr.services.leave_accrual

import domains.hr.services.lms

import domains.hr.services.lms_permission_lock

import domains.hr.services.offboarding

import domains.hr.services.okr_engine

import domains.hr.services.payroll_engine

import domains.hr.services.payroll.payroll_service

import domains.hr.services.performance.performance_service

import domains.hr.services.shift_handover

import domains.hr.services.shift_roster_service

import domains.hr.services.shift_scheduling

import domains.hr.services.succession_service

import domains.hr.services.travel_detector

import domains.hr.services.travel_service

# REMOVED: registry referenced 'services.location.main' but no such module exists in the codebase

import domains.logistics.services.geo_fence_service

import domains.logistics.services.live_tracking_service

import domains.logistics.services.logistics_engine

import domains.logistics.services.health.service

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

import domains.suppliers.services.badges.supplier_badge_service

import domains.suppliers.services.health.supplier_health_engine

import domains.suppliers.services.suppliers_write_service

import structlog

logger = structlog.get_logger(__name__)

