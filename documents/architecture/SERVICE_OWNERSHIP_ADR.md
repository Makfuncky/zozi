# ADR-001: Service Module Ownership & Naming Boundaries (S2 remediation)

- **Status:** Accepted
- **Date:** 2026-08-07
- **Audit ref:** `SYSTEM_AUDIT_REPORT.md` — 🟡 **S2** (overlapping service stems in `backend/services`)
- **Decision:** Codify a single naming convention for service modules and assign a
  canonical owner to every overlapping stem group. New code MUST follow the
  convention; existing overlaps are documented here as the source of truth.

## 1. Naming convention (the rule S2 enforces)

| Suffix | Role | May import | Must NOT import |
|--------|------|-----------|----------------|
| `_service` | Read / query / API-surface logic for a domain | models, `core`, sibling `_service` | controllers, routers |
| `_engine` | Pure computation / scoring / orchestration | models, `core` | controllers, routers, `_write_service` |
| `_read_service` | Read-only data access for a domain | models, `core` | controllers, routers, `_write_service` |
| `_write_service` | Persistence-only helper (no business logic) | models, `core` | controllers, routers, other `_write_service` |
| `*_re-export` shim | Backward-compatible `from X import Y` only | the canonical module | controllers, routers, sibling services |

**Rule of thumb:** if two files share a stem (e.g. `notification_engine` vs
`notification_service`), the `_engine` does the math and the `_service` exposes
it; the `_write_service` only persists. They never import each other.

## 2. Overlapping stem groups — canonical ownership

Each row states the single responsibility so ambiguity (the S2 defect) is removed.

### advanc* — Advanced catalog discovery
- `advanced_filter_service` — faceted / advanced product filtering queries.
- `advanced_search_engine` — search execution engine (ranking, tokenization).

### bg_rem* — Background removal
- `bg_removal_presets` — curated VPS-safe preset configurations for supplier uploads.
- `bg_removal_service` — unified runtime dispatcher over the 6 bg-removal pipelines.

### comman* — Command center
- `command_center_background` — background jobs that pre-compute/cache Tier-2 metrics.
- `command_center_service` — synchronous metric aggregation for the command center UI.

### commis* — Commission
- `commission_engine` — deterministic hybrid commission calculation.
- `commission_write_service` — re-export shim; persistence lives in `services.commerce.*`.

### commun* — Communication
- `communication_audit` — communication audit log / compliance capture.
- `communication_write_service` — re-export shim for communication persistence.

### countr* — Country configuration
- `country_ai_research` — async AI enrichment of qualitative country modules.
- `country_auto_populate` — computes confidence score from data completeness.
- `country_data_orchestrator` — autonomous data orchestrator + heuristic engine.
- `country_detection` — lazy GeoLite2 reader / geo detection.
- `country_heuristic_engine` — algorithmic defaults (KYC tiers, gateway suggestions).
- `country_read_service` — read-only access to country config / cities / flags.
- *(related, non-flagged: `country_research`, `country_rls_service`, `country_write_service`)*

### cross* — Cross-border
- `cross_border_detection` — middleware flagging cross-border customer sessions.
- `cross_border_service` — IP/geo detection + currency/tax swapping + localization.
- `cross_border_tracker` — tracks customers shopping across countries.

### data_r* — Data residency
- `data_residency` — residency tier resolution + KMS key selection.
- `data_residency_service` — PII encryption with localized KMS keys.

### downst* — Downstream wiring
- `downstream_hooks` — connects country config to payment/supplier/logistics.
- `downstream_wiring` — auto-wires downstream systems from country config.

### email* — Email
- `email_enrichment` — smart addressing, DLP scanning, threading, notifications.
- `email_event_service` — inbound email event handling / webhooks.
- `email_gateway` — enterprise gateway: role aliases, DLP, PII redaction, templating.
- `email_reputation` — domain reputation checks for fraud detection.

### employ* — Employee
- `employee_activity_logger` — append-only collaboration ledger.
- `employee_communication_service` — internal chat / email / attachments / threads.
- `employee_lifecycle_service` — onboarding & offboarding pipelines.
- `employee_write_service` — re-export shim for employee persistence.

### expens* — Expenses
- `expense_processing` — validation & reimbursement processing.
- `expense_routing` — routes claims by amount / department / hierarchy.

### financ* — Finance
- `finance_automation` — ERP automation (bill OCR → expense → GL posting).
- `finance_transfer_service` — persists provider dispatch metadata on payout rows.
- `financial_reporting` — analytics layer; delegates standard reports downstream.
- `financial_reports_service` — IS / BS / CF generation from the double-entry ledger.

### fraud* — Fraud
- `fraud_detection` — ghost-employee & anomaly detection engine.
- `fraud_detection_service` — real-time fraud scoring / IP intel / velocity checks.
- `fraud_service` — comprehensive fraud detection & prevention facade.

### gatewa* — Payment gateways
- `gateway_auto_enable` — enables gateways per country configuration.
- `gateway_reconciliation_service` — gateway-side reconciliation.

### logist* — Logistics
- `logistics_engine` — country-aware provider orchestration.
- `logistics_health_engine` — partner performance scoring.
- `logistics_partner_pricing` — inter-city distance / pricing calc.
- `logistics_partner_write_service` — re-export shim for partner persistence.
- `logistics_sla_service` — delivery ETAs considering holidays / working days.
- `logistics_write_service` — re-export shim for logistics persistence.

### media* — Media
- `media_service` — hierarchical storage organization (country/supplier/product).
- `media_storage` — upload handling / processing / CDN integration.

### notifi* — Notifications
- `notification_engine` → `notification_engine` — multi-channel engine w/ templates.
- `notification_service` — fraud alerting & notification dispatch.

### paymen* — Payments
- `payment_engine` — orchestrates payment ops across countries / gateways.
- `payment_orchestrator` — dynamically enables/disables gateways by country.
- `payments_write_service` — re-export shim for payment persistence.

### payout* — Payouts
- `payout_batch_service` — smart automated payout batch generation.
- `payout_engine` — payout execution engine.
- `payout_notification_service` — notifies suppliers/partners of new payouts.

### payrol* — Payroll
- `payroll_engine` — salary calc, bank integration, payslips, disbursement.
- `payroll_service` — payroll facade / scheduling.

### promot* — Promotions
- `promotion_bogo_service` — Buy-X-Get-Y promotion types.
- `promotion_engine_service` — re-export shim for promotion engine.
- `promotion_points_service` — points & loyalty tiers.
- `promotions_write_service` — promotion engine persistence.

### shift* — Shifts
- `shift_handover` — auto-generates shift handover sessions.
- `shift_roster_service` — roster management.
- `shift_scheduling` — shift rostering engine.

### suppli* — Suppliers
- `supplier_health_engine` — supplier trust / health scoring.
- `supplier_onboarding_service` — dynamic document upload fields.
- `suppliers_write_service` — centralized supplier write operations.

### travel* — Travel
- `travel_detector` — impossible-travel detection from geo-fence logs.
- `travel_service` — corporate travel & per-diem management.

### treasu* — Treasury
- `treasurer` — EOSB & treasury integration / bonus calculation.
- `treasury_adapter` — treasury service interface for financial transactions.
- `treasury_engine` — double-entry bookkeeping core (GCC chart of accounts).

### video* — Video
- `video_conferencing` — audio transcription (Whisper / fallback).
- `video_service` — video processing / streaming facade.

### websoc* — WebSockets
- `websocket_chat` — real-time chat (entity-scoped rooms, read receipts).
- `websocket_manager` — re-export shim; canonical impl in `services/comms/websocket_manager`.

## 3. Action items (derived from S2)
1. Files marked "no docstring" in the audit (`advanced_filter_service`,
   `advanced_search_engine`, `communication_audit`, `email_event_service`,
   `gateway_reconciliation_service`, `payout_engine`, `payroll_service`,
   `shift_roster_service`, `video_service`) MUST get a one-line module docstring
   stating their role per §2.
2. New service modules MUST NOT introduce a new overlapping stem without an ADR row.
3. Re-export shims stay import-free of controllers/routers (already enforced in code).
