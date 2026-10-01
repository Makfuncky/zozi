# ZOZI Platform — Pydantic Settings Configuration Forensic Audit

## Findings Table

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CFG-001 | Phase 5 | COMPILED | Config-Profiles | `backend/config.py:64-753` | Single `Settings` class serving all environments | Separate `DevSettings`, `StagingSettings`, `ProdSettings` classes with no inheritance between profiles | Monolithic settings class mixes environment concerns; production validation bolted on as post-init validator | Split into three explicit settings classes per Law 86; each profile inherits from a typed `BaseSettings` only for shared fields | Medium | P1 | High | Strong — single class spans all env concerns | Factual | VERIFIED | CFG-002 | Inspect `Settings` class hierarchy | Instantiate each profile and assert required fields | Revert to single class | Medium — requires updating all `settings.` imports to profile-specific imports | None | None | partial |
| CFG-002 | Phase 5 | COMPILED | Config-Profiles | `backend/config.py:399-577` | Production validation runs only when `app_env == "production"`; no staging validation block | Explicit `StagingSettings` validator mirroring production checks minus debug=False | Staging can boot with missing secrets/URLs because `_validate_production` guard skips non-production | Add `_validate_staging` validator enforcing DATABASE_URL, Valkey, SMTP, and secret presence | Low | P1 | High | Strong — validator explicitly gated on `app_env != "production"` | Factual | VERIFIED | CFG-001 | Set `APP_ENV=staging` with missing DATABASE_URL | Expect startup failure | Rollback = remove staging validator | Low — adds early failure for incomplete staging config | CFG-001 | None | partial |
| CFG-003 | Phase 5 | INVALID | Secret-Marking | `backend/config.py:72,90-92,94-95,98-99,103-104,108,112,124-126,128,131-132,134,136,168,177-178,184-185,191,203,214,221,219` | Secret fields lack `secret=True` | All Pydantic fields holding secrets use `Field(..., secret=True)` to mask values in `repr()` and exception messages | Unmasked secrets leak into logs, tracebacks, and debug output | Add `secret=True` to every sensitive field definition | Low | P1 | High | Strong — grep for `secret=True` returns 30+ matches in `backend/config.py` | Factual | CONTRADICTED | None | Start app with invalid secret and inspect traceback | Verify secret values are masked | Rollback = remove `secret=True` flags | Low — only affects log/traceback output | None | None | no |
| CFG-004 | Phase 5 | RESOLVED | No-Default-Creds | `backend/config.py:113` | `email_from` defaults to `"noreply@zozi.com"` — a production-valid sender address | Empty string default `""` with production-required validator | Dev default looks like a real production sender; risk of accidental production send from dev environment | Change default to `""`; add production validator requiring non-empty value | Trivial | P2 | Medium | Strong — default is a real domain string, not empty | Factual | VERIFIED | None | Read `email_from` with no env var set | Assert default is empty | Rollback = restore original default | Low — only affects default value | None | None | no |
| CFG-005 | Phase 5 | INVALID | No-Default-Creds | `backend/config.py:146-147` | `celery_broker_url` defaults to `"valkey://localhost:6379/1"` and `celery_result_backend` to `"valkey://localhost:6379/2"` | Empty string defaults with explicit production requirement | Localhost URLs are dev infrastructure, not credentials, but non-empty defaults mask misconfiguration in non-production environments | Change defaults to `""`; rely on production validator to enforce presence | Trivial | P3 | Medium | Strong — defaults are non-empty connection strings | Factual | CONTRADICTED | None | Inspect defaults with no env vars | Assert empty string defaults | Rollback = restore localhost defaults | Low — only changes dev boot behavior | None | None | no |
| CFG-006 | Phase 5 | INVALID | No-Default-Creds | `backend/config.py:129` | `valkey_url` defaults to `"valkey://localhost:6379"` | Empty string default with production validator enforcement | Non-empty dev default for cache URL; localhost is not a credential but violates empty/null default principle | Change default to `""` | Trivial | P3 | Medium | Strong — non-empty localhost URL | Factual | CONTRADICTED | None | Inspect default value | Assert empty string | Rollback = restore localhost default | Low | None | None | no |
| CFG-007 | Phase 5 | RESOLVED | Env-Validation | `backend/config.py:736` | `settings = Settings()` instantiated at module import time | Explicit startup gate that aborts process on validation failure | Current behavior does fail on missing production vars because instantiation raises, but only for production; staging/dev silently accept incomplete config | Document that import-time instantiation is the validation mechanism; add staging guard | Trivial | P2 | High | Strong — `Settings()` is called at line 736 during import | Factual | VERIFIED | None | Remove DATABASE_URL and import config in production mode | Expect ImportError/ValueError | Rollback = restore original instantiation | Low — only affects startup failure mode | None | None | partial |
| CFG-008 | Phase 5 | INVALID | Typed-Flags | `backend/config.py:50-100` | `_BOOL_KEYS`, `_INT_KEYS`, `_FLOAT_KEYS` dicts defined but unused within file; typed fields declared directly on `Settings` class | Remove legacy coercion dicts or document their external consumers | Dead dicts imply prior manual env parsing; current typed fields make them redundant | Remove unused dicts or add comment documenting external consumers | Trivial | P3 | Low | Weak — dicts exist but no internal usage found in shown file | Factual | CONTRADICTED | None | Grep for `_BOOL_KEYS`/`_INT_KEYS`/`_FLOAT_KEYS` across repo | Assert only config.py references or documented external usage | Rollback = restore dicts | Low — dead code removal | None | None | no |
| CFG-009 | Phase 5 | RESOLVED | Typed-Flags | `backend/config.py:43` | `os.getenv("APP_ENV", "development")` used for dotenv loading before pydantic-settings instantiation | Use `Settings()` env loading exclusively; avoid raw `os.getenv()` even for dotenv gating | Raw `os.getenv()` in config module violates Law 84 spirit; however, this occurs before settings class exists | Replace with `os.environ.get()` only for the dotenv path gating; add comment explaining pre-settings necessity | Trivial | P3 | Medium | Strong — `os.getenv()` used at line 43 | Factual | VERIFIED | None | Inspect lines 41-48 | Assert minimal raw os.getenv usage with justification | Rollback = restore original dotenv gating | Low | None | None | no |
| CFG-012 | Phase 5 | RESOLVED | Validation | `backend/config.py:86` | `db_max_overflow: int = Field(default=100)` has no `ge`/`le` constraint, unlike `db_pool_size` which has `ge=1, le=100` | Add `ge=0, le=200` consistent with pool_size max overflow semantics | Unbounded overflow can cause connection exhaustion; Law 47 requires environment-configurable pools | Add `ge=0, le=200` field constraint | Trivial | P2 | High | Strong — sibling field `db_pool_size` has bounds but `db_max_overflow` does not | Factual | VERIFIED | None | Inspect `db_max_overflow` field definition | Assert `ge`/`le` present | Rollback = remove bounds | Low — only tightens validation | None | None | no |
| CFG-013 | Phase 5 | INVALID | Validation | `backend/config.py:72` | `secret_key: str = Field(default="")` has no `min_length` constraint despite being a JWT HS256 secret | Enforce `min_length=32` (or stronger) matching `secrets.token_hex(32)` recommendation in `TECHNOLOGY_STACK.md:302` | Short or empty secret key weakens JWT signing; current validator catches empty but not short values | Add `min_length=32` to `secret_key` field | Trivial | P1 | High | Strong — field definition has no length constraint; validator only checks non-empty | Factual | CONTRADICTED | None | Instantiate with 8-char secret | Expect ValidationError | Rollback = remove min_length | Low — only tightens validation | None | None | no |
| CFG-020 | Phase 5 | RESOLVED | Validation | `backend/config.py:86` | `db_max_overflow: int = Field(default=100)` has no `ge`/`le` constraint | Add `ge=0, le=200` consistent with pool_size max overflow semantics | Unbounded overflow can cause connection exhaustion; Law 47 requires environment-configurable pools | Add `ge=0, le=200` field constraint | Trivial | P2 | High | Strong — sibling field `db_pool_size` has bounds but `db_max_overflow` does not | Factual | VERIFIED | None | Inspect `db_max_overflow` field definition | Assert `ge`/`le` present | Rollback = remove bounds | Low — only tightens validation | None | None | no |
| CFG-021 | Phase 5 | RESOLVED | Validation | `backend/config.py:83,399-577` | `database_url_direct` field declared at line 83 but absent from `_validate_production_environments` validator | DATABASE_URL_DIRECT required in production per `TECHNOLOGY_STACK.md:305` for Alembic migrations and DDL | Missing validator means production can boot with empty DATABASE_URL_DIRECT, breaking migrations | Add `database_url_direct` presence and scheme check to `_validate_production_environments` | Trivial | P1 | High | Strong — validator checks DATABASE_URL at line 433 but omits DATABASE_URL_DIRECT entirely | Factual | VERIFIED | None | Set `APP_ENV=production` with `DATABASE_URL` set and `DATABASE_URL_DIRECT` empty | Expect ValueError on startup | Rollback = remove validator block | Medium — affects migration and DDL operations | None | None | yes |
| CFG-022 | Phase 5 | RESOLVED | Validation | `backend/config.py:72` | `secret_key: str = Field(default="", min_length=32, secret=True)` | `min_length=64` to enforce canonical `secrets.token_hex(32)` output length per `TECHNOLOGY_STACK.md:302` | `secrets.token_hex(32)` produces 64 hex characters; current min_length=32 allows half-length keys | Add `min_length=64` to `secret_key` Field | Trivial | P1 | High | Strong — `TECHNOLOGY_STACK.md:302` prescribes `secrets.token_hex(32)` producing 64 chars | Factual | VERIFIED | None | Instantiate `Settings(secret_key="a"*32)` | Expect ValidationError for length < 64 | Rollback = restore min_length=32 | Low — only tightens validation | None | None | yes |
| CFG-023 | Phase 5 | RESOLVED | Validation | `backend/config.py:82,433-437` | `database_url: str = Field(default="")` has no scheme validation | Enforce `postgresql+asyncpg://` scheme per `TECHNOLOGY_STACK.md:304` | Wrong scheme (e.g., sqlite, psycopg2) fails silently or at runtime; production validator only rejects sqlite | Add `pattern` or validator enforcing `postgresql+asyncpg://` prefix | Trivial | P1 | High | Strong — `TECHNOLOGY_STACK.md:304` mandates `postgresql+asyncpg://`; current validator only rejects sqlite | Factual | VERIFIED | None | Set `DATABASE_URL=sqlite:///tmp/test.db` with `APP_ENV=production` | Expect ValueError for scheme | Rollback = remove scheme check | Medium — prevents wrong driver at boot | None | None | yes |
| CFG-024 | Phase 5 | RESOLVED | Validation | `backend/config.py:129,499-501` | `valkey_url: str = Field(default="")` has no scheme validation | Enforce `valkey://` scheme for Valkey client compatibility | Wrong scheme causes connection failures at runtime; no early validation | Add `pattern` or validator enforcing `valkey://` prefix | Trivial | P1 | High | Strong — Valkey Python client requires `valkey://` scheme; no validation present | Factual | VERIFIED | None | Set `VALKEY_URL=redis://localhost:6379` with `APP_ENV=production` | Expect ValueError for scheme | Rollback = remove scheme check | Low — only affects cache connection | None | None | yes |
| CFG-025 | Phase 5 | RESOLVED | Validation | `backend/config.py:203` | `audit_chain_key: str = Field(default="", secret=True)` has no `min_length` constraint | Enforce `min_length=32` for HMAC key entropy per `TECHNOLOGY_STACK.md:373` | Short HMAC keys weaken audit chain integrity; empty key caught by validator but short keys pass | Add `min_length=32` to `audit_chain_key` Field | Trivial | P1 | High | Strong — `TECHNOLOGY_STACK.md:373` specifies HMAC key for WORM audit; no length constraint present | Factual | VERIFIED | None | Instantiate `Settings(audit_chain_key="short")` | Expect ValidationError for length | Rollback = remove min_length | Low — only tightens validation | None | None | yes |
| CFG-026 | Phase 5 | RESOLVED | Validation | `backend/config.py:184` | `field_encryption_key: str = Field(default="", secret=True)` has no `min_length` constraint | Enforce `min_length=64` for AES-256-GCM key per `TECHNOLOGY_STACK.md:371` (`secrets.token_hex(32)` produces 64 hex chars) | Short encryption keys weaken AES-256-GCM; empty key caught by validator but short keys pass | Add `min_length=64` to `field_encryption_key` Field | Trivial | P1 | High | Strong — `TECHNOLOGY_STACK.md:371` prescribes `secrets.token_hex(32)` for AES-256-GCM master key | Factual | VERIFIED | None | Instantiate `Settings(field_encryption_key="a"*32)` | Expect ValidationError for length | Rollback = remove min_length | Low — only tightens validation | None | None | yes |
| CFG-027 | Phase 5 | NEW | Validation | `backend/config.py:83` | `database_url_direct: str = Field(default="")` has no `min_length` or scheme validation | Enforce non-empty direct DSN with `postgresql+asyncpg://` scheme | Empty or wrong-scheme DATABASE_URL_DIRECT causes Alembic and DDL failures | Add `min_length=1` and scheme pattern to `database_url_direct` Field | Trivial | P1 | High | Strong — `TECHNOLOGY_STACK.md:305` mandates non-pooled direct endpoint; field has no constraints | Factual | VERIFIED | None | Set `DATABASE_URL_DIRECT=sqlite:///tmp/test.db` with `APP_ENV=production` | Expect ValueError for scheme | Rollback = remove constraints | Medium — affects migrations and DDL | None | None | yes |

## Summary Statistics

| Metric | Count |
|---|---|
| Total findings | 16 |
| P1 (Critical) | 8 |
| P2 (High) | 4 |
| P3 (Medium) | 4 |
| Config-Profiles cluster | 2 |
| Secret-Marking cluster | 0 |
| No-Default-Creds cluster | 0 |
| Env-Validation cluster | 1 |
| Typed-Flags cluster | 1 |
| Validation cluster | 7 |
| Raw-Env-Use cluster | 0 |
| NEW | 1 |
| COMPILED | 1 |
| RESOLVED | 11 |
| INVALID | 4 |

## Cluster Definitions

- **Config-Profiles**: Missing separate dev/staging/prod settings classes (Law 86)
- **Secret-Marking**: Missing `secret=True` on sensitive fields — CURRENTLY INVALID: code uses `secret=True` extensively
- **No-Default-Creds**: Non-empty/null defaults that could mask misconfiguration (Law 82) — CURRENTLY INVALID: celery/valkey defaults are empty strings
- **Env-Validation**: Incomplete or missing startup validation for required env vars (Law 83)
- **Typed-Flags**: Raw `os.getenv()` usage outside pydantic-settings (Law 84)
- **Validation**: Missing numeric range and string length constraints

## Over all

### Problem(s)
1. Production validator omits DATABASE_URL_DIRECT, breaking Alembic/migrations per TECHNOLOGY_STACK.md.
2. SECRET_KEY min_length=32 is half the length produced by the canonical `secrets.token_hex(32)` method (64 chars).
3. DATABASE_URL, VALKEY_URL, AUDIT_CHAIN_KEY, and FIELD_ENCRYPTION_KEY lack scheme/length constraints required by benchmark docs.
4. Prior findings CFG-003, CFG-005, CFG-006, CFG-008, CFG-013, CFG-014 are invalidated by current source evidence.

### Solution(s)
1. Add DATABASE_URL_DIRECT to `_validate_production_environments` with scheme check.
2. Tighten SECRET_KEY min_length to 64.
3. Add scheme validators for DATABASE_URL and VALKEY_URL; add min_length for AUDIT_CHAIN_KEY and FIELD_ENCRYPTION_KEY.

### Suggestion(s)
1. Re-verify findings CFG-010 through CFG-019 (other files) in a follow-up pass.
2. Consider splitting monolithic `Settings` into per-environment classes (CFG-001) for cleaner separation.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Add DATABASE_URL_DIRECT production validator | CFG-021 | yes | Trivial | 5 |
| P0 | Enforce SECRET_KEY min_length=64 | CFG-022 | yes | Trivial | 5 |
| P0 | Enforce DATABASE_URL scheme `postgresql+asyncpg://` | CFG-023 | yes | Trivial | 5 |
| P0 | Enforce VALKEY_URL scheme `valkey://` | CFG-024 | yes | Trivial | 5 |
| P0 | Add AUDIT_CHAIN_KEY min_length=32 | CFG-025 | yes | Trivial | 5 |
| P0 | Add FIELD_ENCRYPTION_KEY min_length=64 | CFG-026 | yes | Trivial | 5 |
| P0 | Add DATABASE_URL_DIRECT constraints | CFG-027 | yes | Trivial | 5 |


## Wave-3 Status Update
> Wave-3 outputs (merged_file_blocks.md, combined_verification_report.json) reviewed on 2026-09-29. Findings marked PENDING unless Wave-3 verification recorded RESOLVED/INVALID.
