# Task Plan — ZOZI Backend: Actual Migration to NEW_STRUCTURE.md

**Goal:** Make the backend *actually* conform to `documents/NEW_STRUCTURE.md` —
code must import `domains/` + `modules/` + `rbac/` + `kernel/` + `infrastructure/`
instead of legacy shims, and `backend/_legacy/` must be deleted. The migration
is currently **cosmetic** (skeleton exists; 1745 `from services.`, 1676
`from models`, 474 `from controllers.` still resolve via `_legacy`). This plan
tracks every change end-to-end.

**Tracking instruments (two, cross-checked):**
1. Automated — `scripts/system_trackers/system_architecture_audit.py` NS gate.
2. Manual — these planning files (`task_plan.md`, `findings.md`, `progress.md`).

**Hard rule:** No phase is "complete" until the audit's NS violations for that
phase are **0** AND `git` boot + `pytest` are green. Cosmetic folder creation
does NOT count as progress.

---

## Phase 0 — Baseline & tracking setup  [Status: in_progress]
**Goal:** Prove the current state, confirm the import-resolution mechanism, seed the debt ledger.
- [x] Measured import debt (1745/1676/474 services/models/controllers; 380 domains) — see `findings.md`
- [x] Confirmed audit gate present (`check_new_structure_compliance` L13793, wired L13970)
- [x] RESOLVED mechanism: `backend/main.py:17` `sys.path.append(.../_legacy)` — legacy re-exports under OLD names; new packages NOT what app runs (see `findings.md` §4)
- [ ] Capture audit NS violation list (audit running: `bgp_011aedbab001ALVN6OyXjJxR87`) → `findings.md` debt ledger
- [ ] Decide: keep `scripts/rewrite_imports.py` (referenced in doc) or write a new AST rewriter
- [ ] Note `domains/UNMAPPED/services` must be triaged in Phase 1

**Gate:** mechanism known; baseline committed to `findings.md`.

## Phase 1 — Taxonomy reconciliation  [Status: pending]
**Goal:** Authoritative `real → NEW_STRUCTURE` domain map (the doc invents
`customers/`, `suppliers/`, `accounts/`, `risk/`, `governance/` not present in
the real tree; real tree has `commerce`, `treasury`, `identity`, `permissions`,
`hierarchy`, `audit`, `delegators`(95), `router_bridges`(57), `core`(67)).
- [ ] Build mapping table: real service subfolder → target domain
- [ ] Decide homes for ambiguous piles: `core`, `delegators`, `router_bridges`, `commerce`, `treasury`
- [ ] Confirm module actors: customer/supplier/logistics/admin/employee
- [ ] Resolve `utils/` (67) → `infrastructure/utils` vs `kernel/`
- [ ] Resolve `db/` (12) → `infrastructure/database` (+ single RLS enforcer)

**Gate:** mapping table in `findings.md`; every real folder has a target.

## Phase 2 — Audit as the adoption tracker  [Status: pending]
**Goal:** Extend the audit so it measures *real adoption*, not just shape.
- [ ] Add a "real adoption" metric: ratio `from domains.` / (`from services.`+`from models`+`from controllers.`)
- [ ] Ensure NS11 fires while root `models/` canonical (it does)
- [ ] Ensure NS1–NS4 fire on `_legacy/` abolished layers (they do)
- [ ] Add per-domain debt counters to the report (so each wave is measurable)
- [ ] Wire CI (`architecture-gate.yml`) to fail on any RED NS code

**Gate:** audit prints per-domain adoption + NS counts; CI fails on RED.

## Phase 3 — Wave A: foundation (no dependents break)  [Status: pending]
**Goal:** Relocate leaf infrastructure with AST import-rewrite; keep app booting.
- [ ] `kernel/`: lift `money`/`numbering`/`country`/`period` from `utils`
- [ ] `infrastructure/security` + `redis` + `observability` from `utils`
- [ ] `rbac/`: seed `catalog/roles/resolution/dependencies/service/models` from `utils/staff_permissions.py`, `services/rbac_service.py`, `require_finance_permission`
- [ ] Run `rewrite_imports.py` for these; delete corresponding `_legacy` shim lines
- [ ] **Verify:** boot + `pytest` + audit NS for these packages = 0

**Gate:** Wave A packages import-clean; `_legacy` shim entries for them removed.

## Phase 4 — Wave B: per-domain relocation (smallest-first)  [Status: pending]
**Goal:** `git mv` real logic into `domains/<d>/`, rewrite imports, shrink shims.
- [ ] Pilot: `country` (small, touches RLS = 4th axis) end-to-end
- [ ] Then: comms, media, catalog, orders, payments, logistics, suppliers, customers, hr, finance, treasury, governance
- [ ] For each `d`: move `services/<d>/*`→`domains/<d>/services/`, `models` slice→`domains/<d>/models/`, `db/schemas.py` slice→`domains/<d>/schemas/`
- [ ] Rewrite: `services.<d>.`→`domains.<d>.services.`, `models`→`domains.<d>.models`, `db.`→`infrastructure.database.`, `utils.X`→`infrastructure.X`/`kernel.X`
- [ ] Remove `_legacy` shim lines for the slice; run audit per domain

**Gate per domain:** tests green, boot green, NS for that domain = 0, allowlist shrinks.

## Phase 5 — Wave C: controllers split → module routers  [Status: pending]
**Goal:** Each `controllers/<surface>/..._controller.py` → shell `modules/<m>/routers/<d>_router.py` + logic `domains/<d>/services/`.
- [ ] Retarget `auto_router.py` to emit into `modules/<m>/routers/` (keep AUTO-GENERATED marker)
- [ ] Split controllers by surface token; rewrite `from controllers.` → `from modules.`/`from domains.`
- [ ] Verify generated routers byte-equivalent via `auto_router.py --verify`

**Gate:** `from controllers.` = 0; routers mount under `/api/{m}`.

## Phase 6 — Wave D: retire flat routers + `_legacy`  [Status: pending]
**Goal:** Delete `_legacy/` once every slice is green.
- [ ] Delete `routers/*.py` (already missing at root — confirm) and `_legacy/routers` shim
- [ ] Delete `_legacy/{services,controllers,models,utils,db}` as each hits 0 refs
- [ ] Final: `backend/_legacy/` removed

**Gate:** `_legacy/` gone; full audit NS = 0; `DOMAIN_ALLOWLIST.yaml` = 0.

## Phase 7 — Law enforcement + frontend  [Status: pending]
**Goal:** Enforce the Seven Laws; align frontend to the catalog.
- [ ] `import-linter` / extended `coherence_gate`: `modules→domains→infrastructure`, no `domain→module`, cross-domain reads only via `ports.py`/`events.py`
- [ ] Swap `require_finance_permission`/`ADMIN_PERMISSION_MAP` → `require_feature("...")` + `rbac/`
- [ ] Country as 4th axis: single RLS enforcer + `country_staff_assignments`
- [ ] Frontend: add `web_app/src/lib/rbac.ts` (fetch `/rbac/catalog`); generate `shared/src/permissions.ts`; **delete `shared/src/adminPermissions.ts`**
- [ ] Align `web_app/src/app` route groups to modules; match `/api/{m}` prefixes

**Gate:** import-lint 0 violations; allowlist 0; frontend uses catalog not hardcoded map.

---

## Decisions Made
| Decision | Rationale |
|---|---|
| Trust disk, not the doc's reality-check | Doc lines 794–811 describe a pre-migration tree that no longer exists |
| Audit NS gate = automated tracker | It already catches false-migration; extend, don't rebuild |
| Real adoption measured by `from domains.` ratio | Folder shape alone is misleading (current proof) |

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| (none yet — Phase 0 in progress) | — | — |

## Next Step
Capture the running audit's NS violation list (`bgp_011aedbab001ALVN6OyXjJxR87`)
into the `findings.md` debt ledger, then begin Phase 1 taxonomy reconciliation
(build the real→target domain map; triage `domains/UNMAPPED`).
