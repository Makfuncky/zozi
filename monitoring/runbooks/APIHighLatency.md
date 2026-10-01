# Runbook: APIHighLatency

## Alert
- **Name:** APIHighLatency
- **Severity:** Warning
- **Expression:** `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.8`
- **For:** 5m

## Symptoms
- API endpoints feel slow to users.
- p95 latency exceeds 800ms for affected endpoints.
- Load balancer or CDN reports elevated origin response times.

## Diagnosis Steps
1. Identify affected endpoints:
   ```promql
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.8
   ```
2. Check downstream dependency latency (database queries, cache hits, external APIs).
3. Review resource utilization on application servers (CPU, memory, I/O).
4. Look for recent traffic spikes or expensive query patterns in logs.

## Remediation Steps
1. Scale out application pods/servers if resource utilization is high.
2. Optimize slow database queries or add missing indexes.
3. Enable caching for frequently accessed, expensive endpoints.
4. If traffic is spiking unexpectedly, apply rate limiting or enable auto-scaling.

## Escalation Contacts
- Backend team lead
- SRE/Performance engineering
