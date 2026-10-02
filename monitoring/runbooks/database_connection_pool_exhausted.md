# Database Connection Pool Exhausted

## Alert
DatabaseConnectionPoolExhausted

## Symptoms
- Alert fires when `db_connections.checkedout / db_connections.size > 0.9` for 5 minutes
- API requests start failing with connection timeout errors
- Application logs show `PoolExhausted` or `TimeoutError` from the database driver

## Triage
1. Check current connection count: `SELECT count(*) FROM pg_stat_activity;`
2. Identify long-running queries: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;`
3. Review recent deployments or migrations that may have opened unclosed connections

## Resolution
- Kill idle or long-running connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE ...`
- Restart the application pool if connections are not being released properly
- Verify connection pool settings (max_connections, pool_size) match workload

## Prevention
- Ensure all database sessions use context managers or `finally` blocks
- Monitor connection pool metrics in dashboards
- Set up connection pool sizing alerts before hitting 90%
