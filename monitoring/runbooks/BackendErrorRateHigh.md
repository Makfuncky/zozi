# Runbook: BackendErrorRateHigh

## Alert
- **Name:** BackendErrorRateHigh
- **Severity:** Critical
- **Expression:** `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05`
- **For:** 5m

## Symptoms
- Elevated 5xx HTTP responses across one or more endpoints.
- User-facing errors or partial outages.
- Monitoring dashboards show 5xx rate spike above 5%.

## Diagnosis Steps
1. Identify affected endpoints from alert annotations or Prometheus:
   ```promql
   rate(http_requests_total{status=~"5.."}[5m])
   ```
2. Check backend application logs for exception stack traces or unhandled errors.
3. Correlate with recent deployments, config changes, or dependency failures (DB, cache, external APIs).
4. Verify health of upstream services and network connectivity.

## Remediation Steps
1. Roll back recent deployment if the error started after a deploy.
2. Fix or revert misconfigured feature flags or environment variables.
3. Restart unhealthy application pods/servers.
4. If external dependency is failing, enable fallback behavior or circuit breaker.
5. Communicate status to stakeholders and update status page if needed.

## Escalation Contacts
- Backend team lead
- Platform/SRE on-call
