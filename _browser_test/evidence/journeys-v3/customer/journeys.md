# customer journeys — journeys-v3

Catalogue rows: 40
Cart rows: 0
Final URL: http://localhost:3000/tickets
Console errors: 0
Failed requests: 0
4xx/5xx: 0

| # | step | action | outcome | detail |
|---|---|---|---|---|
| 1 | session | api bootstrap | ok |  |
| 2 | home | cards on landing | ok | 40 rows |
| 3 | catalog | product count | ok | 40 rows |
| 4 | catalog | click "Price" | ok |  |
| 5 | catalog-filter-applied | choose first option | not-found |  |
| 6 | search | results for 'tea' | ok | 40 rows |
| 7 | open-product | open first item | ok | http://localhost:3000/products |
| 8 | add-to-cart | click "Add to Cart" | ok |  |
| 9 | cart | line items | not-found | 0 rows |
| 10 | cart-qty | click | not-found | [data-testid="increase-qty"] / [aria-label*="increase" i] / [aria-label*="increment" i] / button:/^\+$/increase/incremen |
| 11 | cart-promo | fill | not-found | input[name*="promo" i] / input[placeholder*="promo" i] / input[placeholder*="code" i] |
| 12 | cart-promo | click | not-found | button:/apply/i / text:/apply/i |
| 13 | checkout | click "Proceed to Checkout" | ok |  |
| 14 | checkout-address | reached checkout | ok | http://localhost:3000/checkout |
| 15 | checkout | fill | not-found | input[name*="street" i] / input[placeholder*="street" i] / input[name*="address" i] |
| 16 | checkout | fill | not-found | input[name*="city" i] / input[placeholder*="city" i] |
| 17 | checkout | fill | not-found | input[name*="phone" i] / input[type="tel"] |
| 18 | checkout-cod | click | not-found | text:/cash on delivery/i / text:/\bCOD\b/ / radio:/cash/i / button:/cash on delivery/i |
| 19 | place-order | click | not-found | button:/place order/i / button:/confirm order/i / button:/complete order/i / text:/place order/i |
| 20 | place-order | no order confirmation detected | not-found | http://localhost:3000/checkout |
| 21 | orders | order rows | not-found | 0 rows |
| 22 | order-detail | open first order | not-found |  |
| 23 | order-tracking | open tracking | not-found |  |
| 24 | wishlist | saved items | not-found | 0 rows |
| 25 | wishlist | click | not-found | button:/move to cart/add to cart/i / text:/move to cart/i |
| 26 | addresses | saved addresses | not-found | 0 rows |
| 27 | returns | returns centre | ok | http://localhost:3000/returns |

Total 27 interactions, 17 not completed.