# Session Note — CG3 circular call chain (1 → 0)

**Date:** 2026-08-10 (evening session)
**Audit finding:** `CG3 | 1 | RED | call-graph | circular call chain: controllers.supplier_controller → services.cash_management_service → controllers.supplier_controller`

## Verified authentic
`services/cash_management_service.py:2097` imported `run_badge_recalculation_cycle` from
`controllers.supplier_controller` (a function-level import → call-graph edge). The controller
imports `cash_management_service` for payout ops → true module-level cycle.

The service-layer home (`services/supplier_badge_service.py`) only had a thin credibility-only
variant; the scheduler (`run_scheduled_finance_cycle`) needs the FULL cycle (badge tier change +
setup billing + recurring billing + audit + cache bump) — return contract:
`suppliers_processed / badges_changed / billings_created / recurring_billings_created`.

## Fix (behavior-preserving port into the services layer)
1. **Ported the full badge recalculation closure** (13 functions + 4 constants, 461 lines) from
   `controllers/supplier_controller.py` into `services/supplier_badge_service.py`, replacing the
   thin `refresh_supplier_badge` / `run_badge_recalculation_cycle` stubs:
   - helpers: `_round_badge_amount`, `_ensure_supplier_profile_record`, `_start_of_month` family,
     `_badge_period_bounds`, `_load_active_badge_tiers`, `_badge_tier_meets_metrics`,
     `_compute_badge_threshold_metrics`, `_select_eligible_badge_tier`, `_serialize_badge_billing_record`,
     `_find_existing_badge_billing`, `_create_badge_billing_record`, `_maybe_create_recurring_badge_billing`,
     `_badge_for_score`
   - constants: `_BADGE_THRESHOLDS`, `_FULFILLED_ORDER_STATUSES`, `_MANUAL_BADGE_LEVELS`, `_BADGE_AMOUNT_QUANT`
   - `refresh_supplier_badge(supplier_id, db)` (full) and `run_badge_recalculation_cycle(db)` (full)
   - legacy scoring (fulfilment/review/docs/age/products model) ported as **`_legacy_compute_credibility_score`**
     to avoid clashing with the service's own new-model `compute_credibility_score` (kept public).
   - service's thin `admin_set_supplier_badge` internal call updated to the new refresh signature.
2. **Controller** (`controllers/supplier_controller.py`, −400 lines): deleted the ported closure,
   kept the surface functions (`list_supplier_badge_catalog`, `list_supplier_badge_billing_history`,
   `record_badge_billing_payment`, `purchase_supplier_badge`, `admin_set_supplier_badge`,
   `compute_credibility_score`) and re-imports the helpers/refresh/cycle from the service
   (controllers→services is the allowed direction). All facade symbols + router call sites intact.
3. **Cycle break**: `cash_management_service.py:2097-2098` re-pointed to
   `services.supplier_badge_service.run_badge_recalculation_cycle` and
   `services.admin_analytics_service.refresh_admin_analytics_snapshots` (service→service).

## Behavior parity (verified)
AST-diffed all 13 ported functions + 4 constants against `git HEAD:controllers/supplier_controller.py`:
**byte-identical** (only the intentional `compute_credibility_score` → `_legacy_…` rename).

## Validation
- CG3 detector replica (cross-layer import graph): `services.cash_management_service` and
  `services.supplier_badge_service` both have **zero controllers imports** → cycle gone.
- New `tests/test_cg3_circular_chain_break.py` 7/7 (no-controllers guards, scheduler result
  contract, signature contracts, controller re-export identity, facade intact).
- Regression sweep (CG3 + CA3 + LC1 + MW3 + PERF2 + SEC5 + controller_subpackages): **49/49 pass**.
- App boots; only router-registration warnings from the concurrent agent's W1 router migration
  (pre-existing — `routers.admin_promotions`/`routers.countries` renamed by them; unrelated).
- Authoritative audit re-run launched; CG3 expected to drop.

## Notes / pre-existing (untouched)
- `tests/test_supplier_badge_service.py` (agent's in-flight test for the domain-organized
  `services.supplier.supplier_badge_service` + `controllers.supplier.supplier_controller`, which
  don't exist yet) fails at collection with ModuleNotFoundError — pre-existing, their migration target.
- `backend/tests/test_recovery_write_services.py` fails at collection: `data.models` missing
  `EmployeeRiskScore` export (agent's committed churn) — pre-existing.
- SEC5 test path updated to the DOM3-migrated home (`controllers/configuration/database.py`);
  the migrated implementation is stronger (sqlalchemy `table()` construct, no raw `text()` SQL).
