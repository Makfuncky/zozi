# Unnecessary Files — Complete Removal List

> Generated: 2026-08-26  
> Total files identified: **500+**

---

## Priority 1 — SECURITY RISK (Delete Immediately)

| # | File | Reason |
|---|------|--------|
| 1 | `.token` | **Hardcoded JWT token** — security risk |

---

## Priority 2 — Root-Level Temporary Files

| # | File | Size | Reason |
|---|------|------|--------|
| 1 | `_tmp_arch.txt` | ~500 B | Python traceback error dump |
| 2 | `audit_migration_tracker.py` | ~50 KB | Migration tracking script (v9) — should be in scripts/ or removed |
| 3 | `login_form.yml` | ~3 KB | Browser test fixture |
| 4 | `CORRECTIONS_ACCURATE.txt` | ~20 KB | Import corrections log |
| 5 | `DOMAIN_API_SUMMARY.txt` | ~15 KB | Regenerable API summary |
| 6 | `logs/pytest_baseline.txt` | ~300 B | pytest ImportError debug output |

---

## Priority 3 — Entire Directories (Safe to Delete)

| # | Directory | Files | Reason |
|---|-----------|-------|--------|
| 4 | `.kilo/worktrees/` | 35 dirs | Old agent worktrees from previous sessions |
| 5 | `.freebuff/` | 10 files | Preview/development artifacts, SQLite cache DBs |
| 6 | `.playwright-mcp/` | 15 files | Browser testing session snapshots |
| 7 | `frontend/web_app/_extra_files/` | 24 files | Python prototype, CSS regeneration artifacts |

---

## Priority 4 — Backend Temporary Scripts

| # | File | Reason |
|---|------|--------|
| 1 | `backend/_scripts_patch_payments.py` | One-off patch script |
| 2 | `backend/_scripts_patch_payments2.py` | Duplicate of above |
| 3 | `backend/_scripts_patch_payments3.py` | Third iteration of same script |
| 4 | `backend/audit_dup_fix.py` | One-off duplicate table fix |
| 5 | `backend/chat_system.py` | Misplaced file (empty/placeholder) |

### backend/_extra_files/
| # | File | Reason |
|---|------|--------|
| 6 | `backend/_extra_files/_diagnose_accounts.py` | Diagnostic script in quarantine |
| 7 | `backend/_extra_files/_compute_namespaces.py` | Research script |

### backend/scripts/ (all temporary)
| # | File | Reason |
|---|------|--------|
| 8 | `_remap_services_controllers.py` | One-off migration helper |
| 9 | `_remap_legacy_to_domains.py` | One-off migration helper |
| 10 | `_remap_comprehensive.py` | Comprehensive wiring remapper |
| 11 | `_patch_rewriter.py` | Patches rewrite_imports.py |
| 12 | `_make_controller_shims.py` | Creates re-export shims |
| 13 | `_graph_analysis.py` | Research script (DELETE after use) |
| 14 | `_fix_controllers_imports.py` | One-off controller import fixer |
| 15 | `_fix_admin_controller_cycle.py` | One-off circular import breaker |
| 16 | `_diagnose_tree.py` | Alembic migration tree diagnostic |
| 17 | `_boot_check.py` | Manual boot check script |
| 18 | `_audit_tmp.py` | Temporary audit script |
| 19 | `_analyze_routers_for_migration.py` | Router analysis |
| 20 | `_analyze_graph.py` | Alembic graph analysis |
| 21 | `_analyze_controllers.py` | Controller analysis |
| 22 | `test_create_all.py` | 6-line create_all script |
| 23 | `verify_syntax.py` | Manual syntax verification |
| 24 | `validate_migrations.py` | Alembic migration validator |
| 25 | `triage_routers.py` | Router triage for migration |
| 26 | `safe_structure_migration.py` | Large migration utility |

### backend/tests/
| # | File | Reason |
|---|------|--------|
| 27 | `tests/_tmp_introspect.py` | Temporary test (assert True) |

---

## Priority 5 — Backend Empty/Placeholder Files

| # | File | Size | Reason |
|---|------|------|--------|
| 1 | `backend/infrastructure/utils/ai_service.py` | 4 lines | Empty placeholder comment only |

---

## Priority 6 — infrastructure/utils/ Files That Still Contain Business Logic

These are NOT shims — they contain actual business logic that should be in domains/.

| # | File | Size | Current Issue | Shift | 
|---|------|------|---------------|-------|
| 1 | `infrastructure/utils/operations_service.py` | 655 lines | Admin data export, CSV streaming, PII redaction — business logic in infrastructure | backend\provider as tools | 
| 2 | `infrastructure/utils/misc_write_service.py` | 280 lines | Superset of misc_write.py with merged admin_write_service logic | need recommendation |
| 3 | `infrastructure/utils/realtime.py` | 686 lines | WebSocket hubs, Redis pub/sub — should be in domains/governance or infrastructure/messaging | I guess it is on right place according to the ARCHITECTURE_DIAGRAM.md | 
| 4 | `infrastructure/utils/workflow_engine.py` | 141 lines | Business workflow engine — duplicate of domains/governance/services/workflow_engine.py | remove duplicate |
| 5 | `infrastructure/utils/staff_permissions.py` | 190 lines | Permission definitions — should be in rbac/ or domains/governance | it is already inside of domains/governance check and verify |
| 6 | `infrastructure/utils/export_read.py` | 81 lines | Query builders — duplicate of domains/governance/services/export_read.py | remove duplicate |

---

## Priority 7 — Duplicate Files (Keep Canonical, Delete Duplicate)

| # | Keep | Delete | Reason |
|---|------|--------|--------|
| 1 | `domains/analytics/services/dashboards/admin_analytics_service.py` | `domains/analytics/services/admin_analytics_service.py` | Duplicate |
| 2 | `domains/analytics/services/dashboards/admin_dashboard_service.py` | `domains/analytics/services/admin_dashboard_service.py` | Duplicate |
| 3 | `domains/analytics/services/dashboards/analytics_service.py` | `domains/analytics/services/analytics_service.py` | Duplicate |
| 4 | `domains/analytics/services/aggregation/command_center_background.py` | `domains/analytics/services/command_center_background.py` | Duplicate |
| 5 | `domains/governance/services/command_center/service.py` | `domains/analytics/services/aggregation/command_center_service.py` | Duplicate |
| 6 | `domains/analytics/services/aggregation/command_center_query_service.py` | `domains/analytics/services/command_center_query_service.py` | Duplicate |
| 7 | `providers/media/services/ai_upload_service.py` | `domains/analytics/services/*/ai_upload_service.py` | 3 duplicates |
| 8 | `domains/audit/services/logs/audit_query_service.py` | `domains/audit/services/audit_query_service.py` | Duplicate |
| 9 | `domains/audit/services/logs/audit_trail_service.py` | `domains/audit/services/audit_trail_service.py` | Duplicate |
| 10 | `domains/promotions/services/engine/admin_promotions_write_service.py` | `domains/promotions/services/admin_promotions_write_service.py` | Duplicate |
| 11 | `domains/customers/services/referrals/referrals_service.py` | `domains/customers/services/referrals_service.py` | Duplicate |
| 12 | `domains/hr/services/travel/travel_service.py` | `domains/country/services/research/travel_service.py` | Duplicate |
| 13 | `domains/country/services/localization/translation_service.py` | `domains/comms/services/translation/translation_service.py` | Duplicate |
| 14 | `domains/suppliers/services/profile/supplier_payouts_service.py` | `domains/country/services/payout/supplier_payouts_service.py` | Duplicate |
| 15 | `infrastructure/utils/misc_write.py` | `infrastructure/utils/misc_write_service.py` | Near-identical |
| 16 | `tests/architecture/_gen_service_provider_baseline.py` | `tests/_gen_service_provider_baseline.py` | Duplicate |
| 17 | `tests/architecture/_gen_router_baseline.py` | `tests/_gen_router_baseline.py` | Duplicate |
| 18 | `domains/governance/models/core.py` | `domains/accounts/models/core.py` | core.py duplicated |

---

## Priority 8 — Frontend Duplicate Files

### shared/src/ (delete root-level, keep __tests__/)
| # | File | Reason |
|---|------|--------|
| 1 | `frontend/shared/src/localization.test.ts` | Duplicate of __tests__/ version |
| 2 | `frontend/shared/src/money.test.ts` | Duplicate of __tests__/ version |
| 3 | `frontend/shared/src/orderHelpers.test.ts` | Duplicate of __tests__/ version |
| 4 | `frontend/shared/src/checkoutHelpers.test.ts` | Duplicate of __tests__/ version |
| 5 | `frontend/shared/src/chatbot.test.ts` | Duplicate of __tests__/ version |
| 6 | `frontend/shared/src/cartHelpers.test.ts` | Duplicate of __tests__/ version |

### shared/src/logo/ (consolidate to components/logo/)
| # | File | Reason |
|---|------|--------|
| 7 | `frontend/shared/src/logo/ZoziLogo.tsx` | Duplicate of components/logo/ |
| 8 | `frontend/shared/src/logo/LogoAnimation.tsx` | Duplicate of components/logo/ |
| 9 | `frontend/shared/src/logo/Logo.web.tsx` | Duplicate of components/logo/ |
| 10 | `frontend/shared/src/logo/Logo.native.tsx` | Duplicate of components/logo/ |
| 11 | `frontend/shared/src/logo/web.ts` | Duplicate of components/logo/ |
| 12 | `frontend/shared/src/logo/types.ts` | Duplicate of components/logo/ |
| 13 | `frontend/shared/src/logo/native.ts` | Duplicate of components/logo/ |
| 14 | `frontend/shared/src/logo/index.ts` | Duplicate of components/logo/ |

---

## Priority 9 — Frontend Debug/Temp Scripts

### web_app/e2e/ (debug specs)
| # | File | Reason |
|---|------|--------|
| 1 | `frontend/web_app/e2e/debug2.spec.ts` | Debug: image upload |
| 2 | `frontend/web_app/e2e/debug3.spec.ts` | Debug: image upload |
| 3 | `frontend/web_app/e2e/debug4.spec.ts` | Debug: image upload |
| 4 | `frontend/web_app/e2e/debug5.spec.ts` | Debug: React state |
| 5 | `frontend/web_app/e2e/debug6.spec.ts` | Debug: React hydration |
| 6 | `frontend/web_app/e2e/debug-price.spec.ts` | Debug: price filter |
| 7 | `frontend/web_app/e2e/debug_test6.js` | Debug: JS variant |

### web_app/ (verify/temp scripts)
| # | File | Reason |
|---|------|--------|
| 8 | `frontend/web_app/verify_cart.cjs` | Temp verification |
| 9 | `frontend/web_app/verify_imgs.cjs` | Temp verification |
| 10 | `frontend/web_app/verify_hash_dbg.cjs` | Temp verification |
| 11 | `frontend/web_app/verify_hash.cjs` | Temp verification |
| 12 | `frontend/web_app/verify_chatbot.cjs` | Temp verification |
| 13 | `frontend/web_app/verify_style.cjs` | Temp verification |
| 14 | `frontend/web_app/verify_pages.cjs` | Temp verification |
| 15 | `frontend/web_app/verify_zero.cjs` | Temp verification |

### web_app/ (audit/temp scripts)
| # | File | Reason |
|---|------|--------|
| 16 | `frontend/web_app/_audit_content.cjs` | Temp audit |
| 17 | `frontend/web_app/_audit_auth.cjs` | Temp audit |
| 18 | `frontend/web_app/_audit_ar.cjs` | Temp audit |
| 19 | `frontend/web_app/_audit_panels.cjs` | Temp audit |
| 20 | `frontend/web_app/_audit_net.cjs` | Temp audit |
| 21 | `frontend/web_app/_audit_markers.cjs` | Temp audit |
| 22 | `frontend/web_app/_audit_low.cjs` | Temp audit |
| 23 | `frontend/web_app/_audit_html.cjs` | Temp audit |
| 24 | `frontend/web_app/_audit_treasury.cjs` | Temp audit |
| 25 | `frontend/web_app/_audit_tabs.cjs` | Temp audit |
| 26 | `frontend/web_app/_audit_single.cjs` | Temp audit |
| 27 | `frontend/web_app/_audit_valid.cjs` | Temp audit |

### web_app/ (diag scripts)
| # | File | Reason |
|---|------|--------|
| 28 | `frontend/web_app/e2e/diag-perf.spec.ts` | Diagnostic: perf |
| 29 | `frontend/web_app/e2e/diag-logistics.spec.ts` | Diagnostic: logistics |
| 30 | `frontend/web_app/e2e/diag-console.spec.ts` | Diagnostic: console |
| 31 | `frontend/web_app/scripts/diag_login.cjs` | Diagnostic script |
| 32 | `frontend/web_app/scripts/diag_checkout.cjs` | Diagnostic script |
| 33 | `frontend/web_app/debug-postcss.js` | Debug utility |

---

## Priority 10 — Frontend Backup Files

| # | File | Reason |
|---|------|--------|
| 1 | `frontend/web_app/__tests__/ErrorBoundary.test.tsx.bak` | Backup file |

---

## Priority 11 — Placeholder/Stub Router Files

These are explicit PLACEHOLDER stubs with no implementation.

| # | File | Reason |
|---|------|--------|
| 1 | Check `modules/employee/routers/` for placeholder stubs | 4 files may be placeholders |

---

