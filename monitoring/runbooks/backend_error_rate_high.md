# Backend Error Rate High

## Alert
BackendErrorRateHigh

## Symptoms
- Alert fires when 5xx error rate exceeds 5% over a 5-minute window
- Users see HTTP 500/502/503 responses
- Application logs show unhandled exceptions or downstream service failures

## Triage
1. Check recent deployments or configuration changes
2. Review Sentry dashboard for new error patterns matching the 5xx spike
3. Verify downstream services (payment, inventory, shipping) are healthy
4. Check database and cache for errors

## Resolution
- Roll back recent deployment if error rate correlates with deploy time
- Restart unhealthy downstream services
- Apply hotfix if a specific exception is identified
- Scale application instances if the issue is resource exhaustion

## Prevention
- Add circuit breakers for downstream dependencies
- Improve error handling in critical paths
- Set up deployment canaries to catch errors before full rollout
