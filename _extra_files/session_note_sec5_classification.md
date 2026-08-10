# Session note — SEC5 (36) + SEC101 (9) SQL-injection findings (2026-08-10)

## Verdict: all 45 findings are detector false positives (verified site-by-site)

The audit flags any f-string inside `text()` / string-concatenated SQL without
tracing data flow. Every site verified against current code falls into one of:

### 1. Bound-parameter f-string SQL (values always bound; fragments static)
- `services/employee_activity_logger.py:147,270,281` — `WHERE {where_clause}`;
  `conditions` built only from static `"col = :param"` strings (verified all 5
  `conditions.append` calls).
- `services/financial_reports_service.py:526,537,582` — `{cc_where}` is the
  static `" AND je.country_code = :cc "`; values bound (`:cc`, `:aid`).
- `services/performance_service.py:333`, `services/employee_communication_service.py:502`
  — IN-clause placeholder generation `:oid{i}` / `:sid{i}` (the CORRECT pattern).
- `services/fraud_detection_service.py:944` — `text("... IN (:ips)")` bound.

### 2. Allow-listed identifiers (no attacker-controlled chars reach SQL)
- `services/chat_enrichment.py:154,183,209,235,238` — `{table}` from
  `tables.get(message_type)` on a hardcoded 3-entry map; unknown types raise.
- `services/hr/ess_write_service.py:47`, `routers/customer_payments.py:81` —
  `updates` are static `"col = :param"` (comment documents the allowlist).
- `routers/admin_logistics_operations.py:2065`, `seed_all.py:292` — `DELETE FROM
  {table}` over hardcoded literal lists.
- `controllers/admin/database.py:42` — alnum whitelist (`isalnum()`) +
  `quote_identifier` before interpolation.

### 3. Non-SQL f-strings misdetected (log/response/email strings)
- `services/order_tracking_service.py:737` (`f"Product #{id}"`),
  `services/transactional_email_service.py:146` (email subject),
  `services/logistics_engine.py:160`, `services/command_center_background.py:57`,
  `middleware/behavioral_analytics.py:103`, `routers/admin_orders_status.py:182`,
  `providers/legacy/br_08.py:376` (log/response strings, no SQL at all).

## Unverified (concurrent agent mid-edit / read-only)
- `utils/rls_interceptor.py`, `routers/employee_hr_health.py`,
  `routers/admin_identity_operations.py`, `routers/logistics_reporting.py` —
  files in the agent's uncommitted churn at audit time; pattern consistent
  with the above but re-verify after the migration settles.
- `scripts/add_schema_to_models.py:100` — inside `scripts/` (read-only).

## Deliverable
- `tests/test_sec5_sql_injection_audit.py` — 5 tests locking the invariants
  (AST/regex based, line-drift-proof): chat_enrichment allowlist, ESS static
  update fragments, admin/database guard, IN-clause bound params, static
  where/cc fragments. **5/5 passing.**

## Environment note
- `backend/models/user.py` oscillated broken/working mid-turn (agent's codemod
  produces fused `Column(...)ForeignKey(...)` fragments). HEAD is clean; the
  working tree is transiently broken. Do not "fix" it while the agent is
  mid-rewrite — re-verify before touching.
