# Customer Tests

Customer-facing journeys: browse, product detail, cart, checkout, order tracking, cross-border tax.

## Files

- `customer-core-flow.spec.ts` — browse → product detail → add to cart → checkout → order tracking.
- `cross-border-checkout.spec.ts` — admin tax/gateway/logistics config → customer checkout.
- `customer-search.spec.ts` — category, price, rating, voice, image search.
- `customer-cart.spec.ts` — cart persistence, quantity updates, empty cart, cross-border tax.
- `customer-wishlist.spec.ts` — add to wishlist, persistence across sessions.
