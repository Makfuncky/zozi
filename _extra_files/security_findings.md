# SECURITY domain — audit findings inventory

**Total:** 154 findings (29 RED) across 34 files

## By code

### DBA03 (24)

- 🟡 **DBA03** `backend\models\fraud.py:105` — model 'IPReputation' table 'ip_reputations' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:128` — model 'DeviceFingerprint' table 'device_fingerprints' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:148` — model 'CreditCardBin' table 'credit_card_bins' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:160` — model 'ReturnAbusePattern' table 'return_abuse_patterns' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:16` — model 'FraudEvent' table 'fraud_events' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:174` — model 'SupplierFraudIndicator' table 'supplier_fraud_indicators' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:189` — model 'LogisticsFraudIndicator' table 'logistics_fraud_indicators' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:204` — model 'FraudAlert' table 'fraud_alerts' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:224` — model 'IPAccountLinkage' table 'ip_account_linkages' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:239` — model 'VelocityCounter' table 'fraud_velocity_counters' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:253` — model 'FraudScoringLog' table 'fraud_scoring_logs' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:281` — model 'FraudCase' table 'fraud_cases' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:311` — model 'FraudCaseAssignment' table 'fraud_case_assignments' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:328` — model 'DLPViolation' table 'dlp_violations' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:350` — model 'MeetingTranscript' table 'meeting_transcripts' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:365` — model 'MeetingActionItem' table 'meeting_action_items' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:384` — model 'MeetingRecording' table 'meeting_recordings' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:48` — model 'FraudBlacklist' table 'fraud_blacklist' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:64` — model 'FraudRule' table 'fraud_rules' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:85` — model 'ManualReviewQueue' table 'manual_review_queue' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:11` — model 'IncidentWarRoom' table 'incident_war_rooms' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:29` — model 'IncidentThread' table 'incident_threads' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:41` — model 'IncidentActionItem' table 'incident_action_items' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:58` — model 'WarRoomTemplate' table 'war_room_templates' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*

### CG1 (20)

- 🔴 **CG1** `backend\controllers\auth_controller.py:163` — forbidden call: controllers._serialize_referral_event() → db.ReferralPointEventSchema() → *controllers must not call db directly*
- 🔴 **CG1** `backend\controllers\auth_controller.py:556` — forbidden call: controllers.register_user() → db.model_validate() → *controllers must not call db directly*
- 🔴 **CG1** `backend\controllers\auth_controller.py:719` — forbidden call: controllers.get_referral_dashboard() → db.ReferralDashboardSchema() → *controllers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:148` — forbidden call: routers.get_threat_feed_status() → db.ThreatFeedStatus() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:42` — forbidden call: routers.list_fraud_events() → db.FraudEventOut() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:62` — forbidden call: routers.add_to_blacklist() → models.FraudBlacklist() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:85` — forbidden call: routers.create_rule() → models.FraudRule() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:105` — forbidden call: routers.register() → models.User() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:112` — forbidden call: routers.register() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:112` — forbidden call: routers.register() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:143` — forbidden call: routers.refresh() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:143` — forbidden call: routers.refresh() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:52` — forbidden call: routers._record_login_history() → models.UserLoginHistory() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:82` — forbidden call: routers.login() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:82` — forbidden call: routers.login() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:99` — forbidden call: routers.register() → db._validate_password_complexity() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:107` — forbidden call: routers.refresh() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:43` — forbidden call: routers._issue_tokens() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:70` — forbidden call: routers.login() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:85` — forbidden call: routers.register() → db.TokenResponse() → *routers must not call db directly*

### PERF4 (17)

- 🟡 **PERF4** `backend\services\effective_permissions.py:200` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\effective_permissions.py:272` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_admin_service.py:116` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_admin_service.py:150` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_admin_service.py:80` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:103` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:118` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:162` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:84` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:1052` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:1083` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:289` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_service.py:66` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:39` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:48` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:63` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:76` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*

### HL302 (11)

- 🟡 **HL302** `backend\controllers\auth_controller.py` — swallowed exception (lines: 112, 223, 251, 461, 495, 670 +5 more) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\controllers\iam_controller.py` — swallowed exception (lines: 69) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\dependencies\fraud_events.py` — swallowed exception (lines: 43) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\middleware\impossible_travel_middleware.py` — swallowed exception (lines: 108, 121, 133, 141, 148, 153) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\routers\admin_security_detection.py` — swallowed exception (lines: 192) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\routers\admin_security_registration.py` — swallowed exception (lines: 113, 133, 100, 172, 59) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\routers\public_security_registration.py` — swallowed exception (lines: 79, 98, 136) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\services\auth_service.py` — swallowed exception (lines: 76, 600, 827, 239) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\services\effective_permissions.py` — swallowed exception (lines: 146, 162, 173, 189, 205) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\services\fraud_detection_service.py` — swallowed exception (lines: 124, 140, 643, 48, 753, 1014 +5 more) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL302** `backend\utils\auth.py` — swallowed exception (lines: 65, 183, 291, 322, 360, 37 +10 more) → *log with logger.exception(...); re-raise or return controlled error*

### CIR2 (10)

- 🟡 **CIR2** `backend\routers\admin_permissions_primitives_access.py:16` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_permissions_validation.py:16` — circuit bypass: routers -> services (services) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_detection.py:1` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_detection.py:8` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*
- 🟡 **CIR2** `backend\routers\admin_security_health.py:4` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_operations.py:1` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_operations.py:6` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*
- 🟡 **CIR2** `backend\routers\admin_security_registration.py:15` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*
- 🟡 **CIR2** `backend\routers\admin_security_registration.py:4` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\public_security_registration.py:25` — circuit bypass: routers -> services (services.db_write) → *routers should call controllers; direct router -> service usage skips the orchestration layer*

### QUAL1 (8)

- 🟡 **QUAL1** `backend\controllers\auth_controller.py` — 4 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 280, 295, 762, 775) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\dependencies\fraud_events.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 43) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\middleware\impossible_travel_middleware.py` — 6 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 108, 121, 133, 141, 148, 153) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\routers\admin_security_registration.py` — 2 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 59, 172) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\routers\public_security_registration.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 136) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\services\effective_permissions.py` — 4 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 162, 173, 189, 205) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\services\fraud_detection_service.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 753) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL1** `backend\utils\auth.py` — 9 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 92, 110, 131, 154, 175, 225, 236, 254, 265) → *log or re-raise; silent swallowing hides bugs*

### API101 (7)

- 🟡 **API101** `backend\routers\admin_permissions_validation.py` — endpoint(s) missing response_model: list_categories, create_category, update_category, delete_category, list_permissions, create_permission → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\admin_security_detection.py` — endpoint(s) missing response_model: remove_from_blacklist, assign_review, resolve_review, update_threat_feeds → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\admin_security_health.py` — endpoint(s) missing response_model: get_risk_score, ghost_employees, impossible_travel, update_risk, team_health, audit_timeline → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\admin_security_registration.py` — endpoint(s) missing response_model: csrf_token, logout → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\admin_security_validation.py` — endpoint(s) missing response_model: create_card, enroll_bio, validate_geo, log_geo, get_qr, qr_login → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\public_security_registration.py` — endpoint(s) missing response_model: csrf_token, logout → *add response_model for type safety and docs*
- 🟡 **API101** `backend\routers\supplier_security.py` — endpoint(s) missing response_model: list_public_suppliers, resolve_public_supplier_slug, get_public_supplier, get_supplier_products_public → *add response_model for type safety and docs*

### HL801 (7)

- 🟡 **HL801** `backend\controllers\auth_controller.py` — function(s) need timing/metrics: _user_public_payload (calls=28), get_current_user (calls=44), get_optional_user (calls=40), handle_google_oauth_callback (calls=25), handle_facebook_oauth_callback (calls=25), register_user (calls=75) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\controllers\security\admin_users.py` — function(s) need timing/metrics: delete_user_admin (calls=30) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\middleware\csrf_middleware.py` — function(s) need timing/metrics: dispatch (calls=25) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\routers\admin_security_registration.py` — function(s) need timing/metrics: login (calls=34), register (calls=36), refresh (calls=34) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\services\auth_service.py` — function(s) need timing/metrics: authenticate_kiosk_qr (calls=43), authenticate_sso (calls=30) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\services\fraud_detection_service.py` — function(s) need timing/metrics: check_ip_reputation (calls=31), calculate_score (calls=69) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **HL801** `backend\services\ghost_watchdog.py` — function(s) need timing/metrics: find_ghost_employees (calls=39) → *add timing decorator / Prometheus histogram / duration_ms logs*

### W4 (4)

- 🟡 **W4** `backend\controllers\auth_controller.py:143` — controller imports another controller ('controllers.admin_controller') → *extract shared logic into a service or util; controllers stay thin*
- 🟡 **W4** `backend\controllers\permissions\permissions.py:21` — controller imports another controller ('controllers.analytics.analytics') → *extract shared logic into a service or util; controllers stay thin*
- 🟡 **W4** `backend\controllers\security\admin_auth.py:11` — controller imports another controller ('controllers.auth_controller') → *extract shared logic into a service or util; controllers stay thin*
- 🟡 **W4** `backend\controllers\security\admin_users.py:17` — controller imports another controller ('controllers.customer.users') → *extract shared logic into a service or util; controllers stay thin*

### CA2 (4)

- 🟡 **CA2** `backend\controllers\auth_controller.py` — file contains signals for 7 domains: identity(36), commerce(9), customer(8), catalog(5), security(4), comms(4), media(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*
- 🟡 **CA2** `backend\services\auth_write_service.py` — file contains signals for 5 domains: identity(26), comms(6), customer(5), catalog(5), commerce(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*
- 🟡 **CA2** `backend\services\effective_permissions.py` — file contains signals for 3 domains: permissions(7), security(6), identity(4) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*
- 🟡 **CA2** `backend\services\permission_service.py` — file contains signals for 4 domains: security(6), identity(5), catalog(4), permissions(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*

### HL204 (3)

- 🟡 **HL204** `backend\controllers\auth_controller.py` — possible secret in log (lines: 431, 848) → *never log secrets; log only IDs/status*
- 🟡 **HL204** `backend\routers\admin_security_registration.py` — possible secret in log (lines: 104) → *never log secrets; log only IDs/status*
- 🟡 **HL204** `backend\utils\auth.py` — possible secret in log (lines: 97, 100) → *never log secrets; log only IDs/status*

### HL101 (3)

- 🟡 **HL101** `backend\controllers\auth_controller.py` — oversized file (1021 lines) → *split by responsibility/domain*
- 🟡 **HL101** `backend\services\auth_service.py` — oversized file (1114 lines) → *split by responsibility/domain*
- 🟡 **HL101** `backend\services\fraud_detection_service.py` — oversized file (1097 lines) → *split by responsibility/domain*

### SEC5 (3)

- 🔴 **SEC5** `backend\services\fraud_detection_service.py:944` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*
- 🔴 **SEC5** `backend\services\permission_service.py:77` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*
- 🔴 **SEC5** `backend\services\permission_service.py:85` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*

### CIR1 (2)

- 🔴 **CIR1** `backend\routers\admin_security_registration.py:22` — circuit violation: routers -> middleware (middleware.csrf_middleware) is outside the allowed circuit → *routers may import only: controllers, data, db, dependencies, events, utils*
- 🔴 **CIR1** `backend\utils\security_audit.py:8` — circuit violation: utils -> db (db.models) is outside the allowed circuit → *utils may import only: none*

### A2 (2)

- 🟡 **A2** `backend\services\auth_service.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **A2** `backend\services\security\impossible_travel_write_service.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*

### A1 (2)

- 🟡 **A1** `backend\controllers\auth_controller.py` — architecture hotspot: fan_in=63, fan_out=17, instability=0.21 → *reduce coupling; split responsibilities or introduce an abstraction layer*
- 🟡 **A1** `backend\utils\auth.py` — architecture hotspot: fan_in=37, fan_out=1, instability=0.03 → *reduce coupling; split responsibilities or introduce an abstraction layer*

### QUAL3 (2)

- 🟡 **QUAL3** `backend\services\auth_service.py:657` — oversized function 'authenticate_kiosk_qr' (132 lines) → *extract smaller functions / service methods; long functions hide side effects*
- 🟡 **QUAL3** `backend\services\fraud_detection_service.py:430` — oversized function 'calculate_score' (149 lines) → *extract smaller functions / service methods; long functions hide side effects*

### DBA32 (2)

- 🟡 **DBA32** `backend\routers\admin_security_detection.py:39` — OFFSET pagination on hot table detected → *use cursor-based (keyset) pagination for hot lists*
- 🟡 **DBA32** `backend\routers\supplier_security.py:25` — OFFSET pagination on hot table detected → *use cursor-based (keyset) pagination for hot lists*

### DBA11 (2)

- 🟡 **DBA11** `backend\models\fraud.py:48` — table 'fraud_blacklist': should be plural → *snake_case plural table names*
- 🟡 **DBA11** `backend\models\fraud.py:85` — table 'manual_review_queue': should be plural → *snake_case plural table names*

### HL102 (2)

- 🟡 **HL102** `backend\services\auth_service.py` — oversized function(s): authenticate_biometric (87L), authenticate_kiosk_qr (132L), authenticate_sso (86L), _issue_session (114L) → *extract smaller functions*
- 🟡 **HL102** `backend\services\fraud_detection_service.py` — oversized function(s): calculate_score (149L) → *extract smaller functions*

### R1 (1)

- 🔴 **R1** `backend\controllers\iam_controller.py:18` — APIRouter outside routers/ -> endpoint mis-registered/shadowed → *backend/routers/*

### DG (1)

- 🔴 **DG** `backend\dependencies\fraud_events.py:11` — forbidden dependency edge: dependencies -> services → *layer contract: dependencies may not depend on services; route via services/*

### W3 (1)

- 🔴 **W3** `backend\services\effective_permissions.py:516` — imports controller 'controllers.auth_controller' from services (controller logic belongs in services/utils) → *move the imported logic to services/<domain>/ or utils/*

### CG2 (1)

- 🔴 **CG2** `backend\routers\admin_security_registration.py:154` — upward call: routers.csrf_token() → middleware.generate_csrf_token() → *calls must flow downward in the circuit; extract shared logic to a lower layer*

### QUAL2 (1)

- 🟡 **QUAL2** `backend\services\auth_service.py` — technical debt markers present (3 TODO/FIXME/XXX/HACK) → *convert important markers into tasks/ADRs; delete stale ones*

### MET2 (1)

- 🟡 **MET2** `backend\routers\admin_security_registration.py` — high instability: I=1.00 (Ca=0, Ce=11) → *module is very fragile; add abstractions or reduce outgoing dependencies*

### PERF2 (1)

- 🟡 **PERF2** `backend\services\effective_permissions.py` — 1 possible DB query inside loop (N+1 risk); batch queries / use joins / preload relationships (lines: 277) → *batch the query / use joins / preload relationships instead of querying per item*

### HL601 (1)

- 🟡 **HL601** `backend\controllers\auth_controller.py` — sequential external calls: handle_google_oauth_callback (2 calls), handle_facebook_oauth_callback (2 calls) → *use asyncio.gather or ThreadPoolExecutor; add timeout + retry*

### HL303 (1)

- 🟡 **HL303** `backend\utils\security_audit.py` — broad except Exception (lines: 87) → *narrow exception types; always log with context*

### MR104 (1)

- 🟡 **MR104** `backend\controllers\permissions\permissions.py` — global mutable state: STAFF_PERMISSION_GROUPS → *use dependency injection / singleton*

### Q1 (1)

- 🟡 **Q1** `backend\middleware\impossible_travel_middleware.py` — 5 DB read(s) via .query() in this file; delegate reads to a service (lines: 184, 205, 211, 220, 224) → *delegate DB reads to services/<domain>/; routers/controllers should call service methods*

### PG102 (1)

- 🟡 **PG102** `backend\services\fraud_detection_service.py` — WebSocket handler in Python: fraud_detection_service → *Python for business logic; Node.js gateway for high-throughput real-time*

### PG103 (1)

- 🟡 **PG103** `backend\routers\admin_security_detection.py` — CPU-bound in request path: list_fraud_events → *offload to worker (Celery/arq) or Node.js worker thread*

### HL502 (1)

- 🟡 **HL502** `backend\models\security\__init__.py` — star import at lines: 13, 14 → *use explicit imports*

### RN1 (1)

- 🟡 **RN1** `backend\routers\auth.py` — flat router filename 'auth.py' is not comprehensive; missing surface, operation → *rename to {surface}_{domain}_{operation}.py, e.g. admin_orders_management.py, supplier_orders_fulfillment.py, customer_orders_tracking.py*

### SC101 (1)

- 🟡 **SC101** `backend\routers\admin_security_detection.py` — list endpoint(s) missing pagination: list_blacklist, list_rules, list_review_queue → *add skip/limit or cursor pagination*

### SC501 (1)

- 🟡 **SC501** `backend\routers\admin_security_detection.py` — heavy operation in request path: list_fraud_events → *offload to background job; return 202 Accepted*

### SYM1 (1)

- 🟡 **SYM1** `backend\services\triple_auth.py:78` — symbol 'BiometricValidator' (class) defined but never referenced outside its module → *verify usage; delete if dead code*

### SEC6 (1)

- 🟡 **SEC6** `backend\services\fraud_detection_service.py:925` — potential SSRF: URL from variable used in HTTP request → *validate/whitelist URLs before making requests*

## By file

### `backend\models\fraud.py` (22 findings, 0 RED)

- 🟡 **DBA03** `backend\models\fraud.py:105` — model 'IPReputation' table 'ip_reputations' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:128` — model 'DeviceFingerprint' table 'device_fingerprints' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:148` — model 'CreditCardBin' table 'credit_card_bins' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:160` — model 'ReturnAbusePattern' table 'return_abuse_patterns' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:16` — model 'FraudEvent' table 'fraud_events' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:174` — model 'SupplierFraudIndicator' table 'supplier_fraud_indicators' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:189` — model 'LogisticsFraudIndicator' table 'logistics_fraud_indicators' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:204` — model 'FraudAlert' table 'fraud_alerts' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:224` — model 'IPAccountLinkage' table 'ip_account_linkages' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:239` — model 'VelocityCounter' table 'fraud_velocity_counters' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:253` — model 'FraudScoringLog' table 'fraud_scoring_logs' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:281` — model 'FraudCase' table 'fraud_cases' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:311` — model 'FraudCaseAssignment' table 'fraud_case_assignments' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:328` — model 'DLPViolation' table 'dlp_violations' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:350` — model 'MeetingTranscript' table 'meeting_transcripts' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:365` — model 'MeetingActionItem' table 'meeting_action_items' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:384` — model 'MeetingRecording' table 'meeting_recordings' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:48` — model 'FraudBlacklist' table 'fraud_blacklist' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:64` — model 'FraudRule' table 'fraud_rules' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\fraud.py:85` — model 'ManualReviewQueue' table 'manual_review_queue' missing: uuid, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA11** `backend\models\fraud.py:48` — table 'fraud_blacklist': should be plural → *snake_case plural table names*
- 🟡 **DBA11** `backend\models\fraud.py:85` — table 'manual_review_queue': should be plural → *snake_case plural table names*

### `backend\routers\admin_security_registration.py` (19 findings, 11 RED)

- 🔴 **CG1** `backend\routers\admin_security_registration.py:105` — forbidden call: routers.register() → models.User() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:112` — forbidden call: routers.register() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:112` — forbidden call: routers.register() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:143` — forbidden call: routers.refresh() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:143` — forbidden call: routers.refresh() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:52` — forbidden call: routers._record_login_history() → models.UserLoginHistory() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:82` — forbidden call: routers.login() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:82` — forbidden call: routers.login() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_registration.py:99` — forbidden call: routers.register() → db._validate_password_complexity() → *routers must not call db directly*
- 🔴 **CG2** `backend\routers\admin_security_registration.py:154` — upward call: routers.csrf_token() → middleware.generate_csrf_token() → *calls must flow downward in the circuit; extract shared logic to a lower layer*
- 🔴 **CIR1** `backend\routers\admin_security_registration.py:22` — circuit violation: routers -> middleware (middleware.csrf_middleware) is outside the allowed circuit → *routers may import only: controllers, data, db, dependencies, events, utils*
- 🟡 **API101** `backend\routers\admin_security_registration.py` — endpoint(s) missing response_model: csrf_token, logout → *add response_model for type safety and docs*
- 🟡 **CIR2** `backend\routers\admin_security_registration.py:15` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*
- 🟡 **CIR2** `backend\routers\admin_security_registration.py:4` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **HL204** `backend\routers\admin_security_registration.py` — possible secret in log (lines: 104) → *never log secrets; log only IDs/status*
- 🟡 **HL302** `backend\routers\admin_security_registration.py` — swallowed exception (lines: 113, 133, 100, 172, 59) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL801** `backend\routers\admin_security_registration.py` — function(s) need timing/metrics: login (calls=34), register (calls=36), refresh (calls=34) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **MET2** `backend\routers\admin_security_registration.py` — high instability: I=1.00 (Ca=0, Ce=11) → *module is very fragile; add abstractions or reduce outgoing dependencies*
- 🟡 **QUAL1** `backend\routers\admin_security_registration.py` — 2 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 59, 172) → *log or re-raise; silent swallowing hides bugs*

### `backend\controllers\auth_controller.py` (12 findings, 3 RED)

- 🔴 **CG1** `backend\controllers\auth_controller.py:163` — forbidden call: controllers._serialize_referral_event() → db.ReferralPointEventSchema() → *controllers must not call db directly*
- 🔴 **CG1** `backend\controllers\auth_controller.py:556` — forbidden call: controllers.register_user() → db.model_validate() → *controllers must not call db directly*
- 🔴 **CG1** `backend\controllers\auth_controller.py:719` — forbidden call: controllers.get_referral_dashboard() → db.ReferralDashboardSchema() → *controllers must not call db directly*
- 🟡 **A1** `backend\controllers\auth_controller.py` — architecture hotspot: fan_in=63, fan_out=17, instability=0.21 → *reduce coupling; split responsibilities or introduce an abstraction layer*
- 🟡 **CA2** `backend\controllers\auth_controller.py` — file contains signals for 7 domains: identity(36), commerce(9), customer(8), catalog(5), security(4), comms(4), media(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*
- 🟡 **HL101** `backend\controllers\auth_controller.py` — oversized file (1021 lines) → *split by responsibility/domain*
- 🟡 **HL204** `backend\controllers\auth_controller.py` — possible secret in log (lines: 431, 848) → *never log secrets; log only IDs/status*
- 🟡 **HL302** `backend\controllers\auth_controller.py` — swallowed exception (lines: 112, 223, 251, 461, 495, 670 +5 more) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL601** `backend\controllers\auth_controller.py` — sequential external calls: handle_google_oauth_callback (2 calls), handle_facebook_oauth_callback (2 calls) → *use asyncio.gather or ThreadPoolExecutor; add timeout + retry*
- 🟡 **HL801** `backend\controllers\auth_controller.py` — function(s) need timing/metrics: _user_public_payload (calls=28), get_current_user (calls=44), get_optional_user (calls=40), handle_google_oauth_callback (calls=25), handle_facebook_oauth_callback (calls=25), register_user (calls=75) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **QUAL1** `backend\controllers\auth_controller.py` — 4 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 280, 295, 762, 775) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **W4** `backend\controllers\auth_controller.py:143` — controller imports another controller ('controllers.admin_controller') → *extract shared logic into a service or util; controllers stay thin*

### `backend\routers\admin_security_detection.py` (12 findings, 4 RED)

- 🔴 **CG1** `backend\routers\admin_security_detection.py:148` — forbidden call: routers.get_threat_feed_status() → db.ThreatFeedStatus() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:42` — forbidden call: routers.list_fraud_events() → db.FraudEventOut() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:62` — forbidden call: routers.add_to_blacklist() → models.FraudBlacklist() → *routers must not call models directly*
- 🔴 **CG1** `backend\routers\admin_security_detection.py:85` — forbidden call: routers.create_rule() → models.FraudRule() → *routers must not call models directly*
- 🟡 **API101** `backend\routers\admin_security_detection.py` — endpoint(s) missing response_model: remove_from_blacklist, assign_review, resolve_review, update_threat_feeds → *add response_model for type safety and docs*
- 🟡 **CIR2** `backend\routers\admin_security_detection.py:1` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_detection.py:8` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*
- 🟡 **DBA32** `backend\routers\admin_security_detection.py:39` — OFFSET pagination on hot table detected → *use cursor-based (keyset) pagination for hot lists*
- 🟡 **HL302** `backend\routers\admin_security_detection.py` — swallowed exception (lines: 192) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **PG103** `backend\routers\admin_security_detection.py` — CPU-bound in request path: list_fraud_events → *offload to worker (Celery/arq) or Node.js worker thread*
- 🟡 **SC101** `backend\routers\admin_security_detection.py` — list endpoint(s) missing pagination: list_blacklist, list_rules, list_review_queue → *add skip/limit or cursor pagination*
- 🟡 **SC501** `backend\routers\admin_security_detection.py` — heavy operation in request path: list_fraud_events → *offload to background job; return 202 Accepted*

### `backend\services\fraud_detection_service.py` (12 findings, 1 RED)

- 🔴 **SEC5** `backend\services\fraud_detection_service.py:944` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*
- 🟡 **HL101** `backend\services\fraud_detection_service.py` — oversized file (1097 lines) → *split by responsibility/domain*
- 🟡 **HL102** `backend\services\fraud_detection_service.py` — oversized function(s): calculate_score (149L) → *extract smaller functions*
- 🟡 **HL302** `backend\services\fraud_detection_service.py` — swallowed exception (lines: 124, 140, 643, 48, 753, 1014 +5 more) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL801** `backend\services\fraud_detection_service.py` — function(s) need timing/metrics: check_ip_reputation (calls=31), calculate_score (calls=69) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:1052` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:1083` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection_service.py:289` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PG102** `backend\services\fraud_detection_service.py` — WebSocket handler in Python: fraud_detection_service → *Python for business logic; Node.js gateway for high-throughput real-time*
- 🟡 **QUAL1** `backend\services\fraud_detection_service.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 753) → *log or re-raise; silent swallowing hides bugs*
- 🟡 **QUAL3** `backend\services\fraud_detection_service.py:430` — oversized function 'calculate_score' (149 lines) → *extract smaller functions / service methods; long functions hide side effects*
- 🟡 **SEC6** `backend\services\fraud_detection_service.py:925` — potential SSRF: URL from variable used in HTTP request → *validate/whitelist URLs before making requests*

### `backend\routers\public_security_registration.py` (8 findings, 4 RED)

- 🔴 **CG1** `backend\routers\public_security_registration.py:107` — forbidden call: routers.refresh() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:43` — forbidden call: routers._issue_tokens() → db.model_validate() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:70` — forbidden call: routers.login() → db.TokenResponse() → *routers must not call db directly*
- 🔴 **CG1** `backend\routers\public_security_registration.py:85` — forbidden call: routers.register() → db.TokenResponse() → *routers must not call db directly*
- 🟡 **API101** `backend\routers\public_security_registration.py` — endpoint(s) missing response_model: csrf_token, logout → *add response_model for type safety and docs*
- 🟡 **CIR2** `backend\routers\public_security_registration.py:25` — circuit bypass: routers -> services (services.db_write) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **HL302** `backend\routers\public_security_registration.py` — swallowed exception (lines: 79, 98, 136) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **QUAL1** `backend\routers\public_security_registration.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 136) → *log or re-raise; silent swallowing hides bugs*

### `backend\services\effective_permissions.py` (7 findings, 1 RED)

- 🔴 **W3** `backend\services\effective_permissions.py:516` — imports controller 'controllers.auth_controller' from services (controller logic belongs in services/utils) → *move the imported logic to services/<domain>/ or utils/*
- 🟡 **CA2** `backend\services\effective_permissions.py` — file contains signals for 3 domains: permissions(7), security(6), identity(4) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*
- 🟡 **HL302** `backend\services\effective_permissions.py` — swallowed exception (lines: 146, 162, 173, 189, 205) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **PERF2** `backend\services\effective_permissions.py` — 1 possible DB query inside loop (N+1 risk); batch queries / use joins / preload relationships (lines: 277) → *batch the query / use joins / preload relationships instead of querying per item*
- 🟡 **PERF4** `backend\services\effective_permissions.py:200` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\effective_permissions.py:272` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **QUAL1** `backend\services\effective_permissions.py` — 4 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 162, 173, 189, 205) → *log or re-raise; silent swallowing hides bugs*

### `backend\services\auth_service.py` (7 findings, 0 RED)

- 🟡 **A2** `backend\services\auth_service.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **HL101** `backend\services\auth_service.py` — oversized file (1114 lines) → *split by responsibility/domain*
- 🟡 **HL102** `backend\services\auth_service.py` — oversized function(s): authenticate_biometric (87L), authenticate_kiosk_qr (132L), authenticate_sso (86L), _issue_session (114L) → *extract smaller functions*
- 🟡 **HL302** `backend\services\auth_service.py` — swallowed exception (lines: 76, 600, 827, 239) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **HL801** `backend\services\auth_service.py` — function(s) need timing/metrics: authenticate_kiosk_qr (calls=43), authenticate_sso (calls=30) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **QUAL2** `backend\services\auth_service.py` — technical debt markers present (3 TODO/FIXME/XXX/HACK) → *convert important markers into tasks/ADRs; delete stale ones*
- 🟡 **QUAL3** `backend\services\auth_service.py:657` — oversized function 'authenticate_kiosk_qr' (132 lines) → *extract smaller functions / service methods; long functions hide side effects*

### `backend\services\ghost_watchdog.py` (5 findings, 0 RED)

- 🟡 **HL801** `backend\services\ghost_watchdog.py` — function(s) need timing/metrics: find_ghost_employees (calls=39) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:39` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:48` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:63` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\ghost_watchdog.py:76` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*

### `backend\utils\auth.py` (4 findings, 0 RED)

- 🟡 **A1** `backend\utils\auth.py` — architecture hotspot: fan_in=37, fan_out=1, instability=0.03 → *reduce coupling; split responsibilities or introduce an abstraction layer*
- 🟡 **HL204** `backend\utils\auth.py` — possible secret in log (lines: 97, 100) → *never log secrets; log only IDs/status*
- 🟡 **HL302** `backend\utils\auth.py` — swallowed exception (lines: 65, 183, 291, 322, 360, 37 +10 more) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **QUAL1** `backend\utils\auth.py` — 9 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 92, 110, 131, 154, 175, 225, 236, 254, 265) → *log or re-raise; silent swallowing hides bugs*

### `backend\models\incident.py` (4 findings, 0 RED)

- 🟡 **DBA03** `backend\models\incident.py:11` — model 'IncidentWarRoom' table 'incident_war_rooms' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:29` — model 'IncidentThread' table 'incident_threads' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:41` — model 'IncidentActionItem' table 'incident_action_items' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*
- 🟡 **DBA03** `backend\models\incident.py:58` — model 'WarRoomTemplate' table 'war_room_templates' missing: uuid, created_at/updated_at, soft-delete, version, created_by/updated_by → *use AuditMixin + SoftDeleteMixin + TenantMixin*

### `backend\services\fraud_detection.py` (4 findings, 0 RED)

- 🟡 **PERF4** `backend\services\fraud_detection.py:103` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:118` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:162` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_detection.py:84` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*

### `backend\dependencies\fraud_events.py` (3 findings, 1 RED)

- 🔴 **DG** `backend\dependencies\fraud_events.py:11` — forbidden dependency edge: dependencies -> services → *layer contract: dependencies may not depend on services; route via services/*
- 🟡 **HL302** `backend\dependencies\fraud_events.py` — swallowed exception (lines: 43) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **QUAL1** `backend\dependencies\fraud_events.py` — 1 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 43) → *log or re-raise; silent swallowing hides bugs*

### `backend\middleware\impossible_travel_middleware.py` (3 findings, 0 RED)

- 🟡 **HL302** `backend\middleware\impossible_travel_middleware.py` — swallowed exception (lines: 108, 121, 133, 141, 148, 153) → *log with logger.exception(...); re-raise or return controlled error*
- 🟡 **Q1** `backend\middleware\impossible_travel_middleware.py` — 5 DB read(s) via .query() in this file; delegate reads to a service (lines: 184, 205, 211, 220, 224) → *delegate DB reads to services/<domain>/; routers/controllers should call service methods*
- 🟡 **QUAL1** `backend\middleware\impossible_travel_middleware.py` — 6 weak exception handling location(s); log or re-raise instead of swallowing exceptions (lines: 108, 121, 133, 141, 148, 153) → *log or re-raise; silent swallowing hides bugs*

### `backend\services\permission_service.py` (3 findings, 2 RED)

- 🔴 **SEC5** `backend\services\permission_service.py:77` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*
- 🔴 **SEC5** `backend\services\permission_service.py:85` — potential SQL injection: string interpolation in SQL query without visible parameterization → *use parameterized queries or SQLAlchemy ORM; never interpolate user input into SQL*
- 🟡 **CA2** `backend\services\permission_service.py` — file contains signals for 4 domains: security(6), identity(5), catalog(4), permissions(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*

### `backend\services\fraud_admin_service.py` (3 findings, 0 RED)

- 🟡 **PERF4** `backend\services\fraud_admin_service.py:116` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_admin_service.py:150` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
- 🟡 **PERF4** `backend\services\fraud_admin_service.py:80` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*

### `backend\controllers\iam_controller.py` (2 findings, 1 RED)

- 🔴 **R1** `backend\controllers\iam_controller.py:18` — APIRouter outside routers/ -> endpoint mis-registered/shadowed → *backend/routers/*
- 🟡 **HL302** `backend\controllers\iam_controller.py` — swallowed exception (lines: 69) → *log with logger.exception(...); re-raise or return controlled error*

### `backend\controllers\permissions\permissions.py` (2 findings, 0 RED)

- 🟡 **MR104** `backend\controllers\permissions\permissions.py` — global mutable state: STAFF_PERMISSION_GROUPS → *use dependency injection / singleton*
- 🟡 **W4** `backend\controllers\permissions\permissions.py:21` — controller imports another controller ('controllers.analytics.analytics') → *extract shared logic into a service or util; controllers stay thin*

### `backend\controllers\security\admin_users.py` (2 findings, 0 RED)

- 🟡 **HL801** `backend\controllers\security\admin_users.py` — function(s) need timing/metrics: delete_user_admin (calls=30) → *add timing decorator / Prometheus histogram / duration_ms logs*
- 🟡 **W4** `backend\controllers\security\admin_users.py:17` — controller imports another controller ('controllers.customer.users') → *extract shared logic into a service or util; controllers stay thin*

### `backend\routers\admin_permissions_validation.py` (2 findings, 0 RED)

- 🟡 **API101** `backend\routers\admin_permissions_validation.py` — endpoint(s) missing response_model: list_categories, create_category, update_category, delete_category, list_permissions, create_permission → *add response_model for type safety and docs*
- 🟡 **CIR2** `backend\routers\admin_permissions_validation.py:16` — circuit bypass: routers -> services (services) → *routers should call controllers; direct router -> service usage skips the orchestration layer*

### `backend\routers\admin_security_health.py` (2 findings, 0 RED)

- 🟡 **API101** `backend\routers\admin_security_health.py` — endpoint(s) missing response_model: get_risk_score, ghost_employees, impossible_travel, update_risk, team_health, audit_timeline → *add response_model for type safety and docs*
- 🟡 **CIR2** `backend\routers\admin_security_health.py:4` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*

### `backend\routers\admin_security_operations.py` (2 findings, 0 RED)

- 🟡 **CIR2** `backend\routers\admin_security_operations.py:1` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*
- 🟡 **CIR2** `backend\routers\admin_security_operations.py:6` — circuit bypass: routers -> models (models) → *routers should not read models directly; use controllers/services*

### `backend\utils\security_audit.py` (2 findings, 1 RED)

- 🔴 **CIR1** `backend\utils\security_audit.py:8` — circuit violation: utils -> db (db.models) is outside the allowed circuit → *utils may import only: none*
- 🟡 **HL303** `backend\utils\security_audit.py` — broad except Exception (lines: 87) → *narrow exception types; always log with context*

### `backend\routers\supplier_security.py` (2 findings, 0 RED)

- 🟡 **API101** `backend\routers\supplier_security.py` — endpoint(s) missing response_model: list_public_suppliers, resolve_public_supplier_slug, get_public_supplier, get_supplier_products_public → *add response_model for type safety and docs*
- 🟡 **DBA32** `backend\routers\supplier_security.py:25` — OFFSET pagination on hot table detected → *use cursor-based (keyset) pagination for hot lists*

### `backend\controllers\security\admin_auth.py` (1 findings, 0 RED)

- 🟡 **W4** `backend\controllers\security\admin_auth.py:11` — controller imports another controller ('controllers.auth_controller') → *extract shared logic into a service or util; controllers stay thin*

### `backend\routers\admin_permissions_primitives_access.py` (1 findings, 0 RED)

- 🟡 **CIR2** `backend\routers\admin_permissions_primitives_access.py:16` — circuit bypass: routers -> services (services.db_read) → *routers should call controllers; direct router -> service usage skips the orchestration layer*

### `backend\services\security\impossible_travel_write_service.py` (1 findings, 0 RED)

- 🟡 **A2** `backend\services\security\impossible_travel_write_service.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*

### `backend\routers\admin_security_validation.py` (1 findings, 0 RED)

- 🟡 **API101** `backend\routers\admin_security_validation.py` — endpoint(s) missing response_model: create_card, enroll_bio, validate_geo, log_geo, get_qr, qr_login → *add response_model for type safety and docs*

### `backend\middleware\csrf_middleware.py` (1 findings, 0 RED)

- 🟡 **HL801** `backend\middleware\csrf_middleware.py` — function(s) need timing/metrics: dispatch (calls=25) → *add timing decorator / Prometheus histogram / duration_ms logs*

### `backend\models\security\__init__.py` (1 findings, 0 RED)

- 🟡 **HL502** `backend\models\security\__init__.py` — star import at lines: 13, 14 → *use explicit imports*

### `backend\routers\auth.py` (1 findings, 0 RED)

- 🟡 **RN1** `backend\routers\auth.py` — flat router filename 'auth.py' is not comprehensive; missing surface, operation → *rename to {surface}_{domain}_{operation}.py, e.g. admin_orders_management.py, supplier_orders_fulfillment.py, customer_orders_tracking.py*

### `backend\services\triple_auth.py` (1 findings, 0 RED)

- 🟡 **SYM1** `backend\services\triple_auth.py:78` — symbol 'BiometricValidator' (class) defined but never referenced outside its module → *verify usage; delete if dead code*

### `backend\services\auth_write_service.py` (1 findings, 0 RED)

- 🟡 **CA2** `backend\services\auth_write_service.py` — file contains signals for 5 domains: identity(26), comms(6), customer(5), catalog(5), commerce(3) — consider splitting if sub-domains are independently reusable → *split only if a sub-domain is independently reusable; multi-domain orchestration services are normal*

### `backend\services\fraud_service.py` (1 findings, 0 RED)

- 🟡 **PERF4** `backend\services\fraud_service.py:66` — unbounded query: .all() without .limit() → *add .limit() to prevent loading entire tables into memory*
