"""Employee workspace service — role-based workspace configuration."""
from __future__ import annotations
import logging
from typing import Optional

from sqlalchemy.orm import Session

from domains.hr.models.employee_models import (
    EmployeeRoleAssignment,
)

logger = logging.getLogger(__name__)

# Default features per role
ROLE_FEATURES = {
    "moderator": ["review_queue", "content_queue", "user_reports", "activity_log"],
    "supplier_coordinator": ["supplier_issues", "purchase_orders", "supplier_chat", "performance"],
    "customer_coordinator": ["ticket_queue", "customer_chat", "returns_queue", "satisfaction"],
    "promotion_manager": ["campaign_builder", "banner_manager", "deal_manager", "calendar", "analytics"],
    "order_fulfillment": ["order_queue", "picking_list", "packing_station", "shipping_queue", "inventory_alerts"],
    "delivery_coordinator": ["route_planner", "live_tracking", "pod_verification", "failed_deliveries"],
    "finance_clerk": ["invoice_queue", "payment_queue", "reconciliation", "reports", "audit_trail"],
    "hr_coordinator": ["employee_records", "onboarding_queue", "leave_approval", "attendance_issues"],
    "data_entry": ["product_queue", "bulk_import", "quality_check"],
    "quality_analyst": ["inspection_queue", "complaint_queue", "reports", "supplier_scorecard"],
    "social_media": ["post_calendar", "content_queue", "engagement", "analytics"],
    "inventory_manager": ["stock_levels", "reorder_queue", "warehouse_transfers", "stock_count"],
    "returns_processor": ["return_queue", "refund_queue", "exchange_queue", "quality_check"],
    "content_writer": ["writing_queue", "seo_queue", "blog_queue", "review_queue"],
    "photography_editor": ["image_queue", "retouch_queue", "upload_queue", "gallery"],
    "accounts_payable": ["invoice_queue", "payment_schedule", "approval_queue", "payment_history"],
    "accounts_receivable": ["outstanding_invoices", "followup_queue", "payment_receipts", "aging_report"],
}

# Default widgets per role
ROLE_WIDGETS = {
    "moderator": ["pending_reviews", "recent_moderation", "flagged_content"],
    "supplier_coordinator": ["open_issues", "pending_orders", "supplier_rating"],
    "customer_coordinator": ["open_tickets", "response_time", "satisfaction_score"],
    "promotion_manager": ["active_campaigns", "upcoming_promos", "performance"],
    "order_fulfillment": ["orders_today", "pending_picks", "shipping_status"],
    "delivery_coordinator": ["active_routes", "pending_deliveries", "failed_deliveries"],
    "finance_clerk": ["pending_invoices", "payment_status", "reconciliation_status"],
    "hr_coordinator": ["pending_leave", "onboarding_tasks", "employee_count"],
    "data_entry": ["products_pending", "import_queue", "quality_score"],
    "quality_analyst": ["inspection_pending", "complaints_today", "quality_score"],
    "social_media": ["scheduled_posts", "engagement_rate", "followers_growth"],
    "inventory_manager": ["low_stock_alerts", "pending_reorders", "warehouse_capacity"],
    "returns_processor": ["pending_returns", "refund_queue", "exchange_queue"],
    "content_writer": ["writing_queue", "seo_tasks", "published_content"],
    "photography_editor": ["images_pending", "recent_edits", "upload_queue"],
    "accounts_payable": ["pending_invoices", "upcoming_payments", "paid_today"],
    "accounts_receivable": ["outstanding_amount", "overdue_invoices", "collected_today"],
}


class EmployeeWorkspaceService:
    """Service for managing employee workspace based on roles."""

    def __init__(self, db: Session):
        self.db = db

    def get_employee_roles(self, employee_id: int) -> list[str]:
        """Get all roles assigned to an employee."""
        assignments = self.db.query(EmployeeRoleAssignment).filter(
            EmployeeRoleAssignment.employee_id == employee_id,
            EmployeeRoleAssignment.is_active.is_(True),
            EmployeeRoleAssignment.is_deleted.is_(False),
        ).all()
        return [a.role for a in assignments]

    def get_primary_role(self, employee_id: int) -> Optional[str]:
        """Get the primary role of an employee."""
        assignment = self.db.query(EmployeeRoleAssignment).filter(
            EmployeeRoleAssignment.employee_id == employee_id,
            EmployeeRoleAssignment.is_primary.is_(True),
            EmployeeRoleAssignment.is_active.is_(True),
            EmployeeRoleAssignment.is_deleted.is_(False),
        ).first()
        return assignment.role if assignment else None

    def get_workspace_config(self, employee_id: int) -> dict:
        """Get workspace configuration for an employee."""
        roles = self.get_employee_roles(employee_id)
        if not roles:
            return self._get_default_workspace()

        primary_role = self.get_primary_role(employee_id) or roles[0]
        features = ROLE_FEATURES.get(primary_role, [])
        widgets = ROLE_WIDGETS.get(primary_role, [])

        # Merge features from all roles
        for role in roles:
            if role != primary_role:
                features.extend(ROLE_FEATURES.get(role, []))
        features = list(set(features))  # Deduplicate

        return {
            "role": primary_role,
            "all_roles": roles,
            "features": features,
            "widgets": widgets,
            "primary_role": primary_role,
        }

    def get_work_queue(self, employee_id: int) -> dict:
        """Get work queue for an employee based on their role."""
        roles = self.get_employee_roles(employee_id)
        queue = {}

        for role in roles:
            if role == "customer_coordinator":
                queue["tickets"] = {"count": 0, "label": "Open Tickets"}
            elif role == "supplier_coordinator":
                queue["supplier_issues"] = {"count": 0, "label": "Supplier Issues"}
            elif role == "moderator":
                queue["reviews"] = {"count": 0, "label": "Pending Reviews"}
            elif role == "order_fulfillment":
                queue["orders"] = {"count": 0, "label": "Orders to Process"}
            elif role == "delivery_coordinator":
                queue["deliveries"] = {"count": 0, "label": "Pending Deliveries"}
            elif role == "finance_clerk":
                queue["invoices"] = {"count": 0, "label": "Invoices to Process"}
            elif role == "hr_coordinator":
                queue["onboarding"] = {"count": 0, "label": "Onboarding Tasks"}
            elif role == "data_entry":
                queue["products"] = {"count": 0, "label": "Products to Enter"}
            elif role == "quality_analyst":
                queue["inspections"] = {"count": 0, "label": "Pending Inspections"}
            elif role == "social_media":
                queue["posts"] = {"count": 0, "label": "Scheduled Posts"}
            elif role == "inventory_manager":
                queue["reorders"] = {"count": 0, "label": "Items to Reorder"}
            elif role == "returns_processor":
                queue["returns"] = {"count": 0, "label": "Pending Returns"}
            elif role == "content_writer":
                queue["articles"] = {"count": 0, "label": "Articles to Write"}
            elif role == "photography_editor":
                queue["images"] = {"count": 0, "label": "Images to Edit"}
            elif role == "accounts_payable":
                queue["payables"] = {"count": 0, "label": "Invoices to Pay"}
            elif role == "accounts_receivable":
                queue["receivables"] = {"count": 0, "label": "Outstanding Invoices"}

        return queue

    def _get_default_workspace(self) -> dict:
        """Return default workspace for employees without roles."""
        return {
            "role": "general_employee",
            "all_roles": [],
            "features": ["profile", "leave", "attendance", "payslips"],
            "widgets": ["personal_stats", "leave_balance", "attendance"],
            "primary_role": None,
        }


class RoleAssignmentService:
    """Service for managing role assignments (by Admin-HR)."""

    def __init__(self, db: Session):
        self.db = db

    def assign_role(
        self,
        employee_id: int,
        role: str,
        assigned_by: int,
        is_primary: bool = False,
        department: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> EmployeeRoleAssignment:
        """Assign a role to an employee."""
        # Check if already assigned
        existing = self.db.query(EmployeeRoleAssignment).filter(
            EmployeeRoleAssignment.employee_id == employee_id,
            EmployeeRoleAssignment.role == role,
            EmployeeRoleAssignment.is_deleted.is_(False),
        ).first()
        if existing:
            existing.is_active = True
            existing.is_primary = is_primary
            self.db.commit()
            return existing

        assignment = EmployeeRoleAssignment(
            employee_id=employee_id,
            role=role,
            assigned_by=assigned_by,
            is_primary=is_primary,
            department=department,
            country_code=country_code,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke_role(self, employee_id: int, role: str) -> bool:
        """Revoke a role from an employee."""
        assignment = self.db.query(EmployeeRoleAssignment).filter(
            EmployeeRoleAssignment.employee_id == employee_id,
            EmployeeRoleAssignment.role == role,
            EmployeeRoleAssignment.is_deleted.is_(False),
        ).first()
        if not assignment:
            return False
        assignment.is_active = False
        self.db.commit()
        return True

    def get_employee_roles(self, employee_id: int) -> list[EmployeeRoleAssignment]:
        """Get all role assignments for an employee."""
        return self.db.query(EmployeeRoleAssignment).filter(
            EmployeeRoleAssignment.employee_id == employee_id,
            EmployeeRoleAssignment.is_active.is_(True),
            EmployeeRoleAssignment.is_deleted.is_(False),
        ).all()


def get_workspace_service(db: Session) -> EmployeeWorkspaceService:
    """Factory for EmployeeWorkspaceService."""
    return EmployeeWorkspaceService(db)


def get_role_assignment_service(db: Session) -> RoleAssignmentService:
    """Factory for RoleAssignmentService."""
    return RoleAssignmentService(db)
