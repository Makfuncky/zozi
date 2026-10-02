# FORENSIC AUDIT FALSE-POSITIVE REVIEW

## Summary Table

| Claim | Audit Value | Verified Value | Verdict |
|-------|-------------|----------------|---------|
| 1. Celery candidate | 0 of 1 | 1 app at `backend/jobs/celery_app.py:16`, 13 beat entries | FALSE POSITIVE |
| 2. Stub handlers | 44 of 79 | 44 match regex, but 6 actually write via `_send_notification` helper | FALSE POSITIVE |
| 3. Handover guarantees | 0 of 10 | 10 functions, 0 have all 5 guarantees | CORRECT |
| 4. Missing QA tables | 5 missing | 3 are false positives (`return_rejection`, `sla_breach` present; `supplier_scorecard`, `proof_of_delivery` are name-only refs) | FALSE POSITIVE |
| 5. Feature catalog | declared=371, dead=152, undefined=15 | declared=371 correct; dead=152 correct for full-repo scan; undefined gates include garbage comment strings (real undefined=7) | FALSE POSITIVE |
| 6. Supplier onboarding state machine | not a real state machine | Real `VALID_TRANSITIONS` state machine confirmed | FALSE POSITIVE |
| 7. Celery schedule coverage | 1 of 54 | 38 tasks total, 13 beat_schedule entries; audit missed `@shared_task` tasks | FALSE POSITIVE |

## FALSE POSITIVES TO FIX

1. **s19_workflow Celery candidate check** (Claim 1): Only scans top-level `backend/*.py`, misses nested `backend/jobs/celery_app.py`.
2. **s19_workflow stub detector** (Claim 2): Regex misses DB writes performed via helper calls like `_send_notification`.
3. **s19_workflow QA probes** (Claim 4): Regex matches column names and role strings instead of actual model/table definitions.
4. **s18_feature_matrix require_feature regex** (Claim 5): Matches inside comments/docstrings, producing garbage undefined gates like `") and stripped.endswith("`, `X.*`, `foo.*`, `x`, `domain.action`.
5. **s19_workflow status integrity / Celery task scan** (Claim 7): Misses `@shared_task` tasks in non-celery_app modules; uses wrong denominator (54 vs actual 38).

## RECOMMENDED ACTION

Fix the five scanner regexes/globs above to eliminate these false positives; no code changes to the application are required.
