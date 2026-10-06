# customer journeys — journeys-v2

Catalogue rows: 40
Cart rows: 0
Final URL: http://localhost:3000/tickets
Console errors: 0
Failed requests: 0
4xx/5xx: 0

| # | step | action | outcome | detail |
|---|---|---|---|---|
| 1 | session | api bootstrap | ok |  |
| 2 | home | cards on landing | ok | 0 rows |
| 3 | catalog | product count | ok | 40 rows |
| 4 | catalog | click "Price" | ok |  |
| 5 | catalog-filter-applied | choose first option | not-found |  |
| 6 | search | results for 'tea' | ok | 40 rows |
| 7 | open-product | open first item | not-found | [data-testid="product-card"] / a[href*='/products/'] / [data-testid$="-product-card"] |
| 8 | open-product-fallback | direct /products/1 | ok | http://localhost:3000/products/1 |
| 9 | add-to-cart | click | not-found | button:/add to cart/i / button:/add to bag/i / text:/add to cart/i / [data-testid="add-to-cart"] / button:has-text('Add  |
| 10 | cart | line items | not-found | 0 rows |
| 11 | cart-qty | click | not-found | [data-testid="increase-qty"] / [aria-label*="increase" i] / [aria-label*="increment" i] / button:/^\+$/increase/incremen |
| 12 | cart-promo | fill | not-found | input[name*="promo" i] / input[placeholder*="promo" i] / input[placeholder*="code" i] |
| 13 | cart-promo | click | not-found | button:/apply/i / text:/apply/i |
| 14 | checkout | click "Add products to your cart and proceed to checkou" | ok |  |
| 15 | checkout-address | reached checkout | ok | http://localhost:3000/checkout |
| 16 | checkout | fill | not-found | input[name*="street" i] / input[placeholder*="street" i] / input[name*="address" i] |
| 17 | checkout | fill | not-found | input[name*="city" i] / input[placeholder*="city" i] |
| 18 | checkout | fill | not-found | input[name*="phone" i] / input[type="tel"] |
| 19 | checkout-cod | click | not-found | text:/cash on delivery/i / text:/\bCOD\b/ / radio:/cash/i / button:/cash on delivery/i |
| 20 | place-order | click | not-found | button:/place order/i / button:/confirm order/i / button:/complete order/i / text:/place order/i |
| 21 | place-order | no order confirmation detected | not-found | http://localhost:3000/checkout |
| 22 | orders | order rows | not-found | 0 rows |
| 23 | order-detail | open first order | not-found |  |
| 24 | order-tracking | open tracking | not-found |  |
| 25 | wishlist | saved items | not-found | 0 rows |
| 26 | wishlist | click | not-found | button:/move to cart/add to cart/i / text:/move to cart/i |
| 27 | addresses | saved addresses | not-found | 0 rows |
| 28 | returns | returns centre | ok | http://localhost:3000/returns |

Total 28 interactions, 19 not completed.