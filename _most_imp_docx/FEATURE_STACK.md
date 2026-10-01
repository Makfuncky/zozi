# ZOZI — Complete Feature Register

Below is every feature we have, plus every feature we need. Each row is one feature. Status codes:

| Code | Meaning |
|---|---|
| **LIVE** | Endpoint + RBAC + frontend surface confirmed working |
| **BE-ONLY** | Backend endpoint exists; no frontend or no RBAC gate |
| **FE-ONLY** | Frontend surface exists; no matching backend |
| **GATED** | Endpoint + RBAC, missing frontend |
| **UN-GATED** | Endpoint exists with no `require_feature` |
| **ORPHAN-RBAC** | Feature key defined, never referenced |
| **MISSING** | Wanted but not implemented |
| **BROKEN** | Exists but failing tests |

Tables are grouped by actor. Within each actor, grouped by domain. This is the working register — read top to bottom, act on the status.

---

## A. CUSTOMER — Buyer Actor

### A.1 Authentication & Identity

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Email/password login | `POST /auth/login` | Submit credentials → verify hash → issue JWT | bcrypt-verified, 72-byte limit, rate-limited 5/15min | LIVE |
| Customer | TOTP completion | `POST /auth/totp/complete` | Enter 6-digit code after password | pyotp, 30s window ±1 | LIVE |
| Customer | Social login (Google) | `GET /auth/social/google/start` → callback | Redirect → consent → exchange code → link identity | id_token verified via Google JWKS | LIVE |
| Customer | Social login (Facebook) | `GET /auth/social/facebook/start` → callback | Same flow, Facebook OAuth2 | | LIVE |
| Customer | Register new account | `POST /auth/register` | Email + password + full name → create user | Password strength validated; email verification sent | LIVE |
| Customer | Register form (web) | `POST /auth/register-form` | Multipart form register variant | | LIVE |
| Customer | Refresh token | `POST /auth/refresh` | Rotate access + refresh tokens | Reuse detection revokes entire family | LIVE |
| Customer | Logout | `POST /auth/logout` | Blacklist jti + revoke refresh family | | LIVE |
| Customer | Forgot password | `POST /auth/forgot-password` | Submit email → enqueue reset email | 30-min token, SHA-256 hashed | LIVE |
| Customer | Reset password | `POST /auth/reset-password` | Submit token + new password | Revokes all sessions | LIVE |
| Customer | Verify email | `GET /auth/verify-email/{token}` | Click link → mark verified | One-time token | LIVE |
| Customer | Resend verification | `POST /auth/resend-verification` | Re-issue verification email | Rate-limited | LIVE |
| Customer | Get current user | `GET /auth/me` | Return user profile from JWT | | LIVE |
| Customer | Login history | `accounts.user_login_histories` | Written on every login | | BE-ONLY |
| Customer | Device binding | `accounts.user_devices` | Fingerprint captured on login | Untrusted device → step-up MFA | LIVE |
| Customer | Session list | `GET /customer/accounts/sessions` | List active sessions | | ORPHAN-RBAC |
| Customer | Session revoke | `DELETE /customer/accounts/sessions/{id}` | Force logout a session | | ORPHAN-RBAC |
| Customer | TOTP setup | `POST /customer/accounts/totp/setup` | Generate secret + QR | Field-encrypted secret | ORPHAN-RBAC |
| Customer | TOTP enable | `POST /customer/accounts/totp/enable` | Confirm code → enable MFA | | ORPHAN-RBAC |
| Customer | TOTP disable | `POST /customer/accounts/totp/disable` | Disable MFA (password required) | | ORPHAN-RBAC |
| Customer | TOTP status | `GET /customer/accounts/totp/status` | Return MFA state | | ORPHAN-RBAC |

### A.2 Profile & Addresses

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | View profile | `GET /customer/accounts/profile` | Return user profile | | LIVE |
| Customer | Update profile | `PUT /customer/accounts/profile` | Update name, phone, avatar | | LIVE |
| Customer | Change password | `POST /customer/accounts/change-password` | Old + new password | Adds old to history | LIVE |
| Customer | Upload avatar | `POST /customer/accounts/avatar` | Presigned upload | R2 storage | ORPHAN-RBAC |
| Customer | List addresses | `GET /customer/accounts` | Return address book | Max 10 per user | ORPHAN-RBAC |
| Customer | Create address | `POST /customer/accounts` | Add new address | Country validation | ORPHAN-RBAC |
| Customer | Update address | `PUT /customer/accounts/{id}` | Update address | | ORPHAN-RBAC |
| Customer | Delete address | `DELETE /customer/accounts/{id}` | Soft delete | Blocked if pending order uses it | ORPHAN-RBAC |
| Customer | Set default address | `POST /customer/accounts/{id}/set-default` | Mark as default | Unsets previous default | ORPHAN-RBAC |

### A.3 Catalog Browsing

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Browse products | `GET /customer/catalog/products` | List with filters + pagination | Keyset pagination, only approved products | LIVE |
| Customer | Product detail | `GET /customer/catalog/products/{id}` | Return product + variants + reviews | Includes wishlist/cart state if auth | LIVE |
| Customer | Search products | `GET /customer/catalog/search` | Full-text search | `tsvector` + `pg_trgm` | LIVE |
| Customer | Autocomplete | `GET /customer/catalog/autocomplete` | Suggest query completions | | ORPHAN-RBAC |
| Customer | List categories | `GET /customer/catalog/categories` | Category tree | Materialized path | LIVE |
| Customer | Get banners | `GET /customer/catalog/banners` | Country + time-scoped banners | Sorted by sort_order | LIVE |
| Customer | Recommendations | `GET /customer/catalog/recommended` | AI-personalized products | | LIVE |
| Customer | Last-seen products | `GET /customer/accounts/last-seen` | Recently viewed | | ORPHAN-RBAC |
| Customer | List suppliers | `GET /customer/suppliers/products/suppliers` | Products by supplier | | LIVE |
| Customer | Country list | `GET /customer/country/countries` | Supported countries | | LIVE |
| Customer | Currency context | `GET /customer/country/currency/context` | Detect currency from IP | | LIVE |

### A.4 Cart & Wishlist

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | View cart | `GET /customer/orders/cart` | Return cart items + totals | | LIVE |
| Customer | Add to cart | `POST /customer/orders/items` | Add product/variant + qty | Stock validated, idempotent merge | LIVE |
| Customer | Update cart item | `PUT /customer/orders/items/{product_id}` | Change qty | Re-validates stock | LIVE |
| Customer | Remove cart item | `DELETE /customer/orders/items/{product_id}` | Remove item | | LIVE |
| Customer | Sync cart | `PUT /customer/orders/sync` | Reconcile cart across devices | | LIVE |
| Customer | Cart totals | `POST /customer/orders/totals` | Compute subtotal + tax + shipping | Same math as order total | LIVE |
| Customer | Add to wishlist | `POST /customer/promotions/wishlist/{product_id}` | Add product to wishlist | Idempotent | LIVE |
| Customer | Remove from wishlist | `DELETE /customer/promotions/wishlist/{product_id}` | Remove | | LIVE |

### A.5 Checkout & Payment

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Shipping quote | `POST /customer/logistics/shipping-quote` | Return carrier options | Zone + partner pricing | LIVE |
| Customer | Cart shipping quote | `POST /customer/orders/shipping-quote` | Cart-specific rates | | LIVE |
| Customer | Checkout preview | `POST /customer/orders/preview` | Draft order with totals | | LIVE |
| Customer | Create order | `POST /customer/orders` | Place order | Idempotency required, stock reserved | LIVE |
| Customer | Available methods | `GET /customer/finance/methods` | List gateways for country | | ORPHAN-RBAC |
| Customer | Create payment intent | `POST /customer/finance/create-payment-intent` | Initialize gateway intent | Idempotency required | LIVE |
| Customer | Stripe checkout | `POST /customer/finance/stripe/create-checkout-session` | Stripe Elements | | LIVE |
| Customer | Tap payment | `POST /customer/finance/tap/create` | Tap gateway | | LIVE |
| Customer | PayTabs payment | `POST /customer/finance/paytabs/create` | PayTabs gateway | | LIVE |
| Customer | PayPal payment | `POST /customer/finance/paypal/create` | PayPal redirect | | LIVE |
| Customer | Thawani payment | `POST /customer/finance/thawani/create-session` | Thawani gateway | | LIVE |
| Customer | Confirm card payment | `POST /customer/finance/confirm-card-payment` | Confirm after Elements | Emits payment.captured | LIVE |
| Customer | Payment webhook | `POST /webhooks/payments/{slug}` | Gateway callback | Signature verified, idempotent | LIVE |
| Customer | Finance config | `GET /customer/finance/config` | Runtime config | | LIVE |
| Customer | Gateway test | `POST /customer/finance/config/gateways/{code}/test` | Test gateway creds | | ORPHAN-RBAC |

### A.6 Orders

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | List orders | `GET /customer/orders` | Order history | Filtered by user + RLS | LIVE |
| Customer | Order detail | `GET /customer/orders/{id}` | Full order with items | | LIVE |
| Customer | Order invoice | `GET /customer/orders/{id}/invoice` | Download PDF | Celery-generated | LIVE |
| Customer | Track shipment | `GET /customer/orders/{id}/tracking` | Shipment events | | LIVE |
| Customer | Cancel order | `POST /customer/orders/{id}/cancel` | Cancel before packing | Refund if paid | LIVE |
| Customer | Confirmation response | `POST /customer/orders/{id}/confirmation-requests/{cid}/respond` | Respond to delivery confirmation | | LIVE |
| Customer | Scan receipt | `POST /customer/orders/{id}/scan-receipt` | Attach delivery receipt | | LIVE |

### A.7 Returns

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | List returns | `GET /customer/orders/returns` | Return requests | | LIVE |
| Customer | Create return | `POST /customer/orders/returns` | Request return | Within window, with images | LIVE |
| Customer | Return detail | `GET /customer/orders/{return_id}` | Full return view | | LIVE |
| Customer | Update return | `PUT /customer/orders/{return_id}` | Edit return | Before approval | LIVE |
| Customer | Return status | `PUT /customer/orders/{return_id}/status` | Advance workflow | | LIVE |

### A.8 Promotions & Loyalty

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Validate coupon | `POST /customer/promotions/validate` | Apply coupon | Usage limit, min order checks | LIVE |
| Customer | Coupon validate (GET) | `GET /customer/promotions/validate` | Preview discount | | LIVE |
| Customer | View promotions | `GET /customer/promotions/products/{id}` | Product promotions | | LIVE |
| Customer | Delete coupon | `DELETE /customer/promotions/coupons/{id}` | Remove applied coupon | | LIVE |
| Customer | View coins balance | `GET /customer/accounts/coins` | Loyalty points | | ORPHAN-RBAC |
| Customer | Redeem coins | `POST /customer/accounts/coins/redeem` | Apply coins to order | Max 50% of subtotal | ORPHAN-RBAC |
| Customer | View referral config | `GET /customer/governance/referral-config` | Referral settings | | LIVE |
| Customer | View referral code | `GET /customer/finance/my-code` | Own referral code | | LIVE |

### A.9 Reviews

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Write review | `POST /customer/promotions/reviews` | Submit rating + comment | Requires purchase | LIVE |
| Customer | Delete review | `DELETE /customer/promotions/reviews/{id}` | Remove own review | Soft delete | LIVE |
| Customer | View product reviews | `GET /customer/promotions/products/{id}` | Reviews list | | LIVE |

### A.10 Support & Communications

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | List tickets | `GET /customer/accounts/support_ticket` | Support tickets | | FE-ONLY |
| Customer | Notifications list | `GET /customer/comms/notifications` | Own notifications | | LIVE |
| Customer | Mark read | `POST /customer/comms/notifications/{id}/read` | Read receipt | | LIVE |
| Customer | Chatbot | `GET /chatbot` (public) | AI chat interface | Local ollama | FE-ONLY |
| Customer | Translate | `POST /customer/comms/translate` | i18n text translate | | ORPHAN-RBAC |
| Customer | Format currency | `POST /customer/comms/format-currency` | Currency formatting | | ORPHAN-RBAC |

### A.11 Data & Privacy

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Data export request | `POST /customer/accounts/data-export` | GDPR export | ZIP via Celery, 30-day rate limit | ORPHAN-RBAC |
| Customer | Delete account request | `POST /customer/accounts/delete-request` | Request deletion | 14-day cooling off | ORPHAN-RBAC |
| Customer | View audit timeline | `GET /customer/audit/my-timeline` | Personal audit trail | | LIVE |
| Customer | View audit activity | `GET /customer/audit/my-activity` | Personal activity | | LIVE |
| Customer | Consent view | `GET /customer/governance/consent` | Consent status | | LIVE |

### A.12 Customer Analytics

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Customer | Personal summary | `GET /customer/analytics/summary` | Dashboard summary | | LIVE |
| Customer | Recommendations feed | `GET /customer/analytics/recommendations` | Personalized feed | | LIVE |
| Customer | Personal analytics | `GET /customer/analytics/last-seen` | Recently viewed | | LIVE |

---

## B. SUPPLIER — Seller Actor

### B.1 Onboarding & KYC

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | Register | `POST /auth/register` (role=supplier) | Create user + draft profile | | LIVE |
| Supplier | View onboarding status | `GET /supplier/suppliers/status` | Pipeline progress | | BE-ONLY |
| Supplier | Create onboarding pipeline | `POST /supplier/suppliers/pipelines` | Start onboarding | | BE-ONLY |
| Supplier | Upload pipeline document | `POST /supplier/suppliers/pipelines/{id}/documents` | KYC doc upload | Presigned R2 | BE-ONLY |
| Supplier | Complete pipeline step | `POST /supplier/suppliers/pipelines/{id}/steps/{name}/complete` | Mark step done | | BE-ONLY |
| Supplier | Submit KYC | `POST /supplier/suppliers/kyc` | Trigger KYC verification | | BE-ONLY |
| Supplier | View profile | `GET /supplier/suppliers/profile` | Business profile | | LIVE |
| Supplier | Create profile | `POST /supplier/suppliers/profile` | Initial setup | | LIVE |
| Supplier | Update profile | `PUT /supplier/suppliers/profile` | Edit details | | LIVE |
| Supplier | Upload document | `POST /supplier/suppliers/documents` | New KYC doc | Presigned upload | LIVE |
| Supplier | Review document | `PUT /supplier/suppliers/documents/{id}/review` | Mark approved/rejected | Admin-triggered | LIVE |
| Supplier | View documents | `GET /supplier/suppliers/documents` | List docs | | LIVE |
| Supplier | Health view | `GET /supplier/suppliers/health/suppliers/{id}` | Credibility score | | LIVE |

### B.2 Products & Catalog

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | List products | `GET /supplier/catalog` | Own product list | | LIVE |
| Supplier | View product | `GET /supplier/catalog/{id}` | Full product detail | | LIVE |
| Supplier | Update product | `PUT /supplier/catalog/{id}` | Edit product fields | | LIVE |
| Supplier | Delete product | `DELETE /supplier/catalog/{id}` | Remove product | Soft delete | LIVE |
| Supplier | Update discount | `PUT /supplier/catalog/{id}/discount` | Set discount price | | ORPHAN-RBAC |
| Supplier | Upload image | `POST /supplier/catalog/{id}/image` | Product image | R2 presigned | ORPHAN-RBAC |
| Supplier | Bulk upload | `POST /supplier/catalog/bulk-upload` | Batch product creation | Excel/CSV | FE-ONLY |
| Supplier | AI-assisted upload | `POST /supplier/catalog/ai-upload` | Photos → AI extract | Ollama vision + ONNX | FE-ONLY |
| Supplier | Video upload | `POST /supplier/catalog/videos/upload` | Product video | R2 + CDN | FE-ONLY |
| Supplier | BG compare | `POST /supplier/upload/bg-compare` | Compare bg-removal results | rembg | FE-ONLY |

### B.3 Orders

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | List orders | `GET /supplier/orders` | Order list | Filtered by supplier_id | LIVE |
| Supplier | View order | `GET /supplier/orders/{id}` | Order detail | | LIVE |
| Supplier | Print label | `GET /supplier/orders/{id}/label` | Shipping label PDF | Barcode + QR | LIVE |
| Supplier | Parcel proof upload | `POST /supplier/orders/{id}/parcel-proof` | Packaging proof photo | | ORPHAN-RBAC |
| Supplier | Parcel proof verify | `POST /supplier/orders/{id}/parcel-proof/verify` | Auto + manual verify | | ORPHAN-RBAC |
| Supplier | Reference image | `GET /supplier/orders/{id}/parcel-proof/reference-image` | AI-generated reference | | ORPHAN-RBAC |
| Supplier | Verification history | `GET /supplier/orders/parcel-verification-history` | Prior verifications | | ORPHAN-RBAC |

### B.4 Finance

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | Commission ledger | `GET /supplier/finance/ledger` | Commission entries | | LIVE |
| Supplier | Category list | `GET /supplier/finance/categories` | Per-category rates | | LIVE |
| Supplier | Update category rate | `PUT /supplier/finance/categories/{slug}` | Adjust rate | Some countries only | LIVE |
| Supplier | Effective rate | `GET /supplier/finance/effective-rate` | Current rate | | LIVE |
| Supplier | Product commission | `GET /supplier/finance/products/{id}` | Per-product override | | LIVE |
| Supplier | Global config | `GET /supplier/finance/global` | Commission config | | BE-ONLY |
| Supplier | Update global | `PUT /supplier/finance/global` | Update global | | BE-ONLY |
| Supplier | Preview calculation | `POST /supplier/finance/preview` | Simulate payout | | BE-ONLY |
| Supplier | Badge tiers | `GET /supplier/finance/badge-tiers` | Available tiers | | LIVE |
| Supplier | Bank account | `GET /supplier/finance/bank-account` | Bank details | | LIVE |
| Supplier | Update bank account | `PUT /supplier/finance/bank-account` | Edit bank details | Verification freeze | LIVE |
| Supplier | List bank accounts | `GET /supplier/accounts/bank-accounts` | All bank accounts | | LIVE |
| Supplier | Create bank account | `POST /supplier/accounts/bank-accounts` | Add new account | Verification pending | LIVE |
| Supplier | Update bank account | `PUT /supplier/accounts/bank-accounts/{id}` | Edit | | LIVE |
| Supplier | Delete bank account | `DELETE /supplier/accounts/bank-accounts/{id}` | Remove | | LIVE |
| Supplier | Payout list | `GET /supplier/finance/payouts` | Payout history | | LIVE |
| Supplier | Request payout | `POST /supplier/finance/payouts/request` | Trigger payout | Eligible settlements only | LIVE |
| Supplier | Payout status summary | `GET /supplier/finance/payout-status/summary` | Buckets | | ORPHAN-RBAC |
| Supplier | Payout status orders | `GET /supplier/finance/payout-status/orders` | Per-order status | | ORPHAN-RBAC |
| Supplier | Order payment status | `GET /supplier/finance/orders/{id}/payment-status` | Payment state | | BE-ONLY |
| Supplier | Suppliers list | `GET /supplier/finance/suppliers` | Related suppliers | | BE-ONLY |
| Supplier | Supplier detail | `GET /supplier/finance/suppliers/{id}` | Detail | | BE-ONLY |
| Supplier | Delete supplier | `DELETE /supplier/finance/suppliers/{id}` | Admin action | | BE-ONLY |

### B.5 Analytics

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | Summary | `GET /supplier/analytics/summary` | Dashboard KPI | | LIVE |
| Supplier | Products analytics | `GET /supplier/analytics/products` | Top products | | LIVE |
| Supplier | Orders analytics | `GET /supplier/analytics/orders` | Recent orders | | LIVE |
| Supplier | Revenue trend | `GET /supplier/analytics/revenue-trend` | Chart data | | LIVE |
| Supplier | Provider summary | `GET /supplier/analytics/provider/summary` | Provider metrics | | ORPHAN-RBAC |
| Supplier | Reports | `GET /supplier/reports` | Reports list | | FE-ONLY |

### B.6 Support & Disputes

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | List disputes | `GET /supplier/governance/disputes` | Dispute list | | LIVE |
| Supplier | Notifications | `GET /supplier/comms/notifications` | Own notifications | | LIVE |
| Supplier | Mark read | `POST /supplier/comms/notifications/{id}/read` | Read receipt | | LIVE |
| Supplier | Support tickets | `GET /supplier/comms/tickets` | Tickets | | LIVE |
| Supplier | Create ticket | `POST /supplier/comms/tickets` | New ticket | | LIVE |
| Supplier | Ticket detail | `GET /supplier/comms/tickets/{id}` | Full view | | LIVE |
| Supplier | Reply | `POST /supplier/comms/tickets/{id}/reply` | Add reply | | LIVE |
| Supplier | Chat direct | `POST /supplier/comms/chat/direct` | 1:1 chat | WebSocket | LIVE |
| Supplier | Chat history | `GET /supplier/comms/chat/history/{chat_id}` | Messages | | LIVE |
| Supplier | Notification preferences | `GET /supplier/notification-preferences` | Preferences | | FE-ONLY |

### B.7 Supplier Sessions

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Supplier | Change password | `POST /supplier/accounts/change-password` | Update password | | LIVE |
| Supplier | Session list | `GET /supplier/accounts/sessions` | Active sessions | | ORPHAN-RBAC |
| Supplier | Session revoke | `DELETE /supplier/accounts/sessions/{id}` | Force logout | | ORPHAN-RBAC |
| Supplier | TOTP setup | `POST /supplier/accounts/totp/setup` | Enable MFA | | ORPHAN-RBAC |
| Supplier | TOTP status | `GET /supplier/accounts/totp/status` | MFA state | | ORPHAN-RBAC |

---

## C. LOGISTICS PARTNER — Delivery Actor (Individual + Company)

### C.1 Registration & Profile

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | Register (individual) | `POST /auth/register` | Solo courier signup | Subtype in JWT | LIVE |
| Logistics | Register (company) | `POST /auth/register` | Fleet operator signup | Company KYC | LIVE |
| Logistics | View profile | `GET /logistics/profile` | Business profile | | LIVE |
| Logistics | Update profile | `PUT /logistics/profile` | Edit details | | LIVE |
| Logistics | Accept terms | `POST /logistics/profile/terms/accept` | Accept TOS | | LIVE |
| Logistics | Submit for review | `POST /logistics/profile/submit-review` | Trigger admin review | | LIVE |
| Logistics | Upload document | `POST /logistics/me/docs/upload` | KYC doc | Presigned R2 | LIVE |
| Logistics | List documents | `GET /logistics/me/docs` | Own docs | | LIVE |
| Logistics | Delete document | `DELETE /logistics/me/docs/{id}` | Remove doc | | LIVE |

### C.2 Service Areas & Pricing

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | List service areas | `GET /logistics/service-areas` | Own areas | | LIVE |
| Logistics | Create area | `POST /logistics/service-areas` | Add coverage | Approval required | LIVE |
| Logistics | Update area | `PUT /logistics/service-areas/{id}` | Edit | | LIVE |
| Logistics | Delete area | `DELETE /logistics/service-areas/{id}` | Remove | | LIVE |
| Logistics | List pricing profiles | `GET /logistics/pricing-profiles` | Rates | | LIVE |
| Logistics | Create pricing profile | `POST /logistics/pricing-profiles` | Add pricing | Approval required | LIVE |
| Logistics | Update pricing | `PUT /logistics/pricing-profiles/{id}` | Edit rates | | LIVE |
| Logistics | Delete pricing | `DELETE /logistics/pricing-profiles/{id}` | Remove | | LIVE |
| Logistics | Vehicle rules | `GET /logistics/vehicle-rules` | Vehicle capacities | | LIVE |
| Logistics | Create vehicle rule | `POST /logistics/vehicle-rules` | Add vehicle | Approval required | LIVE |
| Logistics | Update vehicle rule | `PUT /logistics/vehicle-rules/{id}` | Edit | | LIVE |
| Logistics | Delete vehicle rule | `DELETE /logistics/vehicle-rules/{id}` | Remove | | LIVE |
| Logistics | Category rules | `GET /logistics/category-rules` | Category-specific pricing | | LIVE |
| Logistics | Create category rule | `POST /logistics/category-rules` | Add rule | Approval required | LIVE |
| Logistics | Update category rule | `PUT /logistics/category-rules/{id}` | Edit | | LIVE |
| Logistics | Delete category rule | `DELETE /logistics/category-rules/{id}` | Remove | | LIVE |
| Logistics | Pricing insights | `GET /logistics/pricing-insights` | Market comparison | | ORPHAN-RBAC |

### C.3 Shipments

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | Dashboard | `GET /logistics/dashboard` | KPI summary | | LIVE |
| Logistics | Active shipments | `GET /logistics/shipments/active` | Current assignments | | LIVE |
| Logistics | Shipment detail | `GET /logistics/shipments/{id}/events` | Event history | | LIVE |
| Logistics | Scan lookup | `GET /logistics/shipments/scan` | Lookup by scan code | | LIVE |
| Logistics | Update status | `PUT /logistics/shipments/{id}/status` | Advance status | State machine validated | LIVE |
| Logistics | Bulk status update | `PUT /logistics/shipments/bulk-status` | Batch update | Max 100 | LIVE |
| Logistics | Scan receive | `POST /logistics/{order_id}/scan-receive` | Pick up from supplier | Barcode validated | LIVE |
| Logistics | Update transit | `POST /logistics/{order_id}/update-transit` | Add transit event | | LIVE |
| Logistics | Deliver | `POST /logistics/{order_id}/deliver` | Mark delivered | Signature capture | LIVE |
| Logistics | Confirm pickup | `POST /logistics/{order_id}/confirm-pickup` | Confirm pickup | | LIVE |
| Logistics | Cancel pickup | `POST /logistics/{order_id}/cancel-pickup` | Cancel assigned pickup | Fee if after pickup | LIVE |
| Logistics | Label | `GET /logistics/{order_id}/label` | Print label | | LIVE |
| Logistics | Confirmation request | `POST /logistics/shipments/{id}/confirmation-request` | Request confirmation | | LIVE |

### C.4 Payouts & COD

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | Payout list | `GET /logistics/payouts` | Payout history | | LIVE |
| Logistics | Pending payouts | `GET /logistics/payouts/pending` | Pending view | | LIVE |
| Logistics | Request payout | `POST /logistics/payouts/request` | Trigger payout | Eligible settlements | LIVE |
| Logistics | Verify payout | `POST /logistics/payouts/{id}/verify` | Confirm receipt | | LIVE |
| Logistics | COD remittances | `GET /logistics/me/cod-remittance-receipts` | COD history | | LIVE |
| Logistics | Bank account | `GET /logistics/me/bank-account` | Bank details | | LIVE |
| Logistics | Update bank account | `PUT /logistics/me/bank-account` | Edit bank | Verification freeze | LIVE |
| Logistics | Bank accounts list | `GET /logistics/bank-accounts` | All accounts | | LIVE |
| Logistics | Create bank account | `POST /logistics/bank-accounts` | Add | Verification pending | LIVE |
| Logistics | Update bank account | `PUT /logistics/bank-accounts/{id}` | Edit | | LIVE |
| Logistics | Delete bank account | `DELETE /logistics/bank-accounts/{id}` | Remove | | LIVE |

### C.5 Finance & Analytics

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | COD remittances | `GET /logistics/finance/cod-remittances` | Finance view | | BE-ONLY |
| Logistics | Ledger | `GET /logistics/finance/ledger` | Ledger entries | | BE-ONLY |
| Logistics | Settlements | `GET /logistics/finance/settlements` | Settlement list | | BE-ONLY |
| Logistics | Finance summary | `GET /logistics/finance/summary` | Summary | | BE-ONLY |
| Logistics | Delivery performance | `GET /logistics/analytics/delivery-performance` | KPI metrics | | LIVE |
| Logistics | Shipments analytics | `GET /logistics/analytics/shipments` | Volume trend | | LIVE |
| Logistics | Provider summary | `GET /logistics/analytics/provider/summary` | Provider metrics | | ORPHAN-RBAC |

### C.6 Communications & Support

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | Notifications | `GET /logistics/comms/notifications` | Own notifications | | LIVE |
| Logistics | Mark read | `POST /logistics/comms/notifications/{id}/read` | Read receipt | | LIVE |
| Logistics | Chat direct | `POST /logistics/comms/chat/direct` | 1:1 chat | | LIVE |
| Logistics | Chat history | `GET /logistics/comms/chat/history/{id}` | Messages | | LIVE |
| Logistics | Tickets | `GET /logistics/comms/tickets` | Ticket list | | LIVE |
| Logistics | Create ticket | `POST /logistics/comms/tickets` | New ticket | | LIVE |
| Logistics | Reply ticket | `POST /logistics/comms/tickets/{id}/reply` | Reply | | LIVE |
| Logistics | Proxy channels | `GET /logistics/comms/proxy/channels` | Masked channels | | LIVE |

### C.7 Account

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Logistics | Change password | `POST /logistics/accounts/change-password` | Update password | | LIVE |
| Logistics | Sessions | `GET /logistics/accounts/sessions` | Active sessions | | ORPHAN-RBAC |
| Logistics | Revoke session | `DELETE /logistics/accounts/sessions/{id}` | Force logout | | ORPHAN-RBAC |
| Logistics | TOTP | `POST /logistics/accounts/totp/setup` | Enable MFA | | ORPHAN-RBAC |

---

## D. EMPLOYEE — Staff Actor

### D.1 Profile & Self-Service

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View own profile | `GET /employee/accounts/profile` | Own data | | LIVE |
| Employee | Update profile | `PUT /employee/accounts/profile` | Edit own | | LIVE |
| Employee | View HR profile | `GET /employee/hr/profile` | HR-perspective | | LIVE |
| Employee | Update HR profile | `PUT /employee/hr/profile` | HR field edit | | LIVE |
| Employee | Change password | `POST /employee/accounts/change-password` | Update | | LIVE |

### D.2 Attendance

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View attendance | `GET /employee/accounts/attendance` | Own records | | LIVE |
| Employee | View attendance (HR) | `GET /employee/hr/attendance` | HR view | | LIVE |
| Employee | Check-in | `POST /employee/hr/admin/{code}/employees/{id}/check-in` | Kiosk check-in | Geo-fence validated | LIVE |
| Employee | Check-out | `POST /employee/hr/admin/{code}/employees/{id}/check-out` | Check-out | Computes hours | LIVE |
| Employee | Geo check-in | `POST /employee/hr/admin/{code}/employees/{id}/geo-check-in` | Geo location | Haversine | LIVE |
| Employee | Validate geo | `POST /employee/hr/geo/validate` | Validate location | | LIVE |
| Employee | QR token | `POST /employee/hr/employees/{id}/qr-token` | Generate QR | Dynamic | LIVE |
| Employee | QR login | `POST /employee/hr/employees/qr-login` | Login via QR | | LIVE |
| Employee | Bio enrollment | `hr.employee_biometrics` | Fingerprint/face | | LIVE |
| Employee | ID card | `hr.physical_id_cards` | Physical card | | LIVE |

### D.3 Leave

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View balance | `GET /employee/accounts/leave/balance` | Leave balance | | LIVE |
| Employee | View history | `GET /employee/accounts/leave/history` | Leave history | | LIVE |
| Employee | Submit leave | `POST /employee/accounts/leave/request` | Leave request | Balance validated | LIVE |
| Employee | HR leave balance | `GET /employee/hr/leave/balance` | HR view | | LIVE |
| Employee | HR leave history | `GET /employee/hr/leave/history` | HR view | | LIVE |
| Employee | HR leave request | `POST /employee/hr/leave/request` | HR request | | LIVE |
| Employee | Approve leave | `PATCH /employee/hr/admin/{code}/employees/leave-requests/{id}` | Manager approval | SLA escalation | LIVE |

### D.4 Payroll & Payslips

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View payslips (HR) | `GET /employee/hr/payslips` | List | | LIVE |
| Employee | View payslips (accounts) | `GET /employee/accounts/payslips` | Self-service | | LIVE |
| Employee | Payroll status | `GET /employee/hr/payroll/status/{country_code}` | Status | | BE-ONLY |
| Employee | Payroll bank account | `GET /employee/hr/payroll/bank-accounts/{employee_id}` | Bank details | | BE-ONLY |
| Employee | Approve payroll | `POST /employee/hr/payroll/approve` | Maker-checker | | LIVE |
| Employee | Run payroll batch | `POST /employee/hr/payroll/batch` | Trigger batch | | LIVE |
| Employee | Calculate payroll | `POST /employee/hr/payroll/calculate/{employee_id}` | Compute single | | LIVE |

### D.5 Performance & OKRs

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View OKRs | `GET /employee/accounts/okrs` | Own OKRs | | LIVE |
| Employee | View OKRs (HR) | `GET /employee/hr/okrs` | HR view | | LIVE |
| Employee | Create OKR | `POST /employee/hr/hr/okr` | Define objective | | ORPHAN-RBAC |
| Employee | View OKR detail | `GET /employee/hr/hr/okr/{id}` | Detail | | ORPHAN-RBAC |
| Employee | Update OKR progress | `PATCH /employee/hr/hr/okr/{id}/progress` | Progress update | | ORPHAN-RBAC |
| Employee | Create KPI | `POST /employee/hr/hr/kpi` | Define KPI | | ORPHAN-RBAC |
| Employee | View KPI | `GET /employee/hr/hr/kpi/employee/{id}` | KPI list | | ORPHAN-RBAC |
| Employee | Update KPI value | `PUT /employee/hr/hr/kpi/{id}/value` | Progress | | ORPHAN-RBAC |
| Employee | Submit review | `POST /employee/hr/hr/reviews` | 360 review | | ORPHAN-RBAC |
| Employee | View reviews | `GET /employee/hr/hr/reviews/{id}` | Reviews | | ORPHAN-RBAC |
| Employee | Performance view | `GET /employee/analytics/performance` | Own performance | | LIVE |
| Employee | Team view | `GET /employee/analytics/team` | Team data | | ORPHAN-RBAC |

### D.6 Org Chart & Hierarchy

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View org chart | `GET /employee/accounts/org-chart` | Tree view | | LIVE |
| Employee | HR org chart | `GET /employee/hr/org-chart` | HR view | | LIVE |
| Employee | View org unit | `GET /employee/hr/org-chart/{unit_id}` | Subtree | | LIVE |
| Employee | List org units | `GET /employee/hr/org-units` | Units | | LIVE |
| Employee | Create org unit | `POST /employee/hr/org-units` | New unit | | LIVE |
| Employee | Update org unit | `PUT /employee/hr/org-units/{id}` | Edit | | LIVE |
| Employee | Rebuild paths | `POST /employee/hr/org-units/rebuild-paths` | Path maintenance | | LIVE |
| Employee | Unit employees | `GET /employee/hr/org-units/{id}/employees` | Members | | LIVE |
| Employee | Unit subtree | `GET /employee/hr/org-units/{id}/subtree` | Subtree | | LIVE |
| Employee | Manager chain | `GET /employee/hr/employee/{id}/chain` | Reporting chain | | LIVE |
| Employee | Subordinates | `GET /employee/hr/employee/{id}/subordinates` | Direct reports | | LIVE |
| Employee | Matrix managers | `GET /employee/hr/employee/{id}/matrix-managers` | Dotted-line | | LIVE |
| Employee | Matrix subordinates | `GET /employee/hr/employee/{id}/matrix-subordinates` | Dotted-line | | LIVE |
| Employee | Assign matrix | `POST /employee/hr/matrix/assign` | Create matrix relation | | LIVE |
| Employee | Delete matrix | `DELETE /employee/hr/matrix/{id}` | Remove | | LIVE |
| Employee | Can-manage check | `GET /employee/hr/employee/{uid}/can-manage/{target}` | Auth check | | LIVE |
| Employee | Detect circular | `GET /employee/hr/detect-circular` | Cycle detection | | LIVE |

### D.7 Documents, Assets, Training

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
|---|---|---|---|
| Employee | Upload document | `POST /employee/hr/employees/{id}/documents` | Doc upload | Presigned R2 | LIVE |
| Employee | View documents | `GET /employee/hr/employees/{id}/documents` | Own docs | | LIVE |
| Employee | Approve document | `PATCH /employee/hr/admin/{code}/employees/documents/{id}` | Manager approval | | LIVE |
| Employee | View assets | `GET /employee/hr/admin/{code}/employees/{id}/assets` | Assigned assets | | LIVE |
| Employee | Assign asset | `POST /employee/hr/employees/{id}/assets` | Add asset | | LIVE |
| Employee | View dependents | `GET /employee/hr/employees/{id}/dependents` | Dependents | | LIVE |
| Employee | Add dependent | `POST /employee/hr/hr/{id}/dependents` | Add | | LIVE |
| Employee | View addresses | `GET /employee/hr/employees/{id}/addresses` | Addresses | | LIVE |
| Employee | Add address | `POST /employee/hr/hr/{id}/addresses` | Add | | LIVE |
| Employee | View relations | `GET /employee/hr/admin/{code}/employees/{id}/relations` | Relations | | LIVE |
| Employee | Add relation | `POST /employee/hr/admin/{code}/employees/{id}/relations` | Add | | LIVE |
| Employee | Delete relation | `DELETE /employee/hr/admin/{code}/employees/relations/{id}` | Remove | | LIVE |
| Employee | Training modules | `POST /employee/hr/modules` | Create module | | ORPHAN-RBAC |
| Employee | Assign training | `POST /employee/hr/{employee_id}/assign` | Assign | | ORPHAN-RBAC |
| Employee | Complete training | `POST /employee/hr/{employee_id}/complete` | Complete | | ORPHAN-RBAC |

### D.8 Work Logs, Expenses, Travel

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Log work | `POST /employee/hr/admin/{code}/employees/{id}/work-logs` | Work entry | | LIVE |
| Employee | View work logs | `GET /employee/hr/admin/{code}/employees/{id}/work-logs` | Own logs | | LIVE |
| Employee | Approve work log | `PATCH /employee/hr/admin/{code}/employees/work-logs/{id}/approve` | Manager approval | | LIVE |
| Employee | Submit expense | `POST /employee/hr/employees/{id}/expenses` | Expense claim | Receipt required >50 | LIVE |
| Employee | View expenses | `GET /employee/governance/expenses` | Own expenses | | LIVE |
| Employee | Travel request | `hr.employee_travel_requests` | Travel plan | | LIVE |
| Employee | Approve travel | `POST /employee/hr/travel/{id}/approve` | Manager approval | | LIVE |

### D.9 Shifts & Handover

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | View roster | `GET /employee/hr/admin/{code}/employees/shifts` | Shift calendar | | LIVE |
| Employee | Create shift | `POST /employee/hr/admin/{code}/employees/shifts` | Schedule | | LIVE |
| Employee | Handover session | `hr.shift_handover_sessions` | Handover | Must acknowledge | LIVE |
| Employee | Handover tasks | `hr.shift_handover_tasks` | Task list | | LIVE |

### D.10 Compliance & Safety

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Compliance status | `GET /employee/governance/compliance-status` | Status | | LIVE |
| Employee | Audit compliance | `GET /employee/audit/compliance/status` | Audit view | | LIVE |
| Employee | COI check | `GET /employee/hr/hr/{id}/coi-check` | Conflict check | | LIVE |
| Employee | COI report | `POST /employee/hr/hr/{id}/coi-report` | File report | | LIVE |
| Employee | Disciplinary list | `GET /employee/hr/hr/disciplinary` | Cases | | LIVE |
| Employee | Disciplinary create | `POST /employee/hr/hr/{id}/disciplinary` | New case | | LIVE |
| Employee | Offboarding list | `GET /employee/hr/hr/offboarding` | Cases | | LIVE |
| Employee | Offboarding create | `POST /employee/hr/hr/{id}/offboarding` | Initiate | EOSB computed | LIVE |
| Employee | Kill switch | `POST /employee/hr/employees/{id}/kill-switch` | Emergency disable | | LIVE |
| Employee | Alumni eligibility | `GET /employee/hr/alumni/{id}/eligibility` | Alumni check | | ORPHAN-RBAC |
| Employee | Create alumni | `POST /employee/hr/alumni` | Add to alumni | | ORPHAN-RBAC |

### D.11 Security

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Ghost employees | `GET /employee/security/ghost-employees` | Anomalies | | LIVE |
| Employee | Impossible travel | `GET /employee/security/impossible-travel` | Travel alerts | | LIVE |
| Employee | Team health | `GET /employee/security/team-health/{manager_id}` | Team metrics | | LIVE |
| Employee | Risk score view | `GET /employee/security/{id}/risk-score` | Own score | | LIVE |
| Employee | Risk score update | `POST /employee/security/{id}/risk-score` | Update | | LIVE |
| Employee | Audit timeline | `GET /employee/security/{id}/audit-timeline` | Timeline | | LIVE |

### D.12 Finance Operations (Employee Finance Role)

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Accounts list | `GET /employee/finance/accounts` | Chart of accounts | | LIVE |
| Employee | Account detail | `GET /employee/finance/accounts/{code}` | Account | | LIVE |
| Employee | Balances | `GET /employee/finance/balances/{code}` | Balance | | LIVE |
| Employee | Trial balance | `GET /employee/finance/trial-balance` | Report | | LIVE |
| Employee | Journal entries list | `GET /employee/finance/journal-entries` | Entries | | LIVE |
| Employee | Create journal entry | `POST /employee/finance/journal-entries` | New entry | Maker-checker | LIVE |
| Employee | Reverse entry | `POST /employee/finance/journal-entries/reverse` | Reversal | | LIVE |
| Employee | Entry detail | `GET /employee/finance/journal-entries/{id}` | Detail | | LIVE |
| Employee | AP list | `GET /employee/finance/ap` | Payables | | LIVE |
| Employee | AP ledger | `GET /employee/finance/ap-ledger` | AP ledger | | LIVE |
| Employee | Post AP payable | `POST /employee/finance/ap-ledger/payable` | Post | | LIVE |
| Employee | Post AP payment | `POST /employee/finance/ap-ledger/payment` | Payment | | LIVE |
| Employee | AR list | `GET /employee/finance/ar` | Receivables | | LIVE |
| Employee | Post AR invoice | `POST /employee/finance/ar-ledger/invoice` | Invoice | | LIVE |
| Employee | Post AR payment | `POST /employee/finance/ar-ledger/payment` | Payment | | LIVE |
| Employee | Periods list | `GET /employee/finance/periods` | Fiscal periods | | LIVE |
| Employee | Current period | `GET /employee/finance/periods/current` | Current | | LIVE |
| Employee | Get-or-create period | `POST /employee/finance/periods/get-or-create` | Upsert | | LIVE |
| Employee | Close period | `POST /employee/finance/periods/close` | Close | Irreversible | LIVE |
| Employee | Reports list | `GET /employee/finance/reports` | Reports | | LIVE |
| Employee | Income statement | `POST /employee/finance/reports/income-statement` | Generate | | LIVE |
| Employee | Balance sheet | `POST /employee/finance/reports/balance-sheet` | Generate | | LIVE |
| Employee | Cash flow | `POST /employee/finance/reports/cash-flow` | Generate | | LIVE |
| Employee | Cash flow forecast | `POST /employee/finance/cash-flow-forecast` | Forecast | | LIVE |
| Employee | Bank settings | `GET /employee/finance/admin/bank-settings` | Bank config | | LIVE |
| Employee | Update bank settings | `PUT /employee/finance/admin/bank-settings` | Update | | LIVE |
| Employee | Test bank connection | `POST /employee/finance/admin/bank-settings/test-connection` | Test | | LIVE |
| Employee | Bank transactions | `GET /employee/finance/admin/bank-transactions` | Transactions | | LIVE |
| Employee | Create transaction | `POST /employee/finance/admin/bank-transactions` | Manual entry | | LIVE |
| Employee | Auto reconcile | `POST /employee/finance/admin/bank-transactions/auto-reconcile` | Reconcile | | LIVE |
| Employee | Import statement | `POST /employee/finance/admin/bank-transactions/import` | Import | | LIVE |
| Employee | Flag transaction | `POST /employee/finance/admin/bank-transactions/{id}/flag` | Flag | | LIVE |
| Employee | Reconcile transaction | `POST /employee/finance/admin/bank-transactions/{id}/reconcile` | Match | | LIVE |
| Employee | Resolve transaction | `POST /employee/finance/admin/bank-transactions/{id}/resolve` | Resolve | | LIVE |
| Employee | Badge billings | `GET /employee/finance/admin/badge-billings` | Billings | | LIVE |
| Employee | Record badge payment | `POST /employee/finance/admin/badge-billings/{id}/record-payment` | Record | | LIVE |
| Employee | Ledger view | `GET /employee/finance/admin/ledger` | Ledger | | LIVE |
| Employee | Supplier settlements | `GET /employee/finance/admin/supplier-settlements` | Settlements | | LIVE |
| Employee | Logistics settlements | `GET /employee/finance/admin/logistics-settlements` | Settlements | | LIVE |
| Employee | Payouts supplier | `POST /employee/finance/admin/payouts/supplier/process` | Process | | LIVE |
| Employee | Payouts logistics | `POST /employee/finance/admin/payouts/logistics/process` | Process | | LIVE |
| Employee | Dispatch payouts | `POST /employee/finance/admin/payouts/{kind}/dispatch` | Dispatch | | LIVE |
| Employee | Refunds | `GET /employee/finance/admin/refunds` | Refunds | | LIVE |
| Employee | VAT remittances | `GET /employee/finance/admin/vat-remittances` | VAT | | LIVE |
| Employee | Create VAT remittance | `POST /employee/finance/admin/vat-remittances` | Create | | LIVE |
| Employee | Reconciliation summary | `GET /employee/finance/admin/reconciliation-summary` | Summary | | LIVE |
| Employee | Transfer providers | `GET /employee/finance/admin/transfer-providers` | Providers | | LIVE |
| Employee | COD receipts | `GET /employee/finance/admin/cod-remittance-receipts` | Receipts | | LIVE |
| Employee | Verify COD | `POST /employee/finance/admin/cod-remittance-receipts/{id}/verify` | Verify | | LIVE |
| Employee | Reject COD | `POST /employee/finance/admin/cod-remittance-receipts/{id}/reject` | Reject | | LIVE |
| Employee | COD remittance | `POST /employee/finance/admin/cod-remittance/{settlement_id}` | Remit | | LIVE |
| Employee | Finance summary | `GET /employee/finance/admin/summary` | Summary | | LIVE |
| Employee | Logistics summary | `GET /employee/finance/logistics/summary` | Summary | | LIVE |
| Employee | Supplier summary | `GET /employee/finance/supplier/summary` | Summary | | LIVE |

### D.13 Employee ERP (Orders Domain)

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Purchase orders | `GET /employee/orders/purchase-orders` | PO list | | LIVE |
| Employee | Create PO | `POST /employee/orders/purchase-orders` | New PO | | LIVE |
| Employee | PO detail | `GET /employee/orders/purchase-orders/{id}` | Detail | | LIVE |
| Employee | Confirm PO | `POST /employee/orders/purchase-orders/{id}/confirm` | Confirm | | LIVE |
| Employee | Receive PO | `POST /employee/orders/purchase-orders/{id}/receive` | Goods receipt | | LIVE |
| Employee | Sales orders | `GET /employee/orders/sales-orders` | SO list | | LIVE |
| Employee | Create SO | `POST /employee/orders/sales-orders` | New SO | | LIVE |
| Employee | SO detail | `GET /employee/orders/sales-orders/{id}` | Detail | | LIVE |
| Employee | Confirm SO | `POST /employee/orders/sales-orders/{id}/confirm` | Confirm | | LIVE |
| Employee | Dispatch SO | `POST /employee/orders/sales-orders/{id}/dispatch` | Dispatch | | LIVE |
| Employee | Invoice SO | `POST /employee/orders/sales-orders/{id}/invoice` | Invoice | | LIVE |
| Employee | Goods receipts | `GET /employee/orders/goods-receipts` | GR list | | LIVE |
| Employee | GR detail | `GET /employee/orders/goods-receipts/{id}` | Detail | | LIVE |
| Employee | Three-way match | `POST /employee/orders/three-way-match` | Match | | LIVE |
| Employee | Stock view | `GET /employee/orders/stock` | Stock levels | | LIVE |
| Employee | Stock movements | `GET /employee/orders/stock/movements` | Movement log | | LIVE |
| Employee | Warehouses | `GET /employee/orders/warehouses` | Warehouse list | | LIVE |
| Employee | Create warehouse | `POST /employee/orders/warehouses` | Add | | LIVE |
| Employee | Dunning run | `POST /employee/orders/dunning/run` | Dunning | | LIVE |
| Employee | Job detail | `GET /employee/orders/{job_id}` | Job | | ORPHAN-RBAC |

### D.14 Communications

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee | Inbox | `GET /employee/comms/inbox` | Unified inbox | | LIVE |
| Employee | Unified inbox | `GET /employee/comms/unified-inbox` | Combined | | LIVE |
| Employee | Direct chat | `POST /employee/comms/direct` | 1:1 | WebSocket | LIVE |
| Employee | Group chat | `POST /employee/comms/group` | Create group | | LIVE |
| Employee | Send message | `POST /employee/comms/message` | Message | | LIVE |
| Employee | Chat history | `GET /employee/comms/history/{chat_id}` | Messages | | LIVE |
| Employee | Read receipts | `POST /employee/comms/read` | Mark read | | LIVE |
| Employee | Threads list | `GET /employee/comms/threads` | Threads | | LIVE |
| Employee | Create thread | `POST /employee/comms/threads` | New | | LIVE |
| Employee | Thread messages | `GET /employee/comms/threads/{id}/messages` | Messages | | LIVE |
| Employee | Send thread message | `POST /employee/comms/threads/{id}/messages` | Send | | LIVE |
| Employee | Entity threads | `GET /employee/comms/entity/threads/{id}/messages` | Entity chat | | LIVE |
| Employee | Internal message | `POST /employee/comms/internal` | Internal | | LIVE |
| Employee | Notifications | `GET /employee/comms/notifications` | Notifications | | LIVE |
| Employee | Send notification | `POST /employee/comms/notifications/send` | Send | | ORPHAN-RBAC |
| Employee | Bulk notification | `POST /employee/comms/notifications/bulk` | Bulk | | ORPHAN-RBAC |
| Employee | Mark read | `POST /employee/comms/notifications/{id}/read` | Read | | LIVE |
| Employee | Tickets | `GET /employee/comms/tickets` | Support tickets | | LIVE |
| Employee | Create ticket | `POST /employee/comms/tickets` | Create | | LIVE |
| Employee | Ticket messages | `POST /employee/comms/tickets/{id}/messages` | Message | | LIVE |
| Employee | Reply ticket | `POST /employee/comms/tickets/{id}/reply` | Reply | | LIVE |
| Employee | Email send | `POST /employee/comms/send` | Send email | | LIVE |
| Employee | Bulk email | `POST /employee/comms/send/bulk` | Bulk send | | LIVE |
| Employee | Transactional email | `POST /employee/comms/send/transactional` | Transactional | | LIVE |
| Employee | Alias email | `POST /employee/comms/send/alias` | Alias send | | LIVE |
| Employee | Suppressions | `GET /employee/comms/suppressions` | Suppressed list | | LIVE |
| Employee | Update suppression | `PATCH /employee/comms/suppressions/{id}` | Update | | LIVE |
| Employee | Templates | `GET /employee/comms/templates` | Email templates | | LIVE |
| Employee | Create template | `POST /employee/comms/templates` | Create | | LIVE |
| Employee | Update template | `PUT /employee/comms/templates/{id}` | Edit | | LIVE |
| Employee | Delete template | `DELETE /employee/comms/templates/{id}` | Remove | | LIVE |
| Employee | Campaigns | `GET /employee/comms/campaigns` | List | | LIVE |
| Employee | Create campaign | `POST /employee/comms/campaigns` | New | | LIVE |
| Employee | Email config | `GET /employee/comms/config/runtime` | Config | | LIVE |
| Employee | Update config | `PUT /employee/comms/config/runtime` | Update | | LIVE |
| Employee | Test send | `POST /employee/comms/config/test-send` | Test | | LIVE |
| Employee | Proxy channels | `GET /employee/comms/proxy/channels` | Proxy | | LIVE |
| Employee | Proxy calls | `POST /employee/comms/proxy/calls/initiate` | Call | | ORPHAN-RBAC |
| Employee | End proxy call | `POST /employee/comms/proxy/calls/{id}/end` | End | | ORPHAN-RBAC |
| Employee | Proxy messages | `POST /employee/comms/proxy/messages` | Message | | ORPHAN-RBAC |

### D.15 HR Admin Functions (Employee with Authority)

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Employee (HR) | Admin employees | `GET/POST/PATCH/DELETE /employee/hr/admin/{code}/employees` | Employee CRUD | | LIVE |
| Employee (HR) | Admin offices | `GET/POST/PUT/DELETE /employee/hr/admin/{code}/offices` | Office CRUD | | LIVE |
| Employee (HR) | Employee roles | `GET/POST /employee/hr/admin/{code}/employee-roles` | Role assignment | | LIVE |
| Employee (HR) | Leave admin | `GET/POST/PATCH /employee/hr/admin/{code}/employees/leave-requests` | Leave admin | | LIVE |
| Employee (HR) | Work log approve | `PATCH /employee/hr/admin/{code}/employees/work-logs/{id}/approve` | Approve | | LIVE |
| Employee (HR) | KPI | `POST /employee/hr/hr/kpi` | KPI mgmt | | LIVE |
| Employee (HR) | OKRs | `POST /employee/hr/hr/okr` | OKR mgmt | | LIVE |
| Employee (HR) | Approval chain | `POST /employee/hr/approval-chain` | Define chain | | LIVE |
| Employee (HR) | Reassign manager | `POST /employee/hr/reassign-manager` | Hierarchy change | | LIVE |
| Employee (HR) | Backfill authority | `POST /employee/hr/backfill-authority-levels` | Maintenance | | LIVE |
| Employee (HR) | Country scope | `POST /employee/hr/country-scope/switch` | Switch country | | LIVE |
| Employee (HR) | Scope view | `GET /employee/hr/country-scope/{user_id}` | View | | LIVE |
| Employee (HR) | Localization | `GET /employee/hr/localization/{country_code}` | Config | | LIVE |
| Employee (HR) | Health board | `GET /employee/hr/hr/health-board` | Team health | | LIVE |
| Employee (HR) | Individual health | `GET /employee/hr/hr/health/{id}` | Detail | | LIVE |
| Employee (HR) | HR dashboard | `GET /employee/hr/hr_dashboard/health` | Dashboard | | LIVE |
| Employee (HR) | Shift handover | `GET /employee/hr/shift_handover/health` | Status | | LIVE |
| Employee (HR) | Required authority | `GET /employee/hr/required-authority/{resource_type}` | Policy | | LIVE |
| Employee (HR) | Bench strength | `GET /employee/hr/bench-strength` | Succession | | LIVE |
| Employee (HR) | Successors | `GET /employee/hr/successors/{role_name}` | Succession | | LIVE |
| Employee (HR) | Lock check | `GET /employee/hr/{employee_id}/lock/{permission}` | Permission check | | LIVE |
| Employee (HR) | Progress | `GET /employee/hr/{employee_id}/progress` | Onboarding progress | | LIVE |
| Employee (HR) | Public employee | `GET /employee/hr/public` | Public directory | | LIVE |

---

## E. ADMIN — super_admin

### E.1 Command Center

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Comprehensive dashboard | `GET /admin/command-center/comprehensive-dashboard` | Load | Real-time metrics | LIVE |
| Admin | Dashboard | `GET /admin/command-center/dashboard` | Load | Standard view | LIVE |
| Admin | Dashboard stats | `GET /admin/command-center/dashboard-stats` | Load | Stats | LIVE |
| Admin | Heartbeat | `GET /admin/command-center/heartbeat` | Poll | Health | LIVE |
| Admin | System metrics | `GET /admin/command-center/system-metrics` | Load | System metrics | LIVE |
| Admin | Realtime metrics | `GET /admin/command-center/realtime-metrics` | Poll | Realtime | LIVE |
| Admin | Treasury metrics | `GET /admin/command-center/treasury-metrics` | Load | Treasury | LIVE |
| Admin | Fraud alerts | `GET /admin/command-center/fraud-alerts` | Load | Alerts | LIVE |
| Admin | Alerts list | `GET /admin/command-center/alerts` | Load | List | LIVE |
| Admin | Resolve alert | `POST /admin/command-center/alerts/{id}/resolve` | Resolve | | LIVE |
| Admin | Headlines | `GET /admin/command-center/headlines` | Load | Headlines | LIVE |
| Admin | News list | `GET /admin/command-center/news` | Load | News | LIVE |
| Admin | Create news | `POST /admin/command-center/news` | Add | | LIVE |
| Admin | Delete news | `DELETE /admin/command-center/news/{id}` | Remove | | LIVE |
| Admin | Command center root | `GET /admin/command-center/` | Root | | LIVE |

### E.2 Accounts & Users

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List users | `GET /admin/accounts/users` | User list | | LIVE |
| Admin | Users by country | `GET /admin/accounts/users/{country_code}` | Filter | | LIVE |
| Admin | User detail | `GET /admin/accounts/users/{id}` | Detail | | LIVE |
| Admin | Update user | `PATCH /admin/accounts/users/{id}` | Edit | | LIVE |
| Admin | Delete user | `DELETE /admin/accounts/users/{country_code}/{id}` | Soft delete | | LIVE |
| Admin | Hard delete | `DELETE /admin/accounts/users/{country_code}/{id}/hard` | Hard delete | Rare | LIVE |
| Admin | Archive user | `POST /admin/accounts/users/{country_code}/{id}/archive` | Archive | | LIVE |
| Admin | Restore user | `POST /admin/accounts/users/{country_code}/{id}/restore` | Restore | | LIVE |
| Admin | Toggle active | `POST /admin/accounts/users/{country_code}/{id}/toggle-active` | Toggle | | LIVE |
| Admin | Toggle active (global) | `POST /admin/accounts/users/bulk/toggle-active-global` | Bulk | | LIVE |
| Admin | Assign role | `PATCH /admin/accounts/users/{country_code}/{id}/role` | Role change | Maker-checker | LIVE |
| Admin | Bulk role | `POST /admin/accounts/users/bulk/role` | Bulk | | LIVE |
| Admin | Bulk archive | `POST /admin/accounts/users/bulk/archive` | Bulk | | LIVE |
| Admin | Bulk restore | `POST /admin/accounts/users/bulk/restore` | Bulk | | LIVE |
| Admin | Bulk delete | `POST /admin/accounts/users/bulk/delete` | Bulk | | LIVE |
| Admin | Bulk toggle | `POST /admin/accounts/users/bulk/toggle-active` | Bulk | | LIVE |
| Admin | Reset password | `POST /admin/accounts/users/{country_code}/{id}/reset-password` | Reset | | LIVE |
| Admin | Staff list | `GET /admin/accounts/staff` | Staff | | LIVE |
| Admin | Create staff | `POST /admin/accounts/staff` | Create | | LIVE |
| Admin | Update staff | `PUT /admin/accounts/staff/{id}` | Edit | | LIVE |
| Admin | Delete staff | `DELETE /admin/accounts/staff/{id}` | Remove | | LIVE |
| Admin | Bulk staff | `POST /admin/accounts/staff/bulk` | Bulk | | LIVE |
| Admin | Bank accounts pending | `GET /admin/accounts/bank-accounts/{country_code}/pending` | List | | LIVE |
| Admin | Verify bank account | `POST /admin/accounts/bank-accounts/{country_code}/{kind}/{id}/verify` | Verify | | LIVE |
| Admin | Delete bank account | `DELETE /admin/accounts/bank-accounts/{country_code}/{kind}/{id}` | Remove | | LIVE |

### E.3 Analytics

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Summary | `GET /admin/analytics/summary` | Load | | LIVE |
| Admin | Overview | `GET /admin/analytics/overview` | Load | | ORPHAN-RBAC |
| Admin | Stats | `GET /admin/analytics/stats` | Load | | ORPHAN-RBAC |
| Admin | Timeseries | `GET /admin/analytics/timeseries` | Load | | ORPHAN-RBAC |
| Admin | Top products | `GET /admin/analytics/top-products` | Load | | ORPHAN-RBAC |
| Admin | User growth | `GET /admin/analytics/user-growth` | Load | | ORPHAN-RBAC |
| Admin | Payments | `GET /admin/analytics/payments` | Load | | LIVE |
| Admin | Payouts | `GET /admin/analytics/payouts` | Load | | LIVE |
| Admin | Logistics | `GET /admin/analytics/logistics` | Load | | LIVE |
| Admin | Employees | `GET /admin/analytics/employees` | Load | | LIVE |
| Admin | Chatbot | `GET /admin/analytics/chatbot` | Load | | ORPHAN-RBAC |
| Admin | Commission | `GET /admin/analytics/commission` | Load | | LIVE |
| Admin | Treasury | `GET /admin/analytics/treasury` | Load | | LIVE |
| Admin | Treasury metrics | `GET /admin/analytics/treasury/metrics` | Load | | LIVE |
| Admin | Customer insights | `GET /admin/analytics/customer-insights` | Load | | ORPHAN-RBAC |
| Admin | Provider summary | `GET /admin/analytics/provider/summary` | Load | | ORPHAN-RBAC |
| Admin | Refresh snapshots | `POST /admin/analytics/snapshots/refresh` | Refresh | Celery | ORPHAN-RBAC |
| Admin | Health | `GET /admin/analytics/health` | Health | | LIVE |

### E.4 Country Management

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List countries | `GET /admin/country/` | List | | LIVE |
| Admin | Create country | `POST /admin/country/` | Create | | LIVE |
| Admin | Country detail | `GET /admin/country/{code}` | Detail | | LIVE |
| Admin | Update country | `PATCH /admin/country/{code}` | Edit | | LIVE |
| Admin | Delete country | `DELETE /admin/country/{code}` | Soft delete | | LIVE |
| Admin | Toggle active | `POST /admin/country/{code}/toggle-active` | Toggle | | LIVE |
| Admin | Archive | `POST /admin/country/{code}/archive` | Archive | | LIVE |
| Admin | Restore | `POST /admin/country/{code}/restore` | Restore | | LIVE |
| Admin | Country config | `GET /admin/country/{code}/config` | Config view | | ORPHAN-RBAC |
| Admin | Bulk archive | `POST /admin/country/bulk/archive` | Bulk | | ORPHAN-RBAC |
| Admin | Bulk restore | `POST /admin/country/bulk/restore` | Bulk | | ORPHAN-RBAC |
| Admin | List cities | `GET /admin/country/{code}/cities` | Cities | | ORPHAN-RBAC |
| Admin | Create city | `POST /admin/country/{code}/cities` | Add | | ORPHAN-RBAC |
| Admin | Update city | `PUT /admin/country/{code}/cities/{id}` | Edit | | ORPHAN-RBAC |
| Admin | Delete city | `DELETE /admin/country/{code}/cities/{id}` | Remove | | ORPHAN-RBAC |
| Admin | List staff | `GET /admin/country/{code}/staff` | Staff | | LIVE |
| Admin | Assign staff | `POST /admin/country/{code}/staff` | Assign | | LIVE |
| Admin | Delete staff | `DELETE /admin/country/{code}/staff/{id}` | Remove | | LIVE |
| Admin | Tax rates | `GET /admin/country/{code}/tax-rates` | Tax list | | ORPHAN-RBAC |
| Admin | Create tax rate | `POST /admin/country/{code}/tax-rates` | Add | | ORPHAN-RBAC |
| Admin | Communications | `GET /admin/country/communications` | List | | LIVE |
| Admin | Send communication | `POST /admin/country/{code}/communications` | Send | | LIVE |
| Admin | Mark read | `PUT /admin/country/communications/{id}/read` | Read | | LIVE |
| Admin | List commission rates | `GET /admin/country/countries/{code}/commission-rates` | Rates | | LIVE |
| Admin | Create commission rate | `POST /admin/country/countries/{code}/commission-rates` | Add | | LIVE |
| Admin | Delete commission rate | `DELETE /admin/country/countries/{code}/commission-rates/{tier}/{name}` | Remove | | LIVE |

### E.5 Config Versions

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List versions | `GET /admin/config_versions/{country_code}` | List | | LIVE |
| Admin | Create version | `POST /admin/config_versions/{country_code}` | Draft | | LIVE |
| Admin | Version detail | `GET /admin/config_versions/{country_code}/{id}` | Detail | | LIVE |
| Admin | Update version | `PATCH /admin/config_versions/{country_code}/{id}` | Edit | | LIVE |
| Admin | Approve version | `POST /admin/config_versions/{country_code}/{id}/approve` | Approve | Maker-checker | LIVE |
| Admin | Publish version | `POST /admin/config_versions/{country_code}/{id}/publish` | Publish | | LIVE |
| Admin | Archive version | `POST /admin/config_versions/{country_code}/{id}/archive` | Archive | | LIVE |

### E.6 Catalog

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List products | `GET /admin/catalog/products/{country_code}` | List | | LIVE |
| Admin | Pending products | `GET /admin/catalog/products/{country_code}/pending` | Pending | | LIVE |
| Admin | Approve product | `PUT /admin/catalog/products/{country_code}/{id}/approve` | Approve | | LIVE |
| Admin | Reject product | `PUT /admin/catalog/products/{country_code}/{id}/reject` | Reject | | LIVE |
| Admin | Badge product | `PATCH /admin/catalog/products/{country_code}/{id}/badge` | Badge | | LIVE |
| Admin | Archive product | `POST /admin/catalog/products/{country_code}/{id}/archive` | Archive | | LIVE |
| Admin | Restore product | `POST /admin/catalog/products/{country_code}/{id}/restore` | Restore | | LIVE |
| Admin | Delete product | `DELETE /admin/catalog/products/{country_code}/{id}` | Delete | | LIVE |
| Admin | Bulk archive | `POST /admin/catalog/products/{country_code}/bulk/archive` | Bulk | | LIVE |
| Admin | Bulk restore | `POST /admin/catalog/products/{country_code}/bulk/restore` | Bulk | | LIVE |
| Admin | Bulk moderate | `POST /admin/catalog/products/{country_code}/bulk/moderate` | Bulk | | LIVE |
| Admin | Bulk category change | `POST /admin/catalog/products/{country_code}/bulk/category-change` | Bulk | | LIVE |
| Admin | List categories | `GET /admin/catalog/categories/{country_code}` | List | | LIVE |
| Admin | Create category | `POST /admin/catalog/categories/{country_code}` | Add | | LIVE |
| Admin | Update category | `PUT /admin/catalog/categories/{country_code}/{id}` | Edit | | LIVE |
| Admin | Delete category | `DELETE /admin/catalog/categories/{country_code}/{id}` | Remove | | LIVE |
| Admin | Archive category | `POST /admin/catalog/categories/{country_code}/{id}/archive` | Archive | | LIVE |
| Admin | Restore category | `POST /admin/catalog/categories/{country_code}/{id}/restore` | Restore | | LIVE |
| Admin | Reorder categories | `POST /admin/catalog/categories/{country_code}/reorder` | Reorder | | LIVE |
| Admin | Bulk archive cats | `POST /admin/catalog/categories/{country_code}/bulk/archive` | Bulk | | LIVE |
| Admin | Bulk restore cats | `POST /admin/catalog/categories/{country_code}/bulk/restore` | Bulk | | LIVE |

### E.7 Orders

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Orders list | `GET /admin/orders/campaigns` | Orders list | | LIVE |
| Admin | Orders metrics | `GET /admin/orders/metrics` | Metrics | | LIVE |
| Admin | Campaigns detail | `GET /admin/orders/campaigns/{country_code}` | Campaigns | | LIVE |
| Admin | Create campaign | `POST /admin/orders/campaigns/{country_code}` | Add | | LIVE |
| Admin | Delete campaign | `DELETE /admin/orders/campaigns/{country_code}/{id}` | Remove | | LIVE |
| Admin | Orders routes health | `GET /admin/orders/admin_orders_routes/health` | Health | | ORPHAN-RBAC |

### E.8 Disputes

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List disputes | `GET /admin/disputes` | List | | LIVE |
| Admin | Update dispute | `PATCH /admin/disputes/{id}` | Resolve | | LIVE |
| Admin | Bulk update | `POST /admin/disputes/bulk` | Bulk | | LIVE |

### E.9 Finance

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Rates list | `GET /admin/finance/{country_code}/rates` | Rates | | ORPHAN-RBAC |
| Admin | Create rate | `POST /admin/finance/{country_code}/rates` | Add | | ORPHAN-RBAC |
| Admin | Update rate | `PUT /admin/finance/{country_code}/rates/{id}` | Edit | | ORPHAN-RBAC |
| Admin | Badge tiers | `GET /admin/finance/{country_code}/badge-tiers` | List | | ORPHAN-RBAC |
| Admin | Create badge tier | `POST /admin/finance/{country_code}/badge-tiers` | Add | | ORPHAN-RBAC |
| Admin | Update badge tier | `PUT /admin/finance/{country_code}/badge-tiers/{id}` | Edit | | ORPHAN-RBAC |

### E.10 Governance

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Config checkout | `GET /admin/governance/config/checkout` | Config | | ORPHAN-RBAC |

### E.11 HR

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | COI check | `GET /admin/hr/hr/{id}/coi-check` | Check | | LIVE |
| Admin | COI report | `POST /admin/hr/hr/{id}/coi-report` | Report | | ORPHAN-RBAC |
| Admin | Disciplinary | `GET /admin/hr/hr/disciplinary` | List | | ORPHAN-RBAC |
| Admin | Create disciplinary | `POST /admin/hr/hr/{id}/disciplinary` | Create | | ORPHAN-RBAC |
| Admin | Offboarding | `GET /admin/hr/hr/offboarding` | List | | ORPHAN-RBAC |
| Admin | Create offboarding | `POST /admin/hr/hr/{id}/offboarding` | Initiate | | ORPHAN-RBAC |
| Admin | Compliance work hours | `GET /admin/hr/compliance/work-hours/{id}` | Report | | LIVE |
| Admin | Compliance report | `GET /admin/hr/compliance/report/{id}` | Report | | LIVE |
| Admin | Overtime | `POST /admin/hr/compliance/overtime` | Calculate | | LIVE |
| Admin | Employee expenses | `POST /admin/hr/employees/{id}/expenses` | Submit | | LIVE |
| Admin | Employee assets | `POST /admin/hr/employees/{id}/assets` | Assign | | LIVE |
| Admin | Employee leave balance | `GET /admin/hr/employees/{id}/leave-balance` | View | | LIVE |
| Admin | Employee addresses | `POST /admin/hr/hr/{id}/addresses` | Add | | LIVE |
| Admin | Employee dependents | `POST /admin/hr/hr/{id}/dependents` | Add | | LIVE |
| Admin | Employee graph | `GET /admin/hr/hr/{id}/graph` | Graph | | LIVE |
| Admin | Employee compliance | `GET /admin/hr/hr/{id}/compliance` | Compliance | | LIVE |

### E.12 Logistics

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Partners list | `GET /admin/logistics/{country_code}/partners` | List | | LIVE |
| Admin | Approve partner | `PUT /admin/logistics/{country_code}/partners/{id}/approve` | Approve | | LIVE |
| Admin | Reject partner | `PUT /admin/logistics/{country_code}/partners/{id}/reject` | Reject | | LIVE |
| Admin | Toggle partner | `POST /admin/logistics/{country_code}/partners/{id}/toggle-active` | Toggle | | LIVE |
| Admin | Archive partner | `POST /admin/logistics/{country_code}/partners/{id}/archive` | Archive | | LIVE |
| Admin | Restore partner | `POST /admin/logistics/{country_code}/partners/{id}/restore` | Restore | | LIVE |
| Admin | Delete partner | `DELETE /admin/logistics/{country_code}/partners/{id}` | Delete | | LIVE |
| Admin | Logistics routes health | `GET /admin/logistics/admin_logistics_routes/health` | Health | | ORPHAN-RBAC |

### E.13 Promotions

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | List banners | `GET /admin/promotions/banners/{country_code}` | List | | LIVE |
| Admin | All banners | `GET /admin/promotions/banners/{country_code}/all` | All | | LIVE |
| Admin | Create banner | `POST /admin/promotions/banners/{country_code}` | Add | | LIVE |
| Admin | Update banner | `PUT /admin/promotions/banners/{country_code}/{id}` | Edit | | LIVE |
| Admin | Delete banner | `DELETE /admin/promotions/banners/{country_code}/{id}` | Remove | | LIVE |
| Admin | Promotions routes health | `GET /admin/promotions/admin_promotions_routes/health` | Health | | ORPHAN-RBAC |

### E.14 Security

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Security events | `GET /admin/security/events` | Events | | ORPHAN-RBAC |
| Admin | Score entity | `POST /admin/security/score` | Score | Fraud | ORPHAN-RBAC |
| Admin | Blacklist | `GET /admin/security/blacklist` | List | | ORPHAN-RBAC |
| Admin | Add blacklist | `POST /admin/security/blacklist` | Add | | ORPHAN-RBAC |
| Admin | Remove blacklist | `DELETE /admin/security/blacklist/{id}` | Remove | | ORPHAN-RBAC |
| Admin | Rules | `GET /admin/security/rules` | List | | ORPHAN-RBAC |
| Admin | Create rule | `POST /admin/security/rules` | Add | | ORPHAN-RBAC |
| Admin | Review queue | `GET /admin/security/review` | Review | | ORPHAN-RBAC |
| Admin | Threat feeds | `GET /admin/security/threat-feeds/status` | Status | | ORPHAN-RBAC |
| Admin | Update threat feeds | `POST /admin/security/threat-feeds/update` | Update | | ORPHAN-RBAC |
| Admin | Risk score view | `GET /admin/security/{employee_id}/risk-score` | View | | ORPHAN-RBAC |
| Admin | Ghost employees | `GET /admin/ghost-employees` | List | | ORPHAN-RBAC |
| Admin | Impossible travel | `GET /admin/impossible-travel` | List | | ORPHAN-RBAC |
| Admin | Team health | `GET /admin/team-health/{manager_id}` | Health | | ORPHAN-RBAC |
| Admin | Audit timeline | `GET /admin/{employee_id}/audit-timeline` | Timeline | | ORPHAN-RBAC |
| Admin | Risk score update | `POST /admin/{employee_id}/risk-score` | Update | | ORPHAN-RBAC |
| Admin | RBAC catalog | `GET /rbac/catalog` | Catalog | | LIVE |
| Admin | OTP start | `POST /admin/otp/start` | Start OTP | | ORPHAN-RBAC |
| Admin | OTP verify | `POST /admin/otp/verify` | Verify OTP | | ORPHAN-RBAC |

### E.15 Permissions & RBAC

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Categories | `GET /admin/permissions/categories` | List | | LIVE |
| Admin | Create category | `POST /admin/permissions/categories` | Add | | LIVE |
| Admin | Delete category | `DELETE /admin/permissions/categories/{id}` | Remove | | LIVE |
| Admin | Permissions list | `GET /admin/permissions/list` | All atoms | | LIVE |
| Admin | Assign role | `POST /admin/permissions/roles/assign` | Grant | Maker-checker | LIVE |
| Admin | Revoke role | `POST /admin/permissions/roles/revoke` | Revoke | | LIVE |
| Admin | Role detail | `GET /admin/permissions/roles/{role}` | Detail | | LIVE |
| Admin | User override | `POST /admin/permissions/users/override` | Override | | LIVE |

### E.16 Staff

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Staff list | `GET /admin/staff` | List | | LIVE |
| Admin | Create staff | `POST /admin/staff` | Create | | LIVE |
| Admin | Update staff | `PUT /admin/staff/{id}` | Edit | | LIVE |
| Admin | Patch staff | `PATCH /admin/staff/{id}` | Partial | | LIVE |
| Admin | Delete staff | `DELETE /admin/staff/{id}` | Remove | | LIVE |
| Admin | Bulk update | `PUT /admin/staff/bulk` | Bulk | | LIVE |
| Admin | Permission catalog | `GET /admin/staff/permission-catalog` | Catalog | | LIVE |
| Admin | Users | `GET /admin/users` | Users | | LIVE |
| Admin | Reset password | `POST /admin/users/{id}/reset-password` | Reset | | LIVE |

### E.17 Suppliers

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Suppliers list | `GET /admin/suppliers` | List | | LIVE |
| Admin | Supplier detail | `GET /admin/suppliers/{id}` | Detail | | LIVE |
| Admin | Supplier products | `GET /admin/suppliers/{id}/products` | Products | | LIVE |
| Admin | Resolve slug | `GET /admin/suppliers/resolve/{slug}` | Resolve | | ORPHAN-RBAC |
| Admin | Admin suppliers health | `GET /admin/suppliers/admin_suppliers_routes/health` | Health | | ORPHAN-RBAC |
| Admin | Public suppliers health | `GET /admin/suppliers/public_suppliers_routes/health` | Health | | ORPHAN-RBAC |

### E.18 Tickets

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Ticket list | `GET /admin/tickets` | List | | LIVE |
| Admin | Ticket detail | `GET /admin/tickets/{id}` | Detail | | LIVE |
| Admin | Reply | `POST /admin/tickets/{id}/reply` | Reply | | LIVE |
| Admin | Update status | `PUT /admin/tickets/{id}/status` | Status | | LIVE |

### E.19 Audit & Communications

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Audit list | `GET /admin/comms/audit` | List | | LIVE |
| Admin | Audit export | `GET /admin/comms/audit/export` | Export | | LIVE |
| Admin | Campaigns | `GET /admin/comms/campaigns` | List | | LIVE |
| Admin | Campaign detail | `GET /admin/comms/campaigns/{country_code}` | Detail | | LIVE |
| Admin | Create campaign | `POST /admin/comms/campaigns/{country_code}` | Add | | LIVE |
| Admin | Delete campaign | `DELETE /admin/comms/campaigns/{country_code}/{id}` | Remove | | LIVE |
| Admin | Metrics | `GET /admin/comms/metrics` | Metrics | | LIVE |

### E.20 Customers (Admin)

| Actor | Feature | Key Action | Workflow Step | Detail Description | Status |
|---|---|---|---|---|---|
| Admin | Referrals config | `GET /admin/customers/referrals/config` | Config | | LIVE |
| Admin | Reviews list | `GET /admin/customers/reviews` | List | | LIVE |
| Admin | Reviews by product | `GET /admin/customers/reviews/products/{id}` | Filter | | LIVE |
| Admin | Update review | `PUT /admin/customers/reviews/{id}` | Edit | | LIVE |
| Admin | Add wishlist | `POST /admin/customers/{product_id}` | Add | | ORPHAN-RBAC |
| Admin | Delete wishlist | `DELETE /admin/customers/` | Remove | | ORPHAN-RBAC |
| Admin | List wishlist | `GET /admin/customers/` | List | | ORPHAN-RBAC |

---

## F. ADMIN — Sub-roles

Sub-roles are `super_admin` with a bounded feature set. No folder-level separation. Enforced via RBAC.

| Role | Purpose | Key Capabilities |
|---|---|---|
| `sub_admin` | Bounded administrator | Configurable subset of super_admin's features, restricted to a set of countries and modules |
| `moderator` | Catalog + supplier doc review | `catalog.write`, `catalog.category.manage`, `suppliers.documents.write`, `suppliers.verification.manage` |
| `finance_officer` | Finance operations | `finance.*`, `accounts.bank-accounts.*`, `governance.treasury.read`, `governance.analytics.read` |
| `country_manager` | Single-country admin | Country-scoped full admin (except super_admin actions like creating countries) |
| `auditor` | Read-only compliance | `audit.read`, `audit.logs.export`, `governance.analytics.read`, `finance.*.read` (all read-only) |

**Enforcement rules:**
- Sub-admin cannot grant a permission they don't hold (checked in `/admin/permissions/roles/assign`).
- Country_manager's RLS context is locked to their assigned country.
- Sensitive grants (`finance.*`, `accounts.user.delete`) require maker-checker.

---

## G. SYSTEM — Automated Actors

### G.1 Cron Jobs

| Actor | Feature | Trigger | Detail | Status |
|---|---|---|---|---|
| System | Payout sweep | Daily 02:00 UTC | Aggregate + create payout batches | LIVE |
| System | Reconciliation cron | Hourly | Match bank ↔ ledger | LIVE |
| System | Bank statement importer | Daily | Pull statements | LIVE |
| System | FX revaluation | Month-end | Revalue foreign-currency balances | LIVE |
| System | Accrual reversal | Month-start | Reverse prior-month accruals | LIVE |
| System | Payroll run | Monthly | Per-country payroll batch | LIVE |
| System | Fraud monitoring | Every 5 min | Score pending orders | LIVE |
| System | Ghost order detector | Daily | Stuck orders > 48h | LIVE |
| System | Data retention | Weekly | Purge expired data | LIVE |
| System | Threat feed updater | Hourly | Update threat intel | LIVE |

### G.2 Event-Driven

| Actor | Feature | Trigger | Detail | Status |
|---|---|---|---|---|
| System | Send verification email | `user.created` | Queued email | LIVE |
| System | Send order confirmation | `order.paid` | Email + push | LIVE |
| System | Send payout notification | `payout.dispatched` | Email + SMS | LIVE |
| System | Update supplier credibility | `order.delivered` | Recompute | LIVE |
| System | Update order status | `payment.captured` | Confirm order | LIVE |
| System | Dunning email | Order overdue | Reminder | LIVE |
| System | Leave escalation | SLA breach | Escalate to next authority | LIVE |
| System | Activity ledger write | Any state change | Append to ledger | LIVE |
| System | Audit log write | Any state change | WORM | LIVE |

### G.3 Webhooks

| Actor | Feature | Trigger | Detail | Status |
|---|---|---|---|---|
| System | Payment webhook | `POST /webhooks/payments/{slug}` | Verify signature, emit event | LIVE |
| System | Email webhook (Resend) | `POST /webhooks/email/resend` | Delivery events | LIVE |
| System | SMS webhook | `POST /webhooks/sms/{provider}` | Delivery receipts | LIVE |
| System | Bank webhook | `POST /webhooks/bank/{provider}` | Transaction events | LIVE |

---

## H. Features Still Wanted (Not Built)

Features we need but do not have. Each is a fresh build.

### H.1 Admin Sub-Role UX

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Admin | Sub-role dedicated UI | `/admin/sub-roles` page | Currently no UI to manage sub_admin, moderator, etc. | MISSING |
| Admin | Country scope switcher in admin header | Session UI | Multi-country admin needs switch | MISSING |
| Admin | Automation control panel | `/admin/automation` | Toggle jobs, view exceptions | MISSING |
| Admin | Exception queue UI | `/admin/exceptions` | Failed jobs, mismatches | MISSING |
| Admin | Command center alerts drill-down | UI | Per-alert detail view | MISSING |

### H.2 Supplier Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Supplier | Analytics report export | `POST /supplier/analytics/export` | CSV/PDF download | MISSING |
| Supplier | Batch product edit | UI | Bulk update across N products | MISSING |
| Supplier | Contract view/sign | `GET /supplier/contracts` | Legal contract | MISSING |
| Supplier | Insurance upload | `POST /supplier/insurance` | Policy docs | MISSING |
| Supplier | Storefront customization | `/supplier/storefront` | Public page editor | MISSING |

### H.3 Logistics Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Logistics | Fleet management (company) | `/logistics-partner/fleet` | Drivers, vehicles, assignments | MISSING |
| Logistics | Driver list | `GET /logistics/fleet/drivers` | Manage drivers | MISSING |
| Logistics | Vehicle registry | `GET /logistics/fleet/vehicles` | Fleet vehicles | MISSING |
| Logistics | Route optimization | AI-suggested routes | Batch routing | MISSING |
| Logistics | Live tracking map (partner view) | UI | Current shipments on map | MISSING |

### H.4 Employee Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Employee | Mobile EMS app | `app/(tabs)/employee/*` | No mobile screens yet | MISSING |
| Employee | ESS portal | Self-service page | Profile, docs, leave, payslips | MISSING |
| Employee | Internal email client | `/employee/comms/email` | Inbox, compose | MISSING |
| Employee | Video meeting scheduler | `/employee/comms/video` | Calendar + invites | MISSING |
| Employee | Employee workspace | `/employee/workspace` | Unified dashboard | MISSING |
| Employee | Training module UI | `/employee/training` | LMS interface | MISSING |
| Employee | Schedule view | `/employee/schedule` | Shift calendar | MISSING |
| Employee | Task board | `/employee/workspace/tasks` | Personal tasks | MISSING |

### H.5 Customer Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Customer | Live order tracking map | UI | Real-time on map | MISSING |
| Customer | Chatbot with AI | `/chatbot` | Local ollama | FE-ONLY |
| Customer | Product Q&A | `POST /customer/catalog/{id}/questions` | Ask seller | MISSING |
| Customer | Gift cards | `POST /customer/promotions/gift-cards` | Send/redeem | MISSING |
| Customer | Subscription orders | `POST /customer/orders/subscriptions` | Recurring | MISSING |

### H.6 Automation Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| System | Auto-rostering | Weekly cron | Publish shifts | MISSING |
| System | Auto-leave approval | On request | ≤3 days + no conflict | MISSING |
| System | Auto-offboarding | On termination | Revoke + transfer + EOSB | MISSING |
| System | Auto-onboarding | On offer accepted | Pipeline execution | MISSING |
| System | Auto-COI detection | On hierarchy change | Flag conflicts | MISSING |
| System | Auto-attendance anomaly | On scan | Geolocation + device trust | LIVE |
| System | Auto-performance signals | Nightly | Health scores | MISSING |
| System | Auto document expiry alerts | Daily | 30/14/7 day warnings | MISSING |
| System | Auto comms compliance | On message write | DLP + legal-hold | PARTIAL |
| System | Auto meeting intelligence | On recording end | Transcript → actions | PARTIAL |

### H.7 Security & Compliance

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Admin | KYC verification UI | `/admin/security/kyc` | Document review | MISSING |
| Admin | DLP violation review | `/admin/security/dlp` | Quarantine list | MISSING |
| Admin | Legal hold controls | `/admin/security/legal-holds` | Freeze data | MISSING |
| Admin | Data residency map | `/admin/country/residency` | Compliance view | MISSING |
| Admin | PCI-DSS audit view | `/admin/security/pci` | Compliance dashboard | MISSING |

### H.8 Analytics Enhancements

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| Admin | Attrition risk model | `GET /admin/analytics/attrition` | Predictive | MISSING |
| Admin | DEI dashboard | `GET /admin/analytics/dei` | Equity metrics | MISSING |
| Admin | Cohort analysis | `GET /admin/analytics/cohorts` | User cohorts | MISSING |
| Admin | Custom report builder | `/admin/analytics/builder` | Drag-drop reports | MISSING |
| Admin | Scheduled report emails | `POST /admin/analytics/schedule` | Auto-deliver | MISSING |

### H.9 Integrations

| Actor | Feature | Key Action | Detail | Status |
|---|---|---|---|---|
| System | Twilio SMS | `POST /webhooks/sms/twilio` | Self-hosted SMS | PARTIAL |
| System | WhatsApp Cloud API | `POST /webhooks/whatsapp` | Self-hosted WA | PARTIAL |
| System | Resend email | `POST /webhooks/email/resend` | Alt SMTP | LIVE |
| System | Bank API (open banking) | `POST /webhooks/bank` | Auto-import statements | PARTIAL |
| System | Stripe Connect | `POST /webhooks/stripe/connect` | Supplier onboarding | PARTIAL |

---

## I. Feature Counts by Actor

| Actor | Live | BE-Only | FE-Only | Gated | Ungated | Orphan-RBAC | Missing |
|---|---|---|---|---|---|---|---|
| Customer | ~65 | 0 | 5 | 0 | 0 | ~20 | ~8 |
| Supplier | ~45 | 12 | 5 | 0 | 0 | ~10 | ~10 |
| Logistics | ~50 | 5 | 0 | 0 | 0 | ~5 | ~10 |
| Employee | ~110 | 5 | 0 | 0 | 0 | ~25 | ~10 |
| Admin (super) | ~200 | 0 | 0 | 0 | ~30 | ~50 | ~20 |
| Admin (sub-roles) | 0 | 0 | 0 | 0 | 0 | 0 | ~10 |
| System | ~25 | 0 | 0 | 0 | 0 | 0 | ~15 |
| **TOTAL** | **~495** | **~22** | **~10** | **0** | **~30** | **~110** | **~85** |

---

## J. How to Use This Register

1. **Pick one actor.** Start with the actor whose features you use most.
2. **For each row:** verify the endpoint works, the feature gate is applied, the RLS is set, the audit is written.
3. **Update Status** in this file. Move `ORPHAN-RBAC` → `LIVE` after wiring the frontend. Move `MISSING` → `BE-ONLY` after building the endpoint.
4. **Never let a row linger.** A row with `MISSING` for more than a sprint either becomes a ticket or is deleted from scope.
5. **Regenerate this register quarterly** from `_feature_extraction/02_inventory.md` + a frontend surface scan + `SECURITY_POSTURE.md`.

---

*End of complete feature register. This is the working document; update it as features ship or are removed.*