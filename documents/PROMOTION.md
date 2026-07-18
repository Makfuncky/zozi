
### Promotion Engine Overview
A single, modular promotion engine that supports **tiered order discounts**, **referral points**, **campaign coupons**, **supplier-funded promotions**, **buy-one-get-one (BOGO)**, **flash sales**, and **loyalty programs**. It is deterministic, auditable, scalable, and easy for Admins to configure and monitor. Promotions are separate from commission and logistics and recorded in a **Promotion Ledger**. The engine uses a rules-based architecture for flexibility and real-time application at checkout.

### Implementation Status (April 2026)
The following parts are now implemented in code:

- **Admin Promotion Builder panel** in web admin (`/admin/promotions?section=builder`) with:
  - master ON/OFF controls
  - stacking mode control
  - numeric controls (points, caps, delays)
  - percentage controls (max discount percent)
  - amount controls (max discount amount)
  - tier CRUD editor (add/edit/delete/toggle/sort)
  - live discount preview calculator
- **Backend Promotion Builder APIs** under `/admin/promotions/*`:
  - `GET /admin/promotions/config`
  - `PUT /admin/promotions/config`
  - `GET /admin/promotions/tiers`
  - `POST /admin/promotions/tiers`
  - `PUT /admin/promotions/tiers/{tier_id}`
  - `DELETE /admin/promotions/tiers/{tier_id}`
  - `POST /admin/promotions/preview`
- **Persistence models**:
  - `promotion_engine_configs`
  - `promotion_order_tiers`
  - `promotion_ledger_entries`
- **Checkout integration (phase 1)**:
  - order-tier discount is applied server-side during order pricing when `engine_enabled=true` and `allow_order_tier_discounts=true`
  - order-tier application writes to `promotion_ledger_entries`
  - default config keeps engine **OFF** to avoid behavior regressions until Admin enables it

Current scope is **order-tier engine + admin controls**. Product/category coupon unification, referral awarding workflow, supplier co-funding split accounting, and full promotion line-item breakdown in checkout response are planned next phases.

**Key Principles**
- **Modularity**: Each promotion type is a pluggable module.
- **Determinism**: Consistent application across all orders.
- **Auditability**: Full ledger for every application.
- **Scalability**: Handles high-volume orders with caching and async processing.
- **Integration**: Works with inventory, shipping, and payment systems.

---

### Engine Architecture
The promotion engine is built as a microservice within the backend, using Python with FastAPI for APIs. It consists of:

- **Rules Engine**: Uses a custom rules evaluator (inspired by Drools) to apply promotions based on conditions.
- **Promotion Evaluator**: Core service that takes cart/order data and applies eligible promotions in precedence order.
- **Ledger Service**: Records all applications immutably.
- **Fraud Detection Module**: Integrates with ML models for anomaly detection.
- **Admin API**: RESTful endpoints for CRUD on promotions.
- **Customer API**: Endpoints for applying coupons, redeeming points.

**Data Flow**
1. Cart/Order data sent to evaluator.
2. Fetch active promotions from DB/cache.
3. Evaluate rules in precedence order.
4. Apply stacking/best-only logic.
5. Calculate final discount.
6. Record in ledger.
7. Return applied promotions to frontend.

**Caching**: Redis for active promotions and user points balance.
**Async Processing**: Background jobs for ledger writes and fraud checks.

---

### Promotion Rules and Priority
| **Rule Level** | **Applies To** | **Precedence** | **Notes** |
|---|---|---:|---|
| **Product Coupon** | Specific SKU | 1 (highest) | Overrides category and order-level promotions |
| **Category Coupon** | Product category | 2 | Applies when no product coupon |
| **BOGO** | Buy X get Y free | 3 | Applies to qualifying items |
| **Flash Sale** | Time-limited discounts | 4 | Highest discount wins |
| **Order Tier Discount** | Order value thresholds | 5 | Applies once per order; stack rules configurable |
| **Referral Reward** | Referrer and Referee | 6 | Applied after order validation |
| **Supplier Promotion** | Supplier-funded discounts | 7 | Can override or co-fund other promotions |
| **Loyalty Program** | Points-based rewards | 8 | Cumulative benefits |
| **Global Coupon** | Sitewide campaigns | 9 (fallback) | Lowest precedence |

**Application logic**: Evaluate in precedence order; allow either **stacking** (multiple promotions combined) or **best-only** (apply the single best discount) — Admin chooses per campaign. For conflicting promotions, use precedence; for BOGO, apply to cheapest qualifying item first.

---

### Order Tier Discounts (Your thresholds tuned)
| **Order Value** | **Discount** |
|---:|---:|
| 10 OMR ≤ order < 25 OMR | **0.500 OMR** off |
| 25 OMR ≤ order < 50 OMR | **1.500 OMR** off |
| 50 OMR ≤ order < 100 OMR | **4.000 OMR** off |
| order ≥ 100 OMR | **Custom % or fixed** (Admin sets) |

**Rules**
- Discount is applied at checkout after coupons but before taxes/shipping.  
- Discounts are **non‑refundable** unless Admin reverses.  
- Admin can set whether discounts are **visible** to customers as "You saved X" or shown as line item.

---

### BOGO Promotions
**Types**
- Buy 1 Get 1 Free (B1G1)
- Buy 2 Get 1 Free (B2G1)
- Custom ratios

**Rules**
- Applies to specific products or categories.
- Free item is the cheapest qualifying item.
- Can stack with other promotions if allowed.
- Inventory check: Ensure free item is in stock.

**Example**: Buy any 2 items from category "Electronics", get the cheaper one free.

---

### Flash Sales
**Features**
- Time-limited discounts (e.g., 1 hour, 24 hours).
- High discount percentages (up to 70%).
- Limited stock or quantity.

**Rules**
- Countdown timer on product pages.
- Automatic end when time expires or stock depleted.
- No stacking with other discounts unless specified.
- Notification via email/SMS to subscribers.

**Example**: 50% off all laptops for the next 2 hours.

---

### Referral Points System
| **Event** | **Points** | **Conversion** |
|---|---:|---:|
| Successful referral (referee completes first paid order) | **100 points** to referrer; **100 points** to referee | **1,000 points = 1 OMR** redeemable on purchases |
| Points expiry | Configurable (recommend 12 months) | Points expire if unused |
| Max monthly reward cap | Configurable (recommend 20 referrals/month) | Prevents abuse |

**Redemption rules**
- Points can be used as partial payment at checkout.  
- Minimum redemption threshold: **1,000 points** (1 OMR).  
- Points cannot be converted to cash; only applied to orders.  
- Points ledger records `event_id`, `user_id`, `points`, `source`, `expiry_date`.

---

### Loyalty Program
**Tiers**
- Bronze: 0-500 points
- Silver: 501-1000 points
- Gold: 1001+ points

**Benefits**
- Bronze: 5% extra points on purchases
- Silver: 10% extra points + free shipping on orders >50 OMR
- Gold: 15% extra points + priority support

**Rules**
- Points earned on every purchase (1 point per 1 OMR spent).
- Tier upgrades automatic.
- Annual reset or cumulative.

---

### Fraud Prevention and Safeguards
| **Risk** | **Mitigation** |
|---|---|
| Fake accounts to claim referral | Require email + phone verification; first order must clear payment and not be refunded within X days |
| Self-referral using multiple accounts | Block same IP/device patterns; require unique payment method for referee; ML-based clustering |
| Coupon stacking abuse | Admin sets stacking rules per campaign; default: best-only for order-tier discounts |
| Points farming | Cap points per referrer per month; flag unusual referral velocity for review; anomaly detection |
| Supplier collusion | Supplier-funded promotions require signed agreement and audit trail |
| Flash sale bots | Rate limiting, CAPTCHA, stock depletion checks |
| BOGO manipulation | Limit to one per customer; inventory validation |

**Advanced Safeguards**
- **ML Models**: Train on historical data to detect fraudulent patterns (e.g., unusual referral networks).
- **Real-time Monitoring**: Alerts for high-volume coupon redemptions.
- **IP Geolocation**: Block VPNs or suspicious locations.
- **Device Fingerprinting**: Track device IDs for multi-account detection.

**Verification steps**: Payment confirmation, shipping address uniqueness, KYC for high-value redemptions, behavioral analysis.

---

### UI Elements and Admin Controls
**Customer Dashboard**
- **Referral Card**: shows referral code/link, share buttons, referrals count, points balance, next reward milestone.  
- **Rewards History**: list of earned and redeemed points with expiry.  
- **Available Coupons**: active coupons and expiry.

**Admin Dashboard**
- **Promotion Builder**: create product/category/order/referral/supplier promotions; set stacking rules; set effective dates.  
- **Tier Editor**: edit order thresholds and discount amounts.  
- **Points Manager**: view points ledger, adjust points, set expiry policy.  
- **Fraud Monitor**: alerts, flagged accounts, IP/device clustering.  
- **Campaign Analytics**: conversion, CAC, LTV uplift, referral ROI.

**Checkout UX**
- Show applied promotions line-by-line; show points applied and remaining balance; show final payable amount.

---

### Promotion Ledger Schema (essential fields)
`promotion_id`, `type`, `applied_to`, `user_id`, `order_id`, `discount_amount`, `points_awarded`, `points_redeemed`, `source`, `stacking_flag`, `created_at`, `expires_at`, `admin_id`, `adjusted_flag`.

---

### Technical Implementation Details

**Database Schema**
- **promotions** table: Stores promotion definitions (id, type, rules JSON, active, dates).
- **promotion_applications** table: Ledger entries (as above).
- **user_points** table: Current points balance per user.
- **points_transactions** table: Detailed points history.

**APIs**
- `POST /promotions/apply`: Apply promotions to cart/order.
- `GET /promotions/active`: List active promotions for user.
- `POST /admin/promotions`: Create/update promotions.
- `POST /points/redeem`: Redeem points.

**Integration Points**
- **Checkout Service**: Calls promotion engine before payment.
- **Order Service**: Updates ledger post-order.
- **Inventory Service**: Checks stock for BOGO/flash sales.
- **Notification Service**: Sends alerts for flash sales, points expiry.

**Testing**
- Unit tests for rules engine.
- Integration tests with mock carts.
- Load testing for high-traffic flash sales.
- A/B testing framework for campaign optimization.

**Performance**
- Cache active promotions in Redis.
- Async ledger writes using Celery.
- Horizontal scaling for peak times.

---

### KPIs and Measurement
- **Referral Conversion Rate** = referees who complete first purchase / referral clicks.  
- **Cost per Acquisition (CPA)** from referrals = total referral cost / new customers.  
- **Average Order Value (AOV)** uplift from promotions.  
- **Redemption Rate** of points.  
- **Fraud Rate** = flagged events / total referral events.  
- **ROI** per campaign = incremental gross margin from referred orders − promotion cost.

---

### Campaign Examples and Playbook
**Welcome Boost**
- New user gets **100 points** + **10% off first order** (max 10 OMR). Points unlock after first paid order clears.

**Order Tier Nudge**
- Show “Spend 15 OMR more to get 4 OMR off” banner; use A/B test to tune thresholds.

**Referral Sprint**
- Limited 30‑day campaign: referrer gets **2 OMR** for each successful referral (instead of 1 OMR) for first 100 referrers; cap 10 per user.

**Supplier Co‑funded Promo**
- Supplier pays 50% of discount for a 2‑week campaign; Admin sets supplier share and ledger records supplier contribution.

---

### Rollout Plan (90/180/360)
**Phase 1: Core Engine (0–90 days)**
- Implement rules engine, order tier discounts, referral points, basic coupons.
- Build ledger, fraud checks (basic).
- Integrate with checkout.
- Pilot to 1,000 users; monitor KPIs.

**Phase 2: Advanced Features (90–180 days)**
- Add BOGO, flash sales, loyalty program, supplier co-funding.
- Enhance fraud prevention with ML.
- Admin dashboard full build.
- Scale to 10,000 users; A/B test promotions.

**Phase 3: Optimization & Scale (180–360 days)**
- Real-time analytics, automated campaign optimization.
- Full integration with inventory/shipping.
- Global expansion support.
- Enterprise features: bulk promotions, API for partners.

**Dependencies**
- Backend team for engine development.
- Data team for ML fraud detection.
- QA for extensive testing.
- Marketing for campaign design.

---

### Final Recommendations
- Use **dual incentives**: small immediate discount for referee + points/cashback for referrer.  
- Keep **order-tier discounts** simple and visible to nudge AOV.  
- Enforce **strong verification** for referral rewards to prevent abuse.  
- Track everything in **Promotion Ledger** for auditability and supplier reconciliation.  
- Start with a **small pilot** and iterate using KPI-driven A/B tests.

---



### Promotion Builder Settings for Admin

**Purpose** Configure, launch, and audit promotions (order tiers, coupons, referral points, supplier co‑funding) from one builder.

#### Builder Layout and Controls
- **Campaign Name** — text; required.  
- **Campaign Type** — dropdown: *Order Tier Discount; Product Coupon; Category Coupon; Referral Bonus; Supplier Co‑funded*.  
- **Status** — toggle: *Draft / Active / Paused / Ended*.  
- **Effective Dates** — start date; end date; timezone.  
- **Audience** — dropdown: *All customers; New customers only; Specific segments (by tag)*.  
- **Stacking Rule** — radio: *Best Only; Stack All; Custom (select allowed types)*.  
- **Max Uses** — numeric per user; global cap.  
- **Fraud Controls** — toggles: *Require phone verification; Block same IP/device; Minimum payment method uniqueness*.  
- **Notes** — free text for audit reason.

#### Discount Configuration Fields
- **Discount Type** — radio: *Fixed amount; Percentage; Points*.  
- **Value** — numeric (e.g., 4.00 OMR or 10%).  
- **Apply To** — dropdown: *Order total; Specific SKU; Category; Shipping*.  
- **Min Order Value** — numeric threshold.  
- **Combinable With** — checkboxes for coupon, referral, supplier co‑funded.  
- **Supplier Contribution** — numeric % or fixed amount (for supplier‑funded campaigns).  
- **Preview** — live calculator showing sample orders and resulting discount.

#### Referral Points Configuration
- **Points per Event** — e.g., 100 points for successful referral.  
- **Referrer Reward** — choose: *Points; Fixed credit; Coupon*.  
- **Referee Reward** — choose: *Points; Discount on first order*.  
- **Points Conversion** — e.g., 1,000 points = 1 OMR.  
- **Redemption Rules** — min points to redeem; partial redemption allowed toggle.  
- **Expiry** — points validity in months.  
- **Monthly Cap** — max referrals rewarded per referrer.  
- **Verification Delay** — days to wait before awarding (to avoid refunds abuse).

#### Order Tier Editor (preconfigured thresholds)
- **Tier Rows** editable:
  - **Tier Name** — e.g., Tier A.  
  - **Min Order** — 10 OMR.  
  - **Max Order** — 24.99 OMR.  
  - **Discount** — 0.50 OMR.  
  - **Stacking Allowed** — yes/no.  
- **Default Tiers** (editable):  
  - 10–24.99 OMR → **0.50 OMR** off.  
  - 25–49.99 OMR → **1.50 OMR** off.  
  - 50–99.99 OMR → **4.00 OMR** off.  
  - ≥100 OMR → admin sets % or fixed.

#### Coupon Builder Quick Options
- **Code** — auto‑generate or custom.  
- **Single Use / Multi Use** toggle.  
- **Auto Apply** toggle for targeted campaigns.  
- **Visibility** — show on product pages or hidden.

---

### Promotion Ledger and Data Model

**Purpose** Immutable record of every promotion application for audit, finance reconciliation, and fraud review.

**Essential Fields**
- **promotion_id**  
- **campaign_name**  
- **type** (order_tier, coupon, referral, supplier_cofund)  
- **user_id**  
- **order_id**  
- **discount_amount** (OMR)  
- **points_awarded**  
- **points_redeemed**  
- **supplier_contribution** (OMR)  
- **stacking_flag** (true/false)  
- **applied_rules** (JSON summary)  
- **created_at**  
- **expires_at**  
- **admin_id**  
- **fraud_flag** (enum: none, pending, confirmed)  
- **adjusted_flag** (true/false) and **adjustment_reason**

**Operational Notes**
- Every promotion application writes one ledger row.  
- Supplier contributions are recorded separately for reconciliation.  
- Points ledger is a related table with `event_id`, `user_id`, `points`, `source`, `expiry_date`.

---

### Checkout Flow and UX

**Order Calculation Sequence**
1. Validate coupons and product/category rules.  
2. Apply **Product Coupon** if present.  
3. Apply **Category Coupon** if no product coupon.  
4. Apply **Order Tier Discount**.  
5. Apply **Referral Reward** (if referee).  
6. Apply **Points Redemption** (user choice).  
7. Apply **Supplier Co‑funding** adjustments.  
8. Show final payable amount, line items: *Subtotal; Discounts (line by line); Points used; Shipping; Taxes; Total*.

**Customer UI Elements**
- **Referral Card** (prominent in account and checkout): shows code, share buttons, points balance, progress to next tier.  
- **Savings Banner**: “You saved 4.00 OMR on this order” with breakdown.  
- **Points Redemption Widget**: slider or input to choose points to apply.  
- **Promotion Preview**: before checkout show “If you add X OMR more, you’ll unlock Y discount.”

---

### Fraud Prevention Rules

**Automated Checks**
- Require phone verification for referee before awarding.  
- Delay awarding referral reward until first order is non‑refunded for `n` days.  
- Block rewards for same IP/device clusters beyond threshold.  
- Flag rapid referral velocity for manual review.

**Manual Controls**
- Admin can quarantine suspicious rewards and reverse ledger entries.  
- Reports for unusual patterns: high refunds among referees, many referrals from same device.

---

### Customer Facing Referral Card Copy

**Header** Invite friends, earn rewards  
**Body** Share your code **`MHD123`**. When a friend makes their first purchase using your code, you both get **100 points** and the friend gets **10% off** their first order.  
**CTA Buttons** Share via WhatsApp; Share via SMS; Copy Code  
**Progress** You have **300 points**. Redeem at checkout. **1,000 points = 1 OMR**.  
**Footer** Points expire in 12 months. Max 20 rewarded referrals per month.

---

### Campaign Examples and Templates

**Welcome Boost Template**
- **Type** Referral + Order Tier  
- **Referrer** 100 points per successful referral.  
- **Referee** 10% off first order (max 10 OMR).  
- **Verification** Phone + payment confirmation; 7‑day hold for refunds.

**AOV Nudge Template**
- **Type** Order Tier  
- **Message** “Add 15 OMR more to save 4.00 OMR.”  
- **Stacking** Best Only.  
- **Target** Users with AOV in bottom 30%.

**Referral Sprint Template**
- **Type** Referral (time‑limited)  
- **Referrer** 2 OMR credit for first 10 referrals in 30 days.  
- **Cap** 10 per user.  
- **Fraud** stricter verification.

**Supplier Co‑funded Template**
- **Type** Supplier Co‑funded Coupon  
- **Split** Supplier pays 50% of discount; ZoZi pays 50%.  
- **Ledger** Record supplier contribution per order for reconciliation.

---

### KPIs to Monitor

- **Referral Conversion Rate** = referees who complete first purchase / referral clicks.  
- **Cost per Acquisition from Referrals** = total referral cost / new customers.  
- **AOV Uplift** from promotions.  
- **Points Redemption Rate** = points redeemed / points issued.  
- **Fraud Rate** = flagged events / total referral events.  
- **Supplier ROI** on co‑funded promotions.

---

### Rollout Plan

**Phase 1 Pilot (0–30 days)**  
- Implement referral code generation, points ledger, order tier discounts, basic fraud checks.  
- Soft launch to 1,000 users.

**Phase 2 Scale (30–60 days)**  
- Add supplier co‑funding, stacking rules, admin analytics, and automated fraud quarantines.

**Phase 3 Optimize (60–90 days)**  
- A/B test thresholds and messages, introduce tiered referral bonuses, automate supplier reconciliation.

---

### Future Enhancements
- **AI-Driven Personalization**: Use customer data to auto-suggest promotions.
- **Omnichannel Support**: Apply promotions across web, mobile, in-store.
- **Blockchain for Ledger**: Immutable records using blockchain for high-security audits.
- **Dynamic Pricing**: Adjust prices based on demand and promotions.
- **Gamification**: Turn loyalty into a game with badges, levels.
- **Sustainability Promotions**: Discounts for eco-friendly purchases.

---

