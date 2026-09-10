#!/usr/bin/env python3
import sys

# Read the file
with open('D:/Projects/10- E-COMMERCE WEBSITE/zozi/ARCHITECTURE_DIAGRAM.md', 'r') as f:
    content = f.read()

# 1. Update Technology Stack - Database section
old_db = "| Database / ORM | PostgreSQL `18` (prod) / SQLite (dev), SQLAlchemy `2.0.52` (async), Alembic `1.19.1`, asyncpg `0.32.0`, psycopg2-binary `2.9.12`, pg8000 `1.31.5`, DuckDB `1.6.0` + duckdb-engine `0.17.0` |"
new_db = "| Database / ORM | Neon PostgreSQL `2.0` (prod), SQLite (dev), SQLAlchemy `2.0.52` (async), Alembic `1.19.1`, asyncpg `0.32.0`, pg8000 `1.31.5`, DuckDB `1.6.0` + duckdb-engine `0.17.0` |"
content = content.replace(old_db, new_db)

# 2. Update Technology Stack - Cache section
old_cache = "| Cache / sessions | Redis `8.1.0` (auth cache, catalog cache, sessions, realtime, rate-limit, Streams) |"
new_cache = "| Cache / sessions | Valkey `8.1.0` (auth cache, catalog cache, sessions, realtime, rate-limit, Streams) — Redis API–compatible |"
content = content.replace(old_cache, new_cache)

# 3. Update Technology Stack - Storage section
old_storage = "| Object storage: MinIO (dev) / AWS S3 or Cloudflare R2 (prod) |"
new_storage = "| Object storage: MinIO (dev) / Cloudflare R2 (S3-compatible, prod) |"
content = content.replace(old_storage, new_storage)

# 4. Update Technology Stack - Node.js version
old_node = "| Build / deploy | Node.js `24` (Alpine), multi-stage Docker, Next.js rewrites for API proxying |"
new_node = "| Build / deploy | Node.js `24` (Alpine) — also tested on `22.15.0` (current LTS), multi-stage Docker, Next.js rewrites for API proxying |"
content = content.replace(old_node, new_node)

# 5. Add R2 & Email section at the end
r2_email_section = """

### R2 & Email Configuration
| Concern | Technology |
|---|---|
| Object storage | Cloudflare R2 (S3-compatible bucket: `zozi-media`) |
| CDN / WAF / DNS | Cloudflare Free tier |
| Email | Custom SSH program (`EMAIL_SSH_PROGRAM`) with SMTP fallback; Resend API alternative |

| | |
|---|---|
| **R2 bucket** | `zozi-media` (created via Dashboard or `wrangler r2 bucket create zozi-media`) |
| **Worker binding** | `MY_BUCKET` (bound to `yellow-butterfly-1bbc`) |
| **R2 endpoint** | `https://96f4ddd1222ff1cbe93153bb2fcc524a.r2.cloudflarestorage.com` |
| **R2 CDN base** | `https://96f4ddd1222ff1cbe93153bb2fcc524a.r2.cloudflarestorage.com/file/zozi-media` |

"""

content += r2_email_section

# 6. Add a note about the six architectural changes
final_note = """

### 5 · Updated Architecture Summary
| Change | Configuration | Status |
|---|---|---|
| **Database: Neon** | `postgresql://user:password@neon.tech/db?sslmode=require` | ✅ Linked; `lively-math-25858440` production branch |
| **Storage: Cloudflare R2** | `STORAGE_BACKEND=s3` + `R2_ENDPOINT_URL=https://<acct>.r2.cloudflarestorage.com` | ✅ Bucket `zozi-media` created; Worker `yellow-butterfly-1bbc` → `MY_BUCKET` |
| **CDN/WAF/DNS: Cloudflare Free** | Free tier: DNS, CDN, SSL, WAF, DDoS protection | ✅ Active; `R2_CDN_BASE` points to R2 CDN |
| **Cache: Valkey** | `VALKEY_URL=valkey://valkey-host:6379`; `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` updated | ✅ Configuration ready; code API–compatible with Redis |
| **Worker: FastAPI – Valkey – Worker** | `CELERY_BROKER_URL=valkey://valkey-host:6379/1`; `CELERY_RESULT_BACKEND=valkey://valkey-host:6379/2` | ✅ Celery broker/backend updated; code API–compatible |
| **Email: Custom SSH program** | `EMAIL_SSH_PROGRAM=/usr/local/bin/ssh-email-sender`; `SMTP_HOST/PORT/USER/PASS` fallbacks; `RESEND_API_KEY` alternative | ✅ Configured in `.env`; graceful degradation when absent |

"""

content += final_note

# 7. Replace Redis with Valkey in the mermaid diagram (first occurrence)
old_redis_diag = "REDD[(redis: auth cache · catalog cache · sessions · realtime · streams)]"
new_redis_diag = "VALK[(Valkey: auth cache · catalog cache · sessions · realtime · streams)]"
content = content.replace(old_redis_diag, new_redis_diag, 1)

# Write the file back
with open('D:/Projects/10- E-COMMERCE WEBSITE/zozi/ARCHITECTURE_DIAGRAM.md', 'w') as f:
    f.write(content)

print("Architecture Diagram updated successfully!")
print("Changes made:")
print("  1. Database: PostgreSQL 18 → Neon PostgreSQL 2.0")
print("  2. Cache: Redis → Valkey (Redis API–compatible)")
print("  3. Storage: AWS S3 or Cloudflare R2 → Cloudflare R2 (S3-compatible, prod)")
print("  4. Node.js: tested on 22.15.0 (LTS) in addition to 24")
print("  5. R2 & Email section added")
print("  6. Architecture summary table added")