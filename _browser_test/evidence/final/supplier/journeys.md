# supplier journeys — final

Catalogue rows: 1
Order rows: 0
Final URL: http://localhost:3000/supplier/credibility
Console errors: 0
Failed requests: 0
4xx/5xx: 0

| # | step | action | outcome | detail |
|---|---|---|---|---|
| 1 | session | api bootstrap | ok |  |
| 2 | dashboard | kpi cards | ok | 0 rows |
| 3 | catalog | my products | ok | 1 rows |
| 4 | catalog-add | click | not-found | button:/add product/new product/create product/\+\s*add/i / text:/add product/new product/i / [data-testid="add-product" |
| 5 | product-form | fill | not-found | input[name*="name" i] / input[placeholder*="name" i] |
| 6 | product-form | fill | not-found | input[name*="sku" i] / input[placeholder*="sku" i] |
| 7 | product-form | fill | not-found | input[name*="price" i] / input[type="number"] |
| 8 | product-form | fill | not-found | input[name*="stock" i] |
| 9 | product-form | fill | not-found | textarea[name*="description" i] / textarea |
| 10 | product-form | fields filled | not-found | 0/5 |
| 11 | catalog-submit | click "CREATED" | ok |  |
| 12 | orders | assigned orders | not-found | 0 rows |
| 13 | order-detail-and-fulfil | open order | not-found |  |
| 14 | advance-status | click | not-found | button:/mark (as )?(shipped/ready/packed/dispatched)/i / button:/confirm/advance/update status/i / text:/mark as shipped |
| 15 | earnings | surface | ok | 0 rows @ /supplier/commission |
| 16 | payouts | surface | ok | 0 rows @ /supplier/invoices |
| 17 | analytics | surface | ok | 0 rows @ /supplier/analytics |

Total 17 interactions, 10 not completed.