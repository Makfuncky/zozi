# ZOZI — Remediation Plan (compiled from the forensic audit)

_Generated 2026-10-06T01:51:47.885770+00:00 from audit run `20261006T014348Z-6f76c8` at commit `3e0d1d818ebc08f1df17c5464543dd96aa7b0d94`._

This is the **solution half** of the audit. The audit states what is wrong; this states what to do, in what order, and how to prove each step is finished.

## How to use this plan

1. Work **wave by wave**. A wave may only start when the previous wave is green — this is what makes the result trustworthy rather than merely different.
2. Wave 0 is the gate: until it passes, no other verification means anything.
3. Each step carries its own `verify` command. Run it. A step whose verification does not change is not done.
4. Steps marked **verify** are *not* instructions to change code. They are claims the audit could not confirm statically; confirm or dismiss them first.
5. Steps marked **improve** are recommendations. They never gate a release.
6. Mark progress with `--status`; the compiler round-trips it.

## Verification gate

- Findings adjudicated: **98.4% independently confirmed**
- False positives + wrong locations: **0.0%**
- Not actionable as stated (incl. already fixed): **0.1%**
- P0 noise (false or mislocated): **0.0%**

A low *confirmed* share is expected and is not a defect: a claim with no independent re-check cannot honestly be called confirmed. It is routed to a verification task instead of being silently trusted.

### How this plan may be followed

1. **Every `fix` step was independently re-derived** before it reached this document. Nothing else is presented as a fix.
2. **A `verify` step is not an instruction to change code.** It is a claim the tooling could not adjudicate; confirm or dismiss it first.
3. **1 finding(s) were rejected outright** (false positive or already fixed) and are listed in the Rejected appendix with counter-evidence. They are not work.
4. **A CONFIRMED verdict proves the claim, not the fix.** The `fix` text still needs engineering review — most of all for law, schema and security changes.

## Totals

- Findings consumed: **1335**
- Findings rejected (false positive / already fixed): **1**
- Confirmed fix steps: **1314**
- Recommendations consumed: **19**
- Release-gating steps: **1314** (~2606.0h at S=1h M=2.5h L=6h XL=20h)
- Improvement steps: **19** (not gating)
- Untrusted claims needing verification first: **0**
- Work packages (the unit of work): **793**

## Work package index

Finish a whole package, not a single line. A package is one cluster touched by one person or one agent, with a single coherent outcome.

| Wave | Package | Steps | Files | Est. h | Focus |
|------|---------|-------|-------|--------|-------|
| 1 | `WP1-IDEMPOTENCY` | 10 | 4 | 25.0 | idempotency_key: Optional[str] = None, |
| 1 | `WP1-FE-DANGEROUS` | 6 | 4 | 6.0 | `dangerouslySetInnerHTML={{` executes or injects untrusted code in th… |
| 1 | `WP1-STUB-SUBSCRIBER` | 4 | 4 | 10.0 | stub subscriber module: 3 handlers, 3 `# Future:` markers |
| 1 | `WP1-PAYMENT-WEBHOOK` | 3 | 3 | 3.0 | payment adapter references webhooks but shows no signature verificati… |
| 1 | `WP1-CONTRADICTION-TARGET-VS-CODE` | 2 | 2 | 5.0 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | back… |
| 1 | `WP1-RLS` | 2 | 2 | 5.0 | canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` e… |
| 1 | `WP1-AP-TODO-ONLY-IMPLEMENTATION` | 1 | 1 | 2.5 | TODO-only implementation: 151 occurrence(s); sample `backend/domains/… |
| 1 | `WP1-AP-UNIMPLEMENTED-PLACEHOLDER` | 1 | 1 | 2.5 | Unimplemented placeholder: 257 occurrence(s); sample `backend/domains… |
| 1 | `WP1-CHAIN-CHAIN-005` | 1 | 1 | 6.0 | CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 s… |
| 1 | `WP1-CONTRADICTION-DOC-VS-CODE` | 1 | 1 | 2.5 | one router per module: every router file registered | backend/modules… |
| 1 | `WP1-CONTRADICTION-FRONTEND-VS-BACKEND` | 1 | 1 | 2.5 | Law 13 (5 modules): no standalone hr module | frontend/web_app/next.c… |
| 1 | `WP1-EVENT-SPINE` | 1 | 1 | 20.0 | 44 of 79 event handlers (44/79) log and return without performing the… |
| 1 | `WP1-EXTRA-MODULE` | 1 | 1 | 2.5 | top-level module `finance` exists |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str,… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 18 float-for-money signal(s); first: `"total_amount": float(order.tot… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_pr… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 73 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converte… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converte… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `"amount": float(converted_total)… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"amount": float(p.amount),` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 36 float-for-money signal(s); first: `amount: Decimal | float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `line_total = float(line.get("qua… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"]… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `subtotal: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 30 float-for-money signal(s); first: `shipping_amount = float(getattr… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total=float(total_amount),` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `min_amount: Optional[float]` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total = round(after_discount + s… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `unit_price = float(item.price or… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `unit_price: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `min_payout_amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `entry["amount"] = float(match.gr… |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| 1 | `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` |
| 1 | `WP1-HTTP-CORS` | 1 | 1 | 1.0 | the security middleware handles OPTIONS by calling call_next() and th… |
| 1 | `WP1-MIGRATION-HEADS` | 1 | 1 | 1.0 | 4 divergent migration heads: 20261002_0001, 20261003_0001, 20261003_0… |
| 1 | `WP1-SSRF` | 1 | 1 | 2.5 | 26 caller-influenced outbound URL call(s) without safe-URL guard; fir… |
| 1 | `WP1-TABLE-DRIFT` | 1 | 1 | 2.5 | migrations reference schemas no ORM model declares: customer(5), comm… |
| 1 | `WP1-UNGATED-ROUTE` | 1 | 1 | 2.5 | 2 endpoint(s) across 2 router(s) have no visible auth/gate dependency… |
| 1 | `WP1-WORKFLOW-RUNTIME` | 1 | 1 | 2.5 | `backend/jobs/reconciliation_cron.py` imports `domains.finance.servic… |
| 1 | `WP1-SETTINGS-CONTRACT` | 12 | 7 | 12.0 | settings.NEWS_API_KEY is read but Settings declares no such field |
| 1 | `WP1-LAW-ARCHITECTURE` | 4 | 1 | 4.0 | Law 1 (Arrows point down) violated: 33 reverse-layer import(s) |
| 1 | `WP1-LAW-SECURITY` | 2 | 1 | 2.0 | Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s) |
| 1 | `WP1-INTERACTION-MODAL` | 1 | 1 | 2.5 | 28 destructive control(s) in 8 modal file(s) with no confirmation step |
| 2 | `WP2-CIRCULAR-IMPORT` | 20 | 6 | 50.0 | circular package dependency: domains.accounts -> domains.audit -> dom… |
| 2 | `WP2-INFRA-IMPORTS-ABOVE` | 15 | 12 | 37.5 | `infra imports above`: imports `domains` |
| 2 | `WP2-TF-MISSING-COUNTRY-CODE` | 9 | 4 | 9.0 | 1x missing country_code in table `notifications`: user-facing table `… |
| 2 | `WP2-MODULE-IMPORTS-INFRASTRUCTURE` | 7 | 7 | 17.5 | `module imports infrastructure`: imports `infrastructure.utils.router… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 6 | 1 | 15.0 | cross-domain import `domains.accounts.models.banking` (domains.govern… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 15.0 | cross-domain import `domains.accounts.models.user` (domains.logistics… |
| 2 | `WP2-LAW-CODE-QUALITY` | 6 | 1 | 6.0 | Law 19 (No float for money) violated: 18 Float column(s); 0 float mon… |
| 2 | `WP2-FORBIDDEN-PACKAGE` | 5 | 2 | 5.0 | forbidden package declared: `prometheus-client`==0.26.0 |
| 2 | `WP2-LAW-DATABASE` | 4 | 1 | 4.0 | Law 45 (No N+1 queries) violated: 304/390 relationship(s) without laz… |
| 2 | `WP2-SUPPLY-CHAIN` | 4 | 1 | 4.0 | no dependency scanning step in CI |
| 2 | `WP2-VERSION-DRIFT` | 4 | 3 | 4.0 | `eslint: ^9` does not satisfy pinned `10` |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 3 | 1 | 7.5 | cross-domain import `domains.accounts.models.user` (domains.orders ->… |
| 2 | `WP2-INTENT-STUB` | 3 | 3 | 3.0 | 1 placeholder response(s) ('not yet wired') in live module |
| 2 | `WP2-MIGRATION-DESTRUCTIVE` | 3 | 3 | 3.0 | upgrade() performs an unguarded destructive op at line 246 with no ex… |
| 2 | `WP2-PROVIDER-RESILIENCE` | 3 | 1 | 7.5 | circuit breaker present in 8/94 provider modules |
| 2 | `WP2-CI-CD` | 2 | 1 | 5.0 | pipeline lacks: secret scanning |
| 2 | `WP2-COLOR-DRIFT` | 2 | 1 | 40.0 | 165 hardcoded hex colour(s) across 33 component file(s) outside the t… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.accoun… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.audit ->… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 2 | 1 | 5.0 | cross-domain import `domains.comms.models.communication` (domains.cat… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.comms ->… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.country -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 5.0 | cross-domain import `domains.customers.models.cross_country_session`… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.core` (domains.customers… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.financ… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 5.0 | cross-domain import `domains.comms.models.suppliers` (domains.finance… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.govern… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 2 | 1 | 5.0 | cross-domain import `domains.audit.services.logs.audit_service` (doma… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.promotion… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 5.0 | cross-domain import `domains.accounts.models.banking` (domains.suppli… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.suppli… |
| 2 | `WP2-EXTRA-DOMAIN` | 2 | 2 | 5.0 | domain package `media` exists |
| 2 | `WP2-INTERACTION-BUTTON` | 2 | 1 | 3.5 | 949 of 1466 button elements have no explicit type; inside a <form> th… |
| 2 | `WP2-LAW-PROVIDER` | 2 | 1 | 2.0 | Law 123 (Single SDK per provider) violated: 3 provider file(s) contai… |
| 2 | `WP2-ROUTER-DB-ACCESS` | 2 | 2 | 5.0 | router touches DB/ORM directly (1 hit(s)) |
| 2 | `WP2-UNGATED-ROUTE` | 2 | 2 | 5.0 | endpoint `list_employees_public` has no visible auth/feature gate |
| 2 | `WP2-AP-TODO-ONLY` | 1 | 1 | 6.0 | TODO-only implementation: 296 occurrence(s); sample backend/domains/a… |
| 2 | `WP2-CHAIN-CHAIN-002` | 1 | 1 | 6.0 | CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1… |
| 2 | `WP2-CHAIN-CHAIN-003` | 1 | 1 | 6.0 | CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0… |
| 2 | `WP2-CHAIN-CHAIN-006` | 1 | 1 | 6.0 | CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps locat… |
| 2 | `WP2-CONTRADICTION-TARGET-VS-CODE` | 1 | 1 | 2.5 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | bac… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | cross-domain import `domains.governance.core.approval_matrix_service`… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.a… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.general_ledger` (domains.… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.audit… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.audit -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.catalog -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.c… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.comms… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.com… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.c… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.catalog.models.upload_job` (domains.comm… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.comms -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.tax_rules` (domains.count… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.coun… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.coupon_usage` (domains… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.customers… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.admin` (domains.financ… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.finance -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.finance -… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.f… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.gover… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.governa… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.gove… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.audit.services.retention_service` (domai… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (do… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.hr ->… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.hr -> d… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.hr -> d… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.hr -> dom… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.country_control` (domains… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.logist… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.logisti… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.customers.models.cross_country_session`… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.log… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | cross-domain import `domains.security.models.fraud` (domains.logistic… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.order… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.governance.models.core` (domains.orders… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.orders… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.orde… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.ord… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (do… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | cross-domain import `domains.finance.services.payments.payment_engine… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.promo… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.promot… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | cross-domain import `domains.orders.customer_coupons_create_service`… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.security… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.suppliers.models.fraud_indicators` (doma… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.secu… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.supplie… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.country.models.countries` (domains.suppl… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.comms.models.communication` (domains.sup… |
| 2 | `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (do… |
| 2 | `WP2-DB-POOL` | 1 | 1 | 1.0 | no pool_size configuration found |
| 2 | `WP2-ENV-RAW` | 1 | 1 | 1.0 | 140 raw os.getenv/environ read(s) bypass typed settings |
| 2 | `WP2-EVENT-SPINE` | 1 | 1 | 2.5 | only 6/125 defined event type(s) referenced by services |
| 2 | `WP2-FINANCE-AUTOMATION` | 1 | 1 | 20.0 | no implementation found for: bad_debt_provision |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `max_commission_amount: Optional[… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `discount_value: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 11 float-for-money signal(s); first: `min_price: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `intent["entities"]["price_range"… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.P… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `total_amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `total_duration_ms: Optional[floa… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 13 float-for-money signal(s); first: `cod_max_amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dic… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"]… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"balance": float(balance),` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.P… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 8 float-for-money signal(s); first: `commission_reserve: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"commission": float(result[1] or… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"price": float(p.price) if p.pri… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"salary": float(employee.salary)… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `"base_salary": float(base_salary… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `return {"total_paid": float(tota… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"salary": float(emp.salary),` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_days": float(l.total_days… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `return {'total_revenue': float(t… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `return float(payout.amount)` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_cost": float(total),` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 31 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_revenue": float(total_rev… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"estimated_distance_km": round(t… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 7 float-for-money signal(s); first: `max_combined_discount_amount: Op… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `charge_amount = float(data.get("… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `"charge_amount": float(charge_am… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 50 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `discount_amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 8 float-for-money signal(s); first: `discount_value: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_to… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_to… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `"max_combined_discount_amount":… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `amount: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `avg_order_value = float(total_re… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 16 float-for-money signal(s); first: `"total_revenue": float(total_re… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `first_revenue = sum(float(o.tota… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `return float(config.supplier_onb… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `"price": float(product.price),` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `coverage = float(fg_pixels / tot… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"total_revenue": float(total_rev… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"total_pending": float(total_pen… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 63 float-for-money signal(s); first: `price: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `net_amount = float(subtotal_deci… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float | None` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `min_price: float | None` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `min_price: float | None` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `total_revenue: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `base_price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"price_min": round(base * 0.75,… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 9 float-for-money signal(s); first: `current_price: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `"support": round(freq / total_or… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 4 float-for-money signal(s); first: `parsed["min_price"] = float(matc… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `"positive": round(sentiment_coun… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `total = float(h * w) if h * w el… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `return float(psutil.virtual_memo… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `white_balance_strength: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 3 float-for-money signal(s); first: `result["total"] = float(match.gr… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-OC` | 1 | 1 | 2.5 | 2 float-for-money signal(s); first: `"amount": float(amt),` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-SH` | 1 | 1 | 2.5 | 5 float-for-money signal(s); first: `key=lambda x: (not x.get("availa… |
| 2 | `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-VO` | 1 | 1 | 2.5 | 1 float-for-money signal(s); first: `result["amount"] = float(amount_… |
| 2 | `WP2-HANDOVER` | 1 | 1 | 6.0 | 10 of 10 handover/takeover function(s) are missing at least one safet… |
| 2 | `WP2-HTTP-CSP` | 1 | 1 | 1.0 | 3 place(s) default a CORS/CSP origin to localhost |
| 2 | `WP2-INTERACTION-FORM` | 1 | 1 | 2.5 | 465 of 743 text input(s) have no label, aria-label or id association |
| 2 | `WP2-INTERACTION-MODAL` | 1 | 1 | 6.0 | 26 of 27 modal/drawer implementations have no focus management |
| 2 | `WP2-INTERACTION-STATE` | 1 | 1 | 2.5 | 138 empty or console-only catch handler(s) |
| 2 | `WP2-LAW-CONFIG` | 1 | 1 | 1.0 | Law 84 (Typed feature flags) violated: 138 raw os.getenv read(s) |
| 2 | `WP2-N-PLUS-1` | 1 | 1 | 1.0 | 304/397 relationship() declarations omit lazy= |
| 2 | `WP2-OFFSET-PAGINATION` | 1 | 1 | 1.0 | 89 OFFSET pagination usage(s) (sample: .offset(safe_offset)) |
| 2 | `WP2-ORPHAN-FEATURE` | 1 | 1 | 1.0 | 224 orphan feature atom(s) defined but never gated (e.g. accounts.add… |
| 2 | `WP2-PII-LOGS` | 1 | 1 | 2.5 | 8 log statement(s) may include PII/secrets (sample: logger.error("Fai… |
| 2 | `WP2-PROVIDER-CONFIG` | 1 | 1 | 1.0 | 13 provider module(s) read secrets via raw os.getenv |
| 2 | `WP2-PROVIDER-HEALTH` | 1 | 1 | 1.0 | 88/93 provider modules lack health_check() |
| 2 | `WP2-PROVIDER-TIMEOUT` | 1 | 1 | 1.0 | 62/93 provider modules declare no timeout |
| 2 | `WP2-QUALITY-ASSURANCE` | 1 | 1 | 20.0 | no implementation found for: product_inspection, proof_of_delivery, s… |
| 2 | `WP2-RAW-GETENV` | 1 | 1 | 2.5 | 130 raw os.getenv/os.environ read(s) in production paths (top: provid… |
| 2 | `WP2-ROOT-DISCIPLINE` | 1 | 1 | 1.0 | 109 temp/debug/health-test file(s) at backend root: _audit_boot_check… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 69: pass-only: except Excepti… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 743: pass-only: except Attrib… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 75: truly-silent: except (Val… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 87: pass-only: except ValueEr… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 7529: truly-silent: except Ex… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 1111: truly-silent: except Ex… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 3407: truly-silent: except HT… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 693: truly-silent: except Exc… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 78: truly-silent: except Exce… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 44: pass-only: except Excepti… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 102: pass-only: except (json.… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 30: pass-only: except ValueEr… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 9 silent except block(s); first at line 1431: truly-silent: except Ex… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 518: truly-silent: except Exc… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 139: truly-silent: except Exc… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except (Ty… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 280: pass-only: except Except… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 203: pass-only: except Except… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 437: truly-silent: except (Ty… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 49: truly-silent: except Exce… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 26: truly-silent: except Exce… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 88: pass-only: except ValueEr… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 128: truly-silent: except Val… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 25: truly-silent: except (jso… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 141: truly-silent: except (Ty… |
| 2 | `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 102: truly-silent: except (ht… |
| 2 | `WP2-TABLE-GOVERNANCE` | 1 | 1 | 2.5 | 0 table(s) lack audit timestamps and 2 lack soft delete |
| 2 | `WP2-TABLE-RELATION` | 1 | 1 | 6.0 | 304 of 390 relationship() calls omit lazy= |
| 2 | `WP2-WORKFLOW-RUNTIME` | 1 | 1 | 1.0 | 20 of 38 Celery task(s) are defined but never registered in a beat sc… |
| 3 | `WP3-FE-TYPE-ESCAPE` | 25 | 25 | 25.0 | 22 type-safety escape(s) (`@ts-ignore` / `as any`) in application sou… |
| 3 | `WP3-LAW-NOT-STATICALLY-VERIFIABLE` | 25 | 1 | 62.5 | Law 315 (Operations) is not verifiable from source: Log aggregation |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 25 | 1 | 25.0 | 1x rel lazy in table `physical_id_cards`: relationship `employee` has… |
| 3 | `WP3-ALLOWLIST` | 20 | 1 | 50.0 | allowlist entry without dated removal plan: `domains.finance.services… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 20 | 1 | 20.0 | 1x timestamp default in table `transaction_ledgers`: `updated_at` use… |
| 3 | `WP3-LAW-GAP-CHECKABLE` | 19 | 1 | 114.0 | 5 law(s) in 'Technology' have no check but ARE decidable from source:… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 18 | 1 | 18.0 | 2x rel lazy in table `ticket_messages`: relationship `ticket` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 17 | 1 | 17.0 | 1x rel lazy in table `country_feature_flags`: relationship `country`… |
| 3 | `WP3-FILE-TOO-LONG` | 16 | 16 | 96.0 | file has 4561 lines (split candidate) |
| 3 | `WP3-JOB-RESILIENCE` | 14 | 14 | 35.0 | celery task module with no DLQ reference |
| 3 | `WP3-ROUTER-BUSINESS-LOGIC` | 11 | 11 | 27.5 | router contains 8 branch statements (business logic signal) |
| 3 | `WP3-LAW-TEST-ISOLATION` | 10 | 2 | 10.0 | test mutates process-global state with no cleanup in scope: os.enviro… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 10 | 1 | 10.0 | 1x rel lazy in table `entity_chat_threads`: relationship `messages` h… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 9 | 1 | 22.5 | 17 function(s) in this file duplicate `backend/domains/logistics/serv… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 9 | 1 | 9.0 | 1x rel lazy in table `categories`: relationship `products` has no laz… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 9 | 1 | 9.0 | 2x rel lazy in table `fraud_events`: relationship `user` has no lazy= |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 9 | 1 | 9.0 | 1x timestamp default in table `country_feature_flags`: `updated_at` u… |
| 3 | `WP3-VERSION-DRIFT` | 9 | 2 | 9.0 | `dompurify: ^3.3.3` does not satisfy pinned `3.4.0` |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 8 | 1 | 20.0 | 4 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-TEST-NO-ASSERT` | 8 | 8 | 20.0 | test file contains no assertions |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 8 | 1 | 8.0 | 3x rel lazy in table `shift_handover_logs`: relationship `user` has n… |
| 3 | `WP3-MIGRATION-DOWNGRADE` | 7 | 7 | 7.0 | empty/missing downgrade() |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 6 | 1 | 6.0 | 1x rel lazy in table `user_sessions`: relationship `user` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 6 | 1 | 6.0 | 5x rel lazy in table `logistics_partners`: relationship `profile` has… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 6.0 | 1x timestamp default in table `logistics_partner_profiles`: `updated_… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` | 6 | 1 | 6.0 | 2x timestamp default in table `supplier_profiles`: `created_at` uses… |
| 3 | `WP3-DUPLICATE-FILE` | 5 | 5 | 12.5 | byte-identical duplicate file(s): backend/domains/finance/exceptions.… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 5 | 1 | 5.0 | 1x rel lazy in table `admin_change_audit_logs`: relationship `admin`… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 4 | 1 | 10.0 | 15 function(s) in this file duplicate `backend/domains/logistics/serv… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 4 | 1 | 4.0 | 4x rel lazy in table `chart_of_categories`: relationship `parent` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 4 | 1 | 4.0 | 1x rel lazy in table `purchase_orders`: relationship `lines` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 4 | 1 | 4.0 | 1x rel lazy in table `supplier_profiles`: relationship `user` has no… |
| 3 | `WP3-TF-SCHEMA-UNKNOWN` | 4 | 1 | 4.0 | 1x schema unknown in table `payment_methods`: schema `payments` is no… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 4.0 | 1x timestamp default in table `announcements`: `updated_at` uses Pyth… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 4.0 | 1x timestamp default in table `email_campaigns`: `updated_at` uses Py… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 4.0 | 2x timestamp default in table `commission_agreements`: `created_at` u… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 4.0 | 1x timestamp default in table `payout_rules`: `created_at` uses Pytho… |
| 3 | `WP3-DESIGN-PRIMITIVES` | 3 | 2 | 11.0 | 673 hand-rolled card/input class strings across 166 files duplicate a… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-FINA` | 3 | 1 | 7.5 | 10 function(s) in this file duplicate `backend/domains/finance/servic… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 3 | 1 | 7.5 | 4 function(s) in this file duplicate `backend/domains/customers/servi… |
| 3 | `WP3-ENV-UNDECLARED` | 3 | 3 | 3.0 | env var `OTEL_DISABLED` read but not declared in .env.example, typed… |
| 3 | `WP3-FE-DEBUG` | 3 | 3 | 3.0 | 3 console/debugger statement(s) left in application source |
| 3 | `WP3-ROUTER-EMPTY` | 3 | 3 | 7.5 | file lives in routers/ but declares zero endpoint decorators |
| 3 | `WP3-RUNBOOKS` | 3 | 3 | 7.5 | no deploy runbook found |
| 3 | `WP3-SUPPLY-CHAIN` | 3 | 3 | 3.0 | workflow declares no `permissions:` block |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 3 | 1 | 3.0 | 1x rel lazy in table `addresses`: relationship `user` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 3 | 1 | 3.0 | 3x rel lazy in table `onboarding_pipelines`: relationship `user` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 3.0 | 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 3.0 | 2x rel lazy in table `commission_groups`: relationship `categories` h… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 3.0 | 3x rel lazy in table `support_tickets`: relationship `replies` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 3.0 | 3x rel lazy in table `incident_war_rooms`: relationship `threads` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 3.0 | 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` ha… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 3 | 1 | 3.0 | 17x rel lazy in table `country_configs`: relationship `communications… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 3 | 1 | 3.0 | 1x rel lazy in table `coupons`: relationship `country` has no lazy= |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 2 | 1 | 5.0 | 4 function(s) in this file duplicate `backend/domains/country/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 2 | 1 | 5.0 | 4 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 2 | 1 | 5.0 | 3 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 2 | 1 | 5.0 | 11 function(s) in this file duplicate `backend/infrastructure/databas… |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 2.0 | 14 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 2.0 | 50 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 2.0 | 13 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-LAW-STRUCTURE` | 2 | 1 | 2.0 | Law 12 (15 domains) violated: extra domain(s): media, payments |
| 3 | `WP3-TF-MISSING-IS-DELETED` | 2 | 1 | 2.0 | 1x missing is_deleted in table `shipment_tracking_projections`: table… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 2 | 1 | 2.0 | 2x rel lazy in table `referrals`: relationship `referrer` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 2 | 1 | 2.0 | 1x rel lazy in table `payout_rules`: relationship `country` has no la… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 2 | 1 | 2.0 | 2x rel lazy in table `document_verifications`: relationship `pipeline… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 2 | 1 | 2.0 | 1x rel lazy in table `permission_categories`: relationship `permissio… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 2 | 1 | 2.0 | 1x timestamp default in table `direct_chat_rooms`: `updated_at` uses… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 2 | 1 | 2.0 | 2x timestamp default in table `country_configs`: `created_at` uses Py… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 2 | 1 | 2.0 | 2x timestamp default in table `referrals`: `created_at` uses Python-s… |
| 3 | `WP3-AP-EMPTY-HANDLER-PASS` | 1 | 1 | 1.0 | Empty handler (pass): 5 occurrence(s); sample `backend/infrastructure… |
| 3 | `WP3-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` | 1 | 1 | 1.0 | Stub function (NotImplementedError): 37 occurrence(s); sample `backen… |
| 3 | `WP3-BASE-IMAGE` | 1 | 1 | 1.0 | dev database image `postgres:18-alpine` (documented: postgres:16-alpi… |
| 3 | `WP3-CACHE-COVERAGE` | 1 | 1 | 2.5 | cache references (157) below list-endpoint count (479) |
| 3 | `WP3-COLOR-DRIFT` | 1 | 1 | 6.0 | 302 inline `style={...}` prop(s) across 76 files; inline colour canno… |
| 3 | `WP3-COUNT-QUERIES` | 1 | 1 | 2.5 | 308 `.count()` calls (expensive on large tables) |
| 3 | `WP3-COVERAGE-ROUTE` | 1 | 1 | 1.0 | 3 spec file(s) navigate to paths that no longer exist in the app rout… |
| 3 | `WP3-DB-POOL` | 1 | 1 | 1.0 | asyncpg statement_cache_size=0 not set |
| 3 | `WP3-DEEP-NESTING` | 1 | 1 | 2.5 | 91 function(s) exceed 4 nesting levels (max seen 17) |
| 3 | `WP3-DOCS` | 1 | 1 | 2.5 | SETUP.md missing |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-AUDI` | 1 | 1 | 2.5 | 3 function(s) in this file duplicate `backend/domains/audit/services/… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/comms/services/… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/country/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/accounts/servic… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 5 function(s) in this file duplicate `backend/domains/comms/services/… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 6 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 11 function(s) in this file duplicate `backend/domains/analytics/serv… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/governance/serv… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/audit/services/… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/country/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/country/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 function(s) in this file duplicate `backend/domains/logistics/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/serializ… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 function(s) in this file duplicate `backend/domains/customers/servi… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 6 function(s) in this file duplicate `backend/domains/orders/services… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/customer… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/services… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) in this file duplicate `backend/domains/orders/services… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/promotions/serv… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 6 function(s) in this file duplicate `backend/domains/promotions/serv… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 4 function(s) in this file duplicate `backend/domains/governance/serv… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 11 function(s) in this file duplicate `backend/domains/orders/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/services… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/accounts/servic… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/domains/catalog/service… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/infrastructure/messagin… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-MIDDLEWARE-R` | 1 | 1 | 2.5 | 6 function(s) in this file duplicate `backend/middleware/middleware_h… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-MODULES-SUPP` | 1 | 1 | 2.5 | 1 function(s) in this file duplicate `backend/modules/logistics/route… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 3 function(s) in this file duplicate `backend/jobs/mcp_marketplace_se… |
| 3 | `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AS` | 1 | 1 | 2.5 | 8 function(s) in this file duplicate `backend/jobs/async_workers.py`… |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/accounting` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/analytics` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/audit-logs` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/bank-accounts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/banners` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/barcode` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/catalog` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/categories` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/chat` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/coc` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/command-center/alerts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/command-center/fraud` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/command-center/headlines/create` has no `error.tsx` boun… |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/command-center/headlines` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/command-center` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/commission` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/comms-test` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/communication` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/countries/[code]/staff` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/countries` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/coupons` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/dashboard` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/disputes` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/email` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/employees` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/ess` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/exports` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/finance` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/flash-sales` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/hr` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/inventory-alerts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/invoices` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/logistics-partners` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/logistics` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/moderation` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/orders` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/organization` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/payments` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/payouts/background-jobs` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/payouts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/payroll` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/permissions` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/product-verification` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/products` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/promotions` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/resolution` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/returns` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/staff` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/supplier-documents` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/suppliers` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/tickets/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/tickets` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/treasury` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/users` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `admin/video` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `archive` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `auth/callback` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `brand` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `chatbot` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `contact` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `customer/(auth)/login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/(auth)/login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/attendance` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/dashboard` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/documents` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/leaves` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/notifications` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/payroll` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/performance` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/profile` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/schedule` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/training` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/workspace` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `employee/workspace/tasks` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/(auth)/login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/(auth)/register` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/analytics` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/dashboard` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/payouts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/profile` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/routes` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/scan` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partner/shipments` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partners/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logistics-partners` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `logo-animation` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `meet/[room]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `newsletter/preferences` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `newsletter/unsubscribe` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `offers` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `orders/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `products/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `products/category` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `profile/referrals` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `r/[code]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `register` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `reset-password` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `returns/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier-storefront/[slug]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/(auth)/login` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/(auth)/register` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/analytics` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/batch-upload` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/bulk` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/commission` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/credibility` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/dashboard` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/disputes` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/documents` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/guide` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/inventory` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/invoices` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/labels/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/labels` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/list-product` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/logistics` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/notification-preferences` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/orders/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/orders` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/payouts` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/products/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/products/add` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/products` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/profile` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/regions` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/reports` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/returns` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/support` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/terms` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/upload/bg-compare` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/upload` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `supplier/videos/upload` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `suppliers/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `suppliers` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `tickets/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `tracking/[id]` has no `error.tsx` boundary |
| 3 | `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | route `verify-email` has no `error.tsx` boundary |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 12 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 12 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 4 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 16 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 9 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 30 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 34 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 31 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 6 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 24 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 25 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 4 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 14 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 36 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 15 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 14 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 18 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 15 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 2 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 7 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 6 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 66 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 7 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 30 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 4 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 2 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 5 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 28 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 raw Tailwind palette class(es) bypass the semantic token scale |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 7 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 9 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 6 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 5 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 9 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| 3 | `WP3-FEATURE-GATE` | 1 | 1 | 2.5 | 146 declared feature(s) are never referenced by any gate |
| 3 | `WP3-HTTP-CSP` | 1 | 1 | 1.0 | the CSP uses the deprecated `report-uri` directive |
| 3 | `WP3-HTTP-HEADERS` | 1 | 1 | 1.0 | the security middleware emits X-XSS-Protection (1 site(s)) |
| 3 | `WP3-INTERACTION-BUTTON` | 1 | 1 | 1.0 | 2 icon-only button(s) expose no accessible name |
| 3 | `WP3-INTERACTION-MODAL` | 1 | 1 | 1.0 | 23 of 27 modal implementations do not close on Escape |
| 3 | `WP3-LAW-DOCS` | 1 | 1 | 1.0 | Law 248 (Runbooks) violated: 0 doc file(s) under docs/ |
| 3 | `WP3-LAW-FRONTEND-CONTRACT` | 1 | 1 | 1.0 | tsconfig does not enable strict mode (strict=false), so the type chec… |
| 3 | `WP3-LAW-GIT-HYGIENE` | 1 | 1 | 1.0 | no CODEOWNERS or branch-protection document, so required review is no… |
| 3 | `WP3-LAW-MIGRATION` | 1 | 1 | 1.0 | Law 27 (Delete temp scripts) violated: 105 temp/debug file(s) at back… |
| 3 | `WP3-LAW-PERFORMANCE` | 1 | 1 | 1.0 | Law 222 (Keyset pagination) violated: 88 OFFSET usage(s) |
| 3 | `WP3-LAW-UNATTRIBUTED` | 1 | 1 | 2.5 | 133 law(s) are enforced by a check but no finding cites them, so no r… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-CONFIG-PY` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_validate_required_secrets_i… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 10 function(s) >50 lines; longest sample `authenticate_password` = 59… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `list_products` = 119 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 5… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `send_message` = 58 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 7… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_country_public_payload` = 8… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_order_payment_status` =… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 1… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 li… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 9 function(s) >50 lines; longest sample `get_payment_methods_status`… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 6… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 11 function(s) >50 lines; longest sample `generate_supplier_payout_ba… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_t… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 li… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score`… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 l… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lin… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 li… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt`… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `bulk_update_order_status_adm… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_return_request` = 67… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdo… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 li… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SECU` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 li… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 1… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 141 l… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lin… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `persist_supplier_product` =… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `process_product_image` = 52… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `persist_supplier_product` =… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_sh… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_load_environment_email_conf… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 l… |
| 3 | `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-MAIN-PY` | 1 | 1 | 2.5 | 2 function(s) >50 lines; longest sample `health_deps` = 52 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_order` = 79 lines |
| 3 | `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 2.5 | 3 function(s) >50 lines; longest sample `create_payment_page` = 89 li… |
| 3 | `WP3-ORPHAN-JOB` | 1 | 1 | 2.5 | 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_r… |
| 3 | `WP3-ORPHAN-PROVIDER` | 1 | 1 | 1.0 | 87 provider module(s) never referenced by any domain file: __header__… |
| 3 | `WP3-PACKAGE-MANAGER` | 1 | 1 | 1.0 | non-canonical lockfile `package-lock.json` present |
| 3 | `WP3-PRINT-LOGGING` | 1 | 1 | 2.5 | 6 `print()` call(s) in production paths (sample backend/domains/_mixi… |
| 3 | `WP3-PROVIDER-EXTRA` | 1 | 1 | 1.0 | provider package(s) outside the canonical tree: _helpers.py, analytic… |
| 3 | `WP3-PUBLIC-BY-DESIGN` | 1 | 1 | 2.5 | 9 endpoint(s) are unauthenticated by design (1 authentication entry p… |
| 3 | `WP3-READ-REPLICA` | 1 | 1 | 1.0 | read-replica engine exists but `get_read_db` is never used by domains |
| 3 | `WP3-RLS` | 1 | 1 | 1.0 | RLS script does not FORCE row level security |
| 3 | `WP3-SEARCH-INDEX` | 1 | 1 | 1.0 | 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike(… |
| 3 | `WP3-SELECT-STAR` | 1 | 1 | 1.0 | 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM a… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-CONFIG-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 937: truly-silent: except Att… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 2.5 | 6 silent except block(s); first at line 3080: pass-only: except Excep… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 54: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 126: truly-silent: except (Ty… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 219: pass-only: except (TypeE… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 454: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 281: truly-silent: except Web… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 166: truly-silent: except Val… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 283: truly-silent: except Web… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 84: pass-only: except WebSock… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 218: truly-silent: except (js… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 191: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 70: pass-only: except (json.J… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 480: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 276: truly-silent: except Web… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 232: pass-only: except (TypeE… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 444: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 43: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 97: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 120: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 85: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 126: truly-silent: except (js… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 6 silent except block(s); first at line 1439: pass-only: except Excep… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 28: truly-silent: except (Val… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 355: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 168: pass-only: except (Value… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 73: truly-silent: except (Val… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 508: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 55: pass-only: except (json.J… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 284: truly-silent: except (Va… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 5 silent except block(s); first at line 211: pass-only: except Attrib… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 67: truly-silent: except (Typ… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 362: truly-silent: except (Ty… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 527: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 188: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 174: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 1104: truly-silent: except (T… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 18: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 599: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except Runtime… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 92: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 323: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 22: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 132: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 57: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 31: pass-only: except (ValueE… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 110: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 7 silent except block(s); first at line 67: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except Runtime… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-JOBS-VIDEO-T` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 104: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 351: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MAIN-PY` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 199: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 245: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 424: truly-silent: except Val… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 242: truly-silent: except Uni… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MODULES-ADMI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 203: pass-only: except WebSoc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-MODULES-CUST` | 1 | 1 | 2.5 | 3 silent except block(s); first at line 160: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 78: truly-silent: except urll… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 231: pass-only: except OSErro… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 288: truly-silent: except jso… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 148: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 127: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 39: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 245: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 158: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 312: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 119: pass-only: except Except… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 288: truly-silent: except Exc… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 30: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 4 silent except block(s); first at line 95: truly-silent: except Exce… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 513: truly-silent: except (Va… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 24: pass-only: except Excepti… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 44: truly-silent: except Valu… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` | 1 | 1 | 2.5 | 2 silent except block(s); first at line 99: truly-silent: except Unic… |
| 3 | `WP3-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` | 1 | 1 | 2.5 | 1 silent except block(s); first at line 33: truly-silent: except Exce… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 1.0 | 1x rel lazy in table `otp_codes`: relationship `user` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 1x rel lazy in table `meeting_recordings`: relationship `starter` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 3x rel lazy in table `messages`: relationship `country` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_basics`: relationship `country` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_economics`: relationship `country` has… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_legals`: relationship `country` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 1x rel lazy in table `country_taxes`: relationship `country` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 1.0 | 2x rel lazy in table `cross_country_customer_sessions`: relationship… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 1.0 | 1x rel lazy in table `legal_contract_templates`: relationship `countr… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 1x rel lazy in table `shipping_rules`: relationship `country` has no… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1.0 | 1x rel lazy in table `order_items`: relationship `order` has no lazy= |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 1x rel lazy in table `coupon_usages`: relationship `country` has no l… |
| 3 | `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 1x rel lazy in table `promotion_engine_configs`: relationship `countr… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` | 1 | 1 | 1.0 | 2x timestamp default in table `upload_jobs`: `created_at` uses Python… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 1x timestamp default in table `messages`: `created_at` uses Python-si… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 1.0 | 2x timestamp default in table `news_articles`: `created_at` uses Pyth… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_basics`: `created_at` uses Pyt… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_economics`: `created_at` uses… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_legals`: `created_at` uses Pyt… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 1.0 | 2x timestamp default in table `country_taxes`: `created_at` uses Pyth… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 2x timestamp default in table `city_distance_matrices`: `created_at`… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 1.0 | 1x timestamp default in table `shipping_rules`: `created_at` uses Pyt… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 2x timestamp default in table `coupon_usages`: `created_at` uses Pyth… |
| 3 | `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 1.0 | 2x timestamp default in table `promotion_engine_configs`: `created_at… |
| 5 | `WP5-RECOMMENDATIONS-REC-AUTOMATION` | 8 | 7 | 13.0 | Automate the human-in-the-loop queue and the serial write loops |
| 5 | `WP5-RECOMMENDATIONS-REC-DATA` | 4 | 5 | 27.5 | Model and seed the full 5-tier product taxonomy |
| 5 | `WP5-RECOMMENDATIONS-REC-WORKFLOW` | 2 | 2 | 26.0 | Turn the event spine into real work, or delete it |
| 5 | `WP5-RECOMMENDATIONS-REC-DESIGN` | 1 | 1 | 6.0 | Adopt the existing UI primitives and delete duplicated markup |
| 5 | `WP5-RECOMMENDATIONS-REC-FINANCE` | 1 | 1 | 20.0 | Automate the manual finance processes end to end |
| 5 | `WP5-RECOMMENDATIONS-REC-FRONTEND` | 1 | 1 | 2.5 | Standardise interaction state handling across all screens |
| 5 | `WP5-RECOMMENDATIONS-REC-OPS` | 1 | 1 | 1.0 | Add a dispatch smoke test for every scheduled task |
| 5 | `WP5-RECOMMENDATIONS-REC-QA` | 1 | 1 | 20.0 | Introduce a quality-gate chain across fulfilment |

## Wave plan

| Wave | Title | Steps | Blockers | Gates | Verifications | Est. hours |
|------|-------|-------|----------|-------|---------------|------------|
| 1 | Fix the hard blockers that prevent correct behaviour | 91 | 72 | 0 | 0 | 205.0 |
| 2 | Close correctness and security defects | 345 | 0 | 0 | 0 | 877.5 |
| 3 | Close coverage, quality and performance defects | 878 | 0 | 0 | 0 | 1523.5 |
| 5 | Improvement track — recommendations (not release-gating) | 19 | 0 | 0 | 0 | 116.0 |

---
## Wave 1 · Fix the hard blockers that prevent correct behaviour

#### Work packages in wave 1 (55)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP1-IDEMPOTENCY` | 10 | 4 | 10 | 0 | 25.0 | idempotency_key: Optional[str] = None, |
| `WP1-FE-DANGEROUS` | 6 | 4 | 6 | 0 | 6.0 | `dangerouslySetInnerHTML={{` executes or injects untrusted code in the browser bundle |
| `WP1-STUB-SUBSCRIBER` | 4 | 4 | 4 | 0 | 10.0 | stub subscriber module: 3 handlers, 3 `# Future:` markers |
| `WP1-PAYMENT-WEBHOOK` | 3 | 3 | 3 | 0 | 3.0 | payment adapter references webhooks but shows no signature verification |
| `WP1-CONTRADICTION-TARGET-VS-CODE` | 2 | 2 | 2 | 0 | 5.0 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists |
| `WP1-RLS` | 2 | 2 | 2 | 0 | 5.0 | canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed |
| `WP1-AP-TODO-ONLY-IMPLEMENTATION` | 1 | 1 | 1 | 0 | 2.5 | TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1` |
| `WP1-AP-UNIMPLEMENTED-PLACEHOLDER` | 1 | 1 | 1 | 0 | 2.5 | Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service… |
| `WP1-CHAIN-CHAIN-005` | 1 | 1 | 1 | 0 | 6.0 | CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes |
| `WP1-CONTRADICTION-DOC-VS-CODE` | 1 | 1 | 1 | 0 | 2.5 | one router per module: every router file registered | backend/modules/employee/routers: hr.py file and hr/ package coex… |
| `WP1-CONTRADICTION-FRONTEND-VS-BACKEND` | 1 | 1 | 1 | 0 | 2.5 | Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists |
| `WP1-EVENT-SPINE` | 1 | 1 | 1 | 0 | 20.0 | 44 of 79 event handlers (44/79) log and return without performing the write they imply |
| `WP1-EXTRA-MODULE` | 1 | 1 | 1 | 0 | 2.5 | top-level module `finance` exists |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 4 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 73 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `"display_amount": float(converted_total),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 7 float-for-money signal(s); first: `"amount": float(converted_total),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `"amount": float(p.amount),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 36 float-for-money signal(s); first: `amount: Decimal | float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price",… |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` | 1 | 1 | 1 | 0 | 2.5 | 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 7 float-for-money signal(s); first: `subtotal: float` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 30 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `total=float(total_amount),` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `min_amount: Optional[float]` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `total = round(after_discount + shipping + vat, 2)` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))` |
| `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 5 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 1 | 0 | 2.5 | 6 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 1 | 0 | 2.5 | 5 float-for-money signal(s); first: `unit_price: float` |
| `WP1-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `min_payout_amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 1 | 0 | 2.5 | 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` | 1 | 1 | 1 | 0 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: Optional[float]` |
| `WP1-HTTP-CORS` | 1 | 1 | 1 | 0 | 1.0 | the security middleware handles OPTIONS by calling call_next() and then decorating the result, so the router has alread… |
| `WP1-MIGRATION-HEADS` | 1 | 1 | 1 | 0 | 1.0 | 4 divergent migration heads: 20261002_0001, 20261003_0001, 20261003_0009, 20261004_0021_fix_products_fk_and_defaults |
| `WP1-SSRF` | 1 | 1 | 1 | 0 | 2.5 | 26 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authoriza… |
| `WP1-TABLE-DRIFT` | 1 | 1 | 1 | 0 | 2.5 | migrations reference schemas no ORM model declares: customer(5), commerce(1) |
| `WP1-UNGATED-ROUTE` | 1 | 1 | 1 | 0 | 2.5 | 2 endpoint(s) across 2 router(s) have no visible auth/gate dependency (sample: backend/modules/employee/routers/hr.py:6… |
| `WP1-WORKFLOW-RUNTIME` | 1 | 1 | 1 | 0 | 2.5 | `backend/jobs/reconciliation_cron.py` imports `domains.finance.services.treasury.cash_management_service.run_scheduled_… |
| `WP1-SETTINGS-CONTRACT` | 12 | 7 | 0 | 0 | 12.0 | settings.NEWS_API_KEY is read but Settings declares no such field |
| `WP1-LAW-ARCHITECTURE` | 4 | 1 | 0 | 0 | 4.0 | Law 1 (Arrows point down) violated: 33 reverse-layer import(s) |
| `WP1-LAW-SECURITY` | 2 | 1 | 0 | 0 | 2.0 | Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s) |
| `WP1-INTERACTION-MODAL` | 1 | 1 | 0 | 0 | 2.5 | 28 destructive control(s) in 8 modal file(s) with no confirmation step |

##### `WP1-IDEMPOTENCY` — idempotency_key: Optional[str] = None,

- **cluster:** `CLUSTER-idempotency` · **steps:** 10 (0 closed) · **files:** 4 · **est.:** 25.0h
- **files:** `backend/domains/customers/services/coins/zozi_coins_service.py`, `backend/domains/finance/services/payments/payment_engine.py`, `backend/domains/promotions/services/coupons/coupon_service.py`, `backend/domains/security/services/detection/public_security_detection_service.py`

[ ] `LOGIC-297` — idempotency_key: Optional[str] = None,
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '171p' backend/domains/customers/services/coins/zozi_coins_service.py`
[ ] `LOGIC-298` — idempotency_key: Optional unique key for deduplication.
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '184p' backend/domains/customers/services/coins/zozi_coins_service.py`
[ ] `LOGIC-299` — idempotency_key: Optional[str] = None
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '367p' backend/domains/finance/services/payments/payment_engine.py`
[ ] `LOGIC-300` — idempotency_key: Optional[str] = None,
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '538p' backend/domains/promotions/services/coupons/coupon_service.py`
[ ] `LOGIC-301` — idempotency_key: Optional unique key for deduplication (24h TTL).
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '554p' backend/domains/promotions/services/coupons/coupon_service.py`
[ ] `LOGIC-302` — def _idempotency_key(idempotency_key: Optional[str] = Header(None, alias=_IDEMPOTENCY_KEY_HEADER)) -> Optional[str]:
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '25p' backend/domains/security/services/detection/public_security_detection_service.py`
[ ] `LOGIC-303` — def remove_from_blacklist(entry_id: int, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key:…
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '83p' backend/domains/security/services/detection/public_security_detection_service.py`
[ ] `LOGIC-304` — def create_rule(payload: FraudRuleCreate, _: User=Depends(require_admin), db: Session=Depends(get_db), idempotency_key:…
    - do: Make the idempotency key required and enforce uniqueness
    - verify: `sed -n '104p' backend/domains/security/services/detection/public_security_detection_service.py`
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-idempotency`)

##### `WP1-FE-DANGEROUS` — `dangerouslySetInnerHTML={{` executes or injects untrusted code in the browser bundle

- **cluster:** `CLUSTER-fe-dangerous` · **steps:** 6 (0 closed) · **files:** 4 · **est.:** 6.0h
- **files:** `frontend/web_app/src/app/layout.tsx`, `frontend/web_app/src/app/products/[id]/page.tsx`, `frontend/web_app/src/components/admin/CreateCampaignForm.tsx`, `frontend/web_app/src/components/admin/EmailTemplateManager.tsx`

[ ] `SEC-006` — `dangerouslySetInnerHTML={{` executes or injects untrusted code in the browser bundle
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/app/layout.tsx`
[ ] `SEC-007` — `dangerouslySetInnerHTML={{` executes or injects untrusted code in the browser bundle
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/app/layout.tsx`
[ ] `SEC-008` — `dangerouslySetInnerHTML={{` executes or injects untrusted code in the browser bundle
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/app/products/[id]/page.tsx`
[ ] `SEC-009` — `<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formData.html_content) }} />` executes or injects untrusted…
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/components/admin/CreateCampaignForm.tsx`
[ ] `SEC-010` — `<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(template.content) }} />` executes or injects untrusted code…
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/components/admin/EmailTemplateManager.tsx`
[ ] `SEC-011` — `<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formData.content) }} />` executes or injects untrusted code…
    - do: sanitise the value before rendering, or remove the eval
    - verify: `grep -n 'dangerouslySetInnerHTML\|eval(' frontend/web_app/src/components/admin/EmailTemplateManager.tsx`

##### `WP1-STUB-SUBSCRIBER` — stub subscriber module: 3 handlers, 3 `# Future:` markers

- **cluster:** `CLUSTER-stub-subscriber` · **steps:** 4 (0 closed) · **files:** 4 · **est.:** 10.0h
- **files:** `backend/domains/finance/subscribers.py`, `backend/domains/logistics/subscribers.py`, `backend/domains/orders/subscribers.py`, `backend/domains/payments/subscribers.py`

[ ] `WIRE-005` — stub subscriber module: 3 handlers, 3 `# Future:` markers
    - do: Implement the handlers or remove the registrations
[ ] `WIRE-006` — stub subscriber module: 5 handlers, 5 `# Future:` markers
    - do: Implement the handlers or remove the registrations
[ ] `WIRE-007` — stub subscriber module: 5 handlers, 5 `# Future:` markers
    - do: Implement the handlers or remove the registrations
[ ] `WIRE-008` — stub subscriber module: 4 handlers, 4 `# Future:` markers
    - do: Implement the handlers or remove the registrations

##### `WP1-PAYMENT-WEBHOOK` — payment adapter references webhooks but shows no signature verification

- **cluster:** `CLUSTER-payment-webhook` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `backend/providers/payments/config.py`, `backend/providers/payments/registry.py`, `backend/providers/payments/webhook_models.py`

[ ] `PROV-001` — payment adapter references webhooks but shows no signature verification
    - do: Verify the gateway signature with the stored secret
[ ] `PROV-002` — payment adapter references webhooks but shows no signature verification
    - do: Verify the gateway signature with the stored secret
[ ] `PROV-003` — payment adapter references webhooks but shows no signature verification
    - do: Verify the gateway signature with the stored secret

##### `WP1-CONTRADICTION-TARGET-VS-CODE` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists

- **cluster:** `CLUSTER-contradiction-target_vs_code` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/modules/finance/`, `backend/domains/payments/`

[ ] `CONTRAD-001` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 13): fixed 5 modules | backend/modules/finance/: a 6th module directory exists
    - do: Decide which source is authoritative and align the other; user decision required
[ ] `CONTRAD-002` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/payments/: domain package `payments`…
    - do: Decide which source is authoritative and align the other; user decision required

##### `WP1-RLS` — canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed

- **cluster:** `CLUSTER-rls` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/infrastructure/database/rls_interceptor.py`, `backend/middleware/country_context.py`

[ ] `WIRE-002` — canonical `set_rls_context()` sets ContextVars only; no `SET LOCAL` executed
    - do: Execute SET LOCAL in the active transaction (never session-level SET)
    - verify: `grep -n 'set_rls_context' -A30 backend/infrastructure/database/rls_interceptor.py`
[ ] `WIRE-003` — RLS mismatch: policies read `app.current_country_code` while middleware sets `app.country_scope`
    - do: Align the variable name (and keep SET LOCAL, not SET)
    - verify: `grep -rn 'current_setting' backend/infrastructure/database/sql`

##### `WP1-AP-TODO-ONLY-IMPLEMENTATION` — TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1`

- **cluster:** `CLUSTER-ap-todo-only-implementation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/admin/admin_service.py`

[ ] `AP-003` — TODO-only implementation: 151 occurrence(s); sample `backend/domains/governance/services/admin/admin_service.py:1`
    - do: Replace TODO scaffolding with real implementations

##### `WP1-AP-UNIMPLEMENTED-PLACEHOLDER` — Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service.py:21`

- **cluster:** `CLUSTER-ap-unimplemented-placeholder` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/identity/identity_admin_service.py`

[ ] `AP-002` — Unimplemented placeholder: 257 occurrence(s); sample `backend/domains/accounts/services/identity/identity_admin_service…
    - do: Implement or remove the placeholder endpoint

##### `WP1-CHAIN-CHAIN-005` — CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-005` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/`

[ ] `BLOCK-003` — CHAIN-005 (Admin ledger posting and reconciliation) is PARTIAL: 2/2 steps located; events 0/1; tests=yes
    - do: Implement the missing steps/events and add a chain integration test

##### `WP1-CONTRADICTION-DOC-VS-CODE` — one router per module: every router file registered | backend/modules/employee/routers: hr.py file and hr/ package coexist

- **cluster:** `CLUSTER-contradiction-doc_vs_code` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers`

[ ] `CONTRAD-034` — one router per module: every router file registered | backend/modules/employee/routers: hr.py file and hr/ package coex…
    - do: Align backend/modules/employee/routers with one router per module

##### `WP1-CONTRADICTION-FRONTEND-VS-BACKEND` — Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists

- **cluster:** `CLUSTER-contradiction-frontend_vs_backend` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/next.config.ts`

[ ] `CONTRAD-029` — Law 13 (5 modules): no standalone hr module | frontend/web_app/next.config.ts: /hr/* rewrite exists
    - do: Decide which source is authoritative and align the other; user decision required

##### `WP1-EVENT-SPINE` — 44 of 79 event handlers (44/79) log and return without performing the write they imply

- **cluster:** `CLUSTER-event-spine` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains`

[ ] `WF-stub-subscribers` — 44 of 79 event handlers (44/79) log and return without performing the write they imply
    - do: either implement each handler or stop publishing the event; a handler marked `# Future:` should raise in non-dev so it cannot be mistaken for working code
    - verify: `grep -rn '# Future:' backend/domains | wc -l`

##### `WP1-EXTRA-MODULE` — top-level module `finance` exists

- **cluster:** `CLUSTER-extra-module` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/finance`

[ ] `ARCH-001` — top-level module `finance` exists
    - do: Move finance routers under a canonical module or delete the package
    - verify: `ls backend/modules`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/tax/country_tax_service.py`

[ ] `LOGIC-117` — 1 float-for-money signal(s); first: `CATEGORY_TAX_PROFILES: dict[str, dict[str, float | None]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/tax/country_tax_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/schemas/finance_schemas.py`

[ ] `LOGIC-122` — 4 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/schemas/finance_schemas.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `LOGIC-123` — 18 float-for-money signal(s); first: `"total_amount": float(order.total or 0),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/country/supplier_finance_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-124` — 1 float-for-money signal(s); first: `"unit_cost_fx": float(pl.unit_price),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/data_import_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_service.py`

[ ] `LOGIC-125` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/finance_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/accounting_controller.py`

[ ] `LOGIC-126` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/ledger/accounting_controller.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 73 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `LOGIC-127` — 73 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/ledger/general_ledger.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_paypal.py`

[ ] `LOGIC-128` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_paypal.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_stripe.py`

[ ] `LOGIC-129` — 1 float-for-money signal(s); first: `"display_amount": float(converted_total),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_stripe.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 7 float-for-money signal(s); first: `"amount": float(converted_total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-130` — 7 float-for-money signal(s); first: `"amount": float(converted_total),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/gateway_tap.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 3 float-for-money signal(s); first: `"amount": float(p.amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-131` — 3 float-for-money signal(s); first: `"amount": float(p.amount),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/payment_engine.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-132` — 5 float-for-money signal(s); first: `"gateway_amount": float(gateway_amount),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payments/payment_orchestrator.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 36 float-for-money signal(s); first: `amount: Decimal | float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payouts/payout_batch_service.py`

[ ] `LOGIC-133` — 36 float-for-money signal(s); first: `amount: Decimal | float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/payouts/payout_batch_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/trading_service.py`

[ ] `LOGIC-134` — 4 float-for-money signal(s); first: `line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price",…
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/trading_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-FINA` — 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/treasury/cash_management_service.py`

[ ] `LOGIC-135` — 4 float-for-money signal(s); first: `shipping_amount = float(getattr(allocation, "shipping_amount", 0) or 0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/finance/services/treasury/cash_management_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/cart_service__orders.py`

[ ] `LOGIC-163` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/cart/cart_service__orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 7 float-for-money signal(s); first: `subtotal: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/service.py`

[ ] `LOGIC-164` — 7 float-for-money signal(s); first: `subtotal: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/cart/service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 30 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-165` — 30 float-for-money signal(s); first: `shipping_amount = float(getattr(order, "shipping_amount", 0) or 0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/core/logistics.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 3 float-for-money signal(s); first: `total=float(total_amount),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-166` — 3 float-for-money signal(s); first: `total=float(total_amount),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/core/order_engine.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 3 float-for-money signal(s); first: `min_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `LOGIC-167` — 3 float-for-money signal(s); first: `min_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/orders_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-ORDE` — 1 float-for-money signal(s); first: `total = round(after_discount + shipping + vat, 2)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `LOGIC-168` — 1 float-for-money signal(s); first: `total = round(after_discount + shipping + vat, 2)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/orders/services/tracking/service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders.py`

[ ] `LOGIC-185` — 3 float-for-money signal(s); first: `unit_price = float(item.price or 0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/orders/supplier_orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-186` — 6 float-for-money signal(s); first: `subtotal = float(sum((item.price or 0) * item.quantity for item in items))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/orders/supplier_orders_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 5 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/profile/supplier_payouts_service.py`

[ ] `LOGIC-191` — 5 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/profile/supplier_payouts_service.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-CUST` — 2 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/orders.py`

[ ] `LOGIC-202` — 2 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 6 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/finance.py`

[ ] `LOGIC-207` — 6 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/finance.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 5 float-for-money signal(s); first: `unit_price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/orders.py`

[ ] `LOGIC-210` — 5 float-for-money signal(s); first: `unit_price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/orders.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 2 float-for-money signal(s); first: `min_payout_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/finance.py`

[ ] `LOGIC-215` — 2 float-for-money signal(s); first: `min_payout_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/finance.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/finance_ai.py`

[ ] `LOGIC-219` — 1 float-for-money signal(s); first: `entry["amount"] = float(match.group(1).replace(",", ""))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/finance_ai.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/base.py`

[ ] `LOGIC-229` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/base.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/base_models.py`

[ ] `LOGIC-230` — 2 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/base_models.py | head -20`

##### `WP1-FLOAT-MONEY-BACKEND-PROVIDERS-PA` — 2 float-for-money signal(s); first: `gross_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/webhook_models.py`

[ ] `LOGIC-231` — 2 float-for-money signal(s); first: `gross_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/payments/webhook_models.py | head -20`

##### `WP1-HTTP-CORS` — the security middleware handles OPTIONS by calling call_next() and then decorating the result, so the router has already answered the prefli

- **cluster:** `CLUSTER-http-cors` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `SEC-cors-preflight-static` — the security middleware handles OPTIONS by calling call_next() and then decorating the result, so the router has alread…
    - do: return a Response(status_code=204, headers=...) for OPTIONS without calling call_next, or delete the hand-rolled headers and mount Starlette's CORSMiddleware at app level
    - verify: `curl -i -X OPTIONS http://127.0.0.1:8000/api/v1/auth/login -H 'Origin: http://localhost:3000' -H 'Access-Control-Request-Method: POST'`

##### `WP1-MIGRATION-HEADS` — 4 divergent migration heads: 20261002_0001, 20261003_0001, 20261003_0009, 20261004_0021_fix_products_fk_and_defaults

- **cluster:** `CLUSTER-migration-heads` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/alembic/versions/`

[ ] `MIG-001` — 4 divergent migration heads: 20261002_0001, 20261003_0001, 20261003_0009, 20261004_0021_fix_products_fk_and_defaults
    - do: Merge the branches into a single linear history
    - verify: `cd backend && alembic -c alembic/alembic.ini heads`

##### `WP1-SSRF` — 26 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authorization": f"Bearer {secr

- **cluster:** `CLUSTER-ssrf` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `SEC-005` — 26 caller-influenced outbound URL call(s) without safe-URL guard; first: `response = httpx.get(url, headers={"Authoriza…
    - do: Wrap calls in require_safe_url()/allowlist validation

##### `WP1-TABLE-DRIFT` — migrations reference schemas no ORM model declares: customer(5), commerce(1)

- **cluster:** `CLUSTER-table-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/alembic/versions`

[ ] `DB-schema-drift` — migrations reference schemas no ORM model declares: customer(5), commerce(1)
    - do: rename the schema references in the affected migrations to the ORM schema, and add a test that every schema literal in a migration exists in Base.metadata
    - verify: `pytest backend/tests/architecture -k schema`

##### `WP1-UNGATED-ROUTE` — 2 endpoint(s) across 2 router(s) have no visible auth/gate dependency (sample: backend/modules/employee/routers/hr.py:682 list_employees_pub

- **cluster:** `CLUSTER-ungated-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr.py`

[ ] `WIRE-009` — 2 endpoint(s) across 2 router(s) have no visible auth/gate dependency (sample: backend/modules/employee/routers/hr.py:6…
    - do: Add the auth dependency or move the route to public_routers
    - verify: `grep -n 'def list_employees_public' backend/modules/employee/routers/hr.py`

##### `WP1-WORKFLOW-RUNTIME` — `backend/jobs/reconciliation_cron.py` imports `domains.finance.services.treasury.cash_management_service.run_scheduled_reconciliation_cycle`

- **cluster:** `CLUSTER-workflow-runtime` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/jobs/reconciliation_cron.py`

[ ] `WF-dangling-import` — `backend/jobs/reconciliation_cron.py` imports `domains.finance.services.treasury.cash_management_service.run_scheduled_…
    - do: implement `run_scheduled_reconciliation_cycle` in domains.finance.services.treasury.cash_management_service, or remove the import and the task
    - verify: `cd backend && python -c 'import domains.finance.services.treasury.cash_management_service; print()'`

##### `WP1-SETTINGS-CONTRACT` — settings.NEWS_API_KEY is read but Settings declares no such field

- **cluster:** `CLUSTER-settings-contract` · **steps:** 12 (0 closed) · **files:** 7 · **est.:** 12.0h
- **files:** `backend/domains/analytics/services/aggregation/command_center_service.py`, `backend/domains/orders/services/core/order_engine.py`, `backend/providers/geography/country.py`, `backend/providers/geography/geo.py`, `backend/domains/governance/services/auth/iam_service_accounts.py`, `backend/infrastructure/messaging/email_service.py`, `backend/modules/admin/routers/governance.py`

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
[ ] `ENV-005` — settings.qr_secret_key is read but Settings declares no such field
    - do: add `qr_secret_key` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'qr_secret_key' backend/config.py`
[ ] `ENV-006` — settings.free_shipping_threshold is read but Settings declares no such field
    - do: add `free_shipping_threshold` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'free_shipping_threshold' backend/config.py`
[ ] `ENV-007` — settings.smtp_username is read but Settings declares no such field
    - do: add `smtp_username` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'smtp_username' backend/config.py`
[ ] `ENV-008` — settings.smtp_use_tls is read but Settings declares no such field
    - do: add `smtp_use_tls` to the Settings class in backend/config.py, or correct the read site
    - verify: `grep -n 'smtp_use_tls' backend/config.py`
    - … and 4 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-settings-contract`)

##### `WP1-LAW-ARCHITECTURE` — Law 1 (Arrows point down) violated: 33 reverse-layer import(s)

- **cluster:** `CLUSTER-law-architecture` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/`

[ ] `LAW-001` — Law 1 (Arrows point down) violated: 33 reverse-layer import(s)
    - do: Fix Law-1 violation: Arrows point down
[ ] `LAW-003` — Law 3 (Cross-domain events/ports) violated: event-spine findings=1
    - do: Fix Law-3 violation: Cross-domain events/ports
[ ] `LAW-005` — Law 5 (Country is orthogonal) violated: SET LOCAL present=False; policy var=app.current_country_code; middleware var=ap…
    - do: Fix Law-5 violation: Country is orthogonal
[ ] `LAW-007` — Law 7 (Allowlist only shrinks) violated: 20 entr(ies), 20 without dated removal plan
    - do: Fix Law-7 violation: Allowlist only shrinks

##### `WP1-LAW-SECURITY` — Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s)

- **cluster:** `CLUSTER-law-security` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/`

[ ] `LAW-034` — Law 34 (Parameterized SQL) violated: 3 f-string SQL site(s)
    - do: Fix Law-34 violation: Parameterized SQL
[ ] `LAW-275` — Law 275 (Encryption at rest) violated: field encryption module missing
    - do: Fix Law-275 violation: Encryption at rest

##### `WP1-INTERACTION-MODAL` — 28 destructive control(s) in 8 modal file(s) with no confirmation step

- **cluster:** `CLUSTER-interaction-modal` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src`

[ ] `IX-destructive-confirm` — 28 destructive control(s) in 8 modal file(s) with no confirmation step
    - do: wrap the destructive action in the confirm dialog primitive and name the affected record in the prompt
    - verify: `grep -rEni 'onClick.*\b(delete|refund|revoke|void|cancel)\b' frontend/web_app/src --include=*.tsx`

_This wave has 91 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 2 · Close correctness and security defects

#### Work packages in wave 2 (241)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP2-CIRCULAR-IMPORT` | 20 | 6 | 0 | 0 | 50.0 | circular package dependency: domains.accounts -> domains.audit -> domains.accounts |
| `WP2-INFRA-IMPORTS-ABOVE` | 15 | 12 | 0 | 0 | 37.5 | `infra imports above`: imports `domains` |
| `WP2-TF-MISSING-COUNTRY-CODE` | 9 | 4 | 0 | 0 | 9.0 | 1x missing country_code in table `notifications`: user-facing table `notifications` lacks `country_code` |
| `WP2-MODULE-IMPORTS-INFRASTRUCTURE` | 7 | 7 | 0 | 0 | 17.5 | `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules` |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 6 | 1 | 0 | 0 | 15.0 | cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 22 occurrence(s) in thi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 0 | 0 | 15.0 | cross-domain import `domains.accounts.models.user` (domains.logistics -> domains.accounts); 28 occurrence(s) in this fi… |
| `WP2-LAW-CODE-QUALITY` | 6 | 1 | 0 | 0 | 6.0 | Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s) |
| `WP2-FORBIDDEN-PACKAGE` | 5 | 2 | 0 | 0 | 5.0 | forbidden package declared: `prometheus-client`==0.26.0 |
| `WP2-LAW-DATABASE` | 4 | 1 | 0 | 0 | 4.0 | Law 45 (No N+1 queries) violated: 304/390 relationship(s) without lazy= |
| `WP2-SUPPLY-CHAIN` | 4 | 1 | 0 | 0 | 4.0 | no dependency scanning step in CI |
| `WP2-VERSION-DRIFT` | 4 | 3 | 0 | 0 | 4.0 | `eslint: ^9` does not satisfy pinned `10` |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 3 | 1 | 0 | 0 | 7.5 | cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file |
| `WP2-INTENT-STUB` | 3 | 3 | 0 | 0 | 3.0 | 1 placeholder response(s) ('not yet wired') in live module |
| `WP2-MIGRATION-DESTRUCTIVE` | 3 | 3 | 0 | 0 | 3.0 | upgrade() performs an unguarded destructive op at line 246 with no expand-contract staging |
| `WP2-PROVIDER-RESILIENCE` | 3 | 1 | 0 | 0 | 7.5 | circuit breaker present in 8/94 provider modules |
| `WP2-CI-CD` | 2 | 1 | 0 | 0 | 5.0 | pipeline lacks: secret scanning |
| `WP2-COLOR-DRIFT` | 2 | 1 | 0 | 0 | 40.0 | 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files exc… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.country -> domains.accounts); 3 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurren… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in t… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 2 | 1 | 0 | 0 | 5.0 | cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this f… |
| `WP2-EXTRA-DOMAIN` | 2 | 2 | 0 | 0 | 5.0 | domain package `media` exists |
| `WP2-INTERACTION-BUTTON` | 2 | 1 | 0 | 0 | 3.5 | 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit |
| `WP2-LAW-PROVIDER` | 2 | 1 | 0 | 0 | 2.0 | Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic |
| `WP2-ROUTER-DB-ACCESS` | 2 | 2 | 0 | 0 | 5.0 | router touches DB/ORM directly (1 hit(s)) |
| `WP2-UNGATED-ROUTE` | 2 | 2 | 0 | 0 | 5.0 | endpoint `list_employees_public` has no visible auth/feature gate |
| `WP2-AP-TODO-ONLY` | 1 | 1 | 0 | 0 | 6.0 | TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58 |
| `WP2-CHAIN-CHAIN-002` | 1 | 1 | 0 | 0 | 6.0 | CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes |
| `WP2-CHAIN-CHAIN-003` | 1 | 1 | 0 | 0 | 6.0 | CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no |
| `WP2-CHAIN-CHAIN-006` | 1 | 1 | 0 | 0 | 6.0 | CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes |
| `WP2-CONTRADICTION-TARGET-VS-CODE` | 1 | 1 | 0 | 0 | 2.5 | _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/media/: domain package `media` exists |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occur… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.catalog -> domains.accounts); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in th… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 6 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s)… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this f… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) i… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurre… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) i… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurr… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in t… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this f… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (domains.orders -> domains.logistics); 34 occurrence(… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurren… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurren… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this fi… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this… |
| `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrenc… |
| `WP2-DB-POOL` | 1 | 1 | 0 | 0 | 1.0 | no pool_size configuration found |
| `WP2-ENV-RAW` | 1 | 1 | 0 | 0 | 1.0 | 140 raw os.getenv/environ read(s) bypass typed settings |
| `WP2-EVENT-SPINE` | 1 | 1 | 0 | 0 | 2.5 | only 6/125 defined event type(s) referenced by services |
| `WP2-FINANCE-AUTOMATION` | 1 | 1 | 0 | 0 | 20.0 | no implementation found for: bad_debt_provision |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `discount_value: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 11 float-for-money signal(s); first: `min_price: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `total_amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 13 float-for-money signal(s); first: `cod_max_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"balance": float(balance),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `price_band_lo: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 8 float-for-money signal(s); first: `commission_reserve: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 9 float-for-money signal(s); first: `"base_salary": float(base_salary),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `"salary": float(emp.salary),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"total_days": float(l.total_days),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_… |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `return float(payout.amount)` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"total_cost": float(total),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 31 float-for-money signal(s); first: `duty_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `"estimated_distance_km": round(total_distance, 1),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 7 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 6 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 50 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `discount_amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 8 float-for-money signal(s); first: `discount_value: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount",… |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `discount_value: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `amount: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 16 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 6 float-for-money signal(s); first: `"price": float(product.price),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),` |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_U… |
| `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `price: float` |
| `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 63 float-for-money signal(s); first: `price: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `net_amount = float(subtotal_decimal)` |
| `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float | None` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `min_price: float | None` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 6 float-for-money signal(s); first: `order_total: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `min_price: float | None` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `salary: Optional[float]` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `gross_amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `total_revenue: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `base_price: float` |
| `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `total: float` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `"price_min": round(base * 0.75, 3),` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 9 float-for-money signal(s); first: `current_price: float` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `"positive": round(sentiment_counts["positive"] / total, 4),` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `return float(psutil.virtual_memory().total / 1024 / 1024)` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `white_balance_strength: float` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-OC` | 1 | 1 | 0 | 0 | 2.5 | 2 float-for-money signal(s); first: `"amount": float(amt),` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `amount: float` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-SH` | 1 | 1 | 0 | 0 | 2.5 | 5 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))` |
| `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-VO` | 1 | 1 | 0 | 0 | 2.5 | 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)` |
| `WP2-HANDOVER` | 1 | 1 | 0 | 0 | 6.0 | 10 of 10 handover/takeover function(s) are missing at least one safety guarantee |
| `WP2-HTTP-CSP` | 1 | 1 | 0 | 0 | 1.0 | 3 place(s) default a CORS/CSP origin to localhost |
| `WP2-INTERACTION-FORM` | 1 | 1 | 0 | 0 | 2.5 | 465 of 743 text input(s) have no label, aria-label or id association |
| `WP2-INTERACTION-MODAL` | 1 | 1 | 0 | 0 | 6.0 | 26 of 27 modal/drawer implementations have no focus management |
| `WP2-INTERACTION-STATE` | 1 | 1 | 0 | 0 | 2.5 | 138 empty or console-only catch handler(s) |
| `WP2-LAW-CONFIG` | 1 | 1 | 0 | 0 | 1.0 | Law 84 (Typed feature flags) violated: 138 raw os.getenv read(s) |
| `WP2-N-PLUS-1` | 1 | 1 | 0 | 0 | 1.0 | 304/397 relationship() declarations omit lazy= |
| `WP2-OFFSET-PAGINATION` | 1 | 1 | 0 | 0 | 1.0 | 89 OFFSET pagination usage(s) (sample: .offset(safe_offset)) |
| `WP2-ORPHAN-FEATURE` | 1 | 1 | 0 | 0 | 1.0 | 224 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.ca… |
| `WP2-PII-LOGS` | 1 | 1 | 0 | 0 | 2.5 | 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc)) |
| `WP2-PROVIDER-CONFIG` | 1 | 1 | 0 | 0 | 1.0 | 13 provider module(s) read secrets via raw os.getenv |
| `WP2-PROVIDER-HEALTH` | 1 | 1 | 0 | 0 | 1.0 | 88/93 provider modules lack health_check() |
| `WP2-PROVIDER-TIMEOUT` | 1 | 1 | 0 | 0 | 1.0 | 62/93 provider modules declare no timeout |
| `WP2-QUALITY-ASSURANCE` | 1 | 1 | 0 | 0 | 20.0 | no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach |
| `WP2-RAW-GETENV` | 1 | 1 | 0 | 0 | 2.5 | 130 raw os.getenv/os.environ read(s) in production paths (top: providers=65, infrastructure=41, domains=13, middleware=… |
| `WP2-ROOT-DISCIPLINE` | 1 | 1 | 0 | 0 | 1.0 | 109 temp/debug/health-test file(s) at backend root: _audit_boot_check.py, _tmp_add_ce.py, _tmp_check_gl.py, _tmp_check_… |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 69: pass-only: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 743: pass-only: except AttributeError: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError): |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 87: pass-only: except ValueError: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 5 silent except block(s); first at line 7529: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 1111: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 3407: truly-silent: except HTTPException as exc: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 693: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 78: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 44: pass-only: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 5 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 30: pass-only: except ValueError: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 9 silent except block(s); first at line 1431: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 518: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 139: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 5 silent except block(s); first at line 280: pass-only: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 203: pass-only: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError): |
| `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 49: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 26: truly-silent: except Exception: |
| `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 88: pass-only: except ValueError: |
| `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 128: truly-silent: except ValueError: |
| `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError): |
| `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 141: truly-silent: except (TypeError, ValueError): |
| `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 102: truly-silent: except (httpx.HTTPError, ValueError, KeyError) as exc: |
| `WP2-TABLE-GOVERNANCE` | 1 | 1 | 0 | 0 | 2.5 | 0 table(s) lack audit timestamps and 2 lack soft delete |
| `WP2-TABLE-RELATION` | 1 | 1 | 0 | 0 | 6.0 | 304 of 390 relationship() calls omit lazy= |
| `WP2-WORKFLOW-RUNTIME` | 1 | 1 | 0 | 0 | 1.0 | 20 of 38 Celery task(s) are defined but never registered in a beat schedule |

##### `WP2-CIRCULAR-IMPORT` — circular package dependency: domains.accounts -> domains.audit -> domains.accounts

- **cluster:** `CLUSTER-circular-import` · **steps:** 20 (0 closed) · **files:** 6 · **est.:** 50.0h
- **files:** `domains.accounts`, `domains.comms`, `domains.catalog`, `domains.audit`, `domains.country`, `domains.customers`

[ ] `ARCH-143` — circular package dependency: domains.accounts -> domains.audit -> domains.accounts
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.audit' backend/accounts`
[ ] `ARCH-144` — circular package dependency: domains.accounts -> domains.audit -> domains.comms -> domains.accounts
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.audit' backend/accounts`
[ ] `ARCH-145` — circular package dependency: domains.accounts -> domains.audit -> domains.comms -> domains.catalog -> domains.accounts
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.audit' backend/accounts`
[ ] `ARCH-146` — circular package dependency: domains.comms -> domains.catalog -> domains.comms
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.catalog' backend/comms`
[ ] `ARCH-147` — circular package dependency: domains.accounts -> domains.audit -> domains.comms -> domains.catalog -> domains.country -…
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.audit' backend/accounts`
[ ] `ARCH-148` — circular package dependency: domains.catalog -> domains.country -> domains.catalog
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.country' backend/catalog`
[ ] `ARCH-149` — circular package dependency: domains.accounts -> domains.audit -> domains.comms -> domains.catalog -> domains.country -…
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.audit' backend/accounts`
[ ] `ARCH-150` — circular package dependency: domains.audit -> domains.comms -> domains.catalog -> domains.country -> domains.customers…
    - do: Break the cycle with a port/event boundary
    - verify: `grep -rn 'from domains.comms' backend/audit`
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-circular-import`)

##### `WP2-INFRA-IMPORTS-ABOVE` — `infra imports above`: imports `domains`

- **cluster:** `CLUSTER-infra-imports-above` · **steps:** 15 (0 closed) · **files:** 12 · **est.:** 37.5h
- **files:** `backend/infrastructure/database/init_db.py`, `backend/infrastructure/database/seed/_common.py`, `backend/infrastructure/geography/__init__.py`, `backend/infrastructure/messaging/email_service.py`, `backend/infrastructure/messaging/realtime.py`, `backend/infrastructure/ml/worker.py`, `backend/infrastructure/storage/backup.py`, `backend/infrastructure/storage/storage.py`

[ ] `ARCH-024` — `infra imports above`: imports `domains`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'domains' backend/infrastructure/database/init_db.py`
[ ] `ARCH-025` — `infra imports above`: imports `domains.finance.services.seeders.treasury_seeder`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'domains.finance.services.seeders.treasury_seeder' backend/infrastructure/database/seed/_common.py`
[ ] `ARCH-026` — `infra imports above`: imports `providers.geography.geoip`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'providers.geography.geoip' backend/infrastructure/geography/__init__.py`
[ ] `ARCH-027` — `infra imports above`: imports `providers.geography.ip`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'providers.geography.ip' backend/infrastructure/geography/__init__.py`
[ ] `ARCH-028` — `infra imports above`: imports `providers.comms.email`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'providers.comms.email' backend/infrastructure/messaging/email_service.py`
[ ] `ARCH-029` — `infra imports above`: imports `domains.accounts.models.user`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'domains.accounts.models.user' backend/infrastructure/messaging/realtime.py`
[ ] `ARCH-030` — `infra imports above`: imports `providers.image.bg_remover`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'providers.image.bg_remover' backend/infrastructure/ml/worker.py`
[ ] `ARCH-031` — `infra imports above`: imports `providers.storage`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'providers.storage' backend/infrastructure/storage/backup.py`
    - … and 7 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-infra-imports-above`)

##### `WP2-TF-MISSING-COUNTRY-CODE` — 1x missing country_code in table `notifications`: user-facing table `notifications` lacks `country_code`

- **cluster:** `CLUSTER-tf-missing-country_code` · **steps:** 9 (0 closed) · **files:** 4 · **est.:** 9.0h
- **files:** `backend/domains/comms/models/communication.py`, `backend/domains/comms/models/marketing.py`, `backend/domains/logistics/models/read_models/__init__.py`, `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-046` — 1x missing country_code in table `notifications`: user-facing table `notifications` lacks `country_code`
    - do: Fix missing-country_code on notifications
[ ] `TF-047` — 1x missing country_code in table `ticket_messages`: user-facing table `ticket_messages` lacks `country_code`
    - do: Fix missing-country_code on ticket_messages
[ ] `TF-051` — 1x missing country_code in table `faqs`: user-facing table `faqs` lacks `country_code`
    - do: Fix missing-country_code on faqs
[ ] `TF-067` — 1x missing country_code in table `internal_emails`: user-facing table `internal_emails` lacks `country_code`
    - do: Fix missing-country_code on internal_emails
[ ] `TF-071` — 1x missing country_code in table `masked_messages`: user-facing table `masked_messages` lacks `country_code`
    - do: Fix missing-country_code on masked_messages
[ ] `TF-081` — 1x missing country_code in table `email_campaigns`: user-facing table `email_campaigns` lacks `country_code`
    - do: Fix missing-country_code on email_campaigns
[ ] `TF-224` — 1x missing country_code in table `shipment_tracking_projections`: user-facing table `shipment_tracking_projections` lac…
    - do: Fix missing-country_code on shipment_tracking_projections
[ ] `TF-251` — 1x missing country_code in table `supplier_documents`: user-facing table `supplier_documents` lacks `country_code`
    - do: Fix missing-country_code on supplier_documents
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-missing-country_code`)

##### `WP2-MODULE-IMPORTS-INFRASTRUCTURE` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`

- **cluster:** `CLUSTER-module-imports-infrastructure` · **steps:** 7 (0 closed) · **files:** 7 · **est.:** 17.5h
- **files:** `backend/modules/admin/routers/__init__.py`, `backend/modules/admin/routers/comms.py`, `backend/modules/customer/routers/__init__.py`, `backend/modules/customer/routers/reviews.py`, `backend/modules/employee/routers/__init__.py`, `backend/modules/logistics/routers/__init__.py`, `backend/modules/supplier/routers/__init__.py`

[ ] `ARCH-041` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.utils.router_loader.load_router_submodules' backend/modules/admin/routers/__init__.py`
[ ] `ARCH-042` — `module imports infrastructure`: imports `infrastructure.messaging.ws_manager.manager`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.messaging.ws_manager.manager' backend/modules/admin/routers/comms.py`
[ ] `ARCH-043` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.utils.router_loader.load_router_submodules' backend/modules/customer/routers/__init__.py`
[ ] `ARCH-044` — `module imports infrastructure`: imports `infrastructure.storage.storage._store`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.storage.storage._store' backend/modules/customer/routers/reviews.py`
[ ] `ARCH-045` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.utils.router_loader.load_router_submodules' backend/modules/employee/routers/__init__.py`
[ ] `ARCH-046` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.utils.router_loader.load_router_submodules' backend/modules/logistics/routers/__init__.py`
[ ] `ARCH-047` — `module imports infrastructure`: imports `infrastructure.utils.router_loader.load_router_submodules`
    - do: Route through the sanctioned layer (events/ports/service call)
    - verify: `grep -n 'infrastructure.utils.router_loader.load_router_submodules' backend/modules/supplier/routers/__init__.py`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 22 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 15.0h
- **files:** `backend/domains/governance/ports.py`

[ ] `ARCH-086` — cross-domain import `domains.accounts.models.banking` (domains.governance -> domains.accounts); 22 occurrence(s) in thi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/governance`
[ ] `ARCH-089` — cross-domain import `domains.comms.models.fraud` (domains.governance -> domains.comms); 26 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/governance`
[ ] `ARCH-091` — cross-domain import `domains.customers.models.customer_schema_models` (domains.governance -> domains.customers); 1 occu…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.customers' backend/domains/governance`
[ ] `ARCH-096` — cross-domain import `domains.promotions.models.coupon_usage` (domains.governance -> domains.promotions); 15 occurrence(…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/governance`
[ ] `ARCH-097` — cross-domain import `domains.security.models.fraud` (domains.governance -> domains.security); 39 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.security' backend/domains/governance`
[ ] `ARCH-098` — cross-domain import `domains.suppliers.models.suppliers` (domains.governance -> domains.suppliers); 10 occurrence(s) in…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.suppliers' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.accounts.models.user` (domains.logistics -> domains.accounts); 28 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 15.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `ARCH-103` — cross-domain import `domains.accounts.models.user` (domains.logistics -> domains.accounts); 28 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/logistics`
[ ] `ARCH-108` — cross-domain import `domains.finance.models.payments` (domains.logistics -> domains.finance); 49 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/logistics`
[ ] `ARCH-109` — cross-domain import `domains.governance.models.admin` (domains.logistics -> domains.governance); 68 occurrence(s) in th…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/logistics`
[ ] `ARCH-110` — cross-domain import `domains.hr.models.employee_models` (domains.logistics -> domains.hr); 7 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/logistics`
[ ] `ARCH-111` — cross-domain import `domains.orders.models.order_entities` (domains.logistics -> domains.orders); 26 occurrence(s) in t…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/logistics`
[ ] `ARCH-112` — cross-domain import `domains.promotions.models.promotions` (domains.logistics -> domains.promotions); 1 occurrence(s) i…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/logistics`

##### `WP2-LAW-CODE-QUALITY` — Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s)

- **cluster:** `CLUSTER-law-code-quality` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/`

[ ] `LAW-019` — Law 19 (No float for money) violated: 18 Float column(s); 0 float money config field(s)
    - do: Fix Law-19 violation: No float for money
[ ] `LAW-021` — Law 21 (Timestamps = server_default) violated: 97 Python-side timestamp default(s)
    - do: Fix Law-21 violation: Timestamps = server_default
[ ] `LAW-023` — Law 23 (Audit columns) violated: 2 table(s) missing audit columns
    - do: Fix Law-23 violation: Audit columns
[ ] `LAW-058` — Law 58 (No print() in production) violated: 7 print() call(s) in production code
    - do: Fix Law-58 violation: No print() in production
[ ] `LAW-059` — Law 59 (No silent exceptions) violated: 68 pass/return-None-only except block(s) (sample scan)
    - do: Fix Law-59 violation: No silent exceptions
[ ] `LAW-062` — Law 62 (TODO/FIXME hygiene) violated: 286 untracked TODO/FIXME
    - do: Fix Law-62 violation: TODO/FIXME hygiene

##### `WP2-FORBIDDEN-PACKAGE` — forbidden package declared: `prometheus-client`==0.26.0

- **cluster:** `CLUSTER-forbidden-package` · **steps:** 5 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/requirements.txt`, `backend/requirements-compiled.txt`

[ ] `TECH-014` — forbidden package declared: `prometheus-client`==0.26.0
    - do: Remove prometheus-client; use the canonical replacement
    - verify: `grep -rni 'prometheus-client' backend/requirements*.txt`
[ ] `TECH-015` — forbidden package declared: `limits`==5.8.0
    - do: Remove limits; use the canonical replacement
    - verify: `grep -rni 'limits' backend/requirements*.txt`
[ ] `TECH-016` — forbidden package declared: `requests`==2.34.2
    - do: Remove requests; use the canonical replacement
    - verify: `grep -rni 'requests' backend/requirements*.txt`
[ ] `TECH-017` — forbidden package declared: `slowapi`==0.1.10
    - do: Remove slowapi; use the canonical replacement
    - verify: `grep -rni 'slowapi' backend/requirements*.txt`
[ ] `TECH-018` — forbidden package declared: `tzlocal`==5.4.4
    - do: Remove tzlocal; use the canonical replacement
    - verify: `grep -rni 'tzlocal' backend/requirements*.txt`

##### `WP2-LAW-DATABASE` — Law 45 (No N+1 queries) violated: 304/390 relationship(s) without lazy=

- **cluster:** `CLUSTER-law-database` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/`

[ ] `LAW-045` — Law 45 (No N+1 queries) violated: 304/390 relationship(s) without lazy=
    - do: Fix Law-45 violation: No N+1 queries
[ ] `LAW-049` — Law 49 (Linear migration history) violated: 4 migration heads
    - do: Fix Law-49 violation: Linear migration history
[ ] `LAW-053` — Law 53 (Index FK columns) violated: 26 FK(s) without index=True (verify composite indexes manually)
    - do: Fix Law-53 violation: Index FK columns
[ ] `LAW-054` — Law 54 (Soft delete) violated: 2 table(s) without is_deleted
    - do: Fix Law-54 violation: Soft delete

##### `WP2-SUPPLY-CHAIN` — no dependency scanning step in CI

- **cluster:** `CLUSTER-supply-chain` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `.github/workflows/`

[ ] `SC-001` — no dependency scanning step in CI
    - do: Add the scanning step to CI
[ ] `SC-002` — no secret scanning in CI
    - do: Add the scanning step to CI
[ ] `SC-003` — no SBOM generation in CI
    - do: Add the scanning step to CI
[ ] `SC-004` — no container scan in CI
    - do: Add the scanning step to CI

##### `WP2-VERSION-DRIFT` — `eslint: ^9` does not satisfy pinned `10`

- **cluster:** `CLUSTER-version-drift` · **steps:** 4 (0 closed) · **files:** 3 · **est.:** 4.0h
- **files:** `frontend/web_app/package.json`, `frontend/mobile_app/package.json`, `backend/requirements.txt`

[ ] `TECH-004` — `eslint: ^9` does not satisfy pinned `10`
    - do: Upgrade eslint to 10
[ ] `TECH-008` — `eslint: ^9.0.0` does not satisfy pinned `10`
    - do: Upgrade eslint to 10
[ ] `TECH-019` — `valkey==6.1.1` does not satisfy pinned `9.0.6+`
    - do: Update valkey to the pinned version
    - verify: `grep -i 'valkey' backend/requirements.txt`
[ ] `TECH-020` — `celery==5.4.0` does not satisfy pinned `5.5+`
    - do: Update celery to the pinned version
    - verify: `grep -i 'celery' backend/requirements.txt`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/orders/ports.py`

[ ] `ARCH-115` — cross-domain import `domains.accounts.models.user` (domains.orders -> domains.accounts); 11 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/orders`
[ ] `ARCH-117` — cross-domain import `domains.catalog.models.products` (domains.orders -> domains.catalog); 10 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/orders`
[ ] `ARCH-125` — cross-domain import `domains.promotions.services.admin_promotion_service` (domains.orders -> domains.promotions); 8 occ…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/orders`

##### `WP2-INTENT-STUB` — 1 placeholder response(s) ('not yet wired') in live module

- **cluster:** `CLUSTER-intent-stub` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `backend/domains/comms/services/admin/__init__.py`, `backend/modules/admin/routers/country.py`, `backend/modules/admin/routers/orders.py`

[ ] `INTENT-001` — 1 placeholder response(s) ('not yet wired') in live module
    - do: Implement or remove the placeholder
[ ] `INTENT-002` — 1 placeholder response(s) ('not yet wired') in live module
    - do: Implement or remove the placeholder
[ ] `INTENT-003` — 1 placeholder response(s) ('not yet wired') in live module
    - do: Implement or remove the placeholder

##### `WP2-MIGRATION-DESTRUCTIVE` — upgrade() performs an unguarded destructive op at line 246 with no expand-contract staging

- **cluster:** `CLUSTER-migration-destructive` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py`, `backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py`, `backend/alembic/versions/2026_10_04_0014_encrypt_payment_gateway_credentials.py`

[ ] `MIG-002` — upgrade() performs an unguarded destructive op at line 246 with no expand-contract staging
    - do: Split into expand + contract steps with a rollback window
    - verify: `sed -n '246p' backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py`
[ ] `MIG-008` — upgrade() performs an unguarded destructive op at line 79 with no expand-contract staging
    - do: Split into expand + contract steps with a rollback window
    - verify: `sed -n '79p' backend/alembic/versions/2026_09_03_0004_audit_logs_fulltext_search_vector.py`
[ ] `MIG-011` — upgrade() performs an unguarded destructive op at line 111 with no expand-contract staging
    - do: Split into expand + contract steps with a rollback window
    - verify: `sed -n '111p' backend/alembic/versions/2026_10_04_0014_encrypt_payment_gateway_credentials.py`

##### `WP2-PROVIDER-RESILIENCE` — circuit breaker present in 8/94 provider modules

- **cluster:** `CLUSTER-provider-resilience` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/providers/`

[ ] `OBS-001` — circuit breaker present in 8/94 provider modules
    - do: Wrap provider calls in pybreaker breakers
[ ] `OBS-002` — retry policy present in 7/94 provider modules
    - do: Add bounded retries with jitter
[ ] `OBS-003` — explicit timeout in 29/94 provider modules
    - do: Add explicit HTTP timeouts

##### `WP2-CI-CD` — pipeline lacks: secret scanning

- **cluster:** `CLUSTER-ci-cd` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `.github/workflows/`

[ ] `D2P-001` — pipeline lacks: secret scanning
    - do: Add a secret scanning step
[ ] `D2P-002` — pipeline lacks: dependency scanning
    - do: Add a dependency scanning step

##### `WP2-COLOR-DRIFT` — 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files excluded — a literal is 

- **cluster:** `CLUSTER-color-drift` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 40.0h
- **files:** `frontend/web_app/src`

[ ] `DS-hex-drift` — 165 hardcoded hex colour(s) across 33 component file(s) outside the token layer (brand SVG, chart and palette files exc…
    - do: convert literals to `var(--color-*)` references or Tailwind token classes; brand assets (logo SVG) may keep literals but must be isolated in src/shared/logo/
    - verify: `grep -rEon '#[0-9a-fA-F]{6}' frontend/web_app/src | grep -v 'src/styles/tokens.css' | wc -l`
[ ] `DS-palette-drift` — 375 raw Tailwind palette class(es) across 52 files bypass the semantic token scale
    - do: replace the raw palette classes with semantic token classes, starting with the five worst files; add an ESLint rule so they cannot come back
    - verify: `grep -rEn '(bg|text|border)-(slate|gray|zinc|neutral)-[0-9]{2,3}' frontend/web_app/src | wc -l`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/accounts/models/user.py`

[ ] `ARCH-048` — cross-domain import `domains.catalog.models.products` (domains.accounts -> domains.catalog); 4 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/accounts`
[ ] `ARCH-049` — cross-domain import `domains.customers.models.customer_schema_models` (domains.accounts -> domains.customers); 3 occurr…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.customers' backend/domains/accounts`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/audit/services/compliance_engine.py`

[ ] `ARCH-053` — cross-domain import `domains.accounts.models.user` (domains.audit -> domains.accounts); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/audit`
[ ] `ARCH-056` — cross-domain import `domains.hr.models.employee_models` (domains.audit -> domains.hr); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/audit`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` — cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/catalog/services/products/admin_products_service.py`

[ ] `ARCH-058` — cross-domain import `domains.comms.models.communication` (domains.catalog -> domains.comms); 1 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/catalog`
[ ] `ARCH-059` — cross-domain import `domains.governance.models.core` (domains.catalog -> domains.governance); 1 occurrence(s) in this f…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/catalog`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `ARCH-061` — cross-domain import `domains.accounts.models.user` (domains.comms -> domains.accounts); 2 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/comms`
[ ] `ARCH-065` — cross-domain import `domains.governance.models.core` (domains.comms -> domains.governance); 19 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.accounts.models.user` (domains.country -> domains.accounts); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/country/models/__init__.py`

[ ] `ARCH-068` — cross-domain import `domains.accounts.models.user` (domains.country -> domains.accounts); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/country`
[ ] `ARCH-073` — cross-domain import `domains.logistics.models.shipping_rules` (domains.country -> domains.logistics); 3 occurrence(s) i…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.logistics' backend/domains/country`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `ARCH-069` — cross-domain import `domains.customers.models.cross_country_session` (domains.country -> domains.customers); 1 occurren…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.customers' backend/domains/country`
[ ] `ARCH-071` — cross-domain import `domains.governance.models.legal_contract_template` (domains.country -> domains.governance); 2 occu…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/country`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/customers/services/cart_service.py`

[ ] `ARCH-074` — cross-domain import `domains.accounts.models.core` (domains.customers -> domains.accounts); 9 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/customers`
[ ] `ARCH-075` — cross-domain import `domains.catalog.models.products` (domains.customers -> domains.catalog); 5 occurrence(s) in this f…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/customers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `ARCH-079` — cross-domain import `domains.catalog.models.products` (domains.finance -> domains.catalog); 2 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/finance`
[ ] `ARCH-083` — cross-domain import `domains.logistics.models.erp` (domains.finance -> domains.logistics); 26 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.logistics' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `ARCH-080` — cross-domain import `domains.comms.models.suppliers` (domains.finance -> domains.comms); 4 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/finance`
[ ] `ARCH-081` — cross-domain import `domains.country.models.countries` (domains.finance -> domains.country); 5 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/governance/services/export_read_service.py`

[ ] `ARCH-088` — cross-domain import `domains.catalog.models.products` (domains.governance -> domains.catalog); 10 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/governance`
[ ] `ARCH-095` — cross-domain import `domains.orders.models.orders` (domains.governance -> domains.orders); 12 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `ARCH-116` — cross-domain import `domains.audit.services.logs.audit_service` (domains.orders -> domains.audit); 2 occurrence(s) in t…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.audit' backend/domains/orders`
[ ] `ARCH-120` — cross-domain import `domains.customers.services.coupons_service` (domains.orders -> domains.customers); 1 occurrence(s)…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.customers' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/promotions/services/engine/admin_commerce_configuration_service.py`

[ ] `ARCH-127` — cross-domain import `domains.accounts.models.user` (domains.promotions -> domains.accounts); 2 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/promotions`
[ ] `ARCH-130` — cross-domain import `domains.governance.models.admin` (domains.promotions -> domains.governance); 2 occurrence(s) in th…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/promotions`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `ARCH-135` — cross-domain import `domains.accounts.models.banking` (domains.suppliers -> domains.accounts); 7 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/suppliers`
[ ] `ARCH-140` — cross-domain import `domains.governance` (domains.suppliers -> domains.governance); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/suppliers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/suppliers/services/analytics/supplier_analytics_service.py`

[ ] `ARCH-136` — cross-domain import `domains.catalog.models.products` (domains.suppliers -> domains.catalog); 7 occurrence(s) in this f…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/suppliers`
[ ] `ARCH-142` — cross-domain import `domains.orders.models.orders` (domains.suppliers -> domains.orders); 14 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/suppliers`

##### `WP2-EXTRA-DOMAIN` — domain package `media` exists

- **cluster:** `CLUSTER-extra-domain` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/domains/media`, `backend/domains/payments`

[ ] `ARCH-002` — domain package `media` exists
    - do: Demote media to canonical domain or document an ARCH change
    - verify: `ls backend/domains`
[ ] `ARCH-003` — domain package `payments` exists
    - do: Demote payments to canonical domain or document an ARCH change
    - verify: `ls backend/domains`

##### `WP2-INTERACTION-BUTTON` — 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit

- **cluster:** `CLUSTER-interaction-button` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 3.5h
- **files:** `frontend/web_app/src`

[ ] `IX-button-type` — 949 of 1466 button elements have no explicit type; inside a <form> the HTML default is type=submit
    - do: add type="button" to every non-submit button; add an ESLint rule (react/button-has-type) so it cannot regress
    - verify: `grep -rEc '<button(\s|>)' frontend/web_app/src --include=*.tsx | awk -F: '$2>0' | wc -l`
[ ] `IX-mutation-error-swallowed` — 9 mutating action(s) sit next to an empty or console-only catch
    - do: replace the swallowed catch with a toast.error (or rethrow) and add a pending state so the button cannot be double-fired
    - verify: `grep -rEn 'catch\s*(\([^)]*\))?\s*\{\s*\}' frontend/web_app/src --include=*.tsx`

##### `WP2-LAW-PROVIDER` — Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic

- **cluster:** `CLUSTER-law-provider` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/`

[ ] `LAW-123` — Law 123 (Single SDK per provider) violated: 3 provider file(s) containing routing logic
    - do: Fix Law-123 violation: Single SDK per provider
[ ] `LAW-129` — Law 129 (Health checks) violated: 5/93 providers have health_check()
    - do: Fix Law-129 violation: Health checks

##### `WP2-ROUTER-DB-ACCESS` — router touches DB/ORM directly (1 hit(s))

- **cluster:** `CLUSTER-router-db-access` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/modules/admin/routers/staff.py`, `backend/modules/customer/routers/reviews.py`

[ ] `ARCH-165` — router touches DB/ORM directly (1 hit(s))
    - do: Move DB access into the domain service
    - verify: `grep -nE 'get_db|Session|session\.' backend/modules/admin/routers/staff.py`
[ ] `ARCH-169` — router touches DB/ORM directly (1 hit(s))
    - do: Move DB access into the domain service
    - verify: `grep -nE 'get_db|Session|session\.' backend/modules/customer/routers/reviews.py`

##### `WP2-UNGATED-ROUTE` — endpoint `list_employees_public` has no visible auth/feature gate

- **cluster:** `CLUSTER-ungated-route` · **steps:** 2 (0 closed) · **files:** 2 · **est.:** 5.0h
- **files:** `backend/modules/employee/routers/hr.py`, `backend/modules/employee/routers/hr/employees.py`

[ ] `WIRE-010` — endpoint `list_employees_public` has no visible auth/feature gate
    - do: Add Depends(get_current_user) + require_feature(...)
[ ] `WIRE-011` — endpoint `list_employees_public` has no visible auth/feature gate
    - do: Add Depends(get_current_user) + require_feature(...)

##### `WP2-AP-TODO-ONLY` — TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58

- **cluster:** `CLUSTER-ap-todo-only` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `AP-005` — TODO-only implementation: 296 occurrence(s); sample backend/domains/accounts/models/core.py:58
    - do: Implement or remove the marked paths

##### `WP2-CHAIN-CHAIN-002` — CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-002` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/finance/`

[ ] `BLOCK-001` — CHAIN-002 (Supplier payout) is PARTIAL: 3/3 steps located; events 0/1; tests=yes
    - do: Implement the missing steps/events and add a chain integration test

##### `WP2-CHAIN-CHAIN-003` — CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no

- **cluster:** `CLUSTER-chain-chain-003` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/orders/`

[ ] `BLOCK-002` — CHAIN-003 (Return and refund) is PARTIAL: 3/3 steps located; events 0/1; tests=no
    - do: Implement the missing steps/events and add a chain integration test

##### `WP2-CHAIN-CHAIN-006` — CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes

- **cluster:** `CLUSTER-chain-chain-006` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/`

[ ] `BLOCK-004` — CHAIN-006 (Customer registration and KYC) is PARTIAL: 3/3 steps located; events 0/1; tests=yes
    - do: Implement the missing steps/events and add a chain integration test

##### `WP2-CONTRADICTION-TARGET-VS-CODE` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/media/: domain package `media` exists

- **cluster:** `CLUSTER-contradiction-target_vs_code` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/media/`

[ ] `CONTRAD-003` — _most_imp_docx/ARCHITECTURE_STACK.md (Law 12): fixed 15 domains | backend/domains/media/: domain package `media` exists
    - do: Decide which source is authoritative and align the other; user decision required

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/permissions/permission_service.py`

[ ] `ARCH-050` — cross-domain import `domains.governance.core.approval_matrix_service` (domains.accounts -> domains.governance); 3 occur…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/accounts`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ACCO` — cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/users/user_management_service.py`

[ ] `ARCH-051` — cross-domain import `domains.promotions.models.promotions` (domains.accounts -> domains.promotions); 1 occurrence(s) in…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/accounts`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ANAL` — cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/analytics/models/analytics_schema_models.py`

[ ] `ARCH-052` — cross-domain import `domains.finance.models.general_ledger` (domains.analytics -> domains.finance); 1 occurrence(s) in…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/analytics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/data_residency_service.py`

[ ] `ARCH-054` — cross-domain import `domains.country.models.countries` (domains.audit -> domains.country); 4 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/audit`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-AUDI` — cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/ediscovery.py`

[ ] `ARCH-055` — cross-domain import `domains.finance.models.finance` (domains.audit -> domains.finance); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/audit`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` — cross-domain import `domains.accounts.models.core` (domains.catalog -> domains.accounts); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/models/products.py`

[ ] `ARCH-057` — cross-domain import `domains.accounts.models.core` (domains.catalog -> domains.accounts); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/catalog`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CATA` — cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/ports.py`

[ ] `ARCH-060` — cross-domain import `domains.promotions.models.promotions` (domains.catalog -> domains.promotions); 3 occurrence(s) in…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/catalog`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `ARCH-063` — cross-domain import `domains.country.models.countries` (domains.comms -> domains.country); 4 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/models/suppliers.py`

[ ] `ARCH-067` — cross-domain import `domains.suppliers.models.suppliers` (domains.comms -> domains.suppliers); 7 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.suppliers' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/ports.py`

[ ] `ARCH-066` — cross-domain import `domains.promotions.models.promotions` (domains.comms -> domains.promotions); 4 occurrence(s) in th…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/utility/shared_utils.py`

[ ] `ARCH-062` — cross-domain import `domains.catalog.models.upload_job` (domains.comms -> domains.catalog); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COMM` — cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/tickets/tickets_service.py`

[ ] `ARCH-064` — cross-domain import `domains.finance.models.finance` (domains.comms -> domains.finance); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/comms`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 6 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/ports.py`

[ ] `ARCH-070` — cross-domain import `domains.finance.models.tax_rules` (domains.country -> domains.finance); 6 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/country`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-COUN` — cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/geo/country_detection.py`

[ ] `ARCH-072` — cross-domain import `domains.hr.models.employee_models` (domains.country -> domains.hr); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/country`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/coupons_read_service.py`

[ ] `ARCH-077` — cross-domain import `domains.promotions.models.coupon_usage` (domains.customers -> domains.promotions); 6 occurrence(s)…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/customers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-CUST` — cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/customer_health_engine.py`

[ ] `ARCH-076` — cross-domain import `domains.orders.models.orders` (domains.customers -> domains.orders); 4 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/customers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/admin_commission_service.py`

[ ] `ARCH-082` — cross-domain import `domains.governance.models.admin` (domains.finance -> domains.governance); 17 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `ARCH-084` — cross-domain import `domains.orders.models.orders` (domains.finance -> domains.orders); 14 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_service.py`

[ ] `ARCH-078` — cross-domain import `domains.accounts.models.user` (domains.finance -> domains.accounts); 9 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-FINA` — cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `ARCH-085` — cross-domain import `domains.promotions.models.promotions` (domains.finance -> domains.promotions); 1 occurrence(s) in…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.promotions' backend/domains/finance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/models/admin.py`

[ ] `ARCH-090` — cross-domain import `domains.country.models.countries` (domains.governance -> domains.country); 7 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/admin/bulk_ops_service.py`

[ ] `ARCH-092` — cross-domain import `domains.finance.models.finance` (domains.governance -> domains.finance); 4 occurrence(s) in this f…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/approval/approval_matrix_service.py`

[ ] `ARCH-093` — cross-domain import `domains.hr.models.employee_models` (domains.governance -> domains.hr); 5 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/audit/__init__.py`

[ ] `ARCH-087` — cross-domain import `domains.audit.services.retention_service` (domains.governance -> domains.audit); 2 occurrence(s) i…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.audit' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-GOVE` — cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/users_service.py`

[ ] `ARCH-094` — cross-domain import `domains.logistics.models.logistics_entities` (domains.governance -> domains.logistics); 12 occurre…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.logistics' backend/domains/governance`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-M` — cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `ARCH-100` — cross-domain import `domains.country.models.countries` (domains.hr -> domains.country); 9 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/hr`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/coi_service.py`

[ ] `ARCH-102` — cross-domain import `domains.governance.models.core` (domains.hr -> domains.governance); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/hr`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/hr_service.py`

[ ] `ARCH-101` — cross-domain import `domains.finance.models.finance` (domains.hr -> domains.finance); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/hr`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-HR-S` — cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/hr_employee_service.py`

[ ] `ARCH-099` — cross-domain import `domains.accounts.models.core` (domains.hr -> domains.accounts); 4 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/hr`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/ports.py`

[ ] `ARCH-106` — cross-domain import `domains.country.models.country_control` (domains.logistics -> domains.country); 50 occurrence(s) i…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_fallback_service.py`

[ ] `ARCH-104` — cross-domain import `domains.catalog.models.products` (domains.logistics -> domains.catalog); 10 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_operations_service.py`

[ ] `ARCH-105` — cross-domain import `domains.comms.models.marketing` (domains.logistics -> domains.comms); 21 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/country_communication_service.py`

[ ] `ARCH-107` — cross-domain import `domains.customers.models.cross_country_session` (domains.logistics -> domains.customers); 2 occurr…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.customers' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/shipment_service.py`

[ ] `ARCH-114` — cross-domain import `domains.suppliers.models.suppliers` (domains.logistics -> domains.suppliers); 1 occurrence(s) in t…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.suppliers' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-LOGI` — cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/health/service.py`

[ ] `ARCH-113` — cross-domain import `domains.security.models.fraud` (domains.logistics -> domains.security); 2 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.security' backend/domains/logistics`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/models/order_entities.py`

[ ] `ARCH-119` — cross-domain import `domains.country.models.countries` (domains.orders -> domains.country); 1 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/service.py`

[ ] `ARCH-122` — cross-domain import `domains.governance.models.core` (domains.orders -> domains.governance); 12 occurrence(s) in this f…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.governance' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/admin_extra.py`

[ ] `ARCH-118` — cross-domain import `domains.comms.models.marketing` (domains.orders -> domains.comms); 14 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/misc.py`

[ ] `ARCH-123` — cross-domain import `domains.hr.models.employee_models` (domains.orders -> domains.hr); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/disputes/service.py`

[ ] `ARCH-126` — cross-domain import `domains.suppliers.models.suppliers` (domains.orders -> domains.suppliers); 1 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.suppliers' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.logistics.models.logistics_entities` (domains.orders -> domains.logistics); 34 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/logistics_partner_service.py`

[ ] `ARCH-124` — cross-domain import `domains.logistics.models.logistics_entities` (domains.orders -> domains.logistics); 34 occurrence(…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.logistics' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-ORDE` — cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `ARCH-121` — cross-domain import `domains.finance.services.payments.payment_engine` (domains.orders -> domains.finance); 11 occurren…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/orders`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `ARCH-129` — cross-domain import `domains.country.models.countries` (domains.promotions -> domains.country); 2 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/promotions`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/coupon_service.py`

[ ] `ARCH-128` — cross-domain import `domains.catalog.models.products` (domains.promotions -> domains.catalog); 2 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.catalog' backend/domains/promotions`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-PROM` — cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/customer_coupons_create_service.py`

[ ] `ARCH-131` — cross-domain import `domains.orders.customer_coupons_create_service` (domains.promotions -> domains.orders); 1 occurren…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.orders' backend/domains/promotions`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/detection/public_security_detection_service.py`

[ ] `ARCH-132` — cross-domain import `domains.accounts.models.user` (domains.security -> domains.accounts); 3 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.accounts' backend/domains/security`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `ARCH-134` — cross-domain import `domains.suppliers.models.fraud_indicators` (domains.security -> domains.suppliers); 2 occurrence(s…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.suppliers' backend/domains/security`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SECU` — cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/health/flat_risk_service.py`

[ ] `ARCH-133` — cross-domain import `domains.hr.models.employee_models` (domains.security -> domains.hr); 5 occurrence(s) in this file
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.hr' backend/domains/security`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/badges/badge_write_service.py`

[ ] `ARCH-139` — cross-domain import `domains.finance.models.finance` (domains.suppliers -> domains.finance); 1 occurrence(s) in this fi…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.finance' backend/domains/suppliers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/contract/contract_service.py`

[ ] `ARCH-138` — cross-domain import `domains.country.models.countries` (domains.suppliers -> domains.country); 2 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.country' backend/domains/suppliers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/disputes_service.py`

[ ] `ARCH-137` — cross-domain import `domains.comms.models.communication` (domains.suppliers -> domains.comms); 18 occurrence(s) in this…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.comms' backend/domains/suppliers`

##### `WP2-CROSS-DOMAIN-DIRECT-BACKEND-DOMAINS-SUPP` — cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrence(s) in this file

- **cluster:** `CLUSTER-cross-domain-direct` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `ARCH-141` — cross-domain import `domains.logistics.models.logistics_entities` (domains.suppliers -> domains.logistics); 3 occurrenc…
    - do: Move the call behind the owning domain's ports/ or emit an event
    - verify: `grep -rn 'from domains.logistics' backend/domains/suppliers`

##### `WP2-DB-POOL` — no pool_size configuration found

- **cluster:** `CLUSTER-db-pool` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `DB-005` — no pool_size configuration found
    - do: Configure the pool in the engine factory

##### `WP2-ENV-RAW` — 140 raw os.getenv/environ read(s) bypass typed settings

- **cluster:** `CLUSTER-env-raw` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/config.py`

[ ] `ENV-016` — 140 raw os.getenv/environ read(s) bypass typed settings
    - do: Move reads into config.py settings

##### `WP2-EVENT-SPINE` — only 6/125 defined event type(s) referenced by services

- **cluster:** `CLUSTER-event-spine` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/`

[ ] `WIRE-004` — only 6/125 defined event type(s) referenced by services
    - do: Publish or delete the unused event classes

##### `WP2-FINANCE-AUTOMATION` — no implementation found for: bad_debt_provision

- **cluster:** `CLUSTER-finance-automation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/finance`

[ ] `FIN-manual-processes` — no implementation found for: bad_debt_provision
    - do: implement each as a Celery task with an idempotent posting path and a daily exception report, and register it in the beat schedule
    - verify: `grep -rn 'bad_debt\|gateway_fee' backend/domains/finance`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-ACCO` — 1 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/permissions/permission_service.py`

[ ] `LOGIC-103` — 1 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/accounts/services/permissions/permission_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/commission_service.py`

[ ] `LOGIC-105` — 1 float-for-money signal(s); first: `max_commission_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/commission_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 1 float-for-money signal(s); first: `discount_value: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/product_discount_service.py`

[ ] `LOGIC-106` — 1 float-for-money signal(s); first: `discount_value: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/products/product_discount_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 11 float-for-money signal(s); first: `min_price: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-107` — 11 float-for-money signal(s); first: `min_price: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/products/products_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/ai_search_service.py`

[ ] `LOGIC-108` — 2 float-for-money signal(s); first: `intent["entities"]["price_range"] = float(price_match.group(1))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/search/ai_search_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CATA` — 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-109` — 31 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/catalog/services/search/search_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 2 float-for-money signal(s); first: `total_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/transactional.py`

[ ] `LOGIC-110` — 2 float-for-money signal(s); first: `total_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/email/transactional.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `LOGIC-111` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/messaging/chat_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COMM` — 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/utility/shared_utils.py`

[ ] `LOGIC-112` — 2 float-for-money signal(s); first: `total_duration_ms: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/comms/services/shared/utility/shared_utils.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/ports.py`

[ ] `LOGIC-113` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/ports.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 13 float-for-money signal(s); first: `cod_max_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_config_admin_service.py`

[ ] `LOGIC-114` — 13 float-for-money signal(s); first: `cod_max_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/core/country_config_admin_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/localization/localization_service.py`

[ ] `LOGIC-115` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/localization/localization_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-COUN` — 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_heuristic_engine.py`

[ ] `LOGIC-116` — 1 float-for-money signal(s); first: `_BASE_COMMISSIONS: dict[str, dict[str, float]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/country/services/research/country_heuristic_engine.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/cart_service.py`

[ ] `LOGIC-118` — 3 float-for-money signal(s); first: `subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/cart_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 1 float-for-money signal(s); first: `"balance": float(balance),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/coins/zozi_coins_service.py`

[ ] `LOGIC-119` — 1 float-for-money signal(s); first: `"balance": float(balance),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/coins/zozi_coins_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 5 float-for-money signal(s); first: `price_band_lo: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/recommendations/recommendation_service.py`

[ ] `LOGIC-120` — 5 float-for-money signal(s); first: `price_band_lo: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/recommendations/recommendation_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-CUST` — 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-121` — 14 float-for-money signal(s); first: `PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/customers/services/search_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 2 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/read_models/governance_read_models.py`

[ ] `LOGIC-136` — 2 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/read_models/governance_read_models.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/schemas/governance_schemas.py`

[ ] `LOGIC-137` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/schemas/governance_schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 3 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/approval/approval_matrix_service.py`

[ ] `LOGIC-138` — 3 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/approval/approval_matrix_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 8 float-for-money signal(s); first: `commission_reserve: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-139` — 8 float-for-money signal(s); first: `commission_reserve: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/command_center/command_center_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `LOGIC-140` — 4 float-for-money signal(s); first: `"commission": float(result[1] or 0),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/command_center/service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/products_service.py`

[ ] `LOGIC-141` — 1 float-for-money signal(s); first: `"price": float(p.price) if p.price is not None else None,`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/products_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-GOVE` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/settings/governance_package_service.py`

[ ] `LOGIC-142` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/governance/services/settings/governance_package_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/employee_service.py`

[ ] `LOGIC-143` — 2 float-for-money signal(s); first: `"salary": float(employee.salary) if employee.salary else None,`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/employees/employee_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/hr_employee_service.py`

[ ] `LOGIC-144` — 1 float-for-money signal(s); first: `"salary": float(row[5]) if row[5] else None,`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/hr_employee_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 9 float-for-money signal(s); first: `"base_salary": float(base_salary),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_engine.py`

[ ] `LOGIC-145` — 9 float-for-money signal(s); first: `"base_salary": float(base_salary),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/payroll/payroll_engine.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_service.py`

[ ] `LOGIC-146` — 1 float-for-money signal(s); first: `return {"total_paid": float(total), "total_records": count, "paid_count": paid}`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/payroll/payroll_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 3 float-for-money signal(s); first: `"salary": float(emp.salary),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/dei_auditor.py`

[ ] `LOGIC-147` — 3 float-for-money signal(s); first: `"salary": float(emp.salary),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/performance/dei_auditor.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `"total_days": float(l.total_days),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/shift/shift_roster_service.py`

[ ] `LOGIC-148` — 1 float-for-money signal(s); first: `"total_days": float(l.total_days),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/shift/shift_roster_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-HR-S` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/travel/travel_service.py`

[ ] `LOGIC-149` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/hr/services/travel/travel_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_orders': total_orders

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_fallback_service.py`

[ ] `LOGIC-150` — 3 float-for-money signal(s); first: `return {'total_revenue': float(total_revenue), 'total_users': total_users, 'total_…
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_fallback_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 2 float-for-money signal(s); first: `duty_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_imports_service.py`

[ ] `LOGIC-151` — 2 float-for-money signal(s); first: `duty_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_imports_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 1 float-for-money signal(s); first: `return float(payout.amount)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_logistics_operations_service.py`

[ ] `LOGIC-152` — 1 float-for-money signal(s); first: `return float(payout.amount)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/admin_logistics_operations_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 1 float-for-money signal(s); first: `"total_cost": float(total),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/logistics_engine.py`

[ ] `LOGIC-153` — 1 float-for-money signal(s); first: `"total_cost": float(total),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/logistics_engine.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 31 float-for-money signal(s); first: `duty_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-154` — 31 float-for-money signal(s); first: `duty_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/core/service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py`

[ ] `LOGIC-155` — 3 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/country/admin_logistics_fallback_read_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 2 float-for-money signal(s); first: `"estimated_distance_km": round(total_distance, 1),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/geo/routing_service.py`

[ ] `LOGIC-156` — 2 float-for-money signal(s); first: `"estimated_distance_km": round(total_distance, 1),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/geo/routing_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 7 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `LOGIC-157` — 7 float-for-money signal(s); first: `max_combined_discount_amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/admin_logistics_operations_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_partner_service.py`

[ ] `LOGIC-158` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/logistics_partner_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_pricing_service.py`

[ ] `LOGIC-159` — 3 float-for-money signal(s); first: `charge_amount = float(data.get("charge_amount", 0) or 0)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/logistics_pricing_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 6 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/pricing_service.py`

[ ] `LOGIC-160` — 6 float-for-money signal(s); first: `"charge_amount": float(charge_amount or 0),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/pricing_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 50 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-161` — 50 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-LOGI` — 3 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/settlement_service.py`

[ ] `LOGIC-162` — 3 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/logistics/services/partners/settlement_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `discount_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/events.py`

[ ] `LOGIC-169` — 1 float-for-money signal(s); first: `discount_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/events.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 8 float-for-money signal(s); first: `discount_value: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/admin_promotion_ops_service.py`

[ ] `LOGIC-170` — 8 float-for-money signal(s); first: `discount_value: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/admin_promotion_ops_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/admin_promotion_service.py`

[ ] `LOGIC-171` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/admin_promotion_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/coin_service.py`

[ ] `LOGIC-172` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coins/coin_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/promotion_points_service.py`

[ ] `LOGIC-173` — 1 float-for-money signal(s); first: `base_points = int(float(order_total)) * points_per_omr`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coins/promotion_points_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 6 float-for-money signal(s); first: `order_total: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/customer_coupons_create_service.py`

[ ] `LOGIC-174` — 6 float-for-money signal(s); first: `order_total: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/coupons/customer_coupons_create_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_commerce_configuration_service.py`

[ ] `LOGIC-175` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/admin_commerce_configuration_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_promotions_write_service.py`

[ ] `LOGIC-176` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/admin_promotions_write_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount", 0) or 0),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/promotion_service.py`

[ ] `LOGIC-177` — 4 float-for-money signal(s); first: `"max_combined_discount_amount": float(getattr(row, "max_combined_discount_amount",…
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/engine/promotion_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-PROM` — 4 float-for-money signal(s); first: `discount_value: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/promotion_admin_write_service.py`

[ ] `LOGIC-178` — 4 float-for-money signal(s); first: `discount_value: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/promotions/services/promotion_admin_write_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SECU` — 4 float-for-money signal(s); first: `amount: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-179` — 4 float-for-money signal(s); first: `amount: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/security/services/fraud/fraud_detection_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/events.py`

[ ] `LOGIC-180` — 2 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/events.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/analytics/supplier_analytics_service.py`

[ ] `LOGIC-181` — 2 float-for-money signal(s); first: `avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/analytics/supplier_analytics_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 16 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-182` — 16 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/health/supplier_health.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health_engine.py`

[ ] `LOGIC-183` — 2 float-for-money signal(s); first: `first_revenue = sum(float(o.total_amount) for o in first_half)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/health/supplier_health_engine.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py`

[ ] `LOGIC-184` — 2 float-for-money signal(s); first: `return float(config.supplier_onboarding_fee)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/onboarding/supplier_onboarding_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 5 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-187` — 5 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_product_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 5 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-188` — 5 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_products.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 6 float-for-money signal(s); first: `"price": float(product.price),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products_service.py`

[ ] `LOGIC-189` — 6 float-for-money signal(s); first: `"price": float(product.price),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_products_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py`

[ ] `LOGIC-190` — 2 float-for-money signal(s); first: `coverage = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/products/supplier_supplier_upload_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/profile/supplier_profile.py`

[ ] `LOGIC-192` — 1 float-for-money signal(s); first: `"total_revenue": float(total_revenue),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/profile/supplier_profile.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/settlement/multi_currency_settlement.py`

[ ] `LOGIC-193` — 3 float-for-money signal(s); first: `"total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_U…
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/settlement/multi_currency_settlement.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-DOMAINS-SUPP` — 2 float-for-money signal(s); first: `price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-194` — 2 float-for-money signal(s); first: `price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/domains/suppliers/services/supplier_shared.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 63 float-for-money signal(s); first: `price: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/schemas.py`

[ ] `LOGIC-195` — 63 float-for-money signal(s); first: `price: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/database/schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 2 float-for-money signal(s); first: `net_amount = float(subtotal_decimal)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/downstream_wiring.py`

[ ] `LOGIC-196` — 2 float-for-money signal(s); first: `net_amount = float(subtotal_decimal)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/messaging/downstream_wiring.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-INFRASTRUCTU` — 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/analytics.py`

[ ] `LOGIC-197` — 1 float-for-money signal(s); first: `total_revenue = float(row[1]) if row and row[1] else 0.0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/infrastructure/utils/analytics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/hr.py`

[ ] `LOGIC-198` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/admin/routers/hr.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-ADMI` — 1 float-for-money signal(s); first: `amount: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/security.py`

[ ] `LOGIC-199` — 1 float-for-money signal(s); first: `amount: float | None`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/admin/routers/security.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 4 float-for-money signal(s); first: `min_price: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/catalog.py`

[ ] `LOGIC-200` — 4 float-for-money signal(s); first: `min_price: float | None`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/catalog.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/comms.py`

[ ] `LOGIC-201` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/comms.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 6 float-for-money signal(s); first: `order_total: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/promotions.py`

[ ] `LOGIC-203` — 6 float-for-money signal(s); first: `order_total: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/routers/promotions.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-CUST` — 3 float-for-money signal(s); first: `total: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/serializers/customer_serializers.py`

[ ] `LOGIC-204` — 3 float-for-money signal(s); first: `total: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/customer/serializers/customer_serializers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `min_price: float | None`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/catalog.py`

[ ] `LOGIC-205` — 2 float-for-money signal(s); first: `min_price: float | None`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/catalog.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/country.py`

[ ] `LOGIC-206` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/country.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `salary: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr.py`

[ ] `LOGIC-208` — 2 float-for-money signal(s); first: `salary: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/hr.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `salary: Optional[float]`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/hr/schemas.py`

[ ] `LOGIC-209` — 2 float-for-money signal(s); first: `salary: Optional[float]`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/hr/schemas.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/routers/suppliers.py`

[ ] `LOGIC-211` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/routers/suppliers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-EMPL` — 2 float-for-money signal(s); first: `gross_amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/employee/serializers/employee_serializers.py`

[ ] `LOGIC-212` — 2 float-for-money signal(s); first: `gross_amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/employee/serializers/employee_serializers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-LOGI` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/logistics/routers/logistics.py`

[ ] `LOGIC-213` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/logistics/routers/logistics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 1 float-for-money signal(s); first: `total_revenue: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/analytics.py`

[ ] `LOGIC-214` — 1 float-for-money signal(s); first: `total_revenue: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/analytics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 4 float-for-money signal(s); first: `base_price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/logistics.py`

[ ] `LOGIC-216` — 4 float-for-money signal(s); first: `base_price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/routers/logistics.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-MODULES-SUPP` — 3 float-for-money signal(s); first: `total: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/serializers/supplier_serializers.py`

[ ] `LOGIC-217` — 3 float-for-money signal(s); first: `total: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/modules/supplier/serializers/supplier_serializers.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 2 float-for-money signal(s); first: `"price_min": round(base * 0.75, 3),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/ai_variant_config.py`

[ ] `LOGIC-218` — 2 float-for-money signal(s); first: `"price_min": round(base * 0.75, 3),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/ai_variant_config.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 9 float-for-money signal(s); first: `current_price: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/price_intelligence.py`

[ ] `LOGIC-220` — 9 float-for-money signal(s); first: `current_price: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/price_intelligence.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/recommendation.py`

[ ] `LOGIC-221` — 1 float-for-money signal(s); first: `"support": round(freq / total_orders, 6) if total_orders > 0 else 0.0,`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/recommendation.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/search.py`

[ ] `LOGIC-222` — 4 float-for-money signal(s); first: `parsed["min_price"] = float(match.group(1))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/search.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-AI` — 3 float-for-money signal(s); first: `"positive": round(sentiment_counts["positive"] / total, 4),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/sentiment.py`

[ ] `LOGIC-223` — 3 float-for-money signal(s); first: `"positive": round(sentiment_counts["positive"] / total, 4),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ai/sentiment.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-BG` — 3 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/bg_removal/bg_removal_service.py`

[ ] `LOGIC-224` — 3 float-for-money signal(s); first: `total = float(h * w) if h * w else 1.0`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/bg_removal/bg_removal_service.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` — 1 float-for-money signal(s); first: `return float(psutil.virtual_memory().total / 1024 / 1024)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/memory_management__br_08_.py`

[ ] `LOGIC-225` — 1 float-for-money signal(s); first: `return float(psutil.virtual_memory().total / 1024 / 1024)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/image/bg_remover/memory_management__br_08_.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` — 1 float-for-money signal(s); first: `white_balance_strength: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-226` — 1 float-for-money signal(s); first: `white_balance_strength: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/image/free_image_tools.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-IM` — 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/ocr.py`

[ ] `LOGIC-227` — 3 float-for-money signal(s); first: `result["total"] = float(match.group(1).replace(",", ""))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/image/ocr.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-OC` — 2 float-for-money signal(s); first: `"amount": float(amt),`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ocr/ocr_parser.py`

[ ] `LOGIC-228` — 2 float-for-money signal(s); first: `"amount": float(amt),`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/ocr/ocr_parser.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-QR` — 1 float-for-money signal(s); first: `amount: float`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/qr/qr_generator.py`

[ ] `LOGIC-232` — 1 float-for-money signal(s); first: `amount: float`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/qr/qr_generator.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-SH` — 5 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/shipping/shipping_calculator.py`

[ ] `LOGIC-233` — 5 float-for-money signal(s); first: `key=lambda x: (not x.get("available", False), x.get("total", float("inf")))`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/shipping/shipping_calculator.py | head -20`

##### `WP2-FLOAT-MONEY-BACKEND-PROVIDERS-VO` — 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)`

- **cluster:** `CLUSTER-float-money` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/voice/voice_to_text.py`

[ ] `LOGIC-234` — 1 float-for-money signal(s); first: `result["amount"] = float(amount_str)`
    - do: Convert to Decimal and use kernel.money rounding helpers
    - verify: `grep -nE 'float\(|Float|: float' backend/providers/voice/voice_to_text.py | head -20`

##### `WP2-HANDOVER` — 10 of 10 handover/takeover function(s) are missing at least one safety guarantee

- **cluster:** `CLUSTER-handover` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains`

[ ] `WF-handover-unguarded` — 10 of 10 handover/takeover function(s) are missing at least one safety guarantee
    - do: route every transfer through a single HandoverService that asserts permission, writes the audit record, emits a notification, and is idempotent on (object, from, to)
    - verify: `grep -rn 'handover\|takeover' backend/domains | wc -l`

##### `WP2-HTTP-CSP` — 3 place(s) default a CORS/CSP origin to localhost

- **cluster:** `CLUSTER-http-csp` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `SEC-localhost-origin-default` — 3 place(s) default a CORS/CSP origin to localhost
    - do: require the origin in production; fail closed when frontend_url is unset
    - verify: `grep -rn 'localhost:3000\|localhost:8000' backend/middleware`

##### `WP2-INTERACTION-FORM` — 465 of 743 text input(s) have no label, aria-label or id association

- **cluster:** `CLUSTER-interaction-form` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src`

[ ] `IX-input-label` — 465 of 743 text input(s) have no label, aria-label or id association
    - do: pair each input with a <label htmlFor>, or add aria-label
    - verify: `npx axe http://localhost:3100 --tags wcag2a,wcag2aa`

##### `WP2-INTERACTION-MODAL` — 26 of 27 modal/drawer implementations have no focus management

- **cluster:** `CLUSTER-interaction-modal` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `frontend/web_app/src`

[ ] `IX-modal-focus` — 26 of 27 modal/drawer implementations have no focus management
    - do: use a headless dialog primitive (Radix Dialog / Headless UI) or add onOpenAutoFocus + a Tab sentinel
    - verify: `npx playwright test e2e/a11y --tags wcag2a`

##### `WP2-INTERACTION-STATE` — 138 empty or console-only catch handler(s)

- **cluster:** `CLUSTER-interaction-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `frontend/web_app/src`

[ ] `IX-error-swallow` — 138 empty or console-only catch handler(s)
    - do: replace with the error toast / ErrorBoundary path; enable `@typescript-eslint/no-empty` and `no-console` in CI
    - verify: `grep -rEn 'catch\s*(\([^)]*\))?\s*\{\s*\}' frontend/web_app/src --include=*.tsx | wc -l`

##### `WP2-LAW-CONFIG` — Law 84 (Typed feature flags) violated: 138 raw os.getenv read(s)

- **cluster:** `CLUSTER-law-config` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-084` — Law 84 (Typed feature flags) violated: 138 raw os.getenv read(s)
    - do: Fix Law-84 violation: Typed feature flags

##### `WP2-N-PLUS-1` — 304/397 relationship() declarations omit lazy=

- **cluster:** `CLUSTER-n-plus-1` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/`

[ ] `DB-010` — 304/397 relationship() declarations omit lazy=
    - do: Add lazy="selectin" to the relationship declarations
    - verify: `grep -rn 'relationship(' backend/domains | grep -v 'lazy=' | head`

##### `WP2-OFFSET-PAGINATION` — 89 OFFSET pagination usage(s) (sample: .offset(safe_offset))

- **cluster:** `CLUSTER-offset-pagination` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `DB-012` — 89 OFFSET pagination usage(s) (sample: .offset(safe_offset))
    - do: Switch the hot lists to cursor pagination
    - verify: `grep -n '.offset(' backend/domains/accounts/services/auth/auth_service.py`

##### `WP2-ORPHAN-FEATURE` — 224 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.cart.read, accounts.car

- **cluster:** `CLUSTER-orphan-feature` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/`

[ ] `FEAT-003` — 224 orphan feature atom(s) defined but never gated (e.g. accounts.address.set_default, accounts.audit.read, accounts.ca…
    - do: Gate the atoms or delete them from the catalog

##### `WP2-PII-LOGS` — 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc))

- **cluster:** `CLUSTER-pii-logs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `OBS-005` — 8 log statement(s) may include PII/secrets (sample: logger.error("Failed to send password reset email: %s", exc))
    - do: Mask or drop PII fields before logging

##### `WP2-PROVIDER-CONFIG` — 13 provider module(s) read secrets via raw os.getenv

- **cluster:** `CLUSTER-provider-config` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-006` — 13 provider module(s) read secrets via raw os.getenv
    - do: Move the reads into typed config

##### `WP2-PROVIDER-HEALTH` — 88/93 provider modules lack health_check()

- **cluster:** `CLUSTER-provider-health` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-005` — 88/93 provider modules lack health_check()
    - do: Add BaseProvider.health_check() implementations

##### `WP2-PROVIDER-TIMEOUT` — 62/93 provider modules declare no timeout

- **cluster:** `CLUSTER-provider-timeout` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-007` — 62/93 provider modules declare no timeout
    - do: Add explicit timeouts to HTTP/SDK calls

##### `WP2-QUALITY-ASSURANCE` — no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach

- **cluster:** `CLUSTER-quality-assurance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains`

[ ] `QA-mechanisms-absent` — no implementation found for: product_inspection, proof_of_delivery, supplier_scorecard, sla_breach
    - do: model each missing mechanism (table + service + event) and gate the downstream transition on it
    - verify: `grep -rn 'class .*Inspection\|proof_of_delivery\|supplier_score' backend/domains`

##### `WP2-RAW-GETENV` — 130 raw os.getenv/os.environ read(s) in production paths (top: providers=65, infrastructure=41, domains=13, middleware=8, jobs=3)

- **cluster:** `CLUSTER-raw-getenv` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `OPS-016` — 130 raw os.getenv/os.environ read(s) in production paths (top: providers=65, infrastructure=41, domains=13, middleware=…
    - do: Move each variable into typed settings

##### `WP2-ROOT-DISCIPLINE` — 109 temp/debug/health-test file(s) at backend root: _audit_boot_check.py, _tmp_add_ce.py, _tmp_check_gl.py, _tmp_check_gl2.py, _tmp_check_gl

- **cluster:** `CLUSTER-root-discipline` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `FILE-001` — 109 temp/debug/health-test file(s) at backend root: _audit_boot_check.py, _tmp_add_ce.py, _tmp_check_gl.py, _tmp_check_…
    - do: Delete the temp/debug scripts (they also embed secrets), keep one test runner
    - verify: `ls backend/_tmp_*.py backend/health_test_*.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` — 1 silent except block(s); first at line 69: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/public_security_registration_service.py`

[ ] `LOGIC-052` — 1 silent except block(s); first at line 69: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/accounts/services/auth/public_security_registration_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 743: pass-only: except AttributeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/ports.py`

[ ] `LOGIC-062` — 1 silent except block(s); first at line 743: pass-only: except AttributeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/ports.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-063` — 1 silent except block(s); first at line 75: truly-silent: except (ValueError, IndexError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/data_import_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 87: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/finance_ai_service.py`

[ ] `LOGIC-064` — 1 silent except block(s); first at line 87: pass-only: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/finance_ai_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 5 silent except block(s); first at line 7529: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `LOGIC-005` — 5 silent except block(s); first at line 7529: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/ledger/general_ledger.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 2 silent except block(s); first at line 1111: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-025` — 2 silent except block(s); first at line 1111: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/payments/gateway_tap.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 1 silent except block(s); first at line 3407: truly-silent: except HTTPException as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-065` — 1 silent except block(s); first at line 3407: truly-silent: except HTTPException as exc:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/payments/payment_engine.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-FINA` — 2 silent except block(s); first at line 693: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-026` — 2 silent except block(s); first at line 693: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/finance/services/payments/payment_orchestrator.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 78: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/core/kms_encryption.py`

[ ] `LOGIC-076` — 1 silent except block(s); first at line 78: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/security/services/core/kms_encryption.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 44: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/detection/public_security_detection_service.py`

[ ] `LOGIC-077` — 1 silent except block(s); first at line 44: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/security/services/detection/public_security_detection_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 5 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-008` — 5 silent except block(s); first at line 102: pass-only: except (json.JSONDecodeError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/security/services/fraud/fraud_detection_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SECU` — 1 silent except block(s); first at line 30: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/security_provider_helpers.py`

[ ] `LOGIC-075` — 1 silent except block(s); first at line 30: pass-only: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/security/services/security_provider_helpers.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 9 silent except block(s); first at line 1431: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-001` — 9 silent except block(s); first at line 1431: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/health/supplier_health.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 3 silent except block(s); first at line 518: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-019` — 3 silent except block(s); first at line 518: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 2 silent except block(s); first at line 139: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_verify_service.py`

[ ] `LOGIC-032` — 2 silent except block(s); first at line 139: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/orders/supplier_orders_verify_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-078` — 1 silent except block(s); first at line 237: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_product_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 5 silent except block(s); first at line 280: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-009` — 5 silent except block(s); first at line 280: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_products.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 1 silent except block(s); first at line 203: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products_service.py`

[ ] `LOGIC-079` — 1 silent except block(s); first at line 203: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/products/supplier_products_service.py`

##### `WP2-SILENT-EXCEPT-BACKEND-DOMAINS-SUPP` — 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-010` — 4 silent except block(s); first at line 437: truly-silent: except (TypeError, ValueError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/suppliers/services/supplier_shared.py`

##### `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 3 silent except block(s); first at line 49: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/security/dependencies.py`

[ ] `LOGIC-021` — 3 silent except block(s); first at line 49: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/security/dependencies.py`

##### `WP2-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 26: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/security/kms_integration.py`

[ ] `LOGIC-085` — 1 silent except block(s); first at line 26: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/security/kms_integration.py`

##### `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 1 silent except block(s); first at line 88: pass-only: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/finance_ai.py`

[ ] `LOGIC-088` — 1 silent except block(s); first at line 88: pass-only: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/ai/finance_ai.py`

##### `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-FI` — 1 silent except block(s); first at line 128: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/finance/bank_api.py`

[ ] `LOGIC-090` — 1 silent except block(s); first at line 128: truly-silent: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/finance/bank_api.py`

##### `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` — 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/generic.py`

[ ] `LOGIC-046` — 2 silent except block(s); first at line 25: truly-silent: except (json.JSONDecodeError, ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/payments/generic.py`

##### `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-PA` — 2 silent except block(s); first at line 141: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paypal.py`

[ ] `LOGIC-047` — 2 silent except block(s); first at line 141: truly-silent: except (TypeError, ValueError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/payments/paypal.py`

##### `WP2-SILENT-EXCEPT-BACKEND-PROVIDERS-SE` — 1 silent except block(s); first at line 102: truly-silent: except (httpx.HTTPError, ValueError, KeyError) as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/security/watchlist.py`

[ ] `LOGIC-101` — 1 silent except block(s); first at line 102: truly-silent: except (httpx.HTTPError, ValueError, KeyError) as exc:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/security/watchlist.py`

##### `WP2-TABLE-GOVERNANCE` — 0 table(s) lack audit timestamps and 2 lack soft delete

- **cluster:** `CLUSTER-table-governance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains`

[ ] `DB-missing-governance-columns` — 0 table(s) lack audit timestamps and 2 lack soft delete
    - do: inherit the mixins (or set them on the declarative base) instead of declaring columns per model; add a compliance test over Base.metadata
    - verify: `pytest backend/tests/architecture -k compliance`

##### `WP2-TABLE-RELATION` — 304 of 390 relationship() calls omit lazy=

- **cluster:** `CLUSTER-table-relation` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/infrastructure/database`

[ ] `DB-relationship-loading` — 304 of 390 relationship() calls omit lazy=
    - do: set lazy='raise' on the declarative base and annotate each relationship with 'selectin' or 'joined'
    - verify: `grep -rEc 'relationship\(' backend/domains --include=*.py | awk -F: '$2>0' | wc -l`

##### `WP2-WORKFLOW-RUNTIME` — 20 of 38 Celery task(s) are defined but never registered in a beat schedule

- **cluster:** `CLUSTER-workflow-runtime` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/jobs/celery_app.py`

[ ] `WF-unscheduled-tasks` — 20 of 38 Celery task(s) are defined but never registered in a beat schedule
    - do: add a beat_schedule entry per recurring task, or document the task as event-triggered and delete the unused decoration
    - verify: `cd backend && celery -A celery_app inspect conf | grep -A40 beat`

_This wave has 345 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 3 · Close coverage, quality and performance defects

#### Work packages in wave 3 (489)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP3-FE-TYPE-ESCAPE` | 25 | 25 | 0 | 0 | 25.0 | 22 type-safety escape(s) (`@ts-ignore` / `as any`) in application source |
| `WP3-LAW-NOT-STATICALLY-VERIFIABLE` | 25 | 1 | 0 | 0 | 62.5 | Law 315 (Operations) is not verifiable from source: Log aggregation |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` | 25 | 1 | 0 | 0 | 25.0 | 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy= |
| `WP3-ALLOWLIST` | 20 | 1 | 0 | 0 | 50.0 | allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.mod… |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 20 | 1 | 0 | 0 | 20.0 | 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default |
| `WP3-LAW-GAP-CHECKABLE` | 19 | 1 | 0 | 0 | 114.0 | 5 law(s) in 'Technology' have no check but ARE decidable from source: 108: SQLite in dev, 116: Email via SMTP, 117: SMS… |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 18 | 1 | 0 | 0 | 18.0 | 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 17 | 1 | 0 | 0 | 17.0 | 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy= |
| `WP3-FILE-TOO-LONG` | 16 | 16 | 0 | 0 | 96.0 | file has 4561 lines (split candidate) |
| `WP3-JOB-RESILIENCE` | 14 | 14 | 0 | 0 | 35.0 | celery task module with no DLQ reference |
| `WP3-ROUTER-BUSINESS-LOGIC` | 11 | 11 | 0 | 0 | 27.5 | router contains 8 branch statements (business logic signal) |
| `WP3-LAW-TEST-ISOLATION` | 10 | 2 | 0 | 0 | 10.0 | test mutates process-global state with no cleanup in scope: os.environ["APP_ENV"] = app_env |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 10 | 1 | 0 | 0 | 10.0 | 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy= |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 9 | 1 | 0 | 0 | 22.5 | 17 function(s) in this file duplicate `backend/domains/logistics/services/partners/logistics_pricing_service.py` (norma… |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 9 | 1 | 0 | 0 | 9.0 | 1x rel lazy in table `categories`: relationship `products` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 9 | 1 | 0 | 0 | 9.0 | 2x rel lazy in table `fraud_events`: relationship `user` has no lazy= |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 9 | 1 | 0 | 0 | 9.0 | 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default |
| `WP3-VERSION-DRIFT` | 9 | 2 | 0 | 0 | 9.0 | `dompurify: ^3.3.3` does not satisfy pinned `3.4.0` |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 8 | 1 | 0 | 0 | 20.0 | 4 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_logistics_operations_service.py` (n… |
| `WP3-TEST-NO-ASSERT` | 8 | 8 | 0 | 0 | 20.0 | test file contains no assertions |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 8 | 1 | 0 | 0 | 8.0 | 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy= |
| `WP3-MIGRATION-DOWNGRADE` | 7 | 7 | 0 | 0 | 7.0 | empty/missing downgrade() |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 6 | 1 | 0 | 0 | 6.0 | 1x rel lazy in table `user_sessions`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 6 | 1 | 0 | 0 | 6.0 | 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy= |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 6 | 1 | 0 | 0 | 6.0 | 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` | 6 | 1 | 0 | 0 | 6.0 | 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default |
| `WP3-DUPLICATE-FILE` | 5 | 5 | 0 | 0 | 12.5 | byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 5 | 1 | 0 | 0 | 5.0 | 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy= |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 0 | 10.0 | 15 function(s) in this file duplicate `backend/domains/logistics/services/partners/service.py` (normalized AST): `looku… |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 4 | 1 | 0 | 0 | 4.0 | 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 4 | 1 | 0 | 0 | 4.0 | 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` | 4 | 1 | 0 | 0 | 4.0 | 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy= |
| `WP3-TF-SCHEMA-UNKNOWN` | 4 | 1 | 0 | 0 | 4.0 | 1x schema unknown in table `payment_methods`: schema `payments` is not canonical |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 0 | 0 | 4.0 | 1x timestamp default in table `announcements`: `updated_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 4 | 1 | 0 | 0 | 4.0 | 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 0 | 0 | 4.0 | 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` | 4 | 1 | 0 | 0 | 4.0 | 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default |
| `WP3-DESIGN-PRIMITIVES` | 3 | 2 | 0 | 0 | 11.0 | 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-FINA` | 3 | 1 | 0 | 0 | 7.5 | 10 function(s) in this file duplicate `backend/domains/finance/services/data_import_service.py` (normalized AST): `crea… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 3 | 1 | 0 | 0 | 7.5 | 4 function(s) in this file duplicate `backend/domains/customers/services/cart_write_service.py` (normalized AST): `get_… |
| `WP3-ENV-UNDECLARED` | 3 | 3 | 0 | 0 | 3.0 | env var `OTEL_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK |
| `WP3-FE-DEBUG` | 3 | 3 | 0 | 0 | 3.0 | 3 console/debugger statement(s) left in application source |
| `WP3-ROUTER-EMPTY` | 3 | 3 | 0 | 0 | 7.5 | file lives in routers/ but declares zero endpoint decorators |
| `WP3-RUNBOOKS` | 3 | 3 | 0 | 0 | 7.5 | no deploy runbook found |
| `WP3-SUPPLY-CHAIN` | 3 | 3 | 0 | 0 | 3.0 | workflow declares no `permissions:` block |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 3 | 1 | 0 | 0 | 3.0 | 1x rel lazy in table `addresses`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 3 | 1 | 0 | 0 | 3.0 | 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 0 | 0 | 3.0 | 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` | 3 | 1 | 0 | 0 | 3.0 | 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 0 | 0 | 3.0 | 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 0 | 0 | 3.0 | 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 3 | 1 | 0 | 0 | 3.0 | 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 3 | 1 | 0 | 0 | 3.0 | 17x rel lazy in table `country_configs`: relationship `communications` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 3 | 1 | 0 | 0 | 3.0 | 1x rel lazy in table `coupons`: relationship `country` has no lazy= |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 2 | 1 | 0 | 0 | 5.0 | 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 2 | 1 | 0 | 0 | 5.0 | 4 function(s) in this file duplicate `backend/domains/logistics/services/geo/map_service.py` (normalized AST): `get_cit… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 2 | 1 | 0 | 0 | 5.0 | 3 function(s) in this file duplicate `backend/domains/catalog/services/categories/categories_service.py` (normalized AS… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 2 | 1 | 0 | 0 | 5.0 | 11 function(s) in this file duplicate `backend/infrastructure/database/permission_service.py` (normalized AST): `list_c… |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 0 | 0 | 2.0 | 14 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 0 | 0 | 2.0 | 50 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 2 | 1 | 0 | 0 | 2.0 | 13 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-LAW-STRUCTURE` | 2 | 1 | 0 | 0 | 2.0 | Law 12 (15 domains) violated: extra domain(s): media, payments |
| `WP3-TF-MISSING-IS-DELETED` | 2 | 1 | 0 | 0 | 2.0 | 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted` |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 0 | 2.0 | 2x rel lazy in table `referrals`: relationship `referrer` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `payout_rules`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` | 2 | 1 | 0 | 0 | 2.0 | 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` | 2 | 1 | 0 | 0 | 2.0 | 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy= |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 2 | 1 | 0 | 0 | 2.0 | 1x timestamp default in table `direct_chat_rooms`: `updated_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 2 | 1 | 0 | 0 | 2.0 | 2x timestamp default in table `country_configs`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` | 2 | 1 | 0 | 0 | 2.0 | 2x timestamp default in table `referrals`: `created_at` uses Python-side default |
| `WP3-AP-EMPTY-HANDLER-PASS` | 1 | 1 | 0 | 0 | 1.0 | Empty handler (pass): 5 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270` |
| `WP3-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` | 1 | 1 | 0 | 0 | 1.0 | Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3… |
| `WP3-BASE-IMAGE` | 1 | 1 | 0 | 0 | 1.0 | dev database image `postgres:18-alpine` (documented: postgres:16-alpine) |
| `WP3-CACHE-COVERAGE` | 1 | 1 | 0 | 0 | 2.5 | cache references (157) below list-endpoint count (479) |
| `WP3-COLOR-DRIFT` | 1 | 1 | 0 | 0 | 6.0 | 302 inline `style={...}` prop(s) across 76 files; inline colour cannot be themed |
| `WP3-COUNT-QUERIES` | 1 | 1 | 0 | 0 | 2.5 | 308 `.count()` calls (expensive on large tables) |
| `WP3-COVERAGE-ROUTE` | 1 | 1 | 0 | 0 | 1.0 | 3 spec file(s) navigate to paths that no longer exist in the app router |
| `WP3-DB-POOL` | 1 | 1 | 0 | 0 | 1.0 | asyncpg statement_cache_size=0 not set |
| `WP3-DEEP-NESTING` | 1 | 1 | 0 | 0 | 2.5 | 91 function(s) exceed 4 nesting levels (max seen 17) |
| `WP3-DOCS` | 1 | 1 | 0 | 0 | 2.5 | SETUP.md missing |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-AUDI` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) in this file duplicate `backend/domains/audit/services/data_residency_service.py` (normalized AST): `get_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/catalog/services/ai_upload_service.py` (normalized AST): `_prepro… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST):… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/country/services/country_dropdown_service.py` (normalized AST): `… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/accounts/services/addresses/addresses_service.py` (normalized AST… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST):… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 6 function(s) in this file duplicate `backend/domains/catalog/services/search/search_service.py` (normalized AST): `_bu… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 11 function(s) in this file duplicate `backend/domains/analytics/services/aggregation/command_center_service.py` (norma… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/governance/services/admin/admin_service.py` (normalized AST): `ad… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/audit/services/compliance_engine.py` (normalized AST): `validate_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/country/services/core/country_service.py` (normalized AST): `get_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_locations_service.py` (normaliz… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) in this file duplicate `backend/domains/logistics/services/core/service.py` (normalized AST): `admin_emai… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_service.py` (normalized AST): `_ser… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/logistics/services/sla/service.py` (normalized AST): `get_public_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) in this file duplicate `backend/domains/logistics/services/tracking/service.py` (normalized AST): `calcul… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/serializers.py` (normalized AST): `serialize_address` |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/catalog/services/admin_catalog_orders_service.py` (normalized AST… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) in this file duplicate `backend/domains/customers/services/cart_service.py` (normalized AST): `_resolve_v… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 6 function(s) in this file duplicate `backend/domains/orders/services/admin_orders_service.py` (normalized AST): `updat… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/catalog/services/categories/admin_categories_service.py` (normali… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/customer_coupons_create_service.py` (normalized AST): `del… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/services/packing/service.py` (normalized AST): `_get_order… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `add_banner_if_mi… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/promotions/services/coins/coin_service.py` (normalized AST): `_ge… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 6 function(s) in this file duplicate `backend/domains/promotions/services/promotion_admin_write_service.py` (normalized… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) in this file duplicate `backend/domains/governance/services/risk/flat_risk_service.py` (normalized AST):… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 11 function(s) in this file duplicate `backend/domains/orders/services/disputes/service.py` (normalized AST): `_seriali… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `list_my_document… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/accounts/services/permissions/permission_service.py` (normalized… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/domains/catalog/services/categories/category_tree.py` (normalized AST): `… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/infrastructure/messaging/ws_manager.py` (normalized AST): `_broadcast_to_… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-MIDDLEWARE-R` | 1 | 1 | 0 | 0 | 2.5 | 6 function(s) in this file duplicate `backend/middleware/middleware_helpers.py` (normalized AST): `as_paginated_respons… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-MODULES-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 1 function(s) in this file duplicate `backend/modules/logistics/routers/accounts.py` (normalized AST): `list_sessions_r… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) in this file duplicate `backend/jobs/mcp_marketplace_server.py` (normalized AST): `_pagination_payload`,… |
| `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AS` | 1 | 1 | 0 | 0 | 2.5 | 8 function(s) in this file duplicate `backend/jobs/async_workers.py` (normalized AST): `remove_background_async`, `batc… |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/accounting` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/analytics` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/audit-logs` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/bank-accounts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/banners` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/barcode` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/catalog` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/categories` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/chat` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/coc` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/command-center/alerts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/command-center/fraud` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/command-center/headlines/create` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/command-center/headlines` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/command-center` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/commission` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/comms-test` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/communication` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/countries/[code]/staff` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/countries` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/coupons` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/dashboard` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/disputes` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/email` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/employees` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/ess` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/exports` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/finance` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/flash-sales` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/hr` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/inventory-alerts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/invoices` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/logistics-partners` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/logistics` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/moderation` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/orders` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/organization` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/payments` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/payouts/background-jobs` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/payouts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/payroll` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/permissions` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/product-verification` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/products` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/promotions` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/resolution` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/returns` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/staff` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/supplier-documents` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/suppliers` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/tickets/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/tickets` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/treasury` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/users` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `admin/video` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `archive` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `auth/callback` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `brand` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `chatbot` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `contact` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `customer/(auth)/login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/(auth)/login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/attendance` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/dashboard` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/documents` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/leaves` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/notifications` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/payroll` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/performance` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/profile` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/schedule` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/training` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/workspace` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `employee/workspace/tasks` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/(auth)/login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/(auth)/register` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/analytics` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/dashboard` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/payouts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/profile` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/routes` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/scan` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partner/shipments` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partners/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logistics-partners` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `logo-animation` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `meet/[room]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `newsletter/preferences` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `newsletter/unsubscribe` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `offers` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `orders/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `products/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `products/category` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `profile/referrals` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `r/[code]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `register` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `reset-password` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `returns/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier-storefront/[slug]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/(auth)/login` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/(auth)/register` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/analytics` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/batch-upload` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/bulk` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/commission` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/credibility` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/dashboard` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/disputes` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/documents` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/guide` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/inventory` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/invoices` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/labels/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/labels` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/list-product` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/logistics` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/notification-preferences` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/orders/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/orders` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/payouts` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/products/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/products/add` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/products` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/profile` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/regions` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/reports` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/returns` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/support` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/terms` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/upload/bg-compare` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/upload` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `supplier/videos/upload` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `suppliers/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `suppliers` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `tickets/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `tracking/[id]` has no `error.tsx` boundary |
| `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | route `verify-email` has no `error.tsx` boundary |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 12 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 12 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 4 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 16 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 9 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 30 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 34 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 31 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 6 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 24 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 1 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 25 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 4 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 14 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 36 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 15 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 14 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 18 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 15 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 2 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 7 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 6 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 66 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 7 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 30 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 4 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 3 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 2 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 5 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 28 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 raw Tailwind palette class(es) bypass the semantic token scale |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 7 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 9 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 6 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 5 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 9 hardcoded hex colour(s) outside the token layer |
| `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` | 1 | 1 | 0 | 0 | 1.0 | 8 hardcoded hex colour(s) outside the token layer |
| `WP3-FEATURE-GATE` | 1 | 1 | 0 | 0 | 2.5 | 146 declared feature(s) are never referenced by any gate |
| `WP3-HTTP-CSP` | 1 | 1 | 0 | 0 | 1.0 | the CSP uses the deprecated `report-uri` directive |
| `WP3-HTTP-HEADERS` | 1 | 1 | 0 | 0 | 1.0 | the security middleware emits X-XSS-Protection (1 site(s)) |
| `WP3-INTERACTION-BUTTON` | 1 | 1 | 0 | 0 | 1.0 | 2 icon-only button(s) expose no accessible name |
| `WP3-INTERACTION-MODAL` | 1 | 1 | 0 | 0 | 1.0 | 23 of 27 modal implementations do not close on Escape |
| `WP3-LAW-DOCS` | 1 | 1 | 0 | 0 | 1.0 | Law 248 (Runbooks) violated: 0 doc file(s) under docs/ |
| `WP3-LAW-FRONTEND-CONTRACT` | 1 | 1 | 0 | 0 | 1.0 | tsconfig does not enable strict mode (strict=false), so the type checker will not catch nullability or implicit-any def… |
| `WP3-LAW-GIT-HYGIENE` | 1 | 1 | 0 | 0 | 1.0 | no CODEOWNERS or branch-protection document, so required review is not recorded anywhere in the repository |
| `WP3-LAW-MIGRATION` | 1 | 1 | 0 | 0 | 1.0 | Law 27 (Delete temp scripts) violated: 105 temp/debug file(s) at backend root |
| `WP3-LAW-PERFORMANCE` | 1 | 1 | 0 | 0 | 1.0 | Law 222 (Keyset pagination) violated: 88 OFFSET usage(s) |
| `WP3-LAW-UNATTRIBUTED` | 1 | 1 | 0 | 0 | 2.5 | 133 law(s) are enforced by a check but no finding cites them, so no result is attributable to them (41% of the benchmar… |
| `WP3-LONG-FUNCTION-BACKEND-CONFIG-PY` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 10 function(s) >50 lines; longest sample `authenticate_password` = 59 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `record_consent` = 67 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `list_products` = 119 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `send_message` = 58 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_score_product` = 55 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `create_partner` = 73 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `create_banner` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SECU` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `get_supplier_orders` = 141 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines |
| `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines |
| `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines |
| `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines |
| `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines |
| `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines |
| `WP3-LONG-FUNCTION-BACKEND-MAIN-PY` | 1 | 1 | 0 | 0 | 2.5 | 2 function(s) >50 lines; longest sample `health_deps` = 52 lines |
| `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines |
| `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines |
| `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines |
| `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `create_order` = 79 lines |
| `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` | 1 | 1 | 0 | 0 | 2.5 | 3 function(s) >50 lines; longest sample `create_payment_page` = 89 lines |
| `WP3-ORPHAN-JOB` | 1 | 1 | 0 | 0 | 2.5 | 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler |
| `WP3-ORPHAN-PROVIDER` | 1 | 1 | 0 | 0 | 1.0 | 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_varia… |
| `WP3-PACKAGE-MANAGER` | 1 | 1 | 0 | 0 | 1.0 | non-canonical lockfile `package-lock.json` present |
| `WP3-PRINT-LOGGING` | 1 | 1 | 0 | 0 | 2.5 | 6 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159) |
| `WP3-PROVIDER-EXTRA` | 1 | 1 | 0 | 0 | 1.0 | provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py,… |
| `WP3-PUBLIC-BY-DESIGN` | 1 | 1 | 0 | 0 | 2.5 | 9 endpoint(s) are unauthenticated by design (1 authentication entry point, 8 liveness probe); sample: backend/modules/c… |
| `WP3-READ-REPLICA` | 1 | 1 | 0 | 0 | 1.0 | read-replica engine exists but `get_read_db` is never used by domains |
| `WP3-RLS` | 1 | 1 | 0 | 0 | 1.0 | RLS script does not FORCE row level security |
| `WP3-SEARCH-INDEX` | 1 | 1 | 0 | 0 | 1.0 | 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%")) |
| `WP3-SELECT-STAR` | 1 | 1 | 0 | 0 | 1.0 | 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version"))) |
| `WP3-SILENT-EXCEPT-BACKEND-CONFIG-PY` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 937: truly-silent: except AttributeError: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 2.5 | 6 silent except block(s); first at line 3080: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 54: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 219: pass-only: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 454: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 166: truly-silent: except ValueError: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 191: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 480: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 444: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 43: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 97: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 120: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 85: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 6 silent except block(s); first at line 1439: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 355: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 508: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 5 silent except block(s); first at line 211: pass-only: except AttributeError: |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError): |
| `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 527: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 188: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 174: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError): |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 4 silent except block(s); first at line 18: truly-silent: except Exception: # noqa: BLE001 - Valkey may be unavailable… |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 599: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 92: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 323: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 22: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 132: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 57: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 110: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 7 silent except block(s); first at line 67: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 91: pass-only: except RuntimeError: |
| `WP3-SILENT-EXCEPT-BACKEND-JOBS-VIDEO-T` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 104: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 351: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-MAIN-PY` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 199: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 245: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 424: truly-silent: except ValueError: |
| `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` | 1 | 1 | 0 | 0 | 2.5 | 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError: |
| `WP3-SILENT-EXCEPT-BACKEND-MODULES-ADMI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 203: pass-only: except WebSocketDisconnect: |
| `WP3-SILENT-EXCEPT-BACKEND-MODULES-CUST` | 1 | 1 | 0 | 0 | 2.5 | 3 silent except block(s); first at line 160: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 231: pass-only: except OSError: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 288: truly-silent: except json.JSONDecodeError: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 148: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 127: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 39: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 245: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 158: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 312: truly-silent: except Exception as exc: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 119: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 288: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 30: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 4 silent except block(s); first at line 95: truly-silent: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 513: truly-silent: except (ValueError, TypeError): |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 24: pass-only: except Exception: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 44: truly-silent: except ValueError: |
| `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` | 1 | 1 | 0 | 0 | 2.5 | 2 silent except block(s); first at line 99: truly-silent: except UnicodeDecodeError: |
| `WP3-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` | 1 | 1 | 0 | 0 | 2.5 | 1 silent except block(s); first at line 33: truly-silent: except Exception: |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `otp_codes`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 1.0 | 3x rel lazy in table `messages`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `country_basics`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `country_economics`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `country_legals`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `country_taxes`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` | 1 | 1 | 0 | 0 | 1.0 | 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ORDE` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `order_items`: relationship `order` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy= |
| `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy= |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 1.0 | 1x timestamp default in table `messages`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `news_articles`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `country_basics`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `country_economics`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `country_legals`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` | 1 | 1 | 0 | 0 | 1.0 | 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default |
| `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` | 1 | 1 | 0 | 0 | 1.0 | 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default |

##### `WP3-FE-TYPE-ESCAPE` — 22 type-safety escape(s) (`@ts-ignore` / `as any`) in application source

- **cluster:** `CLUSTER-fe-type-escape` · **steps:** 25 (0 closed) · **files:** 25 · **est.:** 25.0h
- **files:** `frontend/web_app/src/app/admin/finance/_components/AccountingPanels.tsx`, `frontend/web_app/src/app/admin/countries/components/CountriesTabProps.ts`, `frontend/web_app/src/app/admin/payments/page.tsx`, `frontend/web_app/src/lib/logger.ts`, `frontend/web_app/src/app/supplier/products/add/page.tsx`, `frontend/web_app/src/types/framer-motion.d.ts`, `frontend/web_app/src/app/admin/countries/page.tsx`, `frontend/web_app/src/app/admin/ess/page.tsx`

[ ] `TEST-009` — 22 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/admin/finance/_components/AccountingPanels.tsx`
[ ] `TEST-010` — 13 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/admin/countries/components/CountriesTabProps.ts`
[ ] `TEST-011` — 11 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/admin/payments/page.tsx`
[ ] `TEST-012` — 8 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/lib/logger.ts`
[ ] `TEST-013` — 7 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/supplier/products/add/page.tsx`
[ ] `TEST-014` — 7 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/types/framer-motion.d.ts`
[ ] `TEST-015` — 6 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/admin/countries/page.tsx`
[ ] `TEST-016` — 6 type-safety escape(s) (`@ts-ignore` / `as any`) in application source
    - do: narrow the type instead of suppressing the check
    - verify: `grep -cE '@ts-ignore|as any' frontend/web_app/src/app/admin/ess/page.tsx`
    - … and 17 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-fe-type-escape`)

##### `WP3-LAW-NOT-STATICALLY-VERIFIABLE` — Law 315 (Operations) is not verifiable from source: Log aggregation

- **cluster:** `CLUSTER-law-not-statically-verifiable` · **steps:** 25 (0 closed) · **files:** 1 · **est.:** 62.5h
- **files:** `_most_imp_docx/ARCHITECTURE_STACK.md`

[ ] `LAWCOV-001` — Law 315 (Operations) is not verifiable from source: Log aggregation
    - do: verify by other means -- requires a running log pipeline
[ ] `LAWCOV-002` — Law 316 (Operations) is not verifiable from source: Dashboards
    - do: verify by other means -- requires the observability stack to be deployed
[ ] `LAWCOV-003` — Law 317 (Operations) is not verifiable from source: Alerting tiers
    - do: verify by other means -- requires the paging system to be configured
[ ] `LAWCOV-004` — Law 318 (Operations) is not verifiable from source: Capacity planning
    - do: verify by other means -- requires production traffic history
[ ] `LAWCOV-005` — Law 319 (Operations) is not verifiable from source: Release mgmt
    - do: verify by other means -- requires the release system, not the source tree
[ ] `LAWCOV-006` — Law 322 (Operations) is not verifiable from source: Cost allocation
    - do: verify by other means -- requires billing data, not source
[ ] `LAWCOV-007` — Law 324 (Operations) is not verifiable from source: Change mgmt
    - do: verify by other means -- process, not observable from source
[ ] `LAWCOV-008` — Law 325 (Operations) is not verifiable from source: Sustainability
    - do: verify by other means -- organisational, not observable from source
    - … and 17 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-law-not-statically-verifiable`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-HR-M` — 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 25 (0 closed) · **files:** 1 · **est.:** 25.0h
- **files:** `backend/domains/hr/models/employee_models.py`

[ ] `TF-179` — 1x rel lazy in table `physical_id_cards`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on physical_id_cards
[ ] `TF-180` — 1x rel lazy in table `dynamic_qr_sessions`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on dynamic_qr_sessions
[ ] `TF-181` — 1x rel lazy in table `employee_biometrics`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_biometrics
[ ] `TF-182` — 1x rel lazy in table `geo_fence_logs`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on geo_fence_logs
[ ] `TF-183` — 1x rel lazy in table `org_units`: relationship `parent` has no lazy=
    - do: Fix rel-lazy on org_units
[ ] `TF-184` — 18x rel lazy in table `employees`: relationship `office` has no lazy=
    - do: Fix rel-lazy on employees
[ ] `TF-185` — 1x rel lazy in table `employee_attendances`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_attendances
[ ] `TF-186` — 1x rel lazy in table `employee_work_logs`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_work_logs
    - … and 17 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-ALLOWLIST` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.models.suppliers: Suppli

- **cluster:** `CLUSTER-allowlist` · **steps:** 20 (0 closed) · **files:** 1 · **est.:** 50.0h
- **files:** `backend/DOMAIN_ALLOWLIST.yaml`

[ ] `ARCH-004` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.comms.mod…
    - do: Add the removal date or remove the entry
[ ] `ARCH-005` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_engine -> domains.governanc…
    - do: Add the removal date or remove the entry
[ ] `ARCH-006` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.comms.mo…
    - do: Add the removal date or remove the entry
[ ] `ARCH-007` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governan…
    - do: Add the removal date or remove the entry
[ ] `ARCH-008` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.catalog.…
    - do: Add the removal date or remove the entry
[ ] `ARCH-009` — allowlist entry without dated removal plan: `domains.finance.services.commission.commission_service -> domains.governan…
    - do: Add the removal date or remove the entry
[ ] `ARCH-010` — allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> fastapi: HTTPException…
    - do: Add the removal date or remove the entry
[ ] `ARCH-011` — allowlist entry without dated removal plan: `domains.finance.services.cash_management_service -> modules.admin.routers.…
    - do: Add the removal date or remove the entry
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-allowlist`)

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 20 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/finance/models/general_ledger.py`

[ ] `TF-147` — 1x timestamp default in table `transaction_ledgers`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on transaction_ledgers
[ ] `TF-148` — 1x timestamp default in table `supplier_settlements`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on supplier_settlements
[ ] `TF-149` — 1x timestamp default in table `account_balances`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on account_balances
[ ] `TF-150` — 1x timestamp default in table `invoices`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on invoices
[ ] `TF-151` — 1x timestamp default in table `cash_accounts`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on cash_accounts
[ ] `TF-152` — 1x timestamp default in table `treasury_accounts`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on treasury_accounts
[ ] `TF-153` — 1x timestamp default in table `payout_batches`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on payout_batches
[ ] `TF-154` — 1x timestamp default in table `bank_mapping_rules`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on bank_mapping_rules
    - … and 12 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-timestamp-default`)

##### `WP3-LAW-GAP-CHECKABLE` — 5 law(s) in 'Technology' have no check but ARE decidable from source: 108: SQLite in dev, 116: Email via SMTP, 117: SMS / WhatsApp via self-

- **cluster:** `CLUSTER-law-gap-checkable` · **steps:** 19 (0 closed) · **files:** 1 · **est.:** 114.0h
- **files:** `_most_imp_docx/ARCHITECTURE_STACK.md`

[ ] `LAWCOV-026` — 5 law(s) in 'Technology' have no check but ARE decidable from source: 108: SQLite in dev, 116: Email via SMTP, 117: SMS…
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-027` — 4 law(s) in 'Operations' have no check but ARE decidable from source: 312: A/B testing, 314: IaC, 320: DevX, 321: Doc f…
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-028` — 4 law(s) in 'Security' have no check but ARE decidable from source: 284: Zero-trust, 285: CSP, 286: SRI, 292: License c…
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-029` — 3 law(s) in 'Web App' have no check but ARE decidable from source: 183: Theme/styling, 184: Types, 185: Utils
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-030` — 3 law(s) in 'Performance' have no check but ARE decidable from source: 223: Connection pooling, 224: Query optimization…
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-031` — 2 law(s) in 'Resilience' have no check but ARE decidable from source: 304: DR, 309: Dep monitoring
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-032` — 2 law(s) in 'Infrastructure' have no check but ARE decidable from source: 76: Session lifecycle, 149: Session lifecycle
    - do: add a check, or declare the law non-enforceable with a reason
[ ] `LAWCOV-033` — 2 law(s) in 'Provider' have no check but ARE decidable from source: 125: Degrade gracefully, 131: Mock in tests
    - do: add a check, or declare the law non-enforceable with a reason
    - … and 11 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-law-gap-checkable`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 18 (0 closed) · **files:** 1 · **est.:** 18.0h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `TF-048` — 2x rel lazy in table `ticket_messages`: relationship `ticket` has no lazy=
    - do: Fix rel-lazy on ticket_messages
[ ] `TF-050` — 1x rel lazy in table `announcements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on announcements
[ ] `TF-053` — 1x rel lazy in table `help_categories`: relationship `country` has no lazy=
    - do: Fix rel-lazy on help_categories
[ ] `TF-055` — 3x rel lazy in table `proxy_channels`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_channels
[ ] `TF-056` — 5x rel lazy in table `proxy_sessions`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_sessions
[ ] `TF-057` — 4x rel lazy in table `proxy_messages`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_messages
[ ] `TF-058` — 4x rel lazy in table `proxy_call_logs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on proxy_call_logs
[ ] `TF-059` — 1x rel lazy in table `employee_communication_threads`: relationship `country` has no lazy=
    - do: Fix rel-lazy on employee_communication_threads
    - … and 10 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 17 (0 closed) · **files:** 1 · **est.:** 17.0h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `TF-109` — 1x rel lazy in table `country_feature_flags`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_feature_flags
[ ] `TF-111` — 3x rel lazy in table `country_staff_assignments`: relationship `user` has no lazy=
    - do: Fix rel-lazy on country_staff_assignments
[ ] `TF-113` — 1x rel lazy in table `country_config_versions`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_config_versions
[ ] `TF-115` — 1x rel lazy in table `supplier_kyc_requirements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on supplier_kyc_requirements
[ ] `TF-117` — 1x rel lazy in table `logistics_partner_kyc_requirements`: relationship `country` has no lazy=
    - do: Fix rel-lazy on logistics_partner_kyc_requirements
[ ] `TF-118` — 1x rel lazy in table `country_commission_rates`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_commission_rates
[ ] `TF-120` — 1x rel lazy in table `country_localizations`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_localizations
[ ] `TF-121` — 1x rel lazy in table `country_payment_aliases`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_payment_aliases
    - … and 9 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-FILE-TOO-LONG` — file has 4561 lines (split candidate)

- **cluster:** `CLUSTER-file-too-long` · **steps:** 16 (0 closed) · **files:** 16 · **est.:** 96.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`, `backend/domains/country/services/core/country_service.py`, `backend/domains/finance/services/ledger/general_ledger.py`, `backend/domains/finance/services/payments/gateway_tap.py`, `backend/domains/finance/services/payments/payment_engine.py`, `backend/domains/finance/services/payments/payment_orchestrator.py`, `backend/domains/finance/services/payouts/payout_batch_service.py`, `backend/domains/logistics/services/core/service.py`

[ ] `FILE-079` — file has 4561 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-080` — file has 1970 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-081` — file has 17790 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-082` — file has 1858 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-083` — file has 4721 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-084` — file has 1775 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-085` — file has 4150 lines (split candidate)
    - do: Split into capability-scoped modules
[ ] `FILE-086` — file has 3258 lines (split candidate)
    - do: Split into capability-scoped modules
    - … and 8 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-file-too-long`)

##### `WP3-JOB-RESILIENCE` — celery task module with no DLQ reference

- **cluster:** `CLUSTER-job-resilience` · **steps:** 14 (0 closed) · **files:** 14 · **est.:** 35.0h
- **files:** `backend/jobs/accrual_reversal.py`, `backend/jobs/ai_tasks.py`, `backend/jobs/bank_statement_importer.py`, `backend/jobs/data_retention.py`, `backend/jobs/email_tasks.py`, `backend/jobs/fraud_monitoring.py`, `backend/jobs/fx_revaluation.py`, `backend/jobs/ghost_order_detector.py`

[ ] `OPS-001` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-002` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-003` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-004` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-005` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-006` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-007` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
[ ] `OPS-008` — celery task module with no DLQ reference
    - do: Route terminal failures to the DLQ
    - … and 6 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-job-resilience`)

##### `WP3-ROUTER-BUSINESS-LOGIC` — router contains 8 branch statements (business logic signal)

- **cluster:** `CLUSTER-router-business-logic` · **steps:** 11 (0 closed) · **files:** 11 · **est.:** 27.5h
- **files:** `backend/modules/admin/routers/comms.py`, `backend/modules/admin/routers/permissions.py`, `backend/modules/admin/routers/staff.py`, `backend/modules/customer/routers/accounts.py`, `backend/modules/customer/routers/promotions.py`, `backend/modules/employee/routers/comms.py`, `backend/modules/employee/routers/finance.py`, `backend/modules/employee/routers/hr.py`

[ ] `ARCH-163` — router contains 8 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-164` — router contains 12 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-166` — router contains 16 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-167` — router contains 9 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-168` — router contains 17 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-170` — router contains 22 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-171` — router contains 31 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
[ ] `ARCH-172` — router contains 7 branch statements (business logic signal)
    - do: Extract branching logic into the domain service
    - … and 3 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-router-business-logic`)

##### `WP3-LAW-TEST-ISOLATION` — test mutates process-global state with no cleanup in scope: os.environ["APP_ENV"] = app_env

- **cluster:** `CLUSTER-law-test-isolation` · **steps:** 10 (0 closed) · **files:** 2 · **est.:** 10.0h
- **files:** `backend/tests/architecture/test_middleware_order.py`, `backend/tests/security/test_encryption.py`

[ ] `DECLLAW-004` — test mutates process-global state with no cleanup in scope: os.environ["APP_ENV"] = app_env
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-005` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_SALT"] = "abcd"
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-006` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-007` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_SALT"] = "notahexstringbutlong…
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-008` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-009` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-010` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
[ ] `DECLLAW-011` — test mutates process-global state with no cleanup in scope: os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
    - do: use monkeypatch.setenv/delenv, or a fixture that restores the previous value
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-law-test-isolation`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 10 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/comms/models/chat.py`

[ ] `TF-034` — 1x rel lazy in table `entity_chat_threads`: relationship `messages` has no lazy=
    - do: Fix rel-lazy on entity_chat_threads
[ ] `TF-035` — 3x rel lazy in table `video_rooms`: relationship `participants` has no lazy=
    - do: Fix rel-lazy on video_rooms
[ ] `TF-036` — 2x rel lazy in table `video_room_participants`: relationship `room` has no lazy=
    - do: Fix rel-lazy on video_room_participants
[ ] `TF-038` — 1x rel lazy in table `direct_chat_rooms`: relationship `messages` has no lazy=
    - do: Fix rel-lazy on direct_chat_rooms
[ ] `TF-039` — 2x rel lazy in table `group_chat_members`: relationship `room` has no lazy=
    - do: Fix rel-lazy on group_chat_members
[ ] `TF-040` — 2x rel lazy in table `entity_chat_messages`: relationship `thread` has no lazy=
    - do: Fix rel-lazy on entity_chat_messages
[ ] `TF-041` — 2x rel lazy in table `video_room_recordings`: relationship `room` has no lazy=
    - do: Fix rel-lazy on video_room_recordings
[ ] `TF-042` — 2x rel lazy in table `direct_chat_messages`: relationship `room` has no lazy=
    - do: Fix rel-lazy on direct_chat_messages
    - … and 2 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 17 function(s) in this file duplicate `backend/domains/logistics/services/partners/logistics_pricing_service.py` (normalized AST): `_parse_p

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 22.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `FILE-007` — 17 function(s) in this file duplicate `backend/domains/logistics/services/partners/logistics_pricing_service.py` (norma…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/partners/logistics_pricing_service.py`
[ ] `FILE-010` — 13 function(s) in this file duplicate `backend/domains/logistics/services/core/shipment_service.py` (normalized AST): `…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/core/shipment_service.py`
[ ] `FILE-012` — 11 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_service.py` (normalized AST): `rev…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/core/admin_service.py`
[ ] `FILE-019` — 6 function(s) in this file duplicate `backend/domains/logistics/services/partners/partner_service.py` (normalized AST):…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/partners/partner_service.py`
[ ] `FILE-035` — 4 function(s) in this file duplicate `backend/domains/logistics/services/core/location_service.py` (normalized AST): `_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/core/location_service.py`
[ ] `FILE-042` — 3 function(s) in this file duplicate `backend/domains/logistics/services/fulfillment/service.py` (normalized AST): `_pr…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/fulfillment/service.py`
[ ] `FILE-056` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/zone_service.py` (normalized AST): `_seri…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/core/zone_service.py`
[ ] `FILE-069` — 1 function(s) in this file duplicate `backend/domains/logistics/services/partners/contract_service.py` (normalized AST)…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/logistics.py` and `backend/domains/logistics/services/partners/contract_service.py`
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-duplicate-symbol`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 1x rel lazy in table `categories`: relationship `products` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 9.0h
- **files:** `backend/domains/catalog/models/products.py`

[ ] `TF-024` — 1x rel lazy in table `categories`: relationship `products` has no lazy=
    - do: Fix rel-lazy on categories
[ ] `TF-025` — 4x rel lazy in table `products`: relationship `category_rel` has no lazy=
    - do: Fix rel-lazy on products
[ ] `TF-026` — 1x rel lazy in table `reviews`: relationship `product` has no lazy=
    - do: Fix rel-lazy on reviews
[ ] `TF-027` — 1x rel lazy in table `wishlist_items`: relationship `product` has no lazy=
    - do: Fix rel-lazy on wishlist_items
[ ] `TF-028` — 1x rel lazy in table `wishlists`: relationship `product` has no lazy=
    - do: Fix rel-lazy on wishlists
[ ] `TF-029` — 1x rel lazy in table `product_variants`: relationship `product` has no lazy=
    - do: Fix rel-lazy on product_variants
[ ] `TF-030` — 1x rel lazy in table `product_videos`: relationship `product` has no lazy=
    - do: Fix rel-lazy on product_videos
[ ] `TF-031` — 2x rel lazy in table `product_filter_metadatas`: relationship `category` has no lazy=
    - do: Fix rel-lazy on product_filter_metadatas
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `fraud_events`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 9.0h
- **files:** `backend/domains/security/models/fraud.py`

[ ] `TF-238` — 2x rel lazy in table `fraud_events`: relationship `user` has no lazy=
    - do: Fix rel-lazy on fraud_events
[ ] `TF-239` — 1x rel lazy in table `device_fingerprints`: relationship `user` has no lazy=
    - do: Fix rel-lazy on device_fingerprints
[ ] `TF-240` — 1x rel lazy in table `return_abuse_patterns`: relationship `user` has no lazy=
    - do: Fix rel-lazy on return_abuse_patterns
[ ] `TF-241` — 1x rel lazy in table `ip_account_linkages`: relationship `user` has no lazy=
    - do: Fix rel-lazy on ip_account_linkages
[ ] `TF-242` — 1x rel lazy in table `fraud_scoring_logs`: relationship `user` has no lazy=
    - do: Fix rel-lazy on fraud_scoring_logs
[ ] `TF-243` — 2x rel lazy in table `fraud_cases`: relationship `assignee` has no lazy=
    - do: Fix rel-lazy on fraud_cases
[ ] `TF-244` — 3x rel lazy in table `fraud_case_assignments`: relationship `case` has no lazy=
    - do: Fix rel-lazy on fraud_case_assignments
[ ] `TF-245` — 2x rel lazy in table `dlp_violations`: relationship `sender` has no lazy=
    - do: Fix rel-lazy on dlp_violations
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-rel-lazy`)

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 9 (0 closed) · **files:** 1 · **est.:** 9.0h
- **files:** `backend/domains/country/models/country_enhancements.py`

[ ] `TF-108` — 1x timestamp default in table `country_feature_flags`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_feature_flags
[ ] `TF-110` — 1x timestamp default in table `country_staff_assignments`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_staff_assignments
[ ] `TF-112` — 1x timestamp default in table `country_config_versions`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_config_versions
[ ] `TF-114` — 1x timestamp default in table `supplier_kyc_requirements`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on supplier_kyc_requirements
[ ] `TF-116` — 1x timestamp default in table `logistics_partner_kyc_requirements`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_partner_kyc_requirements
[ ] `TF-119` — 1x timestamp default in table `country_localizations`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_localizations
[ ] `TF-122` — 1x timestamp default in table `country_legal_contracts`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_legal_contracts
[ ] `TF-125` — 1x timestamp default in table `country_cities`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on country_cities
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-tf-timestamp-default`)

##### `WP3-VERSION-DRIFT` — `dompurify: ^3.3.3` does not satisfy pinned `3.4.0`

- **cluster:** `CLUSTER-version-drift` · **steps:** 9 (0 closed) · **files:** 2 · **est.:** 9.0h
- **files:** `frontend/web_app/package.json`, `frontend/shared/package.json`

[ ] `TECH-001` — `dompurify: ^3.3.3` does not satisfy pinned `3.4.0`
    - do: Upgrade dompurify to 3.4.0
[ ] `TECH-002` — `jspdf: ^4.1.0` does not satisfy pinned `4.2.1`
    - do: Upgrade jspdf to 4.2.1
[ ] `TECH-003` — `@testing-library/react: ^16.3.2` does not satisfy pinned `16.3.0`
    - do: Upgrade @testing-library/react to 16.3.0
[ ] `TECH-005` — `jest: ^29.0.0` does not satisfy pinned `29.7.0`
    - do: Upgrade jest to 29.7.0
[ ] `TECH-006` — `ts-jest: ^29.0.0` does not satisfy pinned `29.2.5`
    - do: Upgrade ts-jest to 29.2.5
[ ] `TECH-007` — `typescript: ~5.9` does not satisfy pinned `5.9.3`
    - do: Upgrade typescript to 5.9.3
[ ] `TECH-009` — `jest: ^29.0.0` does not satisfy pinned `29.7.0`
    - do: Upgrade jest to 29.7.0
[ ] `TECH-010` — `react: ^19.2.17` does not satisfy pinned `19.2.8`
    - do: Upgrade react to 19.2.8
    - … and 1 more step(s) in this package; full list in `_zozi_audit/logs/plan.json` (filter by cluster `CLUSTER-version-drift`)

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_logistics_operations_service.py` (normalized AST): `get_

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 8 (0 closed) · **files:** 1 · **est.:** 20.0h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `FILE-027` — 4 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_logistics_operations_service.py` (n…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/admin_logistics_operations_service.py`
[ ] `FILE-028` — 4 function(s) in this file duplicate `backend/domains/country/services/core/country_service.py` (normalized AST): `get_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/country/services/core/country_service.py`
[ ] `FILE-039` — 3 function(s) in this file duplicate `backend/domains/logistics/services/core/service.py` (normalized AST): `admin_emai…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/service.py`
[ ] `FILE-048` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_service.py` (normalized AST): `…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/logistics_service.py`
[ ] `FILE-049` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_locations_service.py` (normaliz…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/logistics_locations_service.py`
[ ] `FILE-050` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_engine.py` (normalized AST): `c…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/logistics_engine.py`
[ ] `FILE-061` — 1 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_write_service.py` (normalized A…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/logistics_write_service.py`
[ ] `FILE-062` — 1 function(s) in this file duplicate `backend/domains/logistics/services/core/country_communication_service.py` (normal…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/service.py` and `backend/domains/logistics/services/core/country_communication_service.py`

##### `WP3-TEST-NO-ASSERT` — test file contains no assertions

- **cluster:** `CLUSTER-test-no-assert` · **steps:** 8 (0 closed) · **files:** 8 · **est.:** 20.0h
- **files:** `backend/tests/architecture/test_law19_through_law31.py`, `backend/tests/architecture/test_law2_router_no_db_writes.py`, `backend/tests/domains/accounts/test_accounts.py`, `backend/tests/domains/analytics/test_analytics.py`, `backend/tests/domains/promotions/test_promotions.py`, `backend/tests/domains/test_mapper_configuration.py`, `tests/middleware/test_webhook_ip_whitelist.py`, `tests/security/test_vault.py`

[ ] `TEST-001` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-002` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-003` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-004` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-005` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-006` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-007` — test file contains no assertions
    - do: Add outcome assertions
[ ] `TEST-008` — test file contains no assertions
    - do: Add outcome assertions

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 8 (0 closed) · **files:** 1 · **est.:** 8.0h
- **files:** `backend/domains/country/models/country_control.py`

[ ] `TF-098` — 3x rel lazy in table `shift_handover_logs`: relationship `user` has no lazy=
    - do: Fix rel-lazy on shift_handover_logs
[ ] `TF-099` — 1x rel lazy in table `payment_orchestrator_syncs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on payment_orchestrator_syncs
[ ] `TF-100` — 2x rel lazy in table `supplier_onboarding_syncs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on supplier_onboarding_syncs
[ ] `TF-101` — 1x rel lazy in table `data_residency_records`: relationship `country` has no lazy=
    - do: Fix rel-lazy on data_residency_records
[ ] `TF-102` — 1x rel lazy in table `country_map_configs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_map_configs
[ ] `TF-103` — 1x rel lazy in table `shop_warehouse_locations`: relationship `country` has no lazy=
    - do: Fix rel-lazy on shop_warehouse_locations
[ ] `TF-104` — 2x rel lazy in table `logistics_partner_locations`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_partner_locations
[ ] `TF-105` — 2x rel lazy in table `parcel_location_trackers`: relationship `parcel` has no lazy=
    - do: Fix rel-lazy on parcel_location_trackers

##### `WP3-MIGRATION-DOWNGRADE` — empty/missing downgrade()

- **cluster:** `CLUSTER-migration-downgrade` · **steps:** 7 (0 closed) · **files:** 7 · **est.:** 7.0h
- **files:** `backend/alembic/versions/2026_08_08_21_02-02ebc285f66f_merge_divergent_heads_20260806_0009_and_.py`, `backend/alembic/versions/2026_08_21_0005-20260821_crosscutting_domains.py`, `backend/alembic/versions/2026_08_21_0006-20260821_customer_comm_logistics_media.py`, `backend/alembic/versions/2026_08_21_0007-20260821_user_referral_to_customer.py`, `backend/alembic/versions/2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py`, `backend/alembic/versions/2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py`, `backend/alembic/versions/2026_10_03_0010_merge_20261002_0001__20261003_0001__20261003_0009.py`

[ ] `MIG-003` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-004` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-005` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-006` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-007` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-009` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility
[ ] `MIG-010` — empty/missing downgrade()
    - do: Implement downgrade() or document irreversibility

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `user_sessions`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/accounts/models/user.py`

[ ] `TF-008` — 1x rel lazy in table `user_sessions`: relationship `user` has no lazy=
    - do: Fix rel-lazy on user_sessions
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

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `TF-208` — 5x rel lazy in table `logistics_partners`: relationship `profile` has no lazy=
    - do: Fix rel-lazy on logistics_partners
[ ] `TF-210` — 1x rel lazy in table `logistics_partner_profiles`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_partner_profiles
[ ] `TF-212` — 4x rel lazy in table `logistics_partner_service_areas`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_partner_service_areas
[ ] `TF-214` — 2x rel lazy in table `logistics_pricing_profiles`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_pricing_profiles
[ ] `TF-216` — 2x rel lazy in table `logistics_vehicle_rules`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_vehicle_rules
[ ] `TF-218` — 2x rel lazy in table `logistics_category_pricing_rules`: relationship `partner` has no lazy=
    - do: Fix rel-lazy on logistics_category_pricing_rules

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/logistics/models/logistics_entities.py`

[ ] `TF-209` — 1x timestamp default in table `logistics_partner_profiles`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_partner_profiles
[ ] `TF-211` — 1x timestamp default in table `logistics_partner_service_areas`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_partner_service_areas
[ ] `TF-213` — 1x timestamp default in table `logistics_pricing_profiles`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_pricing_profiles
[ ] `TF-215` — 1x timestamp default in table `logistics_vehicle_rules`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_vehicle_rules
[ ] `TF-217` — 1x timestamp default in table `logistics_category_pricing_rules`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on logistics_category_pricing_rules
[ ] `TF-219` — 1x timestamp default in table `shipments`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on shipments

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-SUPP` — 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 6 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-249` — 2x timestamp default in table `supplier_profiles`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_profiles
[ ] `TF-252` — 2x timestamp default in table `supplier_documents`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_documents
[ ] `TF-255` — 2x timestamp default in table `supplier_notification_preferences`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_notification_preferences
[ ] `TF-256` — 2x timestamp default in table `supplier_badge_catalogs`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_badge_catalogs
[ ] `TF-257` — 2x timestamp default in table `supplier_badges`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_badges
[ ] `TF-259` — 2x timestamp default in table `supplier_badge_billing_histories`: `created_at` uses Python-side default
    - do: Fix timestamp-default on supplier_badge_billing_histories

##### `WP3-DUPLICATE-FILE` — byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py

- **cluster:** `CLUSTER-duplicate-file` · **steps:** 5 (0 closed) · **files:** 5 · **est.:** 12.5h
- **files:** `backend/domains/finance/exceptions.py`, `backend/domains/governance/exceptions.py`, `backend/domains/orders/serializers.py`, `backend/infrastructure/messaging/ws_manager.py`, `backend/middleware/middleware_helpers.py`

[ ] `FILE-002` — byte-identical duplicate file(s): backend/domains/finance/exceptions.py, backend/domains/finance/services/exceptions.py
    - do: Delete the duplicates and keep one owner
[ ] `FILE-003` — byte-identical duplicate file(s): backend/domains/governance/exceptions.py, backend/domains/governance/services/excepti…
    - do: Delete the duplicates and keep one owner
[ ] `FILE-004` — byte-identical duplicate file(s): backend/domains/orders/serializers.py, backend/domains/orders/schemas/serializers.py
    - do: Delete the duplicates and keep one owner
[ ] `FILE-005` — byte-identical duplicate file(s): backend/infrastructure/messaging/ws_manager.py, backend/infrastructure/utils/websocke…
    - do: Delete the duplicates and keep one owner
[ ] `FILE-006` — byte-identical duplicate file(s): backend/middleware/middleware_helpers.py, backend/middleware/router_helpers.py
    - do: Delete the duplicates and keep one owner

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` — 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 5 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/governance/models/admin.py`

[ ] `TF-173` — 1x rel lazy in table `admin_change_audit_logs`: relationship `admin` has no lazy=
    - do: Fix rel-lazy on admin_change_audit_logs
[ ] `TF-174` — 2x rel lazy in table `badge_billing_records`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on badge_billing_records
[ ] `TF-175` — 1x rel lazy in table `promotion_order_tiers`: relationship `country` has no lazy=
    - do: Fix rel-lazy on promotion_order_tiers
[ ] `TF-176` — 2x rel lazy in table `logistics_cod_remittance_receipts`: relationship `settlement` has no lazy=
    - do: Fix rel-lazy on logistics_cod_remittance_receipts
[ ] `TF-177` — 2x rel lazy in table `employee_expenses`: relationship `employee` has no lazy=
    - do: Fix rel-lazy on employee_expenses

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 15 function(s) in this file duplicate `backend/domains/logistics/services/partners/service.py` (normalized AST): `lookup_city_distance_km`, 

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 10.0h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `FILE-008` — 15 function(s) in this file duplicate `backend/domains/logistics/services/partners/service.py` (normalized AST): `looku…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/service.py` and `backend/domains/logistics/services/partners/service.py`
[ ] `FILE-009` — 14 function(s) in this file duplicate `backend/domains/logistics/services/partners/pricing_service.py` (normalized AST)…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/service.py` and `backend/domains/logistics/services/partners/pricing_service.py`
[ ] `FILE-052` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_logistics_operations_service.py` (n…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/service.py` and `backend/domains/logistics/services/core/admin_logistics_operations_service.py`
[ ] `FILE-064` — 1 function(s) in this file duplicate `backend/domains/logistics/services/partners/blocker_service.py` (normalized AST):…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/service.py` and `backend/domains/logistics/services/partners/blocker_service.py`

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/catalog/models/chart_of_categories.py`

[ ] `TF-017` — 4x rel lazy in table `chart_of_categories`: relationship `parent` has no lazy=
    - do: Fix rel-lazy on chart_of_categories
[ ] `TF-018` — 2x rel lazy in table `product_types`: relationship `coc_category` has no lazy=
    - do: Fix rel-lazy on product_types
[ ] `TF-019` — 2x rel lazy in table `category_attributes`: relationship `product_type` has no lazy=
    - do: Fix rel-lazy on category_attributes
[ ] `TF-020` — 1x rel lazy in table `category_attribute_values`: relationship `attribute` has no lazy=
    - do: Fix rel-lazy on category_attribute_values

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/logistics/models/erp.py`

[ ] `TF-204` — 1x rel lazy in table `purchase_orders`: relationship `lines` has no lazy=
    - do: Fix rel-lazy on purchase_orders
[ ] `TF-205` — 1x rel lazy in table `goods_receipt_notes`: relationship `lines` has no lazy=
    - do: Fix rel-lazy on goods_receipt_notes
[ ] `TF-206` — 1x rel lazy in table `sales_orders`: relationship `lines` has no lazy=
    - do: Fix rel-lazy on sales_orders
[ ] `TF-207` — 1x rel lazy in table `import_shipments`: relationship `lines` has no lazy=
    - do: Fix rel-lazy on import_shipments

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SUPP` — 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/suppliers/models/suppliers.py`

[ ] `TF-250` — 1x rel lazy in table `supplier_profiles`: relationship `user` has no lazy=
    - do: Fix rel-lazy on supplier_profiles
[ ] `TF-253` — 1x rel lazy in table `supplier_documents`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on supplier_documents
[ ] `TF-258` — 2x rel lazy in table `supplier_badges`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on supplier_badges
[ ] `TF-260` — 1x rel lazy in table `supplier_badge_billing_histories`: relationship `supplier` has no lazy=
    - do: Fix rel-lazy on supplier_badge_billing_histories

##### `WP3-TF-SCHEMA-UNKNOWN` — 1x schema unknown in table `payment_methods`: schema `payments` is not canonical

- **cluster:** `CLUSTER-tf-schema-unknown` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/payments/models/payment_models.py`

[ ] `TF-227` — 1x schema unknown in table `payment_methods`: schema `payments` is not canonical
    - do: Fix schema-unknown on payment_methods
[ ] `TF-228` — 1x schema unknown in table `payment_attempts`: schema `payments` is not canonical
    - do: Fix schema-unknown on payment_attempts
[ ] `TF-229` — 1x schema unknown in table `refunds`: schema `payments` is not canonical
    - do: Fix schema-unknown on refunds
[ ] `TF-230` — 1x schema unknown in table `payment_intents`: schema `payments` is not canonical
    - do: Fix schema-unknown on payment_intents

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `announcements`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/comms/models/communication.py`

[ ] `TF-049` — 1x timestamp default in table `announcements`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on announcements
[ ] `TF-052` — 1x timestamp default in table `faqs`: `created_at` uses Python-side default
    - do: Fix timestamp-default on faqs
[ ] `TF-054` — 1x timestamp default in table `proxy_channels`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on proxy_channels
[ ] `TF-068` — 1x timestamp default in table `internal_emails`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on internal_emails

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/comms/models/marketing.py`

[ ] `TF-082` — 1x timestamp default in table `email_campaigns`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on email_campaigns
[ ] `TF-084` — 1x timestamp default in table `email_templates`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on email_templates
[ ] `TF-085` — 1x timestamp default in table `newsletter_subscribers`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on newsletter_subscribers
[ ] `TF-087` — 1x timestamp default in table `email_runtime_configs`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on email_runtime_configs

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/finance/models/commission.py`

[ ] `TF-143` — 2x timestamp default in table `commission_agreements`: `created_at` uses Python-side default
    - do: Fix timestamp-default on commission_agreements
[ ] `TF-144` — 2x timestamp default in table `product_commission_overrides`: `created_at` uses Python-side default
    - do: Fix timestamp-default on product_commission_overrides
[ ] `TF-145` — 2x timestamp default in table `commission_ledger_entries`: `created_at` uses Python-side default
    - do: Fix timestamp-default on commission_ledger_entries
[ ] `TF-146` — 2x timestamp default in table `commission_category_rates`: `created_at` uses Python-side default
    - do: Fix timestamp-default on commission_category_rates

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-FINA` — 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 4 (0 closed) · **files:** 1 · **est.:** 4.0h
- **files:** `backend/domains/finance/models/tax_rules.py`

[ ] `TF-167` — 1x timestamp default in table `payout_rules`: `created_at` uses Python-side default
    - do: Fix timestamp-default on payout_rules
[ ] `TF-169` — 1x timestamp default in table `tax_rules`: `created_at` uses Python-side default
    - do: Fix timestamp-default on tax_rules
[ ] `TF-171` — 1x timestamp default in table `payout_rule_categories`: `created_at` uses Python-side default
    - do: Fix timestamp-default on payout_rule_categories
[ ] `TF-172` — 1x timestamp default in table `payout_rule_products`: `created_at` uses Python-side default
    - do: Fix timestamp-default on payout_rule_products

##### `WP3-DESIGN-PRIMITIVES` — 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive

- **cluster:** `CLUSTER-design-primitives` · **steps:** 3 (0 closed) · **files:** 2 · **est.:** 11.0h
- **files:** `frontend/web_app/src`, `frontend/web_app/src/components/ui`

[ ] `DS-duplicate-markup` — 673 hand-rolled card/input class strings across 166 files duplicate an existing primitive
    - do: replace the duplicated class strings with <Card>/<Input>; the primitive already exists, so this is a mechanical sweep
    - verify: `grep -rlE 'rounded-(xl|2xl) border border-(border|surface)' frontend/web_app/src | wc -l`
[ ] `DS-no-variant-system` — none of the 72 primitives use a variant system (class-variance-authority); variants are raw Record<string, string> maps
    - do: adopt `cva` for Button/Card/Badge/Progress variant maps
    - verify: `grep -rl 'cva(' frontend/web_app/src/components/ui | wc -l`
[ ] `DS-primitive-ref` — 63 of 72 primitives do not forward refs and set no displayName
    - do: wrap each primitive body in forwardRef<HTMLElement, Props> and assign `.displayName`
    - verify: `grep -rL 'forwardRef' frontend/web_app/src/components/ui/*.tsx`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-FINA` — 10 function(s) in this file duplicate `backend/domains/finance/services/data_import_service.py` (normalized AST): `create_import_shipment`, 

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `FILE-015` — 10 function(s) in this file duplicate `backend/domains/finance/services/data_import_service.py` (normalized AST): `crea…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/finance/services/ledger/general_ledger.py` and `backend/domains/finance/services/data_import_service.py`
[ ] `FILE-038` — 3 function(s) in this file duplicate `backend/domains/finance/services/country/supplier_finance_service.py` (normalized…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/finance/services/ledger/general_ledger.py` and `backend/domains/finance/services/country/supplier_finance_service.py`
[ ] `FILE-060` — 1 function(s) in this file duplicate `backend/domains/finance/services/ledger/general_ledger.py` (normalized AST): `bui…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/finance/services/ledger/general_ledger.py` and `backend/domains/finance/services/ledger/general_ledger.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 4 function(s) in this file duplicate `backend/domains/customers/services/cart_write_service.py` (normalized AST): `get_cart_item_by_variant`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 7.5h
- **files:** `backend/domains/orders/services/cart/service.py`

[ ] `FILE-034` — 4 function(s) in this file duplicate `backend/domains/customers/services/cart_write_service.py` (normalized AST): `get_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/cart/service.py` and `backend/domains/customers/services/cart_write_service.py`
[ ] `FILE-054` — 2 function(s) in this file duplicate `backend/domains/orders/services/cart/cart_service__orders.py` (normalized AST): `…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/cart/service.py` and `backend/domains/orders/services/cart/cart_service__orders.py`
[ ] `FILE-068` — 1 function(s) in this file duplicate `backend/domains/customers/services/cart_service.py` (normalized AST): `_resolve_v…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/cart/service.py` and `backend/domains/customers/services/cart_service.py`

##### `WP3-ENV-UNDECLARED` — env var `OTEL_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK

- **cluster:** `CLUSTER-env-undeclared` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `backend/infrastructure/observability/tracing.py`, `backend/infrastructure/observability/error_handler.py`, `backend/providers/security/watchlist.py`

[ ] `ENV-013` — env var `OTEL_DISABLED` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add OTEL_DISABLED to typed settings and .env.example
[ ] `ENV-014` — env var `SENTRY_TRACES_SAMPLE_RATE` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add SENTRY_TRACES_SAMPLE_RATE to typed settings and .env.example
[ ] `ENV-015` — env var `WATCHLIST_API_ALLOWED_HOSTS` read but not declared in .env.example, typed settings or TECHNOLOGY_STACK
    - do: Add WATCHLIST_API_ALLOWED_HOSTS to typed settings and .env.example

##### `WP3-FE-DEBUG` — 3 console/debugger statement(s) left in application source

- **cluster:** `CLUSTER-fe-debug` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `frontend/web_app/src/app/login/LoginClient.tsx`, `frontend/web_app/src/lib/logger.ts`, `frontend/web_app/src/lib/api/country.ts`

[ ] `TEST-034` — 3 console/debugger statement(s) left in application source
    - do: remove the statement or route it through the logger
    - verify: `grep -cE 'console\.(log|debug)|debugger;' frontend/web_app/src/app/login/LoginClient.tsx`
[ ] `TEST-035` — 1 console/debugger statement(s) left in application source
    - do: remove the statement or route it through the logger
    - verify: `grep -cE 'console\.(log|debug)|debugger;' frontend/web_app/src/lib/logger.ts`
[ ] `TEST-036` — 1 console/debugger statement(s) left in application source
    - do: remove the statement or route it through the logger
    - verify: `grep -cE 'console\.(log|debug)|debugger;' frontend/web_app/src/lib/api/country.ts`

##### `WP3-ROUTER-EMPTY` — file lives in routers/ but declares zero endpoint decorators

- **cluster:** `CLUSTER-router-empty` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 7.5h
- **files:** `backend/modules/employee/routers/hr/schemas.py`, `backend/modules/employee/routers/hr/schemas_admin.py`, `backend/modules/finance/routers/cash_management.py`

[ ] `ARCH-174` — file lives in routers/ but declares zero endpoint decorators
    - do: Delete or convert to a service module
[ ] `ARCH-175` — file lives in routers/ but declares zero endpoint decorators
    - do: Delete or convert to a service module
[ ] `ARCH-176` — file lives in routers/ but declares zero endpoint decorators
    - do: Delete or convert to a service module

##### `WP3-RUNBOOKS` — no deploy runbook found

- **cluster:** `CLUSTER-runbooks` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 7.5h
- **files:** `docs/runbooks/deploy.md`, `docs/runbooks/rollback.md`, `docs/runbooks/migration.md`

[ ] `D2P-005` — no deploy runbook found
    - do: Write docs/runbooks/deploy.md
[ ] `D2P-006` — no rollback runbook found
    - do: Write docs/runbooks/rollback.md
[ ] `D2P-007` — no migration runbook found
    - do: Write docs/runbooks/migration.md

##### `WP3-SUPPLY-CHAIN` — workflow declares no `permissions:` block

- **cluster:** `CLUSTER-supply-chain` · **steps:** 3 (0 closed) · **files:** 3 · **est.:** 3.0h
- **files:** `.github/workflows/router-generation.yml`, `.github/workflows/schema-audit.yml`, `.`

[ ] `SC-005` — workflow declares no `permissions:` block
    - do: Add an explicit permissions block (contents: read)
[ ] `SC-006` — workflow declares no `permissions:` block
    - do: Add an explicit permissions block (contents: read)
[ ] `SC-007` — no SBOM artifact found in the repository
    - do: Generate SBOM via Syft/CycloneDX in CI and retain it

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `addresses`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/accounts/models/core.py`

[ ] `TF-001` — 1x rel lazy in table `addresses`: relationship `user` has no lazy=
    - do: Fix rel-lazy on addresses
[ ] `TF-002` — 1x rel lazy in table `carts`: relationship `user` has no lazy=
    - do: Fix rel-lazy on carts
[ ] `TF-003` — 2x rel lazy in table `cart_items`: relationship `user` has no lazy=
    - do: Fix rel-lazy on cart_items

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/accounts/models/onboarding.py`

[ ] `TF-004` — 3x rel lazy in table `onboarding_pipelines`: relationship `user` has no lazy=
    - do: Fix rel-lazy on onboarding_pipelines
[ ] `TF-005` — 1x rel lazy in table `onboarding_steps`: relationship `pipeline` has no lazy=
    - do: Fix rel-lazy on onboarding_steps
[ ] `TF-006` — 1x rel lazy in table `ocr_results`: relationship `document_verification` has no lazy=
    - do: Fix rel-lazy on ocr_results

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/catalog/models/ai_upload.py`

[ ] `TF-014` — 1x rel lazy in table `ai_upload_jobs`: relationship `staging_products` has no lazy=
    - do: Fix rel-lazy on ai_upload_jobs
[ ] `TF-015` — 2x rel lazy in table `ai_staging_products`: relationship `job` has no lazy=
    - do: Fix rel-lazy on ai_staging_products
[ ] `TF-016` — 1x rel lazy in table `ai_staging_variants`: relationship `staging_product` has no lazy=
    - do: Fix rel-lazy on ai_staging_variants

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CATA` — 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/catalog/models/commission.py`

[ ] `TF-021` — 2x rel lazy in table `commission_groups`: relationship `categories` has no lazy=
    - do: Fix rel-lazy on commission_groups
[ ] `TF-022` — 1x rel lazy in table `commission_profiles`: relationship `rules` has no lazy=
    - do: Fix rel-lazy on commission_profiles
[ ] `TF-023` — 2x rel lazy in table `commission_rules`: relationship `profile` has no lazy=
    - do: Fix rel-lazy on commission_rules

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/comms/models/communication_schema_models.py`

[ ] `TF-073` — 3x rel lazy in table `support_tickets`: relationship `replies` has no lazy=
    - do: Fix rel-lazy on support_tickets
[ ] `TF-074` — 2x rel lazy in table `support_ticket_replies`: relationship `ticket` has no lazy=
    - do: Fix rel-lazy on support_ticket_replies
[ ] `TF-075` — 2x rel lazy in table `ticket_attachments`: relationship `ticket_reply` has no lazy=
    - do: Fix rel-lazy on ticket_attachments

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/comms/models/incident.py`

[ ] `TF-077` — 3x rel lazy in table `incident_war_rooms`: relationship `threads` has no lazy=
    - do: Fix rel-lazy on incident_war_rooms
[ ] `TF-078` — 2x rel lazy in table `incident_threads`: relationship `war_room` has no lazy=
    - do: Fix rel-lazy on incident_threads
[ ] `TF-079` — 2x rel lazy in table `incident_action_items`: relationship `war_room` has no lazy=
    - do: Fix rel-lazy on incident_action_items

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/comms/models/marketing.py`

[ ] `TF-080` — 3x rel lazy in table `flash_sale_items`: relationship `flash_sale` has no lazy=
    - do: Fix rel-lazy on flash_sale_items
[ ] `TF-083` — 1x rel lazy in table `email_campaigns`: relationship `recipients` has no lazy=
    - do: Fix rel-lazy on email_campaigns
[ ] `TF-086` — 2x rel lazy in table `campaign_recipients`: relationship `campaign` has no lazy=
    - do: Fix rel-lazy on campaign_recipients

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 17x rel lazy in table `country_configs`: relationship `communications` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/country/models/countries.py`

[ ] `TF-092` — 17x rel lazy in table `country_configs`: relationship `communications` has no lazy=
    - do: Fix rel-lazy on country_configs
[ ] `TF-094` — 3x rel lazy in table `country_communications`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_communications
[ ] `TF-095` — 1x rel lazy in table `country_gateway_credentials`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_gateway_credentials

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `coupons`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 3 (0 closed) · **files:** 1 · **est.:** 3.0h
- **files:** `backend/domains/promotions/models/promotions.py`

[ ] `TF-235` — 1x rel lazy in table `coupons`: relationship `country` has no lazy=
    - do: Fix rel-lazy on coupons
[ ] `TF-236` — 1x rel lazy in table `banners`: relationship `country` has no lazy=
    - do: Fix rel-lazy on banners
[ ] `TF-237` — 2x rel lazy in table `flash_sales`: relationship `country` has no lazy=
    - do: Fix rel-lazy on flash_sales

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_within_fence`, `_chec

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/logistics/services/geo/service.py`

[ ] `FILE-030` — 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/geo/service.py` and `backend/domains/country/services/geo/country_detection.py`
[ ] `FILE-031` — 4 function(s) in this file duplicate `backend/domains/logistics/services/geo/map_service.py` (normalized AST): `get_cit…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/geo/service.py` and `backend/domains/logistics/services/geo/map_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/logistics/services/geo/map_service.py` (normalized AST): `get_cities_for_map`, `get_wa

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/logistics/services/shipping/service.py`

[ ] `FILE-032` — 4 function(s) in this file duplicate `backend/domains/logistics/services/geo/map_service.py` (normalized AST): `get_cit…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/shipping/service.py` and `backend/domains/logistics/services/geo/map_service.py`
[ ] `FILE-065` — 1 function(s) in this file duplicate `backend/domains/logistics/services/geo/service.py` (normalized AST): `get_country…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/shipping/service.py` and `backend/domains/logistics/services/geo/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 3 function(s) in this file duplicate `backend/domains/catalog/services/categories/categories_service.py` (normalized AST): `create_category`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/domains/orders/services/core/misc.py`

[ ] `FILE-043` — 3 function(s) in this file duplicate `backend/domains/catalog/services/categories/categories_service.py` (normalized AS…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/misc.py` and `backend/domains/catalog/services/categories/categories_service.py`
[ ] `FILE-057` — 2 function(s) in this file duplicate `backend/domains/accounts/services/addresses/addresses_service.py` (normalized AST…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/misc.py` and `backend/domains/accounts/services/addresses/addresses_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` — 11 function(s) in this file duplicate `backend/infrastructure/database/permission_service.py` (normalized AST): `list_categories`, `create_c

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 5.0h
- **files:** `backend/infrastructure/security/permission_service.py`

[ ] `FILE-014` — 11 function(s) in this file duplicate `backend/infrastructure/database/permission_service.py` (normalized AST): `list_c…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/infrastructure/security/permission_service.py` and `backend/infrastructure/database/permission_service.py`
[ ] `FILE-075` — 1 function(s) in this file duplicate `backend/domains/accounts/services/permissions/permission_service.py` (normalized…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/infrastructure/security/permission_service.py` and `backend/domains/accounts/services/permissions/permission_service.py`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 14 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `frontend/web_app/src/app/brand/page.tsx`

[ ] `WEB-157` — 14 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/brand/page.tsx`
[ ] `WEB-178` — 11 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/brand/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 50 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `frontend/web_app/src/app/supplier/labels/[id]/page.tsx`

[ ] `WEB-146` — 50 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/supplier/labels/[id]/page.tsx`
[ ] `WEB-195` — 2 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/supplier/labels/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 13 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `frontend/web_app/src/app/supplier/products/add/page.tsx`

[ ] `WEB-159` — 13 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/supplier/products/add/page.tsx`
[ ] `WEB-190` — 4 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/supplier/products/add/page.tsx`

##### `WP3-LAW-STRUCTURE` — Law 12 (15 domains) violated: extra domain(s): media, payments

- **cluster:** `CLUSTER-law-structure` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/`

[ ] `LAW-012` — Law 12 (15 domains) violated: extra domain(s): media, payments
    - do: Fix Law-12 violation: 15 domains
[ ] `LAW-013` — Law 13 (5 modules) violated: extra module(s): finance
    - do: Fix Law-13 violation: 5 modules

##### `WP3-TF-MISSING-IS-DELETED` — 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted`

- **cluster:** `CLUSTER-tf-missing-is_deleted` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/logistics/models/read_models/__init__.py`

[ ] `TF-223` — 1x missing is_deleted in table `shipment_tracking_projections`: table `shipment_tracking_projections` lacks `is_deleted`
    - do: Fix missing-is_deleted on shipment_tracking_projections
[ ] `TF-225` — 1x missing is_deleted in table `partner_performance_projections`: table `partner_performance_projections` lacks `is_del…
    - do: Fix missing-is_deleted on partner_performance_projections

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` — 2x rel lazy in table `referrals`: relationship `referrer` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/customers/models/customer_schema_models.py`

[ ] `TF-140` — 2x rel lazy in table `referrals`: relationship `referrer` has no lazy=
    - do: Fix rel-lazy on referrals
[ ] `TF-142` — 2x rel lazy in table `referral_point_events`: relationship `user` has no lazy=
    - do: Fix rel-lazy on referral_point_events

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-FINA` — 1x rel lazy in table `payout_rules`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/finance/models/tax_rules.py`

[ ] `TF-168` — 1x rel lazy in table `payout_rules`: relationship `country` has no lazy=
    - do: Fix rel-lazy on payout_rules
[ ] `TF-170` — 1x rel lazy in table `tax_rules`: relationship `country` has no lazy=
    - do: Fix rel-lazy on tax_rules

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-SECU` — 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/security/models/security_schema_models.py`

[ ] `TF-247` — 2x rel lazy in table `document_verifications`: relationship `pipeline` has no lazy=
    - do: Fix rel-lazy on document_verifications
[ ] `TF-248` — 2x rel lazy in table `kyc_verifications`: relationship `user` has no lazy=
    - do: Fix rel-lazy on kyc_verifications

##### `WP3-TF-REL-LAZY-BACKEND-RBAC-MODELS-` — 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/rbac/models/permission_entities.py`

[ ] `TF-261` — 1x rel lazy in table `permission_categories`: relationship `permissions` has no lazy=
    - do: Fix rel-lazy on permission_categories
[ ] `TF-262` — 1x rel lazy in table `permissions`: relationship `category` has no lazy=
    - do: Fix rel-lazy on permissions

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `direct_chat_rooms`: `updated_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/comms/models/chat.py`

[ ] `TF-037` — 1x timestamp default in table `direct_chat_rooms`: `updated_at` uses Python-side default
    - do: Fix timestamp-default on direct_chat_rooms
[ ] `TF-043` — 2x timestamp default in table `group_chat_rooms`: `created_at` uses Python-side default
    - do: Fix timestamp-default on group_chat_rooms

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_configs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/country/models/countries.py`

[ ] `TF-091` — 2x timestamp default in table `country_configs`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_configs
[ ] `TF-093` — 1x timestamp default in table `country_communications`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_communications

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CUST` — 2x timestamp default in table `referrals`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 2 (0 closed) · **files:** 1 · **est.:** 2.0h
- **files:** `backend/domains/customers/models/customer_schema_models.py`

[ ] `TF-139` — 2x timestamp default in table `referrals`: `created_at` uses Python-side default
    - do: Fix timestamp-default on referrals
[ ] `TF-141` — 2x timestamp default in table `referral_point_events`: `created_at` uses Python-side default
    - do: Fix timestamp-default on referral_point_events

##### `WP3-AP-EMPTY-HANDLER-PASS` — Empty handler (pass): 5 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270`

- **cluster:** `CLUSTER-ap-empty-handler-pass` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/observability/circuit_breaker.py`

[ ] `AP-004` — Empty handler (pass): 5 occurrence(s); sample `backend/infrastructure/observability/circuit_breaker.py:270`
    - do: Implement or delete the handler

##### `WP3-AP-STUB-FUNCTION-NOTIMPLEMENTEDERR` — Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3551`

- **cluster:** `CLUSTER-ap-stub-function-notimplementederror` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `AP-001` — Stub function (NotImplementedError): 37 occurrence(s); sample `backend/domains/accounts/services/auth/auth_service.py:3…
    - do: Implement or remove the stub

##### `WP3-BASE-IMAGE` — dev database image `postgres:18-alpine` (documented: postgres:16-alpine)

- **cluster:** `CLUSTER-base-image` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `docker-compose.yml`

[ ] `TECH-013` — dev database image `postgres:18-alpine` (documented: postgres:16-alpine)
    - do: Align the compose image with the documented dev database

##### `WP3-CACHE-COVERAGE` — cache references (157) below list-endpoint count (479)

- **cluster:** `CLUSTER-cache-coverage` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/`

[ ] `PERF-002` — cache references (157) below list-endpoint count (479)
    - do: Add cache-aside reads with TTL for catalog/list endpoints

##### `WP3-COLOR-DRIFT` — 302 inline `style={...}` prop(s) across 76 files; inline colour cannot be themed

- **cluster:** `CLUSTER-color-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 6.0h
- **files:** `frontend/web_app/src`

[ ] `DS-inline-style` — 302 inline `style={...}` prop(s) across 76 files; inline colour cannot be themed
    - do: move static colours and spacing out of inline styles into the token layer / utility classes; keep only genuinely dynamic values (measured positions, computed transforms)
    - verify: `grep -rc 'style={{' frontend/web_app/src --include=*.tsx | awk -F: '$2>0' | wc -l`

##### `WP3-COUNT-QUERIES` — 308 `.count()` calls (expensive on large tables)

- **cluster:** `CLUSTER-count-queries` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/`

[ ] `PERF-003` — 308 `.count()` calls (expensive on large tables)
    - do: Remove counts from hot list responses

##### `WP3-COVERAGE-ROUTE` — 3 spec file(s) navigate to paths that no longer exist in the app router

- **cluster:** `CLUSTER-coverage-route` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `_browser_test/tests`

[ ] `FEAT-SPEC-ORPHAN` — 3 spec file(s) navigate to paths that no longer exist in the app router
    - do: delete or repoint the orphaned specs
    - verify: `npx playwright test --list`

##### `WP3-DB-POOL` — asyncpg statement_cache_size=0 not set

- **cluster:** `CLUSTER-db-pool` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `DB-006` — asyncpg statement_cache_size=0 not set
    - do: Pass statement_cache_size=0 in connect_args

##### `WP3-DEEP-NESTING` — 91 function(s) exceed 4 nesting levels (max seen 17)

- **cluster:** `CLUSTER-deep-nesting` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/lifespan.py`

[ ] `LOGIC-295` — 91 function(s) exceed 4 nesting levels (max seen 17)
    - do: Refactor with guard clauses / extracted helpers

##### `WP3-DOCS` — SETUP.md missing

- **cluster:** `CLUSTER-docs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `SETUP.md`

[ ] `D2P-008` — SETUP.md missing
    - do: Document provisioning in SETUP.md

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-AUDI` — 3 function(s) in this file duplicate `backend/domains/audit/services/data_residency_service.py` (normalized AST): `get_residency_config`, `e

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/audit/services/flat_data_residency_service.py`

[ ] `FILE-037` — 3 function(s) in this file duplicate `backend/domains/audit/services/data_residency_service.py` (normalized AST): `get_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/audit/services/flat_data_residency_service.py` and `backend/domains/audit/services/data_residency_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CATA` — 1 function(s) in this file duplicate `backend/domains/catalog/services/ai_upload_service.py` (normalized AST): `_preprocess_for_ai`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/ai_upload_service.py`

[ ] `FILE-059` — 1 function(s) in this file duplicate `backend/domains/catalog/services/ai_upload_service.py` (normalized AST): `_prepro…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/catalog/services/products/ai_upload_service.py` and `backend/domains/catalog/services/ai_upload_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COMM` — 4 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST): `_mark_messages_read`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/websocket_handlers.py`

[ ] `FILE-024` — 4 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST):…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/comms/services/messaging/websocket_handlers.py` and `backend/domains/comms/services/public_comms_status_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-COUN` — 2 function(s) in this file duplicate `backend/domains/country/services/country_dropdown_service.py` (normalized AST): `get_cities_dropdown`,

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/geo/country_maps_service.py`

[ ] `FILE-045` — 2 function(s) in this file duplicate `backend/domains/country/services/country_dropdown_service.py` (normalized AST): `…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/country/services/geo/country_maps_service.py` and `backend/domains/country/services/country_dropdown_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` — 2 function(s) in this file duplicate `backend/domains/accounts/services/addresses/addresses_service.py` (normalized AST): `_normalize_addres

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/customer_router_service.py`

[ ] `FILE-046` — 2 function(s) in this file duplicate `backend/domains/accounts/services/addresses/addresses_service.py` (normalized AST…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/customers/services/customer_router_service.py` and `backend/domains/accounts/services/addresses/addresses_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` — 5 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST): `_mark_messages_read`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/public_comms_status_service.py`

[ ] `FILE-022` — 5 function(s) in this file duplicate `backend/domains/comms/services/public_comms_status_service.py` (normalized AST):…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/customers/services/public_comms_status_service.py` and `backend/domains/comms/services/public_comms_status_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-CUST` — 6 function(s) in this file duplicate `backend/domains/catalog/services/search/search_service.py` (normalized AST): `_build_postgres_tsquery`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `FILE-017` — 6 function(s) in this file duplicate `backend/domains/catalog/services/search/search_service.py` (normalized AST): `_bu…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/customers/services/search_service.py` and `backend/domains/catalog/services/search/search_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` — 11 function(s) in this file duplicate `backend/domains/analytics/services/aggregation/command_center_service.py` (normalized AST): `_fetch_r

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `FILE-011` — 11 function(s) in this file duplicate `backend/domains/analytics/services/aggregation/command_center_service.py` (norma…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/governance/services/command_center/service.py` and `backend/domains/analytics/services/aggregation/command_center_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-GOVE` — 2 function(s) in this file duplicate `backend/domains/governance/services/admin/admin_service.py` (normalized AST): `admin_email_stats`, `ad

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/settings/admin_service.py`

[ ] `FILE-047` — 2 function(s) in this file duplicate `backend/domains/governance/services/admin/admin_service.py` (normalized AST): `ad…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/governance/services/settings/admin_service.py` and `backend/domains/governance/services/admin/admin_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-HR-S` — 4 function(s) in this file duplicate `backend/domains/audit/services/compliance_engine.py` (normalized AST): `validate_work_hours`, `calcula

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/compliance_engine.py`

[ ] `FILE-025` — 4 function(s) in this file duplicate `backend/domains/audit/services/compliance_engine.py` (normalized AST): `validate_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/hr/services/compliance_engine.py` and `backend/domains/audit/services/compliance_engine.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/country/services/core/country_service.py` (normalized AST): `get_country_communication

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/country_communication_service.py`

[ ] `FILE-026` — 4 function(s) in this file duplicate `backend/domains/country/services/core/country_service.py` (normalized AST): `get_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/core/country_communication_service.py` and `backend/domains/country/services/core/country_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_within_fence`, `_chec

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/geo/geo_fence_service.py`

[ ] `FILE-029` — 4 function(s) in this file duplicate `backend/domains/country/services/geo/country_detection.py` (normalized AST): `is_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/geo/geo_fence_service.py` and `backend/domains/country/services/geo/country_detection.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_locations_service.py` (normalized AST): `list_logist

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/geo/logistics_locations_service.py`

[ ] `FILE-051` — 2 function(s) in this file duplicate `backend/domains/logistics/services/core/logistics_locations_service.py` (normaliz…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/geo/logistics_locations_service.py` and `backend/domains/logistics/services/core/logistics_locations_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 3 function(s) in this file duplicate `backend/domains/logistics/services/core/service.py` (normalized AST): `admin_email_stats`, `admin_logi

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `FILE-040` — 3 function(s) in this file duplicate `backend/domains/logistics/services/core/service.py` (normalized AST): `admin_emai…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/admin_logistics_operations_service.py` and `backend/domains/logistics/services/core/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 1 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_service.py` (normalized AST): `_serialize_lp_doc`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/contract_service.py`

[ ] `FILE-063` — 1 function(s) in this file duplicate `backend/domains/logistics/services/core/admin_service.py` (normalized AST): `_ser…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/partners/contract_service.py` and `backend/domains/logistics/services/core/admin_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 4 function(s) in this file duplicate `backend/domains/logistics/services/sla/service.py` (normalized AST): `get_public_holidays`, `get_worki

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/sla/service.py`

[ ] `FILE-033` — 4 function(s) in this file duplicate `backend/domains/logistics/services/sla/service.py` (normalized AST): `get_public_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/sla/service.py` and `backend/domains/logistics/services/sla/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-LOGI` — 5 function(s) in this file duplicate `backend/domains/logistics/services/tracking/service.py` (normalized AST): `calculate_distance`, `get_p

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/tracking/service.py`

[ ] `FILE-023` — 5 function(s) in this file duplicate `backend/domains/logistics/services/tracking/service.py` (normalized AST): `calcul…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/logistics/services/tracking/service.py` and `backend/domains/logistics/services/tracking/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 1 function(s) in this file duplicate `backend/domains/orders/serializers.py` (normalized AST): `serialize_address`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/schemas/serializers.py`

[ ] `FILE-066` — 1 function(s) in this file duplicate `backend/domains/orders/serializers.py` (normalized AST): `serialize_address`
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/schemas/serializers.py` and `backend/domains/orders/serializers.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 2 function(s) in this file duplicate `backend/domains/catalog/services/admin_catalog_orders_service.py` (normalized AST): `create_category`,

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/admin_catalog_orders_service.py`

[ ] `FILE-053` — 2 function(s) in this file duplicate `backend/domains/catalog/services/admin_catalog_orders_service.py` (normalized AST…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/admin_catalog_orders_service.py` and `backend/domains/catalog/services/admin_catalog_orders_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 3 function(s) in this file duplicate `backend/domains/customers/services/cart_service.py` (normalized AST): `_resolve_variant`, `add_to_cart

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/cart/cart_service__orders.py`

[ ] `FILE-041` — 3 function(s) in this file duplicate `backend/domains/customers/services/cart_service.py` (normalized AST): `_resolve_v…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/cart/cart_service__orders.py` and `backend/domains/customers/services/cart_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 6 function(s) in this file duplicate `backend/domains/orders/services/admin_orders_service.py` (normalized AST): `update_status`, `archive_o

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/admin.py`

[ ] `FILE-018` — 6 function(s) in this file duplicate `backend/domains/orders/services/admin_orders_service.py` (normalized AST): `updat…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/admin.py` and `backend/domains/orders/services/admin_orders_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 2 function(s) in this file duplicate `backend/domains/catalog/services/categories/admin_categories_service.py` (normalized AST): `create_cat

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/admin_extra.py`

[ ] `FILE-055` — 2 function(s) in this file duplicate `backend/domains/catalog/services/categories/admin_categories_service.py` (normali…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/core/admin_extra.py` and `backend/domains/catalog/services/categories/admin_categories_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 1 function(s) in this file duplicate `backend/domains/orders/customer_coupons_create_service.py` (normalized AST): `delete_coupon`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/customer_coupons_create_service.py`

[ ] `FILE-067` — 1 function(s) in this file duplicate `backend/domains/orders/customer_coupons_create_service.py` (normalized AST): `del…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/customer_coupons_create_service.py` and `backend/domains/orders/customer_coupons_create_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-ORDE` — 1 function(s) in this file duplicate `backend/domains/orders/services/packing/service.py` (normalized AST): `_get_order_and_shipment`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `FILE-071` — 1 function(s) in this file duplicate `backend/domains/orders/services/packing/service.py` (normalized AST): `_get_order…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/orders/services/tracking/service.py` and `backend/domains/orders/services/packing/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` — 2 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `add_banner_if_missing`, `update_banne

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/banners/banner_write_service.py`

[ ] `FILE-058` — 2 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `add_banner_if_mi…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/promotions/services/banners/banner_write_service.py` and `backend/domains/orders/services/core/misc.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` — 1 function(s) in this file duplicate `backend/domains/promotions/services/coins/coin_service.py` (normalized AST): `_get_or_create_points_ro

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/promotion_points_service.py`

[ ] `FILE-072` — 1 function(s) in this file duplicate `backend/domains/promotions/services/coins/coin_service.py` (normalized AST): `_ge…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/promotions/services/coins/promotion_points_service.py` and `backend/domains/promotions/services/coins/coin_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-PROM` — 6 function(s) in this file duplicate `backend/domains/promotions/services/promotion_admin_write_service.py` (normalized AST): `create_coupon

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_promotions_write_service.py`

[ ] `FILE-020` — 6 function(s) in this file duplicate `backend/domains/promotions/services/promotion_admin_write_service.py` (normalized…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/promotions/services/engine/admin_promotions_write_service.py` and `backend/domains/promotions/services/promotion_admin_write_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SECU` — 4 function(s) in this file duplicate `backend/domains/governance/services/risk/flat_risk_service.py` (normalized AST): `detect_ghost_employe

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/health/flat_risk_service.py`

[ ] `FILE-036` — 4 function(s) in this file duplicate `backend/domains/governance/services/risk/flat_risk_service.py` (normalized AST):…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/security/services/health/flat_risk_service.py` and `backend/domains/governance/services/risk/flat_risk_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` — 11 function(s) in this file duplicate `backend/domains/orders/services/disputes/service.py` (normalized AST): `_serialize_dispute`, `_serial

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/disputes_service.py`

[ ] `FILE-013` — 11 function(s) in this file duplicate `backend/domains/orders/services/disputes/service.py` (normalized AST): `_seriali…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/suppliers/services/disputes_service.py` and `backend/domains/orders/services/disputes/service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-DOMAINS-SUPP` — 1 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `list_my_documents`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/documents/supplier_documents_service.py`

[ ] `FILE-073` — 1 function(s) in this file duplicate `backend/domains/orders/services/core/misc.py` (normalized AST): `list_my_document…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/domains/suppliers/services/documents/supplier_documents_service.py` and `backend/domains/orders/services/core/misc.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` — 1 function(s) in this file duplicate `backend/domains/accounts/services/permissions/permission_service.py` (normalized AST): `_compute`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/permission_service.py`

[ ] `FILE-074` — 1 function(s) in this file duplicate `backend/domains/accounts/services/permissions/permission_service.py` (normalized…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/infrastructure/database/permission_service.py` and `backend/domains/accounts/services/permissions/permission_service.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` — 1 function(s) in this file duplicate `backend/domains/catalog/services/categories/category_tree.py` (normalized AST): `_chain_for`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/category_tree.py`

[ ] `FILE-076` — 1 function(s) in this file duplicate `backend/domains/catalog/services/categories/category_tree.py` (normalized AST): `…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/infrastructure/utils/category_tree.py` and `backend/domains/catalog/services/categories/category_tree.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-INFRASTRUCTU` — 1 function(s) in this file duplicate `backend/infrastructure/messaging/ws_manager.py` (normalized AST): `_broadcast_to_room`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/websocket_manager.py`

[ ] `FILE-077` — 1 function(s) in this file duplicate `backend/infrastructure/messaging/ws_manager.py` (normalized AST): `_broadcast_to_…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/infrastructure/utils/websocket_manager.py` and `backend/infrastructure/messaging/ws_manager.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-MIDDLEWARE-R` — 6 function(s) in this file duplicate `backend/middleware/middleware_helpers.py` (normalized AST): `as_paginated_response`, `handle_service_e

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/router_helpers.py`

[ ] `FILE-021` — 6 function(s) in this file duplicate `backend/middleware/middleware_helpers.py` (normalized AST): `as_paginated_respons…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/middleware/router_helpers.py` and `backend/middleware/middleware_helpers.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-MODULES-SUPP` — 1 function(s) in this file duplicate `backend/modules/logistics/routers/accounts.py` (normalized AST): `list_sessions_route`

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/supplier/routers/accounts.py`

[ ] `FILE-078` — 1 function(s) in this file duplicate `backend/modules/logistics/routers/accounts.py` (normalized AST): `list_sessions_r…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/modules/supplier/routers/accounts.py` and `backend/modules/logistics/routers/accounts.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AI` — 3 function(s) in this file duplicate `backend/jobs/mcp_marketplace_server.py` (normalized AST): `_pagination_payload`, `_format_products`, `

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/zozi_mcp.py`

[ ] `FILE-044` — 3 function(s) in this file duplicate `backend/jobs/mcp_marketplace_server.py` (normalized AST): `_pagination_payload`,…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/providers/ai/zozi_mcp.py` and `backend/jobs/mcp_marketplace_server.py`

##### `WP3-DUPLICATE-SYMBOL-BACKEND-PROVIDERS-AS` — 8 function(s) in this file duplicate `backend/jobs/async_workers.py` (normalized AST): `remove_background_async`, `batch_remove_background_a

- **cluster:** `CLUSTER-duplicate-symbol` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/async_workers.py`

[ ] `FILE-016` — 8 function(s) in this file duplicate `backend/jobs/async_workers.py` (normalized AST): `remove_background_async`, `batc…
    - do: Extract the shared implementation(s) into one module and import them from both `backend/providers/async_workers.py` and `backend/jobs/async_workers.py`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/accounting` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/accounting/page.tsx`

[ ] `WEB-005` — route `admin/accounting` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/accounting`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/analytics` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/analytics/page.tsx`

[ ] `WEB-006` — route `admin/analytics` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/analytics`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/audit-logs` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/audit-logs/page.tsx`

[ ] `WEB-007` — route `admin/audit-logs` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/audit-logs`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/bank-accounts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/bank-accounts/page.tsx`

[ ] `WEB-008` — route `admin/bank-accounts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/bank-accounts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/banners` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/banners/page.tsx`

[ ] `WEB-009` — route `admin/banners` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/banners`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/barcode` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/barcode/page.tsx`

[ ] `WEB-010` — route `admin/barcode` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/barcode`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/catalog` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/catalog/page.tsx`

[ ] `WEB-011` — route `admin/catalog` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/catalog`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/categories` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/categories/page.tsx`

[ ] `WEB-012` — route `admin/categories` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/categories`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/chat` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/chat/page.tsx`

[ ] `WEB-013` — route `admin/chat` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/chat`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/coc` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/coc/page.tsx`

[ ] `WEB-014` — route `admin/coc` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/coc`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/command-center/alerts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/command-center/alerts/page.tsx`

[ ] `WEB-015` — route `admin/command-center/alerts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/command-center/alerts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/command-center/fraud` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/command-center/fraud/page.tsx`

[ ] `WEB-016` — route `admin/command-center/fraud` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/command-center/fraud`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/command-center/headlines/create` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/command-center/headlines/create/page.tsx`

[ ] `WEB-017` — route `admin/command-center/headlines/create` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/command-center/headlines/create`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/command-center/headlines` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/command-center/headlines/page.tsx`

[ ] `WEB-018` — route `admin/command-center/headlines` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/command-center/headlines`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/command-center` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/command-center/page.tsx`

[ ] `WEB-019` — route `admin/command-center` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/command-center`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/commission` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/commission/page.tsx`

[ ] `WEB-020` — route `admin/commission` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/commission`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/comms-test` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/comms-test/page.tsx`

[ ] `WEB-021` — route `admin/comms-test` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/comms-test`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/communication` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/communication/page.tsx`

[ ] `WEB-022` — route `admin/communication` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/communication`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/countries/[code]/staff` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/countries/[code]/staff/page.tsx`

[ ] `WEB-023` — route `admin/countries/[code]/staff` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/countries/[code]/staff`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/countries` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/countries/page.tsx`

[ ] `WEB-024` — route `admin/countries` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/countries`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/coupons` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/coupons/page.tsx`

[ ] `WEB-025` — route `admin/coupons` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/coupons`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/dashboard` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/dashboard/page.tsx`

[ ] `WEB-026` — route `admin/dashboard` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/dashboard`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/disputes` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/disputes/page.tsx`

[ ] `WEB-027` — route `admin/disputes` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/disputes`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/email` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/email/page.tsx`

[ ] `WEB-028` — route `admin/email` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/email`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/employees` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/employees/page.tsx`

[ ] `WEB-029` — route `admin/employees` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/employees`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/ess` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/ess/page.tsx`

[ ] `WEB-030` — route `admin/ess` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/ess`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/exports` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/exports/page.tsx`

[ ] `WEB-031` — route `admin/exports` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/exports`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/finance` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/finance/page.tsx`

[ ] `WEB-032` — route `admin/finance` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/finance`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/flash-sales` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/flash-sales/page.tsx`

[ ] `WEB-033` — route `admin/flash-sales` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/flash-sales`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/hr` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/hr/page.tsx`

[ ] `WEB-034` — route `admin/hr` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/hr`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/inventory-alerts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/inventory-alerts/page.tsx`

[ ] `WEB-035` — route `admin/inventory-alerts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/inventory-alerts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/invoices` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/invoices/page.tsx`

[ ] `WEB-036` — route `admin/invoices` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/invoices`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/login/page.tsx`

[ ] `WEB-037` — route `admin/login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/logistics-partners` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/logistics-partners/page.tsx`

[ ] `WEB-039` — route `admin/logistics-partners` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/logistics-partners`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/logistics` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/logistics/page.tsx`

[ ] `WEB-038` — route `admin/logistics` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/logistics`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/moderation` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/moderation/page.tsx`

[ ] `WEB-040` — route `admin/moderation` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/moderation`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/orders` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/orders/page.tsx`

[ ] `WEB-041` — route `admin/orders` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/orders`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/organization` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/organization/page.tsx`

[ ] `WEB-042` — route `admin/organization` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/organization`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/payments` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payments/page.tsx`

[ ] `WEB-043` — route `admin/payments` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/payments`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/payouts/background-jobs` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payouts/background-jobs/page.tsx`

[ ] `WEB-044` — route `admin/payouts/background-jobs` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/payouts/background-jobs`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/payouts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payouts/page.tsx`

[ ] `WEB-045` — route `admin/payouts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/payouts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/payroll` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payroll/page.tsx`

[ ] `WEB-046` — route `admin/payroll` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/payroll`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/permissions` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/permissions/page.tsx`

[ ] `WEB-047` — route `admin/permissions` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/permissions`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/product-verification` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/product-verification/page.tsx`

[ ] `WEB-048` — route `admin/product-verification` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/product-verification`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/products` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/products/page.tsx`

[ ] `WEB-049` — route `admin/products` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/products`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/promotions` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/promotions/page.tsx`

[ ] `WEB-050` — route `admin/promotions` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/promotions`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/resolution` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/resolution/page.tsx`

[ ] `WEB-051` — route `admin/resolution` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/resolution`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/returns` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/returns/page.tsx`

[ ] `WEB-052` — route `admin/returns` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/returns`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/staff` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/staff/page.tsx`

[ ] `WEB-053` — route `admin/staff` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/staff`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/supplier-documents` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/supplier-documents/page.tsx`

[ ] `WEB-054` — route `admin/supplier-documents` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/supplier-documents`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/suppliers` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/suppliers/page.tsx`

[ ] `WEB-055` — route `admin/suppliers` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/suppliers`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/tickets/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/tickets/[id]/page.tsx`

[ ] `WEB-056` — route `admin/tickets/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/tickets/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/tickets` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/tickets/page.tsx`

[ ] `WEB-057` — route `admin/tickets` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/tickets`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/treasury` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/treasury/page.tsx`

[ ] `WEB-058` — route `admin/treasury` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/treasury`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/users` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/users/page.tsx`

[ ] `WEB-059` — route `admin/users` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/users`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `admin/video` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/video/page.tsx`

[ ] `WEB-060` — route `admin/video` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/admin/video`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `archive` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/archive/page.tsx`

[ ] `WEB-061` — route `archive` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/archive`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `auth/callback` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/auth/callback/page.tsx`

[ ] `WEB-062` — route `auth/callback` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/auth/callback`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `brand` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/brand/page.tsx`

[ ] `WEB-063` — route `brand` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/brand`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `chatbot` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/chatbot/page.tsx`

[ ] `WEB-064` — route `chatbot` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/chatbot`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `contact` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/contact/page.tsx`

[ ] `WEB-065` — route `contact` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/contact`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `customer/(auth)/login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/customer/(auth)/login/page.tsx`

[ ] `WEB-066` — route `customer/(auth)/login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/customer/(auth)/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/(auth)/login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/(auth)/login/page.tsx`

[ ] `WEB-067` — route `employee/(auth)/login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/(auth)/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/attendance` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/attendance/page.tsx`

[ ] `WEB-068` — route `employee/attendance` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/attendance`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/dashboard` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/dashboard/page.tsx`

[ ] `WEB-069` — route `employee/dashboard` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/dashboard`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/documents` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/documents/page.tsx`

[ ] `WEB-070` — route `employee/documents` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/documents`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/leaves` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/leaves/page.tsx`

[ ] `WEB-071` — route `employee/leaves` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/leaves`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/notifications` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/notifications/page.tsx`

[ ] `WEB-072` — route `employee/notifications` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/notifications`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/page.tsx`

[ ] `WEB-073` — route `employee` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/payroll` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/payroll/page.tsx`

[ ] `WEB-074` — route `employee/payroll` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/payroll`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/performance` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/performance/page.tsx`

[ ] `WEB-075` — route `employee/performance` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/performance`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/profile` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/profile/page.tsx`

[ ] `WEB-076` — route `employee/profile` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/profile`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/schedule` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/schedule/page.tsx`

[ ] `WEB-077` — route `employee/schedule` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/schedule`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/training` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/training/page.tsx`

[ ] `WEB-078` — route `employee/training` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/training`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/workspace` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/workspace/page.tsx`

[ ] `WEB-079` — route `employee/workspace` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/workspace`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `employee/workspace/tasks` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/workspace/tasks/page.tsx`

[ ] `WEB-080` — route `employee/workspace/tasks` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/employee/workspace/tasks`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/login/page.tsx`

[ ] `WEB-081` — route `login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/(auth)/login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/(auth)/login/page.tsx`

[ ] `WEB-082` — route `logistics-partner/(auth)/login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/(auth)/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/(auth)/register` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/(auth)/register/page.tsx`

[ ] `WEB-083` — route `logistics-partner/(auth)/register` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/(auth)/register`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/analytics` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/analytics/page.tsx`

[ ] `WEB-084` — route `logistics-partner/analytics` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/analytics`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/dashboard` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/dashboard/page.tsx`

[ ] `WEB-085` — route `logistics-partner/dashboard` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/dashboard`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/payouts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/payouts/page.tsx`

[ ] `WEB-086` — route `logistics-partner/payouts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/payouts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/profile` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/profile/page.tsx`

[ ] `WEB-087` — route `logistics-partner/profile` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/profile`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/routes` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/routes/page.tsx`

[ ] `WEB-088` — route `logistics-partner/routes` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/routes`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/scan` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/scan/page.tsx`

[ ] `WEB-089` — route `logistics-partner/scan` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/scan`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partner/shipments` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/shipments/page.tsx`

[ ] `WEB-090` — route `logistics-partner/shipments` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partner/shipments`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partners/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partners/[id]/page.tsx`

[ ] `WEB-091` — route `logistics-partners/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partners/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logistics-partners` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partners/page.tsx`

[ ] `WEB-092` — route `logistics-partners` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logistics-partners`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `logo-animation` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logo-animation/page.tsx`

[ ] `WEB-093` — route `logo-animation` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/logo-animation`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `meet/[room]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/meet/[room]/page.tsx`

[ ] `WEB-094` — route `meet/[room]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/meet/[room]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `newsletter/preferences` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/newsletter/preferences/page.tsx`

[ ] `WEB-095` — route `newsletter/preferences` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/newsletter/preferences`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `newsletter/unsubscribe` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/newsletter/unsubscribe/page.tsx`

[ ] `WEB-096` — route `newsletter/unsubscribe` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/newsletter/unsubscribe`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `offers` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/offers/page.tsx`

[ ] `WEB-097` — route `offers` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/offers`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `orders/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/orders/[id]/page.tsx`

[ ] `WEB-098` — route `orders/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/orders/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `products/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/products/[id]/page.tsx`

[ ] `WEB-099` — route `products/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/products/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `products/category` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/products/category/page.tsx`

[ ] `WEB-100` — route `products/category` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/products/category`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `profile/referrals` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/profile/referrals/page.tsx`

[ ] `WEB-101` — route `profile/referrals` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/profile/referrals`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `r/[code]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/r/[code]/page.tsx`

[ ] `WEB-102` — route `r/[code]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/r/[code]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `register` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/register/page.tsx`

[ ] `WEB-103` — route `register` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/register`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `reset-password` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/reset-password/page.tsx`

[ ] `WEB-104` — route `reset-password` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/reset-password`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `returns/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/returns/[id]/page.tsx`

[ ] `WEB-105` — route `returns/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/returns/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier-storefront/[slug]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier-storefront/[slug]/page.tsx`

[ ] `WEB-139` — route `supplier-storefront/[slug]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier-storefront/[slug]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/(auth)/login` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/(auth)/login/page.tsx`

[ ] `WEB-106` — route `supplier/(auth)/login` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/(auth)/login`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/(auth)/register` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/(auth)/register/page.tsx`

[ ] `WEB-107` — route `supplier/(auth)/register` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/(auth)/register`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/analytics` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/analytics/page.tsx`

[ ] `WEB-108` — route `supplier/analytics` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/analytics`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/batch-upload` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/batch-upload/page.tsx`

[ ] `WEB-109` — route `supplier/batch-upload` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/batch-upload`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/bulk` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/bulk/page.tsx`

[ ] `WEB-110` — route `supplier/bulk` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/bulk`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/commission` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/commission/page.tsx`

[ ] `WEB-111` — route `supplier/commission` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/commission`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/credibility` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/credibility/page.tsx`

[ ] `WEB-112` — route `supplier/credibility` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/credibility`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/dashboard` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/dashboard/page.tsx`

[ ] `WEB-113` — route `supplier/dashboard` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/dashboard`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/disputes` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/disputes/page.tsx`

[ ] `WEB-114` — route `supplier/disputes` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/disputes`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/documents` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/documents/page.tsx`

[ ] `WEB-115` — route `supplier/documents` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/documents`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/guide` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/guide/page.tsx`

[ ] `WEB-116` — route `supplier/guide` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/guide`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/inventory` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/inventory/page.tsx`

[ ] `WEB-117` — route `supplier/inventory` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/inventory`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/invoices` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/invoices/page.tsx`

[ ] `WEB-118` — route `supplier/invoices` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/invoices`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/labels/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/labels/[id]/page.tsx`

[ ] `WEB-119` — route `supplier/labels/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/labels/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/labels` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/labels/page.tsx`

[ ] `WEB-120` — route `supplier/labels` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/labels`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/list-product` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/list-product/page.tsx`

[ ] `WEB-121` — route `supplier/list-product` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/list-product`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/logistics` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/logistics/page.tsx`

[ ] `WEB-122` — route `supplier/logistics` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/logistics`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/notification-preferences` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/notification-preferences/page.tsx`

[ ] `WEB-123` — route `supplier/notification-preferences` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/notification-preferences`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/orders/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/orders/[id]/page.tsx`

[ ] `WEB-124` — route `supplier/orders/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/orders/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/orders` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/orders/page.tsx`

[ ] `WEB-125` — route `supplier/orders` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/orders`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/payouts` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/payouts/page.tsx`

[ ] `WEB-126` — route `supplier/payouts` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/payouts`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/products/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/products/[id]/page.tsx`

[ ] `WEB-127` — route `supplier/products/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/products/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/products/add` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/products/add/page.tsx`

[ ] `WEB-128` — route `supplier/products/add` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/products/add`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/products` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/products/page.tsx`

[ ] `WEB-129` — route `supplier/products` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/products`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/profile` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/profile/page.tsx`

[ ] `WEB-130` — route `supplier/profile` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/profile`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/regions` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/regions/page.tsx`

[ ] `WEB-131` — route `supplier/regions` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/regions`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/reports` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/reports/page.tsx`

[ ] `WEB-132` — route `supplier/reports` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/reports`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/returns` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/returns/page.tsx`

[ ] `WEB-133` — route `supplier/returns` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/returns`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/support` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/support/page.tsx`

[ ] `WEB-134` — route `supplier/support` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/support`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/terms` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/terms/page.tsx`

[ ] `WEB-135` — route `supplier/terms` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/terms`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/upload/bg-compare` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/upload/bg-compare/page.tsx`

[ ] `WEB-136` — route `supplier/upload/bg-compare` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/upload/bg-compare`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/upload` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/upload/page.tsx`

[ ] `WEB-137` — route `supplier/upload` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/upload`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `supplier/videos/upload` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/videos/upload/page.tsx`

[ ] `WEB-138` — route `supplier/videos/upload` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/supplier/videos/upload`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `suppliers/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/suppliers/[id]/page.tsx`

[ ] `WEB-140` — route `suppliers/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/suppliers/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `suppliers` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/suppliers/page.tsx`

[ ] `WEB-141` — route `suppliers` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/suppliers`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `tickets/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/tickets/[id]/page.tsx`

[ ] `WEB-142` — route `tickets/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/tickets/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `tracking/[id]` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/tracking/[id]/page.tsx`

[ ] `WEB-143` — route `tracking/[id]` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/tracking/[id]`

##### `WP3-FE-ROUTE-STATE-FRONTEND-WEB-APP-SRC` — route `verify-email` has no `error.tsx` boundary

- **cluster:** `CLUSTER-fe-route-state` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/verify-email/page.tsx`

[ ] `WEB-144` — route `verify-email` has no `error.tsx` boundary
    - do: add error.tsx to the segment so a failed fetch has a recovery path
    - verify: `ls frontend/web_app/src/app/verify-email`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 12 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/HomeClient.tsx`

[ ] `WEB-160` — 12 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/HomeClient.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 12 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/countries/CountryLedgerTable.tsx`

[ ] `WEB-161` — 12 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/admin/countries/CountryLedgerTable.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 4 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/countries/components/AnalyticsTab.tsx`

[ ] `WEB-189` — 4 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/admin/countries/components/AnalyticsTab.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 1 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/dashboard/_tabs/BannerTab.tsx`

[ ] `WEB-198` — 1 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/admin/dashboard/_tabs/BannerTab.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 16 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/ess/page.tsx`

[ ] `WEB-154` — 16 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/admin/ess/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 9 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/organization/page.tsx`

[ ] `WEB-162` — 9 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/admin/organization/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 30 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payouts/background-jobs/page.tsx`

[ ] `WEB-149` — 30 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/admin/payouts/background-jobs/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 34 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/payouts/page.tsx`

[ ] `WEB-147` — 34 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/admin/payouts/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 1 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/admin/suppliers/page.tsx`

[ ] `WEB-199` — 1 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/admin/suppliers/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 31 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/leaves/page.tsx`

[ ] `WEB-148` — 31 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/employee/leaves/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/page.tsx`

[ ] `WEB-170` — 3 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/employee/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 6 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/employee/workspace/tasks/page.tsx`

[ ] `WEB-167` — 6 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/employee/workspace/tasks/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 1 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/logistics-partner/shipments/page.tsx`

[ ] `WEB-200` — 1 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/logistics-partner/shipments/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 1 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/orders/[id]/page.tsx`

[ ] `WEB-201` — 1 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/orders/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/returns/[id]/page.tsx`

[ ] `WEB-171` — 3 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/returns/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 24 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/bulk/draftUtils.ts`

[ ] `WEB-176` — 24 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/supplier/bulk/draftUtils.ts`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 1 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/orders/[id]/page.tsx`

[ ] `WEB-202` — 1 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/app/supplier/orders/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/products/[id]/page.tsx`

[ ] `WEB-172` — 3 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/supplier/products/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 25 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/supplier/upload/bg-compare/page.tsx`

[ ] `WEB-152` — 25 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/supplier/upload/bg-compare/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 4 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/app/suppliers/[id]/page.tsx`

[ ] `WEB-169` — 4 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/app/suppliers/[id]/page.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 14 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/BackgroundEffect.tsx`

[ ] `WEB-177` — 14 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/BackgroundEffect.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 36 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/BannerCanvasEditor.tsx`

[ ] `WEB-175` — 36 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/BannerCanvasEditor.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/BannerCarousel.tsx`

[ ] `WEB-192` — 3 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/BannerCarousel.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 15 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/CategorySidebar.tsx`

[ ] `WEB-155` — 15 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/CategorySidebar.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 14 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/EcosystemWidget.tsx`

[ ] `WEB-158` — 14 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/EcosystemWidget.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/EmployeeLayout.tsx`

[ ] `WEB-173` — 3 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/EmployeeLayout.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/SignaturePad.tsx`

[ ] `WEB-193` — 3 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/SignaturePad.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 18 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/TestimonialsWidget.tsx`

[ ] `WEB-153` — 18 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/TestimonialsWidget.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/TickerBar.tsx`

[ ] `WEB-163` — 8 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/TickerBar.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 15 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/TopCategoriesWidget.tsx`

[ ] `WEB-156` — 15 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/TopCategoriesWidget.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/admin/AdminVideoPanel.tsx`

[ ] `WEB-174` — 3 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/admin/AdminVideoPanel.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 2 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/admin/commandCenter/hud.tsx`

[ ] `WEB-196` — 2 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/admin/commandCenter/hud.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 7 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/chat/PresenceIndicator.tsx`

[ ] `WEB-165` — 7 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/chat/PresenceIndicator.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 6 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/comms/StatusDock.tsx`

[ ] `WEB-168` — 6 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/comms/StatusDock.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 66 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/country/CountryResearchPanel.tsx`

[ ] `WEB-145` — 66 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/country/CountryResearchPanel.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 7 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/country/InternalCommunicationsSystem.tsx`

[ ] `WEB-166` — 7 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/country/InternalCommunicationsSystem.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 30 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/ems/ActivityTimeline.tsx`

[ ] `WEB-150` — 30 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/ems/ActivityTimeline.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 4 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/map/mapMarker.ts`

[ ] `WEB-191` — 4 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/map/mapMarker.ts`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 3 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/supplier/ParcelAuditWidget.tsx`

[ ] `WEB-194` — 3 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/supplier/ParcelAuditWidget.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 2 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/supplier/ProcessingModal.tsx`

[ ] `WEB-197` — 2 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/supplier/ProcessingModal.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 5 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/supplier/ProductImageCanvas.tsx`

[ ] `WEB-187` — 5 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/components/supplier/ProductImageCanvas.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 28 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/supplier/SmartVariantMatrix.tsx`

[ ] `WEB-151` — 28 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/supplier/SmartVariantMatrix.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 raw Tailwind palette class(es) bypass the semantic token scale

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/components/supplier/VoiceProductInput.tsx`

[ ] `WEB-164` — 8 raw Tailwind palette class(es) bypass the semantic token scale
    - do: replace with the semantic token class
    - verify: `grep -cE '(bg|text|border)-(slate|gray|zinc)-[0-9]{2,3}' frontend/web_app/src/components/supplier/VoiceProductInput.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 7 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/Button.native.tsx`

[ ] `WEB-185` — 7 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/Button.native.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 9 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/ErrorBoundary.tsx`

[ ] `WEB-180` — 9 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/ErrorBoundary.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 6 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/QuickFilters.native.tsx`

[ ] `WEB-186` — 6 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/QuickFilters.native.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/SearchBar.native.tsx`

[ ] `WEB-182` — 8 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/SearchBar.native.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 5 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/SearchBar.web.tsx`

[ ] `WEB-188` — 5 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/SearchBar.web.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/SupplierBadge.native.tsx`

[ ] `WEB-183` — 8 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/SupplierBadge.native.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/components/ui/SupplierBadge.web.tsx`

[ ] `WEB-184` — 8 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/components/ui/SupplierBadge.web.tsx`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 9 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/notificationHelpers.ts`

[ ] `WEB-179` — 9 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/notificationHelpers.ts`

##### `WP3-FE-TOKEN-DRIFT-FRONTEND-WEB-APP-SRC` — 8 hardcoded hex colour(s) outside the token layer

- **cluster:** `CLUSTER-fe-token-drift` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src/shared/ticketHelpers.ts`

[ ] `WEB-181` — 8 hardcoded hex colour(s) outside the token layer
    - do: convert to `var(--color-*)` or a token utility
    - verify: `grep -cE '#[0-9a-fA-F]{6}' frontend/web_app/src/shared/ticketHelpers.ts`

##### `WP3-FEATURE-GATE` — 146 declared feature(s) are never referenced by any gate

- **cluster:** `CLUSTER-feature-gate` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains`

[ ] `FEAT-DEAD` — 146 declared feature(s) are never referenced by any gate
    - do: gate the endpoints that should use them, or delete the dead entries from features.py
    - verify: `python _zozi_audit/zozi_compile.py --check feature-dead`

##### `WP3-HTTP-CSP` — the CSP uses the deprecated `report-uri` directive

- **cluster:** `CLUSTER-http-csp` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `SEC-csp-report-uri` — the CSP uses the deprecated `report-uri` directive
    - do: add a Reporting-Endpoints header and switch to report-to
    - verify: `grep -rn 'report-uri' backend/middleware`

##### `WP3-HTTP-HEADERS` — the security middleware emits X-XSS-Protection (1 site(s))

- **cluster:** `CLUSTER-http-headers` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/middleware/security_headers.py`

[ ] `SEC-xss-header-removed` — the security middleware emits X-XSS-Protection (1 site(s))
    - do: delete the X-XSS-Protection header and rely on the CSP
    - verify: `grep -rn 'x-xss-protection' backend/middleware`

##### `WP3-INTERACTION-BUTTON` — 2 icon-only button(s) expose no accessible name

- **cluster:** `CLUSTER-interaction-button` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src`

[ ] `IX-icon-button-name` — 2 icon-only button(s) expose no accessible name
    - do: add aria-label to each icon-only button
    - verify: `npx axe http://localhost:3100 --tags wcag2a`

##### `WP3-INTERACTION-MODAL` — 23 of 27 modal implementations do not close on Escape

- **cluster:** `CLUSTER-interaction-modal` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/src`

[ ] `IX-modal-escape` — 23 of 27 modal implementations do not close on Escape
    - do: add onEscapeKeyDown / onPointerDownOutside to the dialog primitive
    - verify: `grep -rL 'onEscapeKeyDown\|Escape' frontend/web_app/src/components/ui`

##### `WP3-LAW-DOCS` — Law 248 (Runbooks) violated: 0 doc file(s) under docs/

- **cluster:** `CLUSTER-law-docs` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-248` — Law 248 (Runbooks) violated: 0 doc file(s) under docs/
    - do: Fix Law-248 violation: Runbooks

##### `WP3-LAW-FRONTEND-CONTRACT` — tsconfig does not enable strict mode (strict=false), so the type checker will not catch nullability or implicit-any defects

- **cluster:** `CLUSTER-law-frontend-contract` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/shared/tsconfig.json`

[ ] `DECLLAW-003` — tsconfig does not enable strict mode (strict=false), so the type checker will not catch nullability or implicit-any def…
    - do: set "strict": true (and "noUncheckedIndexedAccess" where feasible)

##### `WP3-LAW-GIT-HYGIENE` — no CODEOWNERS or branch-protection document, so required review is not recorded anywhere in the repository

- **cluster:** `CLUSTER-law-git-hygiene` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `.github`

[ ] `DECLLAW-002` — no CODEOWNERS or branch-protection document, so required review is not recorded anywhere in the repository
    - do: add CODEOWNERS and document the protected-branch rule

##### `WP3-LAW-MIGRATION` — Law 27 (Delete temp scripts) violated: 105 temp/debug file(s) at backend root

- **cluster:** `CLUSTER-law-migration` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-027` — Law 27 (Delete temp scripts) violated: 105 temp/debug file(s) at backend root
    - do: Fix Law-27 violation: Delete temp scripts

##### `WP3-LAW-PERFORMANCE` — Law 222 (Keyset pagination) violated: 88 OFFSET usage(s)

- **cluster:** `CLUSTER-law-performance` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/`

[ ] `LAW-222` — Law 222 (Keyset pagination) violated: 88 OFFSET usage(s)
    - do: Fix Law-222 violation: Keyset pagination

##### `WP3-LAW-UNATTRIBUTED` — 133 law(s) are enforced by a check but no finding cites them, so no result is attributable to them (41% of the benchmark). Sample: Law 14: B

- **cluster:** `CLUSTER-law-unattributed` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `_most_imp_docx/ARCHITECTURE_STACK.md`

[ ] `LAWCOV-045` — 133 law(s) are enforced by a check but no finding cites them, so no result is attributable to them (41% of the benchmar…
    - do: extend `laws=(...)` on the check that actually enforces each one, so the report can attribute findings to laws

##### `WP3-LONG-FUNCTION-BACKEND-CONFIG-PY` — 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/config.py`

[ ] `LOGIC-263` — 3 function(s) >50 lines; longest sample `_validate_required_secrets_in_non_production` = 67 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 10 function(s) >50 lines; longest sample `authenticate_password` = 59 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `LOGIC-239` — 10 function(s) >50 lines; longest sample `authenticate_password` = 59 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 2 function(s) >50 lines; longest sample `record_consent` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/gdpr_service.py`

[ ] `LOGIC-279` — 2 function(s) >50 lines; longest sample `record_consent` = 67 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ACCO` — 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/users/user_management_service.py`

[ ] `LOGIC-240` — 9 function(s) >50 lines; longest sample `get_all_users` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ANAL` — 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/analytics/services/dashboards/analytics_service.py`

[ ] `LOGIC-280` — 2 function(s) >50 lines; longest sample `get_customer_insights` = 55 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/ai_upload_service.py`

[ ] `LOGIC-264` — 3 function(s) >50 lines; longest sample `_enrich_one` = 77 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 2 function(s) >50 lines; longest sample `list_products` = 119 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-281` — 2 function(s) >50 lines; longest sample `list_products` = 119 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CATA` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-245` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/email_gateway.py`

[ ] `LOGIC-282` — 2 function(s) >50 lines; longest sample `_enqueue_email_delivery` = 53 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 3 function(s) >50 lines; longest sample `send_message` = 58 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/chat_service.py`

[ ] `LOGIC-265` — 3 function(s) >50 lines; longest sample `send_message` = 58 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COMM` — 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/shared/chat_threads_query.py`

[ ] `LOGIC-283` — 2 function(s) >50 lines; longest sample `build_unified_inbox_sql` = 78 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` — 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `LOGIC-246` — 5 function(s) >50 lines; longest sample `_country_public_payload` = 82 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-COUN` — 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_heuristic_engine.py`

[ ] `LOGIC-284` — 2 function(s) >50 lines; longest sample `_compute_gateway_feasibility` = 52 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-CUST` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-247` — 5 function(s) >50 lines; longest sample `_score_product` = 55 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/country/supplier_finance_service.py`

[ ] `LOGIC-286` — 2 function(s) >50 lines; longest sample `get_order_payment_status` = 91 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/data_import_service.py`

[ ] `LOGIC-248` — 5 function(s) >50 lines; longest sample `create_import_shipment` = 79 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `LOGIC-235` — 31 function(s) >50 lines; longest sample `seed_chart_of_accounts` = 126 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_paypal.py`

[ ] `LOGIC-266` — 3 function(s) >50 lines; longest sample `create_paypal_order` = 75 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_stripe.py`

[ ] `LOGIC-253` — 4 function(s) >50 lines; longest sample `_create_payment_intent_inner` = 114 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/gateway_tap.py`

[ ] `LOGIC-242` — 7 function(s) >50 lines; longest sample `create_tap_charge` = 82 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_engine.py`

[ ] `LOGIC-241` — 9 function(s) >50 lines; longest sample `get_payment_methods_status` = 91 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payments/payment_orchestrator.py`

[ ] `LOGIC-267` — 3 function(s) >50 lines; longest sample `_build_generic_redirect` = 62 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/payouts/payout_batch_service.py`

[ ] `LOGIC-238` — 11 function(s) >50 lines; longest sample `generate_supplier_payout_batches` = 68 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-FINA` — 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/finance/services/trading_service.py`

[ ] `LOGIC-285` — 2 function(s) >50 lines; longest sample `create_purchase_order` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` — 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/background.py`

[ ] `LOGIC-287` — 2 function(s) >50 lines; longest sample `calculate_and_cache_search_trends` = 55 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-GOVE` — 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-288` — 2 function(s) >50 lines; longest sample `get_dashboard_stats` = 54 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-HR-S` — 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/employees/hr_service.py`

[ ] `LOGIC-268` — 3 function(s) >50 lines; longest sample `upsert_employee_risk_score` = 60 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 2 function(s) >50 lines; longest sample `create_partner` = 73 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/admin_service.py`

[ ] `LOGIC-289` — 2 function(s) >50 lines; longest sample `create_partner` = 73 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-269` — 3 function(s) >50 lines; longest sample `get_email_stats` = 61 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/shipment_service.py`

[ ] `LOGIC-249` — 5 function(s) >50 lines; longest sample `get_orders_to_fulfil` = 61 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/logistics_pricing_service.py`

[ ] `LOGIC-250` — 5 function(s) >50 lines; longest sample `_parse_partner_service_area_payload` = 93 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/partner_service.py`

[ ] `LOGIC-270` — 3 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-LOGI` — 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-243` — 7 function(s) >50 lines; longest sample `normalize_pricing_breakdown_payload` = 98 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-236` — 28 function(s) >50 lines; longest sample `_serialize_partner` = 62 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_admin.py`

[ ] `LOGIC-255` — 4 function(s) >50 lines; longest sample `confirm_order_scan_receipt` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-244` — 7 function(s) >50 lines; longest sample `_group_supplier_totals` = 54 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/orders_service.py`

[ ] `LOGIC-254` — 4 function(s) >50 lines; longest sample `bulk_update_order_status_admin` = 52 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/returns/service.py`

[ ] `LOGIC-271` — 3 function(s) >50 lines; longest sample `create_return_request` = 67 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-ORDE` — 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `LOGIC-256` — 4 function(s) >50 lines; longest sample `_build_order_finance_breakdown` = 83 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coins/promotion_points_service.py`

[ ] `LOGIC-290` — 2 function(s) >50 lines; longest sample `award_points_for_order` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `create_banner` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/admin_promotions_write_service.py`

[ ] `LOGIC-291` — 2 function(s) >50 lines; longest sample `create_banner` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-PROM` — 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/engine/promotion_service.py`

[ ] `LOGIC-292` — 2 function(s) >50 lines; longest sample `_seed_default_tiers` = 60 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SECU` — 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/security/services/fraud/fraud_detection_service.py`

[ ] `LOGIC-293` — 2 function(s) >50 lines; longest sample `check_ip_reputation` = 57 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/health/supplier_health.py`

[ ] `LOGIC-237` — 16 function(s) >50 lines; longest sample `get_supplier_analytics` = 109 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `get_supplier_orders` = 141 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders.py`

[ ] `LOGIC-258` — 4 function(s) >50 lines; longest sample `get_supplier_orders` = 141 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/orders/supplier_orders_service.py`

[ ] `LOGIC-272` — 3 function(s) >50 lines; longest sample `get_supplier_label` = 84 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_product_service.py`

[ ] `LOGIC-273` — 3 function(s) >50 lines; longest sample `persist_supplier_product` = 100 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_products.py`

[ ] `LOGIC-259` — 4 function(s) >50 lines; longest sample `process_product_image` = 52 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/products/supplier_supplier_upload_service.py`

[ ] `LOGIC-294` — 2 function(s) >50 lines; longest sample `ab_test_bg_strategies` = 70 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-DOMAINS-SUPP` — 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/suppliers/services/supplier_shared.py`

[ ] `LOGIC-257` — 4 function(s) >50 lines; longest sample `persist_supplier_product` = 95 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/seed/_common.py`

[ ] `LOGIC-251` — 5 function(s) >50 lines; longest sample `_ensure_demo_pickup_ready_shipment` = 220 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/email_service.py`

[ ] `LOGIC-260` — 4 function(s) >50 lines; longest sample `_load_environment_email_config` = 73 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/realtime.py`

[ ] `LOGIC-274` — 3 function(s) >50 lines; longest sample `_admin_alert_payload` = 70 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-INFRASTRUCTU` — 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/schema_audit.py`

[ ] `LOGIC-261` — 4 function(s) >50 lines; longest sample `check_alembic` = 76 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-MAIN-PY` — 2 function(s) >50 lines; longest sample `health_deps` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/main.py`

[ ] `LOGIC-278` — 2 function(s) >50 lines; longest sample `health_deps` = 52 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-AI` — 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/ai_variant_config.py`

[ ] `LOGIC-262` — 4 function(s) >50 lines; longest sample `_analyze_photo_cv` = 83 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` — 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-275` — 3 function(s) >50 lines; longest sample `smart_crop` = 52 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-IM` — 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/parcel_verification.py`

[ ] `LOGIC-252` — 5 function(s) >50 lines; longest sample `_engine_ssim` = 64 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` — 3 function(s) >50 lines; longest sample `create_order` = 79 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paypal.py`

[ ] `LOGIC-276` — 3 function(s) >50 lines; longest sample `create_order` = 79 lines
    - do: Split the longest functions by responsibility

##### `WP3-LONG-FUNCTION-BACKEND-PROVIDERS-PA` — 3 function(s) >50 lines; longest sample `create_payment_page` = 89 lines

- **cluster:** `CLUSTER-long-function` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/payments/paytabs.py`

[ ] `LOGIC-277` — 3 function(s) >50 lines; longest sample `create_payment_page` = 89 lines
    - do: Split the longest functions by responsibility

##### `WP3-ORPHAN-JOB` — 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler

- **cluster:** `CLUSTER-orphan-job` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/jobs/`

[ ] `OPS-015` — 1 task module(s) never referenced by celery_app/periodic_tasks: dlq_reconciler
    - do: Register the tasks or delete the dead modules

##### `WP3-ORPHAN-PROVIDER` — 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_variant_config, apple, ban

- **cluster:** `CLUSTER-orphan-provider` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-008` — 87 provider module(s) never referenced by any domain file: __header__, _helpers, ai_research_jobs, ai_service, ai_varia…
    - do: Delete or wire the orphan providers

##### `WP3-PACKAGE-MANAGER` — non-canonical lockfile `package-lock.json` present

- **cluster:** `CLUSTER-package-manager` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `frontend/web_app/package-lock.json`

[ ] `TECH-012` — non-canonical lockfile `package-lock.json` present
    - do: Delete package-lock.json

##### `WP3-PRINT-LOGGING` — 6 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159)

- **cluster:** `CLUSTER-print-logging` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/_mixin_compliance.py`

[ ] `OBS-004` — 6 `print()` call(s) in production paths (sample backend/domains/_mixin_compliance.py:159)
    - do: Replace print() with the structured logger

##### `WP3-PROVIDER-EXTRA` — provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py, http.py, news, observ

- **cluster:** `CLUSTER-provider-extra` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/providers/`

[ ] `PROV-004` — provider package(s) outside the canonical tree: _helpers.py, analytics, async_workers.py, auth, automation, config.py,…
    - do: Promote into a canonical provider category or document the addition

##### `WP3-PUBLIC-BY-DESIGN` — 9 endpoint(s) are unauthenticated by design (1 authentication entry point, 8 liveness probe); sample: backend/modules/customer/routers/accou

- **cluster:** `CLUSTER-public-by-design` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/accounts.py`

[ ] `WIRE-012` — 9 endpoint(s) are unauthenticated by design (1 authentication entry point, 8 liveness probe); sample: backend/modules/c…
    - do: Record each in the module's `public_routers` list, or add an inline `# public: <reason>` comment so the exemption is reviewable

##### `WP3-READ-REPLICA` — read-replica engine exists but `get_read_db` is never used by domains

- **cluster:** `CLUSTER-read-replica` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/database/database.py`

[ ] `DB-007` — read-replica engine exists but `get_read_db` is never used by domains
    - do: Wire get_read_db into read paths or remove the unused engine

##### `WP3-RLS` — RLS script does not FORCE row level security

- **cluster:** `CLUSTER-rls` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/infrastructure/database/sql/pg_rls_policies.sql`

[ ] `DB-008` — RLS script does not FORCE row level security
    - do: Add FORCE ROW LEVEL SECURITY per table

##### `WP3-SEARCH-INDEX` — 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%"))

- **cluster:** `CLUSTER-search-index` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/finance/services/ledger/general_ledger.py`

[ ] `DB-013` — 2 leading-wildcard ilike search(es) (sample: Employee.position.ilike("%head%"))
    - do: Add a trigram index or a tsvector search path

##### `WP3-SELECT-STAR` — 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version")))

- **cluster:** `CLUSTER-select-star` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/check_db.py`

[ ] `DB-011` — 3 SELECT * usage(s) (sample: res = conn.execute(text("SELECT * FROM alembic_version")))
    - do: Enumerate the needed columns

##### `WP3-SILENT-EXCEPT-BACKEND-CONFIG-PY` — 1 silent except block(s); first at line 937: truly-silent: except AttributeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/config.py`

[ ] `LOGIC-049` — 1 silent except block(s); first at line 937: truly-silent: except AttributeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/config.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ACCO` — 6 silent except block(s); first at line 3080: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/accounts/services/auth/auth_service.py`

[ ] `LOGIC-003` — 6 silent except block(s); first at line 3080: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/accounts/services/auth/auth_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 3 silent except block(s); first at line 54: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/commission_service.py`

[ ] `LOGIC-014` — 3 silent except block(s); first at line 54: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/catalog/services/commission_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/products/products_service.py`

[ ] `LOGIC-015` — 3 silent except block(s); first at line 126: truly-silent: except (TypeError, ValueError, json.JSONDecodeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/catalog/services/products/products_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CATA` — 1 silent except block(s); first at line 219: pass-only: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/catalog/services/search/search_service.py`

[ ] `LOGIC-053` — 1 silent except block(s); first at line 219: pass-only: except (TypeError, ValueError, json.JSONDecodeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/catalog/services/search/search_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 454: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/email/email_management.py`

[ ] `LOGIC-055` — 1 silent except block(s); first at line 454: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/comms/services/email/email_management.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/messaging/websocket_handlers.py`

[ ] `LOGIC-056` — 1 silent except block(s); first at line 281: truly-silent: except WebSocketDisconnect:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/comms/services/messaging/websocket_handlers.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 1 silent except block(s); first at line 166: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/notification_gateway.py`

[ ] `LOGIC-054` — 1 silent except block(s); first at line 166: truly-silent: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/comms/services/notification_gateway.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/public_comms_status_service.py`

[ ] `LOGIC-016` — 3 silent except block(s); first at line 283: truly-silent: except WebSocketDisconnect:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/comms/services/public_comms_status_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COMM` — 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/comms/services/system_comms_status_service.py`

[ ] `LOGIC-024` — 2 silent except block(s); first at line 84: pass-only: except WebSocketDisconnect:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/comms/services/system_comms_status_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_config_version_service.py`

[ ] `LOGIC-057` — 1 silent except block(s); first at line 218: truly-silent: except (json.JSONDecodeError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/country/services/core/country_config_version_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 191: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/core/country_service.py`

[ ] `LOGIC-058` — 1 silent except block(s); first at line 191: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/country/services/core/country_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/cross_border/cross_border_service.py`

[ ] `LOGIC-059` — 1 silent except block(s); first at line 70: pass-only: except (json.JSONDecodeError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/country/services/cross_border/cross_border_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-COUN` — 1 silent except block(s); first at line 480: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/country/services/research/country_ai_research.py`

[ ] `LOGIC-060` — 1 silent except block(s); first at line 480: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/country/services/research/country_ai_research.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` — 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/public_comms_status_service.py`

[ ] `LOGIC-017` — 3 silent except block(s); first at line 276: truly-silent: except WebSocketDisconnect:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/customers/services/public_comms_status_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-CUST` — 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/customers/services/search_service.py`

[ ] `LOGIC-061` — 1 silent except block(s); first at line 232: pass-only: except (TypeError, ValueError, json.JSONDecodeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/customers/services/search_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` — 2 silent except block(s); first at line 444: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/command_center_service.py`

[ ] `LOGIC-027` — 2 silent except block(s); first at line 444: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/governance/services/command_center/command_center_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-GOVE` — 1 silent except block(s); first at line 43: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/governance/services/command_center/service.py`

[ ] `LOGIC-066` — 1 silent except block(s); first at line 43: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/governance/services/command_center/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 2 silent except block(s); first at line 97: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/payroll/payroll_service.py`

[ ] `LOGIC-028` — 2 silent except block(s); first at line 97: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/hr/services/payroll/payroll_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 1 silent except block(s); first at line 120: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/okr.py`

[ ] `LOGIC-067` — 1 silent except block(s); first at line 120: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/hr/services/performance/okr.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-HR-S` — 1 silent except block(s); first at line 85: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/hr/services/performance/reviews.py`

[ ] `LOGIC-068` — 1 silent except block(s); first at line 85: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/hr/services/performance/reviews.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/logistics_engine.py`

[ ] `LOGIC-069` — 1 silent except block(s); first at line 126: truly-silent: except (json.JSONDecodeError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/core/logistics_engine.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 6 silent except block(s); first at line 1439: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/service.py`

[ ] `LOGIC-004` — 6 silent except block(s); first at line 1439: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/core/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/core/zone_service.py`

[ ] `LOGIC-070` — 1 silent except block(s); first at line 28: truly-silent: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/core/zone_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 355: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

[ ] `LOGIC-029` — 2 silent except block(s); first at line 355: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/admin_logistics_operations_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/contract_service.py`

[ ] `LOGIC-071` — 1 silent except block(s); first at line 168: pass-only: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/contract_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/partner_service.py`

[ ] `LOGIC-018` — 3 silent except block(s); first at line 73: truly-silent: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/partner_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 508: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/partners/service.py`

[ ] `LOGIC-030` — 2 silent except block(s); first at line 508: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/partners/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-LOGI` — 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/logistics/services/sla/service.py`

[ ] `LOGIC-031` — 2 silent except block(s); first at line 55: pass-only: except (json.JSONDecodeError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/logistics/services/sla/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/logistics.py`

[ ] `LOGIC-006` — 5 silent except block(s); first at line 284: truly-silent: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/orders/services/core/logistics.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 5 silent except block(s); first at line 211: pass-only: except AttributeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/core/order_engine.py`

[ ] `LOGIC-007` — 5 silent except block(s); first at line 211: pass-only: except AttributeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/orders/services/core/order_engine.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/returns/service.py`

[ ] `LOGIC-072` — 1 silent except block(s); first at line 67: truly-silent: except (TypeError, ValueError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/orders/services/returns/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-ORDE` — 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/orders/services/tracking/service.py`

[ ] `LOGIC-073` — 1 silent except block(s); first at line 362: truly-silent: except (TypeError, ValueError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/orders/services/tracking/service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-DOMAINS-PROM` — 1 silent except block(s); first at line 527: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/domains/promotions/services/coupons/coupon_service.py`

[ ] `LOGIC-074` — 1 silent except block(s); first at line 527: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/domains/promotions/services/coupons/coupon_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 188: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/database_service.py`

[ ] `LOGIC-080` — 1 silent except block(s); first at line 188: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/database/database_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 174: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/rls_interceptor.py`

[ ] `LOGIC-033` — 2 silent except block(s); first at line 174: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/database/rls_interceptor.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/database/schemas.py`

[ ] `LOGIC-020` — 3 silent except block(s); first at line 1104: truly-silent: except (TypeError, ValueError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/database/schemas.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 4 silent except block(s); first at line 18: truly-silent: except Exception:  # noqa: BLE001 - Valkey may be unavailable in dev/test

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/events/subscriber.py`

[ ] `LOGIC-011` — 4 silent except block(s); first at line 18: truly-silent: except Exception: # noqa: BLE001 - Valkey may be unavailable…
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/events/subscriber.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 599: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/realtime.py`

[ ] `LOGIC-081` — 1 silent except block(s); first at line 599: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/messaging/realtime.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/messaging/ws_manager.py`

[ ] `LOGIC-034` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/messaging/ws_manager.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 92: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/ml/worker.py`

[ ] `LOGIC-082` — 1 silent except block(s); first at line 92: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/ml/worker.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 323: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/audit.py`

[ ] `LOGIC-083` — 1 silent except block(s); first at line 323: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/observability/audit.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 22: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/provider_observability.py`

[ ] `LOGIC-036` — 2 silent except block(s); first at line 22: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/observability/provider_observability.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 1 silent except block(s); first at line 132: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/observability/service_observability.py`

[ ] `LOGIC-084` — 1 silent except block(s); first at line 132: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/observability/service_observability.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 57: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/analytics.py`

[ ] `LOGIC-037` — 2 silent except block(s); first at line 57: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/utils/analytics.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/pagination.py`

[ ] `LOGIC-038` — 2 silent except block(s); first at line 31: pass-only: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/utils/pagination.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 110: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/performance_cache.py`

[ ] `LOGIC-039` — 2 silent except block(s); first at line 110: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/utils/performance_cache.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 7 silent except block(s); first at line 67: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/schema_audit.py`

[ ] `LOGIC-002` — 7 silent except block(s); first at line 67: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/utils/schema_audit.py`

##### `WP3-SILENT-EXCEPT-BACKEND-INFRASTRUCTU` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/infrastructure/utils/websocket_manager.py`

[ ] `LOGIC-040` — 2 silent except block(s); first at line 91: pass-only: except RuntimeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/infrastructure/utils/websocket_manager.py`

##### `WP3-SILENT-EXCEPT-BACKEND-JOBS-VIDEO-T` — 1 silent except block(s); first at line 104: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/jobs/video_tasks.py`

[ ] `LOGIC-086` — 1 silent except block(s); first at line 104: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/jobs/video_tasks.py`

##### `WP3-SILENT-EXCEPT-BACKEND-LIFESPAN-PY` — 1 silent except block(s); first at line 351: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/lifespan.py`

[ ] `LOGIC-050` — 1 silent except block(s); first at line 351: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/lifespan.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MAIN-PY` — 1 silent except block(s); first at line 199: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/main.py`

[ ] `LOGIC-051` — 1 silent except block(s); first at line 199: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/main.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-C` — 3 silent except block(s); first at line 245: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/country_context.py`

[ ] `LOGIC-022` — 3 silent except block(s); first at line 245: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/middleware/country_context.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` — 1 silent except block(s); first at line 424: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/webhook_ip_whitelist.py`

[ ] `LOGIC-087` — 1 silent except block(s); first at line 424: truly-silent: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/middleware/webhook_ip_whitelist.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MIDDLEWARE-W` — 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/middleware/webhook_verification.py`

[ ] `LOGIC-012` — 4 silent except block(s); first at line 242: truly-silent: except UnicodeDecodeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/middleware/webhook_verification.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MODULES-ADMI` — 2 silent except block(s); first at line 203: pass-only: except WebSocketDisconnect:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/admin/routers/comms.py`

[ ] `LOGIC-041` — 2 silent except block(s); first at line 203: pass-only: except WebSocketDisconnect:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/modules/admin/routers/comms.py`

##### `WP3-SILENT-EXCEPT-BACKEND-MODULES-CUST` — 3 silent except block(s); first at line 160: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/modules/customer/routers/orders.py`

[ ] `LOGIC-023` — 3 silent except block(s); first at line 160: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/modules/customer/routers/orders.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/huggingface.py`

[ ] `LOGIC-043` — 2 silent except block(s); first at line 78: truly-silent: except urllib.error.HTTPError as exc:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/ai/huggingface.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 231: pass-only: except OSError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/image_ai_service.py`

[ ] `LOGIC-044` — 2 silent except block(s); first at line 231: pass-only: except OSError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/ai/image_ai_service.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-AI` — 2 silent except block(s); first at line 288: truly-silent: except json.JSONDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ai/text.py`

[ ] `LOGIC-045` — 2 silent except block(s); first at line 288: truly-silent: except json.JSONDecodeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/ai/text.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-CO` — 1 silent except block(s); first at line 148: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/comms/whatsapp_selfhosted.py`

[ ] `LOGIC-089` — 1 silent except block(s); first at line 148: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/comms/whatsapp_selfhosted.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-GE` — 1 silent except block(s); first at line 127: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/geography/geo.py`

[ ] `LOGIC-091` — 1 silent except block(s); first at line 127: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/geography/geo.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 39: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/br_05__clean_edge_refiner.py`

[ ] `LOGIC-095` — 1 silent except block(s); first at line 39: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/bg_remover/br_05__clean_edge_refiner.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 245: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/br_06__precision_geometry_classes.py`

[ ] `LOGIC-096` — 1 silent except block(s); first at line 245: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/bg_remover/br_06__precision_geometry_classes.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 158: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/core_i_o.py`

[ ] `LOGIC-097` — 1 silent except block(s); first at line 158: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/bg_remover/core_i_o.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 312: truly-silent: except Exception as exc:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/public_api.py`

[ ] `LOGIC-098` — 1 silent except block(s); first at line 312: truly-silent: except Exception as exc:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/bg_remover/public_api.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 119: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/bg_remover/session_management.py`

[ ] `LOGIC-099` — 1 silent except block(s); first at line 119: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/bg_remover/session_management.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 288: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/free_image_tools.py`

[ ] `LOGIC-092` — 1 silent except block(s); first at line 288: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/free_image_tools.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 30: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/image.py`

[ ] `LOGIC-093` — 1 silent except block(s); first at line 30: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/image.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 4 silent except block(s); first at line 95: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/ocr.py`

[ ] `LOGIC-013` — 4 silent except block(s); first at line 95: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/ocr.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-IM` — 1 silent except block(s); first at line 513: truly-silent: except (ValueError, TypeError):

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/image/parcel_verification.py`

[ ] `LOGIC-094` — 1 silent except block(s); first at line 513: truly-silent: except (ValueError, TypeError):
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/image/parcel_verification.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OB` — 2 silent except block(s); first at line 24: pass-only: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/observability.py`

[ ] `LOGIC-042` — 2 silent except block(s); first at line 24: pass-only: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/observability.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-OC` — 1 silent except block(s); first at line 44: truly-silent: except ValueError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/ocr/ocr_parser.py`

[ ] `LOGIC-100` — 1 silent except block(s); first at line 44: truly-silent: except ValueError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/ocr/ocr_parser.py`

##### `WP3-SILENT-EXCEPT-BACKEND-PROVIDERS-SC` — 2 silent except block(s); first at line 99: truly-silent: except UnicodeDecodeError:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/providers/scanner/scanner.py`

[ ] `LOGIC-048` — 2 silent except block(s); first at line 99: truly-silent: except UnicodeDecodeError:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/providers/scanner/scanner.py`

##### `WP3-SILENT-EXCEPT-BACKEND-RBAC-CATALOG` — 1 silent except block(s); first at line 33: truly-silent: except Exception:

- **cluster:** `CLUSTER-silent-except` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 2.5h
- **files:** `backend/rbac/catalog.py`

[ ] `LOGIC-102` — 1 silent except block(s); first at line 33: truly-silent: except Exception:
    - do: Add logger.warning(..., exc_info=True) or re-raise
    - verify: `grep -n 'except' backend/rbac/catalog.py`

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ACCO` — 1x rel lazy in table `otp_codes`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/accounts/models/otp.py`

[ ] `TF-007` — 1x rel lazy in table `otp_codes`: relationship `user` has no lazy=
    - do: Fix rel-lazy on otp_codes

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/fraud.py`

[ ] `TF-076` — 1x rel lazy in table `meeting_recordings`: relationship `starter` has no lazy=
    - do: Fix rel-lazy on meeting_recordings

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COMM` — 3x rel lazy in table `messages`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/message.py`

[ ] `TF-089` — 3x rel lazy in table `messages`: relationship `country` has no lazy=
    - do: Fix rel-lazy on messages

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_basics`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_basics.py`

[ ] `TF-097` — 1x rel lazy in table `country_basics`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_basics

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_economics`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_economics.py`

[ ] `TF-107` — 1x rel lazy in table `country_economics`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_economics

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_legals`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_legal.py`

[ ] `TF-135` — 1x rel lazy in table `country_legals`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_legals

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-COUN` — 1x rel lazy in table `country_taxes`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_tax.py`

[ ] `TF-137` — 1x rel lazy in table `country_taxes`: relationship `country` has no lazy=
    - do: Fix rel-lazy on country_taxes

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-CUST` — 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/customers/models/cross_country_session.py`

[ ] `TF-138` — 2x rel lazy in table `cross_country_customer_sessions`: relationship `user` has no lazy=
    - do: Fix rel-lazy on cross_country_customer_sessions

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-GOVE` — 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/governance/models/legal_contract_template.py`

[ ] `TF-178` — 1x rel lazy in table `legal_contract_templates`: relationship `country` has no lazy=
    - do: Fix rel-lazy on legal_contract_templates

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-LOGI` — 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/shipping_rules.py`

[ ] `TF-222` — 1x rel lazy in table `shipping_rules`: relationship `country` has no lazy=
    - do: Fix rel-lazy on shipping_rules

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-ORDE` — 1x rel lazy in table `order_items`: relationship `order` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/orders/models/order_entities.py`

[ ] `TF-226` — 1x rel lazy in table `order_items`: relationship `order` has no lazy=
    - do: Fix rel-lazy on order_items

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `TF-232` — 1x rel lazy in table `coupon_usages`: relationship `country` has no lazy=
    - do: Fix rel-lazy on coupon_usages

##### `WP3-TF-REL-LAZY-BACKEND-DOMAINS-PROM` — 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy=

- **cluster:** `CLUSTER-tf-rel-lazy` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/promotion_config.py`

[ ] `TF-234` — 1x rel lazy in table `promotion_engine_configs`: relationship `country` has no lazy=
    - do: Fix rel-lazy on promotion_engine_configs

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-CATA` — 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/catalog/models/upload_job.py`

[ ] `TF-033` — 2x timestamp default in table `upload_jobs`: `created_at` uses Python-side default
    - do: Fix timestamp-default on upload_jobs

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 1x timestamp default in table `messages`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/message.py`

[ ] `TF-088` — 1x timestamp default in table `messages`: `created_at` uses Python-side default
    - do: Fix timestamp-default on messages

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COMM` — 2x timestamp default in table `news_articles`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/comms/models/news.py`

[ ] `TF-090` — 2x timestamp default in table `news_articles`: `created_at` uses Python-side default
    - do: Fix timestamp-default on news_articles

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_basics`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_basics.py`

[ ] `TF-096` — 2x timestamp default in table `country_basics`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_basics

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_economics`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_economics.py`

[ ] `TF-106` — 2x timestamp default in table `country_economics`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_economics

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_legals`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_legal.py`

[ ] `TF-134` — 2x timestamp default in table `country_legals`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_legals

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-COUN` — 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/country/models/country_tax.py`

[ ] `TF-136` — 2x timestamp default in table `country_taxes`: `created_at` uses Python-side default
    - do: Fix timestamp-default on country_taxes

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/logistics_schema_models.py`

[ ] `TF-220` — 2x timestamp default in table `city_distance_matrices`: `created_at` uses Python-side default
    - do: Fix timestamp-default on city_distance_matrices

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-LOGI` — 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/logistics/models/shipping_rules.py`

[ ] `TF-221` — 1x timestamp default in table `shipping_rules`: `created_at` uses Python-side default
    - do: Fix timestamp-default on shipping_rules

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` — 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/coupon_usage.py`

[ ] `TF-231` — 2x timestamp default in table `coupon_usages`: `created_at` uses Python-side default
    - do: Fix timestamp-default on coupon_usages

##### `WP3-TF-TIMESTAMP-DEFAULT-BACKEND-DOMAINS-PROM` — 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default

- **cluster:** `CLUSTER-tf-timestamp-default` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/domains/promotions/models/promotion_config.py`

[ ] `TF-233` — 2x timestamp default in table `promotion_engine_configs`: `created_at` uses Python-side default
    - do: Fix timestamp-default on promotion_engine_configs

_This wave has 878 steps. Work them by package above; the complete step list is in `_zozi_audit/logs/plan.json`._

---
## Wave 5 · Improvement track — recommendations (not release-gating)

> Improvement track. These do not gate a release. Prioritise by the workload they remove, not by severity.

#### Work packages in wave 5 (8)

| Package | Steps | Files | Blocker | Verify tasks | Est. h | Focus |
|---------|-------|-------|---------|---------------|--------|-------|
| `WP5-RECOMMENDATIONS-REC-AUTOMATION` | 8 | 7 | 0 | 0 | 13.0 | Automate the human-in-the-loop queue and the serial write loops |
| `WP5-RECOMMENDATIONS-REC-DATA` | 4 | 5 | 0 | 0 | 27.5 | Model and seed the full 5-tier product taxonomy |
| `WP5-RECOMMENDATIONS-REC-WORKFLOW` | 2 | 2 | 0 | 0 | 26.0 | Turn the event spine into real work, or delete it |
| `WP5-RECOMMENDATIONS-REC-DESIGN` | 1 | 1 | 0 | 0 | 6.0 | Adopt the existing UI primitives and delete duplicated markup |
| `WP5-RECOMMENDATIONS-REC-FINANCE` | 1 | 1 | 0 | 0 | 20.0 | Automate the manual finance processes end to end |
| `WP5-RECOMMENDATIONS-REC-FRONTEND` | 1 | 1 | 0 | 0 | 2.5 | Standardise interaction state handling across all screens |
| `WP5-RECOMMENDATIONS-REC-OPS` | 1 | 1 | 0 | 0 | 1.0 | Add a dispatch smoke test for every scheduled task |
| `WP5-RECOMMENDATIONS-REC-QA` | 1 | 1 | 0 | 0 | 20.0 | Introduce a quality-gate chain across fulfilment |

##### `WP5-RECOMMENDATIONS-REC-AUTOMATION` — Automate the human-in-the-loop queue and the serial write loops

- **cluster:** `recommendations` · **steps:** 8 (0 closed) · **files:** 7 · **est.:** 13.0h
- **files:** `backend/domains/finance/models/general_ledger.py:640, backend/domains/governance/services/workflow_engine.py:116, backend/domains/hr/services/payroll/payroll_engine.py:885, backend/domains/hr/services/payroll/payroll_service.py:140`, `backend/domains/hr/models/employee_models.py:497, backend/domains/security/models/fraud.py:22, backend/domains/security/models/fraud.py:93, backend/domains/security/models/fraud.py:338`, `backend/domains/audit/services/compliance_engine.py:133, backend/domains/hr/services/compliance_engine.py:131, backend/domains/suppliers/services/onboarding/__init__.py:38`, `backend/domains/finance/services/payments/gateway_stripe.py:630, backend/domains/finance/services/payments/gateway_tap.py:474, backend/domains/finance/services/payments/gateway_tap.py:735`, `backend/domains/finance/services/ledger/general_ledger.py:2968, backend/providers/payments/webhook_models.py:28`, `scripts/audit/full_system_audit.py:2904, scripts/audit/full_system_audit.py:2914`, `backend/domains/finance/services/payments/payment_engine.py:321`

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

##### `WP5-RECOMMENDATIONS-REC-OPS` — Add a dispatch smoke test for every scheduled task

- **cluster:** `recommendations` · **steps:** 1 (0 closed) · **files:** 1 · **est.:** 1.0h
- **files:** `backend/jobs/*.py`

[ ] `REC-OPS-001` — Add a dispatch smoke test for every scheduled task
    - do: add a test that imports every task module and asserts each task's callable resolves, plus a startup self-check in the worker entrypoint that exits non-zero on an unresolvable task.
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
---
## Needs triage (not planned — nothing verified these yet)

20 finding(s) had no independent confirmation, so they are **not** in any wave above. A plan step is an instruction to edit code; an unverified claim is not yet known to be a real defect. They need a probe rule or a human decision first.

| Cluster | Count | Why unverified |
|---------|-------|----------------|
| `CLUSTER-middleware-imports-above` | 2 | no independent verification |
| `CLUSTER-deploy` | 2 | no independent verification |
| `CLUSTER-middleware` | 1 | no independent verification |
| `CLUSTER-silent-except` | 1 | no independent verification |
| `CLUSTER-lockfile` | 1 | no independent verification |
| `CLUSTER-todo-hygiene` | 1 | no independent verification |
| `CLUSTER-rls` | 1 | no independent verification |
| `CLUSTER-web-states` | 1 | no independent verification |
| `CLUSTER-web-routes` | 1 | no independent verification |
| `CLUSTER-web-rewrites` | 1 | no independent verification |
| `CLUSTER-mobile-deps` | 1 | no independent verification |
| `CLUSTER-web-images` | 1 | no independent verification |
| `CLUSTER-bundle` | 1 | no independent verification |
| `CLUSTER-browser-evidence-stale` | 1 | no independent verification |
| `CLUSTER-category-taxonomy` | 1 | no independent verification |
| `CLUSTER-table-index` | 1 | no independent verification |
| `CLUSTER-law-git-hygiene` | 1 | no independent verification |
| `CLUSTER-law-kernel-purity` | 1 | no independent verification |

<details><summary>all of them</summary>

| ID | Cluster | Priority | Verdict | Claim |
|---|---|---|---|---|
| `ARCH-039` | `CLUSTER-middleware-imports-ab…` | P1 | UNVERIFIABLE | `middleware imports above`: imports `domains.accounts.services.auth.security_dependencies` |
| `ARCH-040` | `CLUSTER-middleware-imports-ab…` | P1 | UNVERIFIABLE | `middleware imports above`: imports `providers.geography.ip` |
| `D2P-003` | `CLUSTER-deploy` | P2 | UNVERIFIABLE | container has no HEALTHCHECK |
| `D2P-004` | `CLUSTER-deploy` | P2 | UNVERIFIABLE | container has no HEALTHCHECK |
| `WIRE-001` | `CLUSTER-middleware` | P1 | UNVERIFIABLE | middleware order is ['foundation', 'geo', 'security', 'rate', 'compliance', 'observe', 'a… |
| `LOGIC-035` | `CLUSTER-silent-except` | P2 | UNVERIFIABLE | 2 silent except block(s); first at line 113: pass-only: except Exception: # noqa: BLE001 |
| `TECH-021` | `CLUSTER-lockfile` | P1 | UNVERIFIABLE | pyproject.toml declares no [project.dependencies] |
| `LOGIC-296` | `CLUSTER-todo-hygiene` | P2 | UNVERIFIABLE | 295 TODO/FIXME without ticket reference or expiration date (e.g. backend/domains/accounts… |
| `DB-009` | `CLUSTER-rls` | P1 | UNVERIFIABLE | 0 RLS policy target(s) vs 331 country-scoped table(s) |
| `WEB-001` | `CLUSTER-web-states` | P1 | UNVERIFIABLE | 282 page(s) lack loading/error siblings (sample frontend/web_app/src/app/admin/accounting… |
| `WEB-002` | `CLUSTER-web-routes` | P2 | UNVERIFIABLE | duplicate route trees `logistics-partner` and `logistics-partners` both exist |
| `WEB-003` | `CLUSTER-web-rewrites` | P2 | UNVERIFIABLE | rewrite `/hr/*` targets a non-canonical backend surface |
| `MOB-001` | `CLUSTER-mobile-deps` | P1 | UNVERIFIABLE | dynamically required package(s) absent from package.json: @/lib/api, @paytabs/react-nativ… |
| `WEB-004` | `CLUSTER-web-images` | P2 | UNVERIFIABLE | next/image formats do not enable AVIF |
| `PERF-001` | `CLUSTER-bundle` | P3 | UNVERIFIABLE | no bundle analyzer configured |
| `BROWSER-001` | `CLUSTER-browser-evidence-stale` | P2 | UNVERIFIABLE | browser evidence is STALE: 71 recorded step(s) in _browser_test/reports/run/results.json… |
| `CAT-depth-underused` | `CLUSTER-category-taxonomy` | P1 | UNVERIFIABLE | the schema can express a hierarchy (columns: __tablename__, depth, is_active, parent_id,… |
| `DB-unindexed-hot-column` | `CLUSTER-table-index` | P1 | UNVERIFIABLE | 234 (table, column) pair(s) are filtered or sorted on with no declared index |
| `DECLLAW-001` | `CLUSTER-law-git-hygiene` | P3 | UNVERIFIABLE | no commit-message linter is configured, so Conventional Commits is a convention with noth… |
| `DECLLAW-014` | `CLUSTER-law-kernel-purity` | P1 | UNVERIFIABLE | kernel imports a third-party SDK: from sqlalchemy import Column, DateTime, func |

</details>

---
## Rejected findings (not work)

1 finding(s) were disproved or found already fixed by `zozi_verify.py`. They are excluded from every wave above and are recorded here so the exclusion is auditable.

| ID | Verdict | Cluster | Priority | Counter-evidence |
|----|---------|---------|----------|------------------|
| `LOGIC-104` | ALREADY_FIXED | `CLUSTER-float-money` | P1 | backend/domains/analytics/services/dashboards/admin_analytics_service.py:37 no longer contains a float near t… |

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
