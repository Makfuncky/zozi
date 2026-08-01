# ZOZI Platform Governance Report

**Generated:** 2026-08-01T19:28:45.803152+00:00  
**Repo:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  

---

## Platform Health Score

# 22848/100 (A)

| Metric | Count |
|---|---:|
| RED Violations | 306 |
| YELLOW Advisories | 3606 |
| GREEN Info | 17 |
| **Total findings** | **3518** |

---

## Per-Auditor Scores

| Auditor | Score | Grade | RED | YEL | GRN |
|---|---:|---|---:|---:|---:|
| [ARCH] Architecture | 34098/100 | ? | 116 | 918 | 14 |
| [DB] Database | 52100/100 | ? | 170 | 1146 | 0 |
| [UI] Design | 5148/100 | ? | 14 | 158 | 2 |
| [HP] Health | 49/100 | D | 6 | 1384 | 1 |

---

## Priority Matrix

| Priority | Count | Action |
|---|---:|---|
| P0 - Fix Today | 6 | Production / security risk |
| P1 - Fix This Sprint | 125 | Scaling / performance risk |
| P2 - Fix This Month | 574 | Maintainability / structure |
| P3 - Fix When Convenient | 3224 | Hygiene / style |

---

## Top 30 Unhealthiest Files (All Auditors Combined)

| # | File | Weight | Issues |
|---|---|---:|---|
| 1 | `backend\models\treasury\finance.py` | 1016 | DB03, DB06, DB07, DB08, DB09, DB11, DB31, HL101 |
| 2 | `backend\models\logistics\admin.py` | 818 | DB03, DB06, DB07, DB08, DB09, DB11, DB31 |
| 3 | `backend\models\security\fraud.py` | 332 | DB03, DB06, DB07, DB08, DB09, DB11, DB31 |
| 4 | `backend\models\logistics\country_control.py` | 202 | DB03, DB06, DB07, DB08, DB11 |
| 5 | `backend\models\orders\orders.py` | 196 | DB03, DB06, DB07, DB08, DB11 |
| 6 | `backend\models\logistics\logistics.py` | 118 | DB03, DB06, DB07, DB08, DB09, DB11, DB31 |
| 7 | `backend\models\supplier\onboarding.py` | 114 | DB03, DB06, DB07, DB08, DB09, DB11 |
| 8 | `backend\models\communication\core.py` | 104 | DB03, DB09, DB11, DB18, DB31 |
| 9 | `backend\models\catalog\products.py` | 102 | DB01, DB03, DB09, DB11, DB31 |
| 10 | `backend\services\finance\cash_management_service.py` | 88 | A2, DB32, DG3, HL101, HL102, HL303, HL801, QUAL3 |
| 11 | `backend\models\country\country_enhancements.py` | 80 | DB03, DB11, DB31 |
| 12 | `backend\models\security\permissions.py` | 76 | DB03, DB06, DB07, DB08, DB11, DB31 |
| 13 | `backend\models\hr\employee_models.py` | 72 | DB03, DB09, DB11, DB31, M1 |
| 14 | `backend\models\security\incident.py` | 66 | DB03, DB06, DB07, DB08, DB09, DB11 |
| 15 | `backend\models\communication\communication.py` | 66 | DB03, DB09, DB11, DB31 |
| 16 | `backend\services\treasury\cash_management_service.py` | 58 | DB32, DG3, HL101, HL102, HL303, HL801, PERF2, QUAL3 |
| 17 | `backend\models\analytics\analytics.py` | 58 | DB01, DB03, DB11 |
| 18 | `backend\models\media\media_models.py` | 58 | DB03, DB06, DB07, DB08, DB31 |
| 19 | `backend\controllers\supplier\supplier_controller.py` | 50 | A2, DB19, DB32, HL101, HL102, HL302, HL801, MR101 +5 more |
| 20 | `backend\services\treasury\automation_scheduler.py` | 48 | DG3, HL102, HL303, HL801, PERF2 |
| 21 | `frontend\web_app\src\components\BannerCanvasEditor.tsx` | 44 | DS01, DS02, DS03, DS04, DS10, DS13, FEH101, FEH401 +1 more |
| 22 | `frontend\web_app\src\styles\globals.css` | 44 | DS03, DS04, DS06, DS07, DS08, DS10, DS13 |
| 23 | `backend\models\__init__.py` | 42 | A1, DB02, DG2, HL502 |
| 24 | `backend\controllers\orders\orders_controller.py` | 40 | A2, DB32, HL101, HL102, HL302, HL801, MR101, Q1 +3 more |
| 25 | `backend\routers\admin\command_center_api.py` | 40 | API101, HL101, HL102, HL302, HL801, PG102, Q1, QUAL1 +3 more |
| 26 | `backend\models\country\countries.py` | 40 | DB03, DB09, DB11, DB31 |
| 27 | `backend\routers\admin\command_center.py` | 38 | API101, HL102, HL302, HL801, PG102, Q1, QUAL1, QUAL3 +2 more |
| 28 | `backend\controllers\security\auth_controller.py` | 36 | DB19, DB32, DG, HL101, HL102, HL204, HL302, HL601 +5 more |
| 29 | `backend/services/` | 34 | DOM2, MV1, OB101 |
| 30 | `backend\controllers\finance\payments_controller.py` | 32 | A2, HL101, HL102, HL204, HL302, HL601, HL602, HL801 +3 more |

---

## RED Violations (306 findings)

| Auditor | Rule | Domain | Location | Problem | Fix |
|---|---|---|---|---|---|
| [ARCH] Architecture | F4 | backend | `backend\zozi.db` | must not sit at backend (damages structure/scale) | delete + add to .gitignore |
| [ARCH] Architecture | DG | backend | `backend\controllers\security\auth_controller.py:45` | forbidden dependency edge: controllers -> db.database | layer contract: controllers may not depend on db.database; route via services/ |
| [ARCH] Architecture | W3 | backend | `backend\routers\admin\payments.py:13` | imports controller 'controllers.payments_controller' from routers (controller logic belongs in services/utils) | move the imported logic to services/<domain>/ or utils/ |
| [ARCH] Architecture | DG3 | backend | `backend\services\ai\ai_automation_service.py:22` | cross-domain import ai -> finance violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via finance service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:47` | cross-domain import finance -> logistics_partner_pricing violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics_partner_pricing service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:58` | cross-domain import finance -> finance_transfer_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via finance_transfer_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:70` | cross-domain import finance -> bank_transaction_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via bank_transaction_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:1968` | cross-domain import finance -> supplier_badge_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via supplier_badge_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:1969` | cross-domain import finance -> admin_analytics_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via admin_analytics_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:1970` | cross-domain import finance -> retention_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via retention_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\cash_management_service.py:1000` | cross-domain import finance -> general_ledger_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via general_ledger_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\commission_engine.py:451` | cross-domain import finance -> logistics_partner_pricing violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics_partner_pricing service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\finance_automation.py:465` | cross-domain import finance -> ocr_parser violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via ocr_parser service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\finance_automation.py:502` | cross-domain import finance -> treasury_engine violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via treasury_engine service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\finance_transfer_service.py:1116` | cross-domain import finance -> logistics_partner_pricing violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics_partner_pricing service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\invoice_service.py:172` | cross-domain import finance -> communication violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via communication service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\je_reversal_service.py:15` | cross-domain import finance -> general_ledger_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via general_ledger_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\orphan_detector_service.py:16` | cross-domain import finance -> orders violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via orders service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\payout_batch_service.py:105` | cross-domain import finance -> transactional_email_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via transactional_email_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\finance\tax_service.py:10` | cross-domain import finance -> logistics_partner_pricing violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics_partner_pricing service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\hr\employee_communication_service.py:389` | cross-domain import hr -> communication violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via communication service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\logistics\logistics_engine.py:11` | cross-domain import logistics -> logistics_partner_pricing violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics_partner_pricing service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\logistics\logistics_partner_write_service.py:430` | cross-domain import logistics -> finance_transfer_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via finance_transfer_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\logistics\logistics_sla_service.py:124` | cross-domain import logistics -> treasury_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via treasury_service service facade |
| [ARCH] Architecture | W3 | backend | `backend\services\orders\order_payment_functions.py:35` | imports controller 'controllers.payments_controller' from services (controller logic belongs in services/utils) | move the imported logic to services/<domain>/ or utils/ |
| [ARCH] Architecture | DG3 | backend | `backend\services\orders\trading_service.py:517` | cross-domain import orders -> communication violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via communication service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\supplier\supplier_badge_service.py:99` | cross-domain import supplier -> finance violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via finance service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\supplier\supplier_badge_service.py:392` | cross-domain import supplier -> treasury violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via treasury service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\supplier\suppliers_write_service.py:224` | cross-domain import supplier -> finance_transfer_service violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via finance_transfer_service service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\automation_scheduler.py:32` | cross-domain import treasury -> ai violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via ai service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\automation_scheduler.py:462` | cross-domain import treasury -> orders violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via orders service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\automation_scheduler.py:470` | cross-domain import treasury -> orders violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via orders service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\automation_scheduler.py:227` | cross-domain import treasury -> communication violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via communication service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\badge_billing_service.py:10` | cross-domain import treasury -> supplier violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via supplier service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\cash_management_service.py:47` | cross-domain import treasury -> logistics violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via logistics service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\cash_management_service.py:1968` | cross-domain import treasury -> supplier violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via supplier service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\cash_management_service.py:1969` | cross-domain import treasury -> analytics violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via analytics service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\cash_management_service.py:1970` | cross-domain import treasury -> commerce violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via commerce service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\payout_batch_service.py:105` | cross-domain import treasury -> communication violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via communication service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\treasurer.py:12` | cross-domain import treasury -> hr violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via hr service facade |
| [ARCH] Architecture | DG3 | backend | `backend\services\treasury\treasury_service.py:196` | cross-domain import treasury -> hr violates explicit ownership rules | declare allowed imports in layer_rules.yaml or route via hr service facade |
| [ARCH] Architecture | DG2 | backend | `domain-graph` | circular domain dependency: communication -> orders -> communication | redefine bounded-context boundaries; introduce explicit service contracts / events |
| [ARCH] Architecture | DG2 | backend | `domain-graph` | circular domain dependency: audit -> finance -> supplier_badge_service -> audit | redefine bounded-context boundaries; introduce explicit service contracts / events |
| [ARCH] Architecture | DG2 | backend | `domain-graph` | circular domain dependency: supplier -> treasury -> supplier | redefine bounded-context boundaries; introduce explicit service contracts / events |
| [ARCH] Architecture | W1 | backend | `backend\controllers\ai_controller.py` | 2 session write(s) in this file; move writes into services/<domain>/ (lines: 41, 76) | a services/<domain>/*_service.py method |
| [ARCH] Architecture | W1 | backend | `backend\controllers\products_controller.py` | 5 session write(s) in this file; move writes into services/<domain>/ (lines: 76, 430, 768, 769, 1012) | a services/<domain>/*_service.py method |
| [ARCH] Architecture | W1 | backend | `backend\controllers\treasury\cash_management_controller.py` | 2 session write(s) in this file; move writes into services/<domain>/ (lines: 870, 873) | a services/<domain>/*_service.py method |
| [ARCH] Architecture | W1 | backend | `backend\controllers\supplier\supplier_controller.py` | 3 session write(s) in this file; move writes into services/<domain>/ (lines: 118, 670, 738) | a services/<domain>/*_service.py method |
| [ARCH] Architecture | W1 | backend | `backend\controllers\security\risk_controller.py` | 6 session write(s) in this file; move writes into services/<domain>/ (lines: 22, 37, 85, 99, 107, 124) | move raw SQL to a service or repository layer |
| [ARCH] Architecture | W1 | backend | `backend\controllers\orders\cart_controller.py` | 3 session write(s) in this file; move writes into services/<domain>/ (lines: 119, 226, 237) | a services/<domain>/*_service.py method |

---

## P1 - Fix This Sprint (125 findings)

| Auditor | Rule | Domain | Location | Problem | Fix |
|---|---|---|---|---|---|
| [HP] Health | PG102 | polyglot | `backend\main.py` | WebSocket handler in Python: websocket_background_jobs | Python for business logic; Node.js gateway for high-throughput real-time |
| [HP] Health | HL602 | concurrency | `backend\utils\backup.py` | external call(s) missing timeout: _s3_client:321 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL602 | concurrency | `backend\utils\config.py` | external call(s) missing timeout: _load_field_encryption_key_from_aws_ssm:391 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\utils\email_service.py` | sequential external calls: _send_via_resend (2 calls), _send_via_smtp (2 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\utils\email_service.py` | external call(s) missing timeout: _send_via_resend:353 | always set timeout; add retry + circuit breaker |
| [HP] Health | PG102 | polyglot | `backend\utils\realtime.py` | WebSocket handler in Python: connect_order, connect_user, connect_partner | Python for business logic; Node.js gateway for high-throughput real-time |
| [HP] Health | HL501 | performance | `backend\services\bg_removal_presets.py` | heavy top-level import(s): PIL, numpy | lazy-import inside the function/job that needs them |
| [HP] Health | HL501 | performance | `backend\services\dei_auditor.py` | heavy top-level import(s): numpy | lazy-import inside the function/job that needs them |
| [HP] Health | HL601 | concurrency | `backend\services\finance_transfer_service.py` | sequential external calls: execute_transfer_batch (3 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\services\finance_transfer_service.py` | external call(s) missing timeout: execute_transfer_batch:1016, execute_transfer_batch:996, execute_transfer_batch:1000 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL501 | performance | `backend\services\supplier\onboarding_pipeline.py` | heavy top-level import(s): PIL | lazy-import inside the function/job that needs them |
| [HP] Health | HL501 | performance | `backend\services\media\free_image_tools.py` | heavy top-level import(s): PIL, numpy | lazy-import inside the function/job that needs them |
| [HP] Health | HL501 | performance | `backend\services\media\image_ai_service.py` | heavy top-level import(s): PIL | lazy-import inside the function/job that needs them |
| [HP] Health | HL602 | concurrency | `backend\services\media\storage.py` | external call(s) missing timeout: client:157 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\services\finance\finance_transfer_service.py` | sequential external calls: execute_transfer_batch (3 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\services\finance\finance_transfer_service.py` | external call(s) missing timeout: execute_transfer_batch:1016, execute_transfer_batch:996, execute_transfer_batch:1000 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\services\country\country_ai_research.py` | sequential external calls: _fetch_web_evidence (2 calls), _generate_ai_modules (2 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\services\country\country_ai_research.py` | external call(s) missing timeout: _fetch_web_evidence:370, _generate_ai_modules:403 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\services\country\country_data_orchestrator.py` | sequential external calls: __aenter__ (2 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\services\country\country_data_orchestrator.py` | external call(s) missing timeout: __aenter__:32 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\services\country\country_detection.py` | sequential external calls: _lookup_ipapi (2 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | HL602 | concurrency | `backend\services\country\country_detection.py` | external call(s) missing timeout: _lookup_ipapi:106 | always set timeout; add retry + circuit breaker |
| [HP] Health | HL601 | concurrency | `backend\services\country\cross_border_service.py` | sequential external calls: detect_country_from_ip (2 calls) | use asyncio.gather or ThreadPoolExecutor; add timeout + retry |
| [HP] Health | PG102 | polyglot | `backend\services\communication\websocket_chat.py` | WebSocket handler in Python: get_websocket_chat_service | Python for business logic; Node.js gateway for high-throughput real-time |
| [HP] Health | PG102 | polyglot | `backend\services\communication\websocket_manager.py` | WebSocket handler in Python: connect_staff, connect_user | Python for business logic; Node.js gateway for high-throughput real-time |
| [HP] Health | HL501 | performance | `backend\services\ai\ai_service.py` | heavy top-level import(s): PIL | lazy-import inside the function/job that needs them |
| [HP] Health | HL501 | performance | `backend\services\ai\bg_removal_service.py` | heavy top-level import(s): PIL, numpy | lazy-import inside the function/job that needs them |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\countries.py` | list endpoint(s) missing pagination: list_country_commission_rates | add skip/limit or cursor pagination |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\finance.py` | list endpoint(s) missing pagination: get_ledger, get_vat_liability, get_payout_batches, get_cash_position, supplier_earnings_report | add skip/limit or cursor pagination |
| [HP] Health | PG103 | polyglot | `backend\routers\supplier\supplier.py` | CPU-bound in request path: get_upload_history | offload to worker (Celery/arq) or Node.js worker thread |
| [HP] Health | HL501 | performance | `backend\routers\supplier\supplier_bg_ab_test.py` | heavy top-level import(s): PIL, numpy | lazy-import inside the function/job that needs them |
| [HP] Health | PG103 | polyglot | `backend\routers\supplier\supplier_bg_ab_test.py` | CPU-bound in request path: ab_test_bg_strategies | offload to worker (Celery/arq) or Node.js worker thread |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\supplier_documents.py` | list endpoint(s) missing pagination: list_my_documents, list_all_documents | add skip/limit or cursor pagination |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\supplier_finance.py` | list endpoint(s) missing pagination: get_supplier_payout_summary | add skip/limit or cursor pagination |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\supplier_health.py` | list endpoint(s) missing pagination: list_supplier_health | add skip/limit or cursor pagination |
| [HP] Health | PG103 | polyglot | `backend\routers\supplier\supplier_orders.py` | CPU-bound in request path: get_parcel_verification_history | offload to worker (Celery/arq) or Node.js worker thread |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\supplier_orders.py` | list endpoint(s) missing pagination: list_supplier_orders, get_supplier_label | add skip/limit or cursor pagination |
| [HP] Health | SC101 | scaling | `backend\routers\supplier\supplier_payouts.py` | list endpoint(s) missing pagination: list_payouts | add skip/limit or cursor pagination |
| [HP] Health | PG103 | polyglot | `backend\routers\security\fraud_detection.py` | CPU-bound in request path: list_fraud_events | offload to worker (Celery/arq) or Node.js worker thread |
| [HP] Health | SC101 | scaling | `backend\routers\security\fraud_detection.py` | list endpoint(s) missing pagination: list_blacklist, list_rules, list_review_queue | add skip/limit or cursor pagination |

---

## Findings by Domain

| Domain | Findings |
|---|---:|
| backend | 968 |
| database | 729 |
| models | 471 |
| react | 338 |
| error-handling | 210 |
| frontend | 168 |
| observability | 165 |
| python | 156 |
| api-health | 130 |
| mobile_app | 84 |
| design | 47 |
| scaling | 46 |
| concurrency | 33 |
| logging | 30 |
| repo | 28 |
| memory | 25 |
| web_app | 24 |
| analytics | 22 |
| services | 21 |
| polyglot | 20 |
| performance | 19 |
| security | 17 |
| frontend/components | 13 |
| controllers | 12 |
| mobile_app/shared/web_app | 9 |
| dev | 7 |
| frontend/supplier/products | 7 |
| shared/web_app | 6 |
| migrations | 5 |
| frontend/app | 5 |
| frontend/(tabs)/products | 5 |
| frontend/logistics-partner | 4 |
| frontend/admin/countries | 4 |
| deployment | 3 |
| frontend/lib | 3 |
| frontend/supplier | 3 |
| frontend/supplier/orders | 3 |
| frontend/supplier/bulk | 3 |
| frontend/supplier/batch-upload | 3 |
| frontend/products/[id] | 3 |
| frontend/admin | 3 |
| frontend/admin/payouts | 3 |
| frontend/admin/logistics | 3 |
| frontend/(tabs) | 3 |
| routers | 2 |
| docs | 2 |
| production | 2 |
| mobile_app/shared | 2 |
| frontend/components/admin | 2 |
| frontend/suppliers/[id] | 2 |
| frontend/supplier/upload | 2 |
| frontend/supplier/profile | 2 |
| frontend/profile | 2 |
| frontend/products | 2 |
| frontend/logistics-partner/profile | 2 |
| frontend/admin/treasury | 2 |
| frontend/admin/suppliers | 2 |
| frontend/admin/promotions | 2 |
| frontend/admin/payments | 2 |
| frontend/admin/hr | 2 |
| frontend/shared | 2 |
| pipeline | 2 |
| providers | 1 |
| ai | 1 |
| mobile_app/web_app | 1 |
| shared | 1 |
| documentation | 1 |
| frontend/components/supplier | 1 |
| frontend/tracking/[id] | 1 |
| frontend/tickets/[id] | 1 |
| frontend/supplier/reports | 1 |
| frontend/supplier/payouts | 1 |
| frontend/supplier/labels | 1 |
| frontend/supplier/analytics | 1 |
| frontend/supplier/(auth) | 1 |
| frontend/orders/[id] | 1 |
| frontend/logistics-partner/shipments | 1 |
| frontend/logistics-partner/payouts | 1 |
| frontend/logistics-partner/(auth) | 1 |
| frontend/checkout | 1 |
| frontend/admin/users | 1 |
| frontend/admin/staff | 1 |
| frontend/admin/permissions | 1 |
| frontend/admin/orders | 1 |
| frontend/admin/finance | 1 |
| frontend/admin/ess | 1 |
| frontend/admin/employees | 1 |
| frontend/admin/dashboard | 1 |
| frontend/admin/commission | 1 |
| frontend/admin/command-center | 1 |
| frontend/tracking | 1 |
| frontend/suppliers | 1 |
| frontend/logistics-partners | 1 |
| frontend/(tabs)/orders | 1 |

---

## Fix Priority Roadmap

### Week 1 - P0 (Production Blockers)

- [HP] **SEC101**: raw SQL concatenation (lines: 149)
  - Fix: use parameterized queries / SQLAlchemy ORM
- [HP] **SEC105**: hardcoded credential (lines: 14, 34)
  - Fix: move to env vars / Vault / secrets manager
- [HP] **SEC105**: hardcoded credential (lines: 24)
  - Fix: move to env vars / Vault / secrets manager
- [HP] **SEC105**: hardcoded credential (lines: 472)
  - Fix: move to env vars / Vault / secrets manager
- [HP] **SEC105**: hardcoded credential (lines: 105, 265)
  - Fix: move to env vars / Vault / secrets manager
- [HP] **SEC105**: hardcoded credential (lines: 200)
  - Fix: move to env vars / Vault / secrets manager

### Week 2-3 - P1 (Scaling / Performance)

- **HL403** (1 findings): sync I/O inside async: batch_analyze_images_async:204 (open), _analyze_one:204 (open)
  - Fix: use aiofiles / async pathlib / run_in_executor
- **HL501** (18 findings): heavy top-level import(s): PIL, numpy
  - Fix: lazy-import inside the function/job that needs them
- **HL601** (15 findings): sequential external calls: _send_via_resend (2 calls), _send_via_smtp (2 calls)
  - Fix: use asyncio.gather or ThreadPoolExecutor; add timeout + retry
- **HL602** (18 findings): external call(s) missing timeout: _s3_client:321
  - Fix: always set timeout; add retry + circuit breaker
- **OB101** (5 findings): 62 modules missing structured logger
  - Fix: Add logger = logging.getLogger(__name__). Top: address_controller.py, admin_controller.py, audit_controller.py, categories_controller.py, compliance_controller.py +57 more
- **OB102** (3 findings): 82 modules missing request_id / correlation_id
  - Fix: Add X-Request-ID middleware in main.py (fixes all 82 at once). Top: address_controller.py, admin_controller.py, ai_controller.py, audit_controller.py, categories_controller.py +77 more
- **PG102** (10 findings): WebSocket handler in Python: websocket_background_jobs
  - Fix: Python for business logic; Node.js gateway for high-throughput real-time
- **PG103** (9 findings): CPU-bound in request path: get_upload_history
  - Fix: offload to worker (Celery/arq) or Node.js worker thread
- **SC101** (46 findings): list endpoint(s) missing pagination: list_country_commission_rates
  - Fix: add skip/limit or cursor pagination

### Month 2 - P2 (Maintainability)

Address P2 findings during regular development sprints.
Focus on the Top 30 Unhealthiest Files first.

### Ongoing - P3 (Hygiene)

Fix P3 findings opportunistically during related work.

---

## AI Governance Contract

**Before making ANY code change, the AI must:**

1. Read this report and understand current violations
2. Not introduce new P0/P1 violations
3. Follow the Python + JS polyglot strategy:

| Workload | Best Tool | Why |
|---|---|---|
| Business logic / orchestration | **Python** (FastAPI) | Readability, DB, ecosystem |
| Database operations | **Python** (SQLAlchemy) | ORM, migrations, RLS |
| ML / AI inference | **Python** (PyTorch) | Model ecosystem |
| File / media processing | **Python worker** (Celery/arq) | Background, not request path |
| High-throughput JSON | **Python + orjson** or **Node.js sidecar** | 3-10x faster |
| Real-time WebSocket | **Node.js** gateway + Python backend | 100k+ connections |
| Edge / CDN functions | **Node.js** (Cloudflare/Vercel) | Cold start < 5ms |
| Frontend rendering | **React / Next.js** | Component model, SSR/SSG |
| Client-side CPU work | **Web Worker** or **WASM** | Keep main thread free |

4. Place files in correct domain folders
5. Use structured logging (no print, no console.log)
6. Add response_model to all new endpoints
7. Use cursor pagination (never OFFSET)
8. Add timeout to all external calls
9. Use bulk operations (never N+1 loops)
10. Run this audit before submitting: `python scripts/run_all_audits.py --no-fail`

---

## Individual Audit Reports

| Auditor | Report | JSON |
|---|---|---|
| [ARCH] Architecture | `ARCHITECTURE_AUDIT_REPORT.md` | `out/governance/architecture_audit.json` |
| [DB] Database | `DATABASE_AUDIT_REPORT.md` | `out/governance/database_audit.json` |
| [UI] Design | `DESIGN_AUDIT_REPORT.md` | `out/governance/design_audit.json` |
| [HP] Health | `HEALTH_AUDIT_REPORT.md` | `out/governance/health_audit.json` |

---

*Generated by run_all_audits.py v2.0 at 2026-08-01T19:28:45.803152+00:00*
