# COMPLETION BLOCKERS

> **Compiled:** 2026-10-01
> **Total yes blockers:** 165

## All Yes Blockers (Priority Order)

| ID | Phase | Priority | Effort | Finding | Fix | Source |
|----|-------|----------|--------|---------|-----|--------|
| ALIGN-001 | routing | P0 | L (8h) | Frontend expects: `GET /admin/orders?limit=25&offset=...&status=...&date_range=. | Create proper order management routes under `/api/v1/admin/orders`: GET list, GE | 26_code_alignment.md |
| ARCH-001 | arch | P0 | M (2h) | `modules/finance/` directory exists with `routers/cash_management.py` | Delete `modules/finance/`; move any legitimate routes to `modules/admin/routers/ | 01_architectural.md |
| ARCH-002 | arch | P0 | L (8h) | `domains/payments/` directory exists with models, services, ports, events, subsc | Delete `domains/payments/`; consolidate into `providers/payments/` and `domains/ | 01_architectural.md |
| ARCH-011 | arch | P1 | M (2h) | File contains 49 plain functions with `db: Session` parameters and `APIRouter` d | Delete file or convert to proper router with `@router.get/post` decorators and ` | 01_architectural.md |
| ARCH-014 | arch | P0 | L (4h) | `_on_payment_confirmed`, `_on_payment_refunded`, `_on_order_completed` subscribe | Implement actual cross-domain write logic in subscribers; ensure events are emit | 01_architectural.md |
| ARCHTEST-001 | testing | P0 | S (0.5h) | File does not exist | Create backend/tests/architecture/test_schema_discipline.py verifying __table_ar | 12_tests.md |
| ARCHTEST-002 | testing | P0 | S (0.5h) | File does not exist | Create backend/tests/architecture/test_model_relocation.py asserting each model' | 12_tests.md |
| ARCHTEST-003 | testing | P0 | S (0.5h) | 3 of 4 catalog tests fail with pydantic ValidationError: SECRET_KEY must be at l | Inject 64+ char SECRET_KEY before config.py loads in test environment or mock se | 12_tests.md |
| ARCHTEST-004 | testing | P0 | S (0.5h) | test_every_domain_exposes_features_module fails: domains/media/features.py missi | Add domains/media/features.py with FEATURES dict or exclude media from domain sc | 12_tests.md |
| ARCHTEST-005 | testing | P0 | S (0.5h) | DOMAIN_ALLOWLIST.yaml has 0 entries per _entry_count heuristic; test fails with  | Update _entry_count to detect YAML list entries under cross_domain_imports (coun | 12_tests.md |
| ARCHTEST-009 | testing | P1 | M (3h) | 4251 tests collected / 9 collection errors: SECRET_KEY validation (2), HAS_BANK_ | Fix underlying import errors: SECRET_KEY, HAS_BANK_API, CircuitBreakerRegistry,  | 12_tests.md |
| BLOCKER-001 | boot | P0 | S | `from backend.main import app` fails with ModuleNotFoundError | Add `backend/__init__.py` or update audit commands to run from inside `backend/` | 27_project_completion_blockers.md |
| BLOCKER-002 | boot | P0 | S | `settings.DATABASE_URL` raises AttributeError; actual attribute is `settings.dat | Align config attribute names with documented env var names or update `TECHNOLOGY | 27_project_completion_blockers.md |
| BLOCKER-003 | infra | P0 | S | `valkey_url = valkey://localhost:6379`; connection refused — no local Valkey ser | Start local Valkey via Docker Compose (`docker compose up valkey`) or install Va | 27_project_completion_blockers.md |
| BLOCKER-004 | testing | P0 | M | 4657 tests collected, 6 collection errors | Fix missing imports in 6 test files | 27_project_completion_blockers.md |
| BLOCKER-005 | frontend | P0 | L | 60+ TypeScript errors in `tsc --noEmit` | Fix TypeScript errors in checkout, employee/attendance, supplier/bulk, supplier/ | 27_project_completion_blockers.md |
| BLOCKER-006 | testing | P0 | L | 8335 errors (2954 fixable) in ruff check | Fix or suppress ruff errors across test files | 27_project_completion_blockers.md |
| BLOCKER-007 | db | P0 | L | 5 divergent heads: `20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_ | Merge or squash divergent migration heads into single linear history | 27_project_completion_blockers.md |
| BLOCKER-008 | tech | P0 | M | `fastapi==0.115.2` (target `0.141.x`), `sqlalchemy==2.0.51` (target `2.0.52`), ` | Update versions in requirements.txt to match TECHNOLOGY_STACK.md, remove forbidd | 27_project_completion_blockers.md |
| BLOCKER-009 | tech | P0 | M | `next: 16.3.4` (target `16.3.5`), `framer-motion: 12.43.0` (target `13.2.0+`), ` | Update package.json and pnpm-lock.yaml to match TECHNOLOGY_STACK.md versions | 27_project_completion_blockers.md |
| BROWSER-002 | boot | P0 | M (2h) | Multiple routers skipped due to `name 'Session' is not defined` and missing symb | Fix undefined `Session` import and add missing port symbols to `domains/accounts | 24_browser_behavior.md |
| BROWSER-004 | testing | P0 | L (8h) | All critical paths: UNTESTABLE | Resolve backend and frontend preconditions, then run full browser test suite | 24_browser_behavior.md |
| BROWSER-005 | testing | P0 | M (3h) | Money path: UNTESTABLE | Run `_browser_test/tests/money/payments.spec.ts` and `_browser_test/tests/custom | 24_browser_behavior.md |
| BROWSER-006 | testing | P0 | M (3h) | Security path: UNTESTABLE | Run `_browser_test/tests/auth/*.spec.ts` and `_browser_test/tests/security/rbac. | 24_browser_behavior.md |
| BROWSER-007 | testing | P0 | L (12h) | All 28 dimensions requiring runtime evidence: UNTESTABLE | Resolve all preconditions and run complete browser E2E suite covering all 28 dim | 24_browser_behavior.md |
| CFG-021 | Phase 5 | P1 | Trivial | `database_url_direct` field declared at line 83 but absent from `_validate_produ | Add `database_url_direct` presence and scheme check to `_validate_production_env | config_verification.md |
| CFG-022 | Phase 5 | P1 | Trivial | `secret_key: str = Field(default="", min_length=32, secret=True)` | Add `min_length=64` to `secret_key` Field | config_verification.md |
| CFG-023 | Phase 5 | P1 | Trivial | `database_url: str = Field(default="")` has no scheme validation | Add `pattern` or validator enforcing `postgresql+asyncpg://` prefix | config_verification.md |
| CFG-024 | Phase 5 | P1 | Trivial | `valkey_url: str = Field(default="")` has no scheme validation | Add `pattern` or validator enforcing `valkey://` prefix | config_verification.md |
| CFG-025 | Phase 5 | P1 | Trivial | `audit_chain_key: str = Field(default="", secret=True)` has no `min_length` cons | Add `min_length=32` to `audit_chain_key` Field | config_verification.md |
| CFG-026 | Phase 5 | P1 | Trivial | `field_encryption_key: str = Field(default="", secret=True)` has no `min_length` | Add `min_length=64` to `field_encryption_key` Field | config_verification.md |
| CFG-027 | Phase 5 | P1 | Trivial | `database_url_direct: str = Field(default="")` has no `min_length` or scheme val | Add `min_length=1` and scheme pattern to `database_url_direct` Field | config_verification.md |
| COLLECT-001 | testing | P0 | S | ModuleNotFoundError: No module named 'infrastructure.utils.circuit_breaker' | Add missing infrastructure/utils/circuit_breaker.py module or correct import pat | 12_tests_collection_verify.md |
| COLLECT-002 | testing | P0 | S | ModuleNotFoundError: No module named 'domains.finance.services.payments' | Add missing domains/finance/services/payments/ module or correct import path in  | 12_tests_collection_verify.md |
| COLLECT-003 | testing | P0 | S | ModuleNotFoundError: No module named 'domains.finance.services.payments' | Add missing domains/finance/services/payments/ module or correct import path in  | 12_tests_collection_verify.md |
| COLLECT-004 | testing | P0 | S | 3 collection errors during pytest --collect-only | Resolve underlying import errors in COLLECT-001 through COLLECT-003 | 12_tests_collection_verify.md |
| CONTRAD-001 | arch | P0 | M (2h) | `modules/finance/` directory exists with `routers/cash_management.py` | Delete `modules/finance/`; move any legitimate routes to `modules/admin/routers/ | 07_CONTRADICTIONS.md |
| CONTRAD-002 | arch | P0 | L (8h) | `domains/payments/` directory exists with models, services, ports, events, subsc | Delete `domains/payments/`; consolidate into `providers/payments/` and `domains/ | 07_CONTRADICTIONS.md |
| CONTRAD-005 | tech | P0 | M (2h) | `fastapi==0.115.2` | Bump FastAPI to 0.141.x or update TECHNOLOGY_STACK.md to match installed version | 07_CONTRADICTIONS.md |
| CONTRAD-016 | build | P0 | M (2h) | `slowapi==0.1.10` and `limits==5.8.0` in requirements.txt | Replace `slowapi==0.1.10` and `limits==5.8.0` with `fastapi-limiter-valkey` in r | 07_CONTRADICTIONS.md |
| CONTRAD-020 | config | P0 | S (0.5h) | `vat_rate: float = Field(default=0.0)` and `zozi_commission_rate: float = Field( | Change `vat_rate` and `zozi_commission_rate` to `Decimal` in config.py and remov | 07_CONTRADICTIONS.md |
| CONTRAD-034 | arch | P0 | S (0.5h) | Both `hr.py` (file) and `hr/` (package directory) exist in `modules/employee/rou | Remove the orphaned `hr.py` file; consolidate all HR router code into the `hr/`  | 07_CONTRADICTIONS.md |
| CONTRAD-036 | build | P0 | S (0.5h) | `fastapi-limiter-valkey` not listed in requirements.txt | Add `fastapi-limiter-valkey` to requirements.txt | 07_CONTRADICTIONS.md |
| D2P-001 | infra | P0 | L (8h) | No CI workflows in .github/workflows/ | Create .github/workflows/ with ci.yml, schema-drift.yml, docs-drift.yml, e2e.yml | 13_dev_to_prod.md |
| D2P-006 | infra | P0 | M (3h) | No Coolify configuration in repository | Document deployment target and path; add Coolify env-var mapping or alternative  | 13_dev_to_prod.md |
| D2P-DOCKER-001 | infra | P0 | L (8h) | No Celery workers, no Beat scheduler defined | Add celery-worker-ml, celery-worker-periodic, celery-worker-payouts, celery-work | 13_dev_to_prod_docker_verify.md |
| D2P-DOCKER-002 | infra | P0 | S (0.5h) | valkey:8-alpine | Update valkey image to valkey:9.0-alpine in docker-compose.prod.yml | 13_dev_to_prod_docker_verify.md |
| D2P-DOCKER-003 | infra | P0 | M (3h) | No Coolify configuration file exists | Create Coolify configuration or document Coolify service setup in SETUP.md | 13_dev_to_prod_docker_verify.md |
| DB-001 | db | P0 | L (8h) | 5 divergent migration heads (`20260930_0002`, `20260930_0003`, `20260930_0006`,  | Merge all 5 heads into single linear chain via new merge migration | 06_database.md |
| DRIFT-002 | routing | P0 | L (8h) | File docstring says "Admin orders router — canonical" and prefix is `/api/v1/adm | Move campaign routes to `comms.py`; create proper order management routes under  | 25_ai_drift.md |
| FEAT-001 | logic | P0 | M (2h) | Cart totals use `float` for subtotal in `item.price * item.quantity` | Cast to Decimal before multiplication; use `kernel.money.round_money` | 16_features.md |
| FEAT-002 | logic | P0 | M (2h) | `round(safe_unit_price * max(quantity_value, 0), 2)` uses float | Use `Decimal.quantize(Decimal('0.01'))` for all money fields | 16_features.md |
| FEAT-003 | logic | P0 | M (2h) | `float(product.price)` serialization drops Decimal precision | Serialize prices via `str(product.price)` or kernel money formatter | 16_features.md |
| FEAT-004 | logic | P0 | L (8h) | `INVENTORY_HELD_STATUSES` defined but no inventory release/claim flow found | Add `claim_inventory` on confirmed→processing and `release_inventory` on cancell | 16_features.md |
| FEAT-005 | db | P0 | L (8h) | `payments` table in `finance` schema but `PaymentGatewayConnection.credentials`  | Encrypt `credentials`, `secret_key`, `webhook_secret` columns via AES-256-GCM be | 16_features.md |
| FEAT-009 | logic | P0 | M (2h) | `subtotal = sum(item.price * item.quantity for item in body.items)` uses float | Convert to Decimal via `kernel.money.to_decimal` before arithmetic | 16_features.md |
| FEAT-010 | logic | P0 | M (2h) | `calculate_tax(float(after_discount), country_code, db)` passes float | Pass Decimal to `calculate_tax`; update function signature | 16_features.md |
| FEAT-022 | logic | P0 | L (8h) | `credentials = Column(JSON, nullable=True)` stores gateway API keys unencrypted | Encrypt entire credentials JSON via `field_encryption.py` | 16_features.md |
| FEAT-025 | logic | P0 | L (8h) | `INVENTORY_HELD_STATUSES` constant exists but no claim/release calls in order en | Wire `claim_inventory` in `create_order` and `release_inventory` in `cancel_orde | 16_features.md |
| FEAT-040 | logic | P1 | M (3h) | General ledger exists but tax calculation function signature accepts float | Ensure `calculate_tax` and all ledger writers use Decimal | 16_features.md |
| LOGIC-001 | logic | P0 | S (0.5h) | `CodRemittanceRequest.amount: float` | Change type to `Decimal` with `Field(..., ge=0)` | 03_logical.md |
| LOGIC-002 | logic | P0 | S (0.5h) | `reconcile_in_multi_currency(amount: float, ...)` uses `round(amount * fx, 2)` w | Change signature to `amount: Decimal`, use `Decimal(str(amount)) * rate` then `q | 03_logical.md |
| MOB-001 | mobile | P1 | M (2h) | `expo.modules.updates.ENABLED=false` | Set ENABLED=true; add `expo-updates` to dependencies; configure `runtimeVersion` | 15_frontend_mobile.md |
| MOB-002 | mobile | P1 | M (2h) | `expo-updates` listed as "Always" for OTA JS bundle updates | Install `expo-updates`; wire `Updates.checkForUpdateAsync()` in `_layout.tsx` | 15_frontend_mobile.md |
| OBS-003 | infra | P1 | S (0.5h) | `monitoring/prometheus/prometheus.yml` has `rule_files: []` and empty `alertmana | Remove stale `monitoring/prometheus/prometheus.yml` or align it with the root co | 20_observability_resilience.md |
| OBS-105 | infra | P1 | S (1h) | `_startup_background_jobs()` starts daemon threads for email, finance, ML; no ba | Call `get_backup_manager()` and start a periodic scheduler thread in `lifespan.p | 20_observability_resilience.md |
| OBS-108 | infra | P1 | S (1h) | `run_restore_drill()` method exists and is callable; `scripts/pg_backup.py:309`  | Register a periodic Celery task (or cron job) that calls `run_restore_drill()` a | 20_observability_resilience.md |
| OPS-001 | infra | P0 | S (1h) | `/health/deps` returns 200 with dependency dict even when DB/Valkey/email/paymen | Add `status_code=503` to `JSONResponse` when any critical dep status is `failed` | 04_operational.md |
| OPS-002 | infra | P0 | L (8h) | No `.github/workflows/` directory; no CI/CD pipeline exists | Create `.github/workflows/deploy.yml` with pre-deploy `alembic upgrade head`, `/ | 04_operational.md |
| PERF-001 | db | P0 | S (0.5h) | `cart_items = relationship("CartItem", back_populates="product")` — default `laz | Add `lazy="selectin"` to the `cart_items` relationship | 19_performance.md |
| PERF-002 | frontend | P0 | S (0.5h) | `items = relationship('OrderItem', back_populates='order')` — default `lazy="sel | Add `lazy="selectin"` to the `items` relationship | 19_performance.md |
| SUP-007 | security | P0 | S (0.5h) | `SECRET_KEY=K1shXALnoZnJzgvaq5DIwh9SWXWPX1YGNi5cY97jjTM2cFN4I9F6jWXVITL9fgKW` in | Rotate SECRET_KEY immediately; remove `.env` files from working tree; use Coolif | 28_supply_chain_security.md |
| TECH-001 | tech | P0 | M (2h) | uv.lock contains only virtual package zozi-backend 0.1.0; no [[package]] entries | Run `uv lock` in backend/ to populate uv.lock | 02_technological.md |
| TECH-002 | tech | P0 | M (2h) | pyproject.toml has no [project.dependencies] or [tool.uv] section | Add [project.dependencies] to pyproject.toml with canonical versions | 02_technological.md |
| TECH-003 | tech | P0 | L (8h) | requirements.txt with pip install in Dockerfile and CI | Migrate to uv: add deps to pyproject.toml, remove requirements.txt | 02_technological.md |
| TECH-004 | tech | P0 | M (2h) | `pip install --no-cache-dir -r requirements.txt` | Replace pip install with `COPY pyproject.toml uv.lock . && uv sync --frozen --no | 02_technological.md |
| TECH-005 | tech | P0 | S (1h) | `pip install -r backend/requirements.txt` | Replace pip install with `uv sync --frozen` in CI workflow | 02_technological.md |
| TECH-006 | boot | P0 | S (0.5h) | `FROM python:3.11-slim` | Change base image to python:3.13-slim | 02_technological.md |
| TECH-007 | boot | P0 | M (2h) | `pip install` for dependency installation | Replace pip install with uv | 02_technological.md |
| TECH-008 | tech | P0 | M (3h) | `psycopg2-binary==2.9.12` | Remove psycopg2-binary, replace imports with asyncpg | 02_technological.md |
| TECH-009 | tech | P0 | M (3h) | `requests==2.34.2` | Remove requests, migrate all imports to httpx | 02_technological.md |
| TECH-011 | tech | P0 | M (2h) | `prometheus-client==0.26.0` | Remove prometheus-client, use prometheus-fastapi-instrumentator exclusively | 02_technological.md |
| TECH-014 | tech | P0 | M (4h) | `import paypalrestsdk as _paypal_sdk` | Replace with direct REST calls via httpx | 02_technological.md |
| TECH-015 | tech | P0 | M (4h) | `from paypalcheckoutsdk.core import PayPalHttpClient` | Replace with direct REST calls via httpx | 02_technological.md |
| TECH-020 | tech | P0 | M (2h) | `fastapi==0.115.2` | Upgrade fastapi to 0.141.x | 02_technological.md |
| TECH-030 | tech | P0 | S (0.5h) | starlette unpinned may resolve to <0.47.2 (CVE-2025-54121) or <0.49.1 (CVE-2025- | Pin starlette to >=1.6.0,<1.7.0 | 02_technological.md |
| TECH-050 | tech | P0 | S (1h) | `npm ci --legacy-peer-deps` and `npm run build` | Replace npm with pnpm in Dockerfile | 02_technological.md |
| TF-001 | db | P0 | M | alembic current shows 5 heads: 20260930_0002, 20260930_0003, | Merge 5 heads into 1 | 07_tables_fields.md |
| TF-002 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-003 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-004 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-005 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-006 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-007 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-008 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-009 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-010 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-011 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-012 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-013 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-014 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-015 | db | P1 | M | Table exists in DB but has no matching model in domains/*/mo | Create model class in appropriate domain | 07_tables_fields.md |
| TF-016 | db | P1 | M | Model in backend\domains\hr\models\employee_models.py:531 ha | Add schema to __table_args__ | 07_tables_fields.md |
| TF-017 | db | P1 | M | Model in backend\domains\hr\models\employee_models.py:560 ha | Add schema to __table_args__ | 07_tables_fields.md |
| TF-018 | db | P1 | M | Model exists but table not found in live database | Apply pending Alembic migration | 07_tables_fields.md |
| TF-019 | db | P1 | M | Model exists but table not found in live database | Apply pending Alembic migration | 07_tables_fields.md |
| TF-021 | db | P1 | M | Column 'pipeline_status' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-023 | db | P1 | M | Column 'step_status' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-032 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-034 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-035 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-036 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-038 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-043 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-045 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-047 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-049 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-050 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-052 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-054 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-058 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-060 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-063 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-065 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-066 | db | P1 | M | Column 'is_deleted' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-067 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-069 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-072 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-074 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-075 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-078 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-079 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-080 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-082 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-083 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-085 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-087 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-089 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-090 | db | P1 | M | Column 'is_deleted' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-092 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-093 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-097 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-098 | db | P1 | M | Column 'is_deleted' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-100 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-102 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-103 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-104 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-106 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-107 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-109 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-110 | db | P1 | M | Column 'is_deleted' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-113 | db | P1 | M | Column 'updated_at' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-114 | db | P1 | M | Column 'is_deleted' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-116 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-119 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-122 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-125 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-157 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-227 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-228 | db | P1 | M | Column 'requested_by_id' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-229 | db | P1 | M | Column 'approved_by_id' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-231 | db | P1 | M | Column 'metadata_json' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-233 | db | P1 | M | Column 'metadata_json' in model but not in live DB | Apply migration to add missing column | 07_tables_fields.md |
| TF-269 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
| TF-271 | db | P1 | M | User-facing table missing country_code column (Law 5, 20) | Add country_code column via migration | 07_tables_fields.md |
