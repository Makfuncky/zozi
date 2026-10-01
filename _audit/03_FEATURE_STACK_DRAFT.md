# FEATURE STACK DRAFT

Generated: 2026-09-30T04:40:00Z
Source: FEATURE_STACK_LIST.md

## Canonical feature inventory

### Infrastructure & Cross-Cutting (38)
F-INF-001: Authentication & Identity
F-INF-002: Email Verification
F-INF-003: Password Reset
F-INF-004: TOTP / MFA
F-INF-005: Session & Device Binding
F-INF-006: RBAC / Permissions
F-INF-007: Audit Logging
F-INF-008: Event Bus / Outbox
F-INF-009: Background Jobs
F-INF-010: Scheduler & Cron
F-INF-011: Email Service
F-INF-012: Realtime / WebSockets
F-INF-013: Webhook Ingress
F-INF-014: Notification Engine
F-INF-015: Observability & Monitoring
F-INF-016: Search Engine (hybrid)
F-INF-017: AI Provider Services
F-INF-018: Currency & FX
F-INF-019: Geolocation & Maps
F-INF-020: QR & Barcode Services
F-INF-021: Valkey / Redis Cache
F-INF-022: Database & Migrations
F-INF-023: Data Backup & Retention
F-INF-024: Storage & Media (R2/S3)
F-INF-025: Middleware Pipeline
F-INF-026: Security Infrastructure
F-INF-027: News & RSS Ingestion
F-INF-028: AI Automation
F-INF-029: Data Automation
F-INF-030: Security Automation
F-INF-031: Customer Automation
F-INF-032: Supplier Automation
F-INF-033: Admin Automation
F-INF-034: Workflow Automation Engine
F-INF-035: Rule Engine
F-INF-036: Assignment Engine
F-INF-037: Reminder Engine
F-INF-038: Approval Engine
F-INF-039: Schedule Engine
F-INF-040: Finance Automation
F-INF-041: Inventory Automation
F-INF-042: Order Automation
F-INF-043: Logistics Automation

### Customer (42+)
F-CUST-001: Customer Registration
F-CUST-002: Customer Login
F-CUST-003: Customer Profile & Settings
F-CUST-004: Address Book
F-CUST-005: Cart
F-CUST-006: Checkout (4-step)
F-CUST-007: Payment — Card (Stripe/Tap/PayTabs)
F-CUST-008: Payment — Cash on Delivery
F-CUST-009: Coupon Validation
F-CUST-010: Order History
F-CUST-011: Order Detail & Tracking
F-CUST-012: Order Cancellation
F-CUST-013: Return Request
F-CUST-014: Return Tracking
F-CUST-015: Invoice Viewing
F-CUST-016: Wishlist
F-CUST-017: Reviews & Ratings
F-CUST-018: Product Catalog Browse
F-CUST-019: Product Detail
F-CUST-020: Product Search
F-CUST-021: Image Search
F-CUST-022: Voice Search
F-CUST-023: Recommendations
F-CUST-024: Notifications (In-App)
F-CUST-025: Push Notifications
F-CUST-026: Support Tickets
F-CUST-027: Chatbot
F-CUST-028: Newsletter
F-CUST-029: Referrals
F-CUST-030: Zozi Coins / Rewards
F-CUST-031: Barcode Scan (Receipt Verify)
F-CUST-032: Delivery Confirmation
F-CUST-033: Avatar Upload
F-CUST-034: Data Export (GDPR)
F-CUST-035: Account Deletion Request
F-CUST-036: Loyalty VIP Tiers (MISSING)
F-CUST-037: Saved Payment Methods (MISSING)
F-CUST-038: Apple Pay / Google Pay (MISSING)
F-CUST-039: Product Comparison (MISSING)
F-CUST-040: Social Sharing (MISSING)
F-CUST-041: Video Commerce (PDP) (MISSING)

### Supplier (34)
F-SUP-001: Supplier Registration
F-SUP-002: Supplier Login
F-SUP-003: KYC Onboarding
F-SUP-004: Profile Management
F-SUP-005: Bank Account Setup
F-SUP-006: Product Upload — Method 1 (Manual)
F-SUP-007: Product Upload — Method 2 (Photo-first AI)
F-SUP-008: Product Upload — Method 3 (Voice-first)
F-SUP-009: Bulk CSV Import
F-SUP-010: Bulk CSV Export
F-SUP-011: Image Tools (12 tools)
F-SUP-012: BG Removal Comparison
F-SUP-013: Product Edit
F-SUP-014: Product Delete (soft)
F-SUP-015: Discount Setup
F-SUP-016: Inventory Management
F-SUP-017: Order Management
F-SUP-018: Parcel Proof Upload
F-SUP-019: Parcel Sheet Print
F-SUP-020: Shipping Label Mobile
F-SUP-021: Logistics Zones & Carriers
F-SUP-022: Order Tracking View
F-SUP-023: Analytics & Reports
F-SUP-024: Payout Dashboard
F-SUP-025: Invoice Records
F-SUP-026: Commission Agreement
F-SUP-027: Credibility Badge
F-SUP-028: Storefront / About Page
F-SUP-029: Returns Queue
F-SUP-030: Dispute Center
F-SUP-031: Notification Preferences
F-SUP-032: Supplier Support
F-SUP-033: AI Product Descriptions
F-SUP-034: Multi-User Sub-Accounts (MISSING)
F-SUP-035: Quality Control
F-SUP-036: Legal Contracts
F-SUP-037: Settlement
F-SUP-038: Governance / Admin Operations
F-SUP-039: Compliance
F-SUP-040: Badge Tiers Write
F-SUP-041: Analytics Export
F-SUP-042: Onboarding Pipeline

### Logistics Partner (30)
F-LOG-001: Partner Registration
F-LOG-002: Partner Login
F-LOG-003: Profile & Documents
F-LOG-004: Terms Acceptance
F-LOG-005: Service Areas
F-LOG-006: Delivery Settings (Charges)
F-LOG-007: Pricing Profiles
F-LOG-008: Vehicle Rules
F-LOG-009: Category Rules
F-LOG-010: Dashboard & KPIs
F-LOG-011: Shipment Queue
F-LOG-012: Pickup Claim & Cancel
F-LOG-013: QR Scan Handover
F-LOG-014: Transit Updates
F-LOG-015: Delivery Confirmation
F-LOG-016: Exception Handling
F-LOG-017: Package Metadata
F-LOG-018: GPS Ingestion
F-LOG-019: Delivery Tracking View
F-LOG-020: Barcode Scan
F-LOG-021: Product Verification (receipt)
F-LOG-022: Carrier Management
F-LOG-023: Auto-Invoice on Shipment
F-LOG-024: COD Remittance
F-LOG-025: Bank Account
F-LOG-026: Payout Dashboard
F-LOG-027: Revenue & Payout Center
F-LOG-028: Route Optimization
F-LOG-029: SLA Breach Alerts
F-LOG-030: Analytics
F-LOG-031: Fleet Management (MISSING)
F-LOG-032: Geo / Fence Management
F-LOG-033: Health Score
F-LOG-034: SLA Management
F-LOG-035: COD Reconciliation
F-LOG-036: Country Management

### Employee (50+)
F-EMP-001: Employee Login
F-EMP-002: Self-Service Portal
F-EMP-003: Profile Management
F-EMP-004: Leave Balance & History
F-EMP-005: Leave Request
F-EMP-006: Leave Approval (Manager)
F-EMP-007: Attendance View
F-EMP-008: Check-In / Check-Out
F-EMP-009: QR Kiosk Check-In
F-EMP-010: Payslip Access
F-EMP-011: OKR / KPI View
F-EMP-012: Org Chart View
F-EMP-013: Team Subordinates
F-EMP-014: Shift View
F-EMP-015: Shift Handover
F-EMP-016: Work Logs
F-EMP-017: Performance Review
F-EMP-018: Training Modules
F-EMP-019: Expense Submission
F-EMP-020: Document Upload
F-EMP-021: Internal Chat
F-EMP-022: Internal Email
F-EMP-023: Video Conferencing
F-EMP-024: Contacts Directory
F-EMP-025: Employee Activity Ledger
F-EMP-026: Mobile Employee App (MISSING)
F-EMP-027: Unified Inbox / Confluence
F-EMP-028: PIP Workflow
F-EMP-029: Team Health Radar
F-EMP-030: Purchase Order CRUD
F-EMP-031: Sales Order CRUD
F-EMP-032: Goods Receipt / 3-Way Match
F-EMP-033: Dunning Run
F-EMP-034: Access Recertification
F-EMP-035: Bank-Detail Change Freeze
F-EMP-036: Boomerang Re-hire
F-EMP-037: Continuous Check-ins
F-EMP-038: 360° Performance Review
F-EMP-039: OKR Cascade Framework
F-EMP-040: KPI Metrics Auto-Pull
F-EMP-041: Performance Health Score
F-EMP-042: PIP & Recognition
F-EMP-043: Performance Calibration
F-EMP-044: HR Analytics Dashboards
F-EMP-045: Onboarding SLA Pipeline
F-EMP-046: Probation Alerts
F-EMP-047: Leave Auto-Escalation
F-EMP-048: GCC Labor Law Compliance
F-EMP-049: COI Check / Report
F-EMP-050: Training / LMS
F-EMP-051: Succession Planning
F-EMP-052: Travel Management
F-EMP-053: Employee Assets
F-EMP-054: Employee Documents
F-EMP-055: Dependents / Relations / Matrix
F-EMP-056: ESS (Employee Self Service)
F-EMP-057: Compliance Work Hours / Report / Overtime

### Admin (87+)
F-ADM-001: Admin Login
F-ADM-002: Command Center
F-ADM-003: Dashboard
F-ADM-004: User & Staff Management
F-ADM-005: RBAC & Permission Matrix
F-ADM-006: Audit Logs
F-ADM-007: eDiscovery
F-ADM-008: Product Moderation
F-ADM-009: Category Management
F-ADM-010: Order Management
F-ADM-011: Returns Queue (RMA)
F-ADM-012: Disputes
F-ADM-013: Supplier Management
F-ADM-014: Logistics Partner Management
F-ADM-015: Logistics Charges Approval
F-ADM-016: Country Management
F-ADM-017: Config Versions
F-ADM-018: Country Cities
F-ADM-019: Country Staff Assignment
F-ADM-020: Country Tax Rates
F-ADM-021: Country Commission Rates
F-ADM-022: Feature Flags
F-ADM-023: Bank Accounts Verification
F-ADM-024: Payout Processing
F-ADM-025: Finance Hub
F-ADM-026: Chart of Accounts
F-ADM-027: Journal Entries
F-ADM-028: Trial Balance
F-ADM-029: Fiscal Periods
F-ADM-030: AR / Invoices
F-ADM-031: AP / Bills
F-ADM-032: Expense OCR Capture
F-ADM-033: Bank Reconciliation
F-ADM-034: VAT / Tax
F-ADM-035: Fixed Assets
F-ADM-036: Budgets
F-ADM-037: Reports
F-ADM-038: Payment Gateways
F-ADM-039: Gateway Smart Routing
F-ADM-040: Commission Engine
F-ADM-041: Promotions Builder
F-ADM-042: Banner Management
F-ADM-043: Coupon Management
F-ADM-044: Flash Sales
F-ADM-045: Commission Rates
F-ADM-046: Badge Tiers
F-ADM-047: Treasury
F-ADM-048: Cash Management
F-ADM-049: Supplier Payouts
F-ADM-050: Logistics Payouts
F-ADM-051: COD Reconciliation
F-ADM-052: Refund Management
F-ADM-053: Fraud Detection
F-ADM-054: Threat Feeds
F-ADM-055: Risk Scores
F-ADM-056: Ghost Employees
F-ADM-057: Impossible Travel
F-ADM-058: Team Health Radar
F-ADM-059: Command Center Alerts
F-ADM-060: News / Headlines
F-ADM-061: Communication Hub
F-ADM-062: Email Campaigns
F-ADM-063: Support Tickets (Admin)
F-ADM-064: HR Operations
F-ADM-065: Payroll Processing
F-ADM-066: Employee Documents Review
F-ADM-067: COI Reports
F-ADM-068: Disciplinary Cases
F-ADM-069: Offboarding
F-ADM-070: Employee Analytics
F-ADM-071: Data Export (CSV)
F-ADM-072: Backup & Recovery
F-ADM-073: Cross-Country Analytics
F-ADM-074: Automation Control Tower
F-ADM-075: External Intelligence
F-ADM-076: Payment Gateway Wizard
F-ADM-077: Dispute Resolution Center
F-ADM-078: Product Verification Queue
F-ADM-079: Barcode Scan (Admin)
F-ADM-080: BOGO Promotions
F-ADM-081: Order Tier Discounts
F-ADM-082: Supplier Co-fund
F-ADM-083: Promotion Ledger
F-ADM-084: Moderation Queue
F-ADM-085: Purchase Order CRUD
F-ADM-086: Sales Order CRUD
F-ADM-087: Dunning Run
F-ADM-088: Chart of Accounts Tree
F-ADM-089: Journal Entries
F-ADM-090: Trial Balance
F-ADM-091: Fiscal Period Locking
F-ADM-092: AR / AP Aging
F-ADM-093: Expense OCR Capture
F-ADM-094: Bank Reconciliation
F-ADM-095: VAT / Tax Remittance
F-ADM-096: Fixed Assets Depreciation
F-ADM-097: Budget vs Actual
F-ADM-098: Financial Reports
F-ADM-099: Payment Gateway Wizard
F-ADM-100: Smart Routing / Fallback
F-ADM-101: Universal Payment Connector
F-ADM-102: ZoziPaymentEvent Normalizer
F-ADM-103: AES-256 Credential Vault
F-ADM-104: Generic REST Adapter

### System & Automation (61+)
F-SYS-001: Payout Sweep (Cron 02:00)
F-SYS-002: Reconciliation Cron (hourly)
F-SYS-003: Bank Statement Importer (daily)
F-SYS-004: FX Revaluation (month-end)
F-SYS-005: Accrual Reversal (month-start)
F-SYS-006: Payroll Run (monthly)
F-SYS-007: Fraud Monitoring (every 5 min)
F-SYS-008: Ghost Order Detector (daily)
F-SYS-009: Data Retention (weekly)
F-SYS-010: Threat Feed Updater (hourly)
F-SYS-011: News Ingester (15 min)
F-SYS-012: Auto Document Expiry (daily)
F-SYS-013: Facet Count Refresh (15 min)
F-SYS-014: AI Embeddings Sync (nightly)
F-SYS-015: Escalation Engine (every 5 min)
F-SYS-016: KPI Watchdog (hourly)
F-SYS-017: Event Subscriber — user.created
F-SYS-018: Event Subscriber — order.paid
F-SYS-019: Event Subscriber — payment.captured
F-SYS-020: Event Subscriber — payout.dispatched
F-SYS-021: Event Subscriber — shipment.delivered
F-SYS-022: Event Subscriber — employee.offboarded
F-SYS-023: Event Subscriber — payroll.approved
F-SYS-024: Event Subscriber — order.delivered → commission
F-SYS-025: Event Subscriber — order.delivered → promotion
F-SYS-026: Workflow Automation Engine
F-SYS-027: Rule Engine
F-SYS-028: Assignment Engine
F-SYS-029: Reminder Engine
F-SYS-030: Approval Engine
F-SYS-031: Notification Engine
F-SYS-032: Schedule Engine
F-SYS-033: Finance Automation
F-SYS-034: Inventory Automation
F-SYS-035: Order Automation
F-SYS-036: Logistics Automation
F-SYS-037: AI Automation
F-SYS-038: Data Automation
F-SYS-039: Security Automation
F-SYS-040: Customer Automation
F-SYS-041: Supplier Automation
F-SYS-042: Admin Automation
F-SYS-043: Monitoring & Recovery
F-SYS-044: Outbox Relay
F-SYS-045: Auto Attendance Anomaly
F-SYS-046: Auto-Onboarding
F-SYS-047: Auto-Rostering & Handover
F-SYS-048: Auto-Leave Processing
F-SYS-049: Auto-Payroll & Disbursement
F-SYS-050: Auto-Performance Signals
F-SYS-051: Auto-COI Detection
F-SYS-052: Auto Comms Compliance
F-SYS-053: Auto Meeting Intelligence
F-SYS-054: HR Chatbot + Voice Assistant
F-SYS-055: Auto-Offboarding & Settlement
F-SYS-056: Auto Access Governance
F-SYS-057: Auto HR Analytics & Attrition Risk
F-SYS-058: Import & Purchase Automation
F-SYS-059: Orphan Detector
F-SYS-060: Event Subscriber — shipment.delivered → commission
F-SYS-061: Event Subscriber — shipment.delivered → promotion
