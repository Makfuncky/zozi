# ZOZI Forensic Audit — Frontend Web Technologies

## Agent ID: AGENT_FRONTEND_TECH
## Scope: frontend/web_app/package.json, pnpm-lock.yaml, tsconfig.json, next.config.ts, Dockerfile, frontend/shared/package.json, frontend/shared/tsconfig.json, pnpm-workspace.yaml
## Date: 2026-09-30T02:50:21Z

---

### Summary

| Category | Total Findings | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| Version Drift | 8 | 0 | 2 | 4 | 2 |
| Lockfile / Workspace | 3 | 0 | 1 | 1 | 1 |
| Build Output | 2 | 0 | 1 | 1 | 0 |
| Config | 2 | 0 | 1 | 1 | 0 |
| **Total** | **15** | **0** | **5** | **8** | **2** |

---

## Part A: Version Drift Findings

### TECH-FW-001: Next.js version mismatch

| Field | Value |
|---|---|
| **ID** | TECH-FW-001 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:30` |
| **Current** | `next: 16.3.4` |
| **Target** | `next: 16.3.5` |
| **Delta** | Next.js pinned 1 patch version behind canonical |
| **Fix** | Bump next to 16.3.5 |
| **Effort** | S (0.5h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-002 |
| **Verify** | `cd frontend/web_app && pnpm list next` |
| **Test** | `tests/frontend/test_versions.py::test_next_version` |
| **Rollback** | Revert package.json line 30 |
| **Blast radius** | Frontend build, SSR |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-002: TypeScript version mismatch

| Field | Value |
|---|---|
| **ID** | TECH-FW-002 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:56` |
| **Current** | `typescript: ~5.10` |
| **Target** | `typescript: 5.9.3` |
| **Delta** | package.json allows TypeScript 5.10.x, diverging from canonical 5.9.3 and lockfile 5.9.3 |
| **Fix** | Pin typescript to 5.9.3 |
| **Effort** | S (0.5h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-001 |
| **Verify** | `cd frontend/web_app && pnpm list typescript` |
| **Test** | `tests/frontend/test_versions.py::test_typescript_version` |
| **Rollback** | Revert package.json line 56 |
| **Blast radius** | Frontend type checking |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-003: framer-motion version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-003 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:26` |
| **Current** | `framer-motion: ^12.0.0` (lockfile: 12.43.0) |
| **Target** | `motion: 13.2.0+` (package renamed) |
| **Delta** | framer-motion v12 used; canonical requires motion v13+ with new package name `motion` and import path `motion/react` |
| **Fix** | Replace framer-motion with motion@13.2.0+ and update imports from `framer-motion` to `motion/react` |
| **Effort** | M (4h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-001 |
| **Verify** | `cd frontend/web_app && pnpm list framer-motion` |
| **Test** | `tests/frontend/test_motion_imports.py::test_motion_package` |
| **Rollback** | Revert package.json and imports |
| **Blast radius** | All animated components |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-004: @stripe/react-stripe-js version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-004 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:15` |
| **Current** | `@stripe/react-stripe-js: ^5.6.0` (lockfile: 5.6.1) |
| **Target** | `@stripe/react-stripe-js: 6.9.0` |
| **Delta** | Stripe React Elements pinned 1 major version behind canonical |
| **Fix** | Bump @stripe/react-stripe-js to 6.9.0 |
| **Effort** | S (1h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-005 |
| **Verify** | `cd frontend/web_app && pnpm list @stripe/react-stripe-js` |
| **Test** | `tests/frontend/test_stripe_elements.py::test_stripe_react_version` |
| **Rollback** | Revert package.json line 15 |
| **Blast radius** | Stripe card forms, checkout |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-005: @stripe/stripe-js version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-005 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:16` |
| **Current** | `@stripe/stripe-js: ^8.7.0` (lockfile: 8.11.0) |
| **Target** | `@stripe/stripe-js: 5.5.0+` |
| **Delta** | @stripe/stripe-js is at 8.11.0, exceeding canonical maximum of 5.5.0+; major version drift may break API compatibility |
| **Fix** | Downgrade @stripe/stripe-js to 5.5.0+ or update canonical stack to reflect v8 |
| **Effort** | S (1h) |
| **Priority** | P2 |
| **Confidence** | 4 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-004 |
| **Verify** | `cd frontend/web_app && pnpm list @stripe/stripe-js` |
| **Test** | `tests/frontend/test_stripe_js_version.py::test_stripe_js_compat` |
| **Rollback** | Revert package.json line 16 |
| **Blast radius** | Stripe Elements initialization |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-006: zustand version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-006 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:36` |
| **Current** | `zustand: ^5.0.11` (lockfile: 5.0.15) |
| **Target** | `zustand: 5.0.14` |
| **Delta** | zustand resolved to 5.0.15, 1 patch ahead of canonical 5.0.14 |
| **Fix** | Pin zustand to 5.0.14 |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && pnpm list zustand` |
| **Test** | `tests/frontend/test_versions.py::test_zustand_version` |
| **Rollback** | Revert package.json line 36 |
| **Blast radius** | Client state management |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

## Part B: Lockfile / Workspace Findings

### TECH-FW-007: pnpm-workspace.yaml missing at root

| Field | Value |
|---|---|
| **ID** | TECH-FW-007 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-workspace-config |
| **File:Line** | `pnpm-workspace.yaml` (root) |
| **Current** | No pnpm-workspace.yaml at repository root |
| **Target** | pnpm-workspace.yaml present at root defining workspace packages |
| **Delta** | Root lacks pnpm-workspace.yaml; only frontend/web_app/ and frontend/mobile_app/ contain local workspace configs with allowBuilds |
| **Fix** | Add canonical pnpm-workspace.yaml at root with workspace package globs |
| **Effort** | S (0.5h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-008 |
| **Verify** | `ls pnpm-workspace.yaml` |
| **Test** | `tests/frontend/test_workspace.py::test_root_workspace_exists` |
| **Rollback** | Remove root pnpm-workspace.yaml |
| **Blast radius** | Monorepo workspace resolution |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-008: pnpm-workspace.yaml allowBuilds incomplete

| Field | Value |
|---|---|
| **ID** | TECH-FW-008 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-workspace-config |
| **File:Line** | `frontend/web_app/pnpm-workspace.yaml:1-3` |
| **Current** | `allowBuilds: { core-js: true, unrs-resolver: true }` |
| **Target** | Workspace allowBuilds aligned with monorepo requirements |
| **Delta** | web_app pnpm-workspace.yaml allows `core-js` build, which is non-canonical per TECHNOLOGY_STACK.md |
| **Fix** | Remove `core-js` from allowBuilds or add canonical build exceptions only |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 4 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | TECH-FW-007 |
| **Verify** | `cat frontend/web_app/pnpm-workspace.yaml` |
| **Test** | `tests/frontend/test_workspace.py::test_allowbuilds_canonical` |
| **Rollback** | Revert pnpm-workspace.yaml to previous allowBuilds |
| **Blast radius** | pnpm install in web_app |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-009: postcss conflicting versions in lockfile

| Field | Value |
|---|---|
| **ID** | TECH-FW-009 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-lockfile-conflicts |
| **File:Line** | `frontend/web_app/pnpm-lock.yaml` (packages section) |
| **Current** | postcss@8.5.23 and postcss@8.5.28 both present |
| **Target** | Single postcss version resolved across workspace |
| **Delta** | pnpm-lock.yaml contains two postcss versions (8.5.23 and 8.5.28), indicating peer dependency resolution conflict |
| **Fix** | Align postcss to single version via overrides or peer resolution |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && grep -c "postcss@8.5.23" pnpm-lock.yaml && grep -c "postcss@8.5.28" pnpm-lock.yaml` |
| **Test** | `tests/frontend/test_lockfile.py::test_no_duplicate_versions` |
| **Rollback** | Revert pnpm-lock.yaml to previous postcss resolution |
| **Blast radius** | CSS processing pipeline |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

## Part C: Build Output Findings

### TECH-FW-010: Large chunk in build output

| Field | Value |
|---|---|
| **ID** | TECH-FW-010 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-bundle-size |
| **File:Line** | `frontend/web_app/.next/build/chunks/node_modules__pnpm_1yjis6b._.js` |
| **Current** | Chunk size 280,309 bytes (273.7 KB) |
| **Target** | No chunks > 200 KB |
| **Delta** | pnpm monorepo bootstrap chunk exceeds 200 KB threshold |
| **Fix** | Investigate pnpm chunk splitting or tree-shaking opportunities |
| **Effort** | M (2h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && find .next/build/chunks -name "*.js" -size +200k` |
| **Test** | `tests/frontend/test_bundle.py::test_no_chunk_over_200kb` |
| **Rollback** | Revert Next.js config changes |
| **Blast radius** | Initial page load performance |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-011: No production build artifacts

| Field | Value |
|---|---|
| **ID** | TECH-FW-011 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-build-verification |
| **File:Line** | `frontend/web_app/.next/` |
| **Current** | .next exists but has no BUILD_ID, no output-trace.json, no server/app pages |
| **Target** | Production build artifacts present after `next build` |
| **Delta** | .next directory contains only turbopack/dev artifacts; no production build has been run |
| **Fix** | Run `pnpm build` and verify BUILD_ID and server/app output |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && ls .next/BUILD_ID 2>/dev/null || echo "MISSING"` |
| **Test** | `tests/frontend/test_build.py::test_production_build_exists` |
| **Rollback** | Remove .next and rebuild |
| **Blast radius** | Deployment verification |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

## Part D: Configuration Findings

### TECH-FW-012: shared tsconfig strict mode disabled

| Field | Value |
|---|---|
| **ID** | TECH-FW-012 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-typescript-config |
| **File:Line** | `frontend/shared/tsconfig.json:1` |
| **Current** | `"strict": false` |
| **Target** | `"strict": true` |
| **Delta** | Shared package tsconfig disables strict mode, contradicting canonical requirement for strict TypeScript |
| **Fix** | Set strict to true in shared/tsconfig.json |
| **Effort** | S (0.5h) |
| **Priority** | P1 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/shared && cat tsconfig.json | grep strict` |
| **Test** | `tests/frontend/test_typescript.py::test_shared_strict_mode` |
| **Rollback** | Revert shared/tsconfig.json strict setting |
| **Blast radius** | Shared package type safety |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-013: tailwind-merge version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-013 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:35` |
| **Current** | `tailwind-merge: ^3.5.0` (lockfile: 3.7.0) |
| **Target** | `tailwind-merge: 3.5.0` |
| **Delta** | tailwind-merge resolved to 3.7.0, 2 minor versions ahead of canonical |
| **Fix** | Pin tailwind-merge to 3.5.0 |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && pnpm list tailwind-merge` |
| **Test** | `tests/frontend/test_versions.py::test_tailwind_merge_version` |
| **Rollback** | Revert package.json line 35 |
| **Blast radius** | Tailwind class merging |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-014: dompurify version drift

| Field | Value |
|---|---|
| **ID** | TECH-FW-014 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:41` |
| **Current** | `dompurify: ^3.3.3` (lockfile: 3.4.16) |
| **Target** | `dompurify: 3.4.0` |
| **Delta** | dompurify resolved to 3.4.16 in lockfile, 16 patch versions ahead of canonical 3.4.0 |
| **Fix** | Pin dompurify to 3.4.0 |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && pnpm list dompurify` |
| **Test** | `tests/frontend/test_versions.py::test_dompurify_version` |
| **Rollback** | Revert package.json line 41 |
| **Blast radius** | DOM sanitization |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

### TECH-FW-015: jspdf package.json range mismatch

| Field | Value |
|---|---|
| **ID** | TECH-FW-015 |
| **Phase** | tech |
| **Status** | NEW |
| **Cluster** | CLUSTER-frontend-version-drift |
| **File:Line** | `frontend/web_app/package.json:28` |
| **Current** | `jspdf: ^4.1.0` (lockfile: 4.2.1) |
| **Target** | `jspdf: 4.2.1` |
| **Delta** | jspdf package.json allows 4.1.x versions below canonical 4.2.1; lockfile resolved to 4.2.1 by coincidence |
| **Fix** | Pin jspdf to 4.2.1 |
| **Effort** | S (0.5h) |
| **Priority** | P2 |
| **Confidence** | 5 |
| **Evidence strength** | single |
| **Truth level** | L0 |
| **Claim state** | VERIFIED |
| **Sibling** | — |
| **Verify** | `cd frontend/web_app && pnpm list jspdf` |
| **Test** | `tests/frontend/test_versions.py::test_jspdf_version` |
| **Rollback** | Revert package.json line 28 |
| **Blast radius** | Client-side PDF generation |
| **Depends on** | — |
| **Blocks** | — |
| **Completion blocker** | no |

---

## Over all

### Problem(s)
1. Next.js is pinned to 16.3.4, 1 patch behind canonical 16.3.5.
2. ~~TypeScript in web_app/package.json uses `~5.10` range, diverging from canonical 5.9.3 and lockfile 5.9.3.~~ — **VERIFICATION NOTE:** TECH-FW-002 is factually incorrect; web_app/package.json uses `^5.9.3` and lockfile resolves to 5.9.3, matching canonical. This finding should be closed.
3. framer-motion v12 is used; canonical requires motion v13.2.0+ with renamed package and import path.
4. @stripe/react-stripe-js is at v5.6.1, 1 major version behind canonical v6.9.0.
5. @stripe/stripe-js resolved to 8.11.0, exceeding canonical maximum of 5.5.0+.
6. zustand resolved to 5.0.15, 1 patch ahead of canonical 5.0.14.
7. Root pnpm-workspace.yaml is missing; workspace config exists only in subdirectories.
8. web_app pnpm-workspace.yaml allows `core-js` build, which is non-canonical.
9. pnpm-lock.yaml contains conflicting postcss versions (8.5.23 and 8.5.28).
10. .next build output contains a 273.7 KB pnpm bootstrap chunk exceeding 200 KB threshold.
11. No production build artifacts exist (no BUILD_ID), only turbopack/dev output.
12. shared/tsconfig.json has `strict: false`, violating canonical strict TypeScript requirement.
13. tailwind-merge resolved to 3.7.0, 2 minor versions ahead of canonical 3.5.0.
14. dompurify resolved to 3.4.16 in lockfile, 16 patch versions ahead of canonical 3.4.0.
15. jspdf package.json allows 4.1.x versions below canonical 4.2.1; lockfile resolved to 4.2.1 by coincidence.

### Solution(s)
1. Bump next to 16.3.5 in web_app/package.json.
2. ~~Pin typescript to 5.9.3 in web_app/package.json.~~ — Already at canonical; remove from corrections.
3. Migrate framer-motion v12 to motion v13+ across 30+ files.
4. Bump @stripe/react-stripe-js to 6.9.0 and align @stripe/stripe-js with canonical stack.
5. Pin zustand to 5.0.14.
6. Add canonical pnpm-workspace.yaml at repository root.
7. Remove `core-js` from web_app pnpm-workspace.yaml allowBuilds.
8. Align postcss to single version via pnpm overrides.
9. Investigate pnpm chunk splitting for the 273.7 KB bootstrap chunk.
10. Run production build and verify BUILD_ID exists.
11. Enable strict mode in shared/tsconfig.json.
12. Pin tailwind-merge to 3.5.0.
13. Pin dompurify to 3.4.0.
14. Pin jspdf to 4.2.1.

### Suggestion(s)
1. Add a CI gate that diffs package.json versions against TECHNOLOGY_STACK.md and fails on drift.
2. Add a pre-commit hook that runs `pnpm install --frozen-lockfile` and fails if lockfile changes.
3. Add bundle size CI check that fails if any chunk exceeds 200 KB.
4. Document the motion/framer-motion migration path in a tech debt ticket.
5. Add dependency pins to `backend/pyproject.toml` so backend drift is detectable without parsing `uv.lock`.

### Verification notes
- **TECH-FW-002 is factually incorrect.** Verified against `frontend/web_app/package.json:56` and `pnpm-lock.yaml`: TypeScript is `^5.9.3` / `5.9.3`, matching canonical `5.9.3`. The audit claim of `~5.10` does not match either source. This finding should be closed as `OBSOLETE`.
- All other frontend findings (TECH-FW-001, TECH-FW-003 through TECH-FW-009, TECH-FW-010 through TECH-FW-015) were verified against actual source files and lockfiles.
- Out-of-scope mismatches in backend and mobile are documented in the final section for handoff to their respective audit dimensions.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P1 | Bump next to 16.3.5 | frontend/web_app/package.json | no | S | 5 |
| P1 | Close TECH-FW-002 (TypeScript already at 5.9.3) | frontend/web_app/package.json | no | S | 5 |
| P1 | Enable strict mode in shared/tsconfig.json | frontend/shared/tsconfig.json | no | S | 5 |
| P1 | Add root pnpm-workspace.yaml | pnpm-workspace.yaml | no | S | 5 |
| P2 | Migrate framer-motion v12 to motion v13+ | frontend/web_app/src/**/*.tsx | no | L | 4 |
| P2 | Bump @stripe/react-stripe-js to 6.9.0 | frontend/web_app/package.json | no | S | 5 |
| P2 | Align @stripe/stripe-js with canonical | frontend/web_app/package.json | no | S | 4 |
| P2 | Pin zustand to 5.0.14 | frontend/web_app/package.json | no | S | 5 |
| P2 | Pin tailwind-merge to 3.5.0 | frontend/web_app/package.json | no | S | 5 |
| P2 | Pin dompurify to 3.4.0 | frontend/web_app/package.json | no | S | 5 |
| P2 | Pin jspdf to 4.2.1 | frontend/web_app/package.json | no | S | 5 |
| P2 | Resolve postcss version conflict | pnpm-lock.yaml | no | S | 5 |
| P2 | Investigate large pnpm chunk | .next/build/chunks/ | no | M | 5 |
| P2 | Run production build and verify artifacts | .next/ | no | S | 5 |

## Clusters

| Cluster ID | Phase | Depends on phase | Root cause | Members | Recommended fix | Recommended test | Completion blocker |
|---|---|---|---|---|---|---|---|
| CLUSTER-frontend-version-drift | tech | — | package.json versions diverge from canonical stack | TECH-FW-001, TECH-FW-002, TECH-FW-003, TECH-FW-004, TECH-FW-005, TECH-FW-006, TECH-FW-013, TECH-FW-014, TECH-FW-015 | Align all versions to TECHNOLOGY_STACK.md pins | tests/frontend/test_versions.py | no |
| CLUSTER-workspace-config | tech | — | pnpm workspace configuration incomplete | TECH-FW-007, TECH-FW-008 | Add root pnpm-workspace.yaml; clean allowBuilds | tests/frontend/test_workspace.py | no |
| CLUSTER-lockfile-conflicts | tech | — | Multiple versions of same package in lockfile | TECH-FW-009 | Align postcss via overrides | tests/frontend/test_lockfile.py | no |
| CLUSTER-bundle-size | tech | — | pnpm monorepo bootstrap chunk exceeds threshold | TECH-FW-010 | Investigate chunk splitting | tests/frontend/test_bundle.py | no |
| CLUSTER-build-verification | tech | — | No production build artifacts present | TECH-FW-011 | Run next build and verify | tests/frontend/test_build.py | no |
| CLUSTER-typescript-config | tech | — | Strict mode disabled in shared package | TECH-FW-012 | Enable strict in shared/tsconfig.json | tests/frontend/test_typescript.py | no |

---

## Out-of-Scope Stack Mismatches (Backend & Mobile)

> **Note.** This audit is scoped to frontend/web and frontend/shared. The following
> mismatches exist in other areas of the repo and are documented here for completeness
> but require separate audit dimensions.

### Backend — version drifts in `backend/uv.lock` (no pins in `pyproject.toml`)

| Technology | Canonical (TECHNOLOGY_STACK.md) | Actual (uv.lock) | Delta |
|---|---|---|---|
| uvloop | 0.21.0 | 0.22.1 | +1 minor |
| httptools | 0.7.0 | 0.8.0 | +1 minor |
| tzdata | 2025b | 2026.4 | +1 major |
| Python | 3.13.x | `>=3.11` (pyproject.toml) | No runtime pin |
| FastAPI | 0.141.x | 0.141.0 | ✓ |
| SQLAlchemy | 2.0.52 | 2.0.52 | ✓ |
| Pydantic | 2.13.4 | 2.13.4 | ✓ |
| asyncpg | 0.31.0 | 0.31.0 | ✓ |
| Alembic | 1.19.1+ | 1.19.1 | ✓ |
| valkey (client) | 6.1.1 | 6.1.1 | ✓ |
| Celery | 5.5+ | 5.6.3 | ✓ |
| bcrypt | 5.0.0 | 5.0.0 | ✓ |
| PyJWT | 2.13.0+ | 2.13.0 | ✓ |
| httpx | 0.28.1 | 0.28.1 | ✓ |
| aiofiles | 25.1.0 | 25.1.0 | ✓ |
| pillow | 12.2.0 | 12.2.0 | ✓ |
| structlog | 26.1.0 | 26.1.0 | ✓ |
| pytest | 9.1.1 | 9.1.1 | ✓ |
| pytest-asyncio | 1.4.0 | 1.4.0 | ✓ |
| websockets | 16.1.1+ | 16.1.1 | ✓ |
| gunicorn | 26.0.0 | 26.0.0 | ✓ |
| anyio | 4.15.1 | 4.15.1 | ✓ |
| python-multipart | 0.0.32 | 0.0.32 | ✓ |
| email-validator | 2.3.0 | 2.3.0 | ✓ |
| starlette | >=1.6.0,<1.7.0 | 1.6.0 | ✓ |
| uvicorn | 0.35.0+ | 0.35.0 | ✓ |
| feedparser | 6.0.12 | 6.0.12 | ✓ |
| phonenumbers | 9.0.35 | 9.0.35 | ✓ |
| python-docx | 1.2.0 | 1.2.0 | ✓ |
| openpyxl | 3.1.5 | 3.1.5 | ✓ |
| pyotp | 2.10.0 | 2.10.0 | ✓ |
| prometheus-fastapi-instrumentator | 8.1.0+ | 8.1.0 | ✓ |

> **Critical finding:** `backend/pyproject.toml` contains no dependency pins whatsoever
> (`requires-python = ">=3.11"` only). All backend versions are tracked exclusively in
> `backend/uv.lock`. This means `pyproject.toml` does not reflect the canonical stack
> and cannot be used for drift detection without parsing `uv.lock`.

### Mobile — version drifts in `frontend/mobile_app/package.json`

| Technology | Canonical (TECHNOLOGY_STACK.md) | Actual (mobile_app/package.json) | Delta |
|---|---|---|---|
| Expo SDK | 57.0.20+ | ~57.0.9 | -11 patches |
| React Native | 0.86.3 | 0.81.4 | -5 minors |
| React | 19.2.8 | 19.1.0 | -1 minor |
| react-dom | 19.2.8 | 19.1.0 | -1 minor |
| lucide-react-native | 0.563.0 | ^0.469.0 | -94 patches |
| Playwright | 1.62.1+ | ^1.50.0 | -12 minors |

> **Note:** Mobile `zustand` (`^5.0.14`) and `typescript` (`~5.9.3`) match canonical.

