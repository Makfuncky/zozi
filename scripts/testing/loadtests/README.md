# Load Testing

This folder contains a k6 suite for the core high-traffic flows:

- login token issuance
- browse product listings
- product search
- checkout creation
- payment webhook ingestion
- admin analytics and order list reads

Profiles:

- `baseline`: quick regression profile for routine checks.
- `scale1000`: sustained high-concurrency profile tuned for roughly 1000 active virtual users across browse, search, checkout, and admin traffic.

Example usage:

```powershell
$env:RUNTIME_PROFILE="loadtest"
k6 run scripts/loadtests/k6-core-flows.js `
  -e BASE_URL=http://localhost:8000 `
  -e LOAD_PROFILE=baseline `
  -e PRODUCT_ID=1 `
  -e CUSTOMER_EMAIL=customer@zozi.com `
  -e CUSTOMER_PASSWORD=customer123 `
  -e ADMIN_EMAIL=admin@zozi.com `
  -e ADMIN_PASSWORD=admin123 `
  --summary-export artifacts/k6-core-flows-baseline.json
```

High-concurrency (1000+ users) example:

```powershell
$env:RUNTIME_PROFILE="loadtest"
k6 run scripts/loadtests/k6-core-flows.js `
  -e BASE_URL=http://localhost:8000 `
  -e LOAD_PROFILE=scale1000 `
  -e SCALE_MAX_VUS=1000 `
  -e CUSTOMER_EMAIL=customer@zozi.com `
  -e CUSTOMER_PASSWORD=customer123 `
  -e ADMIN_EMAIL=admin@zozi.com `
  -e ADMIN_PASSWORD=admin123 `
  --summary-export artifacts/k6-core-flows-scale1000.json
```

Environment variables:

- `BASE_URL`: backend origin.
- `LOAD_PROFILE`: `baseline` or `scale1000`.
- `RUNTIME_PROFILE`: set to `loadtest` before starting the backend to switch the API to elevated quota rules for the k6-sensitive auth, browse, search, and checkout routes.
- `SCALE_MAX_VUS`: target concurrency used by `scale1000` profile (default `1000`).
- `PRODUCT_ID`: optional product used for checkout creation. When omitted, the script auto-selects the first catalog item.
- `CUSTOMER_EMAIL` / `CUSTOMER_PASSWORD`: credentials used for login and checkout scenarios.
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: credentials used for login and admin-read scenarios.
- `CUSTOMER_TOKEN` / `ADMIN_TOKEN`: optional pre-issued JWTs that override login during setup.
- `WEBHOOK_SECRET`: optional signature placeholder used by the webhook probe.

Load-test profile defaults:

- `LOADTEST_AUTH_RATE_LIMIT=600/minute`
- `LOADTEST_CATALOG_RATE_LIMIT=2400/minute`
- `LOADTEST_SEARCH_RATE_LIMIT=2400/minute`
- `LOADTEST_CHECKOUT_RATE_LIMIT=600/minute`

For `scale1000`, raise these limits significantly (or shard traffic) so rate limiting does not dominate results. As a starting point, target at least 10x the baseline limits during dedicated performance runs.

Treat this suite as the baseline regression check for concurrency-sensitive backend changes.