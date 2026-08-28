#!/usr/bin/env python3
"""Generate a comprehensive law matrix as an HTML file."""

laws = []

# Helper to add a law
def add(law_id, category, rule, desc, why):
    laws.append({
        "id": law_id,
        "category": category,
        "rule": rule,
        "desc": desc,
        "why": why
    })

# ═══════════════════════════════════════════════════════════════
# Architecture Laws (1-7)
# ═══════════════════════════════════════════════════════════════
add(1, "Architecture", "Arrows point down",
    "Dependencies flow: modules → domains → infrastructure → kernel. Reverse imports FORBIDDEN.",
    "Prevents circular dependencies and unmaintainable coupling between layers.")

add(2, "Architecture", "Thin routers",
    "Router = auth context + require_feature + ONE service call + serialization. No DB writes, no business logic.",
    "Keeps API layer a thin HTTP shim over domain logic. Easy to test and maintain.")

add(3, "Architecture", "Cross-domain events/ports",
    "Cross-domain WRITES via events.py/subscribers.py. Cross-domain READS via ports.py only.",
    "Keeps domains decoupled and independently deployable.")

add(4, "Architecture", "Features single-sourced",
    "Permission atoms defined once in domains/*/features.py. Aggregated by rbac/catalog.py.",
    "Prevents permission drift. Frontend and backend share one permission model.")

add(5, "Architecture", "Country is orthogonal",
    "Every data access scoped by country_code via RLS. Independent of feature check.",
    "Ensures multi-tenant data isolation at the database level.")

add(6, "Architecture", "Schema discipline",
    "Every table in a domain Postgres schema. Alembic is the only schema source.",
    "Naming consistency and single source of truth for schema changes.")

add(7, "Architecture", "Allowlist only shrinks",
    "DOMAIN_ALLOWLIST.yaml tracks temporary cross-domain imports. May only shrink.",
    "Ensures migration toward clean domain boundaries makes forward progress.")

# ═══════════════════════════════════════════════════════════════
# Structural Decisions (8-13)
# ═══════════════════════════════════════════════════════════════
add(8, "Structure", "Router structure",
    "modules/{m}/routers/{d}.py — one file per domain per module (15 per module).",
    "Makes endpoints discoverable by actor+domain combination.")

add(9, "Structure", "Media in providers",
    "domains/media must not exist. All media code in providers/media, providers/image.",
    "Media is an external concern, not a business domain.")

add(10, "Structure", "Kernel is pure",
    "kernel/ contains ONLY pure business primitives. No imports from domains/modules/rbac.",
    "Ensures business primitives are consistent and reusable across all domains.")

add(11, "Structure", "Providers wrap SDKs",
    "A provider wraps exactly one external SDK. No business logic, no domain imports.",
    "External dependencies are isolated and swappable.")

add(12, "Structure", "16 domains",
    "Fixed set: accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers.",
    "Prevents domain sprawl and ensures clear ownership boundaries.")

add(13, "Structure", "5 modules",
    "Fixed set: admin, customer, employee, logistics, supplier.",
    "Ensures the actor model stays coherent and manageable.")

# ═══════════════════════════════════════════════════════════════
# File Placement (14-18)
# ═══════════════════════════════════════════════════════════════
add(14, "File Placement", "Business logic → domains/",
    "All business logic in domain services/services/. No logic in routers or modules.",
    "Business logic is colocated with the data it operates on (DDD).")

add(15, "File Placement", "API endpoints → modules/routers/",
    "Every HTTP endpoint in a module router file named after the domain.",
    "Endpoints grouped by business capability, not CRUD operation.")

add(16, "File Placement", "SDK wrappers → providers/",
    "Every third-party integration under providers/{category}/.",
    "Trivial to find every external dependency and swap implementations.")

add(17, "File Placement", "Cross-domain → events/ports only",
    "events.py (writes) and ports.py (reads) are the ONLY sanctioned cross-domain channels.",
    "Creates a clear, auditable boundary contract between domains.")

add(18, "File Placement", "Root forbidden folders",
    "utils/, routers/, controllers/, services/, models/, db/ FORBIDDEN at backend/ root.",
    "Prevents the 'god directory' anti-pattern.")

# ═══════════════════════════════════════════════════════════════
# Code Quality (19-24)
# ═══════════════════════════════════════════════════════════════
add(19, "Code Quality", "No float for money",
    "Monetary values MUST use Decimal or Numeric. Float FORBIDDEN for money.",
    "Floating-point arithmetic introduces rounding errors causing financial discrepancies.")

add(20, "Code Quality", "country_code = String(2)",
    "Always String(2) following ISO 3166-1 alpha-2.",
    "Consistency across all 16 domains simplifies joins, indexes, and RLS filtering.")

add(21, "Code Quality", "Timestamps = server_default",
    "created_at/updated_at use server_default=func.now() (DB-side), not Python-side.",
    "Timestamps survive clock skew and are consistent in the database.")

add(22, "Code Quality", "FK have ondelete",
    "Every ForeignKey MUST declare explicit ondelete behavior.",
    "Prevents unpredictable behavior across PostgreSQL versions.")

add(23, "Code Quality", "Audit columns",
    "Every model MUST include created_at, updated_at, country_code, is_deleted.",
    "Required for RLS, debugging, compliance, and data recovery.")

add(24, "Code Quality", "No forbidden schemas",
    "core, platform, identity are FORBIDDEN as Postgres schema names.",
    "Prevents monolithic shared-schema architecture.")

# ═══════════════════════════════════════════════════════════════
# Migration (25-29)
# ═══════════════════════════════════════════════════════════════
add(25, "Migration", "Shift files first",
    "All files to correct domains before reorganization. Never replace working code with stubs.",
    "Ensures agents have complete file context for each domain.")

add(26, "Migration", "Backward-compat shims",
    "Temporary re-exports in infrastructure/utils/ for relocated files.",
    "Enables gradual migration without breaking existing imports.")

add(27, "Migration", "Delete temp scripts",
    "Root-level fix_*.py, debug_*.py should be removed after use.",
    "Keeps root clean and architecture clear.")

add(28, "Migration", "_auto_stubs ≠ architecture",
    "_auto_stubs.py are migration scaffolding, not architecture components.",
    "Distinguishes temporary scaffolding from permanent architecture.")

add(29, "Migration", "registry.py ≠ architecture",
    "Service Registry and auto_wire.py were removed from architecture.",
    "Prevents confusion about what is permanent architecture.")

# ═══════════════════════════════════════════════════════════════
# Provider Rules (30-31)
# ═══════════════════════════════════════════════════════════════
add(30, "Provider", "Graceful degradation",
    "Domains handle missing SDKs via HAS_<SDK> flags. Never crash.",
    "System runs in development without all production dependencies.")

add(31, "Provider", "No domain imports",
    "Providers MUST NOT import from domains, modules, rbac, jobs, middleware.",
    "Data flows through parameters only. Ensures providers remain pure wrappers.")

# ═══════════════════════════════════════════════════════════════
# Security (32-44)
# ═══════════════════════════════════════════════════════════════
add(32, "Security", "No hardcoded secrets",
    "JWT keys, API keys, passwords from env vars or secrets manager only.",
    "Attackers can clone repo. Committed secrets = token forgery.")

add(33, "Security", "Token type verification",
    "All JWT decoders MUST verify the type claim (access vs refresh).",
    "Prevents refresh tokens from being used as access tokens.")

add(34, "Security", "Parameterized SQL",
    "Use SQLAlchemy text() with bound parameters or ORM. No f-string interpolation.",
    "Prevents SQL injection attacks.")

add(35, "Security", "CSRF active",
    "CSRF middleware MUST be active in all environments.",
    "Prevents CSRF attacks in misconfigured deployments.")

add(36, "Security", "Security headers",
    "CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy in production.",
    "Prevents XSS, clickjacking, and other browser-based attacks.")

add(37, "Security", "Rate limit fails closed",
    "Redis unreachable = deny requests (not allow all).",
    "Prevents brute-force and DoS when Redis is down.")

add(38, "Security", "Password handling",
    "Passwords >72 bytes rejected with error, never truncated.",
    "bcrypt's 72-byte limit. Silent truncation creates security holes.")

add(39, "Security", "No duplicate auth",
    "Auth logic in exactly one canonical location.",
    "Duplicate implementations with divergent behavior create security holes.")

add(40, "Security", "CORS origin validation",
    "Origin header validated against allowlist before reflection.",
    "Prevents arbitrary websites from making authenticated requests.")

add(41, "Security", "WebSocket auth",
    "WebSocket connections MUST verify JWT type claim equals access.",
    "Prevents stolen refresh tokens from opening WebSocket connections.")

add(42, "Security", "Input validation",
    "All public endpoints use Pydantic schemas. No raw dicts in router signatures.",
    "Prevents malformed data from reaching domain services.")

add(43, "Security", "Security event logging",
    "Auth failures, 403s, rate-limit triggers logged at WARNING+.",
    "Silent security events prevent incident detection.")

add(44, "Security", "Dependency scanning",
    "All deps scanned for CVEs in CI. High/critical block deployment.",
    "Prevents supply-chain attacks via compromised dependencies.")

# ═══════════════════════════════════════════════════════════════
# Database (45-57)
# ═══════════════════════════════════════════════════════════════
add(45, "Database", "No N+1 queries",
    "All relationships declare lazy=selectin or joined. Default lazy=select FORBIDDEN.",
    "N+1 queries bring the database to its knees at 100K+ users.")

add(46, "Database", "No SELECT *",
    "Application queries MUST select explicit columns.",
    "Wastes memory/I/O. Prevents covering indexes. Breaks on column reorder.")

add(47, "Database", "Connection pool sizing",
    "pool_size ≥ 10, max_overflow ≥ 20. Environment-configurable.",
    "Connection exhaustion causes cascading failures under load.")

add(48, "Database", "Read replica separation",
    "Replica connections use independent pool settings. Read-heavy uses get_read_db().",
    "Without replicas, every read competes with writes for connections.")

add(49, "Database", "Linear migration history",
    "Alembic history MUST remain linear. Resolve divergent heads immediately.",
    "Divergent heads break alembic upgrade head and cause deployment failures.")

add(50, "Database", "Explicit transactions",
    "All writes use explicit transaction management. Autocommit FORBIDDEN.",
    "Ensures multi-step operations can roll back on failure.")

add(51, "Database", "Single table ownership",
    "Each table defined in exactly one domain. Duplicate __tablename__ FORBIDDEN.",
    "Duplicate tables cause MetaData conflicts and runtime crashes.")

add(52, "Database", "FK constraints",
    "All FK columns have explicit ForeignKey with ondelete.",
    "Prevents orphan rows and ensures referential integrity.")

add(53, "Database", "Index FK columns",
    "All FK columns have explicit index. PostgreSQL does NOT auto-index FKs.",
    "Without indexes, JOINs degrade to sequential scans.")

add(54, "Database", "Soft delete",
    "All user-facing tables use is_deleted (boolean, default false).",
    "Enables data recovery, audit trails, and safe cascading.")

add(55, "Database", "Schema-per-domain",
    "Every model declares __table_args__ = {schema: <domain>}.",
    "Tables without schema land in public, breaking multi-tenant isolation.")

add(56, "Database", "No forbidden schemas",
    "core, platform, identity FORBIDDEN as schema names.",
    "Prevents accidental coupling through shared schema namespace.")

add(57, "Database", "Migration safety",
    "Destructive migrations include backward-compatible strategy (expand-contract).",
    "Enables zero-downtime rollback.")

# ═══════════════════════════════════════════════════════════════
# Code Quality (58-68)
# ═══════════════════════════════════════════════════════════════
add(58, "Code Quality", "No print() in production",
    "print() FORBIDDEN in production code. Use structlog logger.",
    "print() bypasses log formatting and cannot be filtered by level.")

add(59, "Code Quality", "No silent exceptions",
    "All except blocks MUST log at minimum DEBUG level.",
    "Silent exception swallowing makes debugging impossible.")

add(60, "Code Quality", "No blocking in async",
    "Async functions MUST NOT call blocking I/O. Use asyncio.sleep, httpx.",
    "Blocking calls freeze the event loop, preventing other requests.")

add(61, "Code Quality", "Bounded caches",
    "All in-memory caches have max size and/or TTL. Unbounded dict FORBIDDEN.",
    "Unbounded caches cause OOM at scale.")

add(62, "Code Quality", "TODO/FIXME hygiene",
    "TODO/FIXME must include ticket reference and expiration date.",
    "Ensures technical debt is tracked and doesn't accumulate invisibly.")

add(63, "Code Quality", "Type hints required",
    "All public function signatures MUST have type hints.",
    "Enables static analysis, IDE autocompletion, inline documentation.")

add(64, "Code Quality", "Function length ≤50",
    "Functions SHOULD NOT exceed 50 lines (excl. docstrings/blanks).",
    "Long functions are hard to test, debug, and reason about.")

add(65, "Code Quality", "Indentation ≤4 levels",
    "Maximum 4 levels of indentation per function.",
    "Deeper nesting signals complex control flow needing refactoring.")

add(66, "Code Quality", "No magic numbers",
    "Numeric constants MUST be named constants or config values.",
    "Named constants make business rules self-documenting and easy to change.")

add(67, "Code Quality", "DRY principle",
    "Duplicate code blocks (>5 lines) MUST be extracted into shared functions.",
    "Copy-paste creates maintenance nightmares.")

add(68, "Code Quality", "Consistent errors",
    "All service functions use consistent error pattern (exceptions or Result).",
    "Mixed patterns make error handling unpredictable for callers.")

# ═══════════════════════════════════════════════════════════════
# Testing (69-74)
# ═══════════════════════════════════════════════════════════════
add(69, "Testing", "Domain smoke tests",
    "Every domain MUST have at least one smoke test.",
    "Catches circular imports, missing deps, broken __init__.py, syntax errors.")

add(70, "Testing", "Architecture law tests",
    "Every statically checkable law MUST have a corresponding test.",
    "Ensures laws are actually enforced, not just documented.")

add(71, "Testing", "No broken tests in CI",
    "Collection-time failures MUST block CI. Fix within 24h.",
    "Broken tests hide real failures.")

add(72, "Testing", "Cross-domain integration",
    "Cross-domain flows MUST have integration tests.",
    "Unit tests verify single services; integration tests verify wiring.")

add(73, "Testing", "Performance regression",
    "Critical paths MUST have perf regression tests. Fail on >20% latency.",
    "Prevents slow queries or missing indexes from shipping to production.")

add(74, "Testing", "Test isolation",
    "All tests use transaction-rolled-back sessions. No data leaks.",
    "Each test is independent and order-independent.")

# ═══════════════════════════════════════════════════════════════
# Infrastructure (75-81)
# ═══════════════════════════════════════════════════════════════
add(75, "Infrastructure", "Graceful degradation",
    "External failures MUST degrade gracefully AND log WARNING.",
    "Silent fallbacks hide degradation from ops.")

add(76, "Infrastructure", "Session lifecycle",
    "Sessions managed via FastAPI dependency injection only.",
    "Ensures sessions are properly closed even on exceptions.")

add(77, "Infrastructure", "Async resource safety",
    "Async resources use asyncio.Lock for init and disposal.",
    "Prevents race conditions that create multiple engines.")

add(78, "Infrastructure", "Middleware ordering",
    "Pipeline order FIXED: Foundation → Auth → Rate → Webhook → Geo → Security → Observe → Compliance.",
    "Reordering changes security posture.")

add(79, "Infrastructure", "Global exception handler",
    "Catches all uncaught exceptions. Returns structured response. No stack traces in prod.",
    "Prevents stack trace leakage and ensures consistent error format.")

add(80, "Infrastructure", "Graceful shutdown",
    "Shutdown disposes DB engine, Redis, workers via lifespan.py.",
    "Prevents connection leaks on restart.")

add(81, "Infrastructure", "Health checks",
    "/health, /health/deps, /health/ready verify all critical dependencies.",
    "Load balancers use these for routing decisions.")

# ═══════════════════════════════════════════════════════════════
# Config (82-86)
# ═══════════════════════════════════════════════════════════════
add(82, "Config", "No default credentials",
    "Config fallbacks MUST NOT contain real credentials. Empty/null default.",
    "Prevents accidental use of dev credentials in production.")

add(83, "Config", "Environment validation",
    "Required env vars validated at startup. Missing = immediate failure.",
    "Prevents silent fallbacks to development defaults in production.")

add(84, "Config", "Typed feature flags",
    "Flags use pydantic-settings. Raw os.getenv() FORBIDDEN.",
    "String 'false' is truthy in Python. Typed coercion prevents bugs.")

add(85, "Config", "Secret rotation",
    "Secrets rotatable without deployment via env var updates.",
    "Enables response to credential leaks without full redeployment.")

add(86, "Config", "Env-specific configs",
    "Prod, staging, dev have separate config profiles. No inheritance.",
    "Prevents prod from inheriting dev defaults like debug=True.")

# ═══════════════════════════════════════════════════════════════
# Router (87-91)
# ═══════════════════════════════════════════════════════════════
add(87, "Router", "Auth on protected endpoints",
    "All non-public endpoints MUST use get_current_user or equivalent.",
    "Prevents accidental exposure of sensitive endpoints.")

add(88, "Router", "Feature gate on protected",
    "All non-public endpoints MUST use require_feature() or require_module().",
    "Ensures every protected endpoint has explicit authorization.")

add(89, "Router", "Response serialization",
    "Routers return serialized responses (Pydantic/dicts), never raw ORM models.",
    "Prevents accidental exposure of internal model fields.")

add(90, "Router", "No business logic",
    "Routers contain ONLY: auth, gate, parsing, ONE service call, serialization.",
    "Keeps API layer a thin HTTP shim.")

add(91, "Router", "Documentation",
    "All endpoints MUST have OpenAPI-compatible docstrings.",
    "The OpenAPI spec is the API contract.")

# ═══════════════════════════════════════════════════════════════
# Observability (92-96)
# ═══════════════════════════════════════════════════════════════
add(92, "Observability", "Structured logging",
    "All logs use structlog with context (user_id, request_id, domain, action).",
    "Enables log aggregation, filtering by field, cross-service correlation.")

add(93, "Observability", "Request tracing",
    "All requests carry request_id propagated through service calls.",
    "Enables end-to-end request tracing for debugging.")

add(94, "Observability", "Metrics emission",
    "Critical paths emit Prometheus metrics (latency, error rate, throughput).",
    "Unmonitored critical paths hide degradation.")

add(95, "Observability", "Error tracking",
    "Unhandled exceptions reported to Sentry with fallback to logger.",
    "Prevents silent exception swallowing in production.")

add(96, "Observability", "Audit trail",
    "State-changing operations write to domains/audit/.",
    "WORM audit log enables compliance investigations.")

# ═══════════════════════════════════════════════════════════════
# Wiring (97-106)
# ═══════════════════════════════════════════════════════════════
add(97, "Wiring", "Import direction",
    "Imports MUST follow modules → domains → infrastructure → kernel.",
    "Prevents reverse dependencies.")

add(98, "Wiring", "No circular imports",
    "Circular chains between any two packages FORBIDDEN.",
    "Circular imports cause ImportError at module load time.")

add(99, "Wiring", "No layer crossing",
    "Modules don't import infrastructure directly. Domains don't import modules.",
    "Prevents tight coupling across layers.")

add(100, "Wiring", "Provider isolation",
    "Providers don't import from domains/modules/rbac/jobs/middleware.",
    "Ensures providers remain pure wrappers.")

add(101, "Wiring", "Kernel isolation",
    "kernel/ doesn't import from domains/modules/rbac/providers/jobs/middleware.",
    "Kernel is the universal foundation layer.")

add(102, "Wiring", "Infrastructure isolation",
    "infrastructure/ doesn't import from domains/modules/rbac/providers.",
    "Provides platform primitives to all layers.")

add(103, "Wiring", "Job wiring",
    "Jobs import from domains/ + infrastructure/ only.",
    "Jobs are decoupled from HTTP layer.")

add(104, "Wiring", "Middleware wiring",
    "Middleware imports from infrastructure/ + rbac/ only.",
    "Middleware operates at HTTP layer, needs only platform primitives.")

add(105, "Wiring", "Shared package wiring",
    "@zozi/shared doesn't import from web_app or mobile_app.",
    "Shared is consumed BY apps, never imports FROM them.")

add(106, "Wiring", "Frontend-backend wiring",
    "Frontend communicates via API proxy only. No direct backend imports.",
    "Ensures frontend and backend are decoupled deployables.")

# ═══════════════════════════════════════════════════════════════
# Technology (107-122)
# ═══════════════════════════════════════════════════════════════
add(107, "Technology", "PostgreSQL in prod",
    "Production uses PostgreSQL 15. SQLite for dev/test only.",
    "PostgreSQL provides RLS, proper concurrency, JSONB, full-text search.")

add(108, "Technology", "SQLite in dev",
    "SQLite for zero-config startup. File in .gitignore.",
    "Enables fast local development without DB server.")

add(109, "Technology", "Redis usage",
    "Sessions, catalog cache, rate limiting, blacklist, pub/sub, Celery.",
    "Redis is an ephemeral cache, not a primary data store.")

add(110, "Technology", "Redis failure handling",
    "Sessions→DB fallback, caching pass-through, rate limit fails closed.",
    "System degrades gracefully when Redis is unreachable.")

add(111, "Technology", "Next.js App Router",
    "Web uses Next.js App Router, not Pages Router.",
    "Different routing and rendering models.")

add(112, "Technology", "React Server Components",
    "Data-fetching = Server Components. Client = interactivity/hooks.",
    "RSC reduces JS bundle and enables server-side data access.")

add(113, "Technology", "Expo Router",
    "Mobile uses Expo Router with file-based routing.",
    "Native navigation with deep linking.")

add(114, "Technology", "WebSocket for realtime",
    "WebSocket only for real-time (notifications, chat, tracking).",
    "All other communication uses REST.")

add(115, "Technology", "Celery for jobs",
    "CPU-bound and async jobs use Celery with Redis broker.",
    "Request handlers never block on CPU-bound work.")

add(116, "Technology", "Email via SMTP",
    "Transactional email via providers/comms/email.py. Async sending.",
    "Prevents SMTP latency from blocking request handlers.")

add(117, "Technology", "SMS via Twilio",
    "SMS and WhatsApp via Twilio. Async sending.",
    "Prevents SMS latency from blocking request handlers.")

add(118, "Technology", "Payment gateways",
    "Stripe, Tap, PayPal, PayTabs, Thawani. Each implements BasePaymentGateway.",
    "Multi-PSP enables per-country payment methods.")

add(119, "Technology", "AI/ML backends",
    "Ollama, OpenAI, HuggingFace via providers/ai/. CPU via async_workers.",
    "Isolates AI dependencies and prevents event loop blocking.")

add(120, "Technology", "S3 storage",
    "S3 (prod) or local (dev). Media blobs never in PostgreSQL.",
    "Presigned URLs for direct upload/download. DB stays small.")

add(121, "Technology", "Image processing",
    "Pillow, rembg, OpenCV. Heavy processing via async_workers.",
    "Prevents image processing from blocking the event loop.")

add(122, "Technology", "Leaflet maps",
    "Leaflet + react-leaflet. Geocoding via providers/geography/.",
    "Map tiles from CDN, not bundled.")

# ═══════════════════════════════════════════════════════════════
# Provider Laws (123-131)
# ═══════════════════════════════════════════════════════════════
add(123, "Provider", "Single SDK per provider",
    "Each provider wraps exactly one external SDK or service.",
    "Makes providers independently testable and swappable.")

add(124, "Provider", "HAS_ flags",
    "Every provider exposes HAS_<SDK> boolean flags.",
    "Enables graceful degradation when SDK is absent.")

add(125, "Provider", "Degrade gracefully",
    "When HAS_<SDK> = False, return defaults. Never crash.",
    "System runs without all production dependencies.")

add(126, "Provider", "No business logic",
    "Providers contain ONLY SDK wrapping: auth, formatting, parsing, error mapping.",
    "Business rules belong in domain services, not providers.")

add(127, "Provider", "Config in providers/",
    "API keys, endpoints, timeouts in providers/config.py.",
    "Enables per-environment config without code changes.")

add(128, "Provider", "Async workers for CPU",
    "CPU-bound provider work via providers/async_workers.",
    "Prevents blocking the event loop.")

add(129, "Provider", "Health checks",
    "All providers expose health_check() via BaseProvider.",
    "Enables /health/deps to verify external dependency health.")

add(130, "Provider", "Error mapping",
    "SDK errors mapped to domain exceptions. Raw SDK errors don't leak.",
    "Decouples API from specific SDK error types.")

add(131, "Provider", "Mock in tests",
    "Provider tests mock the external SDK. No real API calls.",
    "Tests are fast, reliable, and don't depend on external services.")

# ═══════════════════════════════════════════════════════════════
# Module Laws (132-139)
# ═══════════════════════════════════════════════════════════════
add(132, "Module", "Module structure",
    "modules/{name}/ with auth/, routers/, serializers/.",
    "Each module is a complete actor context.")

add(133, "Module", "Per-module auth",
    "Each module has its own auth dependency in auth/dependencies.py.",
    "Different actors may need different auth strategies.")

add(134, "Module", "Router file naming",
    "modules/{module}/routers/{domain}.py — one file per domain.",
    "Makes endpoints discoverable by actor+domain.")

add(135, "Module", "Router registration",
    "All router files listed in routers/__init__.py.",
    "Unregistered routers are invisible to FastAPI (dead code).")

add(136, "Module", "Public vs protected",
    "public_routers (no auth) vs routers (auth required).",
    "Enables unauthenticated access to specific endpoints.")

add(137, "Module", "Serializers location",
    "Response serializers in modules/{module}/serializers/.",
    "Different actors may serialize the same model differently.")

add(138, "Module", "5 modules fixed",
    "admin, customer, employee, logistics, supplier. New requires review.",
    "Prevents module sprawl.")

add(139, "Module", "Route prefixes",
    "/admin/*, /customer/*, /employee/*, /logistics-partner/*, /supplier/*.",
    "Prevents route collisions between modules.")

# ═══════════════════════════════════════════════════════════════
# Infrastructure Laws (140-149)
# ═══════════════════════════════════════════════════════════════
add(140, "Infrastructure", "7 subpackages",
    "database/, redis/, storage/, messaging/, observability/, security/, utils/.",
    "Each subpackage has a single responsibility.")

add(141, "Infrastructure", "Database infra",
    "Base, get_db/get_read_db, sessions, RLS, transactions, seeds.",
    "Single place for DB engine and session management.")

add(142, "Infrastructure", "Redis infra",
    "Client singleton, cache abstraction, blacklist, pub/sub.",
    "Prevents connection proliferation.")

add(143, "Infrastructure", "Storage infra",
    "Abstraction interface + backup utilities.",
    "Backends in providers/storage/.")

add(144, "Infrastructure", "Messaging infra",
    "WS manager, realtime, email wrappers, event bus.",
    "Currently in-process; future: Redis pub/sub.")

add(145, "Infrastructure", "Observability infra",
    "OTEL, Prometheus, structlog, Sentry, circuit breaker.",
    "Wires observability into the app at startup.")

add(146, "Infrastructure", "Security infra",
    "JWT, bcrypt, KMS encryption, rate limiting, CSRF, country access.",
    "Canonical location for auth-related code.")

add(147, "Infrastructure", "Utils infra",
    "Pure technical helpers: pagination, datetime, config, caching, HTTP.",
    "Business primitives belong in kernel/, not here.")

add(148, "Infrastructure", "Canonical Base",
    "infrastructure.database.base.Base is THE base. Others FORBIDDEN.",
    "Multiple bases cause MetaData conflicts and migration failures.")

add(149, "Infrastructure", "Session lifecycle",
    "Sessions via FastAPI Depends(get_db) only.",
    "Ensures sessions are closed even on exceptions.")

# ═══════════════════════════════════════════════════════════════
# Domain Laws (150-160)
# ═══════════════════════════════════════════════════════════════
add(150, "Domain", "Domain structure",
    "services/, models/, schemas/, events.py, subscribers.py, ports.py, features.py, read_models/, policies/.",
    "Standardized structure across all 16 domains.")

add(151, "Domain", "Service patterns",
    "Services take primitives, own DB access and transactions.",
    "Services are the entry point for business logic.")

add(152, "Domain", "Model patterns",
    "__tablename__ + __table_args__ = {schema: <domain>}. Canonical Base.",
    "Every model knows its schema and inherits from one base.")

add(153, "Domain", "Schema patterns",
    "Pydantic models for validation. Used by routers (in) and serializers (out).",
    "Schemas are NOT ORM models — different purposes.")

add(154, "Domain", "Event patterns",
    "Named {domain}.{entity}.{action}. Minimal data (IDs, not objects).",
    "Minimizes coupling between event publisher and subscribers.")

add(155, "Domain", "Port patterns",
    "Sanctioned cross-domain READ path. Take db + primitives, return results.",
    "Ports are the ONLY importable thing from another domain.")

add(156, "Domain", "Subscriber patterns",
    "Handle events from other domains. Resolve context, call services.",
    "Subscribers MUST NOT import from other domains directly.")

add(157, "Domain", "Feature patterns",
    "FEATURES = {key: description}. Consistent format across domains.",
    "Enables rbac/catalog.py to aggregate all features.")

add(158, "Domain", "Read model patterns",
    "CQRS-lite projections for this domain's dashboards.",
    "Cross-domain dashboards live in governance/read_models/.")

add(159, "Domain", "Policy patterns",
    "Authorization policies. Enforced by require_feature() and service checks.",
    "Policies are business rules about access, distinct from auth.")

add(160, "Domain", "16 domains fixed",
    "New domains require architecture review.",
    "Prevents domain sprawl.")

# ═══════════════════════════════════════════════════════════════
# RBAC (161-167)
# ═══════════════════════════════════════════════════════════════
add(161, "RBAC", "Catalog single source",
    "Aggregates all features.py via package scan.",
    "CI fails on any require_feature() literal not in catalog.")

add(162, "RBAC", "Role definitions",
    "(module, role) → feature sets. Static code, not DB-driven.",
    "Enables code review of permission grants.")

add(163, "RBAC", "Resolution",
    "actor × role × country → effective set. Redis-cached.",
    "Fast permission checks on every request.")

add(164, "RBAC", "Dependencies",
    "require_feature(...) and require_module(...) FastAPI dependencies.",
    "The gates used by every module router.")

add(165, "RBAC", "Service",
    "Grant/revoke, delegation, maker-checker. All changes audited.",
    "Runtime permission management with full audit trail.")

add(166, "RBAC", "Permission models",
    "Categories, permissions, assignments, overrides, audit log.",
    "Stored in security Postgres schema.")

add(167, "RBAC", "Frontend permissions",
    "permissions.ts GENERATED from GET /rbac/catalog.",
    "UI gating and backend gating share one source.")

# ═══════════════════════════════════════════════════════════════
# Frontend (168-177)
# ═══════════════════════════════════════════════════════════════
add(168, "Frontend", "Monorepo",
    "web_app/ (Next.js), mobile_app/ (Expo), shared/ (cross-platform).",
    "Code sharing while keeping platform-specific code separate.")

add(169, "Frontend", "Next.js version",
    "16.3.1+ with App Router.",
    "Specific CSS processing requirements.")

add(170, "Frontend", "TypeScript strict",
    "strict: true. any requires justification.",
    "Catches null/undefined errors and missing properties at compile time.")

add(171, "Frontend", "State management",
    "Zustand (global), React (local), Query/SWR (server).",
    "Clear separation of state concerns.")

add(172, "Frontend", "Data fetching",
    "Server Components fetch directly. Client Components use API client.",
    "Frontend knows backend only through the API.")

add(173, "Frontend", "API proxy",
    "Next.js rewrites /api/*, /admin/*, etc. to NEXT_PUBLIC_API_URL.",
    "All API traffic through Next.js server routes. No CORS.")

add(174, "Frontend", "Styling",
    "Tailwind CSS + CVA + tailwind-merge + clsx.",
    "Consistent, type-safe styling with design tokens.")

add(175, "Frontend", "Forms",
    "React Hook Form + Zod.",
    "Server validation authoritative; client for UX.")

add(176, "Frontend", "Error handling",
    "API errors → toasts/boundaries. Unhandled → console (dev) / Sentry (prod).",
    "Users never see raw error objects.")

add(177, "Frontend", "Route groups",
    "Organized by actor: (customer), auth/, admin/*, supplier/*, etc.",
    "Each group has its own layout.")

# ═══════════════════════════════════════════════════════════════
# Web App (178-186)
# ═══════════════════════════════════════════════════════════════
add(178, "Web App", "Route structure",
    "page.tsx, layout.tsx, loading.tsx, error.tsx per route.",
    "Next.js App Router convention.")

add(179, "Web App", "Component structure",
    "ui/ (design system), admin/, auth/, chat/, comms/, country/, etc.",
    "Organized by area for discoverability.")

add(180, "Web App", "Hook patterns",
    "useXxx prefix. No JSX in hooks.",
    "Hooks encapsulate logic; components render UI.")

add(181, "Web App", "Lib patterns",
    "api/ (client, auth, country, errors), rbac.ts.",
    "Pure functions and utilities.")

add(182, "Web App", "Service patterns",
    "localizationService, crossBorderService, addressFormatService.",
    "Client-side services are NOT backend domain services.")

add(183, "Web App", "Theme/styling",
    "Design tokens, Tailwind config, global CSS.",
    "Consistent theme across the app.")

add(184, "Web App", "Types",
    "From @zozi/shared + local definitions.",
    "Shared types prevent drift between frontend and backend.")

add(185, "Web App", "Utils",
    "Pure utility functions.",
    "Business logic belongs in services or hooks.")

add(186, "Web App", "Build",
    "next build passes with no errors.",
    "Build failures block deployment.")

# ═══════════════════════════════════════════════════════════════
# Mobile App (187-194)
# ═══════════════════════════════════════════════════════════════
add(187, "Mobile", "Expo SDK 51+",
    "Expo Router with file-based routing.",
    "Native navigation with deep linking.")

add(188, "Mobile", "Route groups",
    "(auth), (tabs), admin/, supplier/, logistics/, employee/.",
    "Each group has its own layout and navigation.")

add(189, "Mobile", "Components",
    "components/ui/ design system. Shared from @zozi/shared.",
    "Consistent design system across platforms.")

add(190, "Mobile", "Lib patterns",
    "api, stores, authPrompt, countryContext, geo, payment, secureStorage.",
    "Same patterns as web where possible.")

add(191, "Mobile", "Platform-specific",
    ".native.ts (RN) / .ts (web) suffixes.",
    "Enables sharing logic while customizing per-platform.")

add(192, "Mobile", "State",
    "Zustand (same stores as web).",
    "Consistent state management across platforms.")

add(193, "Mobile", "Storage",
    "expo-secure-storage for secrets. AsyncStorage for non-sensitive.",
    "Never store secrets in plain AsyncStorage.")

add(194, "Mobile", "Build",
    "EAS Build. Expo Go for dev. App stores for production.",
    "Automated build and submission pipeline.")

# ═══════════════════════════════════════════════════════════════
# Shared Package (195-200)
# ═══════════════════════════════════════════════════════════════
add(195, "Shared", "Structure",
    "api-core, money, i18n, domain helpers, statusColors, requestCache, etc.",
    "Cross-platform TypeScript consumed by both apps.")

add(196, "Shared", "No app imports",
    "MUST NOT import from web_app/ or mobile_app/.",
    "Prevents circular dependency.")

add(197, "Shared", "Permissions generated",
    "permissions.ts GENERATED from backend /rbac/catalog.",
    "UI and backend gating share one source.")

add(198, "Shared", "Cross-platform types",
    "Platform-agnostic. .native.ts for platform adaptations.",
    "Type safety across web and mobile.")

add(199, "Shared", "API core",
    "apiFetch base client with auth, errors, retry.",
    "Consistent API client across platforms.")

add(200, "Shared", "Money formatting",
    "Intl.NumberFormat with locale support.",
    "Consistent monetary display across platforms.")

# ═══════════════════════════════════════════════════════════════
# Config (201-206)
# ═══════════════════════════════════════════════════════════════
add(201, "Config", "Env hierarchy",
    ".env.example → .env → backend/.env → frontend/.env.local.",
    "Each environment has its own file.")

add(202, "Config", "Required vars",
    "SECRET_KEY, DATABASE_URL, REDIS_URL MUST be set in prod.",
    "Missing vars cause immediate startup failure.")

add(203, "Config", "Typed flags",
    "pydantic-settings. No raw os.getenv().",
    "String 'false' is truthy. Typed coercion prevents bugs.")

add(204, "Config", "Secrets manager",
    "AWS Secrets Manager / HashiCorp Vault in production.",
    ".env files are for development only.")

add(205, "Config", "APP_ENV detection",
    "development, test, staging, production.",
    "Behavior changes based on environment.")

add(206, "Config", "CORS allowlist",
    "Comma-separated list. No wildcard in production.",
    "Prevents arbitrary websites from making authenticated requests.")

# ═══════════════════════════════════════════════════════════════
# Testing (207-214)
# ═══════════════════════════════════════════════════════════════
add(207, "Testing", "pytest framework",
    "pytest + pytest-asyncio. Files in tests/domains/ and tests/architecture/.",
    "Standard Python testing stack.")

add(208, "Testing", "Fixtures",
    "db_session, client/admin_client/supplier_client/customer_client, JWT tokens.",
    "Pre-authenticated test clients speed up test writing.")

add(209, "Testing", "Demo users",
    "admin@zozi.com, supplier@zozi.com, customer@zozi.com.",
    "Consistent test users across environments.")

add(210, "Testing", "Test environment",
    "APP_ENV=test. CSRF/rate disabled. SQLite.",
    "Optimized for speed, not production fidelity.")

add(211, "Testing", "Frontend tests",
    "Jest + RTL. E2E: Playwright.",
    "Standard React testing stack.")

add(212, "Testing", "Architecture tests",
    "test_import_laws.py (Laws 1,4,W1,W2), test_feature_catalog.py (Law 4).",
    "Ensures laws are actually enforced.")

add(213, "Testing", "Coverage",
    "Per-domain smoke tests. Per-law tests. CI-enforced.",
    "Minimum viable test coverage.")

add(214, "Testing", "Isolation",
    "Transaction-rolled-back. No leaks. Independent.",
    "Tests don't affect each other.")

# ═══════════════════════════════════════════════════════════════
# Deployment (215-220)
# ═══════════════════════════════════════════════════════════════
add(215, "Deployment", "Docker Compose",
    "db, redis, backend, frontend, Celery workers, beat.",
    "Local development mirrors production architecture.")

add(216, "Deployment", "Production targets",
    "Backend: Railway. Frontend: Vercel. Mobile: EAS Build.",
    "Each platform has its own deployment pipeline.")

add(217, "Deployment", "Migration on deploy",
    "alembic upgrade head automatic before serving traffic.",
    "Schema is always up-to-date before traffic arrives.")

add(218, "Deployment", "Health checks",
    "/health, /health/deps, /health/ready return 200.",
    "Load balancers use these for routing.")

add(219, "Deployment", "Rollback",
    "MUST support rollback. Migrations backward-compatible.",
    "Zero-downtime rollback on failure.")

add(220, "Deployment", "Env promotion",
    "development → staging → production.",
    "Each environment has its own config and database.")

# ═══════════════════════════════════════════════════════════════
# Performance (221-226)
# ═══════════════════════════════════════════════════════════════
add(221, "Performance", "Caching strategy",
    "Redis with TTL. Event-driven invalidation.",
    "Stale cache preferable to cache stampede.")

add(222, "Performance", "Keyset pagination",
    "cursor_paginate_asc. OFFSET FORBIDDEN on hot lists.",
    "OFFSET degrades to O(n) on large tables.")

add(223, "Performance", "Connection pooling",
    "pool_size ≥ 10, max_overflow ≥ 20. PgBouncer.",
    "Connection exhaustion causes cascading failures.")

add(224, "Performance", "Query optimization",
    "Indexes on queried columns. No N+1. No SELECT *.",
    "Slow queries are logged and reviewed.")

add(225, "Performance", "CDN",
    "Static assets, images via CDN. Presigned URLs.",
    "Reduces origin bandwidth by 40-60%.")

add(226, "Performance", "Async processing",
    "CPU-bound work to Celery. Request handlers never block.",
    "Event loop stays responsive under load.")

# ═══════════════════════════════════════════════════════════════
# Data (227-232)
# ═══════════════════════════════════════════════════════════════
add(227, "Data", "RLS enforcement",
    "set_rls_context() sets country_code. All queries filtered.",
    "Data isolation at the database level.")

add(228, "Data", "Soft delete",
    "is_deleted (boolean, default false). Queries filter by default.",
    "Enables data recovery and audit trails.")

add(229, "Data", "Audit columns",
    "created_at/updated_at via TimestampMixin. DB-side defaults.",
    "Required for debugging and compliance.")

add(230, "Data", "Audit trail",
    "WORM log. Actor, action, entity, timestamp, before/after.",
    "Forensic integrity for compliance investigations.")

add(231, "Data", "Data residency",
    "MAY shard by country_code.",
    "Enables compliance with country-specific data laws.")

add(232, "Data", "Backup & recovery",
    "Daily backups. Tested for recovery. PITR. 30-day retention.",
    "Disaster recovery capability.")

# ═══════════════════════════════════════════════════════════════
# API Design (233-239)
# ═══════════════════════════════════════════════════════════════
add(233, "API", "REST conventions",
    "GET (list/detail), POST (create), PUT (update), DELETE.",
    "Standard REST mapping.")

add(234, "API", "Versioning",
    "URL prefix /api/v1/. Breaking = new version. Old deprecated.",
    "Enables API evolution without breaking clients.")

add(235, "API", "JSON format",
    "Request/response JSON. Pydantic validation. Serializer output.",
    "Consistent, validated, serialized.")

add(236, "API", "RFC 7807 errors",
    "Problem Details. No stack traces in production.",
    "Standard error format enables client-side handling.")

add(237, "API", "Pagination format",
    "items + next_cursor + has_more. No count on hot lists.",
    "Count is expensive on large tables.")

add(238, "API", "Filtering/sorting",
    "filter[field]=value, sort=-created_at. Complex: POST body.",
    "Flexible querying without endpoint proliferation.")

add(239, "API", "Idempotency",
    "Idempotency-Key header. 24h expiry.",
    "Duplicate requests don't cause duplicate operations.")

# ═══════════════════════════════════════════════════════════════
# Git (240-244)
# ═══════════════════════════════════════════════════════════════
add(240, "Git", "Branching",
    "main, feature/*, fix/*, release/*, hotfix/*.",
    "Git Flow convention.")

add(241, "Git", "Conventional Commits",
    "type(scope): description. feat, fix, refactor, docs, test, chore, perf, security.",
    "Automated changelog generation.")

add(242, "Git", "PR process",
    "All via PR. CI + review. No direct main pushes.",
    "Code review catches issues before merge.")

add(243, "Git", "Hooks",
    "Pre-commit: ruff. Pre-push: architecture tests.",
    "Automated quality gates.")

add(244, "Git", "Worktrees",
    "Agent Manager uses worktrees. Cleaned up after merge.",
    "Parallel work without branch switching.")

# ═══════════════════════════════════════════════════════════════
# Documentation (245-250)
# ═══════════════════════════════════════════════════════════════
add(245, "Docs", "Architecture docs",
    "ARCHITECTURE_DIAGRAM.md is authoritative. Lock-step with code.",
    "Single source of truth for architecture.")

add(246, "Docs", "Agent docs",
    "AGENTS.md quick reference. Not the full architecture.",
    "Agent onboarding without overwhelming detail.")

add(247, "Docs", "API docs",
    "FastAPI auto-generates at /docs and /redoc.",
    "Always up-to-date with code.")

add(248, "Docs", "Runbooks",
    "docs/runbooks/. Deployment, rollback, incident response.",
    "Tested in staging quarterly.")

add(249, "Docs", "Code comments",
    "Docstrings + WHY comments. Outdated removed.",
    "Comments explain why, not what.")

add(250, "Docs", "Changelog",
    "CHANGELOG.md. Per-release: features, breaking changes, fixes.",
    "User-facing, plain language.")

# ═══════════════════════════════════════════════════════════════
# Scalability (251-270)
# ═══════════════════════════════════════════════════════════════
add(251, "Scalability", "Horizontal scaling",
    "N stateless replicas. Sessions in Redis.",
    "Add replicas to handle more traffic.")

add(252, "Scalability", "Auto-scaling",
    "CPU > 70% scale up. Min 2, max 20.",
    "Handles traffic spikes without manual intervention.")

add(253, "Scalability", "Partitioning",
    "Range partition by created_at (monthly).",
    "Query time constant as data grows.")

add(254, "Scalability", "CQRS",
    "Commands write. Events update read models.",
    "Prevents write contention from slowing reads.")

add(255, "Scalability", "Write-behind cache",
    "Buffer in Redis, flush async.",
    "10-100x reduction in DB write pressure.")

add(256, "Scalability", "Tenant quotas",
    "Per-country limits. 429 on exceed.",
    "Prevents one tenant from monopolizing resources.")

add(257, "Scalability", "Full-text search",
    "Elasticsearch/OpenSearch for catalog.",
    "Sub-100ms search across millions of products.")

add(258, "Scalability", "Image pipeline",
    "Async resize, WebP, metadata strip.",
    "60-80% bandwidth reduction.")

add(259, "Scalability", "API caching",
    "ETag, Last-Modified, Cache-Control. CDN.",
    "40-60% origin load reduction.")

add(260, "Scalability", "PgBouncer",
    "Transaction pooling. max_client_conn=10000.",
    "Multiplexes thousands of client connections.")

add(261, "Scalability", "Read replicas",
    "Auto-route reads. Fallback if lag > 1s.",
    "Offloads primary. Automatic failover.")

add(262, "Scalability", "Archiving",
    "Old data to S3 Glacier.",
    "Keeps operational tables small and fast.")

add(263, "Scalability", "Write buffering",
    "Celery queue for bursty writes.",
    "Prevents DB overload during spikes.")

add(264, "Scalability", "Static assets",
    "Minify, compress, hash, CDN.",
    "Reduces bandwidth and improves cache hit rate.")

add(265, "Scalability", "DB monitoring",
    "Alerts on connections, lag, deadlocks, slow queries.",
    "Early warning of capacity issues.")

add(266, "Scalability", "Synthetic monitoring",
    "Every 60s from multiple regions.",
    "Detects issues before users report them.")

add(267, "Scalability", "Endpoint limits",
    "Max body (10MB), query (100 items), time (30s).",
    "Prevents resource exhaustion.")

add(268, "Scalability", "Load shedding",
    "Shed non-critical first.",
    "Critical paths always served under load.")

add(269, "Scalability", "Cost optimization",
    "Right-size, spot instances, coalescing.",
    "Efficient resource usage at scale.")

add(270, "Scalability", "Chaos engineering",
    "Regular failure experiments.",
    "Validates resilience assumptions.")

# ═══════════════════════════════════════════════════════════════
# Security Hardening (271-295)
# ═══════════════════════════════════════════════════════════════
add(271, "Security", "AI-agent security",
    "Prompt injection prevention.",
    "AI endpoints are new attack surface.")

add(272, "Security", "Data exfiltration",
    "Per-user export limits.",
    "Prevents AI agents from bulk-extracting data.")

add(273, "Security", "Model poisoning",
    "ML input validation before training.",
    "Prevents adversarial training data.")

add(274, "Security", "Adversarial detection",
    "Signature + anomaly detection.",
    "Catches known and novel attack patterns.")

add(275, "Security", "Encryption at rest",
    "AES-256. KMS. TDE.",
    "Protects data if storage is compromised.")

add(276, "Security", "Encryption in transit",
    "TLS 1.3. Certificate pinning.",
    "Protects data from interception.")

add(277, "Security", "Key rotation",
    "Every 90 days. Zero-downtime.",
    "Limits exposure window of compromised keys.")

add(278, "Security", "WORM audit",
    "Write Once Read Many. Tamper-proof.",
    "Forensic integrity for compliance.")

add(279, "Security", "Session binding",
    "Device fingerprint. Concurrent limits.",
    "Prevents session hijacking and abuse.")

add(280, "Security", "Brute force DB level",
    "5 fails = lock. 10 = admin.",
    "Database-level enforcement beyond app.")

add(281, "Security", "Bot detection",
    "Score + block/CAPTCHA.",
    "Prevents automated abuse.")

add(282, "Security", "PII masking",
    "In logs, errors, non-admin responses.",
    "Prevents PII leakage to unauthorized viewers.")

add(283, "Security", "MFA",
    "TOTP for admin/employee.",
    "Second factor prevents credential abuse.")

add(284, "Security", "Zero-trust",
    "mTLS service-to-service.",
    "No implicit trust based on network location.")

add(285, "Security", "CSP",
    "Strict + nonces.",
    "Prevents XSS via injected scripts.")

add(286, "Security", "SRI",
    "Integrity hashes.",
    "Prevents CDN compromise from injecting code.")

add(287, "Security", "All headers",
    "Permissions-Policy, COOP, CORP.",
    "Defense in depth against browser attacks.")

add(288, "Security", "Disclosure process",
    "SECURITY.md. 24h SLA for critical.",
    "Enables responsible vulnerability reporting.")

add(289, "Security", "Pen testing",
    "Annual third-party. OWASP + logic.",
    "Independent security validation.")

add(290, "Security", "Dep pinning",
    "Exact + hashes.",
    "Prevents supply chain attacks via dep substitution.")

add(291, "Security", "SBOM",
    "For every release.",
    "Know what's in the software.")

add(292, "Security", "License compliance",
    "CI-enforced.",
    "Prevents legal issues from incompatible licenses.")

add(293, "Security", "Incident automation",
    "Auto-isolate, revoke, capture.",
    "Fast response limits blast radius.")

add(294, "Security", "Training",
    "Annual. OWASP + social engineering.",
    "Developers are the first line of defense.")

add(295, "Security", "Supply chain",
    "Image scanning + signing.",
    "Prevents compromised containers.")

# ═══════════════════════════════════════════════════════════════
# Resilience (296-310)
# ═══════════════════════════════════════════════════════════════
add(296, "Resilience", "Circuit breaker",
    "All external calls wrapped.",
    "Prevents cascade failures.")

add(297, "Resilience", "Retry + backoff",
    "1-2-4-8s. Jitter. Max 5.",
    "Handles transient failures without thundering herd.")

add(298, "Resilience", "Dead letter queue",
    "Failed events to DLQ. Replayable.",
    "No event silently dropped.")

add(299, "Resilience", "Feature health",
    "Per-feature in /health/deps.",
    "Granular health visibility.")

add(300, "Resilience", "Per-feature fallback",
    "Each feature defines degradation.",
    "Users always see a usable UI.")

add(301, "Resilience", "Error budget",
    "Exhaustion = freeze.",
    "Balances velocity and reliability.")

add(302, "Resilience", "On-call",
    "PagerDuty/Opsgenie. 5min SLA.",
    "Fast human response to critical issues.")

add(303, "Resilience", "Runbooks",
    "Per-alert. Tested quarterly.",
    "Reduces MTTR for known issues.")

add(304, "Resilience", "DR",
    "RPO=5min, RTO=1hr. Multi-region.",
    "Survives regional failures.")

add(305, "Resilience", "DB failover",
    "30s promotion.",
    "Minimal data loss on primary failure.")

add(306, "Resilience", "Multi-region",
    "≥2 regions. Cross-region replication.",
    "Survives regional failures.")

add(307, "Resilience", "Backup verify",
    "Daily restore test.",
    "A backup that can't be restored is worthless.")

add(308, "Resilience", "Drift detection",
    "IaC daily checks.",
    "Prevents configuration surprises.")

add(309, "Resilience", "Dep monitoring",
    "External status pages. Auto-fallback.",
    "Fast response to external degradation.")

add(310, "Resilience", "Post-incident reviews",
    "Blameless. Action items tracked.",
    "Prevents repeat incidents.")

# ═══════════════════════════════════════════════════════════════
# Operational Excellence (311-325)
# ═══════════════════════════════════════════════════════════════
add(311, "Operations", "Feature flags",
    "Gradual rollout. Instant rollback.",
    "Decouples deployment from release.")

add(312, "Operations", "A/B testing",
    "Hash-based. Sticky.",
    "Data-driven feature decisions.")

add(313, "Operations", "Compliance",
    "GDPR. PCI-DSS via Stripe Elements.",
    "Automated compliance reduces legal risk.")

add(314, "Operations", "IaC",
    "Terraform/Pulumi. Manual FORBIDDEN.",
    "Reproducible, auditable infrastructure.")

add(315, "Operations", "Log aggregation",
    "ELK/Loki. 30d hot, 1y cold.",
    "Centralized visibility.")

add(316, "Operations", "Dashboards",
    "Grafana. p50/p95/p99.",
    "Real-time system health visibility.")

add(317, "Operations", "Alerting tiers",
    "P1/P2/P3.",
    "Right urgency for right issues.")

add(318, "Operations", "Capacity planning",
    "Monthly. 3-month projection.",
    "Prevents surprises.")

add(319, "Operations", "Release mgmt",
    "Canary → full. Rollback < 5min.",
    "Safe, fast deployments.")

add(320, "Operations", "DevX",
    "< 10min setup. Hot reload.",
    "Fast onboarding and iteration.")

add(321, "Operations", "Doc freshness",
    "Quarterly reviews.",
    "Outdated docs are worse than no docs.")

add(322, "Operations", "Cost allocation",
    "By domain/team via tagging.",
    "Visibility into cost drivers.")

add(323, "Operations", "Human access",
    "Least-privilege. 24h offboarding.",
    "Limits blast radius of compromised accounts.")

add(324, "Operations", "Change mgmt",
    "All via PR + CI.",
    "Auditable, reviewable changes.")

add(325, "Operations", "Sustainability",
    "Right-size. Carbon tracking.",
    "Environmental responsibility.")

# ═══════════════════════════════════════════════════════════════
# Generate HTML
# ═══════════════════════════════════════════════════════════════
categories = sorted(set(l["category"] for l in laws))
cat_colors = {
    "Architecture": "#58a6ff", "Structure": "#3fb950", "File Placement": "#d29922",
    "Code Design": "#bc8cff", "Security": "#f85149", "Database": "#db6d28",
    "Code Quality": "#39d2c0", "Testing": "#8b949e", "Infrastructure": "#58a6ff",
    "Config": "#d29922", "Router": "#bc8cff", "Observability": "#3fb950",
    "Wiring": "#db6d28", "Technology": "#39d2c0", "Provider": "#bc8cff",
    "Module": "#58a6ff", "Domain": "#3fb950", "RBAC": "#d29922",
    "Frontend": "#58a6ff", "Web App": "#3fb950", "Mobile": "#bc8cff",
    "Shared": "#d29922", "Deployment": "#8b949e", "Performance": "#db6d28",
    "Data": "#39d2c0", "API": "#58a6ff", "Git": "#8b949e",
    "Docs": "#d29922", "Scalability": "#3fb950", "Resilience": "#f85149",
    "Operations": "#bc8cff", "Migration": "#8b949e", "Code Design": "#bc8cff"
}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ZOZI — Law Matrix (325 Laws)</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
h1{color:#58a6ff;text-align:center;margin:5px 0}
.subtitle{text-align:center;color:#8b949e;margin-bottom:20px;font-size:0.9em}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:15px 0}
.stat{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;text-align:center}
.stat .n{font-size:1.5em;font-weight:bold;color:#58a6ff}
.stat .l{font-size:0.75em;color:#8b949e}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0;align-items:center}
.filters input,.filters select{background:#161b22;border:1px solid #30363d;color:#c9d1d9;padding:6px 10px;border-radius:6px;font-size:0.85em}
.filters input{width:200px}
.filters select{cursor:pointer}
.filters label{font-size:0.8em;color:#8b949e}
table{width:100%;border-collapse:collapse;margin:15px 0;font-size:0.78em;background:#161b22;border-radius:6px;overflow:hidden}
th,td{padding:7px 8px;border:1px solid #30363d;text-align:left;vertical-align:top}
th{background:#1c2128;color:#39d2c0;font-weight:600;position:sticky;top:0;z-index:1}
tr:hover{background:rgba(88,166,255,0.05)}
.law-num{font-weight:bold;color:#58a6ff;white-space:nowrap}
.cat{display:inline-block;padding:2px 6px;border-radius:10px;font-size:0.72em;font-weight:600;color:#fff;white-space:nowrap}
.rule{font-weight:600;color:#f8f8f8}
.desc{color:#c9d1d9}
.why{color:#8b949e;font-style:italic}
.hidden{display:none}
.footer{text-align:center;margin-top:20px;padding:15px;border-top:1px solid #30363d;color:#8b949e;font-size:0.8em}
.count-info{text-align:center;color:#8b949e;font-size:0.85em;margin:5px 0}
</style>
</head>
<body>
<h1>ZOZI Platform — Law Matrix</h1>
<p class="subtitle">325 laws governing the architecture, security, and operations of a 100K+ user e-commerce platform</p>

<div class="stats">
<div class="stat"><div class="n">325</div><div class="l">Total Laws</div></div>
<div class="stat"><div class="n">17</div><div class="l">Sections</div></div>
<div class="stat"><div class="n">16</div><div class="l">Domains</div></div>
<div class="stat"><div class="n">5</div><div class="l">Modules</div></div>
</div>

<div class="filters">
<label>Search:</label>
<input type="text" id="search" placeholder="Search laws..." oninput="filterTable()">
<label>Category:</label>
<select id="catFilter" onchange="changeCat()">
<option value="all">All Categories</option>
"""

for cat in sorted(categories):
    html += f'<option value="{cat}">{cat}</option>\n'

html += """</select>
<span class="count-info" id="countInfo">Showing 325 of 325 laws</span>
</div>

<table id="lawTable">
<thead>
<tr>
<th style="width:50px">Law #</th>
<th style="width:100px">Category</th>
<th style="width:180px">Rule</th>
<th>Description</th>
<th style="width:200px">Why</th>
</tr>
</thead>
<tbody>
"""

for law in laws:
    color = cat_colors.get(law["category"], "#8b949e")
    html += f"""<tr data-category="{law['category']}">
<td class="law-num">{law['id']}</td>
<td><span class="cat" style="background:{color}">{law['category']}</span></td>
<td class="rule">{law['rule']}</td>
<td class="desc">{law['desc']}</td>
<td class="why">{law['why']}</td>
</tr>\n"""

html += """</tbody>
</table>

<div class="footer">
<p>ZOZI Platform — Architecture Law Matrix | Generated: 2026-08-27</p>
<p>Full law text: ARCHITECTURE_DIAGRAM.md (§12 for Laws 1-250, §14-17 for Laws 251-325)</p>
</div>

<script>
function filterTable() {
    const search = document.getElementById('search').value.toLowerCase();
    const cat = document.getElementById('catFilter').value;
    const rows = document.querySelectorAll('#lawTable tbody tr');
    let count = 0;
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const rowCat = row.dataset.category;
        const matchSearch = text.includes(search);
        const matchCat = cat === 'all' || rowCat === cat;
        if (matchSearch && matchCat) { row.classList.remove('hidden'); count++; }
        else { row.classList.add('hidden'); }
    });
    document.getElementById('countInfo').textContent = `Showing ${count} of ${rows.length} laws`;
}
function changeCat() { filterTable(); }
</script>
</body>
</html>"""

with open("docs/action/LAW_MATRIX.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated LAW_MATRIX.html with {len(laws)} laws")
print(f"Categories: {len(categories)}")
