# Runbook: SentryNewErrors

## Alert
- **Name:** SentryNewErrors
- **Severity:** Warning
- **Expression:** `increases(sentry_event_total{environment="production"}[1h]) > 0`
- **For:** 0m

## Symptoms
- New error events appear in Sentry for production environment.
- Users may see unexpected exceptions or degraded functionality.
- Error rate increases within the last hour.

## Diagnosis Steps
1. Open the Sentry project for the production environment and review new error events.
2. Identify the top affected endpoints, error types, and user impact.
3. Correlate with recent deployments or code changes.
4. Determine if errors are from a known issue with an existing fix in progress or a new regression.

## Remediation Steps
1. Assign ownership of the error to the responsible team/developer.
2. If a hotfix is available, deploy immediately.
3. If the error is non-critical or transient, monitor and triage after peak hours.
4. Update internal incident tracking and communicate impact to stakeholders.

## Escalation Contacts
- Backend team lead
- Sentry project admin
- Engineering manager on-call
