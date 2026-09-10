Yes. For a **large e-commerce codebase**, I would not ask Opus one giant prompt like _“analyze my application and tell me what is wrong.”_ That will almost certainly produce assumptions, missed files, and hallucinated architecture.

The better approach is to perform a **forensic codebase audit in controlled modules**, where each prompt has a narrow scope, requires evidence from actual files, and explicitly forbids assumptions.

The overall process should be:

**Inventory → Architecture → Dependencies → Code/API → Database → Security → Payments → Performance → Bugs → Dead Code → Tests → Infrastructure → Production Readiness → Migration → Validation**

---

# 1. First: establish the rule for the entire audit

Before giving Opus any sector-specific prompt, give it this **master instruction**.

# CODEBASE FORENSIC AUDIT — MASTER RULES

You are performing a forensic technical audit of an existing software codebase.

The application is a large-scale e-commerce platform comparable in business complexity to Daraz.pk, Alibaba, Shein, Amazon and etc.

Your job is to determine what ACTUALLY EXISTS in the codebase, not what you think the developers intended to build.

## ABSOLUTE RULES

1. NEVER assume a technology, library, package, architecture, feature, security mechanism, database behavior, API, or configuration exists unless you can prove it from the repository.

2. NEVER infer implementation details from:
   - folder names alone
   - README files alone
   - package names alone
   - comments alone
   - variable names alone
   - documentation alone

3. Every important finding MUST contain evidence:
   - file path
   - line number or line range whenever possible
   - relevant symbol/function/class/configuration name

4. Clearly distinguish:
   - VERIFIED — directly confirmed from source/configuration
   - INFERRED — strongly suggested but not directly confirmed
   - UNKNOWN — insufficient evidence

5. Do NOT invent missing information.

6. If something cannot be determined from the available code, explicitly say:
   "NOT DETERMINABLE FROM AVAILABLE CODE."

7. Do not recommend migration or rewriting during the initial forensic analysis unless specifically requested by the current task.

8. Do not judge code quality merely because it uses an older technology. First determine what it actually does.

9. Do not recommend replacing a technology simply because a newer technology exists.

10. Identify contradictions between:
    - source code
    - configuration
    - package manifests
    - database models
    - API definitions
    - deployment configuration
    - documentation

11. Never silently resolve contradictions. Report them.

12. Do not treat an unused dependency as proof that the library is actually used.

13. Do not treat an imported library as proof that its functionality is meaningfully used.

14. Trace important functionality through actual call paths whenever possible.

15. For security findings, distinguish:
    - confirmed vulnerability
    - security weakness
    - potential risk requiring verification

16. For production-readiness findings, distinguish:
    - blocking issue
    - high-risk issue
    - medium issue
    - low issue
    - informational

17. Do not modify files during this audit.

18. Do not execute destructive commands.

19. Do not expose or reproduce secrets, API keys, passwords, tokens, private keys, payment credentials, or personally identifiable information. Report their existence and location without revealing the secret value.

## EVIDENCE STANDARD

For every major conclusion use:

Finding:
Status: VERIFIED / INFERRED / UNKNOWN
Evidence:
Files:
Symbols:
Impact:
Confidence:

If evidence is insufficient, say so. 

## IMPORTANT

The objective is to build a factual technical map of the existing application before any migration decision is made.

Do not redesign the application yet.

Do not assume what the application SHOULD be.

Determine what the application IS on the basis of quality evidence which you will extract after reading the `code`and `codebase`, and not from documents files

---

# 2. Audit architecture in layers

Don't give Opus all the following prompts simultaneously.

Give them **one at a time**.

That keeps its context focused and makes the results much more trustworthy.

---

# PHASE 1 — Repository Inventory

### Prompt 01 — Complete Codebase Inventory

# TASK 01 — COMPLETE REPOSITORY INVENTORY

Perform ONLY a structural inventory of the repository.

Do not evaluate code quality yet.

Determine:

1. Complete directory structure.
2. Important files.
3. Application entry points.
4. Backend applications.
5. Frontend applications.
6. Worker/background applications.
7. CLI applications.
8. Scripts.
9. Configuration files.
10. Environment files/templates.
11. Docker files.
12. CI/CD files.
13. Infrastructure files and circuit.
14. Database migration files and circuit. 
15. ORM/model definitions.
16. API definitions.
17. Test directories.
18. Documentation.
19. Generated files.
20. Build artifacts.
21. Static assets.
22. Uploaded/user-generated asset handling.
23. Third-party integrations.

For every major directory determine its apparent responsibility.

DO NOT assume responsibility from directory name alone. Verify by examining representative files.

Output:

## Repository Structure

Provide a tree-like representation.

## Application Components

| Component | Location | Evidence | Confidence |

## Entry Points

| Entry Point | File | Function/Class | Purpose | Evidence |

## Configuration

| Configuration | File | Technology/Purpose | Evidence |

## Build/Deployment

| File | Technology | Purpose | Evidence |

## Unknown Areas

List anything that cannot be determined.

## Suspicious Areas

Only identify structural anomalies. Do not perform a security or quality audit yet.

IMPORTANT:
Do not recommend changes.
Do not recommend migration.
Do not infer architecture that is not supported by code.

---

# PHASE 2 — Technology Stack

### Prompt 02 — Exact Technology Stack

# TASK 02 — TECHNOLOGY / FRAMEWORK / LIBRARY INVENTORY

Determine the ACTUAL technology stack used by this repository.

Inspect:

- package.json
- lock files
- requirements files
- pyproject.toml
- Cargo.toml
- go.mod
- composer.json
- pom.xml
- build.gradle
- Dockerfiles
- CI/CD configuration
- configuration files
- imports
- framework initialization
- source code
- generated/build configuration

Identify:

1. Programming languages.
2. Runtime versions.
3. Frameworks.
4. Libraries.
5. ORM.
6. Database drivers.
7. Validation libraries.
8. Authentication libraries.
9. Authorization libraries.
10. HTTP clients.
11. HTTP servers.
12. Caching.
13. Queues.
14. Background workers.
15. Search engines.
16. Object/file storage.
17. Image processing.
18. Email.
19. SMS.
20. Payment providers.
21. Logging.
22. Monitoring.
23. Analytics.
24. Testing frameworks.
25. Build tools.
26. Package managers.
27. Infrastructure technologies.
28. Container technologies.
29. Cloud services.
30. CDN/reverse proxy technologies.

For every technology:

| Technology | Version | Declared Dependency? | Actually Imported? | Actually Used? | Evidence | Confidence |

IMPORTANT:

"Installed" does NOT mean "used".

"Imported" does NOT necessarily mean "functionally used".

Trace usage where practical.

Do not recommend upgrades yet.

End with:

## VERIFIED STACK

Only technologies conclusively confirmed.

## SUSPECTED STACK

Technologies that appear likely but lack sufficient evidence.

## UNKNOWN

Things that cannot currently be determined.

---

# PHASE 3 — Dependency Forensics

This is extremely important because AI-generated applications often contain garbage dependencies.

### Prompt 03 — Dependency Audit

# TASK 03 — DEPENDENCY FORENSIC AUDIT

Audit ONLY third-party dependencies and package management.

Determine:

1. Direct dependencies.
2. Transitive dependencies where available.
3. Dependency versions.
4. Lock-file consistency.
5. Duplicate packages.
6. Multiple versions of the same package.
7. Unused dependencies.
8. Imported-but-unused dependencies.
9. Dependencies declared but apparently never used.
10. Libraries used without being declared.
11. Deprecated packages.
12. Abandoned/unmaintained packages.
13. Known incompatible package combinations.
14. Runtime/build-time dependency confusion.
15. Development dependencies incorrectly required in production.
16. Production dependencies incorrectly classified as development-only.
17. Version conflicts.
18. Framework/plugin compatibility issues.
19. Native dependencies.
20. Packages with known security vulnerabilities.

For every finding provide:

Package:
Version:
Manifest:
Lockfile version:
Observed usage:
Status:
Evidence:
Risk:
Recommended action:

Do NOT recommend upgrading everything automatically.

For vulnerabilities, distinguish:

- confirmed by package/security metadata
- potentially vulnerable
- cannot verify

Do not claim a CVE exists unless evidence confirms it.

End with:

### Dependency Health Score

Provide separate scores for:

- correctness
- maintainability
- security
- reproducibility

Explain every score using evidence.

---

# PHASE 4 — Import & Codebase Depth

This directly answers your question:

> “What imports or code functions exist in it?”

### Prompt 04 — Import Map

# TASK 04 — IMPORT / MODULE DEPENDENCY MAP

Build a factual map of imports and module dependencies.

For every significant source module determine:

- file path
- language
- imports
- imported symbols
- internal module dependencies
- external dependencies
- exported symbols
- classes
- functions
- constants
- important side effects

Do NOT list every trivial language builtin unless necessary.

Focus on application-level dependencies.

Output:

## MODULE INVENTORY

| File | Imports | Internal Dependencies | External Dependencies | Exports |

## HIGH-DEPENDENCY MODULES

Identify modules imported by many other modules.

## CIRCULAR DEPENDENCIES

Identify confirmed circular dependency chains.

## ORPHAN MODULES

Identify modules that appear not to be referenced.

Do not assume an orphan module is dead code; explain why it appears orphaned.

## ARCHITECTURAL HOTSPOTS

Identify modules with unusually high dependency concentration.

Evidence is mandatory.

---

# PHASE 5 — Function/Class Inventory

### Prompt 05 — Code Surface Map

# TASK 05 — APPLICATION CODE SURFACE MAP

Map the application's significant executable code.

Identify:

- classes
- public functions
- API handlers
- service functions
- repository/data-access functions
- background jobs
- event handlers
- port handlers
- middleware
- authentication functions
- authorization functions
- payment functions
- order functions
- inventory functions
- product/categories functions
- cart functions
- checkout functions
- user/customer functions
- admin functions
- supplier functions
- logistic partner functions
- employee functions
- multi-countries functions
- automation functions
- finance/reporting/accounts/tax/payout/expenses/commission manage functions
- notification functions
- file-upload functions
- search functions
- caching functions
- external integration functions
- all domains/provider/infrastructure/rbac/etc functions

For every important symbol provide:

| Symbol | File | Type | Called By | Calls | Purpose | Evidence |

Identify:

1. Extremely large functions.
2. Extremely large classes.
3. Highly coupled modules.
4. Deep call chains.
5. Functions with many responsibilities.
6. Global state.
7. Singleton-like state.
8. Hidden side effects.
9. Duplicate implementations.

Do NOT call something bad merely because it is large.

Explain why each hotspot matters.

Do not refactor anything yet.

---

# PHASE 6 — Business Logic

Now we find out what the application **actually does**.

### Prompt 06 — Business Domain Mapping

# TASK 06 — E-COMMERCE BUSINESS DOMAIN MAP

Analyze ONLY business functionality.

Determine which e-commerce capabilities actually exist.

Investigate:

- user registration
- login
- profiles
- sellers
- seller onboarding
- product catalog
- categories
- attributes
- variants
- pricing
- discounts
- coupons
- promotions
- cart
- wishlist
- checkout
- orders
- order items
- inventory
- warehouses
- shipping
- delivery
- returns
- refunds
- cancellations
- reviews
- ratings
- seller settlements
- commissions
- invoices
- taxes
- payments
- notifications
- customer support
- search
- recommendations
- admin functionality
- employee functionality
- supplier functionality
- logistic functionality


For each capability classify:

IMPLEMENTED
PARTIALLY IMPLEMENTED
STUBBED
REFERENCED BUT NOT IMPLEMENTED
NOT FOUND
UNKNOWN

Evidence is mandatory.

Trace important workflows.

For example:

Product → Cart → Checkout → Payment → Order → Inventory → Shipping

Do not assume this workflow exists.

Document the actual workflow found in code.

End with:

## ACTUAL BUSINESS CAPABILITIES

## MISSING / PARTIAL CAPABILITIES

## BUSINESS LOGIC RISKS

---

# PHASE 7 — Database

This is one of the most important audits for a Daraz-scale system.

### Prompt 07 — Database Forensics

# TASK 07 — DATABASE FORENSIC AUDIT

Analyze ONLY database architecture and data access.

Determine:

1. Database technology.
2. Database version if determinable.
3. ORM/query builder.
4. Database connection configuration.
5. Models/entities.
6. Tables.
7. Relationships.
8. Primary keys.
9. Foreign keys.
10. Unique constraints.
11. Check constraints.
12. Indexes.
13. Transactions.
14. Isolation assumptions.
15. Migrations.
16. Seed data.
17. Raw SQL.
18. N+1 query risks.
19. Unbounded queries.
20. Missing pagination.
21. Missing indexes.
22. Excessive joins.
23. Duplicate data.
24. Denormalization.
25. Data integrity risks.
26. Race-condition risks.
27. Soft-delete implementation.
28. Audit/history mechanisms.
29. Tenant/seller isolation where applicable.
30. Sensitive data storage.

Trace:

User → Cart → Order → Payment → Inventory

where those relationships exist.

For every major table/model provide:

| Model/Table | Purpose | Relationships | Important Constraints | Indexes | Evidence |

Do not redesign the database yet.

Do not assume a missing constraint exists because application code checks it.

Distinguish application-level validation from database-level enforcement.

---

# PHASE 8 — API

### Prompt 08 — API Surface

# TASK 08 — API FORENSIC AUDIT

Analyze ONLY API architecture.

Inventory:

- REST endpoints
- GraphQL
- RPC
- WebSockets
- webhooks
- internal APIs
- external APIs

For every endpoint provide:

| Method | Route | Handler | Auth | Authorization | Input | Output | DB/Service Calls | Evidence |

Determine:

1. Authentication mechanism.
2. Authorization mechanism.
3. Role system.
4. Permission system.
5. Input validation.
6. Output validation.
7. Error handling.
8. Rate limiting.
9. Pagination.
10. Filtering.
11. Sorting.
12. Idempotency.
13. CORS.
14. CSRF protections where relevant.
15. File upload handling.
16. API versioning.
17. Sensitive information exposure.
18. Debug endpoints.
19. Admin endpoints.
20. Internal endpoints accidentally exposed.

Trace important endpoints from:

request → middleware → authentication → authorization → validation → business logic → database → response.

Do not assume middleware protects an endpoint unless the actual routing/middleware configuration proves it.

---

# PHASE 9 — Authentication & Authorization

### Prompt 09 — Security: Identity

# TASK 09 — AUTHENTICATION / AUTHORIZATION SECURITY AUDIT

Analyze ONLY identity and access control.

Inspect:

- registration
- login
- logout
- sessions
- cookies
- JWT
- refresh tokens
- password hashing
- password reset
- email verification
- MFA
- OAuth
- roles
- permissions
- seller accounts
- admin accounts
- privileged operations

Determine actual mechanisms from source code.

Check for:

- plaintext passwords
- weak hashing
- insecure token storage
- token leakage
- missing expiration
- session fixation
- privilege escalation
- IDOR/BOLA
- missing authorization
- horizontal privilege escalation
- vertical privilege escalation
- insecure password reset
- account enumeration
- missing brute-force protection
- insecure cookies
- missing CSRF protection where applicable
- excessive token lifetime
- improper logout
- authorization performed only on frontend

For every finding:

Severity:
Confirmed/Potential:
Affected endpoint/function:
Evidence:
Attack scenario:
Impact:
Recommended remediation:

Do not claim exploitability without evidence.

---

# PHASE 10 — Payment Security

For an e-commerce platform this deserves its own isolated audit.

### Prompt 10 — Payment Gateway

# TASK 10 — PAYMENT SYSTEM FORENSIC AND SECURITY AUDIT

Analyze ONLY payment-related functionality.

Identify all payment providers and integrations actually present.

Inspect:

- payment initialization
- payment sessions
- payment intents
- callbacks
- webhooks
- payment verification
- signatures
- transaction IDs
- order/payment relationship
- refunds
- partial refunds
- failed payments
- retries
- duplicate callbacks
- idempotency
- currency handling
- amount calculation
- discounts
- taxes
- shipping charges
- payment status transitions
- secrets
- API credentials
- frontend payment handling

Trace the complete flow:

Cart
→ Price calculation
→ Checkout
→ Payment creation
→ Gateway
→ Callback/Webhook
→ Verification
→ Order state
→ Inventory state
→ Notification

Determine whether the system trusts:

- frontend prices
- frontend quantities
- frontend discounts
- frontend payment status
- webhook data without verification

Look specifically for:

- price manipulation
- amount tampering
- replay
- duplicate payment processing
- webhook spoofing
- missing signature verification
- race conditions
- double order creation
- double inventory deduction
- refund authorization problems
- secret exposure
- sensitive payment data storage

Do not expose any real credentials.

Output confirmed findings separately from potential findings.

---

# PHASE 11 — Security Full Audit

After the specialized audits, do the broader security pass.

### Prompt 11 — Full Application Security

# TASK 11 — APPLICATION SECURITY AUDIT

Perform a comprehensive defensive security audit of the application.

Analyze:

- authentication
- authorization
- API security
- input validation
- SQL injection
- NoSQL injection where applicable
- command injection
- SSRF
- XSS
- CSRF
- file upload
- path traversal
- deserialization
- template injection
- open redirects
- CORS
- security headers
- secrets
- logging
- error messages
- dependency vulnerabilities
- exposed debug functionality
- admin interfaces
- rate limiting
- brute-force protection
- data exposure
- sensitive data handling
- encryption
- transport security assumptions
- webhook security

For every finding use:

ID:
Severity:
Confirmed/Potential:
Category:
Affected file:
Affected function/endpoint:
Evidence:
Why it is vulnerable:
Impact:
Recommended remediation:
Confidence:

Do not provide exploit instructions beyond what is necessary to demonstrate the issue.

Do not expose secrets.

Prioritize actual exploitable issues over theoretical concerns.

---

# PHASE 12 — Performance & Computation

This answers your:

> “best way to optimize computation”

### Prompt 12 — Performance Forensics

# TASK 12 — PERFORMANCE / COMPUTATION AUDIT

Analyze application performance without modifying the code.

Identify computational hotspots in:

- CPU-intensive operations
- database queries
- loops
- nested loops
- serialization
- deserialization
- JSON processing
- image processing
- file processing
- API calls
- external integrations
- synchronous blocking operations
- asynchronous operations
- background jobs
- caching
- repeated calculations
- repeated database access
- network calls

Look for:

- N+1 queries
- O(n²) or worse algorithms
- unnecessary repeated computation
- excessive serialization
- blocking I/O
- unnecessary synchronous work
- missing caching
- cache misuse
- excessive memory allocation
- large payloads
- missing pagination
- repeated external API requests
- inefficient image processing
- expensive operations inside request handlers

For every hotspot provide:

Location:
Operation:
Observed behavior:
Estimated complexity where determinable:
Why it is expensive:
Evidence:
Potential optimization:
Expected benefit:
Risk of optimization:

Do NOT invent benchmark numbers.

If actual profiling data does not exist, explicitly state that performance conclusions are static-analysis findings and not measured benchmarks.

---

# PHASE 13 — Dead Code

AI-generated projects commonly have enormous amounts of this.

### Prompt 13 — Dead Code

# TASK 13 — DEAD CODE / UNUSED CODE AUDIT

Identify code that appears unused.

Analyze:

- unused imports
- unused variables
- unused functions
- unused classes
- unused modules
- unreachable branches
- obsolete feature implementations
- duplicate implementations
- abandoned experiments
- commented-out code
- unused API routes
- unused models
- unused configuration
- unused environment variables
- unused dependencies

IMPORTANT:

Do NOT label code as dead merely because no direct reference was found.

Consider:

- dynamic imports
- reflection
- framework discovery
- dependency injection
- route registration
- plugin systems
- CLI entry points
- event handlers
- configuration-driven behavior
- external callers

Classify:

CONFIRMED DEAD
PROBABLY DEAD
POSSIBLY USED DYNAMICALLY
UNKNOWN

Provide evidence for every item.

---

# PHASE 14 — Contradictions & Bugs

### Prompt 14 — Logic Consistency

# TASK 14 — BUG / CONTRADICTION / INCONSISTENCY AUDIT

Search for contradictions and logic defects.

Check consistency between:

- frontend and backend
- API contracts and implementations
- models and database
- migrations and models
- validation and business logic
- configuration and code
- environment variables and usage
- payment states
- order states
- inventory states
- authentication states
- package versions
- deployment configuration
- documentation and implementation

Look for:

- impossible states
- missing state transitions
- contradictory conditions
- incorrect defaults
- type mismatches
- null/None handling bugs
- race conditions
- transaction boundary problems
- incorrect exception handling
- swallowed errors
- inconsistent validation
- duplicated business rules
- stale code paths
- frontend/backend contract mismatches

For each confirmed defect:

Bug ID:
Severity:
Location:
Evidence:
Expected behavior:
Actual behavior:
Why it is incorrect:
Affected workflow:
Recommended fix:

Do not call something a bug unless the source supports the conclusion.

---

# PHASE 15 — Testing

### Prompt 15 — Test Coverage Reality

# TASK 15 — TESTING FORENSIC AUDIT

Determine the ACTUAL testing state.

Inspect:

- unit tests
- integration tests
- API tests
- end-to-end tests
- database tests
- payment tests
- security tests
- frontend tests
- load tests
- regression tests
- CI test execution

Determine:

1. What is tested?
2. What is not tested?
3. Whether tests actually execute.
4. Whether tests are meaningful.
5. Broken tests.
6. Flaky tests.
7. Mock-heavy tests that don't validate real behavior.
8. Missing critical workflow tests.

Pay special attention to:

- authentication
- authorization
- checkout
- payment
- order creation
- inventory
- refunds
- seller operations
- admin operations

Do not calculate a fake percentage if reliable coverage data is unavailable.

Clearly distinguish:

tested
partially tested
untested
unknown.

---

# PHASE 16 — Infrastructure / Deployment

### Prompt 16 — Production Infrastructure

# TASK 16 — DEPLOYMENT / INFRASTRUCTURE AUDIT

Analyze how the application is intended to run in production.

Inspect:

- Docker
- Docker Compose
- Kubernetes
- reverse proxy
- web server
- application server
- workers
- queues
- databases
- Valkey/cache
- object storage
- CDN
- DNS configuration
- TLS configuration
- CI/CD
- environment configuration
- secrets management
- logging
- monitoring
- backups
- health checks
- readiness checks
- liveness checks
- scaling configuration

Determine:

- how application starts
- how requests reach application
- how background jobs run
- how data is stored
- how files are stored
- how services communicate
- how deployments occur
- how failures are handled

Identify single points of failure.

Do not design the target architecture yet.

Document the architecture that actually exists or can be proven.

---

# PHASE 17 — Production Readiness

Only after all previous investigations.

### Prompt 17 — Production Readiness Assessment

# TASK 17 — PRODUCTION READINESS ASSESSMENT

Using ONLY findings supported by previous forensic analysis and repository evidence, evaluate whether this application is production-ready for a large-scale e-commerce business.

Evaluate:

1. Architecture
2. Code quality
3. Dependency health
4. Database integrity
5. API quality
6. Authentication
7. Authorization
8. Payment security
9. Business logic correctness
10. Performance
11. Scalability
12. Reliability
13. Observability
14. Testing
15. CI/CD
16. Infrastructure
17. Backup/recovery
18. Security
19. Maintainability
20. Operational readiness

Classify each:

READY
PARTIALLY READY
NOT READY
UNKNOWN

Then create:

## PRODUCTION BLOCKERS

Issues that must be resolved before production.

## HIGH-RISK ISSUES

Issues that could seriously affect users, money, security, or availability.

## MEDIUM-RISK ISSUES

## LOW-RISK ISSUES

## UNKNOWN / REQUIRES VALIDATION

Do NOT recommend a complete rewrite merely because the code is poor.

Explain whether the existing system can realistically be:

- repaired
- refactored
- partially migrated
- incrementally replaced
- or should be substantially rewritten

Do not make that decision based on aesthetics.

Use evidence.

---

# 3. Now comes the most important part: Migration

**Do not ask Opus “upgrade everything to the latest.”**

That is one of the worst ways to migrate a large application.

You first create the **current-state map**, then establish a **target architecture**, then migrate incrementally.

---

# PHASE 18 — Target Technology Research

For this one, I would actually allow current-version research rather than asking the model to rely on its training knowledge.

### Prompt 18 — Technology Selection

# TASK 18 — TARGET TECHNOLOGY EVALUATION

Using the verified current architecture from the previous audit, design a target technology stack for a large-scale production e-commerce platform.

Do NOT automatically select the newest technology.

Evaluate technologies based on:

- maturity
- ecosystem
- security
- performance
- scalability
- maintainability
- developer availability
- operational complexity
- long-term support
- migration difficulty
- compatibility with existing system
- production track record
- observability
- testing ecosystem

For each current technology determine:

KEEP
UPGRADE
REPLACE
REMOVE
INTRODUCE

For every proposed replacement provide:

Current:
Proposed:
Reason:
Advantages:
Disadvantages:
Migration difficulty:
Compatibility concerns:
Operational impact:
Security impact:
Performance impact:
Evidence:

IMPORTANT:

"Latest" does NOT automatically mean "best".

Prefer mature, production-proven technologies unless there is a compelling reason otherwise.

Do not perform migration yet.

---

# PHASE 19 — Target Architecture

### Prompt 19

# TASK 19 — TARGET PRODUCTION ARCHITECTURE

Based on the verified current system and approved technology evaluation, design the target architecture.

The target must support a large-scale e-commerce platform.

Address:

- frontend
- backend
- API gateway/reverse proxy
- authentication
- authorization
- database
- caching
- queues
- background workers
- search
- object storage
- CDN
- payments
- notifications
- observability
- logging
- monitoring
- CI/CD
- infrastructure
- backups
- disaster recovery
- security
- scaling

Do NOT automatically use microservices.

Explicitly compare:

1. Modular monolith
2. Modular monolith + workers
3. Selective service extraction
4. Full microservices

Choose the architecture based on actual business and scaling requirements.

For every major architectural decision explain:

Problem:
Decision:
Reason:
Alternative:
Why alternative was rejected:
Migration impact:
Operational complexity:

---

# PHASE 20 — Migration Strategy

This is where your actual migration plan comes from.

### Prompt 20 — Full Migration Roadmap

# TASK 20 — INDUSTRIAL MIGRATION ROADMAP

Create a production-grade migration plan from the CURRENT VERIFIED SYSTEM to the TARGET ARCHITECTURE.

The migration must minimize:

- downtime
- data loss
- security risk
- business disruption
- rollback difficulty

Use incremental migration wherever practical.

Organize the migration into phases.

For every phase provide:

Phase:
Objective:
Prerequisites:
Files/components affected:
Database changes:
API changes:
Infrastructure changes:
Testing required:
Deployment strategy:
Rollback strategy:
Risk:
Exit criteria:

Include:

1. Repository cleanup
2. Dependency stabilization
3. Test foundation
4. Security remediation
5. Database stabilization
6. Architecture refactoring
7. API stabilization/versioning
8. Infrastructure modernization
9. Observability
10. Performance optimization
11. Payment hardening
12. Incremental feature migration
13. Data migration
14. Traffic migration
15. Production validation
16. Legacy removal

Use techniques such as:

- feature flags
- strangler pattern where appropriate
- expand/contract database migrations
- backward-compatible APIs
- dual-read where justified
- dual-write only when justified and carefully controlled
- shadow traffic where appropriate
- canary deployment
- blue/green deployment where appropriate

Do not recommend dual-write casually.

For every migration stage specify rollback conditions.

End with:

## MIGRATION DEPENDENCY GRAPH

Show which phases must happen before others.

## CRITICAL PATH

Identify the steps that determine overall migration duration.

---

# 4. But I strongly recommend one more layer

You said:

> “AI context and hallucinations issue.”

Exactly.

So make Opus maintain a **Fact Ledger**.

Give it this prompt after the first few audits.

### Prompt 21 — Evidence Ledger

# TASK 21 — FACT / EVIDENCE LEDGER

Create a centralized evidence ledger from all previous audit results.

Every significant statement about the application must be classified:

VERIFIED
INFERRED
UNKNOWN
CONTRADICTED

For VERIFIED findings record:

ID:
Claim:
Evidence:
File:
Line:
Symbol:
Audit:
Confidence:

For INFERRED findings:

ID:
Claim:
Evidence:
Reasoning:
What would be required to verify:
Confidence:

For UNKNOWN:

ID:
Unknown:
Why it cannot be determined:
What artifact would be required:

For CONTRADICTED:

ID:
Claim:
Evidence A:
Evidence B:
Conflict:

IMPORTANT:

If a later analysis contradicts an earlier finding, do NOT silently overwrite it.

Record the contradiction and determine which evidence is stronger.

This ledger is the authoritative factual basis for subsequent architecture and migration decisions.

Do not add assumptions to the ledger.

---

# 5. Then make Opus create the final "master picture"

After all audits:

### Prompt 22 — Executive Technical Report

# TASK 22 — FINAL APPLICATION TECHNICAL ASSESSMENT

Using the completed forensic audit and evidence ledger, produce the final technical assessment.

The report must answer:

## 1. WHAT IS THIS APPLICATION?

Explain what the application actually does.

## 2. WHAT TECHNOLOGIES DOES IT USE?

Provide the verified stack.

## 3. HOW DEEP IS THE CODEBASE?

Provide:

- source files
- modules
- classes
- functions
- API endpoints
- database models
- external integrations
- workers
- major workflows

Use actual repository evidence.

## 4. HOW DOES THE SYSTEM WORK?

Explain the architecture and major request/data flows.

## 5. WHAT IS GOOD?

Identify components that should be preserved.

## 6. WHAT IS BAD?

Identify technical debt and structural problems.

## 7. WHAT IS DANGEROUS?

Security, financial, data-integrity, reliability, or scalability risks.

## 8. WHAT IS BROKEN?

Confirmed bugs and contradictions.

## 9. WHAT IS UNUSED?

Dead/obsolete code and dependencies.

## 10. WHAT IS MISSING?

Capabilities required for production that are absent or incomplete.

## 11. WHAT PREVENTS PRODUCTION?

List production blockers.

## 12. WHAT SHOULD BE KEPT?

Do not rewrite functioning systems unnecessarily.

## 13. WHAT SHOULD BE REFACTORED?

## 14. WHAT SHOULD BE REPLACED?

## 15. TARGET TECHNOLOGY STACK

Provide the proposed production stack with justification.

## 16. TARGET ARCHITECTURE

Describe the target system.

## 17. MIGRATION ROADMAP

Provide ordered phases.

## 18. RISK REGISTER

| Risk | Severity | Probability | Impact | Mitigation |

## 19. FINAL RECOMMENDATION

Choose one:

REPAIR
REFACTOR
PARTIAL MIGRATION
INCREMENTAL REPLACEMENT
MAJOR REWRITE

Explain why.

IMPORTANT:

Do not make claims unsupported by repository evidence.

Separate facts from recommendations.

---

# 6. One very important change I'd make to your approach

Don't think of this as:

> **"Find the latest technologies and migrate to them."**

Think of it as:

> **"Determine what exists → determine what is wrong → determine what needs to change → select technology → migrate only what needs to change."**

For a Daraz-scale system, blindly rewriting everything can be **more dangerous than keeping some ugly code**.

For example:

```text
Old but stable payment integration
        ↓
        KEEP + HARDEN
```

could be better than:

```text
Old payment integration
        ↓
"Let's replace it with the newest library"
        ↓
New bugs
        ↓
Payment failures
        ↓
Duplicate orders
        ↓
Financial reconciliation nightmare
```

---

# 7. Recommended migration philosophy

For this type of application, I'd generally aim for:

```text
                    CURRENT SYSTEM
                         │
                         ▼
                ┌─────────────────┐
                │ FORENSIC AUDIT  │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ STABILIZE       │
                │ Dependencies    │
                │ Tests           │
                │ Security        │
                │ DB integrity    │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ TARGET ARCH.    │
                └────────┬────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        KEEP / REFACTOR        REPLACE
              │                     │
              └──────────┬──────────┘
                         ▼
                 INCREMENTAL
                   MIGRATION
                         │
                         ▼
                  TEST + CANARY
                         │
                         ▼
                  PRODUCTION
                         │
                         ▼
                 REMOVE LEGACY
```

Not:

```text
Old application
      ↓
DELETE
      ↓
NEW EVERYTHING
      ↓
HOPE
```

---

# 8. And there is one more thing I'd do differently for AI

**Never let Opus maintain the entire investigation only inside its chat context.**

Have it produce persistent artifacts after each phase:

```text
/_audit
    00-master-rules.md
    01-repository-inventory.md
    02-technology-stack.md
    03-dependencies.md
    04-import-map.md
    05-code-surface.md
    06-business-domains.md
    07-database.md
    08-api.md
    09-auth.md
    10-payments.md
    11-security.md
    12-performance.md
    13-dead-code.md
    14-bugs.md
    15-testing.md
    16-infrastructure.md
    17-production-readiness.md
    18-technology-selection.md
    19-target-architecture.md
    20-migration-roadmap.md
    21-evidence-ledger.md
    22-final-assessment.md
```

Then every subsequent prompt should say:

> **Use the repository as the primary source of truth. Use previous audit documents only as secondary analysis. If an audit document conflicts with source code, re-check the source code.**

That single rule dramatically reduces **AI drift**.

---

## The most important principle

For your application, I would establish these four levels of truth:

| Level                   | Meaning                                |
| ----------------------- | -------------------------------------- |
| **L0 — Source**         | Actual repository code/configuration   |
| **L1 — Evidence**       | File + line + symbol proving something |
| **L2 — Analysis**       | Conclusions derived from L0/L1         |
| **L3 — Recommendation** | What we think should be changed        |

Never allow:

**L3 → L0**

In other words, don't let the AI's recommended architecture become its assumption about what the existing application already contains.

The correct direction is:

**Source → Evidence → Analysis → Decision → Migration**

That is the process I'd use if the goal is to take a **non-professionally AI-built e-commerce application and turn it into a genuinely industrial, production-grade system** without blindly throwing away useful existing work.
