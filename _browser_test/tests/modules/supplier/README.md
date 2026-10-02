# Supplier Tests

Supplier workflows: registration, catalog management, product upload, KYC, bulk operations, voice-to-catalog, orders, payouts.

## Files

- `supplier-smoke.spec.ts` — registration multi-step, retired route redirects.
- `supplier-search.spec.ts` — supplier query URL redirect, storefront suggestions.
- `supplier-product-upload.spec.ts` — image upload, AI auto-fill, background removal, variants.
- `supplier-kyc.spec.ts` — KYC checklist, toggle requirements, change KYC level.
- `supplier-bulk-upload.spec.ts` — AI assist, manual upload, JSON import, draft duplication.
- `supplier-voice-to-catalog.spec.ts` — voice pipeline, mic denial, batch limits.
- `supplier-orders-payouts.spec.ts` — orders list, parcel sheet, payouts, support tickets.
