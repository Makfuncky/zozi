"""ZOZI Forensic Audit — Canonical constants derived from benchmark docs.

All constants are derived from ARCHITECTURE_STACK.md and TECHNOLOGY_STACK.md
at runtime via parsers in zz_scanners/s02_technology.py and zz_scanners/s08_laws.py.
Embedded fallbacks are used only when parsing fails.
"""

from __future__ import annotations

from pathlib import Path

# Law 13: exactly 5 modules
CANONICAL_MODULES: set[str] = {"admin", "customer", "employee", "logistics", "supplier"}

# Law 12: exactly 15 domains
CANONICAL_DOMAINS: set[str] = {
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "country",
    "customers",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "promotions",
    "security",
    "suppliers",
}

# Law 1: `modules/` routers may import these `infrastructure/` subpackages.
# A router may reach the RBAC gates (Laws 87/88), the SET-LOCAL RLS helpers
# (Law 227), the pagination/config/currency plumbing and the Pydantic DTOs
# (transport). Anything else from `infrastructure` in a router is a bypass.
#
# This lives here, not in the scanner, because the PROBE needs the identical
# list. When the two had separate copies the probe omitted it and refuted every
# genuine `module-imports-infrastructure` finding: the probe asked "is
# `infrastructure` allowed for `modules`?" against the coarse layer table, which
# says yes, while the detector asks the finer question "is THIS subpackage
# allowed?", which is where the finding actually came from.
ROUTER_OK_INFRA: tuple[str, ...] = (
    "infrastructure.security",
    "infrastructure.utils.country_rls",
    "infrastructure.utils.auth",
    "infrastructure.utils.config",
    "infrastructure.utils.currency_service",
    "infrastructure.utils.pagination",
    "infrastructure.utils.invoice_html",
    "infrastructure.utils.background_jobs",
    "infrastructure.database.rls_interceptor",
    "infrastructure.database.schemas",
)

# Approved extra schemas (ARCH §8)
APPROVED_EXTRA_SCHEMAS: set[str] = {"media", "treasury", "ai", "configuration"}

# Forbidden schemas (Laws 24/56)
FORBIDDEN_SCHEMAS: set[str] = {"core", "platform", "identity"}

# Canonical top-level entries at backend/ root (ARCH §3, "Canonical top-level packages")
CANONICAL_BACKEND_ROOT_ENTRIES: set[str] = {
    "main.py",
    "config.py",
    "DOMAIN_ALLOWLIST.yaml",
    "modules",
    "domains",
    "rbac",
    "kernel",
    "infrastructure",
    "providers",
    "jobs",
    "middleware",
    "alembic",
    "scripts",
    "tests",
}

CANONICAL_TOPLEVEL: set[str] = CANONICAL_BACKEND_ROOT_ENTRIES

# Forbidden root dirs (Law 18)
FORBIDDEN_ROOT_DIRS: set[str] = {"utils", "routers", "controllers", "services", "models", "db"}

# Canonical provider subpackages (ARCH §3)
CANONICAL_PROVIDER_DIRS: set[str] = {
    "ai",
    "barcode",
    "bg_removal",
    "comms",
    "finance",
    "geography",
    "image",
    "ocr",
    "payments",
    "qr",
    "security",
    "shipping",
    "storage",
    "async_workers",
}

# Known non-canonical provider subpackages (observed in codebase)
KNOWN_PROVIDER_EXTRAS: set[str] = {"news", "automation", "scanner", "voice", "analytics", "auth", "http", "ml", "redis", "uploads"}

# Forbidden Python packages (TECH §5, §6, §8, §11)
FORBIDDEN_PY_PACKAGES: set[str] = {
    "psycopg",
    "psycopg2",
    "psycopg2-binary",
    "python-jose",
    "jose",
    "pytz",
    "tzlocal",
    "python-magic",
    "prometheus-client",
    "paypal-payments-sdk",
    "requests",
    "slowapi",
    "limits",
}

# Unapproved alternatives (not forbidden, but not chosen)
UNAPPROVED_ALTERNATIVES: set[str] = {"slowapi", "limits"}

# Forbidden JS packages
FORBIDDEN_JS_PACKAGES: set[str] = {
    "@tanstack/react-query",
    "swr",
    "react-router-dom",
}

# Canonical middleware order (Law 78)
MIDDLEWARE_ORDER: list[str] = [
    "foundation",
    "auth",
    "rate_limit",
    "webhook",
    "geo",
    "security",
    "observability",
    "compliance",
]

# Required audit columns on every model (Law 23)
SCHEMA_REQUIRED_COLUMNS: tuple[str, ...] = ("created_at", "updated_at", "country_code", "is_deleted")

# Hints for money-type fields
MONEY_FIELD_HINTS: set[str] = {
    "amount",
    "price",
    "total",
    "subtotal",
    "tax",
    "vat",
    "commission",
    "fee",
    "balance",
    "payout",
    "refund",
    "discount",
    "shipping_cost",
    "rate",
    "salary",
    "wage",
}

# Phase ordering for the compiler
PHASES: list[str] = [
    "emergency",
    "boot",
    "tech",
    "db",
    "logic",
    "arch",
    "security",
    "payment",
    "compliance",
    "frontend",
    "mobile",
    "testing",
    "infra",
    "docs",
    "defer",
]

# Dimension ID -> name (28 dimensions, ordered)
DIMENSIONS: list[tuple[str, str]] = [
    ("01", "architectural"),
    ("02", "technological"),
    ("03", "logical"),
    ("04", "operational"),
    ("05", "wiring"),
    ("06", "database"),
    ("07", "tables_fields"),
    ("08", "providers"),
    ("09", "laws"),
    ("10", "migrations"),
    ("11", "environmental"),
    ("12", "tests"),
    ("13", "dev_to_prod"),
    ("14", "frontend_web"),
    ("15", "frontend_mobile"),
    ("16", "features"),
    ("17", "code_file_management"),
    ("18", "security"),
    ("19", "performance"),
    ("20", "observability_resilience"),
    ("21", "contradictions"),
    ("22", "anti_patterns"),
    ("23", "code_intent"),
    ("24", "browser_behavior"),
    ("25", "ai_drift"),
    ("26", "code_alignment"),
    ("27", "project_completion_blockers"),
    ("28", "supply_chain_security"),
    # 29/30 were added with the law-coverage work. `23_law_coverage` and
    # `24_declared_laws` are both about the AUDIT's own coverage rather than a
    # product area, and numbering them 23/24 collided with existing dimensions --
    # `--dimensions 24` silently selected `24_browser_behavior` and the new checks
    # never ran.
    ("29", "law_coverage"),
    ("30", "declared_laws"),
]

# 28-dimension prefix map
DIMENSION_PREFIXES: dict[str, str] = {
    "01": "ARCH",
    "02": "TECH",
    "03": "LOGIC",
    "04": "OPS",
    "05": "WIRE",
    "06": "DB",
    "07": "TF",
    "08": "PROV",
    "09": "LAW",
    "10": "MIG",
    "11": "ENV",
    "12": "TEST",
    "13": "D2P",
    "14": "WEB",
    "15": "MOB",
    "16": "FEAT",
    "17": "FILE",
    "18": "SEC",
    "19": "PERF",
    "20": "OBS",
    "21": "CONTRAD",
    "22": "AP",
    "23": "INTENT",
    "24": "BROWSER",
    "25": "DRIFT",
    "26": "ALIGN",
    "27": "BLOCK",
    "28": "SC",
    "29": "LAWCOV",
    "30": "DECLLAW",
}

# Human labels used in the report headings ("## Dimension 01 · Architectural")
DIMENSION_LABELS: dict[str, str] = {
    "01_architectural": "01 · Architectural",
    "02_technological": "02 · Technological",
    "03_logical": "03 · Logical",
    "04_operational": "04 · Operational",
    "05_wiring": "05 · Wiring",
    "06_database": "06 · Database",
    "07_tables_fields": "07 · Tables Fields",
    "08_providers": "08 · Providers",
    "09_laws": "09 · Laws",
    "10_migrations": "10 · Migrations",
    "11_environmental": "11 · Environmental",
    "12_tests": "12 · Tests",
    "13_dev_to_prod": "13 · Dev To Prod",
    "14_frontend_web": "14 · Frontend Web",
    "15_frontend_mobile": "15 · Frontend Mobile",
    "16_features": "16 · Features",
    "17_code_file_management": "17 · Code File Management",
    "18_security": "18 · Security",
    "19_performance": "19 · Performance",
    "20_observability_resilience": "20 · Observability Resilience",
    "21_contradictions": "21 · Contradictions",
    "22_anti_patterns": "22 · Anti Patterns",
    "23_code_intent": "23 · Code Intent",
    "24_browser_behavior": "24 · Browser Behavior",
    "25_ai_drift": "25 · Ai Drift",
    "26_code_alignment": "26 · Code Alignment",
    "27_project_completion_blockers": "27 · Project Completion Blockers",
    "28_supply_chain_security": "28 · Supply Chain Security",
    "29_law_coverage": "29 · Law Coverage",
    "30_declared_laws": "30 · Declared Laws",
}

# dimension key -> finding-ID prefix
ID_PREFIX_BY_DIMENSION: dict[str, str] = {
    f"{num}_{name}": DIMENSION_PREFIXES[num] for num, name in DIMENSIONS
}

# --------------------------------------------------------------------------- #
# Benchmark-document loader
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOC_DIR = _REPO_ROOT / "_most_imp_docx"
_DOC_CACHE: dict[str, str] = {}


def load_doc(name: str) -> str:
    """Read a canonical benchmark document from ``_most_imp_docx/``.

    Returns ``""`` when the document is absent so callers can fall back to the
    embedded constants instead of crashing the audit.
    """
    if name in _DOC_CACHE:
        return _DOC_CACHE[name]
    path = _DOC_DIR / name
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        text = ""
    _DOC_CACHE[name] = text
    return text


# --------------------------------------------------------------------------- #
# Version pins (fallback only — s02 parses TECHNOLOGY_STACK.md at runtime)
# --------------------------------------------------------------------------- #

PY_VERSION_PINS_FALLBACK: dict[str, str] = {
    # §1 Runtime & Framework
    "python": "3.13.x", "fastapi": "0.141.x", "starlette": ">=1.6.0,<1.7.0",
    "uvicorn": "0.35.0+", "uvloop": "0.21.0", "httptools": "0.7.0",
    "gunicorn": "26.0.0", "anyio": "4.15.1", "pydantic": "2.13.4",
    "pydantic-settings": "2.9.1+", "python-multipart": "0.0.32",
    "email-validator": "2.3.0",
    # §2 Database & Migrations
    "asyncpg": "0.31.0", "sqlalchemy": "2.0.52", "alembic": "1.19.1+",
    # §4 Storage & Media
    "aiofiles": "25.1.0", "pillow": "12.2.0", "puremagic": "2.2.0",
    "python-slugify": "8.0.4", "rembg": "2.0.69", "opencv-python": "5.0.0",
    "onnxruntime": "1.23.2", "fastembed": "0.4.0+",
    # §5 Auth, Crypto & Rate Limiting
    "pyjwt": "2.13.0+", "bcrypt": "5.0.0", "pyotp": "2.10.0",
    "cryptography": "50.0.1", "fastapi-limiter-valkey": "latest stable",
    "pybreaker": "1.4.1",
    # §6 HTTP Clients & External APIs
    "httpx": "0.28.1", "stripe": "15.5.1", "ollama": "0.6.2+",
    "feedparser": "6.0.12", "phonenumbers": "9.0.35",
    # §8 i18n, Money & Documents
    "py-moneyed": "3.0+", "python-docx": "1.2.0", "openpyxl": "3.1.5",
    # §9 Observability & Logging
    "structlog": "26.1.0", "sentry-sdk": "2.68.1",
    "prometheus-fastapi-instrumentator": "8.1.0+",
    # §10 Testing
    "pytest": "9.1.1", "pytest-asyncio": "1.4.0", "pytest-xdist": "3.6.1+",
    "pytest-cov": "6.0.0+", "respx": "0.23.1+", "factory-boy": "3.3.3",
    "websockets": "16.1.1+", "testcontainers": "4.15.0+",
    # §11 Code Quality & Security Scanning
    "ruff": "0.16.6+", "mypy": "1.14.1+", "import-linter": "2.14+",
    "pre-commit": "4.2.0+", "gitleaks": "8.21.2+", "pip-audit": "2.10.1+",
    "trivy": "0.74.0+", "cosign": "2.6.3+",
}

JS_VERSION_PINS_FALLBACK: dict[str, str] = {
    # §12 Frontend framework, build & language
    "next": "16.3.5", "react": "19.2.8", "typescript": "5.9.3",
    "pnpm": "10.x+", "node": "22.12.0", "sharp": "0.35.4",
    # §13 UI, Styling & Components
    "tailwindcss": "4.3.3", "cva": "0.7.1", "clsx": "2.1.1",
    "tailwind-merge": "3.5.0", "lucide-react": "0.563.0",
    "motion": "13.2.0+", "@zxing/library": "0.21.3", "qrcode": "1.5.4",
    "dompurify": "3.4.0", "chart.js": "4.5.1", "react-chartjs-2": "5.3.1",
    "leaflet": "1.9.4", "react-leaflet": "5.0.0", "jspdf": "4.2.1",
    "jose": "6.2.10",
    # §14 State, Forms & Data
    "zustand": "5.0.14", "react-hook-form": "7.84.0", "zod": "4.3.6",
    "@hookform/resolvers": "5.2.2", "next-intl": "4.14.2",
    # §15 Payments, Errors & Testing
    "@stripe/react-stripe-js": "6.9.0", "@stripe/stripe-js": "5.5.0+",
    "@sentry/nextjs": "9.x+", "jest": "29.7.0", "ts-jest": "29.2.5",
    "@testing-library/react": "16.3.0", "jest-axe": "10.0.0",
    "@playwright/test": "1.62.1+", "detox": "20.0.0+",
    "eslint": "10", "typescript-eslint": "8.62.0", "prettier": "3.3.3",
    # §16 Mobile
    "expo": "57.0.20+", "react-native": "0.86.3", "expo-router": "57.0.19",
    "expo-secure-storage": "14.2.3", "lucide-react-native": "0.563.0",
    "react-native-maps": "1.29.0",
}

# File-name substrings that mark a module as money-critical (Law 19)
MONEY_FILE_HINTS: tuple[str, ...] = (
    "finance", "payout", "commission", "tax", "vat", "billing", "invoice",
    "refund", "treasury", "payment", "checkout", "cart", "price", "money",
    "wallet", "settlement", "ledger", "accounting", "currency",
)

# --------------------------------------------------------------------------- #
# Environment variables (TECHNOLOGY_STACK §20)
# --------------------------------------------------------------------------- #

# Secret=YES *and* Required=Prod in the §20 table
REQUIRED_PROD_ENV: set[str] = {
    "SECRET_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "TAP_SECRET_KEY",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "FIELD_ENCRYPTION_KEY",
    "AUDIT_CHAIN_KEY",
    "KMS_ENCRYPTION_KEY",
    "HASH_SALT",
    # deprecated aliases that still resolve in backend/config.py
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "ENCRYPTION_KEY",
}

# alias -> canonical name (§20 marks these "Deprecated")
DEPRECATED_ENV_ALIASES: dict[str, str] = {
    "REDIS_URL": "VALKEY_URL",
    "S3_BUCKET": "R2_BUCKET",
    "S3_REGION": "R2_REGION",
    "S3_ENDPOINT_URL": "R2_ENDPOINT_URL",
    "S3_CDN_BASE": "R2_CDN_BASE",
    "S3_ACCESS_KEY_ID": "R2_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY": "R2_SECRET_ACCESS_KEY",
    "S3_PRESIGN_TTL_SECONDS": "R2_PRESIGN_TTL_SECONDS",
    "ENCRYPTION_KEY": "FIELD_ENCRYPTION_KEY",
}
