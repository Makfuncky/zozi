# ADR-002: Dependency Direction & Circular-Import Governance (DG2 remediation)

- **Status:** Accepted
- **Date:** 2026-08-07
- **Audit ref:** `SYSTEM_AUDIT_REPORT.md` — 🟡 **DG2** (circular module dependencies)
- **Companion:** `SERVICE_OWNERSHIP_ADR.md` (S2).

## 1. Allowed dependency direction

```
routers ──▶ controllers ──▶ services ──▶ models
   │            │               │            ▲
   └────────────┴───────────────┴────────────┘  (NEVER upward)
```

- `routers` may import `controllers` and `services`.
- `controllers` may import `services` and `models`, **never** `routers`.
- `services` may import `models` and `core`, **never** `controllers` or `routers`.
- `models` may import `core`/`utils`, **never** `services`, `controllers`, or `routers`.
- `core` / `utils` import nothing from the layers above.

A "lower layer" module (e.g. `routers/_permission_primitives.py`,
`backend/core/*`) is the sanctioned place for symbols shared between two
same-layer modules, so neither imports the other.

## 2. Cycle taxonomy found in the audit

### 2a. `routers.permissions` ⇄ `routers.effective_permissions` — FIXED
- **Was:** `permissions.py` imported `check_permission` (and stubs) *from*
  `effective_permissions.py`, while `effective_permissions.py` imported
  `check_permission` back *from* `permissions.py`.
- **Fix (applied 2026-08-07):** the 7 stub symbols moved to the lower-layer
  module `routers/_permission_primitives.py`. `permissions.py` now imports
  stubs from there and uses its own local `check_permission`;
  `effective_permissions.py` keeps a one-way `→ permissions` import.
- **Result:** acyclic. Smoke-tested with `SECRET_KEY` set; import chain
  proceeds past both routers into `models`/`utils` with no `ImportError`.

### 2b. `*_write_service` re-export shims reaching back into controllers — OPEN
The audit flags, e.g.:
`controllers.admin.users → services.users_write_service → controllers.admin.users`.

Root cause: several `*_write_service` modules are **"Generated re-export
shims"** that, to keep legacy imports resolving, do
`from controllers.<x> import (...)`. That reintroduces the controller edge
the refactor was supposed to remove.

**Remediation pattern (apply per shim):**
1. Identify the *canonical* home of each re-exported symbol (today it lives
   in a per-feature service module, e.g. `services.admin.users_write`, not in
   `controllers`).
2. Change the shim to re-export from that canonical service module, **not**
   from `controllers`.
3. Keep the shim import-free of `controllers`/`routers` (matches the
   controller-free contract already honoured by `coupons_write_service`,
   `promotions_write_service`, `commerce_write_service`, etc.).

Affected shims (non-exhaustive, from DG2): `users_write_service`,
`commission_write_service`, `communication_write_service`,
`country_write_service`, `disputes_write_service`, `employee_write_service`,
`hr_write_service`, `iam_write_service`, `invoice_write_service`,
`logistics_partner_write_service`, `logistics_write_service`,
`payments_write_service`, `products_write_service`, `promotion_engine_service`,
`suppliers_write_service`, `users_write_service`, `misc_write_service`,
`banner_write_service`, `commerce_write_service`.

> These are 🟡 advisory. The app currently boots because Python tolerates the
> partial initialization, but the shims violate the direction rule and should
> be repointed as a follow-up cleanup.

### 2c. `models/__init__.py` re-export cycles — BENIGN, convention only
`models/__init__.py` re-exports submodules (`from .user import *`, etc.), so
the graph shows `models → models.X → models`. Python resolves this at runtime
(the app boots). To keep it clean and tooling-friendly:
- Package `__init__.py` files should re-export **only names**, never trigger
  imports that reference the parent package at module-load time.
- Use `from __future__ import annotations` + `TYPE_CHECKING` for type-only
  cross-references between model submodules.
- Prefer explicit symbol imports over `import *` where feasible.

### 2d. `models` ⇄ `models.comms*` and `models` ⇄ `models.<domain>` — BENIGN
Same re-export pattern as 2c; governed by the same convention.

## 3. Enforcement
- New modules MUST obey §1 or they are rejected in review.
- Shared same-layer symbols go in a `*_primitives` / `core` lower layer
  (see the `routers/_permission_primitives.py` reference implementation).
- Re-export shims MUST NOT import `controllers`/`routers` (see §2b).
- Re-run `SYSTEM_AUDIT_REPORT.md` generation after structural changes to
  confirm DG2 count trends down.
