# ZOZI E-Commerce — Complete Pages & Features Catalog

> Generated: 2026-08-31 | Frontend: Next.js 16 (App Router) | Backend: FastAPI 0.115 (Modular Monolith)

---

## Summary

| Module | Frontend Pages | Backend Router Files | Total API Endpoints |
|--------|---------------|---------------------|-------------------|
| **Admin** | 50 | 18 | ~200+ |
| **Customer / Public** | 37 | 18 | ~120+ |
| **Employee** | 12 | 15 | ~100+ |
| **Supplier** | 31 | 16 | ~130+ |
| **Logistics Partner** | 10 | 15 | ~110+ |
| **TOTAL** | **140** | **82** | **~660+** |

---

# 1. ADMIN MODULE

## 1.1 Admin Pages (50 pages)

| S.No | Page Route | Frontend File | Features |
|------|-----------|---------------|----------|
| A_001 | `/admin` | `src/app/admin/page.tsx` | Admin landing page |
| A_002 | `/admin/login` | `src/app/admin/login/page.tsx` | Admin authentication login |
| A_003 | `/admin/dashboard` | `src/app/admin/dashboard/page.tsx` | Dashboard metrics overview, KPI cards |
| A_004 | `/admin/users` | `src/app/admin/users/page.tsx` | User list, CRUD, search/filter |
| A_005 | `/admin/employees` | `src/app/admin/employees/page.tsx` | Employee management, onboarding |
| A_006 | `/admin/staff` | `src/app/admin/staff/page.tsx` | Staff account management |
| A_007 | `/admin/suppliers` | `src/app/admin/suppliers/page.tsx` | Supplier list, approve/reject |
| A_008 | `/admin/supplier-documents` | `src/app/admin/supplier-documents/page.tsx` | Document verification queue |
| A_009 | `/admin/products` | `src/app/admin/products/page.tsx` | Product list, CRUD, moderation |
| A_010 | `/admin/product-verification` | `src/app/admin/product-verification/page.tsx` | Product approval/rejection queue |
| A_011 | `/admin/categories` | `src/app/admin/categories/page.tsx` | Category tree management |
| A_012 | `/admin/orders` | `src/app/admin/orders/page.tsx` | Order list, status management |
| A_013 | `/admin/returns` | `src/app/admin/returns/page.tsx` | Return request management |
| A_014 | `/admin/tickets` | `src/app/admin/tickets/page.tsx` | Support ticket list |
| A_015 | `/admin/tickets/[id]` | `src/app/admin/tickets/[id]/page.tsx` | Ticket detail, admin response, realtime chat |
| A_016 | `/admin/disputes` | `src/app/admin/disputes/page.tsx` | Dispute resolution center |
| A_017 | `/admin/payments` | `src/app/admin/payments/page.tsx` | Payment transaction list |
| A_018 | `/admin/payouts` | `src/app/admin/payouts/page.tsx` | Payout management, approval |
| A_019 | `/admin/payouts/background-jobs` | `src/app/admin/payouts/background-jobs/page.tsx` | Background job monitoring |
| A_020 | `/admin/invoices` | `src/app/admin/invoices/page.tsx` | Invoice management |
| A_021 | `/admin/finance` | `src/app/admin/finance/page.tsx` | Finance overview dashboard |
| A_022 | `/admin/accounting` | `src/app/admin/accounting/page.tsx` | Accounting records |
| A_023 | `/admin/treasury` | `src/app/admin/treasury/page.tsx` | Treasury management, cash flow |
| A_024 | `/admin/bank-accounts` | `src/app/admin/bank-accounts/page.tsx` | Bank account verification |
| A_025 | `/admin/commission` | `src/app/admin/commission/page.tsx` | Commission rate configuration |
| A_026 | `/admin/coupons` | `src/app/admin/coupons/page.tsx` | Coupon code management |
| A_027 | `/admin/promotions` | `src/app/admin/promotions/page.tsx` | Promotion campaigns |
| A_028 | `/admin/flash-sales` | `src/app/admin/flash-sales/page.tsx` | Flash sale scheduling |
| A_029 | `/admin/payroll` | `src/app/admin/payroll/page.tsx` | Employee payroll management |
| A_030 | `/admin/hr` | `src/app/admin/hr/page.tsx` | HR management portal |
| A_031 | `/admin/ess` | `src/app/admin/ess/page.tsx` | Employee self-service admin |
| A_032 | `/admin/logistics` | `src/app/admin/logistics/page.tsx` | Logistics overview |
| A_033 | `/admin/logistics-partners` | `src/app/admin/logistics-partners/page.tsx` | Logistics partner management |
| A_034 | `/admin/moderation` | `src/app/admin/moderation/page.tsx` | Content moderation queue |
| A_035 | `/admin/resolution` | `src/app/admin/resolution/page.tsx` | Resolution center |
| A_036 | `/admin/audit-logs` | `src/app/admin/audit-logs/page.tsx` | Audit trail viewer |
| A_037 | `/admin/permissions` | `src/app/admin/permissions/page.tsx` | Permission management, RBAC |
| A_038 | `/admin/organization` | `src/app/admin/organization/page.tsx` | Organization structure management |
| A_039 | `/admin/countries` | `src/app/admin/countries/page.tsx` | Country management, activation |
| A_040 | `/admin/countries/[code]/staff` | `src/app/admin/countries/[code]/staff/page.tsx` | Country staff assignment |
| A_041 | `/admin/communication` | `src/app/admin/communication/page.tsx` | Communication settings |
| A_042 | `/admin/email` | `src/app/admin/email/page.tsx` | Email template management |
| A_043 | `/admin/exports` | `src/app/admin/exports/page.tsx` | Data export tools |
| A_044 | `/admin/video` | `src/app/admin/video/page.tsx` | Video content management |
| A_045 | `/admin/banners` | `src/app/admin/banners/page.tsx` | Banner promotion management |
| A_046 | `/admin/barcode` | `src/app/admin/barcode/page.tsx` | Barcode management |
| A_047 | `/admin/inventory-alerts` | `src/app/admin/inventory-alerts/page.tsx` | Inventory alert configuration |
| A_048 | `/admin/chat` | `src/app/admin/chat/page.tsx` | Admin chat interface |
| A_049 | `/admin/command-center` | `src/app/admin/command-center/page.tsx` | Command center overview |
| A_050 | `/admin/command-center/headlines` | `src/app/admin/command-center/headlines/page.tsx` | Executive headlines |
| A_051 | `/admin/command-center/headlines/create` | `src/app/admin/command-center/headlines/create/page.tsx` | Create headline |
| A_052 | `/admin/command-center/alerts` | `src/app/admin/command-center/alerts/page.tsx` | Command center alerts |
| A_053 | `/admin/command-center/fraud` | `src/app/admin/command-center/fraud/page.tsx` | Fraud monitoring dashboard |

## 1.2 Admin Backend Routers (18 files)

| Domain | Router File | API Prefix |
|--------|------------|------------|
| Accounts | `modules/admin/routers/accounts.py` | `/api/v1/admin/accounts` |
| Analytics | `modules/admin/routers/analytics.py` | `/api/v1/admin/analytics` |
| Audit | `modules/admin/routers/audit.py` | `/api/v1/admin/audit` |
| Catalog | `modules/admin/routers/catalog.py` | `/api/v1/admin/catalog` |
| Comms | `modules/admin/routers/comms.py` | `/api/v1/admin/comms` |
| Country | `modules/admin/routers/country.py` | `/api/v1/admin/country` |
| Country Versioning | `modules/admin/routers/country_versioning.py` | `/api/v1/admin/country/{code}/config-versions` |
| Customers | `modules/admin/routers/customers.py` | `/api/v1/admin/customers` |
| Finance | `modules/admin/routers/finance.py` | `/api/v1/admin/finance` |
| Governance | `modules/admin/routers/governance.py` | Inline paths |
| HR | `modules/admin/routers/hr.py` | `/api/v1/admin/hr` |
| Logistics | `modules/admin/routers/logistics.py` | `/api/v1/admin/logistics` |
| Media | `modules/admin/routers/media.py` | `/api/v1/admin/media` |
| Orders | `modules/admin/routers/orders.py` | `/api/v1/admin/orders` |
| Payouts | `modules/admin/routers/payouts.py` | Inline paths |
| Promotions | `modules/admin/routers/promotions.py` | `/api/v1/admin/promotions` |
| Security | `modules/admin/routers/security.py` | Inline paths |
| Suppliers | `modules/admin/routers/suppliers.py` | `/api/v1/admin/suppliers` |

---

# 2. CUSTOMER / PUBLIC MODULE

## 2.1 Customer Pages (37 pages)

| S.No | Page Route | Frontend File | Features |
|------|-----------|---------------|----------|
| C_001 | `/` | `src/app/page.tsx` | Home page, product catalog, categories, trending, bestsellers |
| C_002 | `/login` | `src/app/login/page.tsx` | Customer login |
| C_003 | `/register` | `src/app/register/page.tsx` | Customer registration |
| C_004 | `/reset-password` | `src/app/reset-password/page.tsx` | Password reset flow |
| C_005 | `/verify-email` | `src/app/verify-email/page.tsx` | Email verification |
| C_006 | `/auth/callback` | `src/app/auth/callback/page.tsx` | OAuth/auth callback handler |
| C_007 | `/products` | `src/app/products/page.tsx` | Product listing/catalog browse |
| C_008 | `/products/[id]` | `src/app/products/[id]/page.tsx` | Product detail, images, reviews |
| C_009 | `/products/category` | `src/app/products/category/page.tsx` | Category-based filtering |
| C_010 | `/cart` | `src/app/cart/page.tsx` | Shopping cart management |
| C_011 | `/checkout` | `src/app/checkout/page.tsx` | Checkout/payment flow |
| C_012 | `/orders` | `src/app/orders/page.tsx` | Customer order history |
| C_013 | `/orders/[id]` | `src/app/orders/[id]/page.tsx` | Order detail view |
| C_014 | `/wishlist` | `src/app/wishlist/page.tsx` | Saved/wishlist products |
| C_015 | `/offers` | `src/app/offers/page.tsx` | Promotions/discounts listing |
| C_016 | `/profile` | `src/app/profile/page.tsx` | Customer profile management |
| C_017 | `/profile/referrals` | `src/app/profile/referrals/page.tsx` | Referral program dashboard |
| C_018 | `/returns` | `src/app/returns/page.tsx` | Returns list |
| C_019 | `/returns/[id]` | `src/app/returns/[id]/page.tsx` | Return detail |
| C_020 | `/tracking/[id]` | `src/app/tracking/[id]/page.tsx` | Shipment tracking |
| C_021 | `/invoice` | `src/app/invoice/page.tsx` | Invoice view |
| C_022 | `/notifications` | `src/app/notifications/page.tsx` | Customer notifications |
| C_023 | `/tickets/[id]` | `src/app/tickets/[id]/page.tsx` | Support ticket detail, realtime chat |
| C_024 | `/suppliers` | `src/app/suppliers/page.tsx` | Public supplier directory |
| C_025 | `/suppliers/[id]` | `src/app/suppliers/[id]/page.tsx` | Supplier public profile |
| C_026 | `/logistics-partners` | `src/app/logistics-partners/page.tsx` | Public logistics partner directory |
| C_027 | `/logistics-partners/[id]` | `src/app/logistics-partners/[id]/page.tsx` | Logistics partner public profile |
| C_028 | `/supplier-storefront/[slug]` | `src/app/supplier-storefront/[slug]/page.tsx` | Supplier storefront (redirects) |
| C_029 | `/chatbot` | `src/app/chatbot/page.tsx` | AI chatbot interface |
| C_030 | `/barcode-scan` | `src/app/barcode-scan/page.tsx` | Barcode scanner |
| C_031 | `/meet/[room]` | `src/app/meet/[room]/page.tsx` | Video meeting room |
| C_032 | `/contact` | `src/app/contact/page.tsx` | Contact form |
| C_033 | `/help` | `src/app/help/page.tsx` | Help/FAQ center |
| C_034 | `/brand` | `src/app/brand/page.tsx` | Brand page |
| C_035 | `/archive` | `src/app/archive/page.tsx` | Product archive |
| C_036 | `/newsletter/preferences` | `src/app/newsletter/preferences/page.tsx` | Newsletter preferences |
| C_037 | `/newsletter/unsubscribe` | `src/app/newsletter/unsubscribe/page.tsx` | Newsletter unsubscribe |

## 2.2 Customer Backend Routers (18 files)

| Domain | Router File | API Prefix |
|--------|------------|------------|
| Account | `modules/customer/routers/account.py` | `/api/v1/customer/account` |
| Accounts (Auth) | `modules/customer/routers/accounts.py` | Inline paths |
| Analytics | `modules/customer/routers/analytics.py` | Varies |
| Audit | `modules/customer/routers/audit.py` | Varies |
| Catalog | `modules/customer/routers/catalog.py` | `/api/v1/customer/catalog` |
| Cart | `modules/customer/routers/cart.py` | `/api/v1/customer/cart` |
| Comms | `modules/customer/routers/comms.py` | Varies |
| Country | `modules/customer/routers/country.py` | Varies |
| Customers | `modules/customer/routers/customers.py` | Varies |
| Finance | `modules/customer/routers/finance.py` | Varies |
| Governance | `modules/customer/routers/governance.py` | Varies |
| HR | `modules/customer/routers/hr.py` | Varies |
| Logistics | `modules/customer/routers/logistics.py` | Varies |
| Orders | `modules/customer/routers/orders.py` | `/api/v1/customer/orders` |
| Promotions | `modules/customer/routers/promotions.py` | Varies |
| Security | `modules/customer/routers/security.py` | Varies |
| Suppliers | `modules/customer/routers/suppliers.py` | Varies |
| Wishlist | `modules/customer/routers/wishlist.py` | `/api/v1/customer/wishlist` |

---

# 3. EMPLOYEE MODULE

## 3.1 Employee Pages (12 pages)

| S.No | Page Route | Frontend File | Features |
|------|-----------|---------------|----------|
| E_001 | `/employee` | `src/app/employee/page.tsx` | Employee portal landing |
| E_002 | `/employee/(auth)/login` | `src/app/employee/(auth)/login/page.tsx` | Employee login |
| E_003 | `/employee/dashboard` | `src/app/employee/dashboard/page.tsx` | Employee dashboard, KPI overview |
| E_004 | `/employee/profile` | `src/app/employee/profile/page.tsx` | Employee profile management |
| E_005 | `/employee/documents` | `src/app/employee/documents/page.tsx` | Employee document management |
| E_006 | `/employee/hr` | `src/app/employee/hr/page.tsx` | HR self-service portal |
| E_007 | `/employee/training` | `src/app/employee/training/page.tsx` | Training programs, courses |
| E_008 | `/employee/attendance` | `src/app/employee/attendance/page.tsx` | Attendance tracking, check-in/out |
| E_009 | `/employee/leaves` | `src/app/employee/leaves/page.tsx` | Leave management, requests |
| E_010 | `/employee/payroll` | `src/app/employee/payroll/page.tsx` | Payroll/payslip viewing |
| E_011 | `/employee/performance` | `src/app/employee/performance/page.tsx` | Performance reviews, OKRs |
| E_012 | `/employee/ems` | `src/app/employee/ems/page.tsx` | Employee management system |

## 3.2 Employee Backend Routers (15 files)

| Domain | Router File |
|--------|------------|
| Accounts | `modules/employee/routers/accounts.py` |
| Analytics | `modules/employee/routers/analytics.py` |
| Audit | `modules/employee/routers/audit.py` |
| Catalog | `modules/employee/routers/catalog.py` |
| Comms | `modules/employee/routers/comms.py` |
| Country | `modules/employee/routers/country.py` |
| Customers | `modules/employee/routers/customers.py` |
| Finance | `modules/employee/routers/finance.py` |
| Governance | `modules/employee/routers/governance.py` |
| HR | `modules/employee/routers/hr.py` |
| Logistics | `modules/employee/routers/logistics.py` |
| Orders | `modules/employee/routers/orders.py` |
| Promotions | `modules/employee/routers/promotions.py` |
| Security | `modules/employee/routers/security.py` |
| Suppliers | `modules/employee/routers/suppliers.py` |

---

# 4. SUPPLIER MODULE

## 4.1 Supplier Pages (31 pages)

| S.No | Page Route | Frontend File | Features |
|------|-----------|---------------|----------|
| S_001 | `/supplier` | `src/app/supplier/page.tsx` | Supplier portal landing |
| S_002 | `/supplier/(auth)/login` | `src/app/supplier/(auth)/login/page.tsx` | Supplier login |
| S_003 | `/supplier/(auth)/register` | `src/app/supplier/(auth)/register/page.tsx` | Supplier registration |
| S_004 | `/supplier/dashboard` | `src/app/supplier/dashboard/page.tsx` | Supplier dashboard, metrics |
| S_005 | `/supplier/profile` | `src/app/supplier/profile/page.tsx` | Supplier profile management |
| S_006 | `/supplier/documents` | `src/app/supplier/documents/page.tsx` | Supplier document management |
| S_007 | `/supplier/terms` | `src/app/supplier/terms/page.tsx` | Terms & conditions |
| S_008 | `/supplier/guide` | `src/app/supplier/guide/page.tsx` | Supplier onboarding guide |
| S_009 | `/supplier/products` | `src/app/supplier/products/page.tsx` | Product listing |
| S_010 | `/supplier/products/add` | `src/app/supplier/products/add/page.tsx` | Add new product |
| S_011 | `/supplier/products/[id]` | `src/app/supplier/products/[id]/page.tsx` | Product detail/edit |
| S_012 | `/supplier/inventory` | `src/app/supplier/inventory/page.tsx` | Inventory management |
| S_013 | `/supplier/orders` | `src/app/supplier/orders/page.tsx` | Order management |
| S_014 | `/supplier/orders/[id]` | `src/app/supplier/orders/[id]/page.tsx` | Order detail |
| S_015 | `/supplier/returns` | `src/app/supplier/returns/page.tsx` | Return management |
| S_016 | `/supplier/disputes` | `src/app/supplier/disputes/page.tsx` | Dispute management |
| S_017 | `/supplier/invoices` | `src/app/supplier/invoices/page.tsx` | Invoice management |
| S_018 | `/supplier/payouts` | `src/app/supplier/payouts/page.tsx` | Payout tracking |
| S_019 | `/supplier/analytics` | `src/app/supplier/analytics/page.tsx` | Sales analytics |
| S_020 | `/supplier/reports` | `src/app/supplier/reports/page.tsx` | Reports generation |
| S_021 | `/supplier/credibility` | `src/app/supplier/credibility/page.tsx` | Credibility score display |
| S_022 | `/supplier/regions` | `src/app/supplier/regions/page.tsx` | Region management |
| S_023 | `/supplier/logistics` | `src/app/supplier/logistics/page.tsx` | Logistics management |
| S_024 | `/supplier/labels` | `src/app/supplier/labels/page.tsx` | Label management |
| S_025 | `/supplier/labels/[id]` | `src/app/supplier/labels/[id]/page.tsx` | Label detail |
| S_026 | `/supplier/upload` | `src/app/supplier/upload/page.tsx` | Product upload |
| S_027 | `/supplier/upload/bg-compare` | `src/app/supplier/upload/bg-compare/page.tsx` | Background comparison tool |
| S_028 | `/supplier/batch-upload` | `src/app/supplier/batch-upload/page.tsx` | Batch product upload |
| S_029 | `/supplier/bulk` | `src/app/supplier/bulk/page.tsx` | Bulk operations |
| S_030 | `/supplier/videos/upload` | `src/app/supplier/videos/upload/page.tsx` | Video upload |
| S_031 | `/supplier/support` | `src/app/supplier/support/page.tsx` | Supplier support tickets |
| S_032 | `/supplier/notification-preferences` | `src/app/supplier/notification-preferences/page.tsx` | Notification settings |

## 4.2 Supplier Backend Routers (16 files)

| Domain | Router File |
|--------|------------|
| Accounts | `modules/supplier/routers/accounts.py` |
| Analytics | `modules/supplier/routers/analytics.py` |
| Audit | `modules/supplier/routers/audit.py` |
| Catalog | `modules/supplier/routers/catalog.py` |
| Comms | `modules/supplier/routers/comms.py` |
| Country | `modules/supplier/routers/country.py` |
| Customers | `modules/supplier/routers/customers.py` |
| Finance | `modules/supplier/routers/finance.py` |
| Governance | `modules/supplier/routers/governance.py` |
| HR | `modules/supplier/routers/hr.py` |
| Logistics | `modules/supplier/routers/logistics.py` |
| Orders | `modules/supplier/routers/orders.py` |
| Products | `modules/supplier/routers/products.py` |
| Promotions | `modules/supplier/routers/promotions.py` |
| Security | `modules/supplier/routers/security.py` |
| Suppliers | `modules/supplier/routers/suppliers.py` |

---

# 5. LOGISTICS PARTNER MODULE

## 5.1 Logistics Partner Pages (10 pages)

| S.No | Page Route | Frontend File | Features |
|------|-----------|---------------|----------|
| L_001 | `/logistics-partner` | `src/app/logistics-partner/page.tsx` | Logistics partner landing |
| L_002 | `/logistics-partner/(auth)/login` | `src/app/logistics-partner/(auth)/login/page.tsx` | Logistics partner login |
| L_003 | `/logistics-partner/(auth)/register` | `src/app/logistics-partner/(auth)/register/page.tsx` | Logistics partner registration |
| L_004 | `/logistics-partner/dashboard` | `src/app/logistics-partner/dashboard/page.tsx` | Logistics partner dashboard |
| L_005 | `/logistics-partner/profile` | `src/app/logistics-partner/profile/page.tsx` | Partner profile management |
| L_006 | `/logistics-partner/shipments` | `src/app/logistics-partner/shipments/page.tsx` | Shipment management |
| L_007 | `/logistics-partner/scan` | `src/app/logistics-partner/scan/page.tsx` | Package scanning |
| L_008 | `/logistics-partner/routes` | `src/app/logistics-partner/routes/page.tsx` | Route management |
| L_009 | `/logistics-partner/payouts` | `src/app/logistics-partner/payouts/page.tsx` | Payout tracking |
| L_010 | `/logistics-partner/analytics` | `src/app/logistics-partner/analytics/page.tsx` | Delivery analytics |

## 5.2 Logistics Backend Routers (15 files)

| Domain | Router File |
|--------|------------|
| Accounts | `modules/logistics/routers/accounts.py` |
| Analytics | `modules/logistics/routers/analytics.py` |
| Audit | `modules/logistics/routers/audit.py` |
| Catalog | `modules/logistics/routers/catalog.py` |
| Comms | `modules/logistics/routers/comms.py` |
| Country | `modules/logistics/routers/country.py` |
| Customers | `modules/logistics/routers/customers.py` |
| Finance | `modules/logistics/routers/finance.py` |
| Governance | `modules/logistics/routers/governance.py` |
| HR | `modules/logistics/routers/hr.py` |
| Logistics (Core) | `modules/logistics/routers/logistics.py` |
| Orders | `modules/logistics/routers/orders.py` |
| Promotions | `modules/logistics/routers/promotions.py` |
| Security | `modules/logistics/routers/security.py` |
| Suppliers | `modules/logistics/routers/suppliers.py` |

---

# 6. FEATURE MATRIX BY MODULE

## 6.1 Admin Features (Comprehensive)

| Feature Category | Specific Features |
|-----------------|-------------------|
| **Dashboard** | KPI metrics, system health, user growth, revenue analytics, command center |
| **User Management** | CRUD, role assignment, bulk operations, archive/restore, force password reset |
| **Employee Management** | Onboarding, payroll, disciplinary, offboarding, compliance, organization chart |
| **Supplier Management** | Approval queue, document verification, credibility scoring, KYC |
| **Product Management** | Approval/rejection, moderation, bulk archive, category change, badge management |
| **Category Management** | Tree CRUD, reorder, bulk import/export, attribute schema, AI suggestions |
| **Order Management** | Status updates, refunds, bulk operations, campaign management |
| **Return Management** | Return queue, status updates, bulk operations |
| **Finance** | Category rates, badge tiers, commission rates, treasury, accounting |
| **Promotions** | Banners, coupons, flash sales, campaigns |
| **HR** | Leave management, expenses, assets, compliance, COI checks, work hours |
| **Logistics** | Partner approval/rejection, country-level management |
| **Security** | Fraud scoring, blacklist, rules, threat feeds, ghost employees, impossible travel |
| **Audit** | Search, timeline, export, compliance reports |
| **Country** | CRUD, cities, staff assignment, tax rates, commission rates, versioning |
| **Communication** | Campaigns, email, notifications, audit trail |
| **Media** | Upload, presigned URLs, delete |
| **Command Center** | Headlines, alerts, fraud monitoring, system metrics, executive news, realtime metrics |
| **Permissions** | RBAC catalog, hierarchy permissions |
| **Data** | Exports, background job monitoring |

## 6.2 Customer Features

| Feature Category | Specific Features |
|-----------------|-------------------|
| **Authentication** | Login, register, OAuth (Google/Facebook), password reset, TOTP 2FA, sessions |
| **Catalog** | Product browse, search, autocomplete, categories, recommendations, trending |
| **Cart** | Add/remove items, update quantities, shipping quote, totals calculation |
| **Orders** | Create, list, detail, tracking, invoice, cancel, preview, scan receipt |
| **Returns** | Create, list, detail, status updates, bulk operations |
| **Wishlist** | Add, remove, list saved products |
| **Profile** | Update profile, avatar, addresses, change password, coin balance |
| **Referrals** | Dashboard, share, config |
| **Social Auth** | Google OAuth, Facebook OAuth, Google ID token |
| **GDPR** | Data export, deletion request |
| **Notifications** | List, mark read |
| **Support** | Tickets, realtime chat |
| **Public Directories** | Suppliers, logistics partners, brand pages |
| **Communication** | Contact form, newsletter, help/FAQ |
| **AI** | Chatbot, product recommendations |
| **Media** | Barcode scanning, video meetings, logo animation |

## 6.3 Employee Features

| Feature Category | Specific Features |
|-----------------|-------------------|
| **Self-Service** | Profile, documents, attendance, leaves, payslips, performance, OKRs |
| **HR** | Leave requests, expense submission, address registration, dependents |
| **Analytics** | Personal, team, OKR tracking, performance metrics |
| **Comms** | Direct messages, group messages, threads, notifications, tickets |
| **Communication** | Campaigns, templates, transactional sends, inbox, unified inbox |
| **Catalog** | Product browse, categories |
| **Logistics** | Partner management, dashboard |
| **Security** | Risk scores, ghost employee detection, impossible travel |
| **Training** | Programs, courses |
| **Organization** | Org chart, hierarchy |

## 6.4 Supplier Features

| Feature Category | Specific Features |
|-----------------|-------------------|
| **Authentication** | Login, register, TOTP 2FA, sessions, bank accounts |
| **Products** | CRUD, discount management, image upload, batch upload, bulk operations |
| **Inventory** | Stock management, alerts |
| **Orders** | List, detail, status tracking |
| **Returns** | Management, status updates |
| **Disputes** | Management, resolution |
| **Invoices** | Management, generation |
| **Payouts** | Tracking, status, requests |
| **Analytics** | Sales, products, orders, revenue trends |
| **Reports** | Generation, export |
| **Credibility** | Score display, improvement |
| **Regions** | Management, service areas |
| **Logistics** | Carriers, zones, shipments |
| **Labels** | Management, printing |
| **Upload** | Single, batch, video, background comparison |
| **Support** | Tickets, chat, notifications |
| **KYC** | Pipeline, documents, status tracking |
| **Finance** | Global settings, categories, badge tiers, ledger, effective rate |

## 6.5 Logistics Partner Features

| Feature Category | Specific Features |
|-----------------|-------------------|
| **Authentication** | Login, register, TOTP 2FA, sessions, bank accounts |
| **Profile** | Management, terms acceptance, reviews |
| **Shipments** | Create, scan, status updates, history, events, GPS tracking |
| **Orders** | Pending, confirm pickup, scan receive, update transit, deliver, cancel pickup |
| **Routes** | Management, optimization |
| **Carriers** | CRUD, management |
| **Zones** | CRUD, service areas |
| **Pricing** | Profiles, category rules, vehicle rules, insights |
| **Payouts** | Tracking, settlements, COD remittances |
| **Analytics** | Delivery performance, shipments, summary |
| **Finance** | Summary, ledger, settlements |
| **Support** | Tickets, chat, notifications |
| **Compliance** | Status, incidents, fraud alerts |
| **Public** | Directory listing, public profiles |

---

# 7. BACKEND DOMAIN SERVICES (16 Domains)

All modules operate across these 16 domain services in the backend:

| # | Domain | Path | Description |
|---|--------|------|-------------|
| 1 | Accounts | `domains/accounts/` | User accounts, auth, profiles, addresses |
| 2 | Analytics | `domains/analytics/` | Metrics, dashboards, reports |
| 3 | Audit | `domains/audit/` | Audit trail, compliance logging |
| 4 | Catalog | `domains/catalog/` | Products, categories, search |
| 5 | Comms | `domains/comms/` | Email, SMS, notifications, chat |
| 6 | Country | `domains/country/` | Country config, cities, tax, staff |
| 7 | Customers | `domains/customer/` | Customer profiles, reviews, referrals |
| 8 | Finance | `domains/finance/` | Rates, commissions, ledgers |
| 9 | Governance | `domains/governance/` | Compliance, disputes, fraud |
| 10 | HR | `domains/hr/` | Employees, payroll, leave, attendance |
| 11 | Logistics | `domains/logistics/` | Carriers, zones, shipments, tracking |
| 12 | Orders | `domains/orders/` | Order lifecycle, fulfillment |
| 13 | Promotions | `domains/promotions/` | Banners, coupons, campaigns |
| 14 | Security | `domains/security/` | Fraud, blacklist, threat detection |
| 15 | Suppliers | `domains/suppliers/` | Supplier profiles, KYC, pipelines |
| 16 | Shared Kernel | `kernel/` | Money, currency, numbering, country |

---

# 8. CROSS-MODULE SHARED FEATURES

| Feature | Admin | Customer | Employee | Supplier | Logistics |
|---------|:-----:|:--------:|:--------:|:--------:|:---------:|
| Authentication (JWT) | Y | Y | Y | Y | Y |
| TOTP 2FA | Y | Y | Y | Y | Y |
| Session Management | Y | Y | Y | Y | Y |
| Bank Accounts | Y | - | - | Y | Y |
| Notifications | Y | Y | Y | Y | Y |
| Support Tickets | Y | Y | Y | Y | Y |
| Chat/Comms | Y | - | Y | Y | Y |
| Analytics Dashboard | Y | - | Y | Y | Y |
| Audit Trail | Y | - | Y | Y | Y |
| Security/Fraud | Y | - | Y | - | - |
| RBAC/Permissions | Y | - | Y | - | - |

---

*End of document — 140 frontend pages, 82 backend router files, ~660+ API endpoints across 5 modules*
