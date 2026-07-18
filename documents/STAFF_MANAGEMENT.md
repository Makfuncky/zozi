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
