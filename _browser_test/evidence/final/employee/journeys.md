# employee journeys — final

Employee account: ae.manager@zozi.com
Final URL: http://localhost:3000/admin/hr
Console errors: 0
Failed requests: 0
4xx/5xx: 0

| # | step | action | outcome | detail |
|---|---|---|---|---|
| 1 | session | api bootstrap (ae.manager@zozi.com) | ok |  |
| 2 | dashboard | kpi cards | ok | 0 rows |
| 3 | attendance | records | not-found | 0 rows |
| 4 | attendance | click | not-found | button:/clock (in/out)/check (in/out)/punch/i / text:/clock (in/out)/check (in/out)/i |
| 5 | leaves | click | not-found | button:/request leave/new leave/apply for leave/\+.*leave/i / text:/request leave/apply for leave/i |
| 6 | leaves | click | not-found | button:/approve/reject/review/i / text:/approve/reject/i |
| 7 | workspace | task rows | not-found | 0 rows |
| 8 | admin-hr | stat cards | not-found | 0 rows |

Total 8 interactions, 6 not completed.