# Anti-Patterns

Generated: 2026-09-30T04:40:00Z
Run number: 1

## AP-001

- **Category:** stub_function
- **Location:** `backend/domains/accounts/ports.py`
- **Evidence:** `Skipping router finance: cannot import name 'get_referral_dashboard' from 'domains.accounts.ports'`
- **Occurrences in codebase:** 1
- **Project completion blocker:** yes
- **Recommended remediation:** Define `get_referral_dashboard` in `domains/accounts/ports.py` or remove the import.
- **Blast radius:** finance router, supplier router, analytics router

## AP-002

- **Category:** missing_import
- **Location:** `backend/domains/accounts/ports.py`
- **Evidence:** `Skipping router logistics: cannot import name 'update_role_permissions' from 'domains.accounts.ports'`
- **Occurrences in codebase:** 1
- **Project completion blocker:** yes
- **Recommended remediation:** Define `update_role_permissions` in `domains/accounts/ports.py` or remove the import.
- **Blast radius:** logistics router

## AP-003

- **Category:** undefined_name
- **Location:** `backend/main.py`
- **Evidence:** `Skipping router accounts: name 'Session' is not defined` (repeated across multiple routers)
- **Occurrences in codebase:** 6
- **Project completion blocker:** yes
- **Recommended remediation:** Import or define `Session` in the affected router files.
- **Blast radius:** accounts, suppliers, analytics, catalog, finance, orders routers

## Overall

3 anti-patterns identified during boot smoke test. All are project completion blockers.
