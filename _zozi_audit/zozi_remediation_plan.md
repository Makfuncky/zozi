# ZOZI — Remediation Plan (compiled from the forensic audit)

_Generated 2026-10-02T20:35:12.813694+00:00 from audit run `20261002T201354Z-716f9a` at commit `6666d435a947e61ce63cf238439514a248891063`._

This is the **solution half** of the audit. The audit states what is wrong; this states what to do, in what order, and how to prove each step is finished.

## How to use this plan

1. Work **wave by wave**. A wave may only start when the previous wave is green — this is what makes the result trustworthy rather than merely different.
2. Wave 0 is the gate: until it passes, no other verification means anything.
3. Each step carries its own `verify` command. Run it. A step whose verification does not change is not done.
4. Steps marked **verify** are *not* instructions to change code. They are claims the audit could not confirm statically; confirm or dismiss them first.
5. Steps marked **improve** are recommendations. They never gate a release.
6. Mark progress with `--status`; the compiler round-trips it.

## Verification gate

- Findings adjudicated: **17.8% independently confirmed**
- False positives + wrong locations: **7.1%**
- Not actionable as stated (incl. already fixed): **10.4%**
- P0 noise (false or mislocated): **6.4%**

A low *confirmed* share is expected and is not a defect: a claim with no independent re-check cannot honestly be called confirmed. It is routed to a verification task instead of being silently trusted.

### How this plan may be followed

1. **Every `fix` step was independently re-derived** before it reached this document. Nothing else is presented as a fix.
2. **A `verify` step is not an instruction to change code.** It is a claim the tooling could not adjudicate; confirm or dismiss it first.
3. **54 finding(s) were rejected outright** (false positive or already fixed) and are listed in the Rejected appendix with counter-evidence. They are not work.
4. **A CONFIRMED verdict proves the claim, not the fix.** The `fix` text still needs engineering review — most of all for law, schema and security changes.

## Totals

- Findings consumed: **1324**
- Findings rejected (false positive / already fixed): **54**
- Confirmed fix steps: **236**
- Recommendations consumed: **20**
- Release-gating steps: **1274** (~2702.0h at S=1h M=2.5h L=6h XL=20h)
- Improvement steps: **20** (not gating)
- Untrusted claims needing verification first: **1027**
- Work packages (the unit of work): **679**

## Work package index

Finish a whole package, not a single line. A package is one cluster touched by one person or one agent, with a single coherent outcome.

| Wave | Package | Steps | Files | Est. h | Focus |
|------|---------|-------|-------|--------|-------|
| 0 | `WP0-PREFLIGHT` | 4 | 0 | 10.0 | Architecture tests -> INCOMPLETE |
| 0 | `WP0-BOOT-PREFLIGHT` | 1 | 1 | 1.0 | Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: Co… |
| 0 | `WP0-TEST-BROKEN` | 6 | 6 | 15.0 | test file cannot be parsed: SyntaxError line 1: invalid non-printable… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 36 float-for-money signal(s); first: `amount: Decimal | float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"]… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 10 float-for-money signal(s); first: `subtotal: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| 1 | `WP1-IDEMPOTENCY` | 1 | 1 | 2.5 | idempotency_key: Optional[str] = None |
| 1 | `WP1-SETTINGS-CONTRACT` | 12 | 8 | 12.0 | settings.NEWS_API_KEY is read but Settings declares no such field |
| 2 | `WP2-HTTP-HEADERS` | 4 | 1 | 4.0 | `/health` is missing none; deprecated headers present: x-xss-protecti… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `discount_value: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.P… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `total_amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `total_duration_ms: Optional[floa… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"]… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.P… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 10 float-for-money signal(s); first: `commission_reserve: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 45 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 74 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `discount_amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 8 float-for-money signal(s); first: `discount_value: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total = float(weight.scalar() or… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 63 float-for-money signal(s); first: `price: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float | None` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total_revenue: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `base_price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `total = float(h * w) if h * w el… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 22 | 1 | 22.0 | 1x rel lazy in table `dynamic_qr_sessions`: relationship `employee` h… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 16 | 1 | 16.0 | 1x rel lazy in table `announcements`: relationship `country` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 15 | 1 | 15.0 | 3x rel lazy in table `country_staff_assignments`: relationship `user`… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 10 | 1 | 10.0 | 1x rel lazy in table `entity_chat_threads`: relationship `messages` h… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-BG` | 9 | 1 | 9.0 | env var `BG_ALLOW_HEAVY_MODELS` read but not declared in .env.example… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 7 | 1 | 7.0 | 1x rel lazy in table `payment_orchestrator_syncs`: relationship `coun… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 5 | 1 | 5.0 | 1x rel lazy in table `user_login_histories`: relationship `user` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 5 | 1 | 5.0 | 1x rel lazy in table `logistics_partner_profiles`: relationship `part… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 4 | 1 | 4.0 | env var `DB_SEARCH_PATH` read but not declared in .env.example, typed… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 4 | 1 | 4.0 | env var `AZURE_CLIENT_ID` read but not declared in .env.example, type… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 3 | 1 | 3.0 | env var `BG_REMOVAL_MODEL` read but not declared in .env.example, typ… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-CO` | 3 | 1 | 3.0 | env var `WHATSAPP_MODE` read but not declared in .env.example, typed… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 3.0 | 2x rel lazy in table `product_types`: relationship `coc_category` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 3.0 | 3x rel lazy in table `support_tickets`: relationship `replies` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 3 | 1 | 3.0 | 2x rel lazy in table `fraud_cases`: relationship `assignee` has no la… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 2 | 1 | 2.0 | env var `ML_WORKER_IDLE_SHUTDOWN` read but not declared in .env.examp… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 2 | 1 | 2.0 | env var `AI_USE_OLLAMA_TEXT` read but not declared in .env.example, t… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 2 | 1 | 2.0 | env var `ZOZI_MCP_PASSWORD` read but not declared in .env.example, ty… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 2 | 1 | 2.0 | 1x rel lazy in table `carts`: relationship `user` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 2 | 1 | 2.0 | 1x rel lazy in table `onboarding_steps`: relationship `pipeline` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 2.0 | 2x rel lazy in table `ai_staging_products`: relationship `job` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 2.0 | 1x rel lazy in table `commission_profiles`: relationship `rules` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 2.0 | 4x rel lazy in table `products`: relationship `category_rel` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 2.0 | 2x rel lazy in table `incident_threads`: relationship `war_room` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 2 | 1 | 2.0 | 3x rel lazy in table `country_communications`: relationship `country`… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 2 | 1 | 2.0 | 1x rel lazy in table `supplier_documents`: relationship `supplier` ha… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SECU` | 1 | 1 | 1.0 | env var `ENCRYPTION_SALT` read but not declared in .env.example, type… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1.0 | env var `MEDIA_STORAGE_PATH` read but not declared in .env.example, t… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 1.0 | env var `TURNSTILE_SECRET_KEY` read but not declared in .env.example,… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 1.0 | env var `ZOZI_VAULT_MASTER_KEY` read but not declared in .env.example… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 1.0 | env var `PYTEST_CURRENT_TEST` read but not declared in .env.example,… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 1.0 | env var `MAX_PAGE_SIZE` read but not declared in .env.example, typed… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-JOBS-MCP-MAR` | 1 | 1 | 1.0 | env var `ZOZI_MCP_API_URL` read but not declared in .env.example, typ… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-MAIN-PY` | 1 | 1 | 1.0 | env var `LOG_FILE` read but not declared in .env.example, typed setti… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-C` | 1 | 1 | 1.0 | env var `CSRF_DISABLED` read but not declared in .env.example, typed… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-R` | 1 | 1 | 1.0 | env var `REQUEST_TIMEOUT_SECONDS` read but not declared in .env.examp… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-S` | 1 | 1 | 1.0 | env var `FRONTEND_WS_URL` read but not declared in .env.example, type… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AN` | 1 | 1 | 1.0 | env var `ANALYTICS_API_KEY` read but not declared in .env.example, ty… |
| 3 | `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-SE` | 1 | 1 | 1.0 | env var `WATCHLIST_API_URL` read but not declared in .env.example, ty… |
| 3 | `WP3-HTTP-HEADERS` | 1 | 1 | 1.0 | the security middleware emits X-XSS-Protection (1 site(s)) |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 1x rel lazy in table `email_campaigns`: relationship `recipients` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 1.0 | 2x rel lazy in table `referral_point_events`: relationship `user` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1.0 | 1x rel lazy in table `tax_rules`: relationship `country` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 1.0 | 2x rel lazy in table `logistics_cod_remittance_receipts`: relationshi… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 1x rel lazy in table `coupon_usages`: relationship `country` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 1x rel lazy in table `banners`: relationship `country` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 1 | 1 | 1.0 | 2x rel lazy in table `kyc_verifications`: relationship `user` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 1 | 1 | 1.0 | 1x rel lazy in table `permissions`: relationship `category` has no la… |
| 4 | `WP4-WORKFLOW-RUNTIME` | 10 | 3 | 23.5 | `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_… |
| 4 | `WP4-STUB-SUBSCRIBER` | 4 | 4 | 10.0 | stub subscriber module: 3 handlers, 3 `# Future:` markers |
| 4 | `WP4-PAYMENT-WEBHOOK` | 3 | 3 | 3.0 | payment adapter references webhooks but shows no signature verificati… |
| 4 | `WP4-RLS` | 4 | 4 | 7.0 | canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` e… |
| 4 | `WP4-CONTRADICTION-TARGET-VS-CODE` | 3 | 3 | 7.5 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | back… |
| 4 | `WP4-BROWSER-RUNNER-BROKEN` | 2 | 1 | 12.0 | Playwright run produced no executable tests: ReferenceError: __dirnam… |
| 4 | `WP4-PAYMENT-CREDENTIALS` | 2 | 2 | 3.5 | payment gateway secret columns appear to be plain String (no encrypti… |
| 4 | `WP4-STARTUP` | 2 | 2 | 2.0 | startup logged an error from lifespan/Failed to start backup manager… |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` | 2 | 1 | 5.0 | 47 endpoint(s) across 13 router(s) have no visible auth/gate dependen… |
| 4 | `WP4-WS-AUTH` | 2 | 1 | 5.0 | websocket `websocket_user` accepts without token verification |
| 4 | `WP4-EVENT-SPINE` | 2 | 2 | 22.5 | 44 of 79 event handlers (44/79) log and return without performing the… |
| 4 | `WP4-AP-TODO-ONLY-IMPLEMENTATION` | 1 | 1 | 2.5 | TODO-only implementation: 151 occurrence(s); sample `backend/domains/… |
| 4 | `WP4-AP-UNIMPLEMENTED-PLACEHOLDER` | 1 | 1 | 2.5 | Unimplemented placeholder: 257 occurrence(s); sample `backend/domains… |
| 4 | `WP4-CHAIN-CHAIN-005` | 1 | 1 | 6.0 | CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 s… |
| 4 | `WP4-CONTRADICTION-DOC-VS-CODE` | 1 | 1 | 2.5 | one router per module: every router file registered | modules/employe… |
| 4 | `WP4-CONTRADICTION-FRONTEND-VS-BACKEND` | 1 | 1 | 2.5 | Law 13 (5 modules): no standalone hr module | frontend/web_app/next.c… |
| 4 | `WP4-EXTRA-MODULE` | 1 | 1 | 2.5 | top-level module `finance` exists |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str,… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"rate": float(rule.rate),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 18 float-for-money signal(s); first: `"total_amount": float(order.tot… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_pr… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converte… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converte… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `"amount": float(converted_total)… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"amount": float(p.amount),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `line_total = float(line.get("qua… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 39 float-for-money signal(s); first: `shipping_amount = float(getattr… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commi… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `total=float(total_amount),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `min_amount: Optional[float]` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `unit_price = float(item.price or… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `min_payout_amount: float` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `entry["amount"] = float(match.gr… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` |
| 4 | `WP4-SSRF` | 1 | 1 | 2.5 | 22 caller-influenced outbound URL call(s) without safe-URL guard; fir… |
| 4 | `WP4-TABLE-DRIFT` | 1 | 1 | 2.5 | migrations reference schemas no ORM model declares: customer(5), comm… |
| 4 | `WP4-UNCATEGORISED-BACKEND` | 1 | 1 | 6.0 | ruff reports 6604 violation(s); top rules: E402=2065, F401=1984, F821… |
| 4 | `WP4-UNCATEGORISED-BACKEND-TESTS-ARCHIT` | 1 | 1 | 6.0 | the architecture-law suite did not finish in 449.55s (exit 1); 50 fai… |
| 4 | `WP4-UNCATEGORISED-FRONTEND-WEB-APP` | 1 | 1 | 6.0 | 119 TypeScript error(s) across 29 file(s) |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | endpoint `get_rbac_catalog` has no visible auth/feature gate |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 27 | 1 | 71.0 | function `serialize_pricing_profile` duplicates `backend/domains/logi… |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 25 | 1 | 62.5 | endpoint `push_notifications_health` has no visible auth/feature gate |
| 4 | `WP4-ALLOWLIST` | 20 | 1 | 50.0 | allowlist entry without dated removal plan: `domains.finance.services… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 20 | 1 | 20.0 | 1x timestamp default in table `transaction_ledgers`: `updated_at` use… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 20 | 1 | 53.5 | function `scan_lookup_shipment` duplicates `backend/domains/logistics… |
| 4 | `WP4-TF-MISSING-COUNTRY-CODE` | 18 | 8 | 18.0 | 1x missing country_code in table `entity_chat_threads`: user-facing t… |
| 4 | `WP4-CIRCULAR-IMPORT` | 17 | 10 | 42.5 | circular package dependency: domains.accounts -> domains.audit -> dom… |
| 4 | `WP4-INFRA-IMPORTS-ABOVE` | 15 | 12 | 37.5 | `infra imports above`: imports `domains` |
| 4 | `WP4-JOB-RESILIENCE` | 14 | 14 | 35.0 | celery task module with no DLQ reference |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-FINA` | 14 | 1 | 35.0 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 14 | 1 | 38.5 | function `get_supplier_bank_account` duplicates `backend/domains/fina… |
| 4 | `WP4-VERSION-DRIFT` | 13 | 4 | 13.0 | `eslint: ^9` does not satisfy pinned `10` |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` | 11 | 1 | 27.5 | function `_fetch_rss` duplicates `backend/domains/analytics/services/… |
| 4 | `WP4-HTTP-CSP` | 10 | 1 | 10.0 | CSP on `/health`: uses report-uri, superseded by report-to |
| 4 | `WP4-TF-FK-ONDELETE` | 10 | 6 | 10.0 | 1x fk ondelete in table `audit_logs`: FK `country_code` has no ondele… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 9 | 1 | 9.0 | 1x timestamp default in table `country_feature_flags`: `updated_at` u… |
| 4 | `WP4-FEATURE-GATE` | 8 | 5 | 9.5 | `require_feature("catalog.review.create")` gates on a feature that no… |
| 4 | `WP4-TF-MISSING-UPDATED-AT` | 8 | 5 | 8.0 | 1x missing updated_at in table `group_chat_members`: table `group_cha… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 8 | 1 | 20.0 | function `is_within_fence` duplicates `backend/domains/country/servic… |
| 4 | `WP4-LAW-CODE-QUALITY` | 7 | 1 | 7.0 | Law 19 (No float for money) violated: 18 Float column(s); 0 float mon… |
| 4 | `WP4-TEST-NO-ASSERT` | 7 | 7 | 17.5 | test file contains no assertions |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-CUST` | 7 | 1 | 17.5 | endpoint `login` has no visible auth/feature gate |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 6 | 1 | 15.0 | cross-domain import `domains.accounts.models.banking` (domains.govern… |
| 4 | `WP4-LAW-ARCHITECTURE` | 6 | 1 | 6.0 | Law 1 (Arrows point down) violated: 33 reverse-layer import(s) |
| 4 | `WP4-SUPPLY-CHAIN` | 6 | 4 | 6.0 | no dependency scanning step in CI |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 6 | 1 | 6.0 | 2x rel lazy in table `fraud_events`: relationship `user` has no lazy= |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 6 | 1 | 6.0 | 2x timestamp default in table `entity_chat_threads`: `created_at` use… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 6.0 | 1x timestamp default in table `logistics_partner_profiles`: `updated_… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` | 6 | 1 | 6.0 | 2x timestamp default in table `supplier_profiles`: `created_at` uses… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 6 | 1 | 15.0 | function `_build_postgres_tsquery` duplicates `backend/domains/catalo… |
| 4 | `WP4-FORBIDDEN-PACKAGE` | 5 | 2 | 5.0 | forbidden package declared: `prometheus-client`==0.26.0 |
| 4 | `WP4-LAW-DATABASE` | 5 | 1 | 5.0 | Law 45 (No N+1 queries) violated: 305/390 relationship(s) without laz… |
| 4 | `WP4-TF-MISSING-CREATED-AT` | 5 | 3 | 5.0 | 1x missing created_at in table `video_room_participants`: table `vide… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 5 | 1 | 12.5 | function `_mark_messages_read` duplicates `backend/domains/comms/serv… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 4 | 1 | 10.0 | cross-domain import `domains.catalog.models.products` (domains.logist… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 4 | 1 | 10.0 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-TF-MISSING-IS-DELETED` | 4 | 3 | 4.0 | 1x missing is_deleted in table `shipment_tracking_projections`: table… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 4 | 1 | 4.0 | 1x rel lazy in table `admin_change_audit_logs`: relationship `admin`… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 4 | 1 | 4.0 | 1x rel lazy in table `purchase_orders`: relationship `lines` has no l… |
| 4 | `WP4-TF-SCHEMA-UNKNOWN` | 4 | 1 | 4.0 | 1x schema unknown in table `payment_methods`: schema `payments` is no… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 4.0 | 1x timestamp default in table `announcements`: `updated_at` uses Pyth… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 4.0 | 1x timestamp default in table `email_campaigns`: `updated_at` uses Py… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 4.0 | 2x timestamp default in table `commission_agreements`: `created_at` u… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 4.0 | 1x timestamp default in table `payout_rules`: `created_at` uses Pytho… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-COMM` | 4 | 1 | 10.0 | function `_mark_messages_read` duplicates `backend/domains/comms/serv… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-HR-S` | 4 | 1 | 10.0 | function `validate_work_hours` duplicates `backend/domains/audit/serv… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 4 | 1 | 10.0 | function `get_country_communications` duplicates `backend/domains/cou… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 4 | 1 | 10.0 | function `is_within_fence` duplicates `backend/domains/country/servic… |
| 4 | `WP4-COLOR-DRIFT` | 3 | 1 | 46.0 | 165 hardcoded hex colour(s) across 33 component file(s) outside the t… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 3 | 1 | 7.5 | cross-domain import `domains.accounts.models.user` (domains.orders ->… |
| 4 | `WP4-DESIGN-PRIMITIVES` | 3 | 2 | 11.0 | 673 hand-rolled card/input class strings across 166 files duplicate a… |
| 4 | `WP4-DUPLICATE-FILE` | 3 | 3 | 7.5 | byte-identical duplicate file(s): backend/domains/finance/exceptions.… |
| 4 | `WP4-INTERACTION-BUTTON` | 3 | 1 | 4.5 | 949 of 1466 button elements have no explicit type; inside a <form> th… |
| 4 | `WP4-INTERACTION-MODAL` | 3 | 1 | 9.5 | 28 destructive control(s) in 8 modal file(s) with no confirmation step |
| 4 | `WP4-LAW-SECURITY` | 3 | 1 | 3.0 | Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s) |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 3 | 1 | 7.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 3 | 1 | 7.5 | `module imports infrastructure`: imports `infrastructure.database.sch… |
| 4 | `WP4-PROVIDER-RESILIENCE` | 3 | 1 | 7.5 | circuit breaker present in 8/94 provider modules |
| 4 | `WP4-RUNBOOKS` | 3 | 3 | 7.5 | no deploy runbook found |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 3 | 1 | 3.0 | 1x rel lazy in table `physical_id_cards`: relationship `employee` has… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-AUDI` | 3 | 1 | 7.5 | function `get_residency_config` duplicates `backend/domains/audit/ser… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 3 | 1 | 7.5 | function `admin_email_stats` duplicates `backend/domains/logistics/se… |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 3 | 1 | 7.5 | endpoint `list_employees_public` has no visible auth/feature gate |
| 4 | `WP4-CI-CD` | 2 | 1 | 5.0 | pipeline lacks: secret scanning |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.accoun… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.audit ->… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 2 | 1 | 5.0 | cross-domain import `domains.comms.models.communication` (domains.cat… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.comms ->… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 5.0 | cross-domain import `domains.customers.models.cross_country_session`… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.core` (domains.customers… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.financ… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 5.0 | cross-domain import `domains.comms.models.suppliers` (domains.finance… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.govern… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 2 | 1 | 5.0 | cross-domain import `domains.audit.services.logs.audit_service` (doma… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.promotion… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.banking` (domains.suppli… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.suppli… |
| 4 | `WP4-DB-POOL` | 2 | 1 | 2.0 | no pool_size configuration found |
| 4 | `WP4-EXTRA-DOMAIN` | 2 | 2 | 5.0 | domain package `media` exists |
| 4 | `WP4-INTENT-STUB` | 2 | 2 | 2.0 | 1 placeholder response(s) ('not yet wired') in live module |
| 4 | `WP4-LAW-PROVIDER` | 2 | 1 | 2.0 | Law 123 (Single SDK per provider) violated: 3 provider file(s) contai… |
| 4 | `WP4-LAW-STRUCTURE` | 2 | 1 | 2.0 | Law 12 (15 domains) violated: extra domain(s): media, payments |
| 4 | `WP4-MIDDLEWARE-IMPORTS-ABOVE` | 2 | 2 | 5.0 | `middleware imports above`: imports `domains.accounts.services.auth.s… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 2 | 1 | 5.0 | `module imports infrastructure`: imports `infrastructure.database.sch… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 2 | 1 | 5.0 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 2 | 1 | 5.0 | `module imports infrastructure`: imports `infrastructure.utils.invoic… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 2 | 1 | 5.0 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 2.0 | 1x rel lazy in table `categories`: relationship `products` has no laz… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 2.0 | 2x rel lazy in table `ticket_messages`: relationship `ticket` has no… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 2.0 | 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` ha… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 2 | 1 | 2.0 | 1x rel lazy in table `country_feature_flags`: relationship `country`… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 2 | 1 | 2.0 | 1x rel lazy in table `coupons`: relationship `country` has no lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 2 | 1 | 2.0 | 1x rel lazy in table `supplier_profiles`: relationship `user` has no… |
| 4 | `WP4-TF-SCHEMA-MISSING` | 2 | 1 | 2.0 | 1x schema missing in table `payroll_records`: table `payroll_records`… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 2 | 1 | 2.0 | 2x timestamp default in table `country_configs`: `created_at` uses Py… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 2 | 1 | 2.0 | 2x timestamp default in table `referrals`: `created_at` uses Python-s… |
| 4 | `WP4-UNCATEGORISED-ZOZI-AUDIT` | 2 | 1 | 2.0 | check `arch_router_thinness` failed: crashed: NameError: name 'DB_CAL… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` | 2 | 1 | 5.0 | function `get_cities_dropdown` duplicates `backend/domains/country/se… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 2 | 1 | 5.0 | function `_normalize_address_payload` duplicates `backend/domains/acc… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` | 2 | 1 | 5.0 | function `admin_email_stats` duplicates `backend/domains/governance/s… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 2 | 1 | 5.0 | function `list_logistics_partner_locations` duplicates `backend/domai… |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 2 | 1 | 5.0 | endpoint `shift_handover_health` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 2 | 1 | 5.0 | endpoint `list_assigned_shipments` has no visible auth/feature gate |
| 4 | `WP4-AP-EMPTY-HANDLER-PASS` | 1 | 1 | 1.0 | Empty handler (pass): 4 occurrence(s); sample `backend/infrastructure… |
| 4 | `WP4-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` | 1 | 1 | 1.0 | Stub function (NotImplementedError): 37 occurrence(s); sample `backen… |
| 4 | `WP4-AP-TODO-ONLY` | 1 | 1 | 6.0 | TODO-only implementation: 296 occurrence(s); sample backend/domains/a… |
| 4 | `WP4-BASE-IMAGE` | 1 | 1 | 1.0 | dev database image `postgres:18-alpine` (documented: postgres:16-alpi… |
| 4 | `WP4-CACHE-COVERAGE` | 1 | 1 | 2.5 | cache references (155) below list-endpoint count (482) |
| 4 | `WP4-CATEGORY-TAXONOMY` | 1 | 1 | 20.0 | the schema can express a hierarchy (columns: __tablename__, depth, is… |
| 4 | `WP4-CHAIN-CHAIN-002` | 1 | 1 | 6.0 | CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1… |
| 4 | `WP4-CHAIN-CHAIN-003` | 1 | 1 | 6.0 | CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0… |
| 4 | `WP4-CHAIN-CHAIN-006` | 1 | 1 | 6.0 | CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps locat… |
| 4 | `WP4-COUNT-QUERIES` | 1 | 1 | 2.5 | 306 `.count()` calls (expensive on large tables) |
| 4 | `WP4-COVERAGE-ROUTE` | 1 | 1 | 1.0 | 3 spec file(s) navigate to paths that no longer exist in the app rout… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | cross-domain import `domains.governance.core.approval_matrix_service`… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.a… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.general_ledger` (domains.… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.audit… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.audit -… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.c… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.comms… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.com… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.c… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.catalog.models.upload_job` (domains.comm… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.comms -… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models` (domains.country -> dom… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.tax_rules` (domains.count… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.coun… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.coupon_usage` (domains… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.customers… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.admin` (domains.financ… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.finance -… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.finance -… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.f… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.gover… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.governa… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.gove… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.audit.services.retention_service` (domai… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (do… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.hr ->… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.hr -> d… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.hr -> d… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.hr -> dom… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.payments` (domains.logist… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.banking` (domains.logist… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.country_control` (domains… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.logisti… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.customers.models.cross_country_session`… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.log… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.security.models.fraud` (domains.logistic… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.order… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.orders… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.orders… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.orde… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.ord… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.services.core.shipment_service… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.finance.services.payments.payment_engine… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.promo… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.promot… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.orders.customer_coupons_create_service`… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.security… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.fraud_indicators` (doma… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.secu… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.supplie… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.suppl… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.communication` (domains.sup… |
| 4 | `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (do… |
| 4 | `WP4-DEEP-NESTING` | 1 | 1 | 2.5 | 87 function(s) exceed 4 nesting levels (max seen 17) |
| 4 | `WP4-DOCS` | 1 | 1 | 2.5 | SETUP.md missing |
| 4 | `WP4-ENV-RAW` | 1 | 1 | 1.0 | 135 raw os.getenv/environ read(s) bypass typed settings |
| 4 | `WP4-FINANCE-AUTOMATION` | 1 | 1 | 20.0 | no implementation found for: bad_debt_provision |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(cat.com… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commi… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(commiss… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `max_commission_amount: Optional[… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 13 float-for-money signal(s); first: `min_price: Optional[float]` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `intent["entities"]["price_range"… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `return float(data.get("standard_… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dic… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"balance": float(balance),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"commission": float(result[1] or… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"price": float(p.price) if p.pri… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"salary": float(employee.salary)… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `"base_salary": float(base_salary… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `return {"total_paid": float(tota… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(emp.salary),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_days": float(l.total_days… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `return {'total_revenue': float(t… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `return float(payout.amount)` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `"base_rate": float(base_rate),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_revenue": float(total_rev… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `max_combined_discount_amount: Op… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `charge_amount = float(data.get("… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 10 float-for-money signal(s); first: `"charge_amount": float(charge_a… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_to… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_to… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"max_combined_discount_amount":… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `avg_order_value = float(total_re… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"commission_rate": float(default… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 19 float-for-money signal(s); first: `"total_revenue": float(total_re… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `first_revenue = sum(float(o.tota… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `return float(config.supplier_onb… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `"price": float(product.price),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `coverage = float(fg_pixels / tot… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_revenue": float(total_rev… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_pending": float(total_pen… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_pct=float(payload.get("… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `min_price: float | None` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `min_price: float | None` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: float` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 8 float-for-money signal(s); first: `current_price: float` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `parsed["min_price"] = float(matc… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-GE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expir… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `white_balance_strength: float` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `result["total"] = float(match.gr… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-OC` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"amount": float(amt),` |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-SH` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `key=lambda x: (not x.get("availa… |
| 4 | `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-VO` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `result["amount"] = float(amount_… |
| 4 | `WP4-GHOST-FEATURE` | 1 | 1 | 1.0 | 8 gate literal(s) referenced but not defined in any features.py: ) as… |
| 4 | `WP4-HANDOVER` | 1 | 1 | 6.0 | 10 of 10 handover/takeover function(s) are missing at least one safet… |
| 4 | `WP4-INTERACTION-FORM` | 1 | 1 | 2.5 | 465 of 743 text input(s) have no label, aria-label or id association |
| 4 | `WP4-INTERACTION-STATE` | 1 | 1 | 2.5 | 138 empty or console-only catch handler(s) |
| 4 | `WP4-LAW-CONFIG` | 1 | 1 | 1.0 | Law 84 (Typed feature flags) violated: 134 raw os.getenv read(s) |
| 4 | `WP4-LAW-DOCS` | 1 | 1 | 1.0 | Law 248 (Runbooks) violated: 0 doc file(s) under docs/ |
| 4 | `WP4-LAW-MIGRATION` | 1 | 1 | 1.0 | Law 27 (Delete temp scripts) violated: 91 temp/debug file(s) at backe… |
| 4 | `WP4-LAW-PERFORMANCE` | 1 | 1 | 1.0 | Law 222 (Keyset pagination) violated: 89 OFFSET usage(s) |
| 4 | `WP4-LONG-FUNCTION-BACKEND-CONFIG-PY` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_validate_required_secrets_i… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 10 function(s) >50 lines; longest sample `authenticate_password` = 57… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `list_products` = 119 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 5… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `send_message` = 58 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 7… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_country_public_payload` = 8… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_order_payment_status` =… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 1… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 li… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_payment_methods_status`… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 6… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 11 function(s) >50 lines; longest sample `generate_supplier_payout_ba… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_t… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 li… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score`… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 l… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lin… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 li… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt`… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `bulk_update_order_status_adm… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_return_request` = 67… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdo… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 li… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 li… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 1… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 l… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lin… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `persist_supplier_product` =… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `process_product_image` = 52… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `persist_supplier_product` =… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_sh… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_load_environment_email_conf… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 l… |
| 4 | `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `with_retry` = 87 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_order` = 79 lines |
| 4 | `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_payment_page` = 90 li… |
| 4 | `WP4-MIDDLEWARE` | 1 | 1 | 2.5 | middleware order is ['foundation', 'geo', 'security', 'rate', 'compli… |
| 4 | `WP4-MOBILE-DEPS` | 1 | 1 | 2.5 | dynamically required package(s) absent from package.json: @/lib/api,… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.messaging.ws… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.config… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.curren… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.config… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.storage.stor… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.countr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.backgr… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dep… |
| 4 | `WP4-N-PLUS-1` | 1 | 1 | 1.0 | 305/395 relationship() declarations omit lazy= |
| 4 | `WP4-OFFSET-PAGINATION` | 1 | 1 | 1.0 | 90 OFFSET pagination usage(s) (sample: .offset(safe_offset)) |
| 4 | `WP4-ORPHAN-FEATURE` | 1 | 1 | 1.0 | 231 orphan feature atom(s) defined but never gated (e.g. accounts.add… |
| 4 | `WP4-ORPHAN-JOB` | 1 | 1 | 2.5 | 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_r… |
| 4 | `WP4-ORPHAN-PROVIDER` | 1 | 1 | 1.0 | 87 provider module(s) never referenced by any domain file: __header__… |
| 4 | `WP4-PACKAGE-MANAGER` | 1 | 1 | 1.0 | non-canonical lockfile `package-lock.json` present |
| 4 | `WP4-PII-LOGS` | 1 | 1 | 2.5 | 8 log statement(s) may include PII/secrets (sample: logger.error("Fai… |
| 4 | `WP4-PRINT-LOGGING` | 1 | 1 | 2.5 | 3 `print()` call(s) in production paths (sample backend/domains/_mixi… |
| 4 | `WP4-PROVIDER-CONFIG` | 1 | 1 | 1.0 | 13 provider module(s) read secrets via raw os.getenv |
| 4 | `WP4-PROVIDER-EXTRA` | 1 | 1 | 1.0 | provider package(s) outside the canonical tree: _helpers.py, analytic… |
| 4 | `WP4-PROVIDER-HEALTH` | 1 | 1 | 1.0 | 93/93 provider modules lack health_check() |
| 4 | `WP4-PROVIDER-TIMEOUT` | 1 | 1 | 1.0 | 62/93 provider modules declare no timeout |
| 4 | `WP4-QUALITY-ASSURANCE` | 1 | 1 | 20.0 | no implementation found for: product_inspection, proof_of_delivery, s… |
| 4 | `WP4-RAW-GETENV` | 1 | 1 | 2.5 | 126 raw os.getenv/os.environ read(s) in production paths (top: provid… |
| 4 | `WP4-READ-REPLICA` | 1 | 1 | 1.0 | read-replica engine exists but `get_read_db` is never used by domains |
| 4 | `WP4-SEARCH-INDEX` | 1 | 1 | 1.0 | 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike(… |
| 4 | `WP4-SELECT-STAR` | 1 | 1 | 1.0 | 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM a… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-CONFIG-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 895: truly-silent: except Att… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 6 silent except block(s); first at line 3044: pass-only: except Excep… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 69: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 54: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 126: truly-silent: except (Ty… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 212: pass-only: except (TypeE… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 454: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 281: truly-silent: except Web… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 166: truly-silent: except Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 283: truly-silent: except Web… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 84: pass-only: except WebSock… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 218: truly-silent: except (js… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 191: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 70: pass-only: except (json.J… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 480: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 130: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 276: truly-silent: except Web… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 232: pass-only: except (TypeE… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 75: truly-silent: except (Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 87: pass-only: except ValueEr… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 3774: truly-silent: except Ex… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 1111: truly-silent: except Ex… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 3411: truly-silent: except HT… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 693: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 307: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 43: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 97: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 120: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 85: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 126: truly-silent: except (js… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 6 silent except block(s); first at line 1439: pass-only: except Excep… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 28: truly-silent: except (Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 355: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 168: pass-only: except (Value… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 73: truly-silent: except (Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 508: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 55: pass-only: except (json.J… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 284: truly-silent: except (Va… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 211: pass-only: except Attrib… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 67: truly-silent: except (Typ… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 362: truly-silent: except (Ty… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 527: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 78: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 44: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 6 silent except block(s); first at line 102: pass-only: except (json.… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 30: pass-only: except ValueEr… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 9 silent except block(s); first at line 1430: truly-silent: except Ex… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 518: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 139: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except (Ty… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 280: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 203: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 437: truly-silent: except (Ty… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 188: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 174: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 1104: truly-silent: except (T… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 113: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 599: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except Runtime… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 92: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 323: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 22: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 132: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 49: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 26: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 57: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 31: pass-only: except (ValueE… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 110: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 7 silent except block(s); first at line 67: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except Runtime… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 293: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MAIN-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 199: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 245: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 424: truly-silent: except Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 242: truly-silent: except Uni… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 150: pass-only: except WebSoc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 160: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 88: pass-only: except ValueEr… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 78: truly-silent: except urll… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 231: pass-only: except OSErro… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 281: truly-silent: except jso… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 148: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 115: truly-silent: except Val… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 108: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 35: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 155: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 302: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 113: pass-only: except Except… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 288: truly-silent: except Exc… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 95: truly-silent: except Exce… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 510: truly-silent: except (Va… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 24: pass-only: except Excepti… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 44: truly-silent: except Valu… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 25: truly-silent: except (jso… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 135: truly-silent: except (Ty… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 95: truly-silent: except Unic… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 73: truly-silent: except (url… |
| 4 | `WP4-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 33: truly-silent: except Exce… |
| 4 | `WP4-TABLE-GOVERNANCE` | 1 | 1 | 2.5 | 9 table(s) lack audit timestamps and 4 lack soft delete |
| 4 | `WP4-TABLE-INDEX` | 1 | 1 | 6.0 | 233 (table, column) pair(s) are filtered or sorted on with no declare… |
| 4 | `WP4-TABLE-RELATION` | 1 | 1 | 6.0 | 305 of 390 relationship() calls omit lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 1.0 | 1x rel lazy in table `addresses`: relationship `user` has no lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 1.0 | 3x rel lazy in table `onboarding_pipelines`: relationship `user` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 1.0 | 1x rel lazy in table `otp_codes`: relationship `user` has no lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 1.0 | 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 1.0 | 4x rel lazy in table `chart_of_categories`: relationship `parent` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 1.0 | 2x rel lazy in table `commission_groups`: relationship `categories` h… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 1x rel lazy in table `meeting_recordings`: relationship `starter` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 3x rel lazy in table `incident_war_rooms`: relationship `threads` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 3x rel lazy in table `messages`: relationship `country` has no lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 17x rel lazy in table `country_configs`: relationship `communications… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_basics`: relationship `country` has no… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 3x rel lazy in table `shift_handover_logs`: relationship `user` has n… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_economics`: relationship `country` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_legals`: relationship `country` has no… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_taxes`: relationship `country` has no l… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 1.0 | 2x rel lazy in table `cross_country_customer_sessions`: relationship… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 1.0 | 2x rel lazy in table `referrals`: relationship `referrer` has no lazy= |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1.0 | 1x rel lazy in table `payout_rules`: relationship `country` has no la… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 1.0 | 1x rel lazy in table `legal_contract_templates`: relationship `countr… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 5x rel lazy in table `logistics_partners`: relationship `profile` has… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 1x rel lazy in table `shipping_rules`: relationship `country` has no… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 1x rel lazy in table `promotion_engine_configs`: relationship `countr… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 1 | 1 | 1.0 | 2x rel lazy in table `document_verifications`: relationship `pipeline… |
| 4 | `WP4-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 1 | 1 | 1.0 | 1x rel lazy in table `permission_categories`: relationship `permissio… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` | 1 | 1 | 1.0 | 2x timestamp default in table `upload_jobs`: `created_at` uses Python… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 1x timestamp default in table `messages`: `created_at` uses Python-si… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 2x timestamp default in table `news_articles`: `created_at` uses Pyth… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_basics`: `created_at` uses Pyt… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_economics`: `created_at` uses… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_legals`: `created_at` uses Pyt… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_taxes`: `created_at` uses Pyth… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 1 | 1 | 1.0 | 1x timestamp default in table `cross_country_customer_sessions`: `cre… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 2x timestamp default in table `city_distance_matrices`: `created_at`… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 1x timestamp default in table `shipping_rules`: `created_at` uses Pyt… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 2x timestamp default in table `coupon_usages`: `created_at` uses Pyth… |
| 4 | `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 2x timestamp default in table `promotion_engine_configs`: `created_at… |
| 4 | `WP4-TODO-HYGIENE` | 1 | 1 | 2.5 | 295 TODO/FIXME without ticket reference or expiration date (e.g. back… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-ACCO` | 1 | 1 | 6.0 | file has 4518 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | function `_preprocess_for_ai` duplicates `backend/domains/catalog/ser… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` | 1 | 1 | 6.0 | file has 1970 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 6.0 | file has 1858 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 6.0 | file has 4725 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 6.0 | file has 1775 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 6.0 | file has 4150 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | function `_serialize_lp_doc` duplicates `backend/domains/logistics/se… |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` | 1 | 1 | 6.0 | file has 5104 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` | 1 | 1 | 6.0 | file has 1633 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-DOMAINS-SUPP` | 1 | 1 | 6.0 | file has 2786 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-INFRASTRUCTU` | 1 | 1 | 6.0 | file has 2230 lines (split candidate) |
| 4 | `WP4-UNCATEGORISED-BACKEND-MODULES-EMPL` | 1 | 1 | 6.0 | file has 1553 lines (split candidate) |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | endpoint `list_employees_public` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| 4 | `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| 4 | `WP4-UNKNOWN-GATE` | 1 | 1 | 2.5 | 13 require_feature literal(s) not found in any domains/*/features.py… |
| 4 | `WP4-WEB-IMAGES` | 1 | 1 | 2.5 | next/image formats do not enable AVIF |
| 4 | `WP4-WEB-REWRITES` | 1 | 1 | 2.5 | rewrite `/hr/*` targets a non-canonical backend surface |
| 4 | `WP4-WEB-ROUTES` | 1 | 1 | 2.5 | duplicate route trees `logistics-partner` and `logistics-partners` bo… |
| 4 | `WP4-WEB-STATES` | 1 | 1 | 2.5 | 282 page(s) lack loading/error siblings (sample frontend/web_app/src/… |
| 4 | `WP4-WORM` | 1 | 1 | 2.5 | audit trail mutates rows after INSERT (UPDATE on audit table) |
| 5 | `WP5-RECOMMENDATIONS-REC-AUTOMATION` | 8 | 7 | 13.0 | Automate the human-in-the-loop queue and the serial write loops |
| 5 | `WP5-RECOMMENDATIONS-REC-DATA` | 4 | 5 | 27.5 | Model and seed the full 5-tier product taxonomy |
| 5 | `WP5-RECOMMENDATIONS-REC-OPS` | 2 | 2 | 2.0 | Add a dispatch smoke test for every scheduled task |
| 5 | `WP5-RECOMMENDATIONS-REC-WORKFLOW` | 2 | 2 | 26.0 | Turn the event spine into real work, or delete it |
| 5 | `WP5-RECOMMENDATIONS-REC-DESIGN` | 1 | 1 | 6.0 | Adopt the existing UI primitives and delete duplicated markup |
| 5 | `WP5-RECOMMENDATIONS-REC-FINANCE` | 1 | 1 | 20.0 | Automate the manual finance processes end to end |
| 5 | `WP5-RECOMMENDATIONS-REC-FRONTEND` | 1 | 1 | 2.5 | Standardise interaction state handling across all screens |
| 5 | `WP5-RECOMMENDATIONS-REC-QA` | 1 | 1 | 20.0 | Introduce a quality-gate chain across fulfilment |

## Wave plan

| Wave | Title | Steps | Blockers | Gates | Verifications | Est. hours |
|------|-------|-------|----------|-------|---------------|------------|
| 0 | Restore the ability to verify anything (build · boot · test · migrate) | 11 | 5 | 11 | 0 | 26.0 |
| 1 | Fix the hard blockers that prevent correct behaviour | 26 | 14 | 0 | 0 | 47.0 |
| 2 | Close correctness and security defects | 54 | 0 | 0 | 0 | 129.0 |
| 3 | Close coverage, quality and performance defects | 156 | 0 | 0 | 0 | 156.0 |
| 4 | Verification tasks for untrusted claims | 1027 | 61 | 0 | 1027 | 2344.0 |
| 5 | Improvement track — recommendations (not release-gating) | 20 | 0 | 0 | 0 | 117.0 |

---
## Wave 0 · Restore the ability to verify anything (build · boot · test · migrate)

> **Nothing else can be verified until this wave is green.** A static audit run on a project that does not boot, does not migrate, or does not collect its tests produces numbers without meaning.

#### Work packages in wave 0 (3)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP0-PREFLIGHT` | 4 | 0 | 4 | 0 | 10.0 | Architecture tests -> INCOMPLETE |
| `WP0-BOOT-PREFLIGHT` | 1 | 1 | 1 | 0 | 1.0 | Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limi… |
| `WP0-TEST-BROKEN` | 6 | 6 | 0 | 0 | 15.0 | test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF |

##### `WP0-PREFLIGHT` — Architecture tests -> INCOMPLETE

- **cluster:** `CLUSTER-preflight` · **steps:** 4 (0 closed) · **files:** 0 · **est.:** 10.0h

[ ] `PRE-ARCHITECTURE-TESTS` — Architecture tests -> INCOMPLETE
    - do: Resolve the pre-flight failure before trusting any other verification step; nothing downstream can be proven while it fails.
    - verify: `python _zozi_audit/zozi_audit.py --full # this row must become PASS`
[ ] `PRE-BACKEND-LINT` — Backend lint -> FAIL
    - do: Resolve the pre-flight failure before trusting any other verification step; nothing downstream can be proven while it fails.
    - verify: `python _zozi_audit/zozi_audit.py --full # this row must become PASS`
[ ] `PRE-FRONTEND-TYPE-CHECK` — Frontend type check -> FAIL
    - do: Resolve the pre-flight failure before trusting any other verification step; nothing downstream can be proven while it fails.
    - verify: `python _zozi_audit/zozi_audit.py --full # this row must become PASS`
[ ] `PRE-VALKEY-CONNECTIVITY` — Valkey connectivity -> FAIL
    - do: Resolve the pre-flight failure before trusting any other verification step; nothing downstream can be proven while it fails.
    - verify: `python _zozi_audit/zozi_audit.py --full # this row must become PASS`

##### `WP0-BOOT-PREFLIGHT` — Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limiting and the event bu

- **cluster:** `CLUSTER-boot-preflight` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `BLOCK-valkey-unreachable` — Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limi…
    - do: Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed
    - verify: `cd backend && python -c "import valkey; print(valkey.Valkey.from_url('valkey://host:6379').ping())"`

##### `WP0-TEST-BROKEN` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF

- **cluster:** `CLUSTER-test-broken` · **steps:** 6 (0 closed) · **files:** 6 · **est.:** 15.0h
- **files:** `backend/tests/domains/test_auto_payout_sweep.py`, `backend/tests/domains/test_cart.py`, `backend/tests/domains/test_comprehensive_system.py`, `backend/tests/domains/test_ems_edge_cases.py`, `backend/tests/domains/test_ems_lifecycle.py`, `backend/tests/domains/test_search_endpoints.py`

[ ] `TEST-007` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error
[ ] `TEST-008` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error
[ ] `TEST-009` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error
[ ] `TEST-010` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error
[ ] `TEST-011` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error
[ ] `TEST-012` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
    - do: Fix the syntax/import error

[ ] `PRE-ARCHITECTURE-TESTS` — Architecture tests -> INCOMPLETE
[ ] `PRE-BACKEND-LINT` — Backend lint -> FAIL
[ ] `PRE-FRONTEND-TYPE-CHECK` — Frontend type check -> FAIL
[ ] `PRE-VALKEY-CONNECTIVITY` — Valkey connectivity -> FAIL
[ ] `BLOCK-valkey-unreachable` — Valkey unreachable (valkey://localhost:6379/? via .env:VALKEY_URL: ConnectionRefusedError) — cache, sessions, rate limiting and the event bus degrade
[ ] `TEST-007` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
[ ] `TEST-008` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
[ ] `TEST-009` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
[ ] `TEST-010` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
[ ] `TEST-011` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
[ ] `TEST-012` — test file cannot be parsed: SyntaxError line 1: invalid non-printable character U+FEFF
---
## Wave 1 · Fix the hard blockers that prevent correct behaviour

#### Work packages in wave 1 (15)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 4 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 36 float-for-money signal(s); first: `amount: Decimal | float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 10 float-for-money signal(s); first: `subtotal: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 5 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 1 | 0 | 2.5 | 6 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP1-IDEMPOTENCY` | 1 | 1 | 1 | 0 | 2.5 | idempotency_key: Optional[str] = None |
| `WP1-SETTINGS-CONTRACT` | 12 | 8 | 0 | 0 | 12.0 | settings.NEWS_API_KEY is read but Settings declares no such field |

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/schemas/finance_schemas.py`

[ ] `LOGIC-127` — 4 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/schemas/finance_schemas.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_service.py`

[ ] `LOGIC-131` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/finance_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/accounting_controller.py`

[ ] `LOGIC-132` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/ledger/accounting_controller.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 36 float-for-money signal(s); first: `amount: Decimal | float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payouts/payout_batch_service.py`

[ ] `LOGIC-139` — 36 float-for-money signal(s); first: `amount: Decimal | float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payouts/payout_batch_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/treasury/cash_management_service.py`

[ ] `LOGIC-141` — 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/treasury/cash_management_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/cart_service__orders.py`

[ ] `LOGIC-177` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/cart/cart_service__orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 10 float-for-money signal(s); first: `subtotal: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/service.py`

[ ] `LOGIC-178` — 10 float-for-money signal(s); first: `subtotal: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/cart/service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-204` — 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/orders/supplier_orders_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 5 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/profile/supplier_payouts_service.py`

[ ] `LOGIC-209` — 5 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/profile/supplier_payouts_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` — 2 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/orders.py`

[ ] `LOGIC-225` — 2 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 6 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/finance.py`

[ ] `LOGIC-230` — 6 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/finance.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/base.py`

[ ] `LOGIC-252` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/base.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/base_models.py`

[ ] `LOGIC-253` — 2 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/base_models.py | head -20`

##### `WP1-IDEMPOTENCY` — idempotency_key: Optional[str] = None

- **cluster:** `CLUSTER-idempotency` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-322` — idempotency_key: Optional[str] = None
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '371p' backend/domains/finance/services/payments/payment_engine.py`

##### `WP1-SETTINGS-CONTRACT` — settings.NEWS_API_KEY is read but Settings declares no such field

- **cluster:** `CLUSTER-settings-contract` · **steps:** 12 (0 closed) · **files:** 8 · **est.:** 12.0h
- **files:** `backend/domains/analytics/services/aggregation/command_center_service.py`, `backend/domains/orders/services/core/order_engine.py`, `backend/providers/geography/country.py`, `backend/providers/geography/geo.py`, `backend/providers/image/bg_remover/public_api.py`, `backend/domains/governance/services/auth/iam_service_accounts.py`, `backend/infrastructure/messaging/email_service.py`, `backend/infrastructure/storage/backup.py`

[ ] `ENV-001` — settings.NEWS_API_KEY is read but Settings declares no such field
    - do: add `NEWS_API_KEY` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'NEWS_API_KEY' backend/config.py`
[ ] `ENV-002` — settings.shipping_flat_rate is read but Settings declares no such field
    - do: add `shipping_flat_rate` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'shipping_flat_rate' backend/config.py`
[ ] `ENV-003` — settings.geo_default_country is read but Settings declares no such field
    - do: add `geo_default_country` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'geo_default_country' backend/config.py`
[ ] `ENV-004` — settings.geo_ipapi_timeout is read but Settings declares no such field
    - do: add `geo_ipapi_timeout` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'geo_ipapi_timeout' backend/config.py`
[ ] `ENV-005` — settings.bg_preset_models is read but Settings declares no such field
    - do: add `bg_preset_models` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'bg_preset_models' backend/config.py`
[ ] `ENV-006` — settings.qr_secret_key is read but Settings declares no such field
    - do: add `qr_secret_key` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'qr_secret_key' backend/config.py`
[ ] `ENV-007` — settings.free_shipping_threshold is read but Settings declares no such field
    - do: add `free_shipping_threshold` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'free_shipping_threshold' backend/config.py`
[ ] `ENV-008` — settings.smtp_username is read but Settings declares no such field
    - do: add `smtp_username` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'smtp_username' backend/config.py`
    - … and 4 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-settings-contract`)

[ ] `LOGIC-127` — 4 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-131` — 2 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-132` — 1 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-139` — 36 float-for-money signal(s); first: `amount: Decimal | float`
[ ] `LOGIC-141` — 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)`
[ ] `LOGIC-177` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`
[ ] `LOGIC-178` — 10 float-for-money signal(s); first: `subtotal: float`
[ ] `LOGIC-204` — 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))`
[ ] `LOGIC-209` — 5 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-225` — 2 float-for-money signal(s); first: `price: float`
[ ] `LOGIC-230` — 6 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-252` — 2 float-for-money signal(s); first: `amount: float`
[ ] `LOGIC-253` — 2 float-for-money signal(s); first: `amount: Optional[float]`
[ ] `LOGIC-322` — idempotency_key: Optional[str] = None
[ ] `ENV-001` — settings.NEWS_API_KEY is read but Settings declares no such field
[ ] `ENV-002` — settings.shipping_flat_rate is read but Settings declares no such field
[ ] `ENV-003` — settings.geo_default_country is read but Settings declares no such field
[ ] `ENV-004` — settings.geo_ipapi_timeout is read but Settings declares no such field
[ ] `ENV-005` — settings.bg_preset_models is read but Settings declares no such field
[ ] `ENV-006` — settings.qr_secret_key is read but Settings declares no such field
[ ] `ENV-007` — settings.free_shipping_threshold is read but Settings declares no such field
[ ] `ENV-008` — settings.smtp_username is read but Settings declares no such field
[ ] `ENV-009` — settings.smtp_use_tls is read but Settings declares no such field
[ ] `ENV-010` — settings.smtp_use_ssl is read but Settings declares no such field
[ ] `ENV-011` — settings.smtp_timeout_seconds is read but Settings declares no such field
[ ] `ENV-012` — settings.backup_verify_on_create is read but Settings declares no such field
---
## Wave 2 · Close correctness and security defects

#### Work packages in wave 2 (51)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP2-HTTP-HEADERS` | 4 | 1 | 0 | 0 | 4.0 | `/health` is missing none; deprecated headers present: x-xss-protection: removed from all current browsers; ignored, an… |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `discount_value: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `total_amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 10 float-for-money signal(s); first: `commission_reserve: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 45 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 74 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `discount_amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 8 float-for-money signal(s); first: `discount_value: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `total = float(weight.scalar() or 0.0)` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 9 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 63 float-for-money signal(s); first: `price: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float | None` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `total_revenue: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `base_price: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |

##### `WP2-HTTP-HEADERS` — `/health` is missing none; deprecated headers present: x-xss-protection: removed from all current browsers; ignored, and re-enables legacy X

- **cluster:** `CLUSTER-http-headers` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `HTTP-header-policy` — `/health` is missing none; deprecated headers present: x-xss-protection: removed from all current browsers; ignored, an…
    - do: add the missing headers to the security-headers middleware and remove X-XSS-Protection (removed from all current browsers)
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health`
[ ] `HTTP-header-policy` — `/docs` is missing none; deprecated headers present: x-xss-protection: removed from all current browsers; ignored, and…
    - do: add the missing headers to the security-headers middleware and remove X-XSS-Protection (removed from all current browsers)
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health`
[ ] `HTTP-header-policy` — `/openapi.json` is missing none; deprecated headers present: x-xss-protection: removed from all current browsers; ignor…
    - do: add the missing headers to the security-headers middleware and remove X-XSS-Protection (removed from all current browsers)
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health`
[ ] `HTTP-header-policy` — `/definitely-not-a-route` is missing none; deprecated headers present: x-xss-protection: removed from all current brows…
    - do: add the missing headers to the security-headers middleware and remove X-XSS-Protection (removed from all current browsers)
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` — 1 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/permissions/permission_service.py`

[ ] `LOGIC-100` — 1 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/accounts/services/permissions/permission_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `discount_value: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/product_discount_service.py`

[ ] `LOGIC-107` — 1 float-for-money signal(s); first: `discount_value: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/products/product_discount_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-110` — 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/search/search_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 2 float-for-money signal(s); first: `total_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/transactional.py`

[ ] `LOGIC-112` — 2 float-for-money signal(s); first: `total_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/email/transactional.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `LOGIC-113` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/messaging/chat_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/utility/shared_utils.py`

[ ] `LOGIC-114` — 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/shared/utility/shared_utils.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/ports.py`

[ ] `LOGIC-115` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/ports.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/localization/localization_service.py`

[ ] `LOGIC-117` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/localization/localization_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/cart_service.py`

[ ] `LOGIC-121` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/cart_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 5 float-for-money signal(s); first: `price_band_lo: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/recommendations/recommendation_service.py`

[ ] `LOGIC-125` — 5 float-for-money signal(s); first: `price_band_lo: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/recommendations/recommendation_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-126` — 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/search_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 2 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/read_models/governance_read_models.py`

[ ] `LOGIC-142` — 2 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/read_models/governance_read_models.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/schemas/governance_schemas.py`

[ ] `LOGIC-143` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/schemas/governance_schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 3 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/approval/approval_matrix_service.py`

[ ] `LOGIC-145` — 3 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/approval/approval_matrix_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 10 float-for-money signal(s); first: `commission_reserve: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-146` — 10 float-for-money signal(s); first: `commission_reserve: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/command_center/command_center_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/settings/governance_package_service.py`

[ ] `LOGIC-150` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/settings/governance_package_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/travel/travel_service.py`

[ ] `LOGIC-159` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/travel/travel_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 2 float-for-money signal(s); first: `duty_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_imports_service.py`

[ ] `LOGIC-161` — 2 float-for-money signal(s); first: `duty_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_imports_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 45 float-for-money signal(s); first: `duty_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-164` — 45 float-for-money signal(s); first: `duty_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_partner_service.py`

[ ] `LOGIC-171` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/logistics_partner_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 74 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-174` — 74 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/settlement_service.py`

[ ] `LOGIC-175` — 3 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/settlement_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `discount_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/events.py`

[ ] `LOGIC-184` — 1 float-for-money signal(s); first: `discount_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/events.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 8 float-for-money signal(s); first: `discount_value: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/admin_promotion_ops_service.py`

[ ] `LOGIC-185` — 8 float-for-money signal(s); first: `discount_value: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/admin_promotion_ops_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/admin_promotion_service.py`

[ ] `LOGIC-186` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/admin_promotion_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_commerce_configuration_service.py`

[ ] `LOGIC-190` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/admin_commerce_configuration_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_promotions_write_service.py`

[ ] `LOGIC-191` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/admin_promotions_write_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/promotion_admin_write_service.py`

[ ] `LOGIC-193` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/promotion_admin_write_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` — 4 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-195` — 4 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/security/services/fraud/fraud_detection_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/events.py`

[ ] `LOGIC-196` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/events.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 1 float-for-money signal(s); first: `total = float(weight.scalar() or 0.0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/badges/badge_service.py`

[ ] `LOGIC-198` — 1 float-for-money signal(s); first: `total = float(weight.scalar() or 0.0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/badges/badge_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 9 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-205` — 9 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_product_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 5 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-206` — 5 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_products.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 4 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-213` — 4 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/supplier_shared.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 63 float-for-money signal(s); first: `price: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/schemas.py`

[ ] `LOGIC-215` — 63 float-for-money signal(s); first: `price: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/database/schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/analytics.py`

[ ] `LOGIC-218` — 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/utils/analytics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/hr.py`

[ ] `LOGIC-220` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/admin/routers/hr.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` — 1 float-for-money signal(s); first: `amount: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/security.py`

[ ] `LOGIC-222` — 1 float-for-money signal(s); first: `amount: float | None`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/admin/routers/security.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/comms.py`

[ ] `LOGIC-224` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/comms.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 3 float-for-money signal(s); first: `total: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/serializers/customer_serializers.py`

[ ] `LOGIC-227` — 3 float-for-money signal(s); first: `total: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/serializers/customer_serializers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/country.py`

[ ] `LOGIC-229` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/country.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `salary: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr.py`

[ ] `LOGIC-231` — 2 float-for-money signal(s); first: `salary: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/hr.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `salary: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/schemas.py`

[ ] `LOGIC-232` — 2 float-for-money signal(s); first: `salary: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/hr/schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/suppliers.py`

[ ] `LOGIC-234` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/suppliers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/logistics.py`

[ ] `LOGIC-236` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/logistics/routers/logistics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 1 float-for-money signal(s); first: `total_revenue: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/analytics.py`

[ ] `LOGIC-237` — 1 float-for-money signal(s); first: `total_revenue: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/analytics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 4 float-for-money signal(s); first: `base_price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/logistics.py`

[ ] `LOGIC-239` — 4 float-for-money signal(s); first: `base_price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/logistics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 3 float-for-money signal(s); first: `total: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/serializers/supplier_serializers.py`

[ ] `LOGIC-240` — 3 float-for-money signal(s); first: `total: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/serializers/supplier_serializers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` — 5 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/bg_removal/bg_removal_service.py`

[ ] `LOGIC-247` — 5 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/bg_removal/bg_removal_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/qr/qr_generator.py`

[ ] `LOGIC-255` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/qr/qr_generator.py | head -20`

_This wave has 54 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 3 · Close coverage, quality and performance defects

#### Work packages in wave 3 (48)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 22 | 1 | 0 | 0 | 22.0 | 1x rel lazy in table `dynamic_qr_sessions`: relationship `employee` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 16 | 1 | 0 | 0 | 16.0 | 1x rel lazy in table `announcements`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 15 | 1 | 0 | 0 | 15.0 | 3x rel lazy in table `country_staff_assignments`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 10 | 1 | 0 | 0 | 10.0 | 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy= |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-BG` | 9 | 1 | 0 | 0 | 9.0 | env var `BG_ALLOW_HEAVY_MODELS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 7 | 1 | 0 | 0 | 7.0 | 1x rel lazy in table `payment_orchestrator_syncs`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 5 | 1 | 0 | 0 | 5.0 | 1x rel lazy in table `user_login_histories`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 5 | 1 | 0 | 0 | 5.0 | 1x rel lazy in table `logistics_partner_profiles`: relationship `partner` has no lazy= |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 4 | 1 | 0 | 0 | 4.0 | env var `DB_SEARCH_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 4 | 1 | 0 | 0 | 4.0 | env var `AZURE_CLIENT_ID` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 3 | 1 | 0 | 0 | 3.0 | env var `BG_REMOVAL_MODEL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-CO` | 3 | 1 | 0 | 0 | 3.0 | env var `WHATSAPP_MODE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 0 | 0 | 3.0 | 2x rel lazy in table `product_types`: relationship `coc_category` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 0 | 0 | 3.0 | 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 3 | 1 | 0 | 0 | 3.0 | 2x rel lazy in table `fraud_cases`: relationship `assignee` has no lazy= |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 2 | 1 | 0 | 0 | 2.0 | env var `ML_WORKER_IDLE_SHUTDOWN` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 2 | 1 | 0 | 0 | 2.0 | env var `AI_USE_OLLAMA_TEXT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` | 2 | 1 | 0 | 0 | 2.0 | env var `ZOZI_MCP_PASSWORD` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `carts`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `onboarding_steps`: relationship `pipeline` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 0 | 2.0 | 2x rel lazy in table `ai_staging_products`: relationship `job` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `commission_profiles`: relationship `rules` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 0 | 2.0 | 4x rel lazy in table `products`: relationship `category_rel` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 0 | 2.0 | 2x rel lazy in table `incident_threads`: relationship `war_room` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 0 | 2.0 | 3x rel lazy in table `country_communications`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `supplier_documents`: relationship `supplier` has no lazy= |
| `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 1.0 | env var `ENCRYPTION_SALT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 1.0 | env var `MEDIA_STORAGE_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 1.0 | env var `TURNSTILE_SECRET_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 1.0 | env var `ZOZI_VAULT_MASTER_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 1.0 | env var `PYTEST_CURRENT_TEST` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 1.0 | env var `MAX_PAGE_SIZE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-JOBS-MCP-MAR` | 1 | 1 | 0 | 0 | 1.0 | env var `ZOZI_MCP_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-MAIN-PY` | 1 | 1 | 0 | 0 | 1.0 | env var `LOG_FILE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-C` | 1 | 1 | 0 | 0 | 1.0 | env var `CSRF_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-R` | 1 | 1 | 0 | 0 | 1.0 | env var `REQUEST_TIMEOUT_SECONDS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-S` | 1 | 1 | 0 | 0 | 1.0 | env var `FRONTEND_WS_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AN` | 1 | 1 | 0 | 0 | 1.0 | env var `ANALYTICS_API_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-SE` | 1 | 1 | 0 | 0 | 1.0 | env var `WATCHLIST_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-HTTP-HEADERS` | 1 | 1 | 0 | 0 | 1.0 | the security middleware emits X-XSS-Protection (1 site(s)) |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `email_campaigns`: relationship `recipients` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 1.0 | 2x rel lazy in table `referral_point_events`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `tax_rules`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 1.0 | 2x rel lazy in table `logistics_cod_remittance_receipts`: relationship `settlement` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `banners`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 1.0 | 2x rel lazy in table `kyc_verifications`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `permissions`: relationship `category` has no lazy= |

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` — 1x rel lazy in table `dynamic_qr_sessions`: relationship `employee` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 22 (0 closed) · **files:** 1 · **est.:** 22.0h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `TF-204` — 1x rel lazy in table `dynamic_qr_sessions`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on dynamic_qr_sessions
[ ] `TF-207` — 1x rel lazy in table `employee_biometrics`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_biometrics
[ ] `TF-210` — 1x rel lazy in table `geo_fence_logs`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on geo_fence_logs
[ ] `TF-212` — 18x rel lazy in table `employees`: relationship `office` has no lazy=
    - do: Fix rel-lazy on employees
[ ] `TF-213` — 1x rel lazy in table `employee_attendances`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_attendances
[ ] `TF-214` — 1x rel lazy in table `employee_work_logs`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_work_logs
[ ] `TF-215` — 1x rel lazy in table `employee_leave_requests`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_leave_requests
[ ] `TF-216` — 1x rel lazy in table `employee_leave_ledgers`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_leave_ledgers
    - … and 14 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `announcements`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 16 (0 closed) · **files:** 1 · **est.:** 16.0h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `TF-066` — 1x rel lazy in table `announcements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on announcements
[ ] `TF-071` — 3x rel lazy in table `proxy_channels`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_channels
[ ] `TF-072` — 5x rel lazy in table `proxy_sessions`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_sessions
[ ] `TF-073` — 4x rel lazy in table `proxy_messages`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_messages
[ ] `TF-074` — 4x rel lazy in table `proxy_call_logs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_call_logs
[ ] `TF-075` — 1x rel lazy in table `employee_communication_threads`: relationship `country` has no lazy=
    - do: Fix rel-lazy on employee_communication_threads
[ ] `TF-076` — 2x rel lazy in table `external_contact_maskings`: relationship `country` has no lazy=
    - do: Fix rel-lazy on external_contact_maskings
[ ] `TF-077` — 2x rel lazy in table `communication_audit_trails`: relationship `country` has no lazy=
    - do: Fix rel-lazy on communication_audit_trails
    - … and 8 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 3x rel lazy in table `country_staff_assignments`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 15 (0 closed) · **files:** 1 · **est.:** 15.0h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `TF-129` — 3x rel lazy in table `country_staff_assignments`: relationship `user` has no lazy=
    - do: Fix rel-lazy on country_staff_assignments
[ ] `TF-133` — 1x rel lazy in table `supplier_kyc_requirements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on supplier_kyc_requirements
[ ] `TF-135` — 1x rel lazy in table `logistics_partner_kyc_requirements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on logistics_partner_kyc_requirements
[ ] `TF-136` — 1x rel lazy in table `country_commission_rates`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_commission_rates
[ ] `TF-138` — 1x rel lazy in table `country_localizations`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_localizations
[ ] `TF-139` — 1x rel lazy in table `country_payment_aliases`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_payment_aliases
[ ] `TF-141` — 1x rel lazy in table `country_legal_contracts`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_legal_contracts
[ ] `TF-142` — 2x rel lazy in table `country_category_tax_rates`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_category_tax_rates
    - … and 7 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 10 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/comms/models/chat.py`

[ ] `TF-038` — 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy=
    - do: Fix rel-lazy on entity_chat_threads
[ ] `TF-039` — 3x rel lazy in table `video_rooms`: relationship `participants` has no lazy=
    - do: Fix rel-lazy on video_rooms
[ ] `TF-041` — 2x rel lazy in table `video_room_participants`: relationship `room` has no lazy=
    - do: Fix rel-lazy on video_room_participants
[ ] `TF-043` — 1x rel lazy in table `direct_chat_rooms`: relationship `messages` has no lazy=
    - do: Fix rel-lazy on direct_chat_rooms
[ ] `TF-047` — 2x rel lazy in table `group_chat_members`: relationship `room` has no lazy=
    - do: Fix rel-lazy on group_chat_members
[ ] `TF-054` — 2x rel lazy in table `entity_chat_messages`: relationship `thread` has no lazy=
    - do: Fix rel-lazy on entity_chat_messages
[ ] `TF-055` — 2x rel lazy in table `video_room_recordings`: relationship `room` has no lazy=
    - do: Fix rel-lazy on video_room_recordings
[ ] `TF-056` — 2x rel lazy in table `direct_chat_messages`: relationship `room` has no lazy=
    - do: Fix rel-lazy on direct_chat_messages
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-BG` — env var `BG_ALLOW_HEAVY_MODELS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 9.0h
- **files:** `backend/providers/bg_removal/bg_removal_service.py`

[ ] `ENV-020` — env var `BG_ALLOW_HEAVY_MODELS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_ALLOW_HEAVY_MODELS to typed settings and .env.example
[ ] `ENV-021` — env var `BG_DEFAULT_STRATEGY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_DEFAULT_STRATEGY to typed settings and .env.example
[ ] `ENV-022` — env var `BG_HEAVY_COOLDOWN` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_HEAVY_COOLDOWN to typed settings and .env.example
[ ] `ENV-023` — env var `BG_HEAVY_THREADS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_HEAVY_THREADS to typed settings and .env.example
[ ] `ENV-024` — env var `BG_LIGHTWEIGHT_MODE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_LIGHTWEIGHT_MODE to typed settings and .env.example
[ ] `ENV-025` — env var `BG_LIGHT_COOLDOWN` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_LIGHT_COOLDOWN to typed settings and .env.example
[ ] `ENV-026` — env var `BG_LIGHT_THREADS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_LIGHT_THREADS to typed settings and .env.example
[ ] `ENV-027` — env var `BG_MODEL_LOAD_MIN_MB` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_MODEL_LOAD_MIN_MB to typed settings and .env.example
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-env-undeclared`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `payment_orchestrator_syncs`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 7 (0 closed) · **files:** 1 · **est.:** 7.0h
- **files:** `backend/domains/country/models/country_control.py`

[ ] `TF-117` — 1x rel lazy in table `payment_orchestrator_syncs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on payment_orchestrator_syncs
[ ] `TF-118` — 2x rel lazy in table `supplier_onboarding_syncs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on supplier_onboarding_syncs
[ ] `TF-119` — 1x rel lazy in table `data_residency_records`: relationship `country` has no lazy=
    - do: Fix rel-lazy on data_residency_records
[ ] `TF-120` — 1x rel lazy in table `country_map_configs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_map_configs
[ ] `TF-121` — 1x rel lazy in table `shop_warehouse_locations`: relationship `country` has no lazy=
    - do: Fix rel-lazy on shop_warehouse_locations
[ ] `TF-122` — 2x rel lazy in table `logistics_partner_locations`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_partner_locations
[ ] `TF-123` — 2x rel lazy in table `parcel_location_trackers`: relationship `parcel` has no lazy=
    - do: Fix rel-lazy on parcel_location_trackers

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `user_login_histories`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 5 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/accounts/models/user.py`

[ ] `TF-009` — 1x rel lazy in table `user_login_histories`: relationship `user` has no lazy=
    - do: Fix rel-lazy on user_login_histories
[ ] `TF-010` — 1x rel lazy in table `user_devices`: relationship `user` has no lazy=
    - do: Fix rel-lazy on user_devices
[ ] `TF-011` — 1x rel lazy in table `password_reset_tokens`: relationship `user` has no lazy=
    - do: Fix rel-lazy on password_reset_tokens
[ ] `TF-012` — 1x rel lazy in table `email_verification_tokens`: relationship `user` has no lazy=
    - do: Fix rel-lazy on email_verification_tokens
[ ] `TF-013` — 1x rel lazy in table `revoked_tokens`: relationship `user` has no lazy=
    - do: Fix rel-lazy on revoked_tokens

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 1x rel lazy in table `logistics_partner_profiles`: relationship `partner` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 5 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `TF-242` — 1x rel lazy in table `logistics_partner_profiles`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_partner_profiles
[ ] `TF-246` — 2x rel lazy in table `logistics_pricing_profiles`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_pricing_profiles
[ ] `TF-248` — 2x rel lazy in table `logistics_vehicle_rules`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_vehicle_rules
[ ] `TF-250` — 2x rel lazy in table `logistics_category_pricing_rules`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_category_pricing_rules
[ ] `TF-252` — 1x rel lazy in table `shipments`: relationship `assigned_partner` has no lazy=
    - do: Fix rel-lazy on shipments

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `DB_SEARCH_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `ENV-030` — env var `DB_SEARCH_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add DB_SEARCH_PATH to typed settings and .env.example
[ ] `ENV-031` — env var `DB_SSL_CERT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add DB_SSL_CERT to typed settings and .env.example
[ ] `ENV-032` — env var `DB_SSL_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add DB_SSL_KEY to typed settings and .env.example
[ ] `ENV-033` — env var `DB_SSL_ROOT_CERT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add DB_SSL_ROOT_CERT to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `AZURE_CLIENT_ID` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/infrastructure/security/secrets_manager.py`

[ ] `ENV-016` — env var `AZURE_CLIENT_ID` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AZURE_CLIENT_ID to typed settings and .env.example
[ ] `ENV-017` — env var `AZURE_CLIENT_SECRET` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AZURE_CLIENT_SECRET to typed settings and .env.example
[ ] `ENV-018` — env var `AZURE_KEY_VAULT_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AZURE_KEY_VAULT_URL to typed settings and .env.example
[ ] `ENV-019` — env var `AZURE_TENANT_ID` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AZURE_TENANT_ID to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` — env var `BG_REMOVAL_MODEL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/providers/ai/image_ai_service.py`

[ ] `ENV-028` — env var `BG_REMOVAL_MODEL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add BG_REMOVAL_MODEL to typed settings and .env.example
[ ] `ENV-041` — env var `MULTIVIEW_SPACE_ID` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add MULTIVIEW_SPACE_ID to typed settings and .env.example
[ ] `ENV-050` — env var `ZERO123_MODEL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ZERO123_MODEL to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-CO` — env var `WHATSAPP_MODE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/providers/comms/whatsapp_selfhosted.py`

[ ] `ENV-047` — env var `WHATSAPP_MODE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add WHATSAPP_MODE to typed settings and .env.example
[ ] `ENV-048` — env var `WHATSAPP_RATE_LIMIT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add WHATSAPP_RATE_LIMIT to typed settings and .env.example
[ ] `ENV-049` — env var `WHATSAPP_SESSION_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add WHATSAPP_SESSION_PATH to typed settings and .env.example

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 2x rel lazy in table `product_types`: relationship `coc_category` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/catalog/models/chart_of_categories.py`

[ ] `TF-020` — 2x rel lazy in table `product_types`: relationship `coc_category` has no lazy=
    - do: Fix rel-lazy on product_types
[ ] `TF-021` — 2x rel lazy in table `category_attributes`: relationship `product_type` has no lazy=
    - do: Fix rel-lazy on category_attributes
[ ] `TF-022` — 1x rel lazy in table `category_attribute_values`: relationship `attribute` has no lazy=
    - do: Fix rel-lazy on category_attribute_values

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/comms/models/communication_schema_models.py`

[ ] `TF-089` — 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy=
    - do: Fix rel-lazy on support_tickets
[ ] `TF-090` — 2x rel lazy in table `support_ticket_replies`: relationship `ticket` has no lazy=
    - do: Fix rel-lazy on support_ticket_replies
[ ] `TF-091` — 2x rel lazy in table `ticket_attachments`: relationship `ticket_reply` has no lazy=
    - do: Fix rel-lazy on ticket_attachments

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `fraud_cases`: relationship `assignee` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/security/models/fraud.py`

[ ] `TF-278` — 2x rel lazy in table `fraud_cases`: relationship `assignee` has no lazy=
    - do: Fix rel-lazy on fraud_cases
[ ] `TF-279` — 3x rel lazy in table `fraud_case_assignments`: relationship `case` has no lazy=
    - do: Fix rel-lazy on fraud_case_assignments
[ ] `TF-280` — 2x rel lazy in table `dlp_violations`: relationship `sender` has no lazy=
    - do: Fix rel-lazy on dlp_violations

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `ML_WORKER_IDLE_SHUTDOWN` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/infrastructure/ml/worker.py`

[ ] `ENV-039` — env var `ML_WORKER_IDLE_SHUTDOWN` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ML_WORKER_IDLE_SHUTDOWN to typed settings and .env.example
[ ] `ENV-040` — env var `ML_WORKER_POLL_INTERVAL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ML_WORKER_POLL_INTERVAL to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` — env var `AI_USE_OLLAMA_TEXT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/providers/ai/ai_variant_config.py`

[ ] `ENV-013` — env var `AI_USE_OLLAMA_TEXT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AI_USE_OLLAMA_TEXT to typed settings and .env.example
[ ] `ENV-014` — env var `AI_USE_VISION` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add AI_USE_VISION to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AI` — env var `ZOZI_MCP_PASSWORD` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/providers/ai/zozi_mcp.py`

[ ] `ENV-052` — env var `ZOZI_MCP_PASSWORD` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ZOZI_MCP_PASSWORD to typed settings and .env.example
[ ] `ENV-053` — env var `ZOZI_MCP_USERNAME` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ZOZI_MCP_USERNAME to typed settings and .env.example

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `carts`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `TF-002` — 1x rel lazy in table `carts`: relationship `user` has no lazy=
    - do: Fix rel-lazy on carts
[ ] `TF-003` — 2x rel lazy in table `cart_items`: relationship `user` has no lazy=
    - do: Fix rel-lazy on cart_items

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `onboarding_steps`: relationship `pipeline` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/accounts/models/onboarding.py`

[ ] `TF-005` — 1x rel lazy in table `onboarding_steps`: relationship `pipeline` has no lazy=
    - do: Fix rel-lazy on onboarding_steps
[ ] `TF-006` — 1x rel lazy in table `ocr_results`: relationship `document_verification` has no lazy=
    - do: Fix rel-lazy on ocr_results

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 2x rel lazy in table `ai_staging_products`: relationship `job` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/catalog/models/ai_upload.py`

[ ] `TF-017` — 2x rel lazy in table `ai_staging_products`: relationship `job` has no lazy=
    - do: Fix rel-lazy on ai_staging_products
[ ] `TF-018` — 1x rel lazy in table `ai_staging_variants`: relationship `staging_product` has no lazy=
    - do: Fix rel-lazy on ai_staging_variants

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 1x rel lazy in table `commission_profiles`: relationship `rules` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/catalog/models/commission.py`

[ ] `TF-024` — 1x rel lazy in table `commission_profiles`: relationship `rules` has no lazy=
    - do: Fix rel-lazy on commission_profiles
[ ] `TF-025` — 2x rel lazy in table `commission_rules`: relationship `profile` has no lazy=
    - do: Fix rel-lazy on commission_rules

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 4x rel lazy in table `products`: relationship `category_rel` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/catalog/models/products.py`

[ ] `TF-027` — 4x rel lazy in table `products`: relationship `category_rel` has no lazy=
    - do: Fix rel-lazy on products
[ ] `TF-034` — 1x rel lazy in table `product_filter_options`: relationship `filter_metadata` has no lazy=
    - do: Fix rel-lazy on product_filter_options

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 2x rel lazy in table `incident_threads`: relationship `war_room` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/comms/models/incident.py`

[ ] `TF-095` — 2x rel lazy in table `incident_threads`: relationship `war_room` has no lazy=
    - do: Fix rel-lazy on incident_threads
[ ] `TF-096` — 2x rel lazy in table `incident_action_items`: relationship `war_room` has no lazy=
    - do: Fix rel-lazy on incident_action_items

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 3x rel lazy in table `country_communications`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/country/models/countries.py`

[ ] `TF-111` — 3x rel lazy in table `country_communications`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_communications
[ ] `TF-112` — 1x rel lazy in table `country_gateway_credentials`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_gateway_credentials

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` — 1x rel lazy in table `supplier_documents`: relationship `supplier` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-291` — 1x rel lazy in table `supplier_documents`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on supplier_documents
[ ] `TF-298` — 1x rel lazy in table `supplier_badge_billing_histories`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on supplier_badge_billing_histories

##### `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SECU` — env var `ENCRYPTION_SALT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/security/services/security_provider_helpers.py`

[ ] `ENV-034` — env var `ENCRYPTION_SALT` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ENCRYPTION_SALT to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-DOMAINS-SUPP` — env var `MEDIA_STORAGE_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders.py`

[ ] `ENV-038` — env var `MEDIA_STORAGE_PATH` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add MEDIA_STORAGE_PATH to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `TURNSTILE_SECRET_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/security/dependencies.py`

[ ] `ENV-044` — env var `TURNSTILE_SECRET_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add TURNSTILE_SECRET_KEY to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `ZOZI_VAULT_MASTER_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/security/vault.py`

[ ] `ENV-054` — env var `ZOZI_VAULT_MASTER_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ZOZI_VAULT_MASTER_KEY to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `PYTEST_CURRENT_TEST` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/utils/background_jobs.py`

[ ] `ENV-042` — env var `PYTEST_CURRENT_TEST` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add PYTEST_CURRENT_TEST to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-INFRASTRUCTU` — env var `MAX_PAGE_SIZE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/utils/pagination.py`

[ ] `ENV-037` — env var `MAX_PAGE_SIZE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add MAX_PAGE_SIZE to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-JOBS-MCP-MAR` — env var `ZOZI_MCP_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/jobs/mcp_marketplace_server.py`

[ ] `ENV-051` — env var `ZOZI_MCP_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ZOZI_MCP_API_URL to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-MAIN-PY` — env var `LOG_FILE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/main.py`

[ ] `ENV-036` — env var `LOG_FILE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add LOG_FILE to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-C` — env var `CSRF_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/csrf_middleware.py`

[ ] `ENV-029` — env var `CSRF_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add CSRF_DISABLED to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-R` — env var `REQUEST_TIMEOUT_SECONDS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/request_timeout_middleware.py`

[ ] `ENV-043` — env var `REQUEST_TIMEOUT_SECONDS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add REQUEST_TIMEOUT_SECONDS to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-MIDDLEWARE-S` — env var `FRONTEND_WS_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `ENV-035` — env var `FRONTEND_WS_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add FRONTEND_WS_URL to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-AN` — env var `ANALYTICS_API_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/analytics/analytics.py`

[ ] `ENV-015` — env var `ANALYTICS_API_KEY` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add ANALYTICS_API_KEY to typed settings and .env.example

##### `WP3-ENV-UNDECLARED-BACKEND-PROVIDERS-SE` — env var `WATCHLIST_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/security/watchlist.py`

[ ] `ENV-046` — env var `WATCHLIST_API_URL` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add WATCHLIST_API_URL to typed settings and .env.example

##### `WP3-HTTP-HEADERS` — the security middleware emits X-XSS-Protection (1 site(s))

- **cluster:** `CLUSTER-http-headers` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `SEC-xss-header-removed` — the security middleware emits X-XSS-Protection (1 site(s))
    - do: delete the X-XSS-Protection header and rely on the CSP
    - verify: `grep -rn 'x-xss-protection' backend/middleware`

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `email_campaigns`: relationship `recipients` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/marketing.py`

[ ] `TF-100` — 1x rel lazy in table `email_campaigns`: relationship `recipients` has no lazy=
    - do: Fix rel-lazy on email_campaigns

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` — 2x rel lazy in table `referral_point_events`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/customers/models/customer_schema_models.py`

[ ] `TF-162` — 2x rel lazy in table `referral_point_events`: relationship `user` has no lazy=
    - do: Fix rel-lazy on referral_point_events

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` — 1x rel lazy in table `tax_rules`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/finance/models/tax_rules.py`

[ ] `TF-190` — 1x rel lazy in table `tax_rules`: relationship `country` has no lazy=
    - do: Fix rel-lazy on tax_rules

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` — 2x rel lazy in table `logistics_cod_remittance_receipts`: relationship `settlement` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/governance/models/admin.py`

[ ] `TF-198` — 2x rel lazy in table `logistics_cod_remittance_receipts`: relationship `settlement` has no lazy=
    - do: Fix rel-lazy on logistics_cod_remittance_receipts

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `TF-267` — 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy=
    - do: Fix rel-lazy on coupon_usages

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `banners`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/promotions.py`

[ ] `TF-271` — 1x rel lazy in table `banners`: relationship `country` has no lazy=
    - do: Fix rel-lazy on banners

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `kyc_verifications`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/security/models/security_schema_models.py`

[ ] `TF-286` — 2x rel lazy in table `kyc_verifications`: relationship `user` has no lazy=
    - do: Fix rel-lazy on kyc_verifications

##### `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` — 1x rel lazy in table `permissions`: relationship `category` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/rbac/models/permission_entities.py`

[ ] `TF-302` — 1x rel lazy in table `permissions`: relationship `category` has no lazy=
    - do: Fix rel-lazy on permissions

_This wave has 156 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 4 · Verification tasks for untrusted claims

#### Work packages in wave 4 (554)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP4-WORKFLOW-RUNTIME` | 10 | 3 | 9 | 10 | 23.5 | `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_CREATED`, which is not defined anywhere in t… |
| `WP4-STUB-SUBSCRIBER` | 4 | 4 | 4 | 4 | 10.0 | stub subscriber module: 3 handlers, 3 `# Future:` markers |
| `WP4-PAYMENT-WEBHOOK` | 3 | 3 | 3 | 3 | 3.0 | payment adapter references webhooks but shows no signature verification |
| `WP4-RLS` | 4 | 4 | 2 | 4 | 7.0 | canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed |
| `WP4-CONTRADICTION-TARGET-VS-CODE` | 3 | 3 | 2 | 3 | 7.5 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists |
| `WP4-BROWSER-RUNNER-BROKEN` | 2 | 1 | 2 | 2 | 12.0 | Playwright run produced no executable tests: ReferenceError: __dirname is not defined in ES module scope |
| `WP4-PAYMENT-CREDENTIALS` | 2 | 2 | 2 | 2 | 3.5 | payment gateway secret columns appear to be plain String (no encryption marker) |
| `WP4-STARTUP` | 2 | 2 | 2 | 2 | 2.0 | startup logged an error from lifespan/Failed to start backup manager (non-critical): Settings has no attribute |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` | 2 | 1 | 2 | 2 | 5.0 | 47 endpoint(s) across 13 router(s) have no visible auth/gate dependency (sample: backend/modules/admin/routers/analytic… |
| `WP4-WS-AUTH` | 2 | 1 | 2 | 2 | 5.0 | websocket `websocket_user` accepts without token verification |
| `WP4-EVENT-SPINE` | 2 | 2 | 1 | 2 | 22.5 | 44 of 79 event handlers (44/79) log and return without performing the write they imply |
| `WP4-AP-TODO-ONLY-IMPLEMENTATION` | 1 | 1 | 1 | 1 | 2.5 | TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1` |
| `WP4-AP-UNIMPLEMENTED-PLACEHOLDER` | 1 | 1 | 1 | 1 | 2.5 | Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service… |
| `WP4-CHAIN-CHAIN-005` | 1 | 1 | 1 | 1 | 6.0 | CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes |
| `WP4-CONTRADICTION-DOC-VS-CODE` | 1 | 1 | 1 | 1 | 2.5 | one router per module: every router file registered | modules/employee/routers/: hr.py file and hr/ package coexist |
| `WP4-CONTRADICTION-FRONTEND-VS-BACKEND` | 1 | 1 | 1 | 1 | 2.5 | Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists |
| `WP4-EXTRA-MODULE` | 1 | 1 | 1 | 1 | 2.5 | top-level module `finance` exists |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"rate": float(rule.rate),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `"amount": float(converted_total),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"amount": float(p.amount),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price",… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 1 | 2.5 | 39 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `total=float(total_amount),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `min_amount: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `min_payout_amount: float` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` |
| `WP4-SSRF` | 1 | 1 | 1 | 1 | 2.5 | 22 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authoriza… |
| `WP4-TABLE-DRIFT` | 1 | 1 | 1 | 1 | 2.5 | migrations reference schemas no ORM model declares: customer(5), commerce(1) |
| `WP4-UNCATEGORISED-BACKEND` | 1 | 1 | 1 | 1 | 6.0 | ruff reports 6604 violation(s); top rules: E402=2065, F401=1984, F821=1443, F811=1112 |
| `WP4-UNCATEGORISED-BACKEND-TESTS-ARCHIT` | 1 | 1 | 1 | 1 | 6.0 | the architecture-law suite did not finish in 449.55s (exit 1); 50 failure(s) and 5 error(s) were observed before it sto… |
| `WP4-UNCATEGORISED-FRONTEND-WEB-APP` | 1 | 1 | 1 | 1 | 6.0 | 119 TypeScript error(s) across 29 file(s) |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` | 1 | 1 | 1 | 1 | 2.5 | endpoint `get_rbac_catalog` has no visible auth/feature gate |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 27 | 1 | 0 | 27 | 71.0 | function `serialize_pricing_profile` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (norma… |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 25 | 1 | 0 | 25 | 62.5 | endpoint `push_notifications_health` has no visible auth/feature gate |
| `WP4-ALLOWLIST` | 20 | 1 | 0 | 20 | 50.0 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.mod… |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 20 | 1 | 0 | 20 | 20.0 | 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 20 | 1 | 0 | 20 | 53.5 | function `scan_lookup_shipment` duplicates `backend/domains/logistics/services/core/logistics_service.py` (normalized A… |
| `WP4-TF-MISSING-COUNTRY-CODE` | 18 | 8 | 0 | 18 | 18.0 | 1x missing country_code in table `entity_chat_threads`: user-facing table `entity_chat_threads` lacks `country_code` |
| `WP4-CIRCULAR-IMPORT` | 17 | 10 | 0 | 17 | 42.5 | circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -… |
| `WP4-INFRA-IMPORTS-ABOVE` | 15 | 12 | 0 | 15 | 37.5 | `infra imports above`: imports `domains` |
| `WP4-JOB-RESILIENCE` | 14 | 14 | 0 | 14 | 35.0 | celery task module with no DLQ reference |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-FINA` | 14 | 1 | 0 | 14 | 35.0 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 14 | 1 | 0 | 14 | 38.5 | function `get_supplier_bank_account` duplicates `backend/domains/finance/services/country/supplier_finance_service.py`… |
| `WP4-VERSION-DRIFT` | 13 | 4 | 0 | 13 | 13.0 | `eslint: ^9` does not satisfy pinned `10` |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` | 11 | 1 | 0 | 11 | 27.5 | function `_fetch_rss` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py` (normalized… |
| `WP4-HTTP-CSP` | 10 | 1 | 0 | 10 | 10.0 | CSP on `/health`: uses report-uri, superseded by report-to |
| `WP4-TF-FK-ONDELETE` | 10 | 6 | 0 | 10 | 10.0 | 1x fk ondelete in table `audit_logs`: FK `country_code` has no ondelete |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 9 | 1 | 0 | 9 | 9.0 | 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default |
| `WP4-FEATURE-GATE` | 8 | 5 | 0 | 8 | 9.5 | `require_feature("catalog.review.create")` gates on a feature that no features.py declares |
| `WP4-TF-MISSING-UPDATED-AT` | 8 | 5 | 0 | 8 | 8.0 | 1x missing updated_at in table `group_chat_members`: table `group_chat_members` lacks `updated_at` |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 8 | 1 | 0 | 8 | 20.0 | function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST) |
| `WP4-LAW-CODE-QUALITY` | 7 | 1 | 0 | 7 | 7.0 | Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s) |
| `WP4-TEST-NO-ASSERT` | 7 | 7 | 0 | 7 | 17.5 | test file contains no assertions |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-CUST` | 7 | 1 | 0 | 7 | 17.5 | endpoint `login` has no visible auth/feature gate |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 6 | 1 | 0 | 6 | 15.0 | cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 21 occurrence(s) in thi… |
| `WP4-LAW-ARCHITECTURE` | 6 | 1 | 0 | 6 | 6.0 | Law 1 (Arrows point down) violated: 33 reverse-layer import(s) |
| `WP4-SUPPLY-CHAIN` | 6 | 4 | 0 | 6 | 6.0 | no dependency scanning step in CI |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 6 | 1 | 0 | 6 | 6.0 | 2x rel lazy in table `fraud_events`: relationship `user` has no lazy= |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 6 | 1 | 0 | 6 | 6.0 | 2x timestamp default in table `entity_chat_threads`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 0 | 6 | 6.0 | 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` | 6 | 1 | 0 | 6 | 6.0 | 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 6 | 1 | 0 | 6 | 15.0 | function `_build_postgres_tsquery` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized A… |
| `WP4-FORBIDDEN-PACKAGE` | 5 | 2 | 0 | 5 | 5.0 | forbidden package declared: `prometheus-client`==0.26.0 |
| `WP4-LAW-DATABASE` | 5 | 1 | 0 | 5 | 5.0 | Law 45 (No N+1 queries) violated: 305/390 relationship(s) without lazy= |
| `WP4-TF-MISSING-CREATED-AT` | 5 | 3 | 0 | 5 | 5.0 | 1x missing created_at in table `video_room_participants`: table `video_room_participants` lacks `created_at` |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 5 | 1 | 0 | 5 | 12.5 | function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized A… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 4 | 10.0 | cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this… |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 4 | 1 | 0 | 4 | 10.0 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` |
| `WP4-TF-MISSING-IS-DELETED` | 4 | 3 | 0 | 4 | 4.0 | 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted` |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 4 | 1 | 0 | 4 | 4.0 | 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 4 | 4.0 | 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy= |
| `WP4-TF-SCHEMA-UNKNOWN` | 4 | 1 | 0 | 4 | 4.0 | 1x schema unknown in table `payment_methods`: schema `payments` is not canonical |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 0 | 4 | 4.0 | 1x timestamp default in table `announcements`: `updated_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 0 | 4 | 4.0 | 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 0 | 4 | 4.0 | 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 0 | 4 | 4.0 | 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-COMM` | 4 | 1 | 0 | 4 | 10.0 | function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized A… |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-HR-S` | 4 | 1 | 0 | 4 | 10.0 | function `validate_work_hours` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 4 | 10.0 | function `get_country_communications` duplicates `backend/domains/country/services/core/country_service.py` (normalized… |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 4 | 10.0 | function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST) |
| `WP4-COLOR-DRIFT` | 3 | 1 | 0 | 3 | 46.0 | 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files exc… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 3 | 1 | 0 | 3 | 7.5 | cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file |
| `WP4-DESIGN-PRIMITIVES` | 3 | 2 | 0 | 3 | 11.0 | 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive |
| `WP4-DUPLICATE-FILE` | 3 | 3 | 0 | 3 | 7.5 | byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py |
| `WP4-INTERACTION-BUTTON` | 3 | 1 | 0 | 3 | 4.5 | 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit |
| `WP4-INTERACTION-MODAL` | 3 | 1 | 0 | 3 | 9.5 | 28 destructive control(s) in 8 modal file(s) with no confirmation step |
| `WP4-LAW-SECURITY` | 3 | 1 | 0 | 3 | 3.0 | Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s) |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 3 | 1 | 0 | 3 | 7.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 3 | 1 | 0 | 3 | 7.5 | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` |
| `WP4-PROVIDER-RESILIENCE` | 3 | 1 | 0 | 3 | 7.5 | circuit breaker present in 8/94 provider modules |
| `WP4-RUNBOOKS` | 3 | 3 | 0 | 3 | 7.5 | no deploy runbook found |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 3 | 1 | 0 | 3 | 3.0 | 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy= |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-AUDI` | 3 | 1 | 0 | 3 | 7.5 | function `get_residency_config` duplicates `backend/domains/audit/services/data_residency_service.py` (normalized AST) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 3 | 1 | 0 | 3 | 7.5 | function `admin_email_stats` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST) |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 3 | 1 | 0 | 3 | 7.5 | endpoint `list_employees_public` has no visible auth/feature gate |
| `WP4-CI-CD` | 2 | 1 | 0 | 2 | 5.0 | pipeline lacks: secret scanning |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurren… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in t… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 2 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this f… |
| `WP4-DB-POOL` | 2 | 1 | 0 | 2 | 2.0 | no pool_size configuration found |
| `WP4-EXTRA-DOMAIN` | 2 | 2 | 0 | 2 | 5.0 | domain package `media` exists |
| `WP4-INTENT-STUB` | 2 | 2 | 0 | 2 | 2.0 | 1 placeholder response(s) ('not yet wired') in live module |
| `WP4-LAW-PROVIDER` | 2 | 1 | 0 | 2 | 2.0 | Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic |
| `WP4-LAW-STRUCTURE` | 2 | 1 | 0 | 2 | 2.0 | Law 12 (15 domains) violated: extra domain(s): media, payments |
| `WP4-MIDDLEWARE-IMPORTS-ABOVE` | 2 | 2 | 0 | 2 | 5.0 | `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 2 | 1 | 0 | 2 | 5.0 | `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 2 | 1 | 0 | 2 | 5.0 | `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 2 | 1 | 0 | 2 | 5.0 | `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_html` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 2 | 1 | 0 | 2 | 5.0 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 2 | 2.0 | 1x rel lazy in table `categories`: relationship `products` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 2 | 2.0 | 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 2 | 2.0 | 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 2 | 2.0 | 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 2 | 1 | 0 | 2 | 2.0 | 1x rel lazy in table `coupons`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 2 | 2.0 | 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy= |
| `WP4-TF-SCHEMA-MISSING` | 2 | 1 | 0 | 2 | 2.0 | 1x schema missing in table `payroll_records`: table `payroll_records` has no schema declaration |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 2 | 2.0 | 2x timestamp default in table `country_configs`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 2 | 2.0 | 2x timestamp default in table `referrals`: `created_at` uses Python-side default |
| `WP4-UNCATEGORISED-ZOZI-AUDIT` | 2 | 1 | 0 | 2 | 2.0 | check `arch_router_thinness` failed: crashed: NameError: name 'DB_CALL_RE' is not defined |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 2 | 5.0 | function `get_cities_dropdown` duplicates `backend/domains/country/services/country_dropdown_service.py` (normalized AS… |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 2 | 5.0 | function `_normalize_address_payload` duplicates `backend/domains/accounts/services/addresses/addresses_service.py` (no… |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` | 2 | 1 | 0 | 2 | 5.0 | function `admin_email_stats` duplicates `backend/domains/governance/services/admin/admin_service.py` (normalized AST) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 2 | 1 | 0 | 2 | 5.0 | function `list_logistics_partner_locations` duplicates `backend/domains/logistics/services/core/logistics_locations_ser… |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 2 | 1 | 0 | 2 | 5.0 | endpoint `shift_handover_health` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 2 | 1 | 0 | 2 | 5.0 | endpoint `list_assigned_shipments` has no visible auth/feature gate |
| `WP4-AP-EMPTY-HANDLER-PASS` | 1 | 1 | 0 | 1 | 1.0 | Empty handler (pass): 4 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270` |
| `WP4-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` | 1 | 1 | 0 | 1 | 1.0 | Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3… |
| `WP4-AP-TODO-ONLY` | 1 | 1 | 0 | 1 | 6.0 | TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58 |
| `WP4-BASE-IMAGE` | 1 | 1 | 0 | 1 | 1.0 | dev database image `postgres:18-alpine` (documented: postgres:16-alpine) |
| `WP4-CACHE-COVERAGE` | 1 | 1 | 0 | 1 | 2.5 | cache references (155) below list-endpoint count (482) |
| `WP4-CATEGORY-TAXONOMY` | 1 | 1 | 0 | 1 | 20.0 | the schema can express a hierarchy (columns: __tablename__, depth, is_active, parent_id, path, slug, sort_order) but th… |
| `WP4-CHAIN-CHAIN-002` | 1 | 1 | 0 | 1 | 6.0 | CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes |
| `WP4-CHAIN-CHAIN-003` | 1 | 1 | 0 | 1 | 6.0 | CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no |
| `WP4-CHAIN-CHAIN-006` | 1 | 1 | 0 | 1 | 6.0 | CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes |
| `WP4-COUNT-QUERIES` | 1 | 1 | 0 | 1 | 2.5 | 306 `.count()` calls (expensive on large tables) |
| `WP4-COVERAGE-ROUTE` | 1 | 1 | 0 | 1 | 1.0 | 3 spec file(s) navigate to paths that no longer exist in the app router |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occur… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in th… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.accounts.models` (domains.country -> domains.accounts); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 4 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s)… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this f… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) i… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurre… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 47 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.accounts.models.banking` (domains.logistics -> domains.accounts); 27 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) i… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurr… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in t… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this f… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.logistics.services.core.shipment_service` (domains.orders -> domains.logistics); 33 occurr… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurren… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurren… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this fi… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this… |
| `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrenc… |
| `WP4-DEEP-NESTING` | 1 | 1 | 0 | 1 | 2.5 | 87 function(s) exceed 4 nesting levels (max seen 17) |
| `WP4-DOCS` | 1 | 1 | 0 | 1 | 2.5 | SETUP.md missing |
| `WP4-ENV-RAW` | 1 | 1 | 0 | 1 | 1.0 | 135 raw os.getenv/environ read(s) bypass typed settings |
| `WP4-FINANCE-AUTOMATION` | 1 | 1 | 0 | 1 | 20.0 | no implementation found for: bad_debt_provision |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 13 float-for-money signal(s); first: `min_price: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `return float(data.get("standard_rate", 0))` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"balance": float(balance),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 9 float-for-money signal(s); first: `"base_salary": float(base_salary),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(emp.salary),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_days": float(l.total_days),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `return float(payout.amount)` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 5 float-for-money signal(s); first: `"base_rate": float(base_rate),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 9 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 10 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount",… |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `"commission_rate": float(default_commission),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 19 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 6 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 7 float-for-money signal(s); first: `"price": float(product.price),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_U… |
| `WP4-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_pct=float(payload.get("discount_pct", 0)),` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `min_price: float | None` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `min_price: float | None` |
| `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: float` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 8 float-for-money signal(s); first: `current_price: float` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-GE` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expires_at"])` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `white_balance_strength: float` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-OC` | 1 | 1 | 0 | 1 | 2.5 | 2 float-for-money signal(s); first: `"amount": float(amt),` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-SH` | 1 | 1 | 0 | 1 | 2.5 | 9 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))` |
| `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-VO` | 1 | 1 | 0 | 1 | 2.5 | 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)` |
| `WP4-GHOST-FEATURE` | 1 | 1 | 0 | 1 | 1.0 | 8 gate literal(s) referenced but not defined in any features.py: ) assert require_feature_count >= len(endpoints), ( f,… |
| `WP4-HANDOVER` | 1 | 1 | 0 | 1 | 6.0 | 10 of 10 handover/takeover function(s) are missing at least one safety guarantee |
| `WP4-INTERACTION-FORM` | 1 | 1 | 0 | 1 | 2.5 | 465 of 743 text input(s) have no label, aria-label or id association |
| `WP4-INTERACTION-STATE` | 1 | 1 | 0 | 1 | 2.5 | 138 empty or console-only catch handler(s) |
| `WP4-LAW-CONFIG` | 1 | 1 | 0 | 1 | 1.0 | Law 84 (Typed feature flags) violated: 134 raw os.getenv read(s) |
| `WP4-LAW-DOCS` | 1 | 1 | 0 | 1 | 1.0 | Law 248 (Runbooks) violated: 0 doc file(s) under docs/ |
| `WP4-LAW-MIGRATION` | 1 | 1 | 0 | 1 | 1.0 | Law 27 (Delete temp scripts) violated: 91 temp/debug file(s) at backend root |
| `WP4-LAW-PERFORMANCE` | 1 | 1 | 0 | 1 | 1.0 | Law 222 (Keyset pagination) violated: 89 OFFSET usage(s) |
| `WP4-LONG-FUNCTION-BACKEND-CONFIG-PY` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | 10 function(s) >50 lines; longest sample `authenticate_password` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `list_products` = 119 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `send_message` = 58 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines |
| `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines |
| `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines |
| `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines |
| `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines |
| `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `with_retry` = 87 lines |
| `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines |
| `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines |
| `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines |
| `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines |
| `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_order` = 79 lines |
| `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_payment_page` = 90 lines |
| `WP4-MIDDLEWARE` | 1 | 1 | 0 | 1 | 2.5 | middleware order is ['foundation', 'geo', 'security', 'rate', 'compliance', 'observe', 'auth', 'webhook']; canonical is… |
| `WP4-MOBILE-DEPS` | 1 | 1 | 0 | 1 | 2.5 | dynamically required package(s) absent from package.json: @/lib/api, @paytabs/react-native-paytabs, @shared/api-core, @… |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.config.settings` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.currency_service.get_currency_context` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.config.settings` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.storage.storage._store` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 1 | 2.5 | `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier` |
| `WP4-N-PLUS-1` | 1 | 1 | 0 | 1 | 1.0 | 305/395 relationship() declarations omit lazy= |
| `WP4-OFFSET-PAGINATION` | 1 | 1 | 0 | 1 | 1.0 | 90 OFFSET pagination usage(s) (sample: .offset(safe_offset)) |
| `WP4-ORPHAN-FEATURE` | 1 | 1 | 0 | 1 | 1.0 | 231 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.ca… |
| `WP4-ORPHAN-JOB` | 1 | 1 | 0 | 1 | 2.5 | 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler |
| `WP4-ORPHAN-PROVIDER` | 1 | 1 | 0 | 1 | 1.0 | 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_varia… |
| `WP4-PACKAGE-MANAGER` | 1 | 1 | 0 | 1 | 1.0 | non-canonical lockfile `package-lock.json` present |
| `WP4-PII-LOGS` | 1 | 1 | 0 | 1 | 2.5 | 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc)) |
| `WP4-PRINT-LOGGING` | 1 | 1 | 0 | 1 | 2.5 | 3 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159) |
| `WP4-PROVIDER-CONFIG` | 1 | 1 | 0 | 1 | 1.0 | 13 provider module(s) read secrets via raw os.getenv |
| `WP4-PROVIDER-EXTRA` | 1 | 1 | 0 | 1 | 1.0 | provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py,… |
| `WP4-PROVIDER-HEALTH` | 1 | 1 | 0 | 1 | 1.0 | 93/93 provider modules lack health_check() |
| `WP4-PROVIDER-TIMEOUT` | 1 | 1 | 0 | 1 | 1.0 | 62/93 provider modules declare no timeout |
| `WP4-QUALITY-ASSURANCE` | 1 | 1 | 0 | 1 | 20.0 | no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach |
| `WP4-RAW-GETENV` | 1 | 1 | 0 | 1 | 2.5 | 126 raw os.getenv/os.environ read(s) in production paths (top: providers=64, infrastructure=38, domains=13, middleware=… |
| `WP4-READ-REPLICA` | 1 | 1 | 0 | 1 | 1.0 | read-replica engine exists but `get_read_db` is never used by domains |
| `WP4-SEARCH-INDEX` | 1 | 1 | 0 | 1 | 1.0 | 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%")) |
| `WP4-SELECT-STAR` | 1 | 1 | 0 | 1 | 1.0 | 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version"))) |
| `WP4-SILENT-EXCEPT-BACKEND-CONFIG-PY` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 895: truly-silent: except AttributeError: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | 6 silent except block(s); first at line 3044: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 69: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 54: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 212: pass-only: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 454: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 166: truly-silent: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 191: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 480: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 130: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 87: pass-only: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 5 silent except block(s); first at line 3774: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 1111: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 3411: truly-silent: except HTTPException as exc: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 693: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 307: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 43: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 97: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 120: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 85: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 6 silent except block(s); first at line 1439: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 355: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 508: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 5 silent except block(s); first at line 211: pass-only: except AttributeError: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 527: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 78: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 44: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | 6 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 30: pass-only: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 9 silent except block(s); first at line 1430: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 518: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 139: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 5 silent except block(s); first at line 280: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 203: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 2.5 | 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError): |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 188: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 174: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError): |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 113: pass-only: except Exception: # noqa: BLE001 |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 599: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 92: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 323: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 22: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 132: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 49: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 26: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 57: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 110: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 7 silent except block(s); first at line 67: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: |
| `WP4-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 293: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-MAIN-PY` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 199: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 245: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 424: truly-silent: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 0 | 1 | 2.5 | 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError: |
| `WP4-SILENT-EXCEPT-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 150: pass-only: except WebSocketDisconnect: |
| `WP4-SILENT-EXCEPT-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 1 | 2.5 | 3 silent except block(s); first at line 160: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 88: pass-only: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 231: pass-only: except OSError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 281: truly-silent: except json.JSONDecodeError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 148: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 115: truly-silent: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 108: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 35: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 155: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 302: truly-silent: except Exception as exc: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 113: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 288: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 4 silent except block(s); first at line 95: truly-silent: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 510: truly-silent: except (ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 24: pass-only: except Exception: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 44: truly-silent: except ValueError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError): |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 135: truly-silent: except (TypeError, ValueError): |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` | 1 | 1 | 0 | 1 | 2.5 | 2 silent except block(s); first at line 95: truly-silent: except UnicodeDecodeError: |
| `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 73: truly-silent: except (urllib.error.URLError, json.JSONDecodeError, KeyError… |
| `WP4-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` | 1 | 1 | 0 | 1 | 2.5 | 1 silent except block(s); first at line 33: truly-silent: except Exception: |
| `WP4-TABLE-GOVERNANCE` | 1 | 1 | 0 | 1 | 2.5 | 9 table(s) lack audit timestamps and 4 lack soft delete |
| `WP4-TABLE-INDEX` | 1 | 1 | 0 | 1 | 6.0 | 233 (table, column) pair(s) are filtered or sorted on with no declared index |
| `WP4-TABLE-RELATION` | 1 | 1 | 0 | 1 | 6.0 | 305 of 390 relationship() calls omit lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `addresses`: relationship `user` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 1.0 | 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `otp_codes`: relationship `user` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 1.0 | 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 1.0 | 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 1.0 | 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 1.0 | 3x rel lazy in table `messages`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 17x rel lazy in table `country_configs`: relationship `communications` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `country_basics`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `country_economics`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `country_legals`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `country_taxes`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 1.0 | 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 1.0 | 2x rel lazy in table `referrals`: relationship `referrer` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `payout_rules`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 1.0 | 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 1 | 1.0 | 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy= |
| `WP4-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 1 | 1 | 0 | 1 | 1.0 | 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy= |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 1.0 | 1x timestamp default in table `messages`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `news_articles`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `country_basics`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `country_economics`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `country_legals`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 1 | 1.0 | 1x timestamp default in table `cross_country_customer_sessions`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 1.0 | 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default |
| `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 1 | 1.0 | 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default |
| `WP4-TODO-HYGIENE` | 1 | 1 | 0 | 1 | 2.5 | 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts/models/core.py:58; backend/do… |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 1 | 6.0 | file has 4518 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 1 | 2.5 | function `_preprocess_for_ai` duplicates `backend/domains/catalog/services/ai_upload_service.py` (normalized AST) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 1 | 6.0 | file has 1970 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 6.0 | file has 1858 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 6.0 | file has 4725 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 6.0 | file has 1775 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 1 | 6.0 | file has 4150 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 1 | 2.5 | function `_serialize_lp_doc` duplicates `backend/domains/logistics/services/core/admin_service.py` (normalized AST) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 6.0 | file has 5104 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 1 | 6.0 | file has 1633 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 1 | 6.0 | file has 2786 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 1 | 6.0 | file has 2230 lines (split candidate) |
| `WP4-UNCATEGORISED-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 6.0 | file has 1553 lines (split candidate) |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | endpoint `list_employees_public` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 1 | 2.5 | endpoint `health` has no visible auth/feature gate |
| `WP4-UNKNOWN-GATE` | 1 | 1 | 0 | 1 | 2.5 | 13 require_feature literal(s) not found in any domains/*/features.py catalog: catalog.review.create, moderation.supplie… |
| `WP4-WEB-IMAGES` | 1 | 1 | 0 | 1 | 2.5 | next/image formats do not enable AVIF |
| `WP4-WEB-REWRITES` | 1 | 1 | 0 | 1 | 2.5 | rewrite `/hr/*` targets a non-canonical backend surface |
| `WP4-WEB-ROUTES` | 1 | 1 | 0 | 1 | 2.5 | duplicate route trees `logistics-partner` and `logistics-partners` both exist |
| `WP4-WEB-STATES` | 1 | 1 | 0 | 1 | 2.5 | 282 page(s) lack loading/error siblings (sample frontend/web_app/src/app/admin/accounting/loading.tsx) |
| `WP4-WORM` | 1 | 1 | 0 | 1 | 2.5 | audit trail mutates rows after INSERT (UPDATE on audit table) |

##### `WP4-WORKFLOW-RUNTIME` — `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_CREATED`, which is not defined anywhere in the codebase

- **cluster:** `CLUSTER-workflow-runtime` · **steps:** 10 (0 closed) · **files:** 3 · **est.:** 23.5h
- **files:** `backend/jobs/event_workers.py`, `backend/jobs/reconciliation_cron.py`, `backend/jobs/celery_app.py`

[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_CREATED`, which is not defined anywhere in t…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_SHIPPED`, which is not defined anywhere in t…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_DELIVERED`, which is not defined anywhere in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.orders.events.EVENT_ORDER_CANCELLED`, which is not defined anywhere in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.suppliers.events.EVENT_SUPPLIER_VERIFIED`, which is not defined anywhe…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.suppliers.events.EVENT_SUPPLIER_REJECTED`, which is not defined anywhe…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.logistics.events.EVENT_SHIPMENT_CREATED`, which is not defined anywher…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
[ ] `WF-dangling-import` — `backend/jobs/event_workers.py` imports `domains.logistics.events.EVENT_SHIPMENT_DELIVERED`, which is not defined anywh…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -c "import domains.jobs"`
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-workflow-runtime`)

##### `WP4-STUB-SUBSCRIBER` — stub subscriber module: 3 handlers, 3 `# Future:` markers

- **cluster:** `CLUSTER-stub-subscriber` · **steps:** 4 (0 closed) · **files:** 4 · **est.:** 10.0h
- **files:** `backend/domains/finance/subscribers.py`, `backend/domains/logistics/subscribers.py`, `backend/domains/orders/subscribers.py`, `backend/domains/payments/subscribers.py`

[ ] `WIRE-005` — stub subscriber module: 3 handlers, 3 `# Future:` markers
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-006` — stub subscriber module: 5 handlers, 5 `# Future:` markers
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-007` — stub subscriber module: 5 handlers, 5 `# Future:` markers
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-008` — stub subscriber module: 4 handlers, 4 `# Future:` markers
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PAYMENT-WEBHOOK` — payment adapter references webhooks but shows no signature verification

- **cluster:** `CLUSTER-payment-webhook` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `backend/providers/payments/config.py`, `backend/providers/payments/registry.py`, `backend/providers/payments/webhook_models.py`

[ ] `PROV-001` — payment adapter references webhooks but shows no signature verification
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `PROV-002` — payment adapter references webhooks but shows no signature verification
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `PROV-003` — payment adapter references webhooks but shows no signature verification
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-RLS` — canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed

- **cluster:** `CLUSTER-rls` · **steps:** 4 (0 closed) · **files:** 4 · **est.:** 7.0h
- **files:** `backend/infrastructure/database/rls_interceptor.py`, `backend/middleware/country_context.py`, `backend/infrastructure/database/sql/`, `backend/infrastructure/database/sql/pg_rls_policies.sql`

[ ] `WIRE-002` — canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'set_rls_context' -A30 backend/infrastructure/database/rls_interceptor.py`
[ ] `WIRE-003` — RLS mismatch: policies read `app.current_country_code` while middleware sets `app.country_scope`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'current_setting' backend/infrastructure/database/sql`
[ ] `DB-009` — 0 RLS policy target(s) vs 310 country-scoped table(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `DB-008` — RLS script does not FORCE row level security
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-CONTRADICTION-TARGET-VS-CODE` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists

- **cluster:** `CLUSTER-contradiction-target_vs_code` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 7.5h
- **files:** `backend/modules/finance/`, `backend/domains/payments/`, `backend/domains/media/`

[ ] `CONTRAD-001` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `CONTRAD-002` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/payments/: domain package `payments`…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `CONTRAD-003` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/media/: domain package `media` exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-BROWSER-RUNNER-BROKEN` — Playwright run produced no executable tests: ReferenceError: __dirname is not defined in ES module scope

- **cluster:** `CLUSTER-browser-runner-broken` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 12.0h
- **files:** `_browser_test/reports/run/results.json`

[ ] `BROWSER-001` — Playwright run produced no executable tests: ReferenceError: __dirname is not defined in ES module scope
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `BROWSER-002` — Playwright run produced no executable tests: Error: Cannot find module 'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_browse…
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-PAYMENT-CREDENTIALS` — payment gateway secret columns appear to be plain String (no encryption marker)

- **cluster:** `CLUSTER-payment-credentials` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 3.5h
- **files:** `backend/domains/finance/`, `backend/domains/finance/models/payments.py`

[ ] `PROV-004` — payment gateway secret columns appear to be plain String (no encryption marker)
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `SEC-006` — payment gateway secret field(s) stored without field encryption
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-STARTUP` — startup logged an error from lifespan/Failed to start backup manager (non-critical): Settings has no attribute

- **cluster:** `CLUSTER-startup` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 2.0h
- **files:** `lifespan.py:246`, `backend/lifespan.py`

[ ] `HTTP-startup-error` — startup logged an error from lifespan/Failed to start backup manager (non-critical): Settings has no attribute
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `python -m uvicorn main:app --port 8000 2>&1 | grep -i error`
[ ] `HTTP-startup-error` — startup logged an error from zozi.request/request_failed: False
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `python -m uvicorn main:app --port 8000 2>&1 | grep -i error`

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` — 47 endpoint(s) across 13 router(s) have no visible auth/gate dependency (sample: backend/modules/admin/routers/analytics.py:52 health)

- **cluster:** `CLUSTER-ungated-route` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/admin/routers/analytics.py`

[ ] `WIRE-009` — 47 endpoint(s) across 13 router(s) have no visible auth/gate dependency (sample: backend/modules/admin/routers/analytic…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'def health' backend/modules/admin/routers/analytics.py`
[ ] `WIRE-010` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WS-AUTH` — websocket `websocket_user` accepts without token verification

- **cluster:** `CLUSTER-ws-auth` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/admin/routers/comms.py`

[ ] `SEC-005` — websocket `websocket_user` accepts without token verification
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-058` — WebSocket `websocket_user` calls accept() without a prior JWT check
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `sed -n '138,156p' backend/modules/admin/routers/comms.py`

##### `WP4-EVENT-SPINE` — 44 of 79 event handlers (44/79) log and return without performing the write they imply

- **cluster:** `CLUSTER-event-spine` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 22.5h
- **files:** `backend/domains`, `backend/domains/`

[ ] `WF-stub-subscribers` — 44 of 79 event handlers (44/79) log and return without performing the write they imply
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '# Future:' backend/domains | wc -l`
[ ] `WIRE-004` — only 6/125 defined event type(s) referenced by services
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-AP-TODO-ONLY-IMPLEMENTATION` — TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1`

- **cluster:** `CLUSTER-ap-todo-only-implementation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/admin/admin_service.py`

[ ] `AP-003` — TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-AP-UNIMPLEMENTED-PLACEHOLDER` — Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service.py:21`

- **cluster:** `CLUSTER-ap-unimplemented-placeholder` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/identity/identity_admin_service.py`

[ ] `AP-002` — Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CHAIN-CHAIN-005` — CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-005` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/`

[ ] `BLOCK-004` — CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-CONTRADICTION-DOC-VS-CODE` — one router per module: every router file registered | modules/employee/routers/: hr.py file and hr/ package coexist

- **cluster:** `CLUSTER-contradiction-doc_vs_code` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `modules/employee/routers/`

[ ] `CONTRAD-034` — one router per module: every router file registered | modules/employee/routers/: hr.py file and hr/ package coexist
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CONTRADICTION-FRONTEND-VS-BACKEND` — Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists

- **cluster:** `CLUSTER-contradiction-frontend_vs_backend` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/next.config.ts`

[ ] `CONTRAD-029` — Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-EXTRA-MODULE` — top-level module `finance` exists

- **cluster:** `CLUSTER-extra-module` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/finance`

[ ] `ARCH-001` — top-level module `finance` exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `ls backend/modules`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/tax/country_tax_service.py`

[ ] `LOGIC-120` — 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/tax/country_tax_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"rate": float(rule.rate),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/commission_read_service.py`

[ ] `LOGIC-128` — 1 float-for-money signal(s); first: `"rate": float(rule.rate),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/commission_read_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `LOGIC-129` — 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/country/supplier_finance_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-130` — 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/data_import_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_paypal.py`

[ ] `LOGIC-134` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_paypal.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_stripe.py`

[ ] `LOGIC-135` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_stripe.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 7 float-for-money signal(s); first: `"amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-136` — 7 float-for-money signal(s); first: `"amount": float(converted_total),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_tap.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 3 float-for-money signal(s); first: `"amount": float(p.amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-137` — 3 float-for-money signal(s); first: `"amount": float(p.amount),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/payment_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-138` — 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/payment_orchestrator.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/trading_service.py`

[ ] `LOGIC-140` — 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price",…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/trading_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 39 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-179` — 39 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/core/logistics.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/misc.py`

[ ] `LOGIC-180` — 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/core/misc.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 4 float-for-money signal(s); first: `total=float(total_amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-181` — 4 float-for-money signal(s); first: `total=float(total_amount),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/core/order_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 4 float-for-money signal(s); first: `min_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `LOGIC-182` — 4 float-for-money signal(s); first: `min_amount: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/orders_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders.py`

[ ] `LOGIC-203` — 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/orders/supplier_orders.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 3 float-for-money signal(s); first: `min_payout_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/finance.py`

[ ] `LOGIC-238` — 3 float-for-money signal(s); first: `min_payout_amount: float`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/finance.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/finance_ai.py`

[ ] `LOGIC-242` — 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/finance_ai.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `gross_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/webhook_models.py`

[ ] `LOGIC-254` — 2 float-for-money signal(s); first: `gross_amount: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/webhook_models.py | head -20`

##### `WP4-SSRF` — 22 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authorization": f"Bearer {secr

- **cluster:** `CLUSTER-ssrf` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `SEC-008` — 22 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authoriza…
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-TABLE-DRIFT` — migrations reference schemas no ORM model declares: customer(5), commerce(1)

- **cluster:** `CLUSTER-table-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/alembic/versions`

[ ] `DB-schema-drift` — migrations reference schemas no ORM model declares: customer(5), commerce(1)
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `pytest backend/tests/architecture -k schema`

##### `WP4-UNCATEGORISED-BACKEND` — ruff reports 6604 violation(s); top rules: E402=2065, F401=1984, F821=1443, F811=1112

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/`

[ ] `TECH-lint` — ruff reports 6604 violation(s); top rules: E402=2065, F401=1984, F821=1443, F811=1112
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && ruff check .`

##### `WP4-UNCATEGORISED-BACKEND-TESTS-ARCHIT` — the architecture-law suite did not finish in 449.55s (exit 1); 50 failure(s) and 5 error(s) were observed before it stopped: test_architectu

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/tests/architecture`

[ ] `TEST-arch-hang` — the architecture-law suite did not finish in 449.55s (exit 1); 50 failure(s) and 5 error(s) were observed before it sto…
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
    - verify: `cd backend && python -m pytest tests/architecture -q --timeout=120`

##### `WP4-UNCATEGORISED-FRONTEND-WEB-APP` — 119 TypeScript error(s) across 29 file(s)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `frontend/web_app`

[ ] `WEB-tsc` — 119 TypeScript error(s) across 29 file(s)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
    - verify: `cd frontend/web_app && node_modules/.bin/tsc --noEmit`

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-ADMI` — endpoint `get_rbac_catalog` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/security.py`

[ ] `WIRE-011` — endpoint `get_rbac_catalog` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `serialize_pricing_profile` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 27 (0 closed) · **files:** 1 · **est.:** 71.0h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `FILE-101` — function `serialize_pricing_profile` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (norma…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-102` — function `serialize_category_pricing_rule` duplicates `backend/domains/logistics/services/partners/pricing_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-103` — function `serialize_vehicle_rule` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (normaliz…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-104` — function `resolve_category_rules_for_area` duplicates `backend/domains/logistics/services/partners/pricing_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-105` — function `resolve_vehicle_rule_for_area` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (n…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-106` — function `resolve_pricing_profile_for_area` duplicates `backend/domains/logistics/services/partners/pricing_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-107` — function `serialize_service_area` duplicates `backend/domains/logistics/services/partners/pricing_service.py` (normaliz…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-108` — function `build_partner_delete_blocker` duplicates `backend/domains/logistics/services/partners/blocker_service.py` (no…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
    - … and 19 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-uncategorised`)

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `push_notifications_health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 25 (0 closed) · **files:** 1 · **est.:** 62.5h
- **files:** `backend/modules/employee/routers/comms.py`

[ ] `WIRE-020` — endpoint `push_notifications_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-021` — endpoint `ws_chat_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-022` — endpoint `email_controller_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-023` — endpoint `send_email` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-024` — endpoint `send_transactional` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-025` — endpoint `send_from_alias` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-026` — endpoint `send_bulk` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-027` — endpoint `list_templates` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 17 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-ungated-route`)

##### `WP4-ALLOWLIST` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.models.suppliers: Suppli

- **cluster:** `CLUSTER-allowlist` · **steps:** 20 (0 closed) · **files:** 1 · **est.:** 50.0h
- **files:** `backend/DOMAIN_ALLOWLIST.yaml`

[ ] `ARCH-004` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.mod…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-005` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.governanc…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-006` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.comms.mo…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-007` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governan…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-008` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.catalog.…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-009` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governan…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-010` — allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> fastapi: HTTPException…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `ARCH-011` — allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> modules.admin.routers.…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-allowlist`)

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 20 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/finance/models/general_ledger.py`

[ ] `TF-167` — 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-168` — 1x timestamp default in table `supplier_settlements`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-169` — 1x timestamp default in table `account_balances`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-170` — 1x timestamp default in table `invoices`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-171` — 1x timestamp default in table `cash_accounts`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-172` — 1x timestamp default in table `treasury_accounts`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-173` — 1x timestamp default in table `payout_batches`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-174` — 1x timestamp default in table `bank_mapping_rules`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-timestamp-default`)

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `scan_lookup_shipment` duplicates `backend/domains/logistics/services/core/logistics_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 20 (0 closed) · **files:** 1 · **est.:** 53.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `FILE-064` — function `scan_lookup_shipment` duplicates `backend/domains/logistics/services/core/logistics_service.py` (normalized A…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-065` — function `admin_update_shipment_status` duplicates `backend/domains/logistics/services/core/logistics_service.py` (norm…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-066` — function `create_shipping_zone` duplicates `backend/domains/logistics/services/core/logistics_write_service.py` (normal…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-067` — function `get_email_stats` duplicates `backend/domains/logistics/services/core/admin_logistics_operations_service.py` (…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-068` — function `get_logistics_overview` duplicates `backend/domains/logistics/services/core/admin_logistics_operations_servic…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-069` — function `admin_email_stats` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-070` — function `admin_logistics_overview` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-071` — function `get_country_communications` duplicates `backend/domains/country/services/core/country_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-uncategorised`)

##### `WP4-TF-MISSING-COUNTRY-CODE` — 1x missing country_code in table `entity_chat_threads`: user-facing table `entity_chat_threads` lacks `country_code`

- **cluster:** `CLUSTER-tf-missing-country_code` · **steps:** 18 (0 closed) · **files:** 8 · **est.:** 18.0h
- **files:** `backend/domains/comms/models/chat.py`, `backend/domains/comms/models/communication.py`, `backend/domains/comms/models/fraud.py`, `backend/domains/comms/models/marketing.py`, `backend/domains/customers/models/cross_country_session.py`, `backend/domains/hr/models/employee_models.py`, `backend/domains/logistics/models/read_models/__init__.py`, `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-036` — 1x missing country_code in table `entity_chat_threads`: user-facing table `entity_chat_threads` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-046` — 1x missing country_code in table `group_chat_members`: user-facing table `group_chat_members` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-049` — 1x missing country_code in table `escalation_sla_logs`: user-facing table `escalation_sla_logs` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-052` — 1x missing country_code in table `entity_chat_messages`: user-facing table `entity_chat_messages` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-059` — 1x missing country_code in table `group_chat_messages`: user-facing table `group_chat_messages` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-062` — 1x missing country_code in table `notifications`: user-facing table `notifications` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-063` — 1x missing country_code in table `ticket_messages`: user-facing table `ticket_messages` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-067` — 1x missing country_code in table `faqs`: user-facing table `faqs` lacks `country_code`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 10 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-missing-country_code`)

##### `WP4-CIRCULAR-IMPORT` — circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -> domains.customers -

- **cluster:** `CLUSTER-circular-import` · **steps:** 17 (0 closed) · **files:** 10 · **est.:** 42.5h
- **files:** `domains.accounts ↔ domains.audit`, `domains.catalog ↔ domains.country`, `domains.finance ↔ domains.logistics`, `domains.finance ↔ domains.governance`, `domains.security ↔ domains.suppliers`, `domains.orders ↔ domains.promotions`, `domains.logistics ↔ domains.orders`, `domains.country ↔ domains.customers`

[ ] `ARCH-203` — circular package dependency: domains.accounts -> domains.audit -> domains.catalog -> domains.comms -> domains.country -…
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-204` — circular package dependency: domains.catalog -> domains.country -> domains.customers -> domains.governance
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-205` — circular package dependency: domains.finance -> domains.logistics -> domains.orders -> domains.suppliers
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-206` — circular package dependency: domains.finance -> domains.governance -> domains.logistics -> domains.orders -> domains.se…
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-207` — circular package dependency: domains.security -> domains.suppliers
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-208` — circular package dependency: domains.finance -> domains.governance -> domains.logistics
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-209` — circular package dependency: domains.orders -> domains.promotions
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
[ ] `ARCH-210` — circular package dependency: domains.logistics -> domains.orders
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.
    - … and 9 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-circular-import`)

##### `WP4-INFRA-IMPORTS-ABOVE` — `infra imports above`: imports `domains`

- **cluster:** `CLUSTER-infra-imports-above` · **steps:** 15 (0 closed) · **files:** 12 · **est.:** 37.5h
- **files:** `backend/infrastructure/database/init_db.py`, `backend/infrastructure/database/seed/_common.py`, `backend/infrastructure/geography/__init__.py`, `backend/infrastructure/messaging/email_service.py`, `backend/infrastructure/messaging/realtime.py`, `backend/infrastructure/ml/worker.py`, `backend/infrastructure/storage/backup.py`, `backend/infrastructure/storage/storage.py`

[ ] `ARCH-025` — `infra imports above`: imports `domains`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'domains' backend/infrastructure/database/init_db.py`
[ ] `ARCH-026` — `infra imports above`: imports `domains.finance.services.seeders.treasury_seeder`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'domains.finance.services.seeders.treasury_seeder' backend/infrastructure/database/seed/_common.py`
[ ] `ARCH-027` — `infra imports above`: imports `providers.geography.geoip`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.geography.geoip' backend/infrastructure/geography/__init__.py`
[ ] `ARCH-028` — `infra imports above`: imports `providers.geography.ip`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.geography.ip' backend/infrastructure/geography/__init__.py`
[ ] `ARCH-029` — `infra imports above`: imports `providers.comms.email`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.comms.email' backend/infrastructure/messaging/email_service.py`
[ ] `ARCH-030` — `infra imports above`: imports `domains.accounts.models.user`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'domains.accounts.models.user' backend/infrastructure/messaging/realtime.py`
[ ] `ARCH-031` — `infra imports above`: imports `providers.image.bg_remover`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.image.bg_remover' backend/infrastructure/ml/worker.py`
[ ] `ARCH-032` — `infra imports above`: imports `providers.storage`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.storage' backend/infrastructure/storage/backup.py`
    - … and 7 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-infra-imports-above`)

##### `WP4-JOB-RESILIENCE` — celery task module with no DLQ reference

- **cluster:** `CLUSTER-job-resilience` · **steps:** 14 (0 closed) · **files:** 14 · **est.:** 35.0h
- **files:** `backend/jobs/accrual_reversal.py`, `backend/jobs/ai_tasks.py`, `backend/jobs/bank_statement_importer.py`, `backend/jobs/data_retention.py`, `backend/jobs/email_tasks.py`, `backend/jobs/fraud_monitoring.py`, `backend/jobs/fx_revaluation.py`, `backend/jobs/ghost_order_detector.py`

[ ] `OPS-001` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-002` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-003` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-004` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-005` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-006` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-007` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
[ ] `OPS-008` — celery task module with no DLQ reference
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - … and 6 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-job-resilience`)

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-FINA` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 14 (0 closed) · **files:** 1 · **est.:** 35.0h
- **files:** `backend/modules/finance/routers/cash_management.py`

[ ] `ARCH-073` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-074` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-075` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-076` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-077` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-078` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-079` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py`
[ ] `ARCH-080` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/finance/routers/cash_management.py`
    - … and 6 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-module-imports-infrastructure`)

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` — function `get_supplier_bank_account` duplicates `backend/domains/finance/services/country/supplier_finance_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 14 (0 closed) · **files:** 1 · **est.:** 38.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `FILE-030` — function `get_supplier_bank_account` duplicates `backend/domains/finance/services/country/supplier_finance_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-031` — function `get_supplier_payout_summary` duplicates `backend/domains/finance/services/country/supplier_finance_service.py…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-032` — function `upsert_supplier_bank_account` duplicates `backend/domains/finance/services/country/supplier_finance_service.p…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-033` — function `create_import_shipment` duplicates `backend/domains/finance/services/data_import_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-034` — function `confirm_shipment` duplicates `backend/domains/finance/services/data_import_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-035` — function `_post_goods_in_transit_journal` duplicates `backend/domains/finance/services/data_import_service.py` (normali…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-036` — function `allocate_landed_costs` duplicates `backend/domains/finance/services/data_import_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-037` — function `_compute_allocation_weights` duplicates `backend/domains/finance/services/data_import_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
    - … and 6 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-uncategorised`)

##### `WP4-VERSION-DRIFT` — `eslint: ^9` does not satisfy pinned `10`

- **cluster:** `CLUSTER-version-drift` · **steps:** 13 (0 closed) · **files:** 4 · **est.:** 13.0h
- **files:** `frontend/web_app/package.json`, `frontend/mobile_app/package.json`, `backend/requirements.txt`, `frontend/shared/package.json`

[ ] `TECH-005` — `eslint: ^9` does not satisfy pinned `10`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TECH-009` — `eslint: ^9.0.0` does not satisfy pinned `10`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TECH-020` — `valkey==6.1.1` does not satisfy pinned `9.0.6+`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -i 'valkey' backend/requirements.txt`
[ ] `TECH-021` — `celery==5.4.0` does not satisfy pinned `5.5+`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -i 'celery' backend/requirements.txt`
[ ] `TECH-002` — `dompurify: ^3.3.3` does not satisfy pinned `3.4.0`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TECH-003` — `jspdf: ^4.1.0` does not satisfy pinned `4.2.1`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TECH-004` — `@testing-library/react: ^16.3.2` does not satisfy pinned `16.3.0`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TECH-006` — `jest: ^29.0.0` does not satisfy pinned `29.7.0`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 5 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-version-drift`)

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` — function `_fetch_rss` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 11 (0 closed) · **files:** 1 · **est.:** 27.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `FILE-043` — function `_fetch_rss` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-044` — function `_process_api_response` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-045` — function `get_comprehensive_stats` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-046` — function `_get_system_stats` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py` (nor…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-047` — function `run_commission_simulation` duplicates `backend/domains/analytics/services/aggregation/command_center_service.…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-048` — function `run_sla_simulation` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py` (no…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-049` — function `get_external_intelligence` duplicates `backend/domains/analytics/services/aggregation/command_center_service.…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-050` — function `get_workforce_metrics` duplicates `backend/domains/analytics/services/aggregation/command_center_service.py`…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
    - … and 3 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-uncategorised`)

##### `WP4-HTTP-CSP` — CSP on `/health`: uses report-uri, superseded by report-to

- **cluster:** `CLUSTER-http-csp` · **steps:** 10 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `HTTP-csp-directives` — CSP on `/health`: uses report-uri, superseded by report-to
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-directives` — CSP on `/docs`: uses report-uri, superseded by report-to
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-directives` — CSP on `/openapi.json`: uses report-uri, superseded by report-to
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-directives` — CSP on `/definitely-not-a-route`: uses report-uri, superseded by report-to
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-localhost` — the CSP served on `/health` names localhost origins: connect-src 'self' http://localhost:8000 ws://localhost:3000 http:…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `APP_ENV=production curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-localhost` — the CSP served on `/docs` names localhost origins: connect-src 'self' http://localhost:8000 ws://localhost:3000 http://…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `APP_ENV=production curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-localhost` — the CSP served on `/openapi.json` names localhost origins: connect-src 'self' http://localhost:8000 ws://localhost:3000…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `APP_ENV=production curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
[ ] `HTTP-csp-localhost` — the CSP served on `/definitely-not-a-route` names localhost origins: connect-src 'self' http://localhost:8000 ws://loca…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `APP_ENV=production curl -sS -D - -o /dev/null http://127.0.0.1:8000/health | grep -i content-security-policy`
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-http-csp`)

##### `WP4-TF-FK-ONDELETE` — 1x fk ondelete in table `audit_logs`: FK `country_code` has no ondelete

- **cluster:** `CLUSTER-tf-fk-ondelete` · **steps:** 10 (0 closed) · **files:** 6 · **est.:** 10.0h
- **files:** `backend/domains/audit/models/audit_schema_models.py`, `backend/domains/country/models/country_basics.py`, `backend/domains/governance/models/core.py`, `backend/domains/logistics/models/logistics_schema_models.py`, `backend/domains/payments/models/payment_models.py`, `backend/domains/security/models/security_schema_models.py`

[ ] `TF-014` — 1x fk ondelete in table `audit_logs`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-015` — 1x fk ondelete in table `command_center_views`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-114` — 1x fk ondelete in table `country_basics`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-200` — 1x fk ondelete in table `user_browsing_histories`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-201` — 1x fk ondelete in table `system_health_events`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-253` — 1x fk ondelete in table `city_distance_matrices`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-264` — 2x fk ondelete in table `refunds`: FK `requested_by_id` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-282` — 1x fk ondelete in table `alert_escalation_rules`: FK `country_code` has no ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-fk-ondelete`)

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 9.0h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `TF-126` — 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-128` — 1x timestamp default in table `country_staff_assignments`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-130` — 1x timestamp default in table `country_config_versions`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-132` — 1x timestamp default in table `supplier_kyc_requirements`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-134` — 1x timestamp default in table `logistics_partner_kyc_requirements`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-137` — 1x timestamp default in table `country_localizations`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-140` — 1x timestamp default in table `country_legal_contracts`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-143` — 1x timestamp default in table `country_cities`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-timestamp-default`)

##### `WP4-FEATURE-GATE` — `require_feature("catalog.review.create")` gates on a feature that no features.py declares

- **cluster:** `CLUSTER-feature-gate` · **steps:** 8 (0 closed) · **files:** 5 · **est.:** 9.5h
- **files:** `backend/modules/customer/routers/reviews.py`, `backend/modules/admin/routers/disputes.py`, `backend/modules/admin/routers/promotions.py`, `backend/modules/admin/routers/tickets.py`, `backend/domains`

[ ] `FEAT-UNDEF` — `require_feature("catalog.review.create")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"catalog.review.create"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("moderation.suppliers")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"moderation.suppliers"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("promotions.flash_sales.read")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"promotions.flash_sales.read"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("promotions.flash_sales.write")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"promotions.flash_sales.write"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("support.read")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"support.read"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("support.reply")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"support.reply"' backend/domains/*/features.py`
[ ] `FEAT-UNDEF` — `require_feature("support.update")` gates on a feature that no features.py declares
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn '"support.update"' backend/domains/*/features.py`
[ ] `FEAT-DEAD` — 152 declared feature(s) are never referenced by any gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `python _zozi_audit/zozi_compile.py --check feature-dead`

##### `WP4-TF-MISSING-UPDATED-AT` — 1x missing updated_at in table `group_chat_members`: table `group_chat_members` lacks `updated_at`

- **cluster:** `CLUSTER-tf-missing-updated_at` · **steps:** 8 (0 closed) · **files:** 5 · **est.:** 8.0h
- **files:** `backend/domains/comms/models/chat.py`, `backend/domains/governance/models/admin.py`, `backend/domains/hr/models/employee_models.py`, `backend/domains/suppliers/models/suppliers.py`, `backend/rbac/models/permission_entities.py`

[ ] `TF-045` — 1x missing updated_at in table `group_chat_members`: table `group_chat_members` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-048` — 1x missing updated_at in table `escalation_sla_logs`: table `escalation_sla_logs` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-051` — 1x missing updated_at in table `entity_chat_messages`: table `entity_chat_messages` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-194` — 1x missing updated_at in table `admin_analytics_snapshots`: table `admin_analytics_snapshots` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-206` — 1x missing updated_at in table `employee_biometrics`: table `employee_biometrics` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-209` — 1x missing updated_at in table `geo_fence_logs`: table `geo_fence_logs` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-299` — 1x missing updated_at in table `supplier_disputes`: table `supplier_disputes` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-303` — 1x missing updated_at in table `permission_audit_log`: table `permission_audit_log` lacks `updated_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 8 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/logistics/services/geo/service.py`

[ ] `FILE-089` — function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-090` — function `_check_office_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-091` — function `_haversine_distance` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-092` — function `detect_impossible_travel` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-093` — function `get_cities_for_map` duplicates `backend/domains/logistics/services/geo/map_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-094` — function `get_warehouses_for_map` duplicates `backend/domains/logistics/services/geo/map_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-095` — function `get_delivery_zones` duplicates `backend/domains/logistics/services/geo/map_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-096` — function `get_region_bounds` duplicates `backend/domains/logistics/services/geo/map_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-LAW-CODE-QUALITY` — Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s)

- **cluster:** `CLUSTER-law-code-quality` · **steps:** 7 (0 closed) · **files:** 1 · **est.:** 7.0h
- **files:** `backend/`

[ ] `LAW-019` — Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-021` — Law 21 (Timestamps = server_default) violated: 104 Python-side timestamp default(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-022` — Law 22 (FK have ondelete) violated: 11 FK(s) without ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-023` — Law 23 (Audit columns) violated: 11 table(s) missing audit columns
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-058` — Law 58 (No print() in production) violated: 4 print() call(s) in production code
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-059` — Law 59 (No silent exceptions) violated: 69 pass/return-None-only except block(s) (sample scan)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-062` — Law 62 (TODO/FIXME hygiene) violated: 286 untracked TODO/FIXME
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TEST-NO-ASSERT` — test file contains no assertions

- **cluster:** `CLUSTER-test-no-assert` · **steps:** 7 (0 closed) · **files:** 7 · **est.:** 17.5h
- **files:** `backend/tests/architecture/test_law19_through_law31.py`, `backend/tests/architecture/test_law2_router_no_db_writes.py`, `backend/tests/domains/accounts/test_accounts.py`, `backend/tests/domains/analytics/test_analytics.py`, `backend/tests/domains/promotions/test_promotions.py`, `tests/middleware/test_webhook_ip_whitelist.py`, `tests/security/test_vault.py`

[ ] `TEST-002` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-003` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-004` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-005` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-006` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-013` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TEST-014` — test file contains no assertions
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-CUST` — endpoint `login` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 7 (0 closed) · **files:** 1 · **est.:** 17.5h
- **files:** `backend/modules/customer/routers/accounts.py`

[ ] `WIRE-012` — endpoint `login` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-013` — endpoint `refresh` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-014` — endpoint `me` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-015` — endpoint `logout` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-016` — endpoint `auth_register` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-017` — endpoint `auth_social_google_start` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-018` — endpoint `auth_social_facebook_start` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 21 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 15.0h
- **files:** `backend/domains/governance/ports.py`

[ ] `ARCH-147` — cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 21 occurrence(s) in thi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/governance`
[ ] `ARCH-150` — cross-domain import `domains.comms.models.fraud` (domains.governance -> domains.comms); 26 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/governance`
[ ] `ARCH-152` — cross-domain import `domains.customers.models.customer_schema_models` (domains.governance -> domains.customers); 1 occu…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.customers' backend/domains/governance`
[ ] `ARCH-157` — cross-domain import `domains.promotions.models.coupon_usage` (domains.governance -> domains.promotions); 15 occurrence(…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/governance`
[ ] `ARCH-158` — cross-domain import `domains.security.models.fraud` (domains.governance -> domains.security); 39 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.security' backend/domains/governance`
[ ] `ARCH-159` — cross-domain import `domains.suppliers.models.suppliers` (domains.governance -> domains.suppliers); 10 occurrence(s) in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.suppliers' backend/domains/governance`

##### `WP4-LAW-ARCHITECTURE` — Law 1 (Arrows point down) violated: 33 reverse-layer import(s)

- **cluster:** `CLUSTER-law-architecture` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/`

[ ] `LAW-001` — Law 1 (Arrows point down) violated: 33 reverse-layer import(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-003` — Law 3 (Cross-domain events/ports) violated: event-spine findings=1
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-004` — Law 4 (Features single-sourced) violated: 8 gate literal(s) missing from catalog (moderation.suppliers, promotions.flas…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-005` — Law 5 (Country is orthogonal) violated: SET LOCAL present=False; policy var=app.current_country_code; middleware var=ap…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-006` — Law 6 (Schema discipline) violated: 2/340 table(s) without schema declaration
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-007` — Law 7 (Allowlist only shrinks) violated: 20 entr(ies), 20 without dated removal plan
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-SUPPLY-CHAIN` — no dependency scanning step in CI

- **cluster:** `CLUSTER-supply-chain` · **steps:** 6 (0 closed) · **files:** 4 · **est.:** 6.0h
- **files:** `.github/workflows/`, `.github/workflows/router-generation.yml`, `.github/workflows/schema-audit.yml`, `.`

[ ] `SC-001` — no dependency scanning step in CI
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `SC-002` — no secret scanning in CI
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `SC-003` — no SBOM generation in CI
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `SC-005` — workflow declares no `permissions:` block
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `SC-006` — workflow declares no `permissions:` block
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `SC-007` — no SBOM artifact found in the repository
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `fraud_events`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/security/models/fraud.py`

[ ] `TF-273` — 2x rel lazy in table `fraud_events`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-274` — 1x rel lazy in table `device_fingerprints`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-275` — 1x rel lazy in table `return_abuse_patterns`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-276` — 1x rel lazy in table `ip_account_linkages`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-277` — 1x rel lazy in table `fraud_scoring_logs`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-281` — 2x rel lazy in table `meeting_action_items`: relationship `meeting` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 2x timestamp default in table `entity_chat_threads`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/comms/models/chat.py`

[ ] `TF-037` — 2x timestamp default in table `entity_chat_threads`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-042` — 1x timestamp default in table `direct_chat_rooms`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-050` — 1x timestamp default in table `escalation_sla_logs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-053` — 1x timestamp default in table `entity_chat_messages`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-057` — 2x timestamp default in table `group_chat_rooms`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-060` — 2x timestamp default in table `group_chat_messages`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `TF-241` — 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-243` — 1x timestamp default in table `logistics_partner_service_areas`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-245` — 1x timestamp default in table `logistics_pricing_profiles`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-247` — 1x timestamp default in table `logistics_vehicle_rules`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-249` — 1x timestamp default in table `logistics_category_pricing_rules`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-251` — 1x timestamp default in table `shipments`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` — 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-287` — 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-290` — 2x timestamp default in table `supplier_documents`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-293` — 2x timestamp default in table `supplier_notification_preferences`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-294` — 2x timestamp default in table `supplier_badge_catalogs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-295` — 2x timestamp default in table `supplier_badges`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-297` — 2x timestamp default in table `supplier_badge_billing_histories`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` — function `_build_postgres_tsquery` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 15.0h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `FILE-024` — function `_build_postgres_tsquery` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized A…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-025` — function `_deserialize_sizes` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-026` — function `_product_search_blob` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-027` — function `_score_product` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-028` — function `_sort_ranked_products` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-029` — function `parse_query` duplicates `backend/domains/catalog/services/search/search_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-FORBIDDEN-PACKAGE` — forbidden package declared: `prometheus-client`==0.26.0

- **cluster:** `CLUSTER-forbidden-package` · **steps:** 5 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/requirements.txt`, `backend/requirements-compiled.txt`

[ ] `TECH-015` — forbidden package declared: `prometheus-client`==0.26.0
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rni 'prometheus-client' backend/requirements*.txt`
[ ] `TECH-016` — forbidden package declared: `limits`==5.8.0
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rni 'limits' backend/requirements*.txt`
[ ] `TECH-017` — forbidden package declared: `requests`==2.34.2
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rni 'requests' backend/requirements*.txt`
[ ] `TECH-018` — forbidden package declared: `slowapi`==0.1.10
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rni 'slowapi' backend/requirements*.txt`
[ ] `TECH-019` — forbidden package declared: `tzlocal`==5.4.4
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rni 'tzlocal' backend/requirements*.txt`

##### `WP4-LAW-DATABASE` — Law 45 (No N+1 queries) violated: 305/390 relationship(s) without lazy=

- **cluster:** `CLUSTER-law-database` · **steps:** 5 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/`

[ ] `LAW-045` — Law 45 (No N+1 queries) violated: 305/390 relationship(s) without lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-052` — Law 52 (FK constraints) violated: 11 FK(s) without ondelete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-053` — Law 53 (Index FK columns) violated: 26 FK(s) without index=True (verify composite indexes manually)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-054` — Law 54 (Soft delete) violated: 4 table(s) without is_deleted
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-055` — Law 55 (Schema-per-domain) violated: 2/340 table(s) without schema declaration
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-MISSING-CREATED-AT` — 1x missing created_at in table `video_room_participants`: table `video_room_participants` lacks `created_at`

- **cluster:** `CLUSTER-tf-missing-created_at` · **steps:** 5 (0 closed) · **files:** 3 · **est.:** 5.0h
- **files:** `backend/domains/comms/models/chat.py`, `backend/domains/governance/models/admin.py`, `backend/domains/hr/models/employee_models.py`

[ ] `TF-040` — 1x missing created_at in table `video_room_participants`: table `video_room_participants` lacks `created_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-044` — 1x missing created_at in table `group_chat_members`: table `group_chat_members` lacks `created_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-193` — 1x missing created_at in table `admin_analytics_snapshots`: table `admin_analytics_snapshots` lacks `created_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-205` — 1x missing created_at in table `employee_biometrics`: table `employee_biometrics` lacks `created_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-208` — 1x missing created_at in table `geo_fence_logs`: table `geo_fence_logs` lacks `created_at`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` — function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 5 (0 closed) · **files:** 1 · **est.:** 12.5h
- **files:** `backend/domains/customers/services/public_comms_status_service.py`

[ ] `FILE-019` — function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized A…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-020` — function `_persist_message` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-021` — function `websocket_chat` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-022` — function `websocket_user` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-023` — function `broadcast` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/logistics/services/core/admin_logistics_fallback_service.py`

[ ] `ARCH-165` — cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/logistics`
[ ] `ARCH-170` — cross-domain import `domains.governance.models.admin` (domains.logistics -> domains.governance); 67 occurrence(s) in th…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/logistics`
[ ] `ARCH-171` — cross-domain import `domains.hr.models.employee_models` (domains.logistics -> domains.hr); 6 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/logistics`
[ ] `ARCH-172` — cross-domain import `domains.orders.models.orders` (domains.logistics -> domains.orders); 25 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/logistics`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/modules/admin/routers/logistics.py`

[ ] `ARCH-047` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_super_admin' backend/modules/admin/routers/logistics.py`
[ ] `ARCH-048` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/admin/routers/logistics.py`
[ ] `ARCH-049` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/admin/routers/logistics.py`
[ ] `ARCH-050` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/admin/routers/logistics.py`

##### `WP4-TF-MISSING-IS-DELETED` — 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted`

- **cluster:** `CLUSTER-tf-missing-is_deleted` · **steps:** 4 (0 closed) · **files:** 3 · **est.:** 4.0h
- **files:** `backend/domains/logistics/models/read_models/__init__.py`, `backend/domains/suppliers/models/suppliers.py`, `backend/rbac/models/permission_entities.py`

[ ] `TF-257` — 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-259` — 1x missing is_deleted in table `partner_performance_projections`: table `partner_performance_projections` lacks `is_del…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-300` — 1x missing is_deleted in table `supplier_disputes`: table `supplier_disputes` lacks `is_deleted`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-304` — 1x missing is_deleted in table `permission_audit_log`: table `permission_audit_log` lacks `is_deleted`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` — 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/governance/models/admin.py`

[ ] `TF-195` — 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-196` — 2x rel lazy in table `badge_billing_records`: relationship `supplier` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-197` — 1x rel lazy in table `promotion_order_tiers`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-199` — 2x rel lazy in table `employee_expenses`: relationship `employee` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/logistics/models/erp.py`

[ ] `TF-236` — 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-237` — 1x rel lazy in table `goods_receipt_notes`: relationship `lines` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-238` — 1x rel lazy in table `sales_orders`: relationship `lines` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-239` — 1x rel lazy in table `import_shipments`: relationship `lines` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-SCHEMA-UNKNOWN` — 1x schema unknown in table `payment_methods`: schema `payments` is not canonical

- **cluster:** `CLUSTER-tf-schema-unknown` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/payments/models/payment_models.py`

[ ] `TF-261` — 1x schema unknown in table `payment_methods`: schema `payments` is not canonical
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-262` — 1x schema unknown in table `payment_attempts`: schema `payments` is not canonical
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-263` — 1x schema unknown in table `refunds`: schema `payments` is not canonical
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-265` — 1x schema unknown in table `payment_intents`: schema `payments` is not canonical
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `announcements`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `TF-065` — 1x timestamp default in table `announcements`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-068` — 1x timestamp default in table `faqs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-070` — 1x timestamp default in table `proxy_channels`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-084` — 1x timestamp default in table `internal_emails`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/comms/models/marketing.py`

[ ] `TF-099` — 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-101` — 1x timestamp default in table `email_templates`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-102` — 1x timestamp default in table `newsletter_subscribers`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-104` — 1x timestamp default in table `email_runtime_configs`: `updated_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/finance/models/commission.py`

[ ] `TF-163` — 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-164` — 2x timestamp default in table `product_commission_overrides`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-165` — 2x timestamp default in table `commission_ledger_entries`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-166` — 2x timestamp default in table `commission_category_rates`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/finance/models/tax_rules.py`

[ ] `TF-187` — 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-189` — 1x timestamp default in table `tax_rules`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-191` — 1x timestamp default in table `payout_rule_categories`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-192` — 1x timestamp default in table `payout_rule_products`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-COMM` — function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/comms/services/messaging/websocket_handlers.py`

[ ] `FILE-011` — function `_mark_messages_read` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized A…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-012` — function `_persist_message` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-013` — function `websocket_chat` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-014` — function `broadcast` duplicates `backend/domains/comms/services/public_comms_status_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-HR-S` — function `validate_work_hours` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/hr/services/compliance_engine.py`

[ ] `FILE-056` — function `validate_work_hours` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-057` — function `calculate_overtime` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-058` — function `validate_weekly_rest` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-059` — function `get_compliance_report` duplicates `backend/domains/audit/services/compliance_engine.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `get_country_communications` duplicates `backend/domains/country/services/core/country_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/logistics/services/core/country_communication_service.py`

[ ] `FILE-060` — function `get_country_communications` duplicates `backend/domains/country/services/core/country_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-061` — function `get_cross_border_sessions` duplicates `backend/domains/country/services/core/country_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-062` — function `get_legal_contracts` duplicates `backend/domains/country/services/core/country_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-063` — function `get_shop_warehouses` duplicates `backend/domains/country/services/core/country_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/logistics/services/geo/geo_fence_service.py`

[ ] `FILE-083` — function `is_within_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-084` — function `_check_office_fence` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-085` — function `_haversine_distance` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-086` — function `detect_impossible_travel` duplicates `backend/domains/country/services/geo/country_detection.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-COLOR-DRIFT` — 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files excluded — a literal is 

- **cluster:** `CLUSTER-color-drift` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 46.0h
- **files:** `frontend/web_app/src`

[ ] `DS-hex-drift` — 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files exc…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rEon '#[0-9a-fA-F]{6}' frontend/web_app/src | grep -v 'src/styles/tokens.css' | wc -l`
[ ] `DS-palette-drift` — 375 raw Tailwind palette class(es) across 52 files bypass the semantic token scale
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rEn '(bg|text|border)-(slate|gray|zinc|neutral)-[0-9]{2,3}' frontend/web_app/src | wc -l`
[ ] `DS-inline-style` — 302 inline `style={...}` prop(s) across 76 files; inline colour cannot be themed
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rc 'style={{' frontend/web_app/src --include=*.tsx | awk -F: '$2>0' | wc -l`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/orders/ports.py`

[ ] `ARCH-175` — cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/orders`
[ ] `ARCH-177` — cross-domain import `domains.catalog.models.products` (domains.orders -> domains.catalog); 10 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/orders`
[ ] `ARCH-185` — cross-domain import `domains.promotions.services.admin_promotion_service` (domains.orders -> domains.promotions); 8 occ…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/orders`

##### `WP4-DESIGN-PRIMITIVES` — 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive

- **cluster:** `CLUSTER-design-primitives` · **steps:** 3 (0 closed) · **files:** 2 · **est.:** 11.0h
- **files:** `frontend/web_app/src`, `frontend/web_app/src/components/ui`

[ ] `DS-duplicate-markup` — 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rlE 'rounded-(xl|2xl) border border-(border|surface)' frontend/web_app/src | wc -l`
[ ] `DS-no-variant-system` — none of the 72 primitives use a variant system (class-variance-authority); variants are raw Record<string, string> maps
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rl 'cva(' frontend/web_app/src/components/ui | wc -l`
[ ] `DS-primitive-ref` — 63 of 72 primitives do not forward refs and set no displayName
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rL 'forwardRef' frontend/web_app/src/components/ui/*.tsx`

##### `WP4-DUPLICATE-FILE` — byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py

- **cluster:** `CLUSTER-duplicate-file` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 7.5h
- **files:** `backend/domains/finance/exceptions.py`, `backend/domains/governance/exceptions.py`, `backend/domains/orders/serializers.py`

[ ] `FILE-002` — byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `FILE-003` — byte-identical duplicate file(s): backend/domains/governance/exceptions.py, backend/domains/governance/services/excepti…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `FILE-004` — byte-identical duplicate file(s): backend/domains/orders/serializers.py, backend/domains/orders/schemas/serializers.py
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-INTERACTION-BUTTON` — 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit

- **cluster:** `CLUSTER-interaction-button` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 4.5h
- **files:** `frontend/web_app/src`

[ ] `IX-button-type` — 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rEc '<button(\s|>)' frontend/web_app/src --include=*.tsx | awk -F: '$2>0' | wc -l`
[ ] `IX-mutation-error-swallowed` — 9 mutating action(s) sit next to an empty or console-only catch
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rEn 'catch\s*(\([^)]*\))?\s*\{\s*\}' frontend/web_app/src --include=*.tsx`
[ ] `IX-icon-button-name` — 2 icon-only button(s) expose no accessible name
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `npx axe http://localhost:3100 --tags wcag2a`

##### `WP4-INTERACTION-MODAL` — 28 destructive control(s) in 8 modal file(s) with no confirmation step

- **cluster:** `CLUSTER-interaction-modal` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 9.5h
- **files:** `frontend/web_app/src`

[ ] `IX-destructive-confirm` — 28 destructive control(s) in 8 modal file(s) with no confirmation step
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rEni 'onClick.*\b(delete|refund|revoke|void|cancel)\b' frontend/web_app/src --include=*.tsx`
[ ] `IX-modal-focus` — 26 of 27 modal/drawer implementations have no focus management
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `npx playwright test e2e/a11y --tags wcag2a`
[ ] `IX-modal-escape` — 23 of 27 modal implementations do not close on Escape
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rL 'onEscapeKeyDown\|Escape' frontend/web_app/src/components/ui`

##### `WP4-LAW-SECURITY` — Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s)

- **cluster:** `CLUSTER-law-security` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/`

[ ] `LAW-034` — Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-037` — Law 37 (Rate limit fails closed) violated: rate limiter does not visibly fail closed
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-275` — Law 275 (Encryption at rest) violated: field encryption module missing
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/modules/admin/routers/promotions.py`

[ ] `ARCH-051` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.get_country_or_404`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.get_country_or_404' backend/modules/admin/routers/promotions.py`
[ ] `ARCH-052` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.set_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.set_rls_context' backend/modules/admin/routers/promotions.py`
[ ] `ARCH-053` — `module imports infrastructure`: imports `infrastructure.database.rls_interceptor.clear_rls_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.rls_interceptor.clear_rls_context' backend/modules/admin/routers/promotions.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/modules/admin/routers/staff.py`

[ ] `ARCH-054` — `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.schemas.CreateStaffAccount' backend/modules/admin/routers/staff.py`
[ ] `ARCH-055` — `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.schemas.UpdateStaffAccount' backend/modules/admin/routers/staff.py`
[ ] `ARCH-056` — `module imports infrastructure`: imports `infrastructure.security.country_access.get_country_access_scope`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.country_access.get_country_access_scope' backend/modules/admin/routers/staff.py`

##### `WP4-PROVIDER-RESILIENCE` — circuit breaker present in 8/94 provider modules

- **cluster:** `CLUSTER-provider-resilience` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/providers/`

[ ] `OBS-001` — circuit breaker present in 8/94 provider modules
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `OBS-002` — retry policy present in 7/94 provider modules
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `OBS-003` — explicit timeout in 29/94 provider modules
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-RUNBOOKS` — no deploy runbook found

- **cluster:** `CLUSTER-runbooks` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 7.5h
- **files:** `docs/runbooks/deploy.md`, `docs/runbooks/rollback.md`, `docs/runbooks/migration.md`

[ ] `D2P-005` — no deploy runbook found
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `D2P-006` — no rollback runbook found
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `D2P-007` — no migration runbook found
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` — 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `TF-203` — 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-211` — 1x rel lazy in table `org_units`: relationship `parent` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-232` — 1x rel lazy in table `employee_activity_logs`: relationship `employee` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-AUDI` — function `get_residency_config` duplicates `backend/domains/audit/services/data_residency_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/audit/services/flat_data_residency_service.py`

[ ] `FILE-007` — function `get_residency_config` duplicates `backend/domains/audit/services/data_residency_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-008` — function `encrypt_for_storage` duplicates `backend/domains/audit/services/data_residency_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-009` — function `get_compliance_status` duplicates `backend/domains/audit/services/data_residency_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `admin_email_stats` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `FILE-097` — function `admin_email_stats` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-098` — function `admin_logistics_overview` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-099` — function `admin_reset_demo_data` duplicates `backend/domains/logistics/services/core/service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `list_employees_public` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/modules/employee/routers/hr.py`

[ ] `WIRE-046` — endpoint `list_employees_public` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-047` — endpoint `shift_handover_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-048` — endpoint `hr_dashboard_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CI-CD` — pipeline lacks: secret scanning

- **cluster:** `CLUSTER-ci-cd` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `.github/workflows/`

[ ] `D2P-001` — pipeline lacks: secret scanning
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `D2P-002` — pipeline lacks: dependency scanning
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/accounts/models/user.py`

[ ] `ARCH-111` — cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/accounts`
[ ] `ARCH-112` — cross-domain import `domains.customers.models.customer_schema_models` (domains.accounts -> domains.customers); 3 occurr…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.customers' backend/domains/accounts`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/audit/services/compliance_engine.py`

[ ] `ARCH-116` — cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/audit`
[ ] `ARCH-119` — cross-domain import `domains.hr.models.employee_models` (domains.audit -> domains.hr); 3 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/audit`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` — cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/catalog/services/products/admin_products_service.py`

[ ] `ARCH-120` — cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/catalog`
[ ] `ARCH-121` — cross-domain import `domains.governance.models.core` (domains.catalog -> domains.governance); 1 occurrence(s) in this f…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/catalog`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `ARCH-123` — cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/comms`
[ ] `ARCH-127` — cross-domain import `domains.governance.models.core` (domains.comms -> domains.governance); 19 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `ARCH-131` — cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurren…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.customers' backend/domains/country`
[ ] `ARCH-133` — cross-domain import `domains.governance.models.legal_contract_template` (domains.country -> domains.governance); 2 occu…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/country`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/customers/services/cart_service.py`

[ ] `ARCH-135` — cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/customers`
[ ] `ARCH-136` — cross-domain import `domains.catalog.models.products` (domains.customers -> domains.catalog); 5 occurrence(s) in this f…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/customers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `ARCH-140` — cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/finance`
[ ] `ARCH-144` — cross-domain import `domains.logistics.models.erp` (domains.finance -> domains.logistics); 26 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.logistics' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `ARCH-141` — cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/finance`
[ ] `ARCH-142` — cross-domain import `domains.country.models.countries` (domains.finance -> domains.country); 5 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/governance/services/export_read_service.py`

[ ] `ARCH-149` — cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/governance`
[ ] `ARCH-156` — cross-domain import `domains.orders.models.orders` (domains.governance -> domains.orders); 12 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `ARCH-176` — cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in t…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.audit' backend/domains/orders`
[ ] `ARCH-180` — cross-domain import `domains.customers.services.coupons_service` (domains.orders -> domains.customers); 1 occurrence(s)…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.customers' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/promotions/services/engine/admin_commerce_configuration_service.py`

[ ] `ARCH-187` — cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/promotions`
[ ] `ARCH-190` — cross-domain import `domains.governance.models.admin` (domains.promotions -> domains.governance); 2 occurrence(s) in th…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/promotions`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `ARCH-195` — cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/suppliers`
[ ] `ARCH-200` — cross-domain import `domains.governance` (domains.suppliers -> domains.governance); 3 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/suppliers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/suppliers/services/analytics/supplier_analytics_service.py`

[ ] `ARCH-196` — cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this f…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/suppliers`
[ ] `ARCH-202` — cross-domain import `domains.orders.models.orders` (domains.suppliers -> domains.orders); 14 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/suppliers`

##### `WP4-DB-POOL` — no pool_size configuration found

- **cluster:** `CLUSTER-db-pool` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `DB-005` — no pool_size configuration found
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `DB-006` — asyncpg statement_cache_size=0 not set
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-EXTRA-DOMAIN` — domain package `media` exists

- **cluster:** `CLUSTER-extra-domain` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/domains/media`, `backend/domains/payments`

[ ] `ARCH-002` — domain package `media` exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `ls backend/domains`
[ ] `ARCH-003` — domain package `payments` exists
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `ls backend/domains`

##### `WP4-INTENT-STUB` — 1 placeholder response(s) ('not yet wired') in live module

- **cluster:** `CLUSTER-intent-stub` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 2.0h
- **files:** `backend/modules/admin/routers/country.py`, `backend/modules/admin/routers/orders.py`

[ ] `INTENT-002` — 1 placeholder response(s) ('not yet wired') in live module
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `INTENT-003` — 1 placeholder response(s) ('not yet wired') in live module
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LAW-PROVIDER` — Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic

- **cluster:** `CLUSTER-law-provider` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/`

[ ] `LAW-123` — Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-129` — Law 129 (Health checks) violated: 0/93 providers have health_check()
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LAW-STRUCTURE` — Law 12 (15 domains) violated: extra domain(s): media, payments

- **cluster:** `CLUSTER-law-structure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/`

[ ] `LAW-012` — Law 12 (15 domains) violated: extra domain(s): media, payments
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `LAW-013` — Law 13 (5 modules) violated: extra module(s): finance
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-MIDDLEWARE-IMPORTS-ABOVE` — `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies`

- **cluster:** `CLUSTER-middleware-imports-above` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/middleware/dependencies/auth.py`, `backend/middleware/dependencies/country_detection.py`

[ ] `ARCH-040` — `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'domains.accounts.services.auth.security_dependencies' backend/middleware/dependencies/auth.py`
[ ] `ARCH-041` — `middleware imports above`: imports `providers.geography.ip`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'providers.geography.ip' backend/middleware/dependencies/country_detection.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/admin/routers/accounts.py`

[ ] `ARCH-042` — `module imports infrastructure`: imports `infrastructure.database.schemas.CreateStaffAccount`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.schemas.CreateStaffAccount' backend/modules/admin/routers/accounts.py`
[ ] `ARCH-043` — `module imports infrastructure`: imports `infrastructure.database.schemas.UpdateStaffAccount`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.database.schemas.UpdateStaffAccount' backend/modules/admin/routers/accounts.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` — `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/customer/routers/accounts.py`

[ ] `ARCH-057` — `module imports infrastructure`: imports `infrastructure.security.dependencies.verify_captcha`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.verify_captcha' backend/modules/customer/routers/accounts.py`
[ ] `ARCH-058` — `module imports infrastructure`: imports `infrastructure.utils.auth.decode_token`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.auth.decode_token' backend/modules/customer/routers/accounts.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_html`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/employee/routers/finance.py`

[ ] `ARCH-064` — `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_html`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.invoice_html.generate_invoice_html' backend/modules/employee/routers/finance.py`
[ ] `ARCH-065` — `module imports infrastructure`: imports `infrastructure.utils.invoice_html.generate_invoice_pdf_bytes`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.invoice_html.generate_invoice_pdf_bytes' backend/modules/employee/routers/finance.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/logistics/routers/logistics.py`

[ ] `ARCH-093` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/logistics.py`
[ ] `ARCH-094` — `module imports infrastructure`: imports `infrastructure.utils.pagination.paginated_response`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.pagination.paginated_response' backend/modules/logistics/routers/logistics.py`

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 1x rel lazy in table `categories`: relationship `products` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/catalog/models/products.py`

[ ] `TF-026` — 1x rel lazy in table `categories`: relationship `products` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-033` — 2x rel lazy in table `product_filter_metadatas`: relationship `category` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `TF-064` — 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-069` — 1x rel lazy in table `help_categories`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/comms/models/marketing.py`

[ ] `TF-097` — 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-103` — 2x rel lazy in table `campaign_recipients`: relationship `campaign` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `TF-127` — 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-131` — 1x rel lazy in table `country_config_versions`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `coupons`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/promotions/models/promotions.py`

[ ] `TF-270` — 1x rel lazy in table `coupons`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-272` — 2x rel lazy in table `flash_sales`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` — 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-288` — 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-296` — 2x rel lazy in table `supplier_badges`: relationship `supplier` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-SCHEMA-MISSING` — 1x schema missing in table `payroll_records`: table `payroll_records` has no schema declaration

- **cluster:** `CLUSTER-tf-schema-missing` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `TF-229` — 1x schema missing in table `payroll_records`: table `payroll_records` has no schema declaration
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-231` — 1x schema missing in table `employee_trainings`: table `employee_trainings` has no schema declaration
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_configs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/country/models/countries.py`

[ ] `TF-108` — 2x timestamp default in table `country_configs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-110` — 1x timestamp default in table `country_communications`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` — 2x timestamp default in table `referrals`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/customers/models/customer_schema_models.py`

[ ] `TF-159` — 2x timestamp default in table `referrals`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `TF-161` — 2x timestamp default in table `referral_point_events`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-ZOZI-AUDIT` — check `arch_router_thinness` failed: crashed: NameError: name 'DB_CALL_RE' is not defined

- **cluster:** `CLUSTER-uncategorised` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `_zozi_audit`

[ ] `ARCH-024` — check `arch_router_thinness` failed: crashed: NameError: name 'DB_CALL_RE' is not defined
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `MIG-001` — check `db_migration_graph` failed: crashed: NameError: name 'parsed' is not defined
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` — function `get_cities_dropdown` duplicates `backend/domains/country/services/country_dropdown_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/country/services/geo/country_maps_service.py`

[ ] `FILE-015` — function `get_cities_dropdown` duplicates `backend/domains/country/services/country_dropdown_service.py` (normalized AS…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-016` — function `get_countries_dropdown` duplicates `backend/domains/country/services/country_dropdown_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-CUST` — function `_normalize_address_payload` duplicates `backend/domains/accounts/services/addresses/addresses_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/customers/services/customer_router_service.py`

[ ] `FILE-017` — function `_normalize_address_payload` duplicates `backend/domains/accounts/services/addresses/addresses_service.py` (no…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-018` — function `_serialize_address` duplicates `backend/domains/accounts/services/addresses/addresses_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-GOVE` — function `admin_email_stats` duplicates `backend/domains/governance/services/admin/admin_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/governance/services/settings/admin_service.py`

[ ] `FILE-054` — function `admin_email_stats` duplicates `backend/domains/governance/services/admin/admin_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-055` — function `admin_logistics_overview` duplicates `backend/domains/governance/services/admin/admin_service.py` (normalized…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `list_logistics_partner_locations` duplicates `backend/domains/logistics/services/core/logistics_locations_service.py` (normalized 

- **cluster:** `CLUSTER-uncategorised` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/logistics/services/geo/logistics_locations_service.py`

[ ] `FILE-087` — function `list_logistics_partner_locations` duplicates `backend/domains/logistics/services/core/logistics_locations_ser…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.
[ ] `FILE-088` — function `create_logistics_partner_location` duplicates `backend/domains/logistics/services/core/logistics_locations_se…
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `shift_handover_health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/employee/routers/hr/health.py`

[ ] `WIRE-051` — endpoint `shift_handover_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-052` — endpoint `hr_dashboard_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` — endpoint `list_assigned_shipments` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/modules/logistics/routers/logistics.py`

[ ] `WIRE-055` — endpoint `list_assigned_shipments` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
[ ] `WIRE-056` — endpoint `parcel_tracking_health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-AP-EMPTY-HANDLER-PASS` — Empty handler (pass): 4 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270`

- **cluster:** `CLUSTER-ap-empty-handler-pass` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/observability/circuit_breaker.py`

[ ] `AP-004` — Empty handler (pass): 4 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` — Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3497`

- **cluster:** `CLUSTER-ap-stub-function-notimplementederror` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `AP-001` — Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-AP-TODO-ONLY` — TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58

- **cluster:** `CLUSTER-ap-todo-only` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `AP-005` — TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-BASE-IMAGE` — dev database image `postgres:18-alpine` (documented: postgres:16-alpine)

- **cluster:** `CLUSTER-base-image` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `docker-compose.yml`

[ ] `TECH-014` — dev database image `postgres:18-alpine` (documented: postgres:16-alpine)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CACHE-COVERAGE` — cache references (155) below list-endpoint count (482)

- **cluster:** `CLUSTER-cache-coverage` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/`

[ ] `PERF-002` — cache references (155) below list-endpoint count (482)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-CATEGORY-TAXONOMY` — the schema can express a hierarchy (columns: __tablename__, depth, is_active, parent_id, path, slug, sort_order) but the seeded taxonomy onl

- **cluster:** `CLUSTER-category-taxonomy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/catalog/models/products.py`

[ ] `CAT-depth-underused` — the schema can express a hierarchy (columns: __tablename__, depth, is_active, parent_id, path, slug, sort_order) but th…
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `pytest backend/tests/domains/catalog -k categor`

##### `WP4-CHAIN-CHAIN-002` — CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-002` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/`

[ ] `BLOCK-002` — CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-CHAIN-CHAIN-003` — CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no

- **cluster:** `CLUSTER-chain-chain-003` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/orders/`

[ ] `BLOCK-003` — CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-CHAIN-CHAIN-006` — CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-006` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/`

[ ] `BLOCK-005` — CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-COUNT-QUERIES` — 306 `.count()` calls (expensive on large tables)

- **cluster:** `CLUSTER-count-queries` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/`

[ ] `PERF-003` — 306 `.count()` calls (expensive on large tables)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-COVERAGE-ROUTE` — 3 spec file(s) navigate to paths that no longer exist in the app router

- **cluster:** `CLUSTER-coverage-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `_browser_test/tests`

[ ] `FEAT-SPEC-ORPHAN` — 3 spec file(s) navigate to paths that no longer exist in the app router
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `npx playwright test --list`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/permissions/permission_service.py`

[ ] `ARCH-113` — cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occur…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/accounts`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/users/user_management_service.py`

[ ] `ARCH-114` — cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/accounts`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` — cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/analytics/models/analytics_schema_models.py`

[ ] `ARCH-115` — cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/analytics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/data_residency_service.py`

[ ] `ARCH-117` — cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/audit`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/ediscovery.py`

[ ] `ARCH-118` — cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/audit`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` — cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/ports.py`

[ ] `ARCH-122` — cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/catalog`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `ARCH-125` — cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/models/suppliers.py`

[ ] `ARCH-129` — cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.suppliers' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/ports.py`

[ ] `ARCH-128` — cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in th…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/utility/shared_utils.py`

[ ] `ARCH-124` — cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/tickets/tickets_service.py`

[ ] `ARCH-126` — cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/comms`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.accounts.models` (domains.country -> domains.accounts); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `ARCH-130` — cross-domain import `domains.accounts.models` (domains.country -> domains.accounts); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/country`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/ports.py`

[ ] `ARCH-132` — cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 4 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/country`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/geo/country_detection.py`

[ ] `ARCH-134` — cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/country`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/coupons_read_service.py`

[ ] `ARCH-138` — cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s)…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/customers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/customer_health_engine.py`

[ ] `ARCH-137` — cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/customers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/admin_commission_service.py`

[ ] `ARCH-143` — cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `ARCH-145` — cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_service.py`

[ ] `ARCH-139` — cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `ARCH-146` — cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.promotions' backend/domains/finance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/models/admin.py`

[ ] `ARCH-151` — cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/admin/bulk_ops_service.py`

[ ] `ARCH-153` — cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this f…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/approval/approval_matrix_service.py`

[ ] `ARCH-154` — cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/audit/__init__.py`

[ ] `ARCH-148` — cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) i…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.audit' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/users_service.py`

[ ] `ARCH-155` — cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurre…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.logistics' backend/domains/governance`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` — cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `ARCH-161` — cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/hr`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/coi_service.py`

[ ] `ARCH-163` — cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/hr`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/hr_service.py`

[ ] `ARCH-162` — cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/hr`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/hr_employee_service.py`

[ ] `ARCH-160` — cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/hr`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 47 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `ARCH-169` — cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 47 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.accounts.models.banking` (domains.logistics -> domains.accounts); 27 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/models/logistics_schema_models.py`

[ ] `ARCH-164` — cross-domain import `domains.accounts.models.banking` (domains.logistics -> domains.accounts); 27 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/ports.py`

[ ] `ARCH-167` — cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) i…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_operations_service.py`

[ ] `ARCH-166` — cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/country_communication_service.py`

[ ] `ARCH-168` — cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurr…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.customers' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/shipment_service.py`

[ ] `ARCH-174` — cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in t…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.suppliers' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/health/service.py`

[ ] `ARCH-173` — cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.security' backend/domains/logistics`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/models/order_entities.py`

[ ] `ARCH-179` — cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/service.py`

[ ] `ARCH-182` — cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this f…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.governance' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/admin_extra.py`

[ ] `ARCH-178` — cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/misc.py`

[ ] `ARCH-183` — cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/disputes/service.py`

[ ] `ARCH-186` — cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.suppliers' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.logistics.services.core.shipment_service` (domains.orders -> domains.logistics); 33 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/logistics_service.py`

[ ] `ARCH-184` — cross-domain import `domains.logistics.services.core.shipment_service` (domains.orders -> domains.logistics); 33 occurr…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.logistics' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `ARCH-181` — cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurren…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/orders`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `ARCH-189` — cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/promotions`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/coupon_service.py`

[ ] `ARCH-188` — cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.catalog' backend/domains/promotions`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/customer_coupons_create_service.py`

[ ] `ARCH-191` — cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurren…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.orders' backend/domains/promotions`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/detection/public_security_detection_service.py`

[ ] `ARCH-192` — cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.accounts' backend/domains/security`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `ARCH-194` — cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.suppliers' backend/domains/security`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/health/flat_risk_service.py`

[ ] `ARCH-193` — cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.hr' backend/domains/security`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/badges/badge_write_service.py`

[ ] `ARCH-199` — cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this fi…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.finance' backend/domains/suppliers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/contract/contract_service.py`

[ ] `ARCH-198` — cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.country' backend/domains/suppliers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/disputes_service.py`

[ ] `ARCH-197` — cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.comms' backend/domains/suppliers`

##### `WP4-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `ARCH-201` — cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrenc…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'from domains.logistics' backend/domains/suppliers`

##### `WP4-DEEP-NESTING` — 87 function(s) exceed 4 nesting levels (max seen 17)

- **cluster:** `CLUSTER-deep-nesting` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/lifespan.py`

[ ] `LOGIC-318` — 87 function(s) exceed 4 nesting levels (max seen 17)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-DOCS` — SETUP.md missing

- **cluster:** `CLUSTER-docs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `SETUP.md`

[ ] `D2P-008` — SETUP.md missing
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-ENV-RAW` — 135 raw os.getenv/environ read(s) bypass typed settings

- **cluster:** `CLUSTER-env-raw` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/config.py`

[ ] `ENV-055` — 135 raw os.getenv/environ read(s) bypass typed settings
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-FINANCE-AUTOMATION` — no implementation found for: bad_debt_provision

- **cluster:** `CLUSTER-finance-automation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/finance`

[ ] `FIN-manual-processes` — no implementation found for: bad_debt_provision
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rn 'bad_debt\|gateway_fee' backend/domains/finance`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/categories/bulk_category_service.py`

[ ] `LOGIC-103` — 1 float-for-money signal(s); first: `"commission_rate": float(cat.commission_rate) if cat.commission_rate else None,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/categories/bulk_category_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/categories/categories_service.py`

[ ] `LOGIC-104` — 1 float-for-money signal(s); first: `"commission_rate": float(c.commission_rate) if c.commission_rate is not None else…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/categories/categories_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/categories/category_service.py`

[ ] `LOGIC-105` — 1 float-for-money signal(s); first: `"commission_rate": float(commission_rate) if commission_rate is not None else None…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/categories/category_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/commission_service.py`

[ ] `LOGIC-106` — 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/commission_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 13 float-for-money signal(s); first: `min_price: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-108` — 13 float-for-money signal(s); first: `min_price: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/products/products_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/ai_search_service.py`

[ ] `LOGIC-109` — 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/search/ai_search_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 3 float-for-money signal(s); first: `return float(data.get("standard_rate", 0))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_auto_populate.py`

[ ] `LOGIC-118` — 3 float-for-money signal(s); first: `return float(data.get("standard_rate", 0))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/research/country_auto_populate.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_heuristic_engine.py`

[ ] `LOGIC-119` — 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/research/country_heuristic_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 1 float-for-money signal(s); first: `"balance": float(balance),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/coins/zozi_coins_service.py`

[ ] `LOGIC-122` — 1 float-for-money signal(s); first: `"balance": float(balance),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/coins/zozi_coins_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `LOGIC-147` — 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/command_center/service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/products_service.py`

[ ] `LOGIC-148` — 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/products_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/employee_service.py`

[ ] `LOGIC-151` — 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/employees/employee_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/hr_employee_service.py`

[ ] `LOGIC-152` — 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/hr_employee_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 9 float-for-money signal(s); first: `"base_salary": float(base_salary),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_engine.py`

[ ] `LOGIC-154` — 9 float-for-money signal(s); first: `"base_salary": float(base_salary),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/payroll/payroll_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_service.py`

[ ] `LOGIC-155` — 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/payroll/payroll_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `"salary": float(emp.salary),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/dei_auditor.py`

[ ] `LOGIC-156` — 1 float-for-money signal(s); first: `"salary": float(emp.salary),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/performance/dei_auditor.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `"total_days": float(l.total_days),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/shift/shift_roster_service.py`

[ ] `LOGIC-158` — 1 float-for-money signal(s); first: `"total_days": float(l.total_days),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/shift/shift_roster_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_fallback_service.py`

[ ] `LOGIC-160` — 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_fallback_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `return float(payout.amount)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_operations_service.py`

[ ] `LOGIC-162` — 3 float-for-money signal(s); first: `return float(payout.amount)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_operations_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 5 float-for-money signal(s); first: `"base_rate": float(base_rate),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/logistics_engine.py`

[ ] `LOGIC-163` — 5 float-for-money signal(s); first: `"base_rate": float(base_rate),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/logistics_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py`

[ ] `LOGIC-165` — 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/geo/map_service.py`

[ ] `LOGIC-166` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/geo/map_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/geo/service.py`

[ ] `LOGIC-168` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/geo/service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 9 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `LOGIC-170` — 9 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/admin_logistics_operations_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_pricing_service.py`

[ ] `LOGIC-172` — 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/logistics_pricing_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 10 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/pricing_service.py`

[ ] `LOGIC-173` — 10 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/pricing_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/shipping/service.py`

[ ] `LOGIC-176` — 4 float-for-money signal(s); first: `"car_rate": float(z.car_rate) if z.car_rate else 0,`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/shipping/service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/coin_service.py`

[ ] `LOGIC-187` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coins/coin_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/promotion_points_service.py`

[ ] `LOGIC-188` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coins/promotion_points_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 6 float-for-money signal(s); first: `order_total: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/customer_coupons_create_service.py`

[ ] `LOGIC-189` — 6 float-for-money signal(s); first: `order_total: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coupons/customer_coupons_create_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount", 0) or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/promotion_service.py`

[ ] `LOGIC-192` — 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount",…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/promotion_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/analytics/supplier_analytics_service.py`

[ ] `LOGIC-197` — 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/analytics/supplier_analytics_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `"commission_rate": float(default_commission),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/contract/contract_service.py`

[ ] `LOGIC-199` — 2 float-for-money signal(s); first: `"commission_rate": float(default_commission),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/contract/contract_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 19 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-200` — 19 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/health/supplier_health.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 6 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health_engine.py`

[ ] `LOGIC-201` — 6 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/health/supplier_health_engine.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py`

[ ] `LOGIC-202` — 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 7 float-for-money signal(s); first: `"price": float(product.price),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products_service.py`

[ ] `LOGIC-207` — 7 float-for-money signal(s); first: `"price": float(product.price),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_products_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 3 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py`

[ ] `LOGIC-208` — 3 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_supplier_upload_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/profile/supplier_profile.py`

[ ] `LOGIC-210` — 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/profile/supplier_profile.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/settlement/multi_currency_settlement.py`

[ ] `LOGIC-212` — 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_U…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/settlement/multi_currency_settlement.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/currency_service.py`

[ ] `LOGIC-219` — 1 float-for-money signal(s); first: `"rate_from_aed": float(rate_from_aed),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/utils/currency_service.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-ADMI` — 4 float-for-money signal(s); first: `discount_pct=float(payload.get("discount_pct", 0)),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/promotions.py`

[ ] `LOGIC-221` — 4 float-for-money signal(s); first: `discount_pct=float(payload.get("discount_pct", 0)),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/admin/routers/promotions.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` — 4 float-for-money signal(s); first: `min_price: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/catalog.py`

[ ] `LOGIC-223` — 4 float-for-money signal(s); first: `min_price: float | None`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/catalog.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-CUST` — 6 float-for-money signal(s); first: `order_total: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/promotions.py`

[ ] `LOGIC-226` — 6 float-for-money signal(s); first: `order_total: Optional[float]`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/promotions.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `min_price: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/catalog.py`

[ ] `LOGIC-228` — 2 float-for-money signal(s); first: `min_price: float | None`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/catalog.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `gross_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/serializers/employee_serializers.py`

[ ] `LOGIC-235` — 2 float-for-money signal(s); first: `gross_amount: float`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/serializers/employee_serializers.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 8 float-for-money signal(s); first: `current_price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/price_intelligence.py`

[ ] `LOGIC-243` — 8 float-for-money signal(s); first: `current_price: float`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/price_intelligence.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/search.py`

[ ] `LOGIC-245` — 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/search.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-GE` — 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expires_at"])`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/geography/rates.py`

[ ] `LOGIC-248` — 1 float-for-money signal(s); first: `return float(_RATES_CACHE["expires_at"])`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/geography/rates.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` — 1 float-for-money signal(s); first: `white_balance_strength: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-249` — 1 float-for-money signal(s); first: `white_balance_strength: float`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/image/free_image_tools.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-IM` — 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/ocr.py`

[ ] `LOGIC-250` — 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/image/ocr.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-OC` — 2 float-for-money signal(s); first: `"amount": float(amt),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ocr/ocr_parser.py`

[ ] `LOGIC-251` — 2 float-for-money signal(s); first: `"amount": float(amt),`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ocr/ocr_parser.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-SH` — 9 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/shipping/shipping_calculator.py`

[ ] `LOGIC-256` — 9 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/shipping/shipping_calculator.py | head -20`

##### `WP4-FLOAT-MONEY-BACKEND-PROVIDERS-VO` — 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/voice/voice_to_text.py`

[ ] `LOGIC-257` — 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/voice/voice_to_text.py | head -20`

##### `WP4-GHOST-FEATURE` — 8 gate literal(s) referenced but not defined in any features.py: )
    assert require_feature_count >= len(endpoints), (
        f, catalog.

- **cluster:** `CLUSTER-ghost-feature` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/modules/`

[ ] `FEAT-011` — 8 gate literal(s) referenced but not defined in any features.py: ) assert require_feature_count >= len(endpoints), ( f,…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-HANDOVER` — 10 of 10 handover/takeover function(s) are missing at least one safety guarantee

- **cluster:** `CLUSTER-handover` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains`

[ ] `WF-handover-unguarded` — 10 of 10 handover/takeover function(s) are missing at least one safety guarantee
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rn 'handover\|takeover' backend/domains | wc -l`

##### `WP4-INTERACTION-FORM` — 465 of 743 text input(s) have no label, aria-label or id association

- **cluster:** `CLUSTER-interaction-form` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src`

[ ] `IX-input-label` — 465 of 743 text input(s) have no label, aria-label or id association
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `npx axe http://localhost:3100 --tags wcag2a,wcag2aa`

##### `WP4-INTERACTION-STATE` — 138 empty or console-only catch handler(s)

- **cluster:** `CLUSTER-interaction-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src`

[ ] `IX-error-swallow` — 138 empty or console-only catch handler(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rEn 'catch\s*(\([^)]*\))?\s*\{\s*\}' frontend/web_app/src --include=*.tsx | wc -l`

##### `WP4-LAW-CONFIG` — Law 84 (Typed feature flags) violated: 134 raw os.getenv read(s)

- **cluster:** `CLUSTER-law-config` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-084` — Law 84 (Typed feature flags) violated: 134 raw os.getenv read(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LAW-DOCS` — Law 248 (Runbooks) violated: 0 doc file(s) under docs/

- **cluster:** `CLUSTER-law-docs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-248` — Law 248 (Runbooks) violated: 0 doc file(s) under docs/
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LAW-MIGRATION` — Law 27 (Delete temp scripts) violated: 91 temp/debug file(s) at backend root

- **cluster:** `CLUSTER-law-migration` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-027` — Law 27 (Delete temp scripts) violated: 91 temp/debug file(s) at backend root
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LAW-PERFORMANCE` — Law 222 (Keyset pagination) violated: 89 OFFSET usage(s)

- **cluster:** `CLUSTER-law-performance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-222` — Law 222 (Keyset pagination) violated: 89 OFFSET usage(s)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-CONFIG-PY` — 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/config.py`

[ ] `LOGIC-286` — 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 10 function(s) >50 lines; longest sample `authenticate_password` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `LOGIC-262` — 10 function(s) >50 lines; longest sample `authenticate_password` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 2 function(s) >50 lines; longest sample `record_consent` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/gdpr_service.py`

[ ] `LOGIC-301` — 2 function(s) >50 lines; longest sample `record_consent` = 67 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/users/user_management_service.py`

[ ] `LOGIC-263` — 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` — 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/analytics/services/dashboards/analytics_service.py`

[ ] `LOGIC-302` — 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/ai_upload_service.py`

[ ] `LOGIC-287` — 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 2 function(s) >50 lines; longest sample `list_products` = 119 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-303` — 2 function(s) >50 lines; longest sample `list_products` = 119 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-268` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/email_gateway.py`

[ ] `LOGIC-304` — 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 3 function(s) >50 lines; longest sample `send_message` = 58 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `LOGIC-288` — 3 function(s) >50 lines; longest sample `send_message` = 58 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/chat_threads_query.py`

[ ] `LOGIC-305` — 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` — 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `LOGIC-269` — 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-COUN` — 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_heuristic_engine.py`

[ ] `LOGIC-306` — 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-CUST` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-270` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `LOGIC-308` — 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-271` — 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `LOGIC-258` — 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_paypal.py`

[ ] `LOGIC-289` — 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_stripe.py`

[ ] `LOGIC-276` — 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-265` — 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-264` — 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-290` — 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payouts/payout_batch_service.py`

[ ] `LOGIC-261` — 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/trading_service.py`

[ ] `LOGIC-307` — 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` — 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/background.py`

[ ] `LOGIC-309` — 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` — 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-310` — 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` — 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/hr_service.py`

[ ] `LOGIC-291` — 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 2 function(s) >50 lines; longest sample `create_partner` = 73 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_service.py`

[ ] `LOGIC-311` — 2 function(s) >50 lines; longest sample `create_partner` = 73 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-292` — 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/shipment_service.py`

[ ] `LOGIC-272` — 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_pricing_service.py`

[ ] `LOGIC-273` — 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/partner_service.py`

[ ] `LOGIC-293` — 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-266` — 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-259` — 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_admin.py`

[ ] `LOGIC-278` — 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-267` — 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `LOGIC-277` — 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/returns/service.py`

[ ] `LOGIC-294` — 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `LOGIC-279` — 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/promotion_points_service.py`

[ ] `LOGIC-312` — 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `create_banner` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_promotions_write_service.py`

[ ] `LOGIC-313` — 2 function(s) >50 lines; longest sample `create_banner` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/promotion_service.py`

[ ] `LOGIC-314` — 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SECU` — 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-315` — 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-260` — 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders.py`

[ ] `LOGIC-281` — 4 function(s) >50 lines; longest sample `get_supplier_orders` = 142 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-295` — 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-296` — 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-282` — 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py`

[ ] `LOGIC-316` — 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-280` — 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/seed/_common.py`

[ ] `LOGIC-274` — 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/email_service.py`

[ ] `LOGIC-283` — 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/realtime.py`

[ ] `LOGIC-297` — 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 2 function(s) >50 lines; longest sample `with_retry` = 87 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/retry.py`

[ ] `LOGIC-317` — 2 function(s) >50 lines; longest sample `with_retry` = 87 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/schema_audit.py`

[ ] `LOGIC-284` — 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-AI` — 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/ai_variant_config.py`

[ ] `LOGIC-285` — 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` — 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-298` — 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-IM` — 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/parcel_verification.py`

[ ] `LOGIC-275` — 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` — 3 function(s) >50 lines; longest sample `create_order` = 79 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paypal.py`

[ ] `LOGIC-299` — 3 function(s) >50 lines; longest sample `create_order` = 79 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-LONG-FUNCTION-BACKEND-PROVIDERS-PA` — 3 function(s) >50 lines; longest sample `create_payment_page` = 90 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paytabs.py`

[ ] `LOGIC-300` — 3 function(s) >50 lines; longest sample `create_payment_page` = 90 lines
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-MIDDLEWARE` — middleware order is ['foundation', 'geo', 'security', 'rate', 'compliance', 'observe', 'auth', 'webhook']; canonical is ['foundation', 'auth

- **cluster:** `CLUSTER-middleware` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/orchestrator.py`

[ ] `WIRE-001` — middleware order is ['foundation', 'geo', 'security', 'rate', 'compliance', 'observe', 'auth', 'webhook']; canonical is…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'add_middleware\|setup\|install' backend/middleware/orchestrator.py`

##### `WP4-MOBILE-DEPS` — dynamically required package(s) absent from package.json: @/lib/api, @paytabs/react-native-paytabs, @shared/api-core, @tap-as/sdk-react-nati

- **cluster:** `CLUSTER-mobile-deps` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/mobile_app`

[ ] `MOB-001` — dynamically required package(s) absent from package.json: @/lib/api, @paytabs/react-native-paytabs, @shared/api-core, @…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/catalog.py`

[ ] `ARCH-044` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_super_admin`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_super_admin' backend/modules/admin/routers/catalog.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/comms.py`

[ ] `ARCH-045` — `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.messaging.ws_manager.manager' backend/modules/admin/routers/comms.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-ADMI` — `module imports infrastructure`: imports `infrastructure.utils.config.settings`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/governance.py`

[ ] `ARCH-046` — `module imports infrastructure`: imports `infrastructure.utils.config.settings`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.config.settings' backend/modules/admin/routers/governance.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` — `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/catalog.py`

[ ] `ARCH-059` — `module imports infrastructure`: imports `infrastructure.security.dependencies.get_current_user_optional`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.get_current_user_optional' backend/modules/customer/routers/catalog.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` — `module imports infrastructure`: imports `infrastructure.utils.currency_service.get_currency_context`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/country.py`

[ ] `ARCH-060` — `module imports infrastructure`: imports `infrastructure.utils.currency_service.get_currency_context`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.currency_service.get_currency_context' backend/modules/customer/routers/country.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` — `module imports infrastructure`: imports `infrastructure.utils.config.settings`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/orders.py`

[ ] `ARCH-061` — `module imports infrastructure`: imports `infrastructure.utils.config.settings`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.config.settings' backend/modules/customer/routers/orders.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-CUST` — `module imports infrastructure`: imports `infrastructure.storage.storage._store`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/reviews.py`

[ ] `ARCH-062` — `module imports infrastructure`: imports `infrastructure.storage.storage._store`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.storage.storage._store' backend/modules/customer/routers/reviews.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/attendance.py`

[ ] `ARCH-063` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/attendance.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr.py`

[ ] `ARCH-066` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/attendance.py`

[ ] `ARCH-069` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/attendance.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/employees.py`

[ ] `ARCH-070` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/employees.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/leaves.py`

[ ] `ARCH-071` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/leaves.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/offices.py`

[ ] `ARCH-072` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/hr/offices.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/offices.py`

[ ] `ARCH-067` — `module imports infrastructure`: imports `infrastructure.utils.country_rls.enforce_country_access`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.country_rls.enforce_country_access' backend/modules/employee/routers/offices.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-EMPL` — `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/orders.py`

[ ] `ARCH-068` — `module imports infrastructure`: imports `infrastructure.utils.background_jobs.get_job`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.utils.background_jobs.get_job' backend/modules/employee/routers/orders.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/accounts.py`

[ ] `ARCH-087` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/accounts.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/analytics.py`

[ ] `ARCH-088` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/analytics.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/catalog.py`

[ ] `ARCH-089` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/catalog.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/comms.py`

[ ] `ARCH-090` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/comms.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/country.py`

[ ] `ARCH-091` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/country.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/hr.py`

[ ] `ARCH-092` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/hr.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/orders.py`

[ ] `ARCH-095` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/orders.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/promotions.py`

[ ] `ARCH-096` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/promotions.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/security.py`

[ ] `ARCH-097` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/security.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-LOGI` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/suppliers.py`

[ ] `ARCH-098` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_logistics`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_logistics' backend/modules/logistics/routers/suppliers.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/accounts.py`

[ ] `ARCH-099` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/accounts.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/analytics.py`

[ ] `ARCH-100` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/analytics.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/catalog.py`

[ ] `ARCH-101` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/catalog.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/comms.py`

[ ] `ARCH-102` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/comms.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/country.py`

[ ] `ARCH-103` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/country.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/finance.py`

[ ] `ARCH-104` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/finance.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/hr.py`

[ ] `ARCH-105` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/hr.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/logistics.py`

[ ] `ARCH-106` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/logistics.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/orders.py`

[ ] `ARCH-107` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/orders.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/promotions.py`

[ ] `ARCH-108` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/promotions.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/security.py`

[ ] `ARCH-109` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/security.py`

##### `WP4-MODULE-IMPORTS-INFRASTRUCTURE-BACKEND-MODULES-SUPP` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/suppliers.py`

[ ] `ARCH-110` — `module imports infrastructure`: imports `infrastructure.security.dependencies.require_supplier`
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'infrastructure.security.dependencies.require_supplier' backend/modules/supplier/routers/suppliers.py`

##### `WP4-N-PLUS-1` — 305/395 relationship() declarations omit lazy=

- **cluster:** `CLUSTER-n-plus-1` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/`

[ ] `DB-010` — 305/395 relationship() declarations omit lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rn 'relationship(' backend/domains | grep -v 'lazy=' | head`

##### `WP4-OFFSET-PAGINATION` — 90 OFFSET pagination usage(s) (sample: .offset(safe_offset))

- **cluster:** `CLUSTER-offset-pagination` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `DB-012` — 90 OFFSET pagination usage(s) (sample: .offset(safe_offset))
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n '.offset(' backend/domains/accounts/services/auth/auth_service.py`

##### `WP4-ORPHAN-FEATURE` — 231 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.cart.read, accounts.car

- **cluster:** `CLUSTER-orphan-feature` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/`

[ ] `FEAT-010` — 231 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.ca…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-ORPHAN-JOB` — 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler

- **cluster:** `CLUSTER-orphan-job` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/jobs/`

[ ] `OPS-015` — 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-ORPHAN-PROVIDER` — 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_variant_config, apple, ban

- **cluster:** `CLUSTER-orphan-provider` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-009` — 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_varia…
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-PACKAGE-MANAGER` — non-canonical lockfile `package-lock.json` present

- **cluster:** `CLUSTER-package-manager` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/package-lock.json`

[ ] `TECH-013` — non-canonical lockfile `package-lock.json` present
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PII-LOGS` — 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc))

- **cluster:** `CLUSTER-pii-logs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `OBS-005` — 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc))
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

##### `WP4-PRINT-LOGGING` — 3 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159)

- **cluster:** `CLUSTER-print-logging` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/_mixin_compliance.py`

[ ] `OBS-004` — 3 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PROVIDER-CONFIG` — 13 provider module(s) read secrets via raw os.getenv

- **cluster:** `CLUSTER-provider-config` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-007` — 13 provider module(s) read secrets via raw os.getenv
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PROVIDER-EXTRA` — provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py, http.py, news, observ

- **cluster:** `CLUSTER-provider-extra` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-005` — provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py,…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PROVIDER-HEALTH` — 93/93 provider modules lack health_check()

- **cluster:** `CLUSTER-provider-health` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-006` — 93/93 provider modules lack health_check()
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-PROVIDER-TIMEOUT` — 62/93 provider modules declare no timeout

- **cluster:** `CLUSTER-provider-timeout` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-008` — 62/93 provider modules declare no timeout
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-QUALITY-ASSURANCE` — no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach

- **cluster:** `CLUSTER-quality-assurance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains`

[ ] `QA-mechanisms-absent` — no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `grep -rn 'class .*Inspection\|proof_of_delivery\|supplier_score' backend/domains`

##### `WP4-RAW-GETENV` — 126 raw os.getenv/os.environ read(s) in production paths (top: providers=64, infrastructure=38, domains=13, middleware=8, jobs=3)

- **cluster:** `CLUSTER-raw-getenv` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `OPS-016` — 126 raw os.getenv/os.environ read(s) in production paths (top: providers=64, infrastructure=38, domains=13, middleware=…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-READ-REPLICA` — read-replica engine exists but `get_read_db` is never used by domains

- **cluster:** `CLUSTER-read-replica` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `DB-007` — read-replica engine exists but `get_read_db` is never used by domains
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-SEARCH-INDEX` — 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%"))

- **cluster:** `CLUSTER-search-index` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `DB-013` — 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%"))
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-SELECT-STAR` — 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version")))

- **cluster:** `CLUSTER-select-star` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/check_db.py`

[ ] `DB-011` — 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version")))
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-SILENT-EXCEPT-BACKEND-CONFIG-PY` — 1 silent except block(s); first at line 895: truly-silent: except AttributeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/config.py`

[ ] `LOGIC-049` — 1 silent except block(s); first at line 895: truly-silent: except AttributeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/config.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` — 6 silent except block(s); first at line 3044: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `LOGIC-003` — 6 silent except block(s); first at line 3044: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/accounts/services/auth/auth_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` — 1 silent except block(s); first at line 69: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/public_security_registration_service.py`

[ ] `LOGIC-052` — 1 silent except block(s); first at line 69: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/accounts/services/auth/public_security_registration_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 3 silent except block(s); first at line 54: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/commission_service.py`

[ ] `LOGIC-013` — 3 silent except block(s); first at line 54: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/catalog/services/commission_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-014` — 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/catalog/services/products/products_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 1 silent except block(s); first at line 212: pass-only: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-053` — 1 silent except block(s); first at line 212: pass-only: except (TypeError, ValueError, json.JSONDecodeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/catalog/services/search/search_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 454: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/email_management.py`

[ ] `LOGIC-055` — 1 silent except block(s); first at line 454: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/comms/services/email/email_management.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/websocket_handlers.py`

[ ] `LOGIC-056` — 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/comms/services/messaging/websocket_handlers.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 166: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/notification_gateway.py`

[ ] `LOGIC-054` — 1 silent except block(s); first at line 166: truly-silent: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/comms/services/notification_gateway.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/public_comms_status_service.py`

[ ] `LOGIC-015` — 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/comms/services/public_comms_status_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/system_comms_status_service.py`

[ ] `LOGIC-023` — 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/comms/services/system_comms_status_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_config_version_service.py`

[ ] `LOGIC-057` — 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/country/services/core/country_config_version_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 191: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `LOGIC-058` — 1 silent except block(s); first at line 191: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/country/services/core/country_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/cross_border/cross_border_service.py`

[ ] `LOGIC-059` — 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/country/services/cross_border/cross_border_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 480: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_ai_research.py`

[ ] `LOGIC-060` — 1 silent except block(s); first at line 480: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/country/services/research/country_ai_research.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` — 2 silent except block(s); first at line 130: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/coins/zozi_coins_service.py`

[ ] `LOGIC-024` — 2 silent except block(s); first at line 130: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/customers/services/coins/zozi_coins_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` — 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/public_comms_status_service.py`

[ ] `LOGIC-016` — 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/customers/services/public_comms_status_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` — 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-061` — 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/customers/services/search_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-062` — 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/data_import_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 87: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_ai_service.py`

[ ] `LOGIC-063` — 1 silent except block(s); first at line 87: pass-only: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/finance_ai_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 5 silent except block(s); first at line 3774: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `LOGIC-006` — 5 silent except block(s); first at line 3774: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/ledger/general_ledger.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 2 silent except block(s); first at line 1111: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-025` — 2 silent except block(s); first at line 1111: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/payments/gateway_tap.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 3411: truly-silent: except HTTPException as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-064` — 1 silent except block(s); first at line 3411: truly-silent: except HTTPException as exc:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/payments/payment_engine.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 2 silent except block(s); first at line 693: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-026` — 2 silent except block(s); first at line 693: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/finance/services/payments/payment_orchestrator.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` — 2 silent except block(s); first at line 307: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-027` — 2 silent except block(s); first at line 307: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/governance/services/command_center/command_center_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` — 1 silent except block(s); first at line 43: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `LOGIC-065` — 1 silent except block(s); first at line 43: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/governance/services/command_center/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 2 silent except block(s); first at line 97: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_service.py`

[ ] `LOGIC-028` — 2 silent except block(s); first at line 97: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/hr/services/payroll/payroll_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 1 silent except block(s); first at line 120: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/okr.py`

[ ] `LOGIC-066` — 1 silent except block(s); first at line 120: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/hr/services/performance/okr.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 1 silent except block(s); first at line 85: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/reviews.py`

[ ] `LOGIC-067` — 1 silent except block(s); first at line 85: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/hr/services/performance/reviews.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/logistics_engine.py`

[ ] `LOGIC-068` — 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/core/logistics_engine.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 6 silent except block(s); first at line 1439: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-004` — 6 silent except block(s); first at line 1439: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/core/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/zone_service.py`

[ ] `LOGIC-069` — 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/core/zone_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 355: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `LOGIC-029` — 2 silent except block(s); first at line 355: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/contract_service.py`

[ ] `LOGIC-070` — 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/contract_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/partner_service.py`

[ ] `LOGIC-017` — 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/partner_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 508: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-030` — 2 silent except block(s); first at line 508: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/sla/service.py`

[ ] `LOGIC-031` — 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/logistics/services/sla/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-007` — 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/orders/services/core/logistics.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 5 silent except block(s); first at line 211: pass-only: except AttributeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-008` — 5 silent except block(s); first at line 211: pass-only: except AttributeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/orders/services/core/order_engine.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/returns/service.py`

[ ] `LOGIC-071` — 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/orders/services/returns/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `LOGIC-072` — 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/orders/services/tracking/service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` — 1 silent except block(s); first at line 527: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/coupon_service.py`

[ ] `LOGIC-073` — 1 silent except block(s); first at line 527: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/promotions/services/coupons/coupon_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 78: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/core/kms_encryption.py`

[ ] `LOGIC-075` — 1 silent except block(s); first at line 78: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/security/services/core/kms_encryption.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 44: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/detection/public_security_detection_service.py`

[ ] `LOGIC-076` — 1 silent except block(s); first at line 44: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/security/services/detection/public_security_detection_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 6 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-005` — 6 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/security/services/fraud/fraud_detection_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 30: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/security_provider_helpers.py`

[ ] `LOGIC-074` — 1 silent except block(s); first at line 30: pass-only: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/security/services/security_provider_helpers.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 9 silent except block(s); first at line 1430: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-001` — 9 silent except block(s); first at line 1430: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/health/supplier_health.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 3 silent except block(s); first at line 518: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-018` — 3 silent except block(s); first at line 518: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 2 silent except block(s); first at line 139: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_verify_service.py`

[ ] `LOGIC-032` — 2 silent except block(s); first at line 139: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_verify_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-077` — 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_product_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 5 silent except block(s); first at line 280: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-009` — 5 silent except block(s); first at line 280: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_products.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 1 silent except block(s); first at line 203: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products_service.py`

[ ] `LOGIC-078` — 1 silent except block(s); first at line 203: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_products_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-010` — 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/domains/suppliers/services/supplier_shared.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 188: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/database_service.py`

[ ] `LOGIC-079` — 1 silent except block(s); first at line 188: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/database/database_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 174: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/rls_interceptor.py`

[ ] `LOGIC-033` — 2 silent except block(s); first at line 174: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/database/rls_interceptor.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/schemas.py`

[ ] `LOGIC-019` — 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/database/schemas.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 113: pass-only: except Exception:  # noqa: BLE001

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/events/event_bus.py`

[ ] `LOGIC-035` — 2 silent except block(s); first at line 113: pass-only: except Exception: # noqa: BLE001
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/messaging/events/event_bus.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 599: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/realtime.py`

[ ] `LOGIC-080` — 1 silent except block(s); first at line 599: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/messaging/realtime.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/ws_manager.py`

[ ] `LOGIC-034` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/messaging/ws_manager.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 92: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/ml/worker.py`

[ ] `LOGIC-081` — 1 silent except block(s); first at line 92: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/ml/worker.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 323: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/audit.py`

[ ] `LOGIC-082` — 1 silent except block(s); first at line 323: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/observability/audit.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 22: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/provider_observability.py`

[ ] `LOGIC-036` — 2 silent except block(s); first at line 22: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/observability/provider_observability.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 132: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/service_observability.py`

[ ] `LOGIC-083` — 1 silent except block(s); first at line 132: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/observability/service_observability.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 3 silent except block(s); first at line 49: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/security/dependencies.py`

[ ] `LOGIC-020` — 3 silent except block(s); first at line 49: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/security/dependencies.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 26: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/security/kms_integration.py`

[ ] `LOGIC-084` — 1 silent except block(s); first at line 26: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/security/kms_integration.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 57: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/analytics.py`

[ ] `LOGIC-037` — 2 silent except block(s); first at line 57: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/utils/analytics.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/pagination.py`

[ ] `LOGIC-038` — 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/utils/pagination.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 110: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/performance_cache.py`

[ ] `LOGIC-039` — 2 silent except block(s); first at line 110: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/utils/performance_cache.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 7 silent except block(s); first at line 67: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/schema_audit.py`

[ ] `LOGIC-002` — 7 silent except block(s); first at line 67: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/utils/schema_audit.py`

##### `WP4-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/websocket_manager.py`

[ ] `LOGIC-040` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/infrastructure/utils/websocket_manager.py`

##### `WP4-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` — 1 silent except block(s); first at line 293: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/lifespan.py`

[ ] `LOGIC-050` — 1 silent except block(s); first at line 293: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/lifespan.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MAIN-PY` — 1 silent except block(s); first at line 199: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/main.py`

[ ] `LOGIC-051` — 1 silent except block(s); first at line 199: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/main.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` — 3 silent except block(s); first at line 245: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/country_context.py`

[ ] `LOGIC-021` — 3 silent except block(s); first at line 245: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/middleware/country_context.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` — 1 silent except block(s); first at line 424: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/webhook_ip_whitelist.py`

[ ] `LOGIC-085` — 1 silent except block(s); first at line 424: truly-silent: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/middleware/webhook_ip_whitelist.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` — 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/webhook_verification.py`

[ ] `LOGIC-011` — 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/middleware/webhook_verification.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MODULES-ADMI` — 2 silent except block(s); first at line 150: pass-only: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/comms.py`

[ ] `LOGIC-041` — 2 silent except block(s); first at line 150: pass-only: except WebSocketDisconnect:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/modules/admin/routers/comms.py`

##### `WP4-SILENT-EXCEPT-BACKEND-MODULES-CUST` — 3 silent except block(s); first at line 160: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/orders.py`

[ ] `LOGIC-022` — 3 silent except block(s); first at line 160: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/modules/customer/routers/orders.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 1 silent except block(s); first at line 88: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/finance_ai.py`

[ ] `LOGIC-086` — 1 silent except block(s); first at line 88: pass-only: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/ai/finance_ai.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/huggingface.py`

[ ] `LOGIC-043` — 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/ai/huggingface.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 231: pass-only: except OSError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/image_ai_service.py`

[ ] `LOGIC-044` — 2 silent except block(s); first at line 231: pass-only: except OSError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/ai/image_ai_service.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 281: truly-silent: except json.JSONDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/text.py`

[ ] `LOGIC-045` — 2 silent except block(s); first at line 281: truly-silent: except json.JSONDecodeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/ai/text.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` — 1 silent except block(s); first at line 148: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/comms/whatsapp_selfhosted.py`

[ ] `LOGIC-087` — 1 silent except block(s); first at line 148: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/comms/whatsapp_selfhosted.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` — 1 silent except block(s); first at line 115: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/finance/bank_api.py`

[ ] `LOGIC-088` — 1 silent except block(s); first at line 115: truly-silent: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/finance/bank_api.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` — 1 silent except block(s); first at line 108: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/geography/geo.py`

[ ] `LOGIC-089` — 1 silent except block(s); first at line 108: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/geography/geo.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 35: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/br_05__clean_edge_refiner.py`

[ ] `LOGIC-092` — 1 silent except block(s); first at line 35: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/bg_remover/br_05__clean_edge_refiner.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 237: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/br_06__precision_geometry_classes.py`

[ ] `LOGIC-093` — 1 silent except block(s); first at line 237: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/bg_remover/br_06__precision_geometry_classes.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 155: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/core_i_o.py`

[ ] `LOGIC-094` — 1 silent except block(s); first at line 155: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/bg_remover/core_i_o.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 302: truly-silent: except Exception as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/public_api.py`

[ ] `LOGIC-095` — 1 silent except block(s); first at line 302: truly-silent: except Exception as exc:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/bg_remover/public_api.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 113: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/session_management.py`

[ ] `LOGIC-096` — 1 silent except block(s); first at line 113: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/bg_remover/session_management.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 288: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-090` — 1 silent except block(s); first at line 288: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/free_image_tools.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 4 silent except block(s); first at line 95: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/ocr.py`

[ ] `LOGIC-012` — 4 silent except block(s); first at line 95: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/ocr.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 510: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/parcel_verification.py`

[ ] `LOGIC-091` — 1 silent except block(s); first at line 510: truly-silent: except (ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/image/parcel_verification.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` — 2 silent except block(s); first at line 24: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/observability.py`

[ ] `LOGIC-042` — 2 silent except block(s); first at line 24: pass-only: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/observability.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` — 1 silent except block(s); first at line 44: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ocr/ocr_parser.py`

[ ] `LOGIC-097` — 1 silent except block(s); first at line 44: truly-silent: except ValueError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/ocr/ocr_parser.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` — 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/generic.py`

[ ] `LOGIC-046` — 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/payments/generic.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` — 2 silent except block(s); first at line 135: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paypal.py`

[ ] `LOGIC-047` — 2 silent except block(s); first at line 135: truly-silent: except (TypeError, ValueError):
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/payments/paypal.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` — 2 silent except block(s); first at line 95: truly-silent: except UnicodeDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/scanner/scanner.py`

[ ] `LOGIC-048` — 2 silent except block(s); first at line 95: truly-silent: except UnicodeDecodeError:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/scanner/scanner.py`

##### `WP4-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` — 1 silent except block(s); first at line 73: truly-silent: except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/security/watchlist.py`

[ ] `LOGIC-098` — 1 silent except block(s); first at line 73: truly-silent: except (urllib.error.URLError, json.JSONDecodeError, KeyError…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/providers/security/watchlist.py`

##### `WP4-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` — 1 silent except block(s); first at line 33: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/rbac/catalog.py`

[ ] `LOGIC-099` — 1 silent except block(s); first at line 33: truly-silent: except Exception:
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -n 'except' backend/rbac/catalog.py`

##### `WP4-TABLE-GOVERNANCE` — 9 table(s) lack audit timestamps and 4 lack soft delete

- **cluster:** `CLUSTER-table-governance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains`

[ ] `DB-missing-governance-columns` — 9 table(s) lack audit timestamps and 4 lack soft delete
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `pytest backend/tests/architecture -k compliance`

##### `WP4-TABLE-INDEX` — 233 (table, column) pair(s) are filtered or sorted on with no declared index

- **cluster:** `CLUSTER-table-index` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains`

[ ] `DB-unindexed-hot-column` — 233 (table, column) pair(s) are filtered or sorted on with no declared index
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.
    - verify: `python _zozi_audit/zozi_compile.py --report db`

##### `WP4-TABLE-RELATION` — 305 of 390 relationship() calls omit lazy=

- **cluster:** `CLUSTER-table-relation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/infrastructure/database`

[ ] `DB-relationship-loading` — 305 of 390 relationship() calls omit lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.
    - verify: `grep -rEc 'relationship\(' backend/domains --include=*.py | awk -F: '$2>0' | wc -l`

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `addresses`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `TF-001` — 1x rel lazy in table `addresses`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/models/onboarding.py`

[ ] `TF-004` — 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `otp_codes`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/models/otp.py`

[ ] `TF-007` — 1x rel lazy in table `otp_codes`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/catalog/models/ai_upload.py`

[ ] `TF-016` — 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/catalog/models/chart_of_categories.py`

[ ] `TF-019` — 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/catalog/models/commission.py`

[ ] `TF-023` — 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/fraud.py`

[ ] `TF-093` — 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/incident.py`

[ ] `TF-094` — 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `messages`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/message.py`

[ ] `TF-106` — 3x rel lazy in table `messages`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 17x rel lazy in table `country_configs`: relationship `communications` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/countries.py`

[ ] `TF-109` — 17x rel lazy in table `country_configs`: relationship `communications` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_basics`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_basics.py`

[ ] `TF-115` — 1x rel lazy in table `country_basics`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_control.py`

[ ] `TF-116` — 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_economics`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_economics.py`

[ ] `TF-125` — 1x rel lazy in table `country_economics`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_legals`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_legal.py`

[ ] `TF-153` — 1x rel lazy in table `country_legals`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_taxes`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_tax.py`

[ ] `TF-155` — 1x rel lazy in table `country_taxes`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` — 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/customers/models/cross_country_session.py`

[ ] `TF-158` — 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-CUST` — 2x rel lazy in table `referrals`: relationship `referrer` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/customers/models/customer_schema_models.py`

[ ] `TF-160` — 2x rel lazy in table `referrals`: relationship `referrer` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-FINA` — 1x rel lazy in table `payout_rules`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/finance/models/tax_rules.py`

[ ] `TF-188` — 1x rel lazy in table `payout_rules`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` — 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/governance/models/legal_contract_template.py`

[ ] `TF-202` — 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `TF-240` — 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/shipping_rules.py`

[ ] `TF-256` — 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/promotion_config.py`

[ ] `TF-269` — 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/security/models/security_schema_models.py`

[ ] `TF-284` — 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-REL-LAZY-BACKEND-RBAC-MODELS-` — 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/rbac/models/permission_entities.py`

[ ] `TF-301` — 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy=
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` — 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/catalog/models/upload_job.py`

[ ] `TF-035` — 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `messages`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/message.py`

[ ] `TF-105` — 1x timestamp default in table `messages`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 2x timestamp default in table `news_articles`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/news.py`

[ ] `TF-107` — 2x timestamp default in table `news_articles`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_basics`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_basics.py`

[ ] `TF-113` — 2x timestamp default in table `country_basics`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_economics`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_economics.py`

[ ] `TF-124` — 2x timestamp default in table `country_economics`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_legals`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_legal.py`

[ ] `TF-152` — 2x timestamp default in table `country_legals`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_tax.py`

[ ] `TF-154` — 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` — 1x timestamp default in table `cross_country_customer_sessions`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/customers/models/cross_country_session.py`

[ ] `TF-157` — 1x timestamp default in table `cross_country_customer_sessions`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/logistics_schema_models.py`

[ ] `TF-254` — 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/shipping_rules.py`

[ ] `TF-255` — 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` — 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `TF-266` — 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` — 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/promotion_config.py`

[ ] `TF-268` — 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-TODO-HYGIENE` — 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts/models/core.py:58; backend/domains/accounts/models

- **cluster:** `CLUSTER-todo-hygiene` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `LOGIC-319` — 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts/models/core.py:58; backend/do…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-ACCO` — file has 4518 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `FILE-127` — file has 4518 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-CATA` — function `_preprocess_for_ai` duplicates `backend/domains/catalog/services/ai_upload_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/ai_upload_service.py`

[ ] `FILE-010` — function `_preprocess_for_ai` duplicates `backend/domains/catalog/services/ai_upload_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-COUN` — file has 1970 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `FILE-128` — file has 1970 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` — file has 1858 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `FILE-130` — file has 1858 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` — file has 4725 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `FILE-131` — file has 4725 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` — file has 1775 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `FILE-132` — file has 1775 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-FINA` — file has 4150 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/services/payouts/payout_batch_service.py`

[ ] `FILE-133` — file has 4150 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-LOGI` — function `_serialize_lp_doc` duplicates `backend/domains/logistics/services/core/admin_service.py` (normalized AST)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/contract_service.py`

[ ] `FILE-100` — function `_serialize_lp_doc` duplicates `backend/domains/logistics/services/core/admin_service.py` (normalized AST)
    - confirm: the audit could not establish this statically (L2/INFERRED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` — file has 5104 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `FILE-137` — file has 5104 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-ORDE` — file has 1633 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `FILE-138` — file has 1633 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-DOMAINS-SUPP` — file has 2786 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `FILE-139` — file has 2786 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-INFRASTRUCTU` — file has 2230 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/infrastructure/database/schemas.py`

[ ] `FILE-140` — file has 2230 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNCATEGORISED-BACKEND-MODULES-EMPL` — file has 1553 lines (split candidate)

- **cluster:** `CLUSTER-uncategorised` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/modules/employee/routers/finance.py`

[ ] `FILE-141` — file has 1553 lines (split candidate)
    - confirm: the audit could not establish this statically (L1/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/analytics.py`

[ ] `WIRE-019` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/finance.py`

[ ] `WIRE-045` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `list_employees_public` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/employees.py`

[ ] `WIRE-050` — endpoint `list_employees_public` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-EMPL` — endpoint `health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/suppliers.py`

[ ] `WIRE-049` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` — endpoint `health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/analytics.py`

[ ] `WIRE-053` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNGATED-ROUTE-BACKEND-MODULES-LOGI` — endpoint `health` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/finance.py`

[ ] `WIRE-054` — endpoint `health` has no visible auth/feature gate
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-UNKNOWN-GATE` — 13 require_feature literal(s) not found in any domains/*/features.py catalog: catalog.review.create, moderation.suppliers, promotions.flash_

- **cluster:** `CLUSTER-unknown-gate` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/disputes.py`

[ ] `WIRE-057` — 13 require_feature literal(s) not found in any domains/*/features.py catalog: catalog.review.create, moderation.supplie…
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WEB-IMAGES` — next/image formats do not enable AVIF

- **cluster:** `CLUSTER-web-images` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/next.config.ts`

[ ] `WEB-005` — next/image formats do not enable AVIF
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WEB-REWRITES` — rewrite `/hr/*` targets a non-canonical backend surface

- **cluster:** `CLUSTER-web-rewrites` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/next.config.ts`

[ ] `WEB-004` — rewrite `/hr/*` targets a non-canonical backend surface
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WEB-ROUTES` — duplicate route trees `logistics-partner` and `logistics-partners` both exist

- **cluster:** `CLUSTER-web-routes` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src/app/logistics-partner`

[ ] `WEB-003` — duplicate route trees `logistics-partner` and `logistics-partners` both exist
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WEB-STATES` — 282 page(s) lack loading/error siblings (sample frontend/web_app/src/app/admin/accounting/loading.tsx)

- **cluster:** `CLUSTER-web-states` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src/app/admin/accounting/page.tsx`

[ ] `WEB-002` — 282 page(s) lack loading/error siblings (sample frontend/web_app/src/app/admin/accounting/loading.tsx)
    - confirm: the audit could not establish this statically (L0/VERIFIED). Read the cited location and decide.

##### `WP4-WORM` — audit trail mutates rows after INSERT (UPDATE on audit table)

- **cluster:** `CLUSTER-worm` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/worm_audit.py`

[ ] `SEC-007` — audit trail mutates rows after INSERT (UPDATE on audit table)
    - confirm: the audit could not establish this statically (L1/INFERRED). Read the cited location and decide.

_This wave has 1027 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 5 · Improvement track — recommendations (not release-gating)

> Improvement track. These do not gate a release. Prioritise by the workload they remove, not by severity.

#### Work packages in wave 5 (8)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP5-RECOMMENDATIONS-REC-AUTOMATION` | 8 | 7 | 0 | 0 | 13.0 | Automate the human-in-the-loop queue and the serial write loops |
| `WP5-RECOMMENDATIONS-REC-DATA` | 4 | 5 | 0 | 0 | 27.5 | Model and seed the full 5-tier product taxonomy |
| `WP5-RECOMMENDATIONS-REC-OPS` | 2 | 2 | 0 | 0 | 2.0 | Add a dispatch smoke test for every scheduled task |
| `WP5-RECOMMENDATIONS-REC-WORKFLOW` | 2 | 2 | 0 | 0 | 26.0 | Turn the event spine into real work, or delete it |
| `WP5-RECOMMENDATIONS-REC-DESIGN` | 1 | 1 | 0 | 0 | 6.0 | Adopt the existing UI primitives and delete duplicated markup |
| `WP5-RECOMMENDATIONS-REC-FINANCE` | 1 | 1 | 0 | 0 | 20.0 | Automate the manual finance processes end to end |
| `WP5-RECOMMENDATIONS-REC-FRONTEND` | 1 | 1 | 0 | 0 | 2.5 | Standardise interaction state handling across all screens |
| `WP5-RECOMMENDATIONS-REC-QA` | 1 | 1 | 0 | 0 | 20.0 | Introduce a quality-gate chain across fulfilment |

##### `WP5-RECOMMENDATIONS-REC-AUTOMATION` — Automate the human-in-the-loop queue and the serial write loops

- **cluster:** `recommendations` · **steps:** 8 (0 closed) · **files:** 7 · **est.:** 13.0h
- **files:** `backend/domains/finance/models/general_ledger.py:640, backend/domains/governance/services/workflow_engine.py:116, backend/domains/hr/services/payroll/payroll_engine.py:885, backend/domains/hr/services/payroll/payroll_service.py:140`, `backend/domains/hr/models/employee_models.py:493, backend/domains/security/models/fraud.py:22, backend/domains/security/models/fraud.py:92, backend/domains/security/models/fraud.py:330`, `backend/domains/audit/services/compliance_engine.py:133, backend/domains/hr/services/compliance_engine.py:131, backend/domains/suppliers/services/onboarding/__init__.py:38`, `backend/domains/finance/services/payments/gateway_stripe.py:630, backend/domains/finance/services/payments/gateway_tap.py:474, backend/domains/finance/services/payments/gateway_tap.py:735`, `backend/domains/finance/services/ledger/general_ledger.py:2977, backend/providers/payments/webhook_models.py:28`, `scripts/audit/full_system_audit.py:2904, scripts/audit/full_system_audit.py:2914`, `backend/domains/finance/services/payments/payment_engine.py:325`

[ ] `REC-AUTOMATION-001` — Automate the human-in-the-loop queue and the serial write loops
    - do: for each human-waiting status define an auto-rule with a confidence threshold and an escalation path: e.g. auto-resolve payout holds when the bank line matches the expected amount; auto-assign unreviewed fraud flags round-robin with a firs…
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-002` — Auto-route `pending_approval` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-003` — Auto-route `escalated` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-004` — Auto-route `pending_review` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-005` — Auto-route `pending_verification` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-006` — Auto-route `disputed` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-007` — Auto-route `manual_review` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-AUTOMATION-008` — Auto-route `hold` work
    - do: add a queue table with assignee, SLA and a rule-based auto-assign; surface queue age on the admin dashboard.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-DATA` — Model and seed the full 5-tier product taxonomy

- **cluster:** `recommendations` · **steps:** 4 (0 closed) · **files:** 5 · **est.:** 27.5h
- **files:** `backend/domains/catalog/models/products.py`, `observed depth 3/5`, `backend/domains/**/models/*.py (accounts.supplier_bank_accounts.currency`, `backend/domains/**/models/*.py (178 tables)`, `backend/alembic/versions vs backend/domains/**/models`

[ ] `REC-DATA-001` — Model and seed the full 5-tier product taxonomy
    - do: 1) ship a versioned taxonomy seed covering the 5 tiers; 2) rebuild depth/path on every write via the existing tree builder; 3) add a category tree editor with drag-to-reparent and cycle detection; 4) add facet filters that read the same pa…
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-DATA-002` — Add the missing indexes as model + migration pairs
    - do: generate the index list, add each to the model __table_args__ and write one Alembic migration creating them CONCURRENTLY; add a test asserting every HOT_COLUMN present in a model is indexed.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-DATA-003` — Add optimistic-locking `version` to high-contention tables
    - do: add `version` (with a SQLAlchemy version_id_col) to the tables that are written from more than one process: ledger, payouts, orders, inventory, KYC; leave reference tables alone.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-DATA-004` — Reconcile migration schema names with ORM metadata
    - do: 1) diff every schema literal in migrations against Base.metadata.schemas; 2) write corrective migrations; 3) add a CI test asserting the two sets are equal.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-OPS` — Add a dispatch smoke test for every scheduled task

- **cluster:** `recommendations` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 2.0h
- **files:** `backend/jobs/*.py`, `backend/middleware/security_headers.py`

[ ] `REC-OPS-001` — Add a dispatch smoke test for every scheduled task
    - do: add a test that imports every task module and asserts each task's callable resolves, plus a startup self-check in the worker entrypoint that exits non-zero on an unresolvable task.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-OPS-002` — Replace hand-rolled CORS headers with Starlette CORSMiddleware
    - do: mount `CORSMiddleware` once at app level with allow_origins, allow_methods, allow_headers and allow_credentials; delete the manual header writes; add a preflight test that asserts the status code, not just the headers.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-WORKFLOW` — Turn the event spine into real work, or delete it

- **cluster:** `recommendations` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 26.0h
- **files:** `backend/domains/*/subscribers.py`, `backend/domains/*/**handover*, *_handover*`

[ ] `REC-WORKFLOW-001` — Turn the event spine into real work, or delete it
    - do: triage each handler into (a) implement now, (b) schedule as a remediation item with an owner, (c) delete the publication. Add a test that asserts a published event reaches a handler that performs a write.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`
[ ] `REC-WORKFLOW-002` — Guarantee custody transfer with a single HandoverService
    - do: one HandoverService.transfer(obj, from_party, to_party, reason) that (1) checks permission on both sides, (2) writes an immutable audit record with before/after, (3) notifies both parties, (4) records both ids, (5) is idempotent; then add…
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-DESIGN` — Adopt the existing UI primitives and delete duplicated markup

- **cluster:** `recommendations` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `frontend/web_app/src/components/ui`

[ ] `REC-DESIGN-001` — Adopt the existing UI primitives and delete duplicated markup
    - do: codemod the duplicated class strings to the primitives, then add a lint rule forbidding raw card/input class strings.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-FINANCE` — Automate the manual finance processes end to end

- **cluster:** `recommendations` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/finance (missing: bad_debt_provision)`

[ ] `REC-FINANCE-001` — Automate the manual finance processes end to end
    - do: sequence: (1) gateway-fee reconciliation from settlement files, (2) automated COD remittance on bank credit match, (3) daily bank reconciliation with an unmatched-items report, (4) commission accrual at order capture instead of at payout,…
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-FRONTEND` — Standardise interaction state handling across all screens

- **cluster:** `recommendations` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src (1466 button elements)`

[ ] `REC-FRONTEND-001` — Standardise interaction state handling across all screens
    - do: give the Button primitive a built-in `pending` state that disables itself, and require mutations to pass through one `useMutation` helper that always toasts success and failure.
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

##### `WP5-RECOMMENDATIONS-REC-QA` — Introduce a quality-gate chain across fulfilment

- **cluster:** `recommendations` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains (absent: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach)`

[ ] `REC-QA-001` — Introduce a quality-gate chain across fulfilment
    - do: implement a QualityGate chain: (1) inbound inspection record, (2) dispatch-readiness checklist blocking pick when unmet, (3) proof-of-delivery capture (photo/signature/OTP) required before `delivered`, (4) return reason codes feeding the s…
    - verify: `python _zozi_audit/zozi_audit.py --full # re-measure the metric this recommendation cites`

[ ] `REC-DATA-001` — Model and seed the full 5-tier product taxonomy
[ ] `REC-FINANCE-001` — Automate the manual finance processes end to end
[ ] `REC-QA-001` — Introduce a quality-gate chain across fulfilment
[ ] `REC-WORKFLOW-001` — Turn the event spine into real work, or delete it
[ ] `REC-AUTOMATION-001` — Automate the human-in-the-loop queue and the serial write loops
[ ] `REC-DESIGN-001` — Adopt the existing UI primitives and delete duplicated markup
[ ] `REC-WORKFLOW-002` — Guarantee custody transfer with a single HandoverService
[ ] `REC-DATA-002` — Add the missing indexes as model + migration pairs
[ ] `REC-DATA-003` — Add optimistic-locking `version` to high-contention tables
[ ] `REC-DATA-004` — Reconcile migration schema names with ORM metadata
[ ] `REC-FRONTEND-001` — Standardise interaction state handling across all screens
[ ] `REC-AUTOMATION-002` — Auto-route `pending_approval` work
[ ] `REC-AUTOMATION-003` — Auto-route `escalated` work
[ ] `REC-AUTOMATION-004` — Auto-route `pending_review` work
[ ] `REC-AUTOMATION-005` — Auto-route `pending_verification` work
[ ] `REC-AUTOMATION-006` — Auto-route `disputed` work
[ ] `REC-AUTOMATION-007` — Auto-route `manual_review` work
[ ] `REC-AUTOMATION-008` — Auto-route `hold` work
[ ] `REC-OPS-001` — Add a dispatch smoke test for every scheduled task
[ ] `REC-OPS-002` — Replace hand-rolled CORS headers with Starlette CORSMiddleware
---
## Rejected findings (not work)

54 finding(s) were disproved or found already fixed by `zozi_verify.py`. They are excluded from every wave above and are recorded here so the exclusion is auditable.

| ID | Verdict | Cluster | Priority | Counter-evidence |
|----|---------|---------|----------|------------------|
| `SC-004` | FALSE_POSITIVE | `CLUSTER-supply-chain` | P1 | none of the 2 claim token(s) (container, scan) appear in any of the 5 file(s) under .github/workflows/ |
| `FILE-001` | FALSE_POSITIVE | `CLUSTER-root-discipline` | P1 | none of the 8 claim token(s) (_tmp_check_setcookie.py, _tmp_check_accounts.py, _tmp_check_triggers.py, _tmp_c… |
| `D2P-003` | ALREADY_FIXED | `CLUSTER-deploy` | P2 | none of the 2 claim token(s) (HEALTHCHECK, container) appear anywhere in backend/Dockerfile |
| `D2P-004` | ALREADY_FIXED | `CLUSTER-deploy` | P2 | none of the 2 claim token(s) (HEALTHCHECK, container) appear anywhere in backend/Dockerfile.prod |
| `TECH-022` | ALREADY_FIXED | `CLUSTER-lockfile` | P1 | none of the 3 claim token(s) (project.dependencies, pyproject.toml, declares) appear anywhere in backend/pypr… |
| `LOGIC-101` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/analytics/services/dashboards/admin_analytics_service.py:37 no longer contains a float near t… |
| `LOGIC-102` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/analytics/services/dashboards/analytics_service.py:282 no longer contains a float near the ci… |
| `LOGIC-111` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/comms/services/email/email_management.py:341 no longer contains a float near the cited locati… |
| `LOGIC-116` | FALSE_POSITIVE | `CLUSTER-float-money` | P1 | backend/domains/country/services/core/country_config_admin_service.py:282 `tax_rate` is a rate/ratio, not a m… |
| `LOGIC-123` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/customers/services/customer_health_engine.py:67 no longer contains a float near the cited loc… |
| `LOGIC-124` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/customers/services/profile_service.py:105 no longer contains a float near the cited location |
| `LOGIC-133` | FALSE_POSITIVE | `CLUSTER-float-money` | P0 | backend/domains/finance/services/ledger/general_ledger.py:5836 `VAT_RATES` is a rate/ratio, not a monetary am… |
| `LOGIC-144` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/governance/services/admin/admin_service.py:118 no longer contains a float near the cited loca… |
| `LOGIC-149` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/governance/services/settings/admin_service.py:41 no longer contains a float near the cited lo… |
| `LOGIC-153` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/hr/services/learning/lms_service.py:148 no longer contains a float near the cited location |
| `LOGIC-157` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/hr/services/performance/okr.py:190 no longer contains a float near the cited location |
| `LOGIC-167` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/logistics/services/geo/routing_service.py:68 no longer contains a float near the cited locati… |
| `LOGIC-169` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/logistics/services/health/service.py:63 no longer contains a float near the cited location |
| `LOGIC-183` | ALREADY_FIXED | `CLUSTER-float-money` | P0 | backend/domains/orders/services/tracking/service.py:348 no longer contains a float near the cited location |
| `LOGIC-194` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/security/services/detection/confidence_scoring.py:106 no longer contains a float near the cit… |
| `LOGIC-211` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/suppliers/services/quality/quality_control_service.py:98 no longer contains a float near the… |
| `LOGIC-214` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/suppliers/services/tier/tier_service.py:102 no longer contains a float near the cited location |
| `LOGIC-216` | FALSE_POSITIVE | `CLUSTER-float-money` | P1 | backend/infrastructure/database/seed/logistics.py:18 `total_weight_kg` is a rate/ratio, not a monetary amount… |
| `LOGIC-217` | FALSE_POSITIVE | `CLUSTER-float-money` | P1 | backend/infrastructure/messaging/downstream_wiring.py:124 `tax_rate` is a rate/ratio, not a monetary amount —… |
| `LOGIC-233` | FALSE_POSITIVE | `CLUSTER-float-money` | P0 | backend/modules/employee/routers/orders.py:54 `discount_percent` is a rate/ratio, not a monetary amount — Law… |
| `LOGIC-241` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/providers/ai/ai_variant_config.py:111 no longer contains a float near the cited location |
| `LOGIC-244` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/providers/ai/recommendation.py:273 no longer contains a float near the cited location |
| `LOGIC-246` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/providers/ai/sentiment.py:215 no longer contains a float near the cited location |
| `TF-008` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/accounts/models/user.py:79 relationship() now declares lazy='selectin' |
| `TF-028` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/catalog/models/products.py:103 relationship() now declares lazy='selectin' |
| `TF-029` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/catalog/models/products.py:131 relationship() now declares lazy='selectin' |
| `TF-030` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/catalog/models/products.py:145 relationship() now declares lazy='selectin' |
| `TF-031` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/catalog/models/products.py:159 relationship() now declares lazy='selectin' |
| `TF-032` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/catalog/models/products.py:186 relationship() now declares lazy='selectin' |
| `TF-244` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/logistics/models/logistics_entities.py:88 relationship() now declares lazy='selectin' |
| `TF-260` | FALSE_POSITIVE | `CLUSTER-tf-rel-lazy` | P2 | backend/domains/orders/models/order_entities.py:65 relationship() now declares lazy='selectin' |
| `LOGIC-320` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/customers/services/coins/zozi_coins_service.py declares no idempotency_key field |
| `LOGIC-321` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/customers/services/coins/zozi_coins_service.py declares no idempotency_key field |
| `LOGIC-323` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/promotions/services/coupons/coupon_service.py declares no idempotency_key field |
| `LOGIC-324` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/promotions/services/coupons/coupon_service.py declares no idempotency_key field |
| `LOGIC-325` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/security/services/detection/public_security_detection_service.py declares no idempotency_key… |
| `LOGIC-326` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/security/services/detection/public_security_detection_service.py declares no idempotency_key… |
| `LOGIC-327` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/security/services/detection/public_security_detection_service.py declares no idempotency_key… |
| `LOGIC-328` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/security/services/detection/public_security_detection_service.py declares no idempotency_key… |
| `LOGIC-329` | ALREADY_FIXED | `CLUSTER-idempotency` | P0 | backend/domains/security/services/detection/public_security_detection_service.py declares no idempotency_key… |
| `FILE-005` | ALREADY_FIXED | `CLUSTER-duplicate-file` | P2 | none of the 8 claim token(s) (websocket_manager.py, infrastructure, ws_manager.py, messaging) appear anywhere… |
| `FILE-006` | ALREADY_FIXED | `CLUSTER-duplicate-file` | P2 | none of the 7 claim token(s) (middleware_helpers.py, router_helpers.py, middleware, identical) appear anywher… |
| `FILE-136` | ALREADY_FIXED | `` | P3 | none of the 4 claim token(s) (candidate, split, lines, file) appear anywhere in backend/domains/orders/ports.… |
| `PERF-001` | ALREADY_FIXED | `CLUSTER-bundle` | P3 | none of the 3 claim token(s) (configured, analyzer, bundle) appear anywhere in frontend/web_app/next.config.ts |
| `INTENT-001` | ALREADY_FIXED | `CLUSTER-intent-stub` | P1 | none of the 5 claim token(s) (placeholder, response, module, wired) appear anywhere in backend/domains/comms/… |
| `SEC-cors-preflight-static` | FALSE_POSITIVE | `CLUSTER-http-cors` | P0 | backend/middleware/country_context.py now returns its own response for OPTIONS without calling the router |
| `HTTP-cors-preflight` | FALSE_POSITIVE | `CLUSTER-http-cors` | P0 | backend/middleware/country_context.py now returns its own response for OPTIONS without calling the router |
| `HTTP-cors-preflight` | FALSE_POSITIVE | `CLUSTER-http-cors` | P0 | backend/middleware/country_context.py now returns its own response for OPTIONS without calling the router |
| `HTTP-cookie-flags` | ALREADY_FIXED | `CLUSTER-http-cookies` | P1 | none of the 8 claim token(s) (a27c6a33af01cdc44f302dd7d89ef24bf06124395b737c513300e6a538f8870, csrf_token, Sa… |

---

## Measurement gaps this plan cannot close

The following were measured but cannot be asserted statically. They are listed so nobody mistakes silence for a pass.

- Runtime behaviour: no live boot, HTTP journey, or browser run is part of this plan beyond the pre-flight gate.
- Load and p95 latency: needs `zozi_audit.py --load` against a running stack.
- Third-party gateway behaviour (Stripe/Tap/PayTabs/Thawani/PayPal): needs sandbox credentials and real webhook delivery.
- Mobile (Expo) runtime: no emulator/simulator run is performed.
- LLM-intent agreement: advisory only (L2), never a gate.

---

_Compiled by `_zozi_audit/zozi_compile.py`. Re-run after every audit to refresh this plan._
