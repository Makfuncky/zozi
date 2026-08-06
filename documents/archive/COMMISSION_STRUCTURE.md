# Commission System Blueprint

## Purpose

This document defines the canonical Zozi commission model for:

- Admin management in the Admin Panel Commission page
- Commission calculation during order processing
- Supplier settlement and payout calculation in Finance
- Immutable auditability through a dedicated commission ledger

The target model is deterministic, category-aware, badge-backed, and finance-safe.

## Executive Summary

Zozi uses a single hybrid commission model:

1. Admin override
2. Category rate
3. Badge rate
4. Global default
5. Low-value cap

This keeps the system predictable for Admins, understandable for suppliers, and safe for payout calculations.

## Canonical Algorithm

### Rate Resolution Order

For each supplier order item, resolve the commission rate `r` in this order:

1. If an active supplier-level admin override exists, use that rate.
2. Else if an active category rate exists for the product category, use that rate.
3. Else use the supplier badge tier rate.
4. Else use the global default rate.

### Commission Formula

Percentage commission before cap:

$$
C_{pct} = r \times order\_value
$$

Low-value cap rule:

$$
If\ order\_value < LowValueThreshold,\ then\ C = \min(C_{pct}, FixedCap)
$$

Recommended defaults:

- `LowValueThreshold = 5.00 OMR`
- `FixedCap = 0.500 OMR`

### Canonical Precedence Summary

Admin override -> Category rate -> Badge rate -> Global default -> Low-value cap

## Default Category Rates

All the System should not be fixed and should be editable by the Admin in commision page but the recommended starting rates by category are:

| Category | Default Rate | Rationale |
|---|---:|---|
| Electronics | 8% | High ticket, margin-sensitive |
| Fashion | 14% | Mid margin, promotion-friendly |
| Accessories | 14% | Similar to fashion |
| Furniture | 8% | High ticket, margin-sensitive |
| Beauty | 12% | Mid margin, frequent campaigns |
| Sports | 12% | Mid margin |
| Home and Living | 10% | Mixed margin profile |
| Books | 6% | Low margin, price-sensitive |
| Baby and Kids | 12% | Stable mid margin |
| Automotive | 8% | High ticket, lower percentage needed |
| Crafts | 18% | Higher margin, lower volume |
| Grocery | 5% | Very low margin |

Global fallback rate when no category rule and no badge rule apply:

- `15%`

## Badge Tiers And Supplier Fees

Suppliers pay for badge access. Badge fees and badge commission rates are finance-managed and market-configurable.

| Badge | Setup Fee | Recurring Fee | Commission | Benefits |
|---|---:|---:|---:|---|
| None | 0.000 OMR | 0.000 OMR | 16% | Basic listing, monthly payouts |
| Bronze | 25.000 OMR | 0.000 OMR | 15% | Standard listing, basic analytics |
| Silver | 50.000 OMR | 5.000 OMR/month | 12% | Priority placement, weekly payouts |
| Gold | 100.000 OMR | 10.000 OMR/month | 10% | Featured promos, advanced analytics |
| Platinum | 200.000 OMR | 20.000 OMR/month | 8% | Next-day payouts, account manager |
| Membership | Custom | Custom | Custom | Negotiated benefits and rates |

### Badge Qualification Reference

- Bronze: verified supplier baseline
- Silver: `>= 50` fulfilled orders or `>= 2,000 OMR/month`
- Gold: `>= 200` fulfilled orders or `>= 10,000 OMR/month`
- Platinum: `>= 500` fulfilled orders or `>= 25,000 OMR/month`

Badge qualification is policy data. Badge fees are commercial data. Both are editable by Finance Admins.

## Margin Protection Rule

Margin protection is optional and should only auto-apply when Zozi has a reliable estimated supplier margin input.

Recommended policy:

- If estimated supplier margin is below `10%`, prefer a lower category rate or a negotiated fixed-fee arrangement.
- If no margin data source exists, Finance Admins should manage exceptions with category rates or supplier overrides instead of automatic enforcement.

This keeps the rule honest. A toggle without margin data should not pretend to make a real financial decision.

## Admin Panel Design

### Page Goal

The Admin Panel Commission page must let Finance Admins manage the full commission system without needing direct database access.

### Top-Level Tabs

1. Global Rate
2. Category Rates
3. Supplier Overrides
4. Badge Tiers
5. Preview Calculator

### Required Sections

#### Global Rate

- Global default rate
- Low-value threshold
- Fixed cap amount
- Fixed cap enabled toggle
- Margin protection toggle
- Margin threshold

#### Category Rates

- Inline editable category table
- Rate
- Active toggle
- Notes

#### Supplier Overrides

- Supplier search/list
- Current effective supplier baseline
- Manual override entry
- Reason or note

#### Badge Tiers

- Badge name
- Commission rate
- Setup fee
- Recurring fee
- Recurring interval
- Benefits
- Qualification thresholds

#### Preview Calculator

- Supplier ID
- Order value
- Category slug
- Output applied rate
- Output calculation method
- Output cap usage
- Output ledger preview summary

### Operational Visibility

The page should also expose:

- Recent commission ledger entries
- Recent audit activity for commission changes

This is necessary for Finance Admins to validate live behavior after changing rates.

## Commission Ledger Requirements

Commission calculation must persist immutable records at order-item level.

### Required Fields

- `ledger_id`
- `order_id`
- `order_item_id`
- `supplier_id`
- `product_id`
- `category_slug`
- `badge_level`
- `global_default_rate`
- `category_rate`
- `badge_rate`
- `override_rate`
- `applied_rate`
- `calculation_method`
- `order_value`
- `commission_pct`
- `cap_applied`
- `commission_amount`
- `low_value_threshold_used`
- `fixed_cap_used`
- `override_flag`
- `currency`
- `created_at`

### Adjustment Rule

Disputes must be handled as adjustments with auditability. Finance operations must never silently erase commission history.

## Order System Integration

### Trigger Point

The commission engine runs when ledger entries are created for confirmed orders.

### Calculation Scope

- Resolve commission per order item
- Persist one commission ledger row per order item
- Aggregate item commissions into supplier-facing transaction ledger totals

### Finance Safety

The supplier transaction ledger must store the blended effective commission rate for the supplier slice of the order, not an arbitrary single item rate.

That ensures:

- Transaction ledger displays are honest
- Supplier settlements show the true realized commission percentage
- Payout decisions use the same totals Finance sees in Admin

## Finance And Payout Integration

Supplier payouts must be derived from the same transaction ledger and settlement records created during order finance processing.

### Supplier Settlement Logic

For each delivered order supplier slice:

- Gross amount = product subtotal minus discount share
- Commission deducted = actual commission total from transaction ledger
- VAT on commission = policy VAT rate applied to commission
- Net amount = gross minus commission minus any allocated gateway fee deductions

### Finance Page Expectations

The Finance page should show:

- Transaction ledger rows
- Supplier settlements
- Commission amount deducted
- Effective commission rate snapshot
- Net supplier payable amount

This keeps the Commission page and Finance page aligned.

## Billing For Badge Purchases

Suppliers pay badge fees as part of their commercial plan.

### Required Flow

1. Supplier selects badge plan
2. Supplier pays setup fee and recurring fee if applicable
3. System records badge billing event
4. Badge becomes active after approval or verification
5. Badge commission rate becomes part of commission resolution when no higher-priority rule exists

### Finance Rules

- Badge fees are supplier-borne
- Refunds or manual adjustments must be logged
- Badge billing should appear in supplier billing history or statements

## Governance Rules

- Only Finance Admins may change commission rules
- Every change must include a reason or note where applicable
- Every change must produce an audit log entry
- Category rates should be reviewed quarterly
- Badge fees and tier benefits should be reviewed by market

## KPI Monitoring

Monitor at minimum:

- Average commission percentage
- Supplier churn
- Supplier badge upgrades
- Commission disputes per 1,000 orders
- Category margin impact
- Price competitiveness against key competitors

## Example Calculations

- Electronics order `500 OMR` at `8%` -> `40 OMR`
- Grocery order `2.50 OMR` at `5%` -> `0.125 OMR`
- Books order `4.00 OMR` at `6%` -> `0.240 OMR`
- Accessories order `20 OMR`, Silver supplier `12%`, category `14%` -> category wins -> `2.800 OMR`
- Micro order `1.00 OMR`, Bronze supplier `15%` -> `0.150 OMR`, cap not binding

## Rollout Checklist

1. Seed global config, category rates, and badge tiers.
2. Verify commission API endpoints.
3. Validate Admin Commission page editing flow.
4. Confirm order confirmation creates commission ledger rows.
5. Confirm delivered orders create supplier settlements with correct commission totals.
6. Pilot with a limited supplier cohort and review KPIs.

## Final Recommendation

Zozi should operate a category-first commission engine with badge-backed supplier incentives, admin override control, immutable commission ledgering, and payout-safe finance integration.

That is the correct balance of competitiveness, operational control, and financial traceability.
