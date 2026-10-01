# Runbook: SlowDatabaseQueries

## Alert
- **Name:** SlowDatabaseQueries
- **Severity:** Warning
- **Expression:** `histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 0.1`
- **For:** 5m

## Symptoms
- Database-dependent endpoints show elevated response times.
- p95 query duration exceeds 100ms.
- Users experience slow page loads or timeouts on data-heavy operations.

## Diagnosis Steps
1. Identify slow query types:
   ```promql
   histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 0.1
   ```
2. Check for missing indexes or full-table scans in query plans:
   ```sql
   EXPLAIN ANALYZE <slow_query>;
   ```
3. Review recent schema changes, data growth, or increased traffic.
4. Check database server resource utilization (CPU, memory, disk I/O).

## Remediation Steps
1. Add or rebuild indexes for slow query paths.
2. Optimize queries by reducing joins, paginating large results, or using covering indexes.
3. If data growth is the cause, archive old data or partition large tables.
4. Consider read replicas or query caching for read-heavy workloads.

## Escalation Contacts
- Database team lead
- Backend team lead
- SRE on-call
