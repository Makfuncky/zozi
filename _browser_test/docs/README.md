# Browser Test Suite

This directory contains the end-to-end browser test suite for the ZOZI e-commerce application.

## Structure

- `config/` - Environment and configuration files
- `docs/` - Documentation, pipeline guides, and known issues
- `scripts/` - Helper scripts for running tests
- `src/` - Shared test helpers (auth, api, ui)
- `tests/` - Test suites organized by feature area
  - `preflight.spec.ts` - Environment readiness checks
  - `database.spec.ts` - Database and migration tests
  - `auth/` - Authentication flows (login, logout, session, RBAC gates)
  - `modules/` - Module-specific tests
    - `admin/` - Admin panel (finance, HR, logistics, country, communication, data ops)
    - `customer/` - Customer journeys (browse, cart, checkout, tracking)
    - `supplier/` - Supplier workflows (registration, upload, KYC, bulk, voice-to-catalog)
    - `logistics/` - Logistics operations (pricing, country switching, scan/delivery, COD proof)
    - `employee/` - Employee dashboard (login, orders, customers, HR)
  - `cross-cutting/` - Cross-role tests (design system, panels, visual shell, country research, WebSocket, scaling)
- `reports/` - Test execution artifacts (screenshots, traces, JSON results)
- `playwright.config.ts` - Playwright configuration
- `global-setup.ts` - Pre-test environment verification
- `global-teardown.ts` - Post-test artifact consolidation

## Running Tests

Use the pipeline script:

```powershell
.\scripts\run-pipeline.ps1
```

## Prerequisites

- Playwright browsers installed
- Backend and frontend servers running
- Environment variables configured in `config/stack.env.ps1`
