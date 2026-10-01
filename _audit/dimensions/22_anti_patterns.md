# Anti-Patterns Audit

| Sno | Folder | File | Function / Line | Anti-Pattern | Evidence | Status | project_completion_blocker |
|-----|--------|------|-----------------|--------------|----------|--------|----------------------------|
| 1 | backend/providers | payments/base.py | base.py:160 | Stub function | `raise NotImplementedError` in abstract payment provider base | NEW | no |
| 2 | backend/providers | image/image.py | image.py:134 | Stub function | `raise NotImplementedError` in image provider stub | NEW | no |
| 3 | backend/infrastructure/events | subscriber.py | subscriber.py:75,77,79,105,136 | Empty handler / silent except | `except: pass` blocks swallow event-handling failures | NEW | yes |
| 4 | backend/middleware | webhook_verification.py | webhook_verification.py:167,178 | Silent except | `except: pass` hides webhook auth failures | NEW | yes |
| 5 | backend/middleware | webhook_ip_whitelist.py | webhook_ip_whitelist.py:406 | Silent except | `except: pass` hides IP whitelist failures | NEW | yes |
| 6 | backend/middleware | lifespan.py | lifespan.py:163 | Silent except | `except: pass` hides listener registration failures | NEW | yes |
| 7 | backend/infrastructure/database | transaction.py | transaction.py:69 | Silent except | `except: pass` hides DB transaction errors | NEW | yes |
| 8 | backend/infrastructure/utils | schema_audit.py | schema_audit.py:68,354,365 | Silent except / dead code | `except: pass` hides schema-audit failures | NEW | no |
| 9 | backend | lifespan.py | lifespan.py:301 | Silent except / dead branch | Commented try/except: pass leaves `db_statement_timeout` dead at boot | NEW | yes |
| 10 | backend | modules/customer/routers/accounts.py | accounts.py:86 | Empty handler | `pass` body in customer account router handler — replaced with real implementation delegating to domain services | RESOLVED | no |
| 11 | backend/domains/governance | subscribers.py | subscribers.py:63-237 | TODO-only implementation / commented imports | 25+ commented imports and `# TODO: Module not yet created` stubs | NEW | no |
| 12 | backend/domains/hr | services/__init__.py | services/__init__.py:4-24 | TODO-only implementation | 10+ `# TODO: Module not yet created` stubs in HR services init | NEW | no |
| 13 | backend/domains/finance | services/payouts/payout_batch_service.py | payout_batch_service.py:7-1860 | TODO-only implementation | 30+ `# TODO: Module not yet created` stubs in payout batch service | NEW | yes |
| 14 | backend/domains/logistics | services/partners/admin_logistics_operations_service.py | admin_logistics_operations_service.py:13-148 | TODO-only implementation | 35+ `# TODO: Module not yet created` stubs in logistics ops | NEW | yes |
| 15 | backend/domains/finance | services/__init__.py | services/__init__.py:7-14 | Phantom reference | Commented wildcard imports (`has broken imports`) | NEW | no |
| 16 | backend/domains/governance | services/__init__.py | services/__init__.py:7 | Phantom reference | `# from domains.governance.services.auth import *  # disabled: has broken imports` | NEW | no |
| 17 | backend/domains/suppliers | services/supplier_shared.py | supplier_shared.py:37,39 | Phantom reference | Commented imports to non-existent/unused modules | NEW | no |
| 18 | backend/domains/suppliers | services/orders/supplier_orders_verify_service.py | supplier_orders_verify_service.py:21-41 | Phantom reference | 10+ commented imports to modules not yet created | NEW | no |
| 19 | backend/domains/logistics | services/tracking/service.py | service.py:438-451 | Phantom reference | 6+ commented imports to missing tracking services | NEW | yes |
| 20 | backend/domains/security | services/detection/public_security_detection_service.py | public_security_detection_service.py:15-18 | Phantom reference | Commented imports to `FraudScoringEngine`, `ThreatFeedUpdater` | NEW | no |
| 21 | backend | config.py | config.py:77-259 | Default masks failure | 60+ required secrets default to `""` (empty string), masking missing env config | NEW | yes |
| 22 | backend/domains/finance | services/payouts/payout_batch_service.py | payout_batch_service.py:2599-4121 | Duplicate business logic / Wrong type for money | 25+ `float(cast(Decimal, ...))` serializations repeated across payout API | NEW | yes |
| 23 | backend/domains/finance | services/ledger/general_ledger_service.py | general_ledger_service.py:1387-2538 | Duplicate business logic / Wrong type for money | 10+ `float(...)` and `float(round_money(...))` for ledger amounts | NEW | yes |
| 24 | backend/domains/finance | services/payments/payment_orchestrator.py | payment_orchestrator.py:680-1451 | Duplicate business logic / Wrong type for money | 8+ `float(converted_total)` / `float(gateway_amount)` / `float(amount_diff)` | NEW | yes |
| 25 | backend/domains/catalog | services/products/products_service.py | products_service.py:171-933 | Duplicate business logic / Wrong type for money | 8+ `float(product.price)` / `float(compare_price)` conversions | NEW | yes |
| 26 | backend/domains/suppliers | services/supplier_shared.py | supplier_shared.py:634-823 | Duplicate business logic / Wrong type for money | 5+ `float(raw_price)` / `float(variant.price)` / `float(product_price)` | NEW | yes |
| 27 | backend/domains/customers | services/cart_service.py | cart_service.py:128-149 | Duplicate business logic / Wrong type for money | 3+ `float(product.price)` / `float(sum(...))` for cart totals | NEW | yes |
| 28 | backend/domains/customers | services/coupons_read_service.py | coupons_read_service.py:141-142 | Duplicate business logic / Wrong type for money | `float(discount)` / `float(new_total)` duplicated in write service | NEW | yes |
| 29 | frontend/web_app/src | app/cart/page.tsx | page.tsx:69 | Empty handler | `.catch(() => {})` swallows cart loading errors silently | NEW | no |
| 30 | frontend/web_app/src | app/checkout/page.tsx | page.tsx:218,236,254,269,425 | Empty handler | 5× `.catch(() => {})` / `.catch(() => {/* leave methods null */})` hides checkout failures | NEW | yes |
| 31 | frontend/web_app/src | app/products/page.tsx | page.tsx:268,442,448,475 | Empty handler | 4× `.catch(() => {})` hides product listing/search errors | NEW | no |
| 32 | frontend/web_app/src | components/Header.tsx | Header.tsx:355,384,461 | Empty handler | 3× `.catch(() => {})` hides header/auth errors | NEW | no |
| 33 | frontend/web_app/src | app/admin/orders/page.tsx | page.tsx:187,212,225,249,284 | Empty handler | 5× `.catch(() => ({}))` / `} catch (error) { }` hides admin order failures | NEW | yes |
| 34 | frontend/web_app/src | app/admin/categories/page.tsx | page.tsx:97,117,126,145,158,169 | Empty handler | 6× `.catch(() => ({}))` hides category admin failures | NEW | yes |
| 35 | frontend/web_app/src | components/admin/EmailTemplateManager.tsx | EmailTemplateManager.tsx:47,71,324 | Empty handler | 3× `} catch (error) { }` hides email template errors | NEW | yes |
| 36 | frontend/web_app/src | components/admin/EmailProviderConfigManager.tsx | EmailProviderConfigManager.tsx:134,197,224 | Empty handler | 3× `} catch (error) { }` hides provider config errors | NEW | yes |
| 37 | frontend/web_app/src | components/country/GhostRowForm.tsx | GhostRowForm.tsx:74,121 | Empty handler | 2× `} catch (err: any) { }` hides country row errors | NEW | yes |
| 38 | frontend/web_app/src | app/admin/catalog/page.tsx | page.tsx:76,111,131 | Empty handler | 3× `.catch(() => ({}))` / `} catch (e) { }` hides catalog admin errors | NEW | yes |
| 39 | frontend/shared/src | components/ui/GlassCard.native.tsx | GlassCard.native.tsx:9 | Empty handler | `} catch (e) { }` hides native UI rendering errors | NEW | no |
| 40 | frontend/web_app/src | app/products/[id]/page.tsx | page.tsx:183,198,205 | Empty handler | 3× `.catch(() => {})` hides product detail errors | NEW | no |
| 41 | backend/domains/governance | services/admin/admin_service.py | admin_service.py:4-425 | Commented code | 80+ commented imports for flat_admin_logistics_operations_service | NEW | no |
| 42 | backend/domains/governance | services/settings/admin_service.py | admin_service.py:14-24 | Commented code | 10+ commented imports (`unused`, `module not available`) | NEW | no |
| 43 | backend/domains/finance | ports.py | ports.py:827-867 | Commented code | 15+ commented imports to missing finance services | NEW | no |
| 44 | backend/domains/finance | services/ledger/general_ledger_service.py | general_ledger_service.py:4027,4387,4389,6266,6268,8631,8706 | Commented code | 7+ commented imports to commission/write/read helpers | NEW | no |
| 45 | backend/modules/supplier | routers/security.py | security.py:12 | Orphan route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 46 | backend/modules/supplier | routers/promotions.py | promotions.py:12 | Orphan route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 47 | backend/modules/supplier | routers/hr.py | hr.py:12 | Orphan route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 48 | backend/modules/supplier | routers/country.py | country.py:12 | Orphan route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 49 | backend/modules/admin | routers/orders.py | orders.py:32 | Orphan route | `# TODO: implement via domains.comms.services.email_metrics_service when wired` | NEW | no |
| 50 | backend/modules/admin | routers/country.py | country.py:48 | Orphan route | `detail=f"TODO: {name} not yet wired to a domain service"` — hardcoded failure response | NEW | yes |
| 51 | backend/domains/governance | services/settings/governance_package_service.py | governance_package_service.py:20-26 | Commented code / Phantom reference | 3+ commented imports to AssetTracking, ExpenseProcessing, LeaveAccrual | NEW | no |
| 52 | backend/domains/promotions | services/coupons/commerce_coupons_read_service.py | commerce_coupons_read_service.py:7-10 | Phantom reference | 2+ commented imports to `coupons_read_service` | NEW | no |
| 53 | backend/domains/catalog | services/categories/admin_categories_service.py | admin_categories_service.py:22 | Phantom reference | 1+ commented import to products write service | NEW | no |
| 54 | backend/domains/catalog | services/products/admin_products_service.py | admin_products_service.py:13 | Phantom reference | 1+ commented import to admin_catalog_operations_service | NEW | no |
| 55 | backend/domains/logistics | services/shipping/service.py | service.py:187,196 | TODO-only implementation | 2× `# TODO: Module not yet created` stubs | NEW | yes |
| 56 | backend/domains/logistics | services/partners/admin_logistics_operations_service.py | admin_logistics_operations_service.py:13-148 | TODO-only implementation | 35+ `# TODO: Module not yet created` stubs | NEW | yes |
| 57 | backend/domains/suppliers | services/products/supplier_supplier_upload_service.py | supplier_supplier_upload_service.py:20-52 | TODO-only implementation | 6+ `# TODO: Module not yet created` stubs | NEW | yes |
| 58 | backend/domains/suppliers | services/orders/supplier_orders_verify_service.py | supplier_orders_verify_service.py:21-41 | TODO-only implementation | 10+ `# TODO: Module not yet created` stubs | NEW | yes |
| 59 | backend/domains/hr | services/payroll/payroll_engine.py | payroll_engine.py:52 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 60 | backend/domains/hr | services/hierarchy/hierarchy_service.py | hierarchy_service.py:229,245 | TODO-only implementation | 2× `TODO:` comments for matrix-manager persistence/delete | NEW | yes |
| 61 | backend/domains/hr | ports.py | ports.py:41,505 | TODO-only implementation | 2× `# TODO: payroll_engine not yet created` / `Module not yet created` | NEW | yes |
| 62 | backend/domains/finance | services/payouts/payout_batch_service.py | payout_batch_service.py:1699-1860 | TODO-only implementation | 20+ `# TODO: Module not yet created` stubs | NEW | yes |
| 63 | backend/domains/finance | services/__init__.py | services/__init__.py:7-14 | TODO-only implementation | 4× `# TODO: Module not yet created` stubs | NEW | yes |
| 64 | backend/domains/finance | ports.py | ports.py:827-867 | TODO-only implementation | 8× `# TODO: Module not yet created` / `functions do not exist` | NEW | yes |
| 65 | backend/domains/governance | services/operations.py | operations.py:34 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 66 | backend/domains/governance | services/settings/governance_package_service.py | governance_package_service.py:23,25 | TODO-only implementation | 2× `# TODO: Module not yet created` stubs | NEW | yes |
| 67 | backend/domains/promotions | services/coupons/commerce_coupons_read_service.py | commerce_coupons_read_service.py:7-10 | TODO-only implementation | 2× `# TODO: Module not yet created` stubs | NEW | yes |
| 68 | backend/domains/catalog | services/products/admin_products_service.py | admin_products_service.py:13 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 69 | backend/domains/catalog | services/categories/admin_categories_service.py | admin_categories_service.py:22 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 70 | backend/domains/security | services/detection/public_security_detection_service.py | public_security_detection_service.py:15-18 | TODO-only implementation | 2× `# TODO: Module not yet created` stubs | NEW | yes |
| 71 | backend/domains/suppliers | services/supplier_shared.py | supplier_shared.py:38 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 72 | backend/domains/accounts | services/identity/identity_admin_service.py | identity_admin_service.py:21 | TODO-only implementation | `# TODO: Module not yet created` stub | NEW | yes |
| 73 | backend/domains/accounts | services/auth/public_security_registration_service.py | public_security_registration_service.py:213 | TODO-only implementation | `# TODO Law 3: Replace with domain event` | NEW | yes |
| 74 | backend/domains/accounts | services/auth/auth_service.py | auth_service.py:454,607,3561,3568,3575,3614,3625,3657 | TODO-only implementation | 8× `# TODO:` stubs for geo-velocity, SMS, biometrics, OIDC | NEW | yes |
| 75 | backend/domains/hr | subscribers.py | subscribers.py:7 | TODO-only implementation | `# TODO: Define HR-domain subscribers here` | NEW | no |
| 76 | backend/domains/hr | services/employees/coi_service.py | coi_service.py:183 | TODO-only implementation | `# TODO: Add supplier COI check` | NEW | yes |
| 77 | backend/domains/logistics | services/tracking/service.py | service.py:438-451 | TODO-only implementation | 6× `# TODO: Module not yet created` stubs | NEW | yes |
| 78 | backend/domains/logistics | services/shipping/service.py | service.py:187,196 | TODO-only implementation | 2× `# TODO: Module not yet created` stubs | NEW | yes |
| 79 | backend/modules/supplier | routers/security.py | security.py:12 | Not-wired route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 80 | backend/modules/supplier | routers/promotions.py | promotions.py:12 | Not-wired route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 81 | backend/modules/supplier | routers/hr.py | hr.py:12 | Not-wired route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 82 | backend/modules/supplier | routers/country.py | country.py:12 | Not-wired route | `# TODO: Add endpoints as domain services are implemented` — empty router | NEW | no |
| 83 | backend | config.py | config.py:77-259 | Default masks failure | Empty-string defaults for `secret_key`, `database_url`, API keys, etc. | NEW | yes |
| 84 | backend/infrastructure/valkey | client.py | client.py:37-88 | Silent except / Wrong type for money | NoOpValkey returns `None` for all ops, masking missing cache | NEW | no |
| 85 | backend/infrastructure/messaging | realtime.py | realtime.py:45-508 | Silent except | 8× `return None` / `except: pass` hides messaging failures | NEW | yes |
| 86 | backend/infrastructure/storage | storage.py | storage.py:65,197,209 | Silent except | 3× `return None` hides storage init/upload/delete failures | NEW | yes |
| 87 | backend/infrastructure/utils | background_jobs.py | background_jobs.py:86-187 | Silent except | 6× `return None` hides job dispatch/enqueue failures | NEW | yes |
| 88 | backend/providers/observability | observability.py | observability.py:25,34 | Empty handler | `except: pass` hides observability export failures | NEW | no |
| 89 | frontend/web_app/src | app/checkout/page.tsx | page.tsx:373,398,605 | Empty handler | `} catch (payErr: any) { }` / `.catch(() => setShipping(null))` hides payment failures | NEW | yes |
| 90 | frontend/web_app/src | app/admin/orders/page.tsx | page.tsx:180 | Empty handler | `.catch(() => ({}))` hides admin order error parsing | NEW | yes |
| 91 | frontend/web_app/src | app/admin/categories/page.tsx | page.tsx:69-169 | Empty handler | Repeated `.catch(() => ({}))` in 6 places hides category admin failures | NEW | yes |
| 92 | frontend/web_app/src | app/admin/catalog/page.tsx | page.tsx:69,111,131 | Empty handler | Repeated `.catch(() => ({}))` hides catalog admin failures | NEW | yes |
| 93 | frontend/web_app/src | components/admin/EmailTemplateManager.tsx | EmailTemplateManager.tsx:47,71,324 | Empty handler | `} catch (error) { }` hides email template CRUD failures | NEW | yes |
| 94 | frontend/web_app/src | components/admin/EmailProviderConfigManager.tsx | EmailProviderConfigManager.tsx:134,197,224 | Empty handler | `} catch (error) { }` hides provider config failures | NEW | yes |
| 95 | frontend/web_app/src | components/country/GhostRowForm.tsx | GhostRowForm.tsx:74,121 | Empty handler | `} catch (err: any) { }` hides country row save failures | NEW | yes |
| 96 | frontend/web_app/src | app/products/[id]/page.tsx | page.tsx:183,198,205 | Empty handler | `.catch(() => {})` hides product detail API failures | NEW | no |
| 97 | frontend/web_app/src | app/products/page.tsx | page.tsx:268,442,448,475 | Empty handler | `.catch(() => {})` hides product search/listing failures | NEW | no |
| 98 | frontend/web_app/src | components/Header.tsx | Header.tsx:355,384,461 | Empty handler | `.catch(() => {})` hides header state fetch failures | NEW | no |
| 99 | frontend/web_app/src | app/cart/page.tsx | page.tsx:69 | Empty handler | `.catch(() => {})` hides cart load failure | NEW | no |
| 100 | frontend/web_app/src | app/admin/analytics/page.tsx | page.tsx:102 | Empty handler | `} catch (e) { }` hides analytics fetch failure | NEW | yes |
| 101 | frontend/web_app/src | app/admin/audit-logs/page.tsx | page.tsx:72 | Empty handler | `} catch (err) { }` hides audit log fetch failure | NEW | yes |
| 102 | frontend/web_app/src | app/admin/barcode/page.tsx | page.tsx:135 | Empty handler | `} catch (err: any) { }` hides barcode fetch failure | NEW | yes |
| 103 | frontend/web_app/src | app/admin/comms-test/page.tsx | page.tsx:94 | Empty handler | `} catch (exc) { }` hides comms test failure | NEW | yes |
| 104 | frontend/web_app/src | app/admin/commission/page.tsx | page.tsx:108 | Empty handler | `} catch (err) { }` hides commission fetch failure | NEW | yes |
| 105 | frontend/web_app/src | app/contact/page.tsx | page.tsx:57 | Empty handler | `} catch (err: unknown) { }` hides contact form failure | NEW | no |
| 106 | frontend/web_app/src | app/newsletter/unsubscribe/page.tsx | page.tsx:42 | Empty handler | `} catch (error) { }` hides unsubscribe failure | NEW | no |
| 107 | frontend/web_app/src | app/newsletter/preferences/page.tsx | page.tsx:50,88,116 | Empty handler | 3× `} catch (error) { }` hides newsletter preference failures | NEW | no |
| 108 | frontend/web_app/src | app/verify-email/page.tsx | page.tsx:35 | Empty handler | `.catch(() => { })` hides email verification failure | NEW | no |
| 109 | frontend/web_app/src | app/logistics-partners/page.tsx | page.tsx:72 | Empty handler | `} catch (err) { }` hides logistics partner fetch failure | NEW | no |
| 110 | frontend/web_app/src | app/logistics-partners/[id]/page.tsx | page.tsx:76 | Empty handler | `} catch (err) { }` hides logistics partner detail failure | NEW | no |
| 111 | frontend/web_app/src | app/employee/dashboard/page.tsx | page.tsx:102 | Empty handler | `} catch (e) { }` hides employee dashboard failure | NEW | no |
| 112 | frontend/web_app/src | app/employee/performance/page.tsx | page.tsx:56-57 | Empty handler | `.catch(() => null)` hides OKR/review fetch failures | NEW | no |
| 113 | frontend/web_app/src | app/employee/workspace/page.tsx | page.tsx:45-46 | Empty handler | `.catch(() => null)` hides workspace/task fetch failures | NEW | no |
| 114 | frontend/web_app/src | app/employee/attendance/page.tsx | page.tsx:59-60 | Empty handler | `.catch(() => null)` hides attendance fetch failures | NEW | no |
| 115 | frontend/web_app/src | app/employee/schedule/page.tsx | page.tsx:37-38 | Empty handler | `.catch(() => null)` hides schedule fetch failures | NEW | no |
| 116 | frontend/web_app/src | app/employee/training/page.tsx | page.tsx:53-54 | Empty handler | `.catch(() => null)` hides training fetch failures | NEW | no |
| 117 | frontend/web_app/src | app/employee/profile/page.tsx | page.tsx:132 | Empty handler | `.catch(() => ({}))` hides profile fetch failure | NEW | no |
| 118 | frontend/web_app/src | app/logistics-partner/(auth)/register/page.tsx | page.tsx:79 | Empty handler | `.catch(() => ({}))` hides partner register failure | NEW | no |
| 119 | frontend/web_app/src | app/logistics-partner/analytics/page.tsx | page.tsx:120,123 | Empty handler | `.catch(() => null)` / `.catch(() => [])` hides analytics failure | NEW | no |
| 120 | frontend/web_app/src | app/tracking/[id]/page.tsx | page.tsx:93,116,156 | Empty handler | `.catch(() => null)` hides tracking fetch failures | NEW | no |
| 121 | frontend/web_app/src | app/invoice/page.tsx | page.tsx:73 | Empty handler | `.catch(() => setError(...))` hides invoice fetch failure | NEW | no |
| 122 | frontend/web_app/src | app/archive/page.tsx | page.tsx:62 | Empty handler | `.catch(() => setError(...))` hides archive fetch failure | NEW | no |
| 123 | frontend/web_app/src | app/products/category/page.tsx | page.tsx:44 | Empty handler | `.catch(() => setLoading(false))` hides category fetch failure | NEW | no |
| 124 | frontend/web_app/src | app/wishlist/page.tsx | page.tsx:57,71 | Empty handler | `.catch(() => setLoading(false))` hides wishlist fetch failures | NEW | no |
| 125 | frontend/web_app/src | components/country/CountryResearchPanel.tsx | CountryResearchPanel.tsx:299,304 | Empty handler | `.catch(() => ({}))` / `} catch (err) { }` hides research fetch failure | NEW | yes |
| 126 | frontend/web_app/src | components/country/CountryStaffAssignmentModal.tsx | CountryStaffAssignmentModal.tsx:67 | Empty handler | `} catch (err: any) { }` hides staff assignment failure | NEW | yes |
| 127 | frontend/web_app/src | components/country/ShiftHandoverModal.tsx | ShiftHandoverModal.tsx:57 | Empty handler | `} catch (err: any) { }` hides shift handover failure | NEW | yes |
| 128 | frontend/web_app/src | components/country/LegalContractGenerator.tsx | LegalContractGenerator.tsx:115,151 | Empty handler | 2× `} catch (error) { }` hides contract generation failures | NEW | yes |
| 129 | frontend/web_app/src | components/country/ParcelTracker.tsx | ParcelTracker.tsx:43 | Empty handler | `.catch(() => null)` hides parcel tracking failure | NEW | no |
| 130 | frontend/web_app/src | components/ems/PayrollWorkflow.tsx | PayrollWorkflow.tsx:56,70 | Empty handler | 2× `} catch (e: any) { }` hides payroll workflow failures | NEW | yes |
| 131 | frontend/web_app/src | components/ems/OrgChartTree.tsx | OrgChartTree.tsx:56 | Empty handler | `} catch (e: any) { }` hides org chart fetch failure | NEW | no |
| 132 | frontend/web_app/src | components/ems/ActivityTimeline.tsx | ActivityTimeline.tsx:106 | Empty handler | `} catch (e: any) { }` hides activity timeline failure | NEW | no |
| 133 | frontend/web_app/src | components/BackgroundJobCenter.tsx | BackgroundJobCenter.tsx:57 | Empty handler | `.catch(() => undefined)` hides background job status failure | NEW | no |
| 134 | frontend/web_app/src | components/BannerCarousel.tsx | BannerCarousel.tsx:64 | Empty handler | `.catch(() => {})` hides banner fetch failure | NEW | no |
| 135 | frontend/web_app/src | components/VideoScrollingRow.tsx | VideoScrollingRow.tsx:47 | Empty handler | `.catch(() => {})` hides video fetch failure | NEW | no |
| 136 | frontend/web_app/src | components/MobileSearchOverlay.tsx | MobileSearchOverlay.tsx:227 | Empty handler | `.catch(() => {})` hides search overlay failure | NEW | no |
| 137 | frontend/web_app/src | components/FraudDetectionDashboard.tsx | FraudDetectionDashboard.tsx:93-113 | Empty handler | 5× `.catch(() => null)` / `.catch(() => [])` hides fraud data failures | NEW | yes |
| 138 | frontend/web_app/src | components/ApprovalActionModal.tsx | ApprovalActionModal.tsx:91,94,135 | Empty handler | `.catch(() => ({}))` / `} catch (err) { }` hides approval fetch failure | NEW | yes |
| 139 | frontend/web_app/src | components/auth/GoogleSignInButton.tsx | GoogleSignInButton.tsx:77,82 | Empty handler | `.catch(() => null)` / `} catch (err) { }` hides Google sign-in failure | NEW | yes |
| 140 | frontend/web_app/src | components/admin/CreateCampaignForm.tsx | CreateCampaignForm.tsx:53,108 | Empty handler | 2× `} catch (error) { }` hides campaign form failures | NEW | yes |
| 141 | frontend/web_app/src | components/admin/EmailSuppressionManager.tsx | EmailSuppressionManager.tsx:37,70 | Empty handler | 2× `} catch (err) { }` hides suppression manager failures | NEW | yes |
| 142 | frontend/web_app/src | components/comms/Rail/ThreadContextMenu.tsx | ThreadContextMenu.tsx:78,113 | Empty handler | 2× `} catch (err) { }` hides thread action failures | NEW | yes |
| 143 | frontend/web_app/src | components/comms/Rail/EmailFolderTree.tsx | EmailFolderTree.tsx:63,90,123,144 | Empty handler | 4× `} catch (err) { }` hides folder tree failures | NEW | yes |
| 144 | frontend/web_app/src | app/api/z-rmbg/route.ts | route.ts:64 | Empty handler | `} catch (error) { }` hides AI background removal failure | NEW | no |
| 145 | frontend/web_app/src | app/api/auth/social-callback/route.ts | route.ts:20,75 | Empty handler | `.catch(() => null)` / `} catch (error) { }` hides social auth failure | NEW | yes |
| 146 | frontend/web_app/src | hooks/useSendMessage.ts | useSendMessage.ts:117,145,182,220 | Empty handler | 4× `} catch (err) { }` hides message send/reply failures | NEW | yes |
| 147 | frontend/web_app/src | hooks/useThreadMessages.ts | useThreadMessages.ts:61 | Empty handler | `} catch (e) { }` hides thread message fetch failure | NEW | no |
| 148 | frontend/web_app/src | hooks/useUnifiedInbox.ts | useUnifiedInbox.ts:49 | Empty handler | `} catch (e) { }` hides inbox fetch failure | NEW | no |
| 149 | frontend/web_app/src | hooks/useApprovalCheck.ts | useApprovalCheck.ts:60 | Empty handler | `.catch(() => ({} as any))` hides approval check failure | NEW | yes |
| 150 | frontend/web_app/src | hooks/useCrossBorder.ts | useCrossBorder.ts:68 | Empty handler | `} catch (err) { }` hides cross-border fetch failure | NEW | no |
| 151 | frontend/web_app/src | hooks/useCountryAutoPopulate.ts | useCountryAutoPopulate.ts:85 | Empty handler | `} catch (err: any) { }` hides country auto-populate failure | NEW | no |
| 152 | frontend/web_app/src | lib/cartStore.ts | cartStore.ts:177,195,215,235,246 | Empty handler | 5× `.catch(() => {/* swallow */})` / `.catch(() => {})` hides cart sync failures | NEW | yes |
| 153 | frontend/web_app/src | lib/useAuth.tsx | useAuth.tsx:91 | Empty handler | `} catch (error) { }` hides auth initialization failure | NEW | yes |
| 154 | frontend/web_app/src | lib/authCapabilities.ts | authCapabilities.ts:34,42 | Empty handler | `.catch(() => null)` / `} catch (err) { }` hides capabilities fetch failure | NEW | yes |
| 155 | frontend/web_app/src | lib/api/client.ts | api/client.ts:164 | Empty handler | `} catch (err) { }` hides generic API client failure | NEW | yes |
| 156 | frontend/web_app/src | lib/api/country.ts | api/country.ts:97 | Empty handler | `} catch (error) { }` hides country config fetch failure | NEW | yes |
| 157 | frontend/web_app/src | lib/uploadOrchestrator.ts | uploadOrchestrator.ts:210 | Empty handler | `} catch (err: any) { }` hides upload orchestration failure | NEW | yes |
| 158 | frontend/web_app/src | lib/useBgABTest.ts | useBgABTest.ts:102,130 | Empty handler | 2× `} catch (err: any) { }` hides A/B test fetch failures | NEW | no |
| 159 | frontend/web_app/src | lib/useBgRecommendations.ts | useBgRecommendations.ts:89 | Empty handler | `} catch (err: any) { }` hides recommendations fetch failure | NEW | no |
| 160 | frontend/web_app/src | lib/wishlistStore.ts | wishlistStore.ts:50,62,92 | Empty handler | 3× `.catch(() => null)` hides wishlist mutation failures | NEW | yes |
| 161 | frontend/web_app/src | shared/returnsApi.ts | returnsApi.ts:60 | Empty handler | `.catch(() => ({}))` hides returns API error parsing | NEW | no |
| 162 | frontend/web_app/src | shared/realtime.ts | realtime.ts:131 | Empty handler | `.catch(() => undefined)` hides realtime subscription failure | NEW | no |
| 163 | frontend/web_app/src | shared/api-core.ts | api-core.ts:162 | Empty handler | `.catch(() => null)` hides API response body read failure | NEW | no |
| 164 | frontend/web_app/src | lib/hierarchyApi.ts | hierarchyApi.ts:88,97 | Empty handler | 2× `.catch(() => ({}))` hides hierarchy API error parsing | NEW | no |
| 165 | frontend/web_app/src | lib/payoutsApi.ts | payoutsApi.ts:24,52 | Empty handler | 2× `.catch(() => ({}))` hides payouts API error parsing | NEW | no |
| 166 | frontend/web_app/src | lib/crossBorderService.ts | crossBorderService.ts:99,176,206,236 | Empty handler | 4× `} catch (error) { }` hides cross-border service failures | NEW | yes |
| 167 | frontend/web_app/src | lib/useAdminApi.ts | useAdminApi.ts:103 | Empty handler | `} catch (err) { }` hides admin API failure | NEW | yes |
| 168 | frontend/web_app/src | lib/api/queryStates.ts | api/queryStates.ts:42 | Empty handler | `.catch(() => "")` hides query state read failure | NEW | no |
| 169 | frontend/web_app/src | app/api/auth/social-callback/route.ts | route.ts:20,75 | Empty handler | `.catch(() => null)` / `} catch (error) { }` hides social auth failure | NEW | yes |
| 170 | frontend/web_app/src | app/employee/dashboard/page.tsx | page.tsx:84-89,297 | Empty handler | 6× `.catch(() => null)` / `} catch (e) { }` hides employee dashboard failures | NEW | no |
