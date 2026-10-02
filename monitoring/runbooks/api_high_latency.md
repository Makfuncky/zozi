# API High Latency

## Alert
APIHighLatency

## Symptoms
- Alert fires when p95 latency exceeds 800ms for 5 minutes
- Users experience slow page loads or timeouts
- API response times degrade across one or more endpoints

## Triage
1. Identify the affected endpoint(s) from the alert labels
2. Check database query performance for the endpoint
3. Review external API dependencies and their latency
4. Check application instance CPU and memory utilization
5. Look for traffic spikes or DDoS patterns

## Resolution
- Add database indexes if slow queries are identified
- Cache frequent responses to reduce backend load
- Scale out application instances if CPU/memory are saturated
- Rate-limit or queue requests if downstream services are slow

## Prevention
- Set up per-endpoint latency dashboards
- Implement response caching for read-heavy endpoints
- Configure autoscaling based on request latency
