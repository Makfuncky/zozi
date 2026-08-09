# Admin Controllers Module — Remediation Notes

Module under rescue: `backend/controllers/admin`
Audit source of truth: `SYSTEM_AUDIT_REPORT.md` (read-only; not regenerated this session to honor "never modify" constraint).

## Findings verified against source

| Code | File:Line | Claim | Verdict | Action |
|------|-----------|-------|---------|--------|
| SEC101 | `controllers/admin/database.py:42` | raw SQL concat (injection) | AUTHENTIC | FIXED — replaced `text(f"SELECT COUNT(*) FROM {quoted}")` with `select(func.count()).select_from(table(table_name))` (validated name, no interpolation). |
| SEC5 | `controllers/admin/database.py:42` | potential SQL injection | AUTHENTIC | FIXED — same change as SEC101. |
| SEC5 | `controllers/admin/users.py:369` | potential SQL injection | FALSE POSITIVE | `detail=f"User has related records that must be archived or removed before deletion."` is an `HTTPException` message, not SQL. Documented below. |
| SEC5 | `controllers/admin/users.py:791` | potential SQL injection | FALSE POSITIVE | `f"Successfully updated {len(user_ids)} staff account(s)"` is a return message, not SQL. Documented below. |
| W4 | `controllers/admin/users.py:84-85` | controller imports another controller | AUTHENTIC | FIXED — `users.py` no longer imports `controllers.admin.analytics` / `controllers.admin.admin_auth`. Shared symbols moved to `utils/admin_shared.py`. |
| API2 | `controllers/admin/analytics.py:322` | private `_ALLOWED_BANK_ACCOUNT_KINDS` used externally | AUTHENTIC (API2) | FIXED — made public as `ALLOWED_BANK_ACCOUNT_KINDS` in `utils/admin_shared.py`; `users.py` updated. |
| W1 | `controllers/admin/orders.py:134` | controller manages DB transaction (`with db.begin_nested():`) | AUTHENTIC | UNRESOLVED — see Critical Gap below. |
| DG2 | `controllers.admin -> users -> admin_auth -> auth_controller -> admin_controller -> controllers.admin` | circular dependency | AUTHENTIC (partial) | PARTIALLY ADDRESSED — removed the `users -> analytics/admin_auth` edges. The deeper `admin_auth -> auth_controller -> admin_controller -> controllers.admin` cycle remains (large flat files; needs dedicated work). |

## Changes made

1. `backend/controllers/admin/database.py`
   - `_table_row_count` now uses `select(func.count()).select_from(table(table_name))` (SQLAlchemy construct, no f-string). `table_name` is still validated (`alnum + "_"`).

2. `backend/utils/admin_shared.py` (NEW)
   - `VALID_USER_ROLES`, `ALLOWED_BANK_ACCOUNT_KINDS`, `require_admin_role()` — no controller/ORM dependencies.

3. `backend/controllers/admin/analytics.py`
   - Imports `VALID_USER_ROLES` / `ALLOWED_BANK_ACCOUNT_KINDS` from `utils.admin_shared`; removed local definitions (kept available via package `from .analytics import *`).

4. `backend/controllers/admin/admin_auth.py`
   - `_require_admin` now delegates to `require_admin_role` from `utils.admin_shared` (re-export preserved for backward compatibility).

5. `backend/controllers/admin/users.py`
   - Imports `VALID_USER_ROLES`, `ALLOWED_BANK_ACCOUNT_KINDS`, `require_admin_role` from `utils.admin_shared`.
   - Renamed all `_ALLOWED_BANK_ACCOUNT_KINDS` -> `ALLOWED_BANK_ACCOUNT_KINDS` and `_require_admin(` -> `require_admin_role(`.

## FALSE POSITIVE detail (SEC5 users.py:369 / :791)

The audit's SQL-injection detector flags any f-string near these lines as "string interpolation in SQL query".
Both lines are user-facing messages built with `f"..."`, with NO SQL `text()`/`.execute()` anywhere in scope:
- `users.py:369` -> `HTTPException(status_code=409, detail=f"User has related records that must be archived or removed before deletion.")`
- `users.py:791` -> `return {"message": f"Successfully updated {len(user_ids)} staff account(s)", ...}`

No remediation required. The detector pattern is too broad (flags all f-strings, not only SQL). Not editing the audit script (read-only constraint).

## RESOLVED — recovered 9 lost functions (was CRITICAL GAP)

`services/users_write_service.py` is a re-export **shim** (lazy `__getattr__`). It re-exports 3 symbols
(`delete_bank_account_record`, `toggle_user_active`, `update_user_role`) from `controllers.admin.users` (lazy, to
avoid the `users -> users_write_service -> users` import cycle). The other functions were **lost** when commit
`3d1f49a` ("fixed_voliations_04-08-2026") replaced their real implementations with `_missing_symbol` stubs.

**Recovery (per user decision: "Restore into new canonical module"):** the real implementations were recovered from
`624a1a2` into a NEW canonical module `backend/services/users/user_write_ops.py`
(`backend/services/users/__init__.py` added as package marker). `services.users_write_service` now re-exports them:

- `_delete_order_records`  (called by `controllers/admin/orders.py:135` and `controllers/admin/users.py:354`)
- `_build_user_delete_blocker`  (called by `users.py:341, 413`)
- `_hard_delete_user_record`  (called by `users.py:363`)
- `_delete_user_owned_records`, `_nullify_user_references` (cascade helpers)
- `create_staff_user`  (called by `users.py:624`)
- `force_reset_password`  (called by `users.py:468`)
- `update_bank_account_verification`  (called by `users.py:897`)
- `update_staff_user`  (called by `users.py:587, 690, 771`)
- `create_chatbot_query_event`, `update_user_browsing_history` (analytics/UX side-effects)

These are **real, behavior-preserving implementations** — not stubs. The endpoints
`bulk_delete_orders_admin`, `delete_order_admin(delete_orders=True)`, `delete_user_admin`, `force_reset_password_admin`,
`create_staff_account`, `update_staff_account`, `bulk_update_staff_accounts` now execute real code instead of raising
`NotImplementedError`.

**Fixes applied during recovery:**
- Import path corrected `from models import ...` → `from data.models import ...` (would have `ModuleNotFoundError` otherwise).
- `ShippingZone` added to the `data.models` imports (referenced by `_DELETABLE_USER_OWNED_MODELS` but missing in the
  original — would have `NameError` on import).

**Deliberately NOT regressed:** `toggle_user_active`, `update_user_role`, `delete_bank_account_record` remain the
newer/canonical versions in `controllers/admin/users.py` (they carry audit/`acting_user` handling). The shim's lazy
re-exports point at those rather than at any old copy.

**Verification:** `backend/tests/test_users_write_ops_recovery.py` (20 tests) asserts the 9 symbols are real
callables (not `_missing_symbol` stubs), the shim resolves them to `user_write_ops`, the 3 lazy re-exports resolve to
`controllers.admin.users`, and the deletion/protection logic (`_build_user_delete_blocker`) and staff-user CRUD work
against a rollback `db_session`. All pass.

## Verification done this session

- `python -m py_compile` on all modified files: PASS.
- Static re-check: `users.py` no longer contains `from controllers.admin...` imports; no remaining `_ALLOWED_BANK_ACCOUNT_KINDS` / `_require_admin` references.
- Recovery test: `python -m pytest tests/test_users_write_ops_recovery.py -q` → 20 passed. Confirms the 9 recovered
  functions are real (not `_missing_symbol` stubs), the shim resolves them, and the deletion/protection logic works.
- Import smoke test: `python -c "import controllers.admin, services.users_write_service, controllers.admin.users"`
  succeeds (no circular-import / `NameError` / `ModuleNotFoundError`).
- Audit script NOT re-run: it is hard-coded to overwrite `SYSTEM_AUDIT_REPORT.md` ("ZERO arguments. ZERO flags. Single output"), which conflicts with the "never modify SYSTEM_AUDIT_REPORT.md" constraint. Recommend running it in CI / a separate step after this module is complete.

## OUT OF SCOPE — broader `_missing_symbol` stubs (flagged, not fixed)

A repo-wide grep shows `_missing_symbol` stubs remain across many `services/*` shims (e.g. `banner_write_service`,
`commission_write_service`, `disputes_write_service`, `employee_write_service`, `hr_write_service`, `iam_write_service`,
`invoice_write_service`, `logistics_partner_write_service`, `logistics_write_service`, `admin_analytics_service`,
plus `models/upload_job.py` and `routers/_permission_primitives.py`). These are NOT in `controllers/admin` and are
outside the audit's verified-findings scope, so they were left untouched pending a dedicated, scoped remediation pass.
Notably `services/misc_write_service.py` still stubs `reset_demo_data` (its record-delete trio was already re-pointed
to `utils.soft_delete` in an earlier step).

## PER-SERVICE STUB VERIFICATION (git prohibited)

Decision: user chose "Verify matches only" — inspect each name-matched candidate and rewire only the genuine
canonical impls; leave the rest stubbed. **No git was used** (read-only code search + a temp analyzer only).

Inventory of every `_missing_symbol` stub (~100 symbols across 13 service shims + `models/upload_job.py` +
`routers/_permission_primitives.py`). Of these, only ~10 had a same-named `def` elsewhere in the working tree; on
inspection they are **not** the canonical impls for the shim symbols:

- `create_shipment_event` / `delete_shipment` / `refresh_model` / `update_shipment_event` / `add_notification`
  (matched in `services/suppliers_write_service.py`) — those defs are `(*_args, **_kwargs)` no-op placeholders, i.e.
  themselves stubs. Cross-domain collision. **Left stubbed.**
- `purchase_supplier_badge` (matched in `routers/supplier.py`) and `refresh_supplier_badge`
  (matched in `routers/admin.py`, `routers/admin_suppliers.py`) — these are HTTP route handlers, wrong layer
  (services must not import routers). **Left stubbed.**
- `update_order` (matched in `services/orders/orders_write_service.py` from `logistics_partner_write_service`) —
  ambiguous cross-domain match; left stubbed (conservative).

**Verified rewire (the only genuine one):** `services/orders_write_service.py` had `_missing_symbol` stubs for
`create_order`, `create_order_item`, `update_order`. Their real ORM row-writers exist in the canonical
`services/orders/orders_write_service.py` (`create_order(db, **order_data)`, `create_order_item(db, order_id, **item_data)`,
`update_order(db, order, updates)`) — exactly the row-writers the shim's own comment described. Re-pointed the shim's
lazy `_REEXPORTS` to import them from that canonical module and removed the dead `_missing_symbol` helper.

**Guard test:** `backend/tests/test_orders_write_service_rewire.py` (4 tests) asserts the 3 symbols resolve to the
canonical module and that no `_missing_symbol` stub remains. All pass.

**Net result:** 3 symbols recovered (orders row-writers); ~97 stubs remain because their implementations do not exist
anywhere in the working tree (and git is off-limits, so they cannot be recovered from history). Restoring them would
require writing ~97 new functions from scratch (feature work, no spec) — intentionally NOT done.
