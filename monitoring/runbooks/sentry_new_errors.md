# Sentry New Errors

## Alert
SentryNewErrors

## Symptoms
- Alert fires when new Sentry error events are detected in the last hour
- Users may or may not be impacted depending on error frequency
- Application logs show unhandled exceptions or deprecation warnings

## Triage
1. Open the Sentry project dashboard and review the new issues
2. Determine if the error affects a critical user flow (checkout, login, search)
3. Check the affected user count and event frequency
4. Review the stack trace to identify the root cause

## Resolution
- If critical: deploy a hotfix or roll back the offending release
- If non-critical: file a ticket for the next sprint and suppress the alert if noisy
- If caused by a known browser or platform issue: add a release health ignore rule

## Prevention
- Add error boundaries in frontend to prevent unhandled exceptions
- Configure Sentry alert rules with appropriate severity thresholds
- Run error monitoring review during sprint planning
