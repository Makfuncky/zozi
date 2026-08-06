# Email System Audit

## Scope

This document tracks the current email-system implementation across `frontend/web_app`, `frontend/mobile_app`, `backend`, backend API routes, database setup, tests, and the runtime email configuration slice that was just implemented.

## Current Status

- Working now:
  - customer email verification and resend flows
  - password reset email flow
  - newsletter subscribe, unsubscribe, and preference management
  - admin email templates and campaign management
  - A/B subject testing and campaign recipient analytics primitives
  - DB-backed runtime email provider configuration with hot-reload and admin test-send API
  - Resend webhook verification, delivery event persistence, and suppression handling
  - transactional milestone emails for order creation, payment, refund, return, and shipment updates
- Implemented backend gaps closed in this pass:
  - runtime provider selection without restart
  - purpose-specific sender identity mapping
  - admin API to read, update, and test email configuration
  - Alembic-backed persistence for runtime email config
  - delivery event and suppression tables plus Resend webhook ingestion
- Still missing:
  - mobile admin UI for provider settings and test-send
  - richer suppression management/reporting UI
  - deeper transactional coverage for additional finance/logistics edge cases

## Backend Inventory

### Core Models and Database Setup

| File | Key email models / setup | Notes |
| --- | --- | --- |
| `backend/db/models.py` | `EmailVerificationToken`, `PasswordResetToken`, `NewsletterSubscriber`, `EmailTemplate`, `EmailCampaign`, `CampaignRecipient`, `EmailProviderConfig` | `EmailProviderConfig` is the runtime source of truth for admin-managed provider credentials, sender addresses, and delivery mode. |
| `backend/db/schemas.py` | `EmailProviderConfigUpdate`, `EmailProviderConfigSchema`, `EmailTestSendRequest`, newsletter/template/campaign schemas | Runtime config responses intentionally expose only capability flags, not secrets. |
| `backend/alembic/versions/78b323427448_add_email_marketing_models.py` | newsletter, template, campaign, recipient schema | Existing email marketing schema migration. |
| `backend/alembic/versions/g1h2i3j4k5l6_add_email_ab_and_gps_fields.py` | A/B subject-line campaign fields | Adds `subject_b`, `ab_test_enabled`, `ab_winner_variant`. |
| `backend/alembic/versions/y4z5a6b7c8d9_add_email_provider_runtime_config.py` | runtime provider config table | New migration for hot-reload provider settings and sender identities. |
| `backend/db/seed.py` | seeded email templates | Seeds welcome, flash-sale, new-arrivals, and abandoned-cart templates. |

### Controllers and Service Layer

| File | Key functions | Notes |
| --- | --- | --- |
| `backend/controllers/email_controller.py` | `subscribe_to_newsletter`, `unsubscribe_from_newsletter`, `unsubscribe_with_token`, `get_newsletter_preferences`, `update_newsletter_preferences`, template CRUD, campaign CRUD, `queue_email_campaign_send`, `get_campaign_analytics`, `track_email_open`, `track_email_click`, `get_email_provider_config`, `update_email_provider_config`, `send_test_email_message` | Central email domain controller for newsletter, campaign, analytics, and runtime provider management. |
| `backend/controllers/auth_controller.py` | registration verification send flow, resend verification flow, forgot-password and reset-password email flow | Auth is the main transactional-email entrypoint currently wired end-to-end. |
| `backend/utils/email_service.py` | `send_email`, `send_verification_email`, `send_password_reset_email`, `send_newsletter_welcome_email`, `send_promotional_campaign_email`, `get_email_delivery_status`, `get_email_sender_address`, `refresh_email_runtime_config_cache`, `invalidate_email_runtime_config_cache` | Resolves live transport from DB config first, env config second, preview fallback last. Supports sender purposes: default, promotional, transactional, notification, alert, verification, login_verification, password_reset. |
| `backend/utils/config.py` | email transport settings, `customer_email_verification_mode` | Still provides bootstrap defaults and verification gating behavior. |
| `backend/utils/background_jobs.py` | background job registry used by campaign send queue | Campaign sending remains background-job driven. |

### API Surface

| File | Routes / usage |
| --- | --- |
| `backend/routers/email.py` | `GET /email/config/runtime`, `PUT /email/config/runtime`, `POST /email/config/test-send`, `POST /email/webhooks/resend`, newsletter endpoints, template CRUD routes, campaign CRUD routes, campaign send, analytics, open tracking, click tracking |
| `backend/routers/auth.py` | verify-email, resend-verification, forgot-password, reset-password routes that trigger email delivery |

### Tests

| File | Coverage |
| --- | --- |
| `backend/tests/test_email_runtime_config.py` | admin runtime config read/update, SMTP validation, non-admin rejection, hot-reload test-send path |
| `backend/tests/test_email_webhooks_and_transactional_flows.py` | Resend webhook verification + suppression persistence, order/payment/refund email hooks, return milestone emails, shipment update emails |
| `backend/tests/test_email_campaigns.py` | campaign CRUD, delivery queueing, analytics behavior |
| `backend/tests/test_email_ab.py` | A/B subject testing flows |
| `backend/tests/test_auth.py` | verification, resend, password reset, and auth gating interactions |
| `backend/tests/test_startup_schema_bootstrap.py` | startup/Alembic schema bootstrap safety |

## Frontend Web Inventory

| File | Key UI responsibility | Current state |
| --- | --- | --- |
| `frontend/web_app/src/app/admin/email/page.tsx` | admin email dashboard entrypoint | Covers overview, campaign management, template management, and a delivery-settings tab. |
| `frontend/web_app/src/components/admin/EmailProviderConfigManager.tsx` | runtime provider config form, sender mapping, test-send | New web admin UI for `GET/PUT /email/config/runtime` and `POST /email/config/test-send`. |
| `frontend/web_app/src/components/admin/EmailCampaignManager.tsx` | campaign list, send, status, analytics affordances | Uses campaign API but does not expose runtime provider status or test-send. |
| `frontend/web_app/src/components/admin/EmailTemplateManager.tsx` | template CRUD and editing | Template management exists; no visual builder. |
| `frontend/web_app/src/components/admin/CreateCampaignForm.tsx` | campaign draft creation UI | Supports subject, template, audience, and A/B subject inputs. |
| `frontend/web_app/src/app/verify-email/page.tsx` | verification landing page | Consumes auth verify-email flow. |
| `frontend/web_app/src/app/forgot-password/page.tsx` | forgot-password request form | Sends password-reset request. |
| `frontend/web_app/src/app/reset-password/page.tsx` | password reset completion form | Completes token-based reset flow. |
| `frontend/web_app/src/app/newsletter/page.tsx` | newsletter landing surface | Customer-facing newsletter entrypoint. |
| `frontend/web_app/src/app/newsletter/preferences/page.tsx` | newsletter preference management | Uses newsletter preference APIs. |
| `frontend/web_app/src/app/newsletter/unsubscribe/page.tsx` | unsubscribe confirmation flow | Browser landing for unsubscribe links. |
| `frontend/web_app/src/components/NewsletterSignup.tsx` | reusable signup component | Public newsletter subscription UI. |
| `frontend/shared/src/adminPermissions.ts` | `canAccessAdminEmailManagement()` | Admin-only gating for current email admin UI. |

## Frontend Mobile Inventory

| File | Key UI responsibility | Current state |
| --- | --- | --- |
| `frontend/mobile_app/app/admin/email.tsx` | mobile admin email dashboard | Mirrors campaigns/templates surfaces; no provider-config form yet. |
| `frontend/mobile_app/app/(auth)/verify-email.tsx` | verification flow screen | Mobile verification landing. |
| `frontend/mobile_app/app/(auth)/forgot-password.tsx` | forgot-password request form | Triggers reset email flow. |
| `frontend/mobile_app/app/(auth)/reset-password.tsx` | password reset completion | Token-based reset on mobile. |
| `frontend/mobile_app/app/edit-profile.tsx` | resend verification action and status | Shows email verification state to signed-in users. |
| `frontend/mobile_app/app/change-password.tsx` | authenticated password change | Separate from token-based reset flow. |
| `frontend/mobile_app/components/NewsletterSignup.tsx` | reusable newsletter signup UI | Mobile newsletter opt-in surface. |

## File and Function Summary by Responsibility

### Verification and Account Recovery

- `backend/controllers/auth_controller.py`: account verification send, resend verification, forgot-password, reset-password
- `backend/utils/email_service.py`: delivery helpers used by auth
- `backend/db/models.py`: `EmailVerificationToken`, `PasswordResetToken`
- `frontend/web_app/src/app/verify-email/page.tsx`: verify-email page
- `frontend/web_app/src/app/forgot-password/page.tsx`: forgot-password page
- `frontend/web_app/src/app/reset-password/page.tsx`: reset-password page
- `frontend/mobile_app/app/(auth)/verify-email.tsx`: mobile verify-email screen
- `frontend/mobile_app/app/(auth)/forgot-password.tsx`: mobile forgot-password screen
- `frontend/mobile_app/app/(auth)/reset-password.tsx`: mobile reset-password screen

### Newsletter and Subscription Preferences

- `backend/controllers/email_controller.py`: newsletter subscribe, unsubscribe, preference read/update
- `backend/routers/email.py`: public and authenticated newsletter routes
- `backend/db/models.py`: `NewsletterSubscriber`
- `frontend/web_app/src/components/NewsletterSignup.tsx`: signup widget
- `frontend/web_app/src/app/newsletter/preferences/page.tsx`: preference management
- `frontend/web_app/src/app/newsletter/unsubscribe/page.tsx`: unsubscribe confirmation
- `frontend/mobile_app/components/NewsletterSignup.tsx`: mobile signup widget

### Admin Campaigns and Templates

- `backend/controllers/email_controller.py`: template CRUD, campaign CRUD, analytics, send queue
- `backend/routers/email.py`: template/campaign admin routes
- `backend/db/models.py`: `EmailTemplate`, `EmailCampaign`, `CampaignRecipient`
- `frontend/web_app/src/app/admin/email/page.tsx`: admin dashboard shell
- `frontend/web_app/src/components/admin/EmailCampaignManager.tsx`: web campaign management
- `frontend/web_app/src/components/admin/EmailTemplateManager.tsx`: web template management
- `frontend/web_app/src/components/admin/CreateCampaignForm.tsx`: web campaign composer
- `frontend/mobile_app/app/admin/email.tsx`: mobile admin campaign/template management

### Runtime Provider Configuration

- `backend/db/models.py`: `EmailProviderConfig`
- `backend/db/models.py`: `EmailSuppression`, `EmailDeliveryEvent`
- `backend/db/schemas.py`: `EmailProviderConfigUpdate`, `EmailProviderConfigSchema`, `EmailTestSendRequest`
- `backend/controllers/email_controller.py`: runtime config read/update/test-send logic
- `backend/routers/email.py`: `GET /email/config/runtime`, `PUT /email/config/runtime`, `POST /email/config/test-send`, `POST /email/webhooks/resend`
- `backend/utils/email_service.py`: runtime transport resolution, sender-purpose mapping, suppression enforcement, outbound delivery event recording
- `backend/services/email_event_service.py`: Svix verification, Resend webhook processing, suppression upsert logic, delivery event persistence
- `backend/services/transactional_email_service.py`: order/payment/refund/return/shipment milestone emails
- `frontend/web_app/src/components/admin/EmailProviderConfigManager.tsx`: web admin client for runtime config/test-send routes
- Frontend status: web admin UI exists; mobile admin parity is still pending

## Known Gaps

- No mobile admin screen yet for SMTP/Resend credentials, sender-address mapping, or test-send
- No suppression-list management UI yet for support/admin operations
- No rich template builder or variable-preview tooling
- Broader lifecycle transactional coverage for finance/logistics exception scenarios is still incomplete
- Existing open/click tracking primitives are only partial until campaign HTML/link rewriting is consistently injected end-to-end

## Recommended Next Steps

1. Build the web admin provider-config UI against `GET/PUT /email/config/runtime` and `POST /email/config/test-send`.
2. Add the same provider-config and test-send surface to mobile admin if parity is required.
3. Add admin visibility and release controls for suppression records and delivery events.
4. Expand transactional email triggers for invoices, finance exceptions, and deeper logistics exception handling.