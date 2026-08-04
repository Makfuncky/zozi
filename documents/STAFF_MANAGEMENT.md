# 🏢 Zozi Employee Management System (EMS) — Complete Roadmap

> **Grounding Note:** Your codebase *already* contains ~70% of the HR skeleton (`employees`, `employee_roles`, `org_units`, `employee_attendance`, `employee_biometrics`, `dynamic_qr_sessions`, `geo_fence_logs`, `employee_communication_threads`, `internal_channels`, `direct_chat_rooms`, `shift_handover_sessions`, `coi_reports`, `disciplinary_cases`, `offboarding_cases`, plus `calculate_monthly_payroll` / `generate_payroll_batch`). This roadmap does **not** rebuild from zero — it **completes, wires, and governs** what exists, and fills the genuine gaps (unified login, internal email, performance engine, auto-disbursement, full chat attachments).

---

## 🎯 Core Design Philosophy

*   **One Identity, Many Doors:** A single `users` + `employees` identity logs in via password, OTP, biometric, QR-kiosk, or SSO — same person, same permissions, every device.
*   **Hierarchy = Authority = Permission:** The org chart (`org_units` + `reporting_manager_id` + `authority_level`) is not cosmetic; it *drives* who can approve leave, expenses, payroll, and handovers.
*   **Country Isolation by Default:** Every employee record is `country_code`-scoped and protected by Row-Level Security (RLS); a Country Manager in Oman never sees KSA staff.
*   **Internal-First Communication:** Chat + email resolve *inside* the org by `user_id`/`employee_id` first; only explicitly external addresses hit SMTP.
*   **Performance Feeds Payroll:** KPI/OKR scores flow into bonus multipliers in the auto-disbursement engine — no manual spreadsheet math.

---

## 🗺️ The 14-Phase Roadmap

### **Phase 0 — Foundation Audit & Schema Alignment (Week 1)**
*   **Map existing tables to bounded schemas** per your `DATABASE_ECOSYSTEM_HANDLING_PLAN.md`: move all `employee_*`, `offices`, `org_units`, `shift_handover_*` into the `hr` schema; `internal_channels`, `direct_chat_*`, `employee_communication_threads` into `comms`.
*   **Add missing columns/tables** (gaps identified): `employee_bank_accounts` (or unify into `partner_bank_accounts` with `entity_type='employee'`), `okr_objectives`, `kpi_metrics`, `performance_reviews`, `internal_emails`, `email_folders`, `chat_attachments`, `chat_read_receipts`, `employee_activity_logs`.
*   **Freeze the permission catalog** into a single source-of-truth constant (`HR_PERMISSION_MAP`) consumed by both backend guards and frontend UI.

---

### **Phase 1 — Unified Login & Identity Solution (Weeks 2–3)** ⭐ *(Requested in detail)*

A single authentication service (`auth_service.py`) with **5 login doors**, all converging on the same JWT + RLS context.

*   **Door 1 — Email/Password + TOTP MFA:** Standard web login; if `users.totp_enabled`, prompt the 6-digit code from `users.totp_secret`.
*   **Door 2 — Phone + OTP:** Send SMS/WhatsApp OTP; verify against a short-lived token; create/attach session.
*   **Door 3 — Biometric (Mobile App):** Use `employee_biometrics.fingerprint_hash` / `face_encoding`. Device must already be in `user_devices` with `is_trusted=True`; first-time biometric enrollment requires a password+OTP bootstrap.
*   **Door 4 — QR Office Kiosk (Zero-Password Attendance/Login):** Employee scans a `dynamic_qr_sessions.qr_token` at the office kiosk → backend validates token + expiry + geo-fence (`geo_fence_logs.is_within_fence`) → optional secondary biometric match to block "buddy punching" → logs `employee_attendance` *and* issues a kiosk-scoped session.
*   **Door 5 — SSO (Google/Apple/Microsoft):** For corporate staff; map the SSO `sub` claim to `users.email`, auto-provision the `employees` row on first login if HR pre-registered them.

**Session & Device Security (applies to all doors):**
*   Every login writes a `user_devices` row (device fingerprint, IP, OS, `is_trusted`). Unknown device → force MFA or block.
*   **Concurrent-session policy:** configurable per role (e.g., kiosk sessions auto-expire in 8h; mobile sessions 30 days with refresh-token rotation).
*   **On login, set RLS context:** `SET app.current_country_code = '<employee.country_code>'` so every subsequent query is country-isolated automatically.
*   **Risk scoring:** combine `geo_fence` anomaly + new device + odd hour → if risk > threshold, step-up to MFA or lock + notify manager.

**Login Flow (mobile example):**
1. App opens → check stored refresh token → silent refresh → if valid, go Home.
2. If expired → show biometric prompt (if enrolled + trusted device) else password/OTP.
3. On success → backend returns JWT + sets RLS + emits `employee_logged_in` event to `employee_activity_logs`.

---

### **Phase 2 — Organizational Hierarchy & Org Chart (Weeks 3–4)** ⭐
*   **`org_units` with Materialized Path:** store `path` (e.g., `/1/12/45/`) + `parent_id` for instant subtree queries ("all employees under Gulf Operations").
*   **Solid-line reporting:** `employees.reporting_manager_id` (self-FK) — the *real* chain used for approvals.
*   **Dotted-line / matrix management:** `employee_relations` with `relation_type='matrix_manager'` for project-based reporting without breaking the solid line.
*   **Authority levels:** `employees.authority_level` + `employee_roles.authority_level` — higher number = higher authority; drives approval thresholds (e.g., expense > 500 OMR needs `authority_level ≥ 3`).
*   **Leverage existing services:** `get_org_chart`, `get_user_chain`, `get_all_subordinates`, `can_manage`, `reassign_manager`, `backfill_authority_levels` — expose them via a visual, draggable **Org Chart UI** (admin can drag an employee to a new manager; system recomputes `authority_level` + `path` in one transaction).
*   **Hierarchy invariants (DB triggers):** prevent circular reporting (manager cannot be their own descendant); prevent an employee reporting to a lower authority level unless explicitly flagged as matrix.

---

### **Phase 3 — Permission & RBAC System (Weeks 4–5)** ⭐
*   **Three-layer permission model:**
    1.  **Global role** (`employee_roles.permissions` JSON) — base capabilities (e.g., `hr.leave.approve`).
    2.  **Country role** (`country_staff_assignments.role_in_country`: `country_head`, `country_manager`, `country_finance`, `country_moderator`) — overrides/scope within a country.
    3.  **Hierarchy-derived** — managers inherit approval rights over their subtree via `can_manage()`.
*   **Effective-permission resolver:** `_effective_staff_permissions(user)` merges the three layers with precedence *Country > Hierarchy > Global*, cached in Redis (invalidate on role/hierarchy change).
*   **Granular permission strings** grouped into catalogs: `hr.*`, `finance.*`, `comms.*`, `country.*`, `admin.*` — each mapped in `ADMIN_PERMISSION_MAP` / `STAFF_PERMISSION_GROUPS`.
*   **Permission Matrix UI:** a grid (rows = roles, columns = permission groups) with checkboxes; admin edits propagate via a Maker-Checker draft for sensitive permissions (`finance.ledger.approve`, `users.delete`).
*   **Backend enforcement:** every protected endpoint uses `require_permission("hr.payroll.release")` dependency that calls the resolver + checks RLS country.

---

### **Phase 4 — Country-Wise Employee Management (Week 5)** ⭐
*   **RLS on every `hr`/`comms` table** keyed on `country_code` (already registered in `COUNTRY_AWARE_TABLES`).
*   **Country Staff Assignment console:** assign a `user` to a country with `role_in_country`; an employee can hold *multiple* country assignments (regional roles) — UI shows a country switcher that re-sets the RLS context.
*   **Localization per country:** salary currency (`employees.currency`), leave policy (`employee_leave_ledgers` allocations differ by country), holiday calendar (`country_holiday_calendars`), labor-law rules (notice period, EOSB formula) pulled from `country_configs`.
*   **Cross-country visibility:** only `global`/`admin` roles see the consolidated view; everyone else sees strictly their assigned countries.

---

### **Phase 5 — Admin & Sub-Admin Role Assignment (Week 6)** ⭐
*   **Role tiers:** `admin` (full) → `sub_admin` (scoped) → `country_head` → `country_manager` → `moderator` → `support` → `employee`.
*   **Delegation model:** a `sub_admin` is created by an `admin` and given a *subset* of permissions + a *subset* of countries + a *subset* of modules (e.g., "HR-only sub-admin for Oman"). A sub-admin **cannot grant a permission they don't hold** (enforced in the assignment endpoint).
*   **Maker-Checker for sensitive assignments:** assigning `finance.*` or `admin` rights creates a `pending_*` record requiring a second admin's approval.
*   **Audit every assignment:** write to `finance_audit_logs`/`admin_activity_logs` with `old_value_json`/`new_value_json` + `assigned_by`.
*   **Self-service role request:** employees can *request* elevated access; routed up the hierarchy via `can_manage()` chain for approval.

---

### **Phase 6 — Employee Lifecycle: Onboarding → Offboarding (Weeks 6–7)**
*   **Onboarding pipeline** (`onboarding_pipelines`/`onboarding_steps`): auto-create `users` + `employees`, assign `org_unit`, manager, role, country; trigger document collection (`employee_documents`), biometric enrollment, equipment assignment (`employee_assets`), ID card issuance (`physical_id_cards`), and welcome email — each step tracked with SLA.
*   **Probation tracking:** auto-alert manager at 30/60/90 days; conversion requires a performance check-in.
*   **Offboarding** (`offboarding_cases`): revoke sessions, disable `user_devices`, reclaim `employee_assets`, run exit survey, transfer ownership of their open tasks (`shift_handover_tasks`), archive chat/email per retention policy, mark `employment_status='terminated'` + `termination_date`.

---

### **Phase 7 — Time, Attendance, Leave & Shifts (Weeks 7–8)**
*   **Attendance:** `employee_attendance` via QR-kiosk + biometric + geo-fence; flag `is_anomaly` when Haversine distance > 50m or device untrusted; manager dashboard of anomalies.
*   **Shifts:** `employee_shift_rosters` with auto-scheduling rules; **shift handover** (`shift_handover_sessions` + `shift_handover_tasks`) ensures continuity — outgoing staff must acknowledge pending tasks before clock-out.
*   **Leave:** `employee_leave_requests` routed to `reporting_manager_id`; balances enforced against `employee_leave_ledgers` (allocated/used/carried_forward); country-specific leave types.
*   **Work logs:** `employee_work_logs` with hours + geo + approval workflow → feeds utilization analytics.

---

### **Phase 8 — Internal Communication Suite (Weeks 8–10)** ⭐ *(Requested in detail)*
Build on `direct_chat_rooms`, `direct_chat_messages`, `group_chat_rooms`/`group_chat_members`, `internal_channels`, `internal_messages`, `employee_communication_threads`.

*   **1:1 Chat:** auto-create/return a `direct_chat_room` for any two employees; messages stored with `sender_id`, `body`, `attachment_ids`, `reply_to_id`.
*   **Group Chat:** create room, add `group_chat_members`; roles (admin/member); @mentions resolve to `user_id`.
*   **Channels (Slack-style):** `internal_channels` per department/country/project (e.g., `#oman-sales`, `#finance-announcements`); public vs private; topic + pinned messages.
*   **Rich Attachments (the gap to fill):** add `chat_attachments` linking to `media_assets` — support **image, video, voice note, document**. Voice notes: record in-app → upload compressed `.ogg`/`.m4a` → store duration + waveform JSON for inline playback.
*   **Real-time delivery:** use your existing `WebSocketManager` (`broadcast_to_room`, `send_employee_update`) for new messages, typing indicators, read receipts (`chat_read_receipts`), and online presence.
*   **Message features:** reply threading, edit/delete (with audit), emoji reactions, search (full-text on `body`), forward, and **message retention** per channel policy.
*   **Privacy & compliance:** all internal chat is country-scoped; admins can place a *legal-hold* on a room (freezes deletion) for investigations; every message write logs to `communication_audit_trails`.

---

### **Phase 9 — Internal Email System (Weeks 10–12)** ⭐ *(Requested in detail)*
A full in-org mailbox so employees rarely leave the platform.

*   **Per-employee inbox:** `internal_emails` (sender, recipients[], cc[], subject, body_html, attachments[], folder, labels, thread_id, read_at) + `email_folders` (Inbox, Sent, Drafts, Trash, custom).
*   **Smart addressing router:** when composing, the recipient picker searches the **employee directory first**; if the address matches an internal `users.email`, the message is delivered *in-database* (instant, free, audited). Only truly external addresses are handed to `transactional_email_service` / SMTP relay.
*   **Threading:** `thread_id` + `in_reply_to` to build conversation views; auto-collapse long threads.
*   **Attachments:** reuse `media_assets` + `chat_attachments` pattern; enforce per-org size limits + virus scan hook.
*   **External relay controls:** country/role-based allow-lists for external domains; sensitive-content DLP scan (PII/keywords) before external send; mandatory BCC to compliance for certain roles.
*   **Notifications:** new internal mail → in-app badge + optional push + (configurable) external forwarding digest.
*   **Search & labels:** full-text search across subject+body; user labels/filters/rules ("auto-label invoices from finance@").

---

### **Phase 10 — Employee-to-Employee Logs & Activity Ledger (Week 12)** ⭐
A single append-only **collaboration/activity ledger** (`employee_activity_logs`) answering "who did what, with whom, when."

*   **Logged events:** logins, attendance scans, handovers, mentions in chat/email, document shares, file attachments, approvals given/received, profile edits, hierarchy moves, performance reviews submitted.
*   **Actor + Target + Context:** each row stores `actor_employee_id`, `target_employee_id` (the "with whom"), `action`, `entity_type`, `entity_id`, `country_code`, `metadata_json`, `ip`, `device`.
*   **Use cases:** manager "collaboration heatmap," audit/discovery (`ediscovery`), onboarding buddy tracking, and dispute resolution.
*   **Privacy:** employees see *their own* log; managers see their subtree's; HR/legal see all (gated by permission + logged access).

---

### **Phase 11 — Performance Management & HR Analytics (Weeks 13–15)** ⭐ *(Requested: "who is working good or not")*
*   **OKR/KPI framework:** `okr_objectives` (company → department → individual, cascaded via hierarchy) + `kpi_metrics` (quantitative: sales, tickets resolved, on-time deliveries; pulled automatically from operational tables where possible).
*   **Review cycles:** `performance_reviews` with **360° inputs** — self, manager (`reporting_manager_id`), peers (from `employee_relations`/matrix), and subordinates; weighted into `employees.performance_score`.
*   **Continuous check-ins:** lightweight monthly 1:1 logs between manager and report (stored, searchable); replaces the "annual surprise review."
*   **Auto-derived signals:** combine `attendance` punctuality, `work_logs` hours, KPI attainment, leave abuse patterns, and `is_anomaly` flags into a **Performance Health Score** with red/amber/green — surfaced on the manager dashboard.
*   **Calibration & ranking:** department calibration sessions to normalize scores; flag top/bottom percentiles.
*   **PIP & recognition:** low scores auto-trigger a Performance Improvement Plan workflow (ties to `disciplinary_cases` if unresolved); high scores feed bonus multipliers + `alumni_network`/recognition badges.
*   **HR Analytics dashboards:** headcount by country/department, attrition risk model, gender/pay equity (`DEI` tab), hiring velocity, leave burn rate, overtime cost — all from **materialized views** for speed.

---

### **Phase 12 — Payroll & Auto Salary Disbursement (Weeks 15–17)** ⭐ *(Requested: "auto salaries")*
Wire the existing `generate_payroll_batch` / `calculate_monthly_payroll` into the Finance/Treasury engine.

*   **Payroll inputs auto-aggregated:** base `salary` + attendance (deduct unpaid absences) + overtime (`work_logs`) + approved `employee_expenses` + travel `per_diem_json` + leave encashment + **performance bonus multiplier** (from Phase 11) + statutory deductions (tax, social, EOSB accrual).
*   **Country-specific rules:** tax brackets, EOSB formula, allowances pulled from `country_configs` / `country_payout_rules`.
*   **Payslip generation:** per-employee PDF payslip with breakdown; stored in `employee_documents` (type=`payslip`) — visible only to that employee + payroll admin.
*   **Auto-disbursement pipeline:**
    1.  Payroll batch → creates one `payout_batch` grouping all employees, with line items per employee → their `employee_bank_account` (IBAN/SWIFT).
    2.  **Maker-Checker:** payroll manager *generates*, finance controller *approves* (no self-approval).
    3.  On approval → Treasury engine posts the **double-entry journal** (Salary Expense Dr / Bank & Payables Cr / Tax Payable Cr) → triggers the bank transfer (API or generated bank file).
    4.  Reconcile via the bank-reconciliation engine; flag failed transfers for retry.
*   **Immutability & audit:** once a period is paid + `fiscal_periods` closed, no edits allowed; corrections go through next-period adjustments.
*   **Employee notification:** payslip ready → in-app + email; disbursement done → SMS/email confirmation.

---

### **Phase 13 — Employee Self-Service Portal (ESS) (Week 17)**
*   Mobile + web portal where employees manage their *own*: profile, documents upload, leave requests, expense claims, payslips, tax forms, bank details (with change-verification freeze), shift swap requests, org-chart view of their team, performance goals, and training (`lms`).
*   Reduces HR ticket volume dramatically; every self-service action still writes to the activity ledger.

---

### **Phase 14 — Compliance, COI & Governance (Week 18)**
*   **Conflict-of-Interest engine** (`coi_reports` + `employee_relations`): auto-detect reporting lines between relatives (`employee_dependents`/`employee_relations`) or shared external interests; flag for review.
*   **Document expiry alerts:** `employee_documents`/`employee_certifications` nearing `expiry_date` → auto-notify employee + manager + block certain actions until renewed.
*   **Disciplinary workflow** (`disciplinary_cases`) with evidence attachments and hierarchy-aware approvals.
*   **Data residency & PDPL/GDPR:** PII columns encrypted at rest; right-to-access/export; retention jobs purge chat/email per policy (with legal-hold override).

---

## 🧩 Integration Matrix (How EMS Talks to the Rest of Zozi)

| EMS Module | Integrates With | Mechanism |
|---|---|---|
| Login / Sessions | `core` (users, user_devices), `risk` (fraud) | JWT + RLS context + risk scoring |
| Hierarchy / Approvals | `finance` (expenses, payroll), `hr` (leave) | `can_manage()` + `authority_level` thresholds |
| Country scoping | `country` (configs, holidays, payout rules) | RLS + `country_staff_assignments` |
| Chat / Email attachments | `media` (media_assets) | Shared asset store + CDN |
| Real-time chat | `comms` WebSocket | `WebSocketManager.broadcast_to_room` |
| Payroll disbursement | `finance` + `treasury` | Event-driven: payroll → `payout_batch` → journal → bank |
| Performance bonus | `finance` payroll | KPI score → bonus multiplier |
| Activity logs | `audit` | Append-only `employee_activity_logs` |
| KPI auto-metrics | `commerce`, `logistics`, `support` | Read operational tables (no write-back) |

---

## ⚙️ Technical Architecture Principles

*   **Event-driven, not coupled:** HR actions publish events (`employee_hired`, `payroll_approved`, `review_submitted`); Finance/Comms/Analytics *subscribe*. HR never writes to finance tables directly.
*   **Async heavy work:** payslip PDF generation, bank-file creation, video/voice transcoding, and analytics aggregation run on **Celery/Redis queues** — never block the API.
*   **Performance:** `selectinload`/`joinedload` everywhere; materialized views for HR dashboards; composite indexes on `(country_code, employment_status)`, `(reporting_manager_id)`, `(org_unit_id)`.
*   **Security defaults:** RLS on, MFA for privileged roles, device binding, immutable audit logs, Maker-Checker on money & permissions.
*   **Frontend:** route-driven tabs (you already have `directory, offices, attendance, leaves, shifts, iam, payroll, documents, coi, audit, communications, addresses, performance, disciplinary, hse, alumni, insurance, dei`) — lazy-load each, reuse `EnterpriseDataTable`, respect `useDensity`.

---

## 📅 Suggested Timeline (18 weeks, 1 senior backend + 1 frontend + 0.5 DevOps)

| Weeks | Phases | Key Deliverable |
|---|---|---|
| 1 | 0 | Schema aligned, gaps added, permission catalog frozen |
| 2–3 | 1 | Unified login (5 doors) + device/MFA/RLS |
| 3–5 | 2, 3 | Draggable org chart + RBAC matrix |
| 5–6 | 4, 5 | Country scoping + sub-admin delegation |
| 6–8 | 6, 7 | Lifecycle + attendance/shifts/handover |
| 8–12 | 8, 9 | Full chat (attachments/voice) + internal email |
| 12–13 | 10 | Activity/collaboration ledger |
| 13–15 | 11 | Performance/OKR/360 + HR analytics |
| 15–17 | 12, 13 | Auto payroll disbursement + ESS portal |
| 17–18 | 14 | COI, compliance, hardening, E2E tests |

---

## ✅ Definition of "Done" (Acceptance Criteria)

*   An employee can log in via biometric on mobile *and* QR-kiosk at the office with the same identity and correct country scope.
*   A manager sees their subtree's org chart, approves leave/expenses by authority threshold, and views a performance health board.
*   Two employees exchange a 1:1 chat with a voice note and an image attachment in real time; a department channel broadcasts an announcement.
*   An employee sends an internal email that never touches SMTP; an external email passes DLP + allow-list checks.
*   At month-end, payroll auto-aggregates attendance + expenses + KPI bonus, generates payslips, and—after Maker-Checker—disburses salaries to bank accounts with a balanced double-entry journal, all reconciled automatically.
*   Every action above is captured in the activity ledger and immutable audit logs, fully country-isolated by RLS.

---

This roadmap turns your existing HR tables into a **governed, country-aware, self-driving employee platform** — login, hierarchy, permissions, communication, email, performance, and payroll all operating as one coherent system rather than disconnected screens. produce the **exact database migration (Alembic) for the gap tables** (`employee_bank_accounts`, `okr_*`, `performance_reviews`, `internal_emails`, `chat_attachments`, `employee_activity_logs`) or the **login service code** for the 5-door authentication.


# _____________________________________________________________________________________________

# Employee Chat, Video & Email System

Enterprise communication platform for employee collaboration, video conferencing, and external communication with compliance and security features.

---

## 🏛️ SECTION 1: Database Schema & Implementation Status

### 1.1 Chat Models (core.py) - ✅ IMPLEMENTED

| Model | Status | Description | Location |
|-------|--------|-------------|----------|
| EntityChatThread | ✅ | Generic chat threads for entities | core.py:245-256 |
| EntityChatMessage | ✅ | Messages in entity threads | core.py:258-268 |
| DirectChatRoom | ✅ | One-on-one chat rooms | core.py:328-340 |
| DirectChatMessage | ✅ | Messages in direct chats | core.py:343-353 |
| GroupChatRoom | ✅ | Group chat rooms | core.py:356-369 |
| GroupChatMember | ✅ | Members in group chats | core.py:371-380 |
| GroupChatMessage | ✅ | Messages in group chats | core.py:383-393 |

### 1.2 Video Models (core.py) - ✅ IMPLEMENTED

| Model | Status | Description | Location |
|-------|--------|-------------|----------|
| VideoRoom | ✅ | Video conference rooms | core.py:271-296 |
| VideoRoomParticipant | ✅ | Participants in rooms | core.py:299-311 |
| VideoRoomRecording | ✅ | Meeting recordings | core.py:314-325 |

### 1.3 Email & Notification Models (communication.py) - ✅ IMPLEMENTED

| Model | Status | Description | Location |
|-------|--------|-------------|----------|
| Notification | ✅ | System notifications | communication.py:14-31 |
| TicketMessage | ✅ | Support ticket messages | communication.py:34-42 |
| ProxyChannel | ✅ | Masked communication channels | communication.py:78-91 |
| ProxySession | ✅ | Proxy communication sessions | communication.py:94-106 |
| ProxyMessage | ✅ | Messages through proxy | communication.py:109-122 |
| ProxyCallLog | ✅ | Call logs through proxy | communication.py:125-139 |

### 1.4 Employee Communication Models (communication.py) - ✅ IMPLEMENTED

| Model | Status | Description | Location |
|-------|--------|-------------|----------|
| EmployeeCommunicationThread | ✅ | Employee communication threads | communication.py:147-163 |
| ExternalContactMasking | ✅ | Masked external contacts | communication.py:166-182 |
| CommunicationAuditTrail | ✅ | Audit trail for communications | communication.py:185-202 |
| InternalChannel | ✅ | Internal team channels | communication.py:205-222 |
| InternalChannelMember | ✅ | Channel members | communication.py:225-238 |
| InternalMessage | ✅ | Messages in internal channels | communication.py:241-258 |

### 1.5 Employee Models (employee_models.py) - ✅ IMPLEMENTED

| Model | Status | Description |
|-------|--------|-------------|
| Employee | ✅ | Core employee profile |
| EmployeeAttendance | ✅ | Attendance tracking |
| EmployeeWorkLog | ✅ | Work hours logging |
| EmployeeLeaveRequest | ✅ | Leave management |
| EmployeeShiftRoster | ✅ | Shift scheduling |
| Office | ✅ | Office locations |
| PhysicalIDCard | ✅ | ID card management |
| EmployeeAsset | ✅ | Asset tracking |
| EmployeeDocument | ✅ | Document management |
| EmployeeCertification | ✅ | Certification tracking |
| COIReport | ✅ | Conflict of interest |
| TravelRequest | ✅ | Travel approvals |
| DisciplinaryCase | ✅ | Disciplinary tracking |
| OffboardingCase | ✅ | Offboarding workflow |

---

## 🧠 SECTION 2: Backend Services - Implementation Status

### 2.1 Chat System Service - ✅ IMPLEMENTED

**File:** `backend/services/chat_system.py` (408 lines)

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| create_entity_chat() | Create chat for entity | ✅ |
| create_direct_chat() | Create 1-on-1 chat | ✅ |
| create_group_chat() | Create group chat | ✅ |
| send_message() | Send message to chat | ✅ |
| get_chat_history() | Retrieve message history | ✅ |
| mark_read() | Mark messages as read | ✅ |
| create_thread() | Create entity thread | ✅ |
| get_thread_messages() | Get thread messages | ✅ |
| list_threads() | List all threads | ✅ |

### 2.2 Video Conferencing Service - ✅ IMPLEMENTED

**File:** `backend/services/video_conferencing.py`

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| create_room() | Create video room | ✅ |
| list_rooms() | List all rooms | ✅ |
| generate_token() | Generate meeting token | ✅ |
| generate_watermark() | Add watermarks to frames | ✅ |
| _transcribe_audio() | Transcribe meeting audio | ✅ |
| _translate_text() | Translate transcripts | ✅ |
| add_transcript_segment() | Add transcript segment | ✅ |
| extract_action_items() | Extract action items | ✅ |
| get_transcript() | Get meeting transcript | ✅ |
| start_recording() | Start recording | ✅ |
| end_room() | End meeting | ✅ |
| get_room_details() | Get room details | ✅ |

### 2.3 Email Gateway Service - ✅ IMPLEMENTED

**File:** `backend/services/email_gateway.py`

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| send_internal_email() | Send to internal users | ✅ |
| send_external_email() | Send to external parties | ✅ |
| send_from_alias() | Send from role-based alias | ✅ |
| get_email_templates() | Get available templates | ✅ |
| send_bulk_email() | Send bulk emails | ✅ |
| get_suppression_list() | Get suppressed emails | ✅ |
| track_open() | Track email opens | ✅ |
| DLPScanner.scan_content() | Scan for PII | ✅ |
| RoleBasedAliasManager.get_alias_for_role() | Get role alias | ✅ |
| get_email_history() | Get email history | ✅ NEW |

### 2.4 Internal Communication Service - ✅ NEW

**File:** `backend/services/internal_communication.py`

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| create_channel() | Create internal channel | ✅ |
| get_channel() | Get channel details | ✅ |
| list_channels() | List all channels | ✅ |
| add_member() | Add member to channel | ✅ |
| remove_member() | Remove member from channel | ✅ |
| send_message() | Send internal message | ✅ |
| get_messages() | Get channel messages | ✅ |

### 2.5 External Contact Service - ✅ NEW

**File:** `backend/services/external_contact.py`

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| create_mask() | Create contact mask | ✅ |
| get_mask() | Get mask details | ✅ |
| create_proxy_channel() | Create proxy channel | ✅ |
| send_message() | Send through proxy | ✅ |
| log_call() | Log proxy calls | ✅ |

### 2.6 Communication Audit Service - ✅ NEW

**File:** `backend/services/communication_audit.py`

**Methods Implemented:**
| Method | Description | Status |
|--------|-------------|--------|
| log_event() | Log audit event | ✅ |
| get_audit_trail() | Get audit trail | ✅ |
| export_for_ediscovery() | Export for legal discovery | ✅ |

### 2.7 eDiscovery Service - ✅ IMPLEMENTED

**File:** `backend/services/ediscovery.py`

**Purpose:** Legal discovery and compliance for employee communications

### 2.8 Proxy Communication Service - ✅ IMPLEMENTED

**File:** `backend/services/proxy_communication.py`

**Purpose:** Masked communication between employees and external parties

---

## 🖥️ SECTION 3: API Endpoints - Implementation Status

### 3.1 Chat Controller - ✅ IMPLEMENTED

**File:** `backend/controllers/chat_controller.py`

**Endpoints Implemented:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /direct | Create direct chat |
| POST | /group | Create group chat |
| POST | /message | Send message |
| GET | /history/{chat_id} | Get chat history |
| GET | /threads | List threads |
| POST | /threads | Create thread |
| GET | /threads/{thread_id}/messages | Get thread messages |
| POST | /threads/{thread_id}/messages | Send thread message |
| POST | /read | Mark as read |

### 3.2 Video Controller - ✅ IMPLEMENTED

**File:** `backend/controllers/video_controller.py`

**Endpoints Implemented:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /rooms | Create video room |
| GET | /rooms | List rooms |
| POST | /rooms/{room_id}/tokens | Generate token |
| POST | /rooms/{room_id}/recording | Start recording |
| POST | /rooms/{room_id}/end | End meeting |
| GET | /rooms/{room_id} | Get room details |

### 3.3 Email Controller - ✅ IMPLEMENTED

**File:** `backend/controllers/email_controller.py`

**Endpoints Implemented:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /internal | Send internal email |
| POST | /external | Send external email |
| GET | /templates | Get templates |
| POST | /track-open | Track opens |
| GET | /history/{user_id} | ✅ NEW - Email history |

**Missing Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /bulk | Send bulk emails | ❌ |
| POST | /from-alias | Send from alias | ❌ |

### 3.4 Internal Channels Controller - ✅ NEW

**File:** `backend/routers/internal_channels.py`

**Endpoints Implemented:**
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/internal/channels | Create channel |
| GET | /api/v1/internal/channels | List channels |
| GET | /api/v1/internal/channels/{channel_id} | Get channel |
| POST | /api/v1/internal/channels/{channel_id}/members | Add member |
| DELETE | /api/v1/internal/channels/{channel_id}/members/{user_id} | Remove member |
| POST | /api/v1/internal/channels/{channel_id}/messages | Send message |
| GET | /api/v1/internal/channels/{channel_id}/messages | Get messages |

### 3.5 Audit Trail Controller - ✅ NEW

**File:** `backend/routers/audit.py`

**Endpoints Implemented:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/audit | Get audit trail |
| GET | /api/v1/audit/export | Export for eDiscovery |

---

## 📊 SECTION 4: Feature Matrix - Detailed Status

### 4.1 Video Conferencing Features

| Feature | Implementation | Notes |
|---------|----------------|-------|
| Create Meeting | ✅ | create_room() exists |
| Participant Management | ✅ | VideoRoomParticipant |
| Recording | ✅ | VideoRoomRecording, start_recording() |
| Transcription | ⚠️ Partial | _transcribe_audio() exists, needs real-time |
| Action Items | ✅ | extract_action_items() |
| Watermarked Frames | ✅ | generate_watermark() |
| Token Generation | ✅ | generate_token() |
| Boardroom Mode | ✅ | is_boardroom flag |
| Country Linking | ✅ | country_code field |

### 4.2 Chat Features

| Feature | Implementation | Notes |
|---------|----------------|-------|
| Direct Messaging | ✅ | DirectChatRoom |
| Group Chats | ✅ | GroupChatRoom/Member |
| Entity Threads | ✅ | EntityChatThread |
| Message History | ✅ | Pagination supported |
| Read Receipts | ✅ | read_at field |
| Encryption | ⚠️ Partial | is_encrypted flag exists |
| Country Context | ✅ | country_code field |
| Masked Communication | ⚠️ Partial | is_masked field |
| Employee Threads | ✅ | EmployeeCommunicationThread |
| Internal Channels | ✅ | InternalChannel, InternalMessage |

### 4.3 Email Features

| Feature | Implementation | Notes |
|---------|----------------|-------|
| Internal Email | ✅ | send_internal_email() |
| External Email | ✅ | send_external_email() |
| Role-based Aliases | ✅ | RoleBasedAliasManager |
| DLP Scanning | ✅ | DLPScanner class |
| Bulk Email | ✅ | send_bulk_email() |
| Email Tracking | ✅ | track_open() |
| Templates | ✅ | get_email_templates() |
| Email History | ✅ | get_email_history() |

### 4.4 Employee Communication Features

| Feature | Implementation | Notes |
|---------|----------------|-------|
| Shift Handover | ✅ | ShiftHandoverSession model |
| Office Communication | ⚠️ Partial | Office model exists |
| Country Communication | ⚠️ Partial | CountryCommunicationThread exists |
| External Contact Masking | ⚠️ Partial | ProxyChannel exists but not fully utilized |
| eDiscovery | ✅ | ediscovery.py exists |
| Communication Audit | ⚠️ Partial | CommunicationAuditTrail model exists |
| Internal Channels | ✅ | InternalChannel, InternalMessage |
| Proxy Communication | ✅ | ExternalContactService |

---

## ⚠️ SECTION 5: Missing Components & Needs

### 5.1 Missing Models

All models in communication.py and core.py are implemented. No new models needed.

### 5.2 Missing API Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| POST /api/v1/video/rooms | ✅ Implemented | Create video room |
| GET /api/v1/video/rooms | ✅ Implemented | List rooms |
| GET /api/v1/video/rooms/{id} | ✅ Implemented | Get room details |
| POST /api/v1/chat/internal | ✅ Implemented | Internal team chat |
| GET /api/v1/email/history | ✅ Implemented | Email history |
| GET /api/v1/audit | ✅ Implemented | Audit trail |
| GET /api/v1/internal/channels | ✅ Implemented | List internal channels |
| POST /api/v1/internal/channels | ✅ Implemented | Create internal channel |
| POST /api/v1/internal/channels/{id}/messages | ✅ Implemented | Send internal message |

### 5.3 Missing Services

| Service | Status | Description |
|---------|--------|-------------|
| InternalCommunicationService | ✅ Implemented | Team/internal communications |
| ExternalContactService | ✅ Implemented | Masked external communication |
| CommunicationAuditService | ✅ Implemented | Audit logging |

### 5.4 Missing Frontend Components

| Component | Status | Description |
|-----------|--------|-------------|
| Employee Workspace Page | ⚠️ Partial | Dedicated employee dashboard needed |
| Chat Interface | ⚠️ Partial | Needs country context |
| Video Meeting Scheduler | ⚠️ Partial | UI for scheduling meetings |
| Email Inbox/Outbox | ⚠️ Partial | Email client interface |
| eDiscovery Portal | ⚠️ Partial | Legal discovery interface |
| Internal Channels UI | ⚠️ Partial | Team channel management |
| Communication Audit UI | ⚠️ Partial | Audit trail viewer |

---

## 🚀 SECTION 6: Implementation Roadmap

### Phase 1: Complete Models & Migrations (Week 1)
- [x] All models exist in core.py and communication.py
- [x] No new models needed

### Phase 2: API Endpoints (Week 2) ✅ COMPLETE
- [x] Chat controller exists
- [x] Video controller exists
- [x] Email controller exists
- [x] Internal channels endpoints created
- [x] Audit trail endpoints created
- [x] Email history endpoint created

### Phase 3: Services (Week 2-3) ✅ COMPLETE
- [x] Chat system service
- [x] Video conferencing service
- [x] Email gateway service
- [x] Internal communication service
- [x] External contact service
- [x] Communication audit service

### Phase 4: Frontend Workspace (Week 3-4)
- [ ] Create Employee Workspace page
- [ ] Build Chat interface with country context
- [ ] Build Video Meeting scheduler
- [ ] Build Email inbox/outbox
- [ ] Build eDiscovery portal
- [ ] Build Internal Channels UI
- [ ] Build Communication Audit UI

### Phase 5: Integration (Week 5)
- [ ] Wire fraud detection into communication flows
- [ ] Connect to country staff assignments
- [ ] Implement shift handover workflow
- [ ] Add real-time WebSocket for chat

### Phase 6: Compliance & Security (Week 6)
- [ ] Implement WORM storage for recordings
- [ ] Add GDPR-compliant data export
- [ ] Implement retention policies
- [ ] Add audit logging

---

## 📊 SECTION 7: Key Metrics & Monitoring

### 7.1 Chat Metrics
- Messages per day
- Active users
- Read receipt rate
- Message latency

### 7.2 Video Metrics
- Meeting duration
- Participant count
- Recording rate
- Transcription accuracy

### 7.3 Email Metrics
- Emails sent/received
- Open rate
- DLP blocks
- Bounce rate

### 7.4 Compliance Metrics
- eDiscovery requests fulfilled
- Audit trail completeness
- Retention policy adherence
- Masking success rate

---

## Summary

**Key Technologies:**
- PostgreSQL with JSONB and advanced indexing
- Redis for caching and real-time messaging
- Python/FastAPI for backend services
- SQLAlchemy ORM for models
- WebSocket for real-time chat

**Recent Progress:**
- ✅ Created InternalCommunicationService with channels and messaging
- ✅ Created ExternalContactService for masked communication
- ✅ Created CommunicationAuditService for compliance logging
- ✅ Added internal channels API endpoints (`/api/v1/internal/channels/*`)
- ✅ Added audit trail API endpoints (`/api/v1/audit/*`)
- ✅ Added email history endpoint (`/api/v1/email/history/{user_id}`)

**Current Gaps:**
1. **Frontend Employee Workspace** - No dedicated UI
2. **Video Meeting Scheduler UI** - Meeting scheduling interface
3. **WORM Storage** - For meeting recordings compliance
4. **Real-time WebSocket for chat** - Already exists, needs enhancement

**Next Steps:**
1. Create Employee Workspace frontend page
2. Build Video Meeting scheduler UI
3. Implement WORM-compliant storage for recordings
4. Enhance WebSocket support for real-time messaging
5. Integrate fraud detection signals into communication flows

















































# Staff Management Guide (Codebase Aligned)

## Purpose

This is the canonical guide for staff management behavior in Zozi.

It is aligned with the current implementation in backend and frontend code, not historical drafts.

## Scope

This guide covers:

- Staff roles and permission model
- Staff account lifecycle (create, update, bulk update, delete)
- Permission catalog governance
- API and UI behavior for admin staff management

This guide does not cover:

- Customer-facing user management
- Supplier onboarding workflows
- General authentication flows outside admin reset password

## Canonical Source Files

### Backend

- `backend/utils/staff_permissions.py`
- `backend/routers/admin.py`
- `backend/controllers/admin_controller.py`
- `backend/alembic/versions/s1t2u3v4w5x6_add_staff_management_user_fields.py`

### Frontend

- `frontend/web_app/src/app/admin/staff/page.tsx`
- `frontend/shared/src/adminPermissions.ts`

### Tests

- `backend/tests/test_admin_management.py`
- `frontend/web_app/src/__tests__/pages/adminStaffPage.test.tsx`
- `frontend/web_app/src/__tests__/pages/adminStandalonePages.test.tsx`

## Staff Role Model

Zozi supports four staff roles in the admin space:

- `admin`
- `sub_admin`
- `moderator`
- `support`

Role membership and default permissions are defined in `backend/utils/staff_permissions.py` and mirrored in `frontend/shared/src/adminPermissions.ts`.

## Permission Catalog

### Group: Governance

- `analytics.view`
- `audit.read`
- `hierarchy.view`

### Group: Users and Staff

- `users.read`
- `users.role.update`
- `users.toggle_active`
- `users.delete`
- `users.reset_password`
- `staff.view`
- `staff.create`
- `staff.manage`
- `staff.delete`

### Group: Commerce Operations

- `orders.manage`
- `products.manage`
- `moderation.suppliers`
- `moderation.products`
- `tickets.manage`
- `coupons.manage`
- `payouts.verify`

## Default Permission Behavior

- When a staff account is created without explicit permissions, permissions are assigned from `default_permissions_for_role(role)`.
- When a staff role changes and no explicit permissions are provided, permissions are recalculated from the role default.
- Explicit permissions are always sanitized through `sanitize_staff_permissions`.
- Unknown or duplicate permissions are ignored by sanitizer logic.

## Data Model

Staff profile fields are stored on `users` (migration: `s1t2u3v4w5x6_add_staff_management_user_fields.py`):

- `full_name`
- `staff_role_label`
- `staff_title`
- `staff_department`
- `staff_area_of_operation`
- `staff_hire_date`
- `staff_experience_level`
- `staff_performance_summary`
- `staff_assigned_tasks` (JSON)
- `staff_assigned_projects` (JSON)
- `staff_permissions` (JSON)
- `staff_notes`

## API Surface

All routes below are under `/admin` in `backend/routers/admin.py`.

| Method | Path | Permission gate | Notes |
| --- | --- | --- | --- |
| POST | `/staff` | `staff.create` | Creates staff account. Controller enforces acting role `admin`. |
| GET | `/staff` | `staff.view` | Lists staff accounts and effective permission view. |
| GET | `/staff/permission-catalog` | `staff.manage` | Returns grouped permission catalog and default role map. |
| PUT | `/staff/bulk` | `staff.manage` | Applies same updates to multiple staff users. |
| PUT | `/staff/{user_id}` | `staff.manage` | Updates one staff profile, role, permissions, status. |
| DELETE | `/staff/{user_id}` | `staff.delete` | Deletes staff user if no retention blockers. |
| POST | `/users/{user_id}/reset-password` | `users.reset_password` | Admin password reset for any user. |

## Critical Guardrails

### 1) Admin-only mutation

The controller layer (`create_staff_account`, `update_staff_account`, `bulk_update_staff_accounts`) enforces acting role `admin` for create/update/bulk operations.

### 2) Self-protection rules

For the currently logged-in admin, sensitive self-edits are blocked:

- Role changes
- Permission changes
- Deactivation (`is_active = false`)

### 3) Permission validation

- Incoming permission lists are sanitized against known permission keys.
- Empty permission sets are rejected when explicit permissions are supplied.

### 4) Audit logging

Staff lifecycle actions write audit events, including create, update, bulk update, and delete operations.

## Admin UI Behavior

The staff management workspace at `frontend/web_app/src/app/admin/staff/page.tsx` provides:

- Staff directory listing
- Search and filtering
- Create staff flow
- Profile details view
- Edit and delete actions
- Bulk update workflow
- Permission catalog usage for guided assignment
- Reset password action through admin user endpoint

## Operations & Workflows

This section is the runbook for how operations teams use staff management in production.

### Preconditions

Before running any staff operation:

- You are authenticated as an admin account
- Your account has required admin permissions for the action
- You confirm target user identity and role intent

### Workflow 1: Create Staff Account

**UI Path:**
- Open admin staff workspace: `/admin/staff`
- Use create action in staff directory
- Enter identity, role, and assignment metadata
- Optionally assign explicit permissions

**API Path:** `POST /admin/staff`

**Operational Rules:**
- Email and username must be unique
- If explicit permissions are omitted, role defaults are applied
- Only valid known permissions are persisted
- Creation is audit logged

### Workflow 2: Update Staff Account

**UI Path:**
- Open staff profile from directory
- Edit role, metadata, and assignments
- Save updates

**API Path:** `PUT /admin/staff/{user_id}`

**Operational Rules:**
- Sensitive self-edits are blocked for the acting admin (role, permissions, active status)
- If role changes without explicit permissions, role defaults are applied
- If explicit permissions are provided, at least one valid permission is required
- Update is audit logged

### Workflow 3: Bulk Update Staff Accounts

**UI Path:**
- Select staff rows in directory
- Open bulk update panel
- Apply shared updates

**API Path:** `PUT /admin/staff/bulk`

**Operational Rules:**
- All target IDs must resolve to staff users
- Bulk update with sensitive self-fields is blocked for acting admin
- Invalid target IDs fail the request
- Bulk update is audit logged with target IDs and field list

### Workflow 4: Force Reset User Password

**UI Path:**
- Trigger reset from staff profile or user tools

**API Path:** `POST /admin/users/{user_id}/reset-password`

**Operational Rules:**
- Use for account recovery and incident response
- Requires `users.reset_password` permission
- Confirm user identity before reset
- Communicate reset completion through approved internal process

### Workflow 5: Remove Staff Access

**UI Path:**
- Delete action from staff profile or directory

**API Path:** `DELETE /admin/staff/{user_id}`

**Operational Rules:**
- Validate downstream ownership before deletion
- Deletion is hard-delete behavior and can be blocked by related records
- Deletion is audit logged

### Permission Governance Runbook

**Weekly Review:**
- Review high-privilege assignments (`staff.manage`, `staff.delete`, `users.reset_password`)
- Validate role-to-permission consistency
- Verify no unrecognized permission strings exist

**Monthly Review:**
- Export and review current staff roster, departments, and permissions
- Check dormant or inactive staff accounts
- Validate support and moderator scopes remain least-privilege

**Incident Response:**
For suspicious account behavior:

1. Reset account password immediately.
2. Reduce permissions or deactivate account.
3. Capture audit logs for timeline reconstruction.
4. Restore least-privilege after investigation.

### Data Quality Checklist

For each staff profile, maintain:

- `full_name`
- `staff_role_label`
- `staff_title`
- `staff_department`
- `staff_area_of_operation`
- `staff_hire_date` when available
- `staff_assigned_tasks` and `staff_assigned_projects` where operationally useful
- `staff_notes` for non-sensitive context

### Known Boundaries

- Staff management UI is web-admin focused (`frontend/web_app/src/app/admin/staff/page.tsx`).
- Mutation routes are admin-controlled in backend controller logic.
- Permission catalog is fixed to known backend keys until code changes are deployed.

### Change Control

Any change to staff role or permission model must include:

1. Backend permission update (`backend/utils/staff_permissions.py`)
2. Frontend shared map update (`frontend/shared/src/adminPermissions.ts`)
3. Router/controller behavior review (`backend/routers/admin.py`, `backend/controllers/admin_controller.py`)
4. Test updates
5. Documentation updates (guide, testing checklist)

## Governance Notes

- Keep permission catalog changes synchronized across backend and shared frontend permission maps.
- Treat `backend/utils/staff_permissions.py` as canonical when conflicts appear.
- Update tests in both backend and frontend whenever permission keys or defaults change.

## Maintenance Checklist

When changing staff behavior:

1. Update backend role/permission definitions.
2. Update router/controller authorization and validations if needed.
3. Update shared frontend permission map.
4. Update staff page behavior if new fields or actions are added.
5. Update backend and frontend tests.
6. Refresh this guide and testing documentation.




---




# Staff Management Testing Checklist

## Purpose

This checklist validates staff management behavior against current backend and web-admin implementation.

## Reference Files

- `backend/routers/admin.py`
- `backend/controllers/admin_controller.py`
- `backend/utils/staff_permissions.py`
- `frontend/web_app/src/app/admin/staff/page.tsx`
- `frontend/shared/src/adminPermissions.ts`

## Core API Checks

### Create staff

- [ ] `POST /admin/staff` succeeds for valid payload by admin
- [ ] Duplicate email returns validation error
- [ ] Duplicate username returns validation error
- [ ] Missing explicit permissions falls back to role defaults
- [ ] Invalid permissions are sanitized out

### List staff and catalog

- [ ] `GET /admin/staff` returns staff entries with assignments and effective permissions
- [ ] `GET /admin/staff/permission-catalog` returns grouped permission catalog
- [ ] Catalog includes governance, users, and commerce groups

### Update staff

- [ ] `PUT /admin/staff/{user_id}` updates profile metadata
- [ ] Role change updates default permissions when explicit permissions are omitted
- [ ] Explicit permissions require at least one valid permission
- [ ] Self-update blocks role/permission/deactivation edits

### Bulk update

- [ ] `PUT /admin/staff/bulk` updates multiple users
- [ ] Missing IDs return not found error
- [ ] Self-update block applies for sensitive fields in bulk mode
- [ ] Response includes updated field list and updated users

### Delete and reset

- [ ] `DELETE /admin/staff/{user_id}` removes valid target
- [ ] Missing target returns not found
- [ ] `POST /admin/users/{user_id}/reset-password` updates password with required permission

## Authorization and Permission Checks

- [ ] Non-admin mutation attempts are rejected by controller guards
- [ ] Endpoint permission checks enforce `staff.create`, `staff.view`, `staff.manage`, `staff.delete`
- [ ] Password reset requires `users.reset_password`
- [ ] Unsupported permissions cannot be persisted

## UI Checks (Admin Staff Page)

- [ ] Staff directory loads from `/admin/staff`
- [ ] Permission catalog loads from `/admin/staff/permission-catalog`
- [ ] Create flow submits correct payload
- [ ] Edit flow updates visible profile fields
- [ ] Bulk update flow sends `PUT /admin/staff/bulk`
- [ ] Password reset action calls `/admin/users/{id}/reset-password`
- [ ] Delete flow reflects removal in directory state

## Audit Logging Checks

- [ ] Staff create action writes audit event
- [ ] Staff update action writes audit event with updated fields
- [ ] Staff bulk update writes audit event with target IDs and count
- [ ] Staff delete writes audit event with deleted identity summary

## Regression Test Targets

### Backend

- [ ] `backend/tests/test_admin_management.py`

### Frontend

- [ ] `frontend/web_app/src/__tests__/pages/adminStaffPage.test.tsx`
- [ ] `frontend/web_app/src/__tests__/pages/adminStandalonePages.test.tsx`

## Data Integrity Checks

- [ ] `staff_permissions` field stores only known permission keys
- [ ] `staff_assigned_tasks` and `staff_assigned_projects` remain valid JSON arrays
- [ ] `staff_hire_date` and profile fields persist and round-trip correctly

## Smoke Run Recommendation

Run this minimum suite after any staff-management change:

1. Backend staff management tests.
2. Web admin staff page tests.
3. Manual create-update-bulk-delete cycle on local admin UI.
