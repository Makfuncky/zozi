# ZOZI Database Backup Strategy

**Version:** 1.0  
**Date:** 2026-09-01  
**Status:** Implementation Ready  
**Laws:** 232 (Backup & Recovery), 307 (Backup Verify)

---

## 1. Executive Summary

This document defines the comprehensive backup strategy for the ZOZI e-commerce platform's NEON 15 production database. The strategy ensures **zero data loss** capability through daily full backups combined with continuous WAL (Write-Ahead Log) archiving for point-in-time recovery (PITR).

### Current State Assessment

| Aspect | Status | Risk |
|--------|--------|------|
| Database | NEON 15, ~318 tables | — |
| Existing backups | ❌ None | **Critical** |
| WAL archiving | ❌ Not configured | **High** |
| Off-site storage | ❌ None | **High** |
| Restore testing | ❌ Never performed | **Critical** |
| Monitoring | ❌ No backup alerts | **Medium** |

### Target State

| Aspect | Target | RTO | RPO |
|--------|--------|-----|-----|
| Full backups | Daily at 02:00 UTC | — | 24h |
| WAL archiving | Continuous | — | ~5 min |
| Point-in-time recovery | Any time within retention | 30 min | 5 min |
| Off-site replication | R2-compatible storage | — | 24h |
| Retention | 30 days local + 90 days R2 | — | — |
| Restore testing | Daily automated drill | — | — |

---

## 2. Architecture

### 2.1 Backup Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZOZI Production Environment                  │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Nginx   │───▶│  Backend │───▶│ PgBouncer│───▶│    DB    │  │
│  │  (LB)    │    │ (3 reps) │    │ (pooler) │    │(Primary) │  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│                                                        │        │
│                                               WAL Archive      │
│                                                        │        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │        │
│  │  Backup  │───▶│  Monitor │───▶│  Alert   │         │        │
│  │  Service │    │  Service │    │ Manager  │         │        │
│  └────┬─────┘    └──────────┘    └──────────┘         │        │
│       │                                                │        │
│       ▼                                                ▼        │
│  ┌──────────┐                                  ┌──────────┐    │
│  │  Local   │                                  │   WAL    │    │
│  │ Backups  │                                  │ Archive  │    │
│  │ (30 day) │                                  │ (30 day) │    │
│  └────┬─────┘                                  └──────────┘    │
│       │                                                         │
└───────┼─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Off-Site Storage (R2)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  s3://zozi-backups/                                       │   │
│  │  ├── daily/                                               │   │
│  │  │   ├── zozi_daily_20260901_020000.pgdump               │   │
│  │  │   ├── zozi_daily_20260901_020000.pgdump.meta.json    │   │
│  │  │   └── ...                                              │   │
│  │  └── weekly/                                              │   │
│  │      └── zozi_weekly_20260831_020000.pgdump              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Docker Compose Services

The production stack now includes:

| Service | Image | Purpose | Resources |
|---------|-------|---------|-----------|
| `db` | postgres:18-alpine | Primary database with WAL archiving | 2 CPU, 2GB RAM |
| `pgbouncer` | edoburu/pgbouncer | Connection pooling | 0.5 CPU, 512MB |
| `backend` | zozi-backend | FastAPI application (3 replicas) | 2 CPU, 2GB each |
| `backup` | zozi-backend | Backup cron + scripts | 0.5 CPU, 512MB |
| `redis` | redis:7-alpine | Cache + sessions | 0.5 CPU, 512MB |

### 2.3 Volumes

| Volume | Path | Purpose | Size Estimate |
|--------|------|---------|---------------|
| `postgres_data` | `/var/lib/postgresql/data` | Database files | 50-100GB |
| `wal_archive` | `/wal_archive` | WAL segment archives | 10-20GB |
| `backups` | `/backups` | Compressed backup files | 20-50GB |
| `redis_data` | `/data` | Valkey persistence | 1-2GB |

---

## 3. Backup Procedures

### 3.1 Daily Full Backups

**Schedule:** Every day at 02:00 UTC (low-traffic window)  
**Method:** `pg_dump -Fc` (custom compressed format)  
**Retention:** 30 days local, 90 days R2

```bash
# Automated via cron in backup container
0 2 * * * /app/scripts/pg_backup.py --type daily
```

**Process:**
1. `pg_dump -Fc` creates a consistent snapshot without locking
2. Backup is verified with `pg_restore --list`
3. Metadata sidecar is written (`.meta.json`)
4. Backup is uploaded to R2 (if configured)
5. Old backups beyond retention are rotated

**Estimated backup size:** 5-15 GB (compressed, depends on data volume)  
**Estimated duration:** 15-45 minutes (depends on data volume)

### 3.2 WAL Archiving (Continuous)

**Schedule:** Continuous (triggered by NEON)  
**Method:** `archive_command` copies WAL segments to archive  
**Retention:** 30 days

```sql
-- NEON configuration
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /wal_archive/%f && cp %p /wal_archive/%f'
archive_timeout = 300  -- Force archive every 5 minutes
wal_keep_size = 1024   -- Keep at least 1GB of WAL files
```

**Process:**
1. NEON writes all changes to WAL segments
2. When a segment is full (16MB) or `archive_timeout` elapses, NEON calls `archive_command`
3. The segment is copied to `/wal_archive/`
4. WAL segments older than retention are rotated

**Estimated WAL volume:** 2-5 GB per day (depends on write volume)

### 3.3 Weekly Full Backups (Optional)

**Schedule:** Every Sunday at 03:00 UTC  
**Method:** Same as daily, but tagged as "weekly"  
**Retention:** 90 days on R2

```bash
0 3 * * 0 /app/scripts/pg_backup.py --type weekly
```

---

## 4. Restore Procedures

### 4.1 Full Restore (from daily backup)

**Use case:** Complete database recovery after catastrophic failure

```bash
# 1. Stop application services
docker compose stop backend ml_worker

# 2. Drop and recreate the database
docker compose exec db psql -U zozi -c "DROP DATABASE IF EXISTS zozi;"
docker compose exec db psql -U zozi -c "CREATE DATABASE zozi;"

# 3. Restore from backup
docker compose exec backup pg_restore \
  -h db -U zozi -d zozi \
  --verbose --no-owner --no-privileges \
  /backups/zozi_daily_20260901_020000.pgdump

# 4. Verify restore
docker compose exec db psql -U zozi -d zozi -c "SELECT count(*) FROM information_schema.tables;"

# 5. Restart application
docker compose start backend ml_worker
```

**Estimated time:** 30-60 minutes

### 4.2 Point-in-Time Recovery (PITR)

**Use case:** Recover to a specific moment (e.g., before accidental deletion)

```bash
# 1. Stop NEON
docker compose stop db

# 2. Move current data directory
mv /var/lib/postgresql/data /var/lib/postgresql/data.old

# 3. Restore base backup to data directory
pg_restore -h localhost -U zozi -d zozi /backups/zozi_daily_20260901_020000.pgdump

# 4. Create recovery configuration
cat > /var/lib/postgresql/data/postgresql.auto.conf << EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '2026-09-01 14:30:00 UTC'
recovery_target_action = 'promote'
EOF

# 5. Create recovery signal
touch /var/lib/postgresql/data/recovery.signal

# 6. Start NEON (will recover to target time, then promote)
docker compose start db
```

**Estimated time:** 30-90 minutes (depends on WAL replay volume)

### 4.3 Selective Restore (single table)

**Use case:** Recover a specific table without full restore

```bash
# Restore single table to a temporary database
createdb -h db -U zozi temp_restore
pg_restore -h db -U zozi -d temp_restore \
  --table=orders \
  /backups/zozi_daily_20260901_020000.pgdump

# Export and import the specific data
pg_dump -h db -U zozi -d temp_restore --table=orders | \
  psql -h db -U zozi -d zozi

# Clean up
dropdb -h db -U zozi temp_restore
```

### 4.4 Daily Restore Drill (Automated)

**Schedule:** Every day at 06:00 UTC  
**Method:** Restore to temporary database, verify, clean up

```bash
# Automated via cron
0 6 * * * /app/scripts/pg_backup.py --restore-drill
```

**Process:**
1. Find latest backup
2. Create temporary database `zozi_restore_drill_<timestamp>`
3. Restore backup to temporary database
4. Verify table count and row counts
5. Drop temporary database
6. Log results and update metadata

---

## 5. Storage Requirements

### 5.1 Local Storage

| Component | Daily | 30-Day Total | Notes |
|-----------|-------|--------------|-------|
| Full backups | 5-15 GB | 150-450 GB | Compressed with pg_dump -Fc |
| WAL archives | 2-5 GB | 60-150 GB | 16MB segments |
| Metadata | <1 MB | <30 MB | JSON sidecars |
| **Total** | **7-20 GB** | **210-600 GB** | Plan for 1TB |

### 5.2 R2 Off-Site Storage

| Component | Daily | 90-Day Total | Storage Class |
|-----------|-------|--------------|---------------|
| Daily backups | 5-15 GB | 450-1350 GB | STANDARD |
| Weekly backups | 5-15 GB | 60-180 GB | STANDARD_IA |
| **Total** | **40-105 GB** | **510-1530 GB** | — |

### 5.3 Cost Estimate (R2)

| Storage | Amount | Cost/GB/Month | Monthly Cost |
|---------|--------|---------------|--------------|
| STANDARD | 450 GB | $0.023 | $10.35 |
| STANDARD_IA | 60 GB | $0.0125 | $0.75 |
| **Total** | **510 GB** | — | **~$11/month** |

*Costs based on AWS R2 pricing. R2-compatible providers (R2, DO) may be cheaper.*

---

## 6. Monitoring & Alerting

### 6.1 Prometheus Metrics

The backup service exposes the following metrics on port 9100:

| Metric | Type | Description |
|--------|------|-------------|
| `zozi_backup_latest_age_hours` | gauge | Age of latest backup |
| `zozi_backup_latest_size_bytes` | gauge | Size of latest backup |
| `zozi_backup_count` | gauge | Total backup count |
| `zozi_backup_verified` | gauge | Latest backup verified (1=yes) |
| `zozi_wal_archive_count` | gauge | WAL archive file count |
| `zozi_wal_latest_age_minutes` | gauge | Age of latest WAL archive |
| `zozi_backup_disk_free_bytes` | gauge | Free space on backup disk |
| `zozi_wal_disk_free_bytes` | gauge | Free space on WAL disk |
| `zozi_backup_health` | gauge | Overall health (1=healthy) |

### 6.2 Alert Rules

| Alert | Condition | Severity | Response |
|-------|-----------|----------|----------|
| `BackupNotRunning` | Latest backup > 25h old | **Critical** | Investigate backup service |
| `BackupDiskSpaceLow` | < 10GB free | **Critical** | Rotate backups or expand storage |
| `BackupNotVerified` | Latest not verified | Warning | Run manual verification |
| `WALArchivingDelayed` | Latest WAL > 30min old | Warning | Check archive_command |
| `BackupDiskUsageHigh` | > 85% full | Warning | Plan storage expansion |
| `BackupCountLow` | < 25 backups | Warning | Check rotation settings |

### 6.3 Alert Routing

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Prometheus  │────▶│ Alertmanager │────▶│   PagerDuty  │
│   (alerts)   │     │  (routing)   │     │  (critical)  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐     ┌──────────────┐
                     │    Slack     │     │    Sentry    │
                     │  (#alerts)   │     │  (errors)    │
                     └──────────────┘     └──────────────┘
```

---

## 7. Cron Schedule Summary

| Task | Schedule | Container | Command |
|------|----------|-----------|---------|
| Daily backup | 02:00 UTC daily | `backup` | `pg_backup.py --type daily` |
| Restore drill | 06:00 UTC daily | `backup` | `pg_backup.py --restore-drill` |
| Weekly backup | 03:00 UTC Sunday | `backup` | `pg_backup.py --type weekly` |
| WAL rotation | 04:00 UTC daily | `backup` | `rotate_wal.sh` |
| Health check | Every 15 min | `backup` | `backup_monitor.py check` |
| Metrics export | Continuous | `backup` | Port 9100 |

---

## 8. Implementation Checklist

### Phase 1: Immediate (Day 1)

- [x] Create `pg_backup.py` backup script
- [x] Create `wal_archive.py` WAL configuration script
- [x] Create `backup_monitor.py` monitoring script
- [x] Update `docker-compose.prod.yml` with backup service
- [x] Update `monitoring/alerts.yml` with backup alerts
- [ ] Deploy updated docker-compose to production
- [ ] Verify backup service starts correctly
- [ ] Run first manual backup: `docker compose exec backup pg_backup.py`

### Phase 2: Configuration (Day 2-3)

- [ ] Configure R2 bucket for off-site backups
- [ ] Set R2 credentials in production `.env`
- [ ] Verify WAL archiving is active: `docker compose exec db psql -U zozi -c "SHOW archive_mode;"`
- [ ] Verify first backup uploaded to R2
- [ ] Configure Alertmanager routing for backup alerts

### Phase 3: Testing (Day 4-7)

- [ ] Perform full restore test to temporary database
- [ ] Perform PITR test to specific timestamp
- [ ] Verify alert notifications are received
- [ ] Document any issues found during testing
- [ ] Train team on restore procedures

### Phase 4: Operationalization (Week 2+)

- [ ] Monitor backup success rate (target: 100%)
- [ ] Monitor backup storage usage trends
- [ ] Schedule monthly restore drills
- [ ] Review and update retention policies as needed
- [ ] Document lessons learned

---

## 9. Disaster Recovery Runbook

### Scenario 1: Database Corruption

**Symptoms:** Application errors, data inconsistencies, NEON crash loops

**Response:**
1. Stop application: `docker compose stop backend ml_worker`
2. Identify last good backup: `docker compose exec backup pg_backup.py --list`
3. Restore to new database: Follow Section 4.1
4. If corruption time is known, use PITR: Follow Section 4.2
5. Verify data integrity
6. Restart application

### Scenario 2: Accidental Data Deletion

**Symptoms:** User reports missing data, admin accidentally deleted records

**Response:**
1. Identify deletion time from audit logs
2. Use PITR to recover to just before deletion: Follow Section 4.2
3. Export recovered data
4. Import into production database
5. Verify data completeness

### Scenario 3: Complete Server Failure

**Symptoms:** Hardware failure, cloud region outage

**Response:**
1. Provision new server
2. Install Docker and Docker Compose
3. Clone repository
4. Download latest backup from R2
5. Restore from backup: Follow Section 4.1
6. Replay WAL archives up to latest available
7. Update DNS/load balancer
8. Verify application functionality

### Scenario 4: Ransomware / Security Breach

**Symptoms:** Encrypted files, ransom note, unauthorized access detected

**Response:**
1. Isolate affected systems (do NOT delete anything)
2. Provision clean infrastructure
3. Restore from off-site R2 backup (assumed clean)
4. Verify backup integrity before restore
5. Apply all security patches
6. Rotate all credentials
7. Conduct security audit
8. Restore service

---

## 10. Compliance & Audit

### 10.1 Law Compliance

| Law | Requirement | Implementation |
|-----|-------------|----------------|
| Law 232 | Daily backups, tested for recovery, PITR, 30-day retention | ✅ Daily pg_dump + WAL archiving + restore drills |
| Law 307 | Daily restore test | ✅ Automated restore drill at 06:00 UTC |
| Law 143 | Storage abstraction + backup utilities | ✅ R2 replication via backup.py |

### 10.2 Audit Trail

All backup operations are logged with:
- Timestamp
- Backup type and size
- Verification status
- R2 upload status
- Any errors encountered

Logs are shipped to Loki via Promtail and retained for 1 year.

---

## 11. Maintenance

### 11.1 Weekly Tasks

- [ ] Review backup success/failure logs
- [ ] Check storage usage trends
- [ ] Verify R2 replication is working

### 11.2 Monthly Tasks

- [ ] Perform full restore test (manual)
- [ ] Review and update retention policies
- [ ] Calculate storage costs
- [ ] Update this document if procedures changed

### 11.3 Quarterly Tasks

- [ ] Test disaster recovery runbook
- [ ] Review backup security (encryption, access controls)
- [ ] Evaluate new backup technologies
- [ ] Update team training

---

## Appendix A: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | Yes | — | Database name |
| `POSTGRES_USER` | Yes | — | Database user |
| `POSTGRES_PASSWORD` | Yes | — | Database password |
| `POSTGRES_HOST` | No | localhost | Database host |
| `POSTGRES_PORT` | No | 5432 | Database port |
| `BACKUP_DIR` | No | /backups | Local backup directory |
| `BACKUP_RETENTION_DAYS` | No | 30 | Days to retain backups |
| `WAL_ARCHIVE_DIR` | No | /wal_archive | WAL archive directory |
| `R2_BUCKET` | No | — | R2 bucket for off-site backups |
| `R2_PREFIX` | No | zozi-backups/ | R2 key prefix |
| `R2_REGION` | No | auto | R2 region |
| `R2_ENDPOINT_URL` | No | — | R2 endpoint (for R2, DO) |
| `R2_ACCESS_KEY_ID` | No | — | R2 access key |
| `R2_SECRET_ACCESS_KEY` | No | — | R2 secret key |
| `ALERT_WEBHOOK_URL` | No | — | Slack/Discord webhook |
| `SENTRY_DSN` | No | — | Sentry DSN for alerts |

## Appendix B: File Locations

| File | Path | Purpose |
|------|------|---------|
| Backup script | `backend/scripts/pg_backup.py` | Main backup/restore tool |
| WAL config | `backend/scripts/wal_archive.py` | WAL archiving setup |
| Monitor script | `backend/scripts/backup_monitor.py` | Health checks + alerts |
| Docker compose | `docker-compose.prod.yml` | Production infrastructure |
| Alert rules | `monitoring/alerts.yml` | Prometheus alert definitions |
| This document | `docs/BACKUP_STRATEGY.md` | Strategy documentation |

## Appendix C: Quick Reference

```bash
# Create a manual backup
docker compose exec backup pg_backup.py

# List all backups
docker compose exec backup pg_backup.py --list

# Verify a backup
docker compose exec backup pg_backup.py --verify zozi_daily_20260901_020000.pgdump

# Run restore drill
docker compose exec backup pg_backup.py --restore-drill

# Check backup health
docker compose exec backup backup_monitor.py check

# Get Prometheus metrics
docker compose exec backup backup_monitor.py metrics

# Restore from backup (destructive!)
docker compose exec backup pg_backup.py --restore zozi_daily_20260901_020000.pgdump
```
