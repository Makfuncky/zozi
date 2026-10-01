# TARGET STATE

Generated: 2026-09-30T04:40:00Z

## Synthesized target from benchmark docs

### Architecture
- **Layers:** modules → {rbac, domains}; rbac → domains; domains → {kernel → infrastructure, providers}; jobs → {domains, infrastructure, providers}; middleware → {rbac, infrastructure}
- **Modules:** admin, customer, employee, logistics, supplier (5 fixed)
- **Domains:** accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers (15 fixed)
- **Package layout:** See ARCHITECTURE_STACK.md §3
- **Router thinness:** auth + require_feature + one service call + serialization
- **Cross-domain:** writes via events.py/subscribers.py; reads via ports.py
- **Country scope:** RLS via SET LOCAL app.country_code

### Technology
- **Backend:** Python 3.13.x, FastAPI 0.141.x, Pydantic 2.13.4, SQLAlchemy 2.0.52, Alembic 1.19.1+, asyncpg 0.31.0, Valkey 9.0.6+, Celery 5.5+
- **Frontend:** Next.js 16.3.5, React 19.2.8, TypeScript 5.9.3, Tailwind CSS 4.3.3, Zustand 5.0.14
- **Mobile:** Expo SDK 57.0.20+, React Native 0.86.3
- **Database:** Neon PostgreSQL 18, RLS, 15 domain schemas
- **Storage:** Cloudflare R2
- **Auth:** PyJWT 2.13.0+, bcrypt 5.0.0, pyotp 2.10.0

### Features
- **Total:** ~330+ features across 7 actor groups
- **Missing:** Loyalty VIP Tiers, Saved Payment Methods, Apple Pay/Google Pay, Product Comparison, Social Sharing, Video Commerce (PDP), Fleet Management, Mobile Employee App

### Laws
- **Total:** 325 laws enforced by audit
- **Key:** No reverse imports, no float for money, schema-per-domain, RLS, event bus, feature single-sourced

### Security
- **JWT:** HS256 via PyJWT, type claim verified
- **Passwords:** bcrypt, >72 bytes rejected
- **Field encryption:** AES-256-GCM for PII/financial/TOTP
- **Payment:** AES-256-GCM encrypted credentials, webhook signatures verified
- **WORM audit:** HMAC-signed append-only log

### Operations
- **Health checks:** /health, /health/deps, /health/ready
- **Migrations:** Linear Alembic history, DATABASE_URL_DIRECT for DDL
- **CI/CD:** GitHub Actions, ruff, mypy, import-linter, architecture tests
