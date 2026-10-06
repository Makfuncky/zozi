# logistics journeys — journeys-v5

Shipment rows: 0
Final URL: http://localhost:3000/barcode-scan
Console errors: 0
Failed requests: 0
4xx/5xx: 0

| # | step | action | outcome | detail |
|---|---|---|---|---|
| 1 | session | api bootstrap | ok |  |
| 2 | dashboard | kpi cards | ok | 0 rows |
| 3 | shipments | manifest rows | not-found | 0 rows |
| 4 | shipment-detail | open shipment | not-found |  |
| 5 | parcel | fill | not-found | input[name*="tracking" i] / input[name*="parcel" i] / input[placeholder*="tracking" i] / input[placeholder*="scan" i] |
| 6 | parcel | click | not-found | button:/verify/scan/lookup/check/i / text:/verify/scan/i |
| 7 | mark-picked-up | click | not-found | button:/mark.*(picked/collected)/pick up/collect/i / text:/mark.*(picked/collected)/pick up/collect/i |
| 8 | mark-in-transit | click | not-found | button:/in transit/dispatch/out for delivery/i / text:/in transit/dispatch/out for delivery/i |
| 9 | mark-delivered | click | not-found | button:/mark.*delivered/complete delivery/confirm delivery/i / text:/mark.*delivered/complete delivery/confirm delivery/ |
| 10 | pod | click | not-found | button:/proof of delivery/pod/signature/upload.*proof/i / text:/proof of delivery/pod/i |

Total 10 interactions, 8 not completed.