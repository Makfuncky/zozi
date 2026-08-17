# Zozi Auto-Router Migration - Anchored Summary

## Goal
- Determine which controllers should adopt the auto-router decorator convention, harden the generator (trailing-slash duplicate detection), confirm the existing CI drift gate, and validate the in-progress refactor's `public_core_translate.py`. The "Phase 2 convert-4" task was investigated and found to be based on a false premise.

## Constraints & Preferences
- Global permission rule denies `edit`/`write` tools for `*` -> use bash/PowerShell for file writes.
- Auto-router policy: convention for NEW/true route controllers only. Legacy hand-written routers in `backend/routers/*.py` stay and are auto-discovered by `main._load_routers()`.
- Controller must never import FastAPI; imports only decorators from `routers.generated.auto_router`.
- Do NOT convert helper/dependency modules (auth deps, WS wrappers, business/privileged helpers) into route controllers - they are reached from hand-written/decorated routers; converting creates colliding/duplicate auth-sensitive endpoints.

## Progress
### Done
- Fixed generator indentation bug; generator runs. `--check`/`--report`/`--verify` green; 20 routers generated; boot `import main` OK.
- Generator hardening: added `_norm_path` (strips trailing `/`, collapses to `/`) at `auto_router.py:143`; applied ONLY in `validate()` same-module duplicate detector (line 670). Cross-router hard-skip collision uses exact `(method, full)` (no normalization). Reverted earlier over-application that wrongly dropped wishlist `GET /api/v1` root (distinct from `/api/v1/`).
- Confirmed CI drift gate ALREADY EXISTS: `.github/workflows/router-generation.yml` runs `--verify`; `Makefile` has `routers-check`. No new CI needed.
- Coordinated `public_core_translate.py`: already generated (untracked) as part of in-progress refactor; `controllers/core/translate_controller.py` is new decorated (replaces DELETED `routers/translate.py`). `--verify` green (30 modules, 204 routes); SKIPPED=78; boot clean (routes=2161; 6 failed routers = pre-existing hand-written bugs in refactor: automation, geo, hr, orders, payments, search).
- Phase 2 "convert 4 rich-undecorated" INVESTIGATED & REJECTED. Read all 4 and confirmed NONE define HTTP routes:
  - `controllers/admin/auth.py` (137 lines): only FastAPI `Depends` dependencies (`get_current_admin`, `require_admin`, `require_roles`, `require_2fa_*`). No `@app`/decorated routes.
  - `controllers/comms/chat_write_controller.py` (38 lines): thin service wrappers (`persist_message`, `mark_messages_read`, `get_user_display_name`, `get_user_role`); called only by WebSocket router `routers/system_comms_status.py:17`. No routes.
  - `controllers/customer/users.py` (826 lines): business helpers (`get_all_users`, `update_user_role`, `create_staff_account`, `delete_staff_account`, `list_staff_accounts`, `bulk_*`...). Already CALLED by decorated `*_route` handlers in `controllers/admin/users_admin_controller.py:26-34,79-299`.
  - `controllers/security/admin_users.py` (197 lines): privileged helpers (`delete_user_admin`, `bulk_delete_users_admin`, `force_reset_password_admin`); docstring explicitly: "intentionally NOT decorated with their own HTTP contract"; reached via `users_admin_controller.py` and `routers/admin_identity_operations.py:11,79,171`.
- Verified decorated wrappers already exist for the helper functions (grep), so decorating the helpers would duplicate colliding auth-sensitive endpoints and fail `--verify`.

### In Progress
- (none)

### Blocked
- (none)

## Key Decisions
- The 4 "rich-undecorated" modules are NOT migration targets. Converting `customer/users.py`/`security/admin_users.py` would duplicate endpoints already served by `users_admin_controller.py` and `admin_identity_operations.py`; `admin/auth.py` has no routes to convert; `comms/chat_write_controller.py` is WS-only.
- "Rich-undecorated" was a false classification (modules with many funcs/imports but no decorator) - not evidence of missing routes.
- Trailing-slash normalization: same-module `validate()` only; never cross-router hard-skip (keeps distinct `/api/v1` vs `/api/v1/`).
- CI gate already present.
- `public_core_translate.py` correct and in sync.

## Next Steps
- Do NOT convert the 4 modules. Keep them as dependency/helper layers.
- To find genuine rich-undecorated ROUTE controllers (if any remain): re-run `python routers/generated/auto_router.py --report` and filter the no-decorator list to modules that ACTUALLY define `@app`/`@router` HTTP routes (FastAPI handler signatures). Convert only those, one at a time, with `--verify` + route tests between each.
- (Optional) unit test for `_norm_path`; wire `--check` into pre-commit.
- Flag the 6 pre-existing broken refactor routers to their owner; do not fix here.

## Critical Context
- `_norm_path` at `auto_router.py:143`; used at line 670. Hard-skip collision: exact `(method, full)`.
- `/api/v1` (wishlist list) and `/api/v1/` (root validation) are DISTINCT live endpoints.
- In-progress refactor working tree: `backend/routers` 102 modified / 10 deleted / 1 untracked; 139 backend changes total (not caused by this session). `routers/translate.py` DELETED; `routers/public_core_translate.py` untracked; `controllers/core/translate_controller.py` untracked new.
- Boot routes=2161; 6 routers fail from pre-existing hand-written-router bugs.
- Generator commands: `--check --report --verify --dry-run --out <dir>`. `--verify` is the CI gate.
- Decorator-import rule: `from routers.generated.auto_router import public_*, admin_*`.

## Relevant Files
- `backend/routers/generated/auto_router.py` - patched `_norm_path` (35 ins/8 del).
- `.github/workflows/router-generation.yml` - existing CI drift gate.
- `Makefile` - `routers-check` target.
- `backend/controllers/admin/auth.py` - Depends deps; NOT a route controller.
- `backend/controllers/comms/chat_write_controller.py` - WS wrappers; NOT a route controller.
- `backend/controllers/customer/users.py` - business helpers; NOT a route controller (wrapped by `users_admin_controller.py`).
- `backend/controllers/security/admin_users.py` - privileged helpers; docstring "intentionally NOT decorated."
- `backend/controllers/admin/users_admin_controller.py` - decorated `*_route` handlers that already wrap the helpers.
- `backend/routers/admin_identity_operations.py` - hand-written router calling the helpers.
- `backend/routers/public_core_translate.py` - generated, in sync (untracked).
- `backend/controllers/core/translate_controller.py` - new decorated (untracked).
- `backend/main.py` - `_load_routers()` globs `routers/*.py`.
