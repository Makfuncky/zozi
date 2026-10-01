# ZOZI — Complete Feature List (Master Index)

Format: `Feature | Description | Workflow | Actor(s)`

---

## 1. Infrastructure & Cross-Cutting

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Authentication & Identity | Core login/session infrastructure for every actor | 1. Login (email/password/Google/Facebook/ID-token) → 2. Verify email → 3. TOTP setup/verify → 4. Session established → 5. List/revoke sessions → 6. Logout | All |
| Email Verification | Prove ownership of registered email | 1. Register → 2. Verification email sent → 3. Click link → 4. Account activated | All |
| Password Reset | Recover access after forgotten password | 1. Request reset → 2. Email link → 3. Enter new password → 4. All refresh families revoked → 5. Re-login | All |
| TOTP / MFA | Second-factor authentication | 1. Enable in settings → 2. Scan QR → 3. Verify 6-digit code → 4. Backup codes issued → 5. Prompted on every login | All |
| Session & Device Binding | See and control active sessions | 1. Open security settings → 2. View active sessions → 3. Revoke unrecognized → 4. Target device forced to re-login | All |
| RBAC / Permissions | Feature-gate every endpoint and UI surface | 1. Domain declares feature atom → 2. Catalog aggregates → 3. Role assignment → 4. `require_feature()` gate → 5. Frontend reads generated permissions | All |
| Audit Logging | Append-only record of every state change | 1. Service calls audit.log() → 2. HMAC signature → 3. Row appended → 4. Read via admin timeline / customer activity | All |
| Event Bus / Outbox | Transactional cross-domain messaging | 1. Domain writes business row + outbox row in same TX → 2. Relay worker → 3. Broker → 4. Subscriber consumes → 5. DLQ on failure | System |
| Background Jobs | Off-request heavy work | 1. Scheduler enqueues → 2. Worker claims → 3. Executes → 4. Updates status → 5. Retry / DLQ | System |
| Scheduler & Cron | Time-driven task execution | 1. Cron registered → 2. Fires at interval → 3. Enqueues job → 4. Status tracked → 5. Failure alerts | System |
| Email Service | Transactional + campaign email delivery | 1. Template resolved → 2. Provider selected → 3. Sent → 4. Delivery event recorded → 5. Suppression enforced | All |
| Realtime / WebSockets | Live push to connected clients | 1. WS handshake with token → 2. Channel subscription → 3. Server fan-out → 4. Client updates UI → 5. Reconnect on drop | All |
| Webhook Ingress | External event reception | 1. Receive → 2. Verify signature → 3. IP whitelist → 4. Idempotency check → 5. Route to handler → 6. Retry / DLQ | System |
| Notification Engine | Multi-channel notification delivery | 1. Domain emits event → 2. Subscriber resolves preferences → 3. In-app / push / email queued → 4. Delivered → 5. Read tracked | All |
| Observability & Monitoring | Metrics, logs, traces, alerts | 1. Structured logging → 2. Prometheus scrape → 3. Trace export → 4. Alert rules fire → 5. Grafana dashboard | Admin |
| Search Engine (hybrid) | FTS + pgvector + CLIP product search | 1. Query parsed → 2. Lexical + semantic + visual retrieval → 3. RRF fusion → 4. Filters applied → 5. Cursor paginated results | Customer / All |
| AI Provider Services | Shared AI capabilities (chat, vision, OCR, embeddings) | 1. Service calls provider → 2. Provider health-checked → 3. Inference runs → 4. Result returned → 5. Degraded mode reported if unavailable | System |
| Currency & FX | Multi-currency pricing and conversion | 1. Rate fetched → 2. Cached → 3. Converted at checkout → 4. Revaluation job at month-end | All |
| Geolocation & Maps | Country detection, geo-fencing, routing | 1. Resolve country (JWT → staff → IP → header) → 2. Geo-fence validation → 3. Distance calc → 4. Map render | All |
| QR & Barcode Services | Generate and validate QR codes | 1. Token generated → 2. Signed → 3. Rendered → 4. Scanned → 5. Server-side validation with role/status check | All |
| Valkey / Redis Cache | Session, catalog, rate-limit cache | 1. Key lookup → 2. Miss → 3. Fetch + set with TTL → 4. Invalidate on write | System |
| Database & Migrations | Schema source of truth | 1. Model change → 2. Alembic migration → 3. CI drift check → 4. Deploy → 5. Verified at boot | System |
| Data Backup & Retention | Automated backup + lifecycle retention | 1. Scheduled backup → 2. Verification → 3. Retention policy applied → 4. Cold archive → 5. Destructive purge on expiry | System |
| Storage & Media (R2/S3) | Object storage for all media | 1. Presigned URL issued → 2. Client uploads → 3. Metadata registered → 4. Optimization job → 5. CDN served | All |
| Middleware Pipeline | Ordered security/geo/RLS enforcement | 1. Request enters → 2. Country context → 3. Auth → 4. RBAC → 5. CSRF → 6. Rate limit → 7. Router | System |
| Security Infrastructure | Encryption, KMS, rate-limit, fraud, IP utils | 1. Field-level encryption → 2. Key rotation → 3. Rate-limit checks → 4. Fraud score computed | System |
| News & RSS Ingestion | External market intelligence feed | 1. Fetch RSS/API → 2. Dedupe by hash → 3. Sanitize → 4. AI tag/sentiment → 5. Route to audience | Admin |

---

## 2. Customer

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Customer Registration | Create customer account | 1. Fill form → 2. Verify email → 3. Welcome email → 4. Optional referral link applied | Customer |
| Customer Login | Authenticate customer | 1. Email/password or social → 2. Optional TOTP → 3. RLS context set → 4. Redirect to home | Customer |
| Customer Profile & Settings | Manage personal info, preferences | 1. Open profile → 2. Edit name/phone → 3. Save → 4. Audit logged → 5. Toast confirmation | Customer |
| Address Book | Manage shipping addresses | 1. Open addresses → 2. Add/edit/delete → 3. Set default → 4. Field-level encrypted | Customer |
| Cart | Server-side shopping cart | 1. Add item → 2. Sync across devices → 3. Update qty → 4. Remove → 5. Totals calculated | Customer |
| Checkout (4-step) | Complete purchase | 1. Address → 2. Delivery → 3. Payment → 4. Confirm → 5. Order created → 6. Stock reserved | Customer |
| Payment — Card (Stripe/Tap/PayTabs) | Card payment via gateway | 1. Select card → 2. Payment intent created → 3. 3DS/confirm → 4. Webhook → 5. Order finalized | Customer |
| Payment — Cash on Delivery | Pay on delivery | 1. Select COD → 2. Order placed → 3. Logistics collects cash → 4. Remittance to treasury | Customer |
| Coupon Validation | Apply discount code | 1. Enter code → 2. Validate (expiry/usage/min-order) → 3. Discount applied → 4. Order total updated | Customer |
| Order History | Browse past orders | 1. Open orders → 2. Filter by status/date → 3. View detail → 4. Download invoice | Customer |
| Order Detail & Tracking | Live order status | 1. Open order → 2. View timeline → 3. Live GPS map → 4. Shipment events → 5. Proof-of-delivery | Customer |
| Order Cancellation | Cancel order before fulfillment | 1. Open order → 2. Request cancel → 3. Reason → 4. Inventory restored → 5. Refund queued | Customer |
| Return Request | Request return or replacement | 1. Open delivered order → 2. Select items → 3. Choose return/replacement → 4. Reason + photos → 5. Admin review | Customer |
| Return Tracking | Track return status | 1. Open returns → 2. View status → 3. Reverse shipment → 4. Refund status | Customer |
| Invoice Viewing | Download invoice (HTML/PDF) | 1. Open order → 2. Click invoice → 3. Render → 4. Download | Customer |
| Wishlist | Save products for later | 1. Heart icon on product → 2. Saved → 3. Wishlist page → 4. Move to cart → 5. Feeds recommendations | Customer |
| Reviews & Ratings | Post-purchase review | 1. After delivery → 2. Write review → 3. Star rating → 4. Photos optional → 5. Visible on product page | Customer |
| Product Catalog Browse | Browse products by category/badge | 1. Open catalog → 2. Filter by category/badge → 3. Paginate → 4. Click product | Customer |
| Product Detail | Full product view | 1. Open PDP → 2. View gallery/video → 3. Variants → 4. Supplier info → 5. Reviews → 6. Add to cart | Customer |
| Product Search | Hybrid search | 1. Type query → 2. Autocomplete → 3. Filter/sort → 4. Results → 5. Did-you-mean for typos | Customer |
| Image Search | Search by photo | 1. Upload photo → 2. CLIP embed → 3. Visual similarity → 4. Results | Customer |
| Voice Search | Search by voice | 1. Tap mic → 2. Transcribe → 3. NLP parse → 4. Results | Customer |
| Recommendations | Personalized product suggestions | 1. Browse/purchase signals collected → 2. 5-signal blend → 3. Cache → 4. Rendered | Customer |
| Notifications (In-App) | Real-time notification badge/list | 1. Event occurs → 2. WS pushes → 3. Bell updates → 4. Mark read | Customer |
| Push Notifications | Mobile push alerts | 1. Token registered → 2. Event → 3. Push sent → 4. Tap opens deep link | Customer |
| Support Tickets | Raise and track tickets | 1. Create ticket → 2. Category + attachments → 3. Replies → 4. Status → 5. Closed | Customer |
| Chatbot | AI assistant | 1. Open chat → 2. Query → 3. Intent parsed → 4. Product suggestions / answer → 5. Follow-up | Customer |
| Newsletter | Subscribe and manage preferences | 1. Sign up → 2. Preferences → 3. Unsubscribe → 4. Status tracked | Customer |
| Referrals | Refer friends, earn coins | 1. Get referral code → 2. Share → 3. Friend registers + buys → 4. Points awarded → 5. Redeem at checkout | Customer |
| Zozi Coins / Rewards | Balance and redemption | 1. Earn from purchases/referrals → 2. View balance → 3. Redeem at checkout → 4. Partial payment allowed | Customer |
| Barcode Scan (Receipt Verify) | Verify delivery via scan | 1. Open scanner → 2. Scan parcel QR → 3. Confirm receipt → 4. Order marked delivered | Customer |
| Delivery Confirmation | Confirm receipt (alternate path) | 1. Logistics sends request → 2. Customer notified → 3. Confirm receipt → 4. Order delivered | Customer |
| Avatar Upload | Profile picture | 1. Upload → 2. Presigned URL → 3. Optimized → 4. Profile updated | Customer |
| Data Export (GDPR) | Download personal data | 1. Request export → 2. Job queued → 3. Package built → 4. Download link | Customer |
| Account Deletion Request | Request account removal | 1. Request → 2. Confirmation → 3. Retention policy applied → 4. Data purged/anonymized | Customer |
| Loyalty VIP Tiers | **MISSING** — Bronze/Silver/Gold based on lifetime spend | 1. Spend threshold → 2. Tier upgrade → 3. Multiplier + benefits unlocked | Customer |
| Saved Payment Methods | **MISSING** — vault cards for 1-click | 1. Save card → 2. Token stored → 3. 1-click checkout next time | Customer |
| Apple Pay / Google Pay | **MISSING** — native payment | 1. Tap Pay → 2. OS sheet → 3. Confirm → 4. Order placed | Customer |
| Product Comparison | **MISSING** — compare 2–4 products | 1. Add to compare → 2. Comparison table → 3. Pick winner | Customer |
| Social Sharing | **MISSING** — share products/wishlist | 1. Tap share → 2. OS sheet → 3. Deep link | Customer |
| Video Commerce (PDP) | **MISSING** — video on product page | 1. Video uploaded by supplier → 2. Transcode + captions → 3. Play on PDP | Customer |

---

## 3. Supplier

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Supplier Registration | Create supplier account | 1. Register → 2. Role set → 3. Onboarding wizard → 4. Admin approval | Supplier |
| Supplier Login | Authenticate | 1. Email/password or social → 2. TOTP → 3. Redirect to dashboard | Supplier |
| KYC Onboarding | Submit verification documents | 1. Upload docs (type + expiry) → 2. Admin review → 3. Approved → 4. Status promoted | Supplier |
| Profile Management | Business details, storefront | 1. Open profile → 2. Edit sections (account, business, storefront, security, payout) → 3. Save → 4. Audit | Supplier |
| Bank Account Setup | Register payout bank account | 1. Enter IBAN/SWIFT → 2. Admin verifies → 3. Penney-test → 4. Active for payouts | Supplier |
| Product Upload — Method 1 (Manual) | Fill form manually | 1. Click "Add Product" → 2. Fill all fields → 3. Upload image → 4. Set variants → 5. Publish | Supplier |
| Product Upload — Method 2 (Photo-first AI) | Upload image → AI fills everything | 1. Upload/capture → 2. BG removal + AI analysis parallel → 3. Review AI-filled fields → 4. Quantity popups per color → 5. Verify → 6. Publish | Supplier |
| Product Upload — Method 3 (Voice-first) | Voice note → AI fills | 1. Upload image → 2. Tap mic → 3. Say product details → 4. NLP parse → 5. Review + quantity → 6. Publish | Supplier |
| Bulk CSV Import | Import many products via CSV | 1. Download template → 2. Upload CSV → 3. Validation → 4. Row-by-row processing → 5. Error report | Supplier |
| Bulk CSV Export | Export catalog | 1. Click export → 2. Stream CSV → 3. Download | Supplier |
| Image Tools (12 tools) | BG removal, crop, tone, upscale, etc. | 1. Select image → 2. Choose tools (magic erase, smart crop, rotate, auto-light, denoise, WB, color enhance, auto-levels, upscale, sharpen, compress, WebP) → 3. Process → 4. Compare → 5. Apply | Supplier |
| BG Removal Comparison | Compare 6 BG models side-by-side | 1. Upload → 2. Run 6 models in parallel → 3. Grid/side-by-side/diff view → 4. Pick best | Supplier |
| Product Edit | Update listing | 1. Open product → 2. Edit fields → 3. Save → 4. Audit logged | Supplier |
| Product Delete (soft) | Archive a product | 1. Open product → 2. Delete → 3. Soft-deleted → 4. Hidden from catalog → 5. Restorable | Supplier |
| Discount Setup | Product-level discount | 1. Open product → 2. Set compare_price + window → 3. Save → 4. Lime badge on card | Supplier |
| Inventory Management | Stock levels per variant | 1. Open product → 2. Edit stock per variant → 3. Save → 4. Low-stock alert at ≤5 | Supplier |
| Order Management | Receive and process orders | 1. New order alert → 2. Accept → 3. PROCESSING → 4. Prepare → 5. PREPARED | Supplier |
| Parcel Proof Upload | Photo of packed parcel | 1. Print parcel sheet → 2. Pack → 3. Upload photo → 4. Status → PREPARED → 5. Logistics notified | Supplier |
| Parcel Sheet Print | Print shipping label with QR | 1. Open order → 2. Click "Print Parcel Sheet" → 3. Label rendered → 4. Print | Supplier |
| Shipping Label Mobile | Print/share from app | 1. Open order on mobile → 2. Generate label → 3. Native print/share | Supplier |
| Logistics Zones & Carriers | Manage zones and carriers | 1. Open logistics → 2. CRUD zones → 3. CRUD carriers → 4. Rates applied at checkout | Supplier |
| Order Tracking View | Track own orders | 1. Open order → 2. View shipment events → 3. Handoff status | Supplier |
| Analytics & Reports | Sales, revenue, product performance | 1. Open analytics → 2. Select range → 3. View charts → 4. Export | Supplier |
| Payout Dashboard | View payouts and settlements | 1. Open payouts → 2. View summary → 3. List settlements → 4. Request payout → 5. History | Supplier |
| Invoice Records | View invoices | 1. Open payouts → 2. Invoice tab → 3. Download | Supplier |
| Commission Agreement | View effective rate | 1. Open commission → 2. View global/category/badge/override → 3. Preview calculator | Supplier |
| Credibility Badge | Score + badge tier | 1. Score computed from orders/reviews/docs/timeliness → 2. Badge assigned → 3. Displayed on cards | Supplier |
| Storefront / About Page | Public supplier page | 1. Configure in profile → 2. Banner, logo, About, certs, socials → 3. Publish → 4. Public URL | Supplier |
| Returns Queue | Review returned items | 1. Open returns → 2. View items → 3. Approve/reject/restock → 4. Per-supplier state | Supplier |
| Dispute Center | Raise/respond to disputes | 1. Create dispute → 2. Evidence URLs → 3. Status tracked → 4. Admin resolves | Supplier |
| Notification Preferences | Per-event toggles | 1. Open preferences → 2. Toggle channels → 3. Save | Supplier |
| Supplier Support | Unified ticket surface | 1. Create ticket → 2. Replies → 3. Resolution | Supplier |
| AI Product Descriptions | Generate copy | 1. Click ⚡ AI → 2. Suggestion → 3. Accept/edit | Supplier |
| Multi-User Sub-Accounts | **MISSING** — team roles | 1. Create sub-user → 2. Assign role → 3. Warehouse/accounting/manager permissions | Supplier |
| Quality Control | Product QC and returns QC | 1. Open QC → 2. View product QC status → 3. View returns QC metrics → 4. Return rate computed | Supplier |
| Legal Contracts | Generate country-specific contracts | 1. Open contracts → 2. Generate ToS / Privacy / Supplier Agreement → 3. Country-specific legal template applied | Supplier |
| Settlement | Multi-currency settlement | 1. Open settlements → 2. View multi-currency breakdown → 3. Settlement recorded | Supplier |
| Governance / Admin Operations | Admin supplier operations | 1. Open admin panel → 2. Verify/reject/suspend/reactivate suppliers → 3. Bulk verify → 4. Audit logged | Supplier |
| Compliance | View compliance status | 1. Open compliance → 2. Checklist + status → 3. Remediate | Supplier |
| Badge Tiers Write | Manage badge tiers | 1. Open badge tiers → 2. Edit tier → 3. Commission rate + fees → 4. Qualification thresholds | Supplier |
| Analytics Export | Export analytics to CSV/PDF | 1. Open reports → 2. Export | Supplier |
| Onboarding Pipeline | View/manage onboarding pipeline | 1. Open onboarding → 2. View pipeline progress → 3. Complete stages → 4. Upload documents | Supplier |

---

## 4. Logistics Partner

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Partner Registration | Self-register | 1. Register → 2. Role set → 3. Admin approval required | Logistics |
| Partner Login | Authenticate | 1. Login → 2. Redirect to dashboard | Logistics |
| Profile & Documents | Company details + KYC docs | 1. Open profile → 2. Fill details → 3. Upload docs → 4. Submit for review | Logistics |
| Terms Acceptance | Accept platform terms | 1. Open terms → 2. Read → 3. Accept → 4. Recorded | Logistics |
| Service Areas | Define cities served | 1. Open service areas → 2. Add city → 3. Set charges → 4. Submit for admin approval | Logistics |
| Delivery Settings (Charges) | Pickup + delivery charges per city pair | 1. Open delivery settings → 2. Add country/pickup city/delivery city/charges → 3. Submit → 4. Admin approves → 5. Reflects in cart | Logistics |
| Pricing Profiles | Rule-based pricing | 1. Create profile → 2. Set rules → 3. Activate | Logistics |
| Vehicle Rules | Vehicle-based pricing | 1. Create rule → 2. Set vehicle type + rate → 3. Activate | Logistics |
| Category Rules | Category-specific charges | 1. Create rule → 2. Set category + surcharge → 3. Activate | Logistics |
| Dashboard & KPIs | Performance overview | 1. Open dashboard → 2. View delivery rate, avg transit, scan compliance, SLA → 3. Live fleet map → 4. Route plan → 5. SLA alerts | Logistics |
| Shipment Queue | Available and active shipments | 1. Open queue → 2. See PREPARED shipments flashing → 3. Claim one → 4. Status = PICKING UP → 5. Hidden from others | Logistics |
| Pickup Claim & Cancel | Claim or cancel a pickup | 1. Claim → 2. PICKING UP → 3. Optional cancel before picked → 4. Returns to PREPARED | Logistics |
| QR Scan Handover | Scan parcel at pickup | 1. Open scan → 2. Scan QR → 3. Status = PICKED FROM SUPPLIER → 4. Idempotent | Logistics |
| Transit Updates | Update status through transit | 1. LOGISTIC RECEIVED → 2. DISTRIBUTION CHECKPOINT → 3. OUT FOR DELIVERY → 4. GPS logged | Logistics |
| Delivery Confirmation | Confirm delivery | 1. Capture e-signature → 2. Upload proof → 3. Status = DELIVERED → 4. Settlement triggered | Logistics |
| Exception Handling | Handle delays/failures | 1. Mark DELAYED / RESCHEDULED / FAILED → 2. Return to supplier if FAILED → 3. Cancel | Logistics |
| Package Metadata | Weight, dimensions, notes | 1. Open shipment → 2. Add package_count, weight, dims, notes → 3. Save | Logistics |
| GPS Ingestion | Live location tracking | 1. App sends lat/lng → 2. Attached to shipment event → 3. Visible on map | Logistics |
| Delivery Tracking View | Track own shipments | 1. Open shipments → 2. View events → 3. Timeline | Logistics |
| Barcode Scan | Scan parcel QR | 1. Open scanner → 2. Scan → 3. Lookup shipment → 4. Update status | Logistics |
| Product Verification (receipt) | Verify product at receipt | 1. Open verification → 2. Enter specs + result → 3. Evidence URL → 4. Record created | Logistics |
| Carrier Management | Manage carriers | 1. CRUD carriers → 2. Set tracking URL template | Logistics |
| Auto-Invoice on Shipment | Invoice generated on shipment creation | 1. Shipment created → 2. Invoice auto-generated → 3. Emailed to customer | Logistics |
| COD Remittance | Remit collected cash | 1. Collect cash → 2. Upload receipt → 3. Remit to treasury → 4. Reconciliation | Logistics |
| Bank Account | Payout account | 1. Enter IBAN → 2. Admin verifies → 3. Active | Logistics |
| Payout Dashboard | View payouts & settlements | 1. Open payouts → 2. Summary → 3. Settlements → 4. Request payout | Logistics |
| Revenue & Payout Center | Track earnings | 1. Open dashboard → 2. Revenue summary → 3. Request payout | Logistics |
| Route Optimization | Suggest optimized route | 1. Open route → 2. System uses latest GPS checkpoints → 3. Route suggested | Logistics |
| SLA Breach Alerts | Real-time SLA warnings | 1. Shipment breaches SLA → 2. Alert card → 3. Notification | Logistics |
| Analytics | Delivery performance | 1. Open analytics → 2. View metrics → 3. Export | Logistics |
| Fleet Management | **MISSING** — drivers and vehicles | 1. Add driver → 2. Add vehicle → 3. Assign → 4. Track | Logistics |
| Geo / Fence Management | Geo-fence validation for check-ins | 1. Define geo-fence → 2. Validate check-in location → 3. Log result | Logistics |
| Health Score | View logistics health score | 1. Open dashboard → 2. Score + factors → 3. Improve | Logistics |
| SLA Management | Configure SLA rules | 1. Open SLA → 2. Set rules → 3. Activate → 4. Breach alerts | Logistics |
| COD Reconciliation | Reconcile COD remittances | 1. View receipts → 2. Verify → 3. Match to orders → 4. Flag variance | Logistics |
| Country Management | Manage country logistics config | 1. Open country → 2. Configure logistics settings → 3. Publish | Logistics |

---

## 5. Employee

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Employee Login | Authenticate (5 doors) | 1. Password+TOTP / OTP / Biometric / QR kiosk / SSO → 2. RLS set → 3. Redirect | Employee |
| Self-Service Portal | Personal workspace | 1. Open ESS → 2. Profile, leave, attendance, payslips, OKRs, org chart | Employee |
| Profile Management | Edit personal info | 1. Open profile → 2. Edit → 3. Save → 4. Audit | Employee |
| Leave Balance & History | View leave | 1. Open leave → 2. Balance → 3. History | Employee |
| Leave Request | Request time off | 1. Create request → 2. Auto-approve if ≤ threshold → 3. Else route to manager → 4. Approval | Employee |
| Leave Approval (Manager) | Approve subordinate leave | 1. Notification → 2. Open queue → 3. Approve/reject → 4. Escalation if unactioned | Employee (Manager) |
| Attendance View | View attendance records | 1. Open attendance → 2. Calendar view → 3. Anomalies flagged | Employee |
| Check-In / Check-Out | Manual attendance | 1. Tap check-in → 2. Geo-fence validated → 3. Recorded | Employee |
| QR Kiosk Check-In | Zero-touch attendance | 1. Walk to kiosk → 2. Scan QR → 3. Geo-fence check → 4. Attendance logged → 5. Optional biometric | Employee |
| Payslip Access | View/download payslips | 1. Open payroll → 2. List → 3. Download PDF | Employee |
| OKR / KPI View | View objectives and metrics | 1. Open OKRs → 2. View objectives → 3. Progress → 4. Update KR | Employee |
| Org Chart View | See team structure | 1. Open org chart → 2. Navigate tree → 3. View profiles | Employee |
| Team Subordinates | View reports | 1. Open team → 2. List subordinates → 3. Drill down | Employee (Manager) |
| Shift View | View shift roster | 1. Open shifts → 2. Upcoming → 3. Swap requests | Employee |
| Shift Handover | Acknowledge pending tasks before clock-out | 1. Clock-out attempt → 2. Handover task list → 3. Acknowledge → 4. Clock-out allowed | Employee |
| Work Logs | Log hours | 1. Open work logs → 2. Add entry → 3. Submit → 4. Approval | Employee |
| Performance Review | Self and peer review | 1. Cycle opens → 2. Self-assessment → 3. Manager + peer input → 4. Score computed | Employee |
| Training Modules | Complete assigned training | 1. Open training → 2. View modules → 3. Complete → 4. Progress tracked | Employee |
| Expense Submission | Submit expense | 1. Upload receipt → 2. Fill form → 3. Submit → 4. Approval chain | Employee |
| Document Upload | Upload personal documents | 1. Open documents → 2. Upload → 3. HR review | Employee |
| Internal Chat | 1:1, group, channel chat | 1. Open chat → 2. Select thread → 3. Send message / attachment / voice note | Employee |
| Internal Email | Send internal mail | 1. Compose → 2. Directory-first autocomplete → 3. Send (internal = in-DB) → 4. External = DLP + SMTP | Employee |
| Video Conferencing | Schedule and join meetings | 1. Create meeting → 2. Invite → 3. Join with token → 4. Recording + transcript + action items | Employee |
| Contacts Directory | Lookup colleagues | 1. Open directory → 2. Search → 3. View profile → 4. Start chat/call | Employee |
| Employee Activity Ledger | Personal activity timeline | 1. Open ledger → 2. View actions → 3. Filter | Employee |
| Mobile Employee App | **MISSING** — attendance, leave, payslips on mobile | 1. Biometric login → 2. Access ESS screens | Employee |
| Unified Inbox / Confluence | Single triage queue across chat/email/video/tickets | 1. Open inbox → 2. Lens filter → 3. Open thread → 4. Reply (send-as toggle) → 5. Context inspector | Employee |
| PIP Workflow | Performance Improvement Plan | 1. Low score detected → 2. PIP auto-triggered → 3. Milestones set → 4. Manager reviews → 5. Close or escalate | Employee |
| Team Health Radar | Team performance overview | 1. Open radar → 2. View team metrics → 3. Drill down into issues | Employee (Manager) |
| Purchase Order CRUD | Manage purchase orders | 1. Create PO → 2. Confirm → 3. Receive goods → 4. Match to invoice | Employee |
| Sales Order CRUD | Manage sales orders | 1. Create SO → 2. Confirm → 3. Dispatch → 4. Invoice | Employee |
| Goods Receipt / 3-Way Match | Match PO/GRN/Invoice | 1. Receive goods → 2. Match PO/GRN/Invoice → 3. Post AP | Employee |
| Dunning Run | Automated overdue AR collection | 1. Trigger dunning → 2. Emails day 3/7/14 → 3. Late fee applied | Employee |
| Access Recertification | Quarterly permission review | 1. Quarterly campaign → 2. Auto-revoke unconfirmed grants → 3. Manager review queue → 4. Audit logged | Employee |
| Bank-Detail Change Freeze | Verification freeze + penny-test | 1. Bank detail change → 2. Verification freeze → 3. Penny-test before next payroll → 4. Block until verified | Employee |
| Boomerang Re-hire | Return alumni to active | 1. Alumni re-hire triggered → 2. Restore employee → 3. Reactivate sessions/devices → 4. EOSB settlement reversed | Employee |
| Continuous Check-ins | Monthly 1:1 logs | 1. Monthly 1:1 scheduled → 2. Manager + report log → 3. Stored/searchable → 4. Replaces annual review | Employee |
| 360° Performance Review | Multi-source feedback | 1. Cycle opens → 2. Self + manager + peer + subordinate input → 3. Weighted score → 4. Computed into performance_score | Employee |
| OKR Cascade Framework | Company→dept→individual objectives | 1. Company OKRs set → 2. Cascade via hierarchy → 3. Department → 4. Individual KR progress tracked | Employee |
| KPI Metrics Auto-Pull | Quantitative metrics from ops tables | 1. Nightly cron → 2. Read-only pull from commerce/logistics/support → 3. Compute KPI → 4. Feed into health score/bonus | Employee |
| Performance Health Score | R/A/G performance indicator | 1. Combine attendance + work_logs + KPI + leave patterns + anomalies → 2. Compute R/A/G → 3. Surface on manager dashboard | Employee |
| PIP & Recognition | Low-score PIP / high-score rewards | 1. Low score → auto PIP → 2. Milestones → 3. Close or escalate to disciplinary → 4. High score → bonus multiplier + recognition badges | Employee |
| Performance Calibration | Department score normalization | 1. Calibration session → 2. Normalize scores → 3. Flag top/bottom percentiles → 4. Finalize ratings | Employee |
| HR Analytics Dashboards | Headcount, attrition, DEI, leave burn | 1. Open analytics → 2. Materialized views refresh → 3. Headcount/attrition/DEI/OT cost charts → 4. Export | Employee |
| Onboarding SLA Pipeline | New hire automation with SLA | 1. Offer accepted → 2. Auto-create user+employee → 3. Assign org/role/country → 4. Track steps with SLA → 5. Alert on breach | Employee |
| Probation Alerts | 30/60/90 day conversion alerts | 1. Probation start → 2. Auto-alert manager at 30/60/90 days → 3. Conversion requires check-in → 4. Alert HR on failure | Employee |
| Leave Auto-Escalation | Unactioned leave escalation | 1. Leave request unactioned > config hours → 2. Auto-escalate to next authority_level → 3. Notify → 4. No silent stalls | Employee |
| GCC Labor Law Compliance | Validate work hours, Hajj leave, weekly rest | 1. Validate work hours → 2. Hajj leave check → 3. Weekly rest validation → 4. Compliance report | Employee |
| COI Check / Report | Conflict-of-interest detection | 1. Run COI → 2. Flag conflicts → 3. Report | Employee (HR) |
| Training / LMS | Manage training modules | 1. Create module → 2. Assign → 3. Complete → 4. Track | Employee |
| Succession Planning | Manage succession plans | 1. Create plan → 2. Identify successors → 3. Track readiness | Employee |
| Travel Management | Manage travel requests | 1. Create request → 2. Approve → 3. Track → 4. Reimburse | Employee |
| Employee Assets | Assign/reclaim assets | 1. Assign asset → 2. Track → 3. Reclaim on offboarding | Employee (HR) |
| Employee Documents | Upload/approve/expiry alerts | 1. Upload → 2. Approve → 3. Expiry alerts | Employee (HR) |
| Dependents / Relations / Matrix | Manage family + matrix relations | 1. Open profile → 2. Add dependents/relations/matrix | Employee (HR) |
| ESS (Employee Self Service) | Self-service portal | 1. Open ESS → 2. Profile, leave, attendance, payslips, OKRs, org chart | Employee |
| Compliance Work Hours / Report / Overtime | Compliance + overtime reports | 1. Open compliance → 2. Reports → 3. Overtime validation | Employee (HR) |

---

## 6. Admin

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Admin Login | Authenticate | 1. Email/password → 2. TOTP → 3. RLS + country context → 4. Redirect | Admin |
| Command Center | Single-window ops console | 1. Open → 2. View 6 zones (Heartbeat, Treasury, Growth, Workforce, Intel, Engine Room) → 3. Action drawer → 4. Ctrl+K palette | Admin |
| Dashboard | Landing hub | 1. Open → 2. Overview + exports tabs → 3. Country selector | Admin |
| User & Staff Management | Manage accounts | 1. List users → 2. Create staff → 3. Update → 4. Archive/restore → 5. Bulk actions | Admin |
| RBAC & Permission Matrix | Manage roles | 1. Open permissions → 2. Categories → 3. Roles → 4. Override → 5. Maker-checker on sensitive | Admin |
| Audit Logs | Search and export | 1. Open logs → 2. Filter → 3. Expand → 4. Export CSV/JSON | Admin |
| eDiscovery | Legal discovery | 1. Open eDiscovery → 2. Search by entity → 3. Export with legal-hold respect | Admin |
| Product Moderation | Approve/reject products | 1. Queue → 2. Review → 3. Approve/reject → 4. Badge toggle → 5. Bulk actions | Admin |
| Category Management | Taxonomy CRUD | 1. Open categories → 2. CRUD → 3. Reorder → 4. Bulk archive/restore | Admin |
| Order Management | Oversee all orders | 1. List → 2. Filter (date range, status) → 3. View detail → 4. Change status → 5. Refund/cancel → 6. Audit | Admin |
| Returns Queue (RMA) | Approve/reject returns | 1. Open returns → 2. Review → 3. Approve/reject → 4. Resolution note → 5. Refund triggered | Admin |
| Disputes | Resolve supplier disputes | 1. Open disputes → 2. Review → 3. Resolve → 4. Bulk actions | Admin |
| Supplier Management | Approve/verify suppliers | 1. List → 2. Review KYC → 3. Approve/reject → 4. Badge assignment | Admin |
| Logistics Partner Management | Approve/manage partners | 1. List → 2. Approve/reject → 3. Toggle active → 4. Archive/restore | Admin |
| Logistics Charges Approval | Approve partner charges | 1. See pending charges → 2. Review → 3. Approve/reject → 4. Reflects (or not) in checkout | Admin |
| Country Management | Full CRUD on countries | 1. List → 2. Create → 3. Configure (identity, currency, tax, logistics, payments, legal, KYC) → 4. Draft → 5. Approve → 6. Publish | Admin |
| Config Versions | Version country configs | 1. Draft → 2. Approve → 3. Publish → 4. Rollback | Admin |
| Country Cities | Manage city list | 1. Open country → 2. CRUD cities → 3. Upload lat/lng/population | Admin |
| Country Staff Assignment | Assign staff to countries | 1. Assign → 2. Set role_in_country → 3. RLS + permissions synced | Admin |
| Country Tax Rates | Configure tax | 1. Standard/reduced/exempt → 2. Category overrides → 3. Inclusive/exclusive → 4. Applied at checkout | Admin |
| Country Commission Rates | Configure commission | 1. Category defaults → 2. Badge tiers → 3. Supplier overrides | Admin |
| Feature Flags | Per-country rollout | 1. Define flag → 2. Enable per country/audience → 3. Runtime reads | Admin |
| Bank Accounts Verification | Approve supplier/logistics bank | 1. See pending → 2. Review → 3. Verify/reject | Admin |
| Payout Processing | Batch payouts | 1. View pending → 2. Filter → 3. Generate batch → 4. Maker-checker → 5. Dispatch → 6. Reconcile | Admin |
| Finance Hub | Complete ERP-level finance | 1. Chart of Accounts → 2. Journals → 3. Trial Balance → 4. AR/AP → 5. Periods → 6. Reports | Admin |
| Chart of Accounts | Manage CoA | 1. View tree → 2. Add/edit accounts → 3. Normal side → 4. Active | Admin |
| Journal Entries | Manual + auto journals | 1. Create → 2. Debit/credit lines → 3. Balance check → 4. Post → 5. Immutable | Admin |
| Trial Balance | Real-time GL view | 1. Open → 2. Filter by period → 3. Export | Admin |
| Fiscal Periods | Manage period locks | 1. List → 2. Open/close → 3. Lock prevents back-dated postings | Admin |
| AR / Invoices | Accounts receivable | 1. List invoices → 2. Record payment → 3. Aging report | Admin |
| AP / Bills | Accounts payable | 1. List bills → 2. OCR capture → 3. Approve → 4. Pay | Admin |
| Expense OCR Capture | Scan bills → auto-post AP | 1. Upload → 2. OCR parse → 3. Triple-verify → 4. Auto-post or exception queue | Admin |
| Bank Reconciliation | Match bank lines to GL | 1. Import CSV/API → 2. Auto-match → 3. Split-screen review → 4. Bulk reconcile | Admin |
| VAT / Tax | Remittance tracking | 1. Aggregate output/input → 2. Monthly remittance → 3. Export for authority | Admin |
| Fixed Assets | Asset register + depreciation | 1. Register asset → 2. Monthly depreciation run → 3. Disposal gain/loss | Admin |
| Budgets | Budget vs actual | 1. Create budget → 2. Track actuals → 3. Variance report | Admin |
| Reports | P&L, Balance Sheet, Cash Flow | 1. Select report → 2. Period → 3. Render → 4. Export CSV/PDF | Admin |
| Payment Gateways | Manage provider connections | 1. Add gateway → 2. Enter credentials (AES-256 encrypted) → 3. Test connection → 4. Enable | Admin |
| Gateway Smart Routing | Fallback on health degradation | 1. Health monitor → 2. Success rate <85% → 3. Auto-reroute to Tier 2 → 4. Alert | Admin |
| Commission Engine | Global/category/badge/override | 1. Global rate → 2. Category rates → 3. Badge tiers → 4. Supplier overrides → 5. Preview calculator | Admin |
| Promotions Builder | Coupons, flash sales, banners, tiers | 1. Create campaign → 2. Type (tier/coupon/referral/supplier co-fund) → 3. Stacking rule → 4. Preview → 5. Launch | Admin |
| Banner Management | Canvas editor + country targeting | 1. Create banner → 2. Canvas editor (shapes, text, images, video) → 3. Background effect → 4. Country scope → 5. Publish | Admin |
| Coupon Management | Create/manage coupons | 1. Create → 2. Code + type + value + min order + window → 3. Archive/restore | Admin |
| Flash Sales | Time-boxed campaigns | 1. Create → 2. Products + discount + window → 3. Auto-end on expiry/stock | Admin |
| Commission Rates | Global + per-category | 1. Edit rate → 2. Save → 3. Audit | Admin |
| Badge Tiers | Configure badges | 1. Edit tier → 2. Commission rate + fees → 3. Qualification thresholds | Admin |
| Treasury | Cash position, liabilities, forecasts | 1. Open treasury → 2. Cash buckets → 3. Liabilities → 4. Pending payouts → 5. Forecasts | Admin |
| Cash Management | Transaction ledger + reconciliation | 1. View ledger → 2. Import bank → 3. Auto-reconcile → 4. Flag/resolve exceptions | Admin |
| Supplier Payouts | Process supplier payouts | 1. Filter pending → 2. Generate batch → 3. Approve (≠ maker) → 4. Dispatch → 5. Reconcile | Admin |
| Logistics Payouts | Process logistics payouts | 1. Filter → 2. Generate batch → 3. Approve → 4. Dispatch | Admin |
| COD Reconciliation | Reconcile COD remittances | 1. View receipts → 2. Verify → 3. Match to orders → 4. Flag variance | Admin |
| Refund Management | Refund processing | 1. View refunds → 2. Approve → 3. Route via gateway → 4. Ledger post | Admin |
| Fraud Detection | Score, blacklist, review queue | 1. View events → 2. Score → 3. Blacklist add/remove → 4. Review queue | Admin |
| Threat Feeds | Update external feeds | 1. View status → 2. Update feed → 3. Applied | Admin |
| Risk Scores | Employee/team risk | 1. View risk score → 2. Update → 3. Audit | Admin |
| Ghost Employees | Detect anomalies | 1. Run detector → 2. Review flagged → 3. Action | Admin |
| Impossible Travel | Detect logins from distant places | 1. Detector fires → 2. Alert → 3. Review | Admin |
| Team Health Radar | Team performance | 1. Open → 2. Radar chart → 3. Drill down | Admin |
| Command Center Alerts | Critical alerts + resolve | 1. Alert raised → 2. Tier escalation → 3. Resolve → 4. Audit | Admin |
| News / Headlines | Curate + publish | 1. Fetch → 2. AI tag → 3. Review → 4. Publish | Admin |
| Communication Hub | Email campaigns + chat + video | 1. Admin email panel → 2. Admin chat panel → 3. Admin video panel | Admin |
| Email Campaigns | Send campaigns | 1. Create → 2. Subject + body + audience → 3. Send → 4. Analytics | Admin |
| Support Tickets (Admin) | Reply and resolve | 1. Queue → 2. Open thread → 3. Reply → 4. Status update | Admin |
| HR Operations | Employee oversight | 1. Directory → 2. Org chart → 3. Attendance → 4. Payroll → 5. Compliance | Admin |
| Payroll Processing | Monthly payroll | 1. Aggregate inputs → 2. Anomaly gate → 3. Maker-checker → 4. Treasury journal → 5. Bank dispatch → 6. Payslip PDF | Admin |
| Employee Documents Review | HR approves docs | 1. Queue → 2. Review → 3. Approve/reject | Admin |
| COI Reports | Conflict of interest | 1. Check → 2. Report → 3. Review | Admin |
| Disciplinary Cases | Handle incidents | 1. Create case → 2. Evidence → 3. Approval chain → 4. Record | Admin |
| Offboarding | Employee exit | 1. Create case → 2. Revoke access → 3. Reclaim assets → 4. EOSB settlement | Admin |
| Employee Analytics | HR metrics | 1. Open → 2. Headcount, attrition, DEI, leave burn → 3. Export | Admin |
| Data Export (CSV) | Bulk export | 1. Select entity → 2. Date range → 3. Download CSV | Admin |
| Backup & Recovery | Trigger + restore | 1. Trigger backup → 2. Verify → 3. List backups → 4. Restore drill | Admin |
| Cross-Country Analytics | Compare country performance | 1. Open → 2. Compare metrics → 3. Drill down | Admin |
| Automation Control Tower | Manage automations | 1. List automations → 2. Toggle ON/OFF → 3. View last-run + counters → 4. View DLQ | Admin |
| External Intelligence | Market radar + regulatory shield | 1. View ticker → 2. Regulatory countdowns → 3. Simulate | Admin |
| Payment Gateway Wizard | Onboard new gateway | 1. Select country → 2. Heuristic suggests → 3. Enter credentials → 4. Test → 5. Enable | Admin |
| Dispute Resolution Center | Resolve disputes | 1. List → 2. Review → 3. Resolve → 4. Bulk | Admin |
| Product Verification Queue | Verify products | 1. Queue → 2. Review → 3. Verify/reject | Admin |
| Barcode Scan (Admin) | Scan for ops | 1. Scan → 2. Lookup → 3. Update inventory | Admin |
| BOGO Promotions | Buy X get Y free campaigns | 1. Create → 2. Products + rules → 3. Auto-end on expiry/stock | Admin |
| Order Tier Discounts | Threshold-based order discounts | 1. Create → 2. Value bands → 3. Auto-applied at checkout | Admin |
| Supplier Co-fund | Supplier-funded discount campaigns | 1. Create → 2. Set supplier share → 3. Ledger records contribution | Admin |
| Promotion Ledger | Immutable promotion application record | 1. Promotion applied → 2. Ledger row written → 3. Audit trail | Admin |
| Moderation Queue | Moderate content | 1. Queue → 2. Review → 3. Approve/reject | Admin |
| Purchase Order CRUD | Manage purchase orders | 1. Create PO → 2. Confirm → 3. Receive → 4. 3-way match | Admin |
| Sales Order CRUD | Manage sales orders | 1. Create SO → 2. Confirm → 3. Dispatch → 4. Invoice | Admin |
| Dunning Run | Automated overdue AR collection | 1. Trigger dunning → 2. Emails day 3/7/14 → 3. Late fee applied | Admin |
| Chart of Accounts Tree | Manage CoA hierarchy | 1. View tree → 2. Add/edit accounts → 3. Normal side → 4. Active | Admin |
| Journal Entries | Manual + auto journals | 1. Create → 2. Debit/credit lines → 3. Balance check → 4. Post → 5. Immutable | Admin |
| Trial Balance | Real-time GL view | 1. Open → 2. Filter by period → 3. Export | Admin |
| Fiscal Period Locking | Manage period locks | 1. List → 2. Open/close → 3. Lock prevents back-dated postings | Admin |
| AR / AP Aging | Receivable/payable aging | 1. List invoices/bills → 2. Aging report → 3. Outstanding balances → 4. Export | Admin |
| Expense OCR Capture | Scan bills → auto-post AP | 1. Upload → 2. OCR parse → 3. Triple-verify → 4. Auto-post or exception queue | Admin |
| Bank Reconciliation | Match bank lines to GL | 1. Import CSV/API → 2. Auto-match → 3. Split-screen review → 4. Bulk reconcile | Admin |
| VAT / Tax Remittance | Tax aggregation + remittance | 1. Aggregate output/input → 2. Monthly remittance → 3. Export for authority | Admin |
| Fixed Assets Depreciation | Asset register + depreciation | 1. Register asset → 2. Monthly depreciation run → 3. Disposal gain/loss | Admin |
| Budget vs Actual | Budget variance tracking | 1. Create budget → 2. Track actuals → 3. Variance report | Admin |
| Financial Reports | P&L, Balance Sheet, Cash Flow | 1. Select report → 2. Period → 3. Render → 4. Export CSV/PDF | Admin |
| Payment Gateway Wizard | Onboard new payment gateway | 1. Select country → 2. Heuristic suggests → 3. Enter credentials → 4. Test → 5. Enable | Admin |
| Smart Routing / Fallback | Auto-reroute on gateway degradation | 1. Health monitor → 2. Success rate <85% → 3. Auto-reroute to Tier 2 → 4. Alert | Admin |
| Universal Payment Connector | Unified multi-gateway system | 1. Adapter implements 5 methods → 2. Registry auto-discovers → 3. PaymentEngine routes → 4. Normalized webhook | Admin |
| ZoziPaymentEvent Normalizer | Universal webhook schema | 1. Raw webhook → 2. Adapter translates → 3. Normalize to ZoziPaymentEvent → 4. Idempotency gate → 5. Treasury dispatch | Admin |
| AES-256 Credential Vault | Encrypted gateway secrets | 1. Admin enters credentials → 2. AES-256-GCM encrypt → 3. Store ciphertext → 4. Transparent decrypt on use → 5. Key rotation supported | Admin |
| Generic REST Adapter | No-code gateway setup | 1. Admin inputs Charge URL + Auth + JSON template → 2. DB-stored template → 3. HTTP request made → 4. No Python code needed | Admin |

---

## 7. System & Automation

| Feature | Description | Workflow | Actor |
|---|---|---|---|
| Payout Sweep (Cron 02:00) | Nightly payout processing | 1. Aggregate eligible payouts → 2. Generate batches → 3. Approve (maker-checker) → 4. Dispatch | System |
| Reconciliation Cron (hourly) | Auto-reconcile bank transactions | 1. Import → 2. Match → 3. Auto-reconcile or flag | System |
| Bank Statement Importer (daily) | Import bank statements | 1. Fetch/upload → 2. Parse → 3. Store lines → 4. Notify | System |
| FX Revaluation (month-end) | Revalue foreign-currency balances | 1. Fetch rate → 2. Compute reval → 3. Auto-post | System |
| Accrual Reversal (month-start) | Reverse prior accruals | 1. Find accruals → 2. Generate reversal journal → 3. Post | System |
| Payroll Run (monthly) | Automated payroll cycle | 1. Aggregate inputs → 2. Generate batch → 3. Maker-checker → 4. Journal → 5. Bank | System |
| Fraud Monitoring (every 5 min) | Continuous fraud detection | 1. Scan events → 2. Score → 3. Alert high-risk | System |
| Ghost Order Detector (daily) | Find orders without payment events | 1. Compare paid orders vs payment events → 2. Alert mismatch | System |
| Data Retention (weekly) | Archive and purge old data | 1. Identify expired → 2. Archive to cold → 3. Purge | System |
| Threat Feed Updater (hourly) | Refresh security intelligence | 1. Fetch feeds → 2. Dedupe → 3. Apply | System |
| News Ingester (15 min) | Fetch market news | 1. Fetch RSS/API → 2. Sanitize → 3. AI enrich → 4. Route | System |
| Auto Document Expiry (daily) | Notify before KYC/docs expire | 1. Scan → 2. Notify 30/14/7 days → 3. Block dependent actions | System |
| Facet Count Refresh (15 min) | Refresh search facets | 1. Rebuild mat-view → 2. Invalidate cache | System |
| AI Embeddings Sync (nightly) | Keep product embeddings fresh | 1. Find changed products → 2. Embed → 3. Update index | System |
| Escalation Engine (every 5 min) | Auto-escalate unactioned items | 1. Find past SLA → 2. Escalate tier → 3. Notify | System |
| KPI Watchdog (hourly) | Auto-ticket on KPI regression | 1. Compare vs targets → 2. Fire alerts → 3. Create ticket | System |
| Event Subscriber — user.created | Send verification email | 1. Event → 2. Queue email → 3. Deliver | System |
| Event Subscriber — order.paid | Finalize order | 1. Event → 2. Update order → 3. Send confirmation | System |
| Event Subscriber — payment.captured | Update payment status | 1. Event → 2. Update order → 3. Notify | System |
| Event Subscriber — payout.dispatched | Notify supplier/logistics | 1. Event → 2. Notify | System |
| Event Subscriber — shipment.delivered | Recompute credibility | 1. Event → 2. Recompute score → 3. Update badge | System |
| Event Subscriber — employee.offboarded | EOSB settlement | 1. Event → 2. Treasury journal → 3. Notify | System |
| Event Subscriber — payroll.approved | Post treasury journal | 1. Event → 2. Journal post | System |
| Event Subscriber — order.delivered → commission | Compute commission | 1. Event → 2. Compute → 3. Write ledger | System |
| Event Subscriber — order.delivered → promotion | Award coins | 1. Event → 2. Award points → 3. Credit referral | System |
| Workflow Automation Engine | Visual trigger→condition→action builder | 1. Define trigger → 2. Add conditions → 3. Add actions → 4. Publish → 5. Version | System |
| Rule Engine | Business/country/supplier rules | 1. Define rule → 2. Evaluate at runtime → 3. Apply | System |
| Assignment Engine | Load-balanced assignment | 1. New task → 2. Rank candidates → 3. Assign → 4. Track | System |
| Reminder Engine | Payment/KYC/expiry reminders | 1. Track due → 2. Send reminder → 3. Escalate | System |
| Approval Engine | Multi-level approval workflows | 1. Request → 2. Route to approver → 3. Escalate → 4. Record | System |
| Notification Engine | Email/SMS/push/in-app | 1. Event → 2. Template → 3. Channel → 4. Deliver → 5. Retry | System |
| Schedule Engine | Cron/recurring/delayed jobs | 1. Register job → 2. Fire → 3. Execute → 4. Track | System |
| Finance Automation | Auto journal/commission/payout/recon | 1. Event → 2. Rule → 3. Post → 4. Reconcile | System |
| Inventory Automation | Stock updates + alerts | 1. Order → 2. Reserve → 3. Deliver → 4. Deduct → 5. Low-stock alert | System |
| Order Automation | Validation + routing + split | 1. Validate → 2. Split by supplier → 3. Route → 4. Status | System |
| Logistics Automation | Assignment + route + POD | 1. Assign → 2. Route → 3. Track → 4. POD verify | System |
| AI Automation | Description, categorization, moderation | 1. Input → 2. Provider → 3. Staging → 4. Commit/review | System |
| Data Automation | Import/export/cleanup | 1. Define job → 2. Run → 3. Report | System |
| Security Automation | Login monitoring, ATO, session cleanup | 1. Monitor → 2. Detect → 3. Lock/cleanup | System |
| Customer Automation | Welcome, cart abandonment, loyalty | 1. Trigger → 2. Action → 3. Track | System |
| Supplier Automation | KYC workflow, product approval | 1. Trigger → 2. Action → 3. Notify | System |
| Admin Automation | Alerts, health, digests | 1. Aggregate → 2. Send digest → 3. Alert on anomalies | System |
| Monitoring & Recovery | Automation logs + DLQ | 1. Log → 2. Alert on fail → 3. Retry → 4. DLQ | System |
| Outbox Relay | Transactional event publishing | 1. Read outbox → 2. Publish to broker → 3. Mark processed → 4. DLQ on failure | System |
| Auto Attendance Anomaly | Detect attendance anomalies | 1. Scan → 2. Compute distance/device trust → 3. Flag anomaly → 4. Notify manager | System |
| Auto-Onboarding | Automate new hire setup | 1. Offer accepted → 2. Create user+employee → 3. Assign org/role/country → 4. Trigger docs/assets/ID/welcome mail | System |
| Auto-Rostering & Handover | Auto-schedule shifts and enforce handover | 1. Weekly cron + leave/skills → 2. Publish roster → 3. Block clock-out till handover acknowledged → 4. Notify on coverage conflicts | System |
| Auto-Leave Processing | Auto-approve/route leave requests | 1. Request submitted → 2. Check ledger + calendar + conflicts → 3. Auto-approve if ≤ threshold → 4. Else route up chain → 5. Year-end carry-forward | System |
| Auto-Payroll & Disbursement | Monthly payroll automation | 1. Aggregate inputs → 2. Anomaly gate → 3. Maker-checker → 4. Treasury journal → 5. Bank dispatch → 6. Payslip PDF → 7. Notify | System |
| Auto-Performance Signals | Nightly health score + PIP trigger | 1. Nightly cron → 2. Pull KPIs → 3. Compute R/A/G health score → 4. Trigger PIP if red → 5. Bonus multiplier → payroll | System |
| Auto-COI Detection | Detect conflicts of interest | 1. Hierarchy/relations change → 2. Graph analysis → 3. Flag conflicting lines → 4. Compliance case | System |
| Auto Comms Compliance | DLP + retention + legal-hold | 1. Message/email write → 2. DLP scan → 3. Internal-first routing → 4. Auto legal-hold on case → 5. Retention purge | System |
| Auto Meeting Intelligence | Transcript + action items | 1. Recording ends → 2. Whisper transcript → 3. Extract action items → 4. Assign tasks with due dates → 5. RAG-index | System |
| HR Chatbot + Voice Assistant | HR assistant via NL/voice | 1. NL/voice query → 2. RAG over handbook/policy → 3. Draft request (leave/expense/1:1) → 4. Confirm card → 5. Execute | System |
| Auto-Offboarding & Settlement | Employee exit automation | 1. Termination event → 2. Revoke all → 3. Transfer tasks → 4. Archive per policy → 5. EOSB event → Treasury | System |
| Auto Access Governance | Permission recertification | 1. Quarterly cron → 2. Route requests up chain → 3. Auto-revoke unconfirmed grants → 4. Manager review queue | System |
| Auto HR Analytics & Attrition Risk | Nightly HR analytics | 1. Nightly cron → 2. Refresh mat-views → 3. Compute attrition risk → 4. Alert managers → 5. R/A/G dashboards | System |
| Import & Purchase Automation | PO/GRN/Invoice 3-way match | 1. PO/GRN/vendor-invoice events → 2. 3-way match within tolerance → 3. Landed-cost allocation → 4. Draft AP bill | System |
| Orphan Detector | Find orders/payouts without journal | 1. Daily 03:00 scan → 2. Compare paid orders vs journal entries → 3. Alert mismatch → 4. Critical alert to Command Center | System |

---

## Summary Count

| Section | Approx Features |
|---|---|
| Infrastructure & Cross-Cutting | 38 |
| Customer | 42+ |
| Supplier | 34 |
| Logistics Partner | 30 |
| Employee | 50+ |
| Admin | 87+ |
| System & Automation | 61+ |
| **Total** | **~330+** |

---

**Next step:** once you approve this master index, I'll convert any subset (start with the P0 top-10) into the full YAML feature contract format we agreed on, one feature per block, so we can start the actual content work. Which actor do you want to begin with?
