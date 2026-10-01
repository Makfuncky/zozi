# Production Deployment Guide

## Environment Setup

### Required Environment Variables

```bash
# Core Application
APP_ENV=production
DEBUG=false
SECRET_KEY=<your-secure-secret-key>
ALLOWED_HOSTS=<comma-separated-domains>

# Database (Production PostgreSQL Required)
DATABASE_URL=postgresql://user:password@host:port/database
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_TIMEOUT=30
DB_ECHO=false

# Redis (Caching & Sessions)
REDIS_URL=redis://host:port/db

# Celery
CELERY_BROKER_URL=redis://host:port/db
CELERY_RESULT_BACKEND=redis://host:port/db

# Email
SMTP_HOST=smtp.domain.com
SMTP_PORT=587
SMTP_USER=username
SMTP_PASSWORD=password
SMTP_USE_TLS=true

# Payment Gateways
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring
SENTRY_DSN=https://key@sentry.io/project
```

## Database Configuration

### PostgreSQL Requirements
- **Version**: 14+
- **Connection Pooling**: QueuePool (50 size, 100 overflow)
- **SSL**: Required in production
- **SQLite**: Explicitly rejected at startup in production mode

**Pool Size Validation**:
- Minimum: 10 (production warning if below)
- Maximum: 100 (production warning if above)

### Connection Pool Settings
```python
pool_size = int(os.getenv("DB_POOL_SIZE", 50))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 100))
pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))
pool_recycle = 3600  # 1 hour
pool_pre_ping = True  # Health check on checkout
```

### Health Checks
```bash
# Database connectivity
GET /api/health/database

# Connection pool status
GET /api/health/pool
```

## Deployment Steps

### 1. Pre-deployment Validation
```bash
# Run all tests
pytest tests/ -v --tb=short

# Validate database schema
python -c "from backend.db.database import validate_schema; validate_schema()"

# Check for SQLite in production
python -c "from backend.db.database import validate_production_db; validate_production_db()"
```

### 2. Database Migration
```bash
# Generate migration (if schema changed)
alembic revision --autogenerate -m "description"

# Review migration
alembic show head

# Apply migration
alembic upgrade head

# Verify
alembic current
```

### 3. Application Startup
```bash
# Using Gunicorn
gunicorn backend.app:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile /var/log/gunicorn/access.log \
  --error-logfile /var/log/gunicorn/error.log \
  --log-level info

# Using Uvicorn (for async)
uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### 4. Post-deployment Verification
```bash
# Health check
curl https://your-domain.com/api/health

# Database connection test
curl https://your-domain.com/api/health/database

# Pool status
curl https://your-domain.com/api/health/pool
```

## Monitoring

### Key Metrics to Monitor
1. **Database Connections**: Pool utilization (% of max connections used)
2. **Response Time**: API latency (target < 200ms)
3. **Error Rate**: HTTP 5xx errors (< 1%)
4. **Memory Usage**: Application memory consumption

### Health Endpoints
| Endpoint | Description |
|----------|-------------|
| `/api/health` | Overall application health |
| `/api/health/database` | Database connectivity |
| `/api/health/pool` | Connection pool status |
| `/api/health/redis` | Redis connectivity |

## Rollback Procedure

### If Database Migration Fails
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>

# Restore from backup
pg_restore --dbname=database backup.dump
```

### If Application Fails
```bash
# Stop current processes
pkill -f gunicorn

# Restore previous release
# (Deploy previous git tag or container image)

# Restart application
gunicorn backend.app:app --bind 0.0.0.0:8000
```

## Production Checklist

- [ ] PostgreSQL database created and accessible
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] Load balancer configured
- [ ] CDN configured (if applicable)
- [ ] Rate limiting enabled
- [ ] CORS configured

## Support Contacts

- **Infrastructure**: devops@company.com
- **Database**: dba@company.com
- **Monitoring**: alerts@company.com