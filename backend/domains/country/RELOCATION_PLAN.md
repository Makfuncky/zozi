# Country Services Relocation Plan (Phase 1)

> **STATUS (2026-08-17):** Phase 1 FREE batch COMPLETE — 34 files relocated via move (no deletes). 76 files remain in `country/services/` (43 country-owned + 27 collision-duplicates + 5 no-rule + 1 `main.py` aggregator).

Goal: shift misplaced service files out of `domains/country/services/` (a 111-file mixed dump) into their correct domain `services/` folders, WITHOUT deleting any code. This is the mechanical cleanup that precedes the country-domain reshape described in `documents/NEW_STRUCTURE.md`.

## Inventory result
`domains/country/services/` contains 110 `.py` files (excl. `__init__.py`):
- **43** are genuinely country-owned (kept in place): `country_*`, `countries_service`, `curated_cities`, `cross_border_*`, `localization_service`, `travel_*`, `geo_resolver`, `category_tax_profiles`.
- **67** are misplaced (non-country) and must shift:
  - **35 FREE** – no name collision in target domain, 0 external import references, not re-exported, no sibling relative imports → safe to `git mv` now.
  - **27 COLLISION** – a file of the SAME name already lives in the target domain → these are duplicates; consolidate later, DO NOT DELETE this session.
  - **5 NO-RULE** – need manual classification (left in place this session, classified below).

## Accurate shift list (all 67 misplaced files)

### A. FREE (35) — relocate now via `git mv`
| # | file | target domain |
|---|------|---------------|
| 1 | addresses_service.py | customers |
| 2 | admin_banners_service.py | catalog |
| 3 | admin_categories_service.py | catalog |
| 4 | admin_chat_service.py | comms |
| 5 | admin_commission_service.py | finance |
| 6 | admin_email_service.py | comms |
| 7 | admin_payouts_service.py | finance |
| 8 | admin_promotions_service.py | catalog |
| 9 | admin_suppliers_service.py | suppliers |
| 10 | admin_users_service.py | governance |
| 11 | admin_video_service.py | media |
| 12 | api_geography_location_service.py | logistics |
| 13 | banners_service.py | catalog |
| 14 | cart_service.py | customers |
| 15 | categories_service.py | catalog |
| 16 | comms_unified_service.py | comms |
| 17 | coupons_service.py | customers |
| 18 | email_service.py | comms |
| 19 | ess_service.py | hr |
| 20 | export_read_service.py | customers |
| 21 | geo_service.py | logistics |
| 22 | geography_country_audit_admin_service.py | logistics |
| 23 | geography_country_config_admin_service.py | logistics |
| 24 | logistics_locations_service.py | logistics |
| 25 | referrals_service.py | customers |
| 26 | returns_service.py | customers |
| 27 | reviews_service.py | customers |
| 28 | search_service.py | customers |
| 29 | supplier_documents_service.py | suppliers |
| 30 | supplier_orders_service.py | orders |
| 31 | supplier_products_service.py | catalog |
| 32 | supplier_profile_service.py | suppliers |
| 33 | tickets_service.py | comms |
| 34 | vat_rates.py | finance |
| 35 | wishlist_service.py | customers |

### B. COLLISION (27) — duplicate in target domain; CONSOLIDATE LATER (do not delete)
admin_logistics_service→logistics, admin_orders_service→orders, admin_products_service→catalog, admin_treasury_service→finance, auth_service→governance, cash_management_service→finance, chat_enrichment_service→comms, chatbot_service→comms, commission_service→finance, customer_health_service→customers, employees_service→hr, export_service→customers, hierarchy_service→hr, incident_service→governance, internal_channels_service→comms, logistics_health_service→logistics, logistics_partner_service→logistics, logistics_service→logistics, payroll_service→hr, performance_service→hr, permissions_service→governance, shipments_service→logistics, supplier_finance_service→suppliers, supplier_health_service→suppliers, supplier_payouts_service→finance, translation_service→comms, users_service→governance.

### C. NO-RULE (5) — classified, relocate next pass after ref-check
admin_cash_service→finance, admin_service→governance, hr_service→hr, user_read_service→governance; main.py stays in country (package aggregator).

## Implementation checklist (verify after each batch)
- [ ] Each misplaced file has a confirmed target domain (above).
- [ ] FREE files moved with `git mv` (history preserved, nothing deleted).
- [ ] No moved file is referenced anywhere via `domains.country.services.*` (verified 0 refs up front).
- [ ] Target domain `services/` folders exist (all do).
- [ ] Every moved file passes `python -m py_compile`.
- [ ] `domains/country/services/__init__.py` remains empty (no re-exports broken).
- [ ] No `from modules.` import inside `backend/domains/` (Law 1 of NEW_STRUCTURE.md).
- [ ] App still imports / coherence gate passes / `pytest` green after move.
- [ ] COLLISION + NO-RULE files left untouched this session (do-not-delete respected).
- [ ] Follow-up: accounts/services/ (98 files) has the same misplacement pattern — parallel Phase 2.

## Post-move findings (2026-08-17)
- 34 FREE files relocated; `country/services` reduced 110 → 76 `.py` files. All compile (`py_compile` clean).
- 8 relocated files carry **pre-existing** `from modules.` Law-1 violations. These were already violations while in `country/services`; the move only relocated them into their correct domain (total violation count unchanged, part of the known 83). They are now co-located with their domain and flagged for the Law-1 cleanup pass:
  - `catalog/services/admin_categories_service.py`, `catalog/services/admin_promotions_service.py`
  - `comms/services/email_service.py`
  - `governance/services/admin_users_service.py`
  - `suppliers/services/admin_suppliers_service.py`
  - `customers/services/referrals_service.py`, `customers/services/returns_service.py`, `customers/services/wishlist_service.py`
- `addresses_service.py` was correctly excluded from the FREE batch: it COLLIDES with `customers/services/addresses_service.py` (re-classified as collision).
- App unaffected: the 34 files had 0 external importers and `country/services/__init__.py` is empty, so no import or boot path broke.

## Strategy notes
- Relocating is `git mv` (move, not delete) → satisfies "do not delete".
- Free files are orphaned duplicates (0 importers), so moving cannot break the running app.
- COLLISION files are true duplicates; deleting/merging them is out of scope for "do not delete" and deferred to a consolidation pass with diff review.
