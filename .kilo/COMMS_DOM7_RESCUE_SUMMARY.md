# COMMS / DOM7 / W1 Rescue — Anchored Summary

## Goal
- Clean up DOM7 duplicate/non-canonical domain folders (DONE); run a W1 pilot on `comms_unified.py` (DONE, incl. CIR2 controller); then VERIFY the remaining audit findings (W1/Q1/DG2/API2/DOM2/DOM3) for correctness, and START resolving the ones that are correct.

## Constraints & Preferences
- NEVER modify `scripts/` (read-only) or `SYSTEM_AUDIT_REPORT.md`.
- NEVER delete a file before confirming zero imports reference it; never rename/move without atomically updating ALL imports; never break an import chain.
- NEVER modify `backend/main.py` router registration until a module is fully wired.
- No hardcoded values; config from environment.
- Run app + tests after each module; one module at a time.
- Take advisories seriously.

## Progress
### Done
- DBA07 fixed in `backend/models/comms/marketing.py` (4 pass).
- 23 service-file duplicate consolidation (SYM2/D3): `comms/` canonical; 9/9 rescue tests pass.
- DOM7 `communication/` cleanup: deleted 3 dirs/shims; repointed `models/__init__.py` + 15 `schema_mapping.json` entries; 9/9 rescue tests pass.
- DOM7 `country`/`uploads`/`products`/`suppliers` cleanup: deleted 7 empty package dirs; auditor run6 → DOM7 = 0.
- W1 pilot — `routers/comms_unified.py` → `services/comms/unified_inbox_service.py`:
  - Created `backend/services/comms/unified_inbox_service.py` with `reset_unified_inbox(db, *, user_id, username, user_role, ip_address)` (seed + audit) and `get_unified_inbox(db, *, user_id, lens, cursor, limit, transport)` (raw-SQL read).
  - Refactored `backend/routers/comms_unified.py` to a thin orchestration layer (imports service as `_reset_unified_inbox` / `_get_unified_inbox` to avoid name collision with the endpoint `reset_unified_inbox`). All DB access now in the service.
  - Fixed 3 pre-existing latent runtime bugs in the original reset endpoint (it would have 500'd):
    1. `from seed_comms import seed` → wrong module; corrected to `from jobs.seed_all import seed_comms` (the real function, no args).
    2. `AuditAction.INBOX_RESET` does not exist (`AuditAction` only has create/update/delete/...); now uses `action="inbox_reset"`.
    3. `audit_log(...)` was called with non-existent kwargs (`user_id`, `resource_type`, `status`, `resource_id`); corrected to the real signature `audit_log(db, actor_id, action, entity, entity_key, details=..., ip_address=...)`.
  - New test `tests/test_comms_unified_inbox_service.py` (6 pass): query-building/shape, cursor decode, reset success (seed + success audit), reset failure (failure audit + reraise), and router delegation (W1).
  - Auditor run7: `comms_unified.py` W1 = 0 and Q1 = 0.
  - Residual: new 🟡 CIR2 ("router → service skips orchestration layer"). Advisory only; strict router→controller→service circuit compliance is out of pilot scope.

- CIR2 circuit compliance (next step, now DONE):
  - Created `backend/controllers/comms/unified_inbox_controller.py` — thin wrapper importing `services.comms.unified_inbox_service` (aliased) and exposing `reset_unified_inbox(db, *, user_id, username, user_role, ip_address)` and `get_unified_inbox(db, *, user_id, lens, cursor, limit, transport)`. Matches the existing `controllers/comms/comm_controller.py` style.
  - Repointed `backend/routers/comms_unified.py` import from `services.comms.unified_inbox_service` → `controllers.comms.unified_inbox_controller` (aliases unchanged), so the router no longer imports a service directly.
  - Verification: `import main` → 153 routes; `tests/test_comms_unified_inbox_service.py` + `tests/test_comms_controller_rescue.py` → 11 passed; auditor run8 → NO CIR2 for `comms_unified.py` and NO CIR2 for the new controller (CIR2 only flags routers→services, not controllers→services). Run8 totals 🔴287 🟡4761 🟢79 (±noise vs run7 🔴286 🟡4758).

  - Verification: `import main` OK; new modules import cleanly; auditor run9 → `flash_sales.py` **W1 cleared** (now only Q1/RN1/API101/SC101, all advisory); **no new CIR2**; overall 🔴279 🟡4765 🟢79 (red down vs run8 🔴287). New 🟢 DOM6 (info) flags `flash` as a candidate domain from the two flash controllers — informational only.

- W1 incremental resolution (started): `routers/flash_sales.py`
  - Created `backend/services/commerce/flash_sale_service.py` (`create_flash_sale(db, payload)` — replicates the router's exact inline write: FlashSale + FlashSaleItem rows, commit, refresh).
  - Created `backend/controllers/flash_sales_controller.py` (`create_flash_sale(db, payload)` — thin wrapper; clears CIR2).
  - Repointed `backend/routers/flash_sales.py` to call the controller; removed inline `db.add/commit` and unused `FlashSale`/`FlashSaleItem` imports. Behavior preserved (returns the ORM row; no audit added).
  - Note: the pre-existing `backend/controllers/flash_sale_controller.py` (singular) is itself BROKEN (self-aliases `create_flash_sale_svc = create_flash_sale`, references non-existent `AuditAction.FLASH_SALE_CREATED`, and calls `audit_log` with wrong kwargs). Left untouched (separate latent bug; repairing it is a larger tangent).

### In Progress
- W1 incremental resolution across the remaining 42 routers (pattern: router → `controllers/<domain>/*_controller.py` → `services/<domain>/*_service.py`); started with `flash_sales.py`.

### Blocked
- None.

## Verification of remaining audit findings (done first, per request)
Run8 counts: W1=44 (43 files), Q1=115, DG2=60, API2=106 (capped 100), DOM2=19, DOM3=2.

- **W1 (routers/controllers write to DB)** — CONFIRMED CORRECT. AST-based: flags real `session.add/commit/execute(WRITE)` in routers. Verified on `routers/admin_commission.py` (lines 66/85/108/125). Genuine architectural violation; resolvable incrementally (router→controller→service).
- **Q1 (reads via .query()/execute SELECT in routers)** — same convention; correct but advisory.
- **DG2 (circular deps)** — PARTIAL. The `models/__init__.py` module cycle (`models → models.orders → models`) is REAL (submodules do `from . import Base`, re-entering package init). Domain-graph cycles (e.g. `comms → orders → comms`) are import-structure artifacts. Resolving the models cycle is a high-risk FOUNDATIONAL refactor (touches every model import).
- **API2 (private symbol used externally)** — detection works but it is a CONVENTION/style flag: flags any `_`-prefixed symbol used in another module. Verified `_ALLOWED_TABLES` is a `frozenset` used only inside its own module; `command_center_query_service` defines its OWN same-named symbol. Bulk "fixing" 100+ is cosmetic churn / high regression risk. NOT recommended to mechanically resolve.
- **DOM2 (wrong-folder inference)** — HEURISTIC placement inference; sample `controllers/admin/analytics.py` is a FALSE POSITIVE (legitimately an admin controller; detection keyed on the filename token "analytics"). Many findings expected false positives. NOT safe to apply mechanically.
- **DOM3 (surface folder in domain layer)** — structural rule; `controllers/admin` is a SURFACE folder. Technically consistent with convention, but moving ~30 admin files is a high-risk bulk move. Not recommended as a mechanical fix.

## Resolution decisions
- W1/Q1: resolve incrementally (verified-correct), one file at a time, with full import + test + re-audit verification. 1 file done (`flash_sales.py`).
- API2 / DOM2 / DOM3: do NOT mechanically churn (false-positive-prone / cosmetic / high-risk bulk moves).
- DG2 `models/__init__.py` cycle: defer to a dedicated, careful foundational refactor (out of scope for incremental cleanup).

## Key Decisions
- W1 pilot scoped to ONE file (`comms_unified.py`) per user choice; did NOT touch the other 239 W1 sites.
- Kept `main.py` registration `("comms_unified", "/api/v1/comms")` unchanged.
- Aliased service imports in the router (`_reset_unified_inbox` / `_get_unified_inbox`) to avoid the endpoint/function name collision that would have caused infinite recursion.
- Chose literal `action="inbox_reset"` over editing the shared `AuditAction` enum, to minimize blast radius on a widely-used module.
- Created `backend/controllers/comms/unified_inbox_controller.py` to satisfy the CIR2 circuit rule (router→controller→service); the controller just delegates, all DB logic stays in the service.

## Next Steps
- (In progress) Continue W1 incremental resolution for the remaining 42 routers (verify each: import + tests + re-audit). Highest-value/safest next: small self-contained routers.
- (Recommended skip) API2 / DOM2 / DOM3 — false-positive-prone / cosmetic / high-risk bulk; do not mechanically resolve.
- (Deferred) DG2 `models/__init__.py` cycle — dedicated foundational refactor.
- (Opportunistic) Q1 (115 reads) — advisory; resolve alongside W1 where natural.

## Critical Context
- Test harness: venv `backend/venv/Scripts/python.exe`; run with `PYTHONPATH=backend`, `APP_ENV=test`, `CSRF_DISABLED=true`, `SECRET_KEY=test-secret-key-for-pytest-only`, `FIELD_ENCRYPTION_KEY=test-field-key-00000000000000000000000000000000000`. Tests live at repo-root `tests/`.
- Auditor: zero-arg; auto-detects repo root; writes `SYSTEM_AUDIT_REPORT.md`; run `python scripts/system_trackers/system_architecture_audit.py` from project root. >120s; non-deterministic 🔴 (±1–2) via `learned_domain_edges`. W1 detection flags routers/controllers with `db.add/commit/query/execute` writes; Q1 flags `.query()` reads.
- `utils.audit.audit_log` real signature: `audit_log(db, actor_id, action, entity, entity_key, before=None, after=None, details=None, ip_address=None)` → stores `AuditLog` row; returns bool; swallows its own exceptions. `AuditAction` enum has NO `INBOX_RESET`.
- `jobs.seed_all.seed_comms()` takes no args, creates its own `SessionLocal()`, clears + re-seeds comms tables.
- `services/comms/communication_read_service.py:39` already has `execute_unified_inbox_query` (used elsewhere); the new service replicates the router's exact SQL to preserve behavior.

## Relevant Files
- `backend/services/comms/unified_inbox_service.py` — NEW; holds all comms_unified DB access (W1 fix).
- `backend/controllers/comms/unified_inbox_controller.py` — NEW; thin router→service wrapper (clears CIR2).
- `backend/routers/comms_unified.py` — thin orchestration; imports controller (not service) → no CIR2.
- `tests/test_comms_unified_inbox_service.py` — NEW; 6 pass.
- `backend/jobs/seed_all.py:602` — `seed_comms()` (correct seed source).
- `backend/utils/audit.py:33` — real `audit_log` signature (no `INBOX_RESET`; kwargs differ from original router).
- `backend/main.py:248` — `("comms_unified", "/api/v1/comms")` registration (unchanged).
- `backend/controllers/comms/comm_controller.py` — reference style for the new controller.
- `backend/services/comms/communication_read_service.py:39` — existing `execute_unified_inbox_query` (read helper).
- `SYSTEM_AUDIT_REPORT.md` — run9; flash_sales W1 cleared, no new CIR2.
- `audit_run9.log` — 🔴279 🟡4765 🟢79 debt=125241.
- `backend/services/commerce/flash_sale_service.py` — NEW; flash_sales write (W1 fix).
- `backend/controllers/flash_sales_controller.py` — NEW; thin wrapper (clears CIR2).
- `backend/routers/flash_sales.py` — repointed to controller; W1 cleared.
- `backend/controllers/flash_sale_controller.py` — PRE-EXISTING, BROKEN (self-alias + missing AuditAction + wrong audit_log kwargs); separate latent bug.
- `scripts/system_trackers/system_architecture_audit.py` — read-only.
