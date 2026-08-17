# Router Re-home Plan — Checkpoint (saved 2026-08-17)

## Decision (answers the "do we have a router system?" question)
NEW_STRUCTURE.md KEEPS a router system. It re-homes routers from flat `backend/routers/`
into `backend/modules/{m}/routers/` (per actor: customer/supplier/logistics/admin/employee).
It ABOLISHES the `controllers/` layer (lines 442-457), NOT routers (line 484:
"Routers: they didn't vanish — they were re-homed per actor"). So we RE-HOME routers;
we do NOT delete them.

## Current verified state
- backend/routers/ = 329 router .py files (git-tracked) = the live source.
- backend/controllers/ = DOES NOT EXIST (gone).
- backend/modules/ = 100% UNTRACKED scratch (5 module dirs). admin/routers holds 199
  files whose basenames are NOT in backend/routers => unique/divergent content to
  RECONCILE, never bulk-delete.
- main.py:170 BROKEN: `from modules.routers.public_comms_status import websocket_user`
  (modules.routers does not exist) => app fails to boot.
- main.py also imports directly: routers.logistics_partner_verify, routers.core_countries_routes.
- Authoritative mapping: documents/CONTROLLER_SHIFT_PLAN.md Section 0.1 (329 rows).
  Counts: admin 226, employee 49, supplier 28, customer 14, logistics 12, manual 10.

## Point 1 — Boot fix
main.py:170 => `from routers.public_comms_status import websocket_user`.
(Re-pointed to module path in Point 3 once the file is moved.)

## Point 2 — modules/ skeleton
- backend/modules/__init__.py
- per m in admin,customer,employee,logistics,supplier:
    modules/<m>/__init__.py          (exists)
    modules/<m>/auth/__init__.py      (placeholder; real login later)
    modules/<m>/serializers/__init__.py
    modules/<m>/routers/__init__.py   exposing routers=[], public_routers=[]
- BACKUP the untracked scratch FIRST (preserve the 199 divergent files).

## Point 3 — Relocate 329 routers
1. Backup backend/modules => backend/_scratch_modules_backup (keep divergent files).
2. Recreate clean skeleton (Point 2).
3. For each mapping row: git mv backend/routers/<f> backend/modules/<m>/routers/<f>.
4. Generate modules/<m>/routers/__init__.py lists (routers / public_routers).
5. Rewrite main.py:_load_routers() to per-module discovery loop:
       for m in [customer,supplier,logistics,admin,employee]:
           pkg = import_module(f"modules.{m}.routers")
           for r in pkg.routers:        app.include_router(r, prefix=f"/api/{m}")
           for r in pkg.public_routers: app.include_router(r, prefix=f"/api/{m}")
6. Update 3 anchor imports to module paths (public_comms_status, logistics_partner_verify,
   core_countries_routes).
7. Import-rewrite any `from routers.X` inside moved files.

## Verification gates (all must pass)
- git status shows 329 files as RENAMED (history preserved).
- App boots; _load_routers() registers 329 routers.
- main.py syntax ok; no unresolved `routers.` imports.
- existing test suite / coherence_gate / auto_router --verify green.
- /ws/user and /ws/admin/background-jobs still register.

## Out of scope (later phases)
Domain logic, RBAC, real auth/, frontend route alignment, deleting _legacy.
