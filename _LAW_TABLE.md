
## Project Rules & Decisions (Laws 1-325)

> All 325 laws in a single scannable matrix. Each law appears **once**.

| Law | Category | Rule | Description | Why |
|-----|----------|------|-------------|-----|
| 1 | Architecture | Arrows point down | Dependencies flow: modules → domains → infrastructure → kernel. Reverse imports FORBIDDEN. | Prevents circular dependencies and unmaintainable coupling between layers. |
| 2 | Architecture | Thin routers | Router = auth context + require_feature + ONE service call + serialization. No DB writes, no business logic. | Keeps API layer a thin HTTP shim over domain logic. Easy to test and maintain. |
| 3 | Architecture | Cross-domain events/ports | Cross-domain WRITES via events.py/subscribers.py. Cross-domain READS via ports.py only. | Keeps domains decoupled and independently deployable. |
| 4 | Architecture | Features single-sourced | Permission atoms defined once in domains/*/features.py. Aggregated by rbac/catalog.py. | Prevents permission drift. Frontend and backend share one permission model. |
| 5 | Architecture | Country is orthogonal | Every data access scoped by country_code via RLS. Independent of feature check. | Ensures multi-tenant data isolation at the database level. |
| 6 | Architecture | Schema discipline | Every table in a domain Postgres schema. Alembic is the only schema source. | Naming consistency and single source of truth for schema changes. |
| 7 | Architecture | Allowlist only shrinks | DOMAIN_ALLOWLIST.yaml tracks temporary cross-domain imports. May only shrink. | Ensures migration toward clean domain boundaries makes forward progress. |
| 8 | Structure | Router structure | modules/{m}/routers/{d}.py — one file per domain per module (15 per module). | Makes endpoints discoverable by actor+domain combination. |
| 9 | Structure | Tools in providers | All tools code in providers/ai, providers/image. | tools is an external concern, not a business domain. |
| 10 | Structure | Kernel is pure | kernel/ contains ONLY pure business primitives. No imports from domains/modules/rbac. | Ensures business primitives are consistent and reusable across all domains. |
| 11 | Structure | Providers wrap SDKs | A provider wraps exactly one external SDK. No business logic, no domain imports. | External dependencies are isolated and swappable. |
| 12 | Structure | 15 domains | Fixed set: accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers. | Prevents domain sprawl and ensures clear ownership boundaries. |
| 13 | Structure | 5 modules | Fixed set: admin, customer, employee, logistics, supplier. | Ensures the actor model stays coherent and manageable. |
| 14 | File Placement | Business logic → domains/ | All business logic in domain services/services/. No logic in routers or modules. | Business logic is colocated with the data it operates on (DDD). |
| 15 | File Placement | API endpoints → modules/routers/ | Every HTTP endpoint in a module router file named after the domain. | Endpoints grouped by business capability, not CRUD operation. |
| 16 | File Placement | SDK wrappers → providers/ | Every third-party integration under providers/{category}/. | Trivial to find every external dependency and swap implementations. |
| 17 | File Placement | Cross-domain → events/ports only | events.py (writes) and ports.py (reads) are the ONLY sanctioned cross-domain channels. | Creates a clear, auditable boundary contract between domains. |
| 18 | File Placement | Root forbidden folders | utils/, routers/, controllers/, services/, models/, db/ FORBIDDEN at backend/ root. | Prevents the 'god directory' anti-pattern. |
| 19 | Code Quality | No float for money | Monetary values MUST use Decimal or Numeric. Float FORBIDDEN for money. | Floating-point arithmetic introduces rounding errors causing financial discrepancies. |
| 20 | Code Quality | country_code = String(2) | Always String(2) following ISO 3166-1 alpha-2. | Consistency across all 15 domains simplifies joins, indexes, and RLS filtering. |
| 21 | Code Quality | Timestamps = server_default | created_at/updated_at use server_default=func.now() (DB-side), not Python-side. | Timestamps survive clock skew and are consistent in the database. |
| 22 | Code Quality | FK have ondelete | Every ForeignKey MUST declare explicit ondelete behavior. | Prevents unpredictable behavior across PostgreSQL versions. |
| 23 | Code Quality | Audit columns | Every model MUST include created_at, updated_at, country_code, is_deleted. | Required for RLS, debugging, compliance, and data recovery. |
| 24 | Code Quality | No forbidden schemas | core, platform, identity are FORBIDDEN as Postgres schema names. | Prevents monolithic shared-schema architecture. |
| 25 | Migration | Shift files first | All files to correct domains before reorganization. Never replace working code with stubs. | Ensures agents have complete file context for each domain. |
| 26 | Migration | Backward-compat shims | Temporary re-exports in infrastructure/utils/ for relocated files. | Enables gradual migration without breaking existing imports. |
| 27 | Migration | Delete temp scripts | Root-level fix_*.py, debug_*.py should be removed after use. | Keeps root clean and architecture clear. |
| 28 | Migration | _auto_stubs ≠ architecture | _auto_stubs.py are migration scaffolding, not architecture components. | Distinguishes temporary scaffolding from permanent architecture. |
| 29 | Migration | registry.py ≠ architecture | Service Registry and auto_wire.py were removed from architecture. | Prevents confusion about what is permanent architecture. |
| 30 | Provider | Graceful degradation | Domains handle missing SDKs via HAS_<SDK> flags. Never crash. | System runs in development without all production dependencies. |
| 31 | Provider | No domain imports | Providers MUST NOT import from domains, modules, rbac, jobs, middleware. | Data flows through parameters only. Ensures providers remain pure wrappers. |
| 32 | Security | No hardcoded secrets | JWT keys, API keys, passwords from env vars or secrets manager only. | Attackers can clone repo. Committed secrets = token forgery. |
| 33 | Security | Token type verification | All JWT decoders MUST verify the type claim (access vs refresh). | Prevents refresh tokens from being used as access tokens. |
| 34 | Security | Parameterized SQL | Use SQLAlchemy text() with bound parameters or ORM. No f-string interpolation. | Prevents SQL injection attacks. |
| 35 | Security | CSRF active | CSRF middleware MUST be active in all environments. | Prevents CSRF attacks in misconfigured deployments. |
| 36 | Security | Security headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy in production. | Prevents XSS, clickjacking, and other browser-based attacks. |
| 37 | Security | Rate limit fails closed | Redis unreachable = deny requests (not allow all). | Prevents brute-force and DoS when Redis is down. |
| 38 | Security | Password handling | Passwords >72 bytes rejected with error, never truncated. | bcrypt's 72-byte limit. Silent truncation creates security holes. |
| 39 | Security | No duplicate auth | Auth logic in exactly one canonical location. | Duplicate implementations with divergent behavior create security holes. |
| 40 | Security | CORS origin validation | Origin header validated against allowlist before reflection. | Prevents arbitrary websites from making authenticated requests. |
| 41 | Security | WebSocket auth | WebSocket connections MUST verify JWT type claim equals access. | Prevents stolen refresh tokens from opening WebSocket connections. |
| 42 | Security | Input validation | All public endpoints use Pydantic schemas. No raw dicts in router signatures. | Prevents malformed data from reaching domain services. |
| 43 | Security | Security event logging | Auth failures, 403s, rate-limit triggers logged at WARNING+. | Silent security events prevent incident detection. |
| 44 | Security | Dependency scanning | All deps scanned for CVEs in CI. High/critical block deployment. | Prevents supply-chain attacks via compromised dependencies. |
| 45 | Database | No N+1 queries | All relationships declare lazy=selectin or joined. Default lazy=select FORBIDDEN. | N+1 queries bring the database to its knees at 100K+ users. |
| 46 | Database | No SELECT * | Application queries MUST select explicit columns. | Wastes memory/I/O. Prevents covering indexes. Breaks on column reorder. |
| 47 | Database | Connection pool sizing | pool_size ≥ 10, max_overflow ≥ 20. Environment-configurable. | Connection exhaustion causes cascading failures under load. |
| 48 | Database | Read replica separation | Replica connections use independent pool settings. Read-heavy uses get_read_db(). | Without replicas, every read competes with writes for connections. |
| 49 | Database | Linear migration history | Alembic history MUST remain linear. Resolve divergent heads immediately. | Divergent heads break alembic upgrade head and cause deployment failures. |
| 50 | Database | Explicit transactions | All writes use explicit transaction management. Autocommit FORBIDDEN. | Ensures multi-step operations can roll back on failure. |
| 51 | Database | Single table ownership | Each table defined in exactly one domain. Duplicate __tablename__ FORBIDDEN. | Duplicate tables cause MetaData conflicts and runtime crashes. |
| 52 | Database | FK constraints | All FK columns have explicit ForeignKey with ondelete. | Prevents orphan rows and ensures referential integrity. |
| 53 | Database | Index FK columns | All FK columns have explicit index. PostgreSQL does NOT auto-index FKs. | Without indexes, JOINs degrade to sequential scans. |
| 54 | Database | Soft delete | All user-facing tables use is_deleted (boolean, default false). | Enables data recovery, audit trails, and safe cascading. |
| 55 | Database | Schema-per-domain | Every model declares __table_args__ = {schema: <domain>}. | Tables without schema land in public, breaking multi-tenant isolation. |
| 56 | Database | No forbidden schemas | core, platform, identity FORBIDDEN as schema names. | Prevents accidental coupling through shared schema namespace. |
| 57 | Database | Migration safety | Destructive migrations include backward-compatible strategy (expand-contract). | Enables zero-downtime rollback. |
| 58 | Code Quality | No print() in production | print() FORBIDDEN in production code. Use structlog logger. | print() bypasses log formatting and cannot be filtered by level. |
| 59 | Code Quality | No silent exceptions | All except blocks MUST log at minimum DEBUG level. | Silent exception swallowing makes debugging impossible. |
| 60 | Code Quality | No blocking in async | Async functions MUST NOT call blocking I/O. Use asyncio.sleep, httpx. | Blocking calls freeze the event loop, preventing other requests. |
| 61 | Code Quality | Bounded caches | All in-memory caches have max size and/or TTL. Unbounded dict FORBIDDEN. | Unbounded caches cause OOM at scale. |
| 62 | Code Quality | TODO/FIXME hygiene | TODO/FIXME must include ticket reference and expiration date. | Ensures technical debt is tracked and doesn't accumulate invisibly. |
| 63 | Code Quality | Type hints required | All public function signatures MUST have type hints. | Enables static analysis, IDE autocompletion, inline documentation. |
| 64 | Code Quality | Function length ≤50 | Functions SHOULD NOT exceed 50 lines (excl. docstrings/blanks). | Long functions are hard to test, debug, and reason about. |
| 65 | Code Quality | Indentation ≤4 levels | Maximum 4 levels of indentation per function. | Deeper nesting signals complex control flow needing refactoring. |
| 66 | Code Quality | No magic numbers | Numeric constants MUST be named constants or config values. | Named constants make business rules self-documenting and easy to change. |
| 67 | Code Quality | DRY principle | Duplicate code blocks (>5 lines) MUST be extracted into shared functions. | Copy-paste creates maintenance nightmares. |
| 68 | Code Quality | Consistent errors | All service functions use consistent error pattern (exceptions or Result). | Mixed patterns make error handling unpredictable for callers. |
| 69 | Testing | Domain smoke tests | Every domain MUST have at least one smoke test. | Catches circular imports, missing deps, broken __init__.py, syntax errors. |
| 70 | Testing | Architecture law tests | Every statically checkable law MUST have a corresponding test. | Ensures laws are actually enforced, not just documented. |
| 71 | Testing | No broken tests in CI | Collection-time failures MUST block CI. Fix within 24h. | Broken tests hide real failures. |
| 72 | Testing | Cross-domain integration | Cross-domain flows MUST have integration tests. | Unit tests verify single services; integration tests verify wiring. |
| 73 | Testing | Performance regression | Critical paths MUST have perf regression tests. Fail on >20% latency. | Prevents slow queries or missing indexes from shipping to production. |
| 74 | Testing | Test isolation | All tests use transaction-rolled-back sessions. No data leaks. | Each test is independent and order-independent. |
| 75 | Infrastructure | Graceful degradation | External failures MUST degrade gracefully AND log WARNING. | Silent fallbacks hide degradation from ops. |
| 76 | Infrastructure | Session lifecycle | Sessions managed via FastAPI dependency injection only. | Ensures sessions are properly closed even on exceptions. |
| 77 | Infrastructure | Async resource safety | Async resources use asyncio.Lock for init and disposal. | Prevents race conditions that create multiple engines. |
| 78 | Infrastructure | Middleware ordering | Pipeline order FIXED: Foundation → Auth → Rate → Webhook → Geo → Security → Observe → Compliance. | Reordering changes security posture. |
| 79 | Infrastructure | Global exception handler | Catches all uncaught exceptions. Returns structured response. No stack traces in prod. | Prevents stack trace leakage and ensures consistent error format. |
| 80 | Infrastructure | Graceful shutdown | Shutdown disposes DB engine, Redis, workers via lifespan.py. | Prevents connection leaks on restart. |
| 81 | Infrastructure | Health checks | /health, /health/deps, /health/ready verify all critical dependencies. | Load balancers use these for routing decisions. |
| 82 | Config | No default credentials | Config fallbacks MUST NOT contain real credentials. Empty/null default. | Prevents accidental use of dev credentials in production. |
| 83 | Config | Environment validation | Required env vars validated at startup. Missing = immediate failure. | Prevents silent fallbacks to development defaults in production. |
| 84 | Config | Typed feature flags | Flags use pydantic-settings. Raw os.getenv() FORBIDDEN. | String 'false' is truthy in Python. Typed coercion prevents bugs. |
| 85 | Config | Secret rotation | Secrets rotatable without deployment via env var updates. | Enables response to credential leaks without full redeployment. |
| 86 | Config | Env-specific configs | Prod, staging, dev have separate config profiles. No inheritance. | Prevents prod from inheriting dev defaults like debug=True. |
| 87 | Router | Auth on protected endpoints | All non-public endpoints MUST use get_current_user or equivalent. | Prevents accidental exposure of sensitive endpoints. |
| 88 | Router | Feature gate on protected | All non-public endpoints MUST use require_feature() or require_module(). | Ensures every protected endpoint has explicit authorization. |
| 89 | Router | Response serialization | Routers return serialized responses (Pydantic/dicts), never raw ORM models. | Prevents accidental exposure of internal model fields. |
| 90 | Router | No business logic | Routers contain ONLY: auth, gate, parsing, ONE service call, serialization. | Keeps API layer a thin HTTP shim. |
| 91 | Router | Documentation | All endpoints MUST have OpenAPI-compatible docstrings. | The OpenAPI spec is the API contract. |
| 92 | Observability | Structured logging | All logs use structlog with context (user_id, request_id, domain, action). | Enables log aggregation, filtering by field, cross-service correlation. |
| 93 | Observability | Request tracing | All requests carry request_id propagated through service calls. | Enables end-to-end request tracing for debugging. |
| 94 | Observability | Metrics emission | Critical paths emit Prometheus metrics (latency, error rate, throughput). | Unmonitored critical paths hide degradation. |
| 95 | Observability | Error tracking | Unhandled exceptions reported to Sentry with fallback to logger. | Prevents silent exception swallowing in production. |
| 96 | Observability | Audit trail | State-changing operations write to domains/audit/. | WORM audit log enables compliance investigations. |
| 97 | Wiring | Import direction | Imports MUST follow modules → domains → infrastructure → kernel. | Prevents reverse dependencies. |
| 98 | Wiring | No circular imports | Circular chains between any two packages FORBIDDEN. | Circular imports cause ImportError at module load time. |
| 99 | Wiring | No layer crossing | Modules don't import infrastructure directly. Domains don't import modules. | Prevents tight coupling across layers. |
| 100 | Wiring | Provider isolation | Providers don't import from domains/modules/rbac/jobs/middleware. | Ensures providers remain pure wrappers. |
| 101 | Wiring | Kernel isolation | kernel/ doesn't import from domains/modules/rbac/providers/jobs/middleware. | Kernel is the universal foundation layer. |
| 102 | Wiring | Infrastructure isolation | infrastructure/ doesn't import from domains/modules/rbac/providers. | Provides platform primitives to all layers. |
| 103 | Wiring | Job wiring | Jobs import from domains/ + infrastructure/ only. | Jobs are decoupled from HTTP layer. |
| 104 | Wiring | Middleware wiring | Middleware imports from infrastructure/ + rbac/ only. | Middleware operates at HTTP layer, needs only platform primitives. |
| 105 | Wiring | Shared package wiring | @zozi/shared doesn't import from web_app or mobile_app. | Shared is consumed BY apps, never imports FROM them. |
| 106 | Wiring | Frontend-backend wiring | Frontend communicates via API proxy only. No direct backend imports. | Ensures frontend and backend are decoupled deployables. |
| 107 | Technology | PostgreSQL in prod | Production uses PostgreSQL 15. SQLite for dev/test only. | PostgreSQL provides RLS, proper concurrency, JSONB, full-text search. |
| 108 | Technology | SQLite in dev | SQLite for zero-config startup. File in .gitignore. | Enables fast local development without DB server. |
| 109 | Technology | Redis usage | Sessions, catalog cache, rate limiting, blacklist, pub/sub, Celery. | Redis is an ephemeral cache, not a primary data store. |
| 110 | Technology | Redis failure handling | Sessions→DB fallback, caching pass-through, rate limit fails closed. | System degrades gracefully when Redis is unreachable. |
| 111 | Technology | Next.js App Router | Web uses Next.js App Router, not Pages Router. | Different routing and rendering models. |
| 112 | Technology | React Server Components | Data-fetching = Server Components. Client = interactivity/hooks. | RSC reduces JS bundle and enables server-side data access. |
| 113 | Technology | Expo Router | Mobile uses Expo Router with file-based routing. | Native navigation with deep linking. |
| 114 | Technology | WebSocket for realtime | WebSocket only for real-time (notifications, chat, tracking). | All other communication uses REST. |
| 115 | Technology | Celery for jobs | CPU-bound and async jobs use Celery with Redis broker. | Request handlers never block on CPU-bound work. |
| 116 | Technology | Email via SMTP | Transactional email via providers/comms/email.py. Async sending. | Prevents SMTP latency from blocking request handlers. |
| 117 | Technology | SMS via Twilio | SMS and WhatsApp via Twilio. Async sending. | Prevents SMS latency from blocking request handlers. |
| 118 | Technology | Payment gateways | Stripe, Tap, PayPal, PayTabs, Thawani. Each implements BasePaymentGateway. | Multi-PSP enables per-country payment methods. |
| 119 | Technology | AI/ML backends | Ollama, OpenAI, HuggingFace via providers/ai/. CPU via async_workers. | Isolates AI dependencies and prevents event loop blocking. |
| 120 | Technology | S3 storage | S3 (prod) or local (dev). Media blobs never in PostgreSQL. | Presigned URLs for direct upload/download. DB stays small. |
| 121 | Technology | Image processing | Pillow, rembg, OpenCV. Heavy processing via async_workers. | Prevents image processing from blocking the event loop. |
| 122 | Technology | Leaflet maps | Leaflet + react-leaflet. Geocoding via providers/geography/. | Map tiles from CDN, not bundled. |
| 123 | Provider | Single SDK per provider | Each provider wraps exactly one external SDK or service. | Makes providers independently testable and swappable. |
| 124 | Provider | HAS_ flags | Every provider exposes HAS_<SDK> boolean flags. | Enables graceful degradation when SDK is absent. |
| 125 | Provider | Degrade gracefully | When HAS_<SDK> = False, return defaults. Never crash. | System runs without all production dependencies. |
| 126 | Provider | No business logic | Providers contain ONLY SDK wrapping: auth, formatting, parsing, error mapping. | Business rules belong in domain services, not providers. |
| 127 | Provider | Config in providers/ | API keys, endpoints, timeouts in providers/config.py. | Enables per-environment config without code changes. |
| 128 | Provider | Async workers for CPU | CPU-bound provider work via providers/async_workers. | Prevents blocking the event loop. |
| 129 | Provider | Health checks | All providers expose health_check() via BaseProvider. | Enables /health/deps to verify external dependency health. |
| 130 | Provider | Error mapping | SDK errors mapped to domain exceptions. Raw SDK errors don't leak. | Decouples API from specific SDK error types. |
| 131 | Provider | Mock in tests | Provider tests mock the external SDK. No real API calls. | Tests are fast, reliable, and don't depend on external services. |
| 132 | Module | Module structure | modules/{name}/ with auth/, routers/, serializers/. | Each module is a complete actor context. |
| 133 | Module | Per-module auth | Each module has its own auth dependency in auth/dependencies.py. | Different actors may need different auth strategies. |
| 134 | Module | Router file naming | modules/{module}/routers/{domain}.py — one file per domain. | Makes endpoints discoverable by actor+domain. |
| 135 | Module | Router registration | All router files listed in routers/__init__.py. | Unregistered routers are invisible to FastAPI (dead code). |
| 136 | Module | Public vs protected | public_routers (no auth) vs routers (auth required). | Enables unauthenticated access to specific endpoints. |
| 137 | Module | Serializers location | Response serializers in modules/{module}/serializers/. | Different actors may serialize the same model differently. |
| 138 | Module | 5 modules fixed | admin, customer, employee, logistics, supplier. New requires review. | Prevents module sprawl. |
| 139 | Module | Route prefixes | /admin/*, /customer/*, /employee/*, /logistics-partner/*, /supplier/*. | Prevents route collisions between modules. |
| 140 | Infrastructure | 7 subpackages | database/, redis/, storage/, messaging/, observability/, security/, utils/. | Each subpackage has a single responsibility. |
| 141 | Infrastructure | Database infra | Base, get_db/get_read_db, sessions, RLS, transactions, seeds. | Single place for DB engine and session management. |
| 142 | Infrastructure | Redis infra | Client singleton, cache abstraction, blacklist, pub/sub. | Prevents connection proliferation. |
| 143 | Infrastructure | Storage infra | Abstraction interface + backup utilities. | Backends in providers/storage/. |
| 144 | Infrastructure | Messaging infra | WS manager, realtime, email wrappers, event bus. | Currently in-process; future: Redis pub/sub. |
| 145 | Infrastructure | Observability infra | OTEL, Prometheus, structlog, Sentry, circuit breaker. | Wires observability into the app at startup. |
| 146 | Infrastructure | Security infra | JWT, bcrypt, KMS encryption, rate limiting, CSRF, country access. | Canonical location for auth-related code. |
| 147 | Infrastructure | Utils infra | Pure technical helpers: pagination, datetime, config, caching, HTTP. | Business primitives belong in kernel/, not here. |
| 148 | Infrastructure | Canonical Base | infrastructure.database.base.Base is THE base. Others FORBIDDEN. | Multiple bases cause MetaData conflicts and migration failures. |
| 149 | Infrastructure | Session lifecycle | Sessions via FastAPI Depends(get_db) only. | Ensures sessions are closed even on exceptions. |
| 150 | Domain | Domain structure | services/, models/, schemas/, events.py, subscribers.py, ports.py, features.py, read_models/, policies/. | Standardized structure across all 16 domains. |
| 151 | Domain | Service patterns | Services take primitives, own DB access and transactions. | Services are the entry point for business logic. |
| 152 | Domain | Model patterns | __tablename__ + __table_args__ = {schema: <domain>}. Canonical Base. | Every model knows its schema and inherits from one base. |
| 153 | Domain | Schema patterns | Pydantic models for validation. Used by routers (in) and serializers (out). | Schemas are NOT ORM models — different purposes. |
| 154 | Domain | Event patterns | Named {domain}.{entity}.{action}. Minimal data (IDs, not objects). | Minimizes coupling between event publisher and subscribers. |
| 155 | Domain | Port patterns | Sanctioned cross-domain READ path. Take db + primitives, return results. | Ports are the ONLY importable thing from another domain. |
| 156 | Domain | Subscriber patterns | Handle events from other domains. Resolve context, call services. | Subscribers MUST NOT import from other domains directly. |
| 157 | Domain | Feature patterns | FEATURES = {key: description}. Consistent format across domains. | Enables rbac/catalog.py to aggregate all features. |
| 158 | Domain | Read model patterns | CQRS-lite projections for this domain's dashboards. | Cross-domain dashboards live in governance/read_models/. |
| 159 | Domain | Policy patterns | Authorization policies. Enforced by require_feature() and service checks. | Policies are business rules about access, distinct from auth. |
| 160 | Domain | 15 domains fixed | New domains require architecture review. | Prevents domain sprawl. |
| 161 | RBAC | Catalog single source | Aggregates all features.py via package scan. | CI fails on any require_feature() literal not in catalog. |
| 162 | RBAC | Role definitions | (module, role) → feature sets. Static code, not DB-driven. | Enables code review of permission grants. |
| 163 | RBAC | Resolution | actor × role × country → effective set. Redis-cached. | Fast permission checks on every request. |
| 164 | RBAC | Dependencies | require_feature(...) and require_module(...) FastAPI dependencies. | The gates used by every module router. |
| 165 | RBAC | Service | Grant/revoke, delegation, maker-checker. All changes audited. | Runtime permission management with full audit trail. |
| 166 | RBAC | Permission models | Categories, permissions, assignments, overrides, audit log. | Stored in security Postgres schema. |
| 167 | RBAC | Frontend permissions | permissions.ts GENERATED from GET /rbac/catalog. | UI gating and backend gating share one source. |
| 168 | Frontend | Monorepo | web_app/ (Next.js), mobile_app/ (Expo), shared/ (cross-platform). | Code sharing while keeping platform-specific code separate. |
| 169 | Frontend | Next.js version | 16.3.1+ with App Router. | Specific CSS processing requirements. |
| 170 | Frontend | TypeScript strict | strict: true. any requires justification. | Catches null/undefined errors and missing properties at compile time. |
| 171 | Frontend | State management | Zustand (global), React (local), Query/SWR (server). | Clear separation of state concerns. |
| 172 | Frontend | Data fetching | Server Components fetch directly. Client Components use API client. | Frontend knows backend only through the API. |
| 173 | Frontend | API proxy | Next.js rewrites /api/*, /admin/*, etc. to NEXT_PUBLIC_API_URL. | All API traffic through Next.js server routes. No CORS. |
| 174 | Frontend | Styling | Tailwind CSS + CVA + tailwind-merge + clsx. | Consistent, type-safe styling with design tokens. |
| 175 | Frontend | Forms | React Hook Form + Zod. | Server validation authoritative; client for UX. |
| 176 | Frontend | Error handling | API errors → toasts/boundaries. Unhandled → console (dev) / Sentry (prod). | Users never see raw error objects. |
| 177 | Frontend | Route groups | Organized by actor: (customer), auth/, admin/*, supplier/*, etc. | Each group has its own layout. |
| 178 | Web App | Route structure | page.tsx, layout.tsx, loading.tsx, error.tsx per route. | Next.js App Router convention. |
| 179 | Web App | Component structure | ui/ (design system), admin/, auth/, chat/, comms/, country/, etc. | Organized by area for discoverability. |
| 180 | Web App | Hook patterns | useXxx prefix. No JSX in hooks. | Hooks encapsulate logic; components render UI. |
| 181 | Web App | Lib patterns | api/ (client, auth, country, errors), rbac.ts. | Pure functions and utilities. |
| 182 | Web App | Service patterns | localizationService, crossBorderService, addressFormatService. | Client-side services are NOT backend domain services. |
| 183 | Web App | Theme/styling | Design tokens, Tailwind config, global CSS. | Consistent theme across the app. |
| 184 | Web App | Types | From @zozi/shared + local definitions. | Shared types prevent drift between frontend and backend. |
| 185 | Web App | Utils | Pure utility functions. | Business logic belongs in services or hooks. |
| 186 | Web App | Build | next build passes with no errors. | Build failures block deployment. |
| 187 | Mobile | Expo SDK 51+ | Expo Router with file-based routing. | Native navigation with deep linking. |
| 188 | Mobile | Route groups | (auth), (tabs), admin/, supplier/, logistics/, employee/. | Each group has its own layout and navigation. |
| 189 | Mobile | Components | components/ui/ design system. Shared from @zozi/shared. | Consistent design system across platforms. |
| 190 | Mobile | Lib patterns | api, stores, authPrompt, countryContext, geo, payment, secureStorage. | Same patterns as web where possible. |
| 191 | Mobile | Platform-specific | .native.ts (RN) / .ts (web) suffixes. | Enables sharing logic while customizing per-platform. |
| 192 | Mobile | State | Zustand (same stores as web). | Consistent state management across platforms. |
| 193 | Mobile | Storage | expo-secure-storage for secrets. AsyncStorage for non-sensitive. | Never store secrets in plain AsyncStorage. |
| 194 | Mobile | Build | EAS Build. Expo Go for dev. App stores for production. | Automated build and submission pipeline. |
| 195 | Shared | Structure | api-core, money, i18n, domain helpers, statusColors, requestCache, etc. | Cross-platform TypeScript consumed by both apps. |
| 196 | Shared | No app imports | MUST NOT import from web_app/ or mobile_app/. | Prevents circular dependency. |
| 197 | Shared | Permissions generated | permissions.ts GENERATED from backend /rbac/catalog. | UI and backend gating share one source. |
| 198 | Shared | Cross-platform types | Platform-agnostic. .native.ts for platform adaptations. | Type safety across web and mobile. |
| 199 | Shared | API core | apiFetch base client with auth, errors, retry. | Consistent API client across platforms. |
| 200 | Shared | Money formatting | Intl.NumberFormat with locale support. | Consistent monetary display across platforms. |
| 201 | Config | Env hierarchy | .env.example → .env → backend/.env → frontend/.env.local. | Each environment has its own file. |
| 202 | Config | Required vars | SECRET_KEY, DATABASE_URL, REDIS_URL MUST be set in prod. | Missing vars cause immediate startup failure. |
| 203 | Config | Typed flags | pydantic-settings. No raw os.getenv(). | String 'false' is truthy. Typed coercion prevents bugs. |
| 204 | Config | Secrets manager | AWS Secrets Manager / HashiCorp Vault in production. | .env files are for development only. |
| 205 | Config | APP_ENV detection | development, test, staging, production. | Behavior changes based on environment. |
| 206 | Config | CORS allowlist | Comma-separated list. No wildcard in production. | Prevents arbitrary websites from making authenticated requests. |
| 207 | Testing | pytest framework | pytest + pytest-asyncio. Files in tests/domains/ and tests/architecture/. | Standard Python testing stack. |
| 208 | Testing | Fixtures | db_session, client/admin_client/supplier_client/customer_client, JWT tokens. | Pre-authenticated test clients speed up test writing. |
| 209 | Testing | Demo users | admin@zozi.com, supplier@zozi.com, customer@zozi.com. | Consistent test users across environments. |
| 210 | Testing | Test environment | APP_ENV=test. CSRF/rate disabled. SQLite. | Optimized for speed, not production fidelity. |
| 211 | Testing | Frontend tests | Jest + RTL. E2E: Playwright. | Standard React testing stack. |
| 212 | Testing | Architecture tests | test_import_laws.py (Laws 1,4,W1,W2), test_feature_catalog.py (Law 4). | Ensures laws are actually enforced. |
| 213 | Testing | Coverage | Per-domain smoke tests. Per-law tests. CI-enforced. | Minimum viable test coverage. |
| 214 | Testing | Isolation | Transaction-rolled-back. No leaks. Independent. | Tests don't affect each other. |
| 215 | Deployment | Docker Compose | db, redis, backend, frontend, Celery workers, beat. | Local development mirrors production architecture. |
| 216 | Deployment | Production targets | Backend: Railway. Frontend: Vercel. Mobile: EAS Build. | Each platform has its own deployment pipeline. |
| 217 | Deployment | Migration on deploy | alembic upgrade head automatic before serving traffic. | Schema is always up-to-date before traffic arrives. |
| 218 | Deployment | Health checks | /health, /health/deps, /health/ready return 200. | Load balancers use these for routing. |
| 219 | Deployment | Rollback | MUST support rollback. Migrations backward-compatible. | Zero-downtime rollback on failure. |
| 220 | Deployment | Env promotion | development → staging → production. | Each environment has its own config and database. |
| 221 | Performance | Caching strategy | Redis with TTL. Event-driven invalidation. | Stale cache preferable to cache stampede. |
| 222 | Performance | Keyset pagination | cursor_paginate_asc. OFFSET FORBIDDEN on hot lists. | OFFSET degrades to O(n) on large tables. |
| 223 | Performance | Connection pooling | pool_size ≥ 10, max_overflow ≥ 20. PgBouncer. | Connection exhaustion causes cascading failures. |
| 224 | Performance | Query optimization | Indexes on queried columns. No N+1. No SELECT *. | Slow queries are logged and reviewed. |
| 225 | Performance | CDN | Static assets, images via CDN. Presigned URLs. | Reduces origin bandwidth by 40-60%. |
| 226 | Performance | Async processing | CPU-bound work to Celery. Request handlers never block. | Event loop stays responsive under load. |
| 227 | Data | RLS enforcement | set_rls_context() sets country_code. All queries filtered. | Data isolation at the database level. |
| 228 | Data | Soft delete | is_deleted (boolean, default false). Queries filter by default. | Enables data recovery and audit trails. |
| 229 | Data | Audit columns | created_at/updated_at via TimestampMixin. DB-side defaults. | Required for debugging and compliance. |
| 230 | Data | Audit trail | WORM log. Actor, action, entity, timestamp, before/after. | Forensic integrity for compliance investigations. |
| 231 | Data | Data residency | MAY shard by country_code. | Enables compliance with country-specific data laws. |
| 232 | Data | Backup & recovery | Daily backups. Tested for recovery. PITR. 30-day retention. | Disaster recovery capability. |
| 233 | API | REST conventions | GET (list/detail), POST (create), PUT (update), DELETE. | Standard REST mapping. |
| 234 | API | Versioning | URL prefix /api/v1/. Breaking = new version. Old deprecated. | Enables API evolution without breaking clients. |
| 235 | API | JSON format | Request/response JSON. Pydantic validation. Serializer output. | Consistent, validated, serialized. |
| 236 | API | RFC 7807 errors | Problem Details. No stack traces in production. | Standard error format enables client-side handling. |
| 237 | API | Pagination format | items + next_cursor + has_more. No count on hot lists. | Count is expensive on large tables. |
| 238 | API | Filtering/sorting | filter[field]=value, sort=-created_at. Complex: POST body. | Flexible querying without endpoint proliferation. |
| 239 | API | Idempotency | Idempotency-Key header. 24h expiry. | Duplicate requests don't cause duplicate operations. |
| 240 | Git | Branching | main, feature/*, fix/*, release/*, hotfix/*. | Git Flow convention. |
| 241 | Git | Conventional Commits | type(scope): description. feat, fix, refactor, docs, test, chore, perf, security. | Automated changelog generation. |
| 242 | Git | PR process | All via PR. CI + review. No direct main pushes. | Code review catches issues before merge. |
| 243 | Git | Hooks | Pre-commit: ruff. Pre-push: architecture tests. | Automated quality gates. |
| 244 | Git | Worktrees | Agent Manager uses worktrees. Cleaned up after merge. | Parallel work without branch switching. |
| 245 | Docs | Architecture docs | ARCHITECTURE_DIAGRAM.md is authoritative. Lock-step with code. | Single source of truth for architecture. |
| 246 | Docs | Agent docs | AGENTS.md quick reference. Not the full architecture. | Agent onboarding without overwhelming detail. |
| 247 | Docs | API docs | FastAPI auto-generates at /docs and /redoc. | Always up-to-date with code. |
| 248 | Docs | Runbooks | docs/runbooks/. Deployment, rollback, incident response. | Tested in staging quarterly. |
| 249 | Docs | Code comments | Docstrings + WHY comments. Outdated removed. | Comments explain why, not what. |
| 250 | Docs | Changelog | CHANGELOG.md. Per-release: features, breaking changes, fixes. | User-facing, plain language. |
| 251 | Scalability | Horizontal scaling | N stateless replicas. Sessions in Redis. | Add replicas to handle more traffic. |
| 252 | Scalability | Auto-scaling | CPU > 70% scale up. Min 2, max 20. | Handles traffic spikes without manual intervention. |
| 253 | Scalability | Partitioning | Range partition by created_at (monthly). | Query time constant as data grows. |
| 254 | Scalability | CQRS | Commands write. Events update read models. | Prevents write contention from slowing reads. |
| 255 | Scalability | Write-behind cache | Buffer in Redis, flush async. | 10-100x reduction in DB write pressure. |
| 256 | Scalability | Tenant quotas | Per-country limits. 429 on exceed. | Prevents one tenant from monopolizing resources. |
| 257 | Scalability | Full-text search | Elasticsearch/OpenSearch for catalog. | Sub-100ms search across millions of products. |
| 258 | Scalability | Image pipeline | Async resize, WebP, metadata strip. | 60-80% bandwidth reduction. |
| 259 | Scalability | API caching | ETag, Last-Modified, Cache-Control. CDN. | 40-60% origin load reduction. |
| 260 | Scalability | PgBouncer | Transaction pooling. max_client_conn=10000. | Multiplexes thousands of client connections. |
| 261 | Scalability | Read replicas | Auto-route reads. Fallback if lag > 1s. | Offloads primary. Automatic failover. |
| 262 | Scalability | Archiving | Old data to S3 Glacier. | Keeps operational tables small and fast. |
| 263 | Scalability | Write buffering | Celery queue for bursty writes. | Prevents DB overload during spikes. |
| 264 | Scalability | Static assets | Minify, compress, hash, CDN. | Reduces bandwidth and improves cache hit rate. |
| 265 | Scalability | DB monitoring | Alerts on connections, lag, deadlocks, slow queries. | Early warning of capacity issues. |
| 266 | Scalability | Synthetic monitoring | Every 60s from multiple regions. | Detects issues before users report them. |
| 267 | Scalability | Endpoint limits | Max body (10MB), query (100 items), time (30s). | Prevents resource exhaustion. |
| 268 | Scalability | Load shedding | Shed non-critical first. | Critical paths always served under load. |
| 269 | Scalability | Cost optimization | Right-size, spot instances, coalescing. | Efficient resource usage at scale. |
| 270 | Scalability | Chaos engineering | Regular failure experiments. | Validates resilience assumptions. |
| 271 | Security | AI-agent security | Prompt injection prevention. | AI endpoints are new attack surface. |
| 272 | Security | Data exfiltration | Per-user export limits. | Prevents AI agents from bulk-extracting data. |
| 273 | Security | Model poisoning | ML input validation before training. | Prevents adversarial training data. |
| 274 | Security | Adversarial detection | Signature + anomaly detection. | Catches known and novel attack patterns. |
| 275 | Security | Encryption at rest | AES-256. KMS. TDE. | Protects data if storage is compromised. |
| 276 | Security | Encryption in transit | TLS 1.3. Certificate pinning. | Protects data from interception. |
| 277 | Security | Key rotation | Every 90 days. Zero-downtime. | Limits exposure window of compromised keys. |
| 278 | Security | WORM audit | Write Once Read Many. Tamper-proof. | Forensic integrity for compliance. |
| 279 | Security | Session binding | Device fingerprint. Concurrent limits. | Prevents session hijacking and abuse. |
| 280 | Security | Brute force DB level | 5 fails = lock. 10 = admin. | Database-level enforcement beyond app. |
| 281 | Security | Bot detection | Score + block/CAPTCHA. | Prevents automated abuse. |
| 282 | Security | PII masking | In logs, errors, non-admin responses. | Prevents PII leakage to unauthorized viewers. |
| 283 | Security | MFA | TOTP for admin/employee. | Second factor prevents credential abuse. |
| 284 | Security | Zero-trust | mTLS service-to-service. | No implicit trust based on network location. |
| 285 | Security | CSP | Strict + nonces. | Prevents XSS via injected scripts. |
| 286 | Security | SRI | Integrity hashes. | Prevents CDN compromise from injecting code. |
| 287 | Security | All headers | Permissions-Policy, COOP, CORP. | Defense in depth against browser attacks. |
| 288 | Security | Disclosure process | SECURITY.md. 24h SLA for critical. | Enables responsible vulnerability reporting. |
| 289 | Security | Pen testing | Annual third-party. OWASP + logic. | Independent security validation. |
| 290 | Security | Dep pinning | Exact + hashes. | Prevents supply chain attacks via dep substitution. |
| 291 | Security | SBOM | For every release. | Know what's in the software. |
| 292 | Security | License compliance | CI-enforced. | Prevents legal issues from incompatible licenses. |
| 293 | Security | Incident automation | Auto-isolate, revoke, capture. | Fast response limits blast radius. |
| 294 | Security | Training | Annual. OWASP + social engineering. | Developers are the first line of defense. |
| 295 | Security | Supply chain | Image scanning + signing. | Prevents compromised containers. |
| 296 | Resilience | Circuit breaker | All external calls wrapped. | Prevents cascade failures. |
| 297 | Resilience | Retry + backoff | 1-2-4-8s. Jitter. Max 5. | Handles transient failures without thundering herd. |
| 298 | Resilience | Dead letter queue | Failed events to DLQ. Replayable. | No event silently dropped. |
| 299 | Resilience | Feature health | Per-feature in /health/deps. | Granular health visibility. |
| 300 | Resilience | Per-feature fallback | Each feature defines degradation. | Users always see a usable UI. |
| 301 | Resilience | Error budget | Exhaustion = freeze. | Balances velocity and reliability. |
| 302 | Resilience | On-call | PagerDuty/Opsgenie. 5min SLA. | Fast human response to critical issues. |
| 303 | Resilience | Runbooks | Per-alert. Tested quarterly. | Reduces MTTR for known issues. |
| 304 | Resilience | DR | RPO=5min, RTO=1hr. Multi-region. | Survives regional failures. |
| 305 | Resilience | DB failover | 30s promotion. | Minimal data loss on primary failure. |
| 306 | Resilience | Multi-region | ≥2 regions. Cross-region replication. | Survives regional failures. |
| 307 | Resilience | Backup verify | Daily restore test. | A backup that can't be restored is worthless. |
| 308 | Resilience | Drift detection | IaC daily checks. | Prevents configuration surprises. |
| 309 | Resilience | Dep monitoring | External status pages. Auto-fallback. | Fast response to external degradation. |
| 310 | Resilience | Post-incident reviews | Blameless. Action items tracked. | Prevents repeat incidents. |
| 311 | Operations | Feature flags | Gradual rollout. Instant rollback. | Decouples deployment from release. |
| 312 | Operations | A/B testing | Hash-based. Sticky. | Data-driven feature decisions. |
| 313 | Operations | Compliance | GDPR. PCI-DSS via Stripe Elements. | Automated compliance reduces legal risk. |
| 314 | Operations | IaC | Terraform/Pulumi. Manual FORBIDDEN. | Reproducible, auditable infrastructure. |
| 315 | Operations | Log aggregation | ELK/Loki. 30d hot, 1y cold. | Centralized visibility. |
| 316 | Operations | Dashboards | Grafana. p50/p95/p99. | Real-time system health visibility. |
| 317 | Operations | Alerting tiers | P1/P2/P3. | Right urgency for right issues. |
| 318 | Operations | Capacity planning | Monthly. 3-month projection. | Prevents surprises. |
| 319 | Operations | Release mgmt | Canary → full. Rollback < 5min. | Safe, fast deployments. |
| 320 | Operations | DevX | < 10min setup. Hot reload. | Fast onboarding and iteration. |
| 321 | Operations | Doc freshness | Quarterly reviews. | Outdated docs are worse than no docs. |
| 322 | Operations | Cost allocation | By domain/team via tagging. | Visibility into cost drivers. |
| 323 | Operations | Human access | Least-privilege. 24h offboarding. | Limits blast radius of compromised accounts. |
| 324 | Operations | Change mgmt | All via PR + CI. | Auditable, reviewable changes. |
| 325 | Operations | Sustainability | Right-size. Carbon tracking. | Environmental responsibility. |

---
## Law Quick-Reference Index

| Range | Category | Rows |
|-------|----------|------|
| 1-7 | Architecture | 1-7 |
| 8-13 | Structure | 8-13 |
| 14-18 | File Placement | 14-18 |
| 19-24 | Code Quality | 19-24 |
| 25-29 | Migration | 25-29 |
| 30-31 | Provider | 30-31 |
| 32-44 | Security | 32-44 |
| 45-57 | Database | 45-57 |
| 58-68 | Code Quality | 58-68 |
| 69-74 | Testing | 69-74 |
| 75-81 | Infrastructure | 75-81 |
| 82-86 | Config | 82-86 |
| 87-91 | Router | 87-91 |
| 92-96 | Observability | 92-96 |
| 97-106 | Wiring | 97-106 |
| 107-122 | Technology | 107-122 |
| 123-131 | Provider Laws | 123-131 |
| 132-139 | Module Laws | 132-139 |
| 140-149 | Infrastructure Laws | 140-149 |
| 150-160 | Domain Laws | 150-160 |
| 161-167 | RBAC | 161-167 |
| 168-177 | Frontend | 168-177 |
| 178-186 | Web App | 178-186 |
| 187-194 | Mobile | 187-194 |
| 195-200 | Shared | 195-200 |
| 201-206 | Config | 201-206 |
| 207-214 | Testing | 207-214 |
| 215-220 | Deployment | 215-220 |
| 221-226 | Performance | 221-226 |
| 227-232 | Data | 227-232 |
| 233-239 | API | 233-239 |
| 240-244 | Git | 240-244 |
| 245-250 | Documentation | 245-250 |
| 251-270 | Scalability | 251-270 |
| 271-295 | Security Hardening | 271-295 |
| 296-310 | Resilience | 296-310 |
| 311-325 | Operations | 311-325 |

---

*End of ARCHITECTURE_DIAGRAM.md — 325 laws, each defined once in section*
