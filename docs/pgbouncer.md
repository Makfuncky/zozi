# PgBouncer — ZOZI Production Deployment Guide

PgBouncer sits between the FastAPI application and PostgreSQL, pooling
client connections so that the database never sees more concurrent
backends than it can comfortably handle.

## Why PgBouncer?

ZOZI runs multiple uvicorn workers, each with its own SQLAlchemy
`QueuePool`. Without a proxy, total connections = `workers × pool_size`.
On a 4-worker deployment with the default `pool_size=20`, Postgres
receives 80+ connections even when most requests are waiting on I/O.

PgBouncer with `pool_mode = transaction` multiplexes those 80 clients
onto a much smaller set of server connections (often 20–40), reducing
Postgres memory pressure and context-switch overhead.

## Architecture

```
FastAPI workers → PgBouncer (transaction pool) → PostgreSQL
```

All app servers point to PgBouncer. No worker talks directly to
Postgres. This also lets you restart Postgres or run failover without
dropping client connections.

## Recommended Configuration

### `pgbouncer.ini`

```ini
[databases]
zozimarketplace = host=postgres port=5432 dbname=zozimarketplace

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 40
min_pool_size = 10
reserve_pool_size = 5
max_db_connections = 100
max_user_connections = 100
server_lifetime = 1800
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
```

### `userlist.txt`

```text
"zozimarketplace" "md5<password_hash>"
```

Generate with:

```bash
psql -c "SELECT usename, passwd FROM pg_shadow WHERE usename='zozimarketplace';"
```

## SQLAlchemy Pool Settings Behind PgBouncer

When `DB_BEHIND_PGBOUNCER=true`, use conservative pool settings to
avoid creating connections that PgBouncer cannot multiplex.

```env
DATABASE_URL=postgresql://zozimarketplace:<password>@pgbouncer:6432/zozimarketplace
DB_BEHIND_PGBOUNCER=true
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=0
DB_POOL_RECYCLE=1800
DB_CONNECT_TIMEOUT=10
DB_SSL_MODE=prefer
```

| Setting            | Value   | Rationale                                              |
|--------------------|---------|--------------------------------------------------------|
| `pool_size`        | 25      | Matches PgBouncer `default_pool_size` for 1:1 mapping   |
| `max_overflow`     | 0       | Overflow bypasses PgBouncer accounting                  |
| `pool_recycle`     | 1800    | Aligns with PgBouncer `server_lifetime`                 |
| `pool_pre_ping`    | False   | PgBouncer `server_check_query` handles stale detection  |
| `pool_timeout`     | 10      | Fails fast if PgBouncer queue is saturated              |

## Docker Compose Example

```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    volumes:
      - ./infra/pgbouncer/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini:ro
      - ./infra/pgbouncer/userlist.txt:/etc/pgbouncer/userlist.txt:ro
    ports:
      - "6432:6432"
    depends_on:
      - postgres
    environment:
      - DATABASES_HOST=postgres
      - DATABASES_PORT=5432
      - DATABASES_USER=zozimarketplace
      - DATABASES_DBNAME=zozimarketplace
      - DATABASES_PASSWORD=<secure_password>
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: zozimarketplace
      POSTGRES_USER: zozimarketplace
      POSTGRES_PASSWORD: <secure_password>
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://zozimarketplace:<password>@pgbouncer:6432/zozimarketplace
      DB_BEHIND_PGBOUNCER: "true"
    depends_on:
      - pgbouncer
```

## Transaction Pooling Caveats

PgBouncer `pool_mode = transaction` is safe for standard ORM usage but
breaks apps that rely on session-level state:

- `SET` statements expected to persist for the session
- Temporary tables (`CREATE TEMP TABLE`)
- Advisory locks held across transactions
- `LISTEN / NOTIFY` subscriptions per session
- Driver-side prepared-statement caching across transactions

ZOZI avoids these patterns. If a dependency introduces them, switch to
`pool_mode = session` or refactor the dependency.

## Monitoring

### PgBouncer Admin Console

```bash
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "SHOW POOLS;"
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "SHOW STATS;"
```

Watch `cl_waiting` in `SHOW POOLS`. Non-zero values mean clients are
queued waiting for a server connection.

### Prometheus Exporter

Use `prom-pgbouncer-exporter` or scrape via:

```bash
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer -c "SHOW STATS;" \
  | prom-pgbouncer-exporter
```

### Alert Thresholds

```yaml
- alert: PgBouncerWaitQueue
  expr: pgbouncer_cl_waiting > 0
  for: 2m
  annotations:
    summary: "Clients waiting for PgBouncer server connections"

- alert: PgBouncerServer saturated
  expr: pgbouncer_active_server_connections / pgbouncer_server_connections > 0.9
  for: 5m
  annotations:
    summary: "PgBouncer server connections near exhaustion"
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `cl_waiting` > 0 | `default_pool_size` too small | Increase `default_pool_size` |
| `server_check_query` errors | `pool_pre_ping=True` in SQLAlchemy | Set `pool_pre_ping=False` |
| Auth failures | `auth_file` missing or stale | Regenerate `userlist.txt` |
| High `maxwait` | Slow queries exhausting servers | Tune queries or add `server_idle_timeout` |
