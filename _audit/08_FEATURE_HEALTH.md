# FEATURE HEALTH

> **Derived from:** `dimensions/16_features.md`
> **Compiled:** 2026-10-01

## Summary

- Confirmation: ❌
- Files inspected: 42
- Files compliant: 0
- Files with findings: 42
- Laws implicated: [L-2, L-3, L-5, L-6, L-14, L-19, L-23, L-30, L-31, L-34, L-42, L-45, L-50, L-54, L-55, L-69, L-70, L-72, L-87, L-88, L-90, L-96, L-102a, L-120a, L-123, L-227, L-228, L-229]
- Findings: 42
- P0: 8  P1: 14  P2: 12  P3: 8
- Clusters: 6
- Average confidence: 4/5
- Average evidence strength: multiple
- Status: NEW: 42 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 8 yes · 6 partial · 28 no

## Overall Assessment

### Problem(s)
1. **Float arithmetic in money paths** (FEAT-001, FEAT-002, FEAT-003, FEAT-009, FEAT-010): Multiple locations use `float` for monetary calculations instead of `Decimal`, violating Laws 19, 227, 228 and risking rounding errors in cart totals, order serialization, and tax computation.
2. **Missing inventory claim/release** (FEAT-004, FEAT-025): `INVENTORY_HELD_STATUSES` constant is defined but no inventory claim/release calls are wired into the order creation or cancellation flows, risking oversell.
3. **Plaintext payment credentials** (FEAT-005, FEAT-022): `PaymentGatewayConnection.credentials` and `secret_key`/`webhook_secret` columns store gateway credentials as plain JSON/text, violating Laws 32, 120a and the platform's own field-encryption requirement.
4. **Module-level secret assignment** (FEAT-006): `stripe.api_key` is set at module import time in `payment_engine.py`, creating side effects and making secret rotation impossible without restart.
5. **Return/refund auto-issue** (FEAT-011): Refund is auto-issued when return status changes to `completed` without separate authorization or `finance.ledger.write` gate, creating fraud risk.
6. **Order status machine drift** (FEAT-021): DB check constraint allows statuses (`pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled`, `returned`) but service allows extra statuses (`prepared`, `picking_up`, `failed`, `refunded`), causing runtime constraint violations.
7. **Archived module still imported** (FEAT-016): `promotions_write_service.py` and `promotion_engine_service.py` are marked `ARCHIVED MODULE` but remain in the import path, risking dead code execution.
8. **Hardcoded geo fallback** (FEAT-017): `_get_geo_info` returns hardcoded Dubai coordinates when cache misses, masking real IP geolocation and weakening fraud detection.

### Solution(s)
1. Replace all `float` money arithmetic with `Decimal` using `kernel.money.round_money` and `Decimal.quantize` across cart totals, order serialization, product pricing, and tax calculation.
2. Wire `claim_inventory` into order confirmation flow and `release_inventory` into cancellation/refund flow; ensure transactional consistency.
3. Encrypt all payment gateway credentials, secret keys, and webhook secrets via `infrastructure/security/field_encryption.py` before database persistence; add migration for existing rows.
4. Move all provider SDK secret resolution inside function bodies; remove module-level `stripe.api_key` assignment.
5. Gate refunds behind explicit `refund` action with `finance.ledger.write` feature check; remove auto-refund on return completion.
6. Align DB check constraint with service `valid_statuses`; add Alembic migration to update `chk_orders_status_valid`.
7. Remove archived promotion modules from import paths; consolidate into live `domains/promotions/services/engine/` package.
8. Replace hardcoded geo fallback with actual GeoIP provider call or `None`/`unknown` sentinel.

### Suggestion(s)
1. Add architecture test enforcing `Decimal` for all money columns in serialization paths (Law 19).
2. Add integration test for inventory claim/release lifecycle covering confirm→cancel→refund.
3. Add E2E test for cross-border checkout with tax calculation validation.
4. Run `import-linter` to catch any remaining cross-domain imports from archived modules.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Replace float money math with Decimal in cart totals, order serialization, product pricing, tax calc | FEAT-001, FEAT-002, FEAT-003, FEAT-009, FEAT-010 | yes | L (8h) | 5 |
| P0 | Encrypt payment gateway credentials and secret keys at rest | FEAT-005, FEAT-022 | yes | L (8h) | 5 |
| P0 | Wire inventory claim/release into order status transitions | FEAT-004, FEAT-025 | yes | L (8h) | 4 |
| P0 | Remove module-level `stripe.api_key` assignment; resolve at call time | FEAT-006 | yes | M (3h) | 5 |
| P0 | Gate refunds behind explicit action + finance.ledger.write feature | FEAT-011 | partial | M (3h) | 4 |
| P0 | Align order status DB constraint with service valid_statuses | FEAT-021 | partial | M (3h) | 5 |
| P1 | Add audit_log to admin shipment status override in logistics | FEAT-036 | no | M (2h) | 4 |
| P1 | Verify JWT type claim enforcement in rbac/dependencies.py | FEAT-033 | no | M (2h) | 3 |
| P1 | Verify media schema RLS policies exist | FEAT-020 | partial | M (3h) | 3 |
| P1 | Verify promotion stacking enforcement in engine | FEAT-030 | no | M (3h) | 3 |
| P1 | Add return/refund integration tests | FEAT-023 | no | M (3h) | 4 |
| P1 | Verify category tree rebuild uses batch update | FEAT-041 | no | M (2h) | 3 |
| P1 | Verify KYC tier enforcement per country | FEAT-035 | no | M (3h) | 3 |
| P1 | Add MIME validation test for media uploads | FEAT-034 | no | M (2h) | 3 |
| P1 | Run and verify all Playwright money-path specs | FEAT-042 | partial | M (3h) | 3 |
| P2 | Move payment idempotency TTL to config | FEAT-007 | no | S (1h) | 4 |
| P2 | Add idempotency key to cart sync endpoint | FEAT-026 | no | M (2h) | 3 |
| P2 | Verify RLS on CountryConfig does not block admin reads | FEAT-038 | no | S (1h) | 3 |
| P2 | Return structured coupon error instead of silent zero | FEAT-039 | no | S (1h) | 4 |
| P2 | Verify payout sweep filters by settlement_hold_days | FEAT-018 | no | M (3h) | 3 |
| P2 | Add NO DELETE trigger on permission_audit_log | FEAT-019 | no | L (8h) | 4 |
| P2 | Verify search graceful degradation under provider failure | FEAT-027 | no | S (1h) | 5 |
| P2 | Verify fraud bloom filter graceful fallback | FEAT-032 | no | S (1h) | 5 |
| P2 | Verify return window uses per-product value | FEAT-037 | no | S (1h) | 5 |
| P3 | Verify payment methods country routing | FEAT-029 | no | S (1h) | 5 |
| P3 | Verify soft delete on Order model | FEAT-028 | no | S (1h) | 5 |
| P3 | Remove bare except in email enqueue | FEAT-024 | no | S (1h) | 4 |
| P3 | Verify commission cap precision edge case | FEAT-012 | no | S (1h) | 4 |
| P3 | Migrate CommissionGroup/CommissionRule to single domain schema | FEAT-031 | no | L (8h) | 3 |
| P3 | Verify RLS context scalar binding in set_rls_context | FEAT-013 | partial | M (3h) | 4 |
| P3 | Verify ledger tax calculation Decimal input | FEAT-040 | yes | M (3h) | 4 |
| P3 | Remove archived promotion modules from import paths | FEAT-016 | partial | M (3h) | 5 |
