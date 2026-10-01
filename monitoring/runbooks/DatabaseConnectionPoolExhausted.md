# Runbook: DatabaseConnectionPoolExhausted

## Alert
- **Name:** DatabaseConnectionPoolExhausted
- **Severity:** Critical
- **Expression:** `db_connections.checkedout / db_connections.size > 0.9`
- **For:** 5m

## Symptoms
- Application reports "connection pool exhausted" or "could not acquire connection" errors.
- Increased latency or timeouts on database-dependent endpoints.
- Elevated `db_connections.checkedout` metric approaching pool size.

## Diagnosis Steps
1. Check current connection pool utilization:
   ```promql
   db_connections.checkedout / db_connections.size
   ```
2. Inspect backend logs for connection acquisition timeouts or leaks.
3. Identify long-running queries holding connections:
   ```sql
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';
   ```
4. Review recent deployments or traffic spikes that may have increased load.

## Remediation Steps
1. Kill or optimize long-running queries identified in step 3.
2. Increase pool size if the database can handle additional connections.
3. Restart affected application instances if connections are stuck.
4. Enable connection pool monitoring and set lower warning thresholds to catch exhaustion earlier.

## Escalation Contacts
- Backend/Database team lead
- On-call infrastructure engineer
