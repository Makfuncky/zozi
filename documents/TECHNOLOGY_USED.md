Now I have a complete picture. Here's the comprehensive technology stack for the ZOZI e-commerce platform:

---

## **Backend (FastAPI / Python)**

### **Core Framework & Runtime**
- **FastAPI 0.115.2** — Modern async web framework for APIs
- **Python 3.11** (Docker) / 3.10 (local dev)
- **Uvicorn 0.51.0** — ASGI server with standard extras
- **Gunicorn 26.0.0** — Production WSGI/ASGI process manager

### **Database & ORM**
- **PostgreSQL 15** (production) / **SQLite** (development)
- **SQLAlchemy 2.0.51** — ORM with async support
- **Alembic 1.18.5** — Database migrations
- **asyncpg 0.31.0** — Async PostgreSQL driver
- **psycopg2-binary 2.9.12** — Sync PostgreSQL driver
- **pg8000 1.31.5** — Pure Python PostgreSQL driver
- **DuckDB 1.5.5 + duckdb-engine 0.17.0** — Analytical queries

### **Authentication & Security**
- **python-jose 3.5.0** — JWT encoding/decoding
- **bcrypt 5.0.0** — Password hashing
- **pyotp 2.10.0** — TOTP for 2FA
- **cryptography 49.0.0** — Encryption primitives
- **slowapi 0.1.10** — Rate limiting (with limits 5.8.0)
- **EnhancedSecurityHeadersMiddleware** — CSP, HSTS, security headers
- **CSRFMiddleware** — CSRF protection
- **PCI-DSS compliance middleware** (production)

### **Caching & Session**
- **Redis 8.0.1** — Cache, sessions, rate limiting
- **redis-py 5.x** (implied)

### **Task Queue & Scheduling**
- **APScheduler 3.11.3** — Background job scheduling
- **Custom background job workers** (configurable)

### **Payments & External APIs**
- **Stripe 15.3.1** — Payment processing
- **Stripe Connect** — Marketplace payouts
- **httpx 0.28.1** — Async HTTP client
- **requests 2.34.2** — Sync HTTP client

### **Observability & Monitoring**
- **structlog 26.1.0** — Structured logging
- **OpenTelemetry** (full stack):
  - `opentelemetry-api`, `sdk`, `exporter-otlp-proto-http`
  - `instrumentation-fastapi`, `asgi`, `sqlalchemy`
- **Prometheus** — Metrics via `prometheus-client` + `prometheus-fastapi-instrumentator`
- **Sentry** — Error tracking (`sentry-sdk[fastapi]`)

### **File Handling & Media**
- **aiofiles 25.1.0** — Async file I/O
- **Pillow 12.3.0** — Image processing
- **python-magic 0.4.27** — MIME type detection
- **rembg 2.0.69** — Background removal (AI)
- **opencv-python 5.0.0** — Computer vision
- **onnxruntime 1.23.2** — ML inference

### **Email & Communication**
- **SMTP** via standard library + `email-validator 2.3.0`
- **Twilio** (SMS) — `twilio` not in lockfile but config exists
- **WebSockets** — `websockets 16.1.1` for real-time

### **Utilities & Data Processing**
- **Pydantic 2.13.4** — Validation & settings
- **python-dotenv 1.2.2** — Environment loading
- **python-slugify 8.0.4** — URL slugs
- **pytz 2026.3** / **tzlocal 5.4.4** — Timezone handling
- **babel 2.18.0** — i18n/l10n
- **phonenumbers 9.0.35** — Phone validation
- **faker 40.36.0** — Test data generation
- **numpy, scipy, scikit-image** — Scientific computing
- **python-docx 1.2.0** — Word document generation
- **openpyxl 3.1.5** — Excel handling
- **feedparser 6.0.12** — RSS/Atom parsing
- **schedule 1.2.2** — Simple job scheduling

### **Testing**
- **pytest 9.1.1** + **pytest-asyncio 1.4.0**
- **httpx** for API testing

---

## **Frontend (Next.js 15 / React 19)**

### **Core Framework**
- **Next.js 16.3.1** (App Router, React Server Components)
- **React 18.3.1** / **React DOM 18.3.1**
- **TypeScript 5.8.2** — Strict mode enabled

### **Styling & UI**
- **Tailwind CSS 3.4.19** — Utility-first CSS with custom design system
- **Custom design tokens** — Colors, spacing, typography, shadows, animations
- **class-variance-authority 0.7.1** — Component variant management
- **clsx 2.1.1** — Conditional class names
- **tailwind-merge 3.5.0** — Merge Tailwind classes
- **lucide-react 1.25.0** — Icon library
- **framer-motion 11.5.6** — Animations

### **State Management**
- **Zustand 5.0.11** — Lightweight global state

### **Forms & Validation**
- **React Hook Form** (implied by dependencies)
- **Zod** (implied for schema validation)

### **Payments**
- **@stripe/react-stripe-js 5.6.0**
- **@stripe/stripe-js 8.7.0**

### **Charts & Visualization**
- **chart.js 4.5.1** + **react-chartjs-2 5.3.1**

### **Maps & Location**
- **leaflet 1.9.4** + **react-leaflet 5.0.0**

### **Utilities**
- **jose 6.2.9** — JWT handling in browser
- **dompurify 3.3.3** — XSS sanitization
- **qrcode 1.5.4** — QR code generation
- **jspdf 4.1.0** — PDF generation
- **@zxing/library 0.21.3** — Barcode/QR scanning

### **Testing**
- **Jest 29.7.0** + **ts-jest** + **jest-environment-jsdom**
- **React Testing Library** 16.3.0
- **Playwright 1.61.1** — E2E testing
- **jest-axe 10.0.0** — Accessibility testing

### **Code Quality**
- **ESLint 9** + **TypeScript ESLint** 8.62.0
- **Prettier 3.3.3**
- **eslint-config-next 15.4.5**

### **Build & Deployment**
- **Node.js 20** (Alpine Docker)
- **Multi-stage Docker build** (builder → runner)
- **Next.js rewrites** for API proxying
- **Image optimization** (WebP, remote patterns)

---

## **Infrastructure & DevOps**

### **Containerization**
- **Docker Compose** — Local development stack
- **Multi-stage Dockerfiles** (backend + frontend)
- **PostgreSQL 15-alpine** + **Redis 7-alpine** containers

### **Cloud Deployment**
- **Railway** (backend) — `railway.toml` config
- **Vercel** (frontend) — `vercel.json` config

### **Environment Configuration**
- **Root `.env`** — Docker Compose variables
- **`backend/.env`** — FastAPI settings
- **`frontend/web_app/.env.local`** — Next.js public vars
- **`.env.example`** — Source of truth for required vars

### **Database Migrations**
- **Alembic** with multi-schema support (public, analytics, audit, commerce, etc.)

---

## **Key Architectural Patterns**

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API** | FastAPI + auto-discovered routers | RESTful endpoints with versioning |
| **Auth** | JWT (HS256) + refresh tokens + jti blacklisting | Stateless auth with revocation |
| **Middleware** | 6-layer pipeline (Foundation → Security → Rate Limit → Geo → Observability → Compliance) | Cross-cutting concerns |
| **Database** | SQLAlchemy 2.0 + RLS (Row Level Security) | Multi-tenant data isolation |
| **Caching** | Redis + in-memory | Performance optimization |
| **Real-time** | WebSockets (native + custom manager) | Live updates |
| **Observability** | OpenTelemetry + Prometheus + Sentry + structlog | Full-stack monitoring |

---

## **Shared Package**
- **`@zozi/shared`** — Local NPM package (`frontend/shared`) for TypeScript types, utilities, constants shared between web and mobile
