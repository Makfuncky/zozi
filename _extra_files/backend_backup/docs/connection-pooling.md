# Connection Pooling — ZOZI Backend

## Current QueuePool Settings

Located in `backend/db/database.py`, the engine is configured via environment-driven parameters:

```python
# backend/db/database.py
_pool_kwargs = {
    "pool_size": settings.db_pool_size,        # default 20
    "max_overflow": settings.db_max_overflow,  # default 30
    "pool_recycle": settings.db_pool_recycle,  # default 1800s (30 min)
    "pool_pre_ping": True,
    "pool_timeout": settings.db_connect_timeout, # default 10s
}
```

| Setting            | Default | Meaning                                          |
|--------------------|---------|--------------------------------------------------|
| `pool_size`        | 20      | Persistent connections per process               |
| `max_overflow`     | 30      | Extra connections allowed when pool is exhausted |
| `pool_recycle`     | 1800    | Max age of a connection before forced renewal    |
| `pool_pre_ping`    | True    | `SELECT 1` on checkout to detect stale DB links  |
| `pool_timeout`     | 10      | Max wait (seconds) for a free connection         |

These are `QueuePool` settings designed for direct PostgreSQL connections. When routing through PgBouncer, see **PgBouncer transaction pooling best practices** below.

---

## SQLite (Development) vs PostgreSQL (Production)

### SQLite (Development)

```python
# backend/db/database.py
if _IS_SQLITE:
    poolclass = StaticPool
    _pool_kwargs = {}
```

SQLite uses `StaticPool`, which reuses a single connection across all threads. This is safe in development because:

- SQLite has file-level locking (enforced via `WAL` + `busy_timeout` pragmas).
- There is no network round-trip overhead.
- Connection reuse avoids the overhead of opening a new file handle per request.

Tuning pragmas applied to every SQLite connection:

```python
PRAGMA journal_mode=WAL       # Allow concurrent readers
PRAGMA synchronous=NORMAL     # Balance durability and speed
PRAGMA busy_timeout=5000       # Wait up to 5s for locks
PRAGMA cache_size=-32000       # 32 MB page cache
PRAGMA temp_store=MEMORY       # Keep temp tables in memory
PRAGMA mmap_size=67108864      # 64 MB memory-mapped I/O
```

### PostgreSQL (Production)

```python
# backend/db/database.py
if _IS_POSTGRES:
    poolclass = QueuePool
    _pool_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,
        "pool_timeout": settings.db_connect_timeout,
    }
```

#### Direct Postgres (no PgBouncer)

Recommended settings when connecting directly:

| Setting            | Recommendation                     |
|--------------------|------------------------------------|
| `pool_size`        | 20–30 per uvicorn worker          |
| `max_overflow`     | 0 (let Kubernetes / process manager scale horizontally) |
| `pool_recycle`     | 1800 (align with Postgres `idle_in_transaction_session_timeout`) |
| `pool_pre_ping`    | True (detect network blips)        |
| `pool_timeout`     | 10                                 |

Compute total connection budget:

```
Total = workers × pool_size + overflow headroom
Example: 4 workers × 25 + 0 = 100 connections
```

Ensure Postgres `max_connections` (default 100) accommodates this plus headroom for migrations, psql, monitoring, etc.

#### Postgres Behind PgBouncer

When PgBouncer sits between SQLAlchemy and Postgres:

| Setting            | Recommendation                     |
|--------------------|------------------------------------|
| `pool_size`        | 10–25 per uvicorn worker          |
| `max_overflow`     | 0 (PgBouncer counts per-connection; overflow bypasses PgBouncer accounting) |
| `pool_recycle`     | 1800                               |
| `pool_pre_ping`    | False (PgBouncer's `server_check_query` handles stale connections) |
| `pool_timeout`     | 10                                 |

Set `DB_BEHIND_PGBOUNCER=true` to activate the conservative profile in `database.py`.

---

## PgBouncer Transaction Pooling Best Practices

PgBouncer's `pool_mode = transaction` is the right choice for ORMs because:

- It reuses a server connection only between transactions, not between statements within a transaction.
- It avoids session-level state leaking across requests.
- It maximizes connection multiplexing.

However, **transaction pooling is incompatible** with:

- `SET` statements that expect to persist for the session.
- Temporary tables (`CREATE TEMP TABLE`) that must survive the transaction.
- Advisory locks held across transactions.
- `LISTEN / NOTIFY` channels used as session-level subscriptions.
- `PREPARE` statements cached by the driver across transactions.

If your app or libraries use any of these, switch to:

```ini
pool_mode = session
```

But note: `session` mode ties each client to one server connection for the entire session lifetime, drastically reducing PgBouncer's effectiveness. Prefer fixing the app to avoid session state.

---

## How to Verify Pool Health

### 1. SQLAlchemy Pool Metrics

ZOZI exposes pool metrics via `get_pool_metrics()` in `backend/db/database.py`:

```python
from db.database import get_pool_metrics

print(get_pool_metrics())
# {'size': 25, 'checkedin': 20, 'checkedout': 5, 'overflow': 0}
```

Hook this into a health endpoint:

```python
# backend/api/health.py (example)
from fastapi import APIRouter
from db.database import get_pool_metrics, check_connection_health

router = APIRouter()

@router.get("/health/db")
def db_health():
    return {
        "connected": check_connection_health(),
        **get_pool_metrics(),
    }
```

Watch for:

- `checkedout` consistently near `pool_size` → pool is undersized; increase `DB_POOL_SIZE`.
- `overflow` > 0 → `max_overflow` is being hit; consider scaling horizontally or increasing pool.
- `checkedin` = 0 and `checkedout` = `pool_size` under load → healthy saturation; if requests queue, raise pool.

### 2. Postgres Server-Side View

From psql connected to Postgres directly (bypassing PgBouncer):

```sql
SELECT count(*) AS total_backends,
       count(*) FILTER (WHERE state = 'active') AS active,
       count(*) FILTER (WHERE state = 'idle') AS idle,
       count(*) FILTER (WHERE wait_event_type = 'Lock') AS waiting
FROM pg_stat_activity
WHERE datname = 'zozimarketplace';
```

Healthy patterns:

- `idle` connections near `default_pool_size × workers` is expected.
- `active` spikes correlate with traffic; sustained 100% active with query queueing means the app pool needs to grow.

### 3. PgBouncer Admin Console

```bash
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "SHOW POOLS;"
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "SHOW STATS;"
```

Watch the output of `SHOW POOLS` for `cl_waiting`. Any non-zero value means requests are blocked waiting for a PgBouncer server connection, indicating you should raise `default_pool_size` or investigate slow queries.

### 4. /metrics (Prometheus)

If Prometheus scraping is enabled, add a gauge for pool metrics:

```python
from prometheus_client import Gauge

db_pool_checkedin = Gauge("db_pool_checkedin", "Checked-in SQLAlchemy connections")
db_pool_checkedout = Gauge("db_pool_checkedout", "Checked-out SQLAlchemy connections")
db_pool_overflow = Gauge("db_pool_overflow", "Overflow SQLAlchemy connections")

def export_pool_metrics():
    m = get_pool_metrics()
    db_pool_checkedin.set(m.get("checkedin", 0))
    db_pool_checkedout.set(m.get("checkedout", 0))
    db_pool_overflow.set(m.get("overflow", 0))
```

Alert thresholds:

```yaml
# prometheus/alert_rules.yml
- alert: DbPoolExhausted
  expr: db_pool_checkedout / (db_pool_size + db_pool_overflow) > 0.9
  for: 5m
  annotations:
    summary: "SQLAlchemy connection pool near exhaustion"

- alert: PgBouncerWaitQueue
  expr: pgbouncer_cl_waiting > 0
  for: 2m
  annotations:
    summary: "Clients waiting for PgBouncer server connections"
```

---

## Quick Reference: Environment Variables

```env
# backend/.env
POSTGRES_DB=zozimarketplace
POSTGRES_USER=zozimarketplace
POSTGRES_PASSWORD=<secure_password>

DATABASE_URL=postgresql://zozimarketplace:<secure_password>@pgbouncer:6432/zozimarketplace
DB_BEHIND_PGBOUNCER=true
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=0
DB_POOL_RECYCLE=1800
DB_CONNECT_TIMEOUT=10
DB_SSL_MODE=prefer
```
