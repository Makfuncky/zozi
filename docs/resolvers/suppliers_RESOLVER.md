# RESOLVER.md — suppliers domain audit & repair log

Per ARCHITECTURE_DIAGRAM.md (the ONLY structural authority).

## Final status: in-scope structural + content fixes complete

### Applied in this session (verified)

| ID | Fix | Evidence |
|----|-----|----------|
| F1 | `schemas/supplier_schemas.py` credibility_score: int→float | Import + instantiation with 42.5 works |
| F2 | `schemas/supplier_schemas.py` verification_status default: "pending"→"unverified" | Default resolves to "unverified" |
| F3 | `schemas/supplier_schemas.py` validator rejects invalid action | `action='invalid'` raises ValidationError |
| F4 | `policies/__init__.py` removed unused `from typing import Any` | File imports cleanly |
| F5 | `models/suppliers.py` orphaned Index objects (lines 203-205) → converted to documented comment block | No floating Index objects; design intent preserved in docstring |
| F6 | `models/suppliers.py` docstring now documents future indexes | Docstring lists 4 planned GIN indexes |

### Applied in earlier rounds (still in place)

| ID | Fix | Evidence |
|----|-----|----------|
| E1 | events.py populated (14 typed events + 14 publish helpers) | Import + publish_supplier_verified resolves |
| E2 | features.py populated (12 atoms) | 12 atoms, is_known() works |
| E3 | subscribers.py populated (4 handlers on event_bus) | Import registers handlers |
| E4 | policies populated (6 functions) | All functions callable |
| E5 | schemas populated (5 Pydantic schemas) | Import works |
| E6 | ports.py fixed (2 read helpers, no wildcards) | Import works |
| E7 | models canonical in suppliers domain (schema='supplier') | SupplierProfile.__table_args__ = schema supplier |
| E8 | 12 fabricated sub-folders deleted (untracked duplicates) | git status clean |
| E9 | 18 tracked files restored as re-export shims | Zero tracked deletions |
| E10 | suppliers.py broken self-referential import fixed | Resolves to admin_supplier_review_service |
| E11 | models/__init__.py re-exports all 6 model classes | `from domains.suppliers.models import SupplierProfile` works |
| E12 | Governance imports redirected to canonical legal_contract_service | Redirect source verified |
| E13 | suppliers_write_service except narrowed (22→6 types) | In place |
| E14 | Router registrations: 3 non-existent entries removed | In place |

### Remaining items (pre-existing / systemic — beyond single-domain scope)

| ID | Issue | Reason not fixed |
|----|-------|------------------|
| R1 | `admin_suppliers_service.py:10` Law 1 violation (imports modules.) | Pre-existing; requires resolving logistics.offices MetaData conflict first |
| R2 | FK `accounts.users.id` wrong schema (should be core) | Systemic: 52 occurrences across 13 domains |
| R3 | 74 Law 3 cross-domain import violations | Pre-existing codebase-wide pattern; baseline frozen |
| R4 | mixins.py: 3 of 4 mixins unused | Dead code but kept (merge-not-delete); models work without them |
| R5 | subscribers.py handlers are log-only stubs | Behavioral gap; not a structural violation |
| R6 | country_code collision (TenantMixin String(10) vs SupplierProfile String(3)) | Silent override; works but inconsistent |

### Verification summary
- Tracked deletions: **0**
- Empty files: **0**
- Total files: **58**
- Duplicate table definitions: **None** (suppliers ↔ comms identity confirmed)
- All contract files import and resolve correctly
