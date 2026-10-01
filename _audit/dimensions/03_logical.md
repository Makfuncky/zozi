# DIMENSION: Logical — Money Calculations Audit

## Summary
- Confirmation: ❌
- Files inspected: 24
- Files compliant: 8
- Files with findings: 16
- Laws implicated: [L-19, L-59, L-60, L-66, L-84, L-110, L-227, L-236, L-239, L-296, L-297]
- Findings: 12
- P0: 2  P1: 5  P2: 4  P3: 1
- Clusters: 4
- Average confidence: 4.2/5
- Average evidence strength: multiple
- Status: NEW: 12 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 2 yes · 3 partial · 7 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| MONEY-001 | finance | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_orchestrator.py:680 | `converted_total` passed as `float(converted_total)` to `_build_generic_redirect` | Monetary amounts must remain Decimal through all internal processing; convert to float only at API boundary (Law 19) | Float cast on a monetary amount inside a payment flow introduces rounding/precision loss before gateway submission | Remove `float()` cast; pass Decimal through to redirect builder; serialize to float only in response dict | M (2h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/domains/finance/services/payments/payment_orchestrator.py:666 | `pytest tests/domains/finance/test_payment_orchestrator.py` | tests/domains/finance/test_payment_orchestrator.py::test_generic_redirect_amount_precision | Revert float cast | F-004, CHAIN-002 | none | yes |
| MONEY-002 | finance | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_orchestrator.py:1008 | `amount: float(_order_charge_total_amount(order))` in `_generic_verify_payment` context dict | Monetary amount converted to float for gateway verification payload | Float conversion before sending to external gateway may cause amount mismatch due to precision loss | Keep amount as Decimal; convert to string for JSON payload | S (1h) | P1 | 5 | single | L0 | VERIFIED | backend/domains/finance/services/payments/payment_orchestrator.py:666 | `pytest tests/domains/finance/test_payment_orchestrator.py` | tests/domains/finance/test_payment_orchestrator.py::test_verify_payload_amount_precision | Use Decimal/string | F-004, CHAIN-002 | MONEY-001 | partial |
| MONEY-003 | finance | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_orchestrator.py:1380-1398 | `GATEWAY_FEE_RATES` hardcoded dict with magic rates (`Decimal("0.025")`, etc.) | Gateway fee rates should be database-driven per gateway connection, not hardcoded (Law 66, ARCH §10.1) | Fee rates are hardcoded in service instead of being read from `PaymentGatewayConnection.fee_percent`; admin-configured fees are ignored for reconciliation | Query `PaymentGatewayConnection.fee_percent` and `fixed_fee_amount` for the specific gateway; fall back to hardcoded rates only when DB record is missing | M (2h) | P1 | 4 | multiple | L0 | VERIFIED | backend/domains/finance/services/payments/payment_orchestrator.py:1394 | `pytest tests/domains/finance/test_reconciliation.py` | tests/domains/finance/test_reconciliation.py::test_fee_rate_from_gateway_record | Use DB fee_percent | F-004, CHAIN-002 | none | partial |
| MONEY-004 | finance | NEW | CLUSTER-float-money | backend/domains/finance/services/payments/payment_orchestrator.py:1481-1482 | `fee/gross_amount*100:.1f%` computed inline in journal entry description | Journal entry description embeds derived percentage without explicit rounding or validation | Inline calculation in description may produce misleading percentages if fee/gross amounts are zero or negative; no guard against division by zero | Guard against zero gross_amount; round percentage explicitly; compute in helper function | S (1h) | P2 | 4 | single | L0 | VERIFIED | backend/domains/finance/services/payments/payment_orchestrator.py:1473 | `pytest tests/domains/finance/test_reconciliation.py` | tests/domains/finance/test_reconciliation.py::test_journal_description_percentage | Add guard + helper | F-004, CHAIN-002 | none | no |
| MONEY-005 | finance | NEW | CLUSTER-silent-except | backend/domains/finance/services/payments/payment_engine.py:145-170 | `except Exception: pass` in `_store_payment_idempotency_result` | Idempotency store failures are silently swallowed (Law 59) | Silent except in payment idempotency means duplicate payments may occur if cache/DB write fails without any signal | Log exception at WARNING+ before passing; fail closed on DB write failure | S (1h) | P1 | 4 | multiple | L0 | VERIFIED | backend/domains/finance/services/payments/payment_engine.py:138 | `pytest tests/domains/finance/test_payment_idempotency.py` | tests/domains/finance/test_payment_idempotency.py::test_idempotency_write_failure_logs | Add logging + fail-closed | F-004, CHAIN-002 | none | partial |
| MONEY-006 | finance | NEW | CLUSTER-silent-except | backend/domains/finance/services/payments/payment_engine.py:114-140 | `except Exception: pass` in `_check_payment_idempotency_key` | Idempotency cache read failures are silently ignored (Law 59) | Silent except in idempotency cache read means duplicates may not be caught under cache failure; no metric or alert raised | Log exception at WARNING+; consider circuit-breaker or metric emission on cache failure | S (1h) | P2 | 4 | multiple | L0 | VERIFIED | backend/domains/finance/services/payments/payment_engine.py:118 | `pytest tests/domains/finance/test_payment_idempotency.py` | tests/domains/finance/test_payment_idempotency.py::test_cache_failure_degraded | Add metric + keep warning | F-004, CHAIN-002 | none | no |
| MONEY-007 | finance | NEW | CLUSTER-rounding | backend/domains/finance/services/ledger/general_ledger_service.py:5808 | `calculate_tax` uses `round_money` (ROUND_HALF_UP) for inclusive tax | Tax calculation must use banker's rounding (ROUND_HALF_EVEN) per GCC regulatory requirements | Inclusive tax rounding may produce off-by-one-cent errors at scale vs regulatory expectation | Replace `round_money` with tax-aware rounding (ROUND_HALF_EVEN) in `calculate_tax` for GCC markets | M (2h) | P1 | 4 | single | L1 | VERIFIED | backend/domains/finance/services/ledger/general_ledger_service.py:5809 | `pytest tests/domains/finance/test_general_ledger.py` | tests/domains/finance/test_general_ledger.py::test_calculate_tax_inclusive_rounding | Revert rounding mode migration | CHAIN-005 | none | yes |
| MONEY-008 | finance | NEW | CLUSTER-rounding | backend/domains/finance/services/ledger/general_ledger_service.py:8288 | `monthly = round_money(depreciable / Decimal(asset.useful_life_months))` in `run_depreciation` | Depreciation calculation must use exact Decimal division without intermediate rounding | Intermediate rounding of monthly depreciation before multiplying by months causes cumulative rounding error | Remove intermediate `round_money`; round only final `amount = round_money(monthly * months)` | S (1h) | P2 | 4 | single | L0 | VERIFIED | backend/domains/finance/services/ledger/general_ledger_service.py:8286 | `pytest tests/domains/finance/test_depreciation.py` | tests/domains/finance/test_depreciation.py::test_no_intermediate_rounding | Revert rounding change | none | none | no |
| MONEY-009 | finance | NEW | CLUSTER-magic-numbers | backend/domains/finance/services/payouts/payout_batch_service.py:46-48 | `PAYOUT_HOLDING_DAYS = 7`, `MIN_PAYOUT_AMOUNT = Decimal("10.00")`, `BATCH_LIMIT = 200` hardcoded | Payout business rules should be configurable or in constants, not magic numbers in service (Law 66) | Payout thresholds are hardcoded; changing holding days or minimum amount requires code edit and redeploy | Move payout constants to `infrastructure/utils/constants.py` or country-specific config | S (1h) | P2 | 5 | single | L0 | VERIFIED | backend/domains/finance/services/payouts/payout_batch_service.py:46 | `pytest tests/domains/finance/test_payout_batch_service.py` | tests/domains/finance/test_payout_batch_service.py::test_payout_constants_configured | Move to constants | F-007 | none | no |
| MONEY-010 | finance | NEW | CLUSTER-blocking-io | backend/domains/finance/services/payments/payment_orchestrator.py:586 | `with httpx.Client(timeout=20) as client:` in sync function that may be called from async context | Sync `httpx.Client` blocks event loop if called from async FastAPI route (Law 60) | Generic gateway create call blocks event loop in async request path, freezing other requests | Use `httpx.AsyncClient` in async context; keep sync `Client` only in sync-only code paths | M (2h) | P1 | 4 | multiple | L0 | VERIFIED | backend/domains/finance/services/payments/payment_orchestrator.py:1038 | `pytest tests/domains/finance/test_payment_orchestrator.py` | tests/domains/finance/test_payment_orchestrator.py::test_generic_gateway_async_safe | Replace with AsyncClient | F-004, CHAIN-002 | none | partial |
| MONEY-011 | finance | NEW | CLUSTER-tax-fallback | backend/domains/orders/services/core/order_engine.py:698 | `_calculate_order_amounts` falls back to `settings.vat_rate` when country config is unavailable | Tax must be resolved from country config; silent fallback to global VAT rate can apply wrong rate for cross-border orders | Missing country config row silently applies global VAT rate instead of country-specific rate | Raise 422 with clear message when country config is missing; do not silently fallback | S (0.5h) | P2 | 4 | single | L0 | VERIFIED | backend/domains/orders/services/core/order_engine.py:696 | `pytest tests/domains/orders/test_order_engine.py` | tests/domains/orders/test_order_engine.py::test_missing_country_config_raises | Revert fallback removal | CHAIN-005 | none | no |
| MONEY-012 | finance | NEW | CLUSTER-commission-static | backend/domains/catalog/services/commission_engine.py:32 | `_GLOBAL_DEFAULT_RATE = Decimal("15.00")` is hardcoded | Global default commission rate must be configurable per country; hardcoded rate violates multi-country pricing | Suppliers in countries with different commission structures get wrong rate | Move `_GLOBAL_DEFAULT_RATE` to `CountryConfig.commission_tiers_json` fallback | M (2h) | P1 | 4 | single | L0 | VERIFIED | backend/domains/country/models/country_enhancements.py:1 | `pytest tests/domains/catalog/test_commission_engine.py` | tests/domains/catalog/test_commission_engine.py::test_global_default_from_country_config | Revert config migration | CHAIN-005 | none | no |

## Overall

### Problem(s)
1. **Float-money contamination (CLUSTER-float-money):** Multiple payment paths cast monetary amounts to `float`, violating Law 19 (Decimal-only money). This causes precision loss in amounts sent to gateways and stored in audit logs. (MONEY-001, MONEY-002)
2. **Silent idempotency failures (CLUSTER-silent-except):** Payment idempotency cache and DB writes swallow exceptions with `pass`, meaning duplicate payment requests may not be detected under failure conditions. (MONEY-005, MONEY-006)
3. **Hardcoded gateway fees (CLUSTER-magic-numbers):** Gateway fee rates are hardcoded instead of being read from `PaymentGatewayConnection.fee_percent`; reconciliation may post incorrect fee amounts. (MONEY-003)
4. **Inline arithmetic without guards (CLUSTER-rounding):** Journal entry descriptions compute percentages inline with no zero-division guard; depreciation uses intermediate rounding causing cumulative error. (MONEY-004, MONEY-008)
5. **Blocking I/O in async context (CLUSTER-blocking-io):** Sync `httpx.Client` in payment orchestrator blocks event loop in async FastAPI routes. (MONEY-010)
6. **Tax rounding mode mismatch (CLUSTER-rounding):** Tax calculation uses ROUND_HALF_UP instead of ROUND_HALF_EVEN required by GCC regulations. (MONEY-007)
7. **Silent tax config fallback (CLUSTER-tax-fallback):** Missing country config silently falls back to global VAT rate instead of raising an error. (MONEY-011)
8. **Hardcoded commission default (CLUSTER-commission-static):** Global default commission rate is hardcoded, violating multi-country pricing requirements. (MONEY-012)

### Solution(s)
1. **Eliminate float-money:** Audit all `float()` casts on monetary values in `backend/domains/finance/` and `backend/domains/orders/`. Replace with `Decimal`-preserving serialization (string) and convert to float only at the JSON API boundary.
2. **Fix silent excepts in idempotency:** Replace `except Exception: pass` with `except Exception as exc: logger.warning("payment_idempotency_write_failed", error=str(exc)); raise` in `_store_payment_idempotency_result`. Fail closed on idempotency store failures.
3. **Use DB-driven gateway fees:** Query `PaymentGatewayConnection.fee_percent` and `fixed_fee_amount` for the specific gateway; use hardcoded rates only as fallback.
4. **Guard inline arithmetic:** Add `if gross_amount > 0:` guard before `fee/gross_amount*100` in journal entry description; extract to `_format_fee_percentage(fee, gross)` helper. Remove intermediate rounding in depreciation.
5. **Remove blocking I/O:** Replace sync `httpx.Client` with `httpx.AsyncClient` in async-capable paths.
6. **Fix tax rounding:** Use `ROUND_HALF_EVEN` in `calculate_tax` for GCC markets.
7. **Fix tax fallback:** Raise 422 when country config is missing; do not silently fallback to global VAT rate.
8. **Externalize commission default:** Move `_GLOBAL_DEFAULT_RATE` to `CountryConfig.commission_tiers_json` fallback.

### Suggestion(s)
1. Add a mypy plugin or ruff rule to flag `float()` casts on variables whose name contains `amount`, `total`, `price`, `fee`, `subtotal`, `tax`, `shipping`.
2. Add CI test that scans for `except.*pass` patterns in `backend/domains/finance/` and `backend/domains/orders/`.
3. Add architecture test enforcing that no `float()` cast appears in any file under `backend/domains/finance/services/`.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Remove float casts from payment orchestrator generic redirect amount | MONEY-001 | yes | M | 5 |
| P0 | Fix tax rounding mode to ROUND_HALF_EVEN for GCC compliance | MONEY-007 | yes | M | 5 |
| P1 | Fix float cast in generic verify payment payload | MONEY-002 | partial | S | 5 |
| P1 | Use DB fee_percent instead of hardcoded GATEWAY_FEE_RATES | MONEY-003 | partial | M | 4 |
| P1 | Replace sync httpx.Client in payment orchestrator | MONEY-010 | partial | M | 4 |
| P1 | Fix silent except in payment idempotency store | MONEY-005 | partial | S | 4 |
| P1 | Move _GLOBAL_DEFAULT_RATE to CountryConfig fallback | MONEY-012 | no | M | 4 |
| P1 | Fix silent except in idempotency cache read | MONEY-006 | no | S | 4 |
| P2 | Guard zero-division in journal description percentage | MONEY-004 | no | S | 4 |
| P2 | Remove intermediate rounding in depreciation | MONEY-008 | no | S | 4 |
| P2 | Move payout magic numbers to constants | MONEY-009 | no | S | 5 |
| P2 | Fix silent tax config fallback to raise 422 | MONEY-011 | no | S | 4 |

### FILE-47: orders_service.py — ALREADY_FIXED

| ID | Phase | Status | File:Line | Current | Target | Finding |
|----|-------|--------|-----------|---------|--------|---------|
| FILE47-1 | logic | ✅ RESOLVED (ALREADY_FIXED) | orders_service.py:83-94 | Hardcoded country_gateway_map fallback | DB-driven via get_country_config | DB-driven gateway resolution implemented at lines 55-80; hardcoded map is backward-compat fallback only |
| FILE47-2 | logic | ✅ RESOLVED (ALREADY_FIXED) | orders_service.py:128-135, 420-430 | bulk rejects refunded via 409 guard; single includes in tuple then 409 | Identical 409 behavior | Both bulk_update_order_status_admin and update_order_status raise HTTPException(409) for "refunded" — behaviorally identical |
