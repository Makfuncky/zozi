# Slow Database Queries

## Alert
SlowDatabaseQueries

## Symptoms
- Alert fires when p95 database query duration exceeds 100ms for 5 minutes
- API endpoints that depend on the slow queries return slowly
- Database CPU utilization may be elevated

## Triage
1. Identify the slow query type from the alert labels (`query_type`)
2. Run an EXPLAIN ANALYZE on the query to check for missing indexes or full table scans
3. Check for lock contention or long-running transactions
4. Review recent schema changes or data volume growth

## Resolution
- Add or optimize indexes on the affected tables
- Rewrite the query to use a more efficient execution plan
- Increase `work_mem` or `maintenance_work_mem` if sorting is slow
- Archive or partition old data if table scans are unavoidable

## Prevention
- Set up query performance budgets per endpoint
- Run regular VACUUM ANALYZE on large tables
- Monitor slow query logs and review them weekly
